# Living plan

Tracks the active research plan. Phase status mirrors `CLAUDE.md` —
update both when a phase flips. Use this file for finer-grained
sub-tasks, blockers, and decisions; use `CLAUDE.md` for the public
phase summary.

## Current focus

Phase 2a — recreate Sicilia (2014) power-demand baseline.

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
