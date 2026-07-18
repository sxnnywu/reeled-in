# Person D — Interface & Design — Plan & Learnings (Kimi)

Share-out doc for **Section D**: the dashboard, the spec-registration surface, the
visual system, and the demo narrative. Mirrors the shape of `PERSON_C_PLAN.md`.

Source-of-truth precedence: `SHARED_CONTRACTS.md` > `TEAM_DIVISION.md` > `ARCHITECTURE_FLOW.md`.
This plan schedules work on top of those; it never overrides a contract.

---

## 1. What Section D is (scope)

Person D owns the **Interface & Design** workstream (`workstreams/interface-and-design/PLAN.md`)
plus the presenter/demo role. Concretely, D ships the one screen everyone else's
work becomes visible through:

- **Fleet view** — sandbox state counts + a live grid of N sandbox tiles coloured by `SandboxState`.
- **Traffic feed** — a readable, sampled stream of `agent_message` events (agent → agent).
- **Report view** — summary + severity-coded `Finding`s + stats charts (completion, stall, cost, divergence, nod rate).
- **Spec-registration form** — register a `LoopSpec`; JSON-paste is acceptable for MVP.
- **Demo narrative + deck** — the "one run is an anecdote; QA needs a distribution" story, rehearsed.
- **Nice-to-have** — ElevenLabs voice narration of the report summary.

D does **not** own backend logic, schemas, orchestration, or analysis. D consumes
the contract; D never redefines it.

Why this matters strategically: HackThe6ix judges on **Technical Difficulty · Uniqueness ·
Design · Completeness**. Two of those four axes (Design, Completeness) *are* this
workstream. A polished, working dashboard is how the whole team's technical depth
becomes legible to a judge in a 3-minute pitch.

---

## 2. Hackathon track(s) this is for

| Track | Tool | What D ships for it | Priority |
|---|---|---|---|
| **Best Use of Base44** | Base44 | The entire dashboard (fleet / traffic / report) + spec-registration form, built on Base44 and wired to the FastAPI backend | **Primary** |
| **ElevenLabs** | ElevenLabs | Voice narration of the QA report summary ("your loop nods through a broken fix 3.6% of the time…") | Nice-to-have |
| Overall judging: **Design + Completeness** | Base44 + design templates | Rehearsed happy path + failure-finding moment; visual polish from our templates | Always-on |

Base44, ElevenLabs, Backboard, Warp, MongoDB, Gemini, Figma, Unifold, and Phoebe are all
confirmed HackThe6ix 2026 sponsors. D's declared tracks are **Base44** (owned) and
**ElevenLabs** (if green). Do not over-declare tracks D didn't actually wire —
incoherent track claims cost us on the technical-difficulty axis.

---

## 3. Tools D uses (and exactly how)

| Tool | Role for D | How it's used | Notes / limits (researched) |
|---|---|---|---|
| **Base44** | Primary app builder for the dashboard | Vibe-code the three views + spec form; backend-first (its own DB/entities), then wire to our FastAPI routes | Native real-time (“live updates, no WebSocket config”) applies to **Base44's own entities**, *not* to an external socket. Reach our backend via **backend functions (polling)** or a registered **OpenAPI integration**. See §5. |
| **Design templates** (Figma) | Visual system | Apply existing palette / type / layout shells; do **not** invent a new visual language mid-build | Templates are final per the workstream plan. Figma is a sponsor; keep source files tidy in case we show them. |
| **ElevenLabs** | Report narration (optional) | TTS the report `summary` string into a short voiceover for the demo | Only if the happy path is already green. Scripted, pre-rendered clip is safer than live TTS on stage. |
| **Contract API (FastAPI)** | Data source | Consume §5 routes only; mirror §3 shapes in TS exactly; `run_id` everywhere | 404 on `/report` until ready is expected, not an error — render an empty/"analysis running" state. |

**Env / access D needs:** a Base44 workspace (Builder plan or higher for backend
functions + secrets), the deployed FastAPI base URL, and `ELEVENLABS_API_KEY`
(nice-to-have only). D holds no MongoDB/Gemini keys — D never touches the store directly.

---

## 4. Screens, mapped to the contract (build against these shapes)

