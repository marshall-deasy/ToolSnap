# ToolSnap Data Model Reference

## Overview

ToolSnap is an Android app for CNC machinists to photograph and catalog cutting tools on the shop floor. Data is captured on the phone and exported as structured session folders for import into a PC companion application (desktop database + tool management UI).

Each session folder contains a `manifest.json` (V3 schema) plus photo files.

---

## Directory Structure

```
toolsnap_exports/
├── 2026-02-03_boring-bar-A123/
│   ├── manifest.json
│   ├── photo_0.jpg          ← body shot
│   └── photo_1.jpg          ← label close-up
├── 2026-02-03_half-inch-endmill/
│   ├── manifest.json
│   └── photo.jpg
└── 2026-02-01_cnmg-insert-box/
    ├── manifest.json
    └── photo.jpg
```

Folder naming: `{date}_{sanitized-tool-name}`
Photo naming: `photo.jpg` (single), `photo_0.jpg`/`photo_1.jpg`/etc. (multiple)

---

## Manifest V3 Schema

### Top Level

```json
{
  "schemaVersion": 3,
  "exportedAt": "2026-02-03T14:32:10.456Z",
  "tools": [ ... ],
  "components": [ ... ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `schemaVersion` | int | Always `3` for current format |
| `exportedAt` | ISO 8601 string | When the session was finalized |
| `tools` | array of `ToolManifest` | Every physical item captured in this session |
| `components` | array of `ComponentLinkManifest` | Parent→child relationships between tools |

### ToolManifest

```json
{
  "toolId": "a1b2c3d4-boring-bar-body",
  "name": "Boring Bar A123",
  "category": "BORING_BAR_BODY",
  "type": "assembly",
  "status": "CAPTURED",
  "manufacturer": "Kennametal",
  "catalogNumber": "A12-SCLCR3",
  "description": "3/4\" shank boring bar, CCMT insert, right hand",
  "unitSystem": "IMPERIAL",
  "attributes": {
    "shank_type": "Cylindrical",
    "shank_diameter": "0.750\"",
    "coolant_through": "Yes"
  },
  "photos": ["photo_0.jpg", "photo_1.jpg"],
  "tags": ["lathe", "boring"],
  "notes": "Free text notes from the user",
  "createdAt": "2026-02-03T14:30:00.000Z",
  "modifiedAt": "2026-02-03T14:32:10.456Z"
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `toolId` | string (UUID) | no | Globally unique identifier |
| `name` | string | no | User-entered display name |
| `category` | string (enum) | no | Tool classification — see Category table below |
| `type` | `"assembly"` or `"standalone"` | no | Assemblies have child components |
| `status` | string (enum) | no | `CAPTURED`, `PARTIAL`, `SKIPPED`, `PENDING` |
| `manufacturer` | string | yes | Brand name |
| `catalogNumber` | string | yes | Part/catalog number |
| `description` | string | yes | Free-text description |
| `unitSystem` | `"IMPERIAL"` or `"METRIC"` | yes | Defaults to IMPERIAL |
| `attributes` | Map<String, String> | no | Category-specific key→value pairs (see Attributes section) |
| `photos` | List<String> | no | Filenames (not paths) of photos in the session folder |
| `tags` | List<String> | no | User-applied tags |
| `notes` | string | yes | Free-text notes |
| `createdAt` | ISO 8601 | no | When tool was first created |
| `modifiedAt` | ISO 8601 | no | Last modification time |

### ComponentLinkManifest

Links a child tool to a parent assembly. The same child can appear in multiple assemblies (e.g., a CNMG insert fits multiple boring bars).

```json
{
  "parentToolId": "a1b2c3d4-boring-bar-body",
  "childToolId": "e5f6g7h8-ccmt-insert",
  "role": "INSERT",
  "quantity": 1,
  "notes": "CCMT 21.51 finishing insert — pocket 1"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `parentToolId` | string | References the assembly's `toolId` |
| `childToolId` | string | References the component's `toolId` |
| `role` | string (enum) | How the child participates — see Roles below |
| `quantity` | int | How many of this component (default 1) |
| `notes` | string? | Optional context |

---

## Tool Categories

### Solid Round Tools (standalone — body IS the cutter)

| Enum Value | Display Name | Assembly | Description |
|-----------|-------------|----------|-------------|
| `END_MILL` | End Mill | No | Solid carbide or HSS end mill |
| `DRILL` | Drill | No | Twist drill, center drill, spot drill |
| `TAP` | Tap | No | Tapping tool — solid or replaceable-tip |
| `REAMER` | Reamer | No | Solid or adjustable reamer |

### Indexable Tool Bodies (assemblies — need inserts + hardware)

| Enum Value | Display Name | Assembly | Description |
|-----------|-------------|----------|-------------|
| `INDEXABLE_MILL_BODY` | Indexable Mill Body | **Yes** | Face mill, shell mill, shoulder mill body |
| `INDEXABLE_DRILL_BODY` | Indexable Drill Body | **Yes** | Indexable-insert drill body |
| `BORING_BAR_BODY` | Boring Bar Body | **Yes** | Internal boring/turning bar |
| `TURNING_HOLDER` | Turning Holder | **Yes** | External turning/facing holder |
| `THREADING_HOLDER` | Threading Holder | **Yes** | Thread turning or thread milling holder |
| `GROOVING_HOLDER` | Grooving / Parting Holder | **Yes** | Grooving, parting, cut-off holder |

### Consumables & Hardware (standalone — linked into assemblies)

| Enum Value | Display Name | Description |
|-----------|-------------|-------------|
| `INSERT` | Insert | Replaceable cutting insert |
| `SCREW` | Insert Screw | Torx or hex screw for insert retention |
| `SHIM` | Shim / Seat | Carbide shim or seat under insert |
| `CLAMP` | Clamp | Top clamp or lever lock |
| `WEDGE` | Wedge | Wedge for insert retention |

### Holders & Adapters

| Enum Value | Display Name | Description |
|-----------|-------------|-------------|
| `HOLDER` | Holder / Adapter | Tool holder, collet chuck, hydraulic chuck |
| `COLLET` | Collet | ER collet, TG collet, etc. |
| `RETENTION_KNOB` | Retention Knob | Pull stud / retention knob |

### Catch-all

| Enum Value | Display Name | Description |
|-----------|-------------|-------------|
| `OTHER` | Other | Anything that doesn't fit standard categories |

---

## Category-Specific Attributes

Each category has its own set of attribute keys. The `attributes` map uses these keys.

### Solid Round Tools (END_MILL, DRILL, TAP, REAMER)

| Key | Label | Type | Required | Notes |
|-----|-------|------|----------|-------|
| `cutting_diameter` | Cutting/Drill/Tap/Reamer Diameter | dropdown | **Yes** | From standard diameter list |
| `shank_diameter` | Shank Diameter | dropdown | No | |
| `flutes` | Number of Flutes | dropdown | **Yes** | 1-12+ |
| `flute_length` | Flute / Cutting Length | text | No | e.g. "1.000\"" |
| `helix_angle` | Helix Angle | text | No | END_MILL only |
| `point_angle` | Point Angle | text | No | DRILL only |
| `thread_pitch` | Thread Pitch / TPI | text | No | TAP only |
| `thread_form` | Thread Form | text | No | TAP only, e.g. "UNC", "M" |
| `coating` | Coating | dropdown | No | AlTiN, TiAlN, TiN, etc. |
| `material` | Body Material | dropdown | No | Solid Carbide, HSS, etc. |
| `overall_length` | Overall Length (OAL) | text | No | |
| `coolant_through` | Coolant Through | dropdown | No | Yes/No |

### Indexable Tool Bodies

| Key | Label | Type | Notes |
|-----|-------|------|-------|
| `cutting_diameter` | Cutting Diameter | dropdown | Mill/drill bodies |
| `shank_type` | Shank / Interface | dropdown | CAT40, BT40, HSK63A, etc. |
| `shank_diameter` | Shank Diameter | dropdown | Boring bars |
| `pocket_size` | Insert Pocket Size | text | e.g. "CC / CCMT 21.51" |
| `projection` | Projection / Gauge Length | text | Boring bars |
| `coolant_through` | Coolant Through | dropdown | |
| `overall_length` | Overall Length | text | |
| `shank_size` | Shank Size | text | Turning/grooving holders |
| `hand` | Hand of Cut | dropdown | Right/Left/Neutral |
| `groove_width` | Blade / Groove Width | text | Grooving holders |
| `max_depth` | Max Cut Depth | text | Grooving holders |

### Inserts

| Key | Label | Type | Required | Notes |
|-----|-------|------|----------|-------|
| `iso_designation` | ISO Insert Designation | text | No | e.g. "CNMG 120408" |
| `insert_shape` | Insert Shape | dropdown | **Yes** | Rhombic 80°, Square, Triangle, etc. |
| `insert_size` | IC (Inscribed Circle) | dropdown | No | |
| `thickness` | Insert Thickness | dropdown | No | |
| `nose_radius` | Nose / Corner Radius | dropdown | No | |
| `grade` | Insert Grade | text | No | e.g. "KC5010", "GC4325" |
| `workpiece_material` | Target Workpiece Material | dropdown | No | P/M/K/N/S/H groups |
| `coating` | Insert Coating | dropdown | No | |
| `chipbreaker` | Chipbreaker Style | text | No | e.g. "LF", "PM", "MF" |
| `hand` | Hand of Cut | dropdown | No | |
| `rake` | Rake Angle | dropdown | No | Positive/Negative/Neutral |

### Other Small Components

**Screw:** `size`, `drive_type`, `torque_spec`
**Shim:** `shim_type`, `pocket_size`
**Clamp:** `clamp_type`, `size`
**Wedge:** `wedge_type`, `size`

### Holders & Adapters

| Key | Label | Notes |
|-----|-------|-------|
| `shank_type` | Interface Type | CAT40, BT30, HSK, etc. |
| `bore_size` | Bore / Collet Size | e.g. "ER32", "3/4\" bore" |
| `gauge_length` | Gauge Length | |
| `overall_length` | Overall Length | |
| `coolant_through` | Coolant Through | |
| `collet_system` | Collet System | Collets only |
| `thread_size` | Thread Size | Retention knobs only |

---

## Universal Fields (all non-INSERT categories)

These are prepended to every category's field list:

| Key | Label | Type | Required |
|-----|-------|------|----------|
| `manufacturer` | Manufacturer / Brand | dropdown | **Yes** |
| `catalog_number` | Catalog / Part Number | text | **Yes** |

And appended:

| Key | Label | Type |
|-----|-------|------|
| `notes` | Notes | multiline |

---

## Component Roles

| Enum Value | Display Name | Description |
|-----------|-------------|-------------|
| `INSERT` | Insert | Primary cutting insert |
| `WIPER_INSERT` | Wiper Insert | Wiper/finishing insert |
| `SCREW` | Screw | Insert retention screw |
| `SHIM` | Shim / Seat | Carbide seat under insert |
| `CLAMP` | Clamp | Top clamp or lever lock |
| `WEDGE` | Wedge | Insert retention wedge |
| `COOLANT_PLUG` | Coolant Plug / Nozzle | Coolant delivery component |
| `COLLET` | Collet | Collet in a holder |
| `ADAPTER` | Adapter / Extension | Extension or reducer |
| `OTHER` | Other | Anything else |

---

## Tool Status Values

| Value | Resolved | Needs Attention | Description |
|-------|----------|-----------------|-------------|
| `PENDING` | No | Yes | Not yet started |
| `CAPTURED` | Yes | No | Fully captured — photo and/or data |
| `PARTIAL` | No | Yes | Some data entered, not complete |
| `SKIPPED` | Yes | No | User explicitly skipped |

---

## Import Logic Notes

When the PC companion imports a session folder:

1. Parse `manifest.json` — check `schemaVersion` is 3
2. For each tool in `tools[]`:
   - Insert into `Tools` table (or merge by `catalogNumber` if duplicate)
   - Copy photos to the PC's image store, updating paths
   - Map `category` string to the category enum
   - Store `attributes` as key-value pairs or in category-specific columns
3. For each link in `components[]`:
   - Insert into `Components` junction table
   - Both `parentToolId` and `childToolId` must exist in `Tools`
   - A child tool can appear in multiple assemblies (many-to-many)
4. Build `Compatibility` table from component links:
   - If insert X is linked to boring bar Y, they're compatible
   - Compatibility is derived, not stored in the manifest

### Cross-Session References

A component captured in session A can be referenced by an assembly in session B. The `childToolId` UUID is the linking key. The PC companion should:
- Check if a `toolId` already exists before inserting
- Merge/update if the same tool appears in multiple sessions
- Maintain referential integrity in the Components table

### Photo Storage

Photos in the manifest are filenames relative to the session folder. The PC companion should:
- Copy photos to a central image store (e.g., `images/{toolId}/photo_0.jpg`)
- Store the new path in the database
- Optionally generate thumbnails for the UI

---

## Sample Data

This package includes 3 sample sessions demonstrating the data model:

### Session 1: Boring Bar Assembly (`2026-02-03_boring-bar-A123/`)
- **Parent:** Kennametal A12-SCLCR3 boring bar body (BORING_BAR_BODY, assembly)
- **Child 1:** CCMT 21.51 LF KC5010 insert (INSERT) — role: INSERT
- **Child 2:** M3.5 Torx screw (SCREW) — role: SCREW
- **Child 3:** CCMT carbide shim seat (SHIM) — role: SHIM
- Demonstrates: assembly with 3 linked components, multiple photos on body

### Session 2: Standalone End Mill (`2026-02-03_half-inch-endmill/`)
- **Tool:** Helical Solutions 1/2" 4FL AlTiN end mill (END_MILL, standalone)
- Demonstrates: solid tool with full attributes, single photo, no components

### Session 3: Insert Box (`2026-02-01_cnmg-insert-box/`)
- **Tool 1:** Sandvik CNMG 120408-PM GC4325 (INSERT, standalone)
- **Tool 2:** Sandvik CNMG 120408-WMX GC4325 wiper (INSERT, standalone)
- Demonstrates: multiple standalone inserts in one session, later linkable to assemblies
