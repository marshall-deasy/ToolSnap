package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.config.FormField
import com.toolsnap.config.InputType
import com.toolsnap.ui.theme.ShopFloor

/**
 * Category-aware manual entry form for tool attributes.
 *
 * Renders a list of [FormField] definitions as labeled inputs.
 * DROPDOWN fields open [DropdownPickerSheet] (separate file).
 * Required fields show a red asterisk; saving with missing required
 * fields triggers a confirmation dialog listing what's incomplete.
 */
@Composable
fun ManualEntryScreen(
    formFields: List<FormField>,
    title: String,
    existingValues: Map<String, String> = emptyMap(),
    onSave: (Map<String, String>) -> Unit,
    onCancel: () -> Unit
) {
    val values = remember {
        mutableStateMapOf<String, String>().apply {
            existingValues.forEach { (k, v) -> put(k, v) }
        }
    }

    var activeDropdown by remember { mutableStateOf<FormField?>(null) }
    var showIncompleteDialog by remember { mutableStateOf(false) }
    var missingFields by remember { mutableStateOf<List<String>>(emptyList()) }

    fun doSave() {
        onSave(values.filter { it.value.isNotBlank() })
    }

    fun attemptSave() {
        val missing = formFields
            .filter { it.required }
            .filter { values[it.key].isNullOrBlank() }
            .map { it.label }

        if (missing.isEmpty()) {
            doSave()
        } else {
            missingFields = missing
            showIncompleteDialog = true
        }
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
                Text(
                    text = title.uppercase(),
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Tap dropdowns to select \u2022 type in text fields",
                    fontSize = ShopFloor.LabelSize,
                    color = ShopFloor.StepText.copy(alpha = 0.7f)
                )
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
                text = "Fill in what you know \u2014 * fields are recommended",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Scrollable form fields
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            formFields.forEach { formField ->
                if (formField.inputType == InputType.DROPDOWN) {
                    DropdownFieldInput(
                        formField = formField,
                        value = values[formField.key] ?: "",
                        onClick = { activeDropdown = formField }
                    )
                } else {
                    TextFormFieldInput(
                        formField = formField,
                        value = values[formField.key] ?: "",
                        onValueChange = { values[formField.key] = it }
                    )
                }
            }

            Spacer(Modifier.height(16.dp))
        }

        // Action buttons
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
        ) {
            Button(
                onClick = onCancel,
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SecondaryButton,
                    contentColor = ShopFloor.SecondaryButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Close, null, modifier = Modifier.size(28.dp))
                Spacer(Modifier.size(8.dp))
                Text(
                    "CANCEL",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }

            Button(
                onClick = { attemptSave() },
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Check, null, modifier = Modifier.size(28.dp))
                Spacer(Modifier.size(8.dp))
                Text(
                    "SAVE",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }

    // Bottom sheet dropdown picker
    activeDropdown?.let { dropdownField ->
        DropdownPickerSheet(
            formField = dropdownField,
            currentValue = values[dropdownField.key] ?: "",
            onSelect = { selected ->
                values[dropdownField.key] = selected
                activeDropdown = null
            },
            onDismiss = { activeDropdown = null }
        )
    }

    // Incomplete required fields dialog
    if (showIncompleteDialog) {
        IncompleteFieldsDialog(
            missingLabels = missingFields,
            onSaveAnyway = {
                showIncompleteDialog = false
                doSave()
            },
            onGoBack = { showIncompleteDialog = false }
        )
    }
}

// ======================================================================
// Incomplete fields confirmation dialog
// ======================================================================

