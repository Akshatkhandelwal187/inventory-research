# G6 -- deteriorating items at the carbon/lot-sizing intersection

## Status: DEFERRED out of Phase 5

The current novel model (`src/novel/stage_3a_power_captrade.py`,
`stage_3b_with_green.py`, `stage_3c_multipolicy.py`) does not include a
deterioration term. Sicilia (2014), Hua (2011), Hasan (2021), and
Benjaafar (2013) likewise treat inventory as non-perishable. Adding
deterioration is a structural extension, not a parameter sweep, and
running a "sensitivity sweep" against a deterioration rate that is
not yet a model variable would produce no meaningful numbers.

## What G6 is

From `CLAUDE.md`:

> G6: deteriorating items at the intersection

A deteriorating-items extension would replace the constant inventory
profile assumption with an exponential (or Weibull) decay term,
e.g. `dI/dt = -D(t) - theta*I(t)` for a constant-deterioration
Ghare-Schrader model. The carbon implications are non-trivial: each
deteriorated unit (a) was emitted-to-produce but (b) generates no
revenue and (c) may itself require carbon-priced disposal, so the
cap-and-trade reduction A_eff / h_eff would gain a third effective
cost term (an `s_eff` analogue for deterioration losses).

## Why we are deferring it

1. *Out-of-scope for the current paper.* Phase 5's sensitivity sweeps
   (G1-G5) are tied to existing model variables (n, s, p_c, a, C_cap,
   D_1). G6 requires adding a model variable theta and re-deriving the
   Phase-3a effective-cost reduction. That is a Phase 7+ task.
2. *No baseline to validate against.* Among the five reference papers,
   none combines deterioration with carbon regulation under power
   demand and finite production. We would need a sixth reference
   paper or accept a purely synthetic numerical example -- both of
   which violate the "validation discipline" in `CLAUDE.md`.
3. *Existing structure points the way.* Proposition P1 makes the
   deterioration extension straightforward in principle: a non-zero
   theta yields a modified holding integral I_h(theta), which carries
   into h_eff and the Phase 3a reduction with no further changes. A
   future paper can pick that up.

## What this means for the Phase 5 deliverable

Phase 5 is complete with sensitivity sweeps for G1-G5 (see the
`sweep_g1.py` ... `sweep_g5.py` scripts and accompanying findings
notes). G6 is acknowledged as a known extension and tracked here so
that downstream readers do not interpret its absence as an oversight.
