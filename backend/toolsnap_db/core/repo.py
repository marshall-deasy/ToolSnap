"""Repository — all database read/write operations.

Every query and mutation goes through this module. No other module
writes SQL directly against the Tools/Components/Compatibility/Inventory tables.
"""

from __future__ import annotations

import json
from typing import Optional

from core.database import get_connection, transaction
from core.models import Tool, Component, CompatibilityLink, InventoryRecord
from core.enums import ToolCategory
from utils.text import normalize_for_match, tokenize_search
from utils.json_helpers import extract_searchable_text


# ── Tools ──────────────────────────────────────────────────────────────

def upsert_tool(tool: Tool) -> None:
    """Insert or update a tool row."""
    row = tool.to_row()
    conn = get_connection()
    conn.execute(
        """INSERT INTO Tools (toolId, name, category, type, manufacturer,
           catalogNumber, description, unitSystem, attributes, notes,
           tags, photos, createdAt, modifiedAt)
           VALUES (:toolId, :name, :category, :type, :manufacturer,
           :catalogNumber, :description, :unitSystem, :attributes, :notes,
           :tags, :photos, :createdAt, :modifiedAt)
           ON CONFLICT(toolId) DO UPDATE SET
             name=excluded.name, category=excluded.category, type=excluded.type,
             manufacturer=excluded.manufacturer, catalogNumber=excluded.catalogNumber,
             description=excluded.description, unitSystem=excluded.unitSystem,
             attributes=excluded.attributes, notes=excluded.notes,
             tags=excluded.tags, photos=excluded.photos,
             modifiedAt=excluded.modifiedAt""",
        row,
    )


def get_tool(tool_id: str) -> Tool | None:
    """Fetch a single tool by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM Tools WHERE toolId = ?", (tool_id,)).fetchone()
    return Tool.from_row(row) if row else None


def get_all_tools() -> list[Tool]:
    """Fetch every tool in the database."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM Tools ORDER BY name").fetchall()
    return [Tool.from_row(r) for r in rows]


def search_tools(
    query: str = "",
    category: ToolCategory | None = None,
    tags: list[str] | None = None,
    attribute_filters: dict[str, str] | None = None,
) -> list[Tool]:
    """Search tools with optional filters.

    - query: free-text search across name, manufacturer, catalogNumber, description, attributes
    - category: restrict to one category
    - tags: tool must have ALL specified tags
    - attribute_filters: key/value pairs that must appear in the tool's attributes JSON
    """
    conn = get_connection()

    sql = "SELECT * FROM Tools WHERE 1=1"
    params: list = []

    if category:
        sql += " AND category = ?"
        params.append(category.value)

    rows = conn.execute(sql, params).fetchall()
    tools = [Tool.from_row(r) for r in rows]

    # Apply in-memory filters (text search, tags, attribute filters)
    if query:
        tokens = tokenize_search(query)
        if tokens:
            tools = [t for t in tools if _tool_matches_tokens(t, tokens)]

    if tags:
        tag_set = {normalize_for_match(t) for t in tags}
        tools = [t for t in tools if tag_set.issubset(
            {normalize_for_match(tg) for tg in t.tags}
        )]

    if attribute_filters:
        tools = [t for t in tools if _tool_matches_attributes(t, attribute_filters)]

    tools.sort(key=lambda t: t.name.lower())
    return tools


def delete_tool(tool_id: str) -> None:
    """Delete a tool and all related component/compatibility/inventory rows."""
    conn = get_connection()
    conn.execute("DELETE FROM Components WHERE parentToolId = ? OR childToolId = ?", (tool_id, tool_id))
    conn.execute("DELETE FROM Compatibility WHERE bodyToolId = ? OR insertToolId = ?", (tool_id, tool_id))
    conn.execute("DELETE FROM Inventory WHERE toolId = ?", (tool_id,))
    conn.execute("DELETE FROM Tools WHERE toolId = ?", (tool_id,))


