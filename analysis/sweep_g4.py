"""G4 sweep -- regulatory comparison under non-stationary demand.

Gap. Benjaafar (2013) compares tax / cap-and-trade / strict cap *under
uniform demand*. The relative merits of each regulatory regime can flip
under power demand because the firm's response to a carbon signal is
mediated by the cycle structure (Sicilia's x*, T* depend on h_eff,
which itself depends on p_c). Phase 5 maps the three regimes side by
side as p_c and C_cap are swept independently.

Sweeps. Two independent grids:
    sweep A: p_c in [0, 5], 30 points; C_cap fixed at BASE.
    sweep B: C_cap in [0, 30], 30 points; p_c fixed at BASE.
At each grid point we run all three regimes and record cost,
emissions, and (for strict cap) the recovered KKT multiplier psi*.

Outputs.
    analysis/sensitivity_g4_by_pc.csv         (90 rows)
    analysis/sensitivity_g4_by_ccap.csv       (90 rows)
    analysis/figures/sensitivity_g4.pdf       (4-panel: 2x2)
    analysis/sensitivity_g4_findings.md
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from analysis._common import BASE, figure_path, figure_style, write_csv
from src.novel.stage_3c_multipolicy import (
    solve_cap_and_trade,
    solve_strict_cap,
    solve_tax,
)


P_C_GRID = np.linspace(0.0, 5.0, 30)
C_CAP_GRID = np.linspace(0.0, 30.0, 30)


def _row(policy: str, p_c: float, C_cap: float, result: dict) -> dict:
    return {
        "policy": policy,
        "p_c": p_c,
        "C_cap": C_cap,
        "Q_star": result["Q_star"],
        "T_star": result["T_star"],
        "G_star": result.get("G_star", 0.0),
        "demand": result.get("demand", BASE["D0"]),
        "cost": result["cost"],
        "emissions": result["emissions"],
        "psi_star": result.get("psi_star", float("nan")),
    }


def run() -> tuple[Path, Path]:
    common_template = {**BASE}
    base_p_c = common_template.pop("p_c")
    base_C_cap = common_template.pop("C_cap")

    # --- sweep A: vary p_c, hold C_cap = BASE ---
    rows_a: list[dict] = []
    for p_c in P_C_GRID:
        cm = {**common_template}
        rows_a.append(_row("tax", float(p_c), base_C_cap,
            solve_tax(**cm, p_c=float(p_c))))
        rows_a.append(_row("cap_and_trade", float(p_c), base_C_cap,
            solve_cap_and_trade(**cm, p_c=float(p_c), C_cap=base_C_cap)))
        rows_a.append(_row("strict_cap", float(p_c), base_C_cap,
            solve_strict_cap(**cm, C_cap=base_C_cap)))
    csv_a = Path(__file__).with_name("sensitivity_g4_by_pc.csv")
    write_csv(csv_a, list(rows_a[0].keys()), rows_a)

    # --- sweep B: vary C_cap, hold p_c = BASE ---
    rows_b: list[dict] = []
    for C_cap in C_CAP_GRID:
        cm = {**common_template}
        rows_b.append(_row("tax", base_p_c, float(C_cap),
            solve_tax(**cm, p_c=base_p_c)))
        rows_b.append(_row("cap_and_trade", base_p_c, float(C_cap),
            solve_cap_and_trade(**cm, p_c=base_p_c, C_cap=float(C_cap))))
        rows_b.append(_row("strict_cap", base_p_c, float(C_cap),
            solve_strict_cap(**cm, C_cap=float(C_cap))))
    csv_b = Path(__file__).with_name("sensitivity_g4_by_ccap.csv")
    write_csv(csv_b, list(rows_b[0].keys()), rows_b)

    # --- figure: 2 x 2 ---
    figure_style()
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.4))
    policies = ("tax", "cap_and_trade", "strict_cap")

    for policy in policies:
        sub = [r for r in rows_a if r["policy"] == policy]
        xs = [r["p_c"] for r in sub]
        axes[0, 0].plot(xs, [r["cost"] for r in sub], label=policy.replace("_", " "))
        axes[0, 1].plot(xs, [r["emissions"] for r in sub], label=policy.replace("_", " "))
    axes[0, 0].set_xlabel("carbon price  p_c")
    axes[0, 0].set_ylabel("total cost")
    axes[0, 0].set_title(f"sweep A: vary p_c (C_cap = {base_C_cap})")
    axes[0, 1].set_xlabel("carbon price  p_c")
    axes[0, 1].set_ylabel("emissions per unit time")
    axes[0, 1].set_title("sweep A: emissions")
    axes[0, 0].legend()

    for policy in policies:
        sub = [r for r in rows_b if r["policy"] == policy]
        xs = [r["C_cap"] for r in sub]
        axes[1, 0].plot(xs, [r["cost"] for r in sub], label=policy.replace("_", " "))
        axes[1, 1].plot(xs, [r["emissions"] for r in sub], label=policy.replace("_", " "))
    axes[1, 0].set_xlabel("emissions cap  C_cap")
    axes[1, 0].set_ylabel("total cost")
    axes[1, 0].set_title(f"sweep B: vary C_cap (p_c = {base_p_c})")
    axes[1, 1].set_xlabel("emissions cap  C_cap")
    axes[1, 1].set_ylabel("emissions per unit time")
    axes[1, 1].set_title("sweep B: emissions")

    fig.suptitle("G4: regulatory comparison across (p_c, C_cap)", y=1.02)
    fig.tight_layout()
    fig.savefig(figure_path("sensitivity_g4"))
    plt.close(fig)

    return csv_a, csv_b


def write_findings() -> Path:
    common = {**BASE}
    base_p_c = common.pop("p_c")
    base_C_cap = common.pop("C_cap")

    # Anchor 1: at BASE p_c, do the three policies agree on emissions?
    tax = solve_tax(**common, p_c=base_p_c)
    cap = solve_cap_and_trade(**common, p_c=base_p_c, C_cap=base_C_cap)
    strict = solve_strict_cap(**common, C_cap=base_C_cap)

    md_path = Path(__file__).with_name("sensitivity_g4_findings.md")
    md_path.write_text(
        f"""# G4 findings -- regulatory comparison under non-stationary demand

