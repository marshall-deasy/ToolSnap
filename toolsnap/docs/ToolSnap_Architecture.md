# ToolSnap — Android Capture App Architecture

## Overview

ToolSnap is a field data capture tool for cataloging CNC tooling assemblies. The Android app handles photo capture and on-device OCR only. The actual tooling database lives on a Windows 11 desktop/laptop application that imports the captured data.

---

## Concept

### What It Does

- Guides the user through a step-by-step wizard to photograph and identify assembled tooling (holder body + insert + hardware)
- Runs on-device OCR on tool data labels and speeds/feeds documentation
- Packages each capture session as a self-contained export (images + JSON manifest)
- Hands off to a Windows desktop app for database management, review, and long-term storage

### What It Does NOT Do

- Does not manage the tooling database
- Does not handle searching, filtering, or reporting
- Does not require network access to function (all processing is on-device)

---

## Capture Fields

Each capture session can include up to five photo/data fields. Any field can be skipped. Only the tool name is required to create a database entry.

| Field | Purpose | OCR? | Notes |
|---|---|---|---|
| **Tool Body** | Primary visual reference of the holder | No | Identifies holder type (boring bar, face mill, turning tool, etc.) |
| **Insert** | Photo of the insert for replacement/reorder | No | Captures shape, IC size, chipbreaker style. ISO designation may be visible |
| **Hardware** | Screws, clamps, shims, seats | No | Visual reference for sourcing replacements |
| **Tool Data** | Tool identification and specs | Yes | From body engraving, literature, or printout |
| **Speeds & Feeds** | Recommended cutting parameters | Yes | From manufacturer chart, printout, or manual entry |

---

## Completion Model

Every wizard session produces a DB entry no matter what — even if only a name is provided. Completion is tracked per-field, not as a single flag.

### Field Statuses

- **PENDING** — default state, not yet addressed
- **CAPTURED** — photo taken (and OCR confirmed if applicable)
- **SKIPPED** — user explicitly skipped this field
- **OCR_NEEDS_REVIEW** — OCR ran but user hasn't confirmed the result

### Home Screen Indicators

- Green badge = all fields captured
- Yellow badge = one or more fields skipped or pending
- Session list shows count: "12 tools, 3 incomplete"
- Tapping an incomplete entry opens it directly to fill missing fields

---

## Data Flow

```
User taps ADD TOOLING
    → HomeScreen calls SessionManager.createSession()
    → SessionManager generates session ID + timestamp, returns CaptureSession
    → WizardNavHost launches with that session

ToolNameScreen
    → User enters name → SessionManager.setToolName(name)
    → Navigate to first CaptureStepScreen

CaptureStepScreen (reused for each field via CaptureField enum)
    → "Capture" → launches CameraX preview → user takes photo
        → ImageUtils.savePhoto(sessionId, field) → file path stored in session
        → If field.requiresOcr (TOOL_DATA, SPEEDS_FEEDS):
            → OcrProcessor.extractText(imagePath) → raw text
            → Navigate to OcrReviewScreen with raw text
        → Else: mark field CAPTURED, advance to next step
    → "Skip" → mark field SKIPPED, advance to next step

OcrReviewScreen
    → Shows extracted text, user edits if needed
    → "Confirm" → SessionManager.setOcrText(field, confirmedText)
    → Mark field CAPTURED, advance to next step

SummaryScreen
    → Displays all fields with status (thumbnail / skipped / needs review)
    → "Save" → SessionManager.finalizeSession()
        → SessionExporter.export(session)
            → Writes images + JSON manifest to export directory
        → Returns to HomeScreen

HomeScreen
    → Lists all sessions from export directory
    → Shows completion badges (reads manifests)
    → Tapping incomplete session → SessionDetailScreen → can fill missing fields
```

---

## File / Module Structure

