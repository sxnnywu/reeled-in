# The science behind reeled in's scoring

For the team + the pitch. This documents *why* our brain-network scores relate to
attention/engagement, why some networks are weighted more than others, and — honestly
— which parts are backed by published research vs. which are our own design choices.
Every claim has a source at the bottom. Read the "What's backed vs. what's ours"
section before defending this to a judge.

---

## 0. The one-paragraph version (say this to judges)

reeled in makes **two inferences, and neither is something we invented**:

1. **Video → brain response.** Meta's **TRIBE** model predicts the fMRI response a
   human brain would have to a video. TRIBE won the Algonauts 2025 brain-modeling
   competition (1st of 262 teams) [1][2]. We don't estimate the brain — we use theirs.
2. **Brain response → engagement.** A large body of neuroscience ("**neuroforecasting**"
   and "**inter-subject correlation**") shows that neural responses to media predict
   *population-level* behaviour — preference, sharing, virality, watch-time — often
   **better than people's own self-reports** [3][4][5][6][7].

We chain those two. The honest caveat we lead with: it is a **directional proxy**, not
ground truth, because we're stacking two models. That framing is a strength — it shows
we know the literature and aren't overclaiming.

---

## 1. Does brain activity actually predict whether content engages people?

Yes, and this is the load-bearing claim. The evidence:

- **Inter-subject correlation (ISC).** When many brains respond to a video in the *same
  way at the same time*, that synchrony ("emotionally-laden attention") tracks engagement.
  Dmochowski et al. (2014, *Nature Communications*) showed the **temporal reliability of
  neural processing predicts audience preferences** for TV and ads at the population
  level [4]. ISC peaks during high narrative tension [8] and predicts real-world video
  engagement and memory [9]. A 2025 systematic review confirms ISC as a robust predictor
  of attention [10].
- **Neuroforecasting.** Knutson & Genevsky (Stanford) showed brain activity forecasts
  *aggregate* choices — crowdfunding success, market-level product and food choices —
  and **generalizes across domains**, frequently beating self-report [5][6][11].
- **Virality specifically.** Scholz, Falk et al. (2017, *PNAS*) built a **neural model
  of information virality**: activity in value and self/social-relevance regions predicts
  which articles get shared broadly [7]. Doré et al. (2018, *Cerebral Cortex*) found brain
  activity **tracks population information sharing** [12]; Motoki et al. (2020) forecast
  viral marketing success from social-related neural measures [13].

**Takeaway:** "the brain's response to a video predicts how a population will engage with
it" is an established finding, not a reeled in claim.

---

## 2. The five networks and what each one does

TRIBE predicts whole-brain activity; we reduce it to five functional systems (the same
five the field uses for naturalistic video). What each is, and its documented role:

| System | Brain basis | What it reflects in a video |
|---|---|---|
| **default-mode** ("meaning") | medial prefrontal, posterior cingulate, angular gyrus | narrative, meaning-making, self-relevance, "am I into this" |
| **visual** | occipital + fusiform face area (FFA) | faces, scenes, on-screen text, imagery |
| **language** | Broca's / superior-temporal | speech + caption comprehension |
| **auditory** | primary auditory / Heschl's gyrus | music, sound design, audio texture |
| **motion** | area MT/V5, lateral occipitotemporal | cuts, movement, action |

---

## 3. Why some networks are weighted higher than others

Our engagement blend today:

```
engagement = 0.30·default_mode + 0.25·visual + 0.20·language + 0.15·auditory + 0.10·motion
```

The **ordering** (meaning > visual > language > auditory > motion) is defensible from two
independent lines of evidence:

**A. High-level "associative" networks carry the engagement signal; low-level sensory
networks don't discriminate.** Almost any video drives the auditory and motion systems —
sound and movement light them up regardless of whether the content is good. TRIBE's own
paper makes this concrete: **unimodal models already predict visual/auditory networks
well, but are "systematically outperformed by our multimodal model in high-level
associative cortices"** [1]. The associative cortex — default-mode and language — is where
meaning is *integrated*, and it's the harder, higher-information signal. So the systems
that carry "is this actually engaging" are the associative ones, which is why they're
weighted up.

