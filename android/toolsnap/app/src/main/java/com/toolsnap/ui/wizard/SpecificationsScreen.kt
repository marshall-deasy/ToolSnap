package com.toolsnap.ui.wizard

import androidx.compose.runtime.Composable
import com.toolsnap.config.ComponentTemplates
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.model.UnitSystem
import com.toolsnap.utils.IsoInsertParser

/**
 * Screen 3 — Tool specifications.
 *
 * Renders category-specific form fields from ComponentTemplates.
 * Delegates entirely to ManualEntryScreen for rendering.
 *
 * For INSERT category:
 *   - manufacturer, catalog_number, and iso_designation are excluded
 *     (already captured on Screen 2 as Identity fields)
 *   - If mpnIso is populated, the ISO designation is parsed via
 *     [IsoInsertParser] and matching spec fields are auto-populated
 *     (insert_shape, insert_size, thickness, nose_radius, chipbreaker)
 *   - Auto-populated values appear pre-filled but remain editable
 *
 * For all other categories:
 *   - manufacturer and catalog_number are excluded (from Screen 2)
 *   - No ISO parsing applies
 */
@Composable
fun SpecificationsScreen(
    category: ToolCategory,
    unitSystem: UnitSystem = UnitSystem.IMPERIAL,
    mpnIso: String = "",
    existingValues: Map<String, String> = emptyMap(),
    onNext: (specs: Map<String, String>) -> Unit,
    onBack: () -> Unit,
    onCancel: () -> Unit
) {
    // Get all fields for this category, then remove fields already
    // collected on Screen 2 (Identity).
    val allFields = ComponentTemplates.fieldsFor(category, unitSystem)

    val identityKeys = if (category == ToolCategory.INSERT) {
        // For inserts: manufacturer, catalog_number, AND iso_designation
        // are all captured on Screen 2 already
        setOf("manufacturer", "catalog_number", "iso_designation")
    } else {
        setOf("manufacturer", "catalog_number")
    }

    val specFields = allFields.filter { it.key !in identityKeys }

    // Build pre-populated values: start with any existing values,
    // then layer on ISO-parsed values (existing values take priority
    // so user edits aren't overwritten on back-navigation).
    val prePopulated = buildMap {
        // Parse ISO designation for inserts
        if (category == ToolCategory.INSERT && mpnIso.isNotBlank()) {
            val parseResult = IsoInsertParser.parse(mpnIso, unitSystem)
            if (parseResult != null) {
                putAll(parseResult.fields)
            }
        }
        // Existing values override parsed values (user already edited)
        putAll(existingValues)
    }

    ManualEntryScreen(
        formFields = specFields,
        title = "${category.displayName} — Specifications",
        existingValues = prePopulated,
        onSave = { values -> onNext(values) },
        onCancel = onBack  // "Cancel" on ManualEntryScreen acts as BACK here
    )
}
