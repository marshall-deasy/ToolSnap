package com.toolsnap.core.ocr

import android.content.Context
import android.graphics.Rect
import android.net.Uri
import android.util.Log
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.TextRecognizer
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import java.io.File
import kotlin.coroutines.resume
import kotlinx.coroutines.suspendCancellableCoroutine

private const val TAG = "OcrProcessor"

/**
 * On-device text recognition using Google ML Kit V2 (Play Services).
 *
 * Used for TOOL_DATA and SPEEDS_FEEDS fields to extract
 * text from photos of engravings, labels, and spec sheets.
 *
 * Also provides element-level extraction for the name and identity
 * OCR chip pickers, returning individual words/tokens with bounding
 * box area and confidence scores for prominence sorting.
 *
 * Returns raw extracted text — the user confirms or edits
 * the result on the OCR review screen before it's saved.
 */
object OcrProcessor {

    private val recognizer: TextRecognizer =
        TextRecognition.getClient(TextRecognizerOptions.Builder().build())

    /**
     * A single recognized text element (word/token) with its
     * bounding box area and recognition confidence.
     *
     * [text]       — the recognized word or token
     * [area]       — bounding box area in pixels (width × height), used to sort
     *               by visual prominence on the label
     * [lineIndex]  — which line this element belongs to (for grouping)
     * [confidence] — ML Kit recognition confidence (0.0–1.0), null if unavailable.
     *               Used for confidence-weighted sorting and UI quality indicators.
     */
    data class OcrElement(
        val text: String,
        val area: Int,
        val lineIndex: Int,
        val confidence: Float? = null
    )

    /**
     * Result of an OCR operation.
     *
     * [rawText]   — the full extracted text, newlines preserved
     * [blocks]    — individual text blocks with their content
     * [elements]  — individual words/tokens sorted by prominence (largest and
     *              highest-confidence first), with junk filtered out.
     *              Used by the name and identity OCR chip pickers.
     * [isEmpty]   — true if no text was detected
     * [error]     — human-readable error message if OCR failed, null on success
     */
    data class OcrResult(
        val rawText: String,
        val blocks: List<TextBlock>,
        val elements: List<OcrElement> = emptyList(),
        val isEmpty: Boolean = rawText.isBlank(),
        val error: String? = null
    ) {
        data class TextBlock(
            val text: String,
            val lines: List<String>
        )

        /** True if OCR ran but couldn't extract any text. */
        val isEmptyResult: Boolean get() = error == null && isEmpty

        /** True if OCR failed due to an error. */
        val isFailed: Boolean get() = error != null
    }

    // ── Junk filtering ─────────────────────────────────────────

    /**
     * Junk patterns to filter from chip picker results.
     * Trademarks, copyright symbols, common boilerplate.
     */
    private val JUNK_PATTERNS = listOf(
        Regex("^[®™©]+$"),                        // standalone symbols
        Regex("^\\W+$"),                           // only punctuation/symbols
        Regex("^(?i)made\\s+in$"),                 // "Made in"
        Regex("^(?i)(pat|patent|www|http|com)$"),  // web/patent junk
    )

    /** Minimum length for a chip token (skip single chars unless alphanumeric). */
    private const val MIN_TOKEN_LENGTH = 2

    /** Confidence threshold — elements below this are still included but ranked lower. */
    private const val LOW_CONFIDENCE_THRESHOLD = 0.5f

    /**
     * Check if a token should be excluded from the chip picker.
     */
    private fun isJunk(text: String): Boolean {
        val trimmed = text.trim()
        if (trimmed.length < MIN_TOKEN_LENGTH && !trimmed[0].isLetterOrDigit()) return true
        return JUNK_PATTERNS.any { it.matches(trimmed) }
    }

    // ── Prominence sorting ─────────────────────────────────────

    /**
     * Compute a prominence score combining bounding box area with
     * recognition confidence. Larger, higher-confidence text ranks first.
     *
     * If confidence is unavailable, falls back to area-only sorting.
     */
    private fun prominenceScore(element: OcrElement): Double {
        val conf = element.confidence ?: 1.0f
        return element.area.toDouble() * conf.toDouble()
    }

    // ── Main extraction ────────────────────────────────────────

