package com.toolsnap.ui.wizard

import android.Manifest
import android.content.pm.PackageManager
import android.util.Log
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.toolsnap.ui.theme.ShopFloor
import java.io.File
import java.util.concurrent.Executors

/**
 * Screen 5 — Capture a photo and save the tool.
 *
 * Flow:
 *   1. Camera viewfinder with CAPTURE button
 *   2. After capture: shows preview with RETAKE / SAVE
 *   3. SAVE calls onSave with the photo path
 *
 * Photo is optional — SKIP & SAVE allows saving without a photo.
 */
@Composable
fun PhotoSaveScreen(
    toolSummary: String,
    isSaving: Boolean = false,
    onSave: (photoPath: String?) -> Unit,
    onBack: () -> Unit,
    onCancel: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasCameraPermission = granted
    }

    LaunchedEffect(Unit) {
        if (!hasCameraPermission) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    val imageCapture = remember { ImageCapture.Builder().build() }
    val cameraExecutor = remember { Executors.newSingleThreadExecutor() }

    var capturedPath by remember { mutableStateOf<String?>(null) }
    var capturedBitmap by remember { mutableStateOf<android.graphics.Bitmap?>(null) }

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
                    text = "STEP 5 OF 5",
                    fontSize = ShopFloor.LabelSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText.copy(alpha = 0.8f)
                )
                Text(
                    text = "PHOTO & SAVE",
                    fontSize = ShopFloor.HeadlineSize,
                    fontWeight = FontWeight.Bold,
                    color = ShopFloor.StepText
                )
                Text(
                    text = toolSummary,
                    fontSize = ShopFloor.TitleSize,
                    color = ShopFloor.StepText.copy(alpha = 0.7f),
                    maxLines = 1
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
                text = if (capturedPath == null)
                    "Take a photo of the tool, label, or packaging"
                else
                    "Review the photo — SAVE to finish or RETAKE",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Camera or preview
        if (capturedPath == null) {
            // Live camera viewfinder
            if (hasCameraPermission) {
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                ) {
                    AndroidView(
                        factory = { ctx ->
                            PreviewView(ctx).also { previewView ->
                                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                                cameraProviderFuture.addListener({
                                    val cameraProvider = cameraProviderFuture.get()
                                    val preview = Preview.Builder().build().also {
                                        it.setSurfaceProvider(previewView.surfaceProvider)
                                    }
                                    try {
                                        cameraProvider.unbindAll()
                                        cameraProvider.bindToLifecycle(
                                            lifecycleOwner,
                                            CameraSelector.DEFAULT_BACK_CAMERA,
                                            preview,
                                            imageCapture
                                        )
                                    } catch (e: Exception) {
                                        Log.e("PhotoSave", "Camera bind failed", e)
                                    }
                                }, ContextCompat.getMainExecutor(ctx))
                            }
                        },
                        modifier = Modifier.fillMaxSize()
                    )
                }
            } else {
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.surfaceVariant),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "CAMERA PERMISSION REQUIRED",
                        fontSize = ShopFloor.TitleSize,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Camera buttons
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(ShopFloor.ScreenPadding),
                horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
            ) {
                Button(
                    onClick = onBack,
                    modifier = Modifier
                        .weight(1f)
                        .height(ShopFloor.ButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("BACK", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                }

                // CAPTURE
                Button(
                    onClick = {
                        val outputFile = File(
                            context.cacheDir,
                            "capture_tool_${System.currentTimeMillis()}.jpg"
                        )
                        val outputOptions = ImageCapture.OutputFileOptions.Builder(outputFile).build()
                        imageCapture.takePicture(
                            outputOptions,
                            cameraExecutor,
                            object : ImageCapture.OnImageSavedCallback {
                                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                                    capturedPath = outputFile.absolutePath
                                    try {
                                        capturedBitmap = android.graphics.BitmapFactory
                                            .decodeFile(outputFile.absolutePath)
                                    } catch (_: Exception) { }
                                }
                                override fun onError(exception: ImageCaptureException) {
                                    Log.e("PhotoSave", "Capture failed", exception)
                                }
                            }
                        )
                    },
                    modifier = Modifier
                        .weight(2f)
                        .height(ShopFloor.ButtonHeight),
                    enabled = hasCameraPermission,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.PrimaryButton,
                        contentColor = ShopFloor.PrimaryButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(28.dp))
                    Spacer(Modifier.size(8.dp))
                    Text("CAPTURE", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                }
            }

            // SKIP & SAVE (no photo)
            Button(
                onClick = { onSave(null) },
                enabled = !isSaving,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = ShopFloor.ScreenPadding)
                    .height(ShopFloor.SmallButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF616161),
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("SKIP PHOTO & SAVE", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
            }

        } else {
            // Photo preview
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .background(Color.Black),
                contentAlignment = Alignment.Center
            ) {
                capturedBitmap?.let { bmp ->
                    Image(
                        bitmap = bmp.asImageBitmap(),
                        contentDescription = "Captured photo",
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )
                }
            }

            // RETAKE / SAVE buttons
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(ShopFloor.ScreenPadding),
                horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
            ) {
                Button(
                    onClick = {
                        capturedPath = null
                        capturedBitmap = null
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(ShopFloor.ButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(28.dp))
                    Spacer(Modifier.size(8.dp))
                    Text("RETAKE", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                }

                Button(
                    onClick = { onSave(capturedPath) },
                    enabled = !isSaving,
                    modifier = Modifier
                        .weight(1f)
                        .height(ShopFloor.ButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SuccessButton,
                        contentColor = ShopFloor.SuccessButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    if (isSaving) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp),
                            color = Color.White,
                            strokeWidth = 3.dp
                        )
                    } else {
                        Icon(Icons.Default.Check, null, modifier = Modifier.size(28.dp))
                        Spacer(Modifier.size(8.dp))
                        Text("SAVE", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        // Cancel — always at bottom
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
            Text("CANCEL ENTRY", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
        }
    }
}
