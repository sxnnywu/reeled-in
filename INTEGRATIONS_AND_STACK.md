# Integrations & Tech Stack — Loopy

## Integration Priorities

The more of these we integrate meaningfully, the better — but "meaningfully" is the bar. An integration that doesn't serve the architecture gets cut. Challenge any slot-in that feels forced.

### Priority (must integrate)

| Integration | Proposed Role in Loopy | Status |
|---|---|---|
| **Backboard.io** | Memory/state layer for agents inside test loops; persistent context across loop iterations | [ ] role confirmed |
| **Pheobe** | TBD — confirm what the product does and where it fits (candidate: observability/eval layer) | [ ] role confirmed |
| **Base44** | Rapid front-end / internal tool builder for the QA dashboard or the report viewer | [ ] role confirmed |
| **Warp** | Dev + demo workflow: agentic terminal driving sandbox fleet ops; document usage in demo | [ ] role confirmed |
| **MongoDB** | Central event store for all sandbox interaction data; aggregation pipelines for analysis | [ ] role confirmed |
| **Gemini API** | LLM for (a) agents inside example loops, (b) failure-cluster summarization in reports | [ ] role confirmed |

### Nice-to-have (integrate only if it fits cleanly)

| Integration | Candidate Role | Status |
|---|---|---|
| **Eleven Labs** | Voice-agent example loop (TTS/voice agents as one of the target systems Loopy QAs); voice narration of the QA report | [ ] go/no-go |

Rule: each confirmed integration gets its role, owner workstream, and required env vars recorded in `SHARED_CONTRACTS.md` §Env.

---

## Core Tech Stack (proposed — confirm before stubs are committed)

### Backend

| Technology | Purpose |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI + Uvicorn | REST API + WebSocket for live fleet updates |
| Pydantic 2.x | Event/loop-spec validation (mirrors `SHARED_CONTRACTS.md`) |
| PyMongo `AsyncMongoClient` (pymongo ≥4.9) | Event store access — Motor was deprecated 2025-05-14, EOL 2026-05-14; use `pymongo.AsyncMongoClient` directly (same aggregation-pipeline dicts, `await` call sites) |
| httpx | Async calls to Gemini/Backboard/etc. |
| python-dotenv | Env management |

### Orchestration / Sandboxing

| Technology | Purpose |
|---|---|
| Sandbox substrate — **DECISION PENDING** (see PROJECT_OVERVIEW open questions) | Isolation for N concurrent loop runs |
| Async worker pool (asyncio / task queue) | Fan-out, lifecycle, retries |

### Frontend

| Technology | Purpose |
|---|---|
| Base44 (primary candidate) and/or Next.js + TypeScript | Dashboard: fleet view, live traffic, QA report |
| Existing design templates (Kimi's domain) | Visual system — follow the templates, don't invent new ones |

### Data & Analysis

| Technology | Purpose |
|---|---|
| MongoDB aggregation pipelines | Stall detection, divergence, cost stats |
| Gemini API | Failure clustering summaries, report generation |

---

## Open Source Usage Rules

- Before adopting any open-source tool: read its README, install docs, and best-practice guidance; record the decision + version + link in this file.
- Pin versions in `requirements.txt` / `package.json`.
- Respect licenses; keep attribution where required.

### Adopted OSS (running list)

| Tool | Version | Why | Docs read? |
|---|---|---|---|
| _none yet_ | | | [ ] |
