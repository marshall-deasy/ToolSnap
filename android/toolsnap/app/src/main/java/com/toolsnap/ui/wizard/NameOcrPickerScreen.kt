package com.toolsnap.ui.wizard

import androidx.compose.foundation.Image
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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.toolsnap.core.ocr.OcrProcessor
import com.toolsnap.ui.theme.ShopFloor
import java.io.File

/** Confidence threshold — chips below this get a visual "uncertain" cue. */
private const val LOW_CONFIDENCE = 0.5f

/**
 * OCR chip picker for building a tool name from recognized text.
 *
 * Displays the captured label image, an editable name field, and a
 * FlowRow of tappable chips sorted by confidence-weighted prominence.
 *
 * Low-confidence chips show an amber border and "?" badge so the
 * machinist knows to double-check them.
 *
 * Tapping a chip appends its text to the name field. The field is
 * fully editable so the user can rearrange, delete, or type manually.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun NameOcrPickerScreen(
    imagePath: String,
    elements: List<OcrProcessor.OcrElement>,
    isProcessing: Boolean,
    ocrError: String?,
    onConfirm: (String) -> Unit,
    onRetake: () -> Unit,
    onCancel: () -> Unit
) {
    var nameText by remember { mutableStateOf("") }
    val selectedTokens = remember { mutableStateListOf<String>() }

    Column(modifier = Modifier.fillMaxSize()) {
        // Header
        Box(
            modifier = Modifier.fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Column {
                Text("SCAN LABEL", fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold, color = ShopFloor.StepText)
                Spacer(Modifier.height(4.dp))
                Text("Tap words to build the tool name",
                    fontSize = ShopFloor.BodySize, color = ShopFloor.StepText.copy(alpha = 0.8f))
            }
        }

        // Instruction bar
        Box(
            modifier = Modifier.fillMaxWidth()
                .background(ShopFloor.InstructionBackground)
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 10.dp)
        ) {
            Text(
                "Biggest text shown first · Tap chips in order · Edit the name field directly if needed",
                fontSize = ShopFloor.LabelSize, color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center, fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Scrollable content
        Column(
            modifier = Modifier.weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(ShopFloor.ScreenPadding)
        ) {
            // Editable name field
            OutlinedTextField(
                value = nameText,
                onValueChange = { nameText = it },
                label = { Text("Tool Name", fontSize = ShopFloor.LabelSize) },
                placeholder = { Text("Tap chips below or type here", fontSize = ShopFloor.BodySize) },
                singleLine = true,
                textStyle = TextStyle(fontSize = ShopFloor.TitleSize, fontWeight = FontWeight.SemiBold),
                trailingIcon = {
                    if (nameText.isNotBlank()) {
                        IconButton(onClick = { nameText = ""; selectedTokens.clear() }) {
                            Icon(Icons.Default.Clear, "Clear", modifier = Modifier.size(28.dp))
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth().heightIn(min = ShopFloor.TextFieldMinHeight)
            )

            Spacer(Modifier.height(16.dp))

            // Captured image thumbnail
            if (imagePath.isNotBlank()) {
                Image(
                    painter = rememberAsyncImagePainter(model = File(imagePath)),
                    contentDescription = "Captured label",
                    modifier = Modifier.fillMaxWidth().heightIn(max = 200.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .border(1.dp, Color.Gray.copy(alpha = 0.3f), RoundedCornerShape(8.dp)),
                    contentScale = ContentScale.Fit
                )
                Spacer(Modifier.height(16.dp))
            }

            // OCR status
            when {
                isProcessing -> {
                    Box(Modifier.fillMaxWidth().padding(vertical = 32.dp),
                        contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(Modifier.size(48.dp), color = ShopFloor.PrimaryButton)
                            Spacer(Modifier.height(12.dp))
                            Text("Reading label text…", fontSize = ShopFloor.BodySize, color = Color.Gray)
                        }
                    }
                }
                ocrError != null -> {
                    Box(Modifier.fillMaxWidth()
                        .background(Color(0xFFFFEBEE), RoundedCornerShape(8.dp)).padding(16.dp),
                        contentAlignment = Alignment.Center) {
                        Text(ocrError, fontSize = ShopFloor.BodySize,
                            color = ShopFloor.DangerButton, textAlign = TextAlign.Center)
                    }
                }
                elements.isEmpty() -> {
                    Box(Modifier.fillMaxWidth()
                        .background(Color(0xFFFFF3E0), RoundedCornerShape(8.dp)).padding(16.dp),
                        contentAlignment = Alignment.Center) {
                        Text("No text detected — try retaking with better lighting or a closer shot",
                            fontSize = ShopFloor.BodySize, color = Color(0xFFE65100),
                            textAlign = TextAlign.Center)
                    }
                }
                else -> {
                    Text("DETECTED TEXT", fontSize = ShopFloor.LabelSize,
                        fontWeight = FontWeight.Bold, color = Color.Gray)
                    Spacer(Modifier.height(8.dp))
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        elements.forEach { element ->
                            val isSelected = element.text in selectedTokens
                            NameOcrChip(
                                text = element.text,
                                isSelected = isSelected,
                                isLowConfidence = element.confidence != null
                                        && element.confidence < LOW_CONFIDENCE,
                                onClick = {
                                    if (isSelected) {
                                        selectedTokens.remove(element.text)
                                        nameText = selectedTokens.joinToString(" ")
                                    } else {
                                        selectedTokens.add(element.text)
                                        nameText = if (nameText.isBlank()) element.text
                                            else "$nameText ${element.text}"
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }

        // Action buttons
        Column(
            modifier = Modifier.fillMaxWidth().padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Button(
                onClick = { onConfirm(nameText.trim()) },
                enabled = nameText.trim().isNotBlank() && !isProcessing,
                modifier = Modifier.fillMaxWidth().height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("USE THIS NAME", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
            ) {
                Button(
                    onClick = onRetake,
                    modifier = Modifier.weight(1f).height(ShopFloor.SmallButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("RETAKE", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
                }
                Button(
                    onClick = onCancel,
                    modifier = Modifier.weight(1f).height(ShopFloor.SmallButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.DangerButton,
                        contentColor = ShopFloor.DangerButtonText),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("CANCEL", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

/**
 * Individual tappable chip for an OCR-detected word.
 * Highlights when selected. Low-confidence chips show an
 * amber border and "?" badge.
 */
@Composable
private fun NameOcrChip(
    text: String,
    isSelected: Boolean,
    isLowConfidence: Boolean,
    onClick: () -> Unit
) {
    val bgColor = when {
        isSelected -> ShopFloor.PrimaryButton
        isLowConfidence -> Color(0xFFFFF8E1)
        else -> Color(0xFFE0E0E0)
    }
    val textColor = when {
        isSelected -> Color.White
        isLowConfidence -> Color(0xFF6D4C00)
        else -> Color(0xFF212121)
    }
    val borderColor = when {
        isSelected -> ShopFloor.PrimaryButton
        isLowConfidence -> Color(0xFFFFB300)
        else -> Color(0xFFBDBDBD)
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(bgColor)
            .border(
                width = if (isLowConfidence && !isSelected) 2.dp else 1.dp,
                color = borderColor, shape = RoundedCornerShape(20.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 10.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(text, fontSize = ShopFloor.BodySize,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                color = textColor)
            if (isLowConfidence && !isSelected) {
                Spacer(Modifier.size(4.dp))
                Text("?", fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Bold, color = Color(0xFFFF8F00))
            }
        }
    }
}
