"""
map_structure.py — Portable, self-aware directory structure mapper.

Auto-detects project root (2 levels up by default) and maps entire structure.
Saves timestamped output to project root.

Usage:
    python map_structure.py                        # map project root (auto)
    python map_structure.py C:\Projects\MyApp      # map specified dir
    python map_structure.py --pick                 # show folder picker
    python map_structure.py --depth 3              # limit depth
    python map_structure.py --dirs-only            # directories only
"""

import os
import sys
import argparse
from datetime import datetime

from core import Config, PathResolver, TreeBuilder


# ---------------------------------------------------------------------------
# Self-awareness — where am I?
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
TIMESTAMP_FMT = "%Y%m%d_%H%M%S"


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main():
    """Main entry point for directory structure mapping."""
    parser = argparse.ArgumentParser(
        description="Map directory structure to timestamped text file.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Root directory to map (default: auto-detect project root)",
    )
    parser.add_argument(
        "--pick",
        action="store_true",
        help="Show folder picker GUI instead of auto-detecting",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Maximum depth to traverse",
    )
    parser.add_argument(
        "--dirs-only",
        action="store_true",
        help="Show only directories, no files",
    )
    args = parser.parse_args()

    # Load configuration
    config = Config(CONFIG_PATH)

    # Initialize path resolver
    path_resolver = PathResolver(SCRIPT_DIR, config.levels_up_to_root)

    # Determine target directory to map
    target_dir = _resolve_target_directory(args, path_resolver)
    if not target_dir:
        print("No folder selected. Exiting.")
        sys.exit(0)

    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a valid directory.")
        sys.exit(1)

    # Remember this directory
    path_resolver.save_last_dir(target_dir)

    # Build the tree
    tree_builder = TreeBuilder(
        exclude_dirs=config.exclude_dirs,
        exclude_suffixes=config.exclude_suffixes,
        structure_pattern=config.structure_file_pattern,
    )

    root_name = os.path.basename(target_dir)
    tree_lines, file_count, dir_count = tree_builder.build_tree(
        target_dir,
        depth=args.depth,
        dirs_only=args.dirs_only,
    )

    # Format output
    output = tree_builder.format_output(
        root_name,
        tree_lines,
        file_count,
        dir_count,
    )

    # Save to project root (2 levels up from script)
    project_root = path_resolver.get_project_root()
    output_path = _save_output(project_root, root_name, output)

    # Display results
    print(output)
    print(f"\n--- Saved to: {output_path} ---")


def _resolve_target_directory(args, path_resolver: PathResolver) -> str | None:
    """
    Determine which directory to map based on arguments.

    Args:
        args: Parsed command line arguments
        path_resolver: PathResolver instance

    Returns:
        Absolute path to directory to map, or None if cancelled
    """
    # Explicit path provided
    if args.path:
        return os.path.abspath(args.path)

    # Picker requested
    if args.pick:
        last_dir = path_resolver.load_last_dir()
        picked = path_resolver.pick_folder(last_dir)
        return os.path.abspath(picked) if picked else None

    # Default: auto-detect project root
    return path_resolver.get_project_root()


def _save_output(project_root: str, root_name: str, content: str) -> str:
    """
    Save output to timestamped file in project root.

    Args:
        project_root: Project root directory
        root_name: Name of mapped directory
        content: Tree content to save

    Returns:
        Path to saved file
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FMT)
    filename = f"{root_name.upper()}_STRUCTURE_{timestamp}.txt"
    output_path = os.path.join(project_root, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


if __name__ == "__main__":
    main()
