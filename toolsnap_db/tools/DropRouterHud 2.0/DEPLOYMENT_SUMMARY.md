# DropRouterHud Deployment Summary

## What's New

Complete transformation from "Universal Folder Watcher" to **DropRouterHud** - a cleaner, more focused file routing system.

### Major Changes

**1. Simplified HUD (hud_overlay.py)**
- **Before**: Multi-line display with background, borders, project name, folder name, status updates, minimize/expand
- **After**: Single-line floating text only: `DL → TrailBoss (47)`
- Font: **Consolas Bold 14** - monospaced, clean digital aesthetic
- No background, no border - just green floating text
- Positioned 5px from top, 5px from right
- Instances stack vertically with 5px line spacing
- Right-click menu: Info, Quit (removed pause, minimize options)

**2. Enhanced Tree Dialog (dialogs.py)**
- Added visual indicators:
  - ✓ (green checkmark) for files with known destinations
  - ⚠️ (yellow triangle) for flagged files going to Downloads
- Shows project root folder: `ProjectName (ROOT)`
- Full tree display from root level
- Cleaner, more readable layout

**3. Renamed & Reorganized**
- `project_watcher.py` → `droprouterhud.py`
- `watcher_hud.py` → `hud_overlay.py`
- `watcher_dialogs.py` → `dialogs.py`
- `watcher_config.json` → `config.json`
- `instance_manager.py` → updated with DropRouterHud naming
- Lock files: `~/.droprouterhud_locks/` instead of `~/.folder_watcher_locks/`

**4. Self-Contained Structure**
- Lives in: `tools/DropRouterHud/` subdirectory
- Config uses relative path: `"project_root": "../.."`
- Ignore list: `tools/droprouter_ignore.json`
- All imports updated for new file names

**5. Simplified HUD Updates**
- Removed status message signals (was cluttering the code)
- HUD only shows file count updates
- Console still shows detailed status messages

## File Structure

```
trailboss/                          ← Your project root
├── core/
├── utils/
└── tools/
    ├── DropRouterHud/              ← NEW self-contained system
    │   ├── droprouterhud.py        ← Main script (was project_watcher.py)
    │   ├── hud_overlay.py          ← Minimal HUD (was watcher_hud.py)
    │   ├── dialogs.py              ← Tree preview (was watcher_dialogs.py)
    │   ├── instance_manager.py     ← Multi-instance coordination
    │   ├── config.json             ← Config (was watcher_config.json)
    │   ├── requirements.txt
    │   ├── README.md               ← Complete documentation
    │   └── START.bat               ← Double-click launcher
    └── droprouter_ignore.json      ← Created at runtime
```

## Installation Steps

**1. Extract the zip**
- Extract `tb_droprouterhud.zip` to your TrailBoss project root
- This creates `tools/DropRouterHud/` with all files

**2. Install dependencies** (if not already installed)
```bash
cd tools/DropRouterHud
pip install -r requirements.txt
```

**3. Configure for your project**
Edit `tools/DropRouterHud/config.json`:
- `project_name`: Your project name (displays in HUD)
- `project_root`: Leave as `"../.."` (goes up two levels to project root)
- `prefix`: Your file prefix (e.g., `"tb_"` for TrailBoss)
- `known_root_folders`: List your project's top-level folders

**4. Launch**
Double-click `tools/DropRouterHud/START.bat`

Or from command line:
```bash
cd tools/DropRouterHud
python droprouterhud.py
```

## Usage

**Drop files into Downloads:**
- `tb_strategy.py` → Routes to appropriate folder
- `tb_latest.zip` → Shows tree preview if structured

**HUD displays:**
```
DL → TrailBoss (47)
```
- `DL` = Downloads folder
- `TrailBoss` = Project name (exact folder name from config)
- `(47)` = Number of files processed

**Right-click HUD:**
- **Info** - Show router details
- **Quit** - Stop the router

## Multiple Projects

To use with multiple projects:

**1. Copy to each project**
```
TrailBoss/tools/DropRouterHud/    → tb_ prefix
MarshyBot/tools/DropRouterHud/    → mb_ prefix
ToolSnap/tools/DropRouterHud/     → ts_ prefix
```

**2. Update each config.json**
- Set unique `project_name`
- Set unique `prefix`
- Customize `known_root_folders` for each project

**3. Run all simultaneously**
- Each gets its own HUD position (auto-stacked)
- Each watches for its own prefix
- No conflicts, clean separation

## What Stayed the Same

✓ Smart ZIP structure detection
✓ Pattern-based routing rules
✓ Startup scan for existing files
✓ Ignore list functionality
✓ Multi-instance coordination
✓ Debounce logic for file stability
✓ Auto-overwrite handling
✓ Extension filtering

## Breaking Changes

None - this is a complete replacement, not an update to existing system.

Old system files can be deleted if present:
- `project_watcher.py`
- `watcher_hud.py`
- `watcher_dialogs.py`
- `watcher_config.json`

## Console Output

Console still shows detailed logging:
```
============================================================
  TrailBoss DropRouter
============================================================
Watching: C:\Users\...\Downloads
Prefix:   tb_*
Target:   C:\auto_trading\bots\trailboss
Known:    backtest, config, core, shared, tests, tools, ui, utils
Extensions: .bat, .cfg, .ini, .json, .md, .ps1, .py, .toml, .txt, .yaml, .yml, .zip
------------------------------------------------------------
HUD position: 0
HUD overlay enabled
No existing tb_* files to process.
------------------------------------------------------------
Watching for new files... (Ctrl+C to stop)

📦 Structure zip: tb_latest.zip
    strategy.py  → core
    helpers.py  → utils
  📦 tb_latest.zip: 2 files extracted, zip deleted
```

## Troubleshooting

**HUD not visible:**
```bash
# Check dependencies
pip install PySide6 psutil watchdog

# Test without HUD
python droprouterhud.py --no-hud
```

**Files not routing:**
- Check file has correct prefix (`tb_`, etc.)
- Check file extension is in `watched_extensions`
- Check console for error messages

**Config not loading:**
- Verify `config.json` is valid JSON
- Check `project_root` path is correct (`"../.."` from DropRouterHud folder)

## Next Steps

1. Extract zip to TrailBoss project
2. Review `config.json` settings
3. Double-click `START.bat` to test
4. Drop a test file (`tb_test.txt`) into Downloads
5. Watch HUD update and console output
6. Copy to other projects as needed

## Support Files

All documentation is in `tools/DropRouterHud/README.md`

Lock files location: `~/.droprouterhud_locks/`
Ignore list: `tools/droprouter_ignore.json`
