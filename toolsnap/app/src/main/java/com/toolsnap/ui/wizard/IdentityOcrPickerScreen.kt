package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.ocr.OcrFieldMatcher
import com.toolsnap.core.ocr.OcrProcessor
import com.toolsnap.ui.theme.ShopFloor

/** Confidence threshold — chips below this get a visual "uncertain" cue. */
private const val LOW_CONFIDENCE = 0.5f

/**
 * OCR chip picker for tool identity fields.
 *
 * Shows recognized text elements as tappable chips sorted by
 * confidence-weighted prominence (largest + highest-confidence first).
 *
 * User taps chips to populate EDP, manufacturer, and (for inserts)
 * MPN/ISO fields. All fields are editable for manual correction.
 *
 * Auto-populates fields from [OcrFieldMatcher.MatchResult] when
 * available — user sees pre-filled suggestions they can accept or
 * override by tapping different chips.
 *
 * Low-confidence chips show an amber border and "?" badge so the
 * machinist knows to double-check them.
 *
 * Context-aware: the 3rd field (MPN/ISO) only appears for INSERT
 * category tools.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun IdentityOcrPickerScreen(
    imagePath: String,
    elements: List<OcrProcessor.OcrElement>,
    isProcessing: Boolean,
    ocrError: String?,
    category: ToolCategory = ToolCategory.OTHER,
    matchResult: OcrFieldMatcher.MatchResult? = null,
    initialEdp: String = "",
    initialManufacturer: String = "",
    initialMpnIso: String = "",
    onConfirm: (edp: String, manufacturer: String, mpnIso: String) -> Unit,
    onRetake: () -> Unit,
    onCancel: () -> Unit
) {
    val showMpnIso = OcrFieldMatcher.thirdFieldLabel(category) != null
    val mpnIsoLabel = OcrFieldMatcher.thirdFieldLabel(category) ?: ""

    var edp by remember { mutableStateOf(initialEdp) }
    var manufacturer by remember { mutableStateOf(initialManufacturer) }
    var mpnIso by remember { mutableStateOf(initialMpnIso) }
    val selectedIndices = remember { mutableStateListOf<Int>() }

    // Active field: "edp", "manufacturer", or "mpnIso"
    var activeField by remember { mutableStateOf("edp") }

    // Track which field each chip was assigned to for clean deselect
    val chipAssignment = remember { mutableMapOf<Int, String>() }

    // Auto-populate from matchResult (once, when elements arrive)
    var autoPopulated by remember { mutableStateOf(false) }
    LaunchedEffect(matchResult, elements) {
        if (matchResult != null && elements.isNotEmpty() && !autoPopulated) {
            autoPopulated = true
            if (edp.isBlank() && matchResult.catalogNumber != null) {
                edp = matchResult.catalogNumber
            }
            if (manufacturer.isBlank() && matchResult.manufacturer != null) {
                manufacturer = matchResult.manufacturer
            }
            if (showMpnIso && mpnIso.isBlank() && matchResult.mpnIso != null) {
                mpnIso = matchResult.mpnIso
            }
            // Auto-advance active field to first empty required field
            activeField = when {
                edp.isBlank() -> "edp"
                manufacturer.isBlank() -> "manufacturer"
                showMpnIso && mpnIso.isBlank() -> "mpnIso"
                else -> "edp"
            }
        }
    }

    fun onChipTap(index: Int, text: String) {
        if (selectedIndices.contains(index)) {
            selectedIndices.remove(index)
            when (chipAssignment.remove(index)) {
                "edp" -> edp = edp.replace(text, "").trim().replace(Regex("\\s+"), " ")
                "manufacturer" -> manufacturer = manufacturer.replace(text, "").trim().replace(Regex("\\s+"), " ")
                "mpnIso" -> mpnIso = mpnIso.replace(text, "").trim().replace(Regex("\\s+"), " ")
            }
        } else {
            selectedIndices.add(index)
            chipAssignment[index] = activeField
            when (activeField) {
                "edp" -> {
                    edp = if (edp.isBlank()) text else "$edp $text"
                    // Auto-advance to next empty field
                    if (manufacturer.isBlank()) activeField = "manufacturer"
                    else if (showMpnIso && mpnIso.isBlank()) activeField = "mpnIso"
                }
                "manufacturer" -> {
                    manufacturer = if (manufacturer.isBlank()) text else "$manufacturer $text"
                    if (showMpnIso && mpnIso.isBlank()) activeField = "mpnIso"
                }
                "mpnIso" -> {
                    mpnIso = if (mpnIso.isBlank()) text else "$mpnIso $text"
                }
            }
        }
    }

    // Build instruction text based on active field
    val instructionText = when (activeField) {
        "edp" -> "Tapping chips fills EDP field — tap another field to switch"
        "manufacturer" -> "Tapping chips fills MANUFACTURER field — tap another field to switch"
        "mpnIso" -> "Tapping chips fills $mpnIsoLabel field — tap another field to switch"
        else -> ""
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Header
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Column {
                Text("SCAN RESULTS", fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold, color = ShopFloor.StepText)
                Text("Tap chips to fill fields" +
                        if (matchResult != null && !isProcessing) " · Auto-filled from scan" else "",
                    fontSize = ShopFloor.LabelSize, color = ShopFloor.StepText.copy(alpha = 0.7f))
            }
        }

        // Instruction bar
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.InstructionBackground)
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 10.dp)
        ) {
            Text(
                text = instructionText,
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Scrollable content
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OcrTargetField(
                label = "EDP / Catalog Number", value = edp,
                onValueChange = { edp = it }, isActive = activeField == "edp",
                onActivate = { activeField = "edp" }, required = true
            )
            OcrTargetField(
                label = "Manufacturer", value = manufacturer,
                onValueChange = { manufacturer = it }, isActive = activeField == "manufacturer",
                onActivate = { activeField = "manufacturer" }, required = true
            )
            if (showMpnIso) {
                OcrTargetField(
                    label = mpnIsoLabel, value = mpnIso,
                    onValueChange = { mpnIso = it }, isActive = activeField == "mpnIso",
                    onActivate = { activeField = "mpnIso" }, required = false
                )
            }

            Spacer(Modifier.height(8.dp))

            // OCR chips
            when {
                isProcessing -> {
                    Box(Modifier.fillMaxWidth().height(120.dp), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(modifier = Modifier.size(48.dp))
                            Spacer(Modifier.height(12.dp))
                            Text("Reading label…", fontSize = ShopFloor.BodySize, color = Color(0xFF666666))
                        }
                    }
                }
                ocrError != null -> {
                    Text("OCR failed: $ocrError", fontSize = ShopFloor.BodySize,
                        color = Color(0xFFB71C1C), modifier = Modifier.padding(vertical = 16.dp))
                }
                elements.isEmpty() && !isProcessing -> {
                    Text("No text detected — try retaking with better lighting",
                        fontSize = ShopFloor.BodySize, color = Color(0xFF666666),
                        modifier = Modifier.padding(vertical = 16.dp))
                }
                else -> {
                    Text("RECOGNIZED TEXT", fontSize = ShopFloor.LabelSize,
                        fontWeight = FontWeight.Bold, color = Color(0xFF444444))
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        elements.forEachIndexed { index, element ->
                            IdentityOcrChip(
                                text = element.text,
                                isSelected = selectedIndices.contains(index),
                                isLowConfidence = element.confidence != null
                                        && element.confidence < LOW_CONFIDENCE,
                                onClick = { onChipTap(index, element.text) }
                            )
                        }
                    }
                }
            }
        }

        // Action buttons
        Row(
            modifier = Modifier.fillMaxWidth().padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
        ) {
            Button(
                onClick = onRetake,
                modifier = Modifier.weight(1f).height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF00838F), contentColor = Color.White),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.size(8.dp))
                Text("RETAKE", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
            }

            val canUse = edp.isNotBlank() && manufacturer.isNotBlank()
            Button(
                onClick = { onConfirm(edp.trim(), manufacturer.trim(), mpnIso.trim()) },
                enabled = canUse,
                modifier = Modifier.weight(1f).height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (canUse) ShopFloor.SuccessButton else Color(0xFF888888),
                    contentColor = if (canUse) ShopFloor.SuccessButtonText else Color.White),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Check, null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.size(8.dp))
                Text("USE THIS", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
            }
        }

        // Cancel
        Button(
            onClick = onCancel,
            modifier = Modifier.fillMaxWidth()
                .padding(horizontal = ShopFloor.ScreenPadding)
                .padding(bottom = ShopFloor.ScreenPadding)
                .height(ShopFloor.SmallButtonHeight),
            colors = ButtonDefaults.buttonColors(
                containerColor = ShopFloor.DangerButton, contentColor = ShopFloor.DangerButtonText),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text("CANCEL", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
        }
    }
}

/**
 * A single OCR text chip — tappable to toggle selection.
 * Low-confidence chips show an amber border and "?" badge
 * so the machinist knows to double-check them.
 */
