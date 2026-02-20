@echo off
:: run.bat - Launch LogViewer Flask server
:: Auto-detects project root and opens browser

echo ========================================
echo LogViewer - Starting...
echo ========================================
echo.

python "%~dp0app.py"

pause
