package com.toolsnap.config

import kotlinx.serialization.Serializable

/**
 * Form field and data definitions used by the capture wizard.
 *
 * Option lists live in [DropdownOptions]. Category-specific field
 * routing lives in [ComponentTemplates]. This file provides the
 * shared [FormField], [InputType], and [FormData] types.
 */
object FormTemplates {

    /** Sentinel value for "Other" — triggers free-text entry in the UI */
    const val OTHER_OPTION = "Other\u2026"
}

/**
 * A single input field in a manual entry form.
 *
 * @param dropdownOptions  If [inputType] is [InputType.DROPDOWN], the list of
 *                         selectable values. The last entry should be
 *                         [FormTemplates.OTHER_OPTION] to allow custom entry.
 *                         Null for non-dropdown fields.
 */
data class FormField(
    val key: String,
    val label: String,
    val hint: String,
    val inputType: InputType,
    val dropdownOptions: List<String>? = null,
    val required: Boolean = false
)

enum class InputType {
    TEXT,
    NUMBER,
    DECIMAL,
    MULTILINE,
    /** Rendered as a scrollable picker / bottom-sheet selector in the UI. */
    DROPDOWN
}

/**
 * Serializable form data for the manifest.
 * Maps field key → value entered by the user.
 */
@Serializable
data class FormData(
    val entryMethod: String = "manual",  // "manual" or "ocr"
    val values: Map<String, String> = emptyMap()
) {
    /**
     * Convert form data to a readable text representation
     * (used for display in summary/detail screens).
     */
    fun toDisplayText(): String {
        return values.entries
            .filter { it.value.isNotBlank() }
            .joinToString("\n") { "${it.key}: ${it.value}" }
    }
}
