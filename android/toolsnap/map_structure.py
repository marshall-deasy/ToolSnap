"""
map_structure.py — Portable directory structure mapper.
Assumes it lives in (or is run from) the project root.
Outputs a datetime-stamped structure snapshot for diffing across iterations.

Usage:
    python map_structure.py                        # map current directory
    python map_structure.py C:\\Projects\\MyApp      # map specified directory
    python map_structure.py --depth 3              # limit traversal depth
    python map_structure.py --dirs-only            # directories only
    python map_structure.py --output-dir C:\\logs   # save snapshot elsewhere
"""

import os
import re
import sys
import argparse
from datetime import datetime

# ---------------------------------------------------------------------------
# Config — adjust these, not the logic below
# ---------------------------------------------------------------------------

EXCLUDE_DIRS = {
    "__pycache__", ".git", ".vscode", ".idea",
    "node_modules", ".mypy_cache", ".pytest_cache",
    "venv", ".venv", "env", ".env", ".tox",
    "dist", "build", "egg-info",
}

EXCLUDE_SUFFIXES = (".egg-info",)

# Pattern used for both naming output files and excluding them from the tree
STRUCTURE_FILE_PATTERN = re.compile(r"^.+_STRUCTURE(_\d{8}_\d{6})?\.txt$", re.IGNORECASE)

TIMESTAMP_FMT = "%Y%m%d_%H%M%S"

# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------

def map_tree(root, prefix="", depth=None, current_depth=0, dirs_only=False):
    """Recursively build a list of tree-formatted lines for *root*.

    Returns:
        tuple: (lines, file_count, dir_count)
    """
    lines = []
    file_count = 0
    dir_count = 0

    try:
        entries = sorted(
            os.listdir(root),
            key=lambda e: (not os.path.isdir(os.path.join(root, e)), e.lower()),
        )
    except PermissionError:
        lines.append(f"{prefix}[ACCESS DENIED]")
        return lines, 0, 0

    # Filter
    filtered = []
    for e in entries:
        if e in EXCLUDE_DIRS:
            continue
        if any(e.endswith(s) for s in EXCLUDE_SUFFIXES):
            continue
        if STRUCTURE_FILE_PATTERN.match(e):
            continue
        full = os.path.join(root, e)
        if dirs_only and not os.path.isdir(full):
            continue
        filtered.append(e)

    for i, entry in enumerate(filtered):
        path = os.path.join(root, entry)
        is_last = i == len(filtered) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        if os.path.isdir(path):
            dir_count += 1
            lines.append(f"{prefix}{connector}{entry}/")

            if depth is not None and current_depth + 1 >= depth:
                lines.append(f"{prefix}{extension}└── ...")
            else:
                sub_lines, sub_files, sub_dirs = map_tree(
                    path, prefix + extension, depth, current_depth + 1, dirs_only,
                )
                lines.extend(sub_lines)
                file_count += sub_files
                dir_count += sub_dirs
        else:
            file_count += 1
            lines.append(f"{prefix}{connector}{entry}")

    return lines, file_count, dir_count

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Map a directory structure to a datetime-stamped text file.",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Root directory to map (default: current directory)",
    )
    parser.add_argument(
        "--depth", type=int, default=None,
        help="Max depth to traverse",
    )
    parser.add_argument(
        "--dirs-only", action="store_true",
        help="Show directories only",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to save the snapshot (default: mapped root)",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.path)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a valid directory.")
        sys.exit(1)

    # Build tree
    root_name = os.path.basename(root)
    tree_lines, file_count, dir_count = map_tree(
        root, depth=args.depth, dirs_only=args.dirs_only,
    )

    header = f"{root_name}/"
    footer = f"\n[ Dirs: {dir_count} | Files: {file_count} ]"
    output = "\n".join([header] + tree_lines) + footer

    # Write snapshot
    stamp = datetime.now().strftime(TIMESTAMP_FMT)
    filename = f"{root_name.upper()}_STRUCTURE_{stamp}.txt"

    out_dir = os.path.abspath(args.output_dir) if args.output_dir else root
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(output)
    print(f"\n--- Saved to: {out_path} ---")


if __name__ == "__main__":
    main()
