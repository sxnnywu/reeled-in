# Example Loop Spec — Morning-Triage (6-agent CI-triage)

The one loop Loopy is demoed on, and the loop we build our product understanding around. It's the canonical "Build Your First Loop" example from the *Loop Engineering* paper (p.9): a dev-automation loop that triages red CI builds, routes each failure to a specialist fixer, has an adversarial judge review, merges or bounces, and moves on — with no human in the inner loop.

This doc is the source of truth for the example loop. It defines the agents, topology, seeds, the answer-key oracle, and exactly what Loopy tests on it. Shapes conform to `SHARED_CONTRACTS.md`.

> **Updated 2026-07-17 (Jay/C): expanded from 3 agents to 6.** The 3-agent version was near-linear (one fixer, one reviewer). The 6-agent version adds a classification step + three specialists, which makes routing itself testable: 14 handoff edges instead of 4, misrouting becomes a measurable failure class, and per-handoff fragility gets a real graph to rank. Tier-1/Tier-2 analysis for this loop is already implemented and verified in `backend/` (see PERSON_C_PLAN.md). Post-run critique from the 3-agent draft is dropped.

---

## 0. Source loop (we adopt, not invent)

We do **not** author this loop from scratch. We adopt the published **Daily Triage** loop pattern and expand it to the specialist-routing shape:

- **Source:** `cobusgreyling/loop-engineering` → **`examples/grok/daily-triage.md`**
  https://github.com/cobusgreyling/loop-engineering/blob/main/examples/grok/daily-triage.md
- Patterns index: https://github.com/cobusgreyling/loop-engineering/blob/main/patterns/README.md
- **Topology basis:** the annotated "first loop" in the *Loop Engineering* IEEE working note, §XII p.9 (discovery skill → worktree per finding → generator/evaluator split → human inbox). Its §VI "Five Ways a Loop Goes Wrong" is the failure taxonomy our findings map to.
- Also referenced for triage styles: `serenakeyitan/awesome-agent-loops` (CC BY 4.0) — https://github.com/serenakeyitan/awesome-agent-loops

**Why adopt a real loop:** stronger demo story ("we didn't build a strawman rigged to fail — we QA'd the *published* daily-triage loop the community recommends, and its evaluator nods broken fixes through") and less scaffolding (we lift its prompts/structure instead of inventing them).

> **TODO before the event:** confirm the repo's `LICENSE` and attribute the source loop in our README + demo. (awesome-agent-loops is CC BY 4.0; verify cobusgreyling's terms.)

---

## 1. What the loop does

A single turn realizes the five moves of a loop:

1. **Discovery** — `ci_monitor` reads what's new: CI runs that failed since the last tick, issues opened in the last 24h, commits merged since the last run. Each actionable failure becomes a finding.
2. **Triage / routing** — `triage_agent` classifies each finding (**flaky_test | infra | regression | dependency**) and hands it to the matching specialist. If a specialist bounces it back ("not my kind of problem"), triage re-classifies with their evidence.
3. **Handoff + Generation** — the specialist (`test_fixer` / `infra_fixer` / `dep_fixer`) opens an isolated worktree and drafts a minimal fix.
4. **Verification** — `evaluator` ("assume broken until proven otherwise") runs the tests and either PASSes (merged, ticket closed) or REJECTs back to the specialist with reasons. The evaluator's model is our **A/B knob**.
5. **Persistence** — every finding + status is written to the state file (Backboard memory), so the next run remembers.

Anything the evaluator can't confidently judge goes to a human inbox (never auto-merged). **Scheduling** (a daily trigger) is what makes it a loop; for Loopy each sandbox runs one full turn over one seeded incident.

---

## 2. Controlled build (how we make it QA-able at 1,000×)

We do **not** run this against a real repo/GitHub/CI. We build a **controlled loop**:

- **Real agents** — all six are real Gemini agents making real decisions, prompts adapted from the source pattern.
- **Synthetic incident fixture** — each sandbox is seeded with a generated CI incident carrying a **planted bug** from a small archetype library.
- **Mocked side effects** — "open a PR" writes to the state file; "run tests" is a **deterministic checker** we own.
- **Answer key (the oracle)** — for every planted incident we know the ground truth: the true failure kind, which test must pass, which files must not change. Ground truth is what lets Loopy *prove* when triage misrouted or the evaluator nodded.

---

## 3. Build plan

### Reuse (from the source pattern + paper)
- Five-moves structure; the skeptical-evaluator prompt ("do not praise; find what fails").
- The prioritization rubric (actionable / blocks release / already tracked → skip).
- The "stronger model for the judge" guidance → our **A/B knob**.
- The state-file persistence pattern → **Backboard memory** scoped per sandbox.

