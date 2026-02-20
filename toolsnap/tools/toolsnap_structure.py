"""
ToolSnap Structure Analyzer
Outputs a timestamped tree view of the project structure.

Run: python toolsnap_structure.py
Output: toolsnap_structure_YYYYMMDD_HHMMSS.txt
"""

import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

TOOLSNAP_ROOT = Path("C:/toolsnap")
OUTPUT_DIR = TOOLSNAP_ROOT / "tools"

# Folders to skip entirely
SKIP_FOLDERS = {
    '__pycache__',
    '.git',
    '.gradle',
    '.idea',
    '.kotlin',
    '.cxx',
    '.venv',
    'venv',
    'node_modules',
    'build',
    'captures',
    'generated',
    'intermediates',
    'tmp',
    'kotlin-classes',
    'packaged_manifests',
}

# File extensions to skip
SKIP_EXTENSIONS = {
    '.pyc',
    '.pyo',
    '.class',
    '.dex',
    '.apk',
    '.aab',
    '.jar',
    '.so',
    '.o',
    '.exe',
    '.dll',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.webp',
    '.ico',
    '.ttf',
    '.otf',
    '.woff',
    '.woff2',
}

# Folders where we only show summary, not full contents
SUMMARIZE_FOLDERS = {
    'res',
}

# Max files to show in summarized folders before saying "+ N more"
SUMMARIZE_LIMIT = 5

# ============================================================================
# TREE GENERATION
# ============================================================================

def should_skip(name, is_dir):
    """Check if item should be skipped entirely."""
    if is_dir and name in SKIP_FOLDERS:
        return True
    if not is_dir and Path(name).suffix.lower() in SKIP_EXTENSIONS:
        return True
    return False

def generate_tree(root_path, prefix=""):
    """Generate tree structure as list of strings."""
    lines = []
    root = Path(root_path)

    try:
        items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return lines

    items = [i for i in items if not should_skip(i.name, i.is_dir())]

    for idx, item in enumerate(items):
        is_last_item = (idx == len(items) - 1)
        connector = "+--- " if is_last_item else "|--- "
        extension = "     " if is_last_item else "|    "

        if item.is_dir():
            lines.append(f"{prefix}{connector}{item.name}/")

            if item.name in SUMMARIZE_FOLDERS:
                try:
                    contents = list(item.iterdir())
                    contents = [c for c in contents if not should_skip(c.name, c.is_dir())]
                    file_count = len([c for c in contents if c.is_file()])
                    dir_count = len([c for c in contents if c.is_dir()])

                    dirs = sorted([c for c in contents if c.is_dir()], key=lambda x: x.name)
                    files = sorted([c for c in contents if c.is_file()], key=lambda x: x.name)[:SUMMARIZE_LIMIT]

                    for d in dirs:
                        lines.append(f"{prefix}{extension}|--- {d.name}/")

                    for f in files:
                        lines.append(f"{prefix}{extension}|    {f.name}")

                    remaining = file_count - len(files)
                    if remaining > 0:
                        lines.append(f"{prefix}{extension}|    ... +{remaining} more files")
                except PermissionError:
                    pass
            else:
                lines.extend(generate_tree(item, prefix + extension))
        else:
            lines.append(f"{prefix}{connector}{item.name}")

    return lines

def analyze_structure():
    """Generate and save structure analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"toolsnap_structure_{timestamp}.txt"

    lines = [
        "ToolSnap Structure Analysis",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Root: {TOOLSNAP_ROOT}",
        "=" * 60,
        "",
        str(TOOLSNAP_ROOT),
    ]

    tree_lines = generate_tree(TOOLSNAP_ROOT)
    lines.extend(tree_lines)

    # Summary stats
    lines.extend([
        "",
        "=" * 60,
        "Summary:",
    ])

    ext_counts = {}
    total_files = 0
    total_dirs = 0

    for root, dirs, files in os.walk(TOOLSNAP_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS]
        total_dirs += len(dirs)

        for f in files:
            ext = Path(f).suffix.lower() or '(no ext)'
            if ext not in SKIP_EXTENSIONS:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
                total_files += 1

    lines.append(f"  Total folders: {total_dirs}")
    lines.append(f"  Total files: {total_files}")
    lines.append("")
    lines.append("  Files by type:")

    for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"    {ext}: {count}")

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Structure saved to: {output_file}")
    print(f"Total: {total_dirs} folders, {total_files} files")

    return output_file

if __name__ == "__main__":
    analyze_structure()
