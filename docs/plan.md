# Living plan

Tracks the active research plan. Phase status mirrors `CLAUDE.md` —
update both when a phase flips. Use this file for finer-grained
sub-tasks, blockers, and decisions; use `CLAUDE.md` for the public
phase summary.

## Current focus

Phase 2d — recreate Hasan, Roy, Daryanto & Wee (2021) green-tech investment baseline.

## Open decisions

- Notation freeze: defer until two baselines are implemented (see docs/notation.md).
- Numerical solver default: `scipy.optimize.minimize_scalar` for univariate,
  `brentq` for FOC roots. Reconsider if Phase 3b joint optimisation in (Q, T, G)
  forces a multivariate solver.

## Blockers

(none yet)

## Decision log

- 2026-04-26 — Repo scaffolded. Five reference papers in `papers/`.
  Phase 1 literature review marked complete in CLAUDE.md.
- 2026-04-26 — Phase 2a complete. `solve_sicilia_2014` validated against
  Examples 1-2 and eight Table 1/2 rows in `tests/test_sicilia_2014.py`
  (33 tests, all passing). Cross-check: at n=1 the model reduces to
  Naddor's classical EPQ-with-backorders, also verified.
- 2026-04-26 — Sicilia (2014) Example 1 has a typographical/arithmetic
  error in its printed minimum cost (paper says C*=274.06 $/year, but
  Eq. (21) at the published (x*, T*, s*) yields ~299.07, consistent
  with the FOC identity C*=2·A/T* and with every other validated case).
  We pin our value at the formula-correct ~299.07; see
  `test_example_1_cost_paper_typo`.
- 2026-04-26 — Phase 2b complete. `solve_hua_2011_cap_and_trade`
  reproduces all 7 rows of Hua et al. (2011) Table 1 to within
  ±1 unit (paper rounds to nearest integer); 38 tests passing.
  Theorem-1 trichotomy and Theorem-2 sign properties verified across
  every row. Row 1 has a printed-Q typo in the paper (8453 vs the
  formula-correct 8485 that matches the same row's a0 column);
  documented in the test file.
- 2026-04-26 — Phase 2c complete. Benjaafar et al. (2013) does not
  publish a Hua-style numerical table — its reported results are 15
  qualitative figures from a 15-period MILP whose per-figure
  parameters are not all printed. We therefore implement the paper's
  analytical companion (Appendix II-B, Theorem A.1): three closed-form
  EOQ-style policies (`solve_benjaafar_2013_strict_cap`, `_tax`,
  `_offset`). Validation (25 tests) covers all three Theorem-A.1
  regimes (cap not binding / binding / infeasible), the K/h vs e/h_e
  trichotomy that picks Q1 vs Q2, the equivalence of the tax solver
  with Hua 2011 cap-and-trade at a=0, and the cap-and-offset
  three-regime structure. The multi-period MILP (P1-P7) is deferred;
  its discrete formulation does not yield clean unit-tests against
  printed numbers, and Phase 3c will be built on the analytical EOQ
  layer instead.
