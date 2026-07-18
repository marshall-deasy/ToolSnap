package com.toolsnap.core.session

import android.content.Context
import android.util.Log
import com.toolsnap.config.FormData
import com.toolsnap.core.model.CaptureField
import com.toolsnap.core.model.CaptureSession
import com.toolsnap.core.model.FieldStatus
import com.toolsnap.core.model.PendingComponent
import com.toolsnap.core.model.Tool
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.utils.FileUtils
import com.toolsnap.utils.ImageUtils
import com.toolsnap.utils.JsonUtils
import com.toolsnap.utils.ManifestV3
import java.io.File

private const val TAG = "SessionManager"

/**
 * Manages the lifecycle of capture sessions.
 *
 * Responsibilities:
 *   - Create / activate / abandon / finalize sessions
 *   - Save photos, form data, OCR results to the active session
 *   - Load existing sessions from disk
 *   - Compute completion stats for the home screen
 *
 * V3 manifest writing is delegated to [ManifestExporter].
 */
class SessionManager(private val context: Context) {

    var activeSession: CaptureSession? = null
        private set

    var activeSessionDir: File? = null
        private set

    var lastError: String? = null
        private set

    var activeToolCategory: ToolCategory? = null
        private set

    private var pendingComponents: List<PendingComponent> = emptyList()

    // ------------------------------------------------------------------
    // Tool category
    // ------------------------------------------------------------------

    fun setToolCategory(category: ToolCategory) {
        activeToolCategory = category
        val session = activeSession ?: return
        val current = session.formDataMap[CaptureField.BODY]
        session.formDataMap[CaptureField.BODY] = if (current != null) {
            FormData(
                entryMethod = current.entryMethod,
                values = current.values + ("tool_category" to category.name)
            )
        } else {
            FormData(
                entryMethod = "tool_category",
                values = mapOf("tool_category" to category.name)
            )
        }
        persistActiveSession()
    }

    // ------------------------------------------------------------------
    // Pending components (assembly linking)
    // ------------------------------------------------------------------

    fun setPendingComponents(components: List<PendingComponent>) {
        pendingComponents = components
    }

