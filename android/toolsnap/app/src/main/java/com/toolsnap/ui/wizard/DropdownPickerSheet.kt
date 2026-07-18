package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.config.FormField
import com.toolsnap.ui.theme.ShopFloor
import kotlinx.coroutines.launch

/**
 * Full-height bottom sheet for selecting a dropdown option.
 *
 * Shows all [formField] options plus an "Other…" entry that
 * switches to free-text input. Designed for shop-floor use
 * with large touch targets (56dp+ rows).
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun DropdownPickerSheet(
    formField: FormField,
    currentValue: String,
    onSelect: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var showCustomEntry by remember { mutableStateOf(false) }
    var customText by remember { mutableStateOf("") }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        modifier = Modifier.fillMaxSize()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp)
        ) {
            Text(
                text = formField.label,
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 12.dp)
            )

            if (showCustomEntry) {
                CustomValueEntry(
                    hint = formField.hint,
                    customText = customText,
                    onTextChange = { customText = it },
                    onBack = {
                        showCustomEntry = false
                        customText = ""
                    },
                    onConfirm = { trimmed ->
                        scope.launch {
                            sheetState.hide()
                            onSelect(trimmed)
                        }
                    }
                )
            } else {
                OptionList(
                    options = formField.dropdownOptions ?: emptyList(),
                    currentValue = currentValue,
                    onOptionSelected = { option ->
                        scope.launch {
                            sheetState.hide()
                            onSelect(option)
                        }
                    },
                    onOtherSelected = {
                        showCustomEntry = true
                    },
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun CustomValueEntry(
    hint: String,
    customText: String,
    onTextChange: (String) -> Unit,
    onBack: () -> Unit,
    onConfirm: (String) -> Unit
) {
    OutlinedTextField(
        value = customText,
        onValueChange = onTextChange,
        label = { Text("Custom Value") },
        placeholder = { Text(hint) },
        singleLine = true,
        textStyle = TextStyle(fontSize = ShopFloor.BodySize),
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = ShopFloor.TextFieldMinHeight)
    )

    Spacer(Modifier.height(16.dp))

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Button(
            onClick = onBack,
            modifier = Modifier
                .weight(1f)
                .height(ShopFloor.ButtonHeight),
            colors = ButtonDefaults.buttonColors(
                containerColor = ShopFloor.SecondaryButton,
                contentColor = ShopFloor.SecondaryButtonText
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                "BACK",
                fontSize = ShopFloor.ButtonTextSize,
                fontWeight = FontWeight.Bold
            )
        }

        Button(
            onClick = {
                val trimmed = customText.trim()
                if (trimmed.isNotBlank()) onConfirm(trimmed)
            },
            enabled = customText.trim().isNotBlank(),
            modifier = Modifier
                .weight(1f)
                .height(ShopFloor.ButtonHeight),
            colors = ButtonDefaults.buttonColors(
                containerColor = ShopFloor.SuccessButton,
                contentColor = ShopFloor.SuccessButtonText
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                "USE VALUE",
                fontSize = ShopFloor.ButtonTextSize,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun OptionList(
    options: List<String>,
    currentValue: String,
    onOptionSelected: (String) -> Unit,
    onOtherSelected: () -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        items(options.plus("Other\u2026")) { option ->
            val isOther = option == "Other\u2026"
            val isSelected = option == currentValue

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 56.dp)
                    .clickable {
                        if (isOther) onOtherSelected()
                        else onOptionSelected(option)
                    }
                    .background(
                        if (isSelected) Color(0xFFE3F2FD)
                        else Color.Transparent
                    )
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (isOther) {
                    Icon(
                        imageVector = Icons.Default.Edit,
                        contentDescription = "Custom value",
                        modifier = Modifier.size(24.dp),
                        tint = Color(0xFF1976D2)
                    )
                    Spacer(Modifier.width(12.dp))
                }

                Text(
                    text = option,
                    fontSize = 18.sp,
                    fontWeight = if (isSelected || isOther)
                        FontWeight.SemiBold else FontWeight.Normal,
                    color = if (isOther) Color(0xFF1976D2)
                        else Color.Black,
                    modifier = Modifier.weight(1f)
                )

                if (isSelected) {
                    Icon(
                        imageVector = Icons.Default.Check,
                        contentDescription = "Selected",
                        tint = Color(0xFF1976D2),
                        modifier = Modifier.size(24.dp)
                    )
                }
            }

            if (!isOther) {
                Divider(
                    color = Color(0xFFEEEEEE),
                    thickness = 1.dp
                )
            }
        }
    }
}
