"""Phase 3b validation: power demand + cap-and-trade + green-tech investment.

The Phase 3b model has no published numerical example, so we validate
by reduction:

    1) p_c = 0                     -> G* = 0; reduces to Phase 3a at D = D_0+m v
    2) D_1 = 0 (demand decoupled)  -> G* matches the closed-form FOC
    3) Optimal-cost identity        -> TC* = TC*_3a(D*) + G* - p_c R(G*) - p_c C_cap

plus structural / monotonicity checks on G* and the result-dict contract.
The closed-form G* on the D_1 = 0 path serves as the analytical anchor
for the entire phase.
"""

from __future__ import annotations

import math

import pytest

from src.novel.stage_3a_power_captrade import solve_power_demand_cap_and_trade
from src.novel.stage_3b_with_green import (
    demand,
    reduction,
    solve_power_demand_cap_and_trade_with_green,
)


# ---------------------------------------------------------------------------
# Reduction (1): p_c = 0  ->  G* = 0  ->  Phase 3a at D = D_0 + m v.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "label,D0,n,alpha,h,s,K,m,v",
    [
        ("Sicilia-like, no promotion", 200.0, 2.0, 1.5, 0.05, 0.10, 20.0, 0.0, 0.0),
        ("With promotion", 200.0, 2.0, 1.5, 0.05, 0.10, 20.0, 0.5, 10.0),
        ("Power-demand exponent n=0.5", 400.0, 0.5, 1.4, 0.06, 0.4, 15.0, 0.0, 0.0),
        ("Power-demand exponent n=5.0", 400.0, 5.0, 1.3, 0.06, 0.4, 15.0, 0.2, 5.0),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_zero_carbon_price_reduces_to_phase_3a(
    label: str, D0: float, n: float, alpha: float, h: float, s: float, K: float,
    m: float, v: float,
) -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=D0, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=10.0, e_h=0.5, p_c=0.0, C_cap=0.0,
        a=5.0, b=0.5, D1=0.0, m=m, v=v,
    )
    expected = solve_power_demand_cap_and_trade(
        D=D0 + m * v, n=n, alpha=alpha, h=h, s=s, K=K,
        e_K=10.0, e_h=0.5, p_c=0.0, C_cap=0.0,
    )
    assert out["G_star"] == 0.0
    assert math.isclose(out["R_star"], 0.0, abs_tol=1e-15)
    for key in ("Q_star", "T_star", "B_star", "x_star", "cost"):
        assert math.isclose(out[key], expected[key], rel_tol=1e-12, abs_tol=1e-15)


# ---------------------------------------------------------------------------
# Reduction (2): D_1 = 0  ->  closed-form G* = max(0, (a - 1/p_c)/(2b)).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "p_c,a,b,expected_g",
    [
        (0.0, 5.0, 0.5, 0.0),                          # p_c = 0 corner
        (0.1, 5.0, 0.5, 0.0),                          # p_c a = 0.5 < 1 -> corner
        (0.2, 5.0, 0.5, 0.0),                          # p_c a = 1     -> boundary
        (1.0, 5.0, 0.5, (5.0 - 1.0) / 1.0),            # = 4.0
        (2.0, 5.0, 0.5, (5.0 - 0.5) / 1.0),            # = 4.5
        (10.0, 5.0, 0.5, (5.0 - 0.1) / 1.0),           # = 4.9
        (1.0, 3.0, 1.0, (3.0 - 1.0) / 2.0),            # = 1.0
        (4.0, 3.0, 1.0, (3.0 - 0.25) / 2.0),           # = 1.375
    ],
)
def test_g_star_closed_form_when_decoupled(
    p_c: float, a: float, b: float, expected_g: float,
) -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=p_c, C_cap=0.0,
        a=a, b=b, D1=0.0, m=0.0, v=0.0,
    )
    assert math.isclose(out["G_star"], expected_g, rel_tol=1e-9, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# G* upper bound: a/(2b) is the unconstrained argmax of R(G); the optimum
# never exceeds it (any G > a/(2b) is dominated by 2*a/(2b) - G with same R
# but lower investment cost).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("p_c", [0.0, 0.1, 0.5, 1.0, 5.0, 100.0])
@pytest.mark.parametrize("D1", [0.0, 0.5, 5.0])
def test_g_star_bounded_by_a_over_2b(p_c: float, D1: float) -> None:
    a, b = 5.0, 0.5
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=p_c, C_cap=0.0,
        a=a, b=b, D1=D1, m=0.0, v=0.0,
    )
    assert 0.0 <= out["G_star"] <= a / (2.0 * b) + 1e-9


# ---------------------------------------------------------------------------
# G* monotone non-decreasing in p_c when demand is decoupled.
# ---------------------------------------------------------------------------
def test_g_star_monotone_non_decreasing_in_carbon_price() -> None:
    base = dict(D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
                e_K=10.0, e_h=0.5, C_cap=0.0,
                a=5.0, b=0.5, D1=0.0, m=0.0, v=0.0)
    Gs = [
        solve_power_demand_cap_and_trade_with_green(**base, p_c=p)["G_star"]
        for p in (0.0, 0.1, 0.2, 0.5, 1.0, 5.0, 100.0)
    ]
    for i in range(len(Gs) - 1):
        assert Gs[i + 1] >= Gs[i] - 1e-12, f"G* not non-decreasing: {Gs}"


