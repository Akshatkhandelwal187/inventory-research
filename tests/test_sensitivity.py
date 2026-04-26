"""Phase 5 smoke tests for the gap G1-G5 sensitivity sweeps.

These tests run the full sweep scripts (the grids are small enough that
end-to-end execution is on the order of a few seconds), then assert:
  * the CSV file is created with the expected schema
  * the PDF figure is created and non-empty
  * the markdown findings note is created
  * a single structural identity per sweep that the sweep was *meant*
    to demonstrate (not just "the output exists").
The goal is to prevent silent regressions in the analysis pipeline as
the model evolves; these are NOT a substitute for the proposition
tests in `test_proofs.py`.

A smoke test here is `xfail` only when the sweep itself is correctly
diagnosing a known feature of the model -- e.g., G2's claim that x*
drifts upward with p_c (a feature of the unpriced-backlog asymmetry).
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from analysis import sweep_g1, sweep_g2, sweep_g3, sweep_g4, sweep_g5


ANALYSIS_DIR = Path(__file__).resolve().parent.parent / "analysis"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _assert_artifacts(stem: str, expect_csv_rows: int) -> None:
    csv_path = ANALYSIS_DIR / f"sensitivity_{stem}.csv"
    pdf_path = ANALYSIS_DIR / "figures" / f"sensitivity_{stem}.pdf"
    md_path = ANALYSIS_DIR / f"sensitivity_{stem}_findings.md"
    assert csv_path.exists(), f"missing CSV: {csv_path}"
    rows = _read_csv(csv_path)
    assert len(rows) == expect_csv_rows, (
        f"{csv_path.name}: expected {expect_csv_rows} rows, got {len(rows)}"
    )
    assert pdf_path.exists() and pdf_path.stat().st_size > 0, (
        f"missing or empty PDF: {pdf_path}"
    )
    assert md_path.exists() and md_path.stat().st_size > 0, (
        f"missing or empty findings note: {md_path}"
    )


# ---------------------------------------------------------------------------
# G1: 30 points x 3 policies = 90 rows.
# ---------------------------------------------------------------------------
def test_sweep_g1_artifacts() -> None:
    sweep_g1.run()
    sweep_g1.write_findings()
    _assert_artifacts("g1", expect_csv_rows=90)


def test_sweep_g1_three_policies_present() -> None:
    rows = _read_csv(ANALYSIS_DIR / "sensitivity_g1.csv")
    policies = {r["policy"] for r in rows}
    assert policies == {"tax", "cap_and_trade", "strict_cap"}


def test_sweep_g1_costs_finite() -> None:
    rows = _read_csv(ANALYSIS_DIR / "sensitivity_g1.csv")
    for r in rows:
        cost = float(r["cost"])
        assert cost == cost, "NaN cost in G1"  # NaN check
        assert abs(cost) < 1.0e6, f"runaway cost in G1: {r}"


# ---------------------------------------------------------------------------
# G2: 30 points x 3 carbon-price levels = 90 rows.
# Structural claim: at fixed s, x* increases monotonically with p_c.
# ---------------------------------------------------------------------------
def test_sweep_g2_artifacts() -> None:
    sweep_g2.run()
    sweep_g2.write_findings()
    _assert_artifacts("g2", expect_csv_rows=90)


def test_sweep_g2_x_star_drifts_up_with_p_c() -> None:
    rows = _read_csv(ANALYSIS_DIR / "sensitivity_g2.csv")
    # Pick one s value and verify x* increases with p_c.
    s_anchor = sorted({float(r["s"]) for r in rows})[5]  # arbitrary mid s
    triplet = sorted(
        (r for r in rows if abs(float(r["s"]) - s_anchor) < 1.0e-9),
        key=lambda r: float(r["p_c"]),
    )
    xs = [float(r["x_star"]) for r in triplet]
    assert xs[0] < xs[1] < xs[2], (
        f"x* should rise monotonically with p_c at s={s_anchor}; got {xs}"
    )


# ---------------------------------------------------------------------------
# G3: 25 x 25 = 625 rows.
# Structural claim: G* = 0 wherever p_c * a < 1 (Proposition P3 corner).
# ---------------------------------------------------------------------------
def test_sweep_g3_artifacts() -> None:
    sweep_g3.run()
    sweep_g3.write_findings()
    _assert_artifacts("g3", expect_csv_rows=625)


def test_sweep_g3_corner_below_hyperbola() -> None:
    rows = _read_csv(ANALYSIS_DIR / "sensitivity_g3.csv")
    for r in rows:
        p_c = float(r["p_c"])
        a = float(r["a"])
        G_star = float(r["G_star"])
        if p_c * a < 1.0 - 1.0e-6:
            assert G_star <= 1.0e-6, (
                f"P3 corner violated at p_c={p_c}, a={a}: G*={G_star}"
            )


# ---------------------------------------------------------------------------
# G4: two CSVs, 90 rows each.
# Structural claim: in sweep B (vary C_cap), tax cost is *invariant* in
# C_cap (tax has no cap term). Verifies the regime separation.
# ---------------------------------------------------------------------------
def test_sweep_g4_artifacts() -> None:
    sweep_g4.run()
    sweep_g4.write_findings()
    by_pc = ANALYSIS_DIR / "sensitivity_g4_by_pc.csv"
    by_ccap = ANALYSIS_DIR / "sensitivity_g4_by_ccap.csv"
    assert by_pc.exists() and len(_read_csv(by_pc)) == 90
    assert by_ccap.exists() and len(_read_csv(by_ccap)) == 90
    pdf = ANALYSIS_DIR / "figures" / "sensitivity_g4.pdf"
    assert pdf.exists() and pdf.stat().st_size > 0


def test_sweep_g4_tax_invariant_in_ccap() -> None:
    rows = _read_csv(ANALYSIS_DIR / "sensitivity_g4_by_ccap.csv")
    tax_costs = [float(r["cost"]) for r in rows if r["policy"] == "tax"]
    spread = max(tax_costs) - min(tax_costs)
    assert spread < 1.0e-9, f"tax cost should be invariant in C_cap; spread={spread}"


# ---------------------------------------------------------------------------
# G5: 30 x 2 = 60 rows.
# Structural claim: cap-and-trade G* hits the corner (G*=0) at large D_1,
# while strict-cap G* stays strictly positive across the swept range
# (the cap is binding so investment is forced).
# ---------------------------------------------------------------------------
def test_sweep_g5_artifacts() -> None:
    sweep_g5.run()
    sweep_g5.write_findings()
    _assert_artifacts("g5", expect_csv_rows=60)


def test_sweep_g5_cap_trade_corner_vs_strict_cap() -> None:
    rows = _read_csv(ANALYSIS_DIR / "sensitivity_g5.csv")
    # cap-trade G* should reach exactly zero somewhere in the sweep.
    cap_G = [float(r["G_star"]) for r in rows if r["regime"] == "cap_and_trade"]
    assert min(cap_G) <= 1.0e-6, f"cap-trade G* never reaches corner: min={min(cap_G)}"
    # strict-cap G* should never be zero (cap binds in this configuration).
    st_G = [float(r["G_star"]) for r in rows if r["regime"] == "strict_cap"]
    assert min(st_G) > 1.0e-3, f"strict-cap G* hit zero: min={min(st_G)}"


# ---------------------------------------------------------------------------
# G6 deferral: just check the explanatory note exists and references the
# gap. This documents the scope decision in the test suite.
# ---------------------------------------------------------------------------
def test_g6_deferred_note_exists() -> None:
    md = (ANALYSIS_DIR / "sensitivity_g6_deferred.md").read_text(encoding="utf-8")
    assert "G6" in md and "DEFERRED" in md.upper()
