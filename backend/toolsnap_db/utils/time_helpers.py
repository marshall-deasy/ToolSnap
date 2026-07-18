"""Time helpers — ISO-8601 parsing and formatting."""

from datetime import datetime, timezone


def now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str | None) -> datetime | None:
    """Parse an ISO-8601 string to datetime. Returns None on failure."""
    if not text:
        return None
    try:
        # Handle both 'Z' suffix and +00:00 offset
        cleaned = text.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


def is_newer(a: str | None, b: str | None) -> bool:
    """Return True if timestamp 'a' is strictly newer than timestamp 'b'."""
    dt_a = parse_iso(a)
    dt_b = parse_iso(b)
    if dt_a is None:
        return False
    if dt_b is None:
        return True
    return dt_a > dt_b
