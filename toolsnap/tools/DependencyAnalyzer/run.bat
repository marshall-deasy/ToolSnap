@echo off
:: run.bat - Launch DependencyAnalyzer Flask server
:: Auto-detects project root and analyzes bot folders

echo ========================================
echo DependencyAnalyzer - Starting...
echo ========================================
echo.

python "%~dp0app.py"

pause
