"""Render smart-board HTML in the 'classroom notebook' style.

Concept boards are pure display HTML. The quiz is split: a display header here, with
the clickable options / scored cards driven by Streamlit buttons in app.py.
"""
import html


def _esc(s) -> str:
    return html.escape(str(s))


def thinking_html(fact: str) -> str:
    """A 'working…' card that shows a brilliant fact while the assistant thinks."""
    return (
        '<div class="thinking-card">'
        '<div class="tk-dots"><span></span><span></span><span></span></div>'
        '<div class="tk-label">One moment — preparing your board…</div>'
        f'<div class="tk-fact"><span class="lead">Did you know?</span> {_esc(fact)}</div>'
        "</div>"
    )


def slide_html(title: str, slide: dict, idx: int, total: int, image_url: str | None) -> str:
    """One big lesson slide: topic header, large image, heading, explanation."""
    heading = _esc(slide.get("heading", ""))
    body = _esc(slide.get("body", ""))
    if image_url:
        img = f'<img class="slide-img" src="{_esc(image_url)}" alt="{heading}">'
    else:
        img = '<div class="slide-img placeholder">Image yahan aayega</div>'
    return (
        f'<div class="note-card big-board slide" data-slide="{idx}">'
        f'<div class="slide-top"><span class="slide-topic">{_esc(title)}</span>'
        f'<span class="slide-badge">Slide {idx + 1} / {total}</span></div>'
        f"{img}"
        f'<div class="slide-heading">{heading}</div>'
        f'<div class="slide-body">{body}</div></div>'
    )


def recap_html(remember: str, fun_fact: str, examples=None) -> str:
    """A closing recap card shown on the last slide: examples + key takeaway + fun fact."""
    remember = (remember or "").strip()
    fun = (fun_fact or "").strip()
    examples = examples or []
    if not remember and not fun and not examples:
        return ""

    ex_html = ""
    if examples:
        items = "".join(
            f'<div class="example-card"><span class="ex-tag">e.g.</span>{_esc(e)}</div>' for e in examples
        )
        ex_html = f'<div class="section-label">Examples</div><div class="examples">{items}</div>'

    rb = f'<div class="remember-box"><span class="rb-tag">Remember</span>{_esc(remember)}</div>' if remember else ""
    ff = f'<div class="funfact"><b>Fun fact:</b> {_esc(fun)}</div>' if fun else ""
    return f'<div class="note-card recap">{ex_html}{rb}{ff}</div>'


def quiz_header_html(quiz: dict) -> str:
    """Top card for a quiz: title, progress, live score, and the current question."""
    cur = quiz["questions"][quiz["idx"]]
    total_q = len(quiz["questions"])
    title = _esc(quiz.get("title", "Quiz"))
    badge = f'Sawaal {quiz["idx"] + 1} / {total_q}'
    score = f'⭐ {quiz.get("correct", 0)} / {quiz.get("total", 0)}'
    return (
        f'<div class="note-card"><div class="quiz-top">'
        f'<span class="quiz-badge">{title} &nbsp;•&nbsp; {badge}</span>'
        f'<span class="quiz-score">{score}</span></div>'
        f'<div class="quiz-q">{_esc(cur["q"])}</div></div>'
    )


def quiz_cards_html(cur: dict, picked) -> str:
    """The revealed/answered state: colour the correct (green) and a wrong pick (red)."""
    ans = cur.get("answer_index", 0)
    rows = []
    for i, opt in enumerate(cur["options"]):
        cls = "opt-card"
        if i == ans:
            cls += " correct"
        elif picked is not None and i == picked:
            cls += " wrong"
        else:
            cls += " dim"
        rows.append(f'<div class="{cls}"><span class="k">{chr(65 + i)}</span>{_esc(opt)}</div>')
    explain = (cur.get("explain") or "").strip()
    explain_html = f'<div class="explain-note">💡 {_esc(explain)}</div>' if explain else ""
    return f'<div class="note-card quiz-cards">{"".join(rows)}{explain_html}</div>'