    fun loadExistingTools(): List<Tool> {
        return try {
            val dirs = FileUtils.listSessionDirs(context)
            val tools = mutableListOf<Tool>()
            for (dir in dirs) {
                if (dir.absolutePath == activeSessionDir?.absolutePath) continue
                val result = ManifestV3.readManifest(dir)
                if (result != null) {
                    tools.addAll(result.tools.filter { !it.isAssembly })
                }
            }
            val seen = mutableSetOf<String>()
            tools.filter { t ->
                val key = buildDedupeKey(t)
                if (key != null && key in seen) false
                else { key?.let { seen.add(it) }; true }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load existing tools: ${e.message}", e)
            emptyList()
        }
    }

    private fun buildDedupeKey(tool: Tool): String? {
        val cat = tool.catalogNumber?.takeIf { it.isNotBlank() }
        val mfg = tool.manufacturer?.takeIf { it.isNotBlank() }
        return if (cat != null && mfg != null) {
            "${mfg.trim().lowercase()}|${cat.trim().lowercase()}"
        } else null
    }

    // ------------------------------------------------------------------
    // Session creation
    // ------------------------------------------------------------------

    fun createSession(toolName: String): CaptureSession? {
        val name = toolName.trim()
        if (name.isBlank()) {
            lastError = "Tool name cannot be empty"
            return null
        }

        val session = CaptureSession(toolName = name)

        val dir = try {
            FileUtils.sessionDirUnique(context, name, session.createdAt)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create session directory: ${e.message}", e)
            lastError = "Could not create session folder \u2014 check storage"
            return null
        }

        activeSession = session
        activeSessionDir = dir

        val saved = persistActiveSession()
        if (!saved) {
            lastError = "Could not write initial manifest \u2014 check storage"
            activeSession = null
            activeSessionDir = null
            return null
        }

        lastError = null
        return session
    }

    // ------------------------------------------------------------------
    // Field capture operations
    // ------------------------------------------------------------------

    sealed class PhotoSaveResult {
        data object Success : PhotoSaveResult()
        data class Failure(val message: String) : PhotoSaveResult()
    }

    fun savePhotoWithResult(field: CaptureField, rawPath: String): PhotoSaveResult {
        val session = activeSession
            ?: return PhotoSaveResult.Failure("No active session")
        val dir = activeSessionDir
            ?: return PhotoSaveResult.Failure("No session directory")

        val destFile = FileUtils.imageFile(dir, field)
        val result = ImageUtils.saveAndCompress(rawPath, destFile)

        return when (result) {
            is ImageUtils.SaveResult.Success -> {
                session.imagePaths[field] = destFile.absolutePath
                if (!field.requiresOcr) {
                    session.fieldStatuses[field] = FieldStatus.CAPTURED
                }
                val saved = persistActiveSession()
                if (!saved) {
                    PhotoSaveResult.Failure("Photo saved but manifest write failed")
                } else {
                    lastError = null
                    PhotoSaveResult.Success
                }
            }
            is ImageUtils.SaveResult.Failure -> {
                lastError = result.reason
                PhotoSaveResult.Failure(result.reason)
            }
        }
    }

    fun savePhoto(field: CaptureField, rawPath: String): Boolean {
        return when (savePhotoWithResult(field, rawPath)) {
            is PhotoSaveResult.Success -> true
            is PhotoSaveResult.Failure -> false
        }
    }

    fun saveOcrResult(field: CaptureField, confirmedText: String) {
        val session = activeSession ?: return
        val imagePath = session.imagePaths[field] ?: return
        session.markCapturedWithOcr(field, imagePath, confirmedText)
        persistActiveSession()
    }

    fun saveFormData(field: CaptureField, formData: FormData) {
        val session = activeSession ?: return
        session.markCapturedWithFormData(field, formData)
        persistActiveSession()
    }

    fun saveToolAttributes(field: CaptureField, attributes: Map<String, String>) {
        val session = activeSession ?: return
        val formData = FormData(
            entryMethod = "manual",
            values = attributes
        )
        session.markCapturedWithFormData(field, formData)
        persistActiveSession()
    }

    fun markOcrNeedsReview(field: CaptureField, rawText: String) {
        val session = activeSession ?: return
        val imagePath = session.imagePaths[field] ?: return
        session.markOcrNeedsReview(field, imagePath, rawText)
        persistActiveSession()
    }

    fun skipField(field: CaptureField) {
        val session = activeSession ?: return
        session.markSkipped(field)
        persistActiveSession()
    }

    // ------------------------------------------------------------------
    // Session finalization
    // ------------------------------------------------------------------

    fun finalizeSession(): CaptureSession? {
        val session = activeSession ?: return null
        val dir = activeSessionDir ?: return null
        val category = activeToolCategory

        persistActiveSession()

        if (category != null) {
            ManifestExporter.writeV3(session, dir, category, pendingComponents)
        }

        val finalized = session.copy(
            fieldStatuses = session.fieldStatuses.toMutableMap(),
            imagePaths = session.imagePaths.toMutableMap(),
            ocrTexts = session.ocrTexts.toMutableMap(),
            formDataMap = session.formDataMap.toMutableMap()
        )

        activeSession = null
        activeSessionDir = null
        activeToolCategory = null
        pendingComponents = emptyList()

        return finalized
    }

    fun abandonSession() {
        persistActiveSession()
        activeSession = null
        activeSessionDir = null
        activeToolCategory = null
        pendingComponents = emptyList()
    }

    // ------------------------------------------------------------------
    // Loading existing sessions
    // ------------------------------------------------------------------

    fun loadAllSessions(): List<CaptureSession> {
        return FileUtils.listSessionDirs(context).mapNotNull { dir ->
            loadSessionFromDir(dir)
        }
    }

    fun loadAndActivateSession(folderName: String): CaptureSession? {
        val dir = FileUtils.sessionDirByName(context, folderName)
        if (!dir.exists()) return null
        val session = loadSessionFromDir(dir) ?: return null
        activeSession = session
        activeSessionDir = dir
        return session
    }

    fun loadSessionFromDir(dir: File): CaptureSession? {
        return try {
            val manifest = JsonUtils.readManifest(dir) ?: return null
            JsonUtils.manifestToSession(manifest, dir)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load session from ${dir.name}: ${e.message}", e)
            null
        }
    }

    // ------------------------------------------------------------------
    // Re-capture / reset
    // ------------------------------------------------------------------

    fun resetField(field: CaptureField) {
        val session = activeSession ?: return
        val dir = activeSessionDir ?: return
        try {
            val imageFile = FileUtils.imageFile(dir, field)
            if (imageFile.exists()) imageFile.delete()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to delete image for ${field.fileName}: ${e.message}", e)
        }
        session.resetField(field)
        persistActiveSession()
    }

    // ------------------------------------------------------------------
    // Deletion
    // ------------------------------------------------------------------

    fun deleteSession(folderName: String): Boolean {
        val dir = FileUtils.sessionDirByName(context, folderName)
        if (!dir.exists()) return false
        if (activeSessionDir?.absolutePath == dir.absolutePath) {
            activeSession = null
            activeSessionDir = null
        }
        return FileUtils.deleteSession(dir)
    }

    // ------------------------------------------------------------------
    // Stats
    // ------------------------------------------------------------------

    data class SessionStats(
        val totalSessions: Int,
        val completeSessions: Int,
        val incompleteSessions: Int
    )

    fun getSessionStats(): SessionStats {
        val sessions = loadAllSessions()
        val complete = sessions.count { it.isComplete }
        return SessionStats(
            totalSessions = sessions.size,
            completeSessions = complete,
            incompleteSessions = sessions.size - complete
        )
    }

    // ------------------------------------------------------------------
    // Internal
    // ------------------------------------------------------------------

    fun persistForEdit(): Boolean = persistActiveSession()

    private fun persistActiveSession(): Boolean {
        val session = activeSession ?: return false
        val dir = activeSessionDir ?: return false
        return JsonUtils.writeManifest(session, dir)
    }
}
