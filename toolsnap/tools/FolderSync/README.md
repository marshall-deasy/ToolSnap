# FolderSync

A visual folder comparison tool for identifying and synchronizing files across multiple locations.

## Purpose

FolderSync helps you compare tool folders across multiple locations to identify which has the newest versions. Perfect for cleaning up scattered development tools, backups, and project directories.

## Features

- **Visual Comparison Grid**: Side-by-side view of folders with color-coded status indicators
- **Smart Status Detection**: Automatically identifies newest, older, same, and missing versions
- **Safe Operations**: Rename old versions before replacing (no data loss)
- **Context Actions**: Right-click any cell for location-specific operations
- **Conflict Filtering**: Focus on only the files that need attention

## Installation

### Requirements
- Python 3.10 or higher
- PySide6

### Install Dependencies
```bash
pip install PySide6
```

## Usage

### Launch
```bash
python main.py
```

### Workflow

1. **Add Folders**: Click "+ Add Folder" to select each tools folder you want to compare
   - Example: `C:\auto_trading\bots\trailboss\tools`
   - Example: `C:\auto_trading\bots\marshybot2\tools`
   - Add as many as needed (minimum 2)

2. **Compare**: Click "COMPARE" to scan all folders and build the comparison grid

3. **Review**: The grid shows:
   - ✓ Green = Newest version
   - ⚠ Orange = Older version
   - ❌ Red = Missing from this location
   - ═ Blue = Same age as newest

4. **Take Action**: Right-click any cell to:
   - **Distribute Newest** (from newest cells): Copy to all locations, rename/delete old
   - **Replace with Newest** (from older cells): Update just this location
   - **Copy Newest Here** (from missing cells): Add tool to this location
   - **Rename to .OLD**: Mark for manual cleanup
   - **Delete**: Remove folder permanently
   - **Open in Explorer**: View folder contents

5. **Filter**: Check "Show Only Conflicts" to hide tools that are already in sync

## Status Indicators

| Symbol | Color  | Meaning |
|--------|--------|---------|
| ✓      | Green  | This location has the newest version |
| ⚠      | Orange | This location has an older version |
| ❌     | Red    | Tool is missing from this location |
| ═      | Blue   | Same age as newest (tied) |

## Right-Click Actions

### On Newest (✓) Cells
- **Distribute Newest (Rename Older)**: Copy this version to all locations, rename old versions to `.OLD_timestamp`
- **Distribute Newest (Delete Older)**: Copy this version to all locations, delete old versions

### On Older (⚠) Cells
- **Replace with Newest**: Update just this location with the newest version
- **Rename to .OLD**: Mark this folder for manual cleanup later

### On Missing (❌) Cells
- **Copy Newest Here**: Add the tool to this location

### All Cells
- **Open in Explorer**: View the folder contents
- **Delete This Folder**: Permanently remove (with confirmation)

## Safety Features

- **Rename Before Replace**: Default behavior renames old folders to `.OLD_timestamp` before copying
- **Confirmation Dialogs**: All destructive operations require confirmation
- **Progress Feedback**: Visual progress for all file operations
- **Error Reporting**: Clear messages if operations fail

## Example Use Case

You have 5 tool folders that should be identical:
```
C:\auto_trading\bots\trailboss\tools
C:\auto_trading\bots\marshybot2\tools
C:\auto_trading\bots\mr_bot\tools
C:\ToolSnap\toolsnap\tools
C:\ToolSnap\toolsnap_db\tools
```

Over time, you've edited tools in different locations and lost track of which has the latest versions.

**With FolderSync:**
1. Add all 5 folders
2. Click COMPARE
3. See instantly which folder has the newest `CodeGrep`, `FileTagger`, etc.
4. Right-click the newest and choose "Distribute Newest (Rename Older)"
5. All 5 folders are now synchronized

## Technical Details

### How "Newest" is Determined
- Recursively scans each tool folder for all files
- Uses the newest modification timestamp found anywhere in the folder tree
- Timestamps within 1 second are considered "same age" (filesystem precision tolerance)

### File Operations
- **Copy**: Uses `shutil.copytree` with `dirs_exist_ok=True`
- **Rename**: Appends `.OLD_YYYYMMDD_HHMMSS` to folder name
- **Delete**: Uses `shutil.rmtree` (permanent, not recycle bin)

### Project Structure
```
FolderSync/
├── config.py          # UI constants and colors
├── models.py          # Data structures
├── scanner.py         # Filesystem scanning
├── sync_engine.py     # File operations
├── gui.py             # Qt user interface
├── main.py            # Entry point
└── README.md          # This file
```

## Keyboard Shortcuts

- **Ctrl+A**: Add folder (when folder list has focus)
- **Delete**: Remove selected folder from list
- **F5**: Re-run comparison

## Troubleshooting

### "Permission denied" error
- Make sure no programs have files open in the folders being compared
- Run as administrator if comparing system folders

### Grid is empty after comparison
- Check that the folders contain subdirectories (tool folders)
- Try unchecking "Show Only Conflicts" to see all tools

### "Already exists" error during copy
- Should not happen (operations rename/delete first)
- If it does, manually remove the conflicting folder and retry

## License

Created for personal use. Free to modify and distribute.

## Author

Built for managing scattered development tools across multiple project locations.
