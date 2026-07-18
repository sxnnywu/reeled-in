"""Modal app for Reeled In — Person B (scoring engine).

Functions:
  smoke_test  — Phase 0: confirm an A100 boots and CUDA is visible.
  load_test   — Phase 1a: build the TRIBE image and load the checkpoint on A100
                (text encoder overridden to the ungated unsloth Llama mirror).

Run:
  python3 -m modal run backend/modal_app.py::smoke_test
  python3 -m modal run backend/modal_app.py::load_test
"""

import modal

app = modal.App("reeled-in-scoring")

# Persistent cache for HF weights + TRIBE checkpoint so cold starts don't
# re-download ~20GB of encoders.
cache = modal.Volume.from_name("reeled-in-cache", create_if_missing=True)
CACHE_DIR = "/cache"

# --- Minimal image for the Phase 0 GPU smoke test ---
smoke_image = modal.Image.debian_slim(python_version="3.11").pip_install("torch")

# --- Full TRIBE image: torch pinned <2.7 per tribev2 pyproject, installed from git ---
tribe_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg")
    .pip_install("torch>=2.5.1,<2.7", "torchvision>=0.20,<0.22")
    .run_commands(
        # Clone outside /root: the container cwd is /root, so a /root/tribev2
        # dir would shadow the installed package as an empty namespace package.
        "git clone --depth 1 https://github.com/facebookresearch/tribev2 /opt/tribev2-src",
        "pip install -e /opt/tribev2-src",
        "python -m spacy download en_core_web_sm",
    )
    .env({"HF_HOME": f"{CACHE_DIR}/hf"})
    .add_local_python_source("scoring")
)


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
    from scoring.tribe_model import load_tribe

    model = load_tribe(CACHE_DIR)
    cache.commit()  # persist downloaded weights to the volume

    n_params = sum(p.numel() for p in model.parameters()) if hasattr(model, "parameters") else None
    info = {
        "loaded": True,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "n_params": n_params,
    }
    print("TRIBE load test:", info)
    return info


@app.local_entrypoint()
def main():
    result = smoke_test.remote()
    assert result["cuda_available"], "CUDA not available on the GPU worker"
    print("PASS — A100 booted:", result)
