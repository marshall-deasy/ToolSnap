"""BOM builder — flattens tools and assemblies into an orderable parts list.

Given a list of (tool_id, quantity) pairs, this module:
1. Expands assemblies into their component parts (recursive)
2. Multiplies quantities through the tree
3. Merges duplicate parts by tool_id
4. Returns a flat BOM ready for export
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core import repo
from core.models import Tool
from core.enums import pretty_category


@dataclass
class BomLine:
    """One line in a Bill of Materials."""
    tool_id: str
    name: str
    category: str
    manufacturer: str
    catalog_number: str
    quantity: int
    attributes: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    @property
    def sort_key(self) -> tuple:
        return (self.category, self.manufacturer or "", self.name)


def build_bom(selections: list[tuple[str, int]]) -> list[BomLine]:
    """Build a flat BOM from a list of (tool_id, quantity) selections.

    Assemblies are exploded: if a boring bar has 1 insert + 1 screw,
    ordering qty 2 of the boring bar yields 2 inserts + 2 screws
    (plus the 2 bodies themselves).
    """
    # Accumulate quantities by tool_id
    qty_map: dict[str, int] = {}
    tool_cache: dict[str, Tool] = {}

    for tool_id, qty in selections:
        _explode(tool_id, qty, qty_map, tool_cache)

    # Build BOM lines
    lines: list[BomLine] = []
    for tid, total_qty in qty_map.items():
        tool = tool_cache.get(tid) or repo.get_tool(tid)
        if not tool:
            continue
        lines.append(BomLine(
            tool_id=tid,
            name=tool.name,
            category=pretty_category(tool.category),
            manufacturer=tool.manufacturer or "",
            catalog_number=tool.catalog_number or "",
            quantity=total_qty,
            attributes=dict(tool.attributes),
            notes=tool.notes or "",
        ))

    lines.sort(key=lambda ln: ln.sort_key)
    return lines


def _explode(
    tool_id: str,
    qty: int,
    qty_map: dict[str, int],
    tool_cache: dict[str, Tool],
) -> None:
    """Recursively explode a tool into its components."""
    tool = repo.get_tool(tool_id)
    if not tool:
        return
    tool_cache[tool_id] = tool

    # Add the tool itself
    qty_map[tool_id] = qty_map.get(tool_id, 0) + qty

    # Explode children
    children = repo.get_children(tool_id)
    for comp, child_tool in children:
        child_qty = qty * comp.quantity
        tool_cache[child_tool.tool_id] = child_tool
        _explode(child_tool.tool_id, child_qty, qty_map, tool_cache)


def bom_to_text(lines: list[BomLine], title: str = "ToolSnap BOM") -> str:
    """Format BOM as plain text for clipboard / email paste."""
    if not lines:
        return "No items in BOM."

    parts: list[str] = [title, "=" * len(title), ""]

    # Column widths
    w_qty = 4
    w_name = max(len(ln.name) for ln in lines)
    w_cat = max(len(ln.catalog_number) for ln in lines) if any(ln.catalog_number for ln in lines) else 0
    w_mfg = max(len(ln.manufacturer) for ln in lines) if any(ln.manufacturer for ln in lines) else 0

    # Header
    header = f"{'Qty':<{w_qty}}  {'Name':<{w_name}}"
    if w_mfg:
        header += f"  {'Manufacturer':<{w_mfg}}"
    if w_cat:
        header += f"  {'Catalog #':<{w_cat}}"
    parts.append(header)
    parts.append("-" * len(header))

    # Rows
    for ln in lines:
        row = f"{ln.quantity:<{w_qty}}  {ln.name:<{w_name}}"
        if w_mfg:
            row += f"  {ln.manufacturer:<{w_mfg}}"
        if w_cat:
            row += f"  {ln.catalog_number:<{w_cat}}"
        parts.append(row)

    parts.append("")
    parts.append(f"Total line items: {len(lines)}")
    parts.append(f"Total pieces: {sum(ln.quantity for ln in lines)}")

    return "\n".join(parts)
