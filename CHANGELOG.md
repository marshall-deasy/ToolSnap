# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-08-30

First tagged release. The system works end to end — capture on the tablet,
import and manage on the PC — and the repository is now in a state where
further work can be reviewed rather than just accumulated.

Earlier development predates this changelog; the git history holds it.

### Added

- **Android capture app** (`android/`) — Kotlin/Compose wizard for photographing
  an assembled tool across five fields (body, insert, hardware, tool data,
  speeds & feeds), with on-device OCR on the two text-bearing fields. Each
  session exports as a self-contained folder of photos plus `manifest.json`.
  Fields track status individually, so a partial capture is still a valid entry.
- **PC database application** (`backend/`) — PySide6 desktop app covering
  import, search, assemblies, compatibility mapping, inventory with reorder
  points, QR label generation, and BOM export.
- **Import pipeline** — scans the sync directory, detects manifest schema
  version, migrates older manifests to v3 in memory, and deduplicates against
  the existing catalog on catalog number + manufacturer, falling back to ISO
  designation + grade for inserts.
- **Test suite** — 17 tests over manifest migration, version detection, rescan
  idempotency, and every deduplication rule, run against three real capture
  sessions committed as fixtures.
- **`pyproject.toml`** — dependencies, ruff, and pytest configuration in one
  declarative file, replacing `requirements.txt`.
- **Design documentation** in `docs/` — architecture for both halves, the data
  model and its relational redesign, the sync procedure, and the hardening
  punch list. These previously existed only outside the repository.

### Changed

- Restructured into `android/` and `backend/`; paths, configuration defaults,
  and launch scripts follow.
- `README.md` rewritten against the real tree: correct layout, working
  documentation links, PySide6 rather than Tkinter, and the previously
  undocumented `JAVA_HOME` requirement for command-line Gradle builds.
- `config/settings.json` and `tsdb_sync_tablet.ps1` now resolve the import
  directory relative to the installation instead of a hardcoded absolute path.

### Removed

- The v2 manifest migration path. No manifest has ever carried
  `schemaVersion: 2` — v2 was superseded at the design stage by the relational
  model that shipped as v3, so the branch was unreachable.
- `utils/manifest.py`, an unreferenced duplicate of the live import and
  migration logic in `core/importer.py`.
- The runtime database and the `imports/` landing zone from version control.
  Both are generated on first run and remain on disk; neither is tracked.

### Fixed

- Restored command-line Android builds; the Gradle wrapper JAR was missing.
- Four `.gitignore` rules that matched nothing: three pointed at
  pre-restructure paths, and one carried a trailing comment, which git treats
  as part of the pattern rather than a comment.
- `run_toolsnap_db.bat` launched a path that no longer existed.

[Unreleased]: https://github.com/marshall-deasy/ToolSnap/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/marshall-deasy/ToolSnap/releases/tag/v0.1.0
