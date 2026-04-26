# Living plan

Tracks the active research plan. Phase status mirrors `CLAUDE.md` —
update both when a phase flips. Use this file for finer-grained
sub-tasks, blockers, and decisions; use `CLAUDE.md` for the public
phase summary.

## Current focus

Phase 3b — extend the novel model with Hasan-style green-tech investment
G on top of the Phase 3a power-demand cap-and-trade backbone.

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
- 2026-04-26 — Phase 2.5 complete. docs/notation.md frozen with the
  unified symbol table and a paper-by-paper cross-reference. Carbon
  variables: e_K (per setup), e_h (per unit-time held), e_c (per unit
  produced), e_s (per backlogged unit-time, gap G2, novel), e_d
  (transport), C_cap (cap), p_c (price). Decision variables: Q, T, G,
  B (= -Sicilia's s), x, t_p.
- 2026-04-26 — Phase 3a complete. `solve_power_demand_cap_and_trade`
  combines Sicilia (2014) and Hua (2011) via the clean reduction
      A_eff = K + p_c * e_K,   h_eff = h + p_c * e_h
  so the optimum (Q*, T*, B*) is *exactly* Sicilia's optimum at the
  effective costs and TC*_novel = 2 A_eff / T* - p_c * C_cap. The
  closed form proves Hua's Theorem 1 lifts to power demand. 28 tests
  passing: p_c=0 reproduces every Sicilia case to 1e-12; the EOQ
  limit (n=1, alpha=1e9, s=1e10) reproduces all 7 Hua Table-1 rows;
  optimal-cost identity holds; transfer = C_cap - emissions; Q*
  monotone in p_c in the EOQ limit. Notable observation: with
  backlogs (s finite), Q*(p_c) is *not* monotone in p_c -- Sicilia's
  Eq. (28) FOC for x* depends on h_eff so the optimal backlog ratio
  shifts with carbon price too. Documented for Phase 5 sensitivity
  work; no current-phase blocker.
- 2026-04-26 — Phase 2d complete. `solve_hasan_2021_tax`,
  `_cap_and_trade`, `_strict_cap` reproduce all three Table 3 cases
  (Q*, G*, E*, TP* within +/-0.5/0.01/0.5/1.0 of the paper) plus the
  cost-parameter sensitivity tables (Tables 5/10/11/12/13). Closed
  forms in Lemmas 1-3 contain sign errors so the implementation
  optimises TP_i(Q,G) numerically with scipy Nelder-Mead under the
  Q = D(G) T identity. Three model observations: (i) all three Table-3
  cases give R(G*) = a^2/(4b) = 12.50 exactly, i.e., G* sits at the
  unconstrained argmax of the carbon-reduction function; (ii) the
  paper's strict-cap case (Eq. 19) is structurally identical to
  cap-and-trade with (psi, W) replacing (C_2, U) — psi=5 is supplied
  as an input rather than recovered as a Lagrange multiplier, and
  E*=56.21 != W=10 confirms the cap is not enforced; (iii) Table 8
  (efficiency factor a) and Table 9 (factor b) do NOT match any
  consistent re-optimisation of the documented model — likely a
  separate LINGO worksheet bug — so we validate qualitative
  monotonicity only for those tables.  51 tests passing; full suite
  147 across all four baselines.
