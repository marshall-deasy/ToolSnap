# ToolSnap

**Android tooling capture app + Windows Python database & sync system** for machine shop inventory management.

## Overview
- **Android App** (`toolsnap/`) — Captures photos, manufacturer, part numbers, QR codes, and tooling data on the shop floor.
- **PC Database** (`toolsnap_db/`) — Full desktop application with inventory, BOM, compatibility, importers, QR generation, and UI panels.
- **Integration** — ADB sync, watchers, FolderSync, and DropRouterHud for reliable data transfer from tablet to PC.

## Project Structure
- `toolsnap/` — Android Gradle project
- `toolsnap_db/` — Python backend + Tkinter UI
- `tools/` — Supporting tools (DropRouterHud, MapStructure, LogViewer, etc.)
- `docs/` — Engineering rules, documentation standards, architecture, and sync guides

## Setup & Run
See `docs/setup_toolsnap_structure.ps1` and individual run scripts.

## Development
Follows custom **Governance Stack** (PromptClip for context, DropRouter for atomic deliveries, engineering rules, validators, and low-drift practices).

## Related Documents
- [Architecture](ToolSnap_Architecture.md)
- [Data Model](TOOLSNAP_DATA_MODEL.md)
- [Sync Guide](TOOLSNAP_SYNC_GUIDE.md)