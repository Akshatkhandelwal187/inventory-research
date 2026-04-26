"""Phase 3c — Multi-policy comparison built on the Phase 3b green-tech backbone.

Three carbon regulatory regimes share the Phase 3b operational structure
(Sicilia power demand + Hua emission accounting + Hasan green-tech
investment + Sicilia backlogs); only the carbon-cost / cap interaction
differs:

    Tax:           pay p_c per unit emission. No cap, no rebate.
    Cap-and-trade: pay p_c per unit emission, receive p_c C_cap rebate
                   (cap = ex-ante allowance; trading at price p_c).
    Strict cap:    total emissions <= C_cap, hard constraint, no carbon
                   market. Shadow price psi recovered via KKT.

Reduction. Each policy reduces to Phase 3b at a (p_c, C_cap) pair:
    Tax            -> Phase 3b at p_c = p_c (input),  C_cap = 0
    Cap-and-trade  -> Phase 3b at p_c = p_c (input),  C_cap = C_cap (input)
    Strict cap     -> Phase 3b at p_c = psi (shadow), C_cap = C_cap (input)
                      with psi solved from emissions(psi) = C_cap.

The strict-cap Lagrangian
    L = (operating + investment) + psi (emissions(Q,T,B,G) - C_cap)
      = h I_h + s I_b + K/T + G + psi (e_K/T + e_h I_h - R(G) - C_cap)
      = (h + psi e_h) I_h + s I_b + (K + psi e_K) / T + G - psi R(G) - psi C_cap
is exactly the Phase 3b TC at p_c = psi. Hence the strict-cap optimum
shares decision variables with cap-and-trade at p_c = psi*, but the
firm's *reported* cost differs: under strict cap there is no carbon
market, so the financial outflow is just operating + investment. (At a
binding optimum emissions = C_cap exactly, so the cap-and-trade carbon
term p_c (emissions - C_cap) vanishes -- the *cost* coincides too.)

Reductions:
    p_c = 0                               -> tax = cap-and-trade = pure Sicilia (G=0)
    C_cap = infinity (or large enough)    -> strict cap collapses to Sicilia (G=0)
    Strict cap binding emissions = C_cap  -> cap-and-trade at p_c = psi* matches

Notation (unified): see docs/notation.md. psi here corresponds to Hasan's
strict-cap multiplier (also recorded as p_c in the unified table) but is
solved as an output rather than supplied as an input.

Hasan baseline cross-check. Hasan (2021) implements the strict cap by
treating psi as an input parameter (psi=5, W=10 in Table 3 Case 3),
which leaves the cap unenforced (E*=56.21 != W=10). Phase 3c restores
the rigorous formulation: psi is recovered such that the cap binds
exactly when binding is optimal, else psi=0.
"""

from __future__ import annotations

from typing import TypedDict

from scipy.optimize import brentq

from src.novel.stage_3b_with_green import (
    GreenCapTradeResult,
    solve_power_demand_cap_and_trade_with_green,
)


class TaxResult(TypedDict):
    """Tax regime result: p_c per unit emission, no cap, no trading."""
    Q_star: float
    T_star: float
    B_star: float
    x_star: float
    G_star: float
    R_star: float
    demand: float
    cost: float            # operating + investment + p_c * emissions
    cost_carbon_free: float  # operating + investment only
    emissions: float
    carbon_payment: float  # = p_c * emissions
    A_eff: float
    h_eff: float


class StrictCapResult(TypedDict):
    """Strict-cap regime result: emissions <= C_cap (hard constraint)."""
    Q_star: float
    T_star: float
    B_star: float
    x_star: float
    G_star: float
    R_star: float
    demand: float
    cost: float            # operating + investment (no carbon market)
    emissions: float       # = C_cap when binding (within solver tol)
    psi_star: float        # KKT shadow price; 0 when cap not binding
    cap_binding: bool
    A_eff: float
    h_eff: float


# Cap-and-trade is Phase 3b directly. Re-exported under a policy-symmetric
# name so the three solvers form a uniform comparison API.
solve_cap_and_trade = solve_power_demand_cap_and_trade_with_green


def solve_tax(
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
    a: float,
    b: float,
    D1: float = 0.0,
    m: float = 0.0,
    v: float = 0.0,
) -> TaxResult:
    """Carbon-tax regime. Reduces to Phase 3b at C_cap = 0.

    The firm pays p_c per unit of net emissions; no rebate, no trading.
    Total cost is operating + investment + carbon_payment, exactly
    matching Phase 3b's `cost` field at C_cap = 0.

    Args:
        D0, n, alpha, h, s, K: Phase 3b operational parameters.
        e_K, e_h: emission factors per setup / per unit-time held.
        p_c: tax rate per unit emission (>= 0).
        a, b: green-tech parameters R(G) = aG - bG^2 (a, b > 0).
        D1, m, v: optional demand-coupling and promotion params.

    Returns:
        TaxResult.
    """
    sub = solve_power_demand_cap_and_trade_with_green(
        D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=e_K, e_h=e_h, p_c=p_c, C_cap=0.0,
        a=a, b=b, D1=D1, m=m, v=v,
    )
    return {
        "Q_star": sub["Q_star"],
        "T_star": sub["T_star"],
        "B_star": sub["B_star"],
        "x_star": sub["x_star"],
        "G_star": sub["G_star"],
        "R_star": sub["R_star"],
        "demand": sub["demand"],
        "cost": sub["cost"],
        "cost_carbon_free": sub["cost_carbon_free"],
        "emissions": sub["emissions"],
        "carbon_payment": p_c * sub["emissions"],
        "A_eff": sub["A_eff"],
        "h_eff": sub["h_eff"],
    }


