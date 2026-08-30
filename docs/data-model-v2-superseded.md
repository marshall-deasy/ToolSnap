# ToolSnap V2 Data Model Design

**Purpose:** Replace the current flat five-field session structure with a component-typed architecture that gives each component type (body, insert, hardware) its own relevant fields, supports a searchable database with tool families, and enables purchasing workflows.

**Status:** Design draft — no code changes yet.

---

## 1. What's Wrong with V1

The current model has five fixed `CaptureField` entries (Body, Insert, Hardware, Tool Data, Speeds & Feeds). The Tool Data form applies the same 9 fields — description, manufacturer, catalog number, diameter, insert grade, nose radius, flutes, coating, notes — to every session regardless of what the tool actually is.

Problems this creates:

- A **boring bar body** gets asked about flutes and coating. Neither applies.
- An **insert** gets asked about tool diameter (the body's dimension, not the insert's IC).
- A **face mill body** has a different set of critical dimensions than a drill body.
- There's no way to record **multiple inserts** per assembly (e.g., a face mill with both wiper and standard inserts).
- The Speeds & Feeds data is tied to the session, not to a material/operation combination — so you can't record separate parameters for roughing aluminum vs. finishing steel with the same tool.
- There's no **part number** field on the body or insert records, making purchasing impossible.
- The flat structure makes search nearly useless — you can't query "show me all CNMG inserts" because insert data is buried in a generic form blob.

---

## 2. V2 Data Architecture

### 2.1 Core Hierarchy

```
ToolAssembly (replaces CaptureSession)
│
├── assemblyName: String              (required — what V1 calls "toolName")
├── assemblyType: AssemblyType        (NEW — classifies the whole assembly)
├── sessionId: String
├── createdAt: Instant
├── modifiedAt: Instant               (NEW)
│
├── components: List<ToolComponent>   (NEW — replaces flat field list)
│   ├── ToolComponent [BODY]
│   ├── ToolComponent [INSERT]        (can have 0, 1, or multiple)
│   ├── ToolComponent [HARDWARE]
│   └── ToolComponent [ACCESSORY]     (NEW — adapters, extensions, coolant tubes)
│
├── speedsFeedsRecords: List<SpeedsFeedsRecord>  (NEW — multiple per assembly)
│
├── tags: List<String>                (NEW — user-defined grouping)
├── notes: String                     (NEW — assembly-level notes)
└── photos: List<AssemblyPhoto>       (NEW — assembly-level overview photos)
```

### 2.2 AssemblyType

Classifies the overall tool assembly. Determines which component types are expected and which fields are shown first.

```kotlin
enum class AssemblyType(
    val displayName: String,
    val expectedComponents: List<ComponentType>,
    val description: String
) {
    END_MILL(
        "End Mill",
        listOf(ComponentType.BODY),
        "Solid carbide or HSS — body IS the cutting tool"
    ),
    INDEXABLE_MILL(
        "Indexable Mill",
        listOf(ComponentType.BODY, ComponentType.INSERT, ComponentType.HARDWARE),
        "Face mill, shell mill, shoulder mill with replaceable inserts"
    ),
    DRILL_SOLID(
        "Solid Drill",
        listOf(ComponentType.BODY),
        "Twist drill, center drill, spot drill"
    ),
    DRILL_INDEXABLE(
        "Indexable Drill",
        listOf(ComponentType.BODY, ComponentType.INSERT, ComponentType.HARDWARE),
        "Indexable-insert drill (e.g. Sandvik CoroDrill)"
    ),
    BORING_BAR(
        "Boring Bar",
        listOf(ComponentType.BODY, ComponentType.INSERT, ComponentType.HARDWARE),
        "Internal boring/turning bar"
    ),
    TURNING_TOOL(
        "Turning Tool",
        listOf(ComponentType.BODY, ComponentType.INSERT, ComponentType.HARDWARE),
        "External turning/facing holder"
    ),
    THREADING_TOOL(
        "Threading Tool",
        listOf(ComponentType.BODY, ComponentType.INSERT, ComponentType.HARDWARE),
        "Thread turning or thread milling"
    ),
    GROOVING_PARTING(
        "Grooving / Parting",
        listOf(ComponentType.BODY, ComponentType.INSERT, ComponentType.HARDWARE),
        "Grooving, parting, cut-off tools"
    ),
    TAP(
        "Tap",
        listOf(ComponentType.BODY),
        "Tapping tool — solid or replaceable-tip"
    ),
    REAMER(
        "Reamer",
        listOf(ComponentType.BODY),
        "Solid or adjustable reamer"
    ),
    HOLDER_ONLY(
        "Holder / Adapter",
        listOf(ComponentType.BODY, ComponentType.ACCESSORY),
        "Tool holder, collet chuck, hydraulic chuck, shrink fit"
    ),
    CUSTOM(
        "Custom / Other",
        listOf(ComponentType.BODY),
        "Anything that doesn't fit standard categories"
    );
}
```

