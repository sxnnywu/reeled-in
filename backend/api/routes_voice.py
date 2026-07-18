"""POST /tests/{id}/voice-variants, POST /suggest, GET /tests/{id}/tips. Owner: C (calls D).

Phase 1: stubs shaped exactly per CONTRACTS §5. Phase 3 swaps in D's real functions:
generate_voice_variants(base_media_key, specs), gemini.suggest(base_media_key, context),
llm.tips(user_id) (+ persist users.backboard_thread_id).
"""
import string

from fastapi import APIRouter, Depends

from backend.api.auth import current_user
from backend.api.routes_tests import get_test_or_404
from backend.db import store
from backend.models.schemas import SuggestReq, VoiceVariantsReq
from backend.util import new_id, now_iso

router = APIRouter()

_LABELS = string.ascii_uppercase


@router.post("/tests/{test_id}/voice-variants")
def voice_variants(test_id: str, body: VoiceVariantsReq, user=Depends(current_user)):
    test = get_test_or_404(test_id)
    made = []
    for i, spec in enumerate(body.variants):
        variant_id = new_id("var")
        variant = {
            "id": variant_id,
            "test_id": test_id,
            "label": spec.label or _LABELS[i % len(_LABELS)],
            # Phase 1 stub: no real mux — point at the base video so the UI can play it.
            # Phase 3: D's generate_voice_variants writes media/<variant_id>.mp4.
            "media_key": body.base_media_key,
            "params": {
                "script": spec.script,
                "voice_id": spec.voice_id,
                "voice_settings": spec.voice_settings,
            },
            "created_at": now_iso(),
        }
        store.VARIANTS[variant_id] = variant
        test["variant_ids"].append(variant_id)
        made.append(variant)
    test["updated_at"] = now_iso()
    return {"variants": made}


@router.post("/suggest")
def suggest(body: SuggestReq, user=Depends(current_user)):
    """Phase 1 canned test plan. Phase 3: D's gemini.suggest watches the video (CONTRACTS §5)."""
    return {
        "variants": [
            {"label": "A", "script": "Stop scrolling — watch what happens next.",
             "voice_settings": {"speed": 1.1}},
            {"label": "B", "script": "Here's the one thing everyone misses.",
             "voice_settings": {"speed": 0.95}},
            {"label": "C", "script": "You've never seen it from this angle."},
        ],
        "rationale": "Stub plan (Phase 1) — three hook styles at contrasting pacing. "
                     "Phase 3 wires Gemini to watch the footage and tailor these.",
    }


@router.get("/tests/{test_id}/tips")
def tips(test_id: str, user=Depends(current_user)):
    """Phase 1 canned tips. Phase 3: D's llm.tips(user_id) via Backboard memory."""
    get_test_or_404(test_id)
    return {
        "tips": "Hook in the first 2 seconds, keep cuts under 3 seconds, and land the CTA "
                "while engagement is still climbing. (Personalized tips arrive once your "
                "test history builds.)"
    }
