"""Phase 2b — Hua, Cheng & Wang (2011): EOQ under cap-and-trade.

Reference: papers/Hua_2011.pdf  (pre-print: papers/ssrn1628953.pdf)
Validation target: published Table 1 — see tests/test_hua_2011.py

Notation (Hua paper -> unified):
    K     fixed ordering cost per order
    D     annual demand rate
    h     holding cost per unit per unit time
    e     emissions per order (truck-empty fixed component)
    e0    emissions per unit shipped (variable; default 0)
    g     emissions per unit held per unit time (variable)
    g0    fixed warehouse emissions per period (default 0)
    a     carbon cap per period
    C     carbon price per unit emissions

Decisions:
    Q     order size
    X     transfer of carbon credits  (X > 0 => sells; X < 0 => buys)

Optimal policy (Hua 2011, Eqs. 6-7 with X eliminated via the carbon balance):
    Q* = sqrt( 2 (K + C e) D / (h + C g) )
    TC(Q*) = sqrt( 2 D (K + C e) (h + C g) )  -  C (a - e0 D - g0)
    X* = a  -  CF(Q*)            where CF(Q) = e D / Q + g Q / 2 + e0 D + g0

Transfer threshold (Theorem 3):
    a0 = CF(Q*) = e sqrt( D (h + C g) / (2 (K + C e)) )
                + g sqrt( (K + C e) D / (2 (h + C g)) )
                + e0 D + g0

Comparison anchors:
    Q_classical = sqrt(2 K D / h)        classical EOQ (no carbon term)
    Q_minemit   = sqrt(2 e D / g)        order size that minimises emissions
    cost_classical = sqrt(2 K D h)
"""

from __future__ import annotations

import math
from typing import TypedDict


class HuaResult(TypedDict):
    Q_star: float
    T_star: float
    cost: float
    emissions: float
    transfer: float
    threshold: float
    Q_classical: float
    Q_minemit: float
    cost_classical: float


def solve_hua_2011_cap_and_trade(
    *,
    K: float,
    D: float,
    h: float,
    e: float,
    g: float,
    C: float,
    a: float,
    e0: float = 0.0,
    g0: float = 0.0,
) -> HuaResult:
    """Optimal EOQ under cap-and-trade (Hua, Cheng & Wang 2011).

    Args:
        K: ordering cost per order.
        D: annual demand rate.
        h: holding cost per unit per unit time.
        e: emissions per order (fixed, truck-empty component).
        g: emissions per unit held per unit time.
        C: carbon price (>= 0).
        a: carbon cap per period.
        e0: emissions per unit shipped (>= 0; default 0).
        g0: fixed warehouse emissions per period (>= 0; default 0).

    Returns:
        Dict with unified keys Q_star, T_star, cost, emissions, plus the
        Hua-specific extras transfer (X*), threshold (a0), Q_classical,
        Q_minemit, cost_classical.
    """
    if min(K, D, h) <= 0.0:
        raise ValueError("K, D, h must all be positive.")
    if min(e, g, e0, g0) < 0.0:
        raise ValueError("emission factors must be non-negative.")
    if C < 0.0:
        raise ValueError("Carbon price C must be non-negative.")

    Keff = K + C * e
    heff = h + C * g

    Q_star = math.sqrt(2.0 * Keff * D / heff)
    a_offset = a - e0 * D - g0
    cost = math.sqrt(2.0 * D * Keff * heff) - C * a_offset
    emissions = e * D / Q_star + g * Q_star / 2.0 + e0 * D + g0
    transfer = a - emissions
    threshold = (
        e * math.sqrt(D * heff / (2.0 * Keff))
        + g * math.sqrt(Keff * D / (2.0 * heff))
        + e0 * D + g0
    )
    Q_classical = math.sqrt(2.0 * K * D / h)
    Q_minemit = math.sqrt(2.0 * e * D / g) if g > 0.0 else float("inf")
    cost_classical = math.sqrt(2.0 * K * D * h)

    return {
        "Q_star": Q_star,
        "T_star": Q_star / D,
        "cost": cost,
        "emissions": emissions,
        "transfer": transfer,
        "threshold": threshold,
        "Q_classical": Q_classical,
        "Q_minemit": Q_minemit,
        "cost_classical": cost_classical,
    }
