package com.toolsnap.config

/**
 * Material → coating recommendation data.
 *
 * Used in two places:
 * 1. The standalone Coating Guide screen (reference tool)
 * 2. The insert component form — when the user selects a workpiece
 *    material, the coating dropdown reorders to show best-fit first
 *    via [reorderCoatingsForMaterial].
 */

data class CoatingRecommendation(
    val name: String,
    val reason: String
)

/**
 * Map of workpiece material → ranked list of coating recommendations.
 * Rankings are best-first.  Each reason is one short sentence a
 * machinist can act on at the spindle.
 */
val materialToCoatings: Map<String, List<CoatingRecommendation>> = mapOf(

    "Steel" to listOf(
        CoatingRecommendation("TiAlN", "General-purpose steel workhorse — good heat resistance at moderate speeds"),
        CoatingRecommendation("AlTiN", "Higher aluminum content adds thermal barrier for aggressive feeds"),
        CoatingRecommendation("TiCN", "Hard and slick — ideal for lower-speed steel finishing"),
        CoatingRecommendation("TiN", "Economical all-around coating for mild and medium carbon steel"),
        CoatingRecommendation("AlCrN", "Excellent oxidation resistance on tough alloy steels"),
    ),

    "Stainless Steel" to listOf(
        CoatingRecommendation("AlTiN", "Handles high heat from work-hardening stainless grades"),
        CoatingRecommendation("TiAlN", "Thermal barrier reduces crater wear on austenitic stainless"),
        CoatingRecommendation("AlCrN", "Excellent oxidation resistance at elevated temps"),
        CoatingRecommendation("TiCN", "High hardness resists abrasive wear on martensitic grades"),
        CoatingRecommendation("Nitriding", "Low-cost option for short-run stainless work"),
    ),

    "Aluminum" to listOf(
        CoatingRecommendation("DLC", "Low friction prevents built-up edge — top pick for non-ferrous"),
        CoatingRecommendation("ZrN", "Slippery finish resists aluminum welding to the edge"),
        CoatingRecommendation("Uncoated / Bright", "Polished uncoated carbide works well with sharp edges on aluminum"),
        CoatingRecommendation("TiN", "Budget option — adequate for low-volume aluminum work"),
        CoatingRecommendation("CVD Diamond", "Best for high-silicon aluminum alloys (>12% Si)"),
    ),

    "Cast Iron" to listOf(
        CoatingRecommendation("TiAlN", "Handles abrasive graphite inclusions in gray and ductile iron"),
        CoatingRecommendation("AlTiN", "High-temp stability for dry machining cast iron"),
        CoatingRecommendation("CVD Diamond", "Exceptional wear life on abrasive CGI and gray iron"),
        CoatingRecommendation("TiCN", "Hard coating resists flank wear from abrasive cast iron"),
        CoatingRecommendation("AlCrN", "Good all-around for nodular and malleable iron"),
    ),

    "Titanium Alloys" to listOf(
        CoatingRecommendation("AlTiN", "Thermal barrier critical for titanium's poor heat conductivity"),
        CoatingRecommendation("TiAlN", "Proven performer on Ti-6Al-4V at moderate speeds"),
        CoatingRecommendation("AlCrN", "Resists chemical reaction between coating and titanium"),
        CoatingRecommendation("Uncoated / Bright", "Sharp uncoated edges sometimes outperform coated on titanium"),
        CoatingRecommendation("CrN", "Low friction, low chemical affinity with titanium"),
    ),

    "Nickel Alloys / Inconel" to listOf(
        CoatingRecommendation("AlTiN", "Essential thermal barrier for Inconel's extreme heat generation"),
        CoatingRecommendation("AlCrN", "Oxidation-resistant at the very high temps nickel alloys produce"),
        CoatingRecommendation("TiAlN", "Proven on Waspaloy, Hastelloy, and other nickel-base alloys"),
        CoatingRecommendation("Uncoated / Bright", "Some shops prefer sharp uncoated for light finishing passes"),
        CoatingRecommendation("TiN", "Budget alternative for short-run nickel alloy work"),
    ),

    "Hardened Steel" to listOf(
        CoatingRecommendation("AlTiN", "High-heat coating essential above 45 HRC"),
        CoatingRecommendation("AlCrN", "Excellent for hard milling above 50 HRC"),
        CoatingRecommendation("TiAlN", "Reliable on hardened D2, H13, and tool steels"),
        CoatingRecommendation("CBN", "Best choice for continuous cuts above 55 HRC"),
        CoatingRecommendation("TiCN", "Works for interrupted cuts in hardened steel below 50 HRC"),
    ),

    "Copper / Brass" to listOf(
        CoatingRecommendation("DLC", "Prevents copper adhesion — very low friction"),
        CoatingRecommendation("ZrN", "Excellent non-stick surface for copper and brass"),
        CoatingRecommendation("Uncoated / Bright", "Sharp polished edges work well on soft copper alloys"),
        CoatingRecommendation("TiN", "Adequate for general brass machining"),
        CoatingRecommendation("CrN", "Low-friction option that resists copper buildup"),
    ),

    "Plastics" to listOf(
        CoatingRecommendation("DLC", "Ultra-low friction gives clean cuts with no melting"),
        CoatingRecommendation("Uncoated / Bright", "Razor-sharp uncoated edges for soft plastics"),
        CoatingRecommendation("ZrN", "Slick surface prevents material from sticking"),
        CoatingRecommendation("CrN", "Smooth finish and low friction for engineering plastics"),
        CoatingRecommendation("CVD Diamond", "Best for glass-filled and abrasive composites"),
    ),

    "Composites (CFRP / Fiberglass)" to listOf(
        CoatingRecommendation("CVD Diamond", "Handles extreme abrasion from carbon and glass fibers"),
        CoatingRecommendation("PCD", "Longest life on CFRP — diamond beats everything here"),
        CoatingRecommendation("DLC", "Good mid-range option for short-run composite work"),
        CoatingRecommendation("TiAlN", "Adequate for fiberglass at lower speeds"),
        CoatingRecommendation("Uncoated / Bright", "Sharp carbide works for quick prototype cuts"),
    ),

    "Graphite" to listOf(
        CoatingRecommendation("CVD Diamond", "Essential — graphite destroys uncoated tools in minutes"),
        CoatingRecommendation("DLC", "Good alternative to full diamond for lighter graphite work"),
        CoatingRecommendation("TiAlN", "Budget option but expect 5-10x less life than diamond"),
        CoatingRecommendation("AlTiN", "Acceptable for short-run graphite electrode work"),
        CoatingRecommendation("Uncoated / Bright", "Not recommended — included for reference only"),
    ),
)

