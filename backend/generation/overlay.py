"""ffmpeg audio mux onto a base video. Owner: D."""
import os
import subprocess
from pathlib import Path

# Honors MEDIA_ROOT so all lanes share one media tree (C sets it to /cache on Modal —
# the shared Volume B's scorer reads; PERSON_C_PLAN findings #12/#13). Local default
# unchanged: repo root. [C edit — D please review]
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", Path(__file__).resolve().parents[2]))


def resolve(media_key: str) -> Path:
    return MEDIA_ROOT / media_key


def overlay(base_media_key: str, audio_path: str, out_variant_id: str) -> str:
    """Replace the base video's audio with the voiceover. -> media_key (CONTRACTS §7)."""
    media_key = f"media/{out_variant_id}.mp4"
    out_path = resolve(media_key)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(resolve(base_media_key)),
            "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            str(out_path),
        ],
        check=True,
    )
    return media_key
