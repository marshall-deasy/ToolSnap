package com.toolsnap.config

import com.toolsnap.core.model.CaptureField
import com.toolsnap.core.model.ToolCategory

/**
 * Single source of truth for capture configuration.
 *
 * The wizard, summary, export, and detail screens all read from here.
 * To add a new capture field, update [CaptureField] and this object adapts.
 */
object CaptureConfig {

    /** Default ordered list of fields (legacy — used when no category context). */
    val wizardFields: List<CaptureField> = CaptureField.wizardOrder

    /**
     * Category-aware wizard fields.
     *
     * - Solid tools: BODY (required) + TOOL_DATA (OCR)
     * - Bodies (assemblies): BODY + INSERT + HARDWARE + TOOL_DATA — all skippable
     * - Consumables: BODY (required) + TOOL_DATA (OCR)
     * - Holders: BODY (required) + TOOL_DATA (OCR)
     * - Other: BODY (required) + TOOL_DATA (OCR)
     */
    fun wizardFieldsFor(category: ToolCategory): List<CaptureField> {
        return when {
            category.isBody -> listOf(
                CaptureField.BODY,
                CaptureField.INSERT,
                CaptureField.HARDWARE,
                CaptureField.TOOL_DATA
            )
            else -> listOf(
                CaptureField.BODY,
                CaptureField.TOOL_DATA
            )
        }
    }

    /**
     * Whether a field can be skipped for a given category.
     * Bodies: all fields skippable. Everything else: BODY is required.
     */
    fun canSkip(field: CaptureField, category: ToolCategory): Boolean {
        if (category.isBody) return true
        return field != CaptureField.BODY
    }

    /** Maximum image dimension (longest edge) before compression. */
    const val MAX_IMAGE_DIMENSION = 2048

    /** JPEG compression quality (0–100). */
    const val JPEG_QUALITY = 85

    /** Name of the top-level export directory inside app internal storage. */
    const val EXPORT_DIR_NAME = "toolsnap_exports"

    /** File name for the JSON manifest inside each session export folder. */
    const val MANIFEST_FILE_NAME = "manifest.json"

    /** Temp file name used during atomic manifest writes. */
    const val MANIFEST_TEMP_NAME = "manifest.json.tmp"

    /** Image file extension used for all captured photos. */
    const val IMAGE_EXTENSION = "jpg"

    /** Max chars for the tool-name portion of a folder name. */
    private const val MAX_NAME_LENGTH = 50

    /**
     * Characters illegal on NTFS (Windows), FAT32, and some Linux edge cases.
     * Must be stripped so the session folder can be synced to a PC.
     */
    private val ILLEGAL_FS_CHARS = Regex("[/\\\\:*?\"<>|\\x00-\\x1F]")

    /**
     * Build the image filename for a given field.
     * Example: "body.jpg", "tool_data.jpg"
     */
    fun imageFileName(field: CaptureField): String {
        return "${field.fileName}.${IMAGE_EXTENSION}"
    }

    /**
     * Sanitize a tool name for filesystem safety.
     *
     * - Strips all NTFS/FAT32 illegal characters
     * - Replaces spaces with hyphens
     * - Lowercases
     * - Trims to [MAX_NAME_LENGTH] characters
     * - Falls back to "unnamed" if result is blank
     */
    fun sanitizeToolName(toolName: String): String {
        val sanitized = toolName
            .trim()
            .replace(ILLEGAL_FS_CHARS, "")
            .replace(Regex("\\s+"), "-")           // collapse whitespace to single hyphen
            .replace(Regex("-{2,}"), "-")           // collapse multiple hyphens
            .trimStart('-').trimEnd('-')            // no leading/trailing hyphens
            .lowercase()
            .take(MAX_NAME_LENGTH)

        return sanitized.ifBlank { "unnamed" }
    }

    /**
     * Build a session folder name from tool name and timestamp.
     * Example: "2026-02-03_boring-bar-A123"
     *
     * Sanitizes the tool name for cross-platform filesystem safety.
     */
    fun sessionFolderName(toolName: String, timestamp: String): String {
        return "${timestamp}_${sanitizeToolName(toolName)}"
    }
}
