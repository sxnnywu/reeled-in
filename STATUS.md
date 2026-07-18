# STATUS.md — Living Project Heartbeat

**Update this file at the end of every work session, by every person and every coding agent. Stale = bug.**

Last updated: 2026-07-17 (Jay / Person C session)

---

## Done

- [x] Documentation scaffold created (all root MD files + workstream plans)
- [x] Draft shared contracts (event schema, collections, routes) — DRAFT status, not locked
- [x] Person C: Tier-1 deterministic pipelines (completion, stall, iterations, cost, divergence, per-handoff fragility) — verified vs local Mongo
- [x] Person C: Tier-2 answer-key checks (nod rate, triage accuracy) — verified
- [x] Person C: fake-data seeder w/ 3 planted failure clusters + 6-agent CI-triage LoopSpec (`backend/`)

## In Progress

- Person C (analysis): findings generator → report_builder → /report route (next)

## Next

- [ ] Confirm Pheobe's role (what does the product actually do → where it fits)
- [ ] Decide sandbox substrate (blocker for Orchestration)
- [ ] Confirm Base44 vs Next.js for dashboard
- [ ] Lock `SHARED_CONTRACTS.md` §3–§5 and commit stubs (first 45 min of build)
- [ ] Read docs/best practices for each adopted OSS tool; log in INTEGRATIONS_AND_STACK.md

## Blockers

- (none)

## Handoff Notes

Format for entries below — append, never delete:

```
### [date/time] — [who or which agent]
What changed:
Decisions made:
Gotchas for the next person:
```

### (initial) — scaffold
What changed: full doc structure created; contracts in DRAFT.
Decisions made: workstream-based division (not name-based); push-model event capture assumed; `run_id` naming locked.
Gotchas: sandbox substrate is THE open decision — nothing in Orchestration should hard-commit until it's made.

### 2026-07-17 evening — Jay (Person C) + Claude
What changed: backend/ added — analysis pipelines (Tier 1+2), CI-triage demo spec, fake seeder; PERSON_C_PLAN.md + DEMO_TARGET_CI_TRIAGE.md at root.
Decisions made: Jay prefers the 6-AGENT CI-triage loop as demo target — CONFLICTS with example-loops/morning-triage.md ("the one loop"). NEEDS TEAM ALIGNMENT before A builds the runner.
Gotchas for the next person: analysis needs runner to emit payload keys `classified`, `verdict`, `must_pass_ok` (see PERSON_C_PLAN.md §6); C uses a local models.py mirror until A commits the shared module.

### 2026-07-17 late — Jay (Person C) + Claude
What changed: CUT Solana, Deloitte, Freesolo, Auth0 from ALL docs (PARALLEL_IMPLEMENTATION_PLAN, ARCHITECTURE_FLOW, INTEGRATIONS_AND_STACK, TEAM_DIVISION, PROJECT_OVERVIEW, SHARED_CONTRACTS env, data-and-storage PLAN). Confirmed stack = Backboard, Pheobe (TBD), Base44, Warp, MongoDB, Gemini; ElevenLabs + Unifold remain optional.
Decisions made: we are NOT pursuing those four tracks. If anyone disagrees, raise it before re-adding.
Gotchas for the next person: SOLANA_RPC_URL removed from SHARED_CONTRACTS §6.
