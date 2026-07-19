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


async def seed(folder: str = "demo/precomputed", name: str = "Demo — Hook Battle",
               media_dir: str = "media", only: str = "") -> str:
    from backend.db.repo import repo
    from backend.util import new_id, now_iso

    files = sorted(Path(folder).glob("*.json"))
    if only:  # comma-separated stems, e.g. "IMG_7024,IMG_7025"
        wanted = {s.strip() for s in only.split(",")}
        files = [f for f in files if f.stem in wanted]
    if len(files) < 2:
        raise SystemExit(f"need >=2 Score Object JSONs in {folder}/ (found {len(files)})")

    r = repo()
    await r.upsert_user({"id": DEMO_USER, "email": "demo@reeledin.app", "display_name": "Demo"})

    now = now_iso()
    test = {
        "id": new_id("test"), "user_id": DEMO_USER, "type": "upload", "name": name,
        "status": "pending", "variant_ids": [],
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
            # media_dir: where the actual videos live on the Volume (e.g. media/eval)
            "media_key": f"{media_dir}/{variant_id}.mp4",
            "params": {"note": f"precomputed from {path.name}"},
            "created_at": now_iso(),
        })
        await r.upsert_score(test["id"], score_obj)
        variant_ids.append(variant_id)

    winner = await r.compute_winner(test["id"])
    await r.update_test(test["id"], {
        "variant_ids": variant_ids, "status": "complete",
        "winner_variant_id": winner, "updated_at": now_iso(),
    })
    print(f"seeded {test['id']}: {len(variant_ids)} variants, winner={winner}")
    return test["id"]


async def seed_docs(path: str = "demo/seed/demo_docs.json") -> None:
    """Upsert raw §4-shaped documents {users, tests, variants, scores} — e.g. D's
    hand-crafted demo set (curves are formula-consistent; winner from rank_scores).
    Requires Mongo mode. Usage: python -m backend.db.seed_demo --docs [path]"""
    from backend.db.mongo import db

    data = json.loads(Path(path).read_text())
    d = db()
    total = 0
    for coll in ("users", "tests", "variants", "scores"):
        for doc in data.get(coll, []):
            await d[coll].replace_one({"_id": doc["_id"]}, doc, upsert=True)
            total += 1
    print(f"seeded {total} docs from {path}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--docs" in sys.argv:
        asyncio.run(seed_docs(args[0] if args else "demo/seed/demo_docs.json"))
    else:
        def flag(name, default):
            return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
        asyncio.run(seed(
            args[0] if args else "demo/precomputed",
            name=flag("--name", "Demo — Hook Battle"),
            media_dir=flag("--media-dir", "media"),
            only=flag("--only", ""),
        ))
