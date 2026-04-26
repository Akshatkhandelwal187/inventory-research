# G2 findings -- emissions cost of backlogged shortages

Sweep: backlog-cost rate s in [0.02, 1.00], 30 points, at three carbon
prices p_c in {0, 0.5, 2.0}; cap-and-trade regime. Reference
parameters from `analysis._common.BASE`. Raw data in
`analysis/sensitivity_g2.csv`; figure at
`analysis/figures/sensitivity_g2.pdf`.

## Backlog-ratio drift at s = 0.10

| p_c | h_eff | x*       | emissions | operating cost |
|-----|-------|----------|-----------|-----------------|
| 0.0 | 0.050 | 0.1381 | 76.963 | 11.604 |
| 0.5 | 0.550 | 0.2937 | 7.248 | 17.637 |
| 2.0 | 2.050 | 0.3216 | 1.268 | 23.224 |

## Takeaway

x* rises from 0.1381 (p_c = 0) to
0.3216 (p_c = 2) -- a
+132.9% increase --
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
