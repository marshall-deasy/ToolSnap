"""Configuration management — single source for all app settings."""

import json
import os
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent
_PROJECT_ROOT = _CONFIG_DIR.parent
_SETTINGS_FILE = _CONFIG_DIR / "settings.json"

_DEFAULTS = {
    "import_directory": "",
    "database_path": "toolsnap.db",
    "photo_cache_max_mb": 200,
    "window_width": 1400,
    "window_height": 900,
    "qr_label_size_mm": 30,
    "qr_label_prefix": "TS",
}

_settings: dict = {}


def load() -> dict:
    """Load settings from disk, filling missing keys with defaults."""
    global _settings
    if _SETTINGS_FILE.exists():
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            _settings = json.load(f)
    else:
        _settings = {}
    for key, default in _DEFAULTS.items():
        _settings.setdefault(key, default)
    return _settings


def save() -> None:
    """Persist current settings to disk."""
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(_settings, f, indent=4)


def get(key: str, fallback=None):
    """Get a single setting value."""
    if not _settings:
        load()
    return _settings.get(key, fallback)


def set_value(key: str, value) -> None:
    """Set a single setting value (call save() to persist)."""
    if not _settings:
        load()
    _settings[key] = value


def get_db_path() -> Path:
    """Resolve database path (relative paths resolve against config dir)."""
    if not _settings:
        load()
    p = Path(_settings["database_path"])
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    return p


def get_import_dir() -> Path | None:
    """Return configured import directory, or None if not set."""
    if not _settings:
        load()
    val = _settings.get("import_directory", "")
    if not val:
        return None
    return Path(val)
