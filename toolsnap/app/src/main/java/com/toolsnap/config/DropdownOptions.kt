package com.toolsnap.config

/**
 * Curated dropdown option lists for tool capture forms.
 *
 * Single source of truth for all option values used in
 * dropdown fields across the app. Referenced by
 * [ComponentTemplates] when building per-category forms.
 */
object DropdownOptions {

    /** Sentinel value for "Other" — triggers free-text entry in the UI. */
    const val OTHER_OPTION = "Other\u2026"

    // ==================================================================
    // Manufacturer
    // ==================================================================

    val manufacturers = listOf(
        "Sandvik Coromant", "Kennametal", "Iscar", "Seco Tools", "Walter",
        "Mitsubishi Materials", "Kyocera", "Sumitomo", "Tungaloy",
        "Dormer Pramet", "OSG", "YG-1", "TaeguTec", "Ingersoll",
        "CERATIZIT", "Widia", "Greenleaf", "Harvey Tool",
        "Helical Solutions", "Niagara Cutter", "Garr Tool", "Gorilla Mill",
        "Micro 100", "Carmex", "Emuge", "Nachi", "Guhring", "MAPAL",
        "Accupro", "Scientific Cutting Tools (SCT)", OTHER_OPTION
    )

    // ==================================================================
    // Coatings
    // ==================================================================

    val coatings = listOf(
        "Uncoated / Bright",
        "TiN (Titanium Nitride)",
        "TiCN (Titanium Carbonitride)",
        "TiAlN (Titanium Aluminum Nitride)",
        "AlTiN (Aluminum Titanium Nitride)",
        "AlCrN (Aluminum Chromium Nitride)",
        "CrN (Chromium Nitride)",
        "ZrN (Zirconium Nitride)",
        "TiB2 (Titanium Diboride)",
        "DLC (Diamond-Like Carbon)",
        "CVD Diamond",
        "PCD (Polycrystalline Diamond)",
        "CBN (Cubic Boron Nitride)",
        "AlTiN Nano",
        "TiAlSiN (nanocomposite)",
        "Black Oxide",
        OTHER_OPTION
    )

    // ==================================================================
    // Dimensions — imperial / metric
    // ==================================================================

    val diametersImperial = listOf(
        "1/16\"", "3/32\"", "1/8\"", "5/32\"", "3/16\"", "7/32\"",
        "1/4\"", "5/16\"", "3/8\"", "7/16\"", "1/2\"", "9/16\"",
        "5/8\"", "3/4\"", "7/8\"", "1\"", "1-1/4\"", "1-1/2\"",
        "2\"", "2-1/2\"", "3\"", OTHER_OPTION
    )

    val diametersMetric = listOf(
        "1mm", "1.5mm", "2mm", "2.5mm", "3mm", "4mm", "5mm", "6mm",
        "8mm", "10mm", "12mm", "14mm", "16mm", "18mm", "20mm",
        "25mm", "32mm", "40mm", "50mm", "63mm", OTHER_OPTION
    )

    val noseRadiiImperial = listOf(
        "Sharp (0)", "0.004\"", "0.008\"", "0.010\"", "0.016\"",
        "0.020\"", "0.032\"", "0.047\"", "0.050\"", "0.060\"",
        "0.0625\"", "0.093\"", "0.120\"", "1/8\" (0.125\")",
        "3/16\" (0.188\")", "1/4\" (0.250\")", "3/8\" (0.375\")",
        "1/2\" (0.500\")", "Full Radius (Ball)", OTHER_OPTION
    )

    val noseRadiiMetric = listOf(
        "Sharp (0)", "0.1mm", "0.2mm", "0.4mm", "0.5mm", "0.8mm",
        "1.0mm", "1.2mm", "1.5mm", "1.6mm", "2.0mm", "2.4mm",
        "3.0mm", "3.2mm", "4.0mm", "5.0mm", "6.0mm", "8.0mm",
        "Full Radius (Ball)", OTHER_OPTION
    )

    val flutes = listOf(
        "1", "2", "3", "4", "5", "6", "7", "8", "10", "12", OTHER_OPTION
    )

