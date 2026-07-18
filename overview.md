# Reeled In — Project Overview

**Hack the 6ix 2026 · pivot from "Loopy" (loop-engineering dev tool) → "Reeled In"**
Last updated: 2026-07-18

## One-liner
Reeled In is a **neural A/B testing tool for short-form video**. Upload two or more variants of a Reel/TikTok and we predict how the human brain engages with each — using Meta's open-source **TRIBE v2** brain model — then declare a winner *before you ever post*.

## The name
"Reeled In" = Instagram **Reel** + "**reeling you in**." It describes the actual metric: does the content hook and hold the viewer's brain.

## The problem
Short-form video has a huge number of creative variables — hook, music, loudness, clip choice, clip order, pacing / cut frequency, on-screen text, CTA. Creators and brands *guess* which combination works and only find out after posting, or after burning ad spend. Real testing today means posting variants live, or expensive human focus groups / eye-tracking. There is no fast, cheap, pre-publish signal for "which edit actually holds attention."

## Our approach
Feed each variant into TRIBE v2 (predicts fMRI brain responses to video / audio / text). Reduce the predicted whole-brain response to **five interpretable functional networks** — visual, auditory, language, motion, and default-mode (meaning / engagement) — as a signal over time. Compare variants on **sustained engagement and retention through the CTA**, and surface a winner with a per-network breakdown and an engagement-over-time curve.

**Honesty line (also our pitch strength):** TRIBE predicts *neural activation*, not emotion or purchase intent. We sell a fast, directional, **pre-flight engagement screen** — not ground truth.

## MVP scope — LOCKED decisions
- **Variant input:** users upload 2+ *finished* video variants; we score and compare. No auto-generation in the MVP (that's a stretch goal, to keep the demo bulletproof).
- **Model hosting:** TRIBE v2 on **Modal** as a scale-to-zero GPU endpoint; **precompute** the demo's scores so the live pitch can't fail on a cold start.
- **App stack:** *being finalized — see Open Decisions.*

## Prize tracks we're building for
Primary win condition is the brain-scoring product itself (**Uniqueness** + **Technical Difficulty** — we run a real ~1B-param neuroscience model, not an API wrapper).

Stacking (LOCKED):
- **ElevenLabs** — generate alternate voiceover / CTA reads and test which one the brain engages with. Adds a second modality + agentic depth.
- **MLH bolt-ons:** **Auth0** (login), **MongoDB Atlas** (store each test's history), **Gemini** (suggest copy / hook variants). ~1 hr each, three extra entries.

Noted, not committed: Backboard (orchestration), Freesolo (fine-tune a plain-English report model — also the SF-flight side quest).

## Honesty / caveats (put these in the pitch — they signal we know the science)
- **Activation ≠ outcome.** A region lighting up ≠ "this ad sells." We present a neural *engagement signal*, a proxy.
- **fMRI is temporally sluggish** (BOLD lag ~4–6 s; model outputs ~1 Hz). Fast sub-2 s cut differences get smoothed → reliable at the ~5 s segment level, not per-frame.
- **Out-of-distribution:** trained on naturalistic long-form (movies / podcasts); punchy short-form is directional, not gospel.
- **License:** TRIBE v2 is **CC BY-NC 4.0** — fine for a hackathon demo, but do NOT target the Base44 "real paying customers" track with it.

## Hackathon logistics (carried over — confirmed facts)
- **Event:** Hack the 6ix 2026 · 9:30 PM Fri Jul 17 → 9:30 AM Sun Jul 19 (36 h) · U of T (Bahen), Toronto · in-person · teams of 1–4.
- All build must happen inside the window. **Initial Devpost submission by 11:59 PM Sat** (declares tracks); editable until 9:30 AM Sun.
- **Deliverables:** in-person **5-min pitch** (they discourage slides — demo live), **public GitHub repo**, **demo video**, Devpost.
- **Judging:** Technical Difficulty · Uniqueness · Design · Completeness. The rubric penalizes "how much heavy lifting is done by external libraries / APIs" → our own scoring + pipeline engineering matters.
- One HT6 track only (Hardware / Environmental / Beginner) + unlimited sponsor + MLH tracks.

## Open decisions (to resolve with Sebastian)
- **App stack** — Python + Gradio/Streamlit vs Next.js/React + Python backend (chatting now). Auth0 + stored per-user history lean slightly toward a real web app.
- 3D brain visualization vs charts-only for the demo.
- Whether to attempt the auto-generate-variants stretch, and which single variable first (music swap is easiest).
- Team size / who builds what.

## Related docs
- `how-tribe-v2-works.md` — technical deep-dive on the model.
- `tech-architecture.md` — coming right after the stack decision.