### 2.3 ToolComponent

Each component in the assembly. The `componentType` determines which form fields appear.

```kotlin
data class ToolComponent(
    val componentId: String = UUID.randomUUID().toString(),
    val componentType: ComponentType,
    val status: ComponentStatus = ComponentStatus.PENDING,

    // === Universal fields (every component has these) ===
    val manufacturer: String? = null,
    val catalogNumber: String? = null,      // the purchasable part number
    val description: String? = null,        // free text or from dropdown
    val unitSystem: UnitSystem = UnitSystem.IMPERIAL,  // metric/imperial toggle

    // === Photo ===
    val photoPath: String? = null,

    // === Type-specific attributes ===
    // Stored as typed map — keys defined by ComponentType templates
    val attributes: MutableMap<String, String> = mutableMapOf(),

    // === Purchasing ===
    val vendor: String? = null,             // where you buy it
    val vendorPartNumber: String? = null,   // vendor's SKU (may differ from mfg catalog#)
    val unitCost: Double? = null,           // last known price
    val notes: String? = null
)

enum class UnitSystem {
    IMPERIAL, METRIC
}
```

### 2.4 ComponentType and Per-Type Attributes

```kotlin
enum class ComponentType(
    val displayName: String
) {
    BODY("Tool Body"),
    INSERT("Insert"),
    HARDWARE("Hardware"),
    ACCESSORY("Accessory");
}
```

**Body attributes** (varies by assembly type — see Section 3):

| Key                 | Label                    | Input     | Applies To                          |
|---------------------|--------------------------|-----------|-------------------------------------|
| `shank_type`        | Shank / Interface        | Dropdown  | All bodies                          |
| `cutting_diameter`  | Cutting Diameter         | Dropdown  | End mills, drills, reamers, taps (unit-aware) |
| `shank_diameter`    | Shank Diameter           | Dropdown  | Solid round-shank tools (unit-aware) |
| `overall_length`    | Overall Length (OAL)     | Text      | All bodies (unit-aware)             |
| `flute_length`      | Flute / Cutting Length   | Text      | End mills, drills (unit-aware)      |
| `flutes`            | Number of Flutes         | Dropdown  | End mills, drills, reamers          |
| `helix_angle`       | Helix Angle              | Text      | End mills                           |
| `projection`        | Projection / Gauge Length| Text      | Boring bars, turning holders (unit-aware) |
| `coating`           | Body Coating             | Dropdown  | Solid carbide/HSS tools             |
| `material`          | Body Material            | Dropdown  | All (carbide, HSS, steel)           |
| `pocket_size`       | Insert Pocket Size       | Text      | Indexable bodies                    |
| `coolant_through`   | Coolant Through          | Dropdown  | All (Yes / No)                      |

**Insert attributes:**

| Key                 | Label                    | Input     | Notes                               |
|---------------------|--------------------------|-----------|---------------------------------------|
| `iso_designation`   | ISO Insert Designation   | Text      | Full string, e.g. "CNMG 120408" — parsed on PC side for search/filter |
| `insert_shape`      | Insert Shape             | Dropdown  | C, D, R, S, T, V, W + full names     |
| `insert_size`       | IC (Inscribed Circle)    | Dropdown  | Standard IC sizes (imperial or metric per unitSystem) |
| `thickness`         | Insert Thickness         | Dropdown  | Standard thicknesses (unit-aware)     |
| `nose_radius`       | Nose / Corner Radius     | Dropdown  | (existing list, unit-aware)           |
| `grade`             | Insert Grade             | Text      | e.g. KC5010, IC808, GC4325           |
| `coating`           | Insert Coating           | Dropdown  | (existing list + material-based reco) |
| `chipbreaker`       | Chipbreaker Style        | Text      | e.g. MF, PM, GC, -MR                 |
| `hand`              | Hand of Cut              | Dropdown  | Right / Left / Neutral                |
| `rake`              | Rake Angle               | Dropdown  | Positive / Negative / Neutral         |
| `workpiece_material`| Target Workpiece Material| Dropdown  | (11 materials from CoatingData — triggers coating reorder) |

