# Living plan

Tracks the active research plan. Phase status mirrors `CLAUDE.md` —
update both when a phase flips. Use this file for finer-grained
sub-tasks, blockers, and decisions; use `CLAUDE.md` for the public
phase summary.

## Current focus

Phase 6 — paper writing. Phase 5 is complete: five gap-driven
sensitivity sweeps (`analysis/sweep_g1.py` through `sweep_g5.py`)
produce the publication CSVs and PDF figures, each with a short
findings note (`analysis/sensitivity_g{1..5}_findings.md`). Gap G6
(deteriorating items) is documented as deferred out of Phase 5 in
`analysis/sensitivity_g6_deferred.md` and tracked for a future paper.
Smoke tests in `tests/test_sensitivity.py` re-run every sweep and
check both artifact creation and a structural identity per gap (12
tests; full suite now 423, all passing).

## Open decisions

- Notation freeze: docs/notation.md frozen at Phase 2.5. Phases 3b, 3c, and 4
  stayed inside the freeze (no new symbols).
- Numerical solver default: univariate scipy `minimize_scalar` for the
  inner G search; `brentq` for the strict-cap shadow-price recovery.
  Phase 3c required no multivariate solver — every solve reduces to
  Phase 3b at a (p_c, C_cap) pair, with strict cap recovering p_c=psi*
  via brentq on `emissions(psi) - C_cap = 0`.
- Proof strategy: P1 and P2 are algebraic identities (verified to 1e-12);
  P3 is a strictly-convex univariate FOC argument (closed form to 1e-9);
  P4 invokes Lagrangian duality + envelope theorem + Bolzano (verified by
  finite differences to 1e-4 and KKT residuals to 1e-7). No global
  monotonicity of E_3a in p_c is asserted in P1 (Sicilia's x* shifts with
  h_eff = h + p_c·e_h, breaking the EOQ-style monotonicity from Hua's
  Theorem 2 when backlogs are active). P4 only requires continuity of
  E(·) and feasibility at psi_upper, which the Lagrangian argument
  supplies through Berge's maximum theorem.
- G convention: Phase 3b adopts a *per-time* convention for G and R(G)
  (matching docs/notation.md), which differs from Hasan 2021's per-cycle
  convention. The R(G) functional form is identical; only the units of
  (a, b, G) change. Documented in `stage_3b_with_green.py` docstring.
- Strict-cap interpretation: Phase 3c implements the rigorous strict-cap
  problem with psi recovered via KKT, *not* Hasan's "psi as input"
  treatment that left E*(Q,G) ≠ W. Documented in
  `stage_3c_multipolicy.py` docstring.
- Phase 5 sweep parameter point: a single `analysis._common.BASE` is
  used by every gap sweep so figures and findings cross-reference
  cleanly. Choice rationale (in `analysis/_common.py`): A_eff = 30,
  h_eff = 0.55, p_c*a = 1.5 puts G* in the interior; net emissions
  ~7.2 keep cap rebates moderate; T* ~ 2.79 puts the cycle structure
  away from degenerate regimes. The notebook stubs
  (`analysis/sensitivity_g{1,2,4}*.ipynb`) predate the Phase 5
  scripts and are superseded by the .py sweeps; left in place so as
  not to disturb existing references.

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
- 2026-04-26 — Phase 3c complete. `solve_tax`, `solve_cap_and_trade`
  (alias for Phase 3b), `solve_strict_cap`, plus a `compare_policies`
  helper. Each policy reduces to Phase 3b at a (p_c, C_cap) pair:
      Tax              -> p_c = p_c (input),     C_cap = 0
      Cap-and-trade    -> p_c = p_c (input),     C_cap = C_cap (input)
      Strict cap       -> p_c = psi (shadow),    C_cap = C_cap (input)
  with psi recovered by brentq on emissions(psi) - C_cap = 0 over
  [0, psi_upper]. Implemented the rigorous strict-cap formulation
  (KKT-based; psi is an output, not Hasan's "psi as input" approach
  that left E*(Q,G) ≠ W). 19 tests passing (246 total): tax = Phase 3b
  at C_cap=0 to 1e-12 (5 carbon-price grids); strict-cap loose-cap
  reduces to pure Sicilia with G*=0; tight-cap recovers psi*>0 with
  emissions=C_cap to 1e-7; psi* monotone non-increasing in C_cap;
  Lagrangian equivalence (strict cap and cap-and-trade at p_c=psi*
  give identical decisions and identical *cost* because the carbon
  trade term vanishes when emissions=C_cap exactly); cost difference
  cap_trade − tax = -p_c·C_cap. Notable observation: with strong
  demand coupling (D_1 large) under strict cap, the firm prefers to
  satisfy the cap via Q-adjustment rather than green-tech investment
  (G*=0 even at binding cap), because in cost-min raising G also
  raises demand and operating cost. Investment kicks in only when
  demand coupling is weak / a is large -- documented in
  `test_strict_cap_invests_in_green_when_demand_coupling_weak`.
