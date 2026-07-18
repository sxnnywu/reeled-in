# Reeled In — Parallel Implementation Plan

Last updated: 2026-07-18. Companion to `team-division.md`, `tech-architecture.md`, `PRD.md`.
People: **A** = Frontend & Design (Base44) · **B** = Scoring Engine (TRIBE/Modal) · **C** = Backend & Data (FastAPI/Mongo) · **D** = Generation & Intelligence (ElevenLabs/ffmpeg/Backboard).

## How to read this
Work is grouped into **phases** (logical stages, not fixed clock hours). Each task is tagged:
- **[PARALLEL]** — can run at the same time as others, no wait.
- **[WAITS ON X]** — cannot start until X is delivered.
- **[BLOCKER]** — until this is done, downstream work cannot begin.
The **Dependency Ledger** at the bottom lists every cross-person dependency in one place.

## Repo layout (annotated with owner)
```
reeled-in/
├─ CONTRACTS.md                 [P0 · whole team]  the two frozen contracts
├─ overview.md / tech-architecture.md / PRD.md / team-division.md / how-tribe-v2-works.md
├─ backend/
│  ├─ requirements.txt          [C]
│  ├─ .env.example              [C]
│  ├─ modal_app.py              [C owns; B adds the GPU function]
│  ├─ main.py                   [C]  FastAPI app served as a Modal ASGI endpoint
│  ├─ models/schemas.py         [C]  Pydantic models mirroring CONTRACTS
│  ├─ api/
│  │  ├─ routes_tests.py        [C]  POST/GET /tests
│  │  ├─ routes_score.py        [C]  POST /tests/{id}/score
│  │  ├─ routes_voice.py        [C→D] POST /voice-variants (calls D)
│  │  └─ routes_history.py      [C]  GET /history
│  ├─ db/
│  │  ├─ mongo.py               [C]  pymongo client + collections
│  │  └─ seed_demo.py           [C+B] load precomputed demo scores into Mongo
│  ├─ scoring/                  [B]
│  │  ├─ tribe_model.py         load TRIBE v2 on the Modal A100
│  │  ├─ extract.py             feature extraction wrappers
│  │  ├─ networks.py            reduce ~20k vertices -> 5 networks
│  │  ├─ metrics.py             peak / sustained / retention -> metrics
│  │  ├─ score.py               score(media) -> ScoreObject  (the public entrypoint)
│  │  └─ precompute.py          batch-score the demo variants
│  ├─ generation/              [D]
│  │  ├─ voice.py               ElevenLabs reads
│  │  ├─ overlay.py             ffmpeg audio mux onto base video
│  │  ├─ variants.py            generate_voice_variants(base, script) -> [videos]
│  │  ├─ llm.py                 Backboard suggestions + memory/RAG
│  │  └─ gemini.py              optional direct Gemini call
│  └─ mocks/
│     ├─ mock_score.py          [C]  canned ScoreObject (matches CONTRACTS)
│     └─ mock_variants.py       [D]  canned variant list
├─ frontend/                    [A · Base44 app + local mirror]
│  ├─ mock_api.json             [A]  canned Score Object for UI dev
│  └─ (Base44 screens/components live in the Base44 project)
└─ demo/
   ├─ dataset/                  [D]  base clips + generated variants
   └─ precomputed/              [B]  precomputed score JSONs
```

