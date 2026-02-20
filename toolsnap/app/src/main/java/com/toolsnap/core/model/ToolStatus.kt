package com.toolsnap.core.model

/**
 * Capture status for a tool in the wizard.
 *
 * Every tool starts as [PENDING] and progresses to a resolved state
 * ([CAPTURED] or [SKIPPED]).  [PARTIAL] indicates the user began
 * entering data but hasn't finished.
 *
 * [isResolved]      — true when no further user action is needed.
 * [needsAttention]  — true when the wizard should revisit this item.
 */
enum class ToolStatus(
    val isResolved: Boolean,
    val needsAttention: Boolean
) {
    /** Not yet started. */
    PENDING(isResolved = false, needsAttention = true),

    /** Fully captured — photo and/or data entered. */
    CAPTURED(isResolved = true, needsAttention = false),

    /** Some data entered, but not complete. */
    PARTIAL(isResolved = false, needsAttention = true),

    /** User explicitly skipped this item. */
    SKIPPED(isResolved = true, needsAttention = false);

    companion object {
        fun fromName(name: String): ToolStatus =
            try { valueOf(name) } catch (_: Exception) { PENDING }
    }
}
