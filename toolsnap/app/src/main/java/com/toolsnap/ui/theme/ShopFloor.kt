package com.toolsnap.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Shop-floor-friendly design constants.
 * Big touch targets, high contrast, clear text.
 *
 * All text fields and dropdowns use [TextFieldMinHeight] so that
 * descenders (g, y, p, q) and labels never get clipped.
 */
object ShopFloor {
    // Button sizing — ham-handed friendly
    val ButtonHeight = 64.dp
    val ButtonMinWidth = 160.dp
    val SmallButtonHeight = 52.dp

    // Font sizes
    val HeadlineSize = 28.sp
    val TitleSize = 22.sp
    val BodySize = 18.sp
    val LabelSize = 16.sp
    val ButtonTextSize = 20.sp
    val SmallButtonTextSize = 18.sp

    // Text field / input sizing
    val TextFieldMinHeight = 72.dp     // enough for label + TitleSize text + descenders
    val DropdownMinHeight = 60.dp      // selector boxes (no label overhead)

    // Padding
    val ScreenPadding = 20.dp
    val CardPadding = 16.dp
    val ButtonSpacing = 16.dp

    // High-contrast button colors
    val PrimaryButton = Color(0xFF1565C0)       // Strong blue
    val PrimaryButtonText = Color.White
    val SecondaryButton = Color(0xFF424242)       // Dark gray
    val SecondaryButtonText = Color.White
    val DangerButton = Color(0xFFC62828)          // Strong red
    val DangerButtonText = Color.White
    val SuccessButton = Color(0xFF2E7D32)         // Strong green
    val SuccessButtonText = Color.White

    // Status colors
    val CapturedColor = Color(0xFF2E7D32)         // Green
    val SkippedColor = Color(0xFF9E9E9E)          // Gray
    val NeedsReviewColor = Color(0xFFE65100)      // Orange
    val PendingColor = Color(0xFFBDBDBD)          // Light gray

    // Instruction bar
    val InstructionBackground = Color(0xFFFFF9C4) // Light yellow
    val InstructionText = Color(0xFF212121)        // Near black
    val InstructionSize = 18.sp

    // Step indicator
    val StepBackground = Color(0xFF1565C0)
    val StepText = Color.White
}
