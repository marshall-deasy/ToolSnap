package com.toolsnap.core.session

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import com.toolsnap.core.model.CaptureField
import com.toolsnap.core.model.CaptureSession
import com.toolsnap.utils.FileUtils
import com.toolsnap.utils.JsonUtils
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Exports capture sessions as self-contained packages.
 *
 * Each session folder already contains images and a manifest
 * (written incrementally by [SessionManager]). This class provides
 * additional export capabilities:
 *
 *   - Re-export (regenerate manifest from current session state)
 *   - ZIP packaging for sharing via email, Bluetooth, etc.
 *   - Share intent creation for Android's share sheet
 *
 * The export folder structure matches what the Windows desktop app expects:
 *
 *     toolsnap_exports/
 *     └── 2026-02-03_boring-bar-A123/
 *         ├── manifest.json
 *         ├── body.jpg
 *         ├── insert.jpg
 *         └── ...
 */
class SessionExporter(private val context: Context) {

    /**
     * Re-export a session — regenerates the manifest from current state.
     * Useful after editing fields on the detail screen.
     *
     * @param session   the session to export
     * @param sessionDir  the session's folder on disk
     * @return true if export succeeded
     */
    fun reExport(session: CaptureSession, sessionDir: File): Boolean {
        return try {
            JsonUtils.writeManifest(session, sessionDir)
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    /**
     * Package a session folder into a ZIP file for sharing.
     * The ZIP mirrors the folder structure:
     *
     *     <tool-name>.zip
     *     └── <session-folder-name>/
     *         ├── manifest.json
     *         ├── body.jpg
     *         └── ...
     *
     * @param sessionDir  the session folder to package
     * @return the ZIP file, or null on failure
     */
    fun packageAsZip(sessionDir: File): File? {
        if (!sessionDir.exists() || !sessionDir.isDirectory) return null

        val zipFile = File(context.cacheDir, "${sessionDir.name}.zip")

        return try {
            ZipOutputStream(FileOutputStream(zipFile)).use { zos ->
                val files = sessionDir.listFiles() ?: return null

                for (file in files) {
                    if (!file.isFile) continue

                    val entryName = "${sessionDir.name}/${file.name}"
                    zos.putNextEntry(ZipEntry(entryName))
                    file.inputStream().use { it.copyTo(zos) }
                    zos.closeEntry()
                }
            }
            zipFile
        } catch (e: Exception) {
            e.printStackTrace()
            zipFile.delete()
            null
        }
    }

    /**
     * Create a share intent for a session's ZIP package.
     * Uses FileProvider for secure URI sharing.
     *
     * @param sessionDir  the session folder to share
     * @return a share Intent, or null if packaging failed
     */
    fun createShareIntent(sessionDir: File): Intent? {
        val zipFile = packageAsZip(sessionDir) ?: return null

        val uri: Uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            zipFile
        )

        return Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
    }

    /**
     * Verify a session export is complete and valid.
     * Checks that the manifest exists and all referenced images are present.
     *
     * @param sessionDir  the session folder to verify
     * @return list of issues found (empty = valid)
     */
    fun verifyExport(sessionDir: File): List<String> {
        val issues = mutableListOf<String>()

        val manifestFile = FileUtils.manifestFile(sessionDir)
        if (!manifestFile.exists()) {
            issues.add("Missing manifest.json")
            return issues
        }

        val manifest = JsonUtils.readManifest(sessionDir)
        if (manifest == null) {
            issues.add("Cannot parse manifest.json")
            return issues
        }

        // Check each field that claims to have an image
        for ((fieldName, fieldData) in manifest.fields) {
            if (fieldData.imageFile != null) {
                val imageFile = File(sessionDir, fieldData.imageFile)
                if (!imageFile.exists()) {
                    issues.add("Missing image: ${fieldData.imageFile} (${fieldName})")
                }
            }
        }

        return issues
    }

    /**
     * Get export summary text for display.
     */
    fun getExportSummary(session: CaptureSession): String {
        val lines = mutableListOf<String>()
        lines.add("Tool: ${session.toolName}")
        lines.add("Captured: ${session.capturedCount}/${session.totalFields}")

        if (session.skippedCount > 0) {
            lines.add("Skipped: ${session.skippedCount}")
        }

        for (field in CaptureField.entries) {
            val status = session.fieldStatuses[field] ?: continue
            val icon = when (status) {
                com.toolsnap.core.model.FieldStatus.CAPTURED -> "✓"
                com.toolsnap.core.model.FieldStatus.SKIPPED -> "—"
                com.toolsnap.core.model.FieldStatus.OCR_NEEDS_REVIEW -> "⚠"
                com.toolsnap.core.model.FieldStatus.PENDING -> "○"
            }
            lines.add("  $icon ${field.displayName}")
        }

        return lines.joinToString("\n")
    }
}
