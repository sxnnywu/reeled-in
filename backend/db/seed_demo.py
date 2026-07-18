"""Seed precomputed demo scores into Mongo — the bulletproof no-GPU demo path. Owner: C (+B).

Usage:
  # 1. pull B's precomputed Score Objects off the Modal volume (or use demo/precomputed/)
  modal volume get reeled-in-cache precomputed demo/precomputed
  # 2. seed (reads backend/.env for MONGODB_URI)
  python -m backend.db.seed_demo [dir=demo/precomputed] [--name "Demo — Hook Battle"]

Creates one complete `upload` test for the demo user from every *.json Score
Object in the folder, with variants labelled A, B, C..., the winner computed via
the shared aggregation pipeline, and status=complete — so the live demo's
GET /tests/{id} and /history need zero GPU work.
"""
import asyncio
import json
import string
import sys
from pathlib import Path

DEMO_USER = "usr_demo00000000"


async def seed(folder: str = "demo/precomputed", name: str = "Demo — Hook Battle") -> str:
    from backend.db.repo import repo
    from backend.util import new_id, now_iso

    files = sorted(Path(folder).glob("*.json"))
    if len(files) < 2:
        raise SystemExit(f"need >=2 Score Object JSONs in {folder}/ (found {len(files)})")

    r = repo()
    await r.upsert_user({"id": DEMO_USER, "email": "demo@reeledin.app", "display_name": "Demo"})

    now = now_iso()
    test = {
        "id": new_id("test"), "user_id": DEMO_USER, "type": "upload", "name": name,
        "objective": "retention", "status": "pending", "variant_ids": [],
        "winner_variant_id": None, "created_at": now, "updated_at": now,
    }
    await r.insert_test(test)

    variant_ids = []
    for i, path in enumerate(files):
        score_obj = json.loads(path.read_text())
        variant_id = score_obj.get("variant_id") or new_id("var")
        score_obj["variant_id"] = variant_id
        await r.insert_variant({
            "id": variant_id, "test_id": test["id"],
            "label": string.ascii_uppercase[i % 26],
            "media_key": f"media/{variant_id}.mp4",
            "params": {"note": f"precomputed from {path.name}"},
            "created_at": now_iso(),
        })
        await r.upsert_score(test["id"], score_obj)
        variant_ids.append(variant_id)

    winner = await r.compute_winner(test["id"], test["objective"])
    await r.update_test(test["id"], {
        "variant_ids": variant_ids, "status": "complete",
        "winner_variant_id": winner, "updated_at": now_iso(),
    })
    print(f"seeded {test['id']}: {len(variant_ids)} variants, winner={winner}")
    return test["id"]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    name = "Demo — Hook Battle"
    if "--name" in sys.argv:
        name = sys.argv[sys.argv.index("--name") + 1]
    asyncio.run(seed(args[0] if args else "demo/precomputed", name))
