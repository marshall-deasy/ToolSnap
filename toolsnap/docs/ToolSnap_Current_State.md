# ToolSnap — Current State

**Last updated:** 2026-02-03 after Delivery 6  
**Project root:** `C:\toolsnap`

---

## What It Is

ToolSnap is an Android tablet app for cataloging CNC tooling assemblies on the shop floor. A machinist walks up to a tool, steps through a wizard that captures photos and data, and the app packages everything into a self-contained session folder. Later, the tablet plugs into a Windows PC via USB and a Python sync script imports sessions into a SQLite database.

The tablet is a capture device, not an archive. The PC holds the database.

---

## What's Built (Deliveries 1–6)

| Delivery | Scope | Status |
|---|---|---|
| 1 — Foundation | Gradle project, data models, enums, config, utils | ✅ Built, deployed |
| 2 — Core Logic | SessionManager, SessionExporter, OcrProcessor | ✅ Built, deployed |
| 3 — UI Screens | All wizard screens, navigation, home screen, detail screen | ✅ Built, deployed |
| 4 — Shop Floor UI | Big buttons, high contrast, PhotoReview/Crop screens, EXIF rotation fix | ✅ Built, deployed |
| 5 — Manual Entry | Three-way choice (ENTER MANUALLY / PHOTO+OCR / SKIP), structured forms, PC DB schema for form values | ✅ Built, deployed |
| 6 — Dropdowns | Six Tool Data fields converted from text inputs to dropdown pickers with industry-standard option lists and "Other…" custom entry | ✅ Built, deployed |

---

## User Flow

```
Home Screen
  └─ tap [+ ADD TOOLING]
       └─ ToolNameScreen → enter name (only required field) → NEXT
            │
            ├── Tool Body ──── TAKE PHOTO → PhotoReview → optional Crop → saved
            ├── Insert ─────── TAKE PHOTO → PhotoReview → optional Crop → saved
            ├── Hardware ───── TAKE PHOTO → PhotoReview → optional Crop → saved
            │
            ├── Tool Data ──── Three-way choice:
            │     ├── ENTER MANUALLY → form with dropdowns + text fields → saved
            │     ├── PHOTO + OCR → camera → ML Kit → review/edit text → saved
            │     └── SKIP
            │
            ├── Speeds & Feeds ── Three-way choice:
            │     ├── ENTER MANUALLY → form with numeric/text fields → saved
            │     ├── PHOTO + OCR → camera → ML Kit → review/edit text → saved
            │     └── SKIP
            │
            └── Summary Screen → review thumbnails + statuses → SAVE
                 └─ returns to Home Screen

Home Screen
  ├── Session list (newest first)
  │     ├── Green ✓ = all fields captured
  │     ├── Yellow ⚠ = incomplete
  │     └── Blue ☁ = synced to PC
  └── [CLEAR X SYNCED SESSIONS] button (appears when synced sessions exist)
```

Any field can be skipped. Any incomplete session can be reopened from the home screen.

---

## Capture Fields

| # | Field | Input Method | OCR? | Notes |
|---|---|---|---|---|
| 1 | Tool Body | Photo only | No | Primary visual reference of holder |
| 2 | Insert | Photo only | No | For replacement/reorder identification |
| 3 | Hardware | Photo only | No | Screws, clamps, shims, seats |
| 4 | Tool Data | Photo+OCR or Manual Form | Yes | 6 dropdown fields + 3 text fields |
| 5 | Speeds & Feeds | Photo+OCR or Manual Form | Yes | 10 text/numeric fields |

---

## Tool Data Form Fields (Delivery 5+6)

The Tool Data manual entry form uses dropdown pickers for six fields and text input for three:

