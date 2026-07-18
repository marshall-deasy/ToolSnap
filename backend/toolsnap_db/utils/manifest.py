"""
Manifest JSON parser — reads V1, V2, and V3 session manifests.

Mirrors the read path in ManifestV3.kt on the Android side.
All versions are normalized to V3 format (tools + components lists)
before being returned to the caller.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.settings import MANIFEST_FILENAME


def read_manifest(session_dir: Path) -> Optional[dict]:
    """
    Read a manifest.json from a session folder.

    Auto-detects schema version and migrates V1/V2 to V3 format.
    Returns a dict with keys: tools (list), components (list).
    Returns None if the file is missing or unparseable.
    """
    manifest_file = session_dir / MANIFEST_FILENAME
    if not manifest_file.exists():
        return None

    try:
        text = manifest_file.read_text(encoding="utf-8")
        data = json.loads(text)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[manifest] Failed to read {manifest_file}: {e}")
        return None

    try:
        version = _detect_version(data)
        if version == 3:
            return _read_v3(data)
        elif version == 2:
            return _migrate_v2(data)
        else:
            return _migrate_v1(data)
    except Exception as e:
        print(f"[manifest] Failed to parse {manifest_file}: {e}")
        return None


def _detect_version(data: dict) -> int:
    """Detect manifest schema version."""
    sv = data.get("schemaVersion")
    if sv == 3:
        return 3
    if sv is not None:
        return 2
    return 1


# ------------------------------------------------------------------
# V3 reader (current format)
# ------------------------------------------------------------------

def _read_v3(data: dict) -> dict:
    """Parse a V3 manifest — already in the target format."""
    tools = []
    for t in data.get("tools", []):
        tools.append({
            "toolId": t.get("toolId", str(uuid.uuid4())),
            "name": t.get("name", ""),
            "category": t.get("category", "OTHER"),
            "type": t.get("type", "standalone"),
            "status": t.get("status", "CAPTURED"),
            "manufacturer": t.get("manufacturer"),
            "catalogNumber": t.get("catalogNumber"),
            "description": t.get("description"),
            "unitSystem": t.get("unitSystem", "IMPERIAL"),
            "attributes": t.get("attributes", {}),
            "photos": t.get("photos", []),
            "tags": t.get("tags", []),
            "notes": t.get("notes"),
            "createdAt": t.get("createdAt", _now_iso()),
            "modifiedAt": t.get("modifiedAt", _now_iso()),
        })

    components = []
    for c in data.get("components", []):
        components.append({
            "parentToolId": c["parentToolId"],
            "childToolId": c["childToolId"],
            "role": c.get("role", "OTHER"),
            "quantity": c.get("quantity", 1),
            "notes": c.get("notes"),
        })

    return {"tools": tools, "components": components}


# ------------------------------------------------------------------
# V2 → V3 migration
# ------------------------------------------------------------------

_V2_ASSEMBLY_TYPE_MAP = {
    "END_MILL": "END_MILL",
    "INDEXABLE_MILL": "INDEXABLE_MILL_BODY",
    "DRILL_SOLID": "DRILL",
    "DRILL_INDEXABLE": "INDEXABLE_DRILL_BODY",
    "BORING_BAR": "BORING_BAR_BODY",
    "TURNING_TOOL": "TURNING_HOLDER",
    "THREADING_TOOL": "THREADING_HOLDER",
    "GROOVING_PARTING": "GROOVING_HOLDER",
    "TAP": "TAP",
    "REAMER": "REAMER",
    "HOLDER_ONLY": "HOLDER",
}

_V2_COMP_TYPE_TO_CATEGORY = {
    "BODY": "OTHER",
    "INSERT": "INSERT",
    "HARDWARE": "SCREW",
    "ACCESSORY": "HOLDER",
}

_V2_COMP_TYPE_TO_ROLE = {
    "INSERT": "INSERT",
    "HARDWARE": "SCREW",
    "ACCESSORY": "ADAPTER",
}


def _migrate_v2(data: dict) -> dict:
    """Migrate a V2 assembly manifest to V3 format."""
    tools = []
    components = []

    parent_category = _V2_ASSEMBLY_TYPE_MAP.get(
        data.get("assemblyType", ""), "OTHER"
    )
    parent_id = data.get("assemblyId", str(uuid.uuid4()))
    comps = data.get("components", [])
    is_assembly = len(comps) > 1

    # Parent tool
    parent = {
        "toolId": parent_id,
        "name": data.get("assemblyName", ""),
        "category": parent_category,
        "type": "assembly" if is_assembly else "standalone",
        "status": "CAPTURED" if data.get("isComplete") else "PARTIAL",
        "manufacturer": None,
        "catalogNumber": None,
        "description": None,
        "unitSystem": "IMPERIAL",
        "attributes": {},
        "photos": data.get("assemblyPhotos", []),
        "tags": data.get("tags", []),
        "notes": data.get("notes"),
        "createdAt": data.get("createdAt", _now_iso()),
        "modifiedAt": data.get("modifiedAt", _now_iso()),
    }
    tools.append(parent)

    # Child components
    for cm in comps:
        comp_type = cm.get("componentType", "OTHER")
        child_category = _V2_COMP_TYPE_TO_CATEGORY.get(comp_type, "OTHER")
        child_id = cm.get("componentId", str(uuid.uuid4()))

        child = {
            "toolId": child_id,
            "name": (cm.get("description")
                     or cm.get("catalogNumber")
                     or child_category),
            "category": child_category,
            "type": "standalone",
            "status": cm.get("status", "CAPTURED"),
            "manufacturer": cm.get("manufacturer"),
            "catalogNumber": cm.get("catalogNumber"),
            "description": cm.get("description"),
            "unitSystem": cm.get("unitSystem", "IMPERIAL"),
            "attributes": cm.get("attributes", {}),
            "photos": [cm["photoFile"]] if cm.get("photoFile") else [],
            "tags": [],
            "notes": cm.get("notes"),
            "createdAt": data.get("createdAt", _now_iso()),
            "modifiedAt": data.get("modifiedAt", _now_iso()),
        }
        tools.append(child)

        role = _V2_COMP_TYPE_TO_ROLE.get(comp_type, "OTHER")
        components.append({
            "parentToolId": parent_id,
            "childToolId": child_id,
            "role": role,
            "quantity": 1,
            "notes": None,
        })

    return {"tools": tools, "components": components}


# ------------------------------------------------------------------
# V1 → V3 migration
# ------------------------------------------------------------------

def _migrate_v1(data: dict) -> dict:
    """Migrate a V1 flat-field manifest to V3 format."""
    tools = []
    components = []

    parent_id = data.get("sessionId", str(uuid.uuid4()))
    created = data.get("createdAt", _now_iso())

    parent = {
        "toolId": parent_id,
        "name": data.get("toolName", "Unknown Tool (V1)"),
        "category": "OTHER",
        "type": "standalone",
        "status": "CAPTURED" if data.get("isComplete") else "PARTIAL",
        "manufacturer": None,
        "catalogNumber": None,
        "description": None,
        "unitSystem": "IMPERIAL",
        "attributes": {},
        "photos": [],
        "tags": [],
        "notes": None,
        "createdAt": created,
        "modifiedAt": created,
    }

    fields = data.get("fields", {})

    # Extract tool_data form values into parent attributes
    tool_data = fields.get("tool_data", {})
    fd = tool_data.get("formData")
    if fd and isinstance(fd, dict):
        values = fd.get("values", {})
        parent["description"] = values.pop("description", None)
        parent["manufacturer"] = values.pop("manufacturer", None)
        parent["catalogNumber"] = values.pop("catalog_number", None)
        parent["attributes"] = values

    # Body photo
    body_field = fields.get("body", {})
    if body_field.get("imageFile"):
        parent["photos"].append(body_field["imageFile"])

    parent["status"] = "CAPTURED" if data.get("isComplete") else "PARTIAL"
    parent["type"] = "assembly"  # V1 sessions were always assemblies
    tools.append(parent)

    # Insert → standalone tool + link
    insert_field = fields.get("insert", {})
    if insert_field.get("status", "PENDING") != "PENDING":
        insert_id = str(uuid.uuid4())
        insert_tool = {
            "toolId": insert_id,
            "name": "Insert (migrated from V1)",
            "category": "INSERT",
            "type": "standalone",
            "status": insert_field.get("status", "CAPTURED"),
            "manufacturer": None,
            "catalogNumber": None,
            "description": None,
            "unitSystem": "IMPERIAL",
            "attributes": {},
            "photos": ([insert_field["imageFile"]]
                       if insert_field.get("imageFile") else []),
            "tags": [],
            "notes": None,
            "createdAt": created,
            "modifiedAt": created,
        }
        tools.append(insert_tool)
        components.append({
            "parentToolId": parent_id,
            "childToolId": insert_id,
            "role": "INSERT",
            "quantity": 1,
            "notes": None,
        })

    # Hardware → standalone tool + link
    hw_field = fields.get("hardware", {})
    if hw_field.get("status", "PENDING") != "PENDING":
        hw_id = str(uuid.uuid4())
        hw_tool = {
            "toolId": hw_id,
            "name": "Hardware (migrated from V1)",
            "category": "OTHER",
            "type": "standalone",
            "status": hw_field.get("status", "CAPTURED"),
            "manufacturer": None,
            "catalogNumber": None,
            "description": None,
            "unitSystem": "IMPERIAL",
            "attributes": {},
            "photos": ([hw_field["imageFile"]]
                       if hw_field.get("imageFile") else []),
            "tags": [],
            "notes": None,
            "createdAt": created,
            "modifiedAt": created,
        }
        tools.append(hw_tool)
        components.append({
            "parentToolId": parent_id,
            "childToolId": hw_id,
            "role": "OTHER",
            "quantity": 1,
            "notes": None,
        })

    return {"tools": tools, "components": components}


def _now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()
