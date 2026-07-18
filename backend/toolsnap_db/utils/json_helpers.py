"""JSON helpers — safe parsing, attribute extraction, merging."""

import json
from typing import Any


def safe_load(text: str | None) -> Any:
    """Parse JSON string, returning empty dict/list on failure."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}


def safe_load_list(text: str | None) -> list:
    """Parse JSON string expected to be a list, returning [] on failure."""
    result = safe_load(text)
    return result if isinstance(result, list) else []


def safe_dump(obj: Any) -> str:
    """Serialize to compact JSON string."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def extract_searchable_text(attributes: dict[str, str]) -> str:
    """Flatten attribute values into a single space-separated string for search."""
    parts = []
    for value in attributes.values():
        if value is not None:
            parts.append(str(value))
    return " ".join(parts)
