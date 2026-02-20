package com.toolsnap.ui.wizard

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
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
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.toolsnap.core.model.CaptureField
import com.toolsnap.ui.theme.ShopFloor
import java.io.File

/**
 * OCR review screen — shows captured image + extracted text.
 * User can edit the text, confirm it, or retake.
 * Shop-floor sized everything.
 */
@Composable
fun OcrReviewScreen(
    field: CaptureField,
    imagePath: String,
    extractedText: String,
    isProcessing: Boolean = false,
    onConfirm: (editedText: String) -> Unit,
    onRetake: () -> Unit
) {
    var editableText by remember(extractedText) { mutableStateOf(extractedText) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        // Header
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Text(
                text = "Review: ${field.displayName}",
                fontSize = ShopFloor.TitleSize,
                fontWeight = FontWeight.Bold,
                color = ShopFloor.StepText
            )
        }

        // Instruction
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.InstructionBackground)
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 12.dp)
        ) {
            Text(
                text = if (isProcessing) "Reading text from image..."
                       else "Review and edit the extracted text below",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        Column(modifier = Modifier.padding(ShopFloor.ScreenPadding)) {
            // Processing indicator
            if (isProcessing) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(60.dp),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(40.dp))
                }
            }

            // Captured image thumbnail
            Image(
                painter = rememberAsyncImagePainter(File(imagePath)),
                contentDescription = "${field.displayName} photo",
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp),
                contentScale = ContentScale.Fit
            )

            Spacer(Modifier.height(16.dp))

            // Label
            Text(
                text = "EXTRACTED TEXT",
                fontSize = ShopFloor.LabelSize,
                fontWeight = FontWeight.Bold,
                color = ShopFloor.SecondaryButton
            )

            Spacer(Modifier.height(8.dp))

            // Editable text field
            OutlinedTextField(
                value = editableText,
                onValueChange = { editableText = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp),
                enabled = !isProcessing,
                textStyle = TextStyle(fontSize = ShopFloor.BodySize),
                placeholder = {
                    if (extractedText.isBlank()) {
                        Text(
                            "No text detected — type manually or retake",
                            fontSize = ShopFloor.BodySize
                        )
                    }
                }
            )

            Spacer(Modifier.height(24.dp))

            // Action buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
            ) {
                // RETAKE
                Button(
                    onClick = onRetake,
                    modifier = Modifier
                        .weight(1f)
                        .height(ShopFloor.ButtonHeight),
                    enabled = !isProcessing,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.DangerButton,
                        contentColor = ShopFloor.DangerButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(
                        Icons.Default.Refresh,
                        contentDescription = null,
                        modifier = Modifier.size(28.dp)
                    )
                    Spacer(Modifier.size(8.dp))
                    Text(
                        "RETAKE",
                        fontSize = ShopFloor.ButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }

                // CONFIRM
                Button(
                    onClick = { onConfirm(editableText) },
                    modifier = Modifier
                        .weight(1f)
                        .height(ShopFloor.ButtonHeight),
                    enabled = !isProcessing,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SuccessButton,
                        contentColor = ShopFloor.SuccessButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(
                        Icons.Default.Check,
                        contentDescription = null,
                        modifier = Modifier.size(28.dp)
                    )
                    Spacer(Modifier.size(8.dp))
                    Text(
                        "CONFIRM",
                        fontSize = ShopFloor.ButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
