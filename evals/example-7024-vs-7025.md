# Eval example — known pair 7024 (boring) vs 7025 (engaging)

Reference example of a Reeled In A/B scoring run. Use this to see what the
pipeline produces and how to read it. Owner: B (scoring).

## The test
- Two real self-recorded clips. **Known answer:** `IMG_7024` = boring,
  `IMG_7025` = engaging (labelled by the recorder for validation).
- Goal: does the model rank the engaging clip higher, and which brain system
  drives the difference.
- Run: `python3 -m modal run backend/modal_app.py::eval_folder --names "IMG_7024,IMG_7025"`

## Result: CORRECT (on the shared scale)
Decision rule (pre-committed): winner = higher `overall`.

| metric (shared scale) | 7024 boring | 7025 engaging | winner |
|---|---|---|---|
| overall | 0.8387 | **0.8645** | 7025 ✓ |
| sustained | 0.6773 | **0.7290** | 7025 |
| peak | 1.0 | 1.0 | tie (saturated) |
| retention | 1.0 | 1.0 | tie (saturated) |

The model picked the engaging clip. `sustained` (average engagement over the
clip) is what separated them; `peak` and `retention` both saturated at 1.0 and
added no signal on this pair.

### Normalization matters
The same pair under the old **per-clip** normalization ranks 7024 (boring)
higher — WRONG. Per-clip min-max stretches every clip to its own 0..1 range and
flattens cross-clip differences. The **shared-scale** normalization (compare all
clips against one batch-wide reference) is what gets it right. This is why the
product must score variants of a test on a shared scale, not independently.

## Per-system breakdown — why 7025 won
Mean shared-normalized activation per brain system (higher = more response):

| brain system | 7024 boring | 7025 engaging | delta (eng − bor) |
|---|---|---|---|
| **auditory** | 0.5615 | 0.7023 | **+0.1408** |
| **language** | 0.6909 | 0.7890 | **+0.0981** |
| **motion** | 0.5939 | 0.6815 | **+0.0876** |
| visual | 0.5731 | 0.5511 | −0.0220 |
| default_mode | 0.6060 | 0.6033 | −0.0027 |

**Read:** the engaging clip won through the **hearing, spoken-language, and
motion** systems — more vocal energy / speech and more on-screen movement drove
more predicted brain response. The **sight** and **meaning** systems were
essentially flat between the two.

## What the model actually ingested
- **Video frames** → sight + motion systems (movement, color, faces, scene).
- **Audio track** → hearing system (voice, music, tone).
- **Spoken words** (auto speech-to-text from the audio) → language system.
  On-screen text is NOT read (only seen as pixels).

The model predicts brain response; it does not directly score color/vibrance or
"good writing." The 5 systems are read out from predicted activity in the
matching brain regions (Destrieux atlas mapping on fsaverage5).

## Caveats
- One pair, thin overall margin (0.026). Directionally right, not proof.
- `peak`/`retention` saturating suggests those formulas may need tuning against
  more hand-labelled pairs (change weights in `CONTRACTS.md` §3 first, then
  `scoring/metrics.py`).
- Scores are a directional engagement proxy, not ground truth (per
  `HOW_TRIBE_V2_WORKS.md`).
