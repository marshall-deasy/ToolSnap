"""Data models — plain dataclasses, no DB or UI coupling."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from core.enums import ToolCategory, ComponentRole, UnitSystem


@dataclass
class Tool:
    tool_id: str
    name: str
    category: ToolCategory
    tool_type: str  # "assembly" | "standalone"
    manufacturer: Optional[str] = None
    catalog_number: Optional[str] = None
    description: Optional[str] = None
    unit_system: Optional[UnitSystem] = None
    attributes: dict[str, str] = field(default_factory=dict)
    notes: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    photos: list[str] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""

    # --- Serialization helpers (DB row ↔ dataclass) ---

    def to_row(self) -> dict:
        """Convert to a dict matching the Tools table columns."""
        return {
            "toolId": self.tool_id,
            "name": self.name,
            "category": self.category.value if isinstance(self.category, ToolCategory) else self.category,
            "type": self.tool_type,
            "manufacturer": self.manufacturer,
            "catalogNumber": self.catalog_number,
            "description": self.description,
            "unitSystem": self.unit_system.value if isinstance(self.unit_system, UnitSystem) else self.unit_system,
            "attributes": json.dumps(self.attributes) if self.attributes else "{}",
            "notes": self.notes,
            "tags": json.dumps(self.tags) if self.tags else "[]",
            "photos": json.dumps(self.photos) if self.photos else "[]",
            "createdAt": self.created_at,
            "modifiedAt": self.modified_at,
        }

    @classmethod
    def from_row(cls, row) -> Tool:
        """Construct from a DB row (dict or sqlite3.Row)."""
        if not isinstance(row, dict):
            row = dict(row)
        return cls(
            tool_id=row["toolId"],
            name=row["name"],
            category=ToolCategory(row["category"]),
            tool_type=row["type"],
            manufacturer=row.get("manufacturer"),
            catalog_number=row.get("catalogNumber"),
            description=row.get("description"),
            unit_system=UnitSystem(row["unitSystem"]) if row.get("unitSystem") else None,
            attributes=json.loads(row.get("attributes") or "{}"),
            notes=row.get("notes"),
            tags=json.loads(row.get("tags") or "[]"),
            photos=json.loads(row.get("photos") or "[]"),
            created_at=row.get("createdAt", ""),
            modified_at=row.get("modifiedAt", ""),
        )

    @classmethod
    def from_manifest_dict(cls, d: dict) -> Tool:
        """Construct from a V3 manifest tool dict."""
        cat = ToolCategory(d["category"])
        us = UnitSystem(d["unitSystem"]) if d.get("unitSystem") else None
        return cls(
            tool_id=d["toolId"],
            name=d["name"],
            category=cat,
            tool_type=d.get("type", "standalone"),
            manufacturer=d.get("manufacturer"),
            catalog_number=d.get("catalogNumber"),
            description=d.get("description"),
            unit_system=us,
            attributes=d.get("attributes") or {},
            notes=d.get("notes"),
            tags=d.get("tags") or [],
            photos=d.get("photos") or [],
            created_at=d.get("createdAt", ""),
            modified_at=d.get("modifiedAt", ""),
        )


@dataclass
class Component:
    parent_tool_id: str
    child_tool_id: str
    role: ComponentRole
    quantity: int = 1
    notes: Optional[str] = None

    def to_row(self) -> dict:
        return {
            "parentToolId": self.parent_tool_id,
            "childToolId": self.child_tool_id,
            "role": self.role.value if isinstance(self.role, ComponentRole) else self.role,
            "quantity": self.quantity,
            "notes": self.notes,
        }

    @classmethod
    def from_row(cls, row) -> Component:
        if not isinstance(row, dict):
            row = dict(row)
        return cls(
            parent_tool_id=row["parentToolId"],
            child_tool_id=row["childToolId"],
            role=ComponentRole(row["role"]),
            quantity=row.get("quantity", 1),
            notes=row.get("notes"),
        )

    @classmethod
    def from_manifest_dict(cls, d: dict) -> Component:
        return cls(
            parent_tool_id=d["parentToolId"],
            child_tool_id=d["childToolId"],
            role=ComponentRole(d["role"]),
            quantity=d.get("quantity", 1),
            notes=d.get("notes"),
        )


@dataclass
class CompatibilityLink:
    body_tool_id: str
    insert_tool_id: str
    fit_notes: Optional[str] = None

    def to_row(self) -> dict:
        return {
            "bodyToolId": self.body_tool_id,
            "insertToolId": self.insert_tool_id,
            "fitNotes": self.fit_notes,
        }

    @classmethod
    def from_row(cls, row) -> CompatibilityLink:
        if not isinstance(row, dict):
            row = dict(row)
        return cls(
            body_tool_id=row["bodyToolId"],
            insert_tool_id=row["insertToolId"],
            fit_notes=row.get("fitNotes"),
        )


@dataclass
class InventoryRecord:
    tool_id: str
    location: Optional[str] = None
    quantity_on_hand: int = 0
    reorder_point: int = 0
    reorder_qty: int = 0
    preferred_vendor: Optional[str] = None
    vendor_part_number: Optional[str] = None
    unit_cost: Optional[float] = None
    last_counted_at: Optional[str] = None
    notes: Optional[str] = None

    def to_row(self) -> dict:
        return {
            "toolId": self.tool_id,
            "location": self.location,
            "quantityOnHand": self.quantity_on_hand,
            "reorderPoint": self.reorder_point,
            "reorderQty": self.reorder_qty,
            "preferredVendor": self.preferred_vendor,
            "vendorPartNumber": self.vendor_part_number,
            "unitCost": self.unit_cost,
            "lastCountedAt": self.last_counted_at,
            "notes": self.notes,
        }

    @classmethod
    def from_row(cls, row) -> InventoryRecord:
        if not isinstance(row, dict):
            row = dict(row)
        return cls(
            tool_id=row["toolId"],
            location=row.get("location"),
            quantity_on_hand=row.get("quantityOnHand", 0),
            reorder_point=row.get("reorderPoint", 0),
            reorder_qty=row.get("reorderQty", 0),
            preferred_vendor=row.get("preferredVendor"),
            vendor_part_number=row.get("vendorPartNumber"),
            unit_cost=row.get("unitCost"),
            last_counted_at=row.get("lastCountedAt"),
            notes=row.get("notes"),
        )
