"""Reeled In API — FastAPI app (served on Modal as an ASGI endpoint). Owner: C (Seb).
Run locally: uvicorn backend.main:app --reload   (loads backend/.env if present)
"""
import os

# Local dev: pick up backend/.env before anything reads the environment.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:  # pragma: no cover — dotenv ships with uvicorn[standard]
    pass

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api import (
    routes_history, routes_media, routes_science, routes_score, routes_tests, routes_voice,
)
from backend.api.errors import ApiError

_STATUS_TO_CODE = {400: "bad_request", 401: "unauthorized", 404: "not_found", 422: "bad_request"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.environ.get("MONGODB_URI"):
        from backend.db.mongo import close, ensure_indexes

        await ensure_indexes()
        yield
        await close()
    else:  # Phase 1: in-memory store (db/store.py), no Atlas needed
        yield


app = FastAPI(title="Reeled In API", lifespan=lifespan)

# CORS (CONTRACTS §6 layer 4): exact origins only — never "*", we send Authorization.
_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:3000", "http://localhost:5173"],  # dev default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

for m in (routes_tests, routes_score, routes_voice, routes_history, routes_media, routes_science):
    app.include_router(m.router, prefix="/api")


# --- CONTRACTS §9 error envelope ---


@app.exception_handler(ApiError)
async def _api_error(_req, exc: ApiError):
    return JSONResponse({"error": {"code": exc.code, "message": exc.message}},
                        status_code=exc.http_status)


@app.exception_handler(StarletteHTTPException)
async def _http_error(_req, exc: StarletteHTTPException):
    code = _STATUS_TO_CODE.get(exc.status_code, "internal")
    return JSONResponse({"error": {"code": code, "message": str(exc.detail)}},
                        status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def _validation_error(_req, exc: RequestValidationError):
    return JSONResponse({"error": {"code": "bad_request", "message": str(exc.errors()[:3])}},
                        status_code=422)


@app.exception_handler(Exception)
async def _unhandled_error(_req, exc: Exception):
    # Catch-all so even unexpected 500s keep the §9 envelope A parses.
    return JSONResponse({"error": {"code": "internal", "message": "internal server error"}},
                        status_code=500)


@app.get("/api/health")
def health():
    return {"ok": True}