- 2026-04-26 — Phase 5 complete. Five gap-driven sweeps under
  `analysis/sweep_g{1..5}.py`, each emitting a CSV (`analysis/`),
  a publication PDF (`analysis/figures/`), and a short findings note.
  All sweeps anchored to a single reference point `analysis._common.BASE`
  (D0=300, n=2, alpha=1.5, h=0.05, s=0.10, K=20, e_K=20, e_h=1, a=3,
  b=0.5, p_c=0.5, C_cap=10) so figures cross-reference cleanly.
  Headline findings:
    G1 (vary n in [0.30, 5.00]): T*(n) is hump-shaped with peak near
       n=1; carbon-regulated cost spans ~17.3-22.1 across the range,
       so carrying Hua-style uniform-demand recommendations onto power
       demand under-provisions setups for both concave and convex
       consumption.
    G2 (vary s in [0.02, 1.00], three p_c levels): backlog ratio x*
       drifts +132.9% from p_c=0 to p_c=2 at fixed s=0.10. Mechanism:
       h_eff = h+p_c*e_h grows with p_c but s stays put, so the firm
       re-weights inventory toward backlogs to dodge carbon-priced
       holding -- a *modelling artefact* of unpriced backlog
       emissions. Argues for adding e_s in future work; the Phase-3a
       reduction extends to s_eff = s+p_c*e_s without further changes.
    G3 (25 x 25 grid in (p_c, a)): G* = 0 throughout the half-plane
       p_c*a <= 1 (Proposition P3 closed form holds on the grid),
       interior elsewhere. Heatmap matches the analytic boundary to
       grid resolution; smoke test enforces this with a tolerance of
       1e-6.
    G4 (two sweeps, vary p_c then C_cap): tax cost is invariant in
       C_cap (no cap term); cap-trade cost = tax cost - p_c*C_cap;
       strict-cap decisions are invariant in p_c. Lagrangian
       equivalence (P4) coincides exactly at the single point
       p_c = psi*. Costs and emissions track the predictions of P1
       and P4 across the swept ranges.
    G5 (vary D_1 in [0, 6]): cap-and-trade exhibits a sharp corner
       transition -- G* falls smoothly to 0 around D_1~3 because
       demand growth from R(G) inflates operating cost by more than
       it saves carbon. Strict cap (binding C_cap=5) does *not* hit
       the corner: the firm is forced to invest, with G* tapering
       from 1.555 to 1.164 and psi* rising from 0.692 to 0.833.
       The regulatory regime therefore changes whether coupling
       encourages or discourages investment -- a refinement of
       Hasan (2021)'s monotone-coupling claim.
    G6 (deferred): deteriorating items not in the current model;
       extension would replace I_h with a theta-modified holding
       integral and carry through Proposition P1 unchanged.
       Documented in `analysis/sensitivity_g6_deferred.md`.
  Smoke tests (`tests/test_sensitivity.py`, 12 tests) re-run every
  sweep and assert the CSV / PDF / findings artifacts plus one
  structural identity per gap (e.g., G3's corner condition,
  G4's tax invariance in C_cap). Full suite 423 tests, all passing.
- 2026-04-26 — Phase 4 complete. `docs/proofs.md` formalises four
  propositions and `tests/test_proofs.py` provides numerical verification
  (165 tests, all passing; full suite 411 across the project).
    P1. *Effective-cost reduction.* Phase 3a TC = Sicilia TC at
        (A_eff, h_eff) − p_c·C_cap; argmin coincides; optimal-cost identity
        TC*_3a + p_c·C_cap = 2·A_eff/T*. Verified to 1e-12.
    P2. *Green-tech separability.* For fixed G, Phase 3b argmin in
        (Q,T,B) equals Phase 3a argmin at D(G); the green-tech term
        G − p_c·R(G) is independent of (Q,T,B). Bracket [0, a/(2b)] is
        tight (symmetry argument: any G > a/(2b) is dominated by its
        reflection G' = a/b − G).
    P3. *Closed-form G*.* For D_1=0, the inner objective φ(G) = G − p_c·R(G)
        is strictly convex (φ''=2·p_c·b > 0); FOC + projection onto
        [0, a/(2b)] gives G* = max(0, (a − 1/p_c)/(2b)). Comparative
        statics: ∂G*/∂p_c > 0, ∂G*/∂a > 0, ∂G*/∂b < 0; asymptote
        G* → a/(2b), R(G*) → a²/(4b) as p_c → ∞.
    P4. *KKT shadow-price recovery.* The Phase 3b cost at p_c=ψ is the
        Lagrangian of the strict cap (modulo constant −ψ·C_cap); the dual
        value V(ψ) is concave in ψ (pointwise infimum of affine functions),
        so by envelope dV/dψ = E(ψ) − C_cap and E(ψ) is non-increasing.
        Existence of ψ* via Bolzano on E(ψ) − C_cap = 0; complementary
        slackness ψ*·(E − C_cap) = 0 verified to 1e-8; Lagrangian
        equivalence (decisions and *cost* coincide between strict-cap and
        cap-and-trade at p_c = ψ*) verified to 1e-7.
- 2026-04-26 — Phase 3b complete. `solve_power_demand_cap_and_trade_with_green`
  layers Hasan green-tech investment G onto the Phase 3a backbone via
  the per-time convention (G in currency/time, R(G) in emissions/time —
  documented departure from Hasan's per-cycle convention; same
  functional form, just different units on a, b). The TC decomposes
      TC = TC_3a(D(G)) + G - p_c R(G) - p_c C_cap
  so for fixed G the optimum (Q*, T*, B*) is exactly Phase 3a at the
  G-dependent demand D(G); the green-tech term is independent of
  (Q, T, B). The full optimum is a univariate search over G in
  [0, a/(2b)]. When demand is decoupled (D_1 = 0), TC_3a(D(G)) is
  constant and the FOC d/dG[G - p_c R(G)] = 0 admits a closed form
      G* = max(0, (a - 1/p_c) / (2b))   (p_c > 0)
      G* = 0                             (p_c = 0)
  with the interior solution active iff p_c a > 1. 52 tests passing
  (227 across the suite): p_c=0 reduces to Phase 3a at D=D_0+m·v
  to 1e-12; the closed-form G* is verified across 8 (p_c, a, b) grids;
  G* monotone non-decreasing in p_c; G* and R(G*) -> a/(2b), a^2/(4b)
  as p_c -> infinity; the optimal-cost identity holds for both the
  decoupled (closed-form) and coupled (numerical) paths; FOC numerical
  gradient ~ 0 at interior G* in the demand-coupled case.