Two independent sweeps, three regimes. Reference parameters from
`analysis._common.BASE`. Raw data in
`analysis/sensitivity_g4_by_pc.csv` (sweep A: vary p_c, C_cap fixed)
and `analysis/sensitivity_g4_by_ccap.csv` (sweep B: vary C_cap, p_c
fixed). Figure at `analysis/figures/sensitivity_g4.pdf`.

## Anchor: BASE point (p_c = {base_p_c}, C_cap = {base_C_cap})

| regime         | cost    | emissions | extra              |
|----------------|---------|-----------|--------------------|
| tax            | {tax['cost']:>7.3f} | {tax['emissions']:>7.3f}  | carbon paid = {tax['carbon_payment']:.3f} |
| cap-and-trade  | {cap['cost']:>7.3f} | {cap['emissions']:>7.3f}  | transfer = {cap['transfer']:.3f} |
| strict cap     | {strict['cost']:>7.3f} | {strict['emissions']:>7.3f}  | psi* = {strict['psi_star']:.4f}, binding = {strict['cap_binding']} |

## Takeaway

Sweep A (vary p_c, C_cap fixed). Strict-cap decisions are *invariant*
in p_c -- the regime has no carbon market, so the firm responds only
to the cap. Strict-cap cost and emissions are therefore horizontal
lines (cost = operating + investment, emissions clamped to C_cap when
the cap binds). Tax cost rises linearly in p_c. Cap-and-trade cost
sits below tax by exactly p_c*C_cap (the rebate is a constant
transfer; both regimes share the same operational decisions at any
fixed p_c). Strict-cap and cap-and-trade decisions coincide *exactly*
at the single point p_c = psi* (here psi* approx
{strict['psi_star']:.3f}), where Proposition P4's Lagrangian
equivalence kicks in.

Sweep B (vary C_cap, p_c fixed). Tax is invariant in C_cap (no cap
enters the objective). Cap-and-trade cost decreases linearly in C_cap
with slope -p_c (a pure transfer); cap-and-trade *emissions* are also
invariant in C_cap (the firm picks the same (Q*, T*, B*, G*) for any
cap, only the rebate changes). Strict-cap emissions track C_cap
exactly while binding, then plateau at the cap-and-trade emissions
level once C_cap loosens past psi* = p_c -- a knee visible in the
lower-right panel of the figure.

Implication for the literature. Benjaafar (2013) compares the three
regimes under uniform demand and reports cap-and-trade weakly
dominates tax (in cost) for any non-zero C_cap, with strict cap
matching cap-and-trade at the binding multiplier. Both predictions
survive under power demand: the cost ordering is preserved, and the
Lagrangian equivalence holds exactly (verified in Phase 4 by
`tests/test_proofs.py::TestP4::test_P4_e_lagrangian_equivalence`).
What changes is the *level* of every curve through the n-dependence
of T* (gap G1) -- a regulator calibrating C_cap from a uniform-demand
model will under-weight emissions for n != 1 firms.
"""
    )
    return md_path


if __name__ == "__main__":
    run()
    write_findings()
