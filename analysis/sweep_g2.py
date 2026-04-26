"""G2 sweep -- emissions cost of backlogged shortages.

Gap. Hua (2011) and downstream EOQ-with-carbon papers do NOT charge
emissions to backlogged units (Sicilia's `s` covers only the financial
penalty). Backlogs nonetheless carry an emissions footprint in practice
-- expedited shipping, emergency production overtime, cold-chain
disruption. The Phase 3a/b reduction inherits this asymmetry: holding
cost rises to h_eff = h + p_c*e_h under carbon pricing, but backlog
cost stays at s. The optimal backlog ratio x* therefore drifts upward
with p_c -- a *modelling artefact* rather than a genuine
emissions-aware response.

Sweep. Vary the backlog-cost rate s across [0.02, 1.00] (30 points)
and run the cap-and-trade solver at three carbon-price levels
(p_c in {0, 0.5, 2.0}). Record x*, emissions, and operating cost. Two
diagnostics:
    (i) drift of x* with p_c at fixed s (the artefact).
    (ii) the emissions consequence: gross holding emissions e_h * I_h
         drop when x* rises (more inventory in backlog territory), but
         this saving is unpriced in the firm's cost expression beyond
         the cap rebate.

Outputs.
    analysis/sensitivity_g2.csv          -- raw grid (90 rows)
    analysis/figures/sensitivity_g2.pdf  -- 3-panel figure
    analysis/sensitivity_g2_findings.md  -- takeaway
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from analysis._common import BASE, figure_path, figure_style, write_csv
from src.novel.stage_3c_multipolicy import solve_cap_and_trade


S_GRID = np.linspace(0.02, 1.00, 30)
P_C_GRID = (0.0, 0.5, 2.0)


def _row(s: float, p_c: float, result: dict) -> dict:
    return {
        "s": s,
        "p_c": p_c,
        "Q_star": result["Q_star"],
        "T_star": result["T_star"],
        "B_star": result["B_star"],
        "x_star": result["x_star"],
        "G_star": result["G_star"],
        "demand": result["demand"],
        "cost_carbon_free": result["cost_carbon_free"],
        "cost": result["cost"],
        "emissions": result["emissions"],
        "h_eff": result["h_eff"],
    }


def run() -> Path:
    rows: list[dict] = []
    for s in S_GRID:
        for p_c in P_C_GRID:
            common = {**BASE, "s": float(s), "p_c": p_c}
            C_cap = common.pop("C_cap")
            res = solve_cap_and_trade(**common, C_cap=C_cap)
            rows.append(_row(float(s), p_c, res))

    csv_path = Path(__file__).with_name("sensitivity_g2.csv")
    write_csv(csv_path, list(rows[0].keys()), rows)

    figure_style()
    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.2), sharex=True)
    for p_c in P_C_GRID:
        sub = [r for r in rows if r["p_c"] == p_c]
        xs = [r["s"] for r in sub]
        axes[0].plot(xs, [r["x_star"] for r in sub], label=f"p_c = {p_c}")
        axes[1].plot(xs, [r["emissions"] for r in sub], label=f"p_c = {p_c}")
        axes[2].plot(xs, [r["cost_carbon_free"] for r in sub], label=f"p_c = {p_c}")
    axes[0].set_ylabel("backlog ratio  x*")
    axes[1].set_ylabel("emissions per unit time")
    axes[2].set_ylabel("operating + investment cost")
    for ax in axes:
        ax.set_xlabel("backlog-cost rate  s")
    axes[0].legend(title="carbon price")
    fig.suptitle(
        "G2: x* drifts up with p_c when backlog emissions are unpriced",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(figure_path("sensitivity_g2"))
    plt.close(fig)

    return csv_path


def write_findings() -> Path:
    """Quantify the x* drift between p_c = 0 and p_c = 2 at fixed s.

    Compares the optimal backlog ratio at the BASE backlog-cost rate
    s = 0.10 across the three p_c levels.
    """
    common = {**BASE}
    C_cap = common.pop("C_cap")
    common.pop("p_c")
    s = float(BASE["s"])

    res_zero = solve_cap_and_trade(**common, p_c=0.0, C_cap=C_cap)
    res_mod = solve_cap_and_trade(**common, p_c=0.5, C_cap=C_cap)
    res_high = solve_cap_and_trade(**common, p_c=2.0, C_cap=C_cap)

    md_path = Path(__file__).with_name("sensitivity_g2_findings.md")
    md_path.write_text(
        f"""# G2 findings -- emissions cost of backlogged shortages

Sweep: backlog-cost rate s in [0.02, 1.00], 30 points, at three carbon
prices p_c in {{0, 0.5, 2.0}}; cap-and-trade regime. Reference
parameters from `analysis._common.BASE`. Raw data in
`analysis/sensitivity_g2.csv`; figure at
`analysis/figures/sensitivity_g2.pdf`.

## Backlog-ratio drift at s = {s:.2f}

| p_c | h_eff | x*       | emissions | operating cost |
|-----|-------|----------|-----------|-----------------|
| 0.0 | {res_zero['h_eff']:.3f} | {res_zero['x_star']:.4f} | {res_zero['emissions']:.3f} | {res_zero['cost_carbon_free']:.3f} |
| 0.5 | {res_mod['h_eff']:.3f} | {res_mod['x_star']:.4f} | {res_mod['emissions']:.3f} | {res_mod['cost_carbon_free']:.3f} |
| 2.0 | {res_high['h_eff']:.3f} | {res_high['x_star']:.4f} | {res_high['emissions']:.3f} | {res_high['cost_carbon_free']:.3f} |

## Takeaway

x* rises from {res_zero['x_star']:.4f} (p_c = 0) to
{res_high['x_star']:.4f} (p_c = 2) -- a
{(res_high['x_star']/res_zero['x_star'] - 1.0)*100.0:+.1f}% increase --
even though the backlog cost rate s is fixed. The mechanism is the
asymmetric carbon pass-through documented in the Phase-3a notes: as p_c
rises, h_eff = h + p_c*e_h grows but s stays put, so the firm
re-weights its inventory profile toward backlogs to dodge the now-more-
expensive holding term. This is purely a *modelling artefact* of
charging emissions only to held units: a real firm whose backlogs
trigger expedited shipping or overtime emissions would face an
analogous s_eff = s + p_c*e_s, capping the drift.

Implication. The natural extension to close gap G2 is to add a
backlog-emission factor e_s and replace s with s_eff in the Phase-3a
reduction. The full reduction structure (Proposition P1) is preserved:
A_eff = K + p_c*e_K, h_eff = h + p_c*e_h, *and* s_eff = s + p_c*e_s.
The current asymmetry is therefore not a load-bearing assumption but
an opportunity -- adding e_s is a one-line change to the existing
solver. The drift quantified here motivates that extension.
"""
    )
    return md_path


if __name__ == "__main__":
    run()
    write_findings()
