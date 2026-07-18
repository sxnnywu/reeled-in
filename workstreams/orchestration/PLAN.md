# Orchestration Workstream — Execution Plan

Source of truth priority: `SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `ARCHITECTURE_FLOW.md`.

Non-negotiable contract rules:
- It is `run_id` everywhere, never `batch_id`
- Do not rename event fields or `SandboxState` values
- Do not change API paths after the frontend starts

## Scope

You own:
- FastAPI app scaffold + config
- Loop-spec ingestion (`POST /api/specs` inline + `POST /api/specs/ingest` for GitHub/folder)
- Fan-out controller + sandbox lifecycle (`POST /api/runs`, `GET /api/runs/{run_id}`)
- Sandbox substrate integration (once decided)
- The loop runner that executes a `LoopSpec` inside a sandbox
- Event emission (batched, conforming to `Event` schema)
- The demo loop (Layer 1): the **morning-triage** 6-agent CI-triage loop — Gemini agents + Backboard memory are that loop's choices, not Loopy platform requirements
- Instrumentation adapter: wraps the loop and records all agent I/O as contract-shaped Events, model-agnostically

You do not own:
- Mongo aggregations/analysis, report generation, collector internals, dashboard

## Deliverables (paths)

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/services/spec_ingestion.py`
- `backend/app/services/fanout_controller.py`
- `backend/app/services/loop_runner.py`
- `backend/app/services/event_emitter.py`
- `backend/app/api/routes/specs.py` (POST /api/specs + POST /api/specs/ingest)
- `backend/app/api/routes/runs.py`
- `backend/app/services/oracle.py`
- `backend/scripts/fake_emitter.py` (streaming HTTP fake emitter)
- `backend/examples/ci_triage_spec.json` (already committed)

## Step-by-Step

### Step 0: Decisions (blocking)
- [ ] Substrate decision: **asyncio for MVP** — already decided, log it in ARCHITECTURE_FLOW.md so no one re-litigates
- [ ] Lock SHARED_CONTRACTS open items with the team (topology edge shape, termination shape, seed_strategy enum — all already resolved in ci_triage_spec.json; officially adopt them)
- [ ] Confirm push-model event capture with Data & Storage

### Step 1: Stubs (target: first 45 min of build)
- [ ] FastAPI scaffold with route shells at final paths
- [ ] `LoopSpec`, `RunBatch`, `SandboxRun`, `Event` Pydantic models copied verbatim from contracts
- [ ] `loop_runner.run(spec, seed) -> SandboxRun` stub committed

### Step 2: Real implementation
- [ ] Spec ingestion + validation
- [ ] Fan-out controller with lifecycle state machine + infra-only retries
- [ ] Loop runner executing topology with Gemini agents
- [ ] Backboard.io state layer inside loops (`state_update` events)
- [ ] Batched event emission (EVENT_BATCH_SIZE)
- [ ] Oracle checker (`oracle.py`) for must_pass / must_not_touch verification
- [ ] Morning-triage seed library variation (identical vs varied, ~10 archetypes)
- [ ] A/B evaluator knob (weak vs strong evaluator model — Phase 3)

### Step 3: Scale
- [ ] 50 concurrent sandboxes stable
- [ ] 100+, then stretch toward 1,000

## Confirm with Data & Storage
- [ ] Collector endpoint ready before first real run
- [ ] Event validation errors: reject batch or drop event?

## Confirm with Interface
- [ ] Fleet state counts shape in `GET /api/runs/{run_id}`

## Risks
- [ ] Do not block on substrate decision — build runner substrate-agnostic
- [ ] Do not retry behavioral failures (they are the product)
- [ ] Do not let example-loop code leak into platform code

## Success Criteria
- [ ] One API call triggers a ≥50-sandbox run and events flow to Mongo

---

## Living Status (update every session)

**Done:** —
**In progress:** —
**Next:** Step 0 decisions
**Handoff notes:** —
