# Optimality proofs for the novel model

Phase 4 deliverable. Formalises four structural results derived in passing
during Phase 3 (a/b/c) into stand-alone propositions with proofs:

  P1. *Effective-cost reduction.* Phase 3a (power demand + cap-and-trade) is
      a Sicilia (2014) problem at modified setup and holding costs.
  P2. *Green-tech separability.* Phase 3b's joint problem in (Q, T, B, G)
      separates into a Phase-3a sub-problem at demand `D(G)` plus a
      univariate term `G − p_c R(G)`.
  P3. *Closed-form G\*.* When demand is decoupled from green-tech
      (`D_1 = 0`), the optimal investment is
      `G* = max(0, (a − 1/p_c) / (2b))`, with interior solution iff
      `p_c · a > 1`.
  P4. *KKT shadow-price recovery.* The strict cap is the Lagrangian dual of
      Phase 3b; its multiplier `ψ` plays the role of `p_c`, and is
      recovered as the unique root of `E(ψ) − C_cap = 0` whenever the cap
      is binding and feasible.

Each proposition is followed by a *numerical verification protocol* — the
tests in `tests/test_proofs.py` exercise the claim across parameter grids.

Notation matches `docs/notation.md`.

---

## P1. Effective-cost reduction (Phase 3a)

**Setting.** Power demand pattern with rate `D`, exponent `n > 0`, finite
production rate `P = α D` (`α > 1`); holding rate `h`, backlog rate `s`,
setup `K`. Carbon cap-and-trade: emissions per setup `e_K`, per
unit-time-held `e_h`, carbon price `p_c ≥ 0`, allowance `C_cap ≥ 0`.

Decision variables `(Q, T, B)` with `Q = D · T` and backlog ratio
`x = B / (D T) ∈ [0, (α−1)/α]`. Let

```
I_h(x, T) = average inventory per unit time
I_b(x, T) = average backlog per unit time
```

both linear in `T` for fixed `x`, with closed forms in
`src/baselines/sicilia_2014.py`.

The Phase-3a per-time total cost is

```
TC_3a(Q, T, B; p_c, C_cap)
    = h · I_h + s · I_b + K / T                                    (operating)
      + p_c · ( e_K / T + e_h · I_h − C_cap ).                     (carbon)
```

The Sicilia (2014) per-time total cost at parameters `(A, h̃)` is

```
TC_sic(Q, T, B; A, h̃) = h̃ · I_h + s · I_b + A / T.
```

**Proposition P1.** Define the *effective costs*

```
A_eff := K + p_c · e_K,        h_eff := h + p_c · e_h.
```

Then for every feasible `(Q, T, B)`:

```
TC_3a(Q, T, B; p_c, C_cap) = TC_sic(Q, T, B; A_eff, h_eff) − p_c · C_cap.   (P1.1)
```

Consequently:

```
arg min TC_3a(·; p_c, C_cap) = arg min TC_sic(·; A_eff, h_eff)              (P1.2)
        Q,T,B                                  Q,T,B
```

and at the optimum, using Sicilia's identity `TC*_sic = 2 A / T*`,

```
TC*_3a(p_c, C_cap) = 2 · A_eff / T*(A_eff, h_eff) − p_c · C_cap.           (P1.3)
```

**Proof.**

Algebraic identity (P1.1): expand both sides.

```
RHS = (h + p_c e_h) · I_h + s · I_b + (K + p_c e_K) / T − p_c · C_cap
    = h · I_h + s · I_b + K / T  +  p_c · ( e_h · I_h + e_K / T )
       − p_c · C_cap
    = LHS.                                                    ☐
```

Argmin coincidence (P1.2): subtract the constant `−p_c · C_cap` (it does
not depend on `(Q, T, B)`); strictly decreasing, monotonic transformation
preserves the argmin set.

Optimal cost (P1.3): Sicilia's first-order condition for `T*` reads
(`/baselines/sicilia_2014.py:_denominator`)

```
T*² · D · denom(x*; n, α, h̃) = A,
```

so `A / T* = D · denom · T*` and `2 A / T*` equals exactly the holding +
backlog + setup terms at the optimum. Apply with `(A, h̃) = (A_eff, h_eff)`
and add the constant `−p_c · C_cap`.                                    ☐

**Reductions.**

- `p_c = 0`:  `A_eff = K`, `h_eff = h`, recovering pure Sicilia (2014).
- `n = 1, α → ∞, B = 0`: power demand collapses to uniform demand;
  Sicilia's EPQ-with-backorders reduces to the classical EOQ at
  `(A, h) = (A_eff, h_eff)`, recovering Hua (2011) Theorem 1.

