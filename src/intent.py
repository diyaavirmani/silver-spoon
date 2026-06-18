"""Lightweight, offline intent router for quiz-control voice commands.

These are handled locally (no LLM call) so navigation feels instant during a live class.
Anything that is NOT a control command is treated as a content request for the brain.
"""

# Hinglish + English keyword sets. Order of checking is: clear, next, reveal, repeat.
_CONTROL = {
    "clear":  ["board saaf", "saaf karo", "clear board", "clear", "mita do", "hata do",
               "khatam karo", "reset"],
    "next":   ["agla sawaal", "agla sawal", "agla", "aage badho", "aage", "next question",
               "next"],
    "prev":   ["pichla", "pichhla", "pichhle", "peeche", "piche", "previous", "back"],
    "reveal": ["sahi jawab", "jawab dikha", "jawab batao", "jawaab", "jawab", "uttar",
               "answer dikha", "answer batao", "answer", "reveal"],
    "repeat": ["phir se", "dobara", "dubara", "dohrao", "wapas suna", "repeat"],
}


def classify(text: str) -> str | None:
    """Return 'clear' | 'next' | 'reveal' | 'repeat' if the utterance is a control
    command, else None (meaning: send it to the brain as a content request)."""
    t = " " + text.lower().strip() + " "
    for cmd in ("clear", "next", "prev", "reveal", "repeat"):
        if any(kw in t for kw in _CONTROL[cmd]):
            return cmd
    return None
