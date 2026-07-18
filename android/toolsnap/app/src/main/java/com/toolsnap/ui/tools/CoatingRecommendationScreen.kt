package com.toolsnap.ui.tools

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.config.CoatingRecommendation
import com.toolsnap.config.materialNames
import com.toolsnap.config.materialToCoatings

/**
 * Material → coating recommendation screen.
 *
 * User picks a workpiece material from the dropdown, sees ranked
 * coating recommendations below — each with a one-line reason a
 * machinist can act on at the spindle.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CoatingRecommendationScreen(
    onBack: () -> Unit
) {
    var selectedMaterial by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }

    val recommendations: List<CoatingRecommendation> =
        materialToCoatings[selectedMaterial] ?: emptyList()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        "Coating Guide",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            modifier = Modifier.size(28.dp)
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp)
        ) {
            Spacer(Modifier.height(16.dp))

            // ---- Material dropdown ----
            ExposedDropdownMenuBox(
                expanded = expanded,
                onExpandedChange = { expanded = it }
            ) {
                OutlinedTextField(
                    value = selectedMaterial,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Workpiece Material", fontSize = 16.sp) },
                    placeholder = { Text("Select material…", fontSize = 18.sp) },
                    trailingIcon = {
                        ExposedDropdownMenuDefaults.TrailingIcon(expanded)
                    },
                    textStyle = TextStyle(fontSize = 22.sp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor()
                )

                ExposedDropdownMenu(
                    expanded = expanded,
                    onDismissRequest = { expanded = false }
                ) {
                    materialNames.forEach { material ->
                        DropdownMenuItem(
                            text = { Text(material, fontSize = 18.sp) },
                            onClick = {
                                selectedMaterial = material
                                expanded = false
                            },
                            contentPadding = PaddingValues(
                                horizontal = 16.dp, vertical = 12.dp
                            )
                        )
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // ---- Subheading ----
            if (selectedMaterial.isNotBlank()) {
                Text(
                    text = "Recommended coatings for $selectedMaterial",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(12.dp))
            }

            // ---- Recommendation cards ----
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 24.dp)
            ) {
                itemsIndexed(recommendations) { index, rec ->
                    CoatingCard(rank = index + 1, recommendation = rec)
                }
            }
        }
    }
}

// ======================================================================
// Single recommendation card
// ======================================================================

@Composable
private fun CoatingCard(
    rank: Int,
    recommendation: CoatingRecommendation
) {
    val rankColor = when (rank) {
        1    -> Color(0xFF2E7D32) // green — best pick
        2    -> Color(0xFF1565C0) // blue
        3    -> Color(0xFF5E35B1) // purple
        else -> Color(0xFF616161) // gray
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Rank badge
            Text(
                text = "#$rank",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = rankColor,
                modifier = Modifier.width(44.dp)
            )

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = recommendation.name,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = recommendation.reason,
                    fontSize = 16.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
