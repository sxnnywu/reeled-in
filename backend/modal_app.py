"""Modal app: serves the FastAPI ASGI app (CPU, scale-to-zero) + hosts the TRIBE GPU fn.
Owner: C wires the app; B fills score_gpu (+ B's smoke/load/score verification fns).

Run (B verification):
  python3 -m modal run backend/modal_app.py::smoke_test
  python3 -m modal run backend/modal_app.py::load_test
  python3 -m modal run backend/modal_app.py::score_test
"""
import modal

app = modal.App("reeled-in")

# Persistent cache for HF weights + TRIBE checkpoint (and variant media under
# /cache/media) so GPU cold starts don't re-download ~20GB of encoders.
cache = modal.Volume.from_name("reeled-in-cache", create_if_missing=True)
CACHE_DIR = "/cache"

# Light image for the FastAPI ASGI app (C's api()).
image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg")  # [C] Phase 3: D's overlay mux + gemini's ffprobe run in-api
    .pip_install_from_requirements("backend/requirements.txt")
    .add_local_python_source("backend")
)

# Heavy image for TRIBE scoring: torch pinned <2.7 per tribev2 pyproject,
# installed from git; clone to /opt so it can't shadow the installed package.
tribe_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg")
    .pip_install("torch>=2.5.1,<2.7", "torchvision>=0.20,<0.22")
    .run_commands(
        "git clone --depth 1 https://github.com/facebookresearch/tribev2 /opt/tribev2-src",
        "pip install -e /opt/tribev2-src",
        "python -m spacy download en_core_web_sm",
    )
    .pip_install("nilearn")  # Destrieux atlas for the vertex->network mapping
    .pip_install("pymongo>=4.9")  # [C] Phase-2 async scoring: GPU writes scores to Mongo
    .env({"HF_HOME": f"{CACHE_DIR}/hf"})
    .add_local_python_source("backend")
)


# Model-free objective signals (CPU): motion, sharpness, YOLO clarity,
# MediaPipe face expression, Whisper transcript.
objective_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0", "libgles2", "libegl1", "libgl1-mesa-dri")
    .pip_install(
        "numpy", "opencv-python-headless", "ultralytics", "mediapipe", "openai-whisper"
    )
    .add_local_python_source("backend")
)


@app.function(image=objective_image, volumes={CACHE_DIR: cache}, timeout=5400)
def analyze_objective(subdir: str = "eval", names: str = "") -> dict:
    """Run all model-free signals on the clips: motion, sharpness (blur), object
    clarity (YOLO), facial expression (MediaPipe), speech transcript (Whisper).
    Each is wrapped so one failing model doesn't sink the rest."""
    import json
    from pathlib import Path

    from backend.scoring.face import analyze_face
    from backend.scoring.hands import analyze_hands
    from backend.scoring.objects import detect_objects
    from backend.scoring.objective import measure_motion, measure_sharpness
    from backend.scoring.transcript import transcribe

    folder = Path(CACHE_DIR) / "media" / subdir
    wanted = {n.strip() for n in names.split(",") if n.strip()}
    clips = {p.stem: str(p) for p in sorted(folder.glob("*.mp4")) if not wanted or p.stem in wanted}

    def safe(fn):
        try:
            return fn()
        except Exception as e:
            return {"error": str(e)[:250]}

    out = {}
    for name, path in clips.items():
        out[name] = {
            "motion": measure_motion(path)["mean_motion"],
            "sharpness": measure_sharpness(path)["sharpness"],
            "clarity": safe(lambda: detect_objects(path, CACHE_DIR)),
            "face": safe(lambda: analyze_face(path, CACHE_DIR)),
            "hands": safe(lambda: analyze_hands(path, CACHE_DIR)),
            "speech": safe(lambda: transcribe(path, CACHE_DIR)),
        }
        cache.commit()
        print(f"done {name}: {json.dumps(out[name])[:400]}")
    print("OBJECTIVE:\n" + json.dumps(out, indent=2))
    return out


@app.function(
    image=image,
    volumes={CACHE_DIR: cache},  # Volume mount: C serves/stores media
    # Two workspace secrets (CONTRACTS §8). Last wins on key conflicts, so D's
    # reeled-in-secrets takes precedence for the generation keys (D owns rotation);
    # Mongo keys exist only in C's reeled-in.
    secrets=[modal.Secret.from_name("reeled-in"), modal.Secret.from_name("reeled-in-secrets")],
)
@modal.asgi_app()
def api():
    import os

    # One media root for all lanes (PERSON_C_PLAN findings #12/#13): the shared Volume.
    os.environ.setdefault("MEDIA_ROOT", CACHE_DIR)
    # Deployed default: real D integrations (ElevenLabs/Gemini/Backboard). Local dev
    # defaults to stub so keyless teammates still run; override via the secret.
    os.environ.setdefault("GENERATION_MODE", "real")
    from backend.main import app as fastapi_app

    return fastapi_app


