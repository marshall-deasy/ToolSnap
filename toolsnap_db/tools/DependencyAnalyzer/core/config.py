"""
Configuration management for DependencyAnalyzer.

Handles loading config from JSON and providing defaults.
"""

import json
import os
from typing import List, Set, Dict


class Config:
    """Manages configuration settings for dependency analysis and cleanup."""

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
            "archive_folder": "archive",
            "scripts_folder": "scripts",
            "output_folder": "output",
            "file_categories": {
                "scripts": [".bat", ".ps1", ".sh", ".cmd"],
                "outputs": [
                    "*_STRUCTURE_*.txt",
                    "*.log",
                    "*_results.json",
                    "*_performance*.json",
                ],
                "temp": [".pyc", ".pyo", "*.pyc", "*.pyo", "__pycache__"],
                "shortcuts": [".lnk"],
                "duplicates": [
                    " (1).",
                    " (2).",
                    " (3).",
                    "_old.",
                    "_backup.",
                    "_FIXED.",
                    "_copy.",
                ],
            },
            "exclude_from_analysis": [
                "__pycache__",
                ".git",
                ".vscode",
                "venv",
                ".venv",
                "node_modules",
                "archive",
                "scripts",
                "output",
            ],
        }

    @property
    def levels_up_to_root(self) -> int:
        """Number of directory levels to traverse up to reach project root."""
        return self._data.get("levels_up_to_root", 2)

    @property
    def archive_folder(self) -> str:
        """Name of folder to archive orphaned files."""
        return self._data.get("archive_folder", "archive")

    @property
    def scripts_folder(self) -> str:
        """Name of folder for script files (.bat, .ps1, etc.)."""
        return self._data.get("scripts_folder", "scripts")

    @property
    def output_folder(self) -> str:
        """Name of folder for output files (logs, structure files, etc.)."""
        return self._data.get("output_folder", "output")

    @property
    def file_categories(self) -> Dict[str, List[str]]:
        """Dictionary of file categories and their patterns."""
        return self._data.get("file_categories", {})

    @property
    def exclude_from_analysis(self) -> Set[str]:
        """Set of directory names to exclude from analysis."""
        return set(self._data.get("exclude_from_analysis", []))

    def save(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
