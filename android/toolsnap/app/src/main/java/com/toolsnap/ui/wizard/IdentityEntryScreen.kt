package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Edit
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.toolsnap.config.DropdownOptions
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.ocr.OcrFieldMatcher
import com.toolsnap.ui.theme.ShopFloor

/**
 * Screen 2 — Tool identity.
 *
 * Two entry paths:
 *   SCAN LABEL → camera → OCR chip picker (IdentityOcrPickerScreen)
 *   ENTER MANUALLY → inline form with EDP + manufacturer dropdown
 *
 * Initial view shows two big buttons. Once data is entered (from either
 * path), the form fields become visible and editable.
 *
 * Auto-generated tool name:
 *   When MPN/ISO is populated → "$manufacturer $mpnIso"
 *     (e.g. "Sandvik Coromant CNMG 120408-PM")
 *   Otherwise → "$manufacturer $edp"
 *     (e.g. "Kennametal A3S2000M400")
 *
 * NEXT gate:
 *   INSERT: manufacturer + mpnIso required, edp optional
 *   Everything else: manufacturer + edp required
 */

private enum class IdentityMode { CHOICE, MANUAL }

@Composable
fun IdentityEntryScreen(
    category: ToolCategory,
    initialEdp: String = "",
    initialManufacturer: String = "",
    initialMpnIso: String = "",
    initialName: String = "",
    onScanLabel: () -> Unit,
    onNext: (edp: String, manufacturer: String, mpnIso: String, toolName: String) -> Unit,
    onBack: () -> Unit,
    onCancel: () -> Unit
) {
    var mode by remember { mutableStateOf(
        if (initialEdp.isNotBlank() || initialManufacturer.isNotBlank())
            IdentityMode.MANUAL else IdentityMode.CHOICE
    ) }
    var edp by remember { mutableStateOf(initialEdp) }
    var manufacturer by remember { mutableStateOf(initialManufacturer) }
    var mpnIso by remember { mutableStateOf(initialMpnIso) }
    var nameOverride by remember { mutableStateOf(initialName) }
    var showNameEdit by remember { mutableStateOf(false) }
    var showManufacturerPicker by remember { mutableStateOf(false) }

    val showMpnIso = OcrFieldMatcher.thirdFieldLabel(category) != null
    val mpnIsoLabel = OcrFieldMatcher.thirdFieldLabel(category) ?: ""

    // Auto-name formula:
    //   When MPN/ISO is populated → Manufacturer + MPN/ISO
    //     (e.g. "Sandvik Coromant CNMG 120408-PM")
    //   Otherwise → Manufacturer + EDP
    //     (e.g. "Kennametal A3S2000M400")
    val autoName = buildString {
        if (manufacturer.isNotBlank()) append(manufacturer)
        val identifier = if (mpnIso.isNotBlank()) mpnIso else edp
        if (manufacturer.isNotBlank() && identifier.isNotBlank()) append(" ")
        if (identifier.isNotBlank()) append(identifier)
    }
    val displayName = nameOverride.ifBlank { autoName }

    // NEXT gate: manufacturer always required.
    // If MPN/ISO field is visible, require at least one of mpnIso or edp.
    // If no MPN/ISO field, require edp.
    val canProceed = manufacturer.isNotBlank() && (
        if (showMpnIso) mpnIso.isNotBlank() || edp.isNotBlank()
        else edp.isNotBlank()
    )

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
                    text = "STEP 2 OF 5",
                    fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText.copy(alpha = 0.8f)
                )
                Text(
                    text = "IDENTIFY THE TOOL",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Text(
                    text = category.displayName,
                    fontSize = ShopFloor.TitleSize,
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
                text = if (showMpnIso)
                    "Manufacturer + MPN/ISO required \u2022 EDP optional"
                else
                    "EDP / catalog number and manufacturer are required",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Content
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            when (mode) {
                IdentityMode.CHOICE -> {
                    Spacer(Modifier.height(24.dp))

                    // SCAN LABEL button
                    Button(
                        onClick = onScanLabel,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(ShopFloor.ButtonHeight),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF00838F),
                            contentColor = Color.White
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(28.dp))
                        Spacer(Modifier.size(12.dp))
                        Text(
                            "SCAN LABEL",
                            fontSize = ShopFloor.ButtonTextSize,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Spacer(Modifier.height(8.dp))

                    // ENTER MANUALLY button
                    Button(
                        onClick = { mode = IdentityMode.MANUAL },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(ShopFloor.ButtonHeight),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = ShopFloor.PrimaryButton,
                            contentColor = ShopFloor.PrimaryButtonText
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Default.Edit, null, modifier = Modifier.size(28.dp))
                        Spacer(Modifier.size(12.dp))
                        Text(
                            "ENTER MANUALLY",
                            fontSize = ShopFloor.ButtonTextSize,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                IdentityMode.MANUAL -> {
                    // EDP / Catalog Number field
                    // For INSERT: optional (MPN/ISO is primary)
                    // For everything else: required
                    Text(
                        text = buildAnnotatedString {
                            append("EDP / Catalog Number")
                            if (!showMpnIso) {
                                withStyle(SpanStyle(color = Color(0xFFD32F2F), fontWeight = FontWeight.Bold)) {
                                    append(" *")
                                }
                            }
                        },
                        fontSize = ShopFloor.LabelSize,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF444444)
                    )
                    OutlinedTextField(
                        value = edp,
                        onValueChange = { edp = it },
                        placeholder = { Text(
                            if (showMpnIso) "e.g. 5722939 (ordering code, optional)"
                            else "e.g. A3S2000M400",
                            fontSize = ShopFloor.BodySize
                        ) },
                        textStyle = TextStyle(fontSize = ShopFloor.BodySize),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(Modifier.height(8.dp))

                    // Manufacturer dropdown (required)
                    Text(
                        text = buildAnnotatedString {
                            append("Manufacturer")
                            withStyle(SpanStyle(color = Color(0xFFD32F2F), fontWeight = FontWeight.Bold)) {
                                append(" *")
                            }
                        },
                        fontSize = ShopFloor.LabelSize,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF444444)
                    )
                    ManufacturerDropdown(
                        value = manufacturer,
                        onClick = { showManufacturerPicker = true }
                    )

                    // MPN / ISO field (INSERT category only — required)
                    if (showMpnIso) {
                        Spacer(Modifier.height(8.dp))
                        Text(
                            text = buildAnnotatedString {
                                append(mpnIsoLabel)
                                withStyle(SpanStyle(color = Color(0xFFD32F2F), fontWeight = FontWeight.Bold)) {
                                    append(" *")
                                }
                            },
                            fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.SemiBold,
                            color = Color(0xFF444444)
                        )
                        OutlinedTextField(
                            value = mpnIso,
                            onValueChange = { mpnIso = it },
                            placeholder = { Text("e.g. CNMG 120408", fontSize = ShopFloor.BodySize) },
                            textStyle = TextStyle(fontSize = ShopFloor.BodySize),
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    // Auto-generated name display
                    if (displayName.isNotBlank()) {
                        Spacer(Modifier.height(16.dp))
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Tool Name",
                                    fontSize = ShopFloor.LabelSize,
                                    fontWeight = FontWeight.SemiBold,
                                    color = Color(0xFF444444)
                                )
                                Text(
                                    text = displayName,
                                    fontSize = ShopFloor.TitleSize,
                                    fontWeight = FontWeight.Medium
                                )
                            }
                            Button(
                                onClick = { showNameEdit = !showNameEdit },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color(0xFFE0E0E0),
                                    contentColor = Color(0xFF333333)
                                ),
                                shape = RoundedCornerShape(8.dp),
                                modifier = Modifier.height(40.dp)
                            ) {
                                Text("EDIT", fontSize = ShopFloor.LabelSize, fontWeight = FontWeight.Bold)
                            }
                        }

                        if (showNameEdit) {
                            OutlinedTextField(
                                value = nameOverride.ifBlank { autoName },
                                onValueChange = { nameOverride = it },
                                label = { Text("Custom name", fontSize = ShopFloor.LabelSize) },
                                textStyle = TextStyle(fontSize = ShopFloor.BodySize),
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }

                    // Switch to scan option
                    Spacer(Modifier.height(16.dp))
                    Button(
                        onClick = onScanLabel,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(ShopFloor.SmallButtonHeight),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF00838F),
                            contentColor = Color.White
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(20.dp))
                        Spacer(Modifier.size(8.dp))
                        Text(
                            "SCAN LABEL INSTEAD",
                            fontSize = ShopFloor.SmallButtonTextSize,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }

        // Bottom buttons
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
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
                Text("BACK", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
            }

            Button(
                onClick = {
                    val finalName = nameOverride.ifBlank { autoName }
                    onNext(edp.trim(), manufacturer.trim(), mpnIso.trim(), finalName.trim())
                },
                enabled = canProceed,
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (canProceed) ShopFloor.SuccessButton else Color(0xFF888888),
                    contentColor = if (canProceed) ShopFloor.SuccessButtonText else Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("NEXT", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                Spacer(Modifier.size(8.dp))
                Icon(Icons.Default.ChevronRight, null, modifier = Modifier.size(28.dp))
            }
        }

        // Cancel
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
            Text("CANCEL", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
        }
    }

    // Manufacturer picker sheet (reuses DropdownPickerSheet)
    if (showManufacturerPicker) {
        DropdownPickerSheet(
            formField = com.toolsnap.config.FormField(
                key = "manufacturer",
                label = "Manufacturer",
                hint = "Select manufacturer",
                inputType = com.toolsnap.config.InputType.DROPDOWN,
                dropdownOptions = DropdownOptions.manufacturers,
                required = true
            ),
            currentValue = manufacturer,
            onSelect = { selected ->
                manufacturer = selected
                showManufacturerPicker = false
            },
            onDismiss = { showManufacturerPicker = false }
        )
    }
}

/**
 * Tappable manufacturer display that opens the picker sheet.
 */
@Composable
private fun ManufacturerDropdown(
    value: String,
    onClick: () -> Unit
) {
    val isEmpty = value.isBlank()
    val borderColor = if (!isEmpty) Color(0xFF1976D2) else Color(0xFFE57373)

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(60.dp)
            .background(
                color = if (!isEmpty) Color(0xFFE3F2FD) else Color.White,
                shape = RoundedCornerShape(8.dp)
            )
            .  clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxSize(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = value.ifBlank { "Select manufacturer…" },
                fontSize = ShopFloor.BodySize,
                color = if (!isEmpty) Color.Black else Color(0xFF999999),
                modifier = Modifier.weight(1f)
            )
            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = "Select",
                modifier = Modifier.size(28.dp),
                tint = Color(0xFF666666)
            )
        }
    }
}
