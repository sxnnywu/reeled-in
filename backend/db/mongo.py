"""MongoDB Atlas via PyMongo Async (Motor is deprecated — PERSON_C_PLAN §7). Owner: C (Seb).

One AsyncMongoClient per container (module-global, lazy), pool tuned for serverless:
small max pool, fail fast on server selection, drop idle sockets. Never create a
client per request. Collections: users, tests, variants, scores.
"""
import asyncio
import os

from pymongo import AsyncMongoClient

# AsyncMongoClient binds to the event loop it was created on — cache one client
# per loop. In production (uvicorn / Modal ASGI) there is exactly one loop, so
# this is the single shared client; under test harnesses that spin extra loops
# it prevents cross-loop reuse crashes.
_clients: dict[int, AsyncMongoClient] = {}


def db():
    loop_id = id(asyncio.get_running_loop())
    client = _clients.get(loop_id)
    if client is None:
        client = AsyncMongoClient(
            os.environ["MONGODB_URI"],
            maxPoolSize=5,
            minPoolSize=0,
            serverSelectionTimeoutMS=5000,
            maxIdleTimeMS=10000,
        )
        _clients[loop_id] = client
    return client[os.environ.get("MONGODB_DB", "reeled_in")]


async def ensure_indexes():
    """Run once on startup (main.py lifespan). Index before scale, never after."""
    d = db()
    await d.tests.create_index([("user_id", 1), ("created_at", -1)])  # /history
    await d.variants.create_index("test_id")
    await d.scores.create_index("test_id")
    await d.scores.create_index("variant_id", unique=True)


async def close():
    client = _clients.pop(id(asyncio.get_running_loop()), None)
    if client is not None:
        await client.close()
