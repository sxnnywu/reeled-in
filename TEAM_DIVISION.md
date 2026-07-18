# Team Division — 4 People, Workstream-Based

## Philosophy

Work is divided by **workstream, not by name**. People float to where they're needed; priorities will shift. The one fixed mapping: the **Interface & Design** workstream is owned by the team's presenter/designer (UI/UX from our existing design templates, partner/stakeholder communication during the event, demo narrative). The three technical members float across **Orchestration** and **Data & Storage**, and pick up Interface engineering tasks (wiring the dashboard to real data) as needed.

## The Core Problem With Naive Parallel Development

Data & Storage needs the event schema before writing aggregation pipelines. Orchestration needs the same schema before emitting events. Interface needs the API shapes before building the dashboard. Done naively, everyone blocks on everyone.

## The Solution: Contract-First

In the first 30–45 minutes of build time:

1. The team agrees on `SHARED_CONTRACTS.md` (event schema, loop spec, API routes, Mongo collections).
2. Stub files are committed defining exact import paths and signatures.
3. Everyone writes real logic against the stubs from minute one.
4. Implementations are filled in behind the agreed interfaces.

## Critical Rule: The Contract Is Final

Once stubs are committed, **no one changes a field name, method signature, route path, or collection name without telling the whole team first.** Changing them unilaterally breaks someone else's code silently. `SHARED_CONTRACTS.md` gets updated FIRST, then the announcement, then the code.

---

## Workstreams

### 1. Orchestration (sandbox fleet + loop runner)

Owns:
- Loop-spec ingestion: normalizing a GitHub repo, folder upload, or inline spec into a `LoopSpec` (Loopy is model-agnostic — we reference the user's agents/skills/connectors, not re-implement them)
- Sandbox lifecycle: provision, run, teardown, retry
- Fan-out controller (N concurrent runs, seeded input variation)
- The demo loop (Layer 1): the **morning-triage** 6-agent CI-triage loop — Gemini agents + Backboard memory here are *that loop's* choices, not Loopy platform requirements
- Instrumentation adapter: wraps the loop, records all agent I/O as contract-shaped `Event`s, model-agnostically
- Event emission from inside sandboxes (conforming to the shared event schema)

Does not own:
- Mongo schema/aggregations, dashboard code, report generation

### 2. Data & Storage (capture + analysis)

Owns:
- MongoDB setup, collections, indexes
- Event ingestion endpoint/collector
- Aggregation pipelines: completion rate, stall detection, divergence, cost stats, failure clustering
- LLM-assisted findings (Gemini summarization of failure clusters)
- QA report generation

Does not own:
- Sandbox lifecycle, example loops, dashboard UI

### 3. Interface & Design (dashboard + narrative)

Owns:
- Dashboard (Base44 primary candidate): fleet status, live agent-to-agent traffic feed, report viewer
- Visual design per our existing templates
- Partner/stakeholder communication during the event
- Demo script and presentation
- Nice-to-have: Eleven Labs voice layer

Does not own:
- Backend logic, schemas, orchestration

Technical members support this workstream for API wiring; the owner focuses on design, comms, and demo.

---

## Cross-Workstream Confirmation Checklists

### Orchestration ↔ Data & Storage
- [ ] Event schema final (field names, types) in `SHARED_CONTRACTS.md`
- [ ] Push vs pull capture decided
- [ ] Batch size / flush strategy for event emission

### Data & Storage ↔ Interface
- [ ] API routes + response shapes final
- [ ] Live update mechanism decided (WebSocket vs polling interval)
- [ ] Report JSON shape final

### Orchestration ↔ Interface
- [ ] Fleet status shape (per-sandbox state enum) final
- [ ] What "live traffic" means on screen (sampled vs full stream)

---

## Success Criteria (per workstream)

Orchestration is done enough when: another workstream can trigger a ≥50-sandbox run via one API call and events flow.
Data & Storage is done enough when: aggregations return real findings from a completed run batch, and a report generates.
Interface is done enough when: the dashboard shows a live run and renders the report, and the demo script is rehearsed end to end.