# ---------------------------------------------------------------------------
# G* and R(G*) approach a/(2b) and a^2/(4b) as p_c -> infinity.
# ---------------------------------------------------------------------------
def test_g_star_approaches_peak_at_high_carbon_price() -> None:
    a, b = 5.0, 0.5
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=1e6, C_cap=0.0,
        a=a, b=b, D1=0.0, m=0.0, v=0.0,
    )
    assert math.isclose(out["G_star"], a / (2.0 * b), rel_tol=1e-5)
    assert math.isclose(out["R_star"], a * a / (4.0 * b), rel_tol=1e-5)


# ---------------------------------------------------------------------------
# Optimal-cost identity:
#   TC* = TC*_3a(D*, C_cap=0) + G* - p_c R(G*) - p_c C_cap.
# Holds for both the decoupled and demand-coupled paths.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "p_c,C_cap,a,b,D1,m,v",
    [
        (0.0, 0.0,   5.0, 0.5, 0.0, 0.0, 0.0),
        (0.5, 50.0,  5.0, 0.5, 0.0, 0.0, 0.0),
        (2.0, 200.0, 5.0, 0.5, 0.0, 0.0, 0.0),
        (1.0, 100.0, 5.0, 0.5, 2.0, 0.0, 0.0),     # demand-coupled
        (3.0, 0.0,   4.0, 1.0, 1.0, 0.3, 10.0),    # full coupling
        (5.0, 500.0, 4.0, 1.0, 0.5, 0.2, 5.0),
    ],
)
def test_optimal_cost_identity(
    p_c: float, C_cap: float,
    a: float, b: float, D1: float, m: float, v: float,
) -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=p_c, C_cap=C_cap,
        a=a, b=b, D1=D1, m=m, v=v,
    )
    inner = solve_power_demand_cap_and_trade(
        D=out["demand"], n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=p_c, C_cap=0.0,
    )
    expected = inner["cost"] + out["G_star"] - p_c * out["R_star"] - p_c * C_cap
    assert math.isclose(out["cost"], expected, rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Carbon-free decomposition: cost = cost_carbon_free + p_c (emissions - C_cap).
# ---------------------------------------------------------------------------
def test_carbon_free_decomposition() -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=0.5, C_cap=80.0,
        a=5.0, b=0.5, D1=0.0, m=0.0, v=0.0,
    )
    expected = out["cost_carbon_free"] + 0.5 * (out["emissions"] - 80.0)
    assert math.isclose(out["cost"], expected, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Net emissions = Phase-3a (gross) emissions  -  R(G*).
# ---------------------------------------------------------------------------
def test_emissions_net_of_green_reduction() -> None:
    base = dict(D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
                e_K=10.0, e_h=0.5, p_c=2.0, C_cap=0.0,
                a=5.0, b=0.5, D1=0.0, m=0.0, v=0.0)
    out = solve_power_demand_cap_and_trade_with_green(**base)
    inner = solve_power_demand_cap_and_trade(
        D=out["demand"], n=base["n"], alpha=base["alpha"], h=base["h"],
        s=base["s"], K=base["K"], e_K=base["e_K"], e_h=base["e_h"],
        p_c=base["p_c"], C_cap=0.0,
    )
    assert math.isclose(
        out["emissions"], inner["emissions"] - out["R_star"], rel_tol=1e-12,
    )


# ---------------------------------------------------------------------------
# Demand coupling: with D_1 > 0 and G* > 0, demand at the optimum exceeds
# the baseline D_0 + m v.
# ---------------------------------------------------------------------------
def test_demand_coupling_lifts_demand() -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=5.0, C_cap=0.0,
        a=5.0, b=0.5, D1=1.0, m=0.0, v=0.0,
    )
    assert out["G_star"] > 0.0
    assert out["R_star"] > 0.0
    assert out["demand"] > 200.0


# ---------------------------------------------------------------------------
# First-order optimality at an interior G* (D_1 > 0 numerical path):
#  numerical d/dG TC*(G)  ~  0.
# ---------------------------------------------------------------------------
def test_first_order_optimality_at_interior() -> None:
    base = dict(D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
                e_K=10.0, e_h=0.5, p_c=5.0, C_cap=0.0,
                a=5.0, b=0.5, D1=1.0, m=0.0, v=0.0)
    out = solve_power_demand_cap_and_trade_with_green(**base)
    G_star = out["G_star"]
    a_, b_ = base["a"], base["b"]
    assert 1e-3 < G_star < a_ / (2.0 * b_) - 1e-3, (
        f"interior G* expected; got {G_star}"
    )

    eps = 1e-5

    def f(G: float) -> float:
        D_G = base["D0"] + base["D1"] * (a_ * G - b_ * G * G) + base["m"] * base["v"]
        sub = solve_power_demand_cap_and_trade(
            D=D_G, n=base["n"], alpha=base["alpha"], h=base["h"], s=base["s"],
            K=base["K"], e_K=base["e_K"], e_h=base["e_h"],
            p_c=base["p_c"], C_cap=0.0,
        )
        return sub["cost"] + G - base["p_c"] * (a_ * G - b_ * G * G)

    grad = (f(G_star + eps) - f(G_star - eps)) / (2.0 * eps)
    assert abs(grad) < 1e-3, f"|f'(G*)| = {abs(grad):.2e} not near 0"


