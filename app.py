"""Vidya — Voice-Enabled AI Teaching Assistant (Option A).

Features:
  1. Live Concept Simplification — spoken Hinglish + projected notebook board.
  2. Voice-Triggered Quizzing — verbal quiz with CLICKABLE options, live scoring, and
     on-screen controls (works by voice OR by tapping).

Pipeline: speak (or type) -> Whisper STT -> intent router -> brain (+RAG) -> board + voice.
"""
import random
from pathlib import Path

import streamlit as st
from streamlit_mic_recorder import mic_recorder

from src import board, brain
from src.facts import FACTS
from src.intent import classify
from src.stt import transcribe
from src.tts import speak_to_file

st.set_page_config(page_title="Vidya — AI Teaching Assistant", page_icon="📒", layout="wide")

_css = Path(__file__).parent / "assets" / "styles.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_grounding():
    try:
        from src.rag import Grounding
        return Grounding(Path(__file__).parent / "knowledge" / "concepts.md")
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=86400)
def cached_image(query: str):
    from src.images import fetch_image_url
    return fetch_image_url(query)


# --- Session state ---
st.session_state.setdefault("mode", None)               # None | "concept" | "quiz"
st.session_state.setdefault("slides", [])
st.session_state.setdefault("slide_idx", 0)
st.session_state.setdefault("concept_title", "")
st.session_state.setdefault("examples", [])
st.session_state.setdefault("remember", "")
st.session_state.setdefault("fun_fact", "")
st.session_state.setdefault("topic", "")
st.session_state.setdefault(
    "quiz",
    {"active": False, "questions": [], "idx": 0, "revealed": False,
     "picked": None, "correct": 0, "total": 0, "answered": set(), "title": ""},
)
st.session_state.setdefault("last_text", "")
st.session_state.setdefault("audio_bytes", None)
st.session_state.setdefault("turn", 0)
st.session_state.setdefault("last_audio_id", None)
st.session_state.setdefault("celebrate", False)


# ============================ helpers ============================
def _say(text: str) -> None:
    """Synthesize speech for `text` into session state (best-effort)."""
    st.session_state.turn += 1
    try:
        path = speak_to_file(text or "…", f"response_{st.session_state.turn % 2}.mp3")
        st.session_state.audio_bytes = Path(path).read_bytes()
    except Exception:
        st.session_state.audio_bytes = None


def do_clear() -> None:
    st.session_state.mode = None
    st.session_state.quiz["active"] = False
    _say("Theek hai, board saaf kar diya.")


# --- quiz actions (shared by voice commands AND on-screen buttons) ---
def quiz_pick(i: int) -> None:
    q = st.session_state.quiz
    cur = q["questions"][q["idx"]]
    q["picked"] = i
    q["revealed"] = True
    if q["idx"] not in q["answered"]:           # score each question only once
        q["answered"].add(q["idx"])
        q["total"] += 1
        if i == cur.get("answer_index", 0):
            q["correct"] += 1
    if i == cur.get("answer_index", 0):
        st.session_state.celebrate = True
        _say("Bilkul sahi jawab! Shabaash!")
    else:
        right = cur["options"][cur.get("answer_index", 0)]
        _say(f"Thoda galat. Sahi jawab hai {right}. {cur.get('explain', '')}")


def quiz_reveal() -> None:
    q = st.session_state.quiz
    cur = q["questions"][q["idx"]]
    q["revealed"] = True
    _say(f"Sahi jawab hai {cur['options'][cur.get('answer_index', 0)]}. {cur.get('explain', '')}")


def quiz_next() -> None:
    q = st.session_state.quiz
    if q["idx"] < len(q["questions"]) - 1:
        q["idx"] += 1
        q["revealed"] = False
        q["picked"] = None
        _say(f"Agla sawaal. {q['questions'][q['idx']]['q']}")
    else:
        _say(f"Quiz poora ho gaya! Aapka score {q['correct']} out of {q['total']}. Shabaash bachcho!")


def quiz_repeat() -> None:
    q = st.session_state.quiz
    _say(q["questions"][q["idx"]]["q"])


# --- concept slideshow actions (shared by arrows AND voice) ---
def slide_next() -> None:
    if st.session_state.slide_idx < len(st.session_state.slides) - 1:
        st.session_state.slide_idx += 1
    cur = st.session_state.slides[st.session_state.slide_idx]
    _say(cur.get("body") or cur.get("heading", ""))


