package com.toolsnap.ui.detail

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Snackbar
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.toolsnap.config.CaptureConfig
import com.toolsnap.core.ocr.OcrProcessor
import com.toolsnap.core.session.SessionManager
import com.toolsnap.ui.theme.ShopFloor
import com.toolsnap.ui.wizard.CaptureStepScreen
import com.toolsnap.ui.wizard.CropScreen
import com.toolsnap.ui.wizard.DataEntryChoiceScreen
import com.toolsnap.ui.wizard.ManualEntryScreen
import com.toolsnap.ui.wizard.OcrReviewScreen
import com.toolsnap.ui.wizard.PhotoReviewScreen
import com.toolsnap.utils.ImageUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Single-field edit flow. Launched from SessionDetailScreen when the
 * user taps the edit pencil on any field card.
 *
 * Loads the existing session, resets the target field, then runs the
 * same capture/entry screens the wizard uses. On completion (or
 * cancellation), saves and returns to the detail screen.
 *
 * Reuses: CaptureStepScreen, PhotoReviewScreen, CropScreen,
 *         DataEntryChoiceScreen, ManualEntryScreen, OcrReviewScreen.
 */

private enum class EditPhase {
    LOADING,         // activating session from disk
    DATA_CHOICE,     // three-way choice (OCR fields only)
    MANUAL_ENTRY,    // structured form
    CAPTURE,         // camera
    PHOTO_REVIEW,    // review taken photo
    CROP,            // crop
    OCR_REVIEW,      // review extracted text
}

