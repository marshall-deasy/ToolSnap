"""
Code file discovery and searching for CodeGrep.

Recursively scans project root for code files and provides search functionality.
"""

import os
import re
import fnmatch
from typing import List, Set, Dict, Tuple


class SearchResult:
    """Represents a single search match with context."""

    def __init__(
        self,
        file_path: str,
        relative_path: str,
        line_number: int,
        line_text: str,
        context_before: List[str],
        context_after: List[str],
    ):
        """
        Initialize search result.

        Args:
            file_path: Absolute path to file
            relative_path: Path relative to project root
            line_number: Line number of match (1-indexed)
            line_text: The matching line
            context_before: Lines before the match
            context_after: Lines after the match
        """
        self.file_path = file_path
        self.relative_path = relative_path
        self.line_number = line_number
        self.line_text = line_text
        self.context_before = context_before
        self.context_after = context_after

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "line_number": self.line_number,
            "line_text": self.line_text,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


class CodeScanner:
    """Scans project directory tree for code files and provides search."""

    def __init__(
        self,
        project_root: str,
        file_patterns: List[str],
        exclude_dirs: Set[str],
        exclude_files: List[str],
        context_lines: int,
        max_results: int,
    ):
        """
        Initialize code scanner.

        Args:
            project_root: Root directory to scan
            file_patterns: List of filename patterns (e.g., ["*.py"])
            exclude_dirs: Set of directory names to skip
            exclude_files: List of file patterns to skip
            context_lines: Number of lines before/after match
            max_results: Maximum results to return
        """
        self.project_root = project_root
        self.file_patterns = file_patterns
        self.exclude_dirs = exclude_dirs
        self.exclude_files = exclude_files
        self.context_lines = context_lines
        self.max_results = max_results
        self._file_cache = None

    def get_code_files(self, force_refresh: bool = False) -> List[str]:
        """
        Get list of all code files in project.

        Args:
            force_refresh: If True, bypass cache and rescan

        Returns:
            List of absolute file paths
        """
        if self._file_cache is not None and not force_refresh:
            return self._file_cache

        code_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Filter out excluded directories in-place
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            # Check each file against patterns
            for filename in files:
                if self._matches_include_pattern(filename) and not self._matches_exclude_pattern(filename):
                    absolute_path = os.path.join(root, filename)
                    code_files.append(absolute_path)

        self._file_cache = sorted(code_files)
        return self._file_cache

    def _matches_include_pattern(self, filename: str) -> bool:
        """Check if filename matches any include pattern."""
        return any(fnmatch.fnmatch(filename, pattern) for pattern in self.file_patterns)

    def _matches_exclude_pattern(self, filename: str) -> bool:
        """Check if filename matches any exclude pattern."""
        return any(fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_files)

    def search(
        self,
        query: str,
        use_regex: bool = False,
        case_sensitive: bool = False,
        whole_word: bool = False,
    ) -> List[SearchResult]:
        """
        Search all code files for query.

        Args:
            query: Search query
            use_regex: If True, treat query as regex
            case_sensitive: If True, case-sensitive search
            whole_word: If True, match whole words only

        Returns:
            List of SearchResult objects
        """
        if not query:
            return []

        results = []
        code_files = self.get_code_files()

        # Compile search pattern
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(query, flags)
            except re.error:
                return []
        else:
            # Escape special regex characters for plain text search
            escaped_query = re.escape(query)
            if whole_word:
                escaped_query = r'\b' + escaped_query + r'\b'
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(escaped_query, flags)

        # Search each file
        for file_path in code_files:
            file_results = self._search_file(file_path, pattern)
            results.extend(file_results)

            # Stop if we hit max results
            if len(results) >= self.max_results:
                results = results[:self.max_results]
                break

        return results

    def _search_file(self, file_path: str, pattern: re.Pattern) -> List[SearchResult]:
        """
        Search a single file for pattern.

        Args:
            file_path: Path to file
            pattern: Compiled regex pattern

        Returns:
            List of SearchResult objects for this file
        """
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            # Search each line
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    # Get context lines
                    context_before = self._get_context_before(lines, line_num)
                    context_after = self._get_context_after(lines, line_num)

                    relative_path = os.path.relpath(file_path, self.project_root)

                    result = SearchResult(
                        file_path=file_path,
                        relative_path=relative_path,
                        line_number=line_num,
                        line_text=line.rstrip('\n\r'),
                        context_before=context_before,
                        context_after=context_after,
                    )
                    results.append(result)

        except Exception:
            # Skip files that can't be read
            pass

        return results

    def _get_context_before(self, lines: List[str], line_num: int) -> List[str]:
        """Get context lines before the match."""
        start_idx = max(0, line_num - self.context_lines - 1)
        end_idx = line_num - 1
        return [line.rstrip('\n\r') for line in lines[start_idx:end_idx]]

    def _get_context_after(self, lines: List[str], line_num: int) -> List[str]:
        """Get context lines after the match."""
        start_idx = line_num
        end_idx = min(len(lines), line_num + self.context_lines)
        return [line.rstrip('\n\r') for line in lines[start_idx:end_idx]]

    def get_file_stats(self) -> Dict[str, int]:
        """
        Get statistics about discovered code files.

        Returns:
            Dictionary with file counts by extension
        """
        code_files = self.get_code_files()
        stats = {}

        for file_path in code_files:
            ext = os.path.splitext(file_path)[1] or 'no_extension'
            stats[ext] = stats.get(ext, 0) + 1

        return stats
