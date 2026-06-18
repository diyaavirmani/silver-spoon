# Vidya — Voice-Enabled AI Teaching Assistant

A hands-free, **Hinglish** voice co-pilot for teachers in Indian government schools.
The teacher speaks a command; Vidya replies **aloud** *and* projects a clean visual on
the classroom **smart board** — no typing, no mouse, no breaking the flow of the lesson.

> Built for the **Connecting Dreams Foundation — Round 2** technical assignment (**Option A**).

---

## What it does (2 of the 4 required features)

### 1. Live Concept Simplification — a visual lesson slideshow
Teacher: *“Explain the water cycle in simple Hinglish.”*
→ Vidya **speaks** an intro and builds a **multi-slide lesson** on the board. Each slide
pairs a **real image/diagram fetched live from the internet** (Wikipedia → Openverse, no API
key) with a short Hinglish heading and explanation. The teacher steps through with
**◀ Previous / Next ▶** (or by voice), and the final slide recaps with **real-life examples,
a “Remember” takeaway, and a fun fact**.

### 2. Voice-Triggered Quizzing — interactive & scored
Teacher: *“Make a quiz on this.”*
→ Vidya **announces** a quiz aloud and shows big **A/B/C/D cards**. Students **tap to
answer** — correct turns green (with a celebration), wrong turns red — and a **live score**
is kept. It’s driven by voice *or* on-screen buttons:
- *“show answer”* → reveal & explain
- *“next question”* · *“repeat”* · *“clear board”*

A small touch of empathy: while the AI thinks, the board shows a **“Did you know?”** world
fact, turning wait time into a teachable moment. Hands stay free for the class throughout.

---

## Tech stack

| Layer | Choice | Why this one |
|---|---|---|
| **UI** | Streamlit | Fast to build; easy to style a large-type, high-contrast smart-board layout |
| **Speech-to-text** | **OpenAI Whisper** (`whisper-1`) | Handles Hindi-English **code-switching** in classroom speech |
| **Brain** | **OpenAI** (`gpt-4o-mini`) → **OpenRouter** fallback | Hinglish reasoning + reliable **JSON** output; auto-fails over if OpenAI is down |
| **Text-to-speech** | **edge-tts** (`en-IN-NeerjaNeural`) | Free neural Indian-English voice that reads Romanized Hinglish naturally |
| **Images** | **Wikipedia → Openverse** (no API key) | Fetches a relevant diagram/photo per slide for self-explanatory visuals |
| **Grounding** | **TF-IDF RAG** + strict prompt guardrails | Anchors facts to a small NCERT-style syllabus corpus; keeps answers grade-appropriate |

**Why no heavy STT/embedding models?** The whole pipeline is API- or CPU-light, so it builds
and runs comfortably in a small Render container and stays responsive in a classroom.

---

## Architecture

```
Browser mic ─► OpenAI Whisper (STT) ─┐
Typed input ─────────────────────────┤
                                     ▼
                         Intent router (src/intent.py)
                         ├─ quiz/slide control? → handled instantly, offline
                         └─ content?            → TF-IDF RAG (src/rag.py)
                                                       │  + syllabus notes
                                                       ▼
                           OpenAI gpt-4o-mini  →  OpenRouter (fallback)
                           (src/brain.py) returns JSON: { mode, speech, slides|quiz }
                                     │
                       ┌─────────────┴──────────────┐
                 edge-tts (voice)            Board (src/board.py)
                 speaks Hinglish             lesson slides + images / quiz cards
```

---

## Prompt design

- **One structured call.** The model is the brain *and* the intent classifier for content:
  a single system prompt makes it decide `mode: "concept" | "quiz"` and return JSON for the
  matching shape (forced via OpenAI **JSON mode**; see `src/brain.py`). Parsing is still
  defensive — code fences are stripped and any malformed reply degrades to plain text.
- **Provider failover.** The brain calls **OpenAI** first and transparently falls back to
  **OpenRouter** on any error, so a single outage or quota hit doesn't kill the demo.
