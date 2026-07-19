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

_STUB_SUGGEST = {  # shape parity with the real Gemini response (§5: note + transcript)
    "variants": [
        {"label": "A", "script": "Stop scrolling — watch what happens next.",
         "voice_settings": {"speed": 1.1}, "note": "Tests an urgency hook at fast pacing."},
        {"label": "B", "script": "Here's the one thing everyone misses.",
         "voice_settings": {"speed": 0.95}, "note": "Tests a curiosity-gap hook at neutral pacing."},
        {"label": "C", "script": "You've never seen it from this angle.",
         "note": "Tests a novelty-framing hook at default delivery."},
    ],
    "rationale": "Stub plan — three hook styles at contrasting pacing. "
                 "GENERATION_MODE=real wires Gemini to watch the footage and tailor these.",
    "transcript": "",
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
        for variant, spec in zip(made, body.variants):  # D returns in spec order
            variant["test_id"] = test_id  # D returns test_id=None; C assigns on persist
            if spec.note:  # §5: suggested variants' creative-bet note lands in params.note
                variant["params"]["note"] = spec.note
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
                           "voice_settings": spec.voice_settings,
                           **({"note": spec.note} if spec.note else {})},
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


def _setup(v: dict) -> str:
    """One-line human description of a variant's knobs (voice humanized, pace bucketed)."""
    p = dict(v.get("params") or {})
    vid = p.pop("voice_id", None)
    bits = []
    if p.get("script"):
        bits.append(f'script "{p["script"][:90]}"')
    if vid:
        bits.append(f"voice {intel.VOICE_NAMES.get(vid, 'a custom voice')}")
    speed = (p.get("voice_settings") or {}).get("speed")
    if speed:
        bits.append(f"{'fast' if speed > 1.02 else 'slow' if speed < 0.98 else 'normal'} pace ({speed})")
    return ", ".join(bits) or "an uploaded clip"


def _improve_context(test: dict, variants: list, scores: list):
    """Per-variant profile (setup + each variant's strongest/weakest brain systems + the
    winner) fed to /tips, so it recommends concrete improvements FOR EACH variant targeting
    its weak areas — not just restating what already won. None if unscored."""
    from backend.analysis import build_analysis
    from backend.science import COMPONENTS

    if not scores:
        return None
    labels = {c["key"]: c["label"] for c in COMPONENTS}
    by_vid = {s["variant_id"]: s for s in scores}
    a = build_analysis(test, variants, scores)
    lines = []
    if a.get("winner_variant_id"):
        wl = next((v["label"] for v in variants if v["id"] == a["winner_variant_id"]), "?")
        lines.append(f"A/B test — Variant {wl} won, mainly on {labels.get(a.get('decisive'), 'the measured signals')}.")
    for v in variants:
        s = by_vid.get(v["id"])
        if not s:
            continue
        means = {k: sum(x) / len(x) for k, x in (s.get("networks") or {}).items() if x}
        if means:
            strong = ", ".join(labels.get(f"brain:{n}", n) for n in sorted(means, key=means.get, reverse=True)[:2])
            weak = ", ".join(labels.get(f"brain:{n}", n) for n in sorted(means, key=means.get)[:2])
            lines.append(f"Variant {v['label']} — {_setup(v)}. Strongest: {strong}. Weakest: {weak}.")
        else:
            lines.append(f"Variant {v['label']} — {_setup(v)}.")
    return "\n".join(lines) or None


def _parse_per_variant(text: str, variants: list):
    """Parse the LLM's 'VARIANT <label>\\n- rec…' blocks into structured per-variant recs.
    Returns None if it doesn't parse (frontend then falls back to the raw `tips` text)."""
    import re

    by_label = {v["label"].strip().upper(): v for v in variants}
    per = []
    for block in re.split(r"(?im)^\s*VARIANT\s+", text or ""):
        block = block.strip()
        if not block:
            continue
        head = block.splitlines()[0].strip().rstrip(":").upper()
        v = by_label.get(head) or (by_label.get(head.split()[0]) if head.split() else None)
        recs = [re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", ln).strip()
                for ln in block.splitlines()[1:]
                if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", ln)]
        if v and recs:
            per.append({"variant_id": v["id"], "label": v["label"], "recommendations": recs[:3]})
    return per or None


@router.get("/tests/{test_id}/tips")
async def tips(test_id: str, user=Depends(current_user)):
    """Per-variant improvement recommendations grounded in THIS test + Backboard memory.
    Returns `{tips: <text>, per_variant: [{variant_id, label, recommendations:[…]}] | null}`."""
    test = await get_test_or_404(test_id)
    if intel.real_mode():
        try:
            variants = await repo().variants_for(test)
            scores = await repo().scores_for(test)
            ctx = _improve_context(test, variants, scores)
            text = await intel.tips(test["user_id"], ctx)
            return {"tips": text, "per_variant": _parse_per_variant(text, variants) if ctx else None}
        except Exception:
            pass  # Backboard hiccup must not break the screen — fall through to stub
    return {"tips": _STUB_TIPS, "per_variant": None}
