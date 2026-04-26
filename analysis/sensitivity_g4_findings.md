# G4 findings -- regulatory comparison under non-stationary demand

Two independent sweeps, three regimes. Reference parameters from
`analysis._common.BASE`. Raw data in
`analysis/sensitivity_g4_by_pc.csv` (sweep A: vary p_c, C_cap fixed)
and `analysis/sensitivity_g4_by_ccap.csv` (sweep B: vary C_cap, p_c
fixed). Figure at `analysis/figures/sensitivity_g4.pdf`.

## Anchor: BASE point (p_c = 0.5, C_cap = 10.0)

| regime         | cost    | emissions | extra              |
|----------------|---------|-----------|--------------------|
| tax            |  21.261 |   7.248  | carbon paid = 3.624 |
| cap-and-trade  |  16.261 |   7.248  | transfer = 2.752 |
| strict cap     |  16.438 |  10.000  | psi* = 0.3838, binding = True |

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
0.384), where Proposition P4's Lagrangian
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
