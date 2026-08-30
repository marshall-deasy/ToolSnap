"""Schema versioning.

Before this existed, init() ran CREATE TABLE IF NOT EXISTS over whatever was
already on disk. A schema change therefore reached new installs and silently
skipped every existing one, surfacing later as "no such column" on a shop PC
rather than as an error at upgrade time. These tests pin the behaviour that
replaced it.
"""

import sqlite3

import pytest

from core import database


def _version(path):
    conn = sqlite3.connect(path)
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def _tables(path):
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


# --- fresh databases --------------------------------------------------------

def test_a_new_database_is_stamped_at_the_current_version(tmp_path):
    db = tmp_path / "fresh.db"
    database.close()
    database.init(db)
    database.close()

    assert _version(db) == database.SCHEMA_VERSION


def test_a_new_database_gets_the_full_baseline_schema(tmp_path):
    db = tmp_path / "fresh.db"
    database.close()
    database.init(db)
    database.close()

    assert {"Tools", "Components", "Compatibility", "Inventory"} <= _tables(db)


def test_reopening_an_up_to_date_database_is_a_no_op(tmp_path):
    db = tmp_path / "fresh.db"
    database.close()
    database.init(db)
    database.close()

    database.init(db)
    conn = database.get_connection()
    conn.execute(
        "INSERT INTO Tools (toolId, name, category, type, createdAt, modifiedAt) "
        "VALUES ('t1', 'Drill', 'DRILL', 'standalone', '2026-01-01', '2026-01-01')"
    )
    conn.commit()
    database.close()

    # Second open must migrate nothing and preserve the row.
    database.init(db)
    count = database.get_connection().execute("SELECT COUNT(*) FROM Tools").fetchone()[0]
    database.close()

    assert count == 1
    assert _version(db) == database.SCHEMA_VERSION


# --- databases that predate versioning --------------------------------------

def test_a_pre_versioning_database_is_adopted_without_losing_data(tmp_path):
    """The case that matters in the field: a toolsnap.db already in a shop.

    It carries the baseline tables and rows but user_version is still 0,
    because it was created before this mechanism existed.
    """
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    conn.executescript(database._SCHEMA_SQL)
    conn.execute(
        "INSERT INTO Tools (toolId, name, category, type, createdAt, modifiedAt) "
        "VALUES ('legacy-1', 'Existing Tap', 'TAP', 'standalone', '2026-01-01', '2026-01-01')"
    )
    conn.commit()
    conn.close()
    assert _version(db) == 0

    database.close()
    database.init(db)
    surviving = database.get_connection().execute(
        "SELECT name FROM Tools WHERE toolId = 'legacy-1'"
    ).fetchone()[0]
    database.close()

    assert surviving == "Existing Tap"
    assert _version(db) == database.SCHEMA_VERSION


# --- guard rails ------------------------------------------------------------

def test_a_database_from_a_newer_build_is_refused(tmp_path):
    db = tmp_path / "future.db"
    conn = sqlite3.connect(db)
    conn.executescript(database._SCHEMA_SQL)
    conn.execute(f"PRAGMA user_version = {database.SCHEMA_VERSION + 5}")
    conn.commit()
    conn.close()

    database.close()
    with pytest.raises(database.SchemaTooNewError):
        database.init(db)
    database.close()


# --- the runner itself ------------------------------------------------------

def test_a_pending_migration_is_applied_and_stamped(tmp_path, monkeypatch):
    """Exercise the upgrade path with a synthetic migration.

    There is only one real version so far, so the mechanism is proved with an
    injected step rather than waiting for the first schema change to test it.
    """
    db = tmp_path / "upgrade.db"
    database.close()
    database.init(db)
    database.close()
    assert database.SCHEMA_VERSION == 1

    next_version = database.SCHEMA_VERSION + 1
    monkeypatch.setitem(
        database._MIGRATIONS,
        next_version,
        ("ALTER TABLE Inventory ADD COLUMN lastOrderedAt TEXT",),
    )
    monkeypatch.setattr(database, "SCHEMA_VERSION", next_version)

    database.init(db)
    columns = {
        r[1] for r in database.get_connection().execute("PRAGMA table_info(Inventory)")
    }
    database.close()

    assert "lastOrderedAt" in columns
    assert _version(db) == next_version


def test_a_failing_migration_does_not_advance_the_version(tmp_path, monkeypatch):
    db = tmp_path / "broken.db"
    database.close()
    database.init(db)
    database.close()
    before = _version(db)

    next_version = database.SCHEMA_VERSION + 1
    monkeypatch.setitem(
        database._MIGRATIONS, next_version, ("ALTER TABLE NoSuchTable ADD COLUMN x TEXT",)
    )
    monkeypatch.setattr(database, "SCHEMA_VERSION", next_version)

    with pytest.raises(sqlite3.OperationalError):
        database.init(db)
    database.close()

    # The stamp must not move, so the next startup retries rather than
    # believing a half-applied upgrade succeeded.
    assert _version(db) == before
