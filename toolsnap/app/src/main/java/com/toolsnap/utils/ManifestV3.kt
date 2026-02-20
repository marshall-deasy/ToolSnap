package com.toolsnap.utils

import com.toolsnap.config.CaptureConfig
import com.toolsnap.core.model.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.time.Instant

/**
 * V3 manifest serialization — flat relational format.
 *
 * Write path always produces V3. Read path auto-detects V1/V2/V3
 * and delegates legacy formats to [ManifestMigration].
 */
object ManifestV3 {

    internal val json = Json {
        prettyPrint = true
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    // ==================================================================
    // Write
    // ==================================================================

    fun writeManifest(
        tools: List<Tool>,
        links: List<ComponentLink>,
        sessionDir: File
    ) {
        val manifest = toManifest(tools, links)
        val file = File(sessionDir, CaptureConfig.MANIFEST_FILE_NAME)
        val tmp = File(sessionDir, ".manifest_tmp.json")
        tmp.writeText(json.encodeToString(manifest))
        tmp.renameTo(file)
    }

    fun toManifest(
        tools: List<Tool>,
        links: List<ComponentLink>
    ): SessionManifestV3 {
        return SessionManifestV3(
            schemaVersion = 3,
            exportedAt = Instant.now().toString(),
            tools = tools.map { t ->
                ToolManifest(
                    toolId = t.toolId,
                    name = t.name,
                    category = t.category.name,
                    type = if (t.isAssembly) "assembly" else "standalone",
                    status = t.status.name,
                    manufacturer = t.manufacturer,
                    catalogNumber = t.catalogNumber,
                    mpnIso = t.mpnIso,
                    description = t.description,
                    unitSystem = t.unitSystem.name,
                    attributes = t.attributes.toMap(),
                    photos = t.photoPaths.mapIndexed { idx, _ ->
                        t.photoFileName(idx)
                    },
                    tags = t.tags.toList(),
                    notes = t.notes,
                    createdAt = t.createdAt.toString(),
                    modifiedAt = t.modifiedAt.toString()
                )
            },
            components = links.map { link ->
                ComponentLinkManifest(
                    parentToolId = link.parentToolId,
                    childToolId = link.childToolId,
                    role = link.role.name,
                    quantity = link.quantity,
                    notes = link.notes
                )
            }
        )
    }

    // ==================================================================
    // Read (auto-detects V1 / V2 / V3)
    // ==================================================================

    data class ManifestReadResult(
        val tools: List<Tool>,
        val links: List<ComponentLink>
    )

    fun readManifest(sessionDir: File): ManifestReadResult? {
        val file = File(sessionDir, CaptureConfig.MANIFEST_FILE_NAME)
        if (!file.exists()) return null

        return try {
            val text = file.readText()
            when {
                text.contains("\"schemaVersion\":3") ||
                text.contains("\"schemaVersion\": 3") ->
                    readV3(text, sessionDir)
                text.contains("\"schemaVersion\"") ->
                    ManifestMigration.migrateV2(text, sessionDir)
                else ->
                    ManifestMigration.migrateV1(text, sessionDir)
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    // ------------------------------------------------------------------
    // V3 reader
    // ------------------------------------------------------------------

    private fun readV3(text: String, sessionDir: File): ManifestReadResult {
        val m = json.decodeFromString<SessionManifestV3>(text)

        val tools = m.tools.map { tm ->
            val tool = Tool(
                toolId = tm.toolId,
                name = tm.name,
                category = ToolCategory.fromName(tm.category),
                isAssembly = tm.type == "assembly",
                status = ToolStatus.fromName(tm.status),
                manufacturer = tm.manufacturer,
                catalogNumber = tm.catalogNumber,
                mpnIso = tm.mpnIso,
                description = tm.description,
                unitSystem = unitSystemFromName(tm.unitSystem),
                notes = tm.notes,
                createdAt = Instant.parse(tm.createdAt),
                modifiedAt = Instant.parse(tm.modifiedAt)
            )
            tool.attributes.putAll(tm.attributes)
            tool.tags.addAll(tm.tags)
            for (photoName in tm.photos) {
                val imgFile = File(sessionDir, photoName)
                if (imgFile.exists()) tool.photoPaths.add(imgFile.absolutePath)
            }
            tool
        }

        val links = m.components.map { cm ->
            ComponentLink(
                parentToolId = cm.parentToolId,
                childToolId = cm.childToolId,
                role = ComponentRole.fromName(cm.role),
                quantity = cm.quantity,
                notes = cm.notes
            )
        }

        return ManifestReadResult(tools, links)
    }

    internal fun unitSystemFromName(name: String?): UnitSystem =
        try { name?.let { UnitSystem.valueOf(it) } ?: UnitSystem.IMPERIAL }
        catch (_: Exception) { UnitSystem.IMPERIAL }
}

// ============================================================================
// V3 serialization classes
// ============================================================================

@Serializable
data class SessionManifestV3(
    val schemaVersion: Int = 3,
    val exportedAt: String,
    val tools: List<ToolManifest> = emptyList(),
    val components: List<ComponentLinkManifest> = emptyList()
)

@Serializable
data class ToolManifest(
    val toolId: String,
    val name: String,
    val category: String,
    val type: String,
    val status: String,
    val manufacturer: String? = null,
    val catalogNumber: String? = null,
    val mpnIso: String? = null,
    val description: String? = null,
    val unitSystem: String? = null,
    val attributes: Map<String, String> = emptyMap(),
    val photos: List<String> = emptyList(),
    val tags: List<String> = emptyList(),
    val notes: String? = null,
    val createdAt: String,
    val modifiedAt: String
)

@Serializable
data class ComponentLinkManifest(
    val parentToolId: String,
    val childToolId: String,
    val role: String,
    val quantity: Int = 1,
    val notes: String? = null
)
