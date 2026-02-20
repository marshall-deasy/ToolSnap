# tsdb_sync_tablet.ps1 — Copy ToolSnap sessions from MTP tablet to PC
# Works with tablets that show as portable devices (no drive letter)

param(
    [string]$TabletName = "Marshall's Tab S7 FE",
    [string]$Destination = "C:\toolsnap_db\imports"
)

Write-Host "=" * 60
Write-Host "  ToolSnap Tablet Sync"
Write-Host "=" * 60
Write-Host ""

# Access the Shell COM object for MTP browsing
$shell = New-Object -ComObject Shell.Application
$myComputer = $shell.Namespace(17)  # 17 = "This PC"

# Find the tablet
$tablet = $null
foreach ($item in $myComputer.Items()) {
    if ($item.Name -like "*$TabletName*") {
        $tablet = $item
        Write-Host "  Found: $($item.Name)"
        break
    }
}

if (-not $tablet) {
    Write-Host ""
    Write-Host "  Tablet '$TabletName' not found."
    Write-Host "  Make sure it's plugged in via USB in File Transfer mode."
    Write-Host ""
    Write-Host "  Connected devices:"
    foreach ($item in $myComputer.Items()) {
        Write-Host "    - $($item.Name)"
    }
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Navigate: Internal Storage > Documents > ToolSnap
$storage = $tablet.GetFolder.Items() | Where-Object { $_.Name -match "Internal|Storage|Tablet" } | Select-Object -First 1
if (-not $storage) {
    # Try first item if naming is different
    $storage = $tablet.GetFolder.Items() | Select-Object -First 1
}

if (-not $storage) {
    Write-Host "  Could not find Internal Storage on tablet."
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Storage: $($storage.Name)"

$documents = $storage.GetFolder.Items() | Where-Object { $_.Name -eq "Documents" } | Select-Object -First 1
if (-not $documents) {
    Write-Host "  Could not find Documents folder."
    Read-Host "Press Enter to exit"
    exit 1
}

$toolsnap = $documents.GetFolder.Items() | Where-Object { $_.Name -eq "ToolSnap" } | Select-Object -First 1
if (-not $toolsnap) {
    Write-Host "  Could not find Documents\ToolSnap folder."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "  Source: $($storage.Name)\Documents\ToolSnap"
Write-Host ""

# Ensure destination exists
if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

# Copy each session folder
$sessions = $toolsnap.GetFolder.Items()
$copied = 0
$skipped = 0

foreach ($session in $sessions) {
    $name = $session.Name
    $destPath = Join-Path $Destination $name

    if (Test-Path $destPath) {
        Write-Host "  SKIP  $name (already in imports)"
        $skipped++
        continue
    }

    Write-Host "  COPY  $name" -NoNewline

    # Create dest folder and copy via Shell (handles MTP)
    New-Item -ItemType Directory -Path $destPath -Force | Out-Null
    $destFolder = $shell.Namespace($destPath)
    $files = $session.GetFolder.Items()
    $fileCount = 0

    foreach ($file in $files) {
        $destFolder.CopyHere($file, 0x14)  # 0x14 = no UI + yes to all
        $fileCount++
    }

    Write-Host " ($fileCount files)"
    $copied++
}

Write-Host ""
Write-Host ("-" * 60)
Write-Host "  Done: $copied copied, $skipped skipped"
Write-Host "  Launch the app and hit Scan & Import"
Write-Host ("-" * 60)
Write-Host ""
Read-Host "Press Enter to exit"