def slide_prev() -> None:
    if st.session_state.slide_idx > 0:
        st.session_state.slide_idx -= 1
    cur = st.session_state.slides[st.session_state.slide_idx]
    _say(cur.get("body") or cur.get("heading", ""))


def handle_utterance(text: str) -> None:
    """Route one utterance: quiz-control command, or a content request to the brain."""
    text = text.strip()
    if not text:
        return
    st.session_state.last_text = text
    q = st.session_state.quiz
    cmd = classify(text)

    if cmd == "clear":
        do_clear()
        return
    if q["active"] and cmd in ("next", "reveal", "repeat"):
        {"reveal": quiz_reveal, "next": quiz_next, "repeat": quiz_repeat}[cmd]()
        return
    # Voice navigation through concept slides
    if st.session_state.mode == "concept" and st.session_state.slides and cmd in ("next", "prev", "repeat"):
        if cmd == "next":
            slide_next()
        elif cmd == "prev":
            slide_prev()
        else:  # repeat current slide
            _say(st.session_state.slides[st.session_state.slide_idx].get("body", ""))
        return

    # Content request -> brain, grounded by the syllabus corpus
    g = get_grounding()
    context = g.search(text) if g else ""
    result = brain.respond(text, context)

    if result.get("mode") == "quiz" and result.get("questions"):
        st.session_state.mode = "quiz"
        st.session_state.quiz = {
            "active": True, "questions": result["questions"], "idx": 0,
            "revealed": False, "picked": None, "correct": 0, "total": 0,
            "answered": set(), "title": result.get("board_title", "Quiz"),
        }
    else:
        st.session_state.mode = "concept"
        slides = result.get("slides") or [{
            "heading": result.get("board_title", ""),
            "body": result.get("speech", ""),
            "image_query": result.get("board_title", ""),
        }]
        st.session_state.slides = slides
        st.session_state.slide_idx = 0
        st.session_state.concept_title = result.get("board_title") or text
        st.session_state.examples = result.get("examples", [])
        st.session_state.remember = result.get("remember", "")
        st.session_state.fun_fact = result.get("fun_fact", "")
        st.session_state.topic = result.get("board_title") or text
    _say(result.get("speech", ""))


# ============================ header ============================
st.markdown('<div class="nb-title">Vidya</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="nb-sub">A voice-first teaching assistant for the Hinglish classroom</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="nb-hint">Speak or type a command — for example, '
    '<b>"Explain photosynthesis in simple Hinglish"</b> or <b>"Quiz the class on it"</b></div>',
    unsafe_allow_html=True,
)