| Field | Input Type | Options |
|---|---|---|
| Tool Description | Dropdown | 23 tool types (End Mill Square, Ball Nose, Corner Radius, Roughing, Finishing, Tapered, Face/Shell Mill, Drill Twist/Center/Indexable, Reamer, Tap, Thread Mill, Boring Bar, Chamfer Mill, Dovetail, T-Slot, Fly Cutter, Slitting Saw, Keyseat, Grooving/Parting, Turning Insert, Form Tool, Other…) |
| Manufacturer | Dropdown | 31 brands (Sandvik Coromant, Kennametal, Iscar, Seco, Walter, Mitsubishi, Kyocera, Sumitomo, Tungaloy, Dormer Pramet, OSG, YG-1, TaeguTec, Ingersoll, CERATIZIT, Widia, Greenleaf, Harvey Tool, Helical, Niagara, Garr, Gorilla Mill, Micro 100, Carmex, Emuge, Nachi, Guhring, MAPAL, Accupro, Scientific Cutting Tools, Other…) |
| Catalog / Part Number | Text | Free entry |
| Tool Diameter | Dropdown | 22 sizes (1/16" through 3", Other…) |
| Insert Grade | Text | Free entry (e.g. KC5010, IC808) |
| Nose / Corner Radius | Dropdown | 20 values (Sharp/0 through 1/2" 0.500", Full Radius Ball, Other…) |
| Flutes / Edges | Dropdown | 12 options (1–12, N/A Insert, Other…) |
| Coating | Dropdown | 17 types (Uncoated, TiN, TiCN, TiAlN, AlTiN, AlCrN, CrN, ZrN, TiB2, DLC, CVD Diamond, PCD, CBN, AlTiN Nano, TiAlSiN nanocomposite, Black Oxide, Other…) |
| Notes | Multiline text | Free entry |

Every dropdown includes an "Other…" option that switches to a free-text input field inside the bottom sheet picker.

## Speeds & Feeds Form Fields

| Field | Input Type |
|---|---|
| Workpiece Material | Text |
| Surface Speed (SFM) | Number |
| Spindle Speed (RPM) | Number |
| Feed per Rev (IPR) | Decimal |
| Feed Rate (IPM) | Decimal |
| Depth of Cut | Text |
| Width of Cut | Text |
| Coolant | Text |
| Operation Type | Text |
| Notes | Multiline |

---

## File Structure

```
C:\toolsnap\
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/toolsnap/
│       │   ├── ToolSnapApp.kt                 — Application class
│       │   ├── MainActivity.kt                — Single activity host
│       │   │
│       │   ├── config/
│       │   │   ├── CaptureConfig.kt           — Field definitions, image sizes, folder naming
│       │   │   └── FormTemplates.kt           — Form field definitions, dropdown option lists, FormData class
│       │   │
│       │   ├── core/
│       │   │   ├── model/
│       │   │   │   ├── CaptureField.kt        — Enum: BODY, INSERT, HARDWARE, TOOL_DATA, SPEEDS_FEEDS
│       │   │   │   ├── CaptureSession.kt      — Session state: statuses, paths, OCR text, form data
│       │   │   │   └── FieldStatus.kt         — Enum: PENDING, CAPTURED, SKIPPED, OCR_NEEDS_REVIEW
│       │   │   ├── session/
│       │   │   │   ├── SessionManager.kt      — Session lifecycle, persistence, state management
│       │   │   │   └── SessionExporter.kt     — Builds export package (images + JSON)
│       │   │   └── ocr/
│       │   │       └── OcrProcessor.kt        — ML Kit text recognition wrapper
│       │   │
│       │   ├── ui/
│       │   │   ├── NavHost.kt                 — Top-level navigation (home ↔ wizard ↔ detail)
│       │   │   ├── theme/
│       │   │   │   ├── Theme.kt               — Material 3 theme
│       │   │   │   └── ShopFloor.kt           — Shop-floor sizing constants (60dp buttons, 20sp text, etc.)
│       │   │   ├── home/
│       │   │   │   └── HomeScreen.kt          — Session list, sync badges, CLEAR SYNCED button
│       │   │   ├── wizard/
│       │   │   │   ├── WizardNavHost.kt       — Wizard step navigation
│       │   │   │   ├── NameEntryScreen.kt     — Tool name input
│       │   │   │   ├── CaptureStepScreen.kt   — Camera capture for each photo field
│       │   │   │   ├── PhotoReviewScreen.kt   — Photo review with USE / RETAKE / CROP
│       │   │   │   ├── CropScreen.kt          — Touch-based image cropping
│       │   │   │   ├── DataEntryChoiceScreen.kt — Three-way: ENTER MANUALLY / PHOTO+OCR / SKIP
│       │   │   │   ├── ManualEntryScreen.kt   — Form UI with dropdowns + text inputs + bottom sheet picker
│       │   │   │   ├── OcrReviewScreen.kt     — OCR result display and editing
│       │   │   │   └── WizardSummaryScreen.kt — Session summary with field statuses
│       │   │   └── detail/
│       │   │       └── SessionDetailScreen.kt — View/reopen completed sessions
│       │   │
│       │   └── utils/
│       │       ├── FileUtils.kt               — Path conventions, Documents/ToolSnap/ storage, sync markers
│       │       ├── ImageUtils.kt              — Resize, compress, EXIF rotation, save
│       │       └── JsonUtils.kt               — Manifest serialization, FormData in manifests
│       │
│       └── res/
│           ├── values/strings.xml
│           ├── values/themes.xml
│           └── xml/file_provider_paths.xml
│
├── build.gradle.kts                           — Root Gradle (Kotlin 1.9.22, Compose BOM)
├── settings.gradle.kts
├── gradle.properties
├── gradle/wrapper/gradle-wrapper.properties
├── gradlew
├── gradlew.bat
│
└── tools/
    └── pc_sync/
        └── toolsnap_sync.py                   — PC-side import: USB detect, SQLite, image copy
```

