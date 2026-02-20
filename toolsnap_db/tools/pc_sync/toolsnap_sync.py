"""
ToolSnap PC Sync — Imports session data from a connected Android tablet into SQLite.

Usage:
    python toolsnap_sync.py                 # Auto-detect tablet drive
    python toolsnap_sync.py D:\             # Specify drive letter
    python toolsnap_sync.py --watch         # Watch for tablet connection

Looks for: <DRIVE>:\Documents\ToolSnap\<session_folders>\manifest.json
Imports into: toolsnap.db (SQLite, created in script directory)
Writes .synced marker into each imported session folder on the tablet.
"""

import json
import os
import shutil
import sqlite3
import string
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_NAME = "toolsnap.db"
TOOLSNAP_RELATIVE_PATH = os.path.join("Documents", "ToolSnap")
MANIFEST_FILE = "manifest.json"
SYNCED_MARKER = ".synced"
IMAGE_STORE_DIR = "toolsnap_images"  # local folder for copied images

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    tool_name       TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    is_complete     INTEGER NOT NULL DEFAULT 0,
    fields_captured INTEGER NOT NULL DEFAULT 0,
    fields_skipped  INTEGER NOT NULL DEFAULT 0,
    fields_total    INTEGER NOT NULL DEFAULT 0,
    folder_name     TEXT NOT NULL,
    synced_at       TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fields (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    field_name      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    entry_method    TEXT,
    image_file      TEXT,
    local_image     TEXT,
    ocr_text        TEXT,
    form_data       TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    UNIQUE(session_id, field_name)
);

CREATE TABLE IF NOT EXISTS form_values (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    field_name      TEXT NOT NULL,
    form_key        TEXT NOT NULL,
    form_value      TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    UNIQUE(session_id, field_name, form_key)
);

CREATE INDEX IF NOT EXISTS idx_sessions_tool ON sessions(tool_name);
CREATE INDEX IF NOT EXISTS idx_fields_session ON fields(session_id);
CREATE INDEX IF NOT EXISTS idx_form_values_session ON form_values(session_id);
CREATE INDEX IF NOT EXISTS idx_form_values_key ON form_values(form_key);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Create/open the database and ensure tables exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(CREATE_TABLES_SQL)
    conn.commit()
    return conn


def session_exists(conn: sqlite3.Connection, session_id: str) -> bool:
    """Check if a session is already in the database."""
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    return row is not None