# ---------------------------------------------------------------------------
# Decoupled closed form gives the SAME TC* as a numerical search via the
# coupled path with D_1 = 1e-12 (effectively decoupled). Sanity check that
# the closed-form branch and the numerical branch agree.
# ---------------------------------------------------------------------------
def test_closed_form_matches_numerical_at_negligible_d1() -> None:
    base = dict(D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
                e_K=10.0, e_h=0.5, p_c=2.0, C_cap=10.0,
                a=5.0, b=0.5, m=0.0, v=0.0)
    closed = solve_power_demand_cap_and_trade_with_green(**base, D1=0.0)
    numer  = solve_power_demand_cap_and_trade_with_green(**base, D1=1e-12)
    # G* differ by O(D1) -- tight match expected.
    assert math.isclose(closed["G_star"], numer["G_star"], rel_tol=1e-5, abs_tol=1e-7)
    assert math.isclose(closed["cost"],   numer["cost"],   rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Promotion-only path (m v > 0, D_1 = 0, p_c = 0): G* = 0 and (Q*, T*) match
# Phase 3a at D = D_0 + m v.
# ---------------------------------------------------------------------------
def test_promotion_only_path() -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=0.0, C_cap=0.0,
        a=5.0, b=0.5, D1=0.0, m=2.0, v=15.0,
    )
    assert out["G_star"] == 0.0
    assert math.isclose(out["demand"], 200.0 + 2.0 * 15.0, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Result-dict contract: required keys, internal consistency.
# ---------------------------------------------------------------------------
def test_result_dict_contract() -> None:
    out = solve_power_demand_cap_and_trade_with_green(
        D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
        e_K=10.0, e_h=0.5, p_c=0.5, C_cap=50.0,
        a=5.0, b=0.5, D1=1.0, m=0.3, v=10.0,
    )
    expected_keys = {
        "Q_star", "T_star", "B_star", "x_star",
        "G_star", "R_star", "demand",
        "cost", "emissions", "transfer", "threshold",
        "A_eff", "h_eff", "cost_carbon_free",
    }
    assert set(out.keys()) == expected_keys
    # Q* = D* T*  (Sicilia identity lifted through Phase 3a).
    assert math.isclose(out["Q_star"], out["demand"] * out["T_star"], rel_tol=1e-9)
    # R(G*) consistent with a, b
    assert math.isclose(
        out["R_star"], 5.0 * out["G_star"] - 0.5 * out["G_star"] ** 2,
        rel_tol=1e-12, abs_tol=1e-15,
    )
    # transfer = C_cap - emissions; threshold = emissions
    assert math.isclose(out["transfer"], 50.0 - out["emissions"], rel_tol=1e-12)
    assert math.isclose(out["threshold"], out["emissions"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Helpers (reduction, demand) match the documented formulas.
# ---------------------------------------------------------------------------
def test_reduction_helper() -> None:
    G, a, b = 4.0, 5.0, 0.5
    assert math.isclose(reduction(G, a=a, b=b), a * G - b * G * G, rel_tol=1e-12)


def test_demand_helper() -> None:
    G = 3.0
    a, b, D0, D1, m, v = 5.0, 0.5, 30.0, 10.0, 0.3, 20.0
    expected = D0 + D1 * (a * G - b * G * G) + m * v
    assert math.isclose(
        demand(G, D0=D0, D1=D1, a=a, b=b, m=m, v=v), expected, rel_tol=1e-12,
    )


# ---------------------------------------------------------------------------
# Validation guards.
# ---------------------------------------------------------------------------
def test_a_must_be_positive() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade_with_green(
            D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
            e_K=10.0, e_h=0.5, p_c=0.5, C_cap=0.0,
            a=0.0, b=0.5,
        )


def test_b_must_be_positive() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade_with_green(
            D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
            e_K=10.0, e_h=0.5, p_c=0.5, C_cap=0.0,
            a=5.0, b=-0.1,
        )


def test_negative_d1_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade_with_green(
            D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
            e_K=10.0, e_h=0.5, p_c=0.5, C_cap=0.0,
            a=5.0, b=0.5, D1=-0.1,
        )


def test_alpha_le_one_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade_with_green(
            D0=200.0, n=2.0, alpha=1.0, h=0.05, s=0.10, K=20.0,
            e_K=10.0, e_h=0.5, p_c=0.5, C_cap=0.0,
            a=5.0, b=0.5,
        )


def test_negative_carbon_price_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade_with_green(
            D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
            e_K=10.0, e_h=0.5, p_c=-0.1, C_cap=0.0,
            a=5.0, b=0.5,
        )
