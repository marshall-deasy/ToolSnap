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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.toolsnap.core.model.CaptureField
import com.toolsnap.ui.theme.ShopFloor
import java.io.File

/**
 * Full-screen photo review after capture.
 * Two big buttons: USE (proceed) or RETAKE (go back to camera).
 */
@Composable
fun PhotoReviewScreen(
    field: CaptureField,
    imagePath: String,
    onUse: () -> Unit,
    onRetake: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(androidx.compose.ui.graphics.Color.Black)
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
                text = "Check the photo — is it clear and in focus?",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Photo preview
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(8.dp),
            contentAlignment = Alignment.Center
        ) {
            Image(
                painter = rememberAsyncImagePainter(File(imagePath)),
                contentDescription = "${field.displayName} photo",
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Fit
            )
        }

        // Action buttons
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
        ) {
            // RETAKE
            Button(
                onClick = onRetake,
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
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

            // USE
            Button(
                onClick = onUse,
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
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
                    "USE",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
