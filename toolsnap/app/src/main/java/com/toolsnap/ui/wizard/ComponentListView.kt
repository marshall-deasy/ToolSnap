package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.core.model.PendingComponent
import com.toolsnap.ui.theme.ShopFloor

/**
 * Main list of components linked to an assembly.
 * Shows current links with remove buttons, plus
 * Quick Add and Link Existing action buttons.
 */
@Composable
internal fun ComponentListView(
    parentCategoryName: String,
    components: List<PendingComponent>,
    onRemove: (Int) -> Unit,
    onQuickAdd: () -> Unit,
    onSearchExisting: () -> Unit,
    onDone: () -> Unit,
    onCancel: () -> Unit
) {
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
                    text = "LINK COMPONENTS",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Add inserts, screws, shims for this $parentCategoryName",
                    fontSize = ShopFloor.LabelSize,
                    color = ShopFloor.StepText.copy(alpha = 0.7f)
                )
            }
        }

        // Instruction
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.InstructionBackground)
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 10.dp)
        ) {
            Text(
                text = if (components.isEmpty())
                    "No components linked yet \u2014 tap a button below to add"
                else
                    "${components.size} component${if (components.size != 1) "s" else ""} linked",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Component list
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (components.isEmpty()) {
                Spacer(Modifier.height(32.dp))
                Text(
                    text = "Assemblies work best with their components.\n\n" +
                        "Quick Add creates a new component on the spot.\n" +
                        "Link Existing finds tools you\u2019ve already captured.",
                    fontSize = ShopFloor.BodySize,
                    color = Color(0xFF666666),
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            } else {
                components.forEachIndexed { index, pc ->
                    ComponentRow(pc) { onRemove(index) }
                }
            }

            Spacer(Modifier.height(16.dp))

            Button(
                onClick = onQuickAdd,
                modifier = Modifier.fillMaxWidth().height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF1976D2),
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Add, null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text("QUICK ADD NEW",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold)
            }

            Spacer(Modifier.height(8.dp))

            Button(
                onClick = onSearchExisting,
                modifier = Modifier.fillMaxWidth().height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF455A64),
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Search, null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text("LINK EXISTING TOOL",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold)
            }

            Spacer(Modifier.height(16.dp))
        }

        // Bottom action bar
        Row(
            modifier = Modifier.fillMaxWidth().padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
        ) {
            Button(
                onClick = onCancel,
                modifier = Modifier.weight(1f).height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SecondaryButton,
                    contentColor = ShopFloor.SecondaryButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("BACK",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold)
            }

            Button(
                onClick = onDone,
                modifier = Modifier.weight(1f).height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Check, null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text(if (components.isEmpty()) "SKIP" else "DONE",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold)
            }
        }
    }
}

// ======================================================================
// Single component row
// ======================================================================

@Composable
private fun ComponentRow(
    component: PendingComponent,
    onRemove: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFFDDDDDD), RoundedCornerShape(8.dp))
            .background(Color(0xFFF5F5F5), RoundedCornerShape(8.dp))
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .background(roleColor(component.role), RoundedCornerShape(4.dp))
                .padding(horizontal = 8.dp, vertical = 4.dp)
        ) {
            Text(
                text = component.role.displayName.uppercase(),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
        }

        Spacer(Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = component.tool.displaySummary(),
                fontSize = ShopFloor.BodySize,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            if (component.quantity > 1) {
                Text(
                    text = "Qty: ${component.quantity}",
                    fontSize = ShopFloor.LabelSize,
                    color = Color(0xFF666666)
                )
            }
        }

        IconButton(onClick = onRemove) {
            Icon(
                Icons.Default.Delete,
                contentDescription = "Remove",
                tint = Color(0xFFD32F2F),
                modifier = Modifier.size(28.dp)
            )
        }
    }
}
