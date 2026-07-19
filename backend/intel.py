"""Intelligence bridge: C's async routes -> D's sync generation/LLM functions. Owner: C (Seb).

GENERATION_MODE env: "real" (D's ElevenLabs/Gemini/Backboard code) or "stub" (canned
shapes). Local default is stub so teammates without keys still run everything; the
deployed api() defaults to real (modal_app sets it).

All D calls run in a worker thread (asyncio.to_thread) so their sync network I/O never
blocks the event loop. The Backboard thread map is injected into D's pluggable store
(llm.configure_thread_store), backed by users.backboard_thread_id through a small SYNC
pymongo client — D's code is sync and runs off-loop, so it can't touch the async repo.
Imports of D's modules are lazy so this file is importable in every image (the GPU
image has no elevenlabs, the local venv may lack nothing but keys).
"""
import asyncio
import copy
import os

_sync_client = None
_mem_threads: dict[str, str] = {}
_configured = False

# Human names for the default ElevenLabs voices (mirror of voice.py DEFAULT_VOICES).
# record_test writes variant params into Backboard memory verbatim, so a raw voice_id
# would surface in /tips as "stick with 21m00Tcm4TlvDq8ikWAM". Translate to the name.
# TODO(D): promote a canonical VOICE_NAMES to generation/voice.py and import it here.
VOICE_NAMES = {
    "21m00Tcm4TlvDq8ikWAM": "Rachel",
    "pNInz6obpgDQGcFmaJgB": "Adam",
    "TxGEqnHWrfWFTfGW9XjX": "Josh",
}


def _humanize_variants(variants: list) -> list:
    """Copy of variants with params.voice_id replaced by a readable params.voice —
    so Backboard memory (and thus /tips) never echoes an opaque voice_id."""
    out = []
    for v in variants:
        v = copy.deepcopy(v)
        params = v.get("params") or {}
        vid = params.pop("voice_id", None)
        if vid:
            params["voice"] = VOICE_NAMES.get(vid, "a custom voice")
        v["params"] = params
        out.append(v)
    return out


def real_mode() -> bool:
    return os.environ.get("GENERATION_MODE", "stub") == "real"


def _users_sync():
    """Sync users collection for the thread map (pymongo MongoClient is thread-safe)."""
    global _sync_client
    if _sync_client is None:
        from pymongo import MongoClient

        _sync_client = MongoClient(
            os.environ["MONGODB_URI"], maxPoolSize=2, serverSelectionTimeoutMS=5000
        )
    return _sync_client[os.environ.get("MONGODB_DB", "reeled_in")].users


def _get_thread(user_id: str):
    if os.environ.get("MONGODB_URI"):
        doc = _users_sync().find_one({"_id": user_id}, {"backboard_thread_id": 1})
        return (doc or {}).get("backboard_thread_id")
    return _mem_threads.get(user_id)


def _set_thread(user_id: str, thread_id: str) -> None:
    if os.environ.get("MONGODB_URI"):
        _users_sync().update_one(
            {"_id": user_id}, {"$set": {"backboard_thread_id": thread_id}}, upsert=True
        )
    else:
        _mem_threads[user_id] = thread_id


def init_intel() -> None:
    """Idempotent. Injects the users.backboard_thread_id store into D's llm module."""
    global _configured
    if _configured:
        return
    from backend.generation import llm

    llm.configure_thread_store(_get_thread, _set_thread)
    _configured = True


async def suggest(base_media_key: str, context: str) -> dict:
    from backend.generation import gemini

    return await asyncio.to_thread(gemini.suggest, base_media_key, context)


async def voice_variants(base_media_key: str, specs: list) -> list:
    """specs = plain dicts (VoiceSpec.model_dump()) — D's fn is dict-based."""
    from backend.generation import variants

    return await asyncio.to_thread(variants.generate_voice_variants, base_media_key, specs)


async def tips(user_id: str, current_result: str = None) -> str:
    init_intel()
    from backend.generation import llm

    return await asyncio.to_thread(llm.tips, user_id, current_result)


async def explain(region_timeline: list):
    """-> [{t, text}] or None on failure (caller falls back to template captions)."""
    from backend.generation import explainer

    try:
        return await asyncio.to_thread(explainer.explain, region_timeline)
    except Exception:
        return None


async def record_test_safe(user_id: str, test: dict, variants: list, winner_variant_id) -> None:
    """Memory write on test completion — best-effort, never sinks the score flow."""
    if not (real_mode() and winner_variant_id):
        return
    init_intel()
    from backend.generation import llm

    try:
        await asyncio.to_thread(
            llm.record_test, user_id, test, _humanize_variants(variants), winner_variant_id)
    except Exception:
        pass


def record_test_sync_safe(user_id: str, test: dict, variants: list, winner_variant_id) -> None:
    """Same, for sync contexts (the GPU completion path in modal_app)."""
    if not (real_mode() and winner_variant_id):
        return
    init_intel()
    from backend.generation import llm

    try:
        llm.record_test(user_id, test, _humanize_variants(variants), winner_variant_id)
    except Exception:
        pass
