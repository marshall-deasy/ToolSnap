"""
Path resolution logic for map_structure.

Handles auto-detection of project root and remembering last mapped directory.
"""

import os


class PathResolver:
    """Resolves project root and manages path-related operations."""

    def __init__(self, script_dir: str, levels_up: int):
        """
        Initialize path resolver.

        Args:
            script_dir: Directory where map_structure.py lives
            levels_up: Number of levels to traverse up for project root
        """
        self.script_dir = script_dir
        self.levels_up = levels_up
        self.last_dir_file = os.path.join(script_dir, ".last_map_dir")

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

    def load_last_dir(self) -> str | None:
        """
        Load the last mapped directory from cache file.

        Returns:
            Path to last mapped directory if valid, None otherwise
        """
        if not os.path.isfile(self.last_dir_file):
            return None

        try:
            with open(self.last_dir_file, "r", encoding="utf-8") as f:
                path = f.read().strip()
                return path if path and os.path.isdir(path) else None
        except IOError:
            return None

    def save_last_dir(self, path: str) -> None:
        """
        Save a directory path to the cache file.

        Args:
            path: Directory path to remember
        """
        try:
            with open(self.last_dir_file, "w", encoding="utf-8") as f:
                f.write(path)
        except IOError:
            pass  # Silent fail - not critical

    def pick_folder(self, last_dir: str | None = None) -> str | None:
        """
        Open GUI folder picker dialog.

        Args:
            last_dir: Previously used directory to show in picker

        Returns:
            Selected folder path or None if cancelled
        """
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox

            root = tk.Tk()
            root.withdraw()

            if last_dir:
                reuse = messagebox.askyesnocancel(
                    "Map Structure",
                    f"Last folder mapped:\n{last_dir}\n\nUse this folder again?",
                )
                if reuse is None:  # Cancel
                    root.destroy()
                    return None
                if reuse:  # Yes
                    root.destroy()
                    return last_dir
                # No → fall through to picker

            folder = filedialog.askdirectory(
                title="Select a folder to map",
                initialdir=last_dir or os.path.expanduser("~"),
            )
            root.destroy()
            return folder if folder else None

        except ImportError:
            # tkinter not available - can't show picker
            return None
