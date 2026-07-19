"""Gemini watches the base video and proposes a test plan (VoiceSpecs). Owner: D."""
import base64
import json
import os
import subprocess
import time

import requests

from backend.generation.overlay import resolve

# Via OpenRouter (paid, no free-tier 429s — the shared AI Studio key kept quota-failing
# /suggest during the hackathon). Same Gemini family, OpenAI-compatible wire format.
MODEL = "google/gemini-3.5-flash"
URL = "https://openrouter.ai/api/v1/chat/completions"

PROMPT = """You are a short-form video A/B testing strategist. Watch this video, including any
existing audio/voiceover it already has. Based on what is actually there — pacing of cuts,
subject, mood, how the first 3 seconds look, what the current audio does or fails to do —
propose {n} voiceover variants the creator could OPTIONALLY test over this footage.

THE VIDEO IS THE CREATIVE VISION — DO NOT REPLACE IT. Your variants are small, testable
tweaks of single variables (hook wording, delivery speed, tone of the read) around what the
footage already is. Every script must fit the mood and subject actually on screen. Never
invent product names, brands, or a new concept for the video. If the creator context clashes
with the footage, say so in the rationale and keep the scripts faithful to the footage.
If the video already has a voiceover, treat it as the baseline your variants compete against.
{context_line}

Return JSON only, matching exactly:
{{"variants": [{{"label": "A", "script": "...", "voice_settings": {{"speed": 1.0}},
    "note": "one sentence, plain creator language: the specific creative bet this variant tests, e.g. 'Tests a question-style hook — does curiosity beat a bold claim on this footage?'"}}, ...],
  "rationale": "2-3 sentences: what you saw in the footage and why these variants test it",
  "transcript": "the words spoken in the video, transcribed verbatim — or null if no speech"}}

Rules: the video is {duration:.0f} seconds long — each script must be comfortably speakable
within it (roughly {max_words} words at normal pace). speed in [0.7, 1.2]. Labels "A", "B",
"C"... Omit voice_settings when defaults are fine. {n} variants."""

WORDS_PER_SEC = 2.5  # comfortable spoken pace


def _duration_sec(media_key: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(resolve(media_key))],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def suggest(base_media_key: str, context: str = "", n: int = 3) -> dict:
    """-> { "variants": [VoiceSpec], "rationale": str } (CONTRACTS §5 /suggest)."""
    video_b64 = base64.b64encode(resolve(base_media_key).read_bytes()).decode()
    duration = _duration_sec(base_media_key)
    prompt = PROMPT.format(
        n=n,
        duration=duration,
        max_words=int(duration * WORDS_PER_SEC),
        context_line=f"Creator context: {context}" if context else "",
    )
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "video_url",
             "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}},
            {"type": "text", "text": prompt},
        ]}],
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}
    for attempt in range(4):  # 503/429 are routine on larger video payloads
        resp = requests.post(URL, headers=headers, json=body, timeout=120)
        if resp.status_code not in (429, 500, 502, 503):
            break
        time.sleep(2 ** attempt * 5)  # 5s, 10s, 20s
    resp.raise_for_status()
    out = json.loads(resp.json()["choices"][0]["message"]["content"])
    out.setdefault("transcript", None)
    for i, v in enumerate(out.get("variants", [])):
        v.setdefault("label", chr(ord("A") + i))
        v.setdefault("note", "")
        # keep only the contract's knobs — Gemini sometimes invents keys
        vs = {k: v["voice_settings"][k] for k in ("speed", "stability", "style")
              if k in v.get("voice_settings", {})}
        if vs:
            v["voice_settings"] = vs
        else:
            v.pop("voice_settings", None)
    return out


if __name__ == "__main__":
    # Run: backend/.venv/bin/python -m backend.generation.gemini [base_media_key] ["context"]
    import sys
    from dotenv import load_dotenv
    load_dotenv(resolve("backend/.env"))
    base = sys.argv[1] if len(sys.argv) > 1 else "demo/dataset/base_clip_1.mp4"
    ctx = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(suggest(base, context=ctx), indent=2))
