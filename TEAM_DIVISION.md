# Reeled In — Team Division (4 people)

Last updated: 2026-07-18. Companion to `TECH_ARCHITECTURE.md` and `PRD.md`.

## Principle
Four parallel lanes with **two frozen contracts** so nobody blocks anybody. The riskiest piece (the TRIBE scoring engine) is isolated behind a data contract — if it runs slow, the other three never stall, because they build against a mock.

## Hour 0–1: freeze two contracts (whole team, together)
Everything parallelizes once these are agreed and written into a shared `CONTRACTS.md` (treat as law):
1. **The API contract** — endpoints + request/response JSON. Owned by C, agreed with A.
2. **The Score Object** — the shape of a scored variant: the 5 network time-series (visual, auditory, language, motion, default-mode) + metrics (peak, sustained, retention-to-CTA, winner flag). Owned by B; consumed by A (display) and C (store).

After this, everyone codes against mocks.

## The four lanes

### Person A — Frontend & Design (Base44)   [you]
- **Owns:** the whole Base44 app — upload screen, Voice-A/B script form, results/winner screen (per-network bars + engagement-over-time curve), history view, login (Base44 auth), the design system, and the demo/pitch visuals.
- **Does NOT own:** any scoring, data, or generation logic.
- **Interface:** consumes the API response JSON.
- **Starts immediately with:** a mock API returning a hardcoded Score Object → builds the entire UI without waiting. Integrates the real API at the end.

### Person B — Scoring Engine (TRIBE on Modal)   [strongest ML person]
- **Owns:** deploying TRIBE v2 on a Modal A100, feature extraction, video → raw brain output → reduce to 5 networks → compute metrics → emit a Score Object. Also precomputes the demo variants' scores.
- **Does NOT own:** the API, the DB, the UI, variant generation.
- **Interface:** one function `score(media) -> ScoreObject`, exposed as a Modal call for C.
- **Starts immediately with:** any stock clips; no teammate dependency. Critical path — isolated on purpose so its risk is contained.

### Person C — Backend & Data (FastAPI + MongoDB)   [strongest backend / integrator]
- **Owns:** the FastAPI app on Modal (all endpoints), MongoDB Atlas schema + pymongo persistence, auth-token verification, and the orchestration that calls B's scorer and D's generators. The integration hub.
- **Does NOT own:** model internals, UI, generation internals.
- **Interface:** defines the REST contract (with A); calls B and D as functions.
- **Starts immediately with:** stub functions for B and D (canned Score Objects / canned variants) → builds and tests the whole API + DB against stubs, swaps in real ones as they land.

### Person D — Generation & Intelligence (ElevenLabs + ffmpeg + Backboard)
- **Owns:** the Voice-A/B pipeline (ElevenLabs reads → ffmpeg audio overlay onto a base video → variant files), the Backboard LLM + memory/RAG layer (suggestions + personalized tips), the optional Gemini call, AND curating the demo dataset (the real example videos/variants for the precomputed demo).
- **Does NOT own:** the API surface, the model, the UI.
- **Interface:** `generate_voice_variants(base_video, script) -> [videos]`, `suggest(...) -> [...]`, `tips(history) -> text`.
- **Starts immediately with:** a base stock clip; independent of teammates. Feeds variant files to B and tips/suggestions to C.

## Dependency map (who feeds whom)
```
A (UI)        -- calls --> C (API)
C (API)       -- calls --> B (score)  and  D (generate)
D (variants)  -- feeds --> B (to score)
B (scores)    -- stored -> C (Mongo)     [precomputed demo path]
```
All four build against mocks from hour 1; real wiring happens at integration.

## Integration order (last third of the hack)
1. C swaps stub scorer → B's real Modal function.
2. C swaps stub generator → D's real ElevenLabs/Backboard.
3. A swaps mock API → C's real endpoints.
4. B's precomputed demo scores seeded into Mongo (B + C) for the bulletproof demo.

## Balance & parallelism notes
- **Riskiest = B** (model wrangling, gated LLaMA, GPU) — isolated so it can't block.
- **Broadest = C** (touches everything) → your best integrator; keep them off feature depth so they stay free to wire.
- **A and D are fully independent from hour 1** (mock JSON / stock clip) → maximum early parallelism.
- Slack (B lands early, or D's lane is light) → precompute more demo variants, hand-validate a few examples (pitch credibility), polish the winner-reveal.

## Auth (small)
Default = Base44 native login (A builds it, C verifies the token). Only if you want the Auth0 prize does this become an A+C task; otherwise leave it.
