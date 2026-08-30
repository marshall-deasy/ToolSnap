# ToolSnap

Tooling database and ordering system for a machine shop. An Android app captures
cutting-tool data on the shop floor; a Windows desktop application manages the
catalog, inventory, and reorder workflow.

## How it fits together

**`android/`** — Kotlin/Compose capture app. Guides the user through photographing
an assembled tool (body, insert, hardware), runs on-device OCR on data labels and
speeds/feeds sheets, and writes each session to a self-contained folder.

**`backend/`** — Python/PySide6 desktop application. Imports those session folders
and manages the relational tooling database: search, assemblies, compatibility,
inventory, QR labels, and BOM export.

The two halves meet at one contract: a session folder containing photos and a
`manifest.json`. The tablet syncs folders into `backend/toolsnap_db/imports/`,
and the desktop app scans that directory on import. Current manifest schema is
**v3**; the importer auto-detects and migrates older manifests in memory.

## Running the desktop application

Requires Python 3.11+.

```bash
cd backend/toolsnap_db
pip install -e .
python main.py
```

Or double-click `run_toolsnap_db.bat`.

The database file (`toolsnap.db`) and the `imports/` landing zone are runtime
state — both are deliberately untracked, and both are created on first run.

## Building the Android app

Requires the Android SDK and a JDK 17+.

```bash
cd android/toolsnap
./gradlew.bat assembleDebug
```

If the build reports `JAVA_HOME is not set`, point it at the JDK bundled with
Android Studio:

```bash
export JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"
```

Output lands in `app/build/outputs/apk/debug/`. The SDK location is read from
`local.properties`, which is untracked — create it if it is missing:

```properties
sdk.dir=C:\Android\Sdk
```

## Documentation

| Document | Contents |
|---|---|
| [`docs/architecture-android.md`](docs/architecture-android.md) | Capture app design and wizard flow |
| [`docs/architecture-backend.md`](docs/architecture-backend.md) | Desktop application brief |
| [`docs/data-model.md`](docs/data-model.md) | Capture and session data model |
| [`docs/data-model-relational-redesign.md`](docs/data-model-relational-redesign.md) | Relational design shipped as v3 |
| [`docs/sync-guide.md`](docs/sync-guide.md) | ADB tablet sync procedure |
| [`docs/hardening-punch-list.md`](docs/hardening-punch-list.md) | Production readiness items |
| [`docs/ENGINEERING_RULES.md`](docs/ENGINEERING_RULES.md) | Engineering conventions |
| [`docs/DOCUMENTATION_STANDARD.md`](docs/DOCUMENTATION_STANDARD.md) | Documentation conventions |

`docs/data-model-v2-superseded.md` and `docs/current-state-2026-02-03.md` are
kept for history; neither describes the current system.

## Development

Work lands on a branch and merges to `main` after review. Agent contributors —
Claude Code, Grok, or otherwise — are additionally bound by the operating
boundaries in [`AGENTS.md`](AGENTS.md).
