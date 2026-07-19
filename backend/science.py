"""The research evidence behind the scoring — served at GET /api/science so the frontend
can show judges the numbers are rooted in published papers, not picked at random. Owner: C (Seb).

Source of truth: SCORING_SCIENCE.md (sources verified via Exa + Apify). Each scoring
`component` key matches `analysis.decisive` ("brain:*" / "signal:*") and the
`network_advantage` / `signal_advantage` keys, so the frontend can look up the exact
paper(s) behind whatever separated a given A/B winner.
"""

# All citations from SCORING_SCIENCE.md §Sources. url=None where no public link exists.
SOURCES = [
    {"id": 1,  "cite": "Meta FAIR — TRIBE: Trimodal Brain Encoder for whole-brain fMRI prediction (arXiv:2507.22229)", "url": "https://arxiv.org/abs/2507.22229"},
    {"id": 2,  "cite": "Meta FAIR wins Algonauts 2025 with a trimodal brain model (1st of 262 teams)", "url": "https://www.startuphub.ai/ai-news/ai-research/2025/meta-fair-wins-algonauts-2025-with-a-trimodal-brain-model"},
    {"id": 3,  "cite": "Hasson et al. (2004, Science) — Intersubject synchronization during natural vision (neurocinematics)", "url": None},
    {"id": 4,  "cite": "Dmochowski et al. (2014, Nature Communications) — Audience preferences predicted by temporal reliability of neural processing", "url": "https://www.nature.com/articles/ncomms5567"},
    {"id": 5,  "cite": "Knutson & Genevsky (2018, Current Directions in Psych. Science) — Neuroforecasting aggregate choice", "url": "https://stanford.edu/~knutson/nfc/knutson18_pre.pdf"},
    {"id": 6,  "cite": "Neuroforecasting reveals generalizable components of choice (2025, PNAS Nexus)", "url": "https://pure.eur.nl/ws/portalfiles/portal/186405116/pgaf029.pdf"},
    {"id": 7,  "cite": "Scholz, Baek, O'Donnell, Falk et al. (2017, PNAS) — A neural model of valuation and information virality", "url": "https://pubmed.ncbi.nlm.nih.gov/28242678/"},
    {"id": 8,  "cite": "Dmochowski et al. (2012, Frontiers in Human Neuroscience) — ISC peaks during narrative tension", "url": None},
    {"id": 9,  "cite": "Cohen et al. (2017) — EEG-ISC predicts real-world engagement & memory for video", "url": None},
    {"id": 10, "cite": "Intersubject correlation as a predictor of attention: a systematic review (2025, BMC Psychology)", "url": "https://link.springer.com/article/10.1186/s40359-025-02879-7"},
    {"id": 11, "cite": "The prediction of market-level food choices by the neural valuation signal (PLOS One)", "url": "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0286648"},
    {"id": 12, "cite": "Doré et al. (2018, Cerebral Cortex) — Brain Activity Tracks Population Information Sharing", "url": "https://brucedore.github.io/Dore_et_al_CC_2018.pdf"},
    {"id": 13, "cite": "Motoki et al. (2020, J. Interactive Marketing) — Social-related neural measures forecast viral marketing success", "url": "https://journals.sagepub.com/doi/abs/10.1016/j.intmar.2020.06.003"},
    {"id": 14, "cite": "The default network dominates neural responses to evolving movie stories (2023, Nature Communications)", "url": "https://www.nature.com/articles/s41467-023-39862-y"},
    {"id": 15, "cite": "The surprising role of the default mode network in naturalistic perception (2020, Communications Biology)", "url": "https://www.nature.com/articles/s42003-020-01602-z"},
    {"id": 16, "cite": "Kanwisher, McDermott, Chun (1997, J. Neuroscience) — The Fusiform Face Area", "url": "https://www.jneurosci.org/content/17/11/4302"},
    {"id": 17, "cite": "Attentional capture by faces (faces capture attention even when task-irrelevant)", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1857737/"},
    {"id": 18, "cite": "McDuff & el Kaliouby — Predicting Ad Liking and Purchase Intent: Large-scale Analysis of Facial Responses to Ads (IEEE Trans. Affective Computing)", "url": "https://www.semanticscholar.org/paper/02da25583f429cb050df61c2ffed7cd1e9a887ca"},
    {"id": 19, "cite": "Automatic facial coding predicts emotion, advertisement and brand effects from video commercials (2023, Frontiers in Neuroscience)", "url": "https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1125983/full"},
    {"id": 20, "cite": "Talking with Your Hands: How Hand Gestures Influence Communication (2025, J. Marketing Research)", "url": "https://doi.org/10.1177/00222437251385922"},
    {"id": 21, "cite": "UBC (2025) — Talk with your hands to be more persuasive", "url": "https://news.ubc.ca/2025/11/talk-with-your-hands-to-be-more-persuasive/"},
    {"id": 22, "cite": "Predicting affective engagement and mental strain from prosodic speech features (2025, Frontiers in Psychiatry)", "url": "https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2025.1656292/full"},
    {"id": 23, "cite": "Dual-Model Prediction of Affective Engagement and Vocal Attractiveness from Speaker Expressiveness (IEEE Trans. Computational Social Systems)", "url": "https://doi.org/10.1109/tcss.2026.3675249"},
    {"id": 24, "cite": "The dynamic effects of visual complexity and scene cuts on viewer attention (2025, J. Academy of Marketing Science)", "url": "https://link.springer.com/article/10.1007/s11747-025-01137-x"},
    {"id": 25, "cite": "Dost & Huang (2026) — Short-form jump-cut style × transition frequency on TikTok engagement", "url": "https://archives.marketing-trends-congress.com/2026/pages/PDF/paper_professor_DOST_HUANG.pdf"},
]

# component.key matches analysis.decisive ("brain:*"/"signal:*") + the *_advantage keys.
COMPONENTS = [
    {"key": "brain:default_mode", "family": "brain", "label": "Meaning & narrative",
     "measures": "Default-mode network — narrative pull, meaning-making, self-relevance.",
     "why": "It dominates neural responses to evolving stories and carries the value signal that predicts sharing/virality — the closest thing to 'engagement,' so it's weighted highest.",
     "source_ids": [14, 15, 7, 5]},
    {"key": "brain:visual", "family": "brain", "label": "Faces & imagery",
     "measures": "Occipital + fusiform face area — faces, scenes, on-screen text.",
     "why": "The fusiform face area is a dedicated face region and faces capture attention even when task-irrelevant — a reliable attention driver in face-heavy short-form.",
     "source_ids": [16, 17]},
    {"key": "brain:language", "family": "brain", "label": "Speech & captions",
     "measures": "Broca's / superior-temporal — speech and caption comprehension.",
     "why": "A high-level associative signal — exactly where the TRIBE brain model's multimodal edge is largest.",
     "source_ids": [1]},
    {"key": "brain:auditory", "family": "brain", "label": "Sound & music",
     "measures": "Primary auditory / Heschl's gyrus — music, sound design, audio texture.",
     "why": "Sensory and near-universal (almost any audio drives it), so it's a weaker discriminator of quality — weighted low.",
     "source_ids": [1]},
    {"key": "brain:motion", "family": "brain", "label": "Cuts & action",
     "measures": "Area MT/V5 — visual motion, cuts, action.",
     "why": "Sensory and near-universal; and per short-form research, more pacing can hurt sustained engagement — so 'moved more' isn't automatically better.",
     "source_ids": [1, 25]},
    {"key": "signal:face_expression", "family": "signal", "label": "Facial expression",
     "measures": "Smile / facial affect measured from the pixels (MediaPipe).",
     "why": "Facial and smile responses predict ad liking and purchase intent at scale — a more expressive delivery reads as more engaging.",
     "source_ids": [18, 19]},
    {"key": "signal:speech_rate", "family": "signal", "label": "Speech rate",
     "measures": "Words per second (Whisper transcript).",
     "why": "Speech rate is part of vocal expressiveness, which predicts affective engagement.",
     "source_ids": [22, 23]},
    {"key": "signal:volume", "family": "signal", "label": "Vocal energy",
     "measures": "Audio loudness / RMS.",
     "why": "Vocal arousal / loudness is part of the prosody that predicts affective engagement.",
     "source_ids": [22, 23]},
    {"key": "signal:hand_gesture", "family": "signal", "label": "Hand gestures",
     "measures": "Hand presence + motion (MediaPipe).",
     "why": "Gesturing raises persuasion, attention and communication quality.",
     "source_ids": [20, 21]},
    {"key": "signal:motion", "family": "signal", "label": "Movement & pacing",
     "measures": "On-screen movement + edit density.",
     "why": "Scene cuts and complexity drive attention — but more is not automatically better (high pacing can reduce sustained engagement).",
     "source_ids": [24, 25]},
    {"key": "signal:clarity", "family": "signal", "label": "Visual clarity",
     "measures": "Focus vs. blur (Laplacian sharpness).",
     "why": "A quality gate (blur is harder to process), not a direct engagement driver — treat as a check.",
     "source_ids": []},
]


def get_science() -> dict:
    """Structured research evidence for GET /api/science."""
    return {
        "headline": "Every score is rooted in published neuroscience + behavioral research — not picked at random.",
        "how_it_works": (
            "reeled in chains two peer-reviewed inferences: (1) video → brain response via Meta's "
            "TRIBE model, which won the Algonauts 2025 brain-modeling competition (1st of 262 teams); "
            "(2) brain response → engagement via neuroforecasting + inter-subject correlation, which "
            "predict population-level preference, sharing and watch-time — often better than people's "
            "own self-reports. Honest caveat we lead with: a directional proxy, not ground truth."
        ),
        "ranking_basis": (
            "An A/B winner is decided by comparing the two videos across the REAL measured signals — "
            "5 TRIBE brain networks + observable production signals (facial expression, gestures, "
            "speech, motion, clarity) — each with its own published evidence. The legacy "
            "peak/sustained/retention/overall stats are NOT the basis."
        ),
        "components": COMPONENTS,
        "weights": {
            "engagement_blend": "0.30·default_mode + 0.25·visual + 0.20·language + 0.15·auditory + 0.10·motion",
            "comparison_share": {"brain_networks": 0.6, "production_signals": 0.4},
            "note": "The ordering is literature-informed; the exact numbers are a transparent prior, not yet fit to outcome data.",
        },
        "benchmarking": {
            "blind_validation": "On 3 hand-labelled talking-head A/B pairs, the model matched the human pick 3/3 (evals/example-7024-vs-7025.md).",
            "next_step": "Fit the signal weights to labelled outcomes (real watch-time or human A/B labels) to move from literature-informed prior to empirically calibrated.",
        },
        "caveats": [
            "Directional proxy: two stacked models, so error compounds.",
            "TRIBE is trained on long-form naturalistic film; punchy short-form is out-of-distribution.",
            "~1 Hz readout — reliable at the ~5-second level, not per-frame.",
            "Signal/network weights are a literature-informed prior, not fitted to outcomes.",
        ],
        "sources": SOURCES,
    }


def sources_for(component_key: str) -> list:
    """The sources backing one component key (e.g. from analysis.decisive)."""
    comp = next((c for c in COMPONENTS if c["key"] == component_key), None)
    if comp is None:
        return []
    by_id = {s["id"]: s for s in SOURCES}
    return [by_id[i] for i in comp["source_ids"] if i in by_id]
