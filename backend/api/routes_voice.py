"""POST /tests/{id}/voice-variants, POST /suggest, GET /tests/{id}/tips. Owner: C (calls D).

Phase 3: real D functions behind GENERATION_MODE=real (ElevenLabs+ffmpeg mux,
Gemini-watches-the-video /suggest, Backboard-personalized /tips) via backend.intel;
stub shapes otherwise so keyless local runs still work end-to-end.
"""
import string

from fastapi import APIRouter, Depends

from backend import intel
from backend.api.auth import current_user
from backend.api.errors import ApiError
from backend.api.routes_tests import get_test_or_404
from backend.db.repo import repo
from backend.media import commit_media
from backend.models.schemas import SuggestReq, VoiceVariantsReq
from backend.util import new_id, now_iso

router = APIRouter()

_LABELS = string.ascii_uppercase

_STUB_SUGGEST = {
    "variants": [
        {"label": "A", "script": "Stop scrolling — watch what happens next.",
         "voice_settings": {"speed": 1.1}},
        {"label": "B", "script": "Here's the one thing everyone misses.",
         "voice_settings": {"speed": 0.95}},
        {"label": "C", "script": "You've never seen it from this angle."},
    ],
    "rationale": "Stub plan — three hook styles at contrasting pacing. "
                 "GENERATION_MODE=real wires Gemini to watch the footage and tailor these.",
}

_STUB_TIPS = ("Hook in the first 2 seconds, keep cuts under 3 seconds, and land the CTA "
              "while engagement is still climbing. (Personalized tips arrive once your "
              "test history builds.)")


@router.post("/tests/{test_id}/voice-variants")
async def voice_variants(test_id: str, body: VoiceVariantsReq, user=Depends(current_user)):
    test = await get_test_or_404(test_id)

    if intel.real_mode():
        # D's pipeline: ElevenLabs read per spec -> ffmpeg mux onto the base video.
        try:
            made = await intel.voice_variants(
                body.base_media_key, [s.model_dump() for s in body.variants]
            )
        except Exception as e:
            raise ApiError("internal", f"voice generation failed: {e}", 500)
        commit_media()  # generated mp4s must be visible to the GPU scorer's reload()
        for variant in made:
            variant["test_id"] = test_id  # D returns test_id=None; C assigns on persist
    else:
        made = []
        for i, spec in enumerate(body.variants):
            made.append({
                "id": new_id("var"),
                "test_id": test_id,
                "label": spec.label or _LABELS[i % len(_LABELS)],
                # stub: no real mux — point at the base video so the UI can play it
                "media_key": body.base_media_key,
                "params": {"script": spec.script, "voice_id": spec.voice_id,
                           "voice_settings": spec.voice_settings},
                "created_at": now_iso(),
            })

    for variant in made:
        await repo().insert_variant(variant)
    await repo().update_test(
        test_id,
        {"variant_ids": test["variant_ids"] + [v["id"] for v in made], "updated_at": now_iso()},
    )
    return {"variants": made}


@router.post("/suggest")
async def suggest(body: SuggestReq, user=Depends(current_user)):
    """Gemini watches the base video -> VoiceSpec test plan (CONTRACTS §5, MLH Gemini track)."""
    if not intel.real_mode():
        return _STUB_SUGGEST
    try:
        return await intel.suggest(body.base_media_key, body.context or "")
    except Exception as e:
        raise ApiError("internal", f"suggest failed: {e}", 500)


@router.get("/tests/{test_id}/tips")
async def tips(test_id: str, user=Depends(current_user)):
    """Personalized tips from Backboard memory (thread map: users.backboard_thread_id)."""
    test = await get_test_or_404(test_id)
    if intel.real_mode():
        try:
            # tips are per-USER memory; the route hangs off a test — resolve owner
            return {"tips": await intel.tips(test["user_id"])}
        except Exception:
            pass  # Backboard hiccup must not break the screen — fall through to stub
    return {"tips": _STUB_TIPS}
