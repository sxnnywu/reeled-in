"""Blind A/B eval harness — Person B.

Scores a batch of clips and picks a per-pair winner on a SHARED scale, so two
clips are actually comparable. The pre-committed decision rule is: winner =
higher `overall`. Fixed here, in code, before any labels are seen.

Two normalizations are computed so we can show the difference:
  - shared : raw activation scaled by one batch-wide reference (the fix).
  - perclip: each clip stretched to its own 0..1 (the current product path,
             which flattens cross-clip differences).
"""

import numpy as np

from backend.scoring import metrics
from backend.scoring.networks import raw_networks, reduce_to_networks

WEIGHTS = metrics.NETWORK_WEIGHTS
DECISION_METRIC = "overall"  # pre-committed winner rule


def _raw_engagement(preds) -> list:
    rn = raw_networks(preds)
    n = len(next(iter(rn.values())))
    return [sum(WEIGHTS[k] * rn[k][t] for k in WEIGHTS) for t in range(n)]


def predict_curves(model, video_path: str):
    """Run TRIBE once, return (raw_engagement, perclip_engagement)."""
    events = model.get_events_dataframe(video_path=video_path)
    preds, _ = model.predict(events=events)
    raw = _raw_engagement(preds)
    perclip = metrics.compute_engagement(reduce_to_networks(preds))
    return raw, perclip


def run_ab_eval(model, clips: dict) -> dict:
    """clips: {name: video_path}. Returns per-clip metrics under both
    normalizations. Shared scale = 95th percentile of all raw values (robust max)."""
    raws, perclips = {}, {}
    for name, path in clips.items():
        raws[name], perclips[name] = predict_curves(model, path)

    all_vals = np.concatenate([np.asarray(v) for v in raws.values()])
    scale = float(np.percentile(all_vals, 95)) or 1.0

    out = {}
    for name in clips:
        shared_norm = [min(1.0, float(v) / scale) for v in raws[name]]
        out[name] = {
            "shared": metrics.compute_metrics(shared_norm),
            "perclip": metrics.compute_metrics(perclips[name]),
        }
    return out


def pair_winner(results: dict, a: str, b: str, mode: str = "shared") -> dict:
    ma, mb = results[a][mode], results[b][mode]
    va, vb = ma[DECISION_METRIC], mb[DECISION_METRIC]
    winner = a if va >= vb else b
    return {"winner": winner, "by": DECISION_METRIC, a: va, b: vb, "margin": round(abs(va - vb), 4)}
