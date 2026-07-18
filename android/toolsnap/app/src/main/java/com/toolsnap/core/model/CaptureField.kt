package com.toolsnap.core.model

/**
 * The four capture fields in a tooling session.
 * Each field represents one photo/data category.
 *
 * [displayName]  — shown in the wizard UI
 * [fileName]     — used for the image file on disk (e.g. "body.jpg")
 * [instruction]  — brief prompt shown above the camera viewfinder
 *
 * NOTE: OCR is now handled by the identity flow (Screen 2 / 2a / 2b)
 * rather than per-field. The old [requiresOcr] flag has been removed.
 */
enum class CaptureField(
    val displayName: String,
    val fileName: String,
    val instruction: String
) {
    BODY(
        displayName = "Tool Body",
        fileName = "body",
        instruction = "Photograph the full tool body / holder"
    ),
    INSERT(
        displayName = "Insert",
        fileName = "insert",
        instruction = "Photograph the insert — capture shape and markings"
    ),
    HARDWARE(
        displayName = "Hardware",
        fileName = "hardware",
        instruction = "Photograph screws, clamps, shims, and seats"
    ),
    TOOL_DATA(
        displayName = "Tool Data",
        fileName = "tool_data",
        instruction = "Photograph the tool label, engraving, or spec sheet"
    );

    /**
     * Legacy compatibility — returns true only for TOOL_DATA.
     * Used by SessionManager and other code that checks OCR eligibility.
     */
    val requiresOcr: Boolean get() = this == TOOL_DATA

    companion object {
        /** Ordered list used by the wizard to iterate steps. */
        val wizardOrder: List<CaptureField> = listOf(
            BODY, INSERT, HARDWARE, TOOL_DATA
        )
    }
}
