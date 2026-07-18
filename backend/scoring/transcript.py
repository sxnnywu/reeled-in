"""Speech transcript via Whisper (open-source) — Person B.

TRIBE listens to speech internally but never gives us the words. Whisper does,
so we can report what was said plus speech-rate stats (talking-head clips live
or die on delivery). Diagnostic + future text/hook features.

Model weights cache to /cache.
"""

_MODEL = None


def _load(cache_dir: str = "/cache", size: str = "base"):
    global _MODEL
    if _MODEL is None:
        import whisper

        _MODEL = whisper.load_model(size, download_root=f"{cache_dir}/whisper")
    return _MODEL


def transcribe(video_path: str, cache_dir: str = "/cache") -> dict:
    model = _load(cache_dir)
    result = model.transcribe(video_path, fp16=False)
    text = result.get("text", "").strip()
    segs = result.get("segments", [])
    dur = float(segs[-1]["end"]) if segs else 0.0
    words = text.split()
    return {
        "text": text,
        "word_count": len(words),
        "words_per_sec": round(len(words) / dur, 2) if dur > 0 else 0.0,
        "duration_sec": round(dur, 1),
    }
