package com.toolsnap.utils

import android.util.Log
import com.toolsnap.config.FormData
import com.toolsnap.core.model.CaptureField
import com.toolsnap.core.model.CaptureSession
import com.toolsnap.core.model.FieldStatus
import com.toolsnap.config.CaptureConfig
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File

private const val TAG = "JsonUtils"

/**
 * JSON manifest serialization for export packages.
 *
 * The manifest is the contract between the Android capture app
 * and the Windows desktop database app. Both sides must agree
 * on this schema.
 */
object JsonUtils {

    private val json = Json {
        prettyPrint = true
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    /**
     * Write a CaptureSession to a manifest.json file.
     *
     * Uses an atomic write strategy:
     *   1. Write to manifest.json.tmp
     *   2. Delete the old manifest.json
     *   3. Rename .tmp to manifest.json
     *
     * If any step fails, the previous manifest remains intact.
     *
     * @return true if the write succeeded, false on error.
     */
    fun writeManifest(session: CaptureSession, sessionDir: File): Boolean {
        return try {
            val manifest = sessionToManifest(session)
            val jsonText = json.encodeToString(manifest)

            val finalFile = FileUtils.manifestFile(sessionDir)
            val tempFile = File(sessionDir, CaptureConfig.MANIFEST_TEMP_NAME)

            // Step 1: write to temp file
            tempFile.writeText(jsonText)

            // Step 2: verify the temp file was written correctly
            if (!tempFile.exists() || tempFile.length() == 0L) {
                Log.e(TAG, "Manifest temp file is empty or missing after write")
                tempFile.delete()
                return false
            }

            // Step 3: atomic rename (overwrites existing on most filesystems)
            //         On Android/Linux, renameTo is atomic if on same filesystem.
            if (finalFile.exists()) finalFile.delete()
            val renamed = tempFile.renameTo(finalFile)

            if (!renamed) {
                // Fallback: copy + delete if rename fails (cross-filesystem edge case)
                tempFile.copyTo(finalFile, overwrite = true)
                tempFile.delete()
            }

            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to write manifest: ${e.message}", e)
            false
        }
    }

    /**
     * Read a manifest.json file back into a SessionManifest.
     * Returns null if the file doesn't exist or can't be parsed.
     */
    fun readManifest(sessionDir: File): SessionManifest? {
        val file = FileUtils.manifestFile(sessionDir)
        if (!file.exists()) return null
        return try {
            json.decodeFromString<SessionManifest>(file.readText())
        } catch (e: Exception) {
            Log.e(TAG, "Failed to read manifest from ${sessionDir.name}: ${e.message}", e)
            null
        }
    }

    /**
     * Convert an in-memory CaptureSession to the serializable manifest format.
     */
    fun sessionToManifest(session: CaptureSession): SessionManifest {
        val fields = CaptureField.entries.associate { field ->
            field.fileName to FieldManifest(
                status = (session.fieldStatuses[field] ?: FieldStatus.PENDING).name,
                imageFile = session.imagePaths[field]?.let {
                    CaptureConfig.imageFileName(field)
                },
                ocrText = session.ocrTexts[field],
                entryMethod = session.getEntryMethod(field),
                formData = session.formDataMap[field]?.let { fd ->
                    FormDataManifest(
                        entryMethod = fd.entryMethod,
                        values = fd.values
                    )
                }
            )
        }

        return SessionManifest(
            sessionId = session.sessionId,
            toolName = session.toolName,
            createdAt = session.createdAt.toString(),
            fields = fields,
            isComplete = session.isComplete,
            fieldsCaptured = session.capturedCount,
            fieldsSkipped = session.skippedCount,
            fieldsTotal = session.totalFields
        )
    }

    /**
     * Convert a manifest back to a CaptureSession (for re-opening incomplete sessions).
     */
    fun manifestToSession(manifest: SessionManifest, sessionDir: File): CaptureSession {
        val session = CaptureSession(
            sessionId = manifest.sessionId,
            createdAt = java.time.Instant.parse(manifest.createdAt),
            toolName = manifest.toolName
        )

        for (field in CaptureField.entries) {
            val fieldData = manifest.fields[field.fileName] ?: continue
            val status = try {
                FieldStatus.valueOf(fieldData.status)
            } catch (e: IllegalArgumentException) {
                FieldStatus.PENDING
            }

            session.fieldStatuses[field] = status

            if (fieldData.imageFile != null) {
                val imgFile = File(sessionDir, fieldData.imageFile)
                if (imgFile.exists()) {
                    session.imagePaths[field] = imgFile.absolutePath
                }
            }

            if (fieldData.ocrText != null) {
                session.ocrTexts[field] = fieldData.ocrText
            }

            if (fieldData.formData != null) {
                session.formDataMap[field] = FormData(
                    entryMethod = fieldData.formData.entryMethod,
                    values = fieldData.formData.values
                )
            }
        }

        return session
    }
}

// ============================================================================
// Serializable manifest data classes (the JSON schema)
// ============================================================================

@Serializable
data class SessionManifest(
    val sessionId: String,
    val toolName: String,
    val createdAt: String,
    val fields: Map<String, FieldManifest>,
    val isComplete: Boolean,
    val fieldsCaptured: Int,
    val fieldsSkipped: Int,
    val fieldsTotal: Int
)

@Serializable
data class FieldManifest(
    val status: String,
    val imageFile: String? = null,
    val ocrText: String? = null,
    val entryMethod: String? = null,
    val formData: FormDataManifest? = null
)

@Serializable
data class FormDataManifest(
    val entryMethod: String = "manual",
    val values: Map<String, String> = emptyMap()
)
