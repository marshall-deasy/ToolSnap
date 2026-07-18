# ToolSnap

Android app for capturing machine shop tooling data (photos, manufacturer, part numbers, etc.) + Windows Python desktop database with import/sync capabilities.

## Overview
- **Android App** (`toolsnap/`) — Field data capture on the shop floor.
- **PC Database** (`toolsnap_db/`) — Tkinter UI, SQLite backend, BOM, inventory, QR, compatibility checks, importers.
- **Sync Tools** — ADB, watchers, FolderSync, DropRouter integration for seamless transfer.

Part of a larger ToolSnap ecosystem with supporting utilities (DropRouterHud, MapStructure, etc.).

## Structure
- `android/` → Planned (current: `toolsnap/`)
- `backend/` → Planned (current: `toolsnap_db/`)
- `tools/` or `archive/` — Supporting desktop tools
- `docs/` — Engineering rules, documentation standards, architecture

## Setup
1. Clone the repo
2. Run setup scripts (see `docs/setup_toolsnap_structure.ps1`)
3. Android: Open in Android Studio
4. Backend: `cd toolsnap_db && pip install -r requirements.txt && python main.py`

## Governance
Follows custom engineering rules + governance stack (PromptClip context management, DropRouter atomic deliveries).

## Related
- [Architecture](docs/ToolSnap_Architecture.md)
- [Data Model](TOOLSNAP_DATA_MODEL.md)