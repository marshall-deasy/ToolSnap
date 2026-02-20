# DropRouterHud v2.0 - Complete Refactor

## Summary of Changes

Version 2.0 is a major refactor that splits functionality into specialized modules, removes all tkinter dependencies, and implements your requirements for zip handling and tree display.

---

## What Changed

### 1. **Modular Architecture** (New)
Split monolithic 730-line file into focused modules:

**routing.py** (NEW - ~150 lines)
- `get_suggested_destination()` - Pattern matching for single files
- `get_structure_destination()` - Path analysis for zip contents
- `validate_routing_rules()` - Config validation helper
- Single source of truth for all routing decisions

**zip_handler.py** (NEW - ~200 lines)
- `get_zip_files()` - Read zip contents
- `detect_zip_mode()` - Structure detection (wrapper folders, known paths)
- `extract_zip_structure()` - Path-based extraction
- Single source of truth for all zip operations

**droprouterhud.py** (REFACTORED - ~250 lines)
- Orchestration only: config, watching, coordination
- Imports from routing.py and zip_handler.py
- No more copy-paste logic
- Clean separation of concerns

### 2. **Pure PySide6** (Fixed)
- Removed all tkinter imports
- Replaced `messagebox.showwarning` with `QMessageBox`
- Added `_show_flagged_notification()` method using PySide6
- Consistent UI framework throughout

### 3. **ALL Zips Show Tree Dialog** (Changed Behavior)
**Before:** Structure zips → dialog, Flat zips → auto-dump to project root
**After:** ALL zips → tree dialog with yellow ⚠️ warnings for unrecognized paths

- User reviews every zip before extraction
- Flagged files default to Downloads folder
- User can accept or reject entire zip
- Respects principle: zip internal structure tells router where files go

### 4. **Tree Always Fully Expanded** (UI Improvement)
- Added `tree.expandAll()` after population
- All folders open by default
- Just scroll with mouse wheel to see everything
- No clicking folder icons to reveal contents

### 5. **Version Display in HUD** (Feature)
**Before:** `DL → TrailBoss (5)`
**After:** `2.0 DL → TrailBoss (5)`

- Version constant at top of droprouterhud.py
- Passed to HUD during creation
- Easy to see which version is running

### 6. **Fixed Critical Bugs**
**Bug 1: Files Not Re-Processing**
- Startup files were permanently blocked from re-processing
- Removed `handler.processing.update(startup_scanned)`
- Processing set now only tracks current operations

**Bug 2: Dialog Crashes**
- Three locations called `.show()` instead of `.show_dialog()`
- Fixed in `_handle_zip()`, `_handle_single()`, and `process_startup()`
- Dialogs now display correctly

---

## File Structure

```
DropRouterHud/
├── routing.py            (NEW)     - Pattern matching & destination logic
├── zip_handler.py        (NEW)     - Zip detection & extraction
├── droprouterhud.py      (CHANGED) - Main orchestrator (refactored)
├── dialogs.py            (CHANGED) - Tree expandAll() added
├── hud_overlay.py        (CHANGED) - Version display added
├── instance_manager.py   (unchanged)
├── config.json           (unchanged)
└── requirements.txt      (unchanged)
```

---

## Manual Steps Required

1. **Backup** your current DropRouterHud folder
2. **Replace** these 5 files:
   - routing.py (new)
   - zip_handler.py (new)
   - droprouterhud.py (updated)
   - dialogs.py (updated)
   - hud_overlay.py (updated)
3. **Keep** your existing:
   - config.json (your routing rules are here)
   - instance_manager.py
   - requirements.txt
   - droprouter_ignore.json (if it exists)

---

## Testing Checklist

### Zips
- [ ] Drop structure zip → see tree dialog, all folders expanded
- [ ] Drop flat zip → see tree dialog with ⚠️ warnings
- [ ] Accept zip → files extract to correct paths
- [ ] Reject zip → nothing extracted
- [ ] Drop same zip twice → both process correctly