def import_session(
    conn: sqlite3.Connection,
    manifest: dict,
    folder_name: str,
    source_dir: Path,
    image_store: Path,
) -> bool:
    """
    Import a single session into the database.
    Copies images to local storage.
    Extracts form data into queryable form_values table.
    Returns True if imported (new or updated), False if skipped.
    """
    sid = manifest["sessionId"]
    now = datetime.now().isoformat()

    # Copy images to local store
    session_image_dir = image_store / folder_name
    session_image_dir.mkdir(parents=True, exist_ok=True)

    if session_exists(conn, sid):
        conn.execute(
            """UPDATE sessions SET
                tool_name=?, is_complete=?, fields_captured=?,
                fields_skipped=?, fields_total=?, updated_at=?
            WHERE session_id=?""",
            (
                manifest["toolName"],
                1 if manifest["isComplete"] else 0,
                manifest["fieldsCaptured"],
                manifest["fieldsSkipped"],
                manifest["fieldsTotal"],
                now,
                sid,
            ),
        )
    else:
        conn.execute(
            """INSERT INTO sessions
                (session_id, tool_name, created_at, is_complete,
                 fields_captured, fields_skipped, fields_total,
                 folder_name, synced_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sid,
                manifest["toolName"],
                manifest["createdAt"],
                1 if manifest["isComplete"] else 0,
                manifest["fieldsCaptured"],
                manifest["fieldsSkipped"],
                manifest["fieldsTotal"],
                folder_name,
                now,
                now,
            ),
        )

    # Import fields
    for field_name, field_data in manifest.get("fields", {}).items():
        image_file = field_data.get("imageFile")
        local_image = None
        entry_method = field_data.get("entryMethod")
        form_data_raw = field_data.get("formData")

        # Copy image file if present
        if image_file:
            src_img = source_dir / image_file
            if src_img.exists():
                dst_img = session_image_dir / image_file
                shutil.copy2(str(src_img), str(dst_img))
                local_image = str(dst_img)

        # Serialize form data as JSON string for the fields table
        form_data_json = json.dumps(form_data_raw) if form_data_raw else None

        # Upsert field
        conn.execute(
            """INSERT INTO fields
                (session_id, field_name, status, entry_method,
                 image_file, local_image, ocr_text, form_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, field_name) DO UPDATE SET
                status=excluded.status,
                entry_method=excluded.entry_method,
                image_file=excluded.image_file,
                local_image=excluded.local_image,
                ocr_text=excluded.ocr_text,
                form_data=excluded.form_data""",
            (
                sid,
                field_name,
                field_data.get("status", "PENDING"),
                entry_method,
                image_file,
                local_image,
                field_data.get("ocrText"),
                form_data_json,
            ),
        )

        # Extract structured form values into queryable table
        if form_data_raw and isinstance(form_data_raw, dict):
            form_values = form_data_raw.get("values", {})
            if isinstance(form_values, dict):
                for form_key, form_value in form_values.items():
                    if form_value:  # skip blank values
                        conn.execute(
                            """INSERT INTO form_values
                                (session_id, field_name, form_key, form_value)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(session_id, field_name, form_key) DO UPDATE SET
                                form_value=excluded.form_value""",
                            (sid, field_name, form_key, str(form_value)),
                        )

    conn.commit()
    return True


def write_synced_marker(session_dir: Path):
    """Write a .synced file into the session folder on the tablet."""
    marker = session_dir / SYNCED_MARKER
    marker.write_text(datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Drive detection
# ---------------------------------------------------------------------------


def find_toolsnap_drives() -> list[Path]:
    """Scan all drive letters for a ToolSnap folder."""
    found = []
    for letter in string.ascii_uppercase:
        drive = Path(f"{letter}:\\")
        ts_path = drive / TOOLSNAP_RELATIVE_PATH
        if ts_path.exists() and ts_path.is_dir():
            found.append(ts_path)
    return found


def scan_sessions(toolsnap_root: Path) -> list[tuple[Path, dict]]:
    """Find all session folders with a valid manifest.json."""
    sessions = []
    if not toolsnap_root.exists():
        return sessions

    for entry in sorted(toolsnap_root.iterdir()):
        if not entry.is_dir():
            continue
        manifest_file = entry / MANIFEST_FILE
        if not manifest_file.exists():
            continue
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            sessions.append((entry, manifest))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [WARN] Bad manifest in {entry.name}: {e}")
    return sessions


# ---------------------------------------------------------------------------
# Main sync
# ---------------------------------------------------------------------------


def run_sync(toolsnap_root: Path, db_path: str = None):
    """Run a full sync from the tablet to the local database."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

    image_store = Path(os.path.dirname(os.path.abspath(__file__))) / IMAGE_STORE_DIR

    print(f"\n{'='*60}")
    print(f"  ToolSnap Sync")
    print(f"  Source:   {toolsnap_root}")
    print(f"  Database: {db_path}")
    print(f"  Images:   {image_store}")
    print(f"{'='*60}\n")

    conn = init_db(db_path)

    sessions = scan_sessions(toolsnap_root)
    if not sessions:
        print("  No sessions found on tablet.")
        conn.close()
        return

    print(f"  Found {len(sessions)} session(s) on tablet.\n")

    imported = 0
    skipped = 0

    for session_dir, manifest in sessions:
        sid = manifest.get("sessionId", "?")
        name = manifest.get("toolName", "?")
        already_synced = (session_dir / SYNCED_MARKER).exists()

        if already_synced and session_exists(conn, sid):
            print(f"  [SKIP]  {name} ({session_dir.name}) — already synced")
            skipped += 1
            continue

        print(f"  [SYNC]  {name} ({session_dir.name})")

        success = import_session(
            conn=conn,
            manifest=manifest,
            folder_name=session_dir.name,
            source_dir=session_dir,
            image_store=image_store,
        )

        if success:
            write_synced_marker(session_dir)
            imported += 1
            fields = manifest.get("fieldsCaptured", 0)
            total = manifest.get("fieldsTotal", 0)

            # Count manual vs OCR entries
            manual_count = sum(
                1 for f in manifest.get("fields", {}).values()
                if f.get("entryMethod") == "manual"
            )
            ocr_count = sum(
                1 for f in manifest.get("fields", {}).values()
                if f.get("entryMethod") == "ocr"
            )

            detail = f"{fields}/{total} fields"
            if manual_count > 0:
                detail += f", {manual_count} manual"
            if ocr_count > 0:
                detail += f", {ocr_count} OCR"
            print(f"          {detail} ✓")

    conn.close()

    print(f"\n{'─'*60}")
    print(f"  Done: {imported} imported, {skipped} already synced")
    print(f"{'─'*60}\n")


def watch_mode():
    """Poll for tablet connection and auto-sync when detected."""
    print("ToolSnap Sync — Watching for tablet connection...")
    print("Press Ctrl+C to stop.\n")

    last_synced = set()

    while True:
        drives = find_toolsnap_drives()
        for ts_root in drives:
            drive_key = str(ts_root)
            if drive_key not in last_synced:
                print(f"\n  Tablet detected: {ts_root}")
                run_sync(ts_root)
                last_synced.add(drive_key)

        current_keys = {str(d) for d in drives}
        disconnected = last_synced - current_keys
        if disconnected:
            for d in disconnected:
                print(f"  Tablet disconnected: {d}")
            last_synced -= disconnected

        time.sleep(3)


# ---------------------------------------------------------------------------
# Query helpers (for use from Python or as examples)
# ---------------------------------------------------------------------------


def query_tools_by_material(db_path: str, material: str):
    """Example: find all tools rated for a specific material."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """SELECT s.tool_name, fv.form_value as material,
                  sfm.form_value as sfm, rpm.form_value as rpm
           FROM form_values fv
           JOIN sessions s ON s.session_id = fv.session_id
           LEFT JOIN form_values sfm ON sfm.session_id = fv.session_id
               AND sfm.field_name = fv.field_name AND sfm.form_key = 'sfm'
           LEFT JOIN form_values rpm ON rpm.session_id = fv.session_id
               AND rpm.field_name = fv.field_name AND rpm.form_key = 'rpm'
           WHERE fv.form_key = 'material'
             AND fv.form_value LIKE ?""",
        (f"%{material}%",),
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--watch" in sys.argv:
        try:
            watch_mode()
        except KeyboardInterrupt:
            print("\nStopped.")
    elif len(sys.argv) > 1 and sys.argv[1] != "--watch":
        root = Path(sys.argv[1]) / TOOLSNAP_RELATIVE_PATH
        if not root.exists():
            root = Path(sys.argv[1])
        run_sync(root)
    else:
        drives = find_toolsnap_drives()
        if not drives:
            print("No tablet with ToolSnap data found.")
            print("Make sure the tablet is connected via USB in File Transfer mode.")
            print(f"Looking for: <DRIVE>:\\{TOOLSNAP_RELATIVE_PATH}\\")
            print("\nUsage:")
            print("  python toolsnap_sync.py              # Auto-detect")
            print("  python toolsnap_sync.py D:\\           # Specify drive")
            print("  python toolsnap_sync.py --watch      # Watch mode")
        else:
            for ts_root in drives:
                run_sync(ts_root)