# --- Input row: mic + typed fallback ---
_, mid, _ = st.columns([1, 2, 1])
with mid:
    audio = mic_recorder(
        start_prompt="Start speaking", stop_prompt="Stop recording",
        just_once=True, use_container_width=True, key="mic",
    )
    st.markdown(
        '<div class="mic-status"><span class="pulse-dot"></span>'
        "Tap to speak, or type your command below</div>",
        unsafe_allow_html=True,
    )
    with st.form("type_form", clear_on_submit=True):
        typed = st.text_input(
            "type", placeholder="or type a command here", label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

# --- Resolve incoming utterance (mic OR typed) and process it ---
incoming = None
new_audio = bool(audio and audio.get("id") != st.session_state.last_audio_id)
typed_in = typed.strip() if submitted else ""

if new_audio or typed_in:
    # Show a brilliant fact while transcribing + thinking, then clear it.
    status = st.empty()
    status.markdown(board.thinking_html(random.choice(FACTS)), unsafe_allow_html=True)
    try:
        if new_audio:
            st.session_state.last_audio_id = audio.get("id")
            incoming = transcribe(audio["bytes"])
        if typed_in:
            incoming = typed_in
        if incoming:
            handle_utterance(incoming)
    except Exception as err:
        st.error(f"Something went wrong: {err}")
    finally:
        status.empty()

# --- Teacher line ---
if st.session_state.last_text:
    st.markdown(
        f'<div class="teacher-wrap"><span class="teacher-chip"><b>Teacher:</b> '
        f"{st.session_state.last_text}</span></div>",
        unsafe_allow_html=True,
    )

# ============================ board ============================
mode = st.session_state.mode
quiz = st.session_state.quiz

if mode == "concept" and st.session_state.slides:
    slides = st.session_state.slides
    idx = st.session_state.slide_idx
    slide = slides[idx]
    with st.spinner(""):
        image_url = cached_image(slide.get("image_query") or st.session_state.concept_title)
    st.markdown(
        board.slide_html(st.session_state.concept_title, slide, idx, len(slides), image_url),
        unsafe_allow_html=True,
    )

    # Prev / counter / Next arrows
    nav1, nav2, nav3 = st.columns([1, 1, 1])
    if nav1.button("◀ Previous", use_container_width=True, disabled=(idx == 0), key="sl_prev"):
        slide_prev(); st.rerun()
    nav2.markdown(f'<div class="slide-count">{idx + 1} / {len(slides)}</div>', unsafe_allow_html=True)
    if nav3.button("Next ▶", use_container_width=True, disabled=(idx >= len(slides) - 1), key="sl_next"):
        slide_next(); st.rerun()

    # Recap on the last slide
    if idx >= len(slides) - 1:
        recap = board.recap_html(
            st.session_state.remember, st.session_state.fun_fact, st.session_state.examples
        )
        if recap:
            st.markdown(recap, unsafe_allow_html=True)

    st.caption('Voice also works: *“next” · “previous” · “repeat” · “clear board”*')
    b1, b2 = st.columns(2)
    if b1.button("Make a quiz on this", use_container_width=True, key="cc_quiz"):
        topic = st.session_state.topic or st.session_state.last_text
        handle_utterance(f"{topic} ka ek chhota quiz banao")
        st.rerun()
    if b2.button("Clear board", use_container_width=True, key="cc_clear"):
        do_clear()
        st.rerun()

elif mode == "quiz" and quiz["active"]:
    cur = quiz["questions"][quiz["idx"]]
    st.markdown(board.quiz_header_html(quiz), unsafe_allow_html=True)

    if not quiz["revealed"]:
        # Clickable options — tap to answer
        cols = st.columns(2)
        for i, opt in enumerate(cur["options"]):
            if cols[i % 2].button(
                f"{chr(65 + i)}.  {opt}", use_container_width=True, key=f"opt_{quiz['idx']}_{i}"
            ):
                quiz_pick(i)
                st.rerun()
    else:
        st.markdown(board.quiz_cards_html(cur, quiz.get("picked")), unsafe_allow_html=True)

    # On-screen controls (mirror the voice commands)
    st.caption('Voice also works: *“show answer” · “next question” · “repeat” · “clear board”*')
    k1, k2, k3 = st.columns(3)
    last_q = quiz["idx"] >= len(quiz["questions"]) - 1
    if not quiz["revealed"]:
        if k1.button("Show answer", use_container_width=True, key="c_reveal"):
            quiz_reveal(); st.rerun()
    else:
        if k1.button("See score" if last_q else "Next question",
                     use_container_width=True, key="c_next"):
            quiz_next(); st.rerun()
    if k2.button("Repeat", use_container_width=True, key="c_repeat"):
        quiz_repeat(); st.rerun()
    if k3.button("Clear board", use_container_width=True, key="c_clear"):
        do_clear(); st.rerun()

else:
    st.markdown(
        '<div class="note-card empty-note"><div class="big">The board is ready</div>'
        '<div class="ex">Tap a topic to begin — or speak / type your own command.</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="try-label">Try one of these</div>', unsafe_allow_html=True)
    starters = [
        ("Water cycle", "Explain the water cycle in simple Hinglish"),
        ("Photosynthesis", "Explain photosynthesis in simple Hinglish"),
        ("Fractions", "Explain fractions in simple Hinglish"),
        ("Solar system", "Explain the solar system in simple Hinglish"),
        ("Gravity", "Explain gravity in simple Hinglish"),
        ("Quiz: Water cycle", "Make a quiz on the water cycle"),
    ]
    scols = st.columns(3)
    for i, (label, prompt) in enumerate(starters):
        if scols[i % 3].button(label, use_container_width=True, key=f"starter_{i}"):
            handle_utterance(prompt)
            st.rerun()

# --- Voice playback + celebration ---
if st.session_state.audio_bytes:
    st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)
if st.session_state.celebrate:
    st.balloons()
    st.session_state.celebrate = False
