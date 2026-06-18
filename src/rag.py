"""Lightweight RAG grounding over a small NCERT-style concept corpus.

Uses TF-IDF + cosine similarity (scikit-learn) — fast, dependency-light, and good
enough to keep the brain's facts anchored to the syllabus. The retrieved snippets are
injected into Claude's context as "SYLLABUS NOTES".
"""
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Grounding:
    def __init__(self, corpus_path: str | Path):
        text = Path(corpus_path).read_text(encoding="utf-8")
        # Each blank-line-separated block is one retrievable chunk.
        self.chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        self._vec = TfidfVectorizer(stop_words="english")
        self._matrix = self._vec.fit_transform(self.chunks)

    def search(self, query: str, k: int = 2, min_score: float = 0.06) -> str:
        """Return the top-k relevant chunks joined together, or '' if nothing is relevant."""
        if not query.strip():
            return ""
        sims = cosine_similarity(self._vec.transform([query]), self._matrix)[0]
        ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)[:k]
        hits = [self.chunks[i] for i, score in ranked if score >= min_score]
        return "\n\n".join(hits)
