"""Backend E2E smoke — drives the deployed API through the full product flow. Owner: D.

Run:  backend/.venv/bin/python -m backend.e2e_smoke [base_url] [clip_path]
Defaults: the deployed Modal API + demo/dataset/base_clip_1.mp4.
Local:    backend/.venv/bin/python -m backend.e2e_smoke http://127.0.0.1:8000 …

Auth: the deployed API enforces Auth0 (since 2026-07-18) — export E2E_TOKEN with a
real Auth0 ACCESS token (grab one from the Base44 app session: DevTools -> the
Authorization header on any API call). Without E2E_TOKEN this falls back to
"Bearer dev", which only works on a local server without AUTH0_* env set.

Flow: create test -> upload base -> /suggest (Gemini watches it) -> /voice-variants
(ElevenLabs renders 2) -> /score -> poll to complete/failed -> /explain -> /tips.
NOTE: real ElevenLabs/Gemini/Backboard calls when the server runs GENERATION_MODE=real
— costs quota, don't loop it. Scoring path depends on the server's SCORING_MODE
("mock" = instant canned scores; "gpu" = real TRIBE batch on the A100).
"""
import os
import sys
import time

import requests

DEFAULT_BASE = "https://jaychopra05--reeled-in-api.modal.run"
POLL_EVERY_SEC = 15
POLL_LIMIT = 60  # 15 min — covers a cold GPU start


def main():
    base = ((len(sys.argv) > 1 and sys.argv[1]) or DEFAULT_BASE).rstrip("/") + "/api"
    clip = sys.argv[2] if len(sys.argv) > 2 else "demo/dataset/base_clip_1.mp4"
    token = os.environ.get("E2E_TOKEN", "dev")
    H = {"Authorization": f"Bearer {token}"}
    if token == "dev":
        print("note: using dev-fallback auth — set E2E_TOKEN for the Auth0-enforced deployed API")

    r = requests.get(f"{base}/health", timeout=30)
    r.raise_for_status()
    print("0 health:", r.json())

    r = requests.post(f"{base}/tests", headers=H, timeout=60,
                      json={"type": "voice", "name": "E2E smoke"})
    if r.status_code == 401:
        print("E2E FAILED: 401 unauthorized — this server enforces Auth0; set E2E_TOKEN "
              "to a real access token (see module docstring)")
        sys.exit(1)
    t = r.json()
    tid = t["id"]
    print("1 test created:", tid)

    with open(clip, "rb") as f:
        r = requests.post(f"{base}/tests/{tid}/base-media", headers=H,
                          files={"file": ("base.mp4", f, "video/mp4")}, timeout=180)
    mk = r.json()["media_key"]
    print("2 base uploaded:", mk)

    r = requests.post(f"{base}/suggest", headers=H, timeout=300,
                      json={"base_media_key": mk, "context": "short-form brand teaser"})
    plan = r.json()
    assert "transcript" in plan, "/suggest missing `transcript` (CONTRACTS §5)"
    print("3 suggest rationale:", plan.get("rationale", "")[:120])
    print("  transcript:", (plan["transcript"] or "<none — no speech in clip>")[:120])

    r = requests.post(f"{base}/tests/{tid}/voice-variants", headers=H, timeout=600,
                      json={"base_media_key": mk, "variants": plan["variants"][:2]})
    print("4 variants:", [(v["label"], v["media_key"]) for v in r.json()["variants"]])

    r = requests.post(f"{base}/tests/{tid}/score", headers=H, timeout=120)
    print("5 score:", r.json().get("status"))

    status = None
    for i in range(POLL_LIMIT):
        full = requests.get(f"{base}/tests/{tid}", headers=H, timeout=60).json()
        status = full["test"]["status"]
        print(f"   poll {i}: {status}")
        if status in ("complete", "failed"):
            break
        time.sleep(POLL_EVERY_SEC)

    if status != "complete":
        print(f"E2E FAILED: final status={status}")
        sys.exit(1)

    sc = full["scores"][0]
    print("6 winner:", full["test"]["winner_variant_id"],
          "| signals[0]:", sc.get("signals"), "| curve len:", len(sc["engagement"]))

    r = requests.post(f"{base}/tests/{tid}/explain", headers=H, timeout=300)
    first = list(r.json()["explanations"].values())[0][:2]
    print("7 explain:", first)

    r = requests.get(f"{base}/tests/{tid}/tips", headers=H, timeout=300)
    print("8 tips:", r.json()["tips"][:140])
    print("E2E PASSED")


if __name__ == "__main__":
    main()