Every view mirrors `SHARED_CONTRACTS.md` §3 field-for-field. Design against C's
**already-verified** numbers so mocks match reality on day one:

> Completion **70%** · Stall **30%** · Divergence **37.9%** · cost p95 **3,779** vs mean **1,806** tok
> Nod rate **3.6%** (2/56 approvals passed a broken fix) · Triage accuracy **87.5%**
> Top fragile handoffs: `infra_fixer→triage` 100%, `evaluator→dep_fixer` 70%

| View | Contract route(s) it reads | Key fields (§3) | Design intent |
|---|---|---|---|
| **Spec form** | `POST /api/specs`, then `POST /api/runs` `{spec_id, n_sandboxes, seed_strategy}` | `LoopSpec`, `RunBatch` | MVP = JSON paste + N + seed strategy (`"identical"｜"varied"`) + launch |
| **Fleet** | `GET /api/runs/{run_id}` (counts) · `GET /api/runs/{run_id}/sandboxes?state=` (grid) | `SandboxState`, `SandboxRun.iterations/termination_reason/total_tokens` | State-count header + N-tile grid; colour by state; the grid "lighting up" is the *distribution* money-shot |
| **Traffic** | `GET /api/runs/{run_id}/events?type=agent_message&limit=` (or WS) | `Event.from_agent/to_agent/payload/ts` | Sampled, human-readable agent→agent lines; NOT the full firehose |
| **Report** | `GET /api/runs/{run_id}/report` (404 until ready) | `Report.summary/findings/stats`, `Finding.severity/title/description/evidence_sandbox_ids` | Summary → severity-coded findings → stat charts. The **nod-rate** finding is the hero card |

---

## 5. Live-data architecture (the one real decision to get right)

Base44 cannot subscribe to our `/ws/runs/{run_id}` socket directly. Three options,
in build order:

1. **Polling (primary, ships first).** A Base44 backend function calls
   `GET /api/runs/{run_id}` + `/sandboxes` + `/events` on an interval
   (`DASHBOARD_POLL_MS = 2000`, already in the contract). Refreshes fleet counts,
   grid, and traffic. Zero coordination cost with B beyond the routes existing.
2. **Entity-mirror for native real-time (enhancement).** A backend function pulls
   sampled events and writes them into a Base44 entity; Base44's built-in live
   subscription then pushes UI updates with no polling flicker. Do this only for the
   traffic feed if polling looks laggy on stage.
3. **Direct WebSocket (only if trivial).** If B exposes a simple bridge, consume it;
   otherwise skip — the demo does not depend on it.

**Decision:** build on **polling** first (matches the contract's own fallback in
`PARALLEL_IMPLEMENTATION_PLAN.md §7`). Treat WS/entity-mirror as polish, not a gate.

---

## 6. Build phases (D's swimlane, H0 = build start)

### Phase 0 — Confirm + set up (H0–H1)
- [ ] Confirm **Base44** for the dashboard; log the decision in `INTEGRATIONS_AND_STACK.md`.
- [ ] Create the Base44 workspace/app; apply design templates (palette, type, layout shells).
- [ ] Confirm live mechanism = **polling first** (§5); note it so no one re-litigates.

### Phase 1 — Mock everything against fake contract data (H1–H3)
- [ ] Mock all three views + spec form using contract-shaped fake JSON (no backend needed).
- [ ] Hard-code C's verified numbers (§4) so mocks look like the real demo.
- [ ] TS/data models mirror §3 exactly — `run_id` everywhere, no invented fields.

### Phase 2 — Wire to real endpoints (H3–H20)
- [ ] Typed API client against §5 routes; polling loop at `DASHBOARD_POLL_MS`.
- [ ] Fleet + traffic on live data as B's routes come online.
- [ ] Report view on real `Report` JSON — **pair with C** once the report chain is stubbed (C is the natural helper per `PARALLEL_IMPLEMENTATION_PLAN §1`).
- [ ] Empty/"analysis running" state for the `/report` 404 window.

