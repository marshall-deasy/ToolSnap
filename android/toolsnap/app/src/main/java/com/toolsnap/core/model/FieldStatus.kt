package com.toolsnap.core.model

/**
 * Status of a single capture field within a session.
 *
 * PENDING          — not yet addressed (default)
 * CAPTURED         — photo taken and (if OCR) text confirmed
 * SKIPPED          — user explicitly skipped this field
 * OCR_NEEDS_REVIEW — OCR ran but user hasn't confirmed the result yet
 */
enum class FieldStatus {
    PENDING,
    CAPTURED,
    SKIPPED,
    OCR_NEEDS_REVIEW;

    /** True if this field has been dealt with (no longer needs attention). */
    val isResolved: Boolean
        get() = this == CAPTURED || this == SKIPPED

    /** True if this field still needs user action. */
    val needsAttention: Boolean
        get() = this == PENDING || this == OCR_NEEDS_REVIEW
}
