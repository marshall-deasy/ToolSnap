# ToolSnap PC Database & Backend — Project Brief

## What This Is

ToolSnap is a CNC tooling catalog system. The Android phone app photographs and catalogs cutting tools on the shop floor. The PC application is the backend: it imports captured data, manages a relational database of all tooling, handles inventory tracking, deduplication, compatibility mapping, search, and purchasing/reorder workflows.

The phone exports flat JSON manifests (one per capture session) into a shared storage directory. The PC scans that directory, reads the manifests, and ingests everything into a SQLite database with four core tables.

---

## Database Schema

### Tools

Every physical item in the shop — end mills, boring bar bodies, inserts, screws, shims, collets — is a row in Tools. There is no separate table per item type. The `category` field classifies the item, and the `attributes` JSON map carries category-specific fields.

```sql
CREATE TABLE Tools (
    toolId          TEXT PRIMARY KEY,    -- UUID from phone or generated on PC
    name            TEXT NOT NULL,       -- human display name
    category        TEXT NOT NULL,       -- from ToolCategory enum (see below)
    type            TEXT NOT NULL,       -- "assembly" | "standalone"
    manufacturer    TEXT,                -- "Kennametal", "Sandvik Coromant"
    catalogNumber   TEXT,                -- manufacturer's part number
    description     TEXT,                -- free-text
    unitSystem      TEXT,                -- "IMPERIAL" | "METRIC"
    attributes      TEXT,                -- JSON object of category-specific key/value pairs
    notes           TEXT,
    tags            TEXT,                -- JSON array of strings, e.g. ["lathe-1", "aluminum"]
    photos          TEXT,                -- JSON array of photo filenames (relative to session dir)
    createdAt       TEXT NOT NULL,       -- ISO-8601
    modifiedAt      TEXT NOT NULL        -- ISO-8601
);

CREATE INDEX idx_tools_category ON Tools(category);
CREATE INDEX idx_tools_manufacturer ON Tools(manufacturer);
CREATE INDEX idx_tools_catalogNumber ON Tools(catalogNumber);
```

**ToolCategory values** (the `category` column):

Solid tools (standalone — body IS the cutter):
- `END_MILL`, `DRILL`, `TAP`, `REAMER`

Indexable tool bodies (assemblies — need inserts and hardware):
- `INDEXABLE_MILL_BODY`, `INDEXABLE_DRILL_BODY`, `BORING_BAR_BODY`
- `TURNING_HOLDER`, `THREADING_HOLDER`, `GROOVING_HOLDER`

Consumables and hardware (standalone items that link into assemblies):
- `INSERT`, `SCREW`, `SHIM`, `CLAMP`, `WEDGE`

Holders and adapters:
- `HOLDER`, `COLLET`, `RETENTION_KNOB`

Catch-all:
- `OTHER`

**Attributes by category** — the JSON `attributes` column carries these keys depending on category:

END_MILL: `cutting_diameter`, `shank_diameter`, `flutes`, `flute_length`, `helix_angle`, `coating`, `material`, `overall_length`, `coolant_through`

DRILL: `cutting_diameter`, `shank_diameter`, `flutes`, `flute_length`, `point_angle`, `coating`, `material`, `coolant_through`, `overall_length`

TAP: `cutting_diameter`, `thread_pitch`, `thread_form`, `flutes`, `coating`, `material`, `overall_length`, `coolant_through`

REAMER: `cutting_diameter`, `shank_diameter`, `flutes`, `flute_length`, `coating`, `material`, `overall_length`, `coolant_through`

INDEXABLE_MILL_BODY: `cutting_diameter`, `pocket_size`, `shank_type`, `coolant_through`, `overall_length`

INDEXABLE_DRILL_BODY: `cutting_diameter`, `shank_type`, `pocket_size`, `coolant_through`, `overall_length`

BORING_BAR_BODY: `shank_type`, `shank_diameter`, `projection`, `pocket_size`, `coolant_through`, `overall_length`

TURNING_HOLDER: `shank_type`, `shank_size`, `projection`, `pocket_size`, `hand`

THREADING_HOLDER: `shank_type`, `shank_size`, `thread_type`, `pocket_size`, `hand`

GROOVING_HOLDER: `shank_type`, `shank_size`, `groove_width`, `max_depth`, `hand`