    // ==================================================================
    // Shank / interface types
    // ==================================================================

    val shankTypes = listOf(
        "CAT40", "CAT50", "BT30", "BT40", "BT50",
        "HSK-A40", "HSK-A63", "HSK-A100",
        "Straight Shank (Weldon)", "Straight Shank (Haas/Set-Screw)",
        "ER16 Collet", "ER20 Collet", "ER25 Collet", "ER32 Collet", "ER40 Collet",
        "Morse Taper #1", "Morse Taper #2", "Morse Taper #3",
        "Morse Taper #4", "Morse Taper #5",
        "Square Shank (Turning)",
        "Capto C3", "Capto C4", "Capto C5", "Capto C6", "Capto C8",
        "KM25", "KM32", "KM40", "KM50",
        OTHER_OPTION
    )

    // ==================================================================
    // Body material
    // ==================================================================

    val bodyMaterials = listOf(
        "Solid Carbide",
        "High Speed Steel (HSS)",
        "Cobalt HSS (HSS-Co / M42)",
        "Powder Metal HSS (PM HSS)",
        "Steel (tool body)",
        "Heavy Metal / Carbide Reinforced",
        OTHER_OPTION
    )

    val boolean = listOf("Yes", "No")

    // ==================================================================
    // Insert-specific
    // ==================================================================

    val insertShapes = listOf(
        "C \u2014 Rhombic 80\u00B0",
        "D \u2014 Rhombic 55\u00B0",
        "K \u2014 Rhombic 55\u00B0 (parallelogram)",
        "R \u2014 Round",
        "S \u2014 Square",
        "T \u2014 Triangular",
        "V \u2014 Rhombic 35\u00B0",
        "W \u2014 Trigon 80\u00B0",
        "A \u2014 Rhombic 85\u00B0",
        "B \u2014 Rhombic 82\u00B0",
        "H \u2014 Hexagonal",
        "L \u2014 Rectangular",
        "O \u2014 Octagonal",
        "P \u2014 Pentagonal",
        OTHER_OPTION
    )

    val insertICImperial = listOf(
        "1/8\" IC", "5/32\" IC", "3/16\" IC",
        "1/4\" IC", "5/16\" IC", "3/8\" IC",
        "1/2\" IC", "5/8\" IC", "3/4\" IC", "1\" IC",
        OTHER_OPTION
    )

    val insertICMetric = listOf(
        "6mm IC", "8mm IC", "9.525mm IC",
        "12mm IC", "12.7mm IC", "16mm IC",
        "19.05mm IC", "25.4mm IC",
        OTHER_OPTION
    )

    val insertThicknessImperial = listOf(
        "3/32\"", "1/8\"", "5/32\"", "3/16\"", "1/4\"", OTHER_OPTION
    )

    val insertThicknessMetric = listOf(
        "2.38mm", "3.18mm", "3.97mm", "4.76mm", "5.56mm", "6.35mm",
        OTHER_OPTION
    )

    val handOfCut = listOf("Right", "Left", "Neutral")

    val rake = listOf("Positive", "Negative", "Neutral")

    // ==================================================================
    // Workpiece material (shared with CoatingData)
    // ==================================================================

    val workpieceMaterials = listOf(
        "Steel",
        "Stainless Steel",
        "Aluminum",
        "Cast Iron",
        "Titanium Alloys",
        "Nickel Alloys / Inconel",
        "Hardened Steel",
        "Copper / Brass",
        "Plastics",
        "Composites (CFRP / Fiberglass)",
        "Graphite"
    )

    // ==================================================================
    // Unit-aware selectors
    // ==================================================================

    fun diameters(unit: com.toolsnap.core.model.UnitSystem): List<String> =
        if (unit == com.toolsnap.core.model.UnitSystem.IMPERIAL) diametersImperial
        else diametersMetric

    fun noseRadii(unit: com.toolsnap.core.model.UnitSystem): List<String> =
        if (unit == com.toolsnap.core.model.UnitSystem.IMPERIAL) noseRadiiImperial
        else noseRadiiMetric
}
