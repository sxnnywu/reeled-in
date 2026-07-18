"""Batch-score + render the demo variants -> /cache/precomputed/. Owner: B.

Scores the demo clips as ONE shared-scale batch (ratified CONTRACTS §3) and
renders their brain frames, then saves each full Score Object to disk so the
demo loads precomputed results instead of running the GPU live.

Demo set = the 6 hand-recorded talking-head clips (IMG_7024..7029), on the
Modal volume at /media/eval/.
"""

import json
import os

from backend.scoring.score import score_batch


def precompute(clips: dict, cache_dir: str = "/cache") -> dict:
    """clips: {variant_id: media_key or path}. Writes /cache/precomputed/<vid>.json
    (full Score Object incl. brain_frames), shared-scale across the batch."""
    out_dir = f"{cache_dir}/precomputed"
    os.makedirs(out_dir, exist_ok=True)

    media_keys = list(clips.values())
    results = score_batch(media_keys, render_brains=True)

    summary = {}
    for score_obj in results:
        vid = score_obj["variant_id"]
        with open(f"{out_dir}/{vid}.json", "w") as f:
            json.dump(score_obj, f)
        summary[vid] = {"metrics": score_obj["metrics"], "n_brain_frames": len(score_obj["brain_frames"])}
        print(f"precomputed {vid}: {score_obj['metrics']}  ({len(score_obj['brain_frames'])} brain frames)")
    return summary
