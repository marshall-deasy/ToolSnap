"""
Application constants — values used by multiple modules.

Path/runtime config lives in config/__init__.py (settings.json).
This file holds compile-time constants only.
"""

from pathlib import Path

# App root — C:\toolsnap_db
APP_DIR = Path(__file__).resolve().parent.parent

# Default import directory — where the phone drops session folders.
DEFAULT_IMPORT_DIR = APP_DIR / "imports"

# Manifest filename the importer looks for inside each session folder.
MANIFEST_FILENAME = "manifest.json"

# When True, tools with matching (catalogNumber, manufacturer) are merged on import.
DEDUP_ENABLED = True
