# droprouterhud.py Update Instructions - Step 2

## Required Change

UnmatchedFilePopup method changed: `.show()` → `.show_dialog()`

### Change: Line ~486

**Old:**
```python
            UnmatchedFilePopup(
                filepath, self.ignore_list,
                lambda il: save_ignore_list(il, cfg),
            ).show()  # ← CHANGE THIS
```

**New:**
```python
            UnmatchedFilePopup(
                filepath, self.ignore_list,
                lambda il: save_ignore_list(il, cfg),
            ).show_dialog()  # ← CHANGED
```

## Quick Find/Replace

**Search:** `UnmatchedFilePopup(`
**Then look for:** `.show()` on that instance
**Replace with:** `.show_dialog()`
**Files:** `droprouterhud.py` only

**Expected:** 1 replacement

## Combined with Step 1

If you haven't already updated from Step 1, you need **3 total changes**:

1. ZipTreeDialog call #1: `.show()` → `.show_dialog()` (line ~422)
2. ZipTreeDialog call #2: `.show()` → `.show_dialog()` (line ~539)
3. UnmatchedFilePopup call: `.show()` → `.show_dialog()` (line ~486)

## Verify

After making changes, search for `.show()` in droprouterhud.py:
- Should find 0 results for dialog instances
- All dialogs should use `.show_dialog()`

## Test

Drop a file with no routing match to test UnmatchedFilePopup:
```
# Example - file with extension not in watched_extensions
tb_test.xyz
```

Should show green-themed popup with:
- "No route for:"
- Filename in green bold
- Green glowing buttons
- Dark semi-transparent background
