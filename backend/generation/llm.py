"""Backboard LLM: RAG/memory + personalized tips. Owner: D.

One Backboard thread per user (user_id -> thread_id). Test outcomes are posted into the
user's thread so Backboard's server-side memory learns their style; tips() asks the same
thread, so answers come back personalized. Thread map lives in a local JSON until C's
Mongo `users` doc takes over at integration (field: backboard_thread_id).
"""
import json
import os

import requests

from backend.generation.overlay import resolve

BASE_URL = "https://app.backboard.io/api"
THREADS_FILE = "media/backboard_threads.json"  # local stand-in for users.backboard_thread_id


def _post(content: str, thread_id: str = None) -> dict:
    body = {"content": content}
    if thread_id:
        body["thread_id"] = thread_id
    resp = requests.post(
        f"{BASE_URL}/threads/messages",
        headers={"X-API-Key": os.environ["BACKBOARD_API_KEY"]},
        json=body,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _threads() -> dict:
    path = resolve(THREADS_FILE)
    return json.loads(path.read_text()) if path.exists() else {}


def _remember_thread(user_id: str, thread_id: str):
    path = resolve(THREADS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    threads = _threads()
    threads[user_id] = thread_id
    path.write_text(json.dumps(threads, indent=2))


def record_test(user_id: str, test: dict, variants: list, winner_variant_id: str) -> str:
    """Write a completed test's outcome into the user's thread (memory write). -> thread_id"""
    by_id = {v["id"]: v for v in variants}
    winner = by_id.get(winner_variant_id, {})
    lines = [
        f"Completed A/B test {test['id']} (objective: {test.get('objective', 'retention')}).",
        f"WINNER: variant {winner.get('label', '?')} — params: {json.dumps(winner.get('params', {}))}.",
        "All variants: " + "; ".join(
            f"{v['label']}: {json.dumps(v.get('params', {}))}" for v in variants),
        "Remember what wins for this creator so future advice is personalized.",
    ]
    out = _post("\n".join(lines), _threads().get(user_id))
    _remember_thread(user_id, out["thread_id"])
    return out["thread_id"]


def tips(user_id: str) -> str:
    """Personalized advice from the user's test history (memory read). -> tips text"""
    out = _post(
        "Based on everything you remember about this creator's past A/B tests — which "
        "variants won and with what scripts, voices, and pacing — give 2-3 short, concrete, "
        "actionable tips for their next short-form video. If you have no history yet, give "
        "2-3 solid general hook/pacing tips and say you'll personalize as they run tests. "
        "Plain text, no markdown.",
        _threads().get(user_id),
    )
    _remember_thread(user_id, out["thread_id"])
    return out["content"]


if __name__ == "__main__":
    # Run: backend/.venv/bin/python -m backend.generation.llm [user_id]
    # Stages two tests where slow "rachel" reads win, then asks for tips —
    # the tips should echo that pattern back (proves the memory loop).
    import sys
    from dotenv import load_dotenv
    load_dotenv(resolve("backend/.env"))
    user = sys.argv[1] if len(sys.argv) > 1 else "usr_smoketest0001"

    def mkv(label, params):
        return {"id": f"var_{label.lower()}00000000000", "label": label, "params": params}

    print(f"user: {user} — recording 2 staged test outcomes (slow rachel wins both)...")
    record_test(user,
        {"id": "test_smoke000001", "objective": "retention"},
        [mkv("A", {"script": "Stop scrolling. Big news.", "voice_id": "rachel", "voice_settings": {"speed": 1.15}}),
         mkv("B", {"script": "Stop scrolling. Big news.", "voice_id": "rachel", "voice_settings": {"speed": 0.9}})],
        "var_b00000000000")
    record_test(user,
        {"id": "test_smoke000002", "objective": "retention"},
        [mkv("A", {"script": "Three mistakes killing your reach.", "voice_id": "josh", "voice_settings": {"speed": 1.1}}),
         mkv("B", {"script": "Three mistakes killing your reach.", "voice_id": "rachel", "voice_settings": {"speed": 0.85}})],
        "var_b00000000000")
    print("=== TIPS (should mention rachel / slower pacing) ===")
    print(tips(user))
