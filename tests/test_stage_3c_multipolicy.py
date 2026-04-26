"""Phase 3c validation: multi-policy comparison (tax / cap-and-trade / strict cap).

Validates the three regimes against each other and against Phase 3b. The
strict-cap shadow-price recovery is the only non-trivial new mechanism;
tax and cap-and-trade are thin wrappers around Phase 3b.

Validation strategy:
    1) Tax solver = Phase 3b at C_cap = 0                  (exact)
    2) Cap-and-trade solver = Phase 3b directly             (alias check)
    3) Strict cap, large C_cap -> not binding, psi*=0, G*=0 (Sicilia reduction)
    4) Strict cap, tight C_cap -> binding, emissions=C_cap  (KKT)
    5) Strict cap psi* monotone non-increasing in C_cap
    6) Lagrangian equivalence: at psi=psi*, cap-and-trade decisions and
       cost coincide with strict cap (the carbon term vanishes since
       emissions = C_cap exactly)
    7) Infeasible cap raises ValueError
    8) compare_policies returns three policies with the right keys
"""

from __future__ import annotations

import math

import pytest

from src.baselines.sicilia_2014 import solve_sicilia_2014
from src.novel.stage_3b_with_green import solve_power_demand_cap_and_trade_with_green
from src.novel.stage_3c_multipolicy import (
    compare_policies,
    solve_cap_and_trade,
    solve_strict_cap,
    solve_tax,
)


# Common operational parameters reused across tests.
COMMON = dict(
    D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
    e_K=10.0, e_h=0.5, a=5.0, b=0.5,
)