INSERT: `iso_designation`, `insert_shape`, `insert_size`, `thickness`, `nose_radius`, `grade`, `workpiece_material`, `coating`, `chipbreaker`, `hand`, `rake`

SCREW: `size`, `drive_type`, `torque_spec`

SHIM: `shim_type`, `pocket_size`

CLAMP: `clamp_type`, `size`

WEDGE: `wedge_type`, `size`

HOLDER: `shank_type`, `bore_size`, `gauge_length`, `overall_length`, `coolant_through`

COLLET: `collet_system`, `bore_size`

RETENTION_KNOB: `shank_type`, `thread_size`

OTHER: `description_custom`, `shank_type`, `cutting_diameter`, `coating`, `material`, `overall_length`

All attribute values are stored as strings, exactly as entered (e.g. `"1/2\""`, `"12.7mm"`, `"4"`, `"Yes"`). No automatic unit conversion.

### Components

Junction table linking child tools to parent assemblies. A boring bar body (parent) has rows linking to its insert, screw, and shim (children). The same insert can appear as a child of multiple parent assemblies.

```sql
CREATE TABLE Components (
    parentToolId    TEXT NOT NULL REFERENCES Tools(toolId),
    childToolId     TEXT NOT NULL REFERENCES Tools(toolId),
    role            TEXT NOT NULL,    -- "INSERT", "WIPER_INSERT", "SCREW", "SHIM",
                                     -- "CLAMP", "WEDGE", "COOLANT_PLUG", "COLLET",
                                     -- "ADAPTER", "OTHER"
    quantity        INTEGER DEFAULT 1,
    notes           TEXT,
    PRIMARY KEY (parentToolId, childToolId, role)
);

CREATE INDEX idx_components_child ON Components(childToolId);
```

### Compatibility

Many-to-many reference data: which inserts physically fit which bodies. This is about *potential* fit, not *current* assembly. The PC builds this initially by observing which inserts appear in which assemblies across all imported data. Manual entries supplement it.

```sql
CREATE TABLE Compatibility (
    bodyToolId      TEXT NOT NULL REFERENCES Tools(toolId),
    insertToolId    TEXT NOT NULL REFERENCES Tools(toolId),
    fitNotes        TEXT,       -- "standard pocket", "requires shim CDB", "wiper position only"
    PRIMARY KEY (bodyToolId, insertToolId)
);

CREATE INDEX idx_compat_insert ON Compatibility(insertToolId);
```

### Inventory

Operational data — stock levels, drawer locations, reorder points, vendor info. Separated from the tool catalog because it changes at a different rate and may be managed by different people. One row per tool (not every tool needs an Inventory row).

```sql
CREATE TABLE Inventory (
    toolId          TEXT PRIMARY KEY REFERENCES Tools(toolId),
    location        TEXT,            -- "CAB-03:DWR-07" (QR-scannable location ID)
    quantityOnHand  INTEGER DEFAULT 0,
    reorderPoint    INTEGER DEFAULT 0,
    reorderQty      INTEGER DEFAULT 0,
    preferredVendor TEXT,            -- "MSC Industrial", "KBC Tools"
    vendorPartNumber TEXT,           -- vendor's SKU (may differ from manufacturer catalog#)
    unitCost        REAL,            -- last known price
    lastCountedAt   TEXT,            -- ISO-8601
    notes           TEXT
);

CREATE INDEX idx_inventory_location ON Inventory(location);
CREATE INDEX idx_inventory_vendor ON Inventory(preferredVendor);
```

---

## Manifest Format (Phone → PC)

The phone writes a `manifest.json` into each session folder. The PC scans the shared storage directory, reads each manifest, and ingests the data.

### V3 Manifest (current)

