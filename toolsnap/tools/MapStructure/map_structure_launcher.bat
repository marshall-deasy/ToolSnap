@echo off
:: map_structure_launcher.bat — thin wrapper for double-click convenience
:: Auto-detects script location. No manual path configuration needed.

python "%~dp0map_structure.py" %*
echo.
pause