**B. The predict-behaviour literature points at the same regions.**
- **default-mode highest:** the default network **dominates neural responses to evolving
  movie stories** [14] and plays a central role in narrative and meaning during
  naturalistic viewing [15]. The virality/neuroforecasting signal lives in overlapping
  value + self/social-relevance regions (VMPFC, part of the DMN) [5][7]. Narrative pull is
  the closest thing to "engagement," so it gets the top weight.
- **visual high (because of faces):** short-form video is face-heavy, and faces are a
  special case — the fusiform face area is a dedicated face region [16] and **faces capture
  attention even when they're irrelevant to the task** [17]. Faces are a strong, reliable
  attention driver, so visual is weighted second.
- **language mid:** speech comprehension is high-level and associative (where TRIBE's edge
  is largest), but not every clip is speech-driven, so it sits below visual.
- **auditory / motion low:** sensory, near-universal, least discriminative of *quality* —
  they respond to almost anything, so they're weighted least.

> **This ordering is literature-informed. The exact numbers are not fitted.** See §5.

---

## 4. The four metrics — what each proxies

From the engagement curve `E` (one value per second):

| Metric | Formula | What it proxies | Grounding |
|---|---|---|---|
| **sustained** | `mean(E)` | held attention across the whole clip | ISC engagement is a *time-averaged* reliability signal [4][10] |
| **retention** | `mean(last third) / mean(first third)` | did it hold to the end or drop off | drop-off = disengagement; the thing watch-time actually measures |
| **peak** | `max(E)` | the single strongest moment | peak neural response / the "hook" moment |
| **overall** | `0.5·sustained + 0.3·retention + 0.2·peak` | one composite for ranking | **heuristic composite (ours)** |

`sustained` and `retention` are the two most defensible (they map to sustained/reliable
engagement and to drop-off). `peak` is a reasonable "hook strength" proxy. `overall`'s
0.5/0.3/0.2 split is a design choice, not a measured constant.

**Scope note (important correction):** `peak`/`sustained`/`retention`/`overall` are legacy
composite numbers. They are fine as *descriptive stats of the engagement curve*, but they
are **NOT the basis for the A/B comparison winner.** A comparison is decided by comparing
the two videos across the **real signals we measure** — the 5 brain networks **plus** the
observable production signals (facial expression, hand gestures, speech rate, motion, etc.)
— each of which has its own published engagement evidence. See **§7**. And none of these
appear as a single video's grade (see §6).

---

## 5. What's backed vs. what's ours (read this before pitching)

**Backed by published research:**
- Brain response to media predicts population engagement/virality (§1). [3–13]
- Which brain systems carry that signal — associative/meaning + value/self-relevance,
  and faces for attention (§3). [1][7][14–17]
- TRIBE is a validated, competition-winning video→brain model (§0). [1][2]

**Our design choices (be upfront about these):**
- The **exact weights** (0.30/0.25/0.20/0.15/0.10) and the **overall split** (0.5/0.3/0.2).
  The *ordering* is literature-informed; the *specific numbers* are a prior we set, not
  fit to outcome data.
- Reducing whole-brain output to exactly these five networks (a standard but chosen
  simplification).

**The honest limitation, and the fix.** We stack two models (video→brain→engagement), so
error compounds and it's a directional proxy. TRIBE is also trained on long-form
naturalistic film, not punchy short-form, and reads out at ~1 Hz — reliable at the
~5-second level, not per-frame. **The principled next step** that turns the heuristic
weights into a real model: fit the weights against labelled outcomes — real watch-time /
view-through data, or human A/B labels (we already have a blind-validation set where the
model matched human picks 3/3). That converts "our prior" into "empirically calibrated,"
which is the version a skeptical judge fully buys.

---

## 6. Two product modes — intended behavior (this is the design, not a suggestion)

reeled in does two different things. They are scored and presented **differently on
purpose**, because the science supports them differently.

### Single video → a brain-signal PROFILE. No overall grade.
There is **no "overall" number, no ranking, no right/wrong** for a single clip. Nothing
is being compared, and "more stimulation" is not "better" — a louder/faster clip lighting
up more of the brain doesn't make it a better video, and real brains differ person to
person anyway. All we are honestly claiming is the **predicted average brain reaction** to
that one clip. So single-video mode shows **only**:
- **which of the 5 systems responded, and where** in the brain (the `region_timeline` +
  `brain_frames`),
