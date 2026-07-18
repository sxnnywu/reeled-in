# reeled in — Session Handoff / Project State

Continuation doc so any agent (or teammate) can pick up mid-build without the chat
history. Written from **Person A (Kimi — Frontend & Design / Base44 + integration)**'s
seat, but useful to everyone. Read `CONTRACTS.md` (the law) alongside this.

Last updated: 2026-07-18.

---

## 1. What the project is
**reeled in** — neural A/B testing for short-form video. Upload 2+ Reel/TikTok variants
(or one base video + voiceover scripts we generate), predict brain-response engagement
via Meta's TRIBE-style scoring, reduce to 5 networks, compute metrics, and call a winner
*before* posting. Honest framing: it's a directional engagement proxy, not a virality
guarantee.

## 2. Team
- **A — Kimi:** Frontend & Design (Base44) + the A↔C integration. ← this handoff's author.
- **B — Jay:** Scoring engine (TRIBE on Modal A100), 5-network reduction, metrics, brain frames.
- **C — Seb:** Backend & Data (FastAPI on Modal + MongoDB Atlas), the API, auth, media serving.
- **D — Sunny:** Generation & Intelligence (ElevenLabs voice, Gemini `/suggest`, Backboard `/tips` + `/explain`).

## 3. Where the code lives (important)
- **Frontend source is NOT in this git repo.** It lives in the **Base44 project** and is
  edited through Base44's AI builder by *pasting prompts* (Base44 = React + Vite + Tailwind).
  This repo's `frontend/` only holds `mock_api.json`. To change the UI you write a Base44
  prompt; you do **not** edit repo files. After any Base44 change you must **Publish** (and
  hard-refresh) for `https://reeled-in.base44.app` to update — this has bitten us twice.
- **This git repo** holds: `backend/` (Seb + Jay + Sunny's code), `CONTRACTS.md`, the docs,
  `testing/TEST_LOG.md`, and `demo/`.

## 4. Live URLs & operational facts
- **Frontend (live):** https://reeled-in.base44.app
- **Backend API (live, persistent Modal deploy):** https://jaychopra05--reeled-in-api.modal.run
  - Routes under `/api/...`; media at `/api/media/{media_key}`. CORS open for the Base44
    origin + localhost. Runs a **dev-fallback user** until Auth0 is turned on (no token needed yet).
- **Frontend API client:** `src/lib/api.js` in the Base44 project — one module, all fetch calls.
  Auth is a **one-line hook**: `setAuthToken(token)` will attach `Authorization: Bearer …`.
- **Auth0 (SPA, public config — safe to share):** domain `dev-1xz0uq0mv6hryu17.us.auth0.com`,
  clientId `SZMANyKXCW3qLnID3Lk9BO6evLOjZAMf`, **audience `https://api.reeledin.app/`**
  (MUST pass audience or the API rejects the id-token; access tokens only; popup mode;
  `@auth0/auth0-react`). Base44 + localhost already whitelisted in Auth0.
- **Demo test IDs:**
  - `test_seed0000001` — seeded "Pacing A/B", complete, winner B, but `brain_frames: []`.
  - A **flipbook demo test seeded from B's precompute (IMG_7024 vs 7025)** exists — it has
    *real* brain frames. Get its id from `GET /api/history`; that's the one for the demo.

## 5. Current status
**Integration (A↔C) — read paths done, on real data:**
- ✅ **Results** renders live data (winner, 4 metrics/variant, 5 network curves + composite,
  timeline driven off `duration_sec`). Loads `?test=<id>`, defaults to the seed.
- ✅ **History** lists real tests.
- ✅ **Home** leads with "upload your variants"; voice framed as the optional branch.
- ✅ **New Test upload create flow** works end-to-end — verified with `test_9935ff4473b4`
  (2 Jay-intro clips): scored `complete`, winner A, **uploaded videos play (media serves 206)**.
- ⏳ **Voice A/B** create flow + `/suggest` **transcript prefill** — implemented, not yet
  tested with a talking-head (speech) clip.
- ⏳ **Auth0 login** — not wired. API is on the dev-fallback user. This is A's main remaining task.

## 6. Integration gotchas already discovered (don't re-learn these)
- `GET /api/tests/{id}` → `{ test, variants, scores }`. The **per-second data (networks,
  engagement, brain_frames, region_timeline, duration_sec) lives in the SCORE objects**, not
  the variants. Match `score.variant_id === variant.id`. (The api.js normalizer merges them.)
- **Variant id field is `id`; score id field is `variant_id`.**
- `GET /api/history` `TestSummary.winner` is an **object** `{ variant_id, label }` (not a
  string); there is **no `winner_overall`**. (Rendering the object as text crashed History; fixed.)
- Scores are **joint/shared-scale normalized per test** (CONTRACTS §3) — comparable only
  **within** a test, never across tests. Don't build cross-test score comparisons.

## 7. Open items / next steps (priority order)
1. **Wire Auth0 login** (frontend) — `@auth0/auth0-react`, `Auth0Provider` with the config in
   §4, `authorizationParams.audience` set, popup mode; get token via `getAccessTokenSilently`,
   feed to `setAuthToken()`. Then tell **Seb** → he flips real auth on (one env change).
2. **Test the Voice A/B create flow** with a talking-head clip: Suggest → confirm the script
   box prefills with the transcript → Generate → Score → Results.
3. **Brain-frame flipbook** (the demo "wow"): live-scored tests *list* `brain_frames` but the
   PNGs **404** (not saved to the volume during live scoring — see test #4 in TEST_LOG). Real
   PNGs exist only via B's precompute (7024 vs 7025). Two needs: (a) backend writes the PNGs
   for the demo test / live path; (b) frontend renders `brain_frames[t]` as
   `<img src={API_ROOT}/api/media/{key}>` (currently a placeholder even when frames exist).
4. **Wire `/explain`** (`POST /api/tests/{id}/explain` → per-second captions) for the brain
   animation caption (currently "—").
5. **Wire the plain-English summary** (currently a placeholder).
6. **Demo prep:** point the demo at the precompute test so the flipbook is live; record the
   video; rehearse the 3-min flow.

## 8. Open team threads (waiting on others)
- **Jay/Seb:** brain-frame PNGs 404 on live tests — write the images, or demo on the precompute test.
- **Sunny (D):** are `/explain` (per-second captions) + a summary endpoint ready to consume?
- **Seb:** purge junk `tests` docs from Atlas (rows named `"string"` + abandoned `pending`);
  waiting on A's Auth0 login to flip real auth on.

## 9. How to keep working on this
- **Frontend change** → write a Base44 prompt (front-end only; never let Base44 build its own
  DB/entities/backend — it calls the external API in §4). Then Publish + hard-refresh.
- **Backend / contract / docs / tests** → edit this repo directly (that's what a terminal
  coding agent is good for), keep `CONTRACTS.md` as the source of truth, log runs in
  `testing/TEST_LOG.md`.
- **Verify** the live site by loading it and checking the network calls hit the Modal API.
