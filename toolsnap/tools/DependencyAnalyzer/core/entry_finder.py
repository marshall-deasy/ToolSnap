"""
Entry point detection for DependencyAnalyzer.

Parses .bat/.ps1 files to find Python entry points.
"""

import os
import re
from typing import List, Optional


class EntryFinder:
    """Finds Python entry points from batch files and scripts."""

    def __init__(self, target_folder: str):
        """
        Initialize entry finder.

        Args:
            target_folder: Folder to search for entry points
        """
        self.target_folder = target_folder

    def find_entry_points(self) -> List[str]:
        """
        Find all Python entry points in the target folder.

        Returns:
            List of absolute paths to Python entry point files
        """
        entry_points = []

        # Look for .bat and .ps1 files in root
        for filename in os.listdir(self.target_folder):
            filepath = os.path.join(self.target_folder, filename)

            if not os.path.isfile(filepath):
                continue

            # Check batch files
            if filename.lower().endswith('.bat'):
                entry = self._parse_bat_file(filepath)
                if entry:
                    entry_points.append(entry)

            # Check PowerShell scripts
            elif filename.lower().endswith('.ps1'):
                entry = self._parse_ps1_file(filepath)
                if entry:
                    entry_points.append(entry)

        # Also look for common entry point filenames
        common_entries = ['main.py', 'bot.py', 'app.py', 'run.py']
        for entry in common_entries:
            entry_path = os.path.join(self.target_folder, entry)
            if os.path.isfile(entry_path) and entry_path not in entry_points:
                entry_points.append(entry_path)

        return entry_points

    def _parse_bat_file(self, filepath: str) -> Optional[str]:
        """
        Parse a .bat file to find Python script it runs.

        Args:
            filepath: Path to .bat file

        Returns:
            Absolute path to Python file, or None if not found
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Look for patterns like:
            # python main.py
            # python -m bot
            # %PYTHON% bot.py
            patterns = [
                r'python\s+([a-zA-Z0-9_]+\.py)',  # python main.py
                r'python\s+-m\s+([a-zA-Z0-9_]+)',  # python -m bot
                r'%PYTHON%\s+([a-zA-Z0-9_]+\.py)',  # %PYTHON% bot.py
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    script_name = match.group(1)
                    # Handle -m module style
                    if not script_name.endswith('.py'):
                        script_name = script_name + '.py'

                    script_path = os.path.join(self.target_folder, script_name)
                    if os.path.isfile(script_path):
                        return script_path

        except Exception:
            pass

        return None

    def _parse_ps1_file(self, filepath: str) -> Optional[str]:
        """
        Parse a .ps1 file to find Python script it runs.

        Args:
            filepath: Path to .ps1 file

        Returns:
            Absolute path to Python file, or None if not found
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Similar patterns as batch files
            patterns = [
                r'python\s+([a-zA-Z0-9_]+\.py)',
                r'python\s+-m\s+([a-zA-Z0-9_]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    script_name = match.group(1)
                    if not script_name.endswith('.py'):
                        script_name = script_name + '.py'

                    script_path = os.path.join(self.target_folder, script_name)
                    if os.path.isfile(script_path):
                        return script_path

        except Exception:
            pass

        return None
