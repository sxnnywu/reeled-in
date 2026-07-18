"""Objective, model-free video signals — Person B.

These are measured directly from the pixels (not predicted by the brain model),
so they're a reliable cross-check on TRIBE's motion system, which was found to
rank a high-camera-motion clip BELOW a static one (see evals/).

measure_motion: frame-to-frame change = how much moved (camera or subject).
Facial-feature signals (smile, mouth-open, head turn) are a planned extension
that needs a face-landmark model — see FACE_FEATURES_TODO below.
"""

import subprocess

import numpy as np


def measure_motion(video_path: str, w: int = 96, h: int = 96, fps: int = 5) -> dict:
    """Mean/peak frame-to-frame luminance change, 0..1. Higher = more movement."""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"scale={w}:{h},format=gray", "-r", str(fps),
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
    ]
    raw = subprocess.run(cmd, capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).astype(np.float32)
    n = frames.size // (w * h)
    if n < 2:
        return {"mean_motion": 0.0, "peak_motion": 0.0, "frames": int(n)}
    frames = frames[: n * w * h].reshape(n, h, w)
    diffs = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2)) / 255.0
    return {
        "mean_motion": round(float(diffs.mean()), 4),
        "peak_motion": round(float(diffs.max()), 4),
        "motion_curve": [round(float(v), 4) for v in diffs],  # per-frame, for alignment
        "frames": int(n),
    }


# FACE_FEATURES_TODO (Jay's idea): smiling / showing teeth / head turns / self-touch
# as engagement cues. Needs a face-landmark model (e.g. mediapipe FaceMesh +
# blendshapes) to get: mouth-open (teeth), smile (mouth-corner lift), head-pose
# delta (turns), and face-region motion. Build as a separate objective signal and
# validate against labelled pairs before trusting "more expression = more engaging".