**Hardware attributes** (each hardware piece is its own component — a screw and a shim are two separate HARDWARE entries, each with its own photo and part number):

| Key                 | Label                    | Input     | Notes                               |
|---------------------|--------------------------|-----------|---------------------------------------|
| `hardware_type`     | Type                     | Dropdown  | Screw, Clamp, Shim, Wedge, Seat, etc.|
| `size`              | Size                     | Text      | e.g. M3.5 x 8, T-15                  |
| `torque_spec`       | Torque Spec              | Text      | e.g. 2.5 N·m                         |
| `quantity`          | Quantity per Assembly     | Number    | How many needed                       |

**Accessory attributes:**

| Key                 | Label                    | Input     | Notes                               |
|---------------------|--------------------------|-----------|---------------------------------------|
| `accessory_type`    | Type                     | Dropdown  | Adapter, Extension, Reducer, Coolant Tube |
| `interface_from`    | Input Interface          | Dropdown  | e.g. CAT40, HSK63A                   |
| `interface_to`      | Output Interface         | Dropdown  | e.g. ER32, Weldon 3/4                |
| `length`            | Length                   | Text      | Extension/adapter length              |

### 2.5 SpeedsFeedsRecord

Decoupled from the session — one assembly can have parameters for multiple materials and operations.

```kotlin
data class SpeedsFeedsRecord(
    val recordId: String = UUID.randomUUID().toString(),
    val workpieceMaterial: String,       // from the 11-material dropdown
    val materialSpec: String? = null,    // specific alloy, e.g. "4140", "Ti-6Al-4V"
    val operation: String,               // Roughing, Finishing, Profiling, etc.
    val sfm: Double? = null,
    val rpm: Int? = null,
    val feedPerRev: Double? = null,      // IPR
    val feedPerTooth: Double? = null,    // IPT (milling)
    val feedPerMin: Double? = null,      // IPM
    val depthOfCut: String? = null,
    val widthOfCut: String? = null,
    val coolant: String? = null,         // Flood, Mist, Air, Dry, MQL
    val notes: String? = null,
    val photoPath: String? = null        // photo of speed/feed chart
)
```

### 2.6 ComponentStatus

Replaces `FieldStatus` with component-level tracking.

```kotlin
enum class ComponentStatus {
    PENDING,            // not yet addressed
    CAPTURED,           // has photo and/or data
    PARTIAL,            // NEW — has some data but not complete
    SKIPPED;            // user explicitly skipped

    val isResolved: Boolean
        get() = this != PENDING
}
```

---

## 3. Form Template Routing

The key insight: which fields appear depends on **both** the component type **and** the assembly type.

```
User selects AssemblyType
  → determines expected ComponentTypes
    → each ComponentType gets a form template
      → template is filtered by AssemblyType context
```

Example: `ComponentType.BODY` shows different fields depending on context:

| Assembly Type    | Body Fields Shown                                                |
|------------------|------------------------------------------------------------------|
| END_MILL         | cutting_diameter, shank_diameter, flutes, flute_length, helix_angle, coating, material, overall_length, coolant_through |
| INDEXABLE_MILL   | cutting_diameter, pocket_size, shank_type, coolant_through, overall_length |
| BORING_BAR       | shank_type, shank_diameter, projection, pocket_size, coolant_through, overall_length |
| TURNING_TOOL     | shank_type (square shank size), projection, pocket_size, hand |
| DRILL_SOLID      | cutting_diameter, shank_diameter, flutes, flute_length, point_angle, coating, material, coolant_through |

Implementation:

```kotlin
object ComponentTemplates {
    fun fieldsFor(
        componentType: ComponentType,
        assemblyType: AssemblyType
    ): List<FormField> {
        return when (componentType) {
            ComponentType.BODY -> bodyFieldsFor(assemblyType)
            ComponentType.INSERT -> insertFields()
            ComponentType.HARDWARE -> hardwareFields()
            ComponentType.ACCESSORY -> accessoryFields()
        }
    }

    private fun bodyFieldsFor(assemblyType: AssemblyType): List<FormField> {
        val base = listOf(manufacturerField, catalogNumberField)
        val specific = when (assemblyType) {
            AssemblyType.END_MILL -> listOf(
                cuttingDiameter, shankDiameter, flutes,
                fluteLength, helixAngle, coating, bodyMaterial,
                overallLength, coolantThrough
            )
            AssemblyType.BORING_BAR -> listOf(
                shankType, shankDiameter, projection,
                pocketSize, coolantThrough, overallLength
            )
            // ... etc
        }
        return base + specific + listOf(notesField)
    }
}
```

