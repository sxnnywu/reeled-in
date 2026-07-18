# SHARED_CONTRACTS.md — Loopy

## How To Use This File (Read First)

This is the **single source of truth** for every data shape, API route, collection name, and constant in this project. All workstreams build against these definitions. Field names, types, and enum values are final once committed — do not change them without announcing to the full team.

**For AI coding agents:** Treat every code block in this file as a specification you must implement exactly. Do not invent field names, do not change types, do not add required fields unless they appear here. When in doubt, the code block wins over any prose description.

**Authoritative precedence:** This file > TEAM_DIVISION.md > ARCHITECTURE_FLOW.md

Status: **DRAFT** — sections marked `LOCKED` are final; everything else is open for challenge until stubs are committed at build start.

---

## 0. Two-Layer Model (context for every shape below)

Loopy has two layers; keep them separate.

- **Layer 1 — the Loop Under Test (the user's).** Model-agnostic: its agents' models, skills, and connectors are whatever the user chose. Loopy runs it behind an instrumentation adapter and only *observes* it. `LoopSpec` **references** the user's loop; it does not re-implement it.
- **Layer 2 — Loopy's QA infrastructure (ours).** MongoDB (events/stats/clustering/reports), Gemini (analysis model), Backboard (longitudinal QA memory + analysis routing), Base44 (dashboard). Sponsors live here.

Implication for shapes: **`AgentDef.model` is the user's loop's model — Loopy never overrides it.** Loopy's own model usage (findings narration) lives in the Analysis Engine, not in these per-loop shapes.

---

## 1. Enums & String Literals

```python
from typing import Literal

SandboxState = Literal[
    "pending", "provisioning", "running",
    "completed", "failed", "stalled", "timed_out",
]

EventType = Literal[
    "agent_message",     # one agent -> another agent
    "tool_call",         # agent invoked a tool
    "tool_result",
    "loop_iteration",    # loop tick boundary
    "state_update",      # loop memory write (Layer-1 loop state, e.g. STATE.md / post-run critique)
    "termination",       # loop ended (carries reason)
    "error",
]

TerminationReason = Literal[
    "goal_reached", "max_iterations", "stall_detected", "timeout", "error",
]

FindingSeverity = Literal["info", "warning", "critical"]

# NEW: how a loop was ingested (Layer-1 source)
LoopSourceKind = Literal["github", "folder", "inline"]
```

## 2. Shared Constants

```python
DEFAULT_MAX_ITERATIONS = 30
DEFAULT_SANDBOX_TIMEOUT_S = 300
DEFAULT_FLEET_SIZE_MVP = 50
STALL_WINDOW = 5          # iterations with no state progress = stalled
EVENT_BATCH_SIZE = 25     # events per collector POST
DASHBOARD_POLL_MS = 2000  # D's primary live-update mechanism (Base44 polls; can't subscribe external WS); WS is enhancement-only
```

## 3. Core Document Shapes (Pydantic — mirror exactly in TS)

```python
class AgentDef(BaseModel):
    agent_id: str
    name: str
    model: str                  # the USER's loop's model (Loopy is model-agnostic; do NOT override)
    system_prompt: str
    tools: list[str] = []

# NEW: reference to the user's loop source + the skills/connectors it needs.
# We REFERENCE these; we do NOT re-model their contents (decided).
class LoopSource(BaseModel):
    kind: LoopSourceKind                # "github" | "folder" | "inline"
    ref: str | None = None              # repo URL / folder id / None for inline
    detected_framework: str | None = None   # e.g. "claude-code", "langgraph", "custom"

class SkillRef(BaseModel):
    name: str
    path: str | None = None             # location in the source (not the file body)

class ConnectorRef(BaseModel):
    name: str
    kind: str                           # e.g. "mcp", "http_tool"
    ref: str | None = None

class LoopSpec(BaseModel):
    spec_id: str
    name: str
    source: LoopSource                  # NEW
    agents: list[AgentDef]
    topology: list[dict]                # TODO(lock): edge shape {from_agent, to_agent, condition}
    termination: dict                   # TODO(lock): {max_iterations, goal_check}
    skills: list[SkillRef] = []         # NEW: references only
    connectors: list[ConnectorRef] = [] # NEW: references only
    created_at: datetime

class RunBatch(BaseModel):
    run_id: str
    spec_id: str
    n_sandboxes: int
    seed_strategy: str          # "identical" | "varied"  TODO(lock): enum
    state: str                  # aggregate state
    created_at: datetime

class SandboxRun(BaseModel):
    sandbox_id: str
    run_id: str
    state: SandboxState
    seed_input: dict | None
    iterations: int
    termination_reason: TerminationReason | None
    total_tokens: int
    started_at: datetime | None
    ended_at: datetime | None

class Event(BaseModel):
    event_id: str
    run_id: str
    sandbox_id: str
    seq: int                    # per-sandbox monotonic sequence
    type: EventType
    ts: datetime
    from_agent: str | None
    to_agent: str | None
    payload: dict               # type-specific body
    tokens: int = 0

class Finding(BaseModel):
    finding_id: str
    run_id: str
    severity: FindingSeverity
    title: str
    description: str
    evidence_sandbox_ids: list[str]
    stat: dict | None           # e.g. {"stall_rate": 0.18}
    status: str = "new"         # NEW: "new" | "recurring" (set via QaMemory comparison)

class Report(BaseModel):
    report_id: str
    run_id: str
    summary: str
    findings: list[Finding]
    stats: dict                 # completion_rate, iteration histogram, cost, divergence
    trend: dict | None          # NEW: deltas vs prior batches, e.g. {"nod_rate": [0.09, 0.06, 0.04]}
    created_at: datetime

# NEW (Layer 2): longitudinal QA memory for a loop, scoped to spec_id.
# Backed by Backboard (entity = spec_id), NOT a Mongo collection.
class QaMemory(BaseModel):
    spec_id: str                # the loop this memory belongs to
    last_run_id: str | None
    known_findings: list[dict]  # signatures of findings seen before -> "recurring" vs "new"
    trend: dict                 # metric history across batches, e.g. {"nod_rate": [...], "stall_rate": [...]}
```

## 4. MongoDB Collections

| Collection | Document | Indexes |
|---|---|---|
| `loop_specs` | LoopSpec | `spec_id` unique |
| `run_batches` | RunBatch | `run_id` unique |
| `sandbox_runs` | SandboxRun | `(run_id, sandbox_id)` unique |
| `events` | Event | `(run_id, sandbox_id, seq)` unique; `(run_id, type)`; `(run_id, sandbox_id)` — **regular collection** (Time Series disabled: no change-stream support + no unique-index support, both load-bearing) |
| `reports` | Report | `run_id` unique |

Naming rule: it is `run_id` everywhere. Never `batch_id`, never `run_batch_id`.

> **`QaMemory` is NOT a Mongo collection** — it lives in **Backboard**, scoped to the `spec_id` entity (Layer-2 longitudinal memory). The Analysis Engine reads/writes it when building a report so findings can be tagged `recurring` and `Report.trend` populated.

## 5. API Routes (FastAPI)

| Method | Path | Body / Params | Returns | Owner |
|---|---|---|---|---|
| POST | `/api/specs` | LoopSpec (sans id) | LoopSpec | Orchestration |
| POST | `/api/specs/ingest` | `{kind, ref}` (github/folder) | LoopSpec (normalized) | Orchestration |
| POST | `/api/runs` | `{spec_id, n_sandboxes, seed_strategy}` | RunBatch | Orchestration |
| GET | `/api/runs/{run_id}` | — | RunBatch + sandbox state counts | Orchestration |
| GET | `/api/runs/{run_id}/sandboxes` | `?state=` | list[SandboxRun] | Data & Storage |
| POST | `/api/events` | `{events: list[Event]}` (batch) | `{accepted: int}` | Data & Storage |
| GET | `/api/runs/{run_id}/events` | `?sandbox_id=&type=&limit=` | list[Event] | Data & Storage |
| GET | `/api/runs/{run_id}/report` | — | Report (404 until ready) | Data & Storage |
| WS | `/ws/runs/{run_id}` | — | fleet status + sampled events stream | Data & Storage |

Route paths are LOCKED once the frontend starts coding against them. (`/api/specs/ingest` is NEW — the GitHub/folder path; `/api/specs` inline-paste stays as the fallback.)

## 6. Env Vars (`.env`, never committed)

```
MONGODB_URI=
GEMINI_API_KEY=            # Layer 2: Loopy's analysis model
BACKBOARD_API_KEY=         # Layer 2: Loopy's QA memory + analysis routing
PHEOBE_API_KEY=            # pending role confirmation
BASE44_...=                # Layer 2: dashboard
ELEVENLABS_API_KEY=        # nice-to-have (report narration)
# NOTE: the Layer-1 loop-under-test brings its OWN model keys via its source/connectors;
# those are not Loopy platform secrets.
```

## 7. Producer / Consumer Map

| Contract | Produced by | Consumed by |
|---|---|---|
| LoopSpec | Orchestration (ingest/normalize) | Orchestration (runner), Interface (spec form) |
| Event | Orchestration (sandbox instrumentation adapter) | Data & Storage (collector, analysis), Interface (traffic feed) |
| SandboxRun states | Orchestration | Interface (fleet view), Data & Storage (stats) |
| Report / Finding | Data & Storage (Analysis Engine) | Interface (report view) |
| QaMemory | Data & Storage (Analysis Engine, via Backboard) | Data & Storage (report builder — recurring tags + trend) |
