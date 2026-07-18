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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.core.model.Tool
import com.toolsnap.ui.theme.ShopFloor

/**
 * Search existing standalone tools to link to an assembly.
 */
@Composable
internal fun SearchExistingView(
    query: String,
    onQueryChange: (String) -> Unit,
    tools: List<Tool>,
    alreadyLinkedIds: Set<String>,
    onToolSelected: (Tool) -> Unit,
    onBack: () -> Unit
) {
    val linkable = tools.filter { t ->
        !t.isAssembly && t.toolId !in alreadyLinkedIds
    }
    val filtered = if (query.isBlank()) linkable else {
        val q = query.trim().lowercase()
        linkable.filter { t ->
            t.name.lowercase().contains(q) ||
            (t.manufacturer?.lowercase()?.contains(q) == true) ||
            (t.catalogNumber?.lowercase()?.contains(q) == true) ||
            t.category.displayName.lowercase().contains(q)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Column {
                Text(
                    text = "LINK EXISTING TOOL",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "${linkable.size} tool${if (linkable.size != 1) "s" else ""} available",
                    fontSize = ShopFloor.LabelSize,
                    color = ShopFloor.StepText.copy(alpha = 0.7f)
                )
            }
        }

        OutlinedTextField(
            value = query,
            onValueChange = onQueryChange,
            placeholder = { Text("Search by name, catalog#, manufacturer\u2026") },
            singleLine = true,
            leadingIcon = {
                Icon(Icons.Default.Search, null, modifier = Modifier.size(24.dp))
            },
            textStyle = TextStyle(fontSize = ShopFloor.BodySize),
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 8.dp)
                .heightIn(min = 56.dp)
        )

        if (filtered.isEmpty()) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(ShopFloor.ScreenPadding),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = if (linkable.isEmpty())
                        "No standalone tools found.\nCapture some inserts or hardware first!"
                    else
                        "No matches for \u201c$query\u201d",
                    fontSize = ShopFloor.BodySize,
                    color = Color(0xFF999999),
                    textAlign = TextAlign.Center
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = ShopFloor.ScreenPadding),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(filtered, key = { it.toolId }) { tool ->
                    SearchResultRow(
                        tool = tool,
                        onClick = { onToolSelected(tool) }
                    )
                }
            }
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

@Composable
private fun SearchResultRow(tool: Tool, onClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 64.dp)
            .border(1.dp, Color(0xFFDDDDDD), RoundedCornerShape(8.dp))
            .background(Color.White, RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .background(Color(0xFF78909C), RoundedCornerShape(4.dp))
                .padding(horizontal = 6.dp, vertical = 3.dp)
        ) {
            Text(
                text = tool.category.displayName.uppercase(),
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                maxLines = 1
            )
        }

        Spacer(Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = tool.displaySummary(),
                fontSize = ShopFloor.BodySize,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            val sub = tool.manufacturer ?: tool.catalogNumber
            if (sub != null) {
                Text(
                    text = sub,
                    fontSize = ShopFloor.LabelSize,
                    color = Color(0xFF666666),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}
