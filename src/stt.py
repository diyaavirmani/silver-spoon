"""Speech-to-text for classroom Hinglish, via OpenAI Whisper.

Note: OpenRouter has no audio endpoint, so transcription uses the OpenAI key only.
If the mic/STT is unavailable, the app's typed-input box provides the same pipeline.
"""
from openai import OpenAI

from .config import OPENAI_API_KEY, STT_MODEL


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe a short WAV clip of Hinglish classroom speech to text."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env (local) or Railway Variables (cloud)."
        )
    client = OpenAI(api_key=OPENAI_API_KEY)
    result = client.audio.transcriptions.create(
        model=STT_MODEL,
        file=("speech.wav", audio_bytes),
        # A prompt nudges Whisper toward code-switched Hindi+English output.
        prompt="Indian classroom speech mixing Hindi and English (Hinglish).",
        temperature=0.0,
    )
    return result.text.strip()