**Implication for emissions sensitivity.** From (P1.2), the Phase-3a
optimal emissions are

```
E*_3a(p_c) = e_K / T*(A_eff, h_eff) + e_h · I_h(x*(h_eff/s), T*(A_eff, h_eff)).
```

This is a function of `p_c` *through* the Sicilia optimum at the
effective costs. We do not claim global monotonicity of `E*_3a` in `p_c`
when backlogs are active (Sicilia's `x*` depends on `h_eff/s` and shifts
non-trivially as `p_c` rises — documented as a Phase-5 sensitivity item).
Monotonicity of *expected* emissions is recovered in the EOQ limit (Hua's
Theorem 2). The KKT proof (P4) does not require global monotonicity in
`p_c`; only continuity and feasibility at `ψ_upper`.

**Numerical verification.**
`tests/test_proofs.py::TestP1`:

- (P1.1) Identity test: random sample of `(Q, T, B; p_c, C_cap)` with
  feasibility check; assert equality to `1e-12` relative tolerance.
- (P1.2) Argmin test: solve Phase 3a directly and Sicilia at
  `(A_eff, h_eff)`; assert `Q*, T*, B*` match to `1e-12`.
- (P1.3) Optimal-cost identity: assert
  `TC*_3a + p_c · C_cap == 2 A_eff / T*` to `1e-12`.

---

## P2. Green-tech separability (Phase 3b)

**Setting.** Phase 3a augmented with green-technology investment rate
`G ≥ 0` (currency / time), reducing emissions by

```
R(G) = a G − b G²,            a, b > 0,
```

and (optionally) coupling demand via

```
D(G) = D_0 + D_1 · R(G) + m · v,            D_0 > 0, D_1, m, v ≥ 0.
```

Per-time cost is

```
TC_3b(Q, T, B, G; p_c, C_cap)
    = h · I_h(D(G)) + s · I_b(D(G)) + K / T                        (operating)
      + p_c · ( e_K / T + e_h · I_h(D(G)) − R(G) − C_cap )          (carbon)
      + G,                                                          (investment)
```

where the dependence on demand is made explicit (`I_h, I_b` scale with
`D(G) · T` through the Sicilia profile; see
`stage_3a_power_captrade._bracket_h`).

**Proposition P2.** For every fixed `G ≥ 0`,

```
TC_3b(Q, T, B, G; p_c, C_cap)
    = TC_3a(Q, T, B; D(G), p_c, 0)
      + G − p_c · R(G)
      − p_c · C_cap.                                                (P2.1)
```

Since `G − p_c R(G) − p_c C_cap` is independent of `(Q, T, B)`, for fixed
`G`,

```
arg min TC_3b(·, G; p_c, C_cap) = arg min TC_3a(·; D(G), p_c, 0).    (P2.2)
       Q,T,B                              Q,T,B
```

The full optimum is therefore the univariate search

```
G* ∈ arg min_{G ∈ [0, a/(2b)]}  [ TC*_3a(D(G); p_c, 0) + G − p_c · R(G) ].  (P2.3)
```

**Proof.**

Identity (P2.1): rearrange `TC_3b`,

```
TC_3b = h I_h + s I_b + K/T  +  p_c (e_K/T + e_h I_h)        ←  TC_3a(·; p_c, 0)
        + G                                                  ←  investment
        − p_c R(G)                                           ←  reduction
        − p_c C_cap.                                         ←  cap rebate
```

The first line is `TC_3a(·; D(G), p_c, 0)` (`I_h, I_b` evaluated at the
G-dependent demand `D(G)`). The remaining three lines depend only on
`G`.                                                                    ☐

Argmin separation (P2.2): the additive `G`-only term shifts the objective
by a constant in `(Q, T, B)`; argmin invariant under additive constants.

Univariate reduction (P2.3): plug the inner argmin (Phase 3a optimum) back
in, giving a function of `G` alone.

**Bounding `G*`.** `R(G) = aG − bG²` is symmetric about `a/(2b)` with
maximum `R(a/(2b)) = a²/(4b)`. For `G > a/(2b)`, both the operating term
(when `D_1 > 0`, demand drops below its peak `D(a/(2b))`) and the
investment term `G` rise while `R(G)` falls. So `G* ∈ [0, a/(2b)]`.