@app.function(image=tribe_image, gpu="A100", volumes={CACHE_DIR: cache}, timeout=7200)
def precompute_demo(subdir: str = "eval") -> dict:
    """Score + render brain frames for the demo clips, saving full Score Objects
    to /cache/precomputed/ for the bulletproof (no live GPU) demo path."""
    import json
    from pathlib import Path

    from backend.scoring.precompute import precompute

    folder = Path(CACHE_DIR) / "media" / subdir
    clips = {p.stem: str(p) for p in sorted(folder.glob("*.mp4"))}
    print(f"Precomputing {len(clips)} demo clips: {list(clips)}")
    summary = precompute(clips, CACHE_DIR)
    cache.commit()
    print("PRECOMPUTE SUMMARY:\n" + json.dumps(summary, indent=2))
    return summary


@app.function(
    image=tribe_image,
    gpu="A100",
    volumes={CACHE_DIR: cache},
    timeout=3600,
    # C's Mongo keys — Phase 2: the GPU fn writes status+scores to Mongo directly.
    secrets=[modal.Secret.from_name("reeled-in")],
)
def score_gpu(media_key: str) -> dict:
    """C calls this with a media_key; returns the Score Object (CONTRACTS.md §3)."""
    from backend.scoring.score import score

    result = score(media_key)
    cache.commit()
    return result


@app.function(
    image=tribe_image,
    gpu="A100",
    volumes={CACHE_DIR: cache},
    timeout=3600,
    secrets=[modal.Secret.from_name("reeled-in")],
)
def score_test_gpu(test_id: str) -> dict:
    """[C] Phase-2 async request-reply (Pattern A — the GPU fn owns status).

    ONE spawn per test (CONTRACTS §3 joint normalization, ratified 2026-07-18:
    "C batches a test's variants into one scoring call"). Scores every variant
    of the test in this single GPU session, persists the Score Objects, computes
    the winner (shared aggregation pipeline), flips status to complete. Failures
    flip status to failed. A polls GET /tests/{id} for the transitions.

    TODO(B): the inner per-variant `score()` calls still use per-clip
    normalization — swap to B's shared-scale batch entrypoint when the eval_ab
    port lands (that swap happens HERE and nowhere else). Until then the batch
    seam is contract-correct but the winner-reliability caveat from
    NORMALIZATION_DECISION.md still applies to GPU-scored tests.
    """
    import os

    from pymongo import MongoClient

    from backend.db.repo import winner_pipeline, _score_doc
    from backend.scoring.score import score
    from backend.util import now_iso

    cache.reload()  # see media committed by the api() container (writer commits, reader reloads)
    client = MongoClient(os.environ["MONGODB_URI"])
    d = client[os.environ.get("MONGODB_DB", "reeled_in")]
    try:
        test = d.tests.find_one({"_id": test_id})
        if not test:
            return {"ok": False, "error": "test not found"}
        by_id = {v["_id"]: v for v in d.variants.find({"test_id": test_id})}
        ordered = [by_id[v] for v in test["variant_ids"] if v in by_id]

        for variant in ordered:  # joint batch: all variants, one session, one model load
            result = score(variant["media_key"])
            result["variant_id"] = variant["_id"]  # authoritative id
            d.scores.replace_one(
                {"variant_id": variant["_id"]}, _score_doc(test_id, result), upsert=True
            )

        rows = list(d.scores.aggregate(winner_pipeline(test_id, test.get("objective", "retention"))))
        winner_id = rows[0]["variant_id"] if rows else None
        d.tests.update_one(
            {"_id": test_id},
            {"$set": {"status": "complete",
                      "winner_variant_id": winner_id,
                      "updated_at": now_iso()}},
        )
        cache.commit()

        # Phase 3: best-effort Backboard memory write (llm.tips personalizes from this).
        os.environ.setdefault("GENERATION_MODE", "real")
        from backend.intel import record_test_sync_safe

        wire_variants = [{"id": v["_id"], "label": v["label"], "params": v.get("params", {})}
                         for v in ordered]
        record_test_sync_safe(test["user_id"], {"id": test_id, "objective": test.get("objective")},
                              wire_variants, winner_id)
        return {"ok": True, "test_id": test_id, "variants_scored": len(ordered)}
    except Exception:
        d.tests.update_one({"_id": test_id},
                           {"$set": {"status": "failed", "updated_at": now_iso()}})
        raise
    finally:
        client.close()


# --- B verification functions ---

smoke_image = modal.Image.debian_slim(python_version="3.11").pip_install("torch")


