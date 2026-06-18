# 🎬 Sahayak — 3-minute walkthrough script

Target: **≤ 3:00**. Screen-record the running app; speak over it. Keep energy warm and
classroom-real. Timestamps are a guide.

---

### 0:00 – 0:25 · The problem (hook)
> “Imagine a teacher in a Haryana government school. One smart board, forty students,
> and her hands are full — chalk, register, no time to type. Students speak Hinglish.
> Meet **Sahayak** — a hands-free, voice-first AI co-pilot for that classroom.”

*On screen:* the Sahayak home board, tagline visible.

---

### 0:25 – 1:20 · Feature 1 — Live Concept Simplification
1. Click the mic. Say: **“Photosynthesis simple Hinglish mein samjhao.”**
2. Let it think (~2s). The board fills in; the voice speaks.

> “She just *spoke* — no typing. Sahayak explains in simple Hinglish, **and** projects it:
> crisp points, an everyday analogy — ‘jaise maa roti banati hai’ — and a little flow
> diagram. That’s the explanation done, hands-free.”

*Tip:* pause so the viewer hears the Hinglish voice for a couple of seconds.

---

### 1:20 – 2:25 · Feature 2 — Voice-Triggered Quizzing
1. Click the mic. Say: **“Ab isi topic ka quiz lo.”** → quiz cards appear, announced aloud.
2. Say: **“Jawab dikhao.”** → correct card lights up green + one-line reason.
3. Say: **“Agla sawaal.”** → next question.

> “Now I just say ‘quiz lo’ and Sahayak runs the quiz for the whole class — announces it,
> shows A-B-C-D on the board, and I control everything by voice: reveal the answer, next
> question, repeat. The teacher never touches the keyboard.”

---

### 2:25 – 3:00 · How it’s built + close
> “Under the hood: Groq Whisper handles Hinglish speech, Claude is the brain returning a
> structured board plus what to say, a small TF-IDF retriever keeps facts on-syllabus, and
> edge-tts gives it an Indian voice. Streamlit projects it on the smart board.
> It’s a proof of concept — but it shows how voice + AI can give every government-school
> teacher a patient, bilingual assistant. That’s **Sahayak**. Thank you!”

*On screen:* show the repo / live URL briefly at the end.

---

## 🎥 Recording tips
- **Test once fully before recording** — first call warms up the models.
- If your room is noisy or the mic is unreliable, use the **type box** for a clean take;
  the pipeline is identical and the demo still reads as voice-driven.
- Project at a **large window size** so the board text is legible in the recording.
- Have keys set in `.env` (local) or Secrets (cloud) before you hit record.
- Two strong demo topics that hit the RAG corpus: **photosynthesis**, **water cycle**.
