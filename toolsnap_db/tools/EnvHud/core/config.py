"""
Configuration management for EnvHud.

Handles loading config from JSON and providing defaults.
"""

import json
import os
from typing import Dict


class Config:
    """Manages configuration settings for EnvHud."""

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
                # Merge with defaults
                defaults = self._get_defaults()
                defaults.update(data)
                return defaults
        except (json.JSONDecodeError, IOError):
            return self._get_defaults()

    @staticmethod
    def _get_defaults() -> dict:
        """Return default configuration values."""
        return {
            "colors": {
                "trading": "#f85149",
                "base": "#8b949e",
                "chatbots": "#3fb950",
                "default": "#58a6ff",
            },
            "refresh_interval_ms": 5000,
        }

    @property
    def colors(self) -> Dict[str, str]:
        """Environment color mappings."""
        return self._data.get("colors", {})

    @property
    def refresh_interval_ms(self) -> int:
        """Refresh interval in milliseconds."""
        return self._data.get("refresh_interval_ms", 5000)

    def get_color_for_env(self, env_name: str) -> str:
        """
        Get color for environment.

        Args:
            env_name: Name of environment

        Returns:
            Hex color code
        """
        return self.colors.get(env_name, self.colors.get("default", "#58a6ff"))

    def save(self) -> None:
        """Save current configuration to JSON file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
