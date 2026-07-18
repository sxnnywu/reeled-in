"""Gemini watches the base video and proposes a test plan (VoiceSpecs). Owner: D."""
import base64
import json
import os

import requests

from backend.generation.overlay import resolve

# 2.5-flash-lite: highest free-tier quota; 2.0-flash 429s on the free tier.
MODEL = "gemini-2.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = """You are a short-form video A/B testing strategist. Watch this video, including any
existing audio/voiceover it already has. Based on what is actually there — pacing of cuts,
subject, mood, how the first 3 seconds look, what the current audio does or fails to do —
propose {n} voiceover variants the creator could OPTIONALLY test over this footage.

Vary the axes that matter for THIS footage: script wording/hook style, delivery speed, tone.
If the video already has a voiceover, treat it as the baseline your variants compete against.
{context_line}

Return JSON only, matching exactly:
{{"variants": [{{"label": "A", "script": "...", "voice_settings": {{"speed": 1.0}}}}, ...],
  "rationale": "2-3 sentences: what you saw in the footage and why these variants test it"}}

Rules: scripts must be speakable in under 10 seconds (~25 words max). speed in [0.7, 1.2].
Labels "A", "B", "C"... Omit voice_settings when defaults are fine. {n} variants."""


def suggest(base_media_key: str, context: str = "", n: int = 3) -> dict:
    """-> { "variants": [VoiceSpec], "rationale": str } (CONTRACTS §5 /suggest)."""
    video_b64 = base64.b64encode(resolve(base_media_key).read_bytes()).decode()
    prompt = PROMPT.format(n=n, context_line=f"Creator context: {context}" if context else "")
    resp = requests.post(
        URL,
        params={"key": os.environ["GEMINI_API_KEY"]},
        json={
            "contents": [{"parts": [
                {"inline_data": {"mime_type": "video/mp4", "data": video_b64}},
                {"text": prompt},
            ]}],
            "generationConfig": {"response_mime_type": "application/json"},
        },
        timeout=120,
    )
    resp.raise_for_status()
    out = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
    for i, v in enumerate(out.get("variants", [])):
        v.setdefault("label", chr(ord("A") + i))
    return out