**Total: 28 Kotlin source files + 5 resource/config files + 6 Gradle files + 1 Python script = 40 files**

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Kotlin |
| UI Framework | Jetpack Compose + Material 3 |
| Camera | CameraX |
| OCR | Google ML Kit (on-device) |
| Serialization | Kotlin Serialization (JSON) |
| Navigation | Compose Navigation |
| Storage | Shared `Documents/ToolSnap/` (USB-accessible) |
| PC Sync | Python 3, SQLite, USB file transfer |

---

## Storage & Export

Sessions are stored in shared external storage at `Documents/ToolSnap/` on the tablet so they're directly accessible via USB file transfer.

### Session Folder Structure

```
Documents/ToolSnap/
└── 2026-02-03_boring-bar-A123/
    ├── manifest.json
    ├── body.jpg            (absent if skipped)
    ├── insert.jpg          (absent if skipped)
    ├── hardware.jpg        (absent if skipped)
    ├── tool_data.jpg       (absent if photo+OCR chosen)
    └── speeds_feeds.jpg    (absent if manual entry or skipped)
```

### Manifest Schema (current)

```json
{
  "sessionId": "uuid-string",
  "toolName": "Boring Bar A123",
  "createdAt": "2026-02-03T14:30:00Z",
  "fields": {
    "body": {
      "status": "CAPTURED",
      "imageFile": "body.jpg",
      "ocrText": null,
      "entryMethod": null,
      "formData": null
    },
    "tool_data": {
      "status": "CAPTURED",
      "imageFile": null,
      "ocrText": "Tool Description: End Mill — Square\nManufacturer: Kennametal\n...",
      "entryMethod": "manual",
      "formData": {
        "entryMethod": "manual",
        "values": {
          "description": "End Mill — Square",
          "manufacturer": "Kennametal",
          "catalog_number": "A3S2000M400",
          "tool_diameter": "1/2\"",
          "insert_grade": "",
          "nose_radius": "0.032\"",
          "flutes": "4",
          "coating": "AlTiN",
          "notes": ""
        }
      }
    },
    "speeds_feeds": {
      "status": "SKIPPED",
      "imageFile": null,
      "ocrText": null,
      "entryMethod": null,
      "formData": null
    }
  },
  "isComplete": false,
  "fieldsCaptured": 2,
  "fieldsSkipped": 1,
  "fieldsTotal": 5
}
```

---

## PC Sync System

### How It Works

