# G3 findings -- joint optimisation of Q, T, G

Sweep: 25 x 25 grid over (p_c, a) with p_c in [0, 5], a in [0.1, 5].
Reference parameters from `analysis._common.BASE`. Raw data in
`analysis/sensitivity_g3.csv`; figure at
`analysis/figures/sensitivity_g3.pdf` (left panel: G* heat-map with
the closed-form boundary p_c*a = 1 overlaid; right panel: share of
total carbon footprint covered by green-tech reduction).

## Anchor points

| regime     | p_c  | a    | p_c*a | G*    | R(G*) | cost    |
|------------|------|------|-------|-------|-------|---------|
| corner     | 0.20 | 1.00 |  0.20 | 0.000 | 0.000 |  15.883 |
| threshold  | 1.00 | 1.00 |  1.00 | 0.000 | 0.000 |  15.658 |
| interior   | 1.00 | 3.00 |  3.00 | 2.000 | 4.000 |  13.658 |
| aggressive | 3.00 | 4.00 | 12.00 | 3.667 | 7.944 | -12.965 |

## Takeaway

The sweep reproduces Proposition P3's corner-vs-interior dichotomy
exactly: G* = 0 throughout the half-plane p_c*a <= 1 (closed form
yields max(0, (a-1/p_c)/(2b)) = 0 there), and G* > 0 above the
hyperbola. The white dashed curve in the left panel traces p_c*a = 1
on the heat-map; the corner / interior boundary aligns with that
analytic curve to within the 25 x 25 grid resolution.

Two practical implications:
  * Carbon-price thresholds matter for technology adoption. A
    not-very-effective green technology (a < 1/p_c) rationally stays
    unused even under positive carbon pricing. Subsidy design has to
    push *either* p_c *or* a above the hyperbola.
  * The joint optimum is decomposable but not separable. Operational
    decisions (Q*, T*) move with G* through D(G) when D_1 > 0, but at
    BASE D_1 = 0 the inner Phase-3a problem is solved once at D_0; G*
    is then a univariate add-on. Proposition P2 makes that decomposition
    rigorous.

The right panel shows the share of total emissions footprint covered
by R(G*). It saturates at 1.0 in the upper-right corner of the plane
(net emissions can go negative, which the share metric clamps via
its own definition). Real-world calibration would cap a or add a
ceiling on R(G), but the structural regime map is otherwise faithful.
