# MapStructure - Complete Refactor Summary

## What Changed

### Architecture Transformation
**Before:** Single 200-line file with mixed concerns
**After:** Clean modular architecture with separation of concerns

### New File Structure
```
MapStructure/
├── core/                          [NEW]
│   ├── __init__.py               Package initialization
│   ├── config.py                 Configuration management (~100 lines)
│   ├── path_resolver.py          Path detection & GUI picker (~120 lines)
│   └── tree_builder.py           Pure tree logic (~160 lines)
├── map_structure.py              Main orchestrator (~150 lines) [REFACTORED]
├── install.py                    Registry installer (~130 lines) [NEW]
├── map_structure_launcher.bat    Launcher wrapper [UPDATED]
├── config.json                   Externalized configuration [NEW]
└── README.md                     Complete documentation [NEW]
```

## Key Improvements

### 1. Smart Auto-Detection (PRIMARY FEATURE)
- **Auto-detects project root** by walking up 2 levels from script location
- **No arguments needed** - just run `python map_structure.py`
- Saves output to project root: `trailboss/TRAILBOSS_STRUCTURE_20250207_153045.txt`

### 2. Zero Hardcoded Paths
- **install.py** detects actual script location and writes registry file dynamically
- No more manual editing of `.reg` files
- Truly portable - works anywhere

### 3. Externalized Configuration
- **config.json** contains all exclusion rules
- Users can customize without touching code
- Easy to add/remove exclusion patterns

### 4. Engineering Rules Compliance
- ✅ **Single source of truth** - each piece of logic in one place
- ✅ **No copy-paste** - shared logic in base classes/modules
- ✅ **Complete working code** - no stubs, all imports resolve
- ✅ **Modular** - each file <400 lines, single responsibility
- ✅ **Separated concerns** - GUI/config/logic all isolated
- ✅ **Config separate** - no hardcoded values in code

## Installation & Setup

### 1. Deploy Files
Extract `MS_latest.zip` to: `C:\auto_trading\bots\trailboss\tools\MapStructure\`

### 2. Run Installer
```bash
cd C:\auto_trading\bots\trailboss\tools\MapStructure
python install.py
```

This will:
- Detect the actual script location
- Generate registry file with correct paths
- Install context menu entries
- Create `map_structure_install.reg` for reference

### 3. Test It
**Option A - Auto mode (recommended):**
```bash
python map_structure.py
```
→ Maps `C:\auto_trading\bots\trailboss\` automatically
→ Saves to `C:\auto_trading\bots\trailboss\TRAILBOSS_STRUCTURE_20250207_153045.txt`

**Option B - Context menu:**
Right-click on any folder → "Map Structure"

**Option C - Double-click:**
Double-click `map_structure_launcher.bat`

## Usage Examples

### Map entire project (auto-detect)
```bash
python map_structure.py
```

### Map specific directory
```bash
python map_structure.py C:\some\other\path
```

### Show folder picker GUI
```bash
python map_structure.py --pick
```

### Limit depth
```bash
python map_structure.py --depth 3
```

### Directories only
```bash
python map_structure.py --dirs-only
```

## Configuration

Edit `config.json` to customize:

```json
{
  "levels_up_to_root": 2,          // How many levels to walk up
  "exclude_dirs": [...],            // Directories to skip
  "exclude_suffixes": [...],        // File suffixes to skip
  "structure_file_pattern": "..."   // Pattern for structure files
}
```

## Manual Steps Required

1. **Deploy** - Extract zip to `C:\auto_trading\bots\trailboss\tools\MapStructure\`
2. **Install** - Run `python install.py` once
3. **Test** - Run `python map_structure.py` to verify
4. **Optional** - Customize `config.json` as needed

## Breaking Changes

### Changed Default Behavior
- **Old:** No args → shows folder picker
- **New:** No args → maps project root (2 levels up)
- **Migration:** Use `--pick` flag to get old picker behavior

### Registry Location
- **Old:** Hardcoded `C:\tools\map_structure_launcher.bat`
- **New:** Auto-detected actual location
- **Migration:** Run `install.py` to update registry

## What Each Module Does

### core/config.py
- Loads/saves configuration from JSON
- Provides property-based access to settings
- Handles defaults and validation

### core/path_resolver.py  
- Detects project root (walks up N levels)
- Manages last-directory cache
- Provides folder picker GUI (tkinter)

### core/tree_builder.py
- Pure tree-building logic
- Filters entries based on exclusion rules
- Recursive directory traversal
- Output formatting

### map_structure.py
- Main orchestrator - ties everything together
- Argument parsing
- File I/O (saving output)
- Minimal business logic (delegates to core)

### install.py
- Detects script location dynamically
- Generates .reg file with actual paths
- Applies registry changes
- Provides uninstall capability

## File Size Comparison

| File | Lines | Responsibility |
|------|-------|----------------|
| core/config.py | ~100 | Configuration |
| core/path_resolver.py | ~120 | Path detection |
| core/tree_builder.py | ~160 | Tree logic |
| map_structure.py | ~150 | Orchestration |
| install.py | ~130 | Installation |

**Total:** ~660 lines (was ~200 lines)
**Improvement:** Better separation, easier to maintain, more features

## Dependencies

- Python 3.9+
- tkinter (optional - for folder picker)
- Windows (for context menu integration)

## Testing Checklist

- [ ] Extract zip to correct location
- [ ] Run `python install.py`
- [ ] Verify registry entries created
- [ ] Test `python map_structure.py` (auto-detect)
- [ ] Verify output saved to `trailboss/` root
- [ ] Test context menu (right-click folder)
- [ ] Test `--pick` flag (folder picker)
- [ ] Test `--depth` and `--dirs-only` flags
- [ ] Customize `config.json` and re-test
- [ ] Test uninstall: `python install.py --uninstall`

## Troubleshooting

**Context menu not appearing:**
- Run `install.py` again
- Check registry: `HKEY_CURRENT_USER\Software\Classes\Directory\shell\MapStructure`
- Verify launcher.bat path is correct

**Output not in project root:**
- Check `config.json` → `levels_up_to_root` setting
- Verify script is at expected depth

**Folder picker not working:**
- Install tkinter: `pip install tk`
- Or use direct path: `python map_structure.py C:\path`

**Exclusions not working:**
- Edit `config.json`
- Verify JSON syntax is valid
- Restart script after changes
