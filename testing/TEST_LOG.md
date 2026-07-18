# reeled in — Frontend Test Log

Running QA log for the Base44 frontend (`https://reeled-in.base44.app`) against the
deployed API (`https://jaychopra05--reeled-in-api.modal.run`). Owner: **A (Kimi)**.

Each entry is one test run: the flow, scenario, outcome, and (where relevant) a
screenshot in [`screenshots/`](screenshots/). Screenshot files are named
`YYYY-MM-DD_<flow>_<short>.png`.

**Legend:** ✅ works · ⚠️ partial (works with caveats) · ❌ broken · ⏳ not yet tested

## Status at a glance
- **Read paths (Results, History):** ✅ live on real API data.
- **Home / flow framing:** ✅ leads with "upload your variants," voice is the optional branch.
- **Create flows (New Test upload, Voice A/B generate):** ⏳ not yet tested end-to-end.
- **Voice A/B transcript prefill:** ⏳ needs a talking-head clip with speech.
- **Brain-frame images:** ⏳ blank on the old seed (`brain_frames: []`); a real-frame demo
  test was just seeded from B's precompute (7024 vs 7025) — needs a render check.
- **Per-second captions (`/explain`):** ⏳ not wired.
- **Plain-English summary:** ⏳ placeholder (LLM summary endpoint not wired).
- **Auth0 login:** ⏳ not wired (API on dev-fallback user).

## Log

| # | Date | Flow / page | Scenario | Outcome | Notes | test_id | Screenshot |
|---|------|-------------|----------|---------|-------|---------|-----------|
| 1 | 2026-07-18 | Home | Flow framing / branding | ✅ | Leads with upload; voice framed as optional branch | — | — |
| 2 | 2026-07-18 | Results (read) | Render seeded test | ✅ | Real data — winner, 4 metrics, 5 network curves + composite, 8s timeline. Videos 404 → placeholder; `brain_frames: []` → placeholder | test_seed0000001 | — |
| 3 | 2026-07-18 | History (read) | List past tests | ✅ | Renders real tests. Junk `"string"`/`pending` rows are backend test data (Seb to purge) | — | — |

<!-- Add new rows below. Template:
| N | YYYY-MM-DD | <flow/page> | <what you did> | ✅/⚠️/❌ | <what worked / broke; error text> | <test_id or —> | <screenshots/file.png or —> |
-->
