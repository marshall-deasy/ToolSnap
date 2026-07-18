@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   ToolSnap ADB Sync
echo ============================================================
echo.

where adb >nul 2>&1
if errorlevel 1 (
    echo   ADB not found. Run: winget install Google.PlatformTools
    pause
    exit /b 1
)

:: Check device
adb devices | findstr /R "device$" >nul 2>&1
if errorlevel 1 (
    echo   No device found. Check USB + USB Debugging.
    echo.
    adb devices
    pause
    exit /b 1
)

echo   Device connected
echo.

set "SRC=/sdcard/Documents/ToolSnap"
set "DEST=C:\toolsnap_db\imports"

if not exist "%DEST%" mkdir "%DEST%"

:: Get session list from tablet
set /a COUNT=0
set /a SKIP=0

for /f "delims=" %%S in ('adb shell "ls -1 %SRC% 2>/dev/null"') do (
    set "NAME=%%S"
    :: Trim trailing carriage return from adb output
    set "NAME=!NAME: =!"
    for /f "delims=" %%N in ("!NAME!") do set "NAME=%%N"
    
    if exist "%DEST%\!NAME!" (
        echo   SKIP  !NAME!
        set /a SKIP+=1
    ) else (
        echo   PULL  !NAME!
        adb pull "%SRC%/!NAME!" "%DEST%\!NAME!" >nul 2>&1
        set /a COUNT+=1
    )
)

echo.
echo ------------------------------------------------------------
echo   Done: %COUNT% pulled, %SKIP% skipped
echo   Delete toolsnap.db, relaunch app, Scan ^& Import
echo ------------------------------------------------------------
echo.
pause