@app.function(gpu="A100", image=smoke_image, timeout=600)
def smoke_test() -> dict:
    import torch

    info = {
        "cuda_available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "torch_version": str(torch.__version__),
    }
    print("A100 smoke test:", info)
    return info


@app.function(gpu="A100", image=tribe_image, volumes={CACHE_DIR: cache}, timeout=3600)
def load_test() -> dict:
    import torch
    from backend.scoring.tribe_model import load_model

    load_model(CACHE_DIR)
    cache.commit()
    info = {"loaded": True, "device": "cuda" if torch.cuda.is_available() else "cpu"}
    print("TRIBE load test:", info)
    return info


@app.function(image=tribe_image, volumes={CACHE_DIR: cache}, timeout=1800)
def mask_test() -> dict:
    """Build the Destrieux vertex->network mask and report vertex counts per
    network (no GPU needed)."""
    import numpy as np

    from backend.scoring.networks import NETWORKS, build_network_mask

    mask = build_network_mask()
    cache.commit()
    counts = {name: int((mask == i).sum()) for i, name in enumerate(NETWORKS)}
    counts["unassigned"] = int((mask == -1).sum())
    info = {"total_vertices": int(mask.shape[0]), "per_network": counts}
    print("Network mask:", info)
    return info


@app.function(gpu="A100", image=tribe_image, volumes={CACHE_DIR: cache}, timeout=7200)
def eval_folder(subdir: str = "eval", names: str = "") -> dict:
    """Score clips in /cache/media/<subdir> on one shared scale. `names` =
    optional comma-separated stems to limit to (e.g. "IMG_7024,IMG_7025").
    Returns per-clip metrics under both normalizations."""
    import json
    from pathlib import Path

    from backend.scoring.eval_ab import run_ab_eval
    from backend.scoring.tribe_model import load_model

    folder = Path(CACHE_DIR) / "media" / subdir
    wanted = {n.strip() for n in names.split(",") if n.strip()}
    clips = {
        p.stem: str(p)
        for p in sorted(folder.glob("*.mp4"))
        if not wanted or p.stem in wanted
    }
    print(f"Scoring {len(clips)} clips: {list(clips)}")

    model = load_model(CACHE_DIR)
    results = run_ab_eval(model, clips)
    cache.commit()
    print("EVAL RESULTS:\n" + json.dumps(results, indent=2))
    return results


@app.function(gpu="A100", image=tribe_image, volumes={CACHE_DIR: cache}, timeout=3600)
def dryrun_eval() -> dict:
    """Generate a CALM clip and a BUSY clip, score both, and show that the
    shared-scale normalization separates them while per-clip flattens them.
    Validates the A/B pipeline before real clips are recorded."""
    import json
    import subprocess
    from pathlib import Path

    from backend.scoring.eval_ab import pair_winner, run_ab_eval
    from backend.scoring.tribe_model import load_model

    d = Path(CACHE_DIR) / "media" / "dryrun"
    d.mkdir(parents=True, exist_ok=True)
    calm, busy = str(d / "calm.mp4"), str(d / "busy.mp4")

    # CALM: static gray frame, silence.
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=gray:s=320x240:d=20:r=25",
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "20",
         "-pix_fmt", "yuv420p", "-shortest", calm],
        check=True, capture_output=True,
    )
    # BUSY: fast-moving test pattern + audible tone.
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=20:size=320x240:rate=30",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
         "-pix_fmt", "yuv420p", "-shortest", busy],
        check=True, capture_output=True,
    )

    model = load_model(CACHE_DIR)
    results = run_ab_eval(model, {"calm": calm, "busy": busy})
    cache.commit()
    verdict = {
        "shared_scale": pair_winner(results, "calm", "busy", "shared"),
        "perclip": pair_winner(results, "calm", "busy", "perclip"),
        "metrics": results,
    }
    print("DRY-RUN A/B:\n" + json.dumps(verdict, indent=2))
    return verdict


@app.function(gpu="A100", image=tribe_image, volumes={CACHE_DIR: cache}, timeout=3600)
def score_test() -> dict:
    """Generate a synthetic clip, score it end-to-end via score(media_key)."""
    import json
    import subprocess
    from pathlib import Path

    from backend.scoring.score import score

    media_dir = Path(CACHE_DIR) / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    clip = media_dir / "var_synthetictest.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=20:size=320x240:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
            "-shortest", "-pix_fmt", "yuv420p", str(clip),
        ],
        check=True,
        capture_output=True,
    )

    result = score("media/var_synthetictest.mp4")
    cache.commit()
    print("Score Object:\n" + json.dumps(result, indent=2)[:2000])
    return result


@app.local_entrypoint()
def main():
    result = smoke_test.remote()
    assert result["cuda_available"], "CUDA not available on the GPU worker"
    print("PASS — A100 booted:", result)
