# Parallel Implementation Plan — Loopy (4 People)

**Goal of this doc:** get four people building at once with the fewest blockers. It maps the real dependency graph, front-loads the tasks that unblock others, and lays out per-person swimlanes across the 36 hours.

Precedence: `SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `ARCHITECTURE_FLOW.md`. This plan is scheduling on top of those — it never overrides a contract.

---

## 1. The four roles

The existing repo has **three workstreams** but **four people**. The heaviest workstream (Data & Storage) has an internal *sequential* chain — capture must exist before analysis can run — so we split it across two people. That gives a clean 4-way split with the most parallelism.

| Person | Role | Workstream | Owns (files) |
|---|---|---|---|
|| **A** | Orchestration / platform spine | Orchestration | `main.py`, `core/config.py`, shared Pydantic models, `spec_ingestion.py`, `fanout_controller.py`, `loop_runner.py`, `event_emitter.py`, `routes/specs.py`, `routes/runs.py`, `examples/ci_triage_spec.json`, **streaming fake emitter** (`scripts/fake_emitter.py`) |
| **B** | Data-Capture / the pipes | Data & Storage (capture half) | `core/database.py`, `event_collector.py`, `routes/events.py`, query route `/sandboxes`, `api/ws.py` (WebSocket) |
| **C** | Data-Analysis / the insights | Data & Storage (analysis half) | `analysis/pipelines.py`, `analysis/clustering.py`, `report_builder.py`, `routes/reports.py` |
| **D** | Interface & Design / presenter | Interface & Design | Dashboard (fleet / traffic / report views), spec-registration form, design system, demo script, deck; nice-to-have ElevenLabs narration |

A, B, C are the three technical members; **D is the presenter/designer** (per `TEAM_DIVISION.md`) and pulls in whichever technical person is free for dashboard wiring in Phase 2 (C is the natural helper — see §5).

---

## 2. The one idea that unlocks everything: the fake event emitter

The slowest, riskiest task on the whole project is **A's real loop runner** (6 Gemini agents executing the morning-triage loop topology, fan-out, Backboard memory for state persistence). Almost everything downstream — B's collector/WebSocket, C's pipelines/findings/report, D's live feed and report view — needs *a stream of contract-shaped events to build against.*

If everyone waits for the real runner, the team serializes behind A. **Solution:** A builds a **streaming fake emitter** (`scripts/fake_emitter.py`) — generates `Event` documents (agent_message, tool_call, loop_iteration, termination incl. `stall_detected`, etc.) for a fake run and POSTs them to B's collector on a timer, including the deliberately planted stall clusters. (A bulk-insert seeder already exists at `backend/scripts/seed_ci_triage_run.py`; the streaming HTTP version is what A builds next.)

The moment fake events flow into Mongo, **B, C, and D are all unblocked in parallel** and can build and test their real logic against realistic data — while A goes off and builds the real runner separately. Then in Phase 3 you swap the fake source for the real morning-triage runner. This single decoupling is what turns a mostly-serial project into a mostly-parallel one.

> **Rule:** A builds scaffold + models + fake emitter *before* starting the real runner. Unblock the team first, then do your long pole.

---

## 3. Dependency graph (what blocks what)

```
[Contract lock] ──┬─► everyone (all real code; shapes are mockable before this)
                  │
[API keys .env] ──┴─► A (Gemini, Backboard), B (Mongo), C (Gemini)   ← provision in first 30 min

