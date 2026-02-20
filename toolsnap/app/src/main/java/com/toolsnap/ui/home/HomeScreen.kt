package com.toolsnap.ui.home

import androidx.compose.foundation.Image
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import coil.compose.rememberAsyncImagePainter
import java.io.File
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudDone
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.DeleteSweep
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.repeatOnLifecycle
import com.toolsnap.core.model.Tool
import com.toolsnap.core.session.SessionManager
import com.toolsnap.ui.theme.ShopFloor
import com.toolsnap.utils.FileUtils
import com.toolsnap.utils.ManifestV3
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * List item for the home screen — wraps a Tool loaded from a V3 manifest.
 */
data class ToolListItem(
    val tool: Tool,
    val folderName: String,
    val isSynced: Boolean
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onNewSession: () -> Unit,
    onSessionClick: (folderName: String) -> Unit,
    onCoatingGuide: () -> Unit = {},
    onExit: () -> Unit = {}
) {
    val context = LocalContext.current
    val sessionManager = remember { SessionManager(context) }
    var items by remember { mutableStateOf<List<ToolListItem>>(emptyList()) }
    var syncedCount by remember { mutableIntStateOf(0) }
    var showClearDialog by remember { mutableStateOf(false) }
    var showPurgeDialog by remember { mutableStateOf(false) }
    var deleteTarget by remember { mutableStateOf<ToolListItem?>(null) }

    // Load tools from disk via V3 manifest reader.
    // This is the FIX: previously used JsonUtils.readManifest() which
    // expected V1 format, but finalizeSession() overwrites manifest.json
    // with V3 format. Now we read V3 directly.
    fun loadSessions() {
        val dirs = FileUtils.listSessionDirs(context)
        items = dirs.mapNotNull { dir ->
            val result = ManifestV3.readManifest(dir) ?: return@mapNotNull null
            val tool = result.tools.firstOrNull() ?: return@mapNotNull null
            ToolListItem(
                tool = tool,
                folderName = dir.name,
                isSynced = FileUtils.isSynced(dir)
            )
        }
        syncedCount = items.count { it.isSynced }
    }

    // Reload every time this screen becomes the active destination.
    val lifecycleOwner = LocalLifecycleOwner.current
    LaunchedEffect(lifecycleOwner) {
        lifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.RESUMED) {
            loadSessions()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        "ToolSnap",
                        fontSize = ShopFloor.HeadlineSize,
                        fontWeight = FontWeight.Bold
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                ),
                actions = {
                    androidx.compose.material3.TextButton(onClick = onCoatingGuide) {
                        Text(
                            "Coatings Guide",
                            fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                    IconButton(onClick = onExit) {
                        Icon(
                            Icons.Default.ExitToApp,
                            contentDescription = "Exit",
                            modifier = Modifier.size(28.dp)
                        )
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = onNewSession,
                containerColor = ShopFloor.PrimaryButton,
                contentColor = ShopFloor.PrimaryButtonText,
                modifier = Modifier.size(72.dp)
            ) {
                Icon(
                    Icons.Default.Add,
                    contentDescription = "New Capture",
                    modifier = Modifier.size(36.dp)
                )
            }
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Clear synced banner — shows when synced sessions exist
            if (syncedCount > 0) {
                Button(
                    onClick = { showClearDialog = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = ShopFloor.ScreenPadding, vertical = 8.dp)
                        .height(ShopFloor.SmallButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF0D47A1),
                        contentColor = Color.White
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(
                        Icons.Default.DeleteSweep,
                        contentDescription = null,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(Modifier.size(8.dp))
                    Text(
                        "CLEAR $syncedCount SYNCED SESSION${if (syncedCount != 1) "S" else ""}",
                        fontSize = ShopFloor.SmallButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            if (items.isEmpty()) {
                EmptyState()
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(ShopFloor.ScreenPadding),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    items(
                        items = items,
                        key = { it.folderName }
                    ) { item ->
                        SwipeToDeleteToolCard(
                            item = item,
                            onClick = { onSessionClick(item.folderName) },
                            onDeleteRequest = { deleteTarget = item }
                        )
                    }

                    // DEV: Purge all button at bottom of list
                    item {
                        Spacer(Modifier.height(16.dp))
                        Button(
                            onClick = { showPurgeDialog = true },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(ShopFloor.SmallButtonHeight),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color(0xFF4A0000),
                                contentColor = Color.White
                            ),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Icon(
                                Icons.Default.DeleteSweep,
                                contentDescription = null,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(Modifier.size(8.dp))
                            Text(
                                "\u26A0 PURGE ALL (${items.size})",
                                fontSize = ShopFloor.SmallButtonTextSize,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Spacer(Modifier.height(80.dp)) // room for FAB
                    }
                }
            }
        }
    }

    // — Delete single session dialog ————————————————
    val target = deleteTarget
    if (target != null) {
        AlertDialog(
            onDismissRequest = { deleteTarget = null },
            title = {
                Text(
                    "Delete Entry?",
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Text(
                    "Permanently delete \"${target.tool.displaySummary()}\" and all its photos?",
                    fontSize = ShopFloor.BodySize
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        sessionManager.deleteSession(target.folderName)
                        deleteTarget = null
                        loadSessions()
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
                    onClick = { deleteTarget = null },
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

    // — Clear synced confirmation dialog ————————————
    if (showClearDialog) {
        AlertDialog(
            onDismissRequest = { showClearDialog = false },
            title = {
                Text(
                    "Clear Synced Sessions?",
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Text(
                    "Delete $syncedCount session${if (syncedCount != 1) "s" else ""} that have been synced to PC? This cannot be undone.",
                    fontSize = ShopFloor.BodySize
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        FileUtils.clearSyncedSessions(context)
                        showClearDialog = false
                        loadSessions()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.DangerButton,
                        contentColor = ShopFloor.DangerButtonText
                    ),
                    modifier = Modifier.height(ShopFloor.SmallButtonHeight),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("DELETE", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                Button(
                    onClick = { showClearDialog = false },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    modifier = Modifier.height(ShopFloor.SmallButtonHeight),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("CANCEL", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
                }
            }
        )
    }

    // — DEV: Purge all confirmation dialog ——————————
    if (showPurgeDialog) {
        AlertDialog(
            onDismissRequest = { showPurgeDialog = false },
            title = {
                Text(
                    "\u26A0 PURGE ALL DATA",
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.DangerButton
                )
            },
            text = {
                Text(
                    "Delete ALL ${items.size} sessions and every photo? This is a dev tool — there is no undo.",
                    fontSize = ShopFloor.BodySize
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        FileUtils.purgeAll(context)
                        showPurgeDialog = false
                        loadSessions()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF4A0000),
                        contentColor = Color.White
                    ),
                    modifier = Modifier.height(ShopFloor.SmallButtonHeight),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("PURGE EVERYTHING", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                Button(
                    onClick = { showPurgeDialog = false },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    modifier = Modifier.height(ShopFloor.SmallButtonHeight),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("CANCEL", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
                }
            }
        )
    }
}

// ======================================================================
// Swipe-to-delete wrapper for tool cards
// ======================================================================

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SwipeToDeleteToolCard(
    item: ToolListItem,
    onClick: () -> Unit,
    onDeleteRequest: () -> Unit
) {
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            if (value == SwipeToDismissBoxValue.EndToStart) {
                onDeleteRequest()
                false // Don't actually dismiss — let dialog confirm first
            } else false
        }
    )

    SwipeToDismissBox(
        state = dismissState,
        enableDismissFromStartToEnd = false,
        enableDismissFromEndToStart = true,
        backgroundContent = {
            val color by animateColorAsState(
                targetValue = when (dismissState.targetValue) {
                    SwipeToDismissBoxValue.EndToStart -> ShopFloor.DangerButton
                    else -> Color.Transparent
                },
                label = "swipe-bg"
            )
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(color, RoundedCornerShape(12.dp))
                    .padding(horizontal = 24.dp),
                contentAlignment = Alignment.CenterEnd
            ) {
                if (dismissState.targetValue == SwipeToDismissBoxValue.EndToStart) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Delete,
                            contentDescription = "Delete",
                            tint = Color.White,
                            modifier = Modifier.size(32.dp)
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "DELETE",
                            color = Color.White,
                            fontSize = ShopFloor.ButtonTextSize,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    ) {
        ToolCard(item = item, onClick = onClick)
    }
}

// ======================================================================
// Empty state
// ======================================================================

@Composable
private fun EmptyState(modifier: Modifier = Modifier) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(
                Icons.Default.Build,
                contentDescription = null,
                modifier = Modifier.size(80.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
            )
            Spacer(Modifier.height(16.dp))
            Text(
                "No tools captured yet",
                fontSize = ShopFloor.TitleSize,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "Tap + to start capturing",
                fontSize = ShopFloor.BodySize,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
            )
        }
    }
}

// ======================================================================
// Tool card
// ======================================================================

@Composable
private fun ToolCard(
    item: ToolListItem,
    onClick: () -> Unit
) {
    val tool = item.tool
    val dateFormatter = remember {
        DateTimeFormatter.ofPattern("MMM d, yyyy  h:mm a")
            .withZone(ZoneId.systemDefault())
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = if (item.isSynced) {
            CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f)
            )
        } else {
            CardDefaults.cardColors()
        }
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.CardPadding),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // ── Thumbnail (preferred) or status icon (fallback) ──
            val firstPhoto = tool.photoPaths.firstOrNull()
            if (firstPhoto != null && File(firstPhoto).exists()) {
                Image(
                    painter = rememberAsyncImagePainter(File(firstPhoto)),
                    contentDescription = "Tool photo",
                    modifier = Modifier
                        .size(52.dp)
                        .clip(RoundedCornerShape(8.dp)),
                    contentScale = ContentScale.Crop
                )
            } else if (item.isSynced) {
                Icon(
                    Icons.Default.CloudDone,
                    contentDescription = "Synced",
                    tint = Color(0xFF0D47A1),
                    modifier = Modifier.size(40.dp)
                )
            } else {
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = "Saved",
                    tint = ShopFloor.CapturedColor,
                    modifier = Modifier.size(40.dp)
                )
            }

            Spacer(Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = tool.displaySummary(),
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(2.dp))
                Row {
                    Text(
                        text = tool.category.displayName,
                        fontSize = ShopFloor.LabelSize,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(Modifier.width(12.dp))
                    Text(
                        text = dateFormatter.format(tool.createdAt),
                        fontSize = ShopFloor.LabelSize,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    if (item.isSynced) {
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "SYNCED",
                            fontSize = ShopFloor.LabelSize,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF0D47A1)
                        )
                    }
                }
            }

            // Sync indicator on right side when thumbnail replaces the left icon
            if (firstPhoto != null && File(firstPhoto).exists() && item.isSynced) {
                Icon(
                    Icons.Default.CloudDone,
                    contentDescription = "Synced",
                    tint = Color(0xFF0D47A1),
                    modifier = Modifier.size(24.dp)
                )
            }
        }
    }
}
