# Unified notation

Phase 2.5 deliverable. Authoritative symbol table for the project — every
baseline implementation and the novel model must use these symbols, not the
paper-specific ones.

> **Status:** stub. To be filled in during Phase 2.5 once at least two
> baselines are implemented and the symbol clashes are visible.

## Decision variables

| Symbol | Meaning | Units |
|--------|---------|-------|
| Q      | lot size | units |
| T      | cycle length | time |
| G      | green-tech investment | currency |
| B      | maximum backlog | units |

## Demand & production

| Symbol | Meaning | Units |
|--------|---------|-------|
| D      | demand rate (or demand-pattern total) | units / time |
| n      | power-demand exponent (Sicilia 2014) | — |
| P      | finite production rate | units / time |

## Cost parameters

| Symbol | Meaning | Units |
|--------|---------|-------|
| K      | fixed setup / ordering cost | currency / order |
| h      | holding cost rate | currency / unit / time |
| s      | shortage / backlog cost rate | currency / unit / time |
| c      | unit purchase / production cost | currency / unit |

## Carbon parameters

| Symbol | Meaning | Units |
|--------|---------|-------|
| e_K    | emissions per setup | kg CO2e / order |
| e_h    | emissions per unit held per unit time | kg CO2e / unit / time |
| e_c    | emissions per unit produced | kg CO2e / unit |
| e_s    | emissions per backlogged unit per unit time (gap G2) | kg CO2e / unit / time |
| C_cap  | emissions cap (cap-and-trade or strict cap) | kg CO2e / period |
| p_c    | carbon price (tax rate or trading price) | currency / kg CO2e |

## Cross-reference: paper-specific → unified

| Hua 2011 | Benjaafar 2013 | Hasan 2021 | Sicilia 2014 | Unified |
|----------|----------------|------------|--------------|---------|
| TBD      | TBD            | TBD        | TBD          | TBD     |
