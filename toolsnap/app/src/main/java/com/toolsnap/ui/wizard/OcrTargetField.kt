package com.toolsnap.ui.wizard

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.toolsnap.ui.theme.ShopFloor

/**
 * A target field card that highlights when active (receiving chip taps).
 *
 * The entire card is tappable to switch which field receives chips.
 * Includes inline EDIT mode for manual text correction and a CLEAR button.
 *
 * Used by IdentityOcrPickerScreen for EDP and Manufacturer fields.
 */
@Composable
fun OcrTargetField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    isActive: Boolean,
    onActivate: () -> Unit,
    required: Boolean = false
) {
    var isEditing by remember { mutableStateOf(false) }

    val borderColor = when {
        isActive -> Color(0xFF00838F)
        value.isNotBlank() -> Color(0xFF1976D2)
        required -> Color(0xFFE57373)
        else -> Color(0xFFBBBBBB)
    }
    val bgColor = when {
        isActive -> Color(0xFFE0F7FA)
        value.isNotBlank() -> Color(0xFFE3F2FD)
        else -> Color.White
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onActivate() },
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(
            width = if (isActive) 3.dp else 1.dp,
            color = borderColor
        ),
        colors = CardDefaults.cardColors(containerColor = bgColor)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
        ) {
            // Label row with status indicator
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = buildAnnotatedString {
                        append(label)
                        if (required) {
                            withStyle(SpanStyle(color = Color(0xFFD32F2F), fontWeight = FontWeight.Bold)) {
                                append(" *")
                            }
                        }
                    },
                    fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Bold,
                    color = if (isActive) Color(0xFF00838F) else Color(0xFF444444)
                )
                Spacer(Modifier.weight(1f))
                if (isActive) {
                    Box(
                        modifier = Modifier
                            .background(Color(0xFF00838F), RoundedCornerShape(6.dp))
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text("◀ CHIPS GO HERE", fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.Bold, color = Color.White)
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .background(Color(0xFFE0E0E0), RoundedCornerShape(6.dp))
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text("TAP TO SELECT", fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.Medium, color = Color(0xFF666666))
                    }
                }
            }

            Spacer(Modifier.height(8.dp))

            if (isEditing) {
                OutlinedTextField(
                    value = value,
                    onValueChange = onValueChange,
                    textStyle = TextStyle(fontSize = ShopFloor.BodySize),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(4.dp))
                Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
                    Box(
                        modifier = Modifier
                            .background(Color(0xFF00838F), RoundedCornerShape(6.dp))
                            .clickable { isEditing = false }
                            .padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text("DONE", fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            } else {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = value.ifBlank { "Tap chips above or EDIT to type" },
                        fontSize = ShopFloor.BodySize,
                        fontWeight = if (value.isNotBlank()) FontWeight.Medium else FontWeight.Normal,
                        color = if (value.isNotBlank()) Color.Black else Color(0xFF999999),
                        modifier = Modifier.weight(1f)
                    )
                    if (value.isNotBlank()) {
                        Spacer(Modifier.size(8.dp))
                        Box(
                            modifier = Modifier
                                .background(Color(0xFFE0E0E0), RoundedCornerShape(6.dp))
                                .clickable { onValueChange("") }
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text("✕", fontSize = ShopFloor.LabelSize,
                                fontWeight = FontWeight.Bold, color = Color(0xFF666666))
                        }
                    }
                    Spacer(Modifier.size(8.dp))
                    Box(
                        modifier = Modifier
                            .background(Color(0xFF1976D2), RoundedCornerShape(6.dp))
                            .clickable { isEditing = true }
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text("EDIT", fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            }
        }
    }
}