@Composable
private fun IncompleteFieldsDialog(
    missingLabels: List<String>,
    onSaveAnyway: () -> Unit,
    onGoBack: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onGoBack,
        title = {
            Text(
                "INCOMPLETE DATA",
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp
            )
        },
        text = {
            Column {
                Text(
                    "These recommended fields are empty:",
                    fontSize = 16.sp,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                missingLabels.forEach { label ->
                    Text(
                        text = "\u2022  $label",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFFB71C1C),
                        modifier = Modifier.padding(vertical = 2.dp)
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onSaveAnyway) {
                Text(
                    "SAVE ANYWAY",
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = ShopFloor.SuccessButton
                )
            }
        },
        dismissButton = {
            TextButton(onClick = onGoBack) {
                Text(
                    "GO BACK",
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = ShopFloor.PrimaryButton
                )
            }
        }
    )
}

// ======================================================================
// Required-aware field label
// ======================================================================

@Composable
private fun FieldLabel(label: String, required: Boolean) {
    if (required) {
        Text(
            text = buildAnnotatedString {
                append(label)
                withStyle(SpanStyle(
                    color = Color(0xFFD32F2F),
                    fontWeight = FontWeight.Bold
                )) {
                    append(" *")
                }
            },
            fontSize = ShopFloor.LabelSize,
            fontWeight = FontWeight.SemiBold,
            color = Color(0xFF444444),
            modifier = Modifier.padding(bottom = 6.dp)
        )
    } else {
        Text(
            text = label,
            fontSize = ShopFloor.LabelSize,
            fontWeight = FontWeight.SemiBold,
            color = Color(0xFF444444),
            modifier = Modifier.padding(bottom = 6.dp)
        )
    }
}

// ======================================================================
// Dropdown field — tappable display row that opens the picker sheet
// ======================================================================

@Composable
private fun DropdownFieldInput(
    formField: FormField,
    value: String,
    onClick: () -> Unit
) {
    val isEmpty = value.isBlank()
    val borderColor = when {
        !isEmpty -> Color(0xFF1976D2)
        formField.required -> Color(0xFFE57373)
        else -> Color(0xFFBBBBBB)
    }

    Column(modifier = Modifier.fillMaxWidth()) {
        FieldLabel(formField.label, formField.required)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 60.dp)
                .border(
                    width = if (!isEmpty || formField.required) 2.dp else 1.dp,
                    color = borderColor,
                    shape = RoundedCornerShape(8.dp)
                )
                .background(
                    color = if (!isEmpty) Color(0xFFE3F2FD) else Color.White,
                    shape = RoundedCornerShape(8.dp)
                )
                .clickable { onClick() }
                .padding(horizontal = 16.dp, vertical = 12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = value.ifBlank { formField.hint },
                    fontSize = ShopFloor.BodySize,
                    color = if (!isEmpty) Color.Black else Color(0xFF999999),
                    modifier = Modifier.weight(1f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Icon(
                    imageVector = Icons.Default.ArrowDropDown,
                    contentDescription = "Select",
                    modifier = Modifier.size(28.dp),
                    tint = Color(0xFF666666)
                )
            }
        }
    }
}

// ======================================================================
// Text / multiline field
// ======================================================================

@Composable
private fun TextFormFieldInput(
    formField: FormField,
    value: String,
    onValueChange: (String) -> Unit
) {
    val labelText = if (formField.required) {
        buildAnnotatedString {
            append(formField.label)
            withStyle(SpanStyle(
                color = Color(0xFFD32F2F),
                fontWeight = FontWeight.Bold
            )) {
                append(" *")
            }
        }
    } else {
        buildAnnotatedString { append(formField.label) }
    }

    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(labelText, fontSize = ShopFloor.LabelSize) },
        placeholder = { Text(formField.hint, fontSize = ShopFloor.BodySize) },
        singleLine = formField.inputType != InputType.MULTILINE,
        keyboardOptions = KeyboardOptions.Default.copy(
            keyboardType = when (formField.inputType) {
                InputType.NUMBER -> KeyboardType.Decimal
                else -> KeyboardType.Text
            }
        ),
        textStyle = TextStyle(fontSize = ShopFloor.BodySize),
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = ShopFloor.TextFieldMinHeight)
    )
}
