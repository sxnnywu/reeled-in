# Visualization Spec — Results screen (single source for A)

**Owner of this doc:** C (Seb). **Implements:** A (Kimi). **Science source:** `SCORING_SCIENCE.md` §6–§7. **Binding rules:** `CONTRACTS.md` §3a.

Why this exists: the Results screen currently shows the same "winner + 4 metrics + retention%" for everything, but the science says a **single video is a profile (no grade)** and a **comparison ranks on real signals, not the composite metrics** — and the metrics are **[0,1] proxy scores, not percentages**. This doc is the exact build sheet to fix that. The backend now hands you an `analysis` object so you don't have to re-derive any of it.

---

## 1. The new backend field: `analysis` (in `GET /tests/{id}`)

The response is now `{ test, variants, scores, analysis }`. **Branch the whole Results screen on `analysis.mode`.**

```jsonc
// SINGLE video (1 variant):
"analysis": { "mode": "profile" }

// COMPARISON (2+ variants), once scored:
"analysis": {
  "mode": "comparison",
  "ranking": [                                   // sorted, winner first (index = signal-rank, NOT a metric)
    { "variant_id": "var_…B", "label": "B", "index": 0.548 },
    { "variant_id": "var_…A", "label": "A", "index": 0.452 }
  ],
  "winner_variant_id": "var_…B",
  "network_advantage": {                          // winner minus runner-up, mean per brain network (family A)
    "default_mode": 0.15, "visual": 0.03, "language": -0.01, "auditory": 0.0, "motion": 0.02
  },
  "signal_advantage": {                           // winner minus runner-up, per production signal (family B)
    "face_expression": 0.30, "speech_rate": 1.0, "hand_gesture": -0.10, "motion": -0.07, "clarity": 250.0
  },
  "decisive": "signal:face_expression"           // the component (brain:* or signal:*) that most separated them
}
```
The winner is decided by the **real signals** (brain networks + production signals) via `scoring/signals.rank_scores` — **not** by peak/sustained/retention/overall. `ranking[0].variant_id` equals `test.winner_variant_id`. In a 2+ test not finished scoring, `analysis` is just `{ mode: "comparison" }` (no ranking) — show a "scoring…" state. `network_advantage` values are on the [0,1] brain scale; `signal_advantage` values are raw per-signal deltas (each signal on its own unit) — render each signal's bar against its own range, and use `decisive` for the headline "what separated them."

---

## 2. Profile mode (`mode === "profile"`) — a picture, NOT a grade

A single clip is a **predicted brain-response profile**. Nothing is compared; "more activation ≠ better." **Show only:**
- The video player.
- The **5 network curves** + the **engagement** curve (all from `scores[0]`).
- The **brain-frame flipbook** (`scores[0].brain_frames`) synced to `region_timeline` captions (once `/explain` is wired; until then show the raw `top_network`/`top_region`).

**Do NOT render, in profile mode:** `overall`, any winner/badge, a letter/number grade, or `retention`. (`overall`/`winner_variant_id` may exist in the payload — ignore them here.)

**Framing copy:** headline "How a viewer's brain would respond to this clip." One caveat line: *"A directional neural proxy — not ground truth."*

---

## 3. Comparison mode (`mode === "comparison"`) — ranking, with the science shown

- **Winner badge:** `ranking[0].label`.
- **Engagement curves overlaid** for all variants on one time axis (from each `scores[i].engagement`).
- **"What separated them" bars:** one bar per brain network from `network_advantage` AND one per production signal from `signal_advantage`, sorted by value; highlight the `decisive` component. Positive = winner stronger.
- **"Why this ranking" panel (required):** take `decisive` (e.g. `"brain:default_mode"` or `"signal:face_expression"`), strip the `brain:`/`signal:` prefix, look it up in the copy map (§4), render its one-liner + citation. This is the credibility piece — per §6, "the ranking is only credible if the research behind it is shown alongside it."
- **Metrics** (if shown at all): render as **proxy scores** (`0.79`, or a 0–1 dial), **labeled "proxy score."** See §6.

---

## 4. Network → rationale copy map (paste into the frontend, from `SCORING_SCIENCE.md` §2–§3)

Keyed by component key (strip the `brain:`/`signal:` prefix from `decisive`, then look up here):