Specifically: for any `G > a/(2b)`, define `G' = a/b − G < a/(2b)`. Then
`R(G') = R(G)` (symmetry) and `G' < G`, so `G' − p_c R(G') < G − p_c R(G)`
strictly. Also `D(G') = D(G)` so the Phase-3a inner cost is identical.
Hence `G' < G` strictly dominates, and the search bracket can be capped
at `a/(2b)` without loss of optimality.                                ☐

**Numerical verification.**
`tests/test_proofs.py::TestP2`:

- (P2.1) Identity at random `(Q, T, B, G)`: build LHS and RHS from
  primitives; equality to `1e-12`.
- (P2.2) Inner-argmin coincidence: for several `G` values, compare
  `solve_power_demand_cap_and_trade(D=D(G))` with the
  `(Q*, T*, B*)` returned by the Phase 3b solver after pinning `G`.
- Bracket dominance: solve Phase 3b explicitly on
  `[0, a/(2b)]`; verify that for any `G > a/(2b)` the symmetric reflection
  `G' = a/b − G` strictly dominates.

---

## P3. Closed-form G\* under decoupled demand (`D_1 = 0`)

**Setting.** Phase 3b with `D_1 = 0`. Then `D(G) = D_0 + m v` is a constant
in `G`; write `D̄ := D_0 + m v`. The inner Phase-3a cost
`TC*_3a(D̄; p_c, 0)` does not depend on `G`. (P2.3) reduces to

```
G* ∈ arg min_{G ∈ [0, a/(2b)]}  φ(G),       φ(G) := G − p_c · R(G).   (P3.0)
```

**Proposition P3.** Let `p_c ≥ 0`, `a, b > 0`. Then

```
                ⎧  0,                       if  p_c · a ≤ 1,
       G* =     ⎨                                                       (P3.1)
                ⎩  (a − 1/p_c) / (2b),       if  p_c · a > 1,
```

with the understanding that `p_c = 0 ⇒ G* = 0`. Moreover the solution is
unique whenever `p_c > 0`.

**Proof.**

Case `p_c = 0`: `φ(G) = G`, strictly increasing on `[0, a/(2b)]`; minimum
at `G = 0`.                                                              ☐

Case `p_c > 0`:

```
φ'(G)  = 1 − p_c · (a − 2 b G) = 1 − p_c · a + 2 p_c · b · G,
φ''(G) = 2 p_c · b > 0.
```

`φ` is strictly convex, so the unconstrained FOC `φ'(G) = 0` gives the
unique unconstrained minimiser

```
Ĝ = (p_c · a − 1) / (2 p_c · b) = (a − 1/p_c) / (2 b).
```

- If `Ĝ ≤ 0`, equivalently `p_c · a ≤ 1`, the constrained minimiser on
  `[0, a/(2b)]` is the boundary `G* = 0` (`φ` is increasing right of `0`).
- If `0 < Ĝ < a/(2b)`, equivalently `p_c · a > 1`, the FOC point `Ĝ` is
  interior. To check: `Ĝ < a/(2b)` ⇔ `a − 1/p_c < a` ⇔ `1/p_c > 0`, which
  always holds. So `Ĝ ∈ (0, a/(2b))` is feasible and is the constrained
  minimiser by strict convexity.
- The boundary `Ĝ = 0` corresponds to `p_c · a = 1`; then both formulas
  in (P3.1) agree (`G* = 0`), so the formula is well-defined at the
  threshold.                                                            ☐

**Asymptotics.** As `p_c → ∞`, `G* → a/(2b) = arg max R`, and
`R(G*) → a²/(4b)`. The marginal cost of investment becomes negligible
relative to the marginal carbon saving, so the firm pushes investment to
the unconstrained-`R` optimum.

**Comparative statics.** From (P3.1), at `p_c · a > 1`:

```
∂G*/∂p_c = 1 / (2 b p_c²) > 0,    ∂G*/∂a = 1 / (2 b)  > 0,
∂G*/∂b  = −(a − 1/p_c) / (2 b²) < 0.
```

So `G*` is strictly increasing in carbon price, increasing in efficiency
factor `a`, and decreasing in curvature factor `b`.

**Numerical verification.**
`tests/test_proofs.py::TestP3`:

- (P3.1) Closed-form: parameter grid; compare solver `G_star` with
  formula; tolerance `1e-9`.
- FOC: `|φ'(G*)|` ≤ `1e-9` at interior solutions.
- SOC: `φ''(G*) = 2 p_c b > 0` (sanity).
- Comparative-statics signs verified by finite differences.
- Asymptotics: at `p_c = 1e6`, `G* ≈ a/(2b)` and `R(G*) ≈ a²/(4b)` to
  `1e-6`.

---

## P4. KKT shadow-price recovery (strict cap)

