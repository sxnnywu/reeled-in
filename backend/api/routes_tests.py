"""POST /tests, /tests/{id}/variants, /tests/{id}/base-media, GET /tests/{id}. Owner: C (Seb)."""
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.api.auth import current_user
from backend.api.errors import ApiError, not_found
from backend.db.repo import repo
from backend.media import resolve_media
from backend.models.schemas import METRICS, CreateTestReq
from backend.util import new_id, now_iso

router = APIRouter()


async def get_test_or_404(test_id: str) -> dict:
    test = await repo().get_test(test_id)
    if test is None:
        raise not_found("test_id")
    return test


async def _save_upload(file: UploadFile, media_key: str) -> None:
    dest = resolve_media(media_key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())


@router.post("/tests")
async def create_test(body: CreateTestReq, user=Depends(current_user)):
    if body.objective not in METRICS:
        raise ApiError("bad_request", f"objective must be one of {METRICS}")
    now = now_iso()
    test = {
        "id": new_id("test"),
        "user_id": user["user_id"],
        "type": body.type.value,
        "name": body.name,  # optional user title; null -> A derives a fallback
        "objective": body.objective,
        "status": "pending",
        "variant_ids": [],
        "winner_variant_id": None,
        "created_at": now,
        "updated_at": now,
    }
    await repo().insert_test(test)
    return test


@router.post("/tests/{test_id}/variants")
async def add_variant(
    test_id: str,
    file: UploadFile = File(...),
    label: str = Form(...),
    params: str = Form("{}"),
    user=Depends(current_user),
):
    test = await get_test_or_404(test_id)
    try:
        params_dict = json.loads(params) if params else {}
    except json.JSONDecodeError:
        raise ApiError("bad_request", "params must be a JSON object string")
    variant_id = new_id("var")
    media_key = f"media/{variant_id}.mp4"  # CONTRACTS §7
    await _save_upload(file, media_key)
    variant = {
        "id": variant_id,
        "test_id": test_id,
        "label": label,
        "media_key": media_key,
        "params": params_dict,
        "created_at": now_iso(),
    }
    await repo().insert_variant(variant)
    await repo().update_test(
        test_id,
        {"variant_ids": test["variant_ids"] + [variant_id], "updated_at": now_iso()},
    )
    return variant


@router.post("/tests/{test_id}/base-media")
async def upload_base_media(test_id: str, file: UploadFile = File(...), user=Depends(current_user)):
    """Voice A/B: upload the base video once -> {media_key} (CONTRACTS §5)."""
    await get_test_or_404(test_id)
    media_key = f"media/{test_id}_base.mp4"
    await _save_upload(file, media_key)
    return {"media_key": media_key}


@router.get("/tests/{test_id}")
async def get_test(test_id: str, user=Depends(current_user)):
    test = await get_test_or_404(test_id)
    variants = await repo().variants_for(test)
    scores = await repo().scores_for(test)
    return {"test": test, "variants": variants, "scores": scores}
