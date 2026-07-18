# SHARED_CONTRACTS.md — Loopy

## How To Use This File (Read First)

This is the **single source of truth** for every data shape, API route, collection name, and constant in this project. All workstreams build against these definitions. Field names, types, and enum values are final once committed — do not change them without announcing to the full team.

**For AI coding agents:** Treat every code block in this file as a specification you must implement exactly. Do not invent field names, do not change types, do not add required fields unless they appear here. When in doubt, the code block wins over any prose description.

**Authoritative precedence:** This file > TEAM_DIVISION.md > ARCHITECTURE_FLOW.md

Status: **DRAFT** — sections marked `LOCKED` are final; everything else is open for challenge until stubs are committed at build start.

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
    "state_update",      # Backboard.io memory write
    "termination",       # loop ended (carries reason)
    "error",
]

TerminationReason = Literal[
    "goal_reached", "max_iterations", "stall_detected", "timeout", "error",
]

FindingSeverity = Literal["info", "warning", "critical"]
```

## 2. Shared Constants

```python
DEFAULT_MAX_ITERATIONS = 30
DEFAULT_SANDBOX_TIMEOUT_S = 300
DEFAULT_FLEET_SIZE_MVP = 50
STALL_WINDOW = 5          # iterations with no state progress = stalled
EVENT_BATCH_SIZE = 25     # events per collector POST
DASHBOARD_POLL_MS = 2000  # if polling; WebSocket preferred
```

## 3. Core Document Shapes (Pydantic — mirror exactly in TS)

```python
class AgentDef(BaseModel):
    agent_id: str
    name: str
    model: str                  # e.g. "gemini-2.0-flash"
    system_prompt: str
    tools: list[str] = []

class LoopSpec(BaseModel):
    spec_id: str
    name: str
    agents: list[AgentDef]
    topology: list[dict]        # TODO(lock): edge shape {from_agent, to_agent, condition}
    termination: dict           # TODO(lock): {max_iterations, goal_check}
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

class Report(BaseModel):
    report_id: str
    run_id: str
    summary: str
    findings: list[Finding]
    stats: dict                 # completion_rate, iteration histogram, cost, divergence
    created_at: datetime
```

## 4. MongoDB Collections

| Collection | Document | Indexes |
|---|---|---|
| `loop_specs` | LoopSpec | `spec_id` unique |
| `run_batches` | RunBatch | `run_id` unique |
| `sandbox_runs` | SandboxRun | `(run_id, sandbox_id)` unique |
| `events` | Event | `(run_id, sandbox_id, seq)`; `(run_id, type)` |
| `reports` | Report | `run_id` unique |

Naming rule: it is `run_id` everywhere. Never `batch_id`, never `run_batch_id`.

## 5. API Routes (FastAPI)

| Method | Path | Body / Params | Returns | Owner |
|---|---|---|---|---|
| POST | `/api/specs` | LoopSpec (sans id) | LoopSpec | Orchestration |
| POST | `/api/runs` | `{spec_id, n_sandboxes, seed_strategy}` | RunBatch | Orchestration |
| GET | `/api/runs/{run_id}` | — | RunBatch + sandbox state counts | Orchestration |
| GET | `/api/runs/{run_id}/sandboxes` | `?state=` | list[SandboxRun] | Data & Storage |
| POST | `/api/events` | `{events: list[Event]}` (batch) | `{accepted: int}` | Data & Storage |
| GET | `/api/runs/{run_id}/events` | `?sandbox_id=&type=&limit=` | list[Event] | Data & Storage |
| GET | `/api/runs/{run_id}/report` | — | Report (404 until ready) | Data & Storage |
| WS | `/ws/runs/{run_id}` | — | fleet status + sampled events stream | Data & Storage |

Route paths are LOCKED once the frontend starts coding against them.

## 6. Env Vars (`.env`, never committed)

```
MONGODB_URI=
GEMINI_API_KEY=
BACKBOARD_API_KEY=
PHEOBE_API_KEY=            # pending role confirmation
BASE44_...=                # pending
ELEVENLABS_API_KEY=        # nice-to-have
```

## 7. Producer / Consumer Map

| Contract | Produced by | Consumed by |
|---|---|---|
| LoopSpec | Orchestration | Orchestration (runner), Interface (spec form) |
| Event | Orchestration (sandboxes) | Data & Storage (collector, analysis), Interface (traffic feed) |
| SandboxRun states | Orchestration | Interface (fleet view), Data & Storage (stats) |
| Report / Finding | Data & Storage | Interface (report view) |
