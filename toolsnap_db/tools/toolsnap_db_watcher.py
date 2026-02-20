"""
Downloads Watcher for ToolSnap DB (PC App)
Watches ~/Downloads for tsdb_* files and routes them into C:\\toolsnap_db.

ZIP files with recognized structure (core/, ui/, config/, utils/)
are auto-extracted to the correct paths — zero popups.

Single files with a pattern match are moved silently.
Unmatched files are logged and skipped.

Run: python toolsnap_db_watcher.py
"""

import os
import re
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
import time
import zipfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ============================================================================
# CONFIGURATION
# ============================================================================

DOWNLOADS_DIR = Path(os.path.expanduser("~")) / "Downloads"
TOOLSNAP_DB_ROOT = Path("C:/toolsnap_db")
WATCHER_DIR = TOOLSNAP_DB_ROOT / "tools"
IGNORE_FILE = WATCHER_DIR / "watcher_ignore.json"
SETTINGS_FILE = WATCHER_DIR / "watcher_settings.json"
ROUTES_FILE = WATCHER_DIR / "watcher_routes.json"

DEBOUNCE_SECONDS = 2.0
TOOLSNAP_PREFIX = "tsdb_"

WATCHED_EXTENSIONS = {
    '.py', '.json', '.yaml', '.yml',
    '.md', '.txt', '.bat', '.ps1', '.zip',
    '.cfg', '.ini', '.toml', '.db',
}

# Known root folders that indicate structure-based zip routing
KNOWN_ROOT_FOLDERS = {'core', 'ui', 'config', 'utils', 'tools', 'imports'}

# ============================================================================
# SETTINGS / IGNORE / ROUTES
# ============================================================================

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'auto_overwrite': True, 'custom_routes': {}}

