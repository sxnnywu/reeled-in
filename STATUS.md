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

### 2026-07-18 — Sunny (Person A) + Oz
What changed: Cross-plan reconciliation after all four person plans landed. Fixed 8 inconsistencies: (1) Motor → PyMongo `AsyncMongoClient` in CLAUDE.md / INTEGRATIONS_AND_STACK / data-and-storage PLAN (Motor is EOL, per B's research); (2) `events` = REGULAR collection everywhere — SHARED_CONTRACTS §4, ARCHITECTURE_FLOW (×5 incl. decisions-log #3 reversal), PARALLEL_IMPLEMENTATION_PLAN §8, PERSON_C_PLAN §6 (Time Series has no change streams + no unique indexes, both load-bearing); (3) sandbox_runs write split documented in PERSON_A_PLAN §3e per B's recommendation (A owns active states, B's collector writes terminal fields from termination events); (4) `verdict` casing fixed in PERSON_B_PLAN — it is uppercase "PASS"/"REJECT"; (5) the "morning-triage vs CI-triage" conflict flagged in B's and D's plans is RESOLVED as a naming misread — morning-triage.md IS the 6-agent CI-triage loop (same loop; ci_triage_spec.json is its LoopSpec); (6) Solana removed from PERSON_B_PLAN §5; (7) polling reframed as D's PRIMARY live-data mechanism (Base44 can't consume external WS) in PARALLEL_IMPLEMENTATION_PLAN §6/§7 + SHARED_CONTRACTS §2 comment; (8) B's four researched decisions (D1–D4) + polling-primary added to ARCHITECTURE_FLOW decisions log as rows 9–12.
Decisions made: adopted B's D1–D4 as team decisions (in the decisions log); D's demo-script blocker cleared.
Gotchas for the next person: SHARED_CONTRACTS §4 events row changed — anyone who read the old time-series spec should re-read it. C's remaining open item in §6 of B's plan: confirm reports collection write access + get_db() swap.