1. Capture tools on shop floor using the tablet
2. Plug tablet into PC via USB (File Transfer mode)
3. Run `python toolsnap_sync.py` (or leave `--watch` running to auto-sync)
4. Script scans `<DRIVE>:\Documents\ToolSnap\` for session folders
5. Reads each `manifest.json`, imports into `toolsnap.db` (SQLite)
6. Copies images to local `toolsnap_images/` directory
7. Writes `.synced` marker into each imported session folder on the tablet
8. On the tablet, tap "CLEAR X SYNCED SESSIONS" to delete imported sessions

### PC Database Schema

```sql
-- Sessions table
sessions (
    session_id      TEXT PRIMARY KEY,
    tool_name       TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    is_complete     INTEGER,
    fields_captured INTEGER,
    fields_skipped  INTEGER,
    fields_total    INTEGER,
    folder_name     TEXT NOT NULL,
    synced_at       TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)

-- Fields table (one row per capture field per session)
fields (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    field_name      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    entry_method    TEXT,
    image_file      TEXT,
    local_image     TEXT,
    ocr_text        TEXT,
    form_data       TEXT,              -- full JSON blob
    UNIQUE(session_id, field_name)
)

-- Form values table (one row per key-value pair, for querying)
form_values (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    field_name      TEXT NOT NULL,
    form_key        TEXT NOT NULL,      -- e.g. "manufacturer", "coating"
    form_value      TEXT NOT NULL,      -- e.g. "Kennametal", "AlTiN"
    UNIQUE(session_id, field_name, form_key)
)
```

The `form_values` table enables queries like:

```sql
-- All Kennametal tools
SELECT s.tool_name FROM sessions s
JOIN form_values fv ON s.session_id = fv.session_id
WHERE fv.form_key = 'manufacturer' AND fv.form_value = 'Kennametal';

-- All tools with AlTiN coating
SELECT s.tool_name FROM sessions s
JOIN form_values fv ON s.session_id = fv.session_id
WHERE fv.form_key = 'coating' AND fv.form_value = 'AlTiN';
```

### Sync Script Modes

```
python toolsnap_sync.py              # Auto-detect tablet drive, sync once
python toolsnap_sync.py D:\          # Specify drive letter
python toolsnap_sync.py --watch      # Poll every 3s, auto-sync on connect
```

---

## Shop Floor UI Standards

All screens follow shop-floor sizing for gloved-hand use on a tablet:

| Element | Size |
|---|---|
| Primary action buttons | 72dp height, 22sp text |
| Secondary buttons | 56dp height, 18sp text |
| Dropdown selector boxes | 60dp height, 18sp text |
| Bottom sheet picker rows | 18sp text, 16dp vertical padding |
| Text input fields | 64dp height, 20sp text |
| Screen padding | 20dp |
| Card padding | 20dp |

Color coding: green = captured, yellow = needs attention, blue = synced, red = danger/delete.

---

## Design Principles

1. **Single source of truth** — field definitions in `CaptureConfig.kt`, form templates in `FormTemplates.kt`, paths in `FileUtils.kt`
2. **No copy-paste patterns** — `CaptureStepScreen` reused for all photo fields, `ManualEntryScreen` reused for both form templates
3. **UI contains no business logic** — screens collect input and display state, processing in `core/`
4. **Config is separate from code** — dropdown lists, field orders, sizing constants all in dedicated config files
5. **Manifest is the contract** — the JSON manifest schema is the interface between Android app and PC sync script
6. **Tablet is a capture device** — no local database, no search, no filtering; that's the PC's job

---

## Delivery Artifacts (ZIP Files)

| Zip | Contents | Purpose |
|---|---|---|
| `ts_full_project.zip` | All 33 files from deliveries 1–3 | Full project scaffold, first working build |
| `ts_delivery_4.zip` | 10 updated UI files | Shop floor UI, photo review, crop, EXIF fix |
| `ts_sync_system.zip` | 5 files (4 app + 1 Python) | USB sync system, shared storage, .synced markers |
| `ts_manual_entry.zip` | 8 files | Manual entry forms, DataEntryChoiceScreen, FormTemplates |
| `ts_dropdowns.zip` | 2 files (FormTemplates.kt + ManualEntryScreen.kt) | Dropdown pickers for 6 Tool Data fields |

Each zip uses `C:\toolsnap` as the root path. Extract and overlay onto the project directory.
