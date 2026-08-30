"""Manifest importer — scans directory, detects version, migrates, deduplicates, ingests."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.models import Tool, Component
from core.enums import ToolCategory
from core.database import transaction
from core import repo
from core.dedup import find_duplicate
from core.compatibility import derive_from_components
from utils.time_helpers import now_iso, is_newer


@dataclass
class ImportResult:
    """Result summary for a single manifest import."""
    directory: str = ""
    version: int = 0
    tools_added: int = 0
    tools_updated: int = 0
    tools_deduplicated: int = 0
    components_added: int = 0
    compatibility_derived: int = 0
    skipped: bool = False
    error: Optional[str] = None


@dataclass
class ScanResult:
    """Result summary for a full directory scan."""
    directories_scanned: int = 0
    manifests_found: int = 0
    imports: list[ImportResult] = field(default_factory=list)

    @property
    def total_tools_added(self) -> int:
        return sum(r.tools_added for r in self.imports)

    @property
    def total_tools_updated(self) -> int:
        return sum(r.tools_updated for r in self.imports)

    @property
    def total_errors(self) -> int:
        return sum(1 for r in self.imports if r.error)


def scan_and_import(import_dir: Path) -> ScanResult:
    """Scan the import directory and ingest all new/changed manifests.

    Each subdirectory is checked for a manifest.json. Already-imported
    manifests (same content hash) are skipped.
    """
    result = ScanResult()

    if not import_dir.is_dir():
        return result

    subdirs = sorted(p for p in import_dir.iterdir() if p.is_dir())
    result.directories_scanned = len(subdirs)

    for subdir in subdirs:
        manifest_path = subdir / "manifest.json"
        if not manifest_path.is_file():
            continue

        result.manifests_found += 1
        import_result = _import_manifest(manifest_path, subdir)
        result.imports.append(import_result)

    return result


def _import_manifest(manifest_path: Path, session_dir: Path) -> ImportResult:
    """Import a single manifest file."""
    result = ImportResult(directory=str(session_dir))

    try:
        raw = manifest_path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Skip if already imported with same content
        if repo.is_manifest_imported(str(session_dir), content_hash):
            result.skipped = True
            return result

        data = json.loads(raw)
        version = _detect_version(data)
        result.version = version

        # Migrate to V3 format in memory
        if version == 1:
            v3_data = _migrate_v1(data, session_dir)
        else:
            v3_data = data

        tools_list = v3_data.get("tools", [])
        components_list = v3_data.get("components", [])

        # Build id remap table for deduplication
        id_remap: dict[str, str] = {}

        with transaction():
            # Process tools
            for tool_dict in tools_list:
                tool = Tool.from_manifest_dict(tool_dict)
                # Prefix photo paths with session directory
                tool.photos = [
                    str(session_dir / p) if not Path(p).is_absolute() else p
                    for p in tool.photos
                ]

                # Fix broken photo paths — if manifest names don't match
                # actual files on disk, scan the session dir for real images
                valid_photos = [p for p in tool.photos if Path(p).is_file()]
                if tool.photos and not valid_photos:
                    # Manifest had photo entries but none exist on disk
                    # Scan session dir for actual image files
                    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
                    actual_images = sorted(
                        str(f) for f in session_dir.iterdir()
                        if f.is_file() and f.suffix.lower() in image_exts
                    )
                    if actual_images:
                        tool.photos = actual_images
                elif valid_photos != tool.photos:
                    # Keep only the ones that exist
                    tool.photos = valid_photos

                existing_id = find_duplicate(tool)
                if existing_id:
                    id_remap[tool.tool_id] = existing_id
                    result.tools_deduplicated += 1
                    # Update existing if incoming is newer
                    existing_tool = repo.get_tool(existing_id)
                    if existing_tool and is_newer(tool.modified_at, existing_tool.modified_at):
                        tool.tool_id = existing_id
                        repo.upsert_tool(tool)
                        result.tools_updated += 1
                else:
                    repo.upsert_tool(tool)
                    result.tools_added += 1

            # Process components (remap IDs for deduplicated tools)
            for comp_dict in components_list:
                comp = Component.from_manifest_dict(comp_dict)
                comp.parent_tool_id = id_remap.get(comp.parent_tool_id, comp.parent_tool_id)
                comp.child_tool_id = id_remap.get(comp.child_tool_id, comp.child_tool_id)
                repo.upsert_component(comp)
                result.components_added += 1

            # Derive compatibility
            result.compatibility_derived = derive_from_components()

            # Record successful import
            repo.record_manifest_import(
                str(session_dir), content_hash,
                len(tools_list), len(components_list),
            )

    except Exception as e:
        result.error = str(e)

    return result


def _detect_version(data: dict) -> int:
    """Auto-detect manifest schema version."""
    sv = data.get("schemaVersion")
    if sv is None:
        return 1
    return int(sv)


def _migrate_v1(data: dict, session_dir: Path) -> dict:
    """Migrate V1 manifest to V3 format.

    V1 is the Android app's native session manifest:
    {
      "sessionId": "...",
      "toolName": "...",
      "fields": {
        "body":      { "status": "CAPTURED", "imageFile": "body.jpg", ... },
        "insert":    { "status": "CAPTURED", "imageFile": "insert.jpg", ... },
        "hardware":  { "status": "SKIPPED", ... },
        "tool_data": { "status": "CAPTURED", "imageFile": "tool_data.jpg",
                       "formData": { "entryMethod": "manual", "values": {...} } }
      }
    }

    Strategy: build a single tool from the form data + all captured photos.
    Category and attributes come from tool_data.formData.values.
    """
    tools = []
    components = []
    ts = now_iso()

    fields = data.get("fields", {})
    tool_name = data.get("toolName", f"V1 Import — {session_dir.name}")

    # Extract form data from tool_data field
    tool_data_field = fields.get("tool_data", {})
    form_data = tool_data_field.get("formData", {})
    form_values = form_data.get("values", {}) if isinstance(form_data, dict) else {}

    # Also check body field for category stash
    body_field = fields.get("body", {})
    body_form = body_field.get("formData", {})
    body_values = body_form.get("values", {}) if isinstance(body_form, dict) else {}

    # Determine category
    raw_category = (
        form_values.get("tool_category")
        or body_values.get("tool_category")
        or "OTHER"
    )
    # Validate category exists in our enum
    try:
        ToolCategory(raw_category)
        category = raw_category
    except ValueError:
        category = "OTHER"

    is_assembly = category in {c.value for c in ToolCategory
                               if c in (ToolCategory.INDEXABLE_MILL_BODY,
                                        ToolCategory.INDEXABLE_DRILL_BODY,
                                        ToolCategory.BORING_BAR_BODY,
                                        ToolCategory.TURNING_HOLDER,
                                        ToolCategory.THREADING_HOLDER,
                                        ToolCategory.GROOVING_HOLDER)}

    # Collect all photos from captured fields (scan all fields, not just known ones)
    photos = []
    for field_key, field_data in fields.items():
        if not isinstance(field_data, dict):
            continue
        status = field_data.get("status", "PENDING")
        image_file = field_data.get("imageFile")
        if status in ("CAPTURED", "OCR_CONFIRMED") and image_file:
            photos.append(image_file)

    # Build attributes from form values (exclude meta keys)
    meta_keys = {"name", "manufacturer", "catalogNumber", "catalog_number",
                 "description", "unitSystem", "tool_category", "notes"}
    attributes = {k: str(v) for k, v in form_values.items() if k not in meta_keys}

    # Merge body form values (category stash, extra attrs)
    for k, v in body_values.items():
        if k not in meta_keys and k not in attributes:
            attributes[k] = str(v)

    tool_id = data.get("sessionId", str(uuid.uuid4()))

    tool = {
        "toolId": tool_id,
        "name": tool_name,
        "category": category,
        "type": "assembly" if is_assembly else "standalone",
        "status": "CAPTURED",
        "manufacturer": form_values.get("manufacturer"),
        "catalogNumber": form_values.get("catalogNumber") or form_values.get("catalog_number"),
        "description": form_values.get("description"),
        "unitSystem": form_values.get("unitSystem", "IMPERIAL"),
        "attributes": attributes,
        "photos": photos,
        "tags": [],
        "notes": form_values.get("notes"),
        "createdAt": data.get("createdAt", ts),
        "modifiedAt": ts,
    }

    tools.append(tool)

    return {"schemaVersion": 3, "exportedAt": ts, "tools": tools, "components": components}
