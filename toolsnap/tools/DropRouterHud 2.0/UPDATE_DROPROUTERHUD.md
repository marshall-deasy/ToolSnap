# droprouterhud.py Update Instructions

## Required Changes

ZipTreeDialog method changed: `.show()` → `.show_dialog()`

### Change #1: Line 422

**Old:**
```python
            dialog = ZipTreeDialog(
                filepath, contents, wrapper,
                project_name, project_root, resolver,
            )
            if not dialog.show():  # ← CHANGE THIS
                print(f"  Skipped: {filepath.name}")
                return
```

**New:**
```python
            dialog = ZipTreeDialog(
                filepath, contents, wrapper,
                project_name, project_root, resolver,
            )
            if not dialog.show_dialog():  # ← CHANGED
                print(f"  Skipped: {filepath.name}")
                return
```

### Change #2: Line 539

**Old:**
```python
                dialog = ZipTreeDialog(
                    filepath, contents, wrapper,
                    project_name, project_root, resolver,
                )
                if dialog.show():  # ← CHANGE THIS
                    extracted, flagged = extract_zip_structure(filepath, wrapper, cfg)
```

**New:**
```python
                dialog = ZipTreeDialog(
                    filepath, contents, wrapper,
                    project_name, project_root, resolver,
                )
                if dialog.show_dialog():  # ← CHANGED
                    extracted, flagged = extract_zip_structure(filepath, wrapper, cfg)
```

## Quick Find/Replace

**Search:** `dialog.show()`
**Replace:** `dialog.show_dialog()`
**Files:** `droprouterhud.py` only

**Expected:** 2 replacements

## Verify

After making changes, search for `.show()` in droprouterhud.py:
- Should find 0 results (or only other unrelated show() calls)
- ZipTreeDialog should only use `.show_dialog()`
