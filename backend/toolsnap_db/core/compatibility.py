"""Compatibility derivation — auto-populate insert/body compatibility from assembly data."""

from core.database import get_connection
from core.models import CompatibilityLink
from core.enums import INDEXABLE_BODY_CATEGORIES, INSERT_ROLES, ToolCategory
from core import repo


def derive_from_components() -> int:
    """Scan Components table and create Compatibility rows for insert↔body pairs.

    Only creates links where:
    - The parent tool's category is an indexable body type
    - The component role is an insert role (INSERT or WIPER_INSERT)

    Returns the number of new compatibility links created.
    """
    conn = get_connection()
    body_categories = tuple(cat.value for cat in INDEXABLE_BODY_CATEGORIES)
    insert_roles = tuple(role.value for role in INSERT_ROLES)

    # Build placeholders for IN clauses
    body_ph = ",".join("?" * len(body_categories))
    role_ph = ",".join("?" * len(insert_roles))

    rows = conn.execute(
        f"""SELECT DISTINCT c.parentToolId, c.childToolId
            FROM Components c
            JOIN Tools t ON c.parentToolId = t.toolId
            WHERE t.category IN ({body_ph})
              AND c.role IN ({role_ph})""",
        (*body_categories, *insert_roles),
    ).fetchall()

    created = 0
    for row in rows:
        body_id = row["parentToolId"]
        insert_id = row["childToolId"]
        # Check if already exists
        existing = conn.execute(
            "SELECT 1 FROM Compatibility WHERE bodyToolId = ? AND insertToolId = ?",
            (body_id, insert_id),
        ).fetchone()
        if not existing:
            link = CompatibilityLink(body_tool_id=body_id, insert_tool_id=insert_id)
            repo.upsert_compatibility(link)
            created += 1

    return created
