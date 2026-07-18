package com.toolsnap.core.model

/**
 * A row in the Components junction table.
 *
 * Links a child tool (insert, screw, shim, etc.) to a parent tool
 * (an assembly like a boring bar or face mill).  The [role] field
 * describes how the child participates in the assembly.
 *
 * The same child tool can appear in multiple assemblies (a CNMG insert
 * might fit three different boring bars).  The same parent can have
 * multiple children with different roles.
 *
 * On the phone, ComponentLinks are captured alongside the assembly.
 * On the PC, they're imported into the Components table and also
 * used to derive the Compatibility table.
 */
data class ComponentLink(
    val parentToolId: String,
    val childToolId: String,
    val role: ComponentRole,
    val quantity: Int = 1,
    val notes: String? = null
)

/**
 * How a child tool participates in an assembly.
 *
 * The enum value is stored as its [name] in the manifest JSON
 * and the Components table's `role` column.
 */
enum class ComponentRole(val displayName: String) {
    INSERT("Insert"),
    WIPER_INSERT("Wiper Insert"),
    SCREW("Screw"),
    SHIM("Shim / Seat"),
    CLAMP("Clamp"),
    WEDGE("Wedge"),
    COOLANT_PLUG("Coolant Plug / Nozzle"),
    COLLET("Collet"),
    ADAPTER("Adapter / Extension"),
    OTHER("Other");

    companion object {
        fun fromName(name: String): ComponentRole =
            try { valueOf(name) } catch (_: Exception) { OTHER }
    }
}
