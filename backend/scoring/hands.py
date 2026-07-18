"""Hand + gesture detection via MediaPipe Gesture Recognizer (open-source) — Person B.

Reports, per clip:
  - hand_present_frac : fraction of frames with a hand visible
  - hand_motion       : how much the hands move over the clip (gesture energy)
  - gestures          : named gestures seen (pointing, open palm, thumbs up, etc.)

Diagnostic stats (amount, not good/bad). Animated hands are a plausible
engagement cue for talking-head content — validate before scoring on it.

Model (gesture_recognizer.task) cached to /cache.
"""

import numpy as np

from backend.scoring.objective import _sample_frames

_RECOGNIZER = None
_TASK_URL = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"


def _load(cache_dir: str = "/cache"):
    global _RECOGNIZER
    if _RECOGNIZER is None:
        import os
        import urllib.request

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        path = f"{cache_dir}/mediapipe/gesture_recognizer.task"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            urllib.request.urlretrieve(_TASK_URL, path)
        opts = vision.GestureRecognizerOptions(
            base_options=python.BaseOptions(model_asset_path=path), num_hands=2
        )
        _RECOGNIZER = vision.GestureRecognizer.create_from_options(opts)
    return _RECOGNIZER


def analyze_hands(video_path: str, cache_dir: str = "/cache", fps: int = 3) -> dict:
    import mediapipe as mp

    frames = _sample_frames(video_path, 256, 256, fps, gray=False)
    if frames is None:
        return {"hand_present_frac": 0.0, "hand_motion": 0.0, "gestures": []}
    rec = _load(cache_dir)

    hand_frames, wrist_x, wrist_y, gestures = 0, [], [], {}
    for f in frames:
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=f.astype("uint8"))
        res = rec.recognize(img)
        if res.hand_landmarks:
            hand_frames += 1
            wrist = res.hand_landmarks[0][0]  # landmark 0 = wrist of first hand
            wrist_x.append(wrist.x)
            wrist_y.append(wrist.y)
        for g in res.gestures or []:
            name = g[0].category_name
            if name and name != "None":
                gestures[name] = gestures.get(name, 0) + 1

    n = len(frames)
    hand_motion = float(np.std(wrist_x) + np.std(wrist_y)) if len(wrist_x) > 1 else 0.0
    top = sorted(gestures.items(), key=lambda kv: -kv[1])[:5]
    return {
        "hand_present_frac": round(hand_frames / n, 3),
        "hand_motion": round(hand_motion, 4),
        "gestures": [name for name, _ in top],
    }
