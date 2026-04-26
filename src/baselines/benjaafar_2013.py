"""Phase 2c — Benjaafar, Li & Daskin (2013): lot-sizing under multiple carbon policies.

Reference: papers/Benjaafar_2013.pdf
Validation target: closed-form analytical EOQ model from Appendix II-B
                   (Theorem A.1) — see tests/test_benjaafar_2013.py.

The paper's primary models (P1-P7) are multi-period MILPs solved with a
commercial MILP solver and reported as 15 figures showing qualitative
curves; the precise per-figure parameters are not all printed in the
paper. The reproducible analytical content is in Appendix II-B, problem
A.P1, the EOQ specialisation that admits closed-form solutions for three
regulatory regimes:

    * strict carbon cap   (A.P1, Theorem A.1)
    * carbon tax          (P2 specialised to EOQ)
    * cap-and-offset      (P4 specialised to EOQ)

Phase 3c will build the unified multi-policy comparison on top of this
EOQ skeleton; the discrete multi-period MILP is deferred.

Notation (Benjaafar Appendix II-B -> unified):
    K        fixed ordering / setup cost per order
    c        unit purchase cost (additive constant in TC)
    h        holding cost per unit per unit time
    e        fixed emissions per order               (unified e_K)
    nu       emissions per unit purchased            (unified e_c)
    h_e      emissions per unit held per unit time   (unified e_h)
    d        deterministic demand rate (units / time)
    cap      emissions cap per unit time
    alpha    carbon tax rate or offset price

Anchors used throughout:
    Q_0   = sqrt(2 K d / h)              classical EOQ
    Q_e   = sqrt(2 e d / h_e)            emission-minimising Q
    c_hat = e d / Q_0 + h_e Q_0 / 2 + nu d   emissions at the classical EOQ
    c_min = sqrt(2 e h_e d) + nu d           minimum achievable emissions

Theorem A.1 in three lines:
    cap >= c_hat       =>  Q* = Q_0          (cap not binding)
    c_min <= cap <c_hat =>  Q* = boundary    (cap binding)
    cap < c_min        =>  infeasible
"""

from __future__ import annotations

import math
from typing import TypedDict


class BenjaafarResult(TypedDict):
    Q_star: float
    T_star: float
    cost: float
    emissions: float
    binding: bool
    offset: float
    Q_classical: float
    Q_minemit: float
    cap_at_classical: float
    cap_minimum: float


# ---------------------------------------------------------------------------
# Internal helpers (not part of the public API).
# ---------------------------------------------------------------------------

def _classical_eoq(K: float, d: float, h: float) -> float:
    return math.sqrt(2.0 * K * d / h)


def _min_emit_eoq(e: float, d: float, h_e: float) -> float:
    return math.sqrt(2.0 * e * d / h_e) if h_e > 0.0 else float("inf")


def _emissions_at(Q: float, *, e: float, d: float, h_e: float, nu: float) -> float:
    return e * d / Q + h_e * Q / 2.0 + nu * d


def _cost_at(Q: float, *, K: float, d: float, h: float, c: float) -> float:
    return K * d / Q + h * Q / 2.0 + c * d


def _validate(K: float, d: float, h: float, e: float, h_e: float,
              c: float, nu: float, alpha: float = 0.0) -> None:
    if min(K, d, h) <= 0.0:
        raise ValueError("K, d, h must all be positive.")
    if min(e, h_e, c, nu, alpha) < 0.0:
        raise ValueError("emission, cost, and price parameters must be non-negative.")


def _build_result(
    *, Q_star: float, K: float, d: float, h: float, c: float,
    e: float, h_e: float, nu: float, binding: bool, offset: float,
    extra_cost: float = 0.0,
) -> BenjaafarResult:
    return {
        "Q_star": Q_star,
        "T_star": Q_star / d,
        "cost": _cost_at(Q_star, K=K, d=d, h=h, c=c) + extra_cost,
        "emissions": _emissions_at(Q_star, e=e, d=d, h_e=h_e, nu=nu),
        "binding": binding,
        "offset": offset,
        "Q_classical": _classical_eoq(K, d, h),
        "Q_minemit": _min_emit_eoq(e, d, h_e),
        "cap_at_classical": _emissions_at(
            _classical_eoq(K, d, h), e=e, d=d, h_e=h_e, nu=nu,
        ),
        "cap_minimum": (
            (math.sqrt(2.0 * e * h_e * d) if h_e > 0 else 0.0) + nu * d
        ),
    }


# ---------------------------------------------------------------------------
# Public solvers.
# ---------------------------------------------------------------------------

