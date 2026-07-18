package com.toolsnap.utils

import com.toolsnap.core.model.*
import kotlinx.serialization.Serializable
import java.io.File
import java.time.Instant

/**
 * V1 and V2 manifest migration — read-only.
 *
 * Parses legacy manifest formats and converts them to the
 * same [ManifestV3.ManifestReadResult] used by V3 reads.
 * Original manifest files are never modified on disk.
 */
internal object ManifestMigration {

    // ------------------------------------------------------------------
    // V2 → V3
    // ------------------------------------------------------------------

    fun migrateV2(
        text: String,
        sessionDir: File
    ): ManifestV3.ManifestReadResult {
        val v2 = ManifestV3.json.decodeFromString<AssemblyManifestV2>(text)

        val tools = mutableListOf<Tool>()
        val links = mutableListOf<ComponentLink>()

        val parentCategory = assemblyTypeToCategory(v2.assemblyType)
        val isAssembly = v2.components.size > 1

        val parentTool = Tool(
            toolId = v2.assemblyId,
            name = v2.assemblyName,
            category = parentCategory,
            isAssembly = isAssembly,
            status = if (v2.isComplete) ToolStatus.CAPTURED else ToolStatus.PARTIAL,
            createdAt = Instant.parse(v2.createdAt),
            modifiedAt = Instant.parse(v2.modifiedAt),
            notes = v2.notes
        )
        parentTool.tags.addAll(v2.tags)

        for (cm in v2.components) {
            val compCategory = v2ComponentTypeToCategory(cm.componentType)
            val tool = Tool(
                toolId = cm.componentId,
                name = cm.description ?: cm.catalogNumber ?: compCategory.displayName,
                category = compCategory,
                status = ToolStatus.fromName(cm.status),
                manufacturer = cm.manufacturer,
                catalogNumber = cm.catalogNumber,
                description = cm.description,
                unitSystem = ManifestV3.unitSystemFromName(cm.unitSystem),
                notes = cm.notes
            )
            tool.attributes.putAll(cm.attributes)
            cm.photoFile?.let { fname ->
                val f = File(sessionDir, fname)
                if (f.exists()) tool.photoPaths.add(f.absolutePath)
            }

            if (compCategory == parentCategory) {
                parentTool.manufacturer = tool.manufacturer
                parentTool.catalogNumber = tool.catalogNumber
                parentTool.description = tool.description
                parentTool.unitSystem = tool.unitSystem
                parentTool.attributes.putAll(tool.attributes)
                parentTool.photoPaths.addAll(tool.photoPaths)
                if (tool.status == ToolStatus.CAPTURED) {
                    parentTool.status = ToolStatus.CAPTURED
                }
            } else {
                tools.add(tool)
                links.add(ComponentLink(
                    parentToolId = parentTool.toolId,
                    childToolId = tool.toolId,
                    role = v2ComponentTypeToRole(cm.componentType)
                ))
            }
        }

        for (photoName in v2.assemblyPhotos) {
            val f = File(sessionDir, photoName)
            if (f.exists()) parentTool.photoPaths.add(f.absolutePath)
        }

        tools.add(0, parentTool)
        return ManifestV3.ManifestReadResult(tools, links)
    }

    // ------------------------------------------------------------------
    // V1 → V3
    // ------------------------------------------------------------------

    fun migrateV1(
        text: String,
        sessionDir: File
    ): ManifestV3.ManifestReadResult {
        val v1 = ManifestV3.json.decodeFromString<SessionManifestV1>(text)

        val tools = mutableListOf<Tool>()
        val links = mutableListOf<ComponentLink>()

        val parentTool = Tool(
            toolId = v1.sessionId,
            name = v1.toolName,
            category = ToolCategory.OTHER,
            isAssembly = true,
            createdAt = Instant.parse(v1.createdAt),
            modifiedAt = Instant.parse(v1.createdAt)
        )

        val bodyField = v1.fields["body"]
        if (bodyField != null) {
            bodyField.imageFile?.let { fname ->
                val f = File(sessionDir, fname)
                if (f.exists()) parentTool.photoPaths.add(f.absolutePath)
            }
        }

        val toolData = v1.fields["tool_data"]
        if (toolData?.formData != null) {
            val fd = toolData.formData
            fd.values["description"]?.let { parentTool.description = it }
            fd.values["manufacturer"]?.let { parentTool.manufacturer = it }
            fd.values["catalog_number"]?.let { parentTool.catalogNumber = it }
            for ((k, v) in fd.values) {
                if (k !in setOf("description", "manufacturer", "catalog_number")) {
                    parentTool.attributes[k] = v
                }
            }
        }
        parentTool.status = if (v1.isComplete) ToolStatus.CAPTURED
            else ToolStatus.PARTIAL
        tools.add(parentTool)

        val insertField = v1.fields["insert"]
        if (insertField != null && insertField.status != "PENDING") {
            val insertTool = Tool(
                category = ToolCategory.INSERT,
                name = "Insert (migrated from V1)",
                status = ToolStatus.fromName(insertField.status),
                createdAt = parentTool.createdAt,
                modifiedAt = parentTool.createdAt
            )
            insertField.imageFile?.let { fname ->
                val f = File(sessionDir, fname)
                if (f.exists()) insertTool.photoPaths.add(f.absolutePath)
            }
            tools.add(insertTool)
            links.add(ComponentLink(
                parentToolId = parentTool.toolId,
                childToolId = insertTool.toolId,
                role = ComponentRole.INSERT
            ))
        }

        val hwField = v1.fields["hardware"]
        if (hwField != null && hwField.status != "PENDING") {
            val hwTool = Tool(
                category = ToolCategory.OTHER,
                name = "Hardware (migrated from V1)",
                status = ToolStatus.fromName(hwField.status),
                createdAt = parentTool.createdAt,
                modifiedAt = parentTool.createdAt
            )
            hwField.imageFile?.let { fname ->
                val f = File(sessionDir, fname)
                if (f.exists()) hwTool.photoPaths.add(f.absolutePath)
            }
            tools.add(hwTool)
            links.add(ComponentLink(
                parentToolId = parentTool.toolId,
                childToolId = hwTool.toolId,
                role = ComponentRole.OTHER
            ))
        }

        return ManifestV3.ManifestReadResult(tools, links)
    }

