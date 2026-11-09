import re
from functools import lru_cache
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit


@lru_cache(maxsize=512)
def _phrase_pattern(phrase: str) -> re.Pattern:
    normalized = " ".join((phrase or "").strip().lower().split())
    if not normalized:
        return re.compile(r"(?!x)x")
    return re.compile(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", re.IGNORECASE)


def contains_phrase(text: str, phrase: str) -> bool:
    """Match a token or phrase without matching inside another word."""
    normalized_text = " ".join((text or "").lower().split())
    return bool(_phrase_pattern(phrase).search(normalized_text))


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(contains_phrase(text, phrase) for phrase in phrases)


def canonical_story_key(title: str, url: str) -> str:
    """Return a stable key for syndicated copies and tracking-URL variants."""
    normalized_title = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()
    normalized_url = (url or "").strip()
    if normalized_url:
        try:
            parsed = urlsplit(normalized_url)
            normalized_url = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))
        except ValueError:
            pass
    return normalized_title if len(normalized_title) >= 20 else (normalized_url or normalized_title)
