"""generate_voice_variants(base, specs) -> [Variant]. Owner: D."""
import secrets
import string
from datetime import datetime, timezone

from backend.generation.overlay import overlay
from backend.generation.voice import DEFAULT_VOICES, generate_read

_LABELS = string.ascii_uppercase


def _variant_id() -> str:
    return "var_" + secrets.token_hex(6)


def generate_voice_variants(base_media_key: str, specs: list) -> list:
    """Render one variant per VoiceSpec (CONTRACTS §5) muxed onto the base video.

    The client chooses which knobs vary across specs — voice, script, pacing, or any mix.
    spec: { script, voice_id?, voice_settings?, label? }  ->  [Variant dict] (CONTRACTS §4)
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    variants = []
    for i, spec in enumerate(specs):
        variant_id = _variant_id()
        voice_id = spec.get("voice_id") or DEFAULT_VOICES[i % len(DEFAULT_VOICES)]
        audio_path = generate_read(
            spec["script"], voice_id,
            voice_settings=spec.get("voice_settings"),
            out_name=variant_id,
        )
        media_key = overlay(base_media_key, audio_path, variant_id)
        variants.append({
            "id": variant_id,
            "test_id": None,  # C assigns when persisting
            "label": spec.get("label") or _LABELS[i],
            "media_key": media_key,
            "params": {
                "script": spec["script"],
                "voice_id": voice_id,
                "voice_settings": spec.get("voice_settings") or {},
            },
            "created_at": now,
        })
    return variants
