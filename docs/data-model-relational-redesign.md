# ToolSnap V2 Data Model — Relational Redesign

**Purpose:** Replace the tree-based assembly→component hierarchy with a flat relational model where every physical item is a first-class row, assemblies are built by linking items together, and inserts can belong to multiple holders.

**Status:** Design document. Supersedes the original V2 Data Model Design.

**What's already built (Phases 1–2):** AssemblyType picker, ComponentTemplates field routing, per-type form definitions, CoatingData integration hook, ManifestV2 serialization. These survive largely intact — the field routing and dropdown lists don't care whether the data lives in a tree or a flat table.

---

## 1. Why the Tree Model Was Wrong

The original V2 design treated assemblies as the primary object and components as children. A CNMG insert "belonged to" a specific boring bar. That's wrong in two ways:

**Inserts are shared.** A CNMG 432 fits dozens of different holders. The insert lives in a drawer, has its own stock count, its own reorder point. It's not a child of any single parent — it's an independent item that participates in many relationships.

**Hardware is shared too.** The same M3.5 torx screw appears in 15 different tool assemblies. Tracking it as a child of each one means 15 separate records with 15 separate reorder workflows for the same physical SKU.

The tree model also conflated "what is this tool" (catalog data) with "where is it and how many do we have" (inventory data). Those change at different rates and are managed by different people.

---

## 2. Four-Table Architecture

