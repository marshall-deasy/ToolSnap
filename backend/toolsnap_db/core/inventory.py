"""Inventory operations — reorder reports, BOM export."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from core import repo
from core.models import InventoryRecord, Tool


@dataclass
class ReorderLine:
    """One line in a reorder report."""
    tool_name: str
    catalog_number: str
    manufacturer: str
    vendor: str
    vendor_part_number: str
    on_hand: int
    reorder_qty: int
    unit_cost: float | None
    line_total: float | None


@dataclass
class ReorderReport:
    """Reorder report grouped by vendor."""
    lines_by_vendor: dict[str, list[ReorderLine]]

    @property
    def total_cost(self) -> float:
        total = 0.0
        for lines in self.lines_by_vendor.values():
            for line in lines:
                if line.line_total is not None:
                    total += line.line_total
        return total

    @property
    def vendor_count(self) -> int:
        return len(self.lines_by_vendor)

    @property
    def line_count(self) -> int:
        return sum(len(lines) for lines in self.lines_by_vendor.values())


def build_reorder_report() -> ReorderReport:
    """Build a reorder report from all low-stock items, grouped by vendor."""
    low_stock = repo.get_low_stock()
    lines_by_vendor: dict[str, list[ReorderLine]] = {}

    for inv, tool in low_stock:
        vendor = inv.preferred_vendor or "No Vendor Assigned"
        line_total = (inv.unit_cost * inv.reorder_qty) if inv.unit_cost else None
        line = ReorderLine(
            tool_name=tool.name,
            catalog_number=tool.catalog_number or "",
            manufacturer=tool.manufacturer or "",
            vendor=vendor,
            vendor_part_number=inv.vendor_part_number or "",
            on_hand=inv.quantity_on_hand,
            reorder_qty=inv.reorder_qty,
            unit_cost=inv.unit_cost,
            line_total=line_total,
        )
        lines_by_vendor.setdefault(vendor, []).append(line)

    # Sort lines within each vendor
    for vendor in lines_by_vendor:
        lines_by_vendor[vendor].sort(key=lambda l: l.tool_name.lower())

    return ReorderReport(lines_by_vendor=lines_by_vendor)


def export_reorder_csv(report: ReorderReport, path: Path) -> None:
    """Write a reorder report to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Vendor", "Tool Name", "Catalog #", "Manufacturer",
            "Vendor Part #", "On Hand", "Order Qty", "Unit Cost", "Line Total",
        ])
        for vendor, lines in sorted(report.lines_by_vendor.items()):
            for line in lines:
                writer.writerow([
                    line.vendor, line.tool_name, line.catalog_number,
                    line.manufacturer, line.vendor_part_number,
                    line.on_hand, line.reorder_qty,
                    f"{line.unit_cost:.2f}" if line.unit_cost else "",
                    f"{line.line_total:.2f}" if line.line_total else "",
                ])


def build_assembly_bom(parent_tool_id: str) -> list[dict]:
    """Build a bill of materials for an assembly — all child tools with inventory info."""
    children = repo.get_children(parent_tool_id)
    bom = []
    for comp, tool in children:
        inv = repo.get_inventory(tool.tool_id)
        bom.append({
            "role": comp.role.value if hasattr(comp.role, "value") else comp.role,
            "quantity_needed": comp.quantity,
            "tool_name": tool.name,
            "catalog_number": tool.catalog_number or "",
            "manufacturer": tool.manufacturer or "",
            "on_hand": inv.quantity_on_hand if inv else 0,
            "vendor": inv.preferred_vendor or "" if inv else "",
            "vendor_part_number": inv.vendor_part_number or "" if inv else "",
            "unit_cost": inv.unit_cost if inv else None,
        })
    return bom


def export_bom_csv(parent_tool_id: str, path: Path) -> None:
    """Export an assembly's BOM to CSV."""
    parent = repo.get_tool(parent_tool_id)
    bom = build_assembly_bom(parent_tool_id)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if parent:
            writer.writerow([f"BOM for: {parent.name}"])
            writer.writerow([])
        writer.writerow([
            "Role", "Qty Needed", "Tool Name", "Catalog #", "Manufacturer",
            "On Hand", "Vendor", "Vendor Part #", "Unit Cost",
        ])
        for item in bom:
            writer.writerow([
                item["role"], item["quantity_needed"], item["tool_name"],
                item["catalog_number"], item["manufacturer"],
                item["on_hand"], item["vendor"], item["vendor_part_number"],
                f"{item['unit_cost']:.2f}" if item["unit_cost"] else "",
            ])
