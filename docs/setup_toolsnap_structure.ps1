$root = "C:\toolsnap"

$folders = @(
    "app\src\main\java\com\toolsnap"
    "app\src\main\java\com\toolsnap\core\model"
    "app\src\main\java\com\toolsnap\core\session"
    "app\src\main\java\com\toolsnap\core\ocr"
    "app\src\main\java\com\toolsnap\config"
    "app\src\main\java\com\toolsnap\utils"
    "app\src\main\java\com\toolsnap\ui\home"
    "app\src\main\java\com\toolsnap\ui\wizard"
    "app\src\main\java\com\toolsnap\ui\detail"
    "app\src\main\java\com\toolsnap\ui\components"
    "app\src\main\java\com\toolsnap\ui\theme"
    "app\src\main\res\layout"
    "app\src\main\res\values"
    "app\src\main\res\drawable"
    "app\src\main\res\mipmap-hdpi"
    "app\src\main\res\mipmap-mdpi"
    "app\src\main\res\mipmap-xhdpi"
    "app\src\main\res\mipmap-xxhdpi"
    "app\src\main\res\mipmap-xxxhdpi"
    "gradle\wrapper"
    "tools\toolsnap_watcher"
    "docs"
)

foreach ($f in $folders) {
    $path = Join-Path $root $f
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  + $f"
    }
}

Write-Host "`nDone. Structure ready at $root"