## Phase 0 — Contracts & Scaffold  [BLOCKER · whole team, together]
Nothing real starts until this is done. Do it synchronously in the first ~hour.
- **Whole team:** write `CONTRACTS.md` — (1) **Score Object** JSON schema (5 network time-series + metrics + winner flag), (2) **API** endpoints + request/response JSON, (3) **auth token** format, (4) **Mongo collection** shapes. This is the gate for everyone.
- **C:** create the repo skeleton (dirs above), `requirements.txt`, `.env.example`, empty `main.py` + `models/schemas.py`.
- **C:** provision **MongoDB Atlas** cluster; put the connection string in the shared secret store.
- **B:** create the **Modal** app; **accept the HuggingFace LLaMA-3.2 gated license now** (do this hour 1 — it's a hard prerequisite for any text/video run); smoke-test that an A100 boots.
- **A:** create the **Base44** project; scaffold empty screens.
- **D:** grab 1–2 base **stock clips**; get **ElevenLabs** + **Backboard** API keys.
- **Exit:** CONTRACTS.md frozen + committed, scaffold pushed → unlock Phase 1.

## Phase 1 — Build against mocks  [maximum parallelism · all four independent]
This is the big parallel window. No one waits on anyone (only on Phase 0).
- **A [PARALLEL]:** `frontend/mock_api.json` (canned Score Object from CONTRACTS) → build **Upload screen**, **Voice-A/B form**, **Results screen** (per-network bars + engagement curve) wired to the mock. Needs only CONTRACTS.
- **B [PARALLEL]:** `scoring/tribe_model.py` + a first `scoring/score.py` that returns a **real ScoreObject for one stock clip** (metrics can be rough). Needs only CONTRACTS (to match output shape). Depends on nobody.
- **C [PARALLEL]:** `models/schemas.py` (Pydantic from CONTRACTS), `db/mongo.py`, `mocks/mock_score.py`, and all `api/routes_*` wired to **stubs** → the full API runs end-to-end on fake data. Needs only CONTRACTS.
- **D [PARALLEL]:** `generation/voice.py` (ElevenLabs) + `generation/overlay.py` (ffmpeg) → produce 2–3 real **voice-variant files** from a stock clip; `mocks/mock_variants.py`. Needs only a stock clip.
- **Exit:** A has a clickable UI on mock data; B scores one clip for real; C's API serves fake data end-to-end; D produces real voice variants.

## Phase 2 — Complete the real pipelines  [mostly parallel · first join points]
- **B [PARALLEL → one join]:** `scoring/networks.py` (20k → 5), `scoring/metrics.py` (peak/sustained/retention), finalize `score.py`; then `scoring/precompute.py`.
  - **[WAITS ON D]** precomputing the *demo* variants needs D's demo dataset. **Mitigation:** B precomputes on stock clips first; D delivers the demo dataset by end of Phase 1 / start of Phase 2 so B is never blocked late.
- **C [PARALLEL]:** real `db/mongo.py` persistence (write/read tests, variants, scores), `routes_history.py`, auth-token verification. Still calling stubs for score/generate.
- **D [PARALLEL]:** `generation/variants.py` (finalize `generate_voice_variants`), `generation/llm.py` (Backboard suggestions + memory/RAG).
  - **[SOFT dep on C]** Backboard RAG reads a creator's history; use a **mock history JSON** (shape from CONTRACTS) until integration.
  - **Deliverable → B:** the **demo dataset** (this is the key early hand-off; deliver it as soon as possible).
- **A [PARALLEL]:** history view, winner-reveal, design polish — all still on the mock.
- **Exit:** real `score()`, real API+DB, real generators — all still independent via mocks/mock-history.

## Phase 3 — Integration  [the sequential join · do in this order]
The only part with hard waits. Kept short because every stub already matches CONTRACTS exactly.
1. **[C ← B]** C swaps the stub scorer → B's real Modal `score()`.  **WAITS ON:** B's `score()` deployed & callable.
2. **[C ← D]** C swaps the stub generator → D's real `generate_voice_variants()` + Backboard.  **WAITS ON:** D done.  *(Steps 1 and 2 are independent — can run at the same time.)*
3. **[A ← C]** A swaps `mock_api.json` → C's real endpoints.  **WAITS ON:** C's API live with real backends (1 & 2).
4. **[C+B]** `db/seed_demo.py` loads precomputed demo scores into Mongo.  **WAITS ON:** B precompute + D dataset + C Mongo. *(Parallel with step 3.)*

## Phase 4 — Demo hardening  [parallel again]
- **A:** winner-reveal polish, pitch visuals, tighten the 3-min flow.
- **B:** hand-validate 2 examples (pitch credibility), `keep_warm` during judging, laptop fallback path.
- **C:** make the precomputed demo path bulletproof; error handling; stable deploy.
- **D:** finalize the demo dataset + narrative; record a fallback demo video.
- **Team:** rehearse the live demo.

## Dependency Ledger (every cross-person dependency)
| # | What | Blocks | Type | Phase | Mitigation |
|---|------|--------|------|-------|------------|
| 1 | CONTRACTS.md (Score Object, API, token, Mongo shapes) | A, B, C, D — all real work | HARD gate | P0 | do first, together |
| 2 | B: HuggingFace LLaMA-3.2 gated access | any TRIBE run | HARD | P0 | accept license hour 1 |
| 3 | Infra: Modal (B,C), Atlas (C), Base44 (A), API keys (all) | each lane | HARD setup | P0 | provision in parallel hour 1 |
| 4 | D: demo dataset (base clips + variants) | B's precompute of demo scores | HARD (demo path) | end P1 | B uses stock clips meanwhile; D delivers early |
| 5 | B: real `score()` Modal fn | C integration step 1 | HARD | P3 | C runs on stub until then |
| 6 | D: real `generate_voice_variants` + Backboard | C integration step 2 | HARD | P3 | C runs on stub until then |
| 7 | C: real API endpoints | A integration step 3 | HARD | P3 | A runs on mock_api until then |
| 8 | B precompute + D dataset + C Mongo | seed_demo (demo path) | HARD | P3/4 | sequence at integration |
| 9 | C: Mongo history shape | D's Backboard RAG | SOFT (shape in CONTRACTS) | P2 | D uses mock history |
| 10 | A: token format | C token verification | SOFT (in CONTRACTS) | P2 | agree in P0 |

## Critical path & parallelism summary
- **Critical path:** CONTRACTS (P0) → **B's TRIBE `score()`** (P1–P2, the riskiest/longest task) → C integration (P3) → seed + demo (P4). **B is the long pole** — keep them unblocked; they need nobody except CONTRACTS, LLaMA access, and a clip.
- **Biggest parallel window:** Phase 1 — all four fully independent.
- **Only real serialization:** the Phase 3 integration order (B→C and D→C, then C→A). Everything else overlaps.
- **Where slack goes** (if B lands early or D's lane is light): precompute more demo variants, hand-validate examples, polish the winner-reveal.