/** Material names in display order (used by dropdowns). */
val materialNames: List<String> = materialToCoatings.keys.toList()

// ==========================================================================
// Integration hook for the insert coating dropdown
// ==========================================================================

/**
 * Reorder the standard coating dropdown options so that recommended
 * coatings for [material] appear first (in recommendation order),
 * followed by a separator, then the remaining coatings alphabetically.
 *
 * Returns the full list if [material] is blank or unrecognized.
 *
 * Each recommended entry is prefixed with "★ " and gets its reason
 * appended in parentheses for inline display in the dropdown.
 *
 * @param allCoatings   the full coating option list (from ComponentTemplates)
 * @param material      the selected workpiece material
 * @return              reordered list suitable for a dropdown
 */
fun reorderCoatingsForMaterial(
    allCoatings: List<String>,
    material: String
): List<CoatingDropdownEntry> {
    val recommendations = materialToCoatings[material]
        ?: return allCoatings.map { CoatingDropdownEntry(it, null, false) }

    val recoNames = recommendations.map { it.name }.toSet()

    val recommended = recommendations.map { rec ->
        // Find the full coating string that contains this short name
        val fullName = allCoatings.firstOrNull { option ->
            option.startsWith(rec.name) || option.contains(rec.name)
        } ?: rec.name
        CoatingDropdownEntry(
            coatingName = fullName,
            reason = rec.reason,
            isRecommended = true
        )
    }

    val remaining = allCoatings
        .filter { option -> recoNames.none { name ->
            option.startsWith(name) || option.contains(name)
        }}
        .map { CoatingDropdownEntry(it, null, false) }

    return recommended + remaining
}

/**
 * A single entry in the reordered coating dropdown.
 * The UI renders recommended entries with a star and reason subtitle.
 */
data class CoatingDropdownEntry(
    val coatingName: String,
    val reason: String?,
    val isRecommended: Boolean
)
