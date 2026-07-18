"""MongoDB Atlas via PyMongo Async (Motor is deprecated — PERSON_C_PLAN §7). Owner: C (Seb).

One AsyncMongoClient per container (module-global, lazy), pool tuned for serverless:
small max pool, fail fast on server selection, drop idle sockets. Never create a
client per request. Collections: users, tests, variants, scores.
"""
import os

from pymongo import AsyncMongoClient

_client: AsyncMongoClient | None = None


def db():
    global _client
    if _client is None:
        _client = AsyncMongoClient(
            os.environ["MONGODB_URI"],
            maxPoolSize=5,
            minPoolSize=0,
            serverSelectionTimeoutMS=5000,
            maxIdleTimeMS=10000,
        )
    return _client[os.environ.get("MONGODB_DB", "reeled_in")]


async def ensure_indexes():
    """Run once on startup (main.py lifespan). Index before scale, never after."""
    d = db()
    await d.tests.create_index([("user_id", 1), ("created_at", -1)])  # /history
    await d.variants.create_index("test_id")
    await d.scores.create_index("test_id")
    await d.scores.create_index("variant_id", unique=True)


async def close():
    global _client
    if _client is not None:
        await _client.close()
        _client = None
