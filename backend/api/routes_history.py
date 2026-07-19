"""GET /history -> {tests: [TestSummary]} (CONTRACTS §5 — enriched, no N+1). Owner: C (Seb)."""
from fastapi import APIRouter, Depends

from backend.api.auth import current_user
from backend.db.repo import repo

router = APIRouter()


@router.get("/history")
async def history(user=Depends(current_user)):
    tests = []
    for t in await repo().list_tests(user["user_id"]):
        winner = None
        wid = t.get("winner_variant_id")
        if wid:
            wv = await repo().get_variant(wid)
            if wv:
                winner = {"variant_id": wid, "label": wv["label"]}
        tests.append({
            "test_id": t["id"],
            "name": t.get("name"),
            "type": t["type"],
            "status": t["status"],
            "created_at": t["created_at"],
            "variant_count": len(t["variant_ids"]),
            "winner": winner,
        })
    return {"tests": tests}
