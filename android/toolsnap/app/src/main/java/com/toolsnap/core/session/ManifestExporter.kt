package com.toolsnap.core.session

import android.util.Log
import com.toolsnap.core.model.CaptureField
import com.toolsnap.core.model.CaptureSession
import com.toolsnap.core.model.ComponentLink
import com.toolsnap.core.model.PendingComponent
import com.toolsnap.core.model.Tool
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.model.ToolStatus
import com.toolsnap.utils.ManifestV3
import java.io.File

private const val TAG = "ManifestExporter"

/**
 * Converts a CaptureSession + ToolCategory into Tool objects
 * and writes a V3 manifest for PC import.
 *
 * The V3 manifest sits alongside the V1 manifest.json as
 * manifest_v3.json. The PC importer prefers V3 when present.
 *
 * For assemblies, pending components are included as additional
 * Tool rows + ComponentLink rows in the manifest.
 */
internal object ManifestExporter {

    /**
     * Build Tool objects from session data and write V3 manifest.
     *
     * @param session      the active capture session
     * @param dir          the session folder on disk
     * @param category     the selected tool category
     * @param components   pending component links (empty for non-assemblies)
     */
    fun writeV3(
        session: CaptureSession,
        dir: File,
        category: ToolCategory,
        components: List<PendingComponent> = emptyList()
    ) {
        try {
            val tool = buildPrimaryTool(session, category)
            val allTools = mutableListOf(tool)
            val links = mutableListOf<ComponentLink>()

            for (pc in components) {
                val childTool = pc.tool
                childTool.touch()
                allTools.add(childTool)

                links.add(
                    ComponentLink(
                        parentToolId = tool.toolId,
                        childToolId = childTool.toolId,
                        role = pc.role,
                        quantity = pc.quantity,
                        notes = pc.notes
                    )
                )
            }

            ManifestV3.writeManifest(allTools, links, dir)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to write V3 manifest: ${e.message}", e)
        }
    }

    /**
     * Build the primary Tool from session form data.
     */
    private fun buildPrimaryTool(
        session: CaptureSession,
        category: ToolCategory
    ): Tool {
        val tool = Tool(
            name = session.toolName,
            category = category,
            isAssembly = category.isAssembly
        )

        // Populate from TOOL_DATA formData
        val toolData = session.formDataMap[CaptureField.TOOL_DATA]
        if (toolData != null) {
            for ((k, v) in toolData.values) {
                when (k) {
                    "manufacturer" -> tool.manufacturer = v
                    "catalog_number" -> tool.catalogNumber = v
                    "mpn_iso" -> tool.mpnIso = v
                    "description" -> tool.description = v
                    "notes" -> tool.notes = v
                    "tool_category" -> { /* skip — stored as category */ }
                    else -> tool.attributes[k] = v
                }
            }
            tool.status = ToolStatus.CAPTURED
        }

        // Also check BODY formData for category stash + extra attrs
        val bodyData = session.formDataMap[CaptureField.BODY]
        if (bodyData != null) {
            for ((k, v) in bodyData.values) {
                if (k != "tool_category" && k !in tool.attributes) {
                    tool.attributes[k] = v
                }
            }
        }

        // Collect photos
        for (field in CaptureField.entries) {
            val path = session.imagePaths[field]
            if (path != null) {
                tool.photoPaths.add(path)
            }
        }

        tool.touch()
        return tool
    }
}
