package com.toolsnap.ui.wizard

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.ui.theme.ShopFloor

/**
 * Category picker — shown after name entry, before capture.
 *
 * Displays all [ToolCategory] values grouped into sections:
 *   - Solid Tools (end mills, drills, taps, reamers)
 *   - Indexable Bodies (face mills, boring bars, turning holders, etc.)
 *   - Consumables & Hardware (inserts, screws, shims, clamps, wedges)
 *   - Holders & Adapters
 *   - Other
 *
 * Each category renders as a tappable card with radio indicator,
 * category name, and description.  Shop-floor sizing: big cards,
 * big text, glove-friendly taps.
 */
@Composable
fun CategoryPickerScreen(
    toolName: String,
    onCategorySelected: (ToolCategory) -> Unit
) {
    var selected by remember { mutableStateOf<ToolCategory?>(null) }

    val sections = remember { buildSections() }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(ShopFloor.ScreenPadding)
    ) {
        // ---- Header ----
        Text(
            text = toolName,
            fontSize = ShopFloor.HeadlineSize,
            fontWeight = FontWeight.Bold,
            maxLines = 1
        )

        Spacer(Modifier.height(4.dp))

        Text(
            text = "What are you capturing?",
            fontSize = ShopFloor.BodySize,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(Modifier.height(16.dp))

        // ---- Sectioned type cards ----
        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(6.dp),
            contentPadding = PaddingValues(bottom = 16.dp)
        ) {
            for (section in sections) {
                item(key = "header_${section.title}") {
                    SectionHeader(section.title)
                }
                items(
                    items = section.categories,
                    key = { it.name }
                ) { category ->
                    CategoryCard(
                        category = category,
                        isSelected = category == selected,
                        onClick = { selected = category }
                    )
                }
            }
        }

        // ---- Continue button ----
        Button(
            onClick = { selected?.let { onCategorySelected(it) } },
            enabled = selected != null,
            modifier = Modifier
                .fillMaxWidth()
                .height(ShopFloor.ButtonHeight),
            colors = ButtonDefaults.buttonColors(
                containerColor = ShopFloor.PrimaryButton,
                contentColor = ShopFloor.PrimaryButtonText
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                "CONTINUE",
                fontSize = ShopFloor.ButtonTextSize,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

// ======================================================================
// Section data
// ======================================================================

private data class PickerSection(
    val title: String,
    val categories: List<ToolCategory>
)

/** Build the grouped section list from ToolCategory.pickerOrder. */
private fun buildSections(): List<PickerSection> = listOf(
    PickerSection(
        "Solid Tools",
        listOf(
            ToolCategory.END_MILL,
            ToolCategory.DRILL,
            ToolCategory.TAP,
            ToolCategory.REAMER
        )
    ),
    PickerSection(
        "Indexable Tool Bodies",
        listOf(
            ToolCategory.INDEXABLE_MILL_BODY,
            ToolCategory.INDEXABLE_DRILL_BODY,
            ToolCategory.BORING_BAR_BODY,
            ToolCategory.TURNING_HOLDER,
            ToolCategory.THREADING_HOLDER,
            ToolCategory.GROOVING_HOLDER
        )
    ),
    PickerSection(
        "Consumables & Hardware",
        listOf(
            ToolCategory.INSERT,
            ToolCategory.SCREW,
            ToolCategory.SHIM,
            ToolCategory.CLAMP,
            ToolCategory.WEDGE
        )
    ),
    PickerSection(
        "Holders & Adapters",
        listOf(
            ToolCategory.HOLDER,
            ToolCategory.COLLET,
            ToolCategory.RETENTION_KNOB
        )
    ),
    PickerSection(
        "Other",
        listOf(ToolCategory.OTHER)
    )
)

// ======================================================================
// Section header
// ======================================================================

@Composable
private fun SectionHeader(title: String) {
    Text(
        text = title,
        fontSize = 16.sp,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier.padding(top = 8.dp, bottom = 2.dp)
    )
}

// ======================================================================
// Single category card
// ======================================================================

@Composable
private fun CategoryCard(
    category: ToolCategory,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val borderColor = if (isSelected)
        ShopFloor.PrimaryButton else Color.Transparent
    val bgColor = if (isSelected)
        ShopFloor.PrimaryButton.copy(alpha = 0.08f)
    else
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(
            width = if (isSelected) 2.dp else 1.dp,
            color = if (isSelected) borderColor
                else MaterialTheme.colorScheme.outlineVariant
        ),
        colors = CardDefaults.cardColors(containerColor = bgColor),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (isSelected) 2.dp else 0.dp
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            RadioButton(
                selected = isSelected,
                onClick = onClick,
                colors = RadioButtonDefaults.colors(
                    selectedColor = ShopFloor.PrimaryButton,
                    unselectedColor = MaterialTheme.colorScheme.onSurfaceVariant
                )
            )

            Spacer(Modifier.width(8.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = category.displayName,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = category.description,
                    fontSize = 15.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    lineHeight = 20.sp
                )
            }
        }
    }
}
