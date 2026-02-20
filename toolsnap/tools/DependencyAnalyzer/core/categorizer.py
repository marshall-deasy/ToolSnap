"""
File categorization for DependencyAnalyzer.

Categorizes files based on usage, type, and patterns.
"""

import os
import fnmatch
from typing import Dict, List, Set
from datetime import datetime


class FileCategory:
    """Represents a categorized file with metadata."""

    def __init__(self, filepath: str, category: str, reason: str):
        """
        Initialize file category.

        Args:
            filepath: Absolute path to file
            category: Category name (active, orphaned, scripts, etc.)
            reason: Reason for categorization
        """
        self.filepath = filepath
        self.category = category
        self.reason = reason
        self.filename = os.path.basename(filepath)
        self.size_bytes = 0
        self.modified_time = None
        self._update_metadata()

    def _update_metadata(self) -> None:
        """Update file size and modification time."""
        try:
            stat = os.stat(self.filepath)
            self.size_bytes = stat.st_size
            self.modified_time = datetime.fromtimestamp(stat.st_mtime)
        except OSError:
            pass

    @property
    def size_display(self) -> str:
        """Human-readable file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"

    @property
    def modified_display(self) -> str:
        """Human-readable modification time."""
        if not self.modified_time:
            return "Unknown"
        return self.modified_time.strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'filepath': self.filepath,
            'filename': self.filename,
            'category': self.category,
            'reason': self.reason,
            'size': self.size_display,
            'modified': self.modified_display,
        }


class Categorizer:
    """Categorizes files in a folder based on usage and patterns."""

    def __init__(
        self,
        target_folder: str,
        active_files: Set[str],
        file_categories: Dict[str, List[str]],
        exclude_dirs: Set[str],
    ):
        """
        Initialize categorizer.

        Args:
            target_folder: Folder to categorize
            active_files: Set of active Python file paths
            file_categories: Dictionary of category patterns from config
            exclude_dirs: Directories to exclude from categorization
        """
        self.target_folder = target_folder
        self.active_files = active_files
        self.file_categories_config = file_categories
        self.exclude_dirs = exclude_dirs

    def categorize_all_files(self) -> Dict[str, List[FileCategory]]:
        """
        Categorize all files in target folder.

        Returns:
            Dictionary mapping category names to lists of FileCategory objects
        """
        categorized = {
            'active': [],
            'orphaned': [],
            'scripts': [],
            'outputs': [],
            'temp': [],
            'shortcuts': [],
            'duplicates': [],
            'unknown': [],
        }

        # Walk the target folder
        for root, dirs, files in os.walk(self.target_folder):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            # Skip if we're inside tools folder (don't categorize the tools)
            rel_path = os.path.relpath(root, self.target_folder)
            if rel_path.startswith('tools'):
                continue

            for filename in files:
                filepath = os.path.join(root, filename)
                file_category = self._categorize_file(filepath)
                categorized[file_category.category].append(file_category)

        # Sort each category by filename
        for category in categorized:
            categorized[category].sort(key=lambda f: f.filename.lower())

        return categorized

    def _categorize_file(self, filepath: str) -> FileCategory:
        """
        Categorize a single file.

        Args:
            filepath: Path to file

        Returns:
            FileCategory object
        """
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        # Check if it's an active Python file
        if filepath in self.active_files:
            return FileCategory(filepath, 'active', 'In import chain')

        # Check if it's a Python file that's not active (orphaned)
        if ext == '.py':
            return FileCategory(filepath, 'orphaned', 'Python file not imported')

        # Check scripts
        if self._matches_patterns(filename, ext, self.file_categories_config.get('scripts', [])):
            return FileCategory(filepath, 'scripts', 'Script file')

        # Check outputs
        if self._matches_patterns(filename, ext, self.file_categories_config.get('outputs', [])):
            return FileCategory(filepath, 'outputs', 'Generated output file')

        # Check temp files
        if self._matches_patterns(filename, ext, self.file_categories_config.get('temp', [])):
            return FileCategory(filepath, 'temp', 'Temporary file')

        # Check shortcuts
        if self._matches_patterns(filename, ext, self.file_categories_config.get('shortcuts', [])):
            return FileCategory(filepath, 'shortcuts', 'Shortcut file')

        # Check duplicates
        if self._matches_patterns(filename, ext, self.file_categories_config.get('duplicates', [])):
            return FileCategory(filepath, 'duplicates', 'Duplicate or backup file')

        # Unknown / other files
        return FileCategory(filepath, 'unknown', 'Uncategorized file')

    def _matches_patterns(self, filename: str, ext: str, patterns: List[str]) -> bool:
        """
        Check if filename or extension matches any pattern.

        Args:
            filename: Name of file
            ext: File extension (with dot)
            patterns: List of patterns to match

        Returns:
            True if matches any pattern
        """
        for pattern in patterns:
            # Extension match
            if pattern.startswith('.') and ext == pattern:
                return True
            # Filename pattern match
            if fnmatch.fnmatch(filename, pattern):
                return True
            # Substring match (for patterns like " (1).")
            if not pattern.startswith('.') and not pattern.startswith('*'):
                if pattern in filename:
                    return True

        return False