    /**
     * Extract text from an image file using ML Kit V2 Text Recognition.
     *
     * Suspending function — call from a coroutine scope.
     * Always returns an [OcrResult]; never throws.
     * Supports cancellation via [suspendCancellableCoroutine].
     *
     * If OCR fails, the result will have [OcrResult.error] set to a
     * human-readable message the UI can display.
     *
     * The result includes element-level data with bounding box areas
     * and confidence scores for prominence sorting in the chip picker UI.
     *
     * @param context    Android context for URI resolution
     * @param imageFile  the captured photo to process
     */
    suspend fun extractText(context: Context, imageFile: File): OcrResult {
        // Pre-flight checks
        if (!imageFile.exists()) {
            return OcrResult(
                rawText = "", blocks = emptyList(),
                error = "Image file not found"
            )
        }

        if (imageFile.length() == 0L) {
            return OcrResult(
                rawText = "", blocks = emptyList(),
                error = "Image file is empty"
            )
        }

        return suspendCancellableCoroutine { continuation ->
            try {
                val image = InputImage.fromFilePath(context, Uri.fromFile(imageFile))
                val task = recognizer.process(image)

                task.addOnSuccessListener { visionText ->
                        if (!continuation.isActive) return@addOnSuccessListener

                        val blocks = visionText.textBlocks.map { block ->
                            OcrResult.TextBlock(
                                text = block.text,
                                lines = block.lines.map { it.text }
                            )
                        }

                        val rawText = visionText.textBlocks
                            .joinToString("\n") { it.text }

                        // Extract element-level data with bounding boxes + confidence
                        val elements = buildElements(visionText)

                        continuation.resume(
                            OcrResult(
                                rawText = rawText,
                                blocks = blocks,
                                elements = elements
                            )
                        )
                    }
                    .addOnFailureListener { e ->
                        if (!continuation.isActive) return@addOnFailureListener

                        Log.e(TAG, "ML Kit V2 recognition failed: ${e.message}", e)

                        val errorMsg = when {
                            e.message?.contains("model", ignoreCase = true) == true ->
                                "OCR model is downloading — try again in a moment"
                            e.message?.contains("memory", ignoreCase = true) == true ->
                                "Image too large for text recognition"
                            e.message?.contains("unavailable", ignoreCase = true) == true ->
                                "Text recognition unavailable — check Google Play Services"
                            else ->
                                "Text recognition failed — try retaking the photo"
                        }

                        continuation.resume(
                            OcrResult(
                                rawText = "", blocks = emptyList(),
                                error = errorMsg
                            )
                        )
                    }
            } catch (e: Exception) {
                Log.e(TAG, "OCR setup error: ${e.message}", e)
                if (continuation.isActive) {
                    continuation.resume(
                        OcrResult(
                            rawText = "", blocks = emptyList(),
                            error = "Could not start text recognition: ${e.message}"
                        )
                    )
                }
            }
        }
    }

    /**
     * Walk the V2 Text result hierarchy, extract every element,
     * filter junk, sort by confidence-weighted prominence, and deduplicate.
     */
    private fun buildElements(
        visionText: com.google.mlkit.vision.text.Text
    ): List<OcrElement> {
        val raw = mutableListOf<OcrElement>()
        var lineIndex = 0

        for (block in visionText.textBlocks) {
            for (line in block.lines) {
                for (element in line.elements) {
                    val bbox = element.boundingBox
                    val area = if (bbox != null) {
                        bbox.width() * bbox.height()
                    } else {
                        0
                    }
                    val text = element.text.trim()
                    if (text.isNotBlank() && !isJunk(text)) {
                        raw.add(
                            OcrElement(
                                text = text,
                                area = area,
                                lineIndex = lineIndex,
                                confidence = element.confidence
                            )
                        )
                    }
                }
                lineIndex++
            }
        }

        // Sort by confidence-weighted prominence — best chips first
        val sorted = raw.sortedByDescending { prominenceScore(it) }

        // Deduplicate (same text appearing multiple times, keep highest-ranked)
        val seen = mutableSetOf<String>()
        return sorted.filter { el ->
            val key = el.text.lowercase()
            if (key in seen) false
            else { seen.add(key); true }
        }
    }
}
