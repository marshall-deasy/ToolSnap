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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.core.model.ComponentRole
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.ui.theme.ShopFloor

/**
 * Role + quantity picker — shared by quick-add and link-existing flows.
 */
@Composable
internal fun RoleQuantityPicker(
    toolSummary: String,
    toolCategory: ToolCategory,
    selectedRole: ComponentRole,
    selectedQuantity: Int,
    onRoleChange: (ComponentRole) -> Unit,
    onQuantityChange: (Int) -> Unit,
    onConfirm: () -> Unit,
    onBack: () -> Unit
) {
    Column(modifier = Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Column {
                Text(
                    text = "SET ROLE & QUANTITY",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = toolSummary,
                    fontSize = ShopFloor.BodySize,
                    color = ShopFloor.StepText.copy(alpha = 0.8f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Role in assembly:",
                fontSize = ShopFloor.TitleSize,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(bottom = 4.dp)
            )

            ComponentRole.entries.forEach { role ->
                val isSelected = role == selectedRole
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 52.dp)
                        .border(
                            width = if (isSelected) 2.dp else 1.dp,
                            color = if (isSelected) Color(0xFF1976D2)
                                else Color(0xFFCCCCCC),
                            shape = RoundedCornerShape(8.dp)
                        )
                        .background(
                            color = if (isSelected) Color(0xFFE3F2FD)
                                else Color.White,
                            shape = RoundedCornerShape(8.dp)
                        )
                        .clickable { onRoleChange(role) }
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    contentAlignment = Alignment.CenterStart
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Radio indicator
                        Box(
                            modifier = Modifier
                                .size(24.dp)
                                .border(
                                    width = 2.dp,
                                    color = if (isSelected) Color(0xFF1976D2)
                                        else Color(0xFFAAAAAA),
                                    shape = RoundedCornerShape(12.dp)
                                )
                                .then(
                                    if (isSelected) Modifier.background(
                                        Color(0xFF1976D2),
                                        RoundedCornerShape(12.dp)
                                    ) else Modifier
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            if (isSelected) {
                                Box(
                                    modifier = Modifier
                                        .size(10.dp)
                                        .background(
                                            Color.White,
                                            RoundedCornerShape(5.dp)
                                        )
                                )
                            }
                        }

                        Spacer(Modifier.width(14.dp))

                        Text(
                            text = role.displayName,
                            fontSize = ShopFloor.BodySize,
                            fontWeight = if (isSelected)
                                FontWeight.SemiBold else FontWeight.Normal
                        )
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            Text(
                text = "Quantity per assembly:",
                fontSize = ShopFloor.TitleSize,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(bottom = 4.dp)
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                listOf(1, 2, 3, 4, 5, 6).forEach { qty ->
                    val isSelected = qty == selectedQuantity
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .border(
                                width = if (isSelected) 2.dp else 1.dp,
                                color = if (isSelected) Color(0xFF1976D2)
                                    else Color(0xFFCCCCCC),
                                shape = RoundedCornerShape(8.dp)
                            )
                            .background(
                                color = if (isSelected) Color(0xFFE3F2FD)
                                    else Color.White,
                                shape = RoundedCornerShape(8.dp)
                            )
                            .clickable { onQuantityChange(qty) },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "$qty",
                            fontSize = 20.sp,
                            fontWeight = if (isSelected) FontWeight.Bold
                                else FontWeight.Normal,
                            color = if (isSelected) Color(0xFF1976D2)
                                else Color.Black
                        )
                    }
                }
            }

            Spacer(Modifier.height(16.dp))
        }

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
                Text(
                    "BACK",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }

            Button(
                onClick = onConfirm,
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Check, null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    "ADD",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

// ======================================================================
// Shared helpers
// ======================================================================

/** Build a default name for a quick-added component. */
internal fun buildToolName(
    category: ToolCategory,
    attrs: Map<String, String>
): String {
    val parts = mutableListOf<String>()
    attrs["manufacturer"]?.takeIf { it.isNotBlank() }?.let { parts.add(it) }
    attrs["catalog_number"]?.takeIf { it.isNotBlank() }?.let { parts.add(it) }

    if (parts.isEmpty()) {
        attrs["iso_designation"]?.takeIf { it.isNotBlank() }?.let { parts.add(it) }
        attrs["grade"]?.takeIf { it.isNotBlank() }?.let { parts.add(it) }
        attrs["size"]?.takeIf { it.isNotBlank() }?.let { parts.add(it) }
        attrs["drive_type"]?.takeIf { it.isNotBlank() }?.let { parts.add(it) }
    }

    return if (parts.isNotEmpty()) parts.joinToString(" ")
        else category.displayName
}

/** Default role based on the component's category. */
internal fun defaultRoleForCategory(category: ToolCategory): ComponentRole =
    when (category) {
        ToolCategory.INSERT -> ComponentRole.INSERT
        ToolCategory.SCREW -> ComponentRole.SCREW
        ToolCategory.SHIM -> ComponentRole.SHIM
        ToolCategory.CLAMP -> ComponentRole.CLAMP
        ToolCategory.WEDGE -> ComponentRole.WEDGE
        ToolCategory.COLLET -> ComponentRole.COLLET
        ToolCategory.RETENTION_KNOB -> ComponentRole.OTHER
        else -> ComponentRole.OTHER
    }

/** Color for role badges. */
internal fun roleColor(role: ComponentRole): Color = when (role) {
    ComponentRole.INSERT -> Color(0xFF1976D2)
    ComponentRole.WIPER_INSERT -> Color(0xFF0277BD)
    ComponentRole.SCREW -> Color(0xFF7B1FA2)
    ComponentRole.SHIM -> Color(0xFF00897B)
    ComponentRole.CLAMP -> Color(0xFFE64A19)
    ComponentRole.WEDGE -> Color(0xFF6D4C41)
    ComponentRole.COOLANT_PLUG -> Color(0xFF0097A7)
    ComponentRole.COLLET -> Color(0xFF388E3C)
    ComponentRole.ADAPTER -> Color(0xFF455A64)
    ComponentRole.OTHER -> Color(0xFF757575)
}
