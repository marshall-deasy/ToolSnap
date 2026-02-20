package com.toolsnap.ui.detail

import androidx.compose.foundation.Image
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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.toolsnap.core.model.Tool
import com.toolsnap.core.session.SessionExporter
import com.toolsnap.core.session.SessionManager
import com.toolsnap.ui.theme.ShopFloor
import com.toolsnap.utils.FileUtils
import com.toolsnap.utils.ManifestV3
import java.io.File
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * Detail screen for viewing and managing a single saved tool session.
 *
 * FIX: Now loads via [ManifestV3.readManifest] which handles V1/V2/V3
 * format auto-detection. This fixes the permanent "Loading…" bug
 * that occurred because the old code path used
 * [SessionManager.loadSessionFromDir] → [JsonUtils.readManifest]
 * which expected V1 format, but the wizard's saveTool() writes V3.
 *
 * Displays the [Tool] object's identity fields, attributes, photos,
 * and notes in a scrollable card list with edit pencils.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SessionDetailScreen(
    folderName: String,
    onBack: () -> Unit,
    onEditField: (folderName: String, fieldIndex: Int) -> Unit
) {
    val context = LocalContext.current
    val sessionManager = remember { SessionManager(context) }
    val exporter = remember { SessionExporter(context) }

    var tool by remember { mutableStateOf<Tool?>(null) }
    var sessionDir by remember { mutableStateOf<File?>(null) }
    var showDeleteDialog by remember { mutableStateOf(false) }
    var refreshKey by remember { mutableStateOf(0) }

    val dateFormatter = remember {
        DateTimeFormatter.ofPattern("MMM d, yyyy  h:mm a")
            .withZone(ZoneId.systemDefault())
    }

    // ── FIX: Load via ManifestV3 (auto-detects V1/V2/V3) ──
    // Previously: sessionManager.loadSessionFromDir(dir) → JsonUtils V1 → null
    LaunchedEffect(folderName, refreshKey) {
        val dir = FileUtils.sessionDirByName(context, folderName)
        sessionDir = dir
        val result = ManifestV3.readManifest(dir)
        tool = result?.tools?.firstOrNull()
    }

    // Bump refreshKey when this composable re-enters composition
    // (i.e. after navigating back from edit flow)
    LaunchedEffect(Unit) { refreshKey++ }

    val currentTool = tool

    if (currentTool == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Loading\u2026", fontSize = ShopFloor.TitleSize)
        }
        return
    }

    // Build the list of displayable detail rows
    val detailRows = buildDetailRows(currentTool)

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        currentTool.displaySummary(),
                        fontSize = ShopFloor.TitleSize,
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack, "Back",
                            modifier = Modifier.size(28.dp)
                        )
                    }
                },
                actions = {
                    IconButton(onClick = {
                        sessionDir?.let { dir ->
                            val intent = exporter.createShareIntent(dir)
                            if (intent != null) {
                                context.startActivity(intent)
                            }
                        }
                    }) {
                        Icon(
                            Icons.Default.Share, "Share",
                            modifier = Modifier.size(28.dp)
                        )
                    }
                    IconButton(onClick = { showDeleteDialog = true }) {
                        Icon(
                            Icons.Default.Delete, "Delete",
                            tint = ShopFloor.DangerButton,
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
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
            contentPadding = PaddingValues(ShopFloor.ScreenPadding),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header — date, category, status
            item {
                Column {
                    Text(
                        text = dateFormatter.format(currentTool.createdAt),
                        fontSize = ShopFloor.BodySize,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(4.dp))
                    Row {
                        Text(
                            text = currentTool.category.displayName,
                            fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(Modifier.width(12.dp))
                        Text(
                            text = currentTool.status.name,
                            fontSize = ShopFloor.LabelSize,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            // Detail field cards
            items(detailRows, key = { it.label }) { row ->
                DetailFieldCard(
                    label = row.label,
                    value = row.value,
                    onEdit = { onEditField(folderName, 0) }
                )
            }

            // Notes card
            if (!currentTool.notes.isNullOrBlank()) {
                item {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onEditField(folderName, 0) },
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                    ) {
                        Column(modifier = Modifier.padding(ShopFloor.CardPadding)) {
                            Text(
                                "Notes",
                                fontSize = ShopFloor.BodySize,
                                fontWeight = FontWeight.SemiBold,
                                modifier = Modifier.padding(bottom = 4.dp)
                            )
                            Text(
                                currentTool.notes!!,
                                fontSize = ShopFloor.LabelSize,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }

            // ── Photos — displayed at the bottom of the detail view ──
            if (currentTool.photoPaths.isNotEmpty()) {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                    ) {
                        Column(modifier = Modifier.padding(ShopFloor.CardPadding)) {
                            Text(
                                "Photos (${currentTool.photoPaths.size})",
                                fontSize = ShopFloor.BodySize,
                                fontWeight = FontWeight.SemiBold,
                                modifier = Modifier.padding(bottom = 8.dp)
                            )
                            currentTool.photoPaths.forEach { path ->
                                Image(
                                    painter = rememberAsyncImagePainter(File(path)),
                                    contentDescription = "Tool photo",
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .heightIn(min = 150.dp, max = 360.dp)
                                        .padding(bottom = 8.dp),
                                    contentScale = ContentScale.Fit
                                )
                            }
                        }
                    }
                }
            }

            // Bottom spacer for comfortable scrolling
            item { Spacer(Modifier.height(24.dp)) }
        }
    }

    // — Delete confirmation dialog ————————————————————
    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = {
                Text(
                    "Delete Entry?",
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Text(
                    "This will permanently delete " +
                        "\"${currentTool.displaySummary()}\" and all its photos.",
                    fontSize = ShopFloor.BodySize
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        sessionManager.deleteSession(folderName)
                        showDeleteDialog = false
                        onBack()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.DangerButton,
                        contentColor = ShopFloor.DangerButtonText
                    ),
                    modifier = Modifier.height(ShopFloor.SmallButtonHeight),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(
                        "DELETE",
                        fontSize = ShopFloor.SmallButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            },
            dismissButton = {
                Button(
                    onClick = { showDeleteDialog = false },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    modifier = Modifier.height(ShopFloor.SmallButtonHeight),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(
                        "CANCEL",
                        fontSize = ShopFloor.SmallButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        )
    }
}

// ======================================================================
// Detail row model
// ======================================================================

private data class DetailRow(
    val label: String,
    val value: String
)

/**
 * Build an ordered list of label→value rows from the Tool's fields.
 * Only includes fields that have non-blank data.
 */
private fun buildDetailRows(tool: Tool): List<DetailRow> {
    val rows = mutableListOf<DetailRow>()

    tool.manufacturer?.takeIf { it.isNotBlank() }?.let {
        rows.add(DetailRow("Manufacturer", it))
    }
    tool.catalogNumber?.takeIf { it.isNotBlank() }?.let {
        rows.add(DetailRow("Catalog / EDP", it))
    }
    tool.mpnIso?.takeIf { it.isNotBlank() }?.let {
        rows.add(DetailRow("MPN / ISO", it))
    }
    tool.description?.takeIf { it.isNotBlank() }?.let {
        rows.add(DetailRow("Description", it))
    }

    // Category-specific attributes (from ComponentTemplates fields)
    for ((key, value) in tool.attributes) {
        if (value.isBlank()) continue
        rows.add(DetailRow(formatKey(key), value))
    }

    if (tool.tags.isNotEmpty()) {
        rows.add(DetailRow("Tags", tool.tags.joinToString(", ")))
    }

    return rows
}

// ======================================================================
// Detail field card
// ======================================================================

@Composable
private fun DetailFieldCard(
    label: String,
    value: String,
    onEdit: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onEdit),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.CardPadding),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = label,
                    fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Medium,
                    color = Color(0xFF555555)
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = value,
                    fontSize = ShopFloor.BodySize,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }

            // Edit pencil — always visible
            IconButton(
                onClick = onEdit,
                modifier = Modifier.size(44.dp)
            ) {
                Icon(
                    Icons.Default.Edit,
                    contentDescription = "Edit $label",
                    tint = ShopFloor.PrimaryButton,
                    modifier = Modifier.size(28.dp)
                )
            }
        }
    }
}

/** Converts "nose_radius" to "Nose Radius" for display. */
private fun formatKey(key: String): String {
    return key.split("_").joinToString(" ") { word ->
        word.replaceFirstChar { it.uppercase() }
    }
}
