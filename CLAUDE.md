# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Current State: Pre-Build

This repo is a **contract-first documentation scaffold** — there is no application code yet. There is no `backend/`, no `requirements.txt`/`package.json`, no build/lint/test tooling. Everything is Markdown specs plus empty workstream plans. The first real build work is: lock `SHARED_CONTRACTS.md` §3–§5, then commit stub files at the exact paths listed in each `workstreams/*/PLAN.md`. Do not invent a directory layout — the planned paths are prescribed in the PLAN.md files.

## What Loopy Is

A QA/observability platform for **loop-engineered agent systems** (multi-agent loops that prompt/evaluate/re-prompt with no human in the loop). Loopy ingests a target agent loop, fans it out across a large fleet of isolated sandboxes (MVP: 50–100 concurrent; stretch: 1,000), captures every agent-to-agent interaction, and produces aggregate QA findings. Thesis: "one run is an anecdote; QA requires a distribution." Read `DUMMY_EXPLANATION.md` → `PROJECT_OVERVIEW.md` for the full framing.

## Architecture: End-to-End Data Flow

The system is one pipeline, split across three workstreams. The full picture requires `ARCHITECTURE_FLOW.md` + `SHARED_CONTRACTS.md` + `EXAMPLE_RUN_FLOW.md` together:

1. **Ingest** (Orchestration): `POST /api/specs` normalizes a target system into a `LoopSpec` (agents, topology, termination) → `loop_specs`.
2. **Fan out** (Orchestration): `POST /api/runs` creates a `RunBatch` (`run_id`) + N `SandboxRun` docs, provisions sandboxes, drives the lifecycle state machine `pending → provisioning → running → completed | failed | stalled | timed_out`.
3. **Capture** (Orchestration emits → Data & Storage stores): each sandbox's loop runner emits `Event`s (agent_message, tool_call, loop_iteration, state_update, termination, error), batched (`EVENT_BATCH_SIZE`) to `POST /api/events` → `events` + `sandbox_runs`.
4. **Analyze** (Data & Storage): Mongo aggregation pipelines compute deterministic stats (completion rate, stall detection via `STALL_WINDOW` no-progress signature, divergence across identical seeds, token/cost); then Gemini clusters/narrates failures into `Finding`s.
5. **Report + Dashboard** (Data & Storage + Interface): `Report` assembled → `reports`; dashboard reads live fleet status + sampled traffic over WebSocket (`/ws/runs/{run_id}`) and renders the report.

**Load-bearing design principles** (violating these breaks the product's point):
- A sandbox/loop failure is **data, not an error** — record and classify it. Only *infra* failures (provisioning) are retried; behavioral failures (stalls, loop errors) are *never* retried — they are the thing being measured.
- Deterministic math decides; the LLM only narrates. Never let Gemini findings replace computed stats.
- Every `Event` carries `run_id` + `sandbox_id` + `seq`, so partial data from a crashed run is still analyzable.

## Contracts Are Law

`SHARED_CONTRACTS.md` is the single source of truth for every data shape, route, collection name, and constant. When docs disagree, precedence is: **`SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `ARCHITECTURE_FLOW.md` > everything else**.

- The identifier is `run_id` **everywhere** — never `batch_id` or `run_batch_id`.
- Pydantic models in §3 must be mirrored exactly in TypeScript on the frontend (same field names).
- Route paths (§5) are LOCKED once the frontend codes against them.
- To change any committed field/route/collection: edit `SHARED_CONTRACTS.md` **first**, mark the change, and tell the human to announce it — then write dependent code. Never rename unilaterally.

## Workstreams (stay in your lane)

Work is divided by workstream, not person. Each `workstreams/*/PLAN.md` lists what it owns, does not own, and its deliverable file paths. Do not modify another workstream's files; code against the contract/stub and record the dependency in your PLAN.md "Handoff Notes".

- **Orchestration** — FastAPI app, spec ingestion (inline + GitHub/folder via `POST /api/specs/ingest`), fan-out controller, sandbox loop runner, instrumentation adapter, event emission, the demo loop (morning-triage 6-agent CI-triage loop, Layer 1).
- **Data & Storage** — MongoDB setup (PyMongo `AsyncMongoClient`), event collector, aggregation pipelines, failure clustering + Gemini findings, report assembly, WebSocket.
- **Interface & Design** — dashboard (Base44 candidate) fleet/traffic/report views, visual design from existing templates, demo narrative. Owned by the presenter/designer; technical members assist on API wiring only.

## Planned Stack (proposed, not yet committed)

Backend: Python 3.11+, FastAPI + Uvicorn, Pydantic 2.x, PyMongo `AsyncMongoClient` (pymongo ≥4.9; Motor is EOL since May 2026), httpx, python-dotenv. Frontend: Base44 and/or Next.js + TypeScript. LLM: Gemini. Two decisions are still open and **block** parts of the build: the **sandbox substrate** (isolation mechanism for N concurrent runs) and **push vs pull** event capture (push assumed). Do not hard-commit Orchestration code to a substrate until decided; build the loop runner substrate-agnostic.

## Living-Docs Discipline (required every session)

These docs are the only memory that survives context loss. Before ending any work session you MUST: check off completed items in the relevant `workstreams/*/PLAN.md`, add newly discovered tasks under "Next", and update `STATUS.md` (Done / In Progress / Next / Handoff Notes). Stale docs are treated as bugs. If a data shape/route/import path changed, update `SHARED_CONTRACTS.md` first.

Secrets live in `.env` (gitignored); required env vars are documented in `SHARED_CONTRACTS.md` §6.
