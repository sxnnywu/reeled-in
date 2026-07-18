# Demo dataset — where it lives

The demo clips and their precomputed scorecards are **on the Modal volume
`reeled-in-cache`**, not committed to git (they're large video binaries).

**6 demo clips** (hand-recorded talking-head, 3 boring/engaging pairs):
- `/media/eval/IMG_7024.mp4` … `IMG_7029.mp4`

**Precomputed scorecards** (full Score Object incl. `brain_frames`, shared-scale
per CONTRACTS §3):
- `/precomputed/IMG_7024.json` … `IMG_7029.json`

**Brain frame PNGs** (the flipbook images):
- `/media/IMG_XXXX_brain_000.png` …

## Regenerate
```
python3 -m modal run backend/modal_app.py::precompute_demo
```
This scores all 6 clips as one shared-scale batch and renders their brain
frames, writing the JSONs above.

## For C (serving to the frontend)
Load a precomputed scorecard from `/precomputed/<variant_id>.json`; serve brain
frames + video by `media_key` from the volume (`GET /api/media/{key}`).

Blind validation of the model against these clips: [`../../evals/`](../../evals/).
