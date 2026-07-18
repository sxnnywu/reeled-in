"""Small shared helpers. Owner: C (Seb)."""
import secrets
from datetime import datetime, timezone


def new_id(prefix: str) -> str:
    """CONTRACTS §1: '<prefix>_' + 12-char lowercase hex, e.g. test_9f2a10bc4d3e."""
    return f"{prefix}_{secrets.token_hex(6)}"


def now_iso() -> str:
    """CONTRACTS §1 timestamp: ISO 8601 UTC, e.g. '2026-07-19T04:20:00Z'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
