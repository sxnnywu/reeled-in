# Reeled In — Project Overview

**Hack the 6ix 2026 · Reeled In**
Last updated: 2026-07-18

## One-liner
Reeled In is a **neural A/B testing tool for short-form video**. Upload two or more variants of a Reel/TikTok — or let us generate voice variants for you — and we predict how the human brain engages with each using Meta's open-source **TRIBE v2** brain model, then declare a winner *before you ever post*.

## The name
"Reeled In" = Instagram **Reel** + "**reeling you in**." The metric is literally: does the content hook and hold the viewer's brain.

## The problem
Short-form video has a huge number of creative variables — hook, music, loudness, clip choice, clip order, pacing / cut frequency, on-screen text, CTA. Creators and brands *guess* which combination works and only find out after posting, or after burning ad spend. Real testing today means posting variants live, or expensive human focus groups / eye-tracking. There is no fast, cheap, pre-publish signal for "which edit actually holds attention."

## Our approach
Feed each variant into TRIBE v2 (predicts fMRI brain responses to video / audio / text). Reduce the predicted whole-brain response to **five interpretable functional networks** — visual, auditory, language, motion, and default-mode (meaning / engagement) — as a signal over time. Compare variants on **sustained engagement and retention through the CTA**, and surface a winner with a per-network breakdown and an engagement-over-time curve.

**Honesty line (also our pitch strength):** TRIBE predicts *neural activation*, not emotion or purchase intent. We sell a fast, directional, **pre-flight engagement screen** — not ground truth.

## MVP scope — LOCKED
- **Two test types:**
  1. **Upload & compare** — user uploads 2+ finished video variants; we score and compare. (No video-editing auto-generation in MVP — deferred stretch.)
  2. **Voice A/B (ElevenLabs)** — user uploads one base video + a voiceover/CTA script; we generate several voice reads via ElevenLabs, overlay each onto the video (ffmpeg audio swap), and score them. The one bit of auto-generation we do in MVP.
- **App stack (DECIDED):** **Base44** = frontend + user login; **FastAPI on Modal** = Python backend (all real work); **MongoDB Atlas** = database; **Backboard** = LLM + memory/RAG layer. (Base44 supersedes the earlier React-vs-Streamlit question.)
- **Model hosting:** TRIBE v2 as a **Modal** GPU function; **precompute** demo scores so the live pitch can't cold-start-fail.

## Prize tracks (LOCKED)
- **Base44** — the app is built on it (frontend + auth) → Venture Builder $2k. Validate with a **free beta / waitlist** (see license caveat), not paid customers.
- **ElevenLabs** — powers the Voice A/B test type.
- **MongoDB Atlas** — system of record (written from the Python backend via pymongo).
- **Backboard** — LLM + memory/RAG (personalized "learns your style" recommendations).

**Out: Phoebe** — Reeled In is an analysis tool, not real-world coordination; forcing it in = scope creep.

**Minor / optional (decide by time):** **Auth0** (vs Base44 native login), a direct **Gemini** call (for the MLH Gemini prize, if not subsumed by Backboard).

## Honesty / caveats (put these in the pitch — they signal we know the science)
- **Activation ≠ outcome.** A region lighting up ≠ "this ad sells." We present a neural *engagement signal*, a proxy.
- **fMRI is temporally sluggish** (BOLD lag ~4–6 s; model outputs ~1 Hz). Fast sub-2 s cut differences get smoothed → reliable at the ~5 s segment level, not per-frame.
- **Out-of-distribution:** trained on naturalistic long-form (movies / podcasts); punchy short-form is directional, not gospel.
- **License:** TRIBE v2 is **CC BY-NC 4.0** — fine for a hackathon demo, but do NOT target the Base44 "real paying customers" track with it; use free-beta/waitlist validation.

## Hackathon logistics (confirmed facts)
- **Event:** Hack the 6ix 2026 · 9:30 PM Fri Jul 17 → 9:30 AM Sun Jul 19 (36 h) · U of T (Bahen), Toronto · in-person · teams of 1–4.
- All build inside the window. **Initial Devpost submission by 11:59 PM Sat** (declares tracks); editable until 9:30 AM Sun.
- **Deliverables:** in-person **5-min pitch** (demo live, they discourage slides), **public GitHub repo**, **demo video**, Devpost.
- **Judging:** Technical Difficulty · Uniqueness · Design · Completeness. Rubric penalizes external-API heavy-lifting → our TRIBE scoring pipeline is the technical core.
- One HT6 track only (Hardware / Environmental / Beginner) + unlimited sponsor + MLH tracks.

## Open decisions
- **Auth:** Base44 native login (default, simplest) vs wire **Auth0** for the extra prize.
- **Gemini:** keep one direct Gemini call for the MLH prize, or let Backboard be the whole LLM layer.
- **3D brain viz** vs charts-only for the results screen.
- **Video-editing auto-gen** (reorder / pace / music) — stretch only; music swap easiest first.
- **Team size / who builds what** — still needed for a task-division plan.

## Related docs
- `HOW_TRIBE_V2_WORKS.md` — model deep-dive.
- `TECH_ARCHITECTURE.md` — full system design + data flow.
- `PRD.md` — product requirements.
