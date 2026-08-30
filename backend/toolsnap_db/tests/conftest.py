"""Shared pytest fixtures for the ToolSnap database tests."""

from pathlib import Path

import pytest

from core import database

FIXTURE_SESSIONS = Path(__file__).parent / "fixtures" / "sessions"


@pytest.fixture
def tmp_db(tmp_path):
    """Give one test an isolated, empty database.

    core.database holds the connection in a module-level global, so it has to
    be closed on both sides of the test — otherwise the next test silently
    reuses the previous test's file.
    """
    database.close()
    database.init(tmp_path / "test.db")
    yield
    database.close()


@pytest.fixture
def sessions():
    """Path to the committed capture-session fixtures."""
    return FIXTURE_SESSIONS
