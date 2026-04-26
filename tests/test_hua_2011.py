"""Validate src/baselines/hua_2011.py against Table 1 of Hua, Cheng & Wang (2011).

Common parameters (Section 3): D = 60000, C = 0.2, a = 8000, e0 = g0 = 0.
Row 4 overrides C = 0.3, a = 10000.

The paper publishes Table 1 with each value rounded to the nearest integer
(or, for h, to two decimals). We pin the implementation to those printed
numbers with abs_tol = 1.0, which accommodates the +/- 0.5 rounding band.

Note on Row 1: the paper prints Q_hat = Q* = Q0 = 8453, but for K=180, h=0.3,
e=600, g=1, D=60000 the formulas give sqrt(72e6) = 8485.28, which is also
what the paper itself reports for a0 in the same row. We treat 8453 as a
typesetting artefact and validate Row 1 against the formula-correct 8485.
"""

from __future__ import annotations

import math

import pytest

from src.baselines.hua_2011 import solve_hua_2011_cap_and_trade


COMMON = dict(D=60000, C=0.2, a=8000)

# (label, params, expected). Expected values are the paper's printed
# Table 1 numbers, except where noted in the docstring.
TABLE_1_CASES: list[tuple[str, dict, dict]] = [
    (
        "Row 1: K=180, h=0.3, e=600, g=1  (g/e = h/K, all Q's coincide)",
        dict(K=180, h=0.3, e=600, g=1, **COMMON),
        # Paper prints 8453 for the three Q columns; this is a typesetting
        # error (it should be 8485, matching the a0 column and the formula).
        dict(
            Q_minemit=8485, Q_star=8485, Q_classical=8485,
            threshold=8485, transfer=-485,
            cost=2643, dco2=0, dtc=97,
        ),
    ),
    (
        "Row 2: K=200, h=0.4, e=500, g=1  (g/e = h/K)",
        dict(K=200, h=0.4, e=500, g=1, **COMMON),
        dict(
            Q_minemit=7746, Q_star=7746, Q_classical=7746,
            threshold=7746, transfer=254,
            cost=3048, dco2=0, dtc=-51,
        ),
    ),
    (
        "Row 3: K=200, h=0.36, e=450, g=1  (g/e > h/K)",
        dict(K=200, h=0.36, e=450, g=1, **COMMON),
        dict(
            Q_minemit=7348, Q_star=7883, Q_classical=8165,
            threshold=7367, transfer=633,
            cost=2815, dco2=23, dtc=-125,
        ),
    ),
    (
        "Row 4: K=250, h=0.4, e=540, g=1.5, C=0.3, a=10000",
        dict(K=250, h=0.4, e=540, g=1.5, D=60000, C=0.3, a=10000),
        dict(
            Q_minemit=6573, Q_star=7627, Q_classical=8660,
            threshold=9968, transfer=32,
            cost=3483, dco2=268, dtc=18,
        ),
    ),
    (
        "Row 5: K=250, h=0.4, e=540, g=1.5  (g/e > h/K)",
        dict(K=250, h=0.4, e=540, g=1.5, **COMMON),
        dict(
            Q_minemit=6573, Q_star=7834, Q_classical=8660,
            threshold=10011, transfer=-2011,
            cost=3884, dco2=225, dtc=420,
        ),
    ),
    (
        "Row 6: K=200, h=0.36, e=800, g=1  (g/e < h/K)",
        dict(K=200, h=0.36, e=800, g=1, **COMMON),
        dict(
            Q_minemit=9798, Q_star=8783, Q_classical=8165,
            threshold=9857, transfer=-1857,
            cost=3319, dco2=105, dtc=379,
        ),
    ),
    (
        "Row 7: K=250, h=0.45, e=900, g=1  (g/e < h/K)",
        dict(K=250, h=0.45, e=900, g=1, **COMMON),
        dict(
            Q_minemit=10392, Q_star=8910, Q_classical=8165,
            threshold=10516, transfer=-2516,
            cost=4191, dco2=181, dtc=517,
        ),
    ),
]


def _emissions_at(Q: float, *, K, D, h, e, g, C, a, e0=0.0, g0=0.0) -> float:
    return e * D / Q + g * Q / 2.0 + e0 * D + g0


