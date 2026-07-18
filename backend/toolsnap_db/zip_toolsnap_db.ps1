# zip_toolsnap_db.ps1 — Create a lean zip of C:\toolsnap_db for Claude review
# Run from any PowerShell prompt:  .\zip_toolsnap_db.ps1

$src  = "C:\toolsnap_db"
$dest = "C:\toolsnap_db_lean.zip"

# Patterns to EXCLUDE (heavy / non-essential)
$excludeExtensions = @(
    '.pyc', '.pyo', '.exe', '.dll', '.obj', '.o', '.so',
    '.egg-info', '.whl', '.tar', '.gz',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.mp4', '.avi', '.mov',
    '.zip', '.rar', '.7z',
    '.log'
)

$excludeFolders = @(
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.idea', '.vs', '.vscode',
    'bin', 'obj', 'dist', 'build', '.mypy_cache',
    '.pytest_cache', 'eggs', '*.egg-info'
)

if (-not (Test-Path $src)) {
    Write-Host "ERROR: $src not found" -ForegroundColor Red
    exit 1
}

# Remove old zip if present
if (Test-Path $dest) { Remove-Item $dest -Force }

# Collect files with filtering
$files = Get-ChildItem -Path $src -Recurse -File | Where-Object {
    $relPath = $_.FullName.Substring($src.Length)
    $pathParts = $relPath.Split('\/')

    # Check if any parent folder is in the exclude list
    $inExcludedFolder = $false
    foreach ($part in $pathParts) {
        if ($excludeFolders -contains $part) {
            $inExcludedFolder = $true
            break
        }
    }

    # Check extension
    $badExt = $excludeExtensions -contains $_.Extension.ToLower()

    # Keep the SQLite DB only if it's under 10 MB (skip huge DBs)
    $bigDb = ($_.Extension -eq '.db' -or $_.Extension -eq '.sqlite') -and $_.Length -gt 10MB

    -not $inExcludedFolder -and -not $badExt -and -not $bigDb
}

# Report what we're packing
$totalKB = [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1KB, 1)
Write-Host "`nFiles to include: $($files.Count)  (~${totalKB} KB)" -ForegroundColor Cyan
Write-Host ""

# Show file tree
foreach ($f in $files) {
    $rel = $f.FullName.Substring($src.Length + 1)
    $sizeKB = [math]::Round($f.Length / 1KB, 1)
    Write-Host "  $rel  (${sizeKB} KB)"
}

Write-Host ""

# Create zip using .NET (preserves folder structure)
Add-Type -AssemblyName System.IO.Compression.FileSystem

$zip = [System.IO.Compression.ZipFile]::Open($dest, 'Create')
foreach ($f in $files) {
    $entryName = $f.FullName.Substring($src.Length + 1)  # relative path
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $zip, $f.FullName, $entryName, 'Optimal'
    ) | Out-Null
}
$zip.Dispose()

$zipSizeKB = [math]::Round((Get-Item $dest).Length / 1KB, 1)
Write-Host "Created: $dest  (${zipSizeKB} KB)" -ForegroundColor Green
Write-Host "Upload this zip to Claude to continue." -ForegroundColor Yellow