**Brain networks (`network_advantage`):**
| key | Label | One-liner for the "why" panel | Cite |
|---|---|---|---|
| `default_mode` | **Meaning & narrative** | "The brain's default-mode network — narrative pull and self-relevance. It dominates responses to evolving stories and carries the value signal that predicts sharing, so it's our strongest engagement signal." | [14][7][5] |
| `visual` | **Faces & imagery** | "Faces and on-screen imagery. The fusiform face area is a dedicated face region and faces capture attention even when irrelevant — a reliable attention driver in face-heavy short-form." | [16][17] |
| `language` | **Speech & captions** | "Speech and caption comprehension — a high-level associative signal (where the brain model's edge is largest), when the clip is speech-driven." | [1] |
| `auditory` | **Sound & music** | "Music, sound design, audio texture. Near-universal and low-level — almost any audio drives it, so it's least discriminative of quality." | [1] |
| `motion` | **Cuts & action** | "Movement and edit pacing. Responds to almost any motion — and per short-form research, *more* pacing can *hurt* sustained engagement, so 'moved more' isn't automatically better." | [1][25] |

**Production signals (`signal_advantage`):**
| key | Label | One-liner for the "why" panel | Cite |
|---|---|---|---|
| `face_expression` | **Facial expression** | "Smiling and facial affect — facial/smile responses predict ad liking and purchase intent at scale, so a more expressive delivery reads as more engaging." | [18][19] |
| `speech_rate` | **Speech rate** | "How fast they talk — part of vocal expressiveness, which predicts affective engagement." | [22][23] |
| `volume` | **Vocal energy** | "Loudness of the audio — vocal arousal/energy is part of the prosody that predicts engagement." | [22][23] |
| `hand_gesture` | **Hand gestures** | "Animated hands — gesturing raises persuasion, attention and communication quality." | [20][21] |
| `motion` (signal) | **Movement** | "Measured on-screen movement. Note: more is not automatically better — high pacing can reduce sustained engagement." | [24][25] |
| `clarity` | **Clarity** | "Focus/sharpness — a quality gate (blur is harder to process), not a direct engagement driver; treat as a check." | — |

(Citation numbers map to `SCORING_SCIENCE.md`'s Sources list.)

---

## 5. Comparison basis — §7's two signal families (DONE)

`SCORING_SCIENCE.md` §7 says a comparison ranks on **two families of signal**, and both are now live:
- **A. The 5 brain networks** — surfaced as `network_advantage` (winner − runner-up, per network).
- **B. Observable production signals** — `face_expression, speech_rate, hand_gesture, motion, clarity`. Now IN the Score Object (`signals`, CONTRACTS §3) and surfaced as `signal_advantage`.

The winner + `ranking` come from `scoring/signals.rank_scores` (brain networks + production signals). **peak/sustained/retention/overall are NOT used to rank** — they are descriptive curve stats only. Build the "why this ranking" panel from both `network_advantage` and `signal_advantage`, and headline it with `decisive`.

> Note: `signals` is `{}` on a Score Object until the objective toolkit has run for that variant. When empty, `signal_advantage` deltas are 0 and the ranking falls back to brain networks only — still valid, never the legacy metrics.

---

## 6. Metrics are proxy scores, not percentages (applies everywhere)

- Never render `retention: 1.0` as "100% retention" or `overall: 0.69` as a "69% grade."
- They're normalized **directional-proxy** values in [0,1] (`SCORING_SCIENCE.md` §5). `retention` is a *ratio* of final-third ÷ first-third engagement, clamped at 1.0 (1.0 = "held or grew," not "perfect").
- Present as `0.69` / a 0–1 dial / a relative bar — with the wording "proxy score," and lead the screen with the "directional proxy, not ground truth" caveat.

---

## 7. A's build checklist
- [ ] Branch Results on `analysis.mode`.
- [ ] Profile: curves + engagement + flipbook + region timeline; **remove** metrics cards / winner / grade; add caveat copy.
- [ ] Comparison: winner badge, overlaid engagement curves, `network_advantage` + `signal_advantage` bars (highlight `decisive`), "why this ranking" panel from §4, metrics (if shown) labeled proxy scores — never as the winner basis.
- [ ] Kill every "%" on a metric; relabel as proxy scores.
- [ ] `signal_advantage` currently `null` — render the family-B bars conditionally so they appear automatically when B ships it.
- [ ] Dev against the updated `frontend/mock_api.json` (now carries an illustrative `analysis` block).
