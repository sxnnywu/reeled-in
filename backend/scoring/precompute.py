"""Batch-score + render the demo variants -> /cache/precomputed/. Owner: B.

For the bulletproof demo: score each demo clip once, render its brain frames,
and save the full Score Object to disk so the live pitch loads precomputed
results instead of waiting on a cold GPU (per PARALLEL_IMPLEMENTATION_PLAN P4).

Demo set = the 6 hand-recorded talking-head clips (IMG_7024..7029).
"""

import json
import os

from backend.scoring import metrics
from backend.scoring.brain_render import render_frames
from backend.scoring.networks import reduce_to_networks
from backend.scoring.regions import region_timeline
from backend.scoring.tribe_model import load_model


def precompute(clips: dict, cache_dir: str = "/cache") -> dict:
    """clips: {variant_id: video_path}. Writes /cache/precomputed/<vid>.json
    (full Score Object incl. brain_frames). Returns a summary."""
    model = load_model(cache_dir)
    out_dir = f"{cache_dir}/precomputed"
    os.makedirs(out_dir, exist_ok=True)

    summary = {}
    for vid, path in clips.items():
        events = model.get_events_dataframe(video_path=path)
        preds, _ = model.predict(events=events)

        networks = reduce_to_networks(preds)
        engagement = metrics.compute_engagement(networks)
        m = metrics.compute_metrics(engagement)
        timeline = region_timeline(preds)
        frames = render_frames(preds, vid, cache_dir)

        score_obj = {
            "variant_id": vid,
            "networks": networks,
            "engagement": engagement,
            "metrics": m,
            "brain_frames": frames,
            "region_timeline": timeline,
            "duration_sec": float(len(engagement)),
            "sample_rate_hz": 1,
        }
        with open(f"{out_dir}/{vid}.json", "w") as f:
            json.dump(score_obj, f)
        summary[vid] = {"metrics": m, "n_brain_frames": len(frames)}
        print(f"precomputed {vid}: {m}  ({len(frames)} brain frames)")
    return summary
