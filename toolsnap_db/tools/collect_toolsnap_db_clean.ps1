# collect_toolsnap_db_clean.ps1
# Collects a clean zip of C:\toolsnap_db, excluding build artifacts, caches, and junk.
# Output: Desktop\toolsnap_db_clean_<timestamp>.zip

$ProjectRoot = "C:\toolsnap_db"
$ProjectName = "toolsnap_db"
$OutputDir = [Environment]::GetFolderPath("Desktop")
$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$ZipPath = Join-Path $OutputDir "${ProjectName}_clean_${Timestamp}.zip"

# --- Excluded directory names (case-insensitive, matched anywhere in path) ---
$ExcludeDirs = @(
    '.git'
    '.gradle'
    '.idea'
    'build'
    'node_modules'
    '__pycache__'
    '.venv'
    'venv'
    '.mypy_cache'
    '.pytest_cache'
    'captures'
    '.cxx'
    '.externalNativeBuild'
    'intermediates'
    'generated'
    'tmp'
    'logs'
)

# --- Excluded file extensions ---
$ExcludeExtensions = @(
    '.apk'
    '.aab'
    '.dex'
    '.class'
    '.jar'
    '.log'
    '.hprof'
    '.DS_Store'
)

# --- Excluded file names ---
$ExcludeFiles = @(
    'local.properties'
    'Thumbs.db'
    'desktop.ini'
)

# -------------------------------------------------------

if (-not (Test-Path $ProjectRoot)) {
    Write-Host "ERROR: Project root not found: $ProjectRoot" -ForegroundColor Red
    exit 1
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

# Remove existing zip if somehow same timestamp
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

Write-Host "Collecting clean snapshot of $ProjectRoot ..." -ForegroundColor Cyan

$archive = [System.IO.Compression.ZipFile]::Open($ZipPath, 'Create')
$filesAdded = 0
$filesSkipped = 0

try {
    Get-ChildItem -Path $ProjectRoot -Recurse -File -Force | ForEach-Object {
        $fullPath = $_.FullName
        $relativePath = $fullPath.Substring($ProjectRoot.Length).TrimStart('\', '/')

        # Check if any parent directory is in the exclude list
        $pathParts = $relativePath.Split('\', '/')
        $skip = $false
        foreach ($part in $pathParts[0..($pathParts.Length - 2)]) {
            if ($ExcludeDirs -contains $part) {
                $skip = $true
                break
            }
        }
        if ($skip) { $filesSkipped++; return }

        # Check file extension
        if ($ExcludeExtensions -contains $_.Extension.ToLower()) { $filesSkipped++; return }

        # Check file name
        if ($ExcludeFiles -contains $_.Name) { $filesSkipped++; return }

        # Skip files larger than 10 MB
        if ($_.Length -gt 10MB) {
            Write-Host "  SKIP (>10MB): $relativePath" -ForegroundColor Yellow
            $filesSkipped++
            return
        }

        # Add to archive using forward slashes for zip compat
        $entryName = $relativePath.Replace('\', '/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $fullPath, $entryName, [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
        $filesAdded++
    }
}
finally {
    $archive.Dispose()
}

$sizeMB = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "  Files included : $filesAdded"
Write-Host "  Files skipped  : $filesSkipped"
Write-Host "  Zip size       : ${sizeMB} MB"
Write-Host "  Output         : $ZipPath" -ForegroundColor Cyan
