package com.toolsnap.core.model

/**
 * Unit system for dimensional fields on a component.
 *
 * Stored per-component so a metric-only insert can live alongside
 * an imperial body in the same assembly.  Dropdown lists (diameter,
 * length, IC size, etc.) switch their option set based on this value.
 *
 * Values are stored as-entered — "1/2\"" or "12.7mm" — no automatic
 * conversion is performed.
 */
enum class UnitSystem(val displayName: String) {
    IMPERIAL("Imperial (inch)"),
    METRIC("Metric (mm)");
}
