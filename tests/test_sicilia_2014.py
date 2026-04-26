"""Validate src/baselines/sicilia_2014.py against published Tables 1-2.

Cases are pulled directly from Sicilia et al. (2014):
    - Examples 1 and 2 from Section 6 (Eqs. 45, 46 and following text).
    - A spread of rows from Tables 1 and 2.

Each case checks the optimal (x*, T*, Q*, s*, cost) against the published
numbers. Tolerances reflect the precision the paper reports (~6 digits for
the worked Examples, ~4 decimals for the tables).

Note on Example 1's published cost (274.055404 $/year):
    Independently substituting the published (x*, T*, s*) into Eq. (21)
    gives ~299, and the FOC identity C* = 2 * A/T* (which Eq. 21 implies
    for any optimum of this model — and which holds to <0.1% for every
    other case in this file) also gives ~299 from the published T*. The
    paper's other listed Example 1 figures (x*, T*, Q*, s*, t') are all
    self-consistent at ~299 and are validated below; only the printed
    cost appears to be a typographical/arithmetic error in the paper.
    See test_example_1_cost_paper_typo for the explicit check.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from src.baselines.sicilia_2014 import solve_sicilia_2014, total_cost


# ---------------------------------------------------------------------------
# Cases that the paper reports correctly and that we validate end-to-end.
# Each: (label, params, expected, abs_tol)
# ---------------------------------------------------------------------------
FULL_CASES: list[tuple[str, dict[str, float], dict[str, float], float]] = [
    (
        "Example 2 (n=0.5, alpha=1.2, w=6)",
        dict(r=1200, n=0.5, alpha=1.2, h=4, w=6, A=100),
        dict(
            x_star=0.029654,
            T_star=0.658703,
            Q_star=790.443743,
            s_star=-23.440159,
            cost=303.626925,
            t_prime=0.601311,
        ),
        1e-3,
    ),
    # Table 1: n=3, alpha=1.1, w=0.1
    (
        "Table1 alpha=1.1, w=0.1",
        dict(r=1200, n=3, alpha=1.1, h=4, w=0.1, A=100),
        dict(
            x_star=0.090007,
            s_star=-586.2918,
            T_star=5.4282,
            Q_star=6513.8467,
            cost=36.8486,
        ),
        1e-3,
    ),
    # Table 1: n=3, alpha=1.5, w=5.0
    (
        "Table1 alpha=1.5, w=5.0",
        dict(r=1200, n=3, alpha=1.5, h=4, w=5.0, A=100),
        dict(
            x_star=0.161603,
            s_star=-90.1421,
            T_star=0.4648,
            Q_star=557.7996,
            cost=430.2627,
        ),
        1e-3,
    ),
    # Table 1: n=3, alpha=1.9, w=1.0
    (
        "Table1 alpha=1.9, w=1.0",
        dict(r=1200, n=3, alpha=1.9, h=4, w=1.0, A=100),
        dict(
            x_star=0.358947,
            s_star=-276.1700,
            T_star=0.6412,
            Q_star=769.3892,
            cost=311.9357,
        ),
        1e-3,
    ),
    # Table 2: n=0.5, alpha=1.5, w=5.0
    (
        "Table2 n=0.5, alpha=1.5",
        dict(r=1200, n=0.5, alpha=1.5, h=4, w=5.0, A=100),
        dict(
            x_star=0.081199,
            s_star=-45.8768,
            T_star=0.4708,
            Q_star=564.9924,
            cost=424.7847,
        ),
        1e-3,
    ),
    # Table 2: n=2.0, alpha=1.1, w=5.0
    (
        "Table2 n=2.0, alpha=1.1",
        dict(r=1200, n=2.0, alpha=1.1, h=4, w=5.0, A=100),
        dict(
            x_star=0.057659,
            s_star=-67.4765,
            T_star=0.9752,
            Q_star=1170.2688,
            cost=205.0820,
        ),
        1e-3,
    ),
    # Table 2: n=2.0, alpha=1.7, w=5.0
    (
        "Table2 n=2.0, alpha=1.7",
        dict(r=1200, n=2.0, alpha=1.7, h=4, w=5.0, A=100),
        dict(
            x_star=0.201163,
            s_star=-103.0885,
            T_star=0.4271,
            Q_star=512.4624,
            cost=468.3267,
        ),
        1e-3,
    ),
    # Table 2: n=5.0, alpha=1.3, w=5.0
    (
        "Table2 n=5.0, alpha=1.3",
        dict(r=1200, n=5.0, alpha=1.3, h=4, w=5.0, A=100),
        dict(
            x_star=0.108902,
            s_star=-70.8316,
            T_star=0.5420,
            Q_star=650.4156,
            cost=368.9948,
        ),
        1e-3,
    ),
]


@pytest.mark.parametrize(
    "label,params,expected,abs_tol",
    FULL_CASES,
    ids=[c[0] for c in FULL_CASES],
)
def test_published_case(
    label: str,
    params: dict[str, float],
    expected: dict[str, float],
    abs_tol: float,
) -> None:
    out = solve_sicilia_2014(**params)
    failures: list[str] = []
    for key, ref in expected.items():
        rel_tol = abs_tol if abs(ref) < 1.0 else abs_tol * abs(ref)
        if not math.isclose(out[key], ref, rel_tol=abs_tol, abs_tol=max(rel_tol, abs_tol)):
            failures.append(f"  {key}: expected {ref:.6f}, got {out[key]:.6f}")
    assert not failures, f"{label}\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Example 1 from Section 6 — every value EXCEPT the printed cost.
# ---------------------------------------------------------------------------
EXAMPLE_1 = dict(r=1200, n=2.0, alpha=1.2, h=4, w=6, A=100)


def test_example_1_non_cost_values() -> None:
    out = solve_sicilia_2014(**EXAMPLE_1)
    expected = dict(
        x_star=0.09399,
        T_star=0.668965,
        Q_star=802.7575,
        s_star=-75.451310,
        t_prime=0.464559,
    )
    for key, ref in expected.items():
        assert math.isclose(out[key], ref, rel_tol=1e-4, abs_tol=1e-4), (
            f"Example 1 {key}: expected {ref}, got {out[key]}"
        )


def test_example_1_cost_paper_typo() -> None:
    """Document the typo: paper prints 274.055404, but Eq. (21) gives ~299.

    We pin our value at ~299 (matches FOC identity 2*A/T* and is consistent
    with every other validated case). If a corrigendum surfaces, update.
    """
    out = solve_sicilia_2014(**EXAMPLE_1)
    paper_published = 274.055404
    foc_identity = 2.0 * EXAMPLE_1["A"] / out["T_star"]  # ~298.97
    assert abs(out["cost"] - foc_identity) < 0.5, (
        "Cost should satisfy C* ~= 2*A/T* by Eq. (21) at the optimum."
    )
    assert abs(out["cost"] - paper_published) > 20.0, (
        "If this assertion fails, the paper's printed Example 1 cost is no "
        "longer anomalous — re-investigate."
    )


# ---------------------------------------------------------------------------
# Cross-check against Sicilia's own special case: uniform demand (n = 1)
# reduces to Naddor's EPQ-with-backorders, Eqs. (38)-(40).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [
        dict(r=1200, n=1.0, alpha=1.2, h=4, w=6, A=100),
        dict(r=500, n=1.0, alpha=1.5, h=2, w=8, A=50),
        dict(r=2000, n=1.0, alpha=2.0, h=10, w=3, A=300),
    ],
)
def test_uniform_demand_reduction(params: dict[str, float]) -> None:
    """At n=1, x*, T*, Q* must match the closed-form Naddor formulas (38)-(40)."""
    out = solve_sicilia_2014(**params)
    alpha, h, w, r, A = (params[k] for k in ("alpha", "h", "w", "r", "A"))

    x_closed = (alpha - 1.0) * h / (alpha * (h + w))
    T_closed = math.sqrt(2.0 * A * alpha * (h + w) / (r * (alpha - 1.0) * w * h))
    Q_closed = math.sqrt(2.0 * A * r * alpha * (h + w) / ((alpha - 1.0) * w * h))

    assert math.isclose(out["x_star"], x_closed, rel_tol=1e-10, abs_tol=1e-12)
    assert math.isclose(out["T_star"], T_closed, rel_tol=1e-10, abs_tol=1e-12)
    assert math.isclose(out["Q_star"], Q_closed, rel_tol=1e-10, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Sanity: x* satisfies Eq. (28) to machine precision.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [c[1] for c in FULL_CASES] + [EXAMPLE_1],
    ids=[c[0] for c in FULL_CASES] + ["Example 1"],
)
def test_x_star_satisfies_eq28(params: dict[str, float]) -> None:
    out = solve_sicilia_2014(**params)
    x = out["x_star"]
    n, alpha, h, w = params["n"], params["alpha"], params["h"], params["w"]
    residual = (1.0 - x) ** n - (x ** n) / ((alpha - 1.0) ** n) - w / (h + w)
    assert abs(residual) < 1e-12, f"Eq. (28) residual {residual:.2e} too large"


# ---------------------------------------------------------------------------
# Sanity: x* lies in (0, (alpha-1)/alpha) for every case.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [c[1] for c in FULL_CASES] + [EXAMPLE_1],
    ids=[c[0] for c in FULL_CASES] + ["Example 1"],
)
def test_x_star_in_feasible_interval(params: dict[str, float]) -> None:
    out = solve_sicilia_2014(**params)
    upper = (params["alpha"] - 1.0) / params["alpha"]
    assert 0.0 < out["x_star"] < upper


# ---------------------------------------------------------------------------
# Sanity: the unified result-dict keys promised in CLAUDE.md are present.
# ---------------------------------------------------------------------------
def test_result_dict_keys() -> None:
    out: dict[str, Any] = solve_sicilia_2014(**EXAMPLE_1)
    for key in ("Q_star", "T_star", "cost", "emissions"):
        assert key in out, f"missing required unified key: {key}"
    assert out["emissions"] == 0.0, "Sicilia 2014 has no emissions component"


# ---------------------------------------------------------------------------
# Numerical: cost(s*, T*) <= cost at perturbed nearby (s, T).
# ---------------------------------------------------------------------------
def test_optimum_is_local_minimum() -> None:
    out = solve_sicilia_2014(**EXAMPLE_1)
    s_star, T_star = out["s_star"], out["T_star"]
    base = total_cost(s_star, T_star, **EXAMPLE_1)
    for ds in (-1.0, 1.0):
        for dT in (-0.01, 0.01):
            assert total_cost(s_star + ds, T_star + dT, **EXAMPLE_1) > base - 1e-6
