"""Text utilities — normalization, comparison, search tokenizing."""

import re
import unicodedata


def normalize_whitespace(text: str | None) -> str:
    """Collapse all whitespace runs to a single space, strip edges."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_match(text: str | None) -> str:
    """Lowercase, strip accents, collapse whitespace — for dedup/search matching."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return normalize_whitespace(text).lower()


def strings_match(a: str | None, b: str | None) -> bool:
    """Case-insensitive, whitespace-normalized equality check."""
    return normalize_for_match(a) == normalize_for_match(b)


def tokenize_search(query: str) -> list[str]:
    """Split a search query into lowercase tokens for matching."""
    normalized = normalize_for_match(query)
    if not normalized:
        return []
    return normalized.split()


def contains_all_tokens(text: str, tokens: list[str]) -> bool:
    """Check if normalized text contains every token (AND search)."""
    norm = normalize_for_match(text)
    return all(tok in norm for tok in tokens)
