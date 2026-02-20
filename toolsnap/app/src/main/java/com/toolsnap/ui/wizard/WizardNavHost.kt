package com.toolsnap.ui.wizard

import android.util.Log
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Snackbar
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.toolsnap.config.CaptureConfig
import com.toolsnap.core.model.ComponentLink
import com.toolsnap.core.model.Tool
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.model.ToolStatus
import com.toolsnap.core.ocr.OcrFieldMatcher
import com.toolsnap.core.ocr.OcrProcessor
import com.toolsnap.utils.FileUtils
import com.toolsnap.utils.ImageUtils
import com.toolsnap.utils.ManifestV3
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.time.Instant
import java.time.LocalDate
import java.time.format.DateTimeFormatter

private const val TAG = "WizardNavHost"

/**
 * New 5-phase wizard orchestrator.
 *
 * Flow:
 *   CLASSIFY → IDENTITY → (OCR_CAPTURE → OCR_PICK) → SPECS →
 *   LINK_COMPONENTS (conditional) → PHOTO_SAVE
 *
 * Builds a [Tool] object in memory. Each screen populates fields.
 * On SAVE, writes ManifestV3 + copies photo to session folder.
 */

private enum class WizardPhase {
    CLASSIFY,
    IDENTITY,
    OCR_CAPTURE,
    OCR_PICK,
    SPECS,
    LINK_COMPONENTS,
    PHOTO_SAVE
}

private enum class ConfirmDialog { NONE, ABANDON }