```
┌─────────────────────────────────────────────────────┐
│  Tools                                              │
│  Every physical item gets a row.                    │
│  category: what kind of thing it is                 │
│  type: assembly | standalone                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐         ┌───────────────────┐     │
│  │  Components   │         │  Compatibility    │     │
│  │  junction:    │         │  many-to-many:    │     │
│  │  parent tool  │         │  insert ↔ body    │     │
│  │  → child tool │         │                   │     │
│  │  + role       │         │                   │     │
│  └──────────────┘         └───────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Inventory                                    │   │
│  │  stock level, location, reorder point, vendor │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 2.1 Tools

Every physical item in the shop — end mills, boring bar bodies, inserts, screws, shims, collet chucks — is a row in Tools. No hierarchy in the table itself.

```
Tools
─────
toolId          TEXT PRIMARY KEY     (UUID)
name            TEXT NOT NULL        ("1/2\" 4-Flute AlTiN End Mill", "CNMG 432 KC5010")
category        TEXT NOT NULL        (from ToolCategory enum)
type            TEXT NOT NULL        ("assembly" | "standalone")
manufacturer    TEXT                 ("Kennametal", "Sandvik Coromant")
catalogNumber   TEXT                 (manufacturer's part number)
description     TEXT                 (free text)
unitSystem      TEXT                 ("IMPERIAL" | "METRIC")
attributes      TEXT                 (JSON map of category-specific fields)
notes           TEXT
tags            TEXT                 (JSON array of strings)
photos          TEXT                 (JSON array of photo filenames)
createdAt       TEXT                 (ISO-8601)
modifiedAt      TEXT                 (ISO-8601)
```

**category** classifies the item and determines which form fields appear (same role AssemblyType played before, but now it applies to every item, not just assemblies):

```kotlin
enum class ToolCategory(
    val displayName: String,
    val description: String
) {
    // Solid round tools (standalone — body IS the cutter)
    END_MILL("End Mill", "Solid carbide or HSS end mill"),
    DRILL("Drill", "Twist drill, center drill, spot drill"),
    TAP("Tap", "Tapping tool — solid or replaceable-tip"),
    REAMER("Reamer", "Solid or adjustable reamer"),

    // Indexable tool bodies (assemblies — need inserts + hardware)
    INDEXABLE_MILL_BODY("Indexable Mill Body", "Face mill, shell mill, shoulder mill body"),
    INDEXABLE_DRILL_BODY("Indexable Drill Body", "Indexable-insert drill body"),
    BORING_BAR_BODY("Boring Bar Body", "Internal boring/turning bar"),
    TURNING_HOLDER("Turning Holder", "External turning/facing holder"),
    THREADING_HOLDER("Threading Holder", "Thread turning or thread milling holder"),
    GROOVING_HOLDER("Grooving / Parting Holder", "Grooving, parting, cut-off holder"),

    // Consumables and hardware (standalone items that link into assemblies)
    INSERT("Insert", "Replaceable cutting insert"),
    SCREW("Insert Screw", "Torx or hex screw for insert retention"),
    SHIM("Shim / Seat", "Carbide shim or seat under insert"),
    CLAMP("Clamp", "Top clamp or lever lock"),
    WEDGE("Wedge", "Wedge for insert retention"),

    // Holders and adapters
    HOLDER("Holder / Adapter", "Tool holder, collet chuck, hydraulic chuck"),
    COLLET("Collet", "ER collet, TG collet, etc."),
    RETENTION_KNOB("Retention Knob", "Pull stud / retention knob"),

    // Catch-all
    OTHER("Other", "Anything that doesn't fit standard categories");
}
```

**type** is either `"assembly"` (a boring bar body that uses inserts and hardware) or `"standalone"` (an end mill, a single insert, a screw). An assembly is just a tool that has rows in the Components table pointing to it as the parent.

**attributes** is a JSON map of category-specific fields. The keys are determined by ComponentTemplates.fieldsFor(category) — the same routing engine from Phase 1, just keyed on ToolCategory instead of ComponentType + AssemblyType:

```json
// END_MILL attributes
{
    "cutting_diameter": "1/2\"",
    "shank_diameter": "1/2\"",
    "flutes": "4",
    "flute_length": "1.000\"",
    "helix_angle": "35°",
    "coating": "AlTiN",
    "material": "Solid Carbide",
    "overall_length": "3.000\"",
    "coolant_through": "No"
}

// INSERT attributes
{
    "iso_designation": "CNMG 120408",
    "insert_shape": "C — Rhombic 80°",
    "insert_size": "1/2\" IC",
    "thickness": "3/16\"",
    "nose_radius": "0.032\"",
    "grade": "KC5010",
    "coating": "TiAlN",
    "chipbreaker": "MF",
    "hand": "Right",
    "rake": "Negative"
}

// SCREW attributes
{
    "size": "M3.5 x 8",
    "drive_type": "Torx T-15",
    "torque_spec": "2.5 N·m"
}
```

### 2.2 Components

Junction table linking items into assemblies. The parent is always an assembly-type tool. The child is any tool — inserts, screws, shims.

```
Components
──────────
parentToolId    TEXT NOT NULL    (FK → Tools.toolId — the assembly)
childToolId     TEXT NOT NULL    (FK → Tools.toolId — the consumable/hardware)
role            TEXT NOT NULL    ("insert", "screw", "shim", "seat",
                                 "clamp", "wedge", "coolant_plug",
                                 "wiper_insert", "collet", "adapter")
quantity        INTEGER          (how many of this item per assembly, default 1)
notes           TEXT             (e.g. "pocket 1 only", "left-hand seat")
PRIMARY KEY (parentToolId, childToolId, role)
```

**role** captures *how* the child participates. A boring bar might have:

```
parentToolId    childToolId                 role        qty
────────────    ─────────────────────       ────        ───
boring-bar-1    cnmg-432-kc5010             insert      1
boring-bar-1    sandvik-5513-020-15         screw       1
boring-bar-1    sandvik-shim-CDB            shim        1
```

A face mill with both standard and wiper inserts:

```
parentToolId    childToolId                 role            qty
────────────    ─────────────────────       ────────────    ───
face-mill-1     apkt-1604-ic808             insert          5
face-mill-1     apkt-1604-wiper-ic808       wiper_insert    1
face-mill-1     iscar-screw-m4x10           screw           6
```

### 2.3 Compatibility

Many-to-many map for inserts that fit multiple bodies. This is reference data — "which inserts can physically go in which holders" — independent of what's actually assembled right now.

```
Compatibility
─────────────
bodyToolId      TEXT NOT NULL    (FK → Tools.toolId — an indexable body)
insertToolId    TEXT NOT NULL    (FK → Tools.toolId — an insert)
fitNotes        TEXT             ("standard pocket", "requires shim CDB", "wiper position only")
PRIMARY KEY (bodyToolId, insertToolId)
```

This answers: "I just broke my CNMG 432 KC5010. What other inserts fit this boring bar?" or "I have a drawer full of WNMG inserts — which holders accept them?"

### 2.4 Inventory

Operational data separated from the tool catalog. Changes independently, different cadence, potentially different users.

```
Inventory
─────────
toolId          TEXT PRIMARY KEY (FK → Tools.toolId)
location        TEXT            ("CAB-03:DWR-07", scanned from QR label)
quantityOnHand  INTEGER         (current stock)
reorderPoint    INTEGER         (alert when stock drops to this level)
reorderQty      INTEGER         (how many to order)
preferredVendor TEXT            ("MSC Industrial", "KBC Tools")
vendorPartNumber TEXT           (vendor's SKU — may differ from mfg catalog#)
unitCost        REAL            (last known price)
lastCountedAt   TEXT            (ISO-8601 — when stock was last verified)
notes           TEXT
```

---

## 3. What This Changes About the Phone App

### 3.1 Capture Flow Redesign

The wizard shifts from "create an assembly, fill in its children" to two distinct flows:

**Flow A — Capture a single tool:**
1. Category picker (what are you capturing?)
2. Name entry
3. Photo(s)
4. Category-specific data form (from ComponentTemplates)
5. Save → one row in Tools

**Flow B — Build an assembly:**
1. Category picker → user selects an indexable body category
2. Name entry
3. Photo + data for the body (same as Flow A)
4. "Add components" step:
   - Search existing tools by name/catalog# → link
   - Or capture a new insert/screw/shim inline → save to Tools, then link
   - Set role and quantity for each linked item
5. Save → one row in Tools (type=assembly) + rows in Components

Most captures will be Flow A. Flow B is for when the machinist is setting up a new assembly and wants to record which insert/hardware goes with which body.

### 3.2 On-Device vs. Desktop

The phone captures tool data and assembly relationships. The manifest faithfully records both so the PC can ingest into the four-table schema.

| Concern | Phone | Desktop |
|---------|-------|---------|
| Capture new tools | ✓ | |
| Build assemblies (link items) | ✓ | ✓ |
| Category-specific forms | ✓ | |
| Compatibility table | | ✓ (built from assembly data + manual entry) |
| Inventory tracking | Future (QR scan) | ✓ (primary) |
| Deduplication | | ✓ (match on catalogNumber + manufacturer) |
| Search / filter | Basic | Full |
| BOM / reorder export | | ✓ |
| QR location scanning | Future | Labels printed here |

### 3.3 Manifest Schema

The manifest is a flat export of one or more tools and their relationships. The PC ingests this into the relational tables.

```json
{
    "schemaVersion": 3,
    "exportedAt": "2026-02-04T...",

    "tools": [
        {
            "toolId": "uuid-1",
            "name": "A32S-SCLCL 12 Boring Bar",
            "category": "BORING_BAR_BODY",
            "type": "assembly",
            "manufacturer": "Sandvik Coromant",
            "catalogNumber": "A32S-SCLCL 12",
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
            "createdAt": "2026-02-04T...",
            "modifiedAt": "2026-02-04T..."
        },
        {
            "toolId": "uuid-2",
            "name": "CCMT 32.51 KC5010",
            "category": "INSERT",
            "type": "standalone",
            "manufacturer": "Kennametal",
            "catalogNumber": "CCMT 32.51 KC5010",
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
            "createdAt": "2026-02-04T...",
            "modifiedAt": "2026-02-04T..."
        },
        {
            "toolId": "uuid-3",
            "name": "Sandvik Screw 5513 020-15",
            "category": "SCREW",
            "type": "standalone",
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
            "createdAt": "2026-02-04T...",
            "modifiedAt": "2026-02-04T..."
        }
    ],

    "components": [
        {
            "parentToolId": "uuid-1",
            "childToolId": "uuid-2",
            "role": "insert",
            "quantity": 1,
            "notes": null
        },
        {
            "parentToolId": "uuid-1",
            "childToolId": "uuid-3",
            "role": "screw",
            "quantity": 1,
            "notes": null
        }
    ]
}
```

Note: no Compatibility or Inventory data in the manifest. Those are desktop-only concerns. The PC *derives* Compatibility entries from the Components data across all imported manifests ("this insert appears in these 4 assemblies, so it's compatible with all 4 bodies").

---

## 4. Form Field Routing

ComponentTemplates.fieldsFor() still works — it just takes a ToolCategory instead of a ComponentType + AssemblyType pair. The field lists from Phase 1 map directly:

| ToolCategory | Fields From |
|---|---|
| END_MILL | Phase 1 bodyFieldsFor(END_MILL) |
| DRILL | Phase 1 bodyFieldsFor(DRILL_SOLID) |
| TAP | Phase 1 bodyFieldsFor(TAP) |
| REAMER | Phase 1 bodyFieldsFor(REAMER) |
| INDEXABLE_MILL_BODY | Phase 1 bodyFieldsFor(INDEXABLE_MILL) |
| INDEXABLE_DRILL_BODY | Phase 1 bodyFieldsFor(DRILL_INDEXABLE) |
| BORING_BAR_BODY | Phase 1 bodyFieldsFor(BORING_BAR) |
| TURNING_HOLDER | Phase 1 bodyFieldsFor(TURNING_TOOL) |
| THREADING_HOLDER | Phase 1 bodyFieldsFor(THREADING_TOOL) |
| GROOVING_HOLDER | Phase 1 bodyFieldsFor(GROOVING_PARTING) |
| INSERT | Phase 1 insertFields() |
| SCREW | hardwareFields() — filtered to screw-relevant subset |
| SHIM | hardwareFields() — filtered to shim-relevant subset |
| CLAMP | hardwareFields() — filtered to clamp-relevant subset |
| HOLDER | Phase 1 bodyFieldsFor(HOLDER_ONLY) |
| OTHER | Phase 1 bodyFieldsFor(CUSTOM) |

The dropdown option lists, coating recommendations, and unit-aware switching all carry forward unchanged.

---

## 5. Coating Recommendation Integration

Unchanged from Phase 1. When a user captures an INSERT, the workpiece_material dropdown triggers reorderCoatingsForMaterial() to surface recommended coatings at the top of the coating dropdown. The standalone Coating Guide screen remains as a reference tool.

---

## 6. V1 → V3 Migration

V1 manifests (no schemaVersion) and V2 manifests (schemaVersion: 2) both need migration paths.

### V1 Migration

```
V1 session → one assembly-type tool (category = OTHER, type = assembly)
V1 body photo → tool photo
V1 insert photo → standalone INSERT tool, linked via Components
V1 hardware photo → standalone OTHER tool, linked via Components
V1 tool_data formData → merged into parent tool's attributes
```

### V2 Migration

```
V2 assembly → tool (category from assemblyType mapping, type = assembly)
V2 components → individual tool rows + Components links
V2 attributes → tool attributes (unchanged format)
```

Both migrations happen on the PC side during import. The phone app only writes V3 manifests going forward. V1/V2 manifest files on disk are never modified.

---

## 7. What Survives From Phases 1–2

| Phase 1–2 Artifact | Status |
|---|---|
| AssemblyType enum | **Replaced** by ToolCategory (broader, covers standalone items too) |
| ComponentType enum | **Removed** — every item is just a Tool with a category |
| ComponentStatus enum | **Survives** as ToolStatus (PENDING, CAPTURED, PARTIAL, SKIPPED) |
| UnitSystem enum | **Survives** unchanged |
| ToolComponent data class | **Replaced** by Tool data class |
| ToolAssembly data class | **Removed** — Tool with type=assembly + Components rows |
| ComponentTemplates | **Survives** — re-keyed on ToolCategory |
| CoatingData + reorderCoatingsForMaterial() | **Survives** unchanged |
| ManifestV2 serialization | **Replaced** by ManifestV3 (flat tool array + components array) |
| AssemblyTypePickerScreen | **Becomes** CategoryPickerScreen (same UI, broader list) |
| WizardNavHost TYPE_SELECT phase | **Survives** — shows CategoryPickerScreen |
| NameEntryScreen | **Survives** unchanged |
| SessionManager.setAssemblyType() | **Becomes** setToolCategory() |

---

## 8. Implementation Plan

### Phase 3A — Data Model Refactor

Replace the tree model classes with relational ones. New files:

- `Tool.kt` — single tool row (replaces ToolAssembly + ToolComponent)
- `ToolCategory.kt` — replaces AssemblyType + ComponentType
- `ToolStatus.kt` — renamed from ComponentStatus
- `ComponentLink.kt` — one row in the Components junction table
- `ManifestV3.kt` — flat serialization (tools array + components array)
- Update `ComponentTemplates.kt` — re-key on ToolCategory

Delete:
- `ToolAssembly.kt`
- `ToolComponent.kt`
- `AssemblyType.kt`
- `ComponentType.kt`
- `ComponentStatus.kt`
- `ManifestV2.kt`

### Phase 3B — Capture Flow

- CategoryPickerScreen replaces AssemblyTypePickerScreen
- Single-tool capture: category → name → photo → form → save
- Assembly capture: same as above, plus "link components" step
- Linking flow: search existing tools or capture new inline

### Phase 4 — Search & Tags

- Search tools by category, attributes, tags, manufacturer
- Filter by category, coating, diameter, manufacturer
- Tag management UI

### Phase 5 — Inventory & QR (future)

- Inventory fields on tools (location, stock, reorder point)
- QR code scanning for location population
- Low-stock alerts
- Reorder workflow (BOM export per vendor)

---

## 9. Design Decisions

1. **Every item is a Tool.** No separate tables for inserts vs. bodies vs. screws. The `category` field classifies them, and form routing gives each category its own fields. This means a screw and an end mill are peers in the database — both searchable, both have photos, both have catalog numbers, both orderable.

2. **Assemblies are Tools with children.** A boring bar assembly is a Tool row with `type=assembly`. Its insert, screw, and shim are also Tool rows. The Components junction table links them. This means you can ask "which assemblies use this insert?" — a query the tree model couldn't answer.

3. **Compatibility is derived, not captured.** The phone doesn't ask "what else does this insert fit?" The PC builds the Compatibility table by observing which inserts appear in which assemblies across all imported data. Over time, the compatibility map grows organically from real usage. Manual entries can supplement it on the desktop.

4. **Inventory is desktop-first.** Stock levels, reorder points, and vendor data live in the Inventory table managed from the PC. The phone captures tool identity; the desktop manages tool logistics. QR scanning on the phone is a future convenience for populating location fields, not for full inventory management.

5. **Deduplication stays on the PC.** When the same CNMG insert is captured in three different assemblies from the phone, the PC database matches on catalogNumber + manufacturer and consolidates to one Tool row with three Components links. The phone manifests carry full data for each capture — simple, offline-safe, no cross-session dependencies.

6. **Manifest V3 is a flat export.** No nesting, no hierarchy. Just an array of tools and an array of component links. The PC imports both arrays into their respective tables. This makes the manifest format a direct mirror of the relational schema, simplifying the import pipeline.

7. **Speeds & Feeds excluded.** S&F is reference-only data that doesn't describe the tool or drive purchasing decisions. It belongs in setup sheets, programs, or a dedicated feeds-and-speeds app — not a tool catalog. Assembly-level photos can capture manufacturer S&F charts if needed.
