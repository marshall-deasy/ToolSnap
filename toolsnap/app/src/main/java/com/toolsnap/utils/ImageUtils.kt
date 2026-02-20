package com.toolsnap.utils

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.util.Log
import androidx.exifinterface.media.ExifInterface
import com.toolsnap.config.CaptureConfig
import java.io.File
import java.io.FileOutputStream

private const val TAG = "ImageUtils"

/**
 * Image processing utilities for captured photos.
 *
 * Handles rotation correction, downscaling, and JPEG compression.
 * All image saving in the app goes through [saveAndCompress].
 */
object ImageUtils {

    /**
     * Result of a save operation with error detail for the UI.
     */
    sealed class SaveResult {
        data object Success : SaveResult()
        data class Failure(val reason: String) : SaveResult()

        val isSuccess: Boolean get() = this is Success
    }

    /**
     * Save a photo from its raw file path to the destination,
     * applying rotation correction, downscaling, and compression.
     *
     * Returns a [SaveResult] with a human-readable error message
     * if the save failed, so the UI can show it.
     *
     * @param sourcePath  path to the raw image from CameraX
     * @param destFile    target file (e.g. <session_dir>/body.jpg)
     */
    fun saveAndCompress(sourcePath: String, destFile: File): SaveResult {
        return try {
            val sourceFile = File(sourcePath)
            if (!sourceFile.exists()) {
                return SaveResult.Failure("Source image not found")
            }

            val bitmap = decodeSampled(sourcePath)
                ?: return SaveResult.Failure("Could not decode image")

            val rotated = applyExifRotation(bitmap, sourcePath)
            val scaled = scaleDown(rotated, CaptureConfig.MAX_IMAGE_DIMENSION)

            // Ensure parent directory exists
            destFile.parentFile?.mkdirs()

            FileOutputStream(destFile).use { out ->
                scaled.compress(Bitmap.CompressFormat.JPEG, CaptureConfig.JPEG_QUALITY, out)
                out.fd.sync()  // force flush to disk
            }

            // Verify the write actually landed
            if (!destFile.exists() || destFile.length() == 0L) {
                return SaveResult.Failure("Image file is empty after save — storage may be full")
            }

            // Recycle intermediate bitmaps if they're different objects
            if (rotated !== bitmap) bitmap.recycle()
            if (scaled !== rotated) rotated.recycle()
            scaled.recycle()

            SaveResult.Success
        } catch (e: java.io.IOException) {
            Log.e(TAG, "I/O error saving image: ${e.message}", e)
            SaveResult.Failure("Storage error — check available space")
        } catch (e: OutOfMemoryError) {
            Log.e(TAG, "OOM saving image", e)
            SaveResult.Failure("Image too large to process")
        } catch (e: Exception) {
            Log.e(TAG, "Unexpected error saving image: ${e.message}", e)
            SaveResult.Failure("Photo save failed: ${e.message}")
        }
    }

    /**
     * Legacy boolean wrapper for backward compatibility.
     * Prefer [saveAndCompress] with SaveResult for new code.
     */
    fun saveAndCompressLegacy(sourcePath: String, destFile: File): Boolean {
        return saveAndCompress(sourcePath, destFile).isSuccess
    }

    /**
     * Normalize image orientation by applying EXIF rotation and saving
     * the corrected file. After this call, the file's pixel data matches
     * how the image should be displayed — no EXIF rotation tag needed.
     *
     * Used by the crop screen so that crop coordinates map directly
     * to the visible image without orientation mismatch.
     *
     * @param imagePath  path to the image file to normalize
     * @return path to the normalized file (same path if already correct,
     *         or a new temp file if rotation was applied)
     */
    fun normalizeOrientation(imagePath: String): String {
        return try {
            val exif = ExifInterface(imagePath)
            val orientation = exif.getAttributeInt(
                ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL
            )

            // No rotation needed
            if (orientation == ExifInterface.ORIENTATION_NORMAL ||
                orientation == ExifInterface.ORIENTATION_UNDEFINED ||
                orientation == 0) {
                return imagePath
            }

            val bitmap = BitmapFactory.decodeFile(imagePath) ?: return imagePath
            val rotated = applyExifRotation(bitmap, imagePath)

            // If no rotation was applied, return original
            if (rotated === bitmap) {
                bitmap.recycle()
                return imagePath
            }

            // Save rotated image to a new file with no EXIF rotation
            val normalizedFile = File(
                File(imagePath).parent,
                "norm_${System.currentTimeMillis()}.jpg"
            )
            FileOutputStream(normalizedFile).use { out ->
                rotated.compress(Bitmap.CompressFormat.JPEG, 95, out)
            }

            // Set EXIF orientation to normal on the new file
            val newExif = ExifInterface(normalizedFile.absolutePath)
            newExif.setAttribute(
                ExifInterface.TAG_ORIENTATION,
                ExifInterface.ORIENTATION_NORMAL.toString()
            )
            newExif.saveAttributes()

            bitmap.recycle()
            rotated.recycle()

            normalizedFile.absolutePath
        } catch (e: Exception) {
            Log.e(TAG, "Failed to normalize orientation: ${e.message}", e)
            imagePath
        }
    }

    /**
     * Decode a bitmap with inSampleSize to avoid OOM on large camera images.
     */
    private fun decodeSampled(path: String): Bitmap? {
        // First pass: get dimensions only
        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(path, options)

        // Calculate sample size
        options.inSampleSize = calculateSampleSize(
            options.outWidth, options.outHeight, CaptureConfig.MAX_IMAGE_DIMENSION
        )
        options.inJustDecodeBounds = false

        return BitmapFactory.decodeFile(path, options)
    }

    /**
     * Calculate the largest inSampleSize (power of 2) that keeps both
     * dimensions above the target size.
     */
    private fun calculateSampleSize(width: Int, height: Int, target: Int): Int {
        var sample = 1
        var w = width
        var h = height
        while (w / 2 >= target && h / 2 >= target) {
            sample *= 2
            w /= 2
            h /= 2
        }
        return sample
    }

    /**
     * Read EXIF orientation and rotate the bitmap accordingly.
     * Camera images are often stored rotated with an EXIF tag.
     */
    private fun applyExifRotation(bitmap: Bitmap, path: String): Bitmap {
        val exif = ExifInterface(path)
        val orientation = exif.getAttributeInt(
            ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL
        )

        val degrees = when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> return bitmap
        }

        val matrix = Matrix().apply { postRotate(degrees) }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    /**
     * Scale a bitmap so its longest edge is at most [maxDimension].
     * Returns the same bitmap if already within bounds.
     */
    private fun scaleDown(bitmap: Bitmap, maxDimension: Int): Bitmap {
        val longestEdge = maxOf(bitmap.width, bitmap.height)
        if (longestEdge <= maxDimension) return bitmap

        val scale = maxDimension.toFloat() / longestEdge
        val newWidth = (bitmap.width * scale).toInt()
        val newHeight = (bitmap.height * scale).toInt()

        return Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
    }
}
