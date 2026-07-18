package com.toolsnap.core.model

import java.time.Instant
import java.util.UUID

/**
 * A single row in the Tools table — every physical item in the shop.
 *
 * End mills, boring bar bodies, inserts, screws, collets — all Tools.
 * [category] determines which form fields appear during capture.
 * [isAssembly] indicates whether this tool has child components
 * linked via [ComponentLink].
 *
 * Universal fields ([manufacturer], [catalogNumber], [description])
 * are first-class properties. Category-specific fields live in the
 * [attributes] map, keyed by the field keys from [ComponentTemplates].
 *
 * [photoPaths] holds 0–N photo filenames for this tool (body shot,
 * label close-up, etc.).
 */
data class Tool(
    val toolId: String = UUID.randomUUID().toString(),
    var name: String = "",
    var category: ToolCategory = ToolCategory.OTHER,
    var isAssembly: Boolean = false,
    var status: ToolStatus = ToolStatus.PENDING,

    // --- Universal catalog fields ---
    var manufacturer: String? = null,
    var catalogNumber: String? = null,
    var description: String? = null,
    var mpnIso: String? = null,
    var unitSystem: UnitSystem = UnitSystem.IMPERIAL,

    // --- Category-specific fields ---
    val attributes: MutableMap<String, String> = mutableMapOf(),

    // --- Photos ---
    val photoPaths: MutableList<String> = mutableListOf(),

    // --- Organization ---
    val tags: MutableList<String> = mutableListOf(),
    var notes: String? = null,

    // --- Timestamps ---
    val createdAt: Instant = Instant.now(),
    var modifiedAt: Instant = Instant.now()
) {
    /** True if this tool has any captured data beyond defaults. */
    val hasData: Boolean
        get() = manufacturer != null ||
                catalogNumber != null ||
                description != null ||
                mpnIso != null ||
                attributes.isNotEmpty() ||
                photoPaths.isNotEmpty()

    /** Update [modifiedAt] to now. */
    fun touch() {
        modifiedAt = Instant.now()
    }

    /**
     * One-line display summary.
     *
     * INSERT category: prefers manufacturer + mpnIso (e.g. "Sandvik Coromant CNMG 120408-PM")
     *   because that's what machinists call inserts — the EDP is just an ordering code.
     * Everything else: manufacturer + catalogNumber, then name, then category.
     */
    fun displaySummary(): String {
        val mfg = manufacturer?.takeIf { it.isNotBlank() }
        val cat = catalogNumber?.takeIf { it.isNotBlank() }
        val iso = mpnIso?.takeIf { it.isNotBlank() }

        return when {
            // INSERT: prefer MPN/ISO designation over EDP
            category == ToolCategory.INSERT && mfg != null && iso != null -> "$mfg $iso"
            category == ToolCategory.INSERT && iso != null -> iso
            // Default: manufacturer + catalog number
            mfg != null && cat != null -> "$mfg $cat"
            cat != null -> cat
            name.isNotBlank() -> name
            else -> category.displayName
        }
    }

    /**
     * Merge new attribute values. Existing keys are overwritten,
     * new keys are added, blank values are removed.
     */
    fun mergeAttributes(values: Map<String, String>) {
        for ((k, v) in values) {
            if (v.isBlank()) attributes.remove(k) else attributes[k] = v
        }
        touch()
    }

    /**
     * Photo filename for disk storage.
     * If the tool has one photo: "photo.jpg"
     * Multiple: "photo_0.jpg", "photo_1.jpg", etc.
     */
    fun photoFileName(index: Int = 0): String {
        val suffix = if (photoPaths.size <= 1 && index == 0) "" else "_$index"
        return "photo${suffix}.jpg"
    }
}
