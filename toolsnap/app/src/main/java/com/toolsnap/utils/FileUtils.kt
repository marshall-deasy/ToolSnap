package com.toolsnap.utils

import android.content.Context
import android.os.Environment
import com.toolsnap.config.CaptureConfig
import com.toolsnap.core.model.CaptureField
import java.io.File
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * Centralized file path conventions for ToolSnap.
 *
 * Sessions are stored in shared storage at Documents/ToolSnap/
 * so they're accessible via USB file transfer for PC sync.
 *
 * All other modules that touch the filesystem import paths from here.
 * No path construction logic lives anywhere else.
 */
object FileUtils {

    private val DATE_FORMATTER = DateTimeFormatter
        .ofPattern("yyyy-MM-dd")
        .withZone(ZoneId.systemDefault())

    private const val TOOLSNAP_DIR = "ToolSnap"
    private const val SYNCED_MARKER = ".synced"

    /**
     * Root storage directory: Documents/ToolSnap/
     * Accessible via USB file transfer when tablet is connected to PC.
     * Falls back to internal storage if external isn't available.
     */
    fun exportRoot(context: Context): File {
        val documentsDir = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOCUMENTS
        )
        val toolSnapDir = File(documentsDir, TOOLSNAP_DIR)
        if (!toolSnapDir.exists()) toolSnapDir.mkdirs()
        return toolSnapDir
    }

    /**
     * Session folder with collision detection.
     *
     * If "2026-02-03_boring-bar" already exists, tries
     * "2026-02-03_boring-bar_2", "_3", etc. up to 99.
     *
     * Created on first access if it doesn't exist.
     */
    fun sessionDirUnique(context: Context, toolName: String, createdAt: Instant): File {
        val dateStr = DATE_FORMATTER.format(createdAt)
        val baseName = CaptureConfig.sessionFolderName(toolName, dateStr)
        val root = exportRoot(context)

        // Try the base name first
        var candidate = File(root, baseName)
        if (!candidate.exists()) {
            candidate.mkdirs()
            return candidate
        }

        // Collision — append suffix _2 through _99
        for (suffix in 2..99) {
            candidate = File(root, "${baseName}_$suffix")
            if (!candidate.exists()) {
                candidate.mkdirs()
                return candidate
            }
        }

        // Extreme edge: fall back to UUID-based name
        val fallback = File(root, "${baseName}_${System.currentTimeMillis()}")
        fallback.mkdirs()
        return fallback
    }

    /**
     * Original sessionDir (no collision detection).
     * Kept for backward compatibility — new code should use [sessionDirUnique].
     */
    fun sessionDir(context: Context, toolName: String, createdAt: Instant): File {
        val dateStr = DATE_FORMATTER.format(createdAt)
        val folderName = CaptureConfig.sessionFolderName(toolName, dateStr)
        return File(exportRoot(context), folderName).also {
            if (!it.exists()) it.mkdirs()
        }
    }

    /**
     * Session folder looked up by folder name (for re-opening).
     */
    fun sessionDirByName(context: Context, folderName: String): File {
        return File(exportRoot(context), folderName)
    }

    /**
     * Path for a captured image within a session folder.
     * Example: <session_dir>/body.jpg
     */
    fun imageFile(sessionDir: File, field: CaptureField): File {
        return File(sessionDir, CaptureConfig.imageFileName(field))
    }

    /**
     * Path for the JSON manifest within a session folder.
     */
    fun manifestFile(sessionDir: File): File {
        return File(sessionDir, CaptureConfig.MANIFEST_FILE_NAME)
    }

    /**
     * List all session folders, sorted newest first.
     */
    fun listSessionDirs(context: Context): List<File> {
        val root = exportRoot(context)
        return root.listFiles()
            ?.filter { it.isDirectory }
            ?.sortedByDescending { it.name }
            ?: emptyList()
    }

    /**
     * Delete a session folder and all its contents.
     */
    fun deleteSession(sessionDir: File): Boolean {
        return sessionDir.deleteRecursively()
    }

    // ======================================================================
    // Sync status helpers
    // ======================================================================

    /**
     * Check if a session has been synced to PC.
     * The PC sync script writes a .synced marker file.
     */
    fun isSynced(sessionDir: File): Boolean {
        return File(sessionDir, SYNCED_MARKER).exists()
    }

    /**
     * Get all synced session directories.
     */
    fun listSyncedDirs(context: Context): List<File> {
        return listSessionDirs(context).filter { isSynced(it) }
    }

    /**
     * Get count of synced sessions.
     */
    fun syncedCount(context: Context): Int {
        return listSyncedDirs(context).size
    }

    /**
     * Delete all synced sessions (bulk clear after PC sync).
     * Returns number of sessions deleted.
     */
    fun clearSyncedSessions(context: Context): Int {
        val synced = listSyncedDirs(context)
        var deleted = 0
        for (dir in synced) {
            if (dir.deleteRecursively()) deleted++
        }
        return deleted
    }

    /**
     * DEV ONLY — Nuke every session folder in the ToolSnap directory.
     * Returns number of sessions deleted.
     */
    fun purgeAll(context: Context): Int {
        val all = listSessionDirs(context)
        var deleted = 0
        for (dir in all) {
            if (dir.deleteRecursively()) deleted++
        }
        return deleted
    }
}
