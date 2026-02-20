package com.toolsnap.core.ocr

import com.toolsnap.config.DropdownOptions
import com.toolsnap.core.model.ToolCategory

/**
 * Classifies OCR elements into identity fields:
 *   manufacturer, catalogNumber (EDP), and mpnIso.
 *
 * Called between OCR completion and the picker screen to provide
 * auto-populated suggestions the user can accept or override.
 *
 * Strategy:
 *   1. Fuzzy-match each element against [DropdownOptions.manufacturers]
 *   2. Detect ISO-style insert designations via regex (for INSERT category)
 *   3. Everything else ranked by prominence → first unmatched = catalogNumber
 *
 * Context-aware:
 *   - [ToolCategory.INSERT]: enables MPN/ISO detection; label = "MPN / ISO"
 *   - All other categories: MPN/ISO field hidden; label logic unchanged
 */
object OcrFieldMatcher {

    /**
     * Result of auto-classification.
     * All fields are nullable — null means "no confident match found".
     */
    data class MatchResult(
        val manufacturer: String? = null,
        val manufacturerConfidence: Float = 0f,
        val catalogNumber: String? = null,
        val catalogNumberConfidence: Float = 0f,
        val mpnIso: String? = null,
        val mpnIsoConfidence: Float = 0f
    )

    // ── ISO insert designation patterns ─────────────────────────
    // Matches standard ISO turning insert codes like:
    //   CNMG120408, CCMT 09T3 08, WNMG 080412, DCMT 11T304
    // Also partial matches with embedded spaces from OCR tokenization.
    private val ISO_INSERT_REGEX = Regex(
        "^[A-Z]{4}\\s?\\d{2,3}\\s?T?\\d{2,4}\\s?\\d{0,2}$",
        RegexOption.IGNORE_CASE
    )

    // Broader catch: any 6-12 char alphanumeric block starting with
    // 2+ letters that looks like a manufacturer part number
    private val MPN_BROAD_REGEX = Regex(
        "^[A-Z]{2,}[\\d-]{2,}[A-Z\\d]*$",
        RegexOption.IGNORE_CASE
    )

    // ── Manufacturer fuzzy matching ─────────────────────────────

    /**
     * Normalized manufacturer names for matching.
     * Built once, compared against every OCR element.
     */
    private val MANUFACTURER_TOKENS: List<Pair<String, List<String>>> by lazy {
        DropdownOptions.manufacturers
            .filter { it != DropdownOptions.OTHER_OPTION }
            .map { name ->
                name to name.lowercase()
                    .replace(Regex("[^a-z0-9\\s]"), "")
                    .split(Regex("\\s+"))
                    .filter { it.length >= 2 }
            }
    }

    /**
     * Check if an OCR text token fuzzy-matches any known manufacturer.
     * Returns the matched manufacturer display name and a confidence score,
     * or null if no match.
     *
     * Matching rules (in priority order):
     *   1. Exact token match against any manufacturer token → 1.0
     *   2. OCR text contains a full manufacturer name → 0.95
     *   3. A manufacturer token starts-with the OCR text (min 4 chars) → 0.8
     *   4. Levenshtein distance ≤ 1 for tokens ≥ 5 chars → 0.7
     */
    private fun matchManufacturer(text: String): Pair<String, Float>? {
        val normalized = text.lowercase().replace(Regex("[^a-z0-9]"), "")
        if (normalized.length < 2) return null

        var bestMatch: String? = null
        var bestScore = 0f

        for ((displayName, tokens) in MANUFACTURER_TOKENS) {
            // Exact token match
            if (normalized in tokens) {
                if (1.0f > bestScore) {
                    bestMatch = displayName; bestScore = 1.0f
                }
                continue
            }

            // Full name containment (OCR text contains "sandvik coromant")
            val fullNorm = displayName.lowercase().replace(Regex("[^a-z0-9]"), "")
            if (fullNorm == normalized) {
                if (0.95f > bestScore) {
                    bestMatch = displayName; bestScore = 0.95f
                }
                continue
            }

            // Prefix match (min 4 chars)
            if (normalized.length >= 4) {
                for (token in tokens) {
                    if (token.startsWith(normalized) || normalized.startsWith(token)) {
                        if (0.8f > bestScore) {
                            bestMatch = displayName; bestScore = 0.8f
                        }
                    }
                }
            }

            // Levenshtein distance ≤ 1 for longer tokens
            if (normalized.length >= 5) {
                for (token in tokens) {
                    if (token.length >= 5 && levenshtein(normalized, token) <= 1) {
                        if (0.7f > bestScore) {
                            bestMatch = displayName; bestScore = 0.7f
                        }
                    }
                }
            }
        }

        return if (bestMatch != null && bestScore >= 0.7f) {
            bestMatch to bestScore
        } else null
    }

    // ── ISO / MPN detection ─────────────────────────────────────

    /**
     * Check if a text token looks like an ISO insert designation
     * or a manufacturer part number (MPN).
     *
     * Returns confidence score or null if no match.
     */
    private fun matchMpnIso(text: String, category: ToolCategory): Pair<String, Float>? {
        if (category != ToolCategory.INSERT) return null

        val cleaned = text.trim().replace(Regex("\\s+"), "")

        // Strong ISO pattern (e.g. CNMG120408)
        if (ISO_INSERT_REGEX.matches(text.trim())) {
            return text.trim() to 0.95f
        }

        // Broader MPN pattern
        if (cleaned.length in 6..16 && MPN_BROAD_REGEX.matches(cleaned)) {
            return cleaned to 0.7f
        }

        return null
    }

