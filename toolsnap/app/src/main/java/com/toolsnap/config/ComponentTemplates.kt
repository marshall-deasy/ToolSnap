package com.toolsnap.config

import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.model.UnitSystem

/**
 * Form field routing for the relational V2 data model.
 *
 * Every [ToolCategory] maps to a specific set of form fields.
 * The single entry point is [fieldsFor]. Dropdown option lists
 * live in [DropdownOptions] — this file only handles routing.
 */
object ComponentTemplates {

    /** Sentinel — re-exported from DropdownOptions for backward compat. */
    const val OTHER_OPTION = DropdownOptions.OTHER_OPTION

    /**
     * Get the form fields for a tool of the given category.
     */
    fun fieldsFor(
        category: ToolCategory,
        unitSystem: UnitSystem = UnitSystem.IMPERIAL
    ): List<FormField> {
        val d = DropdownOptions
        val diameters = d.diameters(unitSystem)
        val noseRadii = d.noseRadii(unitSystem)
        val base = listOf(manufacturerField, catalogNumberField)

        val specific: List<FormField> = when (category) {

            // ── Solid round tools ───────────────────────────────────
            ToolCategory.END_MILL -> listOf(
                dropdown("cutting_diameter", "Cutting Diameter", diameters, required = true),
                dropdown("shank_diameter", "Shank Diameter", diameters),
                dropdown("flutes", "Number of Flutes", d.flutes, required = true),
                text("flute_length", "Flute / Cutting Length", "e.g. 1.000\""),
                dropdown("coating", "Coating", d.coatings),
                dropdown("material", "Body Material", d.bodyMaterials),
                text("overall_length", "Overall Length (OAL)", "e.g. 3.000\""),
                dropdown("coolant_through", "Coolant Through", d.boolean),
            )

            ToolCategory.DRILL -> listOf(
                dropdown("cutting_diameter", "Drill Diameter", diameters, required = true),
                dropdown("shank_diameter", "Shank Diameter", diameters),
                dropdown("flutes", "Number of Flutes", d.flutes, required = true),
                text("flute_length", "Flute Length", "e.g. 3.500\""),
                text("point_angle", "Point Angle", "e.g. 135\u00B0"),
                dropdown("coating", "Coating", d.coatings),
                dropdown("material", "Body Material", d.bodyMaterials),
                dropdown("coolant_through", "Coolant Through", d.boolean),
                text("overall_length", "Overall Length (OAL)", "e.g. 6.000\""),
            )

            ToolCategory.TAP -> listOf(
                dropdown("cutting_diameter", "Tap Size / Diameter", diameters, required = true),
                text("thread_pitch", "Thread Pitch / TPI", "e.g. 20 TPI, 1.5mm"),
                text("thread_form", "Thread Form", "e.g. UNC, UNF, M, NPT"),
                dropdown("flutes", "Number of Flutes", d.flutes, required = true),
                dropdown("coating", "Coating", d.coatings),
                dropdown("material", "Body Material", d.bodyMaterials),
                text("overall_length", "Overall Length", ""),
                dropdown("coolant_through", "Coolant Through", d.boolean),
            )

            ToolCategory.REAMER -> listOf(
                dropdown("cutting_diameter", "Reamer Diameter", diameters, required = true),
                dropdown("shank_diameter", "Shank Diameter", diameters),
                dropdown("flutes", "Number of Flutes", d.flutes, required = true),
                text("flute_length", "Flute Length", ""),
                dropdown("coating", "Coating", d.coatings),
                dropdown("material", "Body Material", d.bodyMaterials),
                text("overall_length", "Overall Length", ""),
                dropdown("coolant_through", "Coolant Through", d.boolean),
            )

            // ── Indexable tool bodies ────────────────────────────────
            ToolCategory.INDEXABLE_MILL_BODY -> listOf(
                dropdown("cutting_diameter", "Cutting Diameter", diameters),
                text("pocket_size", "Insert Pocket Size", "e.g. IC 0.500\""),
                dropdown("shank_type", "Shank / Interface", d.shankTypes),
                dropdown("coolant_through", "Coolant Through", d.boolean),
                text("overall_length", "Overall Length (OAL)", "e.g. 6.5\""),
            )

            ToolCategory.INDEXABLE_DRILL_BODY -> listOf(
                dropdown("cutting_diameter", "Drill Diameter", diameters),
                dropdown("shank_type", "Shank / Interface", d.shankTypes),
                text("pocket_size", "Insert Pocket Size", ""),
                dropdown("coolant_through", "Coolant Through", d.boolean),
                text("overall_length", "Overall Length", "e.g. 7.000\""),
            )

            ToolCategory.BORING_BAR_BODY -> listOf(
                dropdown("shank_type", "Shank / Interface", d.shankTypes),
                dropdown("shank_diameter", "Shank Diameter", diameters),
                text("projection", "Projection / Gauge Length", "e.g. 6.000\""),
                text("pocket_size", "Insert Pocket Size", ""),
                dropdown("coolant_through", "Coolant Through", d.boolean),
                text("overall_length", "Overall Length (OAL)", "e.g. 10.0\""),
            )

            ToolCategory.TURNING_HOLDER -> listOf(
                dropdown("shank_type", "Shank Type", d.shankTypes),
                text("shank_size", "Shank Size", "e.g. 1\" square"),
                text("projection", "Projection", "e.g. 5.000\""),
                text("pocket_size", "Insert Pocket Size", ""),
                dropdown("hand", "Hand of Cut", d.handOfCut),
            )

            ToolCategory.THREADING_HOLDER -> listOf(
                dropdown("shank_type", "Shank Type", d.shankTypes),
                text("shank_size", "Shank Size", "e.g. 1\" square"),
                text("thread_type", "Thread Type", "e.g. External, Internal"),
                text("pocket_size", "Insert Pocket Size", ""),
                dropdown("hand", "Hand of Cut", d.handOfCut),
            )

            ToolCategory.GROOVING_HOLDER -> listOf(
                dropdown("shank_type", "Shank Type", d.shankTypes),
                text("shank_size", "Shank Size", "e.g. 1\" square, blade"),
                text("groove_width", "Blade / Groove Width", "e.g. 0.118\""),
                text("max_depth", "Max Cut Depth", "e.g. 1.250\""),
                dropdown("hand", "Hand of Cut", d.handOfCut),
            )

            // ── Consumables / hardware ──────────────────────────────
            ToolCategory.INSERT -> insertFields(unitSystem)

            ToolCategory.SCREW -> listOf(
                text("size", "Screw Size", "e.g. M3.5 x 8"),
                text("drive_type", "Drive Type", "e.g. Torx T-15, Hex 2mm"),
                text("torque_spec", "Torque Spec", "e.g. 2.5 N\u00B7m"),
            )

            ToolCategory.SHIM -> listOf(
                text("shim_type", "Shim Type", "e.g. Carbide seat, shimmy"),
                text("pocket_size", "For Pocket Size", "e.g. CC / CCMT 3(2.5)_"),
            )

            ToolCategory.CLAMP -> listOf(
                text("clamp_type", "Clamp Type", "e.g. Top clamp, lever lock"),
                text("size", "Size", "e.g. for IC 1/2\""),
            )

            ToolCategory.WEDGE -> listOf(
                text("wedge_type", "Wedge Type", ""),
                text("size", "Size", ""),
            )

            // ── Holders / adapters ──────────────────────────────────
            ToolCategory.HOLDER -> listOf(
                dropdown("shank_type", "Interface Type", d.shankTypes),
                text("bore_size", "Bore / Collet Size", "e.g. ER32, 3/4\" bore"),
                text("gauge_length", "Gauge Length", "e.g. 4.000\""),
                text("overall_length", "Overall Length", ""),
                dropdown("coolant_through", "Coolant Through", d.boolean),
            )

            ToolCategory.COLLET -> listOf(
                text("collet_system", "Collet System", "e.g. ER32, ER40, TG100"),
                text("bore_size", "Bore Size", "e.g. 1/2\", 12mm"),
            )

            ToolCategory.RETENTION_KNOB -> listOf(
                dropdown("shank_type", "Taper Interface", d.shankTypes),
                text("thread_size", "Thread Size", "e.g. 5/8-11"),
            )

            // ── Catch-all ───────────────────────────────────────────
            ToolCategory.OTHER -> listOf(
                text("description_custom", "Description", "Describe the item"),
                dropdown("shank_type", "Shank / Interface", d.shankTypes),
                dropdown("cutting_diameter", "Cutting Diameter", diameters),
                dropdown("coating", "Coating", d.coatings),
                dropdown("material", "Body Material", d.bodyMaterials),
                text("overall_length", "Overall Length", ""),
            )
        }

        return if (category == ToolCategory.INSERT) {
            specific
        } else {
            base + specific + listOf(notesField)
        }
    }

