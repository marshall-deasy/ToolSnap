"""Database connection management, schema initialization and migrations."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Tools (
    toolId          TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    type            TEXT NOT NULL,
    manufacturer    TEXT,
    catalogNumber   TEXT,
    description     TEXT,
    unitSystem      TEXT,
    attributes      TEXT,
    notes           TEXT,
    tags            TEXT,
    photos          TEXT,
    createdAt       TEXT NOT NULL,
    modifiedAt      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tools_category ON Tools(category);
CREATE INDEX IF NOT EXISTS idx_tools_manufacturer ON Tools(manufacturer);
CREATE INDEX IF NOT EXISTS idx_tools_catalogNumber ON Tools(catalogNumber);

CREATE TABLE IF NOT EXISTS Components (
    parentToolId    TEXT NOT NULL REFERENCES Tools(toolId),
    childToolId     TEXT NOT NULL REFERENCES Tools(toolId),
    role            TEXT NOT NULL,
    quantity        INTEGER DEFAULT 1,
    notes           TEXT,
    PRIMARY KEY (parentToolId, childToolId, role)
);

CREATE INDEX IF NOT EXISTS idx_components_child ON Components(childToolId);

CREATE TABLE IF NOT EXISTS Compatibility (
    bodyToolId      TEXT NOT NULL REFERENCES Tools(toolId),
    insertToolId    TEXT NOT NULL REFERENCES Tools(toolId),
    fitNotes        TEXT,
    PRIMARY KEY (bodyToolId, insertToolId)
);

CREATE INDEX IF NOT EXISTS idx_compat_insert ON Compatibility(insertToolId);

CREATE TABLE IF NOT EXISTS Inventory (
    toolId          TEXT PRIMARY KEY REFERENCES Tools(toolId),
    location        TEXT,
    quantityOnHand  INTEGER DEFAULT 0,
    reorderPoint    INTEGER DEFAULT 0,
    reorderQty      INTEGER DEFAULT 0,
    preferredVendor TEXT,
    vendorPartNumber TEXT,
    unitCost        REAL,
    lastCountedAt   TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_inventory_location ON Inventory(location);
CREATE INDEX IF NOT EXISTS idx_inventory_vendor ON Inventory(preferredVendor);

CREATE TABLE IF NOT EXISTS _imported_manifests (
    directory_path  TEXT PRIMARY KEY,
    content_hash    TEXT NOT NULL,
    imported_at     TEXT NOT NULL,
    tool_count      INTEGER DEFAULT 0,
    component_count INTEGER DEFAULT 0
);
"""

_db_path: Path | None = None
_connection: sqlite3.Connection | None = None


# Schema version this build of the application expects.
SCHEMA_VERSION = 1

# Ordered migrations, keyed by the version each one produces: entry N upgrades a
# database from version N-1 to version N. Entry 1 is the baseline schema, so a
# brand-new database is built by replaying every migration in order and ends up
# byte-identical to an old one that was upgraded step by step.
#
# To add a migration:
#   1. add _MIGRATIONS[N] with the ALTER TABLE / CREATE statements
#   2. set SCHEMA_VERSION = N
#
# Never edit an existing entry. Installs that already ran it will not run it
# again, so a retroactive edit silently produces two different schemas.
#
# A str is executed with executescript; a tuple of str is executed statement by
# statement inside one transaction.
_MIGRATIONS: dict[int, "str | tuple[str, ...]"] = {
    1: _SCHEMA_SQL,
}


class SchemaTooNewError(RuntimeError):
    """The database was written by a newer build than this one."""


def _get_user_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _set_user_version(conn: sqlite3.Connection, version: int) -> None:
    # PRAGMA statements do not accept bound parameters.
    conn.execute(f"PRAGMA user_version = {int(version)}")


def _has_baseline_schema(conn: sqlite3.Connection) -> bool:
    """True if this database already has tables but no version stamp."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'Tools'"
    ).fetchone()
    return row is not None


def _apply(conn: sqlite3.Connection, statements: "str | tuple[str, ...]") -> None:
    if isinstance(statements, str):
        conn.executescript(statements)
        return
    try:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def migrate(conn: sqlite3.Connection) -> int:
    """Bring a database up to SCHEMA_VERSION, returning the version reached.

    Safe to call on every startup: already-current databases are untouched.
    """
    version = _get_user_version(conn)

    if version > SCHEMA_VERSION:
        raise SchemaTooNewError(
            f"Database is at schema version {version}, but this build only "
            f"understands {SCHEMA_VERSION}. Update the application rather than "
            f"opening this database with an older one."
        )

    # Databases created before versioning existed carry the baseline schema but
    # no stamp. Adopt them at version 1 instead of replaying the baseline.
    if version == 0 and _has_baseline_schema(conn):
        _set_user_version(conn, 1)
        conn.commit()
        version = 1

    for target in range(version + 1, SCHEMA_VERSION + 1):
        _apply(conn, _MIGRATIONS[target])
        _set_user_version(conn, target)
        conn.commit()
        version = target

    return version


def init(db_path: Path) -> None:
    """Initialize the database: set the path, then create or migrate the schema."""
    global _db_path
    _db_path = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    migrate(get_connection())


def get_connection() -> sqlite3.Connection:
    """Get (or create) the shared database connection."""
    global _connection
    if _connection is None:
        if _db_path is None:
            raise RuntimeError("Database not initialized — call database.init() first")
        _connection = sqlite3.connect(str(_db_path))
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


@contextmanager
def transaction():
    """Context manager for a DB transaction — commits on success, rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def close() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
