# Project Overview — Loopy

## What We're Building

A QA and observability platform for loop-engineered agent orchestration systems. Loopy runs a target agent loop across a large fleet of isolated sandboxes, captures all agent-to-agent communication, and produces statistical QA findings about the loop's behavior.

**The hook:** QA for agent loops today is "run it a few times and eyeball the logs." Loopy makes it empirical — a thousand hermetic runs, full interaction capture, and aggregate analysis that surfaces failure modes no single run would reveal.

**Our example loop:** the **Morning-Triage Loop** — the canonical loop from the *Loop Engineering* paper (a dev-automation loop that reads CI failures / issues / commits, prioritizes work, hands each item to a fixer sub-agent, has a reviewer judge the fix, opens a PR, and moves on). Full definition in `example-loops/morning-triage.md`. We build our product understanding around this loop.

---

## The Problem

**Loop-engineered systems are shipped without real QA.**

Teams that build agent loops (dev-automation, voice agents, fintech workflows, internal automation) can see:

- Individual run logs
- Whether a demo run "worked"

What they CANNOT see:

- Failure rate across many runs of the same loop
- Where loops stall (agents ping-ponging a task, never terminating)
- **Whether the reviewer/judge actually says "no"** — or nods a broken fix through (the paper's "nodding loop," the hardest, most-skipped move)
- Behavioral drift when prompts, models, or inputs change
- Which agent-to-agent handoffs are fragile
- Cost/token distribution across runs

One run is an anecdote. QA requires a distribution.

---

## The Solution

### Phase 1: Ingest the target loop
1. User registers a loop-engineered system: agent definitions, prompts, workflow/loop topology, termination conditions.
2. System normalizes it into Loopy's internal loop spec (see `SHARED_CONTRACTS.md`).
3. For our demo, the registered loop is Morning-Triage (`example-loops/morning-triage.md`).

### Phase 2: Fan out into sandboxes
1. Orchestrator provisions N isolated sandboxes (target 1,000; MVP can demo with 50–100).
2. Each sandbox runs one instance of the loop, seeded with a synthetic morning backlog (CI failures, issues, commits) that contains **planted bugs with a known answer key**.
3. Sandboxes are hermetic: no cross-run contamination, every run attributable.

### Phase 3: Capture everything
1. Every agent-to-agent message, tool call, retry, and loop iteration is streamed to the central store (MongoDB).
2. Events use the shared event schema so all analysis code works on one shape.

### Phase 4: Analyze + report
1. Aggregation jobs compute: completion rate, stall/loop-detection, **nodding-reviewer rate (fix approved but fails the answer key)**, divergence across runs, per-handoff fragility, token/cost stats, failure clustering.
2. LLM-assisted analysis (Gemini) summarizes clusters of failures into human-readable findings.
3. Dashboard shows fleet status live and the final QA report per run batch.

---

## What Loopy tests (three tiers)

- **Tier 1 — automatic, any loop, zero config:** completion rate, stall/non-termination, per-handoff fragility, cross-run divergence, cost/iteration distribution. These are structural properties of the event stream.
- **Tier 2 — user-defined correctness:** the loop author supplies success criteria. For Morning-Triage that's the **answer key** per planted bug (which test must pass, which files must not change, correct priority) — this is what lets Loopy catch the nodding reviewer with ground truth.
- **Tier 3 — LLM-narrated "why":** Gemini clusters the flagged failures and explains the pattern. Rule: **math decides, the LLM only narrates.**

**A/B is a mode, not a test type:** run the same battery across two configs (e.g. weak vs strong reviewer model), fan out both fleets, and diff the distributions ("strong reviewer cut the nod rate 9% → 1% at 1.8× cost").

---

## MVP Definition

A demo is successful if we can, live:

- [ ] Register the Morning-Triage loop (triage → fixer → reviewer)
- [ ] Fan it out to ≥50 concurrent sandboxes, each with a seeded synthetic backlog + answer key
- [ ] Show live agent-to-agent traffic streaming into the dashboard
- [ ] Show at least 3 aggregate QA findings — including the **nodding-reviewer rate** (Tier-2, proven against the answer key), plus stall rate and cost spread
- [ ] Generate one readable QA report

Stretch:

- [ ] 1,000-sandbox run
- [ ] A/B mode: weak vs strong reviewer, distributions compared
- [ ] A second registered loop (e.g. a payments loop) to prove domain-agnosticism / open the Unifold track

---

## Decisions (resolved from earlier open questions)

- **Example loop:** Morning-Triage (replaces the earlier FinFlow placeholder), built as a **controlled loop with synthetic backlog + answer key** — real Gemini agents, but "open PR" is mocked and "tests pass" is a deterministic checker we own. This gives real agent behavior + a ground-truth oracle + cheap enough to run 1,000×.
- **Sandbox substrate:** asyncio task isolation for MVP; runner is substrate-agnostic (real substrate is a later swap).
- **Event capture:** push model (sandboxes emit to the collector).
- **Analysis:** deterministic stats first; LLM narrates clusters second.

## Open Questions (challenge these — plans can change)

- [ ] How rich should the synthetic backlog fixture library be for a convincing "varied" run? (target: ~10 bug archetypes, remixable into 100 seeds)
- [ ] Push vs pull for event capture — confirmed push; revisit only if the collector becomes a bottleneck at scale
- [ ] How much of the "nodding" oracle is a pure test-runner vs an LLM check (keep it deterministic where possible)
