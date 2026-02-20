"""
droprouterhud.py - DropRouterHud main orchestrator.
Version 2.0 - Modular architecture, pure PySide6

Watches Downloads for files prefixed with a project tag, routes them
into the correct project directory using config-driven rules.

ZIP files:
  ALL zips show tree preview dialog.
  Files with recognized paths → extract to those paths.
  Files with unrecognized paths → flagged (yellow warning), sent to Downloads.
  User can accept or reject the entire zip.

Single files:
  Pattern-matched via routing_rules → moved to destination.
  Unmatched → popup with Ignore Once / Always Ignore.

Run: python droprouterhud.py
     python droprouterhud.py --config path/to/config.json
"""

VERSION = "2.0"

import argparse
import json
import os
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from dialogs import ZipTreeDialog, UnmatchedFilePopup
from routing import get_suggested_destination, get_structure_destination
from zip_handler import get_zip_files, detect_zip_mode, extract_zip_structure

# Optional HUD support
try:
    from instance_manager import InstanceManager
    from hud_overlay import create_hud_app
    HUD_AVAILABLE = True
except ImportError:
    HUD_AVAILABLE = False
    print("⚠️  HUD not available (install PySide6 and psutil for overlay)")


# ============================================================================
# PROJECT DISCOVERY
# ============================================================================

def discover_project_name() -> str:
    """
    Auto-discover project/bot name from directory structure.
    Assumes structure: .../botname/tools/DropRouterHud/droprouterhud.py
    Returns the folder name 2 levels up from 'tools' folder (raw, no formatting).
    """
    script_dir = Path(__file__).parent  # DropRouterHud
    tools_dir = script_dir.parent        # tools
    bot_dir = tools_dir.parent           # botname (trailboss, mr_bot, etc.)
    return bot_dir.name


# ============================================================================
# CONFIG
# ============================================================================

DEFAULT_CONFIG = "config.json"


