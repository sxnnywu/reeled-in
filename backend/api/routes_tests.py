"""POST /tests, /tests/{id}/variants, /tests/{id}/base-media, GET /tests/{id}. Owner: C (Seb)."""
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.api.auth import current_user
from backend.api.errors import ApiError, not_found
from backend.db import store
from backend.media import resolve_media
from backend.models.schemas import METRICS, CreateTestReq
from backend.util import new_id, now_iso

router = APIRouter()


def get_test_or_404(test_id: str) -> dict:
    test = store.TESTS.get(test_id)
    if test is None:
        raise not_found("test_id")
    return test


async def _save_upload(file: UploadFile, media_key: str) -> None:
    dest = resolve_media(media_key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())


@router.post("/tests")
def create_test(body: CreateTestReq, user=Depends(current_user)):
    if body.objective not in METRICS:
        raise ApiError("bad_request", f"objective must be one of {METRICS}")
    now = now_iso()
    test = {
        "id": new_id("test"),
        "user_id": user["user_id"],
        "type": body.type.value,
        "objective": body.objective,
        "status": "pending",
        "variant_ids": [],
        "winner_variant_id": None,
        "created_at": now,
        "updated_at": now,
    }
    store.TESTS[test["id"]] = test
    return test


@router.post("/tests/{test_id}/variants")
async def add_variant(
    test_id: str,
    file: UploadFile = File(...),
    label: str = Form(...),
    params: str = Form("{}"),
    user=Depends(current_user),
):
    test = get_test_or_404(test_id)
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
    store.VARIANTS[variant_id] = variant
    test["variant_ids"].append(variant_id)
    test["updated_at"] = now_iso()
    return variant


@router.post("/tests/{test_id}/base-media")
async def upload_base_media(test_id: str, file: UploadFile = File(...), user=Depends(current_user)):
    """Voice A/B: upload the base video once -> {media_key} (CONTRACTS §5)."""
    get_test_or_404(test_id)
    media_key = f"media/{test_id}_base.mp4"
    await _save_upload(file, media_key)
    return {"media_key": media_key}


@router.get("/tests/{test_id}")
def get_test(test_id: str, user=Depends(current_user)):
    test = get_test_or_404(test_id)
    variants = [store.VARIANTS[v] for v in test["variant_ids"] if v in store.VARIANTS]
    scores = [store.SCORES[v] for v in test["variant_ids"] if v in store.SCORES]
    return {"test": test, "variants": variants, "scores": scores}