### Adapt (hermetic at scale)
| Source loop does | We swap it for |
|---|---|
| Real GitHub / CI discovery | Synthetic incident fixture (seed_input) |
| Real worktree + `open PR` | Mocked — writes to state file |
| Real test runner | Deterministic **oracle** checker |
| Daily cron / scheduler | Loopy fan-out (one turn per sandbox) |
| MCP connectors | Stubbed |

### Add (net-new — the QA layer)
- The **answer-key oracle** per seed (`true_kind`, `must_pass`, `must_not_touch`).
- **Event instrumentation** — contract-shaped `Event`s for every message, tool call, state update, termination. Runner MUST emit payload keys `classified` (triage), `verdict` (evaluator), `must_pass_ok` (oracle) — Tier-2 analysis reads them.
- The **seed/archetype library** — ~10 incident archetypes → 100 distinct seeds.
- **Planted failure scenarios** that guarantee the demo findings (§8).

### Phasing (Orchestration / Person A)
1. **Phase 1 (unblocker):** LoopSpec JSON is already committed (`backend/examples/ci_triage_spec.json`); fake emitter exists (`backend/scripts/seed_ci_triage_run.py` — seeds Mongo directly; re-point it at B's collector when live).
2. **Phase 2:** real `loop_runner` executes the 6 Gemini agents over synthetic incidents; oracle checker; real event emission.
3. **Phase 3:** seed library variation; scale 50 → 100 → 1,000; wire the A/B (weak vs strong evaluator).

---

## 4. Agents (`AgentDef[]`)

Six agents — full definitions live in **`backend/examples/ci_triage_spec.json`** (committed, contract-shaped). Summary:

| agent_id | Role | Model tier |
|---|---|---|
| `ci_monitor` | Discovery: watches CI, reports each failure | flash-lite |
| `triage_agent` | Classifies each finding, routes to a specialist, re-triages bounces | flash-lite |
| `test_fixer` | Fixes flaky tests / broken assertions in a worktree | flash |
| `infra_fixer` | Fixes runner/cache/network failures in a worktree | flash |
| `dep_fixer` | Fixes dependency/regression failures in a worktree | flash |
| `evaluator` | Adversarial reviewer; PASS merges, REJECT bounces back | flash — **the A/B knob** |

> Cheap tier for high-frequency monitor/triage; stronger tier for fixers and the judge (the judge is the loop's floor — don't cheap out).

## 5. Topology (`topology[]` — `{from_agent, to_agent, condition}`)

```
ci_monitor → triage_agent                                  finding_discovered
triage_agent → test_fixer | infra_fixer | dep_fixer        classified_<kind>
specialist → evaluator                                     fix_drafted
specialist → triage_agent                                  misrouted_bounce   ← ping-pong risk 1
evaluator → specialist                                     rejected           ← ping-pong risk 2
evaluator → ci_monitor                                     pass_merged_or_human_inbox
```

14 edges total (full list in the spec JSON). The two bounce-back edges are where the planted stalls live; `evaluator → ci_monitor` closes an item.

## 6. Termination (`termination`)

```json
{ "max_iterations": 30, "goal_check": "finding resolved: evaluator PASS and fix merged, or routed to human inbox" }
```

- `goal_reached` — the incident ended in a merge or the human inbox.
- `stall_detected` — `STALL_WINDOW` (5) iterations with no state progress (either ping-pong).
- `max_iterations` / `timeout` — safety caps.

## 7. Seeds + answer key (`SandboxRun.seed_input`)

```json
{
  "failure_kind": "flaky_test",
  "incident": "auth test flaky on retry",
  "answer_key": {
    "true_kind": "flaky_test",
    "must_pass": ["test_auth"],
    "must_not_touch": ["billing.py"]
  }
}
```

- **`seed_strategy: "identical"`** → all sandboxes get the same incident (measures divergence/consistency).
- **`seed_strategy: "varied"`** → each sandbox gets an archetype remix (measures robustness).
- `true_kind` powers the triage-accuracy check; `must_pass` powers the nod check (§9).

---

## 8. Planted failure scenarios (what guarantees the demo findings)

| # | Cluster | What happens | Paper failure class |
|---|---|---|---|
| 1 | **Misroute ping-pong** | triage calls a flaky test "infra"; infra_fixer bounces it back; triage (lacking the specialist's evidence) says "infra" again → stall | Tangled/handoff |
| 2 | **Reject ping-pong** | dep_fixer resubmits the same rejected fix; evaluator rejects for the same uncovered edge case → stall | no-escape-hatch verification |
| 3 | **Nodding evaluator** | oracle says the fix is broken (`must_pass_ok: false`); evaluator PASSes it anyway — run *looks* clean | Nodding loop |

All three are implemented in the fake seeder and verified caught by the analysis (see §9 numbers).

## 9. What Loopy tests on this loop

### Tier 1 — automatic (any loop, zero config) — IMPLEMENTED ✔
| Check | On this loop it means |
|---|---|
| Completion rate | % of incidents that reached merge/inbox |
| Stall / non-termination | either ping-pong hitting `STALL_WINDOW` |
| Per-handoff fragility | 14 edges ranked; the guilty bounce edges top the list |
| Cross-run divergence | identical incident → different routing or outcome |
| Cost / iteration distribution | token spend + iteration count; the p95 tail |

### Tier 2 — correctness vs the answer key — IMPLEMENTED ✔ — the money findings
| Check | Caught because we have ground truth |
|---|---|
| **Nodding evaluator** | evaluator PASSes a fix the oracle says fails `must_pass` → *approved-but-broken* |
| **Triage accuracy** | first classification vs `true_kind`; the confusion pairs *prove* which agent owns the misroute stall |
| Scope violation (next) | fix touches a `must_not_touch` file but is approved |

Current verified numbers on the 80-sandbox fake run: completion 70%, stall 30%, fragility top-2 = the two planted bounce edges (100% / 70%), nod rate 3.6%, triage accuracy 87.5% with every miss = `flaky_test → infra`.

### Tier 3 — LLM-narrated "why"
Gemini clusters flagged failures and explains the pattern. **Math decides, the LLM narrates.**

### A/B mode (a mode, not a new test)
Run the identical battery with `evaluator.model` = weak vs strong (or stricter prompt), fan out both fleets, diff the distributions:
> "Strong evaluator cut the nod rate and stalls, at higher token cost." — the paper's "tune the evaluator" advice, quantified.

---

## 10. Events this loop emits (`EventType`)
- `agent_message` — monitor→triage finding, triage→specialist handoff, specialist→evaluator submit, evaluator→specialist reject, specialist→triage bounce, evaluator→monitor close.
- `tool_call` / `tool_result` — `read_ci_runs`, `worktree`, `run_tests` (oracle; result carries `must_pass_ok`).
- `state_update` — writes to the state file (Backboard memory).
- `loop_iteration` — each turn boundary.
- `termination` — `goal_reached | stall_detected | max_iterations | timeout | error`.

Failures are **data**, not errors (only infra failures retry). Every event carries `run_id + sandbox_id + seq`.

---

## 11. How the sponsors show up (mind the two layers)

**Layer 1 — inside THIS demo loop (the demo loop's choice; swappable, not required of a real user's loop):**
- **Gemini** — powers the six agents (monitor/triage Flash-Lite; fixers/evaluator Flash).
- **Backboard** — the loop's **persistence move**: the state-file memory is Backboard memory scoped per `sandbox_id`; its router is the A/B knob for swapping the evaluator model.

*(A real user's loop would bring its own models/memory — Loopy tests it model-agnostically. We use Gemini/Backboard here only because we authored the demo loop.)*

**Layer 2 — Loopy's own QA infra (always ours, for any loop under test):**
- **Gemini** — the analysis model that narrates failure clusters into `Finding`s (structured JSON, Batch API), served via Backboard.
- **Backboard** — longitudinal QA memory scoped per `spec_id` (trends/regressions across batches) + analysis routing.
- **MongoDB** — event store (regular collection, unique-indexed for idempotency), change-stream live feed, within-batch vector clustering.
- **Base44** — dashboard (fleet + traffic + report).

**Unifold (optional, secondary loop):** this loop has no payments; register a small payments loop for the Unifold track, which also proves Loopy is domain-agnostic. Lead with the CI-triage loop.

---

## 12. The demo money-moments
1. **Nodding evaluator.** One run: triage → fix → evaluator approves → merged. Looks perfect. Run it 80× → Loopy proves, against the answer key, that the evaluator nods broken fixes through, clustered on multi-file changes; the A/B panel shows a stronger evaluator fixes it.
2. **Misroute stall, attributed.** A third of runs never terminate — and Loopy doesn't just say "stalled": per-handoff fragility ranks the guilty edge #1 (`infra_fixer → triage_agent`, 100%), and triage accuracy proves *why* (every misclassification is `flaky_test → infra`). The paper predicted the failure class; Loopy measured it and named the agent responsible.
