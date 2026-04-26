"""Phase 3b — Stage 3a extended with green-technology investment G (Hasan 2021 style).

Decision variables: lot size Q, cycle time T, max backlog B = -Sicilia's s,
green-technology investment rate G.

Builds on Phase 3a's effective-cost reduction by adding Hasan (2021)
green-technology investment. R(G) = a G - b G^2 is a per-time emission
reduction; G is the per-time investment cost. Optionally, demand couples
to G via D(G, v) = D_0 + D_1 R(G) + m v.

Convention note. We adopt a *per-time* convention for G (currency / time)
and R(G) (emissions / time), matching docs/notation.md. This differs
from Hasan (2021), which uses a per-cycle convention (the per-cycle
profit X includes -G, the per-cycle emission tally includes -R(G)). The
functional form R(G) = aG - bG^2 is identical; only the units of (a, b)
change. The per-time convention gives a cleaner reduction to Phase 3a
and a closed-form FOC for G* when demand is decoupled (D_1 = 0).

Key structural result. The per-time TC decomposes as

    TC(Q, T, B, G) = (h + p_c e_h) I_h(x, T) + s I_b(x, T)
                    + (K + p_c e_K) / T          [Phase-3a effective costs]
                    + G - p_c R(G)               [green-tech contribution]
                    - p_c C_cap                  [cap rebate]

so for fixed G the optimal (Q*, T*, B*) is the Phase-3a optimum at the
G-dependent demand D(G) -- the green-tech term G - p_c R(G) does not
depend on (Q, T, B). The full optimum is then a univariate search

    TC*(G) = TC*_3a(D(G), C_cap=0) + G - p_c R(G) - p_c C_cap

over G in [0, a/(2b)]. R(G) is symmetric about a/(2b) and increasing
investment beyond that point is dominated (same R, higher G), so the
upper bound is tight.

Closed-form FOC when D_1 = 0 (no demand coupling): TC*_3a(D_0 + m v) is
constant in G, so the inner objective is just G - p_c R(G); the FOC
1 - p_c (a - 2 b G) = 0 gives

    G* = max(0, (a - 1/p_c) / (2b))      (p_c > 0)
    G* = 0                                (p_c = 0).

The interior solution exists iff p_c a > 1, i.e., the marginal carbon
saving p_c R'(0) = p_c a exceeds the marginal investment cost 1.

Reductions:
    p_c = 0                              -> G* = 0; pure Sicilia at D(0)
    D_1 = 0, m = 0, v = 0, p_c a <= 1    -> G* = 0; pure Phase 3a at D_0
    D_1 = 0                              -> Phase 3a at D_0 + m v; G* closed form

Notation (unified, see docs/notation.md):
    G        green-tech investment per unit time   (currency / time)
    a        green-tech efficiency factor          (R(G) = a G - b G^2)
    b        green-tech curvature factor
    D_0      baseline demand rate
    D_1      demand sensitivity to R(G)
    m        promotion sensitivity
    v        promotion level
"""

from __future__ import annotations

from typing import TypedDict

from scipy.optimize import minimize_scalar

from src.novel.stage_3a_power_captrade import solve_power_demand_cap_and_trade


class GreenCapTradeResult(TypedDict):
    Q_star: float
    T_star: float
    B_star: float
    x_star: float
    G_star: float
    R_star: float
    demand: float
    cost: float
    emissions: float
    transfer: float
    threshold: float
    A_eff: float
    h_eff: float
    cost_carbon_free: float


def reduction(G: float, *, a: float, b: float) -> float:
    """Hasan green-tech reduction R(G) = a G - b G^2 (per unit time)."""
    return a * G - b * G * G


def demand(
    G: float, *,
    D0: float, D1: float, a: float, b: float, m: float, v: float,
) -> float:
    """Hasan demand law D(G, v) = D_0 + D_1 R(G) + m v."""
    return D0 + D1 * reduction(G, a=a, b=b) + m * v


def _g_closed_form(p_c: float, a: float, b: float) -> float:
    """Closed-form G* when demand is decoupled (D_1 = 0)."""
    if p_c <= 0.0:
        return 0.0
    return max(0.0, (a - 1.0 / p_c) / (2.0 * b))