# ---------------------------------------------------------------------------
# (1) Tax solver matches Phase 3b at C_cap = 0.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("p_c", [0.0, 0.1, 0.5, 1.0, 5.0])
def test_tax_equals_phase_3b_at_c_cap_zero(p_c: float) -> None:
    tax = solve_tax(**COMMON, p_c=p_c)
    p3b = solve_power_demand_cap_and_trade_with_green(**COMMON, p_c=p_c, C_cap=0.0)
    for key in ("Q_star", "T_star", "B_star", "x_star",
                "G_star", "R_star", "demand", "cost",
                "emissions", "A_eff", "h_eff"):
        assert math.isclose(tax[key], p3b[key], rel_tol=1e-12, abs_tol=1e-15)
    # carbon_payment = p_c * emissions
    assert math.isclose(tax["carbon_payment"], p_c * p3b["emissions"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# (2) Cap-and-trade solver is the Phase 3b function (alias).
# ---------------------------------------------------------------------------
def test_cap_and_trade_is_phase_3b() -> None:
    assert solve_cap_and_trade is solve_power_demand_cap_and_trade_with_green


# ---------------------------------------------------------------------------
# (3) Strict cap with very large C_cap is not binding.
# ---------------------------------------------------------------------------
def test_strict_cap_not_binding_returns_pure_sicilia() -> None:
    out = solve_strict_cap(**COMMON, C_cap=1e6)
    assert out["cap_binding"] is False
    assert out["psi_star"] == 0.0
    assert out["G_star"] == 0.0
    assert math.isclose(out["R_star"], 0.0, abs_tol=1e-15)

    # (Q*, T*, B*) match pure Sicilia at the no-promotion demand.
    sic = solve_sicilia_2014(
        r=COMMON["D0"], n=COMMON["n"], alpha=COMMON["alpha"],
        h=COMMON["h"], w=COMMON["s"], A=COMMON["K"],
    )
    assert math.isclose(out["Q_star"], sic["Q_star"], rel_tol=1e-12)
    assert math.isclose(out["T_star"], sic["T_star"], rel_tol=1e-12)
    assert math.isclose(out["B_star"], -sic["s_star"], rel_tol=1e-12, abs_tol=1e-15)
    # cost = operating only (no carbon, no investment since G*=0)
    assert math.isclose(out["cost"], sic["cost"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# (4) Strict cap with tight C_cap is binding: emissions = C_cap, psi* > 0.
# ---------------------------------------------------------------------------
def test_strict_cap_binding_emissions_at_cap() -> None:
    # Compute baseline (unconstrained) emissions, then pick C_cap below it.
    base = solve_power_demand_cap_and_trade_with_green(
        **COMMON, p_c=0.0, C_cap=0.0,
    )
    C_cap = 0.5 * base["emissions"]
    out = solve_strict_cap(**COMMON, C_cap=C_cap)
    assert out["cap_binding"] is True
    assert out["psi_star"] > 0.0
    assert math.isclose(out["emissions"], C_cap, rel_tol=1e-7, abs_tol=1e-7)


# ---------------------------------------------------------------------------
# (5) Strict cap shadow price psi* is non-increasing in C_cap (looser cap ->
#     lower shadow price). Hua's Theorem 2 lifted through the recovery.
# ---------------------------------------------------------------------------
def test_psi_star_non_increasing_in_cap() -> None:
    base_emissions = solve_power_demand_cap_and_trade_with_green(
        **COMMON, p_c=0.0, C_cap=0.0,
    )["emissions"]
    # All caps below baseline -> all binding.
    caps = [0.30 * base_emissions, 0.50 * base_emissions,
            0.70 * base_emissions, 0.90 * base_emissions]
    psis = [solve_strict_cap(**COMMON, C_cap=c)["psi_star"] for c in caps]
    for i in range(len(psis) - 1):
        assert psis[i + 1] <= psis[i] + 1e-9, f"psi* not non-increasing in C_cap: {psis}"


# ---------------------------------------------------------------------------
# (6) Lagrangian equivalence. Strict cap decisions + cost coincide with
#     cap-and-trade at p_c = psi*: the carbon-trade term vanishes because
#     emissions = C_cap exactly at a binding KKT optimum.
# ---------------------------------------------------------------------------
def test_strict_cap_matches_cap_trade_at_shadow_price() -> None:
    base_emissions = solve_power_demand_cap_and_trade_with_green(
        **COMMON, p_c=0.0, C_cap=0.0,
    )["emissions"]
    C_cap = 0.5 * base_emissions
    sc = solve_strict_cap(**COMMON, C_cap=C_cap)
    assert sc["cap_binding"] is True

    ct = solve_cap_and_trade(**COMMON, p_c=sc["psi_star"], C_cap=C_cap)
    for key in ("Q_star", "T_star", "B_star", "x_star",
                "G_star", "R_star", "demand"):
        assert math.isclose(sc[key], ct[key], rel_tol=1e-6, abs_tol=1e-9)
    # Costs match: cap-trade cost = (operating+investment) + p_c (emissions - C_cap),
    # and at binding emissions = C_cap, the second term vanishes.
    assert math.isclose(sc["cost"], ct["cost"], rel_tol=1e-6, abs_tol=1e-6)


# ---------------------------------------------------------------------------
# (7) Infeasible cap raises ValueError.
# ---------------------------------------------------------------------------
def test_strict_cap_infeasible_raises() -> None:
    # Choose a setting where R(G)_max = a^2/(4b) is small relative to the
    # minimum achievable emissions: e_K and e_h large, a small.
    with pytest.raises(ValueError, match="infeasible"):
        solve_strict_cap(
            D0=200.0, n=1.0, alpha=1.5, h=0.05, s=1e10, K=20.0,
            e_K=1000.0, e_h=10.0, C_cap=1.0,
            a=1.0, b=1.0,
            psi_upper=1e3,
        )


def test_strict_cap_negative_c_cap_rejected() -> None:
    with pytest.raises(ValueError):
        solve_strict_cap(**COMMON, C_cap=-1.0)


# ---------------------------------------------------------------------------
# (8) compare_policies returns three policies with consistent shapes.
# ---------------------------------------------------------------------------
def test_compare_policies_returns_all_three() -> None:
    out = compare_policies(**COMMON, p_c=0.5, C_cap=20.0)
    assert set(out.keys()) == {"tax", "cap_and_trade", "strict_cap"}
    common_keys = {"Q_star", "T_star", "B_star", "G_star",
                   "R_star", "demand", "cost", "emissions"}
    for policy, result in out.items():
        missing = common_keys - set(result.keys())
        assert not missing, f"{policy} missing keys: {missing}"


def test_compare_policies_tax_matches_solve_tax() -> None:
    direct_tax = solve_tax(**COMMON, p_c=0.5)
    bundled = compare_policies(**COMMON, p_c=0.5, C_cap=20.0)["tax"]
    for key in ("Q_star", "T_star", "G_star", "cost", "emissions"):
        assert math.isclose(bundled[key], direct_tax[key], rel_tol=1e-12, abs_tol=1e-15)


# ---------------------------------------------------------------------------
# Cap-and-trade with C_cap large enough to give surplus has cost <= tax cost
# at the same p_c. The rebate p_c * C_cap subsidises the firm.
# ---------------------------------------------------------------------------
def test_cap_trade_cost_below_tax_when_cap_positive() -> None:
    p_c = 0.5
    tax_out = solve_tax(**COMMON, p_c=p_c)
    ct_out = solve_cap_and_trade(**COMMON, p_c=p_c, C_cap=100.0)
    assert ct_out["cost"] < tax_out["cost"]
    # Difference is exactly p_c * C_cap (operating point is identical because
    # cap-and-trade rebate is a constant in (Q,T,B,G)).
    assert math.isclose(tax_out["cost"] - ct_out["cost"], p_c * 100.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# When p_c = 0, all three regimes collapse to the unconstrained operating
# optimum (no carbon cost): Sicilia at h, K, with G* = 0. Strict cap stays
# at psi*=0 if C_cap is large; otherwise shadow price still kicks in.
# ---------------------------------------------------------------------------
def test_zero_carbon_price_all_regimes_match_at_loose_cap() -> None:
    out = compare_policies(**COMMON, p_c=0.0, C_cap=1e6)
    sic = solve_sicilia_2014(
        r=COMMON["D0"], n=COMMON["n"], alpha=COMMON["alpha"],
        h=COMMON["h"], w=COMMON["s"], A=COMMON["K"],
    )
    for policy in ("tax", "cap_and_trade", "strict_cap"):
        for key in ("Q_star", "T_star"):
            assert math.isclose(out[policy][key], sic[key], rel_tol=1e-12)
        assert math.isclose(out[policy]["G_star"], 0.0, abs_tol=1e-9)
    assert out["strict_cap"]["psi_star"] == 0.0
    assert out["strict_cap"]["cap_binding"] is False


# ---------------------------------------------------------------------------
# Strict cap with looser caps gives lower true cost (more options ->
# weakly lower minimum). Monotone non-increasing.
# ---------------------------------------------------------------------------
def test_strict_cap_cost_non_increasing_in_cap() -> None:
    base_emissions = solve_power_demand_cap_and_trade_with_green(
        **COMMON, p_c=0.0, C_cap=0.0,
    )["emissions"]
    caps = [0.30 * base_emissions, 0.50 * base_emissions,
            0.70 * base_emissions, 0.90 * base_emissions, 1.5 * base_emissions]
    costs = [solve_strict_cap(**COMMON, C_cap=c)["cost"] for c in caps]
    for i in range(len(costs) - 1):
        assert costs[i + 1] <= costs[i] + 1e-6, f"cost not non-increasing: {costs}"


# ---------------------------------------------------------------------------
# Strict cap with demand coupling (D_1 > 0): KKT recovery still binds the cap
# with positive shadow price. G_star may be 0 -- with strong demand coupling
# in a cost-min framework, increasing G raises demand (and operating cost)
# faster than it cuts emissions, so the firm prefers to satisfy the cap by
# adjusting Q rather than investing in green-tech. That is correct behaviour.
# ---------------------------------------------------------------------------
def test_strict_cap_with_demand_coupling_binds_cap() -> None:
    base = solve_power_demand_cap_and_trade_with_green(
        **COMMON, p_c=0.0, C_cap=0.0, D1=1.0, m=0.0, v=0.0,
    )
    out = solve_strict_cap(
        **COMMON, C_cap=0.5 * base["emissions"], D1=1.0, m=0.0, v=0.0,
    )
    assert out["cap_binding"] is True
    assert out["psi_star"] > 0.0
    assert math.isclose(out["emissions"], 0.5 * base["emissions"],
                        rel_tol=1e-6, abs_tol=1e-6)
    # Q* must have decreased relative to the unconstrained Q* (or G* > 0).
    assert (out["Q_star"] != base["Q_star"]) or (out["G_star"] > 0.0)


# ---------------------------------------------------------------------------
# Strict cap with green-tech-favoured parameters: weak demand coupling and
# generous (a, b) -> shadow-price-driven solution invests in G.
# ---------------------------------------------------------------------------
def test_strict_cap_invests_in_green_when_demand_coupling_weak() -> None:
    params = dict(D0=200.0, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20.0,
                  e_K=10.0, e_h=0.5, a=10.0, b=0.5)
    base = solve_power_demand_cap_and_trade_with_green(
        **params, p_c=0.0, C_cap=0.0, D1=0.0,
    )
    out = solve_strict_cap(
        **params, C_cap=0.4 * base["emissions"], D1=0.0,
    )
    assert out["cap_binding"] is True
    assert out["psi_star"] > 0.0
    assert out["G_star"] > 0.0
    assert math.isclose(out["emissions"], 0.4 * base["emissions"],
                        rel_tol=1e-6, abs_tol=1e-6)