def get_tool_count() -> int:
    """Return total number of tools in the database."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM Tools").fetchone()
    return row["cnt"] if row else 0


def get_distinct_values(column: str) -> list[str]:
    """Get distinct non-null values for a Tools column (for filter dropdowns)."""
    allowed = {"category", "manufacturer", "unitSystem"}
    if column not in allowed:
        raise ValueError(f"Column not allowed for distinct query: {column}")
    conn = get_connection()
    rows = conn.execute(
        f"SELECT DISTINCT {column} FROM Tools WHERE {column} IS NOT NULL ORDER BY {column}"
    ).fetchall()
    return [row[0] for row in rows]


def get_all_tags() -> list[str]:
    """Get all unique tags across all tools."""
    conn = get_connection()
    rows = conn.execute("SELECT tags FROM Tools WHERE tags IS NOT NULL AND tags != '[]'").fetchall()
    tag_set: set[str] = set()
    for row in rows:
        try:
            tag_list = json.loads(row["tags"])
            tag_set.update(tag_list)
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(tag_set)


# ── Components ─────────────────────────────────────────────────────────

def upsert_component(comp: Component) -> None:
    """Insert or update a component link."""
    row = comp.to_row()
    conn = get_connection()
    conn.execute(
        """INSERT INTO Components (parentToolId, childToolId, role, quantity, notes)
           VALUES (:parentToolId, :childToolId, :role, :quantity, :notes)
           ON CONFLICT(parentToolId, childToolId, role) DO UPDATE SET
             quantity=excluded.quantity, notes=excluded.notes""",
        row,
    )


def get_children(parent_tool_id: str) -> list[tuple[Component, Tool]]:
    """Get all child components of an assembly, with their tool details."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, t.* FROM Components c
           JOIN Tools t ON c.childToolId = t.toolId
           WHERE c.parentToolId = ?
           ORDER BY c.role, t.name""",
        (parent_tool_id,),
    ).fetchall()
    results = []
    for row in rows:
        comp = Component(
            parent_tool_id=row["parentToolId"],
            child_tool_id=row["childToolId"],
            role=row["role"],
            quantity=row["quantity"],
            notes=row[4],  # component notes (index 4)
        )
        tool = Tool.from_row(row)
        results.append((comp, tool))
    return results


def get_parents(child_tool_id: str) -> list[tuple[Component, Tool]]:
    """Get all assemblies that contain a given tool as a component."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, t.* FROM Components c
           JOIN Tools t ON c.parentToolId = t.toolId
           WHERE c.childToolId = ?
           ORDER BY t.name""",
        (child_tool_id,),
    ).fetchall()
    results = []
    for row in rows:
        comp = Component(
            parent_tool_id=row["parentToolId"],
            child_tool_id=row["childToolId"],
            role=row["role"],
            quantity=row["quantity"],
            notes=row[4],
        )
        tool = Tool.from_row(row)
        results.append((comp, tool))
    return results


def delete_component(parent_tool_id: str, child_tool_id: str, role: str) -> None:
    """Remove a specific component link."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM Components WHERE parentToolId = ? AND childToolId = ? AND role = ?",
        (parent_tool_id, child_tool_id, role),
    )


# ── Compatibility ──────────────────────────────────────────────────────

def upsert_compatibility(link: CompatibilityLink) -> None:
    """Insert or update a compatibility link."""
    row = link.to_row()
    conn = get_connection()
    conn.execute(
        """INSERT INTO Compatibility (bodyToolId, insertToolId, fitNotes)
           VALUES (:bodyToolId, :insertToolId, :fitNotes)
           ON CONFLICT(bodyToolId, insertToolId) DO UPDATE SET
             fitNotes=excluded.fitNotes""",
        row,
    )


def get_compatible_inserts(body_tool_id: str) -> list[tuple[CompatibilityLink, Tool]]:
    """Get all inserts compatible with a given body."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, t.* FROM Compatibility c
           JOIN Tools t ON c.insertToolId = t.toolId
           WHERE c.bodyToolId = ?
           ORDER BY t.name""",
        (body_tool_id,),
    ).fetchall()
    results = []
    for row in rows:
        link = CompatibilityLink(
            body_tool_id=row["bodyToolId"],
            insert_tool_id=row["insertToolId"],
            fit_notes=row["fitNotes"],
        )
        tool = Tool.from_row(row)
        results.append((link, tool))
    return results


def get_compatible_bodies(insert_tool_id: str) -> list[tuple[CompatibilityLink, Tool]]:
    """Get all bodies that accept a given insert."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, t.* FROM Compatibility c
           JOIN Tools t ON c.bodyToolId = t.toolId
           WHERE c.insertToolId = ?
           ORDER BY t.name""",
        (insert_tool_id,),
    ).fetchall()
    results = []
    for row in rows:
        link = CompatibilityLink(
            body_tool_id=row["bodyToolId"],
            insert_tool_id=row["insertToolId"],
            fit_notes=row["fitNotes"],
        )
        tool = Tool.from_row(row)
        results.append((link, tool))
    return results