**Setting.** The strict-cap problem solved in
`stage_3c_multipolicy.solve_strict_cap`:

```
(SC):    min   c_op(Q, T, B, G)
       Q,T,B,G
         s.t.  e(Q, T, B, G)  ≤  C_cap,
               (Q, T, B, G) ∈ Ω,
```

where

```
c_op(Q, T, B, G) = h · I_h + s · I_b + K / T + G            (operating + investment)
e(Q, T, B, G)    = e_K / T + e_h · I_h − R(G)               (net per-time emissions)
```

and `Ω` is the feasible set (`Q = D(G) T > 0`, `0 ≤ x ≤ (α−1)/α`,
`G ∈ [0, a/(2b)]`). Both `c_op` and `e` are continuous on `Ω`.

The Lagrangian is

```
L(Q, T, B, G; ψ) = c_op + ψ · ( e − C_cap )
                  = c_op + ψ · e  − ψ · C_cap.
```

Crucially, `c_op + ψ · e = TC_3b(·; p_c = ψ, C_cap = 0)`, so

```
L(Q, T, B, G; ψ) = TC_3b(Q, T, B, G; ψ, C_cap).                       (P4.0)
```

(The `−ψ · C_cap` is the same constant in both expressions.)

**Proposition P4.** Define the dual value function

```
V(ψ) :=  inf  L(Q, T, B, G; ψ)
        Ω
       =  inf  TC_3b(·; ψ, C_cap),
        Ω

E(ψ) :=  e(Q*(ψ), T*(ψ), B*(ψ), G*(ψ)),
```

where `(Q*(ψ), T*(ψ), B*(ψ), G*(ψ))` is the (Phase 3b) minimiser at
`p_c = ψ`. Then:

(a) `V` is concave in `ψ`.
(b) (Envelope) `dV/dψ = E(ψ) − C_cap`, a.e. in `ψ`.
(c) (Monotonicity) `E(ψ)` is non-increasing in `ψ`.
(d) (Existence) If `V'(0) = E(0) − C_cap ≤ 0`, the cap is not binding at
    `ψ = 0`; (SC) is solved by the Phase 3b minimiser at `ψ = 0` with
    multiplier `ψ* = 0`. Otherwise, if `lim_{ψ → ∞} E(ψ) < C_cap`, there
    exists `ψ* > 0` with `E(ψ*) = C_cap` (binding cap, `ψ*` recovered by
    Bolzano on `E(ψ) − C_cap`).
(e) (Lagrangian equivalence) At a binding optimum, the strict-cap and
    cap-and-trade decisions at `p_c = ψ*` coincide; their reported costs
    coincide as well, since the carbon trade term `p_c · (e − C_cap)`
    vanishes at `e = C_cap`.

**Proof.**

(a) Concavity. `L(·; ψ)` is affine in `ψ` for fixed primal variables.
Pointwise infimum of a family of affine functions is concave. So
`V(ψ) = inf_Ω L(·; ψ)` is concave.                                      ☐

(b) Envelope. `V(ψ) = c_op* + ψ · (e* − C_cap)` at the minimiser.
By Danskin / envelope theorem (applicable when the inner argmin set is a
singleton at the differentiability point — true wherever the Phase 3b
problem has a unique minimiser, which holds outside of measure-zero
boundary transitions),

```
V'(ψ) = (∂L/∂ψ)|_{(Q*, T*, B*, G*)}  =  e(Q*, T*, B*, G*) − C_cap
      = E(ψ) − C_cap.
```

Even at non-differentiable points `V` admits sub-/super-gradients in
`[E(ψ⁺) − C_cap, E(ψ⁻) − C_cap]` (concavity of `V` plus monotonicity in
(c) below).                                                              ☐

(c) Monotonicity. `V` is concave in `ψ` (part a), so `V'` is non-increasing
in `ψ`, i.e. `E(ψ) − C_cap` is non-increasing, i.e. `E(ψ)` is
non-increasing. (Strict decrease holds wherever the Phase 3b minimiser
shifts non-trivially with `ψ`.)                                          ☐

