"""
zip_handler.py - Zip file operations for DropRouterHud.

Handles:
- Zip file reading and validation
- Structure detection (wrapper folders, known paths)
- Extraction with path-based routing

All zip operations are in this module.
"""

import zipfile
from pathlib import Path
from typing import List, Optional, Set, Tuple

from routing import get_structure_destination


def get_zip_files(filepath: Path) -> List[str]:
    """
    Return list of non-directory entries in a zip.
    
    Args:
        filepath: Path to zip file
        
    Returns:
        List of file paths (directories excluded)
        Empty list if zip is unreadable or empty
        
    Example:
        get_zip_files("archive.zip") → ["core/engine.py", "readme.txt"]
    """
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            return [f for f in zf.namelist() if not f.endswith("/")]
    except Exception:
        return []


def detect_zip_mode(
    zip_contents: List[str], 
    known_folders: Set[str],
) -> Tuple[str, Optional[str]]:
    """
    Detect whether zip uses structure-based routing.
    
    Analyzes zip internal paths to determine if they match project structure:
    - Direct match: zip roots ARE project folders (e.g., core/, ui/, tools/)
    - Wrapper match: single root folder contains project folders
    - Flat: no recognized structure
    
    Args:
        zip_contents: List of file paths from zip
        known_folders: Set of recognized project folders (lowercase)
        
    Returns:
        Tuple of (mode, wrapper)
        - mode: "structure" or "flat"
        - wrapper: Wrapper folder name (if found) or None
        
    Examples:
        ["core/engine.py", "ui/dashboard.py"] → ("structure", None)
        ["mybot/core/engine.py", "mybot/ui/dashboard.py"] → ("structure", "mybot")
        ["file1.py", "file2.py"] → ("flat", None)
    """
    if not zip_contents:
        return ("flat", None)
    
    # Extract root-level folders from zip
    root_folders = set()
    for path in zip_contents:
        parts = path.replace("\\", "/").split("/")
        if parts and parts[0]:
            root_folders.add(parts[0].lower())
    
    # Direct match - zip roots ARE project folders
    if root_folders & known_folders:
        return ("structure", None)
    
    # Wrapper check - single root containing known folders
    if len(root_folders) == 1:
        wrapper = list(root_folders)[0]
        nested = set()
        
        for path in zip_contents:
            parts = path.replace("\\", "/").split("/")
            if len(parts) > 1 and parts[1]:
                nested.add(parts[1].lower())
        
        if nested & known_folders:
            # Recover actual case of wrapper folder name
            for path in zip_contents:
                parts = path.replace("\\", "/").split("/")
                if parts[0].lower() == wrapper:
                    return ("structure", parts[0])
    
    return ("flat", None)


def extract_zip_structure(
    zip_filepath: Path,
    wrapper: Optional[str],
    cfg: dict,
) -> Tuple[int, List[str]]:
    """
    Extract zip preserving internal structure, routing by path.
    
    Each file is routed based on its internal path:
    - Recognized paths → extract to project location
    - Unrecognized paths → extract to Downloads (flagged)
    
    Args:
        zip_filepath: Path to zip file
        wrapper: Optional wrapper folder to strip from paths
        cfg: Config dict with project_root and known_root_folders
        
    Returns:
        Tuple of (extracted_count, flagged_files)
        - extracted_count: Number of files successfully extracted
        - flagged_files: List of filenames sent to Downloads
        
    Example:
        extract_zip_structure("bot.zip", None, cfg)
        → (15, ["unknown.txt", "bad/path.py"])
    """
    project_root = cfg["project_root"]
    known_folders = cfg["known_root_folders"]
    downloads = cfg["watch_dir"]
    
    extracted_count = 0
    flagged_files = []
    
    try:
        with zipfile.ZipFile(zip_filepath, "r") as zf:
            for entry in zf.namelist():
                # Skip directories
                if entry.endswith("/"):
                    continue
                
                # Determine destination
                dest_dir, flagged = get_structure_destination(
                    entry, wrapper, project_root, known_folders
                )
                
                # Extract filename
                parts = entry.replace("\\", "/").split("/")
                filename = parts[-1]
                
                if flagged:
                    # Unrecognized path → Downloads
                    dest_path = downloads / filename
                    flagged_files.append(filename)
                else:
                    # Recognized path → project location
                    if dest_dir == "ROOT":
                        dest_path = project_root / filename
                    else:
                        dest_path = project_root / dest_dir / filename
                
                # Create parent directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Overwrite if exists
                if dest_path.exists():
                    dest_path.unlink()
                
                # Extract file
                with zf.open(entry) as source:
                    with open(dest_path, "wb") as target:
                        target.write(source.read())
                
                extracted_count += 1
        
        # Delete zip after successful extraction
        zip_filepath.unlink()
        
        # Console output
        if flagged_files:
            print(f"  📦 {zip_filepath.name}: {extracted_count} files extracted")
            print(f"     ⚠️  {len(flagged_files)} flagged → Downloads")
        else:
            print(f"  📦 {zip_filepath.name}: {extracted_count} files extracted, zip deleted")
    
    except Exception as e:
        print(f"  ERROR extracting {zip_filepath.name}: {e}")
        return (0, [])
    
    return (extracted_count, flagged_files)
