"""
map_structure.py — Portable directory structure mapper.
Run from any folder or pass a path as an argument.
Outputs ROOT_NAME_STRUCTURE.txt in the same directory.

Usage:
    python map_structure.py              # maps current directory
    python map_structure.py C:\Projects  # maps specified directory
    python map_structure.py --depth 3    # limit depth
    python map_structure.py --dirs-only  # directories only
"""

import os
import sys
import argparse

EXCLUDE = {
    "__pycache__", ".git", ".vscode", ".idea",
    "node_modules", ".mypy_cache", ".pytest_cache",
    "venv", ".venv", "env", ".env", ".tox", "dist",
    "build", "egg-info",
}


def map_tree(root, prefix="", depth=None, current_depth=0, dirs_only=False):
    lines = []
    try:
        entries = sorted(os.listdir(root), key=lambda e: (not os.path.isdir(os.path.join(root, e)), e.lower()))
    except PermissionError:
        lines.append(f"{prefix}[ACCESS DENIED]")
        return lines

    if dirs_only:
        entries = [e for e in entries if os.path.isdir(os.path.join(root, e))]

    entries = [e for e in entries if e not in EXCLUDE and not e.endswith(".egg-info")]

    for i, entry in enumerate(entries):
        path = os.path.join(root, entry)
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry}")

        if os.path.isdir(path):
            if depth is not None and current_depth + 1 >= depth:
                extension = "    " if is_last else "│   "
                lines.append(f"{prefix}{extension}└── ...")
            else:
                extension = "    " if is_last else "│   "
                lines.extend(map_tree(path, prefix + extension, depth, current_depth + 1, dirs_only))

    return lines


def main():
    parser = argparse.ArgumentParser(description="Map a directory structure to a text file.")
    parser.add_argument("path", nargs="?", default=".", help="Root directory to map (default: current directory)")
    parser.add_argument("--depth", type=int, default=None, help="Max depth to traverse")
    parser.add_argument("--dirs-only", action="store_true", help="Show directories only")
    args = parser.parse_args()

    root = os.path.abspath(args.path)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a valid directory.")
        sys.exit(1)

    root_name = os.path.basename(root)
    tree_lines = [f"{root_name}/"] + map_tree(root, depth=args.depth, dirs_only=args.dirs_only)
    output = "\n".join(tree_lines)

    out_file = os.path.join(root, f"{root_name.upper()}_STRUCTURE.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(output)
    print(f"\n--- Saved to: {out_file} ---")


if __name__ == "__main__":
    main()
