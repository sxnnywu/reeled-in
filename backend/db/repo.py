"""Persistence layer. Owner: C (Seb).

MongoRepo (PyMongo Async) when MONGODB_URI is set; MemoryRepo (db/store.py dicts)
otherwise — same async interface, so routes are identical in both modes and
teammates without an .env still get a fully working API on fake persistence.

Wire <-> Mongo mapping (CONTRACTS §4): the wire `id` is stored as Mongo `_id`.
Score docs store the full Score Object (§3) + test_id/created_at; reads return
the §3 wire shape.
"""
import os

from backend.db import store
from backend.util import new_id, now_iso


def winner_pipeline(test_id: str, objective: str) -> list:
    """Server-side winner selection (CONTRACTS §5: max metrics[objective]).

    Shared by MongoRepo (async) and the GPU writer in modal_app (sync pymongo).
    Deterministic tie-break on variant_id. PERSON_C_PLAN §5.1 — 8.0-compatible.
    """
    return [
        {"$match": {"test_id": test_id}},
        {"$addFields": {"obj_score": {"$getField": {"field": objective, "input": "$metrics"}}}},
        {"$sort": {"obj_score": -1, "variant_id": 1}},
        {"$limit": 1},
        {"$project": {"_id": 0, "variant_id": 1, "obj_score": 1}},
    ]


def _score_doc(test_id: str, score_obj: dict) -> dict:
    """ScoreObject (§3) -> scores doc (§4). Stable _id per variant => idempotent re-score."""
    return {
        "_id": "score_" + score_obj["variant_id"].removeprefix("var_"),
        "test_id": test_id,
        **score_obj,
        "created_at": now_iso(),
    }


def _score_wire(doc: dict) -> dict:
    """scores doc -> ScoreObject (§3)."""
    return {k: v for k, v in doc.items() if k not in ("_id", "test_id", "created_at")}


class MongoRepo:
    def _db(self):
        from backend.db.mongo import db

        return db()

    # --- tests ---
    async def insert_test(self, test: dict) -> None:
        doc = dict(test)
        doc["_id"] = doc.pop("id")
        await self._db().tests.insert_one(doc)

    async def get_test(self, test_id: str):
        doc = await self._db().tests.find_one({"_id": test_id})
        if doc is None:
            return None
        doc["id"] = doc.pop("_id")
        return doc

    async def update_test(self, test_id: str, fields: dict) -> None:
        await self._db().tests.update_one({"_id": test_id}, {"$set": fields})

    async def list_tests(self, user_id: str) -> list:
        out = []
        cursor = self._db().tests.find({"user_id": user_id}).sort("created_at", -1)
        async for doc in cursor:
            doc["id"] = doc.pop("_id")
            out.append(doc)
        return out

    # --- variants ---
    async def insert_variant(self, variant: dict) -> None:
        doc = dict(variant)
        doc["_id"] = doc.pop("id")
        await self._db().variants.insert_one(doc)

    async def get_variant(self, variant_id: str):
        doc = await self._db().variants.find_one({"_id": variant_id})
        if doc is None:
            return None
        doc["id"] = doc.pop("_id")
        return doc

    async def variants_for(self, test: dict) -> list:
        """In test.variant_ids order."""
        docs = {}
        async for doc in self._db().variants.find({"test_id": test["id"]}):
            doc["id"] = doc.pop("_id")
            docs[doc["id"]] = doc
        return [docs[v] for v in test["variant_ids"] if v in docs]

    # --- scores ---
    async def upsert_score(self, test_id: str, score_obj: dict) -> None:
        doc = _score_doc(test_id, score_obj)
        await self._db().scores.replace_one({"variant_id": score_obj["variant_id"]}, doc, upsert=True)

    async def scores_for(self, test: dict) -> list:
        """ScoreObjects (§3), in test.variant_ids order."""
        docs = {}
        async for doc in self._db().scores.find({"test_id": test["id"]}):
            docs[doc["variant_id"]] = _score_wire(doc)
        return [docs[v] for v in test["variant_ids"] if v in docs]

    async def compute_winner(self, test_id: str, objective: str):
        # PyMongo Async: aggregate() is awaitable and yields the cursor.
        cursor = await self._db().scores.aggregate(winner_pipeline(test_id, objective))
        rows = await cursor.to_list(1)
        return rows[0]["variant_id"] if rows else None

    # --- users ---
    async def upsert_user(self, user: dict) -> None:
        await self._db().users.update_one(
            {"_id": user["id"]},
            {"$setOnInsert": {"email": user.get("email"), "display_name": user.get("display_name", ""),
                              "created_at": now_iso()}},
            upsert=True,
        )


class MemoryRepo:
    """Same interface over db/store.py dicts (no Atlas needed)."""

    async def insert_test(self, test: dict) -> None:
        store.TESTS[test["id"]] = test

    async def get_test(self, test_id: str):
        return store.TESTS.get(test_id)

    async def update_test(self, test_id: str, fields: dict) -> None:
        store.TESTS[test_id].update(fields)

    async def list_tests(self, user_id: str) -> list:
        mine = [t for t in store.TESTS.values() if t["user_id"] == user_id]
        return sorted(mine, key=lambda t: t["created_at"], reverse=True)

    async def insert_variant(self, variant: dict) -> None:
        store.VARIANTS[variant["id"]] = variant

    async def get_variant(self, variant_id: str):
        return store.VARIANTS.get(variant_id)

    async def variants_for(self, test: dict) -> list:
        return [store.VARIANTS[v] for v in test["variant_ids"] if v in store.VARIANTS]

    async def upsert_score(self, test_id: str, score_obj: dict) -> None:
        store.SCORES[score_obj["variant_id"]] = score_obj

    async def scores_for(self, test: dict) -> list:
        return [store.SCORES[v] for v in test["variant_ids"] if v in store.SCORES]

    async def compute_winner(self, test_id: str, objective: str):
        test = store.TESTS[test_id]
        scored = [(v, store.SCORES[v]["metrics"][objective])
                  for v in test["variant_ids"] if v in store.SCORES]
        if not scored:
            return None
        return sorted(scored, key=lambda kv: (-kv[1], kv[0]))[0][0]  # mirror pipeline tie-break

    async def upsert_user(self, user: dict) -> None:
        store.USERS.setdefault(user["id"], {**user, "created_at": now_iso()})


_repo = None


def repo():
    """Chosen once per process: Mongo when MONGODB_URI is set, else in-memory."""
    global _repo
    if _repo is None:
        _repo = MongoRepo() if os.environ.get("MONGODB_URI") else MemoryRepo()
    return _repo
