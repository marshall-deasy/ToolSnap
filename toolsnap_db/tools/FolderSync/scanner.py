"""
FolderSync Scanner
Scans folders and extracts metadata for comparison.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
from models import FolderInfo, ScanResult


def scan_folder_recursive(folder_path: Path) -> tuple[datetime, int, int]:
    """
    Recursively scan a folder to find newest file date, total size, and file count.
    
    Args:
        folder_path: Path to folder to scan
        
    Returns:
        (newest_modification_date, total_size_bytes, file_count)
    """
    if not folder_path.exists() or not folder_path.is_dir():
        return datetime.min, 0, 0
    
    newest_date = datetime.min
    total_size = 0
    file_count = 0
    
    try:
        for item in folder_path.rglob('*'):
            if item.is_file():
                try:
                    stat = item.stat()
                    file_date = datetime.fromtimestamp(stat.st_mtime)
                    file_size = stat.st_size
                    
                    if file_date > newest_date:
                        newest_date = file_date
                    
                    total_size += file_size
                    file_count += 1
                    
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
                    
    except (OSError, PermissionError):
        # If we can't read the directory, return what we have
        pass
    
    return newest_date, total_size, file_count


def scan_tools_folder(tools_path: Path) -> dict[str, FolderInfo]:
    """
    Scan a tools folder and return metadata for each tool subfolder.
    Automatically skips folders with .OLD_ in the name.
    
    Args:
        tools_path: Path to a tools folder (e.g., C:\\...\\trailboss\\tools)
        
    Returns:
        Dictionary mapping tool name to FolderInfo
    """
    results = {}
    
    if not tools_path.exists() or not tools_path.is_dir():
        return results
    
    try:
        # Get immediate subdirectories (each is a tool)
        for item in tools_path.iterdir():
            if item.is_dir():
                tool_name = item.name
                
                # Skip folders with .OLD_ in the name (renamed old versions)
                if '.OLD_' in tool_name:
                    continue
                
                # Scan this tool folder recursively
                newest_date, total_size, file_count = scan_folder_recursive(item)
                
                # Only include if we found files
                if file_count > 0:
                    folder_info = FolderInfo(
                        path=item,
                        newest_file_date=newest_date,
                        total_size=total_size,
                        file_count=file_count
                    )
                    results[tool_name] = folder_info
                    
    except (OSError, PermissionError):
        pass
    
    return results


def scan_multiple_locations(location_paths: list[Path]) -> ScanResult:
    """
    Scan multiple tools folders and build comparison data.
    
    Args:
        location_paths: List of paths to tools folders
        
    Returns:
        ScanResult containing all tools across all locations
    """
    result = ScanResult(location_paths=location_paths)
    
    # Scan each location
    for location_idx, location_path in enumerate(location_paths):
        tools_in_location = scan_tools_folder(location_path)
        
        # Add each tool to the result
        for tool_name, folder_info in tools_in_location.items():
            result.add_tool_location(tool_name, location_idx, folder_info)
    
    return result


def validate_folder_path(path: Path) -> tuple[bool, str]:
    """
    Validate that a folder path is suitable for comparison.
    
    Args:
        path: Path to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not path.exists():
        return False, "Path does not exist"
    
    if not path.is_dir():
        return False, "Path is not a folder"
    
    try:
        # Try to read the directory
        list(path.iterdir())
        return True, ""
    except PermissionError:
        return False, "Permission denied"
    except OSError as e:
        return False, f"Cannot access folder: {e}"


def get_folder_preview(path: Path, max_items: int = 5) -> list[str]:
    """
    Get a preview of tool folders in a location.
    
    Args:
        path: Path to tools folder
        max_items: Maximum number of items to preview
        
    Returns:
        List of tool folder names
    """
    preview = []
    
    try:
        items = [item.name for item in path.iterdir() if item.is_dir()]
        preview = sorted(items)[:max_items]
    except (OSError, PermissionError):
        pass
    
    return preview


def find_old_folders(location_paths: list[Path]) -> list[Path]:
    """
    Find all folders with .OLD_ in their name across all locations.
    
    Args:
        location_paths: List of paths to tools folders
        
    Returns:
        List of paths to .OLD folders
    """
    old_folders = []
    
    for location_path in location_paths:
        if not location_path.exists() or not location_path.is_dir():
            continue
        
        try:
            for item in location_path.iterdir():
                if item.is_dir() and '.OLD_' in item.name:
                    old_folders.append(item)
        except (OSError, PermissionError):
            continue
    
    return old_folders


def search_folders_by_name(
    search_root: Path,
    folder_name: str,
    max_depth: int = 3
) -> list[Path]:
    """
    Search for folders with a specific name.
    
    Args:
        search_root: Root path to search from (e.g., C:/)
        folder_name: Name of folders to find (e.g., 'tools')
        max_depth: Maximum depth to search
        
    Returns:
        List of matching folder paths, sorted alphabetically
    """
    found_folders = []
    seen = set()
    
    # Determine search strategy based on search_root
    if search_root == Path('C:/') or search_root == Path('C:\\'):
        # For C:\ root, use focused search in common locations
        common_locations = [
            'auto_trading',
            'Users',
            'projects',
            'dev',
            'code',
            'workspace',
            'Documents',
            'development',
            'repos',
            'src',
        ]
        
        search_paths = [search_root / loc for loc in common_locations]
    else:
        # For specific paths, search that path directly
        search_paths = [search_root]
    
    # Search each path
    for search_path in search_paths:
        if not search_path.exists() or not search_path.is_dir():
            continue
        
        try:
            # Search up to max_depth levels deep
            for depth in range(1, max_depth + 1):
                pattern = '/'.join(['*'] * depth)
                
                try:
                    for item in search_path.glob(pattern):
                        if item.is_dir() and item.name == folder_name:
                            # Resolve to avoid duplicates from symlinks
                            try:
                                resolved = item.resolve()
                                resolved_str = str(resolved)
                                
                                if resolved_str not in seen:
                                    seen.add(resolved_str)
                                    
                                    # Verify folder has subdirectories (not empty)
                                    try:
                                        has_subdirs = any(sub.is_dir() for sub in item.iterdir())
                                        if has_subdirs:
                                            found_folders.append(item)
                                    except (OSError, PermissionError):
                                        # Can't read contents, skip
                                        pass
                            except (OSError, PermissionError):
                                # Can't resolve, skip
                                pass
                                
                except (OSError, PermissionError):
                    # Can't access this depth level, continue to next
                    continue
                    
        except (OSError, PermissionError):
            # Can't access this location, continue to next
            continue
    
    return sorted(found_folders, key=lambda p: str(p).lower())
