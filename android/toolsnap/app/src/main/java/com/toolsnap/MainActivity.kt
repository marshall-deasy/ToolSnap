package com.toolsnap

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.toolsnap.ui.ToolSnapNavHost
import com.toolsnap.ui.theme.ToolSnapTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ToolSnapTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    PermissionGate {
                        ToolSnapNavHost()
                    }
                }
            }
        }
    }
}

/**
 * Wraps the app content in a camera permission gate.
 *
 * On first launch (or if permission was revoked), shows a clear
 * explanation screen with a big GRANT CAMERA ACCESS button.
 * The app cannot function without camera access.
 *
 * Does NOT request storage permissions — on API 29+ (Android 10+),
 * scoped storage to Documents/ is automatic. The manifest already
 * declares storage permissions with maxSdkVersion="28" for older devices.
 */
@Composable
private fun PermissionGate(content: @Composable () -> Unit) {
    val context = LocalContext.current

    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context, Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    var permissionDenied by remember { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasPermission = granted
        permissionDenied = !granted
    }

    if (hasPermission) {
        content()
    } else {
        // Permission request screen
        CameraPermissionScreen(
            wasDenied = permissionDenied,
            onRequestPermission = {
                launcher.launch(Manifest.permission.CAMERA)
            }
        )

        // Auto-request on first display (not after denial)
        if (!permissionDenied) {
            LaunchedEffect(Unit) {
                launcher.launch(Manifest.permission.CAMERA)
            }
        }
    }
}

/**
 * Full-screen permission explanation.
 * Shop-floor friendly: big text, big button, clear language.
 */
@Composable
private fun CameraPermissionScreen(
    wasDenied: Boolean,
    onRequestPermission: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1B1B1F))
            .padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = if (wasDenied) Icons.Default.Warning else Icons.Default.CameraAlt,
            contentDescription = null,
            tint = if (wasDenied) Color(0xFFFFB300) else Color.White,
            modifier = Modifier.size(80.dp)
        )

        Spacer(Modifier.height(24.dp))

        Text(
            text = if (wasDenied) "CAMERA ACCESS REQUIRED" else "CAMERA PERMISSION",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            textAlign = TextAlign.Center
        )

        Spacer(Modifier.height(16.dp))

        Text(
            text = if (wasDenied) {
                "ToolSnap needs camera access to photograph your tooling. " +
                "Tap below to grant permission, or open Settings → Apps → ToolSnap → Permissions."
            } else {
                "ToolSnap needs camera access to photograph your tooling assemblies."
            },
            fontSize = 18.sp,
            color = Color.White.copy(alpha = 0.8f),
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(40.dp))

        Button(
            onClick = onRequestPermission,
            modifier = Modifier
                .fillMaxWidth()
                .height(72.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF2196F3),
                contentColor = Color.White
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(
                Icons.Default.CameraAlt, null,
                modifier = Modifier.size(32.dp)
            )
            Spacer(Modifier.size(12.dp))
            Text(
                "GRANT CAMERA ACCESS",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}
