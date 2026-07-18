"""Auth (CONTRACTS §6): Auth0 RS256 JWT verified against JWKS -> stable user_id. Owner: C (Seb).

Real mode: AUTH0_DOMAIN + AUTH0_AUDIENCE set -> PyJWT + PyJWKClient (cached, module scope),
audience/issuer checked, ACCESS tokens only (id tokens have the SPA client_id as `aud` and
are rejected by the audience check — by design).
Dev fallback: env unset -> a fixed dev user, so Phase-1 local dev and A's early
integration work without an Auth0 tenant.
"""
import hashlib
import os
from typing import Optional

from fastapi import Header

from backend.api.errors import ApiError

# `email` is not in an Auth0 access token by default — an Auth0 post-login Action adds it
# under this namespaced claim. Best-effort; `sub` is the stable key (CONTRACTS §6).
EMAIL_CLAIM = "https://reeledin.app/email"

_jwks_client = None  # module scope: JWKS cache survives warm Modal containers


def _auth0_enabled() -> bool:
    return bool(os.environ.get("AUTH0_DOMAIN") and os.environ.get("AUTH0_AUDIENCE"))


def _verify(token: str) -> dict:
    import jwt  # PyJWT — lazy import so dev mode runs without it installed
    from jwt import PyJWKClient

    global _jwks_client
    issuer = f"https://{os.environ['AUTH0_DOMAIN']}/"
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{issuer}.well-known/jwks.json", cache_keys=True, lifespan=300)
    try:
        key = _jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],  # whitelist — never trust the header alg
            audience=os.environ["AUTH0_AUDIENCE"],
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except Exception as e:
        raise ApiError("unauthorized", f"invalid token: {e}", 401)


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency -> {"user_id": "usr_...", "email": ...}."""
    if not _auth0_enabled():
        return {"user_id": "usr_" + "0" * 12, "email": "dev@local"}
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError("unauthorized", "missing bearer token", 401)
    claims = _verify(authorization.removeprefix("Bearer "))
    user_id = "usr_" + hashlib.sha256(claims["sub"].encode()).hexdigest()[:12]
    # TODO(C Phase 2): upsert users doc {_id, email, display_name, created_at} in Mongo.
    return {"user_id": user_id, "email": claims.get(EMAIL_CLAIM)}