- the **per-signal numbers and curves over time** (the 5 network curves + the engagement
  curve).

Do **not** surface `overall` (or a "score/grade") in single-video mode. `overall`,
`winner_variant_id`, and `retention`-as-a-verdict are **comparison-only** concepts.
Single video is a picture of how a brain would light up — a profile, not a verdict.

### Two videos → ranking, and show the research.
Only here do we rank. This is where the evidence is strongest (neuroforecasting and ISC
are inherently *relative/ranking* findings — "which of these will a population prefer"
[4][5][7]). The comparison view goes deeper: the winner, the per-system deltas (which
brain system separated them), and — per Jay — it should **surface the reasoning/proxy from
this document** so the viewer (and a judge) sees *why* a higher meaning/visual/language
response predicts more engagement, with the citations. The ranking is only credible if the
research behind it is shown alongside it.

**Frontend implication (Person A):** single-video results screen = profile (systems +
where + curves), no grade. Comparison results screen = winner + per-**signal** breakdown
(the §7 signals, not peak/sustained/retention/overall) + an inline "why this ranking" panel
drawn from this doc.

---

## 7. Comparison mode ranks on the REAL signals — with evidence for each

When two videos are compared, the winner is decided by comparing them across the observable
signals we actually measure. `peak`/`sustained`/`retention`/`overall` are **not** the basis.
Two families of signal, each with published backing:

**A. Predicted neural response — the 5 brain networks (TRIBE).** Covered in §1–3:
neuroforecasting + ISC say a stronger, more *reliable* neural response, especially in the
meaning / visual / language systems, predicts population engagement.

**B. Observable production signals (model-free, measured from the pixels + audio).** Each
maps to a separate behavioral literature:

| Signal we measure | What it is | Evidence it relates to engagement | Source |
|---|---|---|---|
| **facial expression** (smile, mouth-open, brows) | affect on the creator's face | facial/smile responses predict ad liking + purchase intent at scale; facial coding predicts ad & brand effects | McDuff & el Kaliouby [18]; Frontiers 2023 [19] |
| **hand gestures** | gesture presence + motion | gesturing raises persuasion, attention and communication quality | *J. Marketing Research* 2025 [20]; UBC 2025 [21] |
| **speech rate / vocal expressiveness** ("language volume") | words/sec + prosody | prosodic / vocal expressiveness predicts affective engagement in video | Frontiers 2025 [22]; IEEE TCSS [23] |
| **motion / cuts / pacing** | movement + edit density | scene cuts and visual complexity drive attention; on short-form, cut style shapes likes vs. completion — and *too much* pacing hurts sustained engagement | *JAMS* 2025 [24]; short-form jump-cut study [25] |
| **visual clarity / sharpness** | focus vs. blur | quality gate (blur = harder to process); weak *direct* engagement evidence — treat as a clarity check, not an engagement driver |

**The honest nuance (from [25]): more is not better.** In a controlled short-form study,
higher pacing *reduced* sustained engagement, and the best cut style depended on the goal
(seamless cuts → likes; moderate overlapping cuts → completion). So "video A moved more" is
a *fact about the video*, not automatically a point in its favour — the same
"stimulus ≠ better" principle from single-video mode, applied per signal.

**How the winner is decided, and how to show it:** compare the two videos signal-by-signal,
surface the per-signal deltas (which signals separated them), and show the winner with the
evidence above inline. The weighting across signals is — like the network weights — a
literature-informed prior until it is fit to real outcome data (watch-time, or human A/B
labels). Say that; don't present the blend as a measured constant.

---

## Sources

