"""GET /media/{media_key} — stream media bytes (video + brain PNGs) to A. Owner: C (Seb).

URL = API_BASE + "/media/" + media_key verbatim (media_key already starts with "media/",
so a full URL looks like /api/media/media/var_x.mp4). FileResponse handles HTTP Range ->
206 Partial Content, so <video> seeking works for free.

Unauthenticated by design: <video src=...> / <img src=...> tags cannot send an
Authorization header. media_keys are unguessable (12-hex ids). Raised for CONTRACTS §5
ratification in PERSON_C_PLAN §8.1.
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.api.errors import ApiError, not_found
from backend.media import resolve_media

router = APIRouter()

_MEDIA_TYPES = {".mp4": "video/mp4", ".png": "image/png", ".mp3": "audio/mpeg"}


@router.get("/media/{media_key:path}")
def get_media(media_key: str):
    try:
        path = resolve_media(media_key)
    except ValueError:
        raise ApiError("bad_request", "invalid media_key")
    if not path.is_file():
        raise not_found("media_key")
    return FileResponse(path, media_type=_MEDIA_TYPES.get(path.suffix, "application/octet-stream"))
