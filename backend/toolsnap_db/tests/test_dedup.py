"""Import-time deduplication.

DEDUP_ENABLED is on, so importing a tool that already exists merges it into
the existing row instead of creating a second one. A false match silently
collapses two distinct tools into one; a missed match quietly inflates the
catalog. Both are inventory corruption, so the matching rules are pinned here.
"""

import json

from core import repo
from core.importer import scan_and_import


def _write_session(root, dirname, *, tool_id, name, manufacturer, catalog_number,
                   category="TAP", attributes=None):
    """Write a minimal v3 session directory and return its path."""
    session = root / dirname
    session.mkdir(parents=True)
    manifest = {
        "schemaVersion": 3,
        "exportedAt": "2026-02-04T00:00:00.000000Z",
        "tools": [
            {
                "toolId": tool_id,
                "name": name,
                "category": category,
                "type": "standalone",
                "status": "CAPTURED",
                "manufacturer": manufacturer,
                "catalogNumber": catalog_number,
                "description": None,
                "unitSystem": "IMPERIAL",
                "attributes": attributes or {},
                "photos": [],
                "tags": [],
                "notes": None,
                "createdAt": "2026-02-04T00:00:00.000000Z",
                "modifiedAt": "2026-02-04T00:00:00.000000Z",
            }
        ],
        "components": [],
    }
    (session / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return session


def test_same_catalog_and_manufacturer_merges(tmp_db, tmp_path):
    _write_session(tmp_path, "first", tool_id="id-1", name="Tap A",
                   manufacturer="OSG", catalog_number="45667788")
    _write_session(tmp_path, "second", tool_id="id-2", name="Tap B",
                   manufacturer="OSG", catalog_number="45667788")

    result = scan_and_import(tmp_path)

    assert repo.get_tool_count() == 1
    assert result.total_tools_added == 1
    assert sum(r.tools_deduplicated for r in result.imports) == 1


def test_match_ignores_case_and_surrounding_whitespace(tmp_db, tmp_path):
    _write_session(tmp_path, "first", tool_id="id-1", name="Tap A",
                   manufacturer="OSG", catalog_number="45667788")
    _write_session(tmp_path, "second", tool_id="id-2", name="Tap B",
                   manufacturer="  osg  ", catalog_number=" 45667788 ")

    scan_and_import(tmp_path)

    assert repo.get_tool_count() == 1


def test_different_catalog_numbers_stay_separate(tmp_db, tmp_path):
    _write_session(tmp_path, "first", tool_id="id-1", name="Tap A",
                   manufacturer="OSG", catalog_number="45667788")
    _write_session(tmp_path, "second", tool_id="id-2", name="Tap B",
                   manufacturer="OSG", catalog_number="99999999")

    scan_and_import(tmp_path)

    assert repo.get_tool_count() == 2


def test_missing_manufacturer_prevents_a_catalog_match(tmp_db, tmp_path):
    # Both halves of the key must be present, or an unrelated tool sharing a
    # catalog number with a different maker would be absorbed.
    _write_session(tmp_path, "first", tool_id="id-1", name="Tap A",
                   manufacturer=None, catalog_number="45667788")
    _write_session(tmp_path, "second", tool_id="id-2", name="Tap B",
                   manufacturer=None, catalog_number="45667788")

    scan_and_import(tmp_path)

    assert repo.get_tool_count() == 2


def test_inserts_without_catalog_match_on_iso_and_grade(tmp_db, tmp_path):
    attrs = {"iso_designation": "CNMG432", "grade": "IC907"}
    _write_session(tmp_path, "first", tool_id="id-1", name="Insert A",
                   manufacturer=None, catalog_number=None,
                   category="INSERT", attributes=attrs)
    _write_session(tmp_path, "second", tool_id="id-2", name="Insert B",
                   manufacturer=None, catalog_number=None,
                   category="INSERT", attributes=dict(attrs))

    scan_and_import(tmp_path)

    assert repo.get_tool_count() == 1


def test_inserts_with_different_grades_stay_separate(tmp_db, tmp_path):
    _write_session(tmp_path, "first", tool_id="id-1", name="Insert A",
                   manufacturer=None, catalog_number=None, category="INSERT",
                   attributes={"iso_designation": "CNMG432", "grade": "IC907"})
    _write_session(tmp_path, "second", tool_id="id-2", name="Insert B",
                   manufacturer=None, catalog_number=None, category="INSERT",
                   attributes={"iso_designation": "CNMG432", "grade": "IC8250"})

    scan_and_import(tmp_path)

    assert repo.get_tool_count() == 2
