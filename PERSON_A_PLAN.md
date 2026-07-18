# Person A — Orchestration / Platform Spine — Plan

Source-of-truth precedence: `SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `PARALLEL_IMPLEMENTATION_PLAN.md`.
This doc is scheduling and specifics on top of those — it never overrides a contract.

---

## 1. Role summary

You are the platform spine. The whole team runs on your scaffold, your models, and — critically — your **streaming fake emitter**. B, C, and D cannot build real logic until contract-shaped events are flowing into Mongo. Your job, in order:

1. Stand up the FastAPI scaffold + route shells (H0.5–H1)
2. Build the streaming fake emitter — unblock the team (H1–H2) ← **do this before touching the real runner**
3. Build the real morning-triage loop runner + fan-out (H2–H20)
4. Swap fake → real in Phase 3 (H20+)

**The two-layer model (keep this in mind always):**
- **Layer 1 (your territory):** the morning-triage demo loop itself — its Gemini agents, its Backboard state-file memory, its event instrumentation. This is the demo loop's choice, not a Loopy platform requirement, and it's swappable.
- **Layer 2 (C's territory):** Loopy's QA infrastructure — Gemini as the analysis model, Backboard as longitudinal QA memory per `spec_id`. You don't own this layer; just make sure your events are clean so C can build on them.

---

## 2. What's already in the repo (use it, don't re-create)

| File | Status | Notes |
|---|---|---|
| `backend/app/models.py` | Exists (C's mirror) | Byte-for-byte copy of SHARED_CONTRACTS including new shapes (`LoopSource`, `SkillRef`, `ConnectorRef`, `QaMemory`). **You own the canonical version.** Formalize it in place — C imports from this path. |
| `backend/examples/ci_triage_spec.json` | Exists (drafted by C) | Full 6-agent LoopSpec for the morning-triage loop. Use as-is. |
| `backend/scripts/seed_ci_triage_run.py` | Exists | **Bulk-insert seeder** — writes fake events directly to Mongo. Read this before writing the streaming fake emitter to match payload shapes exactly. Your fake emitter is the streaming HTTP version. |
| `backend/requirements.txt` | Exists | Already has fastapi, uvicorn, pymongo, pydantic, google-generativeai, httpx. |
| `backend/.env.example` | Exists | Shows all required keys. |

---

## 3. Your deliverables (file paths)

```
backend/
  app/
    main.py                          <- FastAPI app, mounts routers, lifespan
    core/
      __init__.py
      config.py                      <- Settings (env vars), one import for everyone
    api/
      __init__.py
      routes/
        __init__.py
        specs.py                     <- POST /api/specs + POST /api/specs/ingest
        runs.py                      <- POST /api/runs, GET /api/runs/{run_id}
    services/
      spec_ingestion.py              <- parse + normalize LoopSpec, write to loop_specs
      fanout_controller.py           <- N concurrent sandbox tasks, lifecycle FSM
      loop_runner.py                 <- executes morning-triage inside one sandbox
      event_emitter.py               <- batched POST to /api/events (EVENT_BATCH_SIZE=25)
      oracle.py                      <- deterministic checker (must_pass / must_not_touch)
  scripts/
    fake_emitter.py                  <- MASTER UNBLOCKER: streaming HTTP version of seed_ci_triage_run.py
  examples/
    ci_triage_spec.json              <- already done
```

Optional (Phase 3, Unifold track only, only if runner is stable):
```
  examples/
    payments_loop_spec.json          <- second registered spec, proves Loopy is domain-agnostic