1. Meta FAIR (Brain & AI team). **TRIBE: Trimodal Brain Encoder for whole-brain fMRI response prediction.** arXiv:2507.22229 — https://arxiv.org/abs/2507.22229 (verify exact author list before formal citation)
2. Meta FAIR — Algonauts 2025 winner announcement (1st of 262 teams) — https://www.startuphub.ai/ai-news/ai-research/2025/meta-fair-wins-algonauts-2025-with-a-trimodal-brain-model
3. Hasson et al. (2004, *Science*). Intersubject synchronization during natural vision (neurocinematics).
4. Dmochowski et al. (2014, *Nature Communications*). **Audience preferences are predicted by temporal reliability of neural processing.** — https://www.nature.com/articles/ncomms5567
5. Knutson & Genevsky (2018, *Current Directions in Psychological Science*). **Neuroforecasting aggregate choice.** — https://stanford.edu/~knutson/nfc/knutson18_pre.pdf
6. **Neuroforecasting reveals generalizable components of choice** (2025, *PNAS Nexus*) — https://pure.eur.nl/ws/portalfiles/portal/186405116/pgaf029.pdf
7. Scholz, Baek, O'Donnell, Falk et al. (2017, *PNAS*). **A neural model of valuation and information virality.** — https://pubmed.ncbi.nlm.nih.gov/28242678/
8. Dmochowski et al. (2012, *Frontiers in Human Neuroscience*). ISC peaks during narrative tension.
9. Cohen et al. (2017). EEG-ISC predicts real-world engagement & memory for video.
10. **Intersubject correlation as a predictor of attention: a systematic review** (2025, *BMC Psychology*) — https://link.springer.com/article/10.1186/s40359-025-02879-7
11. **The prediction of market-level food choices by the neural valuation signal** (*PLOS One*) — https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0286648
12. Doré et al. (2018, *Cerebral Cortex*). **Brain Activity Tracks Population Information Sharing.** — https://brucedore.github.io/Dore_et_al_CC_2018.pdf
13. Motoki et al. (2020, *Journal of Interactive Marketing*). Social-related neural measures forecast viral marketing success. — https://journals.sagepub.com/doi/abs/10.1016/j.intmar.2020.06.003
14. **The default network dominates neural responses to evolving movie stories** (2023, *Nature Communications*) — https://www.nature.com/articles/s41467-023-39862-y
15. **The surprising role of the default mode network in naturalistic perception** (2020, *Communications Biology*) — https://www.nature.com/articles/s42003-020-01602-z
16. Kanwisher, McDermott, Chun (1997, *Journal of Neuroscience*). **The Fusiform Face Area.** — https://www.jneurosci.org/content/17/11/4302
17. Attentional capture by faces (faces capture attention even when task-irrelevant) — https://pmc.ncbi.nlm.nih.gov/articles/PMC1857737/
18. McDuff, el Kaliouby et al. **Predicting Ad Liking and Purchase Intent: Large-scale Analysis of Facial Responses to Ads** (*IEEE Trans. Affective Computing*) — https://www.semanticscholar.org/paper/02da25583f429cb050df61c2ffed7cd1e9a887ca
19. **Automatic facial coding predicts self-report of emotion, advertisement and brand effects elicited by video commercials** (2023, *Frontiers in Neuroscience*) — https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1125983/full
20. **Talking with Your Hands: How Hand Gestures Influence Communication** (2025, *Journal of Marketing Research*) — https://doi.org/10.1177/00222437251385922
21. UBC (2025). **Talk with your hands to be more persuasive** — https://news.ubc.ca/2025/11/talk-with-your-hands-to-be-more-persuasive/
22. **Predicting affective engagement and mental strain from prosodic speech features** (2025, *Frontiers in Psychiatry*) — https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2025.1656292/full
23. **Dual-Model Prediction of Affective Engagement and Vocal Attractiveness From Speaker Expressiveness in Video Learning** (*IEEE Trans. Computational Social Systems*) — https://doi.org/10.1109/tcss.2026.3675249
24. **The dynamic effects of visual complexity and scene cuts on viewer attention** (2025, *Journal of the Academy of Marketing Science*) — https://link.springer.com/article/10.1007/s11747-025-01137-x
25. Dost & Huang (2026). Short-form jump-cut style × transition frequency on TikTok engagement (seamless→likes; overlapping→completion; higher pacing reduces sustained engagement) — https://archives.marketing-trends-congress.com/2026/pages/PDF/paper_professor_DOST_HUANG.pdf

*(Sources 3–17 from Exa neural search + direct publisher fetches; 18 confirmed via Apify rag-web-browser; 18–25 from Exa. Verify author lists/years before formal citation.)*