def solve_benjaafar_2013_strict_cap(
    *,
    K: float,
    d: float,
    h: float,
    e: float,
    h_e: float,
    cap: float,
    c: float = 0.0,
    nu: float = 0.0,
) -> BenjaafarResult:
    """EOQ under a strict carbon cap (Benjaafar et al. 2013, Theorem A.1).

    Raises ValueError when cap < c_min (the problem is infeasible).
    """
    _validate(K, d, h, e, h_e, c, nu)

    Q_0 = _classical_eoq(K, d, h)
    Q_e = _min_emit_eoq(e, d, h_e)
    c_hat = _emissions_at(Q_0, e=e, d=d, h_e=h_e, nu=nu)
    c_min_val = (math.sqrt(2.0 * e * h_e * d) if h_e > 0 else 0.0) + nu * d

    if cap < c_min_val - 1e-9:
        raise ValueError(
            f"cap={cap:.4g} below minimum achievable emissions "
            f"c_min={c_min_val:.4g}; problem is infeasible."
        )

    if cap >= c_hat - 1e-12:
        Q_star = Q_0
        binding = False
    else:
        # h_e Q^2 - 2 (cap - nu d) Q + 2 e d = 0 (constraint at equality).
        bb = cap - nu * d
        disc = max(0.0, bb * bb - 2.0 * e * h_e * d)
        sqrt_disc = math.sqrt(disc)
        Q1 = (bb - sqrt_disc) / h_e
        Q2 = (bb + sqrt_disc) / h_e
        # f convex on R+, min at Q_0; on [Q1, Q2] the optimum is the
        # endpoint closer to Q_0. Q_0 < Q_e <=> Q_0 < Q1 here, so:
        Q_star = Q1 if Q_0 < Q_e else Q2
        binding = True

    return _build_result(
        Q_star=Q_star, K=K, d=d, h=h, c=c, e=e, h_e=h_e, nu=nu,
        binding=binding, offset=0.0,
    )


def solve_benjaafar_2013_tax(
    *,
    K: float,
    d: float,
    h: float,
    e: float,
    h_e: float,
    alpha: float,
    c: float = 0.0,
    nu: float = 0.0,
) -> BenjaafarResult:
    """EOQ under a carbon tax of rate alpha (Benjaafar et al. 2013, P2 EOQ form).

    Cost objective:
        TC(Q) = (K + alpha e) d/Q + (h + alpha h_e) Q/2 + (c + alpha nu) d

    Optimal Q has the same closed form as Hua 2011 cap-and-trade
    (without the rebate term -alpha cap):
        Q* = sqrt( 2 (K + alpha e) d / (h + alpha h_e) )
    """
    _validate(K, d, h, e, h_e, c, nu, alpha)

    Keff = K + alpha * e
    heff = h + alpha * h_e
    Q_star = math.sqrt(2.0 * Keff * d / heff)
    tax_paid = alpha * _emissions_at(Q_star, e=e, d=d, h_e=h_e, nu=nu)

    return _build_result(
        Q_star=Q_star, K=K, d=d, h=h, c=c, e=e, h_e=h_e, nu=nu,
        binding=alpha > 0.0, offset=0.0, extra_cost=tax_paid,
    )


def solve_benjaafar_2013_offset(
    *,
    K: float,
    d: float,
    h: float,
    e: float,
    h_e: float,
    cap: float,
    alpha: float,
    c: float = 0.0,
    nu: float = 0.0,
) -> BenjaafarResult:
    """EOQ under cap-and-offset (Benjaafar et al. 2013, P4 EOQ form).

    Firm pays alpha per unit of emissions ABOVE the cap; receives nothing
    for emitting less. Cost objective:
        TC(Q) = K d/Q + h Q/2 + c d + alpha * max(0, emissions(Q) - cap)

    Three regimes:
        c_hat <= cap                         => Q* = Q_0, no offset purchased
        f(Q_alpha) >= cap (offset profitable) => Q* = Q_alpha, z > 0
        otherwise (cap binds, offset not used) => Q* on cap boundary, z = 0
    """
    _validate(K, d, h, e, h_e, c, nu, alpha)

    Q_0 = _classical_eoq(K, d, h)
    c_hat = _emissions_at(Q_0, e=e, d=d, h_e=h_e, nu=nu)

    if c_hat <= cap + 1e-12:
        return _build_result(
            Q_star=Q_0, K=K, d=d, h=h, c=c, e=e, h_e=h_e, nu=nu,
            binding=False, offset=0.0,
        )

    Keff = K + alpha * e
    heff = h + alpha * h_e
    Q_alpha = math.sqrt(2.0 * Keff * d / heff)
    f_at_alpha = _emissions_at(Q_alpha, e=e, d=d, h_e=h_e, nu=nu)

    if f_at_alpha >= cap - 1e-12:
        z = max(0.0, f_at_alpha - cap)
        return _build_result(
            Q_star=Q_alpha, K=K, d=d, h=h, c=c, e=e, h_e=h_e, nu=nu,
            binding=z > 1e-9, offset=z, extra_cost=alpha * z,
        )

    # f(Q_alpha) < cap => offset would not be used; fall back to strict-cap.
    fallback = solve_benjaafar_2013_strict_cap(
        K=K, d=d, h=h, e=e, h_e=h_e, cap=cap, c=c, nu=nu,
    )
    return fallback