```

---

## 4. Step-by-step (in priority order)

### Step 0 — Decisions (H0, first 30 min with the team)

- [ ] Lock `SHARED_CONTRACTS.md` open items. Most are already resolved in existing files; officially adopt them:
  - Topology edge shape: `{"from_agent": str, "to_agent": str, "condition": str}` (already in ci_triage_spec.json)
  - Termination shape: `{"max_iterations": int, "goal_check": str}` (already in ci_triage_spec.json)
  - `seed_strategy` enum: `"identical" | "varied"` (already in models.py)
  - New LoopSpec fields (`source`, `skills`, `connectors`) — confirm shapes with D for the spec-registration form
- [ ] Log substrate decision in ARCHITECTURE_FLOW.md decisions table: **asyncio for MVP** (already decided — just record it)
- [ ] Provision API keys: Gemini + Backboard (you); Mongo Atlas URI (B)

### Step 1 — Scaffold + route shells (H0.5–H1)

Goal: B, C, D can import your models and know the API paths are final.

- [ ] `backend/app/core/config.py` — `Settings` (pydantic-settings): `MONGODB_URI`, `GEMINI_API_KEY`, `BACKBOARD_API_KEY`, `EVENT_COLLECTOR_URL` (default `http://localhost:8000`). One singleton `get_settings()`.
- [ ] `backend/app/main.py` — `FastAPI` app with lifespan (open/close Mongo client). Mount routers at `/api/specs` and `/api/runs`.
- [ ] `backend/app/api/routes/specs.py` — two route shells:
  - `POST /api/specs` — inline paste: accepts LoopSpec body, writes to `loop_specs`, returns LoopSpec
  - `POST /api/specs/ingest` — GitHub/folder path: accepts `{kind, ref}` body, calls spec_ingestion normalizer, returns LoopSpec. Stub for now; real normalizer in Step 3a.
- [ ] `backend/app/api/routes/runs.py` — route shells:
  - `POST /api/runs` — accepts `{spec_id, n_sandboxes, seed_strategy}`, creates RunBatch in `run_batches`, spawns fan-out as background task, returns RunBatch
  - `GET /api/runs/{run_id}` — returns RunBatch + per-state sandbox counts (confirm shape with D at H2 sync — see §5)
- [ ] Announce to the team: scaffold is up, routes are at their final paths.

### Step 2 — Streaming fake emitter (H1–H2) — DO THIS BEFORE THE REAL RUNNER

The bulk seeder (`seed_ci_triage_run.py`) writes events directly to Mongo. Build a **streaming HTTP version** that POSTs to B's collector on a timer — so B can test the collector + WebSocket in real time.

**Read `seed_ci_triage_run.py` first.** Match its payload shapes and planted clusters exactly.

**What `scripts/fake_emitter.py` must do:**
- CLI: `python -m scripts.fake_emitter --n-sandboxes 80 [--run-id UUID]`
- POST a RunBatch to `POST /api/runs` (or write directly to Mongo if B's route isn't live — confirm with B)
- For each sandbox, stream Events via `POST /api/events` in batches of 25, with `asyncio.sleep(0.05)` between batches so B's WebSocket sees real-time flow:
  - `loop_iteration` events (3–30 per sandbox)
  - `agent_message` events: `from_agent` / `to_agent` matching the morning-triage topology
  - `tool_call` + `tool_result` events
  - `state_update` events (Backboard memory writes — Layer-1 state persistence)
  - `termination` event with `reason` in payload
- Plant the two stall clusters C needs (same as the bulk seeder):
  - Cluster 1 (misroute ping-pong, ~30% of sandboxes): `triage_agent -> infra_fixer -> triage_agent -> infra_fixer ...` ending in `stall_detected`
  - Cluster 2 (reject ping-pong, ~10%): `dep_fixer -> evaluator -> dep_fixer -> evaluator ...` ending in `stall_detected`
- Include Tier-2 payload keys in relevant agent_messages (see §6)

- [ ] Fake emitter works end-to-end against B's collector
- [ ] Announce to the team: fake events are flowing. B, C, D: you're unblocked.

### Step 3 — Real services (H2–H20)

Work in order; each is a prereq for the next.

#### 3a. Spec ingestion (`spec_ingestion.py`)

- [ ] `ingest_inline(raw: dict) -> LoopSpec` — validate with Pydantic, upsert into `loop_specs`. Source field: `LoopSource(kind="inline")`.
- [ ] `ingest_from_ref(kind: str, ref: str) -> LoopSpec` — MVP: for known layouts (e.g. Claude Code `.claude/` skills structure), map to LoopSpec; others return error directing user to inline paste. The LoopSpec **references** the user's agents/skills/connectors — never re-implements them.
- [ ] Reject specs with missing required agents or malformed topology edges.

#### 3b. Event emitter (`event_emitter.py`)

- [ ] `EventEmitter(run_id, sandbox_id, collector_url)` class
- [ ] `emit(events: list[Event])` — batches at `EVENT_BATCH_SIZE=25`, POSTs to `/api/events`, retries once on 5xx
- [ ] `emit_one(event: Event)` — convenience wrapper

#### 3c. Oracle checker (`oracle.py`)

