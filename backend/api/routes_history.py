"""GET /history -> {tests: [TestSummary]} (CONTRACTS §5 — enriched, no N+1). Owner: C (Seb)."""
from fastapi import APIRouter, Depends

from backend.api.auth import current_user
from backend.db import store

router = APIRouter()


@router.get("/history")
def history(user=Depends(current_user)):
    mine = [t for t in store.TESTS.values() if t["user_id"] == user["user_id"]]
    tests = []
    for t in sorted(mine, key=lambda t: t["created_at"], reverse=True):
        winner = None
        wid = t.get("winner_variant_id")
        if wid and wid in store.VARIANTS:
            winner = {"variant_id": wid, "label": store.VARIANTS[wid]["label"]}
        tests.append({
            "test_id": t["id"],
            "name": t.get("name"),
            "type": t["type"],
            "objective": t["objective"],
            "status": t["status"],
            "created_at": t["created_at"],
            "variant_count": len(t["variant_ids"]),
            "winner": winner,
        })
    return {"tests": tests}
