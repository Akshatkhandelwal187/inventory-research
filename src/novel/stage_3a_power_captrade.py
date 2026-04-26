"""Phase 3a — Minimum viable contribution: power demand + cap-and-trade.

Combines Sicilia (2014) power-demand structure with Hua (2011) cap-and-trade
emissions accounting. Decision variables: lot size Q, cycle time T, max
backlog B = -s.

Key structural result (proved below). Hua's cap-and-trade carbon cost
collapses cleanly into Sicilia's effective-cost form:

    A_eff = A + p_c * e_K        (setup cost picks up emissions per setup)
    h_eff = h + p_c * e_h        (holding cost picks up emissions per held unit)

so the *cap-and-trade* optimum (Q*, T*, B*) is the *Sicilia* optimum at
(A_eff, h_eff), and the optimal cost is

    TC_novel(Q*, T*, B*) = TC_sicilia(A_eff, h_eff) - p_c * C_cap.

In particular Sicilia's optimal-cost identity TC* = 2 * A / T* lifts to
TC_novel* = 2 * A_eff / T* - p_c * C_cap.

Reductions:
    p_c = 0                                 -> pure Sicilia (2014)
    n = 1, alpha -> infinity, B = 0          -> Hua (2011) cap-and-trade
                                              (uniform demand, instant
                                               replenishment, no backlogs)

Notation (unified, see docs/notation.md):
    D       demand rate                          (Sicilia r, Hua D)
    n       power-demand exponent (n > 0)
    alpha   production-to-demand ratio P / D     (alpha > 1)
    h       holding cost rate
    s       backlog cost rate                    (Sicilia w)
    K       setup / ordering cost                (Sicilia A, Hua K)
    e_K     emissions per setup                  (Hua e)
    e_h     emissions per unit held per time     (Hua g)
    p_c     carbon price (>= 0)                  (Hua C)
    C_cap   emissions cap per unit time          (Hua a)

Decision variables (returned):
    Q       lot size            (= D * T at the Sicilia optimum)
    T       cycle length
    B       maximum backlog (positive scalar; Sicilia's s = -B)
    x       backlog ratio B / (D * T)
"""

from __future__ import annotations

import math
from typing import TypedDict

from src.baselines.sicilia_2014 import solve_sicilia_2014, total_cost as sicilia_total_cost


class PowerCapTradeResult(TypedDict):
    Q_star: float
    T_star: float
    B_star: float
    x_star: float
    cost: float
    emissions: float
    transfer: float
    threshold: float
    A_eff: float
    h_eff: float
    cost_carbon_free: float


def _bracket_h(x: float, T: float, *, D: float, n: float, alpha: float) -> float:
    """Average inventory over a Sicilia (2014) cycle (units), evaluated at (x, T).

    Derivation: from the cycle profile in Sicilia 2014,
        avg inventory = (D T / (n+1)) * [ (1-x)^(n+1)
                                          + x^(n+1) / (alpha - 1)^n
                                          - 1 / alpha^n ].
    Multiplying by h and adding the backlog and setup terms reproduces the
    bracket_h piece of total_cost() in src/baselines/sicilia_2014.py.
    """
    rT = D * T
    return (rT / (n + 1.0)) * (
        (1.0 - x) ** (n + 1.0)
        + x ** (n + 1.0) / (alpha - 1.0) ** n
        - 1.0 / alpha ** n
    )


def emissions_per_unit_time(
    Q: float, T: float, B: float,
    *,
    D: float, n: float, alpha: float,
    e_K: float, e_h: float,
) -> float:
    """Emissions per unit time at a feasible (Q, T, B) operating point.

    Setup: e_K / T (one setup per cycle).
    Holding: e_h * average_inventory(x, T, D, n, alpha)  with x = B / (D T).
    Backlog emissions are *not* included here -- that is gap G2 / Phase 3b+.
    """
    if T <= 0.0 or Q <= 0.0:
        raise ValueError("Q and T must be positive.")
    rT = D * T
    if rT <= 0.0:
        raise ValueError("D * T must be positive.")
    x = B / rT
    return e_K / T + e_h * _bracket_h(x, T, D=D, n=n, alpha=alpha)


def solve_power_demand_cap_and_trade(
    *,
    D: float,
    n: float,
    alpha: float,
    h: float,
    s: float,
    K: float,
    e_K: float,
    e_h: float,
    p_c: float,
    C_cap: float,
) -> PowerCapTradeResult:
    """Optimal (Q*, T*, B*) under power demand and cap-and-trade carbon pricing.

    Solves
        min  TC(Q, T, B) = h * I_h + s * I_b + K / T
                            + p_c * (e_K / T + e_h * I_h - C_cap)
    where I_h, I_b are the per-cycle holding / backlog integrals divided by
    T. The optimisation reduces to a Sicilia (2014) call at the effective
    cost (A = K + p_c * e_K, h = h + p_c * e_h).

    Args:
        D: demand rate (units / time).
        n: power-demand exponent (n > 0).
        alpha: production-to-demand ratio P / D (alpha > 1).
        h: holding cost rate.
        s: backlog cost rate.
        K: setup / ordering cost per order.
        e_K: emissions per setup (>= 0).
        e_h: emissions per unit-held per unit-time (>= 0).
        p_c: carbon price (>= 0).
        C_cap: emissions cap (>= 0).

    Returns:
        Dict with unified keys Q_star, T_star, cost, emissions, plus the
        novel-model extras B_star, x_star, transfer, threshold, A_eff,
        h_eff, cost_carbon_free.
    """
    if min(D, h, s, K, n) <= 0.0:
        raise ValueError("D, h, s, K, n must all be positive.")
    if alpha <= 1.0:
        raise ValueError("alpha must be > 1 (production rate exceeds demand).")
    if min(e_K, e_h, p_c, C_cap) < 0.0:
        raise ValueError("e_K, e_h, p_c, C_cap must all be non-negative.")

    A_eff = K + p_c * e_K
    h_eff = h + p_c * e_h

    sub = solve_sicilia_2014(r=D, n=n, alpha=alpha, h=h_eff, w=s, A=A_eff)
    Q_star = sub["Q_star"]
    T_star = sub["T_star"]
    B_star = -sub["s_star"]
    x_star = sub["x_star"]
    tc_eff = sub["cost"]

    # tc_eff = (h+p_c*e_h)*I_h + s*I_b + (K+p_c*e_K)/T
    #        = TC_carbon_free + p_c * emissions
    emissions = emissions_per_unit_time(
        Q_star, T_star, B_star,
        D=D, n=n, alpha=alpha, e_K=e_K, e_h=e_h,
    )
    cost_carbon_free = tc_eff - p_c * emissions
    cost = tc_eff - p_c * C_cap
    transfer = C_cap - emissions
    threshold = emissions  # at the optimum the firm's emissions ARE the trade threshold

    return {
        "Q_star": Q_star,
        "T_star": T_star,
        "B_star": B_star,
        "x_star": x_star,
        "cost": cost,
        "emissions": emissions,
        "transfer": transfer,
        "threshold": threshold,
        "A_eff": A_eff,
        "h_eff": h_eff,
        "cost_carbon_free": cost_carbon_free,
    }