- [ ] `OracleChecker(seed_input: dict)` — initialized with the sandbox's seed_input (carries the answer key: `true_kind`, `must_pass`, `must_not_touch`)
- [ ] `check_fix(fix_result: dict) -> dict` — returns `{"must_pass_ok": bool, "must_not_touch_ok": bool}`. This is the deterministic test runner we own — not a real test suite.
- [ ] The evaluator agent calls this oracle; result goes into `tool_result` payload and into the evaluator's `agent_message` payload as `must_pass_ok`.

#### 3d. Loop runner (`loop_runner.py`)

- [ ] `run_sandbox(spec: LoopSpec, sandbox_id: str, seed_input: dict, emitter: EventEmitter) -> SandboxRun`
  - Execute the morning-triage topology: call each Gemini agent in turn, respect `from_agent/to_agent/condition` edges
  - Emit `loop_iteration` at each tick boundary
  - Emit `agent_message` for every agent-to-agent hand-off (include Tier-2 payload keys — see §6)
  - Emit `tool_call` + `tool_result` for each tool invocation (oracle checker result goes here)
  - Emit `state_update` when writing to Backboard memory (Layer-1 state persistence per sandbox_id)
  - Emit `termination` when done (`reason` in payload)
  - Stall detection: `STALL_WINDOW=5` iterations with no state progress -> terminate with `stall_detected`
  - Return `SandboxRun` with final state + termination_reason + total_tokens

