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


def commit_media() -> None:
    """Persist Volume writes immediately (writer commits, reader reloads) so the GPU
    container's cache.reload() sees fresh uploads/generated media without waiting on
    Modal's background commit. No-op off Modal (MEDIA_ROOT=/cache only there)."""
    if os.environ.get("MEDIA_ROOT") == "/cache":
        try:
            from backend.modal_app import cache

            cache.commit()
        except Exception:
            pass  # background commit still covers us


def resolve_media(media_key: str) -> Path:
    """media_key ('media/<id>.mp4') -> absolute path, confined to the media/ subtree.

    Rejects traversal AND anything outside <root>/media — the serve route is
    unauthenticated (video/img tags can't send headers), so it must never be able
    to read source files or .env under the local-dev root.
    """
    if not media_key.startswith("media/"):  # §7: every media_key is 'media/...'
        raise ValueError(f"bad media_key: {media_key}")
    root = media_root().resolve()
    media_dir = root / "media"
    path = (root / media_key).resolve()
    if not str(path).startswith(str(media_dir) + os.sep):
        raise ValueError(f"bad media_key: {media_key}")
    return path
