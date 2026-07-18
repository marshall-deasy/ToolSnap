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
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.toolsnap.core.model.CaptureField
import com.toolsnap.ui.theme.ShopFloor
import java.io.File
import java.util.concurrent.Executors

/**
 * Camera capture screen for a single wizard field.
 * Shop-floor sized buttons, clear instructions, high-contrast UI.
 */
@Composable
fun CaptureStepScreen(
    field: CaptureField,
    stepIndex: Int,
    totalSteps: Int,
    onPhotoCaptured: (imagePath: String) -> Unit,
    onSkip: () -> Unit,
    canSkip: Boolean = true,
    onBack: (() -> Unit)? = null,
    onCancel: (() -> Unit)? = null
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

    Column(modifier = Modifier.fillMaxSize()) {
        // Step indicator + field name — high contrast header
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Text(
                text = "STEP ${stepIndex + 1} OF $totalSteps",
                fontSize = ShopFloor.LabelSize,
                fontWeight = FontWeight.Bold,
                color = ShopFloor.StepText.copy(alpha = 0.8f)
            )
            Text(
                text = field.displayName,
                fontSize = ShopFloor.HeadlineSize,
                fontWeight = FontWeight.Bold,
                color = ShopFloor.StepText
            )
        }

        // Instruction bar — yellow background for visibility
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.InstructionBackground)
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 12.dp)
        ) {
            Text(
                text = field.instruction,
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Camera viewfinder
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
                                    Log.e("CaptureStep", "Camera bind failed", e)
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

        // Action buttons — big, high contrast
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
        ) {
            // BACK
            if (onBack != null) {
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
                    Icon(
                        Icons.Default.SkipNext,
                        contentDescription = null,
                        modifier = Modifier.size(28.dp)
                    )
                    Spacer(Modifier.size(8.dp))
                    Text(
                        "BACK",
                        fontSize = ShopFloor.ButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // SKIP (only when allowed)
            if (canSkip) {
                Button(
                    onClick = onSkip,
                    modifier = Modifier
                        .weight(1f)
                        .height(ShopFloor.ButtonHeight),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ShopFloor.SecondaryButton,
                        contentColor = ShopFloor.SecondaryButtonText
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(
                        Icons.Default.SkipNext,
                        contentDescription = null,
                        modifier = Modifier.size(28.dp)
                    )
                    Spacer(Modifier.size(8.dp))
                    Text(
                        "SKIP",
                        fontSize = ShopFloor.ButtonTextSize,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // CAPTURE
            Button(
                onClick = {
                    val outputFile = File(
                        context.cacheDir,
                        "capture_${field.fileName}_${System.currentTimeMillis()}.jpg"
                    )
                    val outputOptions = ImageCapture.OutputFileOptions.Builder(outputFile).build()

                    imageCapture.takePicture(
                        outputOptions,
                        cameraExecutor,
                        object : ImageCapture.OnImageSavedCallback {
                            override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                                onPhotoCaptured(outputFile.absolutePath)
                            }

                            override fun onError(exception: ImageCaptureException) {
                                Log.e("CaptureStep", "Capture failed", exception)
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
                Icon(
                    Icons.Default.CameraAlt,
                    contentDescription = null,
                    modifier = Modifier.size(28.dp)
                )
                Spacer(Modifier.size(8.dp))
                Text(
                    "CAPTURE",
                    fontSize = ShopFloor.ButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        // CANCEL row — always visible when onCancel is provided
        if (onCancel != null) {
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
                    "CANCEL ENTRY",
                    fontSize = ShopFloor.SmallButtonTextSize,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