    // ------------------------------------------------------------------
    // V2 enum mapping helpers
    // ------------------------------------------------------------------

    private fun assemblyTypeToCategory(typeName: String): ToolCategory = when (typeName) {
        "END_MILL"         -> ToolCategory.END_MILL
        "INDEXABLE_MILL"   -> ToolCategory.INDEXABLE_MILL_BODY
        "DRILL_SOLID"      -> ToolCategory.DRILL
        "DRILL_INDEXABLE"  -> ToolCategory.INDEXABLE_DRILL_BODY
        "BORING_BAR"       -> ToolCategory.BORING_BAR_BODY
        "TURNING_TOOL"     -> ToolCategory.TURNING_HOLDER
        "THREADING_TOOL"   -> ToolCategory.THREADING_HOLDER
        "GROOVING_PARTING" -> ToolCategory.GROOVING_HOLDER
        "TAP"              -> ToolCategory.TAP
        "REAMER"           -> ToolCategory.REAMER
        "HOLDER_ONLY"      -> ToolCategory.HOLDER
        else               -> ToolCategory.OTHER
    }

    private fun v2ComponentTypeToCategory(typeName: String): ToolCategory = when (typeName) {
        "BODY"      -> ToolCategory.OTHER
        "INSERT"    -> ToolCategory.INSERT
        "HARDWARE"  -> ToolCategory.SCREW
        "ACCESSORY" -> ToolCategory.HOLDER
        else        -> ToolCategory.OTHER
    }

    private fun v2ComponentTypeToRole(typeName: String): ComponentRole = when (typeName) {
        "INSERT"    -> ComponentRole.INSERT
        "HARDWARE"  -> ComponentRole.SCREW
        "ACCESSORY" -> ComponentRole.ADAPTER
        else        -> ComponentRole.OTHER
    }
}

// ============================================================================
// V2 serialization classes (read-only, for migration)
// ============================================================================

@Serializable
data class AssemblyManifestV2(
    val schemaVersion: Int = 2,
    val assemblyId: String = "",
    val assemblyName: String = "",
    val assemblyType: String = "",
    val createdAt: String = "",
    val modifiedAt: String = "",
    val components: List<V2ComponentManifest> = emptyList(),
    val tags: List<String> = emptyList(),
    val notes: String? = null,
    val assemblyPhotos: List<String> = emptyList(),
    val isComplete: Boolean = false,
    val componentsCaptured: Int = 0,
    val componentsSkipped: Int = 0,
    val componentsTotal: Int = 0
)

@Serializable
data class V2ComponentManifest(
    val componentId: String = "",
    val componentType: String = "",
    val status: String = "",
    val manufacturer: String? = null,
    val catalogNumber: String? = null,
    val description: String? = null,
    val unitSystem: String? = null,
    val photoFile: String? = null,
    val attributes: Map<String, String> = emptyMap(),
    val vendor: String? = null,
    val vendorPartNumber: String? = null,
    val unitCost: Double? = null,
    val notes: String? = null
)

// ============================================================================
// V1 serialization classes (read-only, for migration)
// ============================================================================

@Serializable
data class SessionManifestV1(
    val sessionId: String = "",
    val toolName: String = "",
    val createdAt: String = "",
    val fields: Map<String, FieldManifestV1> = emptyMap(),
    val isComplete: Boolean = false,
    val fieldsCaptured: Int = 0,
    val fieldsSkipped: Int = 0,
    val fieldsTotal: Int = 5
)

@Serializable
data class FieldManifestV1(
    val status: String = "",
    val imageFile: String? = null,
    val ocrText: String? = null,
    val entryMethod: String? = null,
    val formData: FormDataV1? = null
)

@Serializable
data class FormDataV1(
    val entryMethod: String = "manual",
    val values: Map<String, String> = emptyMap()
)
