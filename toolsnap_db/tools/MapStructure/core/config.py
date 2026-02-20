"""
Configuration management for map_structure.

Handles loading config from JSON and providing defaults.
"""

import json
import os
import re
from typing import Set, Tuple


class Config:
    """Manages configuration settings for directory mapping."""

    def __init__(self, config_path: str):
        """
        Initialize config from JSON file.

        Args:
            config_path: Path to config.json file
        """
        self.config_path = config_path
        self._data = self._load_config()

    def _load_config(self) -> dict:
        """Load config from JSON file with fallback to defaults."""
        if not os.path.isfile(self.config_path):
            return self._get_defaults()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults to handle missing keys
                defaults = self._get_defaults()
                defaults.update(data)
                return defaults
        except (json.JSONDecodeError, IOError):
            return self._get_defaults()

    @staticmethod
    def _get_defaults() -> dict:
        """Return default configuration values."""
        return {
            "levels_up_to_root": 2,
            "exclude_dirs": [
                "__pycache__",
                ".git",
                ".vscode",
                ".idea",
                "node_modules",
                ".mypy_cache",
                ".pytest_cache",
                "venv",
                ".venv",
                "env",
                ".env",
                ".tox",
                "dist",
                "build",
                "egg-info",
            ],
            "exclude_suffixes": [".egg-info"],
            "structure_file_pattern": r"^.+_STRUCTURE(_\d{8}_\d{6})?\.txt$",
        }

    @property
    def levels_up_to_root(self) -> int:
        """Number of directory levels to traverse up to reach project root."""
        return self._data.get("levels_up_to_root", 2)

    @property
    def exclude_dirs(self) -> Set[str]:
        """Set of directory names to exclude from mapping."""
        return set(self._data.get("exclude_dirs", []))

    @property
    def exclude_suffixes(self) -> Tuple[str, ...]:
        """Tuple of file/directory suffixes to exclude from mapping."""
        return tuple(self._data.get("exclude_suffixes", []))

    @property
    def structure_file_pattern(self) -> re.Pattern:
        """Compiled regex pattern for identifying structure output files."""
        pattern_str = self._data.get(
            "structure_file_pattern",
            r"^.+_STRUCTURE(_\d{8}_\d{6})?\.txt$",
        )
        return re.compile(pattern_str, re.IGNORECASE)

    def save(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