@pytest.mark.parametrize(
    "label,params,expected",
    TABLE_1_CASES,
    ids=[c[0] for c in TABLE_1_CASES],
)
def test_table_1_row(label: str, params: dict, expected: dict) -> None:
    out = solve_hua_2011_cap_and_trade(**params)

    cf_at_q0 = _emissions_at(out["Q_classical"], **params)
    dco2_computed = cf_at_q0 - out["emissions"]
    dtc_computed = out["cost"] - out["cost_classical"]

    failures: list[str] = []
    direct_keys = (
        "Q_minemit", "Q_star", "Q_classical",
        "threshold", "transfer", "cost",
    )
    for key in direct_keys:
        ref = expected[key]
        got = out[key]
        if not math.isclose(got, ref, abs_tol=1.0):
            failures.append(f"  {key}: expected {ref}, got {got:.2f}")

    if not math.isclose(dco2_computed, expected["dco2"], abs_tol=1.0):
        failures.append(
            f"  dco2: expected {expected['dco2']}, got {dco2_computed:.2f}"
        )
    if not math.isclose(dtc_computed, expected["dtc"], abs_tol=1.0):
        failures.append(
            f"  dtc: expected {expected['dtc']}, got {dtc_computed:.2f}"
        )
    assert not failures, f"{label}\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Theorem 1 trichotomy: Q* sits between Q0 and Q_hat (or coincides if g/e=h/K).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [c[1] for c in TABLE_1_CASES],
    ids=[c[0] for c in TABLE_1_CASES],
)
def test_theorem_1_ordering(params: dict) -> None:
    out = solve_hua_2011_cap_and_trade(**params)
    K, h, e, g = params["K"], params["h"], params["e"], params["g"]
    ratio_carbon, ratio_cost = g / e, h / K
    Qs, Q0, Qh = out["Q_star"], out["Q_classical"], out["Q_minemit"]
    if math.isclose(ratio_carbon, ratio_cost, rel_tol=1e-9):
        assert math.isclose(Qs, Q0, rel_tol=1e-9)
        assert math.isclose(Qs, Qh, rel_tol=1e-9)
    elif ratio_carbon > ratio_cost:
        assert Qh < Qs < Q0, f"expected Qh < Q* < Q0 but got {Qh}, {Qs}, {Q0}"
    else:
        assert Q0 < Qs < Qh, f"expected Q0 < Q* < Qh but got {Q0}, {Qs}, {Qh}"


# ---------------------------------------------------------------------------
# When carbon is free (C=0) the model collapses to the classical EOQ.
# ---------------------------------------------------------------------------
def test_zero_carbon_price_recovers_classical_eoq() -> None:
    out = solve_hua_2011_cap_and_trade(
        K=180, D=60000, h=0.3, e=600, g=1, C=0.0, a=8000,
    )
    assert math.isclose(out["Q_star"], out["Q_classical"], rel_tol=1e-12)
    assert math.isclose(out["cost"], out["cost_classical"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Theorem 2(1): the cap-and-trade Q* never emits MORE than the classical Q0.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [c[1] for c in TABLE_1_CASES],
    ids=[c[0] for c in TABLE_1_CASES],
)
def test_theorem_2_1_emissions_non_increasing(params: dict) -> None:
    out = solve_hua_2011_cap_and_trade(**params)
    cf_at_q0 = _emissions_at(out["Q_classical"], **params)
    assert out["emissions"] <= cf_at_q0 + 1e-9


# ---------------------------------------------------------------------------
# Theorem 2(3): if X < 0 (retailer buys), TC(Q*) > TC0.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [c[1] for c in TABLE_1_CASES],
    ids=[c[0] for c in TABLE_1_CASES],
)
def test_theorem_2_3_buying_implies_higher_cost(params: dict) -> None:
    out = solve_hua_2011_cap_and_trade(**params)
    if out["transfer"] < 0:
        assert out["cost"] > out["cost_classical"] - 1e-9


# ---------------------------------------------------------------------------
# Sanity: required unified keys are present.
# ---------------------------------------------------------------------------
def test_result_dict_keys() -> None:
    out = solve_hua_2011_cap_and_trade(
        K=200, D=60000, h=0.4, e=500, g=1, C=0.2, a=8000,
    )
    for key in ("Q_star", "T_star", "cost", "emissions"):
        assert key in out, f"missing required unified key: {key}"
    assert math.isclose(out["T_star"], out["Q_star"] / 60000, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# threshold == emissions(Q*) by Theorem 3, and X = a - threshold.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [c[1] for c in TABLE_1_CASES],
    ids=[c[0] for c in TABLE_1_CASES],
)
def test_threshold_equals_emissions_at_q_star(params: dict) -> None:
    out = solve_hua_2011_cap_and_trade(**params)
    assert math.isclose(out["threshold"], out["emissions"], rel_tol=1e-12)
    assert math.isclose(out["transfer"], params["a"] - out["threshold"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# e0/g0 offsets shift cost/emissions by exactly C*(e0 D + g0) and don't move Q*.
# Eq. (5): TC(Q) = (K + Ce) D/Q + (h + Cg) Q/2 - C * (a - e0 D - g0). The Q*
# that minimises this is independent of e0, g0; only the constant -C(a - ...)
# moves, raising TC by +C(e0 D + g0). Emissions rise by exactly e0 D + g0.
# ---------------------------------------------------------------------------
def test_e0_g0_offsets_shift_cost_and_emissions_only() -> None:
    base = dict(K=200, D=60000, h=0.4, e=500, g=1, C=0.2, a=8000)
    out_no = solve_hua_2011_cap_and_trade(**base)
    out_yes = solve_hua_2011_cap_and_trade(**base, e0=0.01, g0=100.0)

    assert math.isclose(out_no["Q_star"], out_yes["Q_star"], rel_tol=1e-12)
    extra = 0.01 * 60000 + 100.0
    assert math.isclose(
        out_yes["emissions"] - out_no["emissions"], extra, rel_tol=1e-12,
    )
    assert math.isclose(
        out_yes["cost"] - out_no["cost"], base["C"] * extra, rel_tol=1e-12,
    )
