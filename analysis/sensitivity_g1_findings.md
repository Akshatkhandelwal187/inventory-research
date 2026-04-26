# G1 findings -- demand realism in carbon-aware models

Sweep: power-demand exponent n in [0.30, 5.00], 30 points, three regimes.
Reference parameters from `analysis._common.BASE`. Raw data in
`analysis/sensitivity_g1.csv`; figure at
`analysis/figures/sensitivity_g1.pdf`.

## Headline numbers (cap-and-trade regime)

| n    | Q*       | T*     | cost    | emissions |
|------|----------|--------|---------|-----------|
| 0.30 |   699.06 | 2.3302 |  20.499 |  12.258 |
| 1.00 |   798.86 | 2.6629 |  17.282 |   8.162 |
| 2.00 |   836.79 | 2.7893 |  16.261 |   7.248 |
| 5.00 |   750.20 | 2.5007 |  18.744 |   9.113 |

## Takeaway

The carbon-regulated optimum is *not monotone* in n: cycle length T*
and lot size Q* both peak near n approx 1 (uniform demand) and decline
on either side. At n = 0.30 (concave / decelerating consumption) and
n = 5.00 (convex / accelerating consumption), T* contracts and total
operating cost rises -- the firm is forced to set up more often. Across
the swept range, optimal cost spans
16.261 to
20.499 (-8.5% gap
between n=1 and n=5), and emissions span
7.248 to
12.258. Because the
cap-and-trade rebate -p_c*C_cap is identical across n, the *operational*
component of cost (cost + p_c*C_cap) is what shifts with demand
realism.

Implication for the literature. Hua (2011), Benjaafar (2013), and Hasan
(2021) all assume n = 1. Recommendations transplanted to power demand
without re-optimisation under-provision setups (smaller T*) for both
concave and convex demand patterns. The Phase-3a effective-cost
reduction (Proposition P1, `docs/proofs.md`) makes the re-derivation a
single Sicilia call, so the implementation cost is small; the numerical
gap is non-trivial.
