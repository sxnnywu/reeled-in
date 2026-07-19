"""GET /api/science — the research evidence behind the scoring (judge showcase). Owner: C (Seb).

Public (no auth): static reference content, same for every user, so it works regardless of
auth state. The frontend renders a "science / evidence" panel from it and can tie a specific
A/B result's `analysis.decisive` component to its papers.
"""
from fastapi import APIRouter

from backend.science import get_science

router = APIRouter()


@router.get("/science")
def science():
    return get_science()
