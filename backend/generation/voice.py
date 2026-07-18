"""ElevenLabs reads. Owner: D (Sunny)."""
import os

from elevenlabs.client import ElevenLabs

from backend.generation.overlay import resolve

# Premade ElevenLabs voices — distinct defaults: warm female, deep male, energetic male.
DEFAULT_VOICES = [
    "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "pNInz6obpgDQGcFmaJgB",  # Adam
    "TxGEqnHWrfWFTfGW9XjX",  # Josh
]
MODEL_ID = "eleven_multilingual_v2"


def _client() -> ElevenLabs:
    return ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


def generate_read(script: str, voice_id: str, voice_settings=None, out_name="read", out_dir="media/audio") -> str:
    """Generate one voiceover mp3. voice_settings: e.g. {"speed": 1.15, "stability": 0.5}. -> audio path"""
    out = resolve(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    audio = _client().text_to_speech.convert(
        voice_id=voice_id,
        text=script,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
        voice_settings=voice_settings,
    )
    path = out / f"{out_name}.mp3"
    with open(path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return str(path)
