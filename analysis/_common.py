"""Shared utilities for the Phase 5 sensitivity sweeps.

Keeps a single reference parameter point (`BASE`) so figures across gaps
are comparable. Provides minimal CSV / matplotlib helpers using only the
project's documented stack (numpy, scipy, matplotlib; pandas not added).

The reference point is consistent with `tests/test_proofs.py` and
`tests/test_stage_3c_multipolicy.py`: a moderately-loaded firm with
balanced holding/backlog economics, non-zero per-setup and per-held
emission factors, and an interior green-tech investment when carbon is
priced.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

# Force a non-interactive backend before pyplot is imported. Sweeps run
# headless (CI / batch); the default Tk backend has a Windows-install
# bug on this machine that corrupts figure creation.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


BASE: dict[str, float] = {
    "D0": 300.0,
    "n": 2.0,
    "alpha": 1.5,
    "h": 0.05,
    "s": 0.10,
    "K": 20.0,
    "e_K": 20.0,
    "e_h": 1.0,
    "a": 3.0,
    "b": 0.5,
    "p_c": 0.5,
    "C_cap": 10.0,
}
# At BASE: A_eff = 30, h_eff = 0.55, p_c*a = 1.5 > 1 (interior G*),
# G_max = a/(2b) = 3.0; the closed-form yields G* = (a-1/p_c)/(2b) = 1.0
# with R(G*) = 2.5, demand = 300, T* ~ 2.79, Q* ~ 837, gross emissions
# ~ 9.7, net emissions ~ 7.2 (so the cap C_cap=10 is *just* loose --
# strict cap is non-binding at BASE; tighter caps in the G4 sweep make
# the strict-cap shadow price visible).


ROOT = Path(__file__).resolve().parent
FIGURES_DIR = ROOT / "figures"


def figure_style() -> None:
    """Project-wide matplotlib style for publication figures.

    Serif fonts, vector PDF, no chart junk. Called once at the top of
    every sweep script.
    """
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "legend.frameon": False,
        "lines.linewidth": 1.6,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[dict],
) -> int:
    """Write rows to CSV using stdlib csv (no pandas dependency).

    Returns the number of data rows written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            n += 1
    return n


def figure_path(stem: str) -> Path:
    """Resolve a PDF figure path under analysis/figures/."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR / f"{stem}.pdf"
