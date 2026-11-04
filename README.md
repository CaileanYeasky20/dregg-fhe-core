# dregg-fhe-core# m31-vmatmul

A small relation, specified in Lean and checked by independent implementations (Python, Rust):

> `C = A·B` over the Mersenne-31 field, and `Y = ReLU(C)`.

Fast code (GPU, Rust, anything) may *build witnesses*. It never defines the claim: the Lean
relation does, and the checkers accept or reject whatever the builder returns.

Provenance: drafted with AI assistance. Nothing here is believed on that basis. Each claim
names its proof, its test, or exactly where it is unfinished.

## Relation (v1)
`p = 2^31 − 1`, `F = Z/pZ`. Inputs `A (m×n)`, `B (n×k)`; claimed `C`, `Y` (both `m×k`). Accept iff:
1. every matrix is non-empty, rectangular, entries in `[0, p)`; shapes agree;
2. for `t = 0..5`: `A(Bβ_t) = Cβ_t`, with `β_t ∈ F^k` derived from `SHA-256(A, B, C)`;
3. `Y = relu(C)` entrywise, `relu(x) = x if x ≤ (p−1)/2 else 0`.

Integers are u32 big-endian; every hash input starts with a domain tag.
`ref/m31ref.py` is normative for bytes.

## Ledger
**Proved in Lean**
- C1 Honest products pass every challenge: `accepts_mul`, `layer_complete`.
- C2 The check is exact on a basis (`C` passes on all unit vectors ⇒ `C = A·B`): `eq_mul_of_accepts_basis`.
- C3 `relu` on `ZMod p` matches its ℕ model, pinned at `0`, `(p−1)/2`, `(p−1)/2+1`, `p−1`: `relu_val`.

**Tested, not proved**
- C4 Python and Rust agree on digests, challenges, verdicts and chain roots for every vector.
- C5 Every single-entry tamper of `C` is rejected, as are non-canonical encodings and shape mismatches.
- C6 No overflow at maximal entries (all `p−1`, inner dimension 1000).

**Argued on paper only (unfinished boundary)**
- C9 If `C ≠ AB` and `β` is uniform, one repetition passes with probability ≤ 1/p.
  Lean statement: `freivalds_bad_fraction` in `M31/Open.lean` (the only `sorry`).
- C10 Fiat–Shamir, random-oracle model: forgery probability ≤ q·p^−T.
