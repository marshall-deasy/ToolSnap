package com.toolsnap.core.model

/**
 * Classification for every physical item in the tool catalog.
 *
 * Replaces both `AssemblyType` (what kind of assembly?) and
 * `ComponentType` (body/insert/hardware/accessory?) with a single
 * flat enum. Every tool — whether it's an end mill, an insert, or
 * a torx screw — gets categorized here.
 *
 * [displayName]  — human-readable label in the picker UI
 * [description]  — one-line help text shown below the label
 * [isAssembly]   — true if this category typically needs child
 *                  components linked (inserts, screws, shims).
 *                  A standalone end mill is NOT an assembly.
 *                  A boring bar body IS an assembly (needs inserts).
 *
 * The UI groups these into sections for the picker. The [pickerOrder]
 * list defines the presentation order with section breaks.
 */
enum class ToolCategory(
    val displayName: String,
    val description: String,
    val isAssembly: Boolean = false
) {
    // ── Solid round tools (standalone — body IS the cutter) ──

    END_MILL(
        "End Mill",
        "Solid carbide or HSS end mill"
    ),
    DRILL(
        "Drill",
        "Twist drill, center drill, spot drill"
    ),
    TAP(
        "Tap",
        "Tapping tool — solid or replaceable-tip"
    ),
    REAMER(
        "Reamer",
        "Solid or adjustable reamer"
    ),

    // ── Indexable tool bodies (assemblies — need inserts + hardware) ──

    INDEXABLE_MILL_BODY(
        "Indexable Mill Body",
        "Face mill, shell mill, shoulder mill body",
        isAssembly = true
    ),
    INDEXABLE_DRILL_BODY(
        "Indexable Drill Body",
        "Indexable-insert drill body",
        isAssembly = true
    ),
    BORING_BAR_BODY(
        "Boring Bar Body",
        "Internal boring/turning bar",
        isAssembly = true
    ),
    TURNING_HOLDER(
        "Turning Holder",
        "External turning/facing holder",
        isAssembly = true
    ),
    THREADING_HOLDER(
        "Threading Holder",
        "Thread turning or thread milling holder",
        isAssembly = true
    ),
    GROOVING_HOLDER(
        "Grooving / Parting Holder",
        "Grooving, parting, cut-off holder",
        isAssembly = true
    ),

    // ── Consumables and hardware (standalone — link into assemblies) ──

    INSERT(
        "Insert",
        "Replaceable cutting insert"
    ),
    SCREW(
        "Insert Screw",
        "Torx or hex screw for insert retention"
    ),
    SHIM(
        "Shim / Seat",
        "Carbide shim or seat under insert"
    ),
    CLAMP(
        "Clamp",
        "Top clamp or lever lock"
    ),
    WEDGE(
        "Wedge",
        "Wedge for insert retention"
    ),

    // ── Holders and adapters ──

    HOLDER(
        "Holder / Adapter",
        "Tool holder, collet chuck, hydraulic chuck"
    ),
    COLLET(
        "Collet",
        "ER collet, TG collet, etc."
    ),
    RETENTION_KNOB(
        "Retention Knob",
        "Pull stud / retention knob"
    ),

    // ── Catch-all ──

    OTHER(
        "Other",
        "Anything that doesn't fit standard categories"
    );

    /** Solid round tools — one photo required, OCR available for data. */
    val isSolid: Boolean get() = this in setOf(END_MILL, DRILL, TAP, REAMER)

    /** Indexable tool bodies — assemblies, multiple photos but skippable. */
    val isBody: Boolean get() = isAssembly

    /** Consumables and hardware — one photo required, OCR available. */
    val isConsumable: Boolean get() = this in setOf(INSERT, SCREW, SHIM, CLAMP, WEDGE)

    /** Holders and adapters — one photo required, OCR available. */
    val isHolder: Boolean get() = this in setOf(HOLDER, COLLET, RETENTION_KNOB)

    companion object {
        /**
         * Picker presentation order.  The UI can insert section headers
         * before the first item whose [isAssembly] or item-group changes.
         */
        val pickerOrder: List<ToolCategory> = listOf(
            // Solid tools
            END_MILL, DRILL, TAP, REAMER,
            // Indexable bodies
            INDEXABLE_MILL_BODY, INDEXABLE_DRILL_BODY,
            BORING_BAR_BODY, TURNING_HOLDER,
            THREADING_HOLDER, GROOVING_HOLDER,
            // Consumables / hardware
            INSERT, SCREW, SHIM, CLAMP, WEDGE,
            // Holders
            HOLDER, COLLET, RETENTION_KNOB,
            // Catch-all
            OTHER
        )

        /** Safe parser with fallback to OTHER. */
        fun fromName(name: String): ToolCategory =
            try { valueOf(name) } catch (_: Exception) { OTHER }
    }
}
