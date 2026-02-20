@echo off
REM FolderSync Launcher
REM Double-click this file to start FolderSync

echo Starting FolderSync...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    echo.
    pause
    exit /b 1
)

REM Check if PySide6 is installed
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PySide6 is not installed
    echo.
    echo Installing PySide6...
    pip install PySide6
    if errorlevel 1 (
        echo Failed to install PySide6
        echo Please run: pip install PySide6
        echo.
        pause
        exit /b 1
    )
)

REM Run FolderSync
python main.py

REM If we get here, the program exited
REM Pause only if there was an error
if errorlevel 1 (
    echo.
    echo FolderSync exited with an error.
    pause
)
