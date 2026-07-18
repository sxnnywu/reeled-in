"""Object / clarity detection via YOLO (Ultralytics, open-source) — Person B.

Answers "can you identify what's in the frame". Low detection confidence across
frames = unclear / blurry / hard-to-read video. Also reports what objects appear
and how often a person is present (all our clips are talking-head).

Model-free of the brain model; a diagnostic stat, not an engagement input.
Weights cache to /cache so cold starts don't re-download.
"""

import numpy as np

from backend.scoring.objective import _sample_frames

_MODEL = None


def _load(cache_dir: str = "/cache"):
    global _MODEL
    if _MODEL is None:
        import os
        import urllib.request

        from ultralytics import YOLO

        path = f"{cache_dir}/yolo/yolov8n.pt"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            urllib.request.urlretrieve(
                "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt", path
            )
        _MODEL = YOLO(path)
    return _MODEL


def detect_objects(video_path: str, cache_dir: str = "/cache", fps: int = 2) -> dict:
    frames = _sample_frames(video_path, 384, 384, fps, gray=False)
    if frames is None:
        return {"clarity": 0.0, "objects": [], "person_frac": 0.0}
    model = _load(cache_dir)

    confs, classes, person_hits = [], {}, 0
    for f in frames:
        res = model(f.astype("uint8"), verbose=False)[0]
        best = 0.0
        has_person = False
        for b in res.boxes:
            c = float(b.conf[0])
            name = model.names[int(b.cls[0])]
            classes[name] = classes.get(name, 0) + 1
            best = max(best, c)
            if name == "person":
                has_person = True
        confs.append(best)
        person_hits += int(has_person)

    top = sorted(classes.items(), key=lambda kv: -kv[1])[:5]
    return {
        "clarity": round(float(np.mean(confs)), 4),  # mean top detection confidence
        "objects": [name for name, _ in top],
        "person_frac": round(person_hits / len(frames), 3),
    }
