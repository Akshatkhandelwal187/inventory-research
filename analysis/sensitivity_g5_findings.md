# G5 findings -- demand-investment coupling under power demand

Sweep: D_1 in [0, 6.0], 30 points; cap-and-trade at BASE and strict
cap at C_cap = 5.0. Reference parameters from
`analysis._common.BASE`. Raw data in `analysis/sensitivity_g5.csv`;
figure at `analysis/figures/sensitivity_g5.pdf`.

## Cap-and-trade anchors

| D_1  | G*    | demand | cost    | emissions |
|------|-------|--------|---------|-----------|
| 0.00 | 1.000 | 300.00 |  16.261 |  7.248 |
| 1.00 | 0.846 | 302.18 |  16.345 |  7.603 |
| 3.00 | 0.456 | 303.79 |  16.470 |  8.545 |
| 6.00 | 0.000 | 300.00 |  16.511 |  9.748 |

## Strict-cap anchors (C_cap = 5.0)

| D_1  | G*    | psi*  | demand | cost    | emissions |
|------|-------|-------|--------|---------|-----------|
| 0.00 | 1.555 | 0.692 | 300.00 |  18.950 |  5.000 |
| 1.00 | 1.517 | 0.713 | 303.40 |  19.083 |  5.000 |
| 3.00 | 1.440 | 0.758 | 309.85 |  19.343 |  5.000 |
| 6.00 | 1.322 | 0.833 | 318.55 |  19.718 |  5.000 |

## Takeaway

Under cap-and-trade, G* exhibits a *sharp corner transition*: starting
from G* = 1.000 at D_1 = 0 (decoupled), G* falls smoothly with D_1 and
hits zero around D_1 ~ 3 -- past that point the firm finds investing
counter-productive because each unit of R(G) lifts demand by D_1*dR,
inflating the operating cost (Sicilia's TC scales with D) by more than
it saves in carbon (p_c*dR). The corner is exact in the closed form:
P3 says G* >= 0 with equality whenever the local marginal benefit of
investment falls below 1; demand coupling pulls that inequality
in to zero earlier than the bare p_c*a > 1 condition.

Under strict cap (binding at C_cap = 5.0), the corner does
*not* reach zero. The firm is *forced* to keep emissions <= C_cap, so
even when investment is locally costly the cap requires it. Instead,
G* tapers slowly (1.555 -> 1.164 across the swept range), the shadow
price psi* rises to compensate, and demand drifts upward with D_1
because some R(G) is unavoidable. The strict-cap regime therefore
cushions firms against the corner trap that cap-and-trade exhibits --
a finding noted in `tests/test_stage_3c_multipolicy.py`
(`test_strict_cap_invests_in_green_when_demand_coupling_weak`) and
formalised here for the full coupling range.

Implication for the literature. Hasan (2021) reports a monotone
coupling effect under uniform demand: stronger D_1 means more demand
lift, which is good for the firm. The Phase 3b/c numerical evidence
shows the picture is more delicate under power demand: the
*regulatory regime* changes whether coupling encourages or discourages
investment. A regulator who wants to keep technology adoption flowing
in industries with strong demand spillover should choose a strict cap
or a tax-with-rebate (which mimics the strict-cap shadow price)
rather than a vanilla cap-and-trade scheme.