This replaces the monolithic `FormTemplates.templateFor()` with context-aware routing. No N/A buttons needed — irrelevant fields simply don't appear.

---

## 4. Coating Recommendation Integration

The `materialToCoatings` map from `CoatingData.kt` plugs directly into the insert form.

When the user selects a `workpiece_material` on an insert component, the `coating` dropdown reorders to show best-fit coatings first. Each recommended coating shows its reason string as a subtitle in the dropdown.

```
Insert form:
  [Target Workpiece Material]  →  "Stainless Steel"

  [Insert Coating]
    ★ AlTiN — Handles high heat from work-hardening stainless grades
    ★ TiAlN — Thermal barrier reduces crater wear on austenitic stainless
    ★ AlCrN — Excellent oxidation resistance at elevated temps
    ─── other coatings ───
    CrN
    CVD Diamond
    DLC
    ...
```

The recommendation doesn't restrict choices — it just surfaces the best options at the top.

---

## 5. Manifest V2 Schema

The JSON manifest evolves to support the new structure. V1 manifests are still readable (migration in Section 8).

```json
{
    "schemaVersion": 2,
    "assemblyId": "uuid",
    "assemblyName": "1/2\" 4-Flute AlTiN End Mill",
    "assemblyType": "END_MILL",
    "createdAt": "2026-02-04T...",
    "modifiedAt": "2026-02-04T...",
    "tags": ["aluminum-roughing", "cell-3"],

    "components": [
        {
            "componentId": "uuid",
            "componentType": "BODY",
            "status": "CAPTURED",
            "manufacturer": "Helical Solutions",
            "catalogNumber": "H45AL-RN-30500",
            "description": "End Mill — Square",
            "unitSystem": "IMPERIAL",
            "photoFile": "body.jpg",
            "attributes": {
                "cutting_diameter": "1/2\"",
                "shank_diameter": "1/2\"",
                "flutes": "4",
                "flute_length": "1.000\"",
                "coating": "AlTiN",
                "material": "Solid Carbide",
                "overall_length": "3.000\"",
                "coolant_through": "No"
            },
            "vendor": "MSC Industrial",
            "vendorPartNumber": "08734521",
            "unitCost": 89.50,
            "notes": null
        }
    ],

    "speedsFeedsRecords": [
        {
            "recordId": "uuid",
            "workpieceMaterial": "Aluminum",
            "materialSpec": "6061-T6",
            "operation": "Roughing",
            "sfm": 1000,
            "rpm": 7640,
            "feedPerTooth": 0.004,
            "feedPerMin": 122.2,
            "depthOfCut": "0.500\"",
            "widthOfCut": "0.250\"",
            "coolant": "Flood",
            "notes": "Adaptive toolpath, 10% stepover",
            "photoFile": null
        },
        {
            "recordId": "uuid",
            "workpieceMaterial": "Steel",
            "materialSpec": "4140",
            "operation": "Finishing",
            "sfm": 350,
            "rpm": 2675,
            "feedPerTooth": 0.002,
            "feedPerMin": 21.4,
            "depthOfCut": "0.020\"",
            "widthOfCut": "full width",
            "coolant": "Flood",
            "notes": null,
            "photoFile": "speeds_feeds_steel.jpg"
        }
    ],

    "notes": "Go-to rougher for the Haas VF-2",
    "assemblyPhotos": ["overview.jpg"]
}
```

---

## 6. Database & Search Design

### 6.1 Search Queries the Model Must Support

| Query | What It Hits |
|-------|-------------|
| "all CNMG inserts" | `components[].attributes.iso_designation LIKE 'CNMG%'` |
| "AlTiN coated end mills" | `assemblyType = END_MILL AND components[].attributes.coating = 'AlTiN'` |
| "Kennametal boring bars" | `assemblyType = BORING_BAR AND components[].manufacturer = 'Kennametal'` |
| "tools for Inconel" | `speedsFeedsRecords[].workpieceMaterial = 'Nickel Alloys / Inconel'` OR `components[type=INSERT].attributes.workpiece_material = '...'` |
| "1/2 inch end mills" | `assemblyType = END_MILL AND components[type=BODY].attributes.cutting_diameter = '1/2"'` |
| "reorder insert KC5010" | `components[type=INSERT].attributes.grade = 'KC5010'` → pull catalogNumber + vendor |