def solve_strict_cap(
    *,
    D0: float,
    n: float,
    alpha: float,
    h: float,
    s: float,
    K: float,
    e_K: float,
    e_h: float,
    C_cap: float,
    a: float,
    b: float,
    D1: float = 0.0,
    m: float = 0.0,
    v: float = 0.0,
    psi_upper: float = 1.0e6,
    tol: float = 1.0e-8,
) -> StrictCapResult:
    """Strict-cap regime. Recovers shadow price psi via brentq on the cap.

    Solves
        min  (operating + investment)
        s.t. emissions(Q, T, B, G) <= C_cap.

    KKT-based algorithm:
      Step 1. Solve at psi = 0 (no carbon cost). With p_c = 0, Phase 3b's
              closed-form gives G* = 0 -- the unconstrained optimum.
      Step 2. If emissions <= C_cap (within tol), cap not binding;
              return Step-1 solution with psi* = 0.
      Step 3. Else, bracket psi in [0, psi_upper] and solve
                  emissions_at_psi(psi) - C_cap = 0
              with brentq. Phase 3b's emissions decrease in psi (Hua's
              Theorem 2 lifted), so a unique root exists when feasible.
              Reported cost is operating + investment only (no carbon
              market in a strict cap).

    Args:
        D0, n, alpha, h, s, K: Phase 3b operational parameters.
        e_K, e_h: emission factors per setup / per unit-time held.
        C_cap: strict cap (>= 0); units kg CO2e / time.
        a, b: green-tech parameters.
        D1, m, v: optional demand-coupling and promotion params.
        psi_upper: brentq upper bound for the shadow price. Default 1e6.
        tol: solver tolerance and binding-check slack. Default 1e-8.

    Returns:
        StrictCapResult with psi_star and cap_binding indicator.

    Raises:
        ValueError: if C_cap < 0, or if the cap is infeasible (emissions
            at psi = psi_upper still exceed C_cap).
    """
    if C_cap < 0.0:
        raise ValueError("C_cap must be non-negative.")

    # Step 1+2: psi = 0; with p_c=0 Phase 3b returns G_star = 0.
    base = solve_power_demand_cap_and_trade_with_green(
        D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=e_K, e_h=e_h, p_c=0.0, C_cap=C_cap,
        a=a, b=b, D1=D1, m=m, v=v,
    )
    if base["emissions"] <= C_cap + tol:
        return {
            "Q_star": base["Q_star"],
            "T_star": base["T_star"],
            "B_star": base["B_star"],
            "x_star": base["x_star"],
            "G_star": base["G_star"],
            "R_star": base["R_star"],
            "demand": base["demand"],
            "cost": base["cost_carbon_free"],
            "emissions": base["emissions"],
            "psi_star": 0.0,
            "cap_binding": False,
            "A_eff": base["A_eff"],
            "h_eff": base["h_eff"],
        }

    # Step 3: cap is binding. Verify feasibility at psi_upper, then brentq.
    upper = solve_power_demand_cap_and_trade_with_green(
        D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=e_K, e_h=e_h, p_c=psi_upper, C_cap=C_cap,
        a=a, b=b, D1=D1, m=m, v=v,
    )
    if upper["emissions"] > C_cap + tol:
        raise ValueError(
            f"Strict cap C_cap={C_cap} infeasible at psi_upper={psi_upper}: "
            f"emissions={upper['emissions']:.6f} still exceeds C_cap. "
            f"Either raise psi_upper, relax the cap, or boost the green-tech "
            f"capacity (a, b)."
        )

    def emissions_minus_cap(psi: float) -> float:
        out = solve_power_demand_cap_and_trade_with_green(
            D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
            e_K=e_K, e_h=e_h, p_c=psi, C_cap=C_cap,
            a=a, b=b, D1=D1, m=m, v=v,
        )
        return out["emissions"] - C_cap

    psi_star = float(brentq(
        emissions_minus_cap, 0.0, psi_upper, xtol=tol, rtol=tol,
    ))
    final = solve_power_demand_cap_and_trade_with_green(
        D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=e_K, e_h=e_h, p_c=psi_star, C_cap=C_cap,
        a=a, b=b, D1=D1, m=m, v=v,
    )
    return {
        "Q_star": final["Q_star"],
        "T_star": final["T_star"],
        "B_star": final["B_star"],
        "x_star": final["x_star"],
        "G_star": final["G_star"],
        "R_star": final["R_star"],
        "demand": final["demand"],
        "cost": final["cost_carbon_free"],
        "emissions": final["emissions"],
        "psi_star": psi_star,
        "cap_binding": True,
        "A_eff": final["A_eff"],
        "h_eff": final["h_eff"],
    }


def compare_policies(
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
    psi_upper: float = 1.0e6,
) -> dict[str, dict]:
    """Solve all three regimes at the same operational parameters.

    Tax and cap-and-trade share p_c; cap-and-trade and strict cap share
    C_cap. Tax ignores C_cap; strict cap ignores p_c.

    Returns:
        {'tax': TaxResult, 'cap_and_trade': GreenCapTradeResult,
         'strict_cap': StrictCapResult}, each as a plain dict.
    """
    return {
        "tax": dict(solve_tax(
            D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
            e_K=e_K, e_h=e_h, p_c=p_c,
            a=a, b=b, D1=D1, m=m, v=v,
        )),
        "cap_and_trade": dict(solve_cap_and_trade(
            D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
            e_K=e_K, e_h=e_h, p_c=p_c, C_cap=C_cap,
            a=a, b=b, D1=D1, m=m, v=v,
        )),
        "strict_cap": dict(solve_strict_cap(
            D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
            e_K=e_K, e_h=e_h, C_cap=C_cap,
            a=a, b=b, D1=D1, m=m, v=v,
            psi_upper=psi_upper,
        )),
    }