    // ==================================================================
    // Universal fields
    // ==================================================================

    private val manufacturerField = FormField(
        key = "manufacturer",
        label = "Manufacturer / Brand",
        hint = "Select manufacturer",
        inputType = InputType.DROPDOWN,
        dropdownOptions = DropdownOptions.manufacturers,
        required = true
    )

    private val catalogNumberField = FormField(
        key = "catalog_number",
        label = "Catalog / Part Number",
        hint = "e.g. A3S2000M400",
        inputType = InputType.TEXT,
        required = true
    )

    private val notesField = FormField(
        key = "notes",
        label = "Notes",
        hint = "Any additional info",
        inputType = InputType.MULTILINE
    )

    // ==================================================================
    // INSERT fields (self-contained)
    // ==================================================================

    private fun insertFields(unitSystem: UnitSystem): List<FormField> {
        val d = DropdownOptions
        val icOptions = if (unitSystem == UnitSystem.IMPERIAL)
            d.insertICImperial else d.insertICMetric
        val thicknessOptions = if (unitSystem == UnitSystem.IMPERIAL)
            d.insertThicknessImperial else d.insertThicknessMetric
        val noseRadii = d.noseRadii(unitSystem)

        return listOf(
            manufacturerField,
            catalogNumberField,
            text("iso_designation", "ISO Insert Designation",
                "e.g. CNMG 120408 \u2014 parsed on PC for search"),
            dropdown("insert_shape", "Insert Shape", d.insertShapes, required = true),
            dropdown("insert_size", "IC (Inscribed Circle)", icOptions),
            dropdown("thickness", "Insert Thickness", thicknessOptions),
            dropdown("nose_radius", "Nose / Corner Radius", noseRadii),
            text("grade", "Insert Grade", "e.g. KC5010, IC808, GC4325"),
            dropdown("workpiece_material", "Target Workpiece Material",
                d.workpieceMaterials),
            dropdown("coating", "Insert Coating", d.coatings),
            text("chipbreaker", "Chipbreaker Style", "e.g. MF, PM, GC, -MR"),
            dropdown("hand", "Hand of Cut", d.handOfCut),
            dropdown("rake", "Rake Angle", d.rake),
            notesField,
        )
    }

    // ==================================================================
    // Field builder helpers
    // ==================================================================

    private fun text(key: String, label: String, hint: String, required: Boolean = false) =
        FormField(key = key, label = label, hint = hint, inputType = InputType.TEXT, required = required)

    private fun dropdown(key: String, label: String, options: List<String>, required: Boolean = false) =
        FormField(
            key = key, label = label, hint = "Select\u2026",
            inputType = InputType.DROPDOWN, dropdownOptions = options,
            required = required
        )
}