def solve_power_demand_cap_and_trade_with_green(
    *,
    D0: float,
    n: float,
    alpha: float,
    h: float,
    s: float,
    K: float,
    e_K: float,
    e_h: float,
    p_c: float,
    C_cap: float,
    a: float,
    b: float,
    D1: float = 0.0,
    m: float = 0.0,
    v: float = 0.0,
) -> GreenCapTradeResult:
    """Optimal (Q*, T*, B*, G*) under power demand + cap-and-trade + green-tech.

    For fixed G, runs Phase 3a at the G-dependent demand D(G); then
    minimises TC*_3a(D(G)) + G - p_c R(G) over G in [0, a/(2b)]. When
    D_1 = 0 the inner cost is constant in G and a closed-form G* is used.

    Args:
        D0: baseline demand rate (Hasan's D_0).
        n: power-demand exponent (n > 0).
        alpha: production-to-demand ratio P / D (alpha > 1).
        h: holding cost rate.
        s: backlog cost rate.
        K: setup cost per cycle.
        e_K: emissions per setup (>= 0).
        e_h: emissions per unit-held per unit-time (>= 0).
        p_c: carbon price (>= 0).
        C_cap: emissions cap (>= 0).
        a: green-tech efficiency factor (a > 0).
        b: green-tech curvature factor (b > 0).
        D1: demand sensitivity to R(G); default 0 (decoupled).
        m: promotion sensitivity (>= 0); default 0.
        v: promotion level (>= 0); default 0.

    Returns:
        Dict with unified keys Q_star, T_star, cost, emissions plus
        novel-model extras B_star, x_star, G_star, R_star, demand,
        transfer, threshold, A_eff, h_eff, cost_carbon_free.
    """
    if min(D0, h, s, K, n) <= 0.0:
        raise ValueError("D0, h, s, K, n must all be positive.")
    if alpha <= 1.0:
        raise ValueError("alpha must be > 1 (production rate exceeds demand).")
    if min(e_K, e_h, p_c, C_cap) < 0.0:
        raise ValueError("e_K, e_h, p_c, C_cap must all be non-negative.")
    if a <= 0.0 or b <= 0.0:
        raise ValueError("a and b must be positive.")
    if min(D1, m, v) < 0.0:
        raise ValueError("D1, m, v must all be non-negative.")

    G_max = a / (2.0 * b)  # argmax R(G); search bracket is [0, G_max]

    def _objective(G: float) -> float:
        D_G = demand(G, D0=D0, D1=D1, a=a, b=b, m=m, v=v)
        if D_G <= 0.0:
            return 1e30
        sub = solve_power_demand_cap_and_trade(
            D=D_G, n=n, alpha=alpha, h=h, s=s, K=K,
            e_K=e_K, e_h=e_h, p_c=p_c, C_cap=0.0,
        )
        return sub["cost"] + G - p_c * reduction(G, a=a, b=b)

    if D1 == 0.0:
        G_star = _g_closed_form(p_c, a, b)
    else:
        res = minimize_scalar(
            _objective,
            bounds=(0.0, G_max),
            method="bounded",
            options={"xatol": 1e-9, "maxiter": 500},
        )
        G_candidate = float(res.x)
        # Bounded Brent may settle just inside the interior even when the
        # true optimum is the G=0 corner; compare explicitly.
        G_star = G_candidate if _objective(G_candidate) < _objective(0.0) else 0.0

    # Reconstruct everything at G*.
    R_star = reduction(G_star, a=a, b=b)
    D_star = D0 + D1 * R_star + m * v
    sub = solve_power_demand_cap_and_trade(
        D=D_star, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=e_K, e_h=e_h, p_c=p_c, C_cap=0.0,
    )

    # Per-time emissions = (e_K/T + e_h I_h) - R(G*) -- gross from Phase 3a
    # minus the green-tech reduction.
    emissions = sub["emissions"] - R_star
    cost_carbon_free = sub["cost_carbon_free"] + G_star
    cost = sub["cost"] + G_star - p_c * R_star - p_c * C_cap
    transfer = C_cap - emissions

    return {
        "Q_star": sub["Q_star"],
        "T_star": sub["T_star"],
        "B_star": sub["B_star"],
        "x_star": sub["x_star"],
        "G_star": G_star,
        "R_star": R_star,
        "demand": D_star,
        "cost": cost,
        "emissions": emissions,
        "transfer": transfer,
        "threshold": emissions,
        "A_eff": sub["A_eff"],
        "h_eff": sub["h_eff"],
        "cost_carbon_free": cost_carbon_free,
    }