- **Guardrails baked into the system prompt:** grade 6–10 only, on-syllabus, safe, warm,
  always Roman-script Hinglish, everyday Indian examples; inappropriate asks are redirected.
- **Grounding (RAG):** the utterance is matched against a small NCERT-style corpus
  (`knowledge/concepts.md`) with TF-IDF cosine similarity; the top snippets are injected as
  `SYLLABUS NOTES` and the prompt tells the model to *prefer them for facts*.
- **Fast local commands:** navigation (*next / previous / reveal / repeat / clear*) is
  keyword-routed offline (`src/intent.py`) so it feels instant and costs no tokens mid-class.

---

## Localization

Vidya is built **around Hinglish**, not bolted on:
- **Input** is transcribed with a code-switch-aware model and a Hinglish prompt hint.
- **Taught content** (board text + spoken voice) is constrained to simple Roman-script
  Hinglish with everyday Indian examples (roti, cricket, monsoon, mandi).
- **Voice** uses an Indian-English neural voice tuned for Romanized Hinglish.
- **Chrome vs. content are intentionally separated:** the interface labels are in clean
  English (professional, easy to grade), while everything the *class* sees and hears stays
  Hinglish — the right split for a teacher-facing tool in an Indian classroom.

---

## Run locally

```powershell
cd silver-spoon
python -m venv .venv
.venv\Scripts\activate          # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env          # then paste your keys into .env
streamlit run app.py
```

You need:
- an **OpenAI API key** (required — brain + speech-to-text) — https://platform.openai.com/api-keys
- an **OpenRouter API key** (optional — brain fallback) — https://openrouter.ai/keys

No mic? Use the **type box** under the mic button — same pipeline, handy for testing/demos.

---

## Deploy on Render (→ public live URL)

Render runs the app as a container, configured from the dashboard:

1. Push this repo to GitHub (public).
2. Go to https://render.com → **New + → Web Service** → connect this GitHub repo.
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:**
     ```
     streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
     ```
   - **Instance Type:** Free
4. Under **Environment**, add variables:
   ```
   OPENAI_API_KEY     = sk-...
   OPENROUTER_API_KEY = sk-or-...   # optional fallback
   ```
5. Click **Create Web Service**. When the build finishes you get a public
   `https://<name>.onrender.com` URL — that's the live link.

> The start command binds Streamlit to `0.0.0.0:$PORT` in headless mode, which is what
> Render's proxy expects. Keys live in Render's Environment, never in the repo.
> Note: free instances sleep after ~15 min idle, so the first request after a nap takes
> ~30–50s to wake — open it once before sharing.

---

## Project layout

```
vidya/
├── app.py                 # Streamlit UI, state machine, mic + typed input, slideshow + quiz
├── src/
│   ├── config.py          # keys + model choices
│   ├── stt.py             # OpenAI Whisper speech-to-text
│   ├── brain.py           # OpenAI (→ OpenRouter) — request → {mode, speech, slides|quiz} JSON
│   ├── intent.py          # offline command router (next/prev/reveal/repeat/clear)
│   ├── rag.py             # TF-IDF grounding over the syllabus corpus
│   ├── images.py          # fetch a relevant image per slide (Wikipedia → Openverse)
│   ├── facts.py           # "Did you know?" facts shown while thinking
│   ├── board.py           # board HTML (lesson slides, recap, quiz, thinking card)
│   └── tts.py             # edge-tts speech synthesis
├── knowledge/concepts.md  # NCERT-style grounding corpus
├── assets/styles.css      # classroom-notebook theme + animations
├── .streamlit/config.toml # light notebook theme
└── requirements.txt
```

---

## Scope & honesty

This is a **proof of concept**, not a production app. Known simplifications: the syllabus
corpus is a small starter set; TF-IDF retrieval is deliberately lightweight (swap in
embeddings to scale); image relevance is best on canonical school topics; audio autoplay
depends on the browser. Everything is structured so each of these can grow without reworking
the pipeline.
