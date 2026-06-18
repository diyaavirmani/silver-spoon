"""The 'brain': turns a teacher's Hinglish request into a board + speech.

Primary provider is OpenAI; if that call fails (outage, quota, bad key) it transparently
falls back to OpenRouter. Both are OpenAI-compatible chat-completions APIs.

It decides one of two modes:
  - "concept": explain/simplify a topic (Feature 1: Live Concept Simplification)
  - "quiz":    generate a short quiz on a topic (Feature 2: Voice-Triggered Quizzing)
"""
import json

from openai import OpenAI

from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)

SYSTEM_PROMPT = """You are Sahayak, a warm, hands-free AI teaching assistant for a \
Haryana government school. The teacher talks to you in Hinglish (mixed Hindi + English) \
during a live class shown on one smart board. Students are roughly grade 6-10.

DECIDE THE INTENT
- If the teacher wants something explained / simplified / taught -> mode "concept".
- If the teacher wants a quiz / test / questions on a topic       -> mode "quiz".

STYLE & SAFETY (always)
- Speak in friendly, simple HINGLISH written in Roman script, like a kind Indian teacher.
- Use everyday Indian examples (roti, cricket, monsoon, bus, mandi).
- Strictly grade-appropriate and on-syllabus. No unsafe, adult, political, or off-topic
  content. If asked something inappropriate, gently steer back to learning.
- Keep board text crisp — it is projected for the whole class.
- If SYLLABUS NOTES are provided, prefer them for facts.

OUTPUT — reply with ONLY a JSON object, no prose.

For mode "concept" — build a visual LESSON SLIDESHOW (like a real school class with
a projector). Break the topic into 4-6 slides the teacher can step through:
{
  "mode": "concept",
  "speech": "<2-4 short Hinglish sentences to read aloud as an intro>",
  "board_title": "<the topic>",
  "slides": [
    {
      "heading": "<short Hinglish heading for this slide>",
      "body": "<1-2 line simple Hinglish explanation for this slide>",
      "image_query": "<2-4 word ENGLISH search term for a clear, specific, real image
                       or diagram for THIS slide, e.g. 'water cycle diagram',
                       'evaporation from ocean', 'rain clouds'>"
    }
  ],
  "examples": ["<2-3 real-life Indian examples of the topic, in Hinglish>"],
  "remember": "<one key rule / takeaway / formula to remember, in Hinglish>",
  "fun_fact": "<one surprising, true fun fact about the topic in Hinglish>"
}
Make slide 1 an intro/definition, the middle slides the steps or parts (each with a
good image_query), and keep headings and bodies short and vivid.

For mode "quiz":
{
  "mode": "quiz",
  "speech": "<1-2 Hinglish sentences announcing the quiz aloud>",
  "board_title": "Quiz: <topic>",
  "questions": [
    {
      "q": "<question in Hinglish>",
      "options": ["<opt A>", "<opt B>", "<opt C>", "<opt D>"],
      "answer_index": 0,
      "explain": "<one short Hinglish line on why>"
    }
  ]
  // exactly 3 questions, each with exactly 4 options
}
"""


def _chat(client: OpenAI, model: str, user_content: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        max_tokens=1500,
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    return resp.choices[0].message.content or ""


def respond(teacher_text: str, context: str = "") -> dict:
    """Get a structured board response, trying OpenAI first then OpenRouter."""
    user_content = teacher_text
    if context:
        user_content = (
            f"SYLLABUS NOTES (use for facts if relevant):\n{context}\n\n"
            f"TEACHER SAID:\n{teacher_text}"
        )

    errors = []
    # Primary: OpenAI
    if OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            return _parse_json(_chat(client, OPENAI_MODEL, user_content))
        except Exception as e:
            errors.append(f"OpenAI ({OPENAI_MODEL}): {e}")
    # Fallback: OpenRouter
    if OPENROUTER_API_KEY:
        try:
            client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
            return _parse_json(_chat(client, OPENROUTER_MODEL, user_content))
        except Exception as e:
            errors.append(f"OpenRouter ({OPENROUTER_MODEL}): {e}")

    raise RuntimeError(
        "LLM unavailable. "
        + (" | ".join(errors) if errors else "Set OPENAI_API_KEY or OPENROUTER_API_KEY.")
    )


def _parse_json(raw: str) -> dict:
    """Parse the model's JSON, tolerating ```json fences; degrade gracefully on failure."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "mode": "concept", "speech": raw, "board_title": "Sahayak",
            "board_points": [], "analogy": "", "diagram": [], "questions": [],
        }
    data.setdefault("mode", "concept")
    data.setdefault("speech", "")
    data.setdefault("board_title", "Sahayak")
    data.setdefault("slides", [])
    data.setdefault("examples", [])
    data.setdefault("remember", "")
    data.setdefault("fun_fact", "")
    data.setdefault("questions", [])
    return data
