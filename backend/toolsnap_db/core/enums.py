"""Enums and category metadata — single source of truth for all category/role definitions."""

from enum import Enum


class ToolCategory(str, Enum):
    # Solid tools (standalone)
    END_MILL = "END_MILL"
    DRILL = "DRILL"
    TAP = "TAP"
    REAMER = "REAMER"
    # Indexable bodies (assemblies)
    INDEXABLE_MILL_BODY = "INDEXABLE_MILL_BODY"
    INDEXABLE_DRILL_BODY = "INDEXABLE_DRILL_BODY"
    BORING_BAR_BODY = "BORING_BAR_BODY"
    TURNING_HOLDER = "TURNING_HOLDER"
    THREADING_HOLDER = "THREADING_HOLDER"
    GROOVING_HOLDER = "GROOVING_HOLDER"
    # Consumables / hardware
    INSERT = "INSERT"
    SCREW = "SCREW"
    SHIM = "SHIM"
    CLAMP = "CLAMP"
    WEDGE = "WEDGE"
    # Holders / adapters
    HOLDER = "HOLDER"
    COLLET = "COLLET"
    RETENTION_KNOB = "RETENTION_KNOB"
    # Catch-all
    OTHER = "OTHER"


class ComponentRole(str, Enum):
    INSERT = "INSERT"
    WIPER_INSERT = "WIPER_INSERT"
    SCREW = "SCREW"
    SHIM = "SHIM"
    CLAMP = "CLAMP"
    WEDGE = "WEDGE"
    COOLANT_PLUG = "COOLANT_PLUG"
    COLLET = "COLLET"
    ADAPTER = "ADAPTER"
    OTHER = "OTHER"


class UnitSystem(str, Enum):
    IMPERIAL = "IMPERIAL"
    METRIC = "METRIC"


# Categories that represent indexable bodies (parents that take inserts)
INDEXABLE_BODY_CATEGORIES = frozenset({
    ToolCategory.INDEXABLE_MILL_BODY,
    ToolCategory.INDEXABLE_DRILL_BODY,
    ToolCategory.BORING_BAR_BODY,
    ToolCategory.TURNING_HOLDER,
    ToolCategory.THREADING_HOLDER,
    ToolCategory.GROOVING_HOLDER,
})

# Roles that represent insert-type components (for compatibility derivation)
INSERT_ROLES = frozenset({
    ComponentRole.INSERT,
    ComponentRole.WIPER_INSERT,
})

# Expected attribute keys per category (order = display order in UI)
CATEGORY_ATTRIBUTES: dict[ToolCategory, list[str]] = {
    ToolCategory.END_MILL: [
        "cutting_diameter", "shank_diameter", "flutes", "flute_length",
        "helix_angle", "coating", "material", "overall_length", "coolant_through",
    ],
    ToolCategory.DRILL: [
        "cutting_diameter", "shank_diameter", "flutes", "flute_length",
        "point_angle", "coating", "material", "coolant_through", "overall_length",
    ],
    ToolCategory.TAP: [
        "cutting_diameter", "thread_pitch", "thread_form", "flutes",
        "coating", "material", "overall_length", "coolant_through",
    ],
    ToolCategory.REAMER: [
        "cutting_diameter", "shank_diameter", "flutes", "flute_length",
        "coating", "material", "overall_length", "coolant_through",
    ],
    ToolCategory.INDEXABLE_MILL_BODY: [
        "cutting_diameter", "pocket_size", "shank_type", "coolant_through", "overall_length",
    ],
    ToolCategory.INDEXABLE_DRILL_BODY: [
        "cutting_diameter", "shank_type", "pocket_size", "coolant_through", "overall_length",
    ],
    ToolCategory.BORING_BAR_BODY: [
        "shank_type", "shank_diameter", "projection", "pocket_size",
        "coolant_through", "overall_length",
    ],
    ToolCategory.TURNING_HOLDER: [
        "shank_type", "shank_size", "projection", "pocket_size", "hand",
    ],
    ToolCategory.THREADING_HOLDER: [
        "shank_type", "shank_size", "thread_type", "pocket_size", "hand",
    ],
    ToolCategory.GROOVING_HOLDER: [
        "shank_type", "shank_size", "groove_width", "max_depth", "hand",
    ],
    ToolCategory.INSERT: [
        "iso_designation", "insert_shape", "insert_size", "thickness",
        "nose_radius", "grade", "workpiece_material", "coating",
        "chipbreaker", "hand", "rake",
    ],
    ToolCategory.SCREW: ["size", "drive_type", "torque_spec"],
    ToolCategory.SHIM: ["shim_type", "pocket_size"],
    ToolCategory.CLAMP: ["clamp_type", "size"],
    ToolCategory.WEDGE: ["wedge_type", "size"],
    ToolCategory.HOLDER: [
        "shank_type", "bore_size", "gauge_length", "overall_length", "coolant_through",
    ],
    ToolCategory.COLLET: ["collet_system", "bore_size"],
    ToolCategory.RETENTION_KNOB: ["shank_type", "thread_size"],
    ToolCategory.OTHER: [
        "description_custom", "shank_type", "cutting_diameter",
        "coating", "material", "overall_length",
    ],
}


def pretty_category(cat: ToolCategory) -> str:
    """Human-readable category name for UI display."""
    return cat.value.replace("_", " ").title()


def pretty_attribute(key: str) -> str:
    """Human-readable attribute name for UI display."""
    return key.replace("_", " ").title()