def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def load_ignore_list():
    if IGNORE_FILE.exists():
        try:
            with open(IGNORE_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_ignore_list(ignore_set):
    IGNORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(IGNORE_FILE, 'w') as f:
        json.dump(list(ignore_set), f, indent=2)

def load_routing_config():
    if ROUTES_FILE.exists():
        try:
            with open(ROUTES_FILE, 'r') as f:
                config = json.load(f)
            return config.get('routing_rules', [])
        except Exception as e:
            print(f"WARNING: Failed to load {ROUTES_FILE}: {e}")
    return []

SETTINGS = load_settings()
ROUTING_RULES = load_routing_config()

# ============================================================================
# PATTERN ROUTING (for single loose files)
# ============================================================================

def get_suggested_destination(filename):
    """
    Get suggested destination for a single file using pattern rules.
    Returns: destination string or None
    """
    custom = SETTINGS.get('custom_routes', {})
    if filename in custom:
        return custom[filename]

    for rule in ROUTING_RULES:
        if re.match(rule['pattern'], filename, re.IGNORECASE):
            return rule['destination']

    return None

# ============================================================================
# ZIP STRUCTURE DETECTION
# ============================================================================

def get_zip_files(filepath):
    """Return list of non-directory entries in a zip."""
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            return [f for f in zf.namelist() if not f.endswith('/')]
    except Exception:
        return []

def detect_zip_mode(zip_contents):
    """
    Detect whether zip uses structure-based routing.
    Returns: ('structure', wrapper_folder_or_None) or ('flat', None)
    """
    if not zip_contents:
        return ('flat', None)

    root_folders = set()
    for path in zip_contents:
        parts = path.replace('\\', '/').split('/')
        if parts and parts[0]:
            root_folders.add(parts[0].lower())

    # Direct match — zip roots ARE toolsnap_db folders
    if root_folders & KNOWN_ROOT_FOLDERS:
        return ('structure', None)

    # Wrapper check — single root containing known folders
    if len(root_folders) == 1:
        wrapper = list(root_folders)[0]
        nested = set()
        for path in zip_contents:
            parts = path.replace('\\', '/').split('/')
            if len(parts) > 1 and parts[1]:
                nested.add(parts[1].lower())

        if nested & KNOWN_ROOT_FOLDERS:
            for path in zip_contents:
                parts = path.replace('\\', '/').split('/')
                if parts[0].lower() == wrapper:
                    return ('structure', parts[0])

    return ('flat', None)

def get_structure_destination(zip_path, strip_wrapper=None):
    """
    Derive destination from the zip entry's internal path.
    Returns: (relative_dir, is_flagged)
    """
    path = zip_path.replace('\\', '/')

    if strip_wrapper and path.startswith(strip_wrapper + '/'):
        path = path[len(strip_wrapper) + 1:]

    parts = path.split('/')
    if len(parts) <= 1:
        return ('ROOT', False)

    dir_path = '/'.join(parts[:-1])

    # Trust any path whose top-level folder is a known project folder.
    # This allows new subdirectories (e.g. imports/session_xyz/) to be
    # created on extract without requiring them to already exist on disk.
    top_folder = parts[0].lower()
    if top_folder in KNOWN_ROOT_FOLDERS:
        return (dir_path, False)

    # Fall back to existence checks for paths outside known roots
    full_path = TOOLSNAP_DB_ROOT / dir_path
    if full_path.exists() and full_path.is_dir():
        return (dir_path, False)
    if full_path.parent.exists():
        return (dir_path, False)

    return ('Downloads', True)

# ============================================================================
# ZIP EXTRACTION (structure mode)
# ============================================================================

def extract_zip_structure(zip_path, wrapper):
    """
    Extract a structure-mode zip, routing each file by its internal path.
    Returns: (extracted_count, flagged_list)
    """
    contents = get_zip_files(zip_path)
    flagged = []
    extracted = 0

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for entry in contents:
                dest_dir, is_flagged = get_structure_destination(entry, wrapper)
                filename = Path(entry).name

                if dest_dir in ('', 'ROOT'):
                    dest_path = TOOLSNAP_DB_ROOT
                elif is_flagged:
                    dest_path = DOWNLOADS_DIR
                    flagged.append(filename)
                else:
                    dest_path = TOOLSNAP_DB_ROOT / dest_dir

                dest_path.mkdir(parents=True, exist_ok=True)
                final = dest_path / filename

                if final.exists():
                    final.unlink()

                temp_dir = TOOLSNAP_DB_ROOT / '__temp_extract__'
                temp_file = Path(zf.extract(entry, temp_dir))
                shutil.move(str(temp_file), str(final))
                extracted += 1

                tag = "-> Downloads (flagged)" if is_flagged else f"-> {dest_dir or 'ROOT'}"
                print(f"    {filename}  {tag}")

        temp_dir = TOOLSNAP_DB_ROOT / '__temp_extract__'
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

        zip_path.unlink()
        print(f"  ZIP {zip_path.name}: {extracted} files extracted, zip deleted")

    except Exception as e:
        print(f"  ERROR extracting {zip_path.name}: {e}")

    return extracted, flagged

# ============================================================================
# ZIP EXTRACTION (flat mode)
# ============================================================================

def extract_zip_flat(zip_path, dest_path):
    """Extract entire zip to a single destination directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest_path)
            count = len([f for f in zf.namelist() if not f.endswith('/')])
        zip_path.unlink()
        print(f"  ZIP {zip_path.name}: {count} files -> {dest_path}, zip deleted")
    except Exception as e:
        print(f"  ERROR extracting {zip_path.name}: {e}")

# ============================================================================
# STARTUP TREE DIALOG
# ============================================================================

class ZipTreeDialog:
    """
    Read-only tree showing the file structure that will be extracted,
    with Process / Skip buttons.
    """

    def __init__(self, zip_path, contents, wrapper):
        self.zip_path = zip_path
        self.contents = contents
        self.wrapper = wrapper
        self.accepted = False
        self._build()

    def _build(self):
        self.root = tk.Tk()
        self.root.title(f"ZIP: {self.zip_path.name}")
        self.root.attributes('-topmost', True)
        self.root.resizable(True, True)

        screen_h = self.root.winfo_screenheight()
        height = min(max(400, len(self.contents) * 22 + 200), screen_h - 100)
        self.root.geometry(f'700x{height}+50+30')

        style = ttk.Style()
        style.configure('Header.TLabel', font=('Segoe UI', 13, 'bold'))
        style.configure('TButton', font=('Segoe UI', 11))

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f"ZIP: {self.zip_path.name}",
                  style='Header.TLabel').pack(anchor='w')

        flagged_count = 0
        for entry in self.contents:
            _, is_flagged = get_structure_destination(entry, self.wrapper)
            if is_flagged:
                flagged_count += 1

        summary = f"{len(self.contents)} files"
        if flagged_count:
            summary += f"  ({flagged_count} flagged -- path not found)"
        ttk.Label(main, text=summary, font=('Segoe UI', 10),
                  foreground='gray').pack(anchor='w', pady=(2, 8))

        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=('dest',), show='tree headings',
                                  selectmode='none')
        self.tree.heading('#0', text='File', anchor='w')
        self.tree.heading('dest', text='Destination', anchor='w')
        self.tree.column('#0', width=320, minwidth=200)
        self.tree.column('dest', width=340, minwidth=200)

        scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

        self._populate_tree()

        ttk.Separator(main, orient='horizontal').pack(fill='x', pady=(10, 8))
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill='x')

        ttk.Button(btn_frame, text="Process",
                   command=self._accept).pack(side='right', padx=(5, 0))
        ttk.Button(btn_frame, text="Skip",
                   command=self._skip).pack(side='right')

        self.root.bind('<Return>', lambda e: self._accept())
        self.root.bind('<Escape>', lambda e: self._skip())
        self.root.protocol("WM_DELETE_WINDOW", self._skip)

    def _populate_tree(self):
        entries = sorted(e.replace('\\', '/') for e in self.contents)

        def strip(p):
            if self.wrapper and p.startswith(self.wrapper + '/'):
                return p[len(self.wrapper) + 1:]
            return p

        folder_ids = {}

        for entry in entries:
            display = strip(entry)
            parts = display.split('/')
            filename = parts[-1]
            folder_parts = parts[:-1]

            parent_id = ''
            for i, folder in enumerate(folder_parts):
                folder_key = '/'.join(folder_parts[:i + 1])
                if folder_key not in folder_ids:
                    folder_ids[folder_key] = self.tree.insert(
                        parent_id, 'end', text=f"[DIR] {folder}", open=True, values=('',))
                parent_id = folder_ids[folder_key]

            dest, flagged = get_structure_destination(entry, self.wrapper)
            if flagged:
                dest_display = "Downloads (flagged)"
                tag = 'flagged'
            elif dest == 'ROOT':
                dest_display = "C:/toolsnap_db/"
                tag = 'ok'
            else:
                dest_display = dest
                tag = 'ok'

            self.tree.insert(parent_id, 'end', text=f"  {filename}",
                             values=(dest_display,), tags=(tag,))

        self.tree.tag_configure('flagged', foreground='#CC6600')
        self.tree.tag_configure('ok', foreground='#333333')

    def _accept(self):
        self.accepted = True
        self.root.destroy()

    def _skip(self):
        self.accepted = False
        self.root.destroy()

    def show(self):
        self.root.mainloop()
        return self.accepted

# ============================================================================
# UNMATCHED FILE POPUP
# ============================================================================

class UnmatchedFilePopup:
    """
    Tiny popup for a single file that had no pattern match.
    """

    def __init__(self, filepath, ignore_list):
        self.filepath = Path(filepath)
        self.ignore_list = ignore_list
        self.root = tk.Tk()
        self.root.title("Unmatched File")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)
        self.root.geometry('420x140+50+50')

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="No route for:",
                  font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(main, text=self.filepath.name,
                  font=('Consolas', 11), foreground='#0066cc').pack(anchor='w', pady=(4, 12))

        btn = ttk.Frame(main)
        btn.pack(fill='x')
        ttk.Button(btn, text="Ignore Once", command=self._once).pack(side='left')
        ttk.Button(btn, text="Always Ignore", command=self._always).pack(side='left', padx=5)
        ttk.Button(btn, text="Close", command=self._once).pack(side='right')

        self.root.bind('<Escape>', lambda e: self._once())
        self.root.protocol("WM_DELETE_WINDOW", self._once)

    def _once(self):
        self.root.destroy()

    def _always(self):
        self.ignore_list.add(self.filepath.name)
        save_ignore_list(self.ignore_list)
        print(f"  Always ignoring: {self.filepath.name}")
        self.root.destroy()

    def show(self):
        self.root.mainloop()

# ============================================================================
# FILE WATCHER
# ============================================================================

class DownloadsHandler(FileSystemEventHandler):
    def __init__(self):
        self.ignore_list = load_ignore_list()
        self.pending_files = {}
        self.processing = set()
        self.lock = threading.Lock()

    def on_created(self, event):
        self._queue(event)

    def on_modified(self, event):
        self._queue(event)

    def _queue(self, event):
        if event.is_directory:
            return
        fp = Path(event.src_path)
        if not fp.name.lower().startswith(TOOLSNAP_PREFIX):
            return
        if fp.suffix.lower() not in WATCHED_EXTENSIONS:
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
                if now - ts >= DEBOUNCE_SECONDS:
                    ready.append(fp)
                    del self.pending_files[fp]
        for fp in ready:
            if Path(fp).exists():
                self._handle(fp)

    def _handle(self, filepath):
        filepath = Path(filepath)
        if not filepath.exists() or filepath.name in self.ignore_list:
            return

        is_zip = filepath.suffix.lower() == '.zip'

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
        contents = get_zip_files(filepath)
        if not contents:
            print(f"  Empty or unreadable zip: {filepath.name}")
            return

        mode, wrapper = detect_zip_mode(contents)

        if mode == 'structure':
            print(f"ZIP Structure: {filepath.name}")

            dialog = ZipTreeDialog(filepath, contents, wrapper)
            if not dialog.show():
                print(f"  Skipped: {filepath.name}")
                return

            extracted, flagged = extract_zip_structure(filepath, wrapper)

            if flagged:
                names = "\n".join(f"  {n}" for n in flagged[:15])
                if len(flagged) > 15:
                    names += f"\n... and {len(flagged) - 15} more"
                messagebox.showwarning(
                    "Flagged Files",
                    f"{len(flagged)} file(s) sent to Downloads "
                    f"(paths not found in toolsnap_db):\n\n{names}")
        else:
            print(f"ZIP Flat: {filepath.name} -> project root")
            extract_zip_flat(filepath, TOOLSNAP_DB_ROOT)

    def _handle_single(self, filepath):
        dest = get_suggested_destination(filepath.name)

        if dest is not None:
            if dest in ('', 'ROOT'):
                dest_path = TOOLSNAP_DB_ROOT
                label = 'ROOT'
            else:
                dest_path = TOOLSNAP_DB_ROOT / dest
                label = dest

            dest_path.mkdir(parents=True, exist_ok=True)
            final = dest_path / filepath.name

            if final.exists():
                final.unlink()

            try:
                shutil.move(str(filepath), str(final))
                print(f"  OK {filepath.name} -> {label}")
            except Exception as e:
                print(f"  ERROR moving {filepath.name}: {e}")
        else:
            print(f"  ? No route for: {filepath.name}")
            UnmatchedFilePopup(filepath, self.ignore_list).show()

# ============================================================================
# STARTUP SCAN
# ============================================================================

def scan_existing_files(ignore_list):
    """Find tsdb_* files already sitting in Downloads."""
    files = []
    for f in DOWNLOADS_DIR.iterdir():
        if f.is_file() and f.name.lower().startswith(TOOLSNAP_PREFIX):
            if f.suffix.lower() in WATCHED_EXTENSIONS and f.name not in ignore_list:
                files.append(f)
    return sorted(files, key=lambda f: f.name)

def process_startup(ignore_list):
    """
    Handle files already in Downloads when watcher starts.
    Structure zips get a tree preview. Everything else auto-routes.
    """
    files = scan_existing_files(ignore_list)
    if not files:
        print("No existing tsdb_* files to process.")
        return set()

    scanned_names = {f.name for f in files}
    print(f"Found {len(files)} existing file(s)...")

    for filepath in files:
        is_zip = filepath.suffix.lower() == '.zip'

        if is_zip:
            contents = get_zip_files(filepath)
            mode, wrapper = detect_zip_mode(contents)

            if mode == 'structure' and contents:
                dialog = ZipTreeDialog(filepath, contents, wrapper)
                if dialog.show():
                    extracted, flagged = extract_zip_structure(filepath, wrapper)
                    if flagged:
                        names = "\n".join(f"  {n}" for n in flagged[:15])
                        messagebox.showwarning(
                            "Flagged Files",
                            f"{len(flagged)} file(s) -> Downloads:\n\n{names}")
                else:
                    print(f"  Skipped: {filepath.name}")
            elif contents:
                print(f"ZIP Flat: {filepath.name} -> project root")
                extract_zip_flat(filepath, TOOLSNAP_DB_ROOT)
            else:
                print(f"  Empty zip: {filepath.name}")
        else:
            dest = get_suggested_destination(filepath.name)
            if dest is not None:
                dest_dir = dest if dest not in ('', 'ROOT') else ''
                dest_path = TOOLSNAP_DB_ROOT / dest_dir if dest_dir else TOOLSNAP_DB_ROOT
                dest_path.mkdir(parents=True, exist_ok=True)
                final = dest_path / filepath.name
                if final.exists():
                    final.unlink()
                try:
                    shutil.move(str(filepath), str(final))
                    print(f"  OK {filepath.name} -> {dest_dir or 'ROOT'}")
                except Exception as e:
                    print(f"  ERROR: {filepath.name}: {e}")
            else:
                print(f"  ? No route for: {filepath.name} (skipped)")

    return scanned_names

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("  ToolSnap DB Downloads Watcher")
    print("=" * 60)
    print(f"Watching: {DOWNLOADS_DIR}")
    print(f"Prefix:   {TOOLSNAP_PREFIX}*")
    print(f"Target:   {TOOLSNAP_DB_ROOT}")
    print(f"Extensions: {', '.join(sorted(WATCHED_EXTENSIONS))}")
    print("-" * 60)

    if not DOWNLOADS_DIR.exists():
        print(f"ERROR: Downloads folder not found: {DOWNLOADS_DIR}")
        return
    if not TOOLSNAP_DB_ROOT.exists():
        print(f"ERROR: toolsnap_db folder not found: {TOOLSNAP_DB_ROOT}")
        return

    ignore_list = load_ignore_list()
    startup_scanned = process_startup(ignore_list)

    print("-" * 60)
    print("Watching for new files... (Ctrl+C to stop)\n")

    handler = DownloadsHandler()
    handler.processing.update(startup_scanned)
    observer = Observer()
    observer.schedule(handler, str(DOWNLOADS_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.5)
            handler.process_pending()
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()

    observer.join()
    print("Done.")

if __name__ == "__main__":
    main()
