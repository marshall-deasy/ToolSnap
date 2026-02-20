"""
Configuration management for CodeGrep.

Handles loading config from JSON and providing defaults.
"""

import json
import os
from typing import List, Set


class Config:
    """Manages configuration settings for code search."""

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
            "file_patterns": ["*.py"],
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
                ".tox",
                "dist",
                "build",
                "egg-info",
            ],
            "exclude_files": ["*.pyc", "*.pyo", "*.pyd"],
            "context_lines": 2,
            "max_results": 500,
            "editor_command": "code",
        }

    @property
    def levels_up_to_root(self) -> int:
        """Number of directory levels to traverse up to reach project root."""
        return self._data.get("levels_up_to_root", 2)

    @property
    def file_patterns(self) -> List[str]:
        """List of filename patterns to match for code files."""
        return self._data.get("file_patterns", ["*.py"])

    @property
    def exclude_dirs(self) -> Set[str]:
        """Set of directory names to exclude from scanning."""
        return set(self._data.get("exclude_dirs", []))

    @property
    def exclude_files(self) -> List[str]:
        """List of file patterns to exclude."""
        return self._data.get("exclude_files", [])

    @property
    def context_lines(self) -> int:
        """Number of context lines to show before/after match."""
        return self._data.get("context_lines", 2)

    @property
    def max_results(self) -> int:
        """Maximum number of search results to return."""
        return self._data.get("max_results", 500)

    @property
    def editor_command(self) -> str:
        """Editor command for opening files (e.g., 'code' for VS Code)."""
        return self._data.get("editor_command", "code")

    def save(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