    // ── Main entry point ────────────────────────────────────────

    /**
     * Classify a list of OCR elements into identity fields.
     *
     * Elements should already be sorted by prominence (as returned
     * by [OcrProcessor]). The matcher walks them in order, greedily
     * assigning to fields.
     *
     * @param elements  prominence-sorted OCR elements
     * @param category  current tool category (affects MPN/ISO detection)
     * @return          auto-populated field suggestions
     */
    fun classify(
        elements: List<OcrProcessor.OcrElement>,
        category: ToolCategory
    ): MatchResult {
        var mfgResult: Pair<String, Float>? = null   // displayName, confidence
        var catResult: Pair<String, Float>? = null    // raw text, confidence
        var mpnResult: Pair<String, Float>? = null    // raw text, confidence

        // Track which element indices are consumed
        val consumed = mutableSetOf<Int>()

        // Pass 1: manufacturer matching (highest priority)
        // May need to combine adjacent tokens ("Sandvik" + "Coromant")
        val mfgCandidates = mutableListOf<Triple<Int, String, Float>>() // index, displayName, score
        for ((i, el) in elements.withIndex()) {
            val match = matchManufacturer(el.text)
            if (match != null) {
                mfgCandidates.add(Triple(i, match.first, match.second))
            }
        }

        // Also try combining adjacent-line tokens for multi-word manufacturers
        for (i in 0 until elements.size - 1) {
            val el1 = elements[i]
            val el2 = elements[i + 1]
            if (el1.lineIndex == el2.lineIndex) {
                val combined = "${el1.text} ${el2.text}"
                val match = matchManufacturer(combined)
                if (match != null && match.second > (mfgCandidates.maxOfOrNull { it.third } ?: 0f)) {
                    mfgCandidates.add(Triple(i, match.first, match.second))
                    // Mark both indices
                }
            }
        }

        if (mfgCandidates.isNotEmpty()) {
            val best = mfgCandidates.maxByOrNull { it.third }!!
            mfgResult = best.second to best.third
            consumed.add(best.first)
            // If it was a combined match, also consume the next element
            if (best.first < elements.size - 1 &&
                elements[best.first].lineIndex == elements[best.first + 1].lineIndex
            ) {
                val combinedMatch = matchManufacturer(
                    "${elements[best.first].text} ${elements[best.first + 1].text}"
                )
                if (combinedMatch != null && combinedMatch.second == best.third) {
                    consumed.add(best.first + 1)
                }
            }
        }

        // Pass 2: MPN / ISO detection (INSERT category only)
        if (category == ToolCategory.INSERT) {
            for ((i, el) in elements.withIndex()) {
                if (i in consumed) continue
                val match = matchMpnIso(el.text, category)
                if (match != null && (mpnResult == null || match.second > mpnResult!!.second)) {
                    mpnResult = match
                    consumed.add(i)
                }
            }
        }

        // Pass 3: catalog number — first unconsumed prominent element
        // that looks like an alphanumeric code (not pure words)
        for ((i, el) in elements.withIndex()) {
            if (i in consumed) continue
            val text = el.text.trim()
            // Skip very short tokens and pure-word tokens (likely more manufacturer text)
            if (text.length < 3) continue
            // Prefer tokens with digits (catalog numbers almost always have digits)
            val hasDigit = text.any { it.isDigit() }
            val hasLetter = text.any { it.isLetter() }
            if (hasDigit || (hasLetter && text.length >= 5)) {
                val conf = el.confidence ?: 0.8f
                catResult = text to conf
                consumed.add(i)
                break
            }
        }

        // If no catalog number found with digits, take first unconsumed token
        if (catResult == null) {
            for ((i, el) in elements.withIndex()) {
                if (i in consumed) continue
                if (el.text.trim().length >= 3) {
                    catResult = el.text.trim() to (el.confidence ?: 0.5f)
                    break
                }
            }
        }

        return MatchResult(
            manufacturer = mfgResult?.first,
            manufacturerConfidence = mfgResult?.second ?: 0f,
            catalogNumber = catResult?.first,
            catalogNumberConfidence = catResult?.second ?: 0f,
            mpnIso = mpnResult?.first,
            mpnIsoConfidence = mpnResult?.second ?: 0f
        )
    }

    // ── Context-aware label ─────────────────────────────────────

    /**
     * Returns the appropriate label for the third identity field
     * based on tool category, or null if the field should be hidden.
     */
    fun thirdFieldLabel(category: ToolCategory): String? {
        return when (category) {
            ToolCategory.INSERT -> "MPN / ISO Designation"
            else -> null
        }
    }

    // ── Utilities ───────────────────────────────────────────────

    /** Simple Levenshtein distance for short strings. */
    private fun levenshtein(a: String, b: String): Int {
        val m = a.length
        val n = b.length
        val dp = Array(m + 1) { IntArray(n + 1) }
        for (i in 0..m) dp[i][0] = i
        for (j in 0..n) dp[0][j] = j
        for (i in 1..m) {
            for (j in 1..n) {
                dp[i][j] = if (a[i - 1] == b[j - 1]) {
                    dp[i - 1][j - 1]
                } else {
                    minOf(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
                }
            }
        }
        return dp[m][n]
    }
}
