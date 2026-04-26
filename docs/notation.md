# Unified notation

Phase 2.5 deliverable. Authoritative symbol table for the project — every
baseline implementation and the novel model must use these symbols, not the
paper-specific ones.

> **Status:** frozen at the close of Phase 2d. Re-open only if Phase 3a
> introduces a symbol the existing baselines do not anticipate.

## Decision variables

| Symbol | Meaning | Units |
|--------|---------|-------|
| Q      | lot size | units |
| T      | cycle length | time (year) |
| G      | green-technology investment per unit time | currency / time |
| B      | maximum backlog (positive scalar; Sicilia's `s = -B`) | units |
| t_p    | production phase length within a cycle | time |
| x      | backlog ratio `B / (D · T)` (Sicilia 2014's `x`) | — |

## Demand & production

| Symbol | Meaning | Units |
|--------|---------|-------|
| D      | demand *rate* (units per unit time) | units / time |
| n      | power-demand exponent (Sicilia 2014); n=1 ⇒ uniform | — |
| P      | finite production rate | units / time |
| α      | production-to-demand ratio `P / D` (Sicilia 2014) | — |
| D_0    | baseline / intercept demand (Hasan 2021) | units / time |
| D_1    | coefficient coupling `R(G)` into demand (Hasan 2021) | (units / time) per unit reduction |
| m      | promotion-sensitivity coefficient (Hasan 2021) | (units / time) per unit promotion |
| v      | promotion level (Hasan 2021) | — |
| a      | green-tech efficiency factor in `R(G) = a G − b G²` | 1 / currency |
| b      | green-tech emission factor in `R(G) = a G − b G²` | 1 / currency² |

The Hasan demand law is `D(G, v) = D_0 + D_1 · R(G) + m · v`. When `D_1 = m = 0`,
this collapses to a constant `D_0`, recovering the demand assumption used by
Hua 2011, Benjaafar 2013, and the C=0 limit of Sicilia 2014.

## Cost parameters

| Symbol | Meaning | Units |
|--------|---------|-------|
| K      | fixed setup / ordering cost | currency / order |
| h      | holding cost rate | currency / unit / time |
| s      | shortage / backlog cost rate | currency / unit / time |
| c      | unit purchase / production cost | currency / unit |
| p      | unit selling price | currency / unit |

## Carbon parameters

| Symbol | Meaning | Units |
|--------|---------|-------|
| e_K    | emissions per setup / per order | kg CO₂e / order |
| e_h    | emissions per unit held per unit time | kg CO₂e / unit / time |
| e_c    | emissions per unit purchased / produced | kg CO₂e / unit |
| e_s    | emissions per backlogged unit per unit time (gap **G2**) | kg CO₂e / unit / time |
| e_d    | emissions per unit-distance shipped (Hasan transport) | kg CO₂e / km / shipment |
| C_cap  | emissions cap (cap-and-trade or strict cap) | kg CO₂e / time |
| p_c    | carbon price (tax rate or trading price) | currency / kg CO₂e |

The transport emission factor `e_d` is folded into `e_K` (per-setup emissions)
once the delivery distance `d` is fixed: `e_K_total = e_K + e_d · d`.

## Cross-reference: paper-specific → unified

| Hua 2011 | Benjaafar 2013 | Hasan 2021       | Sicilia 2014 | Unified | Notes |
|----------|----------------|------------------|--------------|---------|-------|
| K        | K              | OC               | A            | K       | Setup / ordering cost |
| D        | d              | D₀ + D₁·R + m·v  | r            | D       | Demand rate (Hasan: derived from G, v) |
| h        | h              | C_h              | h            | h       | Holding cost rate |
| —        | —              | —                | w            | s       | Backlog cost rate |
| —        | c              | C_p (= C₀ + C_T) | —            | c       | Unit purchase cost |
| —        | —              | p                | —            | p       | Unit selling price |
| e        | e              | —                | —            | e_K     | Emissions per setup |
| g        | h_e            | E_h              | —            | e_h     | Emissions per unit-time held |
| e₀       | ν              | —                | —            | e_c     | Emissions per unit purchased |
| —        | —              | —                | —            | e_s     | Backlog emissions rate (**novel**, gap G2) |
| —        | —              | E_T              | —            | e_d     | Transport emissions per unit-distance |
| a        | cap            | U / W            | —            | C_cap   | Emissions cap |
| C        | α              | C₁ / C₂ / ψ      | —            | p_c     | Carbon price |
| —        | —              | a, b             | —            | a, b    | Green-tech reduction R(G) = a G − b G² |
| —        | —              | D₀, D₁           | —            | D₀, D₁  | Demand intercept; green coupling |
| —        | —              | m, v             | —            | m, v    | Promotion sensitivity / level |
| —        | —              | —                | n            | n       | Power-demand exponent |
| —        | —              | —                | α            | α       | Production-to-demand ratio P / D |
| Q        | Q              | Q                | Q            | Q       | Lot size (decision) |
| —        | —              | —                | s, x         | B, x    | Max backlog and backlog ratio (decision) |
| —        | —              | G                | —            | G       | Green-tech investment (decision) |
| X (transfer) | —          | —                | —            | —       | Hua's signed credit transfer; derived as `C_cap − emissions(Q)`. Not a decision. |
| ψ (Lemma 3) | —            | ψ (input)        | —            | p_c     | Hasan's strict-cap multiplier is supplied as an input shadow price (E_paper(Q*,G*) ≠ W), so it plays the role of `p_c`. |

## Implementation notes

- Function signatures throughout `src/baselines/` and `src/novel/` use the
  paper-specific symbols *of the paper they reproduce* (e.g. Hua's
  `solve_hua_2011_cap_and_trade(K, D, h, e, g, C, a)` keeps Hua's letters)
  so cross-checking against the source paper is mechanical. The unified
  symbols above are the API for the novel model and for any
  multi-baseline comparison tooling built in Phase 3.
- Phase 3a (power demand + cap-and-trade) introduces no new symbols — it
  composes Sicilia's `(K, h, s, D, n, α)` with Hua's `(e_K, e_h, p_c, C_cap)`.
- Phase 3b layers Hasan's green-tech block `(G, R(G), a, b, D₀, D₁, m, v)`
  on top.
- Phase 3c brings in the multi-policy comparison; tax / cap-and-trade /
  strict-cap solvers all share the same `(p_c, C_cap)` API surface, with
  the regime selected by enum or by which arguments are non-default.
