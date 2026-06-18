"""Central config: loads API keys and model choices.

Keys are read from Streamlit secrets first (works on Streamlit Cloud), then from a
local .env file / environment variables (works locally and on Railway Variables).
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(key: str) -> str | None:
    # Prefer Streamlit secrets when present; fall back to env vars (Railway / local .env).
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


# --- API keys ---
OPENAI_API_KEY = _get("OPENAI_API_KEY")          # primary: brain + speech-to-text
OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY")  # fallback for the brain only

# --- Models ---
# Brain (chat). gpt-4o-mini is fast + cheap and handles Hinglish + JSON well; bump to
# "gpt-4o" for higher quality.
OPENAI_MODEL = "gpt-4o-mini"
# OpenRouter fallback model id. Keep it OpenAI-compatible for the same JSON behaviour;
# switch to e.g. "anthropic/claude-3.5-sonnet" for cross-provider redundancy.
OPENROUTER_MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Speech-to-text: OpenAI Whisper (good at Hindi-English code-switching).
STT_MODEL = "whisper-1"

# Text-to-speech: Indian-English neural voice reads Roman-script Hinglish naturally.
TTS_VOICE = "en-IN-NeerjaNeural"
