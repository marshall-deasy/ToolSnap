package com.toolsnap.ui.wizard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.toolsnap.config.CaptureConfig
import com.toolsnap.ui.theme.ShopFloor

/**
 * First screen in the wizard — collects the tool / assembly name.
 * Big text, big input, big buttons.
 *
 * Supports two entry modes:
 *   - Type manually in the text field
 *   - SCAN LABEL → camera → OCR chip picker → auto-populate
 *
 * NEXT → proceeds to category picker.
 * SCAN LABEL → launches camera for OCR name extraction.
 * CANCEL → returns to home screen (no session created yet).
 */
@Composable
fun NameEntryScreen(
    onNameConfirmed: (String) -> Unit,
    onScanLabel: (() -> Unit)? = null,
    onCancel: (() -> Unit)? = null,
    initialName: String = ""
) {
    var toolName by remember { mutableStateOf(initialName) }
    var showError by remember { mutableStateOf(false) }

    val trimmed = toolName.trim()
    val sanitized = if (trimmed.isNotBlank()) CaptureConfig.sanitizeToolName(trimmed) else ""

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(ShopFloor.ScreenPadding),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "New Tool Capture",
            fontSize = ShopFloor.HeadlineSize,
            fontWeight = FontWeight.Bold
        )

        Spacer(Modifier.height(8.dp))

        Text(
            text = "Enter the tool name or scan a label",
            fontSize = ShopFloor.BodySize,
            color = ShopFloor.SecondaryButton
        )

        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = toolName,
            onValueChange = {
                toolName = it
                showError = false
            },
            label = { Text("Tool Name", fontSize = ShopFloor.LabelSize) },
            placeholder = { Text("e.g. Boring Bar A123", fontSize = ShopFloor.BodySize) },
            singleLine = true,
            isError = showError,
            textStyle = TextStyle(fontSize = ShopFloor.TitleSize),
            supportingText = when {
                showError -> {{ Text("Tool name is required", fontSize = ShopFloor.LabelSize) }}
                sanitized.isNotBlank() -> {{ Text("Folder: $sanitized", fontSize = ShopFloor.LabelSize) }}
                else -> null
            },
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = ShopFloor.TextFieldMinHeight)
        )

        Spacer(Modifier.height(24.dp))

        // SCAN LABEL button
        if (onScanLabel != null) {
            Button(
                onClick = onScanLabel,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF00695C),
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(
                    Icons.Default.CameraAlt,
                    contentDescription = null,
                    modifier = Modifier.size(28.dp)
                )
                Spacer(Modifier.size(8.dp))
                Text(
                    "SCAN LABEL",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(Modifier.height(16.dp))
        }

        // NEXT button
        Button(
            onClick = {
                if (trimmed.isBlank()) {
                    showError = true
                } else {
                    onNameConfirmed(trimmed)
                }
            },
            enabled = trimmed.isNotBlank(),
            modifier = Modifier
                .fillMaxWidth()
                .height(ShopFloor.ButtonHeight),
            colors = ButtonDefaults.buttonColors(
                containerColor = ShopFloor.PrimaryButton,
                contentColor = ShopFloor.PrimaryButtonText
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                "NEXT",
                fontSize = ShopFloor.ButtonTextSize,
                fontWeight = FontWeight.Bold
            )
        }

        // CANCEL button
        if (onCancel != null) {
            Spacer(Modifier.height(16.dp))

            Button(
                onClick = onCancel,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(ShopFloor.SmallButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SecondaryButton,
                    contentColor = ShopFloor.SecondaryButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    "CANCEL",
                    fontSize = ShopFloor.SmallButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
