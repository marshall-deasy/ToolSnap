# toolsnap_structure.ps1
# Run from anywhere:  powershell -File C:\toolsnap\tools\toolsnap_structure.ps1
# Output: C:\toolsnap\toolsnap_structure.txt

$projectRoot = "C:\toolsnap"
$outputFile  = Join-Path $projectRoot "toolsnap_structure.txt"
$timestamp   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Directories to skip entirely
$skipDirs = @(
    '.gradle', '.idea', '.git', 'build', 'node_modules',
    '__pycache__', '.venv', 'captures', '.cxx', '.kotlin',
    'generated', 'intermediates', 'tmp', 'outputs',
    'kotlin-classes', 'packaged_manifests'
)

# File extensions to skip
$skipExtensions = @(
    '.class', '.dex', '.apk', '.aab', '.jar',
    '.so', '.o', '.exe', '.dll', '.pyc',
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico',
    '.ttf', '.otf', '.woff', '.woff2'
)

function Get-Tree {
    param(
        [string]$Path,
        [string]$Indent = ""
    )

    $items = Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue |
             Where-Object {
                 if ($_.PSIsContainer) {
                     $skipDirs -notcontains $_.Name
                 } else {
                     $skipExtensions -notcontains $_.Extension.ToLower()
                 }
             } |
             Sort-Object { -not $_.PSIsContainer }, Name

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item    = $items[$i]
        $isLast  = ($i -eq $items.Count - 1)
        $branch  = if ($isLast) { "+-- " } else { "|-- " }
        $newIndent = $Indent + $(if ($isLast) { "    " } else { "|   " })

        if ($item.PSIsContainer) {
            "$Indent$branch$($item.Name)/"
            Get-Tree -Path $item.FullName -Indent $newIndent
        } else {
            "$Indent$branch$($item.Name)"
        }
    }
}

$header = @(
    "# ToolSnap Project Structure"
    "# Generated: $timestamp"
    "# Root: $projectRoot"
    ""
    "toolsnap/"
)

$tree = Get-Tree -Path $projectRoot

($header + $tree) | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "Structure written to $outputFile" -ForegroundColor Green
