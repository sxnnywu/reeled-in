"""region_timeline -> plain-English per-second captions (Backboard). Owner: D."""
import json

from backend.generation.llm import _post

PROMPT = """You caption a brain-activity animation that plays beside a short video. Below is a
per-second timeline of the viewer's predicted brain response: at each second t, the most
active brain network/region and its activation strength (0-1).

Write ONE short caption per second for a creator with no neuroscience background — what their
viewer's brain is doing and what it means for the video ("locking onto a face — strong hook",
"language centers lit up — the words are landing", "attention drifting — this beat drags").
Under 12 words each. Plain, punchy, second person about "your viewer".

How to read the networks (use OUR interpretation, exactly):
- visual: eyes locked on the frame (faces/motion on screen are landing)
- auditory: the sound/music/voice has their attention
- language: the words are being processed — the script is landing
- motion: action and movement on screen is gripping them
- default_mode: HIGH = deep narrative immersion — the story feels personally meaningful
  (this is GOOD, our strongest engagement signal; never call it distraction or mind-wandering)
- low activation everywhere = attention drifting; that's when to warn the creator

Timeline:
{timeline}

Return JSON only: [{{"t": 0, "text": "..."}}, ...] — exactly one entry per timeline second."""


def explain(region_timeline: list) -> list:
    """[{t, top_network, top_region, activation}] -> [{t, text}] (CONTRACTS §5 /explain)."""
    out = _post(PROMPT.format(timeline=json.dumps(region_timeline)))
    text = out["content"].strip()
    if "[" in text:  # tolerate prose/code-fence wrapping around the JSON
        text = text[text.index("["):text.rindex("]") + 1]
    captions = json.loads(text)
    return [{"t": int(c["t"]), "text": str(c["text"])} for c in captions]


MOCK_TIMELINE = [  # covers every caption case: hook, language, immersion high + low
    {"t": 0, "top_network": "visual", "top_region": "fusiform_face_area", "activation": 0.85},
    {"t": 1, "top_network": "language", "top_region": "broca_area", "activation": 0.72},
    {"t": 2, "top_network": "auditory", "top_region": "primary_auditory", "activation": 0.55},
    {"t": 3, "top_network": "motion", "top_region": "motion_mt", "activation": 0.68},
    {"t": 4, "top_network": "default_mode", "top_region": "prefrontal_dmn", "activation": 0.80},
    {"t": 5, "top_network": "default_mode", "top_region": "prefrontal_dmn", "activation": 0.15},
]

if __name__ == "__main__":
    # Run: backend/.venv/bin/python -m backend.generation.explainer
    # Captions the mock timeline; t=4 must read as GOOD immersion, t=5 as a warning.
    from dotenv import load_dotenv
    from backend.generation.overlay import resolve
    load_dotenv(resolve("backend/.env"))
    print(json.dumps(explain(MOCK_TIMELINE), indent=2, ensure_ascii=False))
