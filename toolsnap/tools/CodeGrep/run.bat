@echo off
:: run.bat - Launch CodeGrep Flask server
:: Auto-detects project root and starts search interface

echo ========================================
echo CodeGrep - Starting...
echo ========================================
echo.

python "%~dp0app.py"

pause