### Phase 3 — Swap, polish, rehearse (H20–H32)
- [ ] Swap all mocks for real data.
- [ ] Rehearse the "**anecdote vs distribution**" narrative **end-to-end twice**; lock ONE happy path + ONE failure-finding moment (the nod-rate reveal).
- [ ] If green: ElevenLabs narration of the report summary (pre-rendered clip).

### Phase 4 — Freeze + buffer (H32–H36)
- [ ] Feature freeze; bug-fixes on the demo path only.
- [ ] Record backup demo video. Submit Devpost stub early; **declare only Base44 (+ ElevenLabs if wired)**.

---

## 7. Deliverables checklist

- [ ] Fleet view: state counts + live sandbox grid
- [ ] Traffic feed: sampled `agent_message` stream, readable
- [ ] Report view: summary, severity-coded findings, stat charts (nod rate is the hero)
- [ ] Spec-registration form (JSON paste OK for MVP)
- [ ] Demo script rehearsed twice + deck on our templates
- [ ] (Nice-to-have) ElevenLabs report narration

---

## 8. What D needs from others

- **A (Orchestration):** fleet state-counts shape in `GET /api/runs/{run_id}`; confirm what "live traffic" means on screen (sampled, not full stream). ~~Which demo loop is canonical?~~ **Resolved: `example-loops/morning-triage.md` IS the 6-agent CI/CD triage loop** — same loop, different naming. `backend/examples/ci_triage_spec.json` is its LoopSpec. C's verified numbers (§4) are for this loop. Demo script is unblocked.
- **B (Data-Capture):** WebSocket vs polling shape; the `/sandboxes` and `/events` query routes live so polling works; sampled-traffic payload shape.
- **C (Analysis):** **report JSON sign-off before I build the report view** — `Report` in `SHARED_CONTRACTS §3` + the `stats` dict shape from `pipelines.compute_stats`. C's current numbers (§4) are what I design the report cards around.

## 9. Risks & contingencies

- **Don't block on live data** — every view is built on fake contract-shaped data first, so D is never waiting on a real endpoint.
- **Base44 real-time ≠ external socket** (researched) — lead with polling; don't burn hours trying to consume `/ws` directly.
- **Don't restyle mid-build** — templates are final.
- **Demo loop resolved** — morning-triage.md = the 6-agent CI-triage loop = what C already has numbers for. Build views loop-agnostically (they render whatever `Report`/`SandboxRun` contains), which is already the plan.
- **Live TTS is risky on stage** — pre-render the ElevenLabs clip.
- **If B's WebSocket is late** — polling `GET /api/runs/{run_id}` at `DASHBOARD_POLL_MS` is the plan, not a downgrade.

## 10. Demo narrative (the money path)

1. Register the loop (spec form) → launch **≥50** sandboxes.
2. Fleet grid lights up live — "this is the same loop, a thousand times, not once."
3. Traffic feed shows agents handing off — then a cluster visibly **ping-pongs / stalls**.
4. Open the report → the **nod-rate** finding: *"the reviewer approved a fix that fails the answer key 3.6% of the time"* — the thing a single run can never show.
5. (Optional) ElevenLabs reads the one-line verdict.

Protect that path above all else.

---

## Research notes (sources)

- HackThe6ix 2026 — dates **Jul 17–19**, **$15K** pool; confirmed sponsors incl. Base44, ElevenLabs, Backboard, Warp, MongoDB, Gemini, Figma, Unifold, Phoebe: https://hackthe6ix.com/
- Judging axes (Technical Difficulty · Uniqueness · Design · Completeness) + submission reqs (Devpost, demo video, public repo, in-person pitch), from the 2025 edition structure: https://hackthe6ix2025.devpost.com/
- Base44 external-API integration = backend functions (polling) or OpenAPI integrations; native real-time is for Base44's own entities: https://docs.base44.com/Integrations/Using-integrations · https://base44.com/backend

---

## Living Status (update every session)

**Done:** —
**In progress:** Plan authored (this file).
**Next:** Phase 0 — confirm Base44 + create workspace + apply templates.
**Handoff notes:** Live data = polling-first (Base44 can't consume our `/ws` directly). Report view blocked on C's `Report`/`stats` shape sign-off. Demo failure-moment blocked on team picking CI-triage vs morning-triage.
