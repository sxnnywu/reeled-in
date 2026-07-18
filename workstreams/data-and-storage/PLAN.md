# Data & Storage Workstream — Execution Plan

Source of truth priority: `SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `ARCHITECTURE_FLOW.md`.

Non-negotiable contract rules:
- Collections and indexes exactly as contracts §4
- `Event` shape is sacred — analysis assumes it
- `GET /api/runs/{run_id}/report` returns 404 until ready, never a partial

## Scope

You own:
- MongoDB setup (PyMongo `AsyncMongoClient`, pymongo ≥4.9 — Motor is EOL), collections, indexes
- Event collector (`POST /api/events`) with schema validation
- Query routes (`/sandboxes`, `/events`) + WebSocket `/ws/runs/{run_id}`
- Aggregation pipelines: completion rate, stall detection, iteration histogram, divergence, token/cost stats, per-handoff failure rates
- Failure clustering + Gemini-summarized `Finding`s
- Report assembly

You do not own:
- Sandbox lifecycle, loop runner, example loops, dashboard UI

## Deliverables (paths)

- `backend/app/core/database.py`
- `backend/app/services/event_collector.py`
- `backend/app/services/analysis/pipelines.py`
- `backend/app/services/analysis/clustering.py`
- `backend/app/services/report_builder.py`
- `backend/app/api/routes/events.py`
- `backend/app/api/routes/reports.py`
- `backend/app/api/ws.py`

## Step-by-Step

### Step 1: Stubs (first 45 min)
- [ ] Mongo connection + collections + indexes per contracts §4
- [ ] Collector route shell accepting `{events: [...]}` → `{accepted: n}`
- [ ] Report route shell (404)

### Step 2: Real implementation
- [ ] Collector with Pydantic validation + batch insert
- [ ] WebSocket: fleet state counts + sampled event stream
- [ ] Pipelines (deterministic stats first)
- [ ] Stall detector (STALL_WINDOW no-progress signature)
- [ ] Divergence metric for identical-seed control pairs
- [ ] Failure clustering → Gemini summarization → `Finding`s
- [ ] Report assembly + persistence

### Step 3: Nice-to-have
- [ ] (none currently — Solana cut)

## Confirm with Orchestration
- [ ] Event batch flush timing (so live feed isn't laggy)
- [ ] Who marks a `RunBatch` complete

## Confirm with Interface
- [ ] WebSocket message shapes
- [ ] Report JSON final before report-view UI starts

## Risks
- [ ] Do not run analysis on unvalidated events
- [ ] Do not let LLM findings replace deterministic stats — LLM narrates, math decides
- [ ] Index before scale testing, not after

## Success Criteria
- [ ] Real findings + a generated report from a completed ≥50-sandbox batch

---

## Living Status (update every session)

**Done (analysis half / Person C):** Tier-1 pipelines + Tier-2 answer-key checks in `backend/app/services/analysis/`; verified vs local Mongo with seeded fake run (80 sandboxes).
**In progress:** —
**Next:** findings generator → report_builder → routes/reports.py; (capture half) Step 1 stubs still open.
**Handoff notes:** pipelines take any pymongo-style db handle — swap in core/database.py when it lands. Runner must emit `classified` / `verdict` / `must_pass_ok` payload keys for Tier 2.
