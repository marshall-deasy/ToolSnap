"""
Configuration management for LogViewer.

Handles loading config from JSON and providing defaults.
"""

import json
import os
from typing import List, Set


class Config:
    """Manages configuration settings for log viewing."""

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
            "log_patterns": ["*.log"],
            "exclude_dirs": [
                "__pycache__",
                ".git",
                ".vscode",
                ".idea",
                "node_modules",
                "venv",
                ".venv",
                "env",
                ".env",
            ],
            "tail_lines": 100,
            "refresh_interval_ms": 2000,
            "max_file_size_mb": 100,
            "favorites": [],
        }

    @property
    def levels_up_to_root(self) -> int:
        """Number of directory levels to traverse up to reach project root."""
        return self._data.get("levels_up_to_root", 2)

    @property
    def log_patterns(self) -> List[str]:
        """List of filename patterns to match for log files."""
        return self._data.get("log_patterns", ["*.log"])

    @property
    def exclude_dirs(self) -> Set[str]:
        """Set of directory names to exclude from scanning."""
        return set(self._data.get("exclude_dirs", []))

    @property
    def tail_lines(self) -> int:
        """Number of lines to show when tailing a log file."""
        return self._data.get("tail_lines", 100)

    @property
    def refresh_interval_ms(self) -> int:
        """Refresh interval in milliseconds for live tail."""
        return self._data.get("refresh_interval_ms", 2000)

    @property
    def max_file_size_mb(self) -> int:
        """Maximum log file size in MB to allow viewing."""
        return self._data.get("max_file_size_mb", 100)

    @property
    def favorites(self) -> List[str]:
        """List of favorited log file paths (relative to project root)."""
        return self._data.get("favorites", [])

    def add_favorite(self, log_path: str) -> None:
        """
        Add a log file to favorites.

        Args:
            log_path: Relative path to log file from project root
        """
        if log_path not in self._data["favorites"]:
            self._data["favorites"].append(log_path)
            self.save()

    def remove_favorite(self, log_path: str) -> None:
        """
        Remove a log file from favorites.

        Args:
            log_path: Relative path to log file from project root
        """
        if log_path in self._data["favorites"]:
            self._data["favorites"].remove(log_path)
            self.save()

    def save(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
