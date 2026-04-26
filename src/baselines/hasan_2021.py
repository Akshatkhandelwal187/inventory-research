"""Phase 2d — Hasan, Roy, Daryanto & Wee (2021): green-tech investment, three carbon regimes.

Reference: papers/Hasan_2021.pdf
Validation target: published Table 3 numerical examples — see tests/test_hasan_2021.py

The paper develops three EOQ profit-maximisation models for a single-echelon
retailer who invests G dollars per year in green technology. Investment
reduces emissions by R(G) = a G - b G^2 and lifts demand to
    D(G) = D0 + D1 R(G) + m v
where v is a fixed promotion level (paper assumption d).

Per-cycle cash flow (Eq. 12 / 16 / 19, with Q = D T enforced):
    X_i = p D T - C_h D T^2 / 2 - C_p D T - pc * E(Q,G) - G - OC + rb

with E(Q, G) = D E_T d / Q + E_h D T^2 / 2 - R(G)  per cycle, and
    pc = C_1, rb = 0           (carbon tax)
    pc = C_2, rb = C_2 U       (cap-and-trade)
    pc = psi, rb = psi W       (strict carbon limit).

The total profit per unit time is TP_i(Q, G) = X_i / T with T = Q / D(G).

Notes on the strict-cap case (Section 3.4.3):
    Eq. 19 introduces psi as a Lagrange multiplier on E(Q,G) = W. In the
    paper's worked example (Table 3, Case 3), psi = 5 and W = 10 are both
    listed as inputs and the reported E* = 56.21 != W. We therefore expose
    psi and W as input parameters and solve the unconstrained
    maximisation; structurally this matches the cap-and-trade case with
    (C_2, U) replaced by (psi, W).

Notation (Hasan paper -> unified):
    p          unit selling price
    C_0        unit purchase price
    C_T        unit transport cost                 ->  Cp = C_0 + C_T
    C_h        unit holding cost per unit time
    OC         ordering cost per order
    E_T        emissions per unit distance shipped
    d          one-way delivery distance
    E_h        emissions per unit held per unit time
    D_0        constant baseline demand
    D_1        coefficient on R(G) in demand
    a          green-technology efficiency factor
    b          green-technology emission factor (R'' = -2b)
    m          demand sensitivity to promotion level
    v          promotion level
    C_1        carbon tax rate
    C_2        carbon trading price
    U          cap-and-trade emissions cap
    psi        Lagrange multiplier / shadow price under strict limit
    W          emissions cap under strict limit

Decisions: Q (lot size) and G (green investment dollars).
"""

from __future__ import annotations

import math
from typing import TypedDict

from scipy.optimize import minimize


class HasanResult(TypedDict):
    Q_star: float
    T_star: float
    G_star: float
    R_star: float
    demand: float
    emissions: float
    profit: float
    cost: float


def _reduction(G: float, *, a: float, b: float) -> float:
    return a * G - b * G * G


def _demand(G: float, *, D0: float, D1: float, a: float, b: float, m: float, v: float) -> float:
    return D0 + D1 * _reduction(G, a=a, b=b) + m * v


def _emissions_per_cycle(
    Q: float, G: float, *,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
) -> float:
    D = _demand(G, D0=D0, D1=D1, a=a, b=b, m=m, v=v)
    T = Q / D
    return D * ET * d / Q + Eh * Q * T / 2.0 - _reduction(G, a=a, b=b)


def _profit_rate(
    Q: float, G: float, *,
    p: float, Cp: float, Ch: float, OC: float,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
    pc: float, rb: float,
) -> float:
    """Annual profit TP_i(Q, G) for a (carbon-price, rebate) pair."""
    R = _reduction(G, a=a, b=b)
    D = D0 + D1 * R + m * v
    if D <= 0.0 or Q <= 0.0:
        return -math.inf
    T = Q / D
    DT2 = Q * T  # = Q^2 / D
    E_cycle = D * ET * d / Q + Eh * DT2 / 2.0 - R
    X = p * Q - Ch * DT2 / 2.0 - Cp * Q - pc * E_cycle - G - OC + rb
    return X / T


def _validate(
    *, p: float, Cp: float, Ch: float, OC: float,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
) -> None:
    if min(p, Cp, Ch, OC, ET, d, Eh, D0, D1, a, b) <= 0.0:
        raise ValueError("p, Cp, Ch, OC, ET, d, Eh, D0, D1, a, b must all be positive.")
    if min(m, v) < 0.0:
        raise ValueError("m and v must be non-negative.")


