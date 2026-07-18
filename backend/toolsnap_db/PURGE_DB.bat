@echo off
REM ─── PURGE_DB.bat ─────────────────────────────────────────────
REM   Deletes toolsnap.db so the next app launch starts fresh.
REM   Import data in imports\ is NOT deleted — you can re-import.
REM ──────────────────────────────────────────────────────────────

set DB_PATH=C:\toolsnap_db\toolsnap.db

echo.
echo   ╔══════════════════════════════════════╗
echo   ║       ToolSnap — Purge Database      ║
echo   ╠══════════════════════════════════════╣
echo   ║  This will DELETE the database file: ║
echo   ║  %DB_PATH%         ║
echo   ║                                      ║
echo   ║  Your import folders will NOT be     ║
echo   ║  deleted — you can re-import after.  ║
echo   ╚══════════════════════════════════════╝
echo.

choice /C YN /M "Are you sure you want to purge the database"
if errorlevel 2 (
    echo Cancelled.
    goto :end
)

if exist "%DB_PATH%" (
    del /F "%DB_PATH%" 2>nul
    if exist "%DB_PATH%" (
        echo.
        echo ERROR: Could not delete %DB_PATH%
        echo Close ToolSnap first, then try again.
    ) else (
        echo.
        echo Database purged.
        echo Next time you launch ToolSnap, it will create a fresh database.
        echo Go to Import tab and click Scan ^& Import to reload your tools.
    )
) else (
    echo.
    echo Nothing to purge — %DB_PATH% does not exist.
)

:end
echo.
pause
