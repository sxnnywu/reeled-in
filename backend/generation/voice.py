"""ElevenLabs reads. Owner: D (Sunny)."""
import os
from pathlib import Path

from elevenlabs.client import ElevenLabs

from backend.generation.overlay import resolve

# Premade ElevenLabs voices — distinct reads for A/B: warm female, deep male, energetic male.
DEFAULT_VOICES = [
    "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "pNInz6obpgDQGcFmaJgB",  # Adam
    "TxGEqnHWrfWFTfGW9XjX",  # Josh
]
MODEL_ID = "eleven_multilingual_v2"


def _client() -> ElevenLabs:
    return ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


def generate_reads(script: str, voices=None, out_dir="media/audio", voice_settings=None) -> list:
    """Generate one voiceover mp3 per voice. -> [{"voice_id", "audio_path"}]

    voice_settings: optional dict, e.g. {"speed": 1.15, "stability": 0.5} — pacing/delivery knobs.
    """
    voices = voices or DEFAULT_VOICES
    out = resolve(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    client = _client()
    reads = []
    for voice_id in voices:
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=script,
            model_id=MODEL_ID,
            output_format="mp3_44100_128",
            voice_settings=voice_settings,
        )
        path = out / f"read_{voice_id}.mp3"
        with open(path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        reads.append({"voice_id": voice_id, "audio_path": str(path)})
    return reads
