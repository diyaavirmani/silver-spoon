"""Fetch a relevant image URL for a topic — no API key required.

Tries Wikipedia (good for canonical school diagrams) first, then Openverse
(Creative-Commons image search) as a fallback. Returns None if nothing is found.
"""
from urllib.parse import quote

import requests

_HEADERS = {"User-Agent": "Vidya-EduApp/1.0 (classroom teaching assistant)"}
_TIMEOUT = 6


def fetch_image_url(query: str) -> str | None:
    if not query or not query.strip():
        return None
    query = query.strip()

    # 1) Wikipedia page summary thumbnail (clean, education-friendly diagrams)
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query)}",
            headers=_HEADERS, timeout=_TIMEOUT,
        )
        if r.ok:
            data = r.json()
            thumb = (data.get("originalimage") or data.get("thumbnail") or {}).get("source")
            if thumb:
                return thumb
    except Exception:
        pass

    # 2) Openverse Creative-Commons image search
    try:
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "page_size": 1},
            headers=_HEADERS, timeout=_TIMEOUT,
        )
        if r.ok:
            results = r.json().get("results") or []
            if results:
                return results[0].get("thumbnail") or results[0].get("url")
    except Exception:
        pass

    return None
