package com.toolsnap.core.model

/**
 * A component link being built during the assembly capture wizard.
 *
 * Holds the child [Tool] (either newly created inline or referenced
 * from a prior session), plus the [role] and [quantity] that will
 * become a [ComponentLink] when the manifest is written.
 *
 * This is wizard-only state — not persisted until finalizeSession()
 * converts it into Tool rows + ComponentLink rows in the V3 manifest.
 */
data class PendingComponent(
    val tool: Tool,
    val role: ComponentRole,
    val quantity: Int = 1,
    val notes: String? = null
) {
    /** One-line display for the link list UI. */
    fun displayLine(): String {
        val prefix = role.displayName
        val detail = tool.displaySummary()
        val qty = if (quantity > 1) " ×$quantity" else ""
        return "$prefix: $detail$qty"
    }
}
