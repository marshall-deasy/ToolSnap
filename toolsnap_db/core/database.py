"""Database connection management and schema initialization."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

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


def init(db_path: Path) -> None:
    """Initialize the database: set path, create tables if needed."""
    global _db_path
    _db_path = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(_SCHEMA_SQL)


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