**Gemini integration (Layer 1 — the demo loop's model choice):**
- SDK: `google-generativeai`. Models: `gemini-2.0-flash-lite` for ci_monitor/triage_agent; `gemini-2.0-flash` for fixers + evaluator.
- Tool stubs: `read_ci_runs`, `read_ci_logs`, `worktree`, `run_tests` return plausible fake output. The oracle checker IS the real `run_tests` implementation.
- Each agent invocation = one Gemini call. Parse response to determine next routing edge.
- **A/B evaluator knob (Phase 3):** make `evaluator.model` configurable at run time. Weak = `gemini-2.0-flash`; Strong = `gemini-2.0-pro` or stricter prompt. Demo shows: "Strong evaluator cut the nod rate and stalls, at higher token cost."

**Backboard integration (Layer 1 — the demo loop's persistence move):**
- Use Backboard API to persist loop state *per sandbox_id* across iterations.
- Store: current finding assignment (which specialist has it), bounce history, iteration count.
- Emit `state_update` events for every Backboard write.
- If Backboard key is missing: fall back to in-memory dict, log warning — don't break the runner.
- **Critical distinction:** this is Layer-1 Backboard (per sandbox_id, the loop's own memory). Layer-2 Backboard (longitudinal QA memory per spec_id) is C's territory — you don't touch that.

#### 3e. Fan-out controller (`fanout_controller.py`)

- [ ] `run_batch(batch: RunBatch, spec: LoopSpec) -> None` (FastAPI background task)
- [ ] Spawn `n_sandboxes` asyncio tasks, each calling `run_sandbox`
- [ ] Lifecycle FSM per sandbox: `pending -> provisioning -> running -> {completed | failed | stalled | timed_out}`
- [ ] Write **active** state transitions to `sandbox_runs`: A creates the doc (`state=pending`) and updates through `running`. **Terminal state fields (`state`, `termination_reason`, `ended_at`, `total_tokens`, `iterations`) are written by B's collector when it processes `termination` events — do NOT double-write these from the fan-out controller.**
- [ ] Mark `RunBatch.state = "completed"` (or `"failed"`) when all sandboxes finish — coordinate with B on who fires this (recommend: A's background task polls sandbox_runs counts via a Mongo query when all tasks return)
- [ ] Seed strategy:
  - `"identical"` — all sandboxes get the same `seed_input` object. **Identical `seed_input` = control group for C's divergence metric. This is a contract. Enforce it exactly.**
  - `"varied"` — rotate through the morning-triage archetype library (~10 incident archetypes)
- [ ] Cap concurrency at `DEFAULT_FLEET_SIZE_MVP=50` with an asyncio semaphore; scale in Phase 3

### Step 4 — Scale + real swap (H20–H32)

- [ ] Increase semaphore: 50 -> 100 -> 1,000
- [ ] Tune batch flush timing with B: confirm 25-event batches don't lag the WebSocket
- [ ] Swap fake emitter for the real morning-triage runner: confirm real events pass C's schema validation
- [ ] Wire the A/B evaluator knob: two parallel fleets (weak vs strong evaluator); D shows the diff in the dashboard
- [ ] Full demo path: `POST /api/runs` -> 80 sandboxes -> events flow -> C's report generates -> D's dashboard shows it live

### Step 5 — Unifold payments loop (Phase 3, optional, only if runner is stable)

- [ ] `backend/examples/payments_loop_spec.json` — small 3–4 agent payments loop LoopSpec (payer, receiver, reconciler, evaluator). Register it as a second spec to prove Loopy is domain-agnostic.
- No real runner needed; just register the spec. This earns the Unifold track.

---

## 5. API routes — exact shapes (LOCKED)

From `SHARED_CONTRACTS.md §5`. Do not rename paths.

```
POST /api/specs              body: LoopSpec (sans spec_id)                   -> LoopSpec
POST /api/specs/ingest       body: {kind: LoopSourceKind, ref: str}          -> LoopSpec (normalized)
POST /api/runs               body: {spec_id, n_sandboxes, seed_strategy}     -> RunBatch
GET  /api/runs/{run_id}      ->  RunBatch + sandbox state counts
```

`GET /api/runs/{run_id}` extended response shape (confirm with D at H2 sync):
```json
{
  "run_id": "...",
  "spec_id": "...",
  "n_sandboxes": 80,
  "seed_strategy": "identical",
  "state": "running",
  "created_at": "...",
  "sandbox_counts": {
    "pending": 0, "provisioning": 0, "running": 45,
    "completed": 30, "failed": 2, "stalled": 3, "timed_out": 0
  }
}
```

---

## 6. Payload contracts (what C's Tier 2 depends on you for)

Both the fake emitter and the real runner must emit these payload keys. Match `seed_ci_triage_run.py` exactly.

| Event type | from_agent | Required payload keys |
|---|---|---|
| `agent_message` | `triage_agent` | `classified: "flaky_test" or "infra" or "regression" or "dependency"` |
| `agent_message` | `evaluator` | `verdict: "PASS" or "REJECT"`, `must_pass_ok: bool` |
| `tool_result` | any (oracle call) | `must_pass_ok: bool`, `must_not_touch_ok: bool` |

**Divergence convention:** `"identical"` seed strategy -> all sandboxes get the exact same `seed_input` dict. Two sandboxes sharing the same `seed_input.incident_id` are a control pair. C computes divergence as the rate at which control pairs reach different termination states.

**Seed input shape** (match `seed_ci_triage_run.py`):
```json
{
  "incident_id": "...",
  "failure_kind": "flaky_test",
  "incident": "auth test flaky on retry",
  "answer_key": {
    "true_kind": "flaky_test",
    "must_pass": ["test_auth"],
    "must_not_touch": ["billing.py"]
  }
}
```

---

## 7. What A needs from others

| Need | From | When |
|---|---|---|
| `POST /api/events` collector live | B | Before first real events — fake emitter can write directly to Mongo as stopgap |
| Mongo Atlas URI in `.env` | B | Phase 0 |
| `core/database.py` connection helper | B | Step 1 — import it, don't duplicate |
| Sign-off on `GET /api/runs/{run_id}` shape | D | H2 sync |
| Event batch validation-error policy (reject batch vs drop event) | B | H1 sync |
| Gemini API key | Provision yourself | Phase 0 |
| Backboard API key | Provision yourself | Phase 0 |

---

## 8. Risks + mitigations

| Risk | Mitigation |
|---|---|
| Real runner takes longer than H20 | Fake emitter means the demo works regardless — C's pipelines + D's dashboard are already validated against it |
| Gemini latency at 80-concurrent | asyncio + semaphore; Gemini calls are I/O-bound so concurrency helps a lot |
| Backboard API is flaky | In-memory dict fallback; `state_update` events still emit correctly |
| Layer-1 vs Layer-2 confusion for Gemini/Backboard | Read ARCHITECTURE_FLOW.md: Layer-1 = demo loop's choices (swappable); Layer-2 = Loopy's QA infra (C owns) |
| Someone renames a field | All code imports from `backend/app/models.py` (mirrors SHARED_CONTRACTS); a rename causes a Pydantic validation error immediately |

---

## 9. Living status (update every session)

**Done:** —
**In progress:** —
**Next:** Step 0 decisions (H0 team sync), then scaffold + streaming fake emitter
**Handoff notes:**
