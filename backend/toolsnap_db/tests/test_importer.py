"""Manifest import and migration.

The fixtures under tests/fixtures/sessions are real capture sessions taken
off the tablet, one per schema shape the importer actually encounters:

    v1_complete       v1, all five fields CAPTURED
    v1_partial_skips  v1, three CAPTURED and two SKIPPED
    v3_standalone     v3, the current schema
"""

from pathlib import Path

from core import repo
from core.importer import _detect_version, scan_and_import


def _tool_named(name):
    return next(t for t in repo.get_all_tools() if t.name == name)


# --- version detection ------------------------------------------------------

def test_absent_schema_version_is_treated_as_v1():
    # v1 manifests predate the schemaVersion key entirely.
    assert _detect_version({"sessionId": "x", "fields": {}}) == 1


def test_schema_version_is_read_when_present():
    assert _detect_version({"schemaVersion": 3, "tools": []}) == 3


# --- scanning ---------------------------------------------------------------

def test_scan_imports_every_fixture_without_error(tmp_db, sessions):
    result = scan_and_import(sessions)

    assert result.directories_scanned == 3
    assert result.manifests_found == 3
    assert result.total_tools_added == 3
    assert result.total_errors == 0


def test_scan_reports_the_detected_version_per_session(tmp_db, sessions):
    result = scan_and_import(sessions)
    versions = {Path(r.directory).name: r.version for r in result.imports}

    assert versions == {
        "v1_complete": 1,
        "v1_partial_skips": 1,
        "v3_standalone": 3,
    }


def test_rescanning_the_same_sessions_imports_nothing_new(tmp_db, sessions):
    scan_and_import(sessions)
    second = scan_and_import(sessions)

    # Manifests are fingerprinted by content hash, so an unchanged directory
    # is skipped rather than duplicated.
    assert second.total_tools_added == 0
    assert all(r.skipped for r in second.imports)
    assert repo.get_tool_count() == 3


# --- v1 migration -----------------------------------------------------------

def test_v1_collects_every_captured_photo(tmp_db, sessions):
    scan_and_import(sessions)
    tool = _tool_named("1")

    assert len(tool.photos) == 5
    assert {Path(p).name for p in tool.photos} == {
        "body.jpg", "insert.jpg", "hardware.jpg", "tool_data.jpg", "speeds_feeds.jpg",
    }


def test_v1_omits_photos_for_skipped_fields(tmp_db, sessions):
    scan_and_import(sessions)
    tool = _tool_named("5")

    # Session 5 has three CAPTURED fields but only two images on disk; the
    # SKIPPED fields must not contribute photo entries.
    assert len(tool.photos) == 2
    assert {Path(p).name for p in tool.photos} == {"body.jpg", "insert.jpg"}


def test_v1_without_form_data_falls_back_to_other(tmp_db, sessions):
    scan_and_import(sessions)
    tool = _tool_named("1")

    # No formData means no category, manufacturer or attributes to recover.
    assert tool.category.value == "OTHER"
    assert tool.tool_type == "standalone"
    assert tool.manufacturer is None
    assert tool.attributes == {}


def test_v1_photo_paths_are_absolute_and_resolve(tmp_db, sessions):
    scan_and_import(sessions)
    tool = _tool_named("1")

    for photo in tool.photos:
        assert Path(photo).is_absolute()
        assert Path(photo).is_file()


# --- v3 passthrough ---------------------------------------------------------

def test_v3_preserves_identity_fields(tmp_db, sessions):
    scan_and_import(sessions)
    tool = _tool_named("Tap")

    assert tool.category.value == "TAP"
    assert tool.manufacturer == "OSG"
    assert tool.catalog_number == "45667788"


def test_v3_preserves_attributes(tmp_db, sessions):
    scan_and_import(sessions)
    tool = _tool_named("Tap")

    assert tool.attributes == {
        "thread_pitch": "20",
        "flutes": "2",
        "thread_form": "unc",
        "cutting_diameter": '1/4"',
    }
