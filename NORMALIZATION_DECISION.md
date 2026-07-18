# Decision record — normalization (deferred, on purpose)

Owner: B (Jay). Status: **deferred, not changed.** Read with `CONTRACTS.md` §3.

## The issue
Each clip's 5 brain-network curves are min-max normalized to its own 0..1 range
(`networks.reduce_to_networks`). CONTRACTS §3 says "already normalized by B."

We found this **flattens differences between clips**: because every clip is
stretched to fill 0..1, two different videos come out looking similar, and
`peak` saturates near 1.0 for everything. On a known boring-vs-engaging pair it
ranked the pair **backwards**. Since the whole product is comparing variants,
per-clip normalization is a real correctness problem for the winner call.

## What we did instead of changing it
- The **eval/comparison path** (`eval_ab.py`) uses a **shared scale**: all clips
  in a comparison are scored against one batch-wide reference (95th percentile),
  so relative differences survive. This is what got the 3 blind pairs right.
- The **product `score()` path was left on per-clip normalization, unchanged.**

## Why we deferred the product change (the reasoning)
Fixing `score()` properly means scoring a test's variants **together on a shared
scale**, which:
1. Changes the meaning of a single Score Object (it's no longer self-contained —
   its numbers depend on the other variant it's compared against).
2. Contradicts CONTRACTS §3's "already normalized by B" wording → a **contract
   change**, which is shared law and cannot be edited by one lane unilaterally.
3. Changes C's winner logic (C compares stored Score Objects; those would now
   need to be produced in the same shared-scale batch, not independently).

Changing any of that quietly would break C's and A's assumptions mid-build. So
per the "flag major changes before touching shared work" rule, we **documented
it and left it**. The eval proves the fix works; the product adopts it only after
a team decision.

## The proper fix (when the team decides)
- Score all variants of a `test` in one batch, on a shared scale, before writing
  `scores`. Update CONTRACTS §3 to say variants of a test are normalized jointly.
- C: ensure `POST /tests/{id}/score` scores the variant set together, not one at
  a time.
- Add the §10 change-log entry in CONTRACTS first, announce, then change code.

## Current state (so no one is surprised)
- Single-clip scores are fine to render (a clip's own shape is correct).
- **Cross-clip winner from raw per-clip Score Objects is NOT reliable yet** — use
  `eval_ab.py`'s shared-scale path for any A/B comparison until the fix lands.