### Single Files
- [ ] Drop `TB_test.py` → routes based on config patterns
- [ ] Drop unmatched file → see popup, can ignore
- [ ] Drop matched file twice → both process

### HUD
- [ ] Shows `2.0 DL → ProjectName (0)` at startup
- [ ] Count increments when files processed
- [ ] Right-click menu works

### Multi-Instance
- [ ] Run multiple routers → HUDs stack properly
- [ ] Each processes only its own prefix

---

## Debugging Improvements

Clear module boundaries make debugging obvious:

**"Routing not working"** → Check `routing.py`
- Pattern issues
- Destination logic
- Config validation

**"Zip extraction wrong"** → Check `zip_handler.py`
- Structure detection
- Path flagging
- Extraction logic

**"Tree dialog issues"** → Check `dialogs.py`
- UI behavior
- Expand logic

**"Files not detected"** → Check `droprouterhud.py`
- Watchdog setup
- Debouncing
- Event handling

**"HUD not updating"** → Check `hud_overlay.py`
- Display logic
- Signal handling

---

## Routing Rules Help

If single files still aren't routing correctly, check your `config.json`:

### Example routing_rules:
```json
{
  "routing_rules": [
    { "pattern": ".*\\.bat$", "destination": "tools" },
    { "pattern": ".*\\.ps1$", "destination": "tools" },
    { "pattern": ".*backtest.*\\.py$", "destination": "backtest" },
    { "pattern": ".*test.*\\.py$", "destination": "tests" },
    { "pattern": ".*\\.py$", "destination": "core" }
  ]
}
```

**Common mistakes:**
- Forgot `.*` at start: `\\.py$` → should be `.*\\.py$`
- Forgot to escape dot: `.py$` → should be `\\.py$`
- Wrong order: general patterns before specific ones

**Pro tip:** More specific patterns FIRST, general patterns LAST.

---

## What Each Module Does

### routing.py
Answers: "Where should this file go?"
- Matches single files against patterns
- Analyzes zip paths to determine validity
- Validates routing configuration

### zip_handler.py
Answers: "What's in this zip and how do I extract it?"
- Reads zip contents
- Detects structure (wrapper folders, known paths)
- Extracts files to determined locations

### droprouterhud.py
Answers: "What happens when a file appears?"
- Watches Downloads folder
- Coordinates between modules
- Shows dialogs
- Updates HUD
- Manages lifecycle

### dialogs.py
Answers: "How do I show the user what's happening?"
- Tree preview for zips
- Unmatched file popup
- User choices (accept/reject/ignore)

### hud_overlay.py
Answers: "What's the router's status?"
- Floating overlay display
- File count tracking
- Multi-instance positioning

---

## Version History

**v2.0** (2025-02-09)
- Modular architecture (3 new specialized modules)
- Pure PySide6 (removed tkinter)
- All zips show tree dialog (no auto-extract)
- Tree always fully expanded
- Version number in HUD
- Fixed startup blocking bug
- Fixed dialog crash bug

**v1.x** (previous)
- Monolithic 730-line file
- Mixed tkinter/PySide6
- Auto-extracted flat zips
- Startup blocking bug
- Dialog method naming issues

---

## Notes

- **No breaking changes** to config.json format
- **No breaking changes** to ignore list
- **Improved** error messages with module names
- **Easier** to add features (clear module boundaries)
- **Easier** to test (can test modules independently)

If you encounter issues, the modular structure makes it easier to diagnose:
1. Check console output for module name in error
2. Open that specific module file
3. Add debug print statements if needed
4. File an issue with the specific module name

---

## Questions or Issues?

Common scenarios:

**"Routing still not working"**
→ Check patterns in config.json, see routing.py comments

**"Zip tree looks wrong"**
→ Check zip_handler.py detection logic, verify known_root_folders in config

**"HUD not showing version"**
→ Verify you replaced hud_overlay.py

**"Getting import errors"**
→ Verify all 5 files are in same directory

**"Tree not expanded"**
→ Verify you replaced dialogs.py with updated version
