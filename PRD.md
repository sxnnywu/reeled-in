# Reeled In — Product Requirements (PRD)

Last updated: 2026-07-18. Companion to `OVERVIEW.md` and `TECH_ARCHITECTURE.md`.

## Summary
Reeled In predicts how the human brain engages with short-form video, so creators and marketers can A/B test variants of a Reel/TikTok — hook, music, voiceover, pacing, CTA — and pick a winner *before* posting, using Meta's TRIBE v2 brain model instead of live posting or human focus groups.

## Problem
Short-form video has too many creative variables and no cheap pre-publish signal for which edit holds attention. Creators guess, or find out only after posting / after ad spend. Human testing (focus groups, eye-tracking) is slow and expensive.

## Target users
- **Solo creators / influencers** — which edit will hold attention?
- **Small brands / DTC marketers** — de-risk paid-social spend before boosting.
- **Agencies / social teams** — a fast pre-flight check across many variants.

## Goals
- Given >=2 variants, produce a clear, explainable **winner** with a per-network engagement breakdown and an engagement-over-time curve.
- Make the signal **fast and pre-publish** (seconds, no humans).
- Personalize over time (learn what works for a given creator).

## Non-goals
- Not a video *editor* (MVP does not auto-cut/reorder clips).
- Not a claim of predicting sales/virality — it is a neural **engagement** proxy.
- Not handling payments or real ad spend.

## User stories
- As a creator, I upload two edits of my Reel and see which holds attention to the CTA.
- As a marketer, I test three hooks and learn which spikes early engagement.
- As a creator, I type my CTA script, get it read 4 ways, and see which voice lands best (Voice A/B).
- As a returning user, my past tests inform smarter suggestions.

## Features
**MVP**
- **Upload & compare** test type (2+ finished variants).
- **Voice A/B** test type (script -> ElevenLabs reads -> overlay -> score).
- **Scoring engine:** TRIBE -> 5 networks -> peak / sustained / retention-to-CTA metrics.
- **Results screen:** winner call, per-network bars, engagement-over-time curve, plain-English summary (Backboard).
- **Brain animation:** side-by-side video + a per-second brain-frame flipbook lighting up the engaged regions, with an **AI explainer** captioning what each moment means ("your brain is locking onto a face — good hook").
- **Login + history** (Base44 auth, Mongo store), Backboard memory for personalized tips.

**Stretch**
- Video-editing auto-generation (music swap -> reorder -> pacing).
- Live **interactive 3D** brain (rotatable, rendered in-browser) instead of the precomputed flipbook.
- "Act on the winner" (schedule/post) — deliberately deferred (the Phoebe-shaped scope creep we're avoiding).

## What "winner" means (metric definition)
Per variant, from the 5 network time-series: **peak** (max engagement), **sustained** (area under curve over the clip), and **retention-through-CTA** (engagement held to the end vs collapse). The creator picks an objective (e.g. hold attention to the CTA); winner = highest composite on that objective.

## Success criteria
- **Hackathon:** a bulletproof 3-min live demo — upload 2 variants (precomputed), reveal winner + curves; one live "score a fresh clip" moment; clean sponsor-track story (Base44 / ElevenLabs / MongoDB / Backboard). Strong on Technical Difficulty (our TRIBE pipeline), Uniqueness (a brain model is rare), Design, Completeness.
- **Product:** free-beta signups as demand evidence (Base44 track); on a couple of hand-checked examples, the winner is one a human would plausibly agree with.

## Scope / out of scope
In: scoring, comparison, results, voice variants, history/memory. Out: video editing (MVP), payments, real posting, medical/clinical claims.

## Risks & mitigations
- **Scientific validity** (activation != outcome) -> frame as a directional proxy; hand-validate a couple of examples; caveat in the pitch.
- **Temporal smoothing** (~1 Hz; fast cuts blur) -> reliable at ~5 s segment level; do not over-claim per-frame.
- **License CC BY-NC** -> free beta / waitlist only; no paid product.
- **GPU cold start / demo fragility** -> precompute; keep_warm during judging; laptop-fallback recording.
- **Out-of-distribution short-form** -> directional; lead with segment-level insight.

## Open questions
- Auth0 vs Base44 native login.
- Direct Gemini call vs Backboard-only.
- 3D brain viz vs charts-only.
- Video-editing auto-gen stretch (and first variable).
- Team size / roles.