A: scaffold + shared models ──► B (collector typing), C (pipeline typing), D (TS types)
A: route shells (/specs,/runs) ─► D wiring (soft — D mocks first)
B: Mongo conn + collections ───► B collector, C pipelines, C report
B: collector /api/events LIVE ─► A real event emission end-to-end, fake emitter target
A: FAKE EMITTER ───────────────► B (test collector+WS), C (build pipelines), D (live feed+report)   ★ master unblocker
B: WebSocket shape ────────────► D live fleet + traffic wiring
C: pipelines ──► C clustering ──► C findings ──► C report ──► D report view (real)
A: real loop runner + morning-triage ─► real data (swap in for fake emitter in Phase 3)
```

**Decoupled on purpose (do NOT let these become blockers):**
- **Sandbox substrate decision** — build the runner substrate-agnostic (plain `asyncio` tasks for MVP). Real substrate is a Phase-3 swap, not a Phase-0 gate.
- **Interface vs live backend** — D builds every view against fake contract-shaped data first, so D is never blocked waiting for a real endpoint.
- **Real runner vs everything downstream** — broken by the fake emitter (§2).

---

## 4. Blockers register (front-load the top rows)

Ordered by how many people each unblocks. Get the top rows done *first*.

| # | Unblocker task | Owner | Who's blocked until it's done | Must be done by |
|---|---|---|---|---|
| 1 | Lock `SHARED_CONTRACTS` open items (`topology` edge shape, `termination` shape, `seed_strategy` enum) | Whole team | Everyone (all real logic) | H0–H0.5 |
| 2 | Provision API keys into `.env` (Mongo Atlas, Gemini, Backboard) | A + B split | A (loops), B (Mongo), C (findings) | H0–H0.5 |
| 3 | Repo scaffold + **shared Pydantic models module** + route shells at final paths | A | B, C, D (all import/wire against these) | H0.5–H1 |
| 4 | Mongo connection + collections + indexes + collector route *shell* | B | A (event target), C (reads) | H0.5–H1.5 |
| 5 | **Fake event emitter** POSTing contract-shaped events (w/ planted stall) | A | B, C, D (all downstream build/test) | H1–H2 |
| 6 | Collector `/api/events` real (validate + batch insert) | B | Real + fake events actually land | H1.5–H3 |
| 7 | WebSocket `/ws/runs/{run_id}` shape (fleet counts + sampled events) | B | D (live views wiring) | H2–H4 |
| 8 | Deterministic pipelines return numbers from Mongo | C | D (real stats charts), report | H3–H6 |
| 9 | Report JSON assembled + `/report` returns real doc | C | D (real report view) | H8–H12 |
| 10 | Real morning-triage loop runner produces real events | A | Real demo data (swap out fake) | H8–H14 |

Everything not in this table can happen whenever — it blocks no one.

---

## 5. Phased timeline (swimlanes)

Hours are relative to build start (H0 = 9:30 PM Fri). Bands are approximate; the point is the *ordering and hand-offs*, not exact clocks.

### Phase 0 — Contracts + provisioning (H0–H1) · whole team together
- **All:** 20–30 min at a whiteboard to lock the `TODO(lock)` items in `SHARED_CONTRACTS` (topology edge `{from_agent, to_agent, condition}`, termination `{max_iterations, goal_check}`, `seed_strategy` = `"identical" | "varied"`). Commit stubs. **Freeze the contract.**
- **A + B:** split API-key provisioning so it's done in parallel — A grabs Gemini + Backboard, B stands up Mongo Atlas + URI. Everyone pulls a working `.env`.
- **A:** decide substrate = "asyncio for MVP" and log it in the ARCHITECTURE decisions table so no one re-litigates it.
- **D:** confirm Base44 vs Next.js for the dashboard; log it.

### Phase 1 — Unblockers first (H1–H3)
- **A:** commit scaffold + shared models module + route shells → then **build the fake emitter** and point it at B's collector. *(A intentionally delays the real runner until the team is unblocked.)*
- **B:** Mongo connection + collections + indexes → collector route real enough to accept and store the fake emitter's events → start WebSocket.
- **C:** stand up `pipelines.py` against the fake events already landing in Mongo — completion rate + iteration histogram + cost first (pure deterministic math).
- **D:** apply design templates (palette/type/layout); mock all three views (fleet, traffic, report) against contract shapes with fake data. No backend dependency yet.

**Checkpoint @ ~H3:** fake events are flowing into Mongo; B's collector + WS work; C's first pipeline returns real numbers; D has three mocked views. The team is now fully parallel.

### Phase 2 — Parallel build (H3–H20)
- **A:** the real work — fan-out controller + lifecycle state machine, loop runner executing the morning-triage loop (6 Gemini agents, Backboard memory for state persistence via `state_update` events), oracle checker, batched real event emission. Then seed library variation (identical vs varied, ~10 archetypes) + A/B evaluator knob (weak vs strong model).
- **B:** finish WebSocket (fleet counts + sampled traffic), `/sandboxes` + `/events` query routes, harden collector (validation, reject/drop policy). B is now serving D live data.
- **C:** stall detector (`STALL_WINDOW` no-progress signature) → divergence metric (identical-seed control pairs) → per-handoff failure rates → failure clustering → Gemini-narrated `Finding`s → `report_builder` → `/report`.
- **D:** wire views to real endpoints as they come online (B's WebSocket first, then C's report), **with C pairing in** once C's report chain is stubbed. Start drafting the demo script.

**Checkpoint @ ~H12:** a real (or fake-fed) ≥50-sandbox run shows live in the dashboard and produces a real report with at least one real finding.

### Phase 3 — Swap, scale, rehearse (H20–H32)
- **A ↔ B/C:** swap the fake emitter for the real morning-triage runner as the event source. Confirm real events match the schema exactly (they should — same models).
- **A:** scale 50 → 100 → stretch toward 1,000; tune batch flush timing with B so the live feed isn't laggy.
- **C:** confirm findings read well on real data; tune the planted-failure scenarios (misroute ping-pong + reject ping-pong) so the demo's "money moments" reliably appear.
- **D:** swap mock → real data everywhere; rehearse the **"one anecdote vs a distribution"** narrative end-to-end **twice**; lock the one happy path + the one failure-finding moment.
- **Nice-to-haves only if green:** ElevenLabs report narration (D), Unifold payments loop as secondary spec (A — see §8).

### Phase 4 — Freeze + buffer (H32–H36)
- Feature freeze. Only bug-fixes on the demo path. Re-rehearse. Record the backup demo video. Submit Devpost stub early (declare tracks).

---

## 6. Sync points (keep them short, keep them scheduled)

Three standing 5-minute syncs prevent silent contract drift:

1. **Orchestration ↔ Data (H1, then H8):** event batch flush timing; who marks a `RunBatch` complete; validation-error policy (reject batch vs drop event).
2. **Data ↔ Interface (H2, then H10):** WebSocket message shapes; report JSON final before D wires the report view.
3. **Orchestration ↔ Interface (H2):** fleet state-counts shape in `GET /api/runs/{run_id}`; what "live traffic" means on screen (sampled, not full stream).

**The cardinal rule (from `TEAM_DIVISION.md`):** no one changes a field name, signature, route path, or collection name without updating `SHARED_CONTRACTS.md` first, then announcing, then coding. A silent rename breaks someone else's code invisibly.

---

## 7. Contingencies

- **If A is behind on the real runner at H20:** demo on the fake emitter. It emits contract-shaped events, so B/C/D can't tell the difference — the QA story still lands. (This is the whole reason the fake emitter exists.)
- **If B's WebSocket is late:** D falls back to polling `GET /api/runs/{run_id}` at `DASHBOARD_POLL_MS`. The contract already anticipates this.
- **If C's Gemini findings are flaky:** ship deterministic stats + one hand-templated finding narration. Per the contract risk note — *math decides, the LLM only narrates.* The demo survives without the LLM layer.
- **If someone finishes early:** float to the critical path — help A scale the fan-out, or help C on per-handoff analysis, or pair with D on wiring.

**Critical path = A's real runner → C's pipeline chain → the report.** Protect it. Everything else has slack.

---

## 8. Sponsor-track hooks (build them in as you go, don't bolt on later)

These map to Hack the 6ix tracks and mostly fall out of the architecture already:

- **Backboard** — two roles, both core: (1) Layer-1 demo loop state-file memory per sandbox_id (A); (2) Layer-2 Loopy longitudinal QA memory per spec_id + analysis routing that serves Gemini (C). ✔
- **MongoDB (MLH)** — event store (time-series) + aggregations + vector clustering (already core). ✔
- **Gemini (MLH)** — two roles, both core: (1) Layer-1 demo loop agents (A); (2) Layer-2 analysis model that narrates failure clusters into Findings, served via Backboard (C). ✔
- **Warp** — drive the sandbox fleet ops from the agentic terminal; document it in the demo. ✔
- **Base44** — the dashboard/report viewer (if chosen in Phase 0). ✔
- **Unifold ($1k)** — register a small payments loop as a *second* spec to prove Loopy is domain-agnostic; earns the idempotency-as-finding angle. A owns, Phase 3, only if the morning-triage runner is stable. ★
- **ElevenLabs** — voice narration of the report + a voice-agent example loop (D, nice-to-have). ◐

Declare only what you actually wire. Over-declaring incoherent tracks costs you on the technical-difficulty axis.
