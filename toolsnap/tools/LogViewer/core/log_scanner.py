"""
Log file discovery and categorization for LogViewer.

Recursively scans project root for log files and organizes them.
"""

import os
import fnmatch
from datetime import datetime
from typing import List, Dict, Set


class LogFile:
    """Represents a discovered log file with metadata."""

    def __init__(self, absolute_path: str, relative_path: str, root: str):
        """
        Initialize log file metadata.

        Args:
            absolute_path: Full path to log file
            relative_path: Path relative to project root
            root: Project root directory
        """
        self.absolute_path = absolute_path
        self.relative_path = relative_path
        self.root = root
        self.name = os.path.basename(absolute_path)
        self.directory = os.path.dirname(relative_path)
        self.size_bytes = 0
        self.modified_time = None
        self._update_metadata()

    def _update_metadata(self) -> None:
        """Update file size and modification time."""
        try:
            stat = os.stat(self.absolute_path)
            self.size_bytes = stat.st_size
            self.modified_time = datetime.fromtimestamp(stat.st_mtime)
        except OSError:
            pass

    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_display(self) -> str:
        """Human-readable file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_mb:.1f} MB"

    @property
    def modified_display(self) -> str:
        """Human-readable modification time."""
        if not self.modified_time:
            return "Unknown"

        now = datetime.now()
        delta = now - self.modified_time

        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())} sec ago"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)} min ago"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)} hr ago"
        else:
            return self.modified_time.strftime("%Y-%m-%d %H:%M")

    def refresh(self) -> None:
        """Refresh file metadata (size, modified time)."""
        self._update_metadata()


class LogScanner:
    """Scans project directory tree for log files."""

    def __init__(
        self,
        project_root: str,
        log_patterns: List[str],
        exclude_dirs: Set[str],
        max_size_mb: int,
    ):
        """
        Initialize log scanner.

        Args:
            project_root: Root directory to scan
            log_patterns: List of filename patterns (e.g., ["*.log"])
            exclude_dirs: Set of directory names to skip
            max_size_mb: Maximum file size in MB to include
        """
        self.project_root = project_root
        self.log_patterns = log_patterns
        self.exclude_dirs = exclude_dirs
        self.max_size_mb = max_size_mb

    def scan(self) -> List[LogFile]:
        """
        Scan project root for log files.

        Returns:
            List of LogFile objects sorted by directory then name
        """
        log_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Filter out excluded directories in-place
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            # Check each file against patterns
            for filename in files:
                if self._matches_pattern(filename):
                    absolute_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(absolute_path, self.project_root)

                    # Create LogFile object
                    log_file = LogFile(absolute_path, relative_path, self.project_root)

                    # Skip if too large
                    if log_file.size_mb > self.max_size_mb:
                        continue

                    log_files.append(log_file)

        # Sort by directory then name
        log_files.sort(key=lambda f: (f.directory, f.name.lower()))
        return log_files

    def _matches_pattern(self, filename: str) -> bool:
        """
        Check if filename matches any log pattern.

        Args:
            filename: Name of file to check

        Returns:
            True if matches any pattern, False otherwise
        """
        return any(fnmatch.fnmatch(filename, pattern) for pattern in self.log_patterns)

    def group_by_directory(self, log_files: List[LogFile]) -> Dict[str, List[LogFile]]:
        """
        Group log files by their directory.

        Args:
            log_files: List of LogFile objects

        Returns:
            Dictionary mapping directory path to list of LogFiles
        """
        grouped = {}
        for log_file in log_files:
            directory = log_file.directory or "."
            if directory not in grouped:
                grouped[directory] = []
            grouped[directory].append(log_file)
        return grouped
