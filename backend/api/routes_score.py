"""POST /tests/{id}/score, POST /tests/{id}/explain. Owner: C (calls B + D at Phase 3).

Phase 1: scoring is a synchronous mock (contract allows POST /score to return `complete`
when precomputed). Phase 2: set status=scoring, score_gpu.spawn(test_id, media_key) per
variant (never .remote() — 150 s web cap), GPU fn writes status+scores to Mongo, A polls
GET /tests/{id}. Winner selection becomes the Mongo aggregation pipeline (PERSON_C_PLAN §5.1).
"""
from fastapi import APIRouter, Depends

from backend.api.auth import current_user
from backend.api.errors import ApiError
from backend.api.routes_tests import get_test_or_404
from backend.db import store
from backend.mocks.mock_score import mock_score
from backend.util import now_iso

router = APIRouter()

# Phase-1 stand-in for D's explainer (Phase 3: generation/explainer.explain via Backboard).
_CAPTION = {
    "visual": "Eyes locked on the frame — the visuals are landing.",
    "auditory": "The sound has your viewer's full attention.",
    "language": "Language centers lit up — the words are landing.",
    "motion": "On-screen action is gripping them.",
    "default_mode": "Deep narrative immersion — the story feels personal.",
}


def _pick_winner(test: dict) -> str | None:
    """Highest metrics[objective] among scored variants. Phase 2: Mongo aggregation."""
    objective = test["objective"]
    scored = [
        (vid, store.SCORES[vid]["metrics"][objective])
        for vid in test["variant_ids"]
        if vid in store.SCORES
    ]
    return max(scored, key=lambda kv: kv[1])[0] if scored else None


@router.post("/tests/{test_id}/score")
def score_test(test_id: str, user=Depends(current_user)):
    test = get_test_or_404(test_id)
    if len(test["variant_ids"]) < 2:
        raise ApiError("bad_request", "need at least 2 variants to score")
    # Vary curve length slightly per variant so mock metrics differ and the winner is real
    # (floor keeps n sane for tests with many variants).
    for i, vid in enumerate(test["variant_ids"]):
        store.SCORES[vid] = mock_score(vid, n=max(8, 18 - 2 * i))
    test["winner_variant_id"] = _pick_winner(test)
    test["status"] = "complete"
    test["updated_at"] = now_iso()
    return test


@router.post("/tests/{test_id}/explain")
def explain_test(test_id: str, user=Depends(current_user)):
    test = get_test_or_404(test_id)
    explanations = {
        vid: [
            {"t": tick["t"], "text": _CAPTION[tick["top_network"]]}
            for tick in store.SCORES[vid]["region_timeline"]
        ]
        for vid in test["variant_ids"]
        if vid in store.SCORES
    }
    return {"explanations": explanations}
