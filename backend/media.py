"""Media root + safe media_key resolution (CONTRACTS §7). Owner: C (Seb).

ONE physical root for all lanes (PERSON_C_PLAN findings #12/#13):
- Local dev: repo root — the same convention D's generation/overlay.py uses,
  so C-served files and D-generated files land in the same ./media/ tree.
- On Modal: api() sets MEDIA_ROOT=/cache so everything lives on the shared
  `reeled-in-cache` Volume that B's score_gpu reads (/cache/media/...).
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def media_root() -> Path:
    return Path(os.environ.get("MEDIA_ROOT", REPO_ROOT))


def resolve_media(media_key: str) -> Path:
    """media_key ('media/<id>.mp4') -> absolute path under the root. Rejects traversal."""
    root = media_root().resolve()
    path = (root / media_key).resolve()
    if not str(path).startswith(str(root) + os.sep):
        raise ValueError(f"bad media_key: {media_key}")
    return path
