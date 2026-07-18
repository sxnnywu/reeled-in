# Person C — Analysis — Plan & Learnings (Jay)

Share-out doc. What the demo loop is, what C owns, what's already built, what's next.

---

## 1. The loop we're testing (demo target)

A **CI/CD failure-triage loop** — 6 agents that automatically handle red CI builds.
Based on the Loop Engineering paper (p.9 "first loop") + the open-source
`cobusgreyling/loop-engineering` daily-triage pattern. Cite both in the demo.

```
ci_monitor → triage_agent → [test_fixer | infra_fixer | dep_fixer] → evaluator
                 ▲                     │ (bounce back if misrouted)      │
                 └─────────────────────┴──────── REJECT ────────────────┘
                          evaluator PASS → merged → done
```

- **ci_monitor** — watches CI, reports each failure
- **triage_agent** — classifies it (flaky_test / infra / regression / dependency), routes to a specialist
- **3 specialist fixers** — draft the fix in an isolated worktree; can bounce a misrouted item back
- **evaluator** — adversarial reviewer, "assume broken until proven otherwise"; PASS merges, REJECT goes back

Spec JSON: `backend/examples/ci_triage_spec.json` (LoopSpec shape per SHARED_CONTRACTS).

**Answer key (adopted from the 3-agent spec doc):** every seeded incident carries
ground truth — `true_kind`, `must_pass` (which test the fix must pass),
`must_not_touch`. This lets analysis PROVE a run was wrong even when it looked
successful.

## 2. Planted failure clusters (what the demo finds)

| # | Cluster | What happens | Caught by |
|---|---|---|---|
| 1 | Misroute ping-pong | triage calls a flaky test "infra"; infra bounces it back; triage says "infra" again → stall | stall detection + handoff fragility + triage accuracy |
| 2 | Reject ping-pong | dep_fixer resubmits same rejected fix forever | stall detection + handoff fragility |
| 3 | Nodding evaluator | oracle says fix is broken; evaluator PASSes it anyway. Run looks clean | **answer key only** — nod rate |

## 3. C's scope

Tier 1 (no config, any loop): completion, stall, iteration histogram, cost, divergence, per-handoff fragility.
Tier 2 (needs answer key): nod rate, triage classification accuracy.
Tier 3: failure clustering + Gemini-written findings → report → `GET /api/runs/{run_id}/report`.
Rule: **math decides, the LLM only narrates.**

## 4. Built + verified (as of 2026-07-17)

Everything below runs today against local Docker Mongo with self-generated
contract-shaped fake data (80 sandboxes, 1,275 events) — no dependency on A or B.

```
Completion 70% · Stall 30% · Divergence 37.9% · cost p95 3,779 vs mean 1,806 tok
Fragility top-2 = the two planted stall clusters (infra_fixer→triage 100%, evaluator→dep_fixer 70%)
Nod rate 3.6% (2/56 approvals passed a broken fix, evidence sandbox ids attached)
Triage accuracy 87.5% — all misclassifications are flaky_test→infra (= cluster 1 proven)
```

Files: `backend/app/services/analysis/pipelines.py` (Tier 1), `tier2.py` (answer key),
`scripts/seed_ci_triage_run.py` (fake data w/ planted clusters), `scripts/run_analysis_demo.py`.
Repro: `python -m scripts.seed_ci_triage_run && python -m scripts.run_analysis_demo`.

## 5. Next steps (in order)

1. **Findings generator** — turn each stat that crosses a threshold into a `Finding`
   (severity, title, description, evidence ids). Deterministic templates first;
   Gemini (structured JSON output) narrates on top. Works without an API key.
2. **`report_builder.py`** — assemble `Report` (summary + findings + stats), store in `reports`.
3. **`routes/reports.py`** — `GET /api/runs/{run_id}/report`, 404 until ready (contract rule).
4. **Failure clustering** — group stall/error transcripts (Mongo Vector Search if time; deterministic grouping by termination pattern first).
5. Tune nod-rate cluster to ~9% for a punchier demo number.
6. Polish: noise-rate stat + token-budget comparison (from the open-source pattern's 100k/day cap).

## 6. Tracks / tools C is manning

From the confirmed stack (INTEGRATIONS_AND_STACK.md): Backboard, Pheobe, Base44, Warp, MongoDB, Gemini. The two that live in the analysis layer are mine:

| Tool | Why it's C's | What I ship for it |
|---|---|---|
| **MongoDB** | The analysis IS Mongo: aggregation pipelines (Tier 1), regular collection `events` (indexed, change-streamed), Vector Search for failure clustering | Pipelines (done), vector clustering (step 4) |
| **Gemini** — analysis half | Findings narration: structured-JSON output mirroring the `Finding` model, Batch API for the analysis pass | Findings generator + report (steps 1–2). A owns the in-loop-agents half |

Others: Backboard + Warp → A, Base44 → D, Pheobe → role still TBD (if it lands as observability/eval it may touch C — flag me).

## 7. What C needs from others

- **A:** shared models module path (I have a local mirror to swap out); confirm
  "same seed_input = control group" convention for divergence; real runner emits
  `classified`, `verdict`, `must_pass_ok` payload keys (list above) so Tier 2 works on real data.
- **B:** `core/database.py` handle (one-line swap for me); confirm `reports` collection write access.
- **D:** report JSON shape sign-off before building the report view — it's `Report` in SHARED_CONTRACTS §3, stats dict shape in my `pipelines.compute_stats`.
- **Keys:** GEMINI_API_KEY for Tier-3 narration (everything else runs without it).