### 6.2 Tool Families

A **tool family** is a group of assemblies that share a common body but use different inserts or parameters. Examples:

- A boring bar body that takes CCMT, DCMT, or TCMT inserts depending on the operation
- A face mill body loaded with different insert grades for steel vs. aluminum
- The same end mill with different speeds/feeds records for different materials

Implementation: `tags` field on the assembly. Family grouping is a UI concern (group by tag), not a schema concern. This keeps the data model flat and avoids complex relational joins on the phone.

For the PC database, families could become a first-class relation, but for the Android capture app, tags are sufficient.

### 6.3 Purchasing Workflow

Each `ToolComponent` carries `manufacturer`, `catalogNumber`, `vendor`, `vendorPartNumber`, and `unitCost`. A purchasing flow works like this:

1. User browses the DB and selects assemblies they need to reorder
2. System extracts all components with `catalogNumber` populated
3. Groups by vendor → generates a BOM (bill of materials) per vendor
4. Export as CSV, email draft, or clipboard text

BOM line item:

```
Vendor: MSC Industrial
  Qty 1  |  Helical H45AL-RN-30500  |  MSC# 08734521  |  $89.50
  Qty 10 |  Kennametal CNMG120408   |  MSC# 06298714  |  $12.30 ea
```

This is a PC-side feature. The Android app just captures the data — the desktop DB does the aggregation and export.

---

## 7. Wizard Flow Changes

### 7.1 New Capture Flow

```
1. Enter Assembly Name         (same as V1)
2. Select Assembly Type        (NEW — dropdown of AssemblyType values)
3. For each expected component:
     a. Show component header   ("Insert #1 of 1")
     b. Three-way choice:       PHOTO  |  ENTER DATA  |  SKIP
        - PHOTO → camera → review → crop → (OCR if applicable) → save
        - ENTER DATA → type-specific form (fields from ComponentTemplates)
        - SKIP → mark skipped
     c. After completing, ask:  "Add another [Insert]?"  →  YES adds Insert #2
4. Speeds & Feeds              (optional — "Add speed/feed record?")
     a. Select workpiece material
     b. Fill operation params
     c. "Add another?" for additional materials/operations
5. Assembly Notes + Tags       (optional)
6. Review & Save
```

### 7.2 What Changes vs. V1

| V1 | V2 |
|----|-----|
| Fixed 5 fields in fixed order | Dynamic component list based on assembly type |
| One Tool Data form for everything | Per-component-type forms with assembly-type filtering |
| One Speeds & Feeds record | Multiple S&F records per assembly |
| No assembly type classification | Assembly type drives the entire workflow |
| All forms identical | Irrelevant fields never shown |
| No purchasing fields | Every component carries part# and vendor |

---

## 8. V1 → V2 Migration

Existing V1 sessions must remain readable. Migration strategy:

1. **Read path:** When loading a manifest, check for `schemaVersion`. If missing, treat as V1.
2. **V1 → V2 conversion:**
   - `toolName` → `assemblyName`
   - `assemblyType` → `CUSTOM` (can't infer from V1 data)
   - V1 `BODY` field → `ToolComponent(type=BODY, photoPath=..., status=...)`
   - V1 `INSERT` field → `ToolComponent(type=INSERT, photoPath=..., status=...)`
   - V1 `HARDWARE` field → `ToolComponent(type=HARDWARE, photoPath=..., status=...)`
   - V1 `TOOL_DATA` formData → merged into body component's attributes (best effort — keys like `description`, `manufacturer`, `coating` map directly)
   - V1 `SPEEDS_FEEDS` formData → one `SpeedsFeedsRecord` (fields map 1:1)
3. **Write path:** All new saves use V2 schema. Migrated sessions are written as V2 on next edit.
4. **No destructive migration.** V1 manifest files are never deleted. V2 manifest is written alongside as `manifest_v2.json` until full migration is confirmed.

---

## 9. Implementation Phases

### Phase 1 — Data Model (no UI changes)

New Kotlin files only. No existing files modified.

- `ToolAssembly.kt` — new top-level model
- `ToolComponent.kt` — component with typed attributes
- `ComponentType.kt` — enum with display names
- `AssemblyType.kt` — enum with expected components
- `SpeedsFeedsRecord.kt` — decoupled S&F record
- `ComponentTemplates.kt` — per-type form field routing
- `ManifestV2.kt` — V2 serialization classes
- Update `CoatingData.kt` — add integration hook for insert coating dropdown

### Phase 2 — Assembly Type Selection

- Add assembly type picker to wizard (after name entry, before capture)
- Wire component list to assembly type
- Existing photo capture flow unchanged

### Phase 3 — Per-Type Forms

- Replace monolithic Tool Data form with type-aware forms
- Implement `ComponentTemplates.fieldsFor()` routing
- Coating dropdown reacts to workpiece material selection
- "Add another component" flow for multiple inserts

### Phase 4 — Multi-Record Speeds & Feeds

- Replace single S&F form with record-based flow
- Add/edit/delete individual S&F records from detail screen
- Each record tied to a workpiece material + operation

### Phase 5 — Search & Tags

- Assembly-level tags (free text, reusable suggestions)
- Search across assemblies by type, component attributes, tags
- Filter by manufacturer, coating, material, diameter

### Phase 6 — Purchasing Fields & BOM Export (PC side)

- Vendor/cost fields on components
- BOM aggregation on the desktop DB
- Export to CSV / email draft

---

## 10. File Impact Summary

| Current File | Change |
|-------------|--------|
| `CaptureField.kt` | Deprecated — replaced by ComponentType |
| `CaptureSession.kt` | Deprecated — replaced by ToolAssembly |
| `FieldStatus.kt` | Evolves into ComponentStatus |
| `CaptureConfig.kt` | Absorbs assembly type routing |
| `FormTemplates.kt` | Replaced by ComponentTemplates |
| `JsonUtils.kt` | Adds V2 serialization + V1 migration reader |
| `SessionManager.kt` | Evolves into AssemblyManager |
| `WizardNavHost.kt` | Phase 2-3: assembly type step, dynamic component iteration |
| `ManualEntryScreen.kt` | Phase 3: receives per-type form fields (mostly unchanged) |
| `SessionDetailScreen.kt` | Phase 3: shows components instead of flat fields |
| `HomeScreen.kt` | Phase 5: search/filter UI |
| `CoatingData.kt` | Phase 3: integration with insert coating dropdown |

---

## 11. Design Decisions (Resolved)

1. **Insert ISO designation parsing.** The Android app collects the full ISO string (e.g. "CNMG 120408") as a single text field. Parsing into shape/clearance/tolerance/type/size/thickness/nose_radius happens on the PC side for filtering and order-building. This keeps the phone app simple — the machinist just types or OCRs the designation — and puts the query complexity where it belongs (desktop DB with a real search UI).

2. **Metric vs. Imperial.** Tooling is mixed. The app presents a **unit system toggle** (Imperial / Metric) at the assembly or component level. When Imperial is selected, diameter and length dropdowns show fractional inches. When Metric is selected, they show millimeter values. Both sets are maintained in the dropdown data. The toggle persists as a preference (most users will pick one and leave it, but can flip per-tool when entering a metric-only cutter). The `attributes` map stores the value as entered — "1/2\"" or "12.7mm" — no automatic conversion.

3. **Photo per component vs. per assembly.** One photo per component is sufficient for now. Hardware gets its own component entry with one photo — if there are multiple hardware items (screws, shims, clamps), each is a separate `ToolComponent` of type `HARDWARE`. This means a session with a screw AND a shim gets two HARDWARE components, each with its own photo and part number. This is cleaner than cramming multiple items into one photo and aligns with the purchasing model (each hardware piece is a separate purchasable SKU).

4. **Offline-first PC sync.** Folder scan with manifest validation. The PC database scans the ToolSnap shared storage directory, reads each `manifest.json` (or `manifest_v2.json`), and imports/updates its internal DB. Conflict resolution: manifest `modifiedAt` timestamp wins (last-write-wins). The PC app maintains a `last_scan_at` timestamp and only re-reads folders modified after that. Safe, simple, no daemon process needed. If a folder's manifest is corrupt or missing, the PC app flags it for manual review rather than silently skipping it.

5. **Shared component library.** Duplicate on capture, deduplicate on the PC side. When the machinist captures a CNMG 120408 KC5010 insert in two different assemblies, both manifests carry the full component data independently. The PC database deduplicates by matching on `catalogNumber` + `manufacturer` (or `iso_designation` + `grade` for inserts without catalog numbers). This creates a shared component library on the PC that shows "this insert is used in 4 assemblies" and enables bulk reorder across all of them. The Android app stays simple — no cross-session references, no sync issues.
