# 🎣 Reeled In

**Neural A/B testing for short-form video — know which edit hooks the brain *before* you post.**

> Hack the 6ix 2026 · Toronto · Jul 17–19 · (pivot from the earlier "Loopy" concept)

## What it does

Upload two or more variants of a Reel/TikTok — or give us a voiceover script and we'll generate voice variants for you — and Reeled In predicts how the human brain engages with each one using Meta's open-source **TRIBE v2** brain encoding model. We reduce the predicted whole-brain fMRI response to **five interpretable functional networks** (visual, auditory, language, motion, default-mode), compute engagement metrics over time, and declare a winner with a per-network breakdown — all pre-publish, in seconds, no focus groups.

The name: Instagram **Reel** + "**reeling you in**." The metric is literally whether the content hooks and holds the viewer's brain.

## Why

Short-form video has a huge number of creative variables — hook, music, clip order, pacing, on-screen text, CTA — and no cheap pre-publish signal for which combination holds attention. Creators guess and find out after posting or after burning ad spend. Real testing today means posting variants live or expensive human focus groups.

**Honesty line (it's in our pitch on purpose):** TRIBE predicts *neural activation*, not emotion or purchase intent. This is a fast, directional, pre-flight engagement screen — a proxy, not ground truth.

## MVP scope (locked)

Two test types:

1. **Upload & compare** — user uploads 2+ finished video variants; we score and compare. No auto video editing in MVP.
2. **Voice A/B** — user uploads one base video + a voiceover/CTA script; we generate several voice reads via ElevenLabs, overlay each onto the video (ffmpeg audio swap), and score them. The one bit of auto-generation we do ship.

**What "winner" means:** per variant, from the 5 network time-series we compute **peak** engagement, **sustained** engagement (area under curve), and **retention through the CTA** (does engagement hold to the end or collapse). The creator picks an objective; winner = highest composite on it.

## Architecture

```
[Creator's browser]
      |  upload variants / voice script
      v
[Base44 frontend]  --login-->  Base44 built-in auth
      |  authenticated request
      v
[FastAPI on Modal]  -- Python backend / orchestrator --------+
   |-> Modal GPU fn: TRIBE v2 scoring   (or precomputed)     |
   |-> ElevenLabs: generate voice takes (Voice A/B mode)     |
   |-> Backboard: variant suggestions + memory/RAG           |
   |-> MongoDB Atlas: store & fetch tests/scores (pymongo)   |
      |  results JSON  <---------------------------------------+
      v
[Base44 frontend]  renders winner + per-network curves
```

| Piece | Role |
|---|---|
| **Base44** | Frontend (upload UI, results screen) + built-in user auth |
| **FastAPI on Modal** | Python backend — all real logic, secrets, orchestration |
| **Modal GPU function** | Runs TRIBE v2 on an A100 40GB; scale-to-zero; demo scores precomputed |
| **MongoDB Atlas** | System of record (tests, variants, scores, users) — Python-only access via pymongo |
| **Backboard** | LLM + memory/RAG — plain-English summaries + "learns your style" personalization |
| **ElevenLabs** | Voice-variant generation for Voice A/B |

Why two "backends": Base44 can't run heavy ML Python or reliably reach Atlas from Deno; Python isn't a nice frontend with login. Secrets and heavy work live in Python; Base44 is the face and front door.

## Sponsor / prize tracks

- **Base44** — the app is built on it (frontend + auth) → Venture Builder. Validation via **free beta / waitlist** (TRIBE's CC BY-NC license means no paid product).
- **ElevenLabs** — powers the Voice A/B test type.
- **MongoDB Atlas** — system of record.
- **Backboard** — LLM + memory/RAG layer.
- *Optional, decide by time:* Auth0 (vs Base44 native login), one direct Gemini call (MLH prize).
- **Out:** Phoebe — analysis tool, not real-world coordination; forcing it in is scope creep.

## Team (4) — build split

Four parallel lanes, two frozen contracts (the **API contract** and the **Score Object**) agreed in hour 0–1 and written into `CONTRACTS.md` — after that everyone builds against mocks and nobody blocks anybody. Full detail: [`team-division.md`](team-division.md).

| Lane | Owns | Interface |
|---|---|---|
| **A — Frontend & Design** (Base44) | Whole Base44 app: upload, voice-script form, results/winner screen, history, login, design system, pitch visuals | Consumes the API response JSON (mock first) |
| **B — Scoring Engine** (TRIBE on Modal) | TRIBE v2 on A100, 5-network reduction, metrics, Score Object, precomputed demo scores | `score(media) -> ScoreObject` |
| **C — Backend & Data** (FastAPI + MongoDB) | All endpoints, Mongo schema + pymongo, auth verification, orchestration — the integration hub | Defines the REST contract; calls B and D |
| **D — Generation & Intelligence** (ElevenLabs + ffmpeg + Backboard) | Voice-A/B pipeline, Backboard LLM/memory, optional Gemini, demo dataset curation | `generate_voice_variants(...)`, `suggest(...)`, `tips(...)` |

```
A (UI)        -- calls --> C (API)
C (API)       -- calls --> B (score)  and  D (generate)
D (variants)  -- feeds --> B (to score)
B (scores)    -- stored -> C (Mongo)     [precomputed demo path]
```

Integration order (last third): C swaps in B's real scorer → C swaps in D's real generators → A swaps mock API for C's real endpoints → precomputed demo scores seeded into Mongo. Riskiest lane is B (isolated on purpose); broadest is C. Per-person plan files land in the repo as written — name assignments to be added here as they're confirmed.

## Docs

- [`overview.md`](overview.md) — project overview: scope, prize tracks, hackathon logistics, open decisions
- [`team-division.md`](team-division.md) — the 4-lane split, frozen contracts, dependency map, integration order
- [`PRD.md`](PRD.md) — product requirements: users, features, metric definition, risks
- [`tech-architecture.md`](tech-architecture.md) — full system design, endpoints, data flow, secrets
- [`how-tribe-v2-works.md`](how-tribe-v2-works.md) — TRIBE v2 deep-dive: pipeline, the five networks, limits, runtime

## Science caveats (we say these out loud)

- **Activation ≠ outcome.** A region lighting up ≠ "this ad sells." It's an engagement proxy.
- **fMRI is temporally sluggish** (BOLD lag ~4–6 s, output ~1 Hz) → reliable at the ~5 s segment level, not per-frame.
- **Out-of-distribution:** TRIBE trained on long-form naturalistic media; punchy short-form is directional.
- **License:** TRIBE v2 is CC BY-NC 4.0 — hackathon demo fine; no paid go-to-market.

## Open decisions

- Auth0 vs Base44 native login
- Direct Gemini call vs Backboard-only LLM layer
- 3D brain viz vs charts-only results screen
- Video-editing auto-gen (stretch; music swap first if attempted)
- Final team split (see table above)

## Hackathon logistics

36 h build window (9:30 PM Fri → 9:30 AM Sun) · initial Devpost by 11:59 PM Sat · 5-min live pitch, public repo, demo video · judged on Technical Difficulty, Uniqueness, Design, Completeness. The TRIBE scoring pipeline is our technical-difficulty core — the judging rubric penalizes pure API wrappers, and our value is in variant handling, network-reduction + metric design, winner logic, and UX.
