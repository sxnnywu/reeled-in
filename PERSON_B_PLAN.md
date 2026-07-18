# Person B — Data-Capture / "The Pipes" — Plan & Decisions

Share-out doc, mirrors `PERSON_C_PLAN.md`. What B owns, the tech decisions (with
2026 research), how it's implemented, the couplings to A/C/D, and the tracks B mans.

Source of truth: `SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `ARCHITECTURE_FLOW.md`.
The combined `workstreams/data-and-storage/PLAN.md` covers B **and** C; this doc is
the **capture half only** (per `PARALLEL_IMPLEMENTATION_PLAN.md`: B = pipes, C = insights).

---

## 1. What B owns (and explicitly does NOT)

B is the **ingestion + storage + live-feed layer**. Everything that gets data *into*
Mongo and *out* to the dashboard in real time.

**Own (files):**
- `backend/app/core/database.py` — Mongo client, DB handle, index creation
- `backend/app/services/event_collector.py` — validate + idempotent batch insert
- `backend/app/api/routes/events.py` — `POST /api/events`, `GET /api/runs/{run_id}/events`
- `backend/app/api/routes/sandboxes.py` — `GET /api/runs/{run_id}/sandboxes?state=`
- `backend/app/api/ws.py` — `WS /ws/runs/{run_id}` (fleet counts + sampled traffic)

**Do NOT own** (de-scoped so B and C don't collide):
- Aggregation pipelines / findings / report / vector clustering → **C** (already built in `analysis/`)
- `main.py`, shared models module, spec/run routes, loop runner, fake emitter → **A**
- Dashboard UI → **D**

**B's superpower: loop-agnostic.** B stores/forwards whatever contract-shaped events
arrive. The morning-triage-3-agent vs CI-triage-6-agent demo-target debate (see STATUS
handoff) **does not block B** — the `Event` shape is identical either way.

---

## 2. Tech decisions (researched, 2026-current — these UPDATE the docs)

### D1. Async driver = **PyMongo `AsyncMongoClient`**, NOT Motor
Motor was deprecated 2025-05-14; **EOL 2026-05-14 (already passed)**. MongoDB's current
recommendation is PyMongo's native async API (`pymongo.AsyncMongoClient`, pymongo ≥4.9).
Repo already pins `pymongo==4.10.1` → we get it for free. Same aggregation-pipeline dicts
C wrote work unchanged; call sites just `await`.
> Action: the docs (`CLAUDE.md`, `INTEGRATIONS_AND_STACK.md`, data-and-storage PLAN) say
> "Motor" — B updates those to "PyMongo async" and notes why. Talking point for the
> MongoDB track: *we used the current recommended async driver, not the deprecated one.*

### D2. `events` is a **regular collection, not Time Series**
Time Series collections **do not support change streams or unique indexes**. Our live
feed *is* a change stream and our contract (`§4`) requires unique `(run_id, sandbox_id, seq)`
for idempotency. Both are load-bearing; the ~90% TS storage win is irrelevant at MVP–1,000
scale. → **regular collection.**
> Action: this REVERSES ARCHITECTURE_FLOW decisions-log #3 (currently "time-series") and
> the `research/mongodb.md` §1 recommendation. B updates both + announces at the O↔D sync.

### D3. Change streams need a **replica set** → use **MongoDB Atlas** as the shared dev DB
Change streams don't run on a standalone `mongod`. C's `README_PERSON_C.md` starts plain
`mongo:7` (standalone) — fine for C's aggregations, **breaks B's WebSocket**. Two fixes:
- **Primary (recommended):** stand up **Atlas M0/M10** now (B owns Mongo provisioning in
  Phase 0). Atlas is a replica set out of the box → change streams work, and it's the
  MongoDB **sponsor track** surface. One `MONGODB_URI` in `.env`, whole team points at it.
- **Offline fallback:** local single-node replica set —
  `docker run -d -p 27017:27017 mongo:7 --replSet rs0` then `mongosh --eval "rs.initiate()"`.

### D4. Idempotent ingest = unique index + `insert_many(ordered=False)`
A's emitter is at-least-once (it may retry a batch after a network blip). The unique
`(run_id, sandbox_id, seq)` index makes storage **exactly-once**: insert unordered, catch
`BulkWriteError`, treat code-11000 duplicates as already-stored. `accepted = inserted_count`.
No dedup bookkeeping, the index does it.

---

## 3. How it's implemented (build order = the parallel-plan blocker order)

### Step 1 — `core/database.py`  (blocker #4, H0.5–1.5; unblocks A's event target + C's real handle)
```python
from pymongo import AsyncMongoClient
_client: AsyncMongoClient | None = None

async def connect():                     # called from A's FastAPI lifespan on startup
    global _client
    _client = AsyncMongoClient(os.environ["MONGODB_URI"])
    await ensure_indexes(get_db())

def get_db():                            # C swaps her local handle for this (one-line)
    return _client[os.environ.get("LOOPY_DB", "loopy")]

async def ensure_indexes(db):            # idempotent; safe to call every boot
    await db.events.create_index([("run_id",1),("sandbox_id",1),("seq",1)], unique=True)
    await db.events.create_index([("run_id",1),("type",1)])
    await db.sandbox_runs.create_index([("run_id",1),("sandbox_id",1)], unique=True)
    await db.sandbox_runs.create_index([("run_id",1),("state",1)])      # fleet snapshot
    await db.run_batches.create_index("run_id", unique=True)
    await db.reports.create_index("run_id", unique=True)                # C writes, B indexes
    await db.loop_specs.create_index("spec_id", unique=True)
