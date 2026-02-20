package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.toolsnap.core.model.CaptureField
import com.toolsnap.ui.theme.ShopFloor

/**
 * Choice screen for OCR-capable fields.
 * Three big buttons:
 *   1. ENTER MANUALLY — open structured form
 *   2. PHOTO + OCR — camera capture with text extraction
 *   3. SKIP — move to next field
 */
@Composable
fun DataEntryChoiceScreen(
    field: CaptureField,
    stepIndex: Int,
    totalSteps: Int,
    onManualEntry: () -> Unit,
    onPhotoOcr: () -> Unit,
    onSkip: () -> Unit,
    canSkip: Boolean = true,
    onBack: (() -> Unit)? = null,
    onCancel: (() -> Unit)? = null
) {
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        // Header
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Text(
                text = "STEP ${stepIndex + 1} OF $totalSteps",
                fontSize = ShopFloor.LabelSize,
                fontWeight = FontWeight.Bold,
                color = ShopFloor.StepText.copy(alpha = 0.8f)
            )
            Text(
                text = field.displayName,
                fontSize = ShopFloor.HeadlineSize,
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
                text = "How do you want to enter this data?",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Centered button group
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // ENTER MANUALLY
            Button(
                onClick = onManualEntry,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(80.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.PrimaryButton,
                    contentColor = ShopFloor.PrimaryButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Edit, null, modifier = Modifier.size(32.dp))
                Spacer(Modifier.size(12.dp))
                Column {
                    Text(
                        "ENTER MANUALLY",
                        fontSize = ShopFloor.ButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Type values into a form",
                        fontSize = ShopFloor.LabelSize,
                        color = ShopFloor.PrimaryButtonText.copy(alpha = 0.8f)
                    )
                }
            }

            Spacer(Modifier.height(20.dp))

            // PHOTO + OCR
            Button(
                onClick = onPhotoOcr,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(80.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(32.dp))
                Spacer(Modifier.size(12.dp))
                Column {
                    Text(
                        "PHOTO + OCR",
                        fontSize = ShopFloor.ButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Take a photo and extract text",
                        fontSize = ShopFloor.LabelSize,
                        color = ShopFloor.SuccessButtonText.copy(alpha = 0.8f)
                    )
                }
            }

            Spacer(Modifier.height(20.dp))

            // BACK
            if (onBack != null) {
                Button(
                    onClick = onBack,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(ShopFloor.ButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(Icons.Default.SkipNext, null, modifier = Modifier.size(28.dp))
                    Spacer(Modifier.size(8.dp))
                    Text("BACK", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                }

                Spacer(Modifier.height(12.dp))
            }

            // SKIP (only when allowed)
            if (canSkip) {
                Button(
                    onClick = onSkip,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(ShopFloor.ButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(Icons.Default.SkipNext, null, modifier = Modifier.size(28.dp))
                    Spacer(Modifier.size(8.dp))
                    Text("SKIP", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                }
            }
        }

        // CANCEL row — always visible when onCancel is provided
        if (onCancel != null) {
            Button(
                onClick = onCancel,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = ShopFloor.ScreenPadding)
                    .padding(bottom = ShopFloor.ScreenPadding)
                    .height(ShopFloor.SmallButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.DangerButton,
                    contentColor = ShopFloor.DangerButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("CANCEL ENTRY", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
            }
        }
    }
}
