package com.toolsnap.ui.wizard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.ui.theme.ShopFloor

/**
 * Screen 1 — Tool classification.
 *
 * Displays ToolCategory.pickerOrder grouped into sections:
 * Solid Round Tools, Indexable Tool Bodies, Consumables/Hardware,
 * Holders/Adapters, Other.
 *
 * Selecting a category advances to identity entry (Screen 2).
 */
@Composable
fun ClassificationScreen(
    onCategorySelected: (ToolCategory) -> Unit,
    onCancel: () -> Unit
) {
    data class SectionItem(
        val sectionHeader: String? = null,
        val category: ToolCategory? = null
    )

    val sectionedItems = remember {
        buildList {
            add(SectionItem(sectionHeader = "SOLID ROUND TOOLS"))
            ToolCategory.pickerOrder
                .filter { it.isSolid }
                .forEach { add(SectionItem(category = it)) }

            add(SectionItem(sectionHeader = "INDEXABLE TOOL BODIES"))
            ToolCategory.pickerOrder
                .filter { it.isAssembly }
                .forEach { add(SectionItem(category = it)) }

            add(SectionItem(sectionHeader = "CONSUMABLES / HARDWARE"))
            ToolCategory.pickerOrder
                .filter { it.isConsumable }
                .forEach { add(SectionItem(category = it)) }

            add(SectionItem(sectionHeader = "HOLDERS / ADAPTERS"))
            ToolCategory.pickerOrder
                .filter { it.isHolder }
                .forEach { add(SectionItem(category = it)) }

            add(SectionItem(sectionHeader = "OTHER"))
            add(SectionItem(category = ToolCategory.OTHER))
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
                    text = "STEP 1 OF 5",
                    fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText.copy(alpha = 0.8f)
                )
                Text(
                    text = "WHAT TYPE OF TOOL?",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
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
                text = "Select the tool category — this determines which fields appear next",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Category list
        LazyColumn(
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(sectionedItems) { item ->
                if (item.sectionHeader != null) {
                    if (item != sectionedItems.first()) {
                        Spacer(Modifier.height(8.dp))
                    }
                    Text(
                        text = item.sectionHeader,
                        fontSize = ShopFloor.LabelSize,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(vertical = 4.dp)
                    )
                }
                if (item.category != null) {
                    CategoryCard(
                        category = item.category,
                        onClick = { onCategorySelected(item.category) }
                    )
                }
            }
            item { Spacer(Modifier.height(16.dp)) }
        }

        // Cancel button
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
            Text(
                "CANCEL",
                fontSize = ShopFloor.SmallButtonTextSize,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun CategoryCard(
    category: ToolCategory,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.Build,
                contentDescription = null,
                modifier = Modifier.size(28.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(Modifier.size(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = category.displayName,
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = category.description,
                    fontSize = ShopFloor.LabelSize,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Icon(
                Icons.Default.ChevronRight,
                contentDescription = "Select",
                modifier = Modifier.size(28.dp),
                tint = Color(0xFF999999)
            )
        }
    }
}