```
toolsnap/
├── app/src/main/java/com/toolsnap/
│   ├── ToolSnapApp.kt                — Application class, DI setup (~30 lines)
│   ├── MainActivity.kt               — Single activity host, nav setup (~40 lines)
│   │
│   ├── core/                          — Business logic, no UI
│   │   ├── model/
│   │   │   ├── CaptureSession.kt     — Data class: session ID, tool name, timestamp, field statuses
│   │   │   ├── CaptureField.kt       — Enum: BODY, INSERT, HARDWARE, TOOL_DATA, SPEEDS_FEEDS
│   │   │   └── FieldStatus.kt        — Enum: PENDING, CAPTURED, SKIPPED, OCR_NEEDS_REVIEW
│   │   ├── session/
│   │   │   ├── SessionManager.kt     — Creates/manages active capture session, tracks state
│   │   │   └── SessionExporter.kt    — Builds the export package (images + JSON manifest)
│   │   └── ocr/
│   │       └── OcrProcessor.kt       — ML Kit text recognition, returns raw text
│   │
│   ├── ui/                            — Display/interaction only, no business logic
│   │   ├── home/
│   │   │   └── HomeScreen.kt         — Main screen: ADD TOOLING button, session list, incomplete count
│   │   ├── wizard/
│   │   │   ├── WizardNavHost.kt      — Navigation flow through wizard steps
│   │   │   ├── ToolNameScreen.kt     — Step 0: enter tool name (only required field)
│   │   │   ├── CaptureStepScreen.kt  — Reusable screen for each photo step
│   │   │   ├── OcrReviewScreen.kt    — Shows OCR result for confirmation/edit
│   │   │   └── SummaryScreen.kt      — End of wizard: thumbnails, skip indicators, save
│   │   ├── detail/
│   │   │   └── SessionDetailScreen.kt — View/edit a completed or incomplete session
│   │   └── components/
│   │       ├── BigActionButton.kt    — Reusable large touch-friendly button
│   │       ├── StatusBadge.kt        — Green/yellow completion indicator
│   │       └── PhotoThumbnail.kt     — Image preview with placeholder for skipped fields
│   │
│   ├── config/
│   │   └── CaptureConfig.kt          — Field definitions, display names, OCR flags, image sizes
│   │
│   └── utils/
│       ├── ImageUtils.kt             — Resize, compress, save to internal storage
│       ├── JsonUtils.kt              — Manifest serialization/deserialization
│       └── FileUtils.kt              — Directory management, export packaging
│
├── app/src/main/res/                  — Standard Android resources
└── build.gradle.kts                   — Dependencies: CameraX, ML Kit, Compose, Kotlin serialization
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `core/model/` | Pure data classes and enums — no logic, no dependencies |
| `core/session/` | Session lifecycle: create, update fields, finalize, export |
| `core/ocr/` | ML Kit wrapper — takes an image path, returns extracted text |
| `ui/home/` | Entry point UI — session list, add button, completion overview |
| `ui/wizard/` | Step-by-step capture flow — camera, OCR review, summary |
| `ui/detail/` | View/edit existing sessions, fill in skipped fields |
| `ui/components/` | Reusable UI elements shared across screens |
| `config/` | Single source of truth for field definitions and app settings |
| `utils/` | Shared helpers for image processing, JSON, and file management |

---

## Shared Logic Inventory

These are used by more than one module. Each lives in exactly one place.

| Shared Concern | Location | Used By |
|---|---|---|
| Image save/load/compress | `utils/ImageUtils.kt` | CaptureStepScreen, SessionExporter, SessionDetailScreen |
| JSON manifest read/write | `utils/JsonUtils.kt` | SessionExporter, HomeScreen, SessionDetailScreen |
| File path conventions | `utils/FileUtils.kt` | SessionManager, SessionExporter, ImageUtils |
| Field definitions & order | `config/CaptureConfig.kt` | WizardNavHost, CaptureStepScreen, SummaryScreen, StatusBadge |
| Completion status calc | `core/session/SessionManager.kt` | HomeScreen, SummaryScreen, StatusBadge |

**Key principle:** `CaptureConfig.kt` is the single source of truth for what fields exist and their properties. The wizard iterates over it. The summary reads from it. Adding a new photo category means updating the config — everything else adapts automatically.

---

## Export Package Format

Each capture session produces a self-contained folder ready for transfer to the Windows app.

### Directory Structure

```
toolsnap_exports/
└── 2026-02-03_boring-bar-A123/
    ├── manifest.json
    ├── body.jpg            (absent if skipped)
    ├── insert.jpg          (absent if skipped)
    ├── hardware.jpg        (absent if skipped)
    ├── tool_data.jpg       (absent if skipped)
    └── speeds_feeds.jpg    (absent if skipped)
```

### Manifest Schema

```json
{
  "session_id": "uuid-string",
  "tool_name": "Boring Bar A123",
  "created_at": "2026-02-03T14:30:00Z",
  "fields": {
    "body": {
      "status": "CAPTURED",
      "image_file": "body.jpg",
      "ocr_text": null
    },
    "insert": {
      "status": "CAPTURED",
      "image_file": "insert.jpg",
      "ocr_text": null
    },
    "hardware": {
      "status": "SKIPPED",
      "image_file": null,
      "ocr_text": null
    },
    "tool_data": {
      "status": "CAPTURED",
      "image_file": "tool_data.jpg",
      "ocr_text": "SCLCR 12-3B  Kennametal  D=0.750  L=6.0"
    },
    "speeds_feeds": {
      "status": "SKIPPED",
      "image_file": null,
      "ocr_text": null
    }
  },
  "is_complete": false,
  "fields_captured": 3,
  "fields_skipped": 2,
  "fields_total": 5
}
```

---

## Transfer to Windows Desktop

The export folder is a self-contained package. Transfer options (to be decided):

- **USB** — connect phone, pull export folder manually
- **Shared network folder** — phone writes to a mapped drive on the shop network
- **Local HTTP** — desktop app runs a simple endpoint, phone pushes over WiFi
- **Manual copy** — user copies the export folder via file manager

The Windows app watches for or imports these folders, reads the manifest, and builds database entries from the contents.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Kotlin |
| UI Framework | Jetpack Compose |
| Camera | CameraX |
| OCR | Google ML Kit (on-device text recognition) |
| Serialization | Kotlin Serialization (JSON) |
| Navigation | Compose Navigation |
| Local Storage | Internal app storage (files + JSON, no database) |

---

## Design Principles

Per project engineering standards:

1. **Architecture before code** — this document defines the plan
2. **Single source of truth** — field definitions in CaptureConfig, path conventions in FileUtils, no duplication
3. **No copy-paste patterns** — CaptureStepScreen is reused for all photo fields via enum parameterization
4. **Files under 400 lines** — each file has one clear responsibility
5. **UI contains no business logic** — screens collect input and display state, processing happens in core/
6. **Complete working code only** — no stubs, no TODOs, all imports resolve
7. **Config is separate from code** — CaptureConfig.kt holds all tunable values
