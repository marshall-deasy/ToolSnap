"""
Path resolution logic for LogViewer.

Handles auto-detection of project root.
"""

import os


class PathResolver:
    """Resolves project root and manages path-related operations."""

    def __init__(self, script_dir: str, levels_up: int):
        """
        Initialize path resolver.

        Args:
            script_dir: Directory where app.py lives
            levels_up: Number of levels to traverse up for project root
        """
        self.script_dir = script_dir
        self.levels_up = levels_up

    def get_project_root(self) -> str:
        """
        Get project root by walking up from script directory.

        Returns:
            Absolute path to project root
        """
        current = self.script_dir
        for _ in range(self.levels_up):
            parent = os.path.dirname(current)
            if parent == current:  # Hit filesystem root
                break
            current = parent
        return current

    def get_relative_path(self, absolute_path: str, root: str) -> str:
        """
        Get relative path from root to file.

        Args:
            absolute_path: Full path to file
            root: Root directory

        Returns:
            Relative path from root
        """
        try:
            return os.path.relpath(absolute_path, root)
        except ValueError:
            # Different drives on Windows
            return absolute_path