```json
{
    "schemaVersion": 3,
    "exportedAt": "2026-02-04T14:30:00Z",

    "tools": [
        {
            "toolId": "uuid-string",
            "name": "A32S-SCLCL 12 Boring Bar",
            "category": "BORING_BAR_BODY",
            "type": "assembly",
            "status": "CAPTURED",
            "manufacturer": "Sandvik Coromant",
            "catalogNumber": "A32S-SCLCL 12",
            "description": null,
            "unitSystem": "IMPERIAL",
            "attributes": {
                "shank_type": "Straight Shank (Weldon)",
                "shank_diameter": "1-1/4\"",
                "projection": "6.000\"",
                "pocket_size": "CC / CCMT 3(2.5)_",
                "coolant_through": "Yes",
                "overall_length": "10.0\""
            },
            "photos": ["boring_bar_body.jpg"],
            "tags": ["lathe-1", "boring"],
            "notes": null,
            "createdAt": "2026-02-04T14:30:00Z",
            "modifiedAt": "2026-02-04T14:30:00Z"
        },
        {
            "toolId": "uuid-string-2",
            "name": "CCMT 32.51 KC5010",
            "category": "INSERT",
            "type": "standalone",
            "status": "CAPTURED",
            "manufacturer": "Kennametal",
            "catalogNumber": "CCMT 32.51 KC5010",
            "description": null,
            "unitSystem": "IMPERIAL",
            "attributes": {
                "iso_designation": "CCMT 09T304",
                "insert_shape": "C — Rhombic 80°",
                "insert_size": "3/8\" IC",
                "thickness": "1/8\"",
                "nose_radius": "0.016\"",
                "grade": "KC5010",
                "coating": "TiAlN",
                "chipbreaker": "UP",
                "hand": "Right",
                "rake": "Positive"
            },
            "photos": ["insert_top.jpg"],
            "tags": [],
            "notes": null,
            "createdAt": "2026-02-04T14:30:00Z",
            "modifiedAt": "2026-02-04T14:30:00Z"
        },
        {
            "toolId": "uuid-string-3",
            "name": "Sandvik Screw 5513 020-15",
            "category": "SCREW",
            "type": "standalone",
            "status": "CAPTURED",
            "manufacturer": "Sandvik Coromant",
            "catalogNumber": "5513 020-15",
            "unitSystem": "METRIC",
            "attributes": {
                "size": "M3.5 x 8",
                "drive_type": "Torx T-15",
                "torque_spec": "2.5 N·m"
            },
            "photos": ["screw.jpg"],
            "tags": [],
            "notes": null,
            "createdAt": "2026-02-04T14:30:00Z",
            "modifiedAt": "2026-02-04T14:30:00Z"
        }
    ],

    "components": [
        {
            "parentToolId": "uuid-string",
            "childToolId": "uuid-string-2",
            "role": "INSERT",
            "quantity": 1,
            "notes": null
        },
        {
            "parentToolId": "uuid-string",
            "childToolId": "uuid-string-3",
            "role": "SCREW",
            "quantity": 1,
            "notes": null
        }
    ]
}
```

### Legacy Manifests

The PC must also handle two older formats:

**V1** (no `schemaVersion` key): Flat session with fields `body`, `insert`, `hardware`, `tool_data`. Migration: treat the whole session as one `OTHER`-category assembly. `tool_data.formData.values` become the parent tool's attributes. Insert and hardware photos become linked standalone tools.

**V2** (`schemaVersion: 2`): Tree-structured assembly with typed components (BODY, INSERT, HARDWARE, ACCESSORY). Migration: map `assemblyType` to the corresponding ToolCategory, split components into individual Tool rows, create Components links. The `assemblyType` → `ToolCategory` mapping is: `END_MILL`→`END_MILL`, `INDEXABLE_MILL`→`INDEXABLE_MILL_BODY`, `DRILL_SOLID`→`DRILL`, `DRILL_INDEXABLE`→`INDEXABLE_DRILL_BODY`, `BORING_BAR`→`BORING_BAR_BODY`, `TURNING_TOOL`→`TURNING_HOLDER`, `THREADING_TOOL`→`THREADING_HOLDER`, `GROOVING_PARTING`→`GROOVING_HOLDER`, `TAP`→`TAP`, `REAMER`→`REAMER`, `HOLDER_ONLY`→`HOLDER`, `CUSTOM`→`OTHER`.

---

## Import Pipeline

