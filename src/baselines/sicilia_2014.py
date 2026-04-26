"""Phase 2a — Sicilia et al. (2014): power demand, backlogs, finite production rate.

Reference: papers/Sicilia_2014.pdf
Validation target: published numerical examples (Tables 1-2) — see tests/test_sicilia_2014.py

Notation (Sicilia paper -> unified):
    r       average demand rate (units / time)
    n       power-demand pattern index (n > 0)
    alpha   production-rate parameter, P(t) = alpha * D(t), alpha > 1
    h       holding cost per unit per unit time
    w       backlogging (shortage) cost per unit per unit time
    A       ordering cost per order

Decision variables:
    T       scheduling period (cycle length)
    s       reorder point (negative when backlogs allowed)
    Q = r*T replenishment lot size

Optimal policy (Sicilia 2014, Section 4):
    Step 1. Solve Eq. (28) for x* in (0, (alpha-1)/alpha):
        (1 - x)^n  -  x^n / (alpha - 1)^n  =  w / (h + w)
    Step 2. T* = sqrt( A / (r * D(x*)) )                   [Eq. (32)]
        where D(x) = (h+w)/(n+1) * (1-x)^n
                   + n*w/(n+1) * x
                   - h / ((n+1) * alpha^n)
                   - w / (n+1)
    Step 3. s* = -x* * r * T*                              [Eq. (27)]
            Q* = r * T*                                    [Eq.  (8)]
            t' = T* / alpha^n                              [Eq.  (5)]
    Step 4. C* via Eq. (21).
"""

from __future__ import annotations

import math
from typing import TypedDict

from scipy.optimize import brentq


class SiciliaResult(TypedDict):
    Q_star: float
    T_star: float
    cost: float
    emissions: float
    s_star: float
    x_star: float
    t_prime: float


def _denominator(x: float, *, n: float, alpha: float, h: float, w: float) -> float:
    """The bracketed term in Eq. (32)/(33), i.e. r * denom = A / T*^2 at optimum."""
    inv = 1.0 / (n + 1.0)
    return (
        (h + w) * inv * (1.0 - x) ** n
        + n * w * inv * x
        - h * inv / (alpha ** n)
        - w * inv
    )


def total_cost(
    s: float,
    T: float,
    *,
    r: float,
    n: float,
    alpha: float,
    h: float,
    w: float,
    A: float,
) -> float:
    """Total cost per unit time, Eq. (21), valid for -(alpha-1)*r*T/alpha <= s <= 0."""
    rT = r * T
    sQ = s + rT
    neg_s = -s
    rn_Tn = (r ** n) * (T ** n)
    n1 = n + 1.0

    bracket_h = (
        sQ ** n1 / (n1 * rn_Tn)
        + neg_s ** n1 / (n1 * (alpha - 1.0) ** n * rn_Tn)
        - rT / (n1 * alpha ** n)
    )
    bracket_w = (
        sQ ** n1 / (n1 * rn_Tn)
        + neg_s ** n1 / (n1 * (alpha - 1.0) ** n * rn_Tn)
        - s
        - rT / n1
    )
    return h * bracket_h + w * bracket_w + A / T


def solve_sicilia_2014(
    *,
    r: float,
    n: float,
    alpha: float,
    h: float,
    w: float,
    A: float,
) -> SiciliaResult:
    """Optimal (Q*, T*, s*) for the Sicilia (2014) power-demand EPQ with backlogs.

    Args:
        r: average demand rate (units / time).
        n: power-demand pattern index (n > 0).
        alpha: production-rate parameter (alpha > 1).
        h: holding cost per unit per unit time.
        w: backlogging cost per unit per unit time.
        A: ordering / setup cost per order.

    Returns:
        Dict with the unified keys Q_star, T_star, cost, emissions, plus
        the Sicilia-specific extras s_star, x_star, t_prime.
    """
    if alpha <= 1.0:
        raise ValueError("alpha must be > 1 (production rate exceeds demand rate).")
    if n <= 0.0:
        raise ValueError("n must be > 0.")
    if min(r, h, w, A) <= 0.0:
        raise ValueError("r, h, w, A must all be positive.")

    upper = (alpha - 1.0) / alpha
    target = w / (h + w)

    def eq28(x: float) -> float:
        return (1.0 - x) ** n - (x ** n) / ((alpha - 1.0) ** n) - target

    eps = 1e-14 * max(1.0, upper)
    x_star = brentq(eq28, eps, upper - eps, xtol=1e-14, rtol=1e-14, maxiter=200)

    denom = _denominator(x_star, n=n, alpha=alpha, h=h, w=w)
    if denom <= 0.0:
        raise RuntimeError(
            f"Non-positive denominator ({denom:.4g}) in T* formula; "
            "the parameter combination has no interior optimum."
        )

    T_star = math.sqrt(A / (r * denom))
    Q_star = r * T_star
    s_star = -x_star * r * T_star
    t_prime = T_star / (alpha ** n)
    cost = total_cost(s_star, T_star, r=r, n=n, alpha=alpha, h=h, w=w, A=A)

    return {
        "Q_star": Q_star,
        "T_star": T_star,
        "cost": cost,
        "emissions": 0.0,
        "s_star": s_star,
        "x_star": x_star,
        "t_prime": t_prime,
    }
