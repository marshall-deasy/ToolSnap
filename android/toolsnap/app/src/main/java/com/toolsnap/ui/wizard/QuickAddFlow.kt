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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.ui.theme.ShopFloor

/**
 * Category picker for quick-adding consumables/hardware
 * to an assembly. Shows only linkable categories.
 */
@Composable
internal fun QuickAddCategoryPicker(
    onCategorySelected: (ToolCategory) -> Unit,
    onBack: () -> Unit
) {
    val consumableCategories = listOf(
        ToolCategory.INSERT,
        ToolCategory.SCREW,
        ToolCategory.SHIM,
        ToolCategory.CLAMP,
        ToolCategory.WEDGE,
        ToolCategory.COLLET,
        ToolCategory.RETENTION_KNOB,
        ToolCategory.OTHER
    )

    Column(modifier = Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Column {
                Text(
                    text = "WHAT ARE YOU ADDING?",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Pick the component type",
                    fontSize = ShopFloor.LabelSize,
                    color = ShopFloor.StepText.copy(alpha = 0.7f)
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
            consumableCategories.forEach { cat ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 64.dp)
                        .border(1.dp, Color(0xFFBBBBBB), RoundedCornerShape(10.dp))
                        .background(Color.White, RoundedCornerShape(10.dp))
                        .clickable { onCategorySelected(cat) }
                        .padding(horizontal = 20.dp, vertical = 14.dp),
                    contentAlignment = Alignment.CenterStart
                ) {
                    Column {
                        Text(
                            text = cat.displayName,
                            fontSize = ShopFloor.TitleSize,
                            fontWeight = FontWeight.SemiBold
                        )
                        Text(
                            text = cat.description,
                            fontSize = ShopFloor.LabelSize,
                            color = Color(0xFF666666)
                        )
                    }
                }
            }

            Spacer(Modifier.height(16.dp))
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding)
        ) {
            Button(
                onClick = onBack,
                modifier = Modifier
                    .fillMaxWidth()
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
        }
    }
}
