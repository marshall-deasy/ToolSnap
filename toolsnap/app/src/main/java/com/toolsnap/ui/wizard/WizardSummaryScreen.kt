package com.toolsnap.ui.wizard

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.toolsnap.core.model.CaptureField
import com.toolsnap.core.model.CaptureSession
import com.toolsnap.core.model.FieldStatus
import com.toolsnap.ui.theme.ShopFloor

/**
 * Summary screen after all wizard fields.
 * Shows status of each field. Big buttons to save or go back.
 */
@Composable
fun WizardSummaryScreen(
    session: CaptureSession,
    onFinish: () -> Unit,
    onBackToWizard: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        // Header
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Column {
                Text(
                    text = "CAPTURE SUMMARY",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = session.toolName,
                    fontSize = ShopFloor.TitleSize,
                    color = ShopFloor.StepText.copy(alpha = 0.85f)
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "${session.capturedCount} of ${session.totalFields} fields captured",
                    fontSize = ShopFloor.BodySize,
                    color = ShopFloor.StepText.copy(alpha = 0.7f)
                )
            }
        }

        Spacer(Modifier.height(8.dp))

        // Field status list
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = ShopFloor.ScreenPadding)
        ) {
            CaptureField.wizardOrder.forEach { field ->
                val status = session.fieldStatuses[field] ?: FieldStatus.PENDING
                FieldStatusRow(field = field, status = status)
                HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
            }
        }

        // Action buttons
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (session.incompleteFields.isNotEmpty()) {
                Button(
                    onClick = onBackToWizard,
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
                        "BACK",
                        fontSize = ShopFloor.SmallButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Button(
                onClick = onFinish,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    "SAVE",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
private fun FieldStatusRow(
    field: CaptureField,
    status: FieldStatus
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        val (icon, tint) = when (status) {
            FieldStatus.CAPTURED -> Icons.Default.CheckCircle to ShopFloor.CapturedColor
            FieldStatus.SKIPPED -> Icons.Default.SkipNext to ShopFloor.SkippedColor
            FieldStatus.OCR_NEEDS_REVIEW -> Icons.Default.Warning to ShopFloor.NeedsReviewColor
            FieldStatus.PENDING -> Icons.Default.RadioButtonUnchecked to ShopFloor.PendingColor
        }

        Icon(
            icon,
            contentDescription = status.name,
            tint = tint,
            modifier = Modifier.size(32.dp)
        )

        Spacer(Modifier.width(16.dp))

        Column {
            Text(
                text = field.displayName,
                fontSize = ShopFloor.BodySize,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = when (status) {
                    FieldStatus.CAPTURED -> "Captured"
                    FieldStatus.SKIPPED -> "Skipped"
                    FieldStatus.OCR_NEEDS_REVIEW -> "Needs review"
                    FieldStatus.PENDING -> "Not captured"
                },
                fontSize = ShopFloor.LabelSize,
                color = tint
            )
        }
    }
}
