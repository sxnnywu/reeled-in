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
    .env({"HF_HOME": f"{CACHE_DIR}/hf"})
    .add_local_python_source("backend")
)


@app.function(image=image)
@modal.asgi_app()
def api():
    from backend.main import app as fastapi_app

    return fastapi_app


@app.function(image=tribe_image, gpu="A100", volumes={CACHE_DIR: cache}, timeout=3600)
def score_gpu(media_key: str) -> dict:
    """C calls this with a media_key; returns the Score Object (CONTRACTS.md §3)."""
    from backend.scoring.score import score

    result = score(media_key)
    cache.commit()
    return result


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