def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load router config from JSON. Falls back to same-directory default.
    """
    if config_path is None:
        config_path = Path(__file__).parent / DEFAULT_CONFIG

    path = Path(config_path)
    if not path.exists():
        print(f"ERROR: Config not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        cfg = json.load(f)

    # Resolve paths - project_root is relative to config file location
    config_dir = Path(config_path).parent
    cfg["project_root"] = (config_dir / cfg["project_root"]).resolve()
    watch = cfg.get("watch_dir", "~/Downloads")
    cfg["watch_dir"] = Path(os.path.expanduser(watch)).resolve()

    # Defaults
    cfg.setdefault("debounce_seconds", 1.5)
    cfg.setdefault("auto_overwrite", True)
    cfg.setdefault("startup_scan", True)
    cfg.setdefault("routing_rules", [])
    cfg.setdefault("watched_extensions", [".py", ".json", ".zip", ".md", ".txt"])
    cfg.setdefault("known_root_folders", [])

    # Convert extensions to set
    cfg["watched_extensions"] = set(cfg["watched_extensions"])

    # Auto-discover known folders from disk (merge with config list)
    cfg["known_root_folders"] = _discover_known_folders(
        cfg["project_root"], cfg["known_root_folders"],
    )

    return cfg


def _discover_known_folders(root: Path, seed_list: List[str]) -> Set[str]:
    """
    Build known-folder set from config list + actual directories on disk.
    Skips hidden dirs, __pycache__, .git, venv, node_modules.
    """
    skip = {".git", "__pycache__", "venv", ".venv", "node_modules", ".idea", "env"}
    discovered = set()

    if root.exists():
        for item in root.iterdir():
            if item.is_dir() and item.name not in skip and not item.name.startswith("."):
                discovered.add(item.name)

    # Merge seed list (lowercase for matching)
    for folder in seed_list:
        discovered.add(folder)

    return {f.lower() for f in discovered}


# ============================================================================
# PERSISTENCE - ignore list
# ============================================================================

def _ignore_path(cfg: dict) -> Path:
    """Ignore list stored in tools/ folder."""
    return cfg["project_root"] / "tools" / "droprouter_ignore.json"


def load_ignore_list(cfg: dict) -> Set[str]:
    path = _ignore_path(cfg)
    if path.exists():
        try:
            with open(path, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_ignore_list(ignore_set: Set[str], cfg: dict):
    path = _ignore_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(sorted(ignore_set), f, indent=2)


# ============================================================================
# FILE WATCHER
# ============================================================================

class DownloadsHandler(FileSystemEventHandler):
    def __init__(self, cfg: dict, hud=None):
        self.cfg = cfg
        self.hud = hud
        self.ignore_list = load_ignore_list(cfg)
        self.pending_files: Dict[str, float] = {}
        self.processing: Set[str] = set()
        self.lock = threading.Lock()
        self.file_count = 0

        self._prefix = cfg["prefix"].lower()
        self._extensions = cfg["watched_extensions"]
        self._debounce = cfg["debounce_seconds"]

    def on_created(self, event):
        self._queue(event)

    def on_modified(self, event):
        self._queue(event)

    def _queue(self, event):
        if event.is_directory:
            return
        fp = Path(event.src_path)
        if not fp.name.lower().startswith(self._prefix):
            return
        if fp.suffix.lower() not in self._extensions:
            return
        if fp.name in self.ignore_list or fp.name in self.processing:
            return
        with self.lock:
            self.pending_files[str(fp)] = time.time()

    def process_pending(self):
        now = time.time()
        ready = []
        with self.lock:
            for fp, ts in list(self.pending_files.items()):
                if now - ts >= self._debounce:
                    ready.append(fp)
                    del self.pending_files[fp]
        for fp in ready:
            if Path(fp).exists():
                self._handle(fp)

    # ----- core handler -----

    def _handle(self, filepath):
        filepath = Path(filepath)
        if not filepath.exists() or filepath.name in self.ignore_list:
            return

        is_zip = filepath.suffix.lower() == ".zip"

        if is_zip:
            if filepath.name in self.processing:
                return
            self.processing.add(filepath.name)

        try:
            if is_zip:
                self._handle_zip(filepath)
            else:
                self._handle_single(filepath)
        finally:
            self.processing.discard(filepath.name)

    def _handle_zip(self, filepath):
        cfg = self.cfg
        project_root = cfg["project_root"]
        known_folders = cfg["known_root_folders"]
        project_name = cfg["project_name"]

        contents = get_zip_files(filepath)
        if not contents:
            print(f"  ⚠️ Empty or unreadable zip: {filepath.name}")
            return

        # Detect structure (for tree display purposes)
        mode, wrapper = detect_zip_mode(contents, known_folders)

        # ALWAYS show tree dialog for ALL zips
        print(f"📦 Processing zip: {filepath.name}")

        def resolver(entry, wrap):
            return get_structure_destination(entry, wrap, project_root, known_folders)

        dialog = ZipTreeDialog(
            filepath, contents, wrapper,
            project_name, project_root, resolver,
        )
        if not dialog.show_dialog():
            print(f"  Skipped: {filepath.name}")
            return

        extracted, flagged = extract_zip_structure(filepath, wrapper, cfg)
        
        # HUD update: increment count
        self.file_count += 1
        if self.hud:
            self.hud.update_count.emit(self.file_count)

        if flagged:
            # Show flagged files notification using PySide6
            self._show_flagged_notification(flagged, project_name)
    
    def _show_flagged_notification(self, flagged: List[str], project_name: str):
        """Show notification about flagged files using PySide6."""
        try:
            from PySide6.QtWidgets import QMessageBox
            names = "\n".join(f"• {n}" for n in flagged[:15])
            if len(flagged) > 15:
                names += f"\n... and {len(flagged) - 15} more"
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Flagged Files")
            msg.setText(f"{len(flagged)} file(s) sent to Downloads")
            msg.setInformativeText(f"Paths not recognized in {project_name}:")
            msg.setDetailedText(names)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        except ImportError:
            # Fallback to console if PySide6 not available
            print(f"  ⚠️ {len(flagged)} flagged file(s) → Downloads")
            for name in flagged[:15]:
                print(f"    • {name}")
            if len(flagged) > 15:
                print(f"    ... and {len(flagged) - 15} more")

    def _handle_single(self, filepath):
        cfg = self.cfg
        project_root = cfg["project_root"]

        dest = get_suggested_destination(filepath.name, cfg)

        if dest is not None:
            if dest in ("", "ROOT"):
                dest_path = project_root
                label = "ROOT"
            else:
                dest_path = project_root / dest
                label = dest

            dest_path.mkdir(parents=True, exist_ok=True)
            final = dest_path / filepath.name

            if final.exists():
                final.unlink()

            try:
                shutil.move(str(filepath), str(final))
                print(f"  ✓ {filepath.name} → {label}")
                
                # HUD update: increment count
                self.file_count += 1
                if self.hud:
                    self.hud.update_count.emit(self.file_count)
            except Exception as e:
                print(f"  ERROR moving {filepath.name}: {e}")
        else:
            print(f"  ? No route for: {filepath.name}")
            UnmatchedFilePopup(
                filepath, self.ignore_list,
                lambda il: save_ignore_list(il, cfg),
            ).show_dialog()


# ============================================================================
# STARTUP SCAN
# ============================================================================

def scan_existing_files(cfg: dict, ignore_list: Set[str]) -> List[Path]:
    """Find prefixed files already sitting in Downloads."""
    prefix = cfg["prefix"].lower()
    extensions = cfg["watched_extensions"]
    watch_dir = cfg["watch_dir"]

    files = []
    for f in watch_dir.iterdir():
        if f.is_file() and f.name.lower().startswith(prefix):
            if f.suffix.lower() in extensions and f.name not in ignore_list:
                files.append(f)
    return sorted(files, key=lambda f: f.name)


def process_startup(cfg: dict, ignore_list: Set[str]) -> Set[str]:
    """
    Handle files already in Downloads when router starts.
    ALL zips get a tree preview. Single files auto-route.
    """
    project_root = cfg["project_root"]
    project_name = discover_project_name()
    known_folders = cfg["known_root_folders"]

    files = scan_existing_files(cfg, ignore_list)
    if not files:
        print(f"No existing {cfg['prefix']}* files to process.")
        return set()

    scanned_names = {f.name for f in files}
    print(f"Found {len(files)} existing file(s)...")

    for filepath in files:
        is_zip = filepath.suffix.lower() == ".zip"

        if is_zip:
            contents = get_zip_files(filepath)
            
            if not contents:
                print(f"  ⚠️ Empty zip: {filepath.name}")
                continue
            
            # ALWAYS show tree dialog for ALL zips
            mode, wrapper = detect_zip_mode(contents, known_folders)
            
            def resolver(entry, wrap):
                return get_structure_destination(entry, wrap, project_root, known_folders)

            dialog = ZipTreeDialog(
                filepath, contents, wrapper,
                project_name, project_root, resolver,
            )
            if dialog.show_dialog():
                extracted, flagged = extract_zip_structure(filepath, wrapper, cfg)
                if flagged:
                    print(f"  ⚠️ {len(flagged)} file(s) → Downloads")
                    for name in flagged[:10]:
                        print(f"    • {name}")
                    if len(flagged) > 10:
                        print(f"    ... and {len(flagged) - 10} more")
            else:
                print(f"  Skipped: {filepath.name}")
        else:
            dest = get_suggested_destination(filepath.name, cfg)
            if dest is not None:
                dest_dir = dest if dest not in ("", "ROOT") else ""
                dest_path = project_root / dest_dir if dest_dir else project_root
                dest_path.mkdir(parents=True, exist_ok=True)
                final = dest_path / filepath.name
                if final.exists():
                    final.unlink()
                try:
                    shutil.move(str(filepath), str(final))
                    print(f"  ✓ {filepath.name} → {dest_dir or 'ROOT'}")
                except Exception as e:
                    print(f"  ERROR: {filepath.name}: {e}")
            else:
                print(f"  ? No route for: {filepath.name} (skipped)")

    return scanned_names


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="DropRouterHud - prefix-based file routing")
    parser.add_argument(
        "--config", "-c", type=str, default=None,
        help="Path to config.json (default: same directory as script)",
    )
    parser.add_argument(
        "--no-hud", action="store_true",
        help="Disable HUD overlay (console-only mode)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    name = discover_project_name()
    prefix = cfg["prefix"]
    root = cfg["project_root"]
    watch = cfg["watch_dir"]
    exts = cfg["watched_extensions"]

    print("=" * 60)
    print(f"  {name} DropRouter")
    print("=" * 60)
    print(f"Watching: {watch}")
    print(f"Prefix:   {prefix}*")
    print(f"Target:   {root}")
    print(f"Known:    {', '.join(sorted(cfg['known_root_folders']))}")
    print(f"Extensions: {', '.join(sorted(exts))}")
    print("-" * 60)

    if not watch.exists():
        print(f"ERROR: Watch folder not found: {watch}")
        return
    if not root.exists():
        print(f"ERROR: Project folder not found: {root}")
        return

    # Initialize instance manager and HUD
    instance_mgr = None
    hud = None
    app = None
    position_index = 0
    
    hud_enabled = cfg.get("hud", {}).get("enabled", True) and not args.no_hud and HUD_AVAILABLE
    
    if hud_enabled:
        try:
            instance_mgr = InstanceManager(name, str(watch))
            position_index = instance_mgr.acquire_position()
            print(f"HUD position: {position_index}")
            
            app, hud = create_hud_app(name, str(watch), position_index, cfg, VERSION)
            print("HUD overlay enabled")
        except Exception as e:
            print(f"⚠️  Could not initialize HUD: {e}")
            hud_enabled = False

    ignore_list = load_ignore_list(cfg)

    # Process files already sitting in Downloads at startup
    if cfg["startup_scan"]:
        startup_scanned = process_startup(cfg, ignore_list)
        # Note: We don't track startup_scanned files in handler.processing
        # because they're moved/deleted after processing, so filepath.exists()
        # check in _handle() will prevent any race conditions.

    print("-" * 60)
    print("Watching for new files... (Ctrl+C to stop)\n")

    handler = DownloadsHandler(cfg, hud)
    # Note: Don't add startup_scanned to handler.processing!
    # The processing set should only contain files CURRENTLY being processed,
    # not files that were already processed during startup.
    observer = Observer()
    observer.schedule(handler, str(watch), recursive=False)
    observer.start()

    try:
        if app and hud:
            # Run with GUI event loop
            import threading
            
            def watcher_loop():
                """Background thread for file watching."""
                try:
                    while True:
                        time.sleep(0.5)
                        handler.process_pending()
                        
                        # Heartbeat to instance manager
                        if instance_mgr:
                            instance_mgr.heartbeat()
                except KeyboardInterrupt:
                    pass
            
            # Start watcher in background thread
            watcher_thread = threading.Thread(target=watcher_loop, daemon=True)
            watcher_thread.start()
            
            # Run GUI event loop in main thread
            app.exec()
        else:
            # Console-only mode
            while True:
                time.sleep(0.5)
                handler.process_pending()
                
                if instance_mgr:
                    instance_mgr.heartbeat()
    except KeyboardInterrupt:
        print("\nStopping router...")
    finally:
        observer.stop()
        if instance_mgr:
            instance_mgr.release()

    observer.join()
    print("Done.")


if __name__ == "__main__":
    main()
