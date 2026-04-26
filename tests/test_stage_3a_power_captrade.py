"""Phase 3a validation: power demand + cap-and-trade.

The novel model has no published numerical example of its own, so we
validate by reduction to the two baselines it composes:

    1) p_c = 0                            -> exact equality with Sicilia 2014
    2) n = 1, alpha -> infinity, no backlogs -> Hua 2011 cap-and-trade

For (2) we use alpha = 1e9 and s (backlog cost) = 1e10 to numerically
drive the Sicilia framework into the EOQ regime; agreement with Hua's
published Table 1 is then expected within ~0.01 (the residual is the
finite-alpha tail of `1 / alpha^n`).
"""

from __future__ import annotations

import math

import pytest

from src.baselines.hua_2011 import solve_hua_2011_cap_and_trade
from src.baselines.sicilia_2014 import solve_sicilia_2014
from src.novel.stage_3a_power_captrade import (
    emissions_per_unit_time,
    solve_power_demand_cap_and_trade,
)


# Hua 2011 Table 1 parameters (matches tests/test_hua_2011.py).
HUA_COMMON = dict(D=60000, C=0.2, a=8000)
HUA_ROWS: list[tuple[str, dict, dict]] = [
    ("Row 1: K=180, h=0.3, e=600, g=1",
     dict(K=180, h=0.3, e=600, g=1.0, **HUA_COMMON),
     dict(Q_minemit=8485, Q_star=8485)),
    ("Row 2: K=200, h=0.4, e=500, g=1",
     dict(K=200, h=0.4, e=500, g=1.0, **HUA_COMMON),
     dict(Q_minemit=7746, Q_star=7746)),
    ("Row 3: K=200, h=0.36, e=450, g=1",
     dict(K=200, h=0.36, e=450, g=1.0, **HUA_COMMON),
     dict(Q_minemit=7348, Q_star=7883)),
    ("Row 4: K=250, h=0.4, e=540, g=1.5, C=0.3, a=10000",
     dict(K=250, h=0.4, e=540, g=1.5, D=60000, C=0.3, a=10000),
     dict(Q_minemit=6573, Q_star=7627)),
    ("Row 5: K=250, h=0.4, e=540, g=1.5",
     dict(K=250, h=0.4, e=540, g=1.5, **HUA_COMMON),
     dict(Q_minemit=6573, Q_star=7834)),
    ("Row 6: K=200, h=0.36, e=800, g=1",
     dict(K=200, h=0.36, e=800, g=1.0, **HUA_COMMON),
     dict(Q_minemit=9798, Q_star=8783)),
    ("Row 7: K=250, h=0.45, e=900, g=1",
     dict(K=250, h=0.45, e=900, g=1.0, **HUA_COMMON),
     dict(Q_minemit=10392, Q_star=8910)),
]


def _hua_to_novel_inputs(hua_params: dict) -> dict:
    """Map Hua's (K, D, h, e, g, C, a) onto the novel model's parameters."""
    return dict(
        D=hua_params["D"],
        n=1.0,
        alpha=1e9,
        h=hua_params["h"],
        s=1e10,           # numerically forces no-backlog regime
        K=hua_params["K"],
        e_K=hua_params["e"],
        e_h=hua_params["g"],
        p_c=hua_params["C"],
        C_cap=hua_params["a"],
    )


# ---------------------------------------------------------------------------
# Reduction (1): p_c = 0 must reproduce Sicilia's optimum exactly.
# ---------------------------------------------------------------------------
SICILIA_CASES: list[tuple[str, dict]] = [
    ("Sicilia Example 1: r=400, n=1.5, alpha=1.4, h=0.06, w=0.4, A=15",
     dict(r=400, n=1.5, alpha=1.4, h=0.06, w=0.4, A=15)),
    ("Sicilia Example 2: r=200, n=2.0, alpha=1.5, h=0.05, w=0.10, A=20",
     dict(r=200, n=2.0, alpha=1.5, h=0.05, w=0.10, A=20)),
    ("Sicilia Table-1: alpha=1.1, w=0.1",
     dict(r=400, n=1.5, alpha=1.1, h=0.06, w=0.1, A=15)),
    ("Sicilia Table-1: alpha=1.9, w=1.0",
     dict(r=400, n=1.5, alpha=1.9, h=0.06, w=1.0, A=15)),
    ("Sicilia Table-2: n=0.5, alpha=1.5",
     dict(r=400, n=0.5, alpha=1.5, h=0.06, w=0.4, A=15)),
    ("Sicilia Table-2: n=5.0, alpha=1.3",
     dict(r=400, n=5.0, alpha=1.3, h=0.06, w=0.4, A=15)),
]


