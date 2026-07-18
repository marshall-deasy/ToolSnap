package com.toolsnap.core.model

import com.toolsnap.config.FormData
import java.time.Instant
import java.util.UUID

/**
 * Represents a single tooling capture session.
 *
 * Created when the user taps ADD TOOLING and survives through
 * the wizard, export, and later editing of incomplete entries.
 *
 * [toolName] is the only required field — everything else can be
 * skipped and filled in later.
 */
data class CaptureSession(
    val sessionId: String = UUID.randomUUID().toString(),
    val createdAt: Instant = Instant.now(),
    var toolName: String = "",
    val fieldStatuses: MutableMap<CaptureField, FieldStatus> = CaptureField.entries
        .associateWith { FieldStatus.PENDING }
        .toMutableMap(),
    val imagePaths: MutableMap<CaptureField, String> = mutableMapOf(),
    val ocrTexts: MutableMap<CaptureField, String> = mutableMapOf(),
    val formDataMap: MutableMap<CaptureField, FormData> = mutableMapOf()
) {

    /** Count of fields that have been fully captured. */
    val capturedCount: Int
        get() = fieldStatuses.count { it.value == FieldStatus.CAPTURED }

    /** Count of fields explicitly skipped. */
    val skippedCount: Int
        get() = fieldStatuses.count { it.value == FieldStatus.SKIPPED }

    /** Total number of trackable fields. */
    val totalFields: Int
        get() = CaptureField.entries.size

    /** True when every field is either captured or skipped — nothing pending. */
    val isComplete: Boolean
        get() = fieldStatuses.values.all { it.isResolved }

    /** True when at least one field has been captured but the session isn't complete. */
    val isPartial: Boolean
        get() = capturedCount > 0 && !isComplete

    /** List of fields that still need attention (PENDING or OCR_NEEDS_REVIEW). */
    val incompleteFields: List<CaptureField>
        get() = CaptureField.entries.filter {
            fieldStatuses[it]?.needsAttention == true
        }

    /** Mark a field as captured and store its image path. */
    fun markCaptured(field: CaptureField, imagePath: String) {
        fieldStatuses[field] = FieldStatus.CAPTURED
        imagePaths[field] = imagePath
    }

    /** Mark a field as captured with OCR text (for TOOL_DATA, SPEEDS_FEEDS). */
    fun markCapturedWithOcr(field: CaptureField, imagePath: String, ocrText: String) {
        fieldStatuses[field] = FieldStatus.CAPTURED
        imagePaths[field] = imagePath
        ocrTexts[field] = ocrText
    }

    /** Mark a field as captured with manual form data (no photo needed). */
    fun markCapturedWithFormData(field: CaptureField, formData: FormData) {
        fieldStatuses[field] = FieldStatus.CAPTURED
        formDataMap[field] = formData
        // Store a text representation in ocrTexts too for backward compatibility
        ocrTexts[field] = formData.toDisplayText()
    }

    /** Mark a field as needing OCR review (image taken, text extracted, not yet confirmed). */
    fun markOcrNeedsReview(field: CaptureField, imagePath: String, rawOcrText: String) {
        fieldStatuses[field] = FieldStatus.OCR_NEEDS_REVIEW
        imagePaths[field] = imagePath
        ocrTexts[field] = rawOcrText
    }

    /** Mark a field as skipped by the user. */
    fun markSkipped(field: CaptureField) {
        fieldStatuses[field] = FieldStatus.SKIPPED
    }

    /** Reset a field back to pending (for re-capture from detail screen). */
    fun resetField(field: CaptureField) {
        fieldStatuses[field] = FieldStatus.PENDING
        imagePaths.remove(field)
        ocrTexts.remove(field)
        formDataMap.remove(field)
    }

    /**
     * Get display text for a data field — prefers form data display,
     * falls back to OCR text.
     */
    fun getDisplayText(field: CaptureField): String? {
        val form = formDataMap[field]
        if (form != null && form.values.isNotEmpty()) {
            return form.toDisplayText()
        }
        return ocrTexts[field]
    }

    /**
     * Get the data entry method used for a field.
     * Returns "manual", "ocr", or null if no data.
     */
    fun getEntryMethod(field: CaptureField): String? {
        val form = formDataMap[field]
        if (form != null) return form.entryMethod
        if (ocrTexts.containsKey(field)) return "ocr"
        return null
    }
}
