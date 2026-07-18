"""Deduplication — detect and resolve duplicate tools during import."""

from core.database import get_connection
from core.models import Tool
from core.enums import ToolCategory
from utils.text import normalize_for_match


def find_duplicate(tool: Tool) -> str | None:
    """Check if a matching tool already exists in the DB.

    Returns the existing toolId if a duplicate is found, None otherwise.

    Matching rules:
    1. catalogNumber + manufacturer (both must be non-empty)
    2. For INSERTs without catalogNumber: iso_designation + grade (from attributes)
    """
    existing_id = _match_by_catalog(tool)
    if existing_id:
        return existing_id

    if tool.category == ToolCategory.INSERT:
        existing_id = _match_by_insert_attributes(tool)
        if existing_id:
            return existing_id

    return None


def _match_by_catalog(tool: Tool) -> str | None:
    """Match on catalogNumber + manufacturer (case-insensitive, whitespace-normalized)."""
    if not tool.catalog_number or not tool.manufacturer:
        return None

    conn = get_connection()
    rows = conn.execute(
        "SELECT toolId, catalogNumber, manufacturer FROM Tools "
        "WHERE catalogNumber IS NOT NULL AND manufacturer IS NOT NULL"
    ).fetchall()

    target_cat = normalize_for_match(tool.catalog_number)
    target_mfr = normalize_for_match(tool.manufacturer)

    for row in rows:
        if (normalize_for_match(row["catalogNumber"]) == target_cat
                and normalize_for_match(row["manufacturer"]) == target_mfr):
            return row["toolId"]

    return None


def _match_by_insert_attributes(tool: Tool) -> str | None:
    """Fallback for INSERTs: match on iso_designation + grade from attributes."""
    iso = tool.attributes.get("iso_designation", "")
    grade = tool.attributes.get("grade", "")
    if not iso or not grade:
        return None

    target_iso = normalize_for_match(iso)
    target_grade = normalize_for_match(grade)

    conn = get_connection()
    rows = conn.execute(
        "SELECT toolId, attributes FROM Tools WHERE category = ?",
        (ToolCategory.INSERT.value,)
    ).fetchall()

    import json
    for row in rows:
        try:
            attrs = json.loads(row["attributes"] or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        row_iso = normalize_for_match(attrs.get("iso_designation", ""))
        row_grade = normalize_for_match(attrs.get("grade", ""))
        if row_iso == target_iso and row_grade == target_grade:
            return row["toolId"]

    return None