@Composable
private fun IdentityOcrChip(
    text: String,
    isSelected: Boolean,
    isLowConfidence: Boolean,
    onClick: () -> Unit
) {
    val bgColor = when {
        isSelected -> Color(0xFF00838F)
        isLowConfidence -> Color(0xFFFFF8E1)
        else -> Color(0xFFF5F5F5)
    }
    val textColor = when {
        isSelected -> Color.White
        isLowConfidence -> Color(0xFF6D4C00)
        else -> Color(0xFF333333)
    }
    val borderColor = when {
        isSelected -> Color(0xFF00838F)
        isLowConfidence -> Color(0xFFFFB300)
        else -> Color(0xFFCCCCCC)
    }

    Box(
        modifier = Modifier
            .background(bgColor, RoundedCornerShape(20.dp))
            .border(
                width = if (isLowConfidence && !isSelected) 2.dp else 1.dp,
                color = borderColor, shape = RoundedCornerShape(20.dp))
            .clickable { onClick() }
            .padding(horizontal = 14.dp, vertical = 8.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(text, fontSize = ShopFloor.BodySize,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                color = textColor)
            if (isLowConfidence && !isSelected) {
                Spacer(Modifier.size(4.dp))
                Text("?", fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Bold, color = Color(0xFFFF8F00))
            }
        }
    }
}
