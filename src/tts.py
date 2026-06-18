"""Text-to-speech using edge-tts (free Microsoft neural voices)."""
import asyncio

import edge_tts

from .config import TTS_VOICE


async def _synth(text: str, path: str, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)


def speak_to_file(text: str, path: str = "response.mp3", voice: str = TTS_VOICE) -> str:
    """Synthesize Hinglish speech to an mp3 file and return its path."""
    if not text.strip():
        raise ValueError("Nothing to speak.")
    asyncio.run(_synth(text, path, voice))
    return path