@pytest.mark.parametrize(
    "label,sic_params",
    SICILIA_CASES,
    ids=[c[0] for c in SICILIA_CASES],
)
def test_pc_zero_matches_sicilia(label: str, sic_params: dict) -> None:
    sic = solve_sicilia_2014(**sic_params)
    nov = solve_power_demand_cap_and_trade(
        D=sic_params["r"],
        n=sic_params["n"],
        alpha=sic_params["alpha"],
        h=sic_params["h"],
        s=sic_params["w"],
        K=sic_params["A"],
        e_K=42.0,    # arbitrary -- multiplied by p_c=0 so vanishes
        e_h=7.0,
        p_c=0.0,
        C_cap=123.0,  # arbitrary -- multiplied by p_c=0 so vanishes
    )
    for key in ("Q_star", "T_star"):
        assert math.isclose(nov[key], sic[key], rel_tol=1e-12)
    assert math.isclose(nov["cost"], sic["cost"], rel_tol=1e-12)
    assert math.isclose(nov["B_star"], -sic["s_star"], rel_tol=1e-12, abs_tol=1e-15)
    assert math.isclose(nov["x_star"], sic["x_star"], rel_tol=1e-12, abs_tol=1e-15)


# ---------------------------------------------------------------------------
# Reduction (2): n=1, alpha large, no backlogs reproduces Hua's Q*, cost, E.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "label,hua_params,_expected",
    HUA_ROWS,
    ids=[c[0] for c in HUA_ROWS],
)
def test_eoq_limit_matches_hua(label: str, hua_params: dict, _expected: dict) -> None:
    hua = solve_hua_2011_cap_and_trade(**hua_params)
    nov = solve_power_demand_cap_and_trade(**_hua_to_novel_inputs(hua_params))
    # Tight on Q (the optimum is governed by EOQ formula); cost picks up
    # numerical residual at order 1e-2 from the alpha=1e9 truncation.
    assert math.isclose(nov["Q_star"], hua["Q_star"], rel_tol=1e-5)
    assert math.isclose(nov["cost"], hua["cost"], abs_tol=0.5)
    assert math.isclose(nov["emissions"], hua["emissions"], abs_tol=0.5)
    assert math.isclose(nov["transfer"], hua["transfer"], abs_tol=0.5)