def delete_compatibility(body_tool_id: str, insert_tool_id: str) -> None:
    """Remove a compatibility link."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM Compatibility WHERE bodyToolId = ? AND insertToolId = ?",
        (body_tool_id, insert_tool_id),
    )


# ── Inventory ──────────────────────────────────────────────────────────

def upsert_inventory(record: InventoryRecord) -> None:
    """Insert or update an inventory record."""
    row = record.to_row()
    conn = get_connection()
    conn.execute(
        """INSERT INTO Inventory (toolId, location, quantityOnHand, reorderPoint,
           reorderQty, preferredVendor, vendorPartNumber, unitCost, lastCountedAt, notes)
           VALUES (:toolId, :location, :quantityOnHand, :reorderPoint,
           :reorderQty, :preferredVendor, :vendorPartNumber, :unitCost, :lastCountedAt, :notes)
           ON CONFLICT(toolId) DO UPDATE SET
             location=excluded.location, quantityOnHand=excluded.quantityOnHand,
             reorderPoint=excluded.reorderPoint, reorderQty=excluded.reorderQty,
             preferredVendor=excluded.preferredVendor, vendorPartNumber=excluded.vendorPartNumber,
             unitCost=excluded.unitCost, lastCountedAt=excluded.lastCountedAt,
             notes=excluded.notes""",
        row,
    )


def get_inventory(tool_id: str) -> InventoryRecord | None:
    """Fetch inventory record for a tool."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM Inventory WHERE toolId = ?", (tool_id,)).fetchone()
    return InventoryRecord.from_row(row) if row else None


def get_low_stock() -> list[tuple[InventoryRecord, Tool]]:
    """Get all tools where stock is at or below reorder point."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT i.*, t.* FROM Inventory i
           JOIN Tools t ON i.toolId = t.toolId
           WHERE i.quantityOnHand <= i.reorderPoint AND i.reorderPoint > 0
           ORDER BY t.name""",
    ).fetchall()
    results = []
    for row in rows:
        inv = InventoryRecord.from_row(row)
        tool = Tool.from_row(row)
        results.append((inv, tool))
    return results


# ── Import tracking ────────────────────────────────────────────────────

def is_manifest_imported(directory_path: str, content_hash: str) -> bool:
    """Check if a manifest has already been imported with the same content hash."""
    conn = get_connection()
    row = conn.execute(
        "SELECT content_hash FROM _imported_manifests WHERE directory_path = ?",
        (directory_path,),
    ).fetchone()
    if row is None:
        return False
    return row["content_hash"] == content_hash


def record_manifest_import(
    directory_path: str, content_hash: str, tool_count: int, component_count: int
) -> None:
    """Record that a manifest has been successfully imported."""
    from utils.time_helpers import now_iso

    conn = get_connection()
    conn.execute(
        """INSERT INTO _imported_manifests (directory_path, content_hash, imported_at,
           tool_count, component_count)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(directory_path) DO UPDATE SET
             content_hash=excluded.content_hash, imported_at=excluded.imported_at,
             tool_count=excluded.tool_count, component_count=excluded.component_count""",
        (directory_path, content_hash, now_iso(), tool_count, component_count),
    )


# ── Internal helpers ───────────────────────────────────────────────────

def _tool_matches_tokens(tool: Tool, tokens: list[str]) -> bool:
    """Check if a tool matches all search tokens across its searchable fields."""
    searchable = " ".join(filter(None, [
        tool.name,
        tool.manufacturer,
        tool.catalog_number,
        tool.description,
        extract_searchable_text(tool.attributes),
        " ".join(tool.tags),
    ]))
    norm = normalize_for_match(searchable)
    return all(tok in norm for tok in tokens)


def _tool_matches_attributes(tool: Tool, filters: dict[str, str]) -> bool:
    """Check if a tool's attributes match all specified filter key/value pairs."""
    for key, value in filters.items():
        tool_val = tool.attributes.get(key, "")
        if not tool_val:
            return False
        if normalize_for_match(value) not in normalize_for_match(tool_val):
            return False
    return True