The PC scans a configured directory (the phone's shared storage location, synced via USB, cloud, or network share). Each subfolder is a capture session containing a `manifest.json` and photo files.

### Scan Logic

1. List all subdirectories in the import path.
2. For each directory, check if `manifest.json` exists and is readable.
3. Parse the manifest. Auto-detect version: no `schemaVersion` key → V1, `schemaVersion: 2` → V2, `schemaVersion: 3` → V3.
4. Migrate V1/V2 to V3 format in memory (never modify the original manifest file on disk).
5. For each tool in the manifest, run the deduplication check (see below).
6. Upsert tools into the Tools table. Upsert component links into the Components table.
7. Derive Compatibility rows from Components data (see below).
8. Track which manifests have been imported (e.g. a metadata table or a hash of the manifest content) to avoid re-processing unchanged sessions on subsequent scans.

### Deduplication

When the same physical insert is captured in multiple assemblies from the phone, each manifest carries a full copy of that insert's data with a different `toolId`. The PC deduplicates by matching on `catalogNumber + manufacturer` (case-insensitive, whitespace-normalized).

Rules:
- If a tool with the same `catalogNumber` and `manufacturer` already exists in the DB, reuse the existing `toolId`. Do not create a duplicate row.
- If the incoming manifest has a newer `modifiedAt` timestamp, update the existing row's attributes/photos/tags (last-write-wins).
- When reusing an existing tool, remap any Components rows that reference the manifest's `toolId` to point to the existing DB `toolId` instead.
- Tools without a `catalogNumber` are never deduplicated — each gets its own row.
- For inserts, a secondary dedup key is `iso_designation + grade` (from attributes) when `catalogNumber` is missing but both fields are populated.

### Compatibility Derivation

After import, scan the Components table for all rows where the child tool's category is `INSERT` (or `WIPER_INSERT` role). For each (parentToolId, childToolId) pair where the parent's category is an indexable body type, insert a row into the Compatibility table if one doesn't already exist. Over time, this organically builds the "which inserts fit which bodies" reference map from actual usage.

---

## Core Features

### Search & Filter

The primary query interface. Users search across all tools with filters:

- **Category filter**: show only END_MILLs, only INSERTs, etc.
- **Free text search**: matches against name, manufacturer, catalogNumber, description, and JSON attribute values.
- **Attribute filters**: category-aware. When filtering INSERTs, offer insert_shape, grade, coating dropdowns. When filtering END_MILLs, offer cutting_diameter, flutes, coating.
- **Tag filter**: select one or more tags.
- **Assembly membership**: "show all tools used in assembly X" or "show all assemblies that use tool Y."

### Assembly View

For any tool with `type=assembly`, show the parent tool details plus all linked children from the Components table with their roles and quantities. Allow editing: add/remove component links, change quantities, change roles.

### Compatibility View

For any INSERT, show all bodies it's known to fit (from Compatibility table). For any indexable body, show all compatible inserts. Allow manual additions to the Compatibility table.

### Inventory Management

- Set stock levels, reorder points, preferred vendor, unit cost, and drawer/cabinet location for any tool.
- Low-stock alerts: tools where `quantityOnHand <= reorderPoint`.
- Reorder report: group low-stock items by `preferredVendor`, show quantities needed (`reorderQty`), unit costs, and total cost per vendor.
- BOM export: for a given assembly, list all component tools with their inventory status, vendor info, and costs. Export as CSV.

### QR Location Labels

The PC generates and prints QR code labels encoding location IDs like `TS:CAB-03:DWR-07`. These get stuck on tooling cabinet drawers. The phone (future feature) scans these to populate the `location` field during inventory checks. The PC needs a label generation/printing UI — input a location ID, output a printable QR code.

---

## Technology Preferences

- **Database**: SQLite (single file, no server, portable, can live on a network share if needed).
- **Language**: Python is fine. C# is fine. Whatever gets a clean desktop UI fastest.
- **UI**: Needs to be a real desktop GUI, not a web app. The shop PC may not have reliable internet. The UI should be functional and fast — this is a tool crib management app, not a consumer product. Tables, filters, search bars, detail panels.
- **Photo display**: The app needs to display tool photos from the imported session folders. Photos are JPEGs, typically 1–2 MB each.

---

## What NOT to Build

- **Speeds & Feeds**: Excluded from scope. S&F is reference-only data about how you use a tool on specific materials, not about what the tool is. Machinists pull S&F from manufacturer catalogs or proven programs.
- **User authentication**: Single-user desktop app. No login.
- **Cloud sync**: The phone-to-PC sync is folder-based (USB, network share, cloud drive folder). The PC app just reads a local directory.
- **Real-time phone connection**: No Bluetooth, no Wi-Fi direct, no live sync. Import is batch: phone captures, syncs folder, PC scans and imports.
