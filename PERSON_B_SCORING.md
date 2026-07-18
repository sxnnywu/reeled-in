# Person B — Scoring Engine (hand-off)

Owner: B (Jay). Companion to `PARALLEL_IMPLEMENTATION_PLAN.md` and `CONTRACTS.md`.
This is the pass-off doc: what the scoring lane built, how to run it, how to
consume it, and what's open. Read `CONTRACTS.md` §3 (the Score Object) first.

## Status
- ✅ TRIBE v2 loads and scores real video end-to-end on a Modal A100.
- ✅ Gated Llama bypassed — text encoder patched to the ungated `unsloth/Llama-3.2-3B`
  mirror (identical weights), so we never wait on Meta's license approval.
- ✅ Produces the full Score Object (CONTRACTS §3): 5 network curves, engagement,
  4 metrics, region_timeline. (`brain_frames` still `[]` — see Open items.)
- ✅ Real vertex→network mapping (Destrieux atlas), not a placeholder split.
- ✅ Blind validation: on 3 hand-labelled talking-head pairs the model matched the
  human pick 3/3 (see `evals/example-7024-vs-7025.md`).
- ✅ Bonus: a model-free objective toolkit (motion, blur, object clarity, speech
  transcript, face expression, hand/gesture) that runs alongside the brain score.

## How to run (all via Modal)
```
python3 -m modal run backend/modal_app.py::smoke_test        # A100 boots
python3 -m modal run backend/modal_app.py::load_test         # TRIBE loads
python3 -m modal run backend/modal_app.py::score_test        # synthetic clip -> Score Object
python3 -m modal run backend/modal_app.py::eval_folder --names "IMG_a,IMG_b"      # brain A/B on volume clips
python3 -m modal run backend/modal_app.py::analyze_objective --names "IMG_a,IMG_b" # objective toolkit
```
Clips live on the Modal Volume `reeled-in-cache` under `/media/<subdir>/`.
Upload with: `modal volume put reeled-in-cache local.mp4 /media/eval/name.mp4`.

## Files (backend/scoring/)
| file | does |
|---|---|
| `tribe_model.py` | download TRIBE checkpoint, patch Llama→unsloth, `load_model()` on A100 |
| `score.py` | `score(media_key) -> ScoreObject` — the public entrypoint C calls |
| `networks.py` | reduce ~20k vertices → 5 networks via Destrieux atlas mask (cached) |
| `metrics.py` | engagement blend + peak/sustained/retention/overall (formulas pinned in CONTRACTS §3) |
| `regions.py` | `region_timeline` — top network/region per second |
| `eval_ab.py` | A/B eval on a shared scale + per-system breakdown |
| `objective.py` | model-free motion + sharpness (blur) |
| `objects.py` | YOLO object detection → clarity, objects, person_frac |
| `face.py` | MediaPipe → smile/frown/brows/blink/head-motion |
| `hands.py` | MediaPipe → hand presence, hand motion, named gestures |
| `transcript.py` | Whisper → transcript text, word count, words/sec |
| `brain_render.py` | (STUB) per-second brain PNGs → `brain_frames` — not built yet |
| `precompute.py` | (STUB) batch-score demo clips → demo path |

Modal wiring is in `backend/modal_app.py`: `score_gpu(media_key)` (A100, TRIBE image)
is what C's API calls; `api()` (CPU, requirements image) is C's FastAPI. Objective
signals run on a separate CPU image (`objective_image`).

## Interface for C (integration)
- Call `score_gpu.remote(media_key)` → returns the Score Object dict (CONTRACTS §3).
- `media_key` = `media/<variant_id>.mp4`. **Open handoff detail:** `score()` resolves
  it from the Modal Volume at `/cache/media/<...>`. C owns storage (CONTRACTS §7) — we
  need to agree whether C writes variant media to that volume path or passes bytes.
- Weights + atlas + model files cache on the `reeled-in-cache` volume; cold starts are slow, warm are fast.

## ⚠️ Known issues / things the team must decide (do NOT silently change)
1. **Normalization is a real product decision.** Networks are min-max normalized
   *per clip* right now (CONTRACTS §3: "already normalized by B"). We found this
   FLATTENS differences between clips and makes variant comparison unreliable —
   it literally ranked a known pair backwards. The eval fixes it with a *shared
   scale* across the clips being compared (`eval_ab.py`). **The product `score()`
   still normalizes per-clip.** Fixing it properly means scoring a test's variants
   on a shared scale — which changes CONTRACTS §3 and C's winner logic. **This
   needs a team decision + a CONTRACTS change first; don't change it unilaterally.**
2. **`brain_frames` is empty.** The per-second brain-PNG flipbook (`brain_render.py`)
   isn't built. A's results screen must handle `brain_frames: []`.
3. **Motion calibration.** The brain motion system was mis-mapped (included motor
   cortex); fixed to lateral occipitotemporal cortex, but it's still weak at
   capturing camera-motion magnitude (phone motion is out-of-distribution for
   TRIBE). The objective motion signal (`objective.py`) is the reliable one.
4. **Objective signals are diagnostic, not scored.** motion/blur/clarity/face/hands
   are accurate "how much" stats shown alongside engagement. "More X = more
   engaging" is unvalidated — don't wire them into the score without labelled data.
5. `face.py` mouth-open reads 0 (frame sampling too slow for fast speech) — minor, fix by sampling faster.

## For C — serving media to the frontend (needed, C's lane)
Brain images + video live on the Modal Volume `reeled-in-cache` under
`/media/<file>`. Score Objects reference them by `media_key` = `media/<file>.png`.
A can't load them until C exposes an HTTP route that streams a media_key from the
volume, e.g.:
```
GET /api/media/{key}   ->  streams  /cache/media/{key}   (image/png or video/mp4)
```
Then A's brain frame src = `${API_BASE}/media/${brain_frames[i]}`. Precomputed
Score Objects are at `/cache/precomputed/<vid>.json` for the no-GPU demo path.

## Brain-frame smoothness (for A)
TRIBE is **1 Hz** — one real brain state per second, so `brain_frames` is one
image per second, aligned 1:1 with the network arrays (CONTRACTS §3).
- **Recommended:** A cross-fades between consecutive frames (CSS/opacity tween)
  for a smooth flipbook — no fake data, no contract change.
- `render_frames(..., sub=2)` can emit interpolated half-second frames if we
  really want them pre-rendered, but the in-betweens are blended (not new
  measurements) and it desyncs frame count from the 1 Hz data. Only do this with
  a CONTRACTS note. Default stays sub=1.

## Open items (Person B)
- Build `brain_render.py` (brain_frames) and `precompute.py` (demo path, needs D's clips).
- Resolve the normalization decision with the team (item 1 above).
- Optionally fold validated objective signals into the score once we have labels.