```
Collections exactly per contract §4. **Index before scale-testing, never after.**

### Step 2 — collector: `event_collector.py` + `routes/events.py`  (blocker #6, H1.5–3)
`POST /api/events` body `{events: [...]}` → `{accepted: int}`:
1. Validate each event with the Pydantic `Event` model (`model_validate`). Invalid events
   are dropped + logged (not a 500). **Policy to confirm with A:** drop-bad-event vs
   reject-whole-batch — recommend drop-and-count.
2. `insert_many([e.model_dump() for e in valid], ordered=False)` — **plain `model_dump()`,
   NOT `mode="json"`**, so `ts` stays a BSON `datetime` (range queries + C's sorting need it).
3. Catch `BulkWriteError`; `accepted = result.inserted_count` (dups already stored).
4. **Update `sandbox_runs` from events** (see coupling §4-A): on `termination`, set
   `state` + `termination_reason` + `ended_at`; keep `iterations`/`total_tokens` current.
   *This is what feeds every number C computes — if nobody writes these, C's stats are empty.*

`GET /api/runs/{run_id}/events?sandbox_id=&type=&limit=` → filtered find, sort
`(sandbox_id, seq)`, **default `limit=200`** (never dump millions at 1,000×).

### Step 3 — `api/ws.py` : `WS /ws/runs/{run_id}`  (blocker #7, H2–4; unblocks D live views)
On connect → send **initial fleet snapshot** (aggregate `sandbox_runs` by `state`). Then
multiplex two change streams into the socket:
- `db.events.watch([{ "$match": {"operationType":"insert", "fullDocument.run_id": run_id} }])`
  → **sampled** `agent_message`s for the scrolling traffic feed (sample/rate-limit; do not
  forward all N×events to the browser).
- `db.sandbox_runs.watch([...run_id...])` → push **fleet-count deltas** on state changes.

Resilience: keep the **resume token** (`change["_id"]`); on WS drop, reconnect with
`resume_after=token` so no events are missed. Fallback if WS slips: D polls
`GET /api/runs/{run_id}` at `DASHBOARD_POLL_MS` (2000) — already in the contract.

### Step 4 — `routes/sandboxes.py`
`GET /api/runs/{run_id}/sandboxes?state=` → `list[SandboxRun]` (find + optional state filter).
Feeds D's fleet grid + sandbox detail.

### Step 5 — harden
Validation edge cases, WS reconnect, verify indexes are used (`explain`), scale-test 50→1,000,
tune batch-flush timing with A so the feed isn't laggy.

---

## 4. Couplings / handoffs (raise these at the syncs)

**← A (Orchestration):**
- **Who writes `sandbox_runs`?** Recommend: **A creates** the docs + owns `pending/
  provisioning/running`; **B's collector derives** terminal fields (`state`,
  `termination_reason`, `iterations`, `total_tokens`, `ended_at`) from events. Must be
  settled or C's math has no inputs. (This is the plan's open item "who marks a RunBatch complete.")
- A's `main.py` must call B's `database.connect()` in the FastAPI **lifespan** (one client
  per process; never per-request; never share across event loops).
- **Store `payload` verbatim** — C's Tier-2 reads keys *inside* it (`payload.verdict=="pass"`,
  `payload.must_pass_ok`, `payload.classified`). B must not strip/rename payload.
- Confirm event **batch flush timing** (`EVENT_BATCH_SIZE=25`) so the live feed isn't laggy.

**← C (Analysis):** C swaps her local Mongo handle for B's `get_db()` (one line). C reads
`sandbox_runs` (fields above) + `events`; confirm B's `reports` collection is writable by C.

**← D (Interface):** sign off **WebSocket message shapes** (fleet-snapshot msg, fleet-delta
msg, traffic-feed msg) before D wires live views. Poll fallback contract is `GET /api/runs/{run_id}`.

---

## 5. Sponsor tracks B mans

| Track | B's angle | Ship |
|---|---|---|
| **MongoDB Atlas (MLH)** — infra half | The whole ingest+live layer: current async driver (`AsyncMongoClient`), **idempotent bulk ingest** via unique index, index design, and **Change Streams → WebSocket** for a real-time (not polled) feed. C owns the analytics half (aggregation + Vector Search). Together = "we used Atlas well beyond CRUD." | database.py, collector, ws.py |

Not B's: Gemini/Backboard/Warp/Unifold (A), Base44/Auth0/ElevenLabs (D), analytics-side
Mongo + Solana (C). Rule holds: **declare only what's actually wired.**

---

## 6. Open decisions to surface
- [ ] Confirm PyMongo-async (D1) with team; update Motor references in docs.
- [ ] Confirm `events` = regular collection (D2); update ARCHITECTURE decisions-log #3 + research/mongodb.md.
- [ ] Atlas vs local replica set for the shared dev DB (D3) — recommend Atlas.
- [ ] sandbox_runs write ownership (§4-A) — the one that blocks C if unsettled.
- [ ] Validation policy: drop-event vs reject-batch — recommend drop-and-count.

---

## Living Status (update every session)
**Done:** —
**In progress:** plan drafted; decisions D1–D4 researched.
**Next:** Step 1 `core/database.py` (unblocks A + C).
**Handoff notes:** `events` is a REGULAR collection (not time-series) — required for change
streams + the unique index. Driver is PyMongo `AsyncMongoClient`, not Motor (Motor is EOL).
