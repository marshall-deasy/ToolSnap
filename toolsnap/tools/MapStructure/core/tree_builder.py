"""
Directory tree building logic for map_structure.

Pure functions for traversing directories and generating tree representations.
"""

import os
from typing import List, Set, Tuple
import re


class TreeBuilder:
    """Builds text-based directory tree representations."""

    def __init__(
        self,
        exclude_dirs: Set[str],
        exclude_suffixes: Tuple[str, ...],
        structure_pattern: re.Pattern,
    ):
        """
        Initialize tree builder with exclusion rules.

        Args:
            exclude_dirs: Set of directory names to skip
            exclude_suffixes: Tuple of file/dir suffixes to skip
            structure_pattern: Regex pattern for structure output files to skip
        """
        self.exclude_dirs = exclude_dirs
        self.exclude_suffixes = exclude_suffixes
        self.structure_pattern = structure_pattern

    def build_tree(
        self,
        root: str,
        prefix: str = "",
        depth: int | None = None,
        current_depth: int = 0,
        dirs_only: bool = False,
    ) -> Tuple[List[str], int, int]:
        """
        Recursively build directory tree representation.

        Args:
            root: Root directory to map
            prefix: String prefix for tree drawing characters
            depth: Maximum depth to traverse (None = unlimited)
            current_depth: Current recursion depth
            dirs_only: If True, only show directories

        Returns:
            Tuple of (tree_lines, file_count, dir_count)
        """
        lines = []
        file_count = 0
        dir_count = 0

        # Try to read directory contents
        try:
            entries = sorted(
                os.listdir(root),
                key=lambda e: (
                    not os.path.isdir(os.path.join(root, e)),
                    e.lower(),
                ),
            )
        except PermissionError:
            lines.append(f"{prefix}[ACCESS DENIED]")
            return lines, 0, 0

        # Filter entries based on exclusion rules
        filtered = self._filter_entries(root, entries, dirs_only)

        # Process each entry
        for i, entry in enumerate(filtered):
            path = os.path.join(root, entry)
            is_last = i == len(filtered) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            if os.path.isdir(path):
                dir_count += 1
                lines.append(f"{prefix}{connector}{entry}/")

                # Check depth limit
                if depth is not None and current_depth + 1 >= depth:
                    lines.append(f"{prefix}{extension}└── ...")
                else:
                    # Recurse into subdirectory
                    sub_lines, sub_files, sub_dirs = self.build_tree(
                        path,
                        prefix + extension,
                        depth,
                        current_depth + 1,
                        dirs_only,
                    )
                    lines.extend(sub_lines)
                    file_count += sub_files
                    dir_count += sub_dirs
            else:
                file_count += 1
                lines.append(f"{prefix}{connector}{entry}")

        return lines, file_count, dir_count

    def _filter_entries(
        self,
        root: str,
        entries: List[str],
        dirs_only: bool,
    ) -> List[str]:
        """
        Filter directory entries based on exclusion rules.

        Args:
            root: Root directory path
            entries: List of entry names
            dirs_only: If True, exclude all files

        Returns:
            Filtered list of entry names
        """
        filtered = []
        for entry in entries:
            # Skip excluded directories
            if entry in self.exclude_dirs:
                continue

            # Skip entries with excluded suffixes
            if any(entry.endswith(suffix) for suffix in self.exclude_suffixes):
                continue

            # Skip structure output files
            if self.structure_pattern.match(entry):
                continue

            # Skip files if dirs_only mode
            full_path = os.path.join(root, entry)
            if dirs_only and not os.path.isdir(full_path):
                continue

            filtered.append(entry)

        return filtered

    def format_output(
        self,
        root_name: str,
        tree_lines: List[str],
        file_count: int,
        dir_count: int,
    ) -> str:
        """
        Format tree lines into final output string.

        Args:
            root_name: Name of the root directory
            tree_lines: List of tree line strings
            file_count: Total number of files
            dir_count: Total number of directories

        Returns:
            Formatted output string with header and footer
        """
        header = f"{root_name}/"
        footer = f"\n[ Dirs: {dir_count} | Files: {file_count} ]"
        return "\n".join([header] + tree_lines) + footer
