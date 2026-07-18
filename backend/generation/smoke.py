"""Reusable voice-pipeline smoke test. Owner: D (Sunny).

Run:  backend/.venv/bin/python -m backend.generation.smoke [base_media_key]

Cleans previously generated variants out of media/, then renders 5 variants
covering every axis: voice, pacing, script, and a combo.
"""
import sys

from dotenv import load_dotenv

from backend.generation.overlay import resolve
from backend.generation.variants import generate_voice_variants

HOOK = "Stop scrolling. Reeled In shows you which edit hooks the brain before you post."
ALT_HOOK = "Guessing is expensive. Test your reel on a brain, not your follower count."

SPECS = [
    {"label": "A", "script": HOOK, "voice_id": "21m00Tcm4TlvDq8ikWAM"},                                      # baseline (Rachel)
    {"label": "B", "script": HOOK, "voice_id": "pNInz6obpgDQGcFmaJgB"},                                      # voice axis (Adam)
    {"label": "C", "script": HOOK, "voice_id": "21m00Tcm4TlvDq8ikWAM", "voice_settings": {"speed": 1.15}},   # pacing axis
    {"label": "D", "script": ALT_HOOK, "voice_id": "21m00Tcm4TlvDq8ikWAM"},                                  # script axis
    {"label": "E", "script": ALT_HOOK, "voice_id": "TxGEqnHWrfWFTfGW9XjX",
     "voice_settings": {"speed": 0.9, "style": 0.6}},                                                        # combo (Josh, slow, styled)
]


def clean():
    removed = 0
    for pattern in ("media/var_*.mp4", "media/audio/*.mp3"):
        for f in resolve("").glob(pattern):
            f.unlink()
            removed += 1
    print(f"cleaned {removed} old generated file(s)")


def main():
    load_dotenv(resolve("backend/.env"))
    base = sys.argv[1] if len(sys.argv) > 1 else "demo/dataset/base_clip_1.mp4"
    clean()
    print(f"base: {base}")
    for v in generate_voice_variants(base, SPECS):
        p = v["params"]
        print(f"  {v['label']}  {v['media_key']}  voice={p['voice_id'][:8]}  settings={p['voice_settings']}  script={p['script'][:40]!r}")
    print("open media/ to review")


if __name__ == "__main__":
    main()
