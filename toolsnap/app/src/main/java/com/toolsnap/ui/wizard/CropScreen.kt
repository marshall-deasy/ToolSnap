package com.toolsnap.ui.wizard

import android.graphics.BitmapFactory
import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
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
import androidx.compose.material.icons.filled.Crop
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.toolsnap.core.model.CaptureField
import com.toolsnap.ui.theme.ShopFloor
import java.io.File
import java.io.FileOutputStream

/**
 * Crop screen — user drags a selection rectangle over the image.
 * ACCEPT crops to selection, SKIP CROP uses the full image.
 *
 * Crop coordinates are mapped to the actual image bounds within the
 * Fit-scaled container, so the crop works correctly regardless of
 * image orientation or aspect ratio.
 */
@Composable
fun CropScreen(
    field: CaptureField,
    imagePath: String,
    onCropped: (croppedPath: String) -> Unit,
    onSkipCrop: () -> Unit
) {
    val context = LocalContext.current

    // Load image dimensions once to calculate aspect ratio
    val imageSize = remember(imagePath) {
        val opts = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(imagePath, opts)
        Pair(opts.outWidth.toFloat(), opts.outHeight.toFloat())
    }
    val imgW = imageSize.first
    val imgH = imageSize.second

    // Container size in pixels
    var containerWidth by remember { mutableFloatStateOf(1f) }
    var containerHeight by remember { mutableFloatStateOf(1f) }

    // Computed image bounds within the container (after Fit scaling)
    var imgOffsetX by remember { mutableFloatStateOf(0f) }
    var imgOffsetY by remember { mutableFloatStateOf(0f) }
    var imgDisplayW by remember { mutableFloatStateOf(1f) }
    var imgDisplayH by remember { mutableFloatStateOf(1f) }

    // Crop rectangle in PIXEL coordinates relative to the container
    var cropLeft by remember { mutableFloatStateOf(-1f) }
    var cropTop by remember { mutableFloatStateOf(-1f) }
    var cropRight by remember { mutableFloatStateOf(-1f) }
    var cropBottom by remember { mutableFloatStateOf(-1f) }

    var dragMode by remember { mutableStateOf("none") }

    // Recalculate image bounds when container size changes
    fun recalcImageBounds() {
        if (containerWidth <= 0 || containerHeight <= 0 || imgW <= 0 || imgH <= 0) return

        val scaleX = containerWidth / imgW
        val scaleY = containerHeight / imgH
        val scale = minOf(scaleX, scaleY)

        imgDisplayW = imgW * scale
        imgDisplayH = imgH * scale
        imgOffsetX = (containerWidth - imgDisplayW) / 2f
        imgOffsetY = (containerHeight - imgDisplayH) / 2f

        // Initialize crop to 15% inset from image edges if not yet set
        if (cropLeft < 0) {
            val inset = 0.15f
            cropLeft = imgOffsetX + imgDisplayW * inset
            cropTop = imgOffsetY + imgDisplayH * inset
            cropRight = imgOffsetX + imgDisplayW * (1f - inset)
            cropBottom = imgOffsetY + imgDisplayH * (1f - inset)
        }
    }

    // Clamp crop coordinates to stay within the image bounds
    fun clampToImage() {
        val minSize = 30f
        cropLeft = cropLeft.coerceIn(imgOffsetX, cropRight - minSize)
        cropTop = cropTop.coerceIn(imgOffsetY, cropBottom - minSize)
        cropRight = cropRight.coerceIn(cropLeft + minSize, imgOffsetX + imgDisplayW)
        cropBottom = cropBottom.coerceIn(cropTop + minSize, imgOffsetY + imgDisplayH)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        // Header
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.StepBackground)
                .padding(ShopFloor.ScreenPadding)
        ) {
            Text(
                text = "Crop: ${field.displayName}",
                fontSize = ShopFloor.TitleSize,
                fontWeight = FontWeight.Bold,
                color = ShopFloor.StepText
            )
        }

        // Instruction
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(ShopFloor.InstructionBackground)
                .padding(horizontal = ShopFloor.ScreenPadding, vertical = 12.dp)
        ) {
            Text(
                text = "Drag to adjust the crop area, then tap ACCEPT",
                fontSize = ShopFloor.InstructionSize,
                color = ShopFloor.InstructionText,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Image with crop overlay
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(8.dp)
                .onGloballyPositioned { coords ->
                    containerWidth = coords.size.width.toFloat()
                    containerHeight = coords.size.height.toFloat()
                    recalcImageBounds()
                }
                .pointerInput(Unit) {
                    detectDragGestures(
                        onDragStart = { offset ->
                            val cornerThreshold = 60f

                            dragMode = when {
                                kotlin.math.abs(offset.x - cropLeft) < cornerThreshold &&
                                    kotlin.math.abs(offset.y - cropTop) < cornerThreshold -> "tl"
                                kotlin.math.abs(offset.x - cropRight) < cornerThreshold &&
                                    kotlin.math.abs(offset.y - cropTop) < cornerThreshold -> "tr"
                                kotlin.math.abs(offset.x - cropLeft) < cornerThreshold &&
                                    kotlin.math.abs(offset.y - cropBottom) < cornerThreshold -> "bl"
                                kotlin.math.abs(offset.x - cropRight) < cornerThreshold &&
                                    kotlin.math.abs(offset.y - cropBottom) < cornerThreshold -> "br"
                                offset.x in cropLeft..cropRight &&
                                    offset.y in cropTop..cropBottom -> "move"
                                else -> "none"
                            }
                        },
                        onDrag = { change, dragAmount ->
                            change.consume()
                            val dx = dragAmount.x
                            val dy = dragAmount.y

                            when (dragMode) {
                                "move" -> {
                                    val w = cropRight - cropLeft
                                    val h = cropBottom - cropTop
                                    val newLeft = (cropLeft + dx).coerceIn(imgOffsetX, imgOffsetX + imgDisplayW - w)
                                    val newTop = (cropTop + dy).coerceIn(imgOffsetY, imgOffsetY + imgDisplayH - h)
                                    cropLeft = newLeft
                                    cropTop = newTop
                                    cropRight = newLeft + w
                                    cropBottom = newTop + h
                                }
                                "tl" -> { cropLeft += dx; cropTop += dy; clampToImage() }
                                "tr" -> { cropRight += dx; cropTop += dy; clampToImage() }
                                "bl" -> { cropLeft += dx; cropBottom += dy; clampToImage() }
                                "br" -> { cropRight += dx; cropBottom += dy; clampToImage() }
                            }
                        }
                    )
                },
            contentAlignment = Alignment.Center
        ) {
            // Background image
            Image(
                painter = rememberAsyncImagePainter(File(imagePath)),
                contentDescription = "${field.displayName} photo",
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Fit
            )

            // Crop overlay
            Canvas(modifier = Modifier.fillMaxSize()) {
                if (cropLeft < 0) return@Canvas

                // Dim outside crop area
                drawRect(color = Color.Black.copy(alpha = 0.5f), topLeft = Offset.Zero, size = Size(size.width, cropTop))
                drawRect(color = Color.Black.copy(alpha = 0.5f), topLeft = Offset(0f, cropBottom), size = Size(size.width, size.height - cropBottom))
                drawRect(color = Color.Black.copy(alpha = 0.5f), topLeft = Offset(0f, cropTop), size = Size(cropLeft, cropBottom - cropTop))
                drawRect(color = Color.Black.copy(alpha = 0.5f), topLeft = Offset(cropRight, cropTop), size = Size(size.width - cropRight, cropBottom - cropTop))

                // Crop rectangle border
                drawRect(
                    color = Color.White,
                    topLeft = Offset(cropLeft, cropTop),
                    size = Size(cropRight - cropLeft, cropBottom - cropTop),
                    style = Stroke(width = 3.dp.toPx())
                )

                // Corner handles — green, big for fat fingers
                val hs = 20.dp.toPx()
                val hc = Color(0xFF4CAF50)
                drawRect(color = hc, topLeft = Offset(cropLeft - hs / 2, cropTop - hs / 2), size = Size(hs, hs))
                drawRect(color = hc, topLeft = Offset(cropRight - hs / 2, cropTop - hs / 2), size = Size(hs, hs))
                drawRect(color = hc, topLeft = Offset(cropLeft - hs / 2, cropBottom - hs / 2), size = Size(hs, hs))
                drawRect(color = hc, topLeft = Offset(cropRight - hs / 2, cropBottom - hs / 2), size = Size(hs, hs))
            }
        }

        // Action buttons
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(ShopFloor.ScreenPadding),
            horizontalArrangement = Arrangement.spacedBy(ShopFloor.ButtonSpacing)
        ) {
            Button(
                onClick = onSkipCrop,
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SecondaryButton,
                    contentColor = ShopFloor.SecondaryButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.SkipNext, null, modifier = Modifier.size(28.dp))
                Spacer(Modifier.size(8.dp))
                Text("SKIP CROP", fontSize = ShopFloor.SmallButtonTextSize, fontWeight = FontWeight.Bold)
            }

            Button(
                onClick = {
                    if (imgDisplayW <= 0 || imgDisplayH <= 0) {
                        onSkipCrop()
                        return@Button
                    }

                    // Map screen crop coords to normalized image coords (0-1)
                    val normLeft = ((cropLeft - imgOffsetX) / imgDisplayW).coerceIn(0f, 1f)
                    val normTop = ((cropTop - imgOffsetY) / imgDisplayH).coerceIn(0f, 1f)
                    val normRight = ((cropRight - imgOffsetX) / imgDisplayW).coerceIn(0f, 1f)
                    val normBottom = ((cropBottom - imgOffsetY) / imgDisplayH).coerceIn(0f, 1f)

                    val bitmap = BitmapFactory.decodeFile(imagePath)
                    if (bitmap != null) {
                        val bmpW = bitmap.width
                        val bmpH = bitmap.height

                        val pixelLeft = (normLeft * bmpW).toInt().coerceIn(0, bmpW - 1)
                        val pixelTop = (normTop * bmpH).toInt().coerceIn(0, bmpH - 1)
                        val pixelRight = (normRight * bmpW).toInt().coerceIn(pixelLeft + 1, bmpW)
                        val pixelBottom = (normBottom * bmpH).toInt().coerceIn(pixelTop + 1, bmpH)

                        val cropWidth = pixelRight - pixelLeft
                        val cropHeight = pixelBottom - pixelTop

                        if (cropWidth > 0 && cropHeight > 0) {
                            val cropped = Bitmap.createBitmap(bitmap, pixelLeft, pixelTop, cropWidth, cropHeight)

                            val croppedFile = File(context.cacheDir, "cropped_${System.currentTimeMillis()}.jpg")
                            FileOutputStream(croppedFile).use { out ->
                                cropped.compress(Bitmap.CompressFormat.JPEG, 95, out)
                            }

                            cropped.recycle()
                            bitmap.recycle()
                            onCropped(croppedFile.absolutePath)
                        } else {
                            bitmap.recycle()
                            onSkipCrop()
                        }
                    } else {
                        onSkipCrop()
                    }
                },
                modifier = Modifier
                    .weight(1f)
                    .height(ShopFloor.ButtonHeight),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ShopFloor.SuccessButton,
                    contentColor = ShopFloor.SuccessButtonText
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Crop, null, modifier = Modifier.size(28.dp))
                Spacer(Modifier.size(8.dp))
                Text("ACCEPT", fontSize = ShopFloor.ButtonTextSize, fontWeight = FontWeight.Bold)
            }
        }
    }
}