(d) Existence by Bolzano. Define `f(ψ) = E(ψ) − C_cap`, continuous in `ψ`
because the Phase 3b problem has a continuous value function and (under
uniqueness) a continuous minimiser — formally: the Phase 3b objective is
continuous in `(Q, T, B, G, ψ)` and the feasible set is compact in `Ω`
restricted to a precompact box, so by Berge's maximum theorem `E(ψ)` is
continuous. Two cases:

  Case 1 (`f(0) ≤ 0`): `E(0) ≤ C_cap`, the unconstrained-by-cap Phase 3b
  optimum at `ψ = 0` is already feasible; complementary slackness
  satisfied with `ψ* = 0`.

  Case 2 (`f(0) > 0`, `f(ψ_upper) ≤ 0`): by Bolzano `f(ψ*) = 0` for some
  `ψ* ∈ (0, ψ_upper]`. Monotonicity (c) makes the root unique whenever
  `E(·)` is strictly decreasing in a neighbourhood of `ψ*`.

  Case 3 (`f(ψ_upper) > 0`): cap infeasible at this upper bracket. The
  solver raises `ValueError` (`stage_3c_multipolicy.solve_strict_cap`,
  line 238).                                                            ☐

(e) Lagrangian equivalence. At binding `ψ*`, the Phase 3b argmin at
`p_c = ψ*` minimises `L(·; ψ*)` and is feasible for (SC) (since
`E(ψ*) = C_cap`). Strong duality holds (convex objective in `(Q, T)` for
fixed `(B, G, x)`; LICQ-style constraint qualification at the binding
cap), so it solves (SC).

The cap-and-trade *cost* at the same `(Q*, T*, B*, G*)` is

```
TC_cap_trade = c_op + ψ* · (e* − C_cap) = c_op + 0 = c_op,
```

which is precisely the strict-cap reported cost (operating + investment,
no carbon market). Hence the two costs coincide.                        ☐

**Recovery algorithm.** The implementation in
`solve_strict_cap` (`stage_3c_multipolicy.py:153`) executes:

```
1. Compute (Q*, T*, B*, G*) at ψ = 0  (no carbon cost; closed-form G* = 0).
2. If e(·) ≤ C_cap + tol:    return; cap not binding; ψ* = 0.
3. Verify e(·) at ψ_upper:   if > C_cap, raise ValueError (infeasible).
4. brentq on f(ψ) := E(ψ) − C_cap over [0, ψ_upper]:  ψ*.
5. Recompute (Q*, T*, B*, G*) at ψ*; return reported cost = c_op (no
   carbon market).
```

This is the constructive proof of (d) — Phase 4's contribution is
verifying that the abstract Lagrangian framework produces the *same*
`ψ*` as the engineering bracketing scheme, and that complementary
slackness binds exactly.

**Numerical verification.**
`tests/test_proofs.py::TestP4`:

- (a) Concavity: for a grid `ψ_i` and weights `λ_j`, check
  `V(λ ψ_1 + (1−λ) ψ_2) ≥ λ V(ψ_1) + (1−λ) V(ψ_2)`.
- (b) Envelope: finite-difference `V'(ψ)` matches `E(ψ) − C_cap` to
  `1e-5`.
- (c) Monotonicity: `E(ψ)` non-increasing on a 30-point grid in
  `ψ ∈ [0, 50]`.
- (d) Bolzano root: solve strict cap; assert `|E(ψ*) − C_cap| ≤ 1e-7` and
  `ψ* ≥ 0`. Infeasibility test: very tight cap at small `ψ_upper` raises
  `ValueError`.
- (e) Lagrangian equivalence: solve strict cap, then cap-and-trade at
  `p_c = ψ*`; decisions and costs coincide to `1e-7`. Complementary
  slackness: `ψ* · (e − C_cap) ≤ 1e-12`.

---

## Summary table

| Prop. | Claim | Numerical bound |
|-------|------------------------------------------------------|------|
| P1.1  | TC_3a = TC_sic + const                               | 1e-12 |
| P1.2  | argmin TC_3a = argmin TC_sic at (A_eff, h_eff)       | 1e-12 |
| P1.3  | TC*_3a + p_c C_cap = 2 A_eff / T*                    | 1e-12 |
| P2.1  | TC_3b = TC_3a(D(G)) + G − p_c R(G) − p_c C_cap       | 1e-12 |
| P2.2  | inner (Q*, T*, B*) at fixed G = Phase 3a at D(G)     | 1e-9  |
| P3.1  | G* = max(0, (a − 1/p_c)/(2b))                        | 1e-9  |
| P4(a) | V concave in ψ                                       | (qual.)|
| P4(b) | dV/dψ = E(ψ) − C_cap                                 | 1e-5  |
| P4(c) | E(ψ) non-increasing                                  | (qual.)|
| P4(d) | E(ψ*) = C_cap when binding                           | 1e-7  |
| P4(e) | strict-cap = cap-and-trade at p_c = ψ*               | 1e-7  |

All claims are verified by `pytest tests/test_proofs.py`.
