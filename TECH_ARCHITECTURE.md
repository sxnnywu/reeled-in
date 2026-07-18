# Reeled In — Technical Architecture

Last updated: 2026-07-18. Companion to `OVERVIEW.md` and `PRD.md`.

## Stack at a glance
- **Base44** — frontend (upload UI, results screen) + built-in user auth. The "storefront + front door."
- **Python backend: FastAPI served on Modal** — all real logic. Owns the endpoints Base44 calls, MongoDB reads/writes, LLM/memory (Backboard), and voice generation (ElevenLabs).
- **Modal GPU function** — runs TRIBE v2 (A100 40GB). Called by the FastAPI layer; scale-to-zero.
- **MongoDB Atlas** — system of record (tests, variants, scores, users). Touched only by Python (pymongo).
- **Backboard** — unified LLM + embeddings/RAG/memory. The "learns your style" layer.
- **ElevenLabs** — generates voiceover variants for the Voice A/B test type.

**Why two "backends":** Base44 can't run heavy ML Python or reliably reach Atlas from its Deno functions (the native Mongo driver from Deno is flaky and the Atlas Data API is deprecated/EOL); Python isn't a nice frontend with login. Different jobs. Secrets + heavy work live in Python; Base44 is the face + front door.

## End-to-end data flow
```
[Creator's browser]
      |  upload variants / voice script
      v
[Base44 frontend]  --login-->  Base44 built-in auth
      |  authenticated request (short-lived token)
      v
[FastAPI on Modal]  -- the Python backend / orchestrator --+
   |-> Modal GPU fn: TRIBE v2 scoring   (or precomputed)   |
   |-> ElevenLabs: generate voice takes (Voice A/B mode)   |
   |-> Backboard: variant suggestions + memory/RAG         |
   |-> MongoDB Atlas: store & fetch tests/scores (pymongo) |
      |  results JSON  <-------------------------------------+
      v
[Base44 frontend]  renders winner + per-network curves
```

## Components in detail

### 1. Base44 — frontend + auth
Owns: upload screen, the voice-script form, the results/winner screen (including the **side-by-side player**: video + brain-frame flipbook synced per second + the live explainer caption), and login (**Auth0 client-side SPA SDK**; the Base44 app is Public). Calls the FastAPI backend directly over HTTPS with the user's Auth0 JWT as a Bearer token; C verifies it against Auth0's JWKS and CORS locks the origin. No Base44 backend-function courier — backend functions are Builder-plan-only and we stay free (see CONTRACTS §6).

### 2. FastAPI on Modal — the Python backend
The orchestrator; where all real logic and secrets live. Runs as a Modal ASGI web endpoint (CPU, cheap, scale-to-zero) that invokes the GPU function only when scoring is needed.
Endpoints (rough):
- `POST /tests` — create a test (upload mode or voice mode); store metadata in Mongo, return test_id.
- `POST /tests/{id}/score` — run/return scoring for the test's variants.
- `GET  /tests/{id}` — fetch results (from Mongo; precomputed for demo).
- `POST /voice-variants` — Voice A/B: script -> ElevenLabs reads -> overlay -> variants.
- `GET  /history` — a creator's past tests (feeds Backboard memory).
Responsibilities: variant handling, calling the GPU scorer, the 5-network reduction + metric computation, Mongo persistence, Backboard + ElevenLabs calls.

### 3. Modal GPU function — TRIBE v2 scoring
A100 40GB function that loads TRIBE + the three encoders (weights cached on a Modal volume; keep_warm during judging). Input: a video/audio/text variant. Output: (n_timesteps x ~20k vertices) -> reduced to 5 network time-series, plus a **brain-frame flipbook** (one PNG per second, rendered with nilearn/pycortex) and a **region_timeline** (top region/network per second). **Demo strategy: precompute** all demo variants' scores into Mongo ahead of time so the live pitch never waits on a cold GPU; keep one live path for the "score a fresh one" flourish.

### 4. MongoDB Atlas — data
Collections (draft): `users`; `tests` (owner, type, created_at); `variants` (test_id, media ref, params); `scores` (variant_id, 5 network series, metrics, winner flag). Accessed only from FastAPI via pymongo — never from Base44 directly.

### 5. Backboard — LLM + memory/RAG
Three jobs: (a) suggest hook/CTA/copy variants; (b) RAG over a creator's past tests so recommendations personalize over time ("your face-first hooks spike visual+DMN — do it again"); (c) the **brain-animation explainer** — turns B's region_timeline into plain-English per-second captions ("your brain is locking onto a face — good hook"). Called from FastAPI.

### 6. ElevenLabs — voice-variant generation
Voice A/B flow: creator submits a voiceover/CTA script -> FastAPI calls ElevenLabs for N reads (different voices/tone/pace) -> each read is muxed onto the base video via ffmpeg (simple audio swap) -> each variant scored by TRIBE (drives auditory/language/default-mode). The only auto-generation in the MVP.

### 7. Gemini
Gemini: a direct Gemini API call powers the hook/copy suggestions (D owns it) — claims the MLH Gemini prize. Backboard owns RAG/memory + the explainer. Auth: **Auth0** client-side SPA SDK (also claims the MLH Auth0 prize) — see CONTRACTS §6.

## The scoring pipeline (what "winner" means)
Per variant: TRIBE -> 5 network time-series (visual, auditory, language, motion, default-mode) -> metrics: **peak** engagement, **sustained** engagement (area under curve), and **retention through the CTA** (does engagement hold to the end vs collapse). Winner = highest composite on the objective the creator picks (e.g. "hold attention to the CTA"). Caveats: activation != outcome; ~1 Hz temporal smoothing (see overview).

The same per-second predictions feed the **brain animation**: each second's ~20k-vertex map is rendered to a brain PNG (`brain_frames`, the flipbook) and reduced to a top-region label (`region_timeline`); D's explainer narrates it. Rendering is ~1 Hz — the frontend interpolates between frames for smooth playback.

## Security / secrets
All third-party API keys (Modal, Mongo, Backboard, ElevenLabs, Gemini) live server-side in the Python backend. The browser never sees them. The frontend holds only the user's own Auth0 JWT plus public Auth0 config; C authenticates each request by verifying that JWT against Auth0's JWKS, with CORS restricting the origin. (No Base44 "courier" function — backend functions are Builder-plan-only, and we stay free.)

## Sponsor -> component map
| Sponsor | Where it lives |
|---|---|
| Base44 | Frontend (Public app) + the launch/validate story ($2k) |
| Auth0 | Login — client-side SPA SDK; C verifies the JWT via JWKS (MLH Auth0 prize) |
| ElevenLabs | Voice-variant generation (Voice A/B) |
| MongoDB Atlas | System of record (via pymongo) |
| Backboard | LLM + memory/RAG layer + the brain-animation explainer |
| Gemini | Direct call — hook/copy suggestions |
| TRIBE (ours) | Modal GPU pipeline — the technical-difficulty core |

## Open decisions
- Auth: DECIDED — **Auth0** client-side SPA SDK (Base44 app Public); C verifies the JWT via Auth0 JWKS. See CONTRACTS §6.
- Gemini: DECIDED — direct call for suggestions (Backboard owns RAG/memory + explainer).
- 3D brain viz vs charts-only.
- Video-editing auto-gen (stretch); which variable first.
- Team size / who builds what.