@Composable
fun WizardNavHost(
    onFinished: () -> Unit,
    onCancelled: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }

    // Wizard state
    var phase by remember { mutableStateOf(WizardPhase.CLASSIFY) }
    var activeDialog by remember { mutableStateOf(ConfirmDialog.NONE) }
    var isSaving by remember { mutableStateOf(false) }

    // Tool being built
    var tool by remember { mutableStateOf(Tool()) }
    var componentLinks by remember { mutableStateOf<List<ComponentLink>>(emptyList()) }
    var specValues by remember { mutableStateOf<Map<String, String>>(emptyMap()) }

    // Identity fields (kept separate for Screen 2 ↔ OCR round-trip)
    var edp by remember { mutableStateOf("") }
    var manufacturer by remember { mutableStateOf("") }
    var mpnIso by remember { mutableStateOf("") }
    var toolName by remember { mutableStateOf("") }

    // OCR state
    var ocrImagePath by remember { mutableStateOf("") }
    var ocrElements by remember { mutableStateOf<List<OcrProcessor.OcrElement>>(emptyList()) }
    var ocrProcessing by remember { mutableStateOf(false) }
    var ocrError by remember { mutableStateOf<String?>(null) }
    var ocrMatchResult by remember { mutableStateOf<OcrFieldMatcher.MatchResult?>(null) }

    // Existing tools for linking screen
    var existingTools by remember { mutableStateOf<List<Tool>>(emptyList()) }

    fun showError(msg: String) { scope.launch { snackbarHostState.showSnackbar(msg) } }

    fun requestCancel() {
        if (phase != WizardPhase.CLASSIFY) {
            activeDialog = ConfirmDialog.ABANDON
        } else {
            onCancelled()
        }
    }

    /**
     * Write the tool to disk and navigate home.
     */
    fun saveTool(photoPath: String?) {
        if (isSaving) return
        isSaving = true

        scope.launch {
            try {
                withContext(Dispatchers.IO) {
                    // Finalize the tool object
                    tool.catalogNumber = edp
                    tool.manufacturer = manufacturer
                    tool.mpnIso = mpnIso.ifBlank { null }

                    // Auto-generate tool name:
                    //   INSERT category → Manufacturer + MPN/ISO (what machinists call it)
                    //   Everything else → Manufacturer + EDP/catalog number
                    //   User-entered toolName always wins if non-blank
                    tool.name = when {
                        toolName.isNotBlank() -> toolName
                        tool.category == ToolCategory.INSERT && mpnIso.isNotBlank() ->
                            "$manufacturer $mpnIso".trim()
                        else -> "$manufacturer $edp".trim()
                    }
                    tool.status = ToolStatus.CAPTURED
                    tool.mergeAttributes(specValues)
                    tool.touch()

                    // Create session directory
                    val dateStr = LocalDate.now()
                        .format(DateTimeFormatter.ISO_LOCAL_DATE)
                    val folderName = CaptureConfig.sessionFolderName(
                        tool.name, dateStr
                    )
                    val sessionDir = FileUtils.sessionDirByName(context, folderName)
                    if (!sessionDir.exists()) sessionDir.mkdirs()

                    // Handle duplicate folder names
                    val finalDir = if (sessionDir.exists() &&
                        File(sessionDir, CaptureConfig.MANIFEST_FILE_NAME).exists()
                    ) {
                        val altName = "${folderName}_${System.currentTimeMillis() % 10000}"
                        val altDir = FileUtils.sessionDirByName(context, altName)
                        altDir.mkdirs()
                        altDir
                    } else {
                        if (!sessionDir.exists()) sessionDir.mkdirs()
                        sessionDir
                    }

                    // Save photo
                    if (photoPath != null) {
                        val destFile = File(finalDir, "photo_0.jpg")
                        val normalized = ImageUtils.normalizeOrientation(photoPath)
                        ImageUtils.saveAndCompress(normalized, destFile)
                        tool.photoPaths.clear()
                        tool.photoPaths.add(destFile.absolutePath)
                    }

                    // Write V3 manifest
                    ManifestV3.writeManifest(listOf(tool), componentLinks, finalDir)

                    Log.i(TAG, "Tool saved: ${tool.displaySummary()} → ${finalDir.name}")
                }

                isSaving = false
                onFinished()
            } catch (e: Exception) {
                Log.e(TAG, "Save failed: ${e.message}", e)
                isSaving = false
                showError("Save failed — ${e.message}")
            }
        }
    }

    // — Back handlers —————————————————————————————————
    BackHandler(enabled = phase == WizardPhase.CLASSIFY) {
        onCancelled()
    }
    BackHandler(enabled = phase == WizardPhase.IDENTITY) {
        phase = WizardPhase.CLASSIFY
    }
    BackHandler(enabled = phase == WizardPhase.OCR_CAPTURE) {
        phase = WizardPhase.IDENTITY
    }
    BackHandler(enabled = phase == WizardPhase.OCR_PICK) {
        phase = WizardPhase.IDENTITY
    }
    BackHandler(enabled = phase == WizardPhase.SPECS) {
        phase = WizardPhase.IDENTITY
    }
    BackHandler(enabled = phase == WizardPhase.LINK_COMPONENTS) {
        phase = WizardPhase.SPECS
    }
    BackHandler(enabled = phase == WizardPhase.PHOTO_SAVE) {
        if (isSaving) return@BackHandler
        phase = if (tool.category.isAssembly) WizardPhase.LINK_COMPONENTS
               else WizardPhase.SPECS
    }

    // — Scaffold —————————————————————————————————————
    Scaffold(
        snackbarHost = {
            SnackbarHost(hostState = snackbarHostState) { data ->
                Snackbar(
                    snackbarData = data,
                    containerColor = Color(0xFFB71C1C),
                    contentColor = Color.White,
                    modifier = Modifier.padding(16.dp)
                )
            }
        }
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
            when (phase) {

                // ── Screen 1: Classification ─────────────────
                WizardPhase.CLASSIFY -> ClassificationScreen(
                    onCategorySelected = { category ->
                        tool = Tool(category = category, isAssembly = category.isAssembly)
                        phase = WizardPhase.IDENTITY
                    },
                    onCancel = { onCancelled() }
                )

                // ── Screen 2: Identity ───────────────────────
                WizardPhase.IDENTITY -> IdentityEntryScreen(
                    category = tool.category,
                    initialEdp = edp,
                    initialManufacturer = manufacturer,
                    initialMpnIso = mpnIso,
                    initialName = toolName,
                    onScanLabel = {
                        ocrImagePath = ""
                        ocrElements = emptyList()
                        ocrProcessing = false
                        ocrError = null
                        ocrMatchResult = null
                        phase = WizardPhase.OCR_CAPTURE
                    },
                    onNext = { e, m, mi, n ->
                        edp = e; manufacturer = m; mpnIso = mi; toolName = n
                        phase = WizardPhase.SPECS
                    },
                    onBack = { phase = WizardPhase.CLASSIFY },
                    onCancel = { requestCancel() }
                )

                // ── Screen 2a: OCR Camera ────────────────────
                WizardPhase.OCR_CAPTURE -> {
                    // Reuse CaptureStepScreen with minimal params
                    CaptureStepScreen(
                        field = com.toolsnap.core.model.CaptureField.TOOL_DATA,
                        stepIndex = 1,
                        totalSteps = 5,
                        onPhotoCaptured = { path ->
                            scope.launch {
                                val norm = withContext(Dispatchers.IO) {
                                    ImageUtils.normalizeOrientation(path)
                                }
                                ocrImagePath = norm
                                ocrProcessing = true
                                ocrError = null
                                ocrElements = emptyList()
                                phase = WizardPhase.OCR_PICK

                                // Run OCR in background
                                scope.launch {
                                    try {
                                        val result = withContext(Dispatchers.IO) {
                                            OcrProcessor.extractText(
                                                context, File(norm)
                                            )
                                        }
                                        if (result.isFailed) {
                                            ocrError = result.error
                                        } else {
                                            ocrElements = result.elements
                                            // Run field matcher for auto-populate
                                            ocrMatchResult = OcrFieldMatcher.classify(
                                                result.elements, tool.category
                                            )
                                        }
                                    } catch (e: Exception) {
                                        ocrError = "Text recognition failed"
                                    } finally {
                                        ocrProcessing = false
                                    }
                                }
                            }
                        },
                        onSkip = { phase = WizardPhase.IDENTITY },
                        canSkip = true,
                        onBack = { phase = WizardPhase.IDENTITY },
                        onCancel = { requestCancel() }
                    )
                }

                // ── Screen 2b: OCR Chip Picker ───────────────
                WizardPhase.OCR_PICK -> IdentityOcrPickerScreen(
                    imagePath = ocrImagePath,
                    elements = ocrElements,
                    isProcessing = ocrProcessing,
                    ocrError = ocrError,
                    category = tool.category,
                    matchResult = ocrMatchResult,
                    initialEdp = edp,
                    initialManufacturer = manufacturer,
                    initialMpnIso = mpnIso,
                    onConfirm = { e, m, mi ->
                        edp = e; manufacturer = m; mpnIso = mi
                        phase = WizardPhase.IDENTITY
                    },
                    onRetake = {
                        ocrImagePath = ""
                        ocrElements = emptyList()
                        ocrProcessing = false
                        ocrError = null
                        ocrMatchResult = null
                        phase = WizardPhase.OCR_CAPTURE
                    },
                    onCancel = { phase = WizardPhase.IDENTITY }
                )

                // ── Screen 3: Specifications ─────────────────
                WizardPhase.SPECS -> SpecificationsScreen(
                    category = tool.category,
                    mpnIso = mpnIso,
                    existingValues = specValues,
                    onNext = { values ->
                        specValues = values
                        phase = if (tool.category.isAssembly)
                            WizardPhase.LINK_COMPONENTS
                        else
                            WizardPhase.PHOTO_SAVE
                    },
                    onBack = { phase = WizardPhase.IDENTITY },
                    onCancel = { requestCancel() }
                )

                // ── Screen 4: Component Linking (conditional) ─
                WizardPhase.LINK_COMPONENTS -> {
                    if (existingTools.isEmpty()) {
                        scope.launch {
                            existingTools = withContext(Dispatchers.IO) {
                                // Load all tools from existing session folders
                                FileUtils.listSessionDirs(context).flatMap { dir ->
                                    ManifestV3.readManifest(dir)?.tools ?: emptyList()
                                }.filter { !it.isAssembly }
                            }
                        }
                    }
                    ComponentLinkScreen(
                        parentCategoryName = tool.category.displayName,
                        existingComponents = emptyList(),
                        existingTools = existingTools,
                        onDone = { pendingComps ->
                            componentLinks = pendingComps.map { pc ->
                                ComponentLink(
                                    parentToolId = tool.toolId,
                                    childToolId = pc.tool.toolId,
                                    role = pc.role,
                                    quantity = pc.quantity,
                                    notes = pc.notes
                                )
                            }
                            phase = WizardPhase.PHOTO_SAVE
                        },
                        onCancel = { phase = WizardPhase.SPECS }
                    )
                }

                // ── Screen 5: Photo + Save ───────────────────
                WizardPhase.PHOTO_SAVE -> PhotoSaveScreen(
                    toolSummary = when {
                        toolName.isNotBlank() -> toolName
                        tool.category == ToolCategory.INSERT && mpnIso.isNotBlank() ->
                            "$manufacturer $mpnIso".trim()
                        else -> "$manufacturer $edp".trim()
                    },
                    isSaving = isSaving,
                    onSave = { photoPath -> saveTool(photoPath) },
                    onBack = {
                        phase = if (tool.category.isAssembly)
                            WizardPhase.LINK_COMPONENTS
                        else
                            WizardPhase.SPECS
                    },
                    onCancel = { requestCancel() }
                )
            }

            if (isSaving) WizardLoadingOverlay(message = "Saving tool…")
        }
    }

    // — Abandon confirmation dialog ——————————————————
    if (activeDialog == ConfirmDialog.ABANDON) {
        WizardConfirmationDialog(
            title = "CANCEL ENTRY?",
            message = "Discard this tool entry? No data has been saved yet.",
            confirmLabel = "DISCARD",
            dismissLabel = "KEEP WORKING",
            onConfirm = {
                activeDialog = ConfirmDialog.NONE
                onCancelled()
            },
            onDismiss = { activeDialog = ConfirmDialog.NONE }
        )
    }
}
