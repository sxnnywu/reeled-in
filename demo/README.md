# Demo data — ready to use, in the repo

Everything A needs to build the results screen and brain flipbook is committed
here. No Modal access needed for the demo.

## What's here
- `precomputed/IMG_7024.json` … `IMG_7029.json` — 6 full Score Objects
  (shared-scale per CONTRACTS §3). Each has: `networks` (5 curves), `engagement`
  (composite curve), `metrics` (peak/sustained/retention/overall),
  `region_timeline` (top brain region per second), `brain_frames`, `duration_sec`.
- `brain_frames/IMG_XXXX_brain_000.png` … — the flipbook images, one per second
  per clip (140 total, ~4.6MB).

## How A uses it
1. Load a scorecard: `demo/precomputed/IMG_7028.json`.
2. Plot `engagement` + the 5 `networks` curves. Show `metrics` and the winner.
3. Flipbook: iterate `brain_frames`. Each entry looks like
   `"media/IMG_7028_brain_000.png"` — the file is at
   `demo/brain_frames/IMG_7028_brain_000.png` (strip the `media/` prefix).
   Play them in order, one per second, synced to the video. Cross-fade between
   frames for smoothness.

## The 3 pairs (blind-validated, model matched the human pick 3/3)
- 7024 (boring) vs 7025 (engaging)
- 7026 vs 7027 (engaging)
- 7028 (engaging) vs 7029
Details: [`../evals/`](../evals/).

## Videos
The 6 source `.mp4` files are on the Modal volume `reeled-in-cache` at
`/media/eval/` (too large for git). Regenerate all of this with:
`python3 -m modal run backend/modal_app.py::precompute_demo`.