def _optimize(
    *, p: float, Cp: float, Ch: float, OC: float,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
    pc: float, rb: float,
) -> HasanResult:
    G_max = a / b  # feasibility (Eq. 5)
    G0 = a / (2.0 * b)  # argmax R(G)
    D0_eff = D0 + D1 * _reduction(G0, a=a, b=b) + m * v
    # Initial Q from the carbon-free EOQ flavour (rough but in the right ballpark).
    Q0 = math.sqrt(2.0 * OC * D0_eff / Ch)

    def neg_TP(x: tuple[float, float]) -> float:
        Q, G = x
        if Q <= 1e-6 or G <= 1e-6 or G >= G_max - 1e-6:
            return 1e15
        return -_profit_rate(
            Q, G, p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
            D0=D0, D1=D1, a=a, b=b, m=m, v=v, pc=pc, rb=rb,
        )

    res = minimize(
        neg_TP,
        x0=[Q0, G0],
        method="Nelder-Mead",
        options={"xatol": 1e-9, "fatol": 1e-10, "maxiter": 20000, "adaptive": True},
    )
    if not res.success:
        raise RuntimeError(f"Hasan 2021 optimisation failed: {res.message}")

    Q_star, G_star = float(res.x[0]), float(res.x[1])
    R_star = _reduction(G_star, a=a, b=b)
    D_star = D0 + D1 * R_star + m * v
    T_star = Q_star / D_star
    DT2 = Q_star * T_star
    emissions = D_star * ET * d / Q_star + Eh * DT2 / 2.0 - R_star
    profit = -float(res.fun)

    return {
        "Q_star": Q_star,
        "T_star": T_star,
        "G_star": G_star,
        "R_star": R_star,
        "demand": D_star,
        "emissions": emissions,
        "profit": profit,
        "cost": -profit,
    }


# ---------------------------------------------------------------------------
# Public solvers — one per regulatory regime.
# ---------------------------------------------------------------------------

def solve_hasan_2021_tax(
    *,
    p: float, Cp: float, Ch: float, OC: float,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
    C1: float,
) -> HasanResult:
    """Hasan 2021 Case 1: EOQ with green-tech investment under a carbon tax.

    Maximises TP_1(Q, G) = X_1 / T with T = Q / D(G); see Eq. (13).
    """
    _validate(p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
              D0=D0, D1=D1, a=a, b=b, m=m, v=v)
    if C1 < 0.0:
        raise ValueError("C1 (carbon tax) must be non-negative.")
    return _optimize(
        p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
        D0=D0, D1=D1, a=a, b=b, m=m, v=v,
        pc=C1, rb=0.0,
    )


def solve_hasan_2021_cap_and_trade(
    *,
    p: float, Cp: float, Ch: float, OC: float,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
    C2: float, U: float,
) -> HasanResult:
    """Hasan 2021 Case 2: EOQ with green-tech investment under cap-and-trade.

    Maximises TP_2(Q, G) = X_2 / T with T = Q / D(G); see Eq. (17).
    The retailer pays C_2 per unit emission and receives a constant rebate
    C_2 * U regardless of how the cap U compares to actual emissions.
    """
    _validate(p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
              D0=D0, D1=D1, a=a, b=b, m=m, v=v)
    if C2 < 0.0 or U < 0.0:
        raise ValueError("C2 and U must be non-negative.")
    return _optimize(
        p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
        D0=D0, D1=D1, a=a, b=b, m=m, v=v,
        pc=C2, rb=C2 * U,
    )


def solve_hasan_2021_strict_cap(
    *,
    p: float, Cp: float, Ch: float, OC: float,
    ET: float, d: float, Eh: float,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
    psi: float, W: float,
) -> HasanResult:
    """Hasan 2021 Case 3: EOQ with green-tech investment under a strict cap.

    Maximises TP_3(Q, G) = X_3 / T with T = Q / D(G); see Eq. (20).

    The paper's Eq. (19) writes psi as a Lagrange multiplier on the strict
    cap E(Q,G) = W, but Section 4.1 supplies psi and W as numerical inputs
    (psi = 5, W = 10) and reports E* = 56.21 != W. We therefore solve the
    same shadow-price relaxation: structurally identical to cap-and-trade
    with (C_2, U) replaced by (psi, W).
    """
    _validate(p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
              D0=D0, D1=D1, a=a, b=b, m=m, v=v)
    if psi < 0.0 or W < 0.0:
        raise ValueError("psi and W must be non-negative.")
    return _optimize(
        p=p, Cp=Cp, Ch=Ch, OC=OC, ET=ET, d=d, Eh=Eh,
        D0=D0, D1=D1, a=a, b=b, m=m, v=v,
        pc=psi, rb=psi * W,
    )
