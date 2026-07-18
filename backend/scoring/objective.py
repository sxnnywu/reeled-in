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


def _sample_frames(video_path: str, w: int, h: int, fps: int, gray: bool = True):
    px = "gray" if gray else "rgb24"
    fmt = "gray" if gray else "rgb24"
    cmd = ["ffmpeg", "-i", video_path, "-vf", f"scale={w}:{h}" + (",format=gray" if gray else ""),
           "-r", str(fps), "-f", "rawvideo", "-pix_fmt", px, "pipe:1"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    ch = 1 if gray else 3
    n = raw and len(raw) // (w * h * ch)
    if not n:
        return None
    arr = np.frombuffer(raw, np.uint8)[: n * w * h * ch].astype(np.float32)
    return arr.reshape((n, h, w) if gray else (n, h, w, ch))


def measure_volume(video_path: str, sr: int = 16000) -> dict:
    """Audio loudness = RMS energy of the track, in [0,1] (higher = louder).
    Whole-clip aggregate. No audio track -> 0.0."""
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-ac", "1", "-ar", str(sr),
           "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    if not raw:
        return {"volume": 0.0}
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(a * a))) if a.size else 0.0
    return {"volume": round(rms, 5)}


def measure_sharpness(video_path: str, w: int = 240, h: int = 240, fps: int = 2) -> dict:
    """Laplacian variance = focus/sharpness. Low = blurry/soft. Model-free."""
    frames = _sample_frames(video_path, w, h, fps, gray=True)
    if frames is None:
        return {"sharpness": 0.0}
    # Laplacian kernel via numpy (no cv2 dependency for this one).
    k = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    vals = []
    for f in frames:
        lap = (
            f[2:, 1:-1] + f[:-2, 1:-1] + f[1:-1, 2:] + f[1:-1, :-2] - 4 * f[1:-1, 1:-1]
        )
        vals.append(float(lap.var()))
    return {"sharpness": round(float(np.mean(vals)), 2)}
