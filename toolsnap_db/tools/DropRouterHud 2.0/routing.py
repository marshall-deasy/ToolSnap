"""
routing.py - File routing logic for DropRouterHud.

Determines where files should go based on:
- Pattern matching for single files (routing_rules)
- Path analysis for zip contents (structure detection)

Single source of truth for all routing decisions.
"""

import re
from pathlib import Path
from typing import List, Optional, Set, Tuple


def get_suggested_destination(filename: str, cfg: dict) -> Optional[str]:
    """
    Match a single file against routing_rules from config.
    
    Args:
        filename: Name of file to route
        cfg: Config dict with routing_rules
        
    Returns:
        Destination subdirectory string, or None if no match
        
    Example:
        get_suggested_destination("script.bat", cfg) → "tools"
        get_suggested_destination("unknown.xyz", cfg) → None
    """
    for rule in cfg.get("routing_rules", []):
        pattern = rule.get("pattern")
        if not pattern:
            continue
            
        if re.match(pattern, filename, re.IGNORECASE):
            return rule.get("destination")
    
    return None


def get_structure_destination(
    zip_path: str,
    strip_wrapper: Optional[str],
    project_root: Path,
    known_folders: Optional[Set[str]] = None,
) -> Tuple[str, bool]:
    """
    Derive destination from zip entry's internal path.
    
    Trust the path if:
      1. The directory already exists on disk, OR
      2. The top-level folder matches a known root folder.
    
    This prevents flagging nested paths like shared/api/ that haven't
    been created yet but belong to a recognized project subtree.
    
    Args:
        zip_path: Internal path from zip file (e.g., "core/strategy.py")
        strip_wrapper: Optional wrapper folder to strip
        project_root: Project root directory
        known_folders: Set of recognized top-level folders (lowercase)
        
    Returns:
        Tuple of (relative_dir, is_flagged)
        - relative_dir: Path relative to project root, or "ROOT"
        - is_flagged: True if path unrecognized (goes to Downloads)
        
    Examples:
        "core/engine.py" → ("core", False) if core/ is known
        "unknown/file.py" → ("unknown", True) - flagged
        "readme.txt" → ("ROOT", False) - root-level file
    """
    if known_folders is None:
        known_folders = set()
    
    # Normalize path
    path = zip_path.replace("\\", "/")
    
    # Strip wrapper if present
    if strip_wrapper and path.startswith(strip_wrapper + "/"):
        path = path[len(strip_wrapper) + 1:]
    
    # Root-level file (no subdirectory)
    if "/" not in path:
        return ("ROOT", False)
    
    # Extract directory path
    parts = path.split("/")
    top_folder = parts[0].lower()
    dir_path = "/".join(parts[:-1])
    
    # Check if top-level folder is recognized
    if top_folder in known_folders:
        return (dir_path, False)
    
    # Check if directory exists on disk
    full_path = project_root / dir_path
    if full_path.exists() and full_path.is_dir():
        return (dir_path, False)
    
    # Unrecognized path - flag it
    return (dir_path, True)


def validate_routing_rules(rules: List[dict]) -> List[str]:
    """
    Validate routing rule patterns for common errors.
    
    Args:
        rules: List of routing rule dicts with 'pattern' and 'destination'
        
    Returns:
        List of error messages (empty if all valid)
        
    Example:
        rules = [
            {"pattern": ".*\\.py$", "destination": "core"},
            {"pattern": "[invalid(", "destination": "bad"}
        ]
        validate_routing_rules(rules) → ["Rule 2: Invalid regex: ..."]
    """
    errors = []
    
    for i, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            errors.append(f"Rule {i}: Not a dict")
            continue
            
        pattern = rule.get("pattern")
        destination = rule.get("destination")
        
        # Check required fields
        if not pattern:
            errors.append(f"Rule {i}: Missing 'pattern' field")
            continue
        if not destination:
            errors.append(f"Rule {i}: Missing 'destination' field")
            continue
        
        # Validate regex syntax
        try:
            re.compile(pattern)
        except re.error as e:
            errors.append(f"Rule {i}: Invalid regex '{pattern}': {e}")
            continue
        
        # Check for common mistakes
        if not pattern.startswith(".*"):
            errors.append(
                f"Rule {i}: Pattern '{pattern}' should start with '.*' "
                "to match full filename"
            )
        
        if "." in pattern and "\\." not in pattern:
            errors.append(
                f"Rule {i}: Pattern '{pattern}' has unescaped dot - "
                "use '\\.' for literal dot"
            )
    
    return errors