@Composable
fun FieldEditNavHost(
    folderName: String,
    fieldIndex: Int,
    onDone: () -> Unit,
    onCancelled: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val sessionManager = remember { SessionManager(context) }
    val fields = CaptureConfig.wizardFields
    val snackbarHostState = remember { SnackbarHostState() }

    // Validate field index
    if (fieldIndex !in fields.indices) {
        LaunchedEffect(Unit) { onCancelled() }
        return
    }

    val field = fields[fieldIndex]

    var phase by remember { mutableStateOf(EditPhase.LOADING) }

    // Photo state
    var reviewImagePath by remember { mutableStateOf("") }
    var finalImagePath by remember { mutableStateOf("") }

    // OCR state
    var ocrExtractedText by remember { mutableStateOf("") }
    var ocrProcessing by remember { mutableStateOf(false) }
    var ocrError by remember { mutableStateOf<String?>(null) }

    // Processing state
    var isSaving by remember { mutableStateOf(false) }
    var loadingMessage by remember { mutableStateOf("") }

    // Cancel confirmation
    var showCancelDialog by remember { mutableStateOf(false) }

    fun showError(message: String) {
        scope.launch { snackbarHostState.showSnackbar(message) }
    }

    fun showLoading(message: String) {
        loadingMessage = message
        isSaving = true
    }

    fun hideLoading() {
        isSaving = false
        loadingMessage = ""
    }

    /** Return to the field's entry point phase. */
    fun entryPhase(): EditPhase {
        return if (field.requiresOcr) EditPhase.DATA_CHOICE
               else EditPhase.CAPTURE
    }

    // Load and activate session on first composition
    LaunchedEffect(folderName) {
        val session = withContext(Dispatchers.IO) {
            sessionManager.loadAndActivateSession(folderName)
        }
        if (session == null) {
            onCancelled()
            return@LaunchedEffect
        }
        // Don't reset yet — preserve original data in case user cancels.
        // The capture screens work fine with or without existing data.
        // Reset happens implicitly when savePhoto/saveFormData overwrites.
        phase = entryPhase()
    }

    // ---- Back handling ----
    BackHandler(enabled = phase != EditPhase.LOADING) {
        if (isSaving) return@BackHandler
        when (phase) {
            EditPhase.LOADING -> { /* unreachable */ }
            EditPhase.CAPTURE, EditPhase.DATA_CHOICE -> {
                showCancelDialog = true
            }
            EditPhase.MANUAL_ENTRY -> phase = EditPhase.DATA_CHOICE
            EditPhase.PHOTO_REVIEW -> phase = EditPhase.CAPTURE
            EditPhase.CROP -> phase = EditPhase.PHOTO_REVIEW
            EditPhase.OCR_REVIEW -> phase = entryPhase()
        }
    }

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
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (phase) {
                EditPhase.LOADING -> {
                    Box(
                        Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(48.dp)
                            )
                            Spacer(Modifier.height(12.dp))
                            Text(
                                "Loading session…",
                                fontSize = ShopFloor.BodySize
                            )
                        }
                    }
                }

                EditPhase.DATA_CHOICE -> {
                    DataEntryChoiceScreen(
                        field = field,
                        stepIndex = fieldIndex,
                        totalSteps = fields.size,
                        onManualEntry = {
                            phase = EditPhase.MANUAL_ENTRY
                        },
                        onPhotoOcr = { phase = EditPhase.CAPTURE },
                        onSkip = {
                            sessionManager.skipField(field)
                            sessionManager.persistForEdit()
                            onDone()
                        }
                    )
                }

                EditPhase.MANUAL_ENTRY -> {
                    val category = sessionManager.activeToolCategory
                    val formFields = if (category != null)
                        com.toolsnap.config.ComponentTemplates.fieldsFor(category)
                    else emptyList()
                    ManualEntryScreen(
                        formFields = formFields,
                        title = category?.displayName ?: field.displayName,
                        existingValues = sessionManager.activeSession
                            ?.formDataMap?.get(field)?.values ?: emptyMap(),
                        onSave = { attrs ->
                            sessionManager.saveToolAttributes(field, attrs)
                            sessionManager.persistForEdit()
                            onDone()
                        },
                        onCancel = { phase = EditPhase.DATA_CHOICE }
                    )
                }

                EditPhase.CAPTURE -> {
                    CaptureStepScreen(
                        field = field,
                        stepIndex = fieldIndex,
                        totalSteps = fields.size,
                        onPhotoCaptured = { path ->
                            showLoading("Processing photo…")
                            scope.launch {
                                val normalized = withContext(Dispatchers.IO) {
                                    ImageUtils.normalizeOrientation(path)
                                }
                                hideLoading()
                                reviewImagePath = normalized
                                finalImagePath = normalized
                                phase = EditPhase.PHOTO_REVIEW
                            }
                        },
                        onSkip = {
                            sessionManager.skipField(field)
                            sessionManager.persistForEdit()
                            onDone()
                        }
                    )
                }

                EditPhase.PHOTO_REVIEW -> {
                    PhotoReviewScreen(
                        field = field,
                        imagePath = reviewImagePath,
                        onUse = {
                            finalImagePath = reviewImagePath
                            phase = EditPhase.CROP
                        },
                        onRetake = { phase = EditPhase.CAPTURE }
                    )
                }

                EditPhase.CROP -> {
                    fun onPostCrop(imagePath: String) {
                        if (isSaving) return
                        showLoading("Saving photo…")

                        val result = sessionManager.savePhotoWithResult(
                            field, imagePath
                        )
                        when (result) {
                            is SessionManager.PhotoSaveResult.Success -> {
                                if (field.requiresOcr) {
                                    loadingMessage =
                                        "Running text recognition…"
                                    ocrExtractedText = ""
                                    ocrError = null
                                    ocrProcessing = true
                                    phase = EditPhase.OCR_REVIEW
                                } else {
                                    hideLoading()
                                    sessionManager.persistForEdit()
                                    onDone()
                                }
                            }
                            is SessionManager.PhotoSaveResult.Failure -> {
                                hideLoading()
                                showError(result.message)
                                phase = EditPhase.CAPTURE
                            }
                        }
                    }

                    CropScreen(
                        field = field,
                        imagePath = finalImagePath,
                        onCropped = { croppedPath ->
                            finalImagePath = croppedPath
                            onPostCrop(croppedPath)
                        },
                        onSkipCrop = { onPostCrop(finalImagePath) }
                    )
                }

                EditPhase.OCR_REVIEW -> {
                    if (ocrProcessing && ocrExtractedText.isEmpty()
                        && ocrError == null
                    ) {
                        scope.launch {
                            try {
                                val savedPath = sessionManager.activeSession
                                    ?.imagePaths?.get(field) ?: finalImagePath
                                val imageFile = java.io.File(savedPath)

                                val result = withContext(Dispatchers.IO) {
                                    OcrProcessor.extractText(
                                        context, imageFile
                                    )
                                }

                                if (result.isFailed) {
                                    ocrError = result.error
                                    ocrProcessing = false
                                    hideLoading()
                                    showError(
                                        result.error ?: "OCR failed"
                                    )
                                } else {
                                    ocrExtractedText = result.rawText
                                    ocrProcessing = false
                                    ocrError = null
                                    hideLoading()
                                    sessionManager.markOcrNeedsReview(
                                        field, result.rawText
                                    )
                                }
                            } catch (e: Exception) {
                                ocrError =
                                    "Text recognition crashed — " +
                                    "try retaking"
                                ocrProcessing = false
                                hideLoading()
                                showError(ocrError!!)
                            }
                        }
                    }

                    OcrReviewScreen(
                        field = field,
                        imagePath = finalImagePath,
                        extractedText = ocrExtractedText,
                        isProcessing = ocrProcessing,
                        onConfirm = { editedText ->
                            sessionManager.saveOcrResult(field, editedText)
                            sessionManager.persistForEdit()
                            onDone()
                        },
                        onRetake = {
                            sessionManager.resetField(field)
                            ocrError = null
                            phase = entryPhase()
                        }
                    )
                }
            }

            // Loading overlay
            if (isSaving) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.6f)),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(64.dp),
                            color = Color.White,
                            strokeWidth = 5.dp
                        )
                        if (loadingMessage.isNotBlank()) {
                            Spacer(Modifier.height(16.dp))
                            Text(
                                text = loadingMessage,
                                color = Color.White,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Medium,
                                textAlign = TextAlign.Center
                            )
                        }
                    }
                }
            }
        }
    }

    // Cancel confirmation
    if (showCancelDialog) {
        AlertDialog(
            onDismissRequest = { showCancelDialog = false },
            title = {
                Text(
                    "CANCEL EDIT?",
                    fontSize = ShopFloor.TitleSize,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Text(
                    "Discard changes to ${field.displayName}?",
                    fontSize = ShopFloor.BodySize
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        showCancelDialog = false
                        // Original data is preserved — we never reset
                        // until the user completes a new capture.
                        onCancelled()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.DangerButton,
                        contentColor = ShopFloor.DangerButtonText
                    )
                ) {
                    Text("DISCARD", fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                Button(
                    onClick = { showCancelDialog = false },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    )
                ) {
                    Text("KEEP EDITING", fontWeight = FontWeight.Bold)
                }
            }
        )
    }
}
