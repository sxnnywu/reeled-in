"""generate_voice_variants(base, script) -> [Variant]. Owner: D."""
import secrets
import string
from datetime import datetime, timezone

from backend.generation.overlay import overlay
from backend.generation.voice import generate_reads

_LABELS = string.ascii_uppercase


def _variant_id() -> str:
    return "var_" + secrets.token_hex(6)


def generate_voice_variants(base_media_key: str, script: str, voices=None) -> list:
    """One variant per voice read, muxed onto the base video. -> [Variant dict] (CONTRACTS §4)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    variants = []
    for i, read in enumerate(generate_reads(script, voices)):
        variant_id = _variant_id()
        media_key = overlay(base_media_key, read["audio_path"], variant_id)
        variants.append({
            "id": variant_id,
            "test_id": None,  # C assigns when persisting
            "label": _LABELS[i],
            "media_key": media_key,
            "params": {"voice_id": read["voice_id"], "script": script},
            "created_at": now,
        })
    return variants