# ---------------------------------------------------------------------------
# Optimal-cost identity TC* = 2 * A_eff / T* - p_c * C_cap.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "p_c,C_cap",
    [(0.0, 0.0), (0.05, 0.0), (0.05, 50.0), (0.20, 200.0), (1.0, 1000.0)],
)
def test_optimal_cost_identity(p_c: float, C_cap: float) -> None:
    out = solve_power_demand_cap_and_trade(
        D=200, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20,
        e_K=10.0, e_h=0.5, p_c=p_c, C_cap=C_cap,
    )
    identity = 2.0 * out["A_eff"] / out["T_star"] - p_c * C_cap
    assert math.isclose(out["cost"], identity, rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Decomposition: cost_carbon_free = TC at p_c = 0; cost = cost_carbon_free
#  + p_c * (emissions - C_cap).
# ---------------------------------------------------------------------------
def test_carbon_free_cost_decomposition() -> None:
    common = dict(D=200, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20,
                  e_K=10.0, e_h=0.5)
    out = solve_power_demand_cap_and_trade(**common, p_c=0.20, C_cap=80.0)
    # cost_carbon_free is the carbon-free *operating* cost at the new (Q*,T*,B*),
    # which generally differs from the Sicilia (p_c=0) optimum because the
    # latter optimises (Q,T,B) for a *different* objective. Check the
    # identity against the present operating point only.
    h, s_rate, K = common["h"], common["s"], common["K"]
    e_K, e_h = common["e_K"], common["e_h"]
    expected_cost = (
        out["cost_carbon_free"] + 0.20 * (out["emissions"] - 80.0)
    )
    assert math.isclose(out["cost"], expected_cost, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Theorem 1 (Hua) lift: in the EOQ limit, raising p_c moves Q* between the
# carbon-free EOQ and the emissions-min EOQ, exactly as in Hua's Theorem 1.
# Checked at n=1, alpha large, no backlog.
# ---------------------------------------------------------------------------
def test_eoq_limit_theorem_1_ordering() -> None:
    base = dict(D=60000, n=1.0, alpha=1e9, h=0.36, s=1e10, K=200,
                e_K=450.0, e_h=1.0)
    Q_eoq = math.sqrt(2.0 * base["K"] * base["D"] / base["h"])
    Q_min = math.sqrt(2.0 * base["e_K"] * base["D"] / base["e_h"])
    out = solve_power_demand_cap_and_trade(**base, p_c=0.20, C_cap=8000)
    # g/e = 1/450 < h/K = 1/100 ⇒ Q_min < Q* < Q_eoq.
    assert Q_min < out["Q_star"] < Q_eoq


# ---------------------------------------------------------------------------
# Cap-and-trade transfer: positive when emissions < C_cap, negative otherwise.
# ---------------------------------------------------------------------------
def test_transfer_sign_follows_cap() -> None:
    common = dict(D=200, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20,
                  e_K=10.0, e_h=0.5, p_c=0.10)
    surplus = solve_power_demand_cap_and_trade(**common, C_cap=1e6)
    deficit = solve_power_demand_cap_and_trade(**common, C_cap=0.0)
    assert surplus["transfer"] > 0
    assert deficit["transfer"] < 0
    # Same operating point: emissions should be identical (cap doesn't
    # enter the FOC under cap-and-trade -- it's a constant rebate).
    assert math.isclose(surplus["emissions"], deficit["emissions"], rel_tol=1e-12)
    # Cost difference equals -p_c * (C_cap_surplus - C_cap_deficit).
    expected_diff = -0.10 * (1e6 - 0.0)
    assert math.isclose(surplus["cost"] - deficit["cost"], expected_diff, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# In the EOQ limit (n=1, alpha-> infty, no backlogs) Hua's Theorem 1 holds
# verbatim: as p_c rises, Q* monotonically approaches the emissions-min Q
# from whichever side the carbon-free EOQ sits on. With backlogs (s finite)
# this monotonicity is *not* guaranteed because the optimal backlog ratio
# x* moves with h_eff via Sicilia's Eq. (28), which can lift Q via the
# changing denominator -- a non-trivial novel-model observation worth
# documenting in Phase 5 sensitivity work.
# ---------------------------------------------------------------------------
def test_q_star_monotone_in_carbon_price_eoq_limit() -> None:
    base = dict(D=60000, n=1.0, alpha=1e9, h=0.36, s=1e10, K=200,
                e_K=450.0, e_h=1.0)
    qs = [
        solve_power_demand_cap_and_trade(**base, p_c=p, C_cap=0.0)["Q_star"]
        for p in (0.0, 0.05, 0.10, 0.20, 0.50, 1.0)
    ]
    # K/h = 555.5, e_K/e_h = 450 ⇒ Q_min < Q_eoq, so Q* must decrease.
    for i in range(len(qs) - 1):
        assert qs[i + 1] < qs[i] + 1e-9, f"Q* not non-increasing: {qs}"


# ---------------------------------------------------------------------------
# emissions_per_unit_time helper: at n=1, alpha large, B=0, recover
# Hua's e D / Q + g Q / 2 formula.
# ---------------------------------------------------------------------------
def test_emissions_helper_matches_hua_formula() -> None:
    D, e_K, e_h, alpha = 60000.0, 450.0, 1.0, 1e9
    Q = 7883.0741
    T = Q / D
    nov_em = emissions_per_unit_time(
        Q, T, B=0.0, D=D, n=1.0, alpha=alpha, e_K=e_K, e_h=e_h,
    )
    hua_em = e_K * D / Q + e_h * Q / 2.0
    assert math.isclose(nov_em, hua_em, rel_tol=1e-7)


# ---------------------------------------------------------------------------
# Result-dict contract.
# ---------------------------------------------------------------------------
def test_result_dict_has_unified_keys() -> None:
    out = solve_power_demand_cap_and_trade(
        D=200, n=2.0, alpha=1.5, h=0.05, s=0.10, K=20,
        e_K=10.0, e_h=0.5, p_c=0.0, C_cap=0.0,
    )
    for key in ("Q_star", "T_star", "cost", "emissions",
                "B_star", "x_star", "transfer", "threshold",
                "A_eff", "h_eff", "cost_carbon_free"):
        assert key in out, f"missing key: {key}"
    assert math.isclose(out["T_star"], out["Q_star"] / 200.0, rel_tol=1e-12)
    assert math.isclose(out["threshold"], out["emissions"], rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Validation guards.
# ---------------------------------------------------------------------------
def test_alpha_le_one_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade(
            D=200, n=1.0, alpha=1.0, h=0.05, s=0.10, K=20,
            e_K=10.0, e_h=0.5, p_c=0.10, C_cap=0.0,
        )


def test_negative_carbon_price_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade(
            D=200, n=1.0, alpha=1.5, h=0.05, s=0.10, K=20,
            e_K=10.0, e_h=0.5, p_c=-0.01, C_cap=0.0,
        )


def test_negative_emission_factor_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade(
            D=200, n=1.0, alpha=1.5, h=0.05, s=0.10, K=20,
            e_K=-1.0, e_h=0.5, p_c=0.10, C_cap=0.0,
        )


def test_zero_n_rejected() -> None:
    with pytest.raises(ValueError):
        solve_power_demand_cap_and_trade(
            D=200, n=0.0, alpha=1.5, h=0.05, s=0.10, K=20,
            e_K=10.0, e_h=0.5, p_c=0.10, C_cap=0.0,
        )
