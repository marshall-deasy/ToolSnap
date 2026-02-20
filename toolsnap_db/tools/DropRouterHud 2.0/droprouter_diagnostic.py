"""
droprouter_diagnostic.py - Diagnostic tool for DropRouterHud issues

Run this to check:
- Config loading
- Watch directory exists and has files
- File matching criteria
- What files would be processed
"""

import json
import sys
from pathlib import Path

def main():
    # Load config
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        print(f"ERROR: Config not found at {config_path}")
        sys.exit(1)
    
    with open(config_path) as f:
        cfg = json.load(f)
    
    # Resolve paths
    config_dir = config_path.parent
    project_root = (config_dir / cfg["project_root"]).resolve()
    watch_dir = Path(cfg.get("watch_dir", "~/Downloads")).expanduser().resolve()
    
    print("=" * 70)
    print("DROPROUTER DIAGNOSTIC")
    print("=" * 70)
    print(f"Config file:    {config_path}")
    print(f"Project root:   {project_root}")
    print(f"Watch dir:      {watch_dir}")
    print(f"Prefix:         {cfg['prefix']}")
    print(f"Extensions:     {', '.join(cfg.get('watched_extensions', []))}")
    print()
    
    # Check directories exist
    print("DIRECTORY STATUS:")
    print(f"  Project root exists: {project_root.exists()}")
    print(f"  Watch dir exists:    {watch_dir.exists()}")
    print()
    
    if not watch_dir.exists():
        print("ERROR: Watch directory doesn't exist!")
        return
    
    # List all files in watch directory
    all_files = list(watch_dir.glob("*"))
    all_files = [f for f in all_files if f.is_file()]
    
    print(f"FILES IN WATCH DIR: ({len(all_files)} total)")
    for f in sorted(all_files):
        print(f"  {f.name}")
    print()
    
    # Check which files match criteria
    prefix = cfg["prefix"].lower()
    extensions = set(cfg.get("watched_extensions", []))
    
    matching_files = []
    non_matching = []
    
    for f in all_files:
        matches_prefix = f.name.lower().startswith(prefix)
        matches_ext = f.suffix.lower() in extensions
        
        if matches_prefix and matches_ext:
            matching_files.append(f)
        else:
            reason = []
            if not matches_prefix:
                reason.append(f"prefix mismatch (need '{prefix}')")
            if not matches_ext:
                reason.append(f"extension mismatch (need one of {extensions})")
            non_matching.append((f, ", ".join(reason)))
    
    print(f"MATCHING FILES: ({len(matching_files)})")
    if matching_files:
        for f in sorted(matching_files):
            print(f"  ✓ {f.name}")
    else:
        print("  (none)")
    print()
    
    if non_matching:
        print(f"NON-MATCHING FILES: ({len(non_matching)})")
        for f, reason in sorted(non_matching):
            print(f"  ✗ {f.name} - {reason}")
        print()
    
    # Check ignore list
    ignore_path = project_root / "tools" / "droprouter_ignore.json"
    ignore_list = set()
    if ignore_path.exists():
        try:
            with open(ignore_path) as f:
                ignore_list = set(json.load(f))
            print(f"IGNORE LIST: ({len(ignore_list)} items)")
            for item in sorted(ignore_list):
                print(f"  🚫 {item}")
            print()
        except Exception as e:
            print(f"ERROR reading ignore list: {e}")
            print()
    
    # Check for ignored matches
    ignored_matches = [f for f in matching_files if f.name in ignore_list]
    if ignored_matches:
        print(f"MATCHING BUT IGNORED: ({len(ignored_matches)})")
        for f in sorted(ignored_matches):
            print(f"  ⚠️  {f.name}")
        print()
    
    # Final summary
    processable = [f for f in matching_files if f.name not in ignore_list]
    print("=" * 70)
    print("SUMMARY:")
    print(f"  Total files in watch dir:  {len(all_files)}")
    print(f"  Matching prefix+extension: {len(matching_files)}")
    print(f"  In ignore list:            {len(ignored_matches)}")
    print(f"  Should be processed:       {len(processable)}")
    print("=" * 70)
    
    if processable:
        print("\nThese files SHOULD be picked up by DropRouterHud:")
        for f in sorted(processable):
            print(f"  → {f.name}")
    else:
        print("\nNo files are currently eligible for processing.")
        if not matching_files:
            print(f"  Tip: Make sure files start with '{cfg['prefix']}' and have extension in {extensions}")

if __name__ == "__main__":
    main()
