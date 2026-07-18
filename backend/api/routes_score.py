"""POST /tests/{id}/score, POST /tests/{id}/explain. Owner: C (calls B + D).

Scoring modes (SCORING_MODE env, default "mock"):
- "mock": synchronous mock scores, persisted via the repo; status -> complete
  immediately (contract allows `complete` on return when precomputed).
- "gpu": async request-reply (Pattern A) — set status=scoring, spawn ONE Modal
  `score_test_gpu(test_id)` call that scores the test's variants as a single
  batch (CONTRACTS §3 joint normalization: never per-variant calls) and writes
  scores+status+winner to Mongo; A polls GET /tests/{id} until complete/failed.
Already-scored tests (seeded/precomputed demo path) never re-run: the winner is
recomputed and the test flips to complete without touching a GPU.
"""
import os

from fastapi import APIRouter, Depends

from backend.api.auth import current_user
from backend.api.errors import ApiError
from backend.api.routes_tests import get_test_or_404
from backend.db.repo import repo
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


def _spawn_gpu(test_id: str) -> None:
    """Fire-and-forget Modal call (never .remote() — 150 s web cap). One per test."""
    import modal

    fn = modal.Function.from_name(os.environ.get("MODAL_APP_NAME", "reeled-in"), "score_test_gpu")
    fn.spawn(test_id)


async def _finalize(test_id: str, objective: str) -> None:
    winner = await repo().compute_winner(test_id, objective)
    await repo().update_test(
        test_id,
        {"status": "complete", "winner_variant_id": winner, "updated_at": now_iso()},
    )


@router.post("/tests/{test_id}/score")
async def score_test(test_id: str, user=Depends(current_user)):
    test = await get_test_or_404(test_id)
    if len(test["variant_ids"]) < 2:
        raise ApiError("bad_request", "need at least 2 variants to score")

    scored = {s["variant_id"] for s in await repo().scores_for(test)}
    unscored = [v for v in test["variant_ids"] if v not in scored]

    if not unscored:
        # Precomputed/seeded demo path — bulletproof, no GPU involved.
        await _finalize(test_id, test["objective"])
        return await get_test_or_404(test_id)

    if os.environ.get("SCORING_MODE", "mock") == "gpu":
        # Joint normalization (§3): the whole variant set scores together in one
        # batch — partially-scored tests re-score everything for a shared scale.
        await repo().update_test(test_id, {"status": "scoring", "updated_at": now_iso()})
        _spawn_gpu(test_id)
        return await get_test_or_404(test_id)  # A polls until complete/failed

    # mock mode: synchronous, persisted. Slight n variation so metrics differ
    # and the winner is real (floor keeps n sane for many-variant tests).
    for i, vid in enumerate(test["variant_ids"]):
        if vid in scored:
            continue
        await repo().upsert_score(test_id, mock_score(vid, n=max(8, 18 - 2 * i)))
    await _finalize(test_id, test["objective"])
    return await get_test_or_404(test_id)


@router.post("/tests/{test_id}/explain")
async def explain_test(test_id: str, user=Depends(current_user)):
    test = await get_test_or_404(test_id)
    scores = await repo().scores_for(test)
    explanations = {
        s["variant_id"]: [
            {"t": tick["t"], "text": _CAPTION[tick["top_network"]]}
            for tick in s["region_timeline"]
        ]
        for s in scores
    }
    return {"explanations": explanations}
