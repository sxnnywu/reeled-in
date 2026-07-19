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


def _local_get_thread(user_id: str):
    return _threads().get(user_id)


def _local_set_thread(user_id: str, thread_id: str):
    path = resolve(THREADS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    threads = _threads()
    threads[user_id] = thread_id
    path.write_text(json.dumps(threads, indent=2))


# Pluggable thread-map store. Default: local JSON. C: call configure_thread_store with
# getters/setters backed by users.backboard_thread_id at startup — no other change needed.
_get_thread = _local_get_thread
_set_thread = _local_set_thread


def configure_thread_store(get_thread, set_thread):
    """get_thread(user_id) -> thread_id|None; set_thread(user_id, thread_id) -> None."""
    global _get_thread, _set_thread
    _get_thread, _set_thread = get_thread, set_thread


def record_test(user_id: str, test: dict, variants: list, winner_variant_id: str) -> str:
    """Write a completed test's outcome into the user's thread (memory write). -> thread_id"""
    by_id = {v["id"]: v for v in variants}
    winner = by_id.get(winner_variant_id, {})
    lines = [
        f"Completed A/B test {test['id']}.",
        f"WINNER: variant {winner.get('label', '?')} — params: {json.dumps(winner.get('params', {}))}.",
        "All variants: " + "; ".join(
            f"{v['label']}: {json.dumps(v.get('params', {}))}" for v in variants),
        "Remember what wins for this creator so future advice is personalized.",
    ]
    out = _post("\n".join(lines), _get_thread(user_id))
    _set_thread(user_id, out["thread_id"])
    return out["thread_id"]


def tips(user_id: str, current_result: str = None) -> str:
    """Advice for the creator. If `current_result` is given (the test they're viewing on
    the results page), ground the tips in THIS clip's outcome and use memory for extra
    personalization; else fall back to pure cross-test memory. [C edit — D please review]"""
    if current_result:
        prompt = (
            f"THE A/B TEST THE CREATOR IS LOOKING AT RIGHT NOW:\n{current_result}\n\n"
            "Give 2-3 short, concrete, actionable tips to improve THIS clip and what to test "
            "next, grounded specifically in this result — name the winning choice and why it "
            "worked, and suggest the next variable to test. Weave in anything you remember "
            "about their past tests for extra personalization, but keep the tips about this "
            "clip. Do NOT say you have no data. Plain text, no markdown."
        )
    else:
        prompt = (
            "Based on everything you remember about this creator's past A/B tests — which "
            "variants won and with what scripts, voices, and pacing — give 2-3 short, concrete, "
            "actionable tips for their next short-form video. If you have no history yet, give "
            "2-3 solid general hook/pacing tips and say you'll personalize as they run tests. "
            "Plain text, no markdown."
        )
    out = _post(prompt, _get_thread(user_id))
    _set_thread(user_id, out["thread_id"])
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

    # Staged pattern is CONDITIONAL: fast reads win on hype scripts, slow reads win on
    # story/educational scripts; voice is a decoy (winners split rachel/josh). A good
    # memory should surface "match pacing to script energy", not "always go slow".
    print(f"user: {user} — recording 4 staged test outcomes (fast wins hype, slow wins story)...")
    STAGED = [
        ("test_smoke000001",
         [mkv("A", {"script": "STOP. This changes everything. Watch.", "voice_id": "rachel", "voice_settings": {"speed": 1.15}}),
          mkv("B", {"script": "STOP. This changes everything. Watch.", "voice_id": "rachel", "voice_settings": {"speed": 0.85}})],
         "var_a00000000000"),
        ("test_smoke000002",
         [mkv("A", {"script": "When I was 19, I almost quit. Here's what saved me.", "voice_id": "josh", "voice_settings": {"speed": 1.15}}),
          mkv("B", {"script": "When I was 19, I almost quit. Here's what saved me.", "voice_id": "josh", "voice_settings": {"speed": 0.85}})],
         "var_b00000000000"),
        ("test_smoke000003",
         [mkv("A", {"script": "HUGE update. You need this today. Go.", "voice_id": "josh", "voice_settings": {"speed": 1.1}}),
          mkv("B", {"script": "HUGE update. You need this today. Go.", "voice_id": "rachel", "voice_settings": {"speed": 0.9}})],
         "var_a00000000000"),
        ("test_smoke000004",
         [mkv("A", {"script": "Let me explain the one metric most creators ignore.", "voice_id": "rachel", "voice_settings": {"speed": 1.1}}),
          mkv("B", {"script": "Let me explain the one metric most creators ignore.", "voice_id": "rachel", "voice_settings": {"speed": 0.8}})],
         "var_b00000000000"),
    ]
    for test_id, variants, winner in STAGED:
        record_test(user, {"id": test_id}, variants, winner)
    print("=== TIPS (should say: match pacing to script energy, not 'always slow') ===")
    print(tips(user))
