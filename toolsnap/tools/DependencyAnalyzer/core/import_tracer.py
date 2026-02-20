"""
Import tracing for DependencyAnalyzer.

Uses Python AST to trace all imports recursively from entry points.
"""

import ast
import os
from typing import Set, List, Optional


class ImportTracer:
    """Traces Python imports to find all active files."""

    def __init__(self, target_folder: str, exclude_dirs: Set[str]):
        """
        Initialize import tracer.

        Args:
            target_folder: Root folder to analyze
            exclude_dirs: Set of directory names to exclude
        """
        self.target_folder = target_folder
        self.exclude_dirs = exclude_dirs
        self._visited = set()
        self._active_files = set()

    def trace_from_entry_points(self, entry_points: List[str]) -> Set[str]:
        """
        Trace all imports from given entry points.

        Args:
            entry_points: List of Python file paths to start from

        Returns:
            Set of absolute paths to all active Python files
        """
        self._visited.clear()
        self._active_files.clear()

        # Add entry points themselves
        for entry_point in entry_points:
            if os.path.isfile(entry_point):
                self._active_files.add(entry_point)
                self._trace_file(entry_point)

        return self._active_files.copy()

    def _trace_file(self, filepath: str) -> None:
        """
        Recursively trace imports from a single file.

        Args:
            filepath: Path to Python file to trace
        """
        # Avoid infinite loops
        if filepath in self._visited:
            return

        self._visited.add(filepath)

        # Parse the file and find imports
        imports = self._parse_imports(filepath)

        # Resolve each import to a file path
        for import_info in imports:
            resolved = self._resolve_import(filepath, import_info)
            if resolved and resolved not in self._active_files:
                self._active_files.add(resolved)
                # Recursively trace this file
                self._trace_file(resolved)

    def _parse_imports(self, filepath: str) -> List[dict]:
        """
        Parse import statements from a Python file.

        Args:
            filepath: Path to Python file

        Returns:
            List of import information dicts
        """
        imports = []

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ast.parse(content, filename=filepath)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # import X, Y
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'level': 0,
                        })

                elif isinstance(node, ast.ImportFrom):
                    # from X import Y
                    module = node.module or ''
                    imports.append({
                        'type': 'from',
                        'module': module,
                        'level': node.level,  # For relative imports
                    })

        except Exception:
            # Syntax errors, encoding issues, etc. - skip this file
            pass

        return imports

    def _resolve_import(self, from_file: str, import_info: dict) -> Optional[str]:
        """
        Resolve an import to an actual file path.

        Args:
            from_file: File doing the importing
            import_info: Import information dict

        Returns:
            Absolute path to imported file, or None if not found
        """
        module = import_info['module']
        level = import_info['level']

        # Handle relative imports
        if level > 0:
            # Relative import like: from . import X or from .. import Y
            current_dir = os.path.dirname(from_file)
            for _ in range(level - 1):
                current_dir = os.path.dirname(current_dir)

            # Try module as file or package
            if module:
                module_parts = module.split('.')
                search_path = os.path.join(current_dir, *module_parts)
            else:
                search_path = current_dir

            resolved = self._find_module_file(search_path)
            if resolved:
                return resolved

        # Handle absolute imports
        else:
            module_parts = module.split('.')

            # Try from target folder root
            search_path = os.path.join(self.target_folder, *module_parts)
            resolved = self._find_module_file(search_path)
            if resolved:
                return resolved

        return None

    def _find_module_file(self, search_path: str) -> Optional[str]:
        """
        Find the actual Python file for a module path.

        Args:
            search_path: Base path to search

        Returns:
            Absolute path to .py file, or None if not found
        """
        # Check if path is excluded
        for part in search_path.split(os.sep):
            if part in self.exclude_dirs:
                return None

        # Try as direct file
        if search_path.endswith('.py'):
            if os.path.isfile(search_path):
                return search_path
        else:
            py_file = search_path + '.py'
            if os.path.isfile(py_file):
                return py_file

        # Try as package (__init__.py)
        if os.path.isdir(search_path):
            init_file = os.path.join(search_path, '__init__.py')
            if os.path.isfile(init_file):
                return init_file

        return None
