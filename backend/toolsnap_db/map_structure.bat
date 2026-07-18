@echo off
setlocal enabledelayedexpansion

:: map_structure.bat — Portable directory structure mapper
:: Usage:
::   map_structure.bat              Maps current directory
::   map_structure.bat C:\Projects  Maps specified directory

if "%~1"=="" (
    set "ROOT=%cd%"
) else (
    set "ROOT=%~f1"
)

if not exist "%ROOT%\" (
    echo Error: "%ROOT%" is not a valid directory.
    exit /b 1
)

for %%F in ("%ROOT%") do set "ROOT_NAME=%%~nxF"

set "OUTFILE=%ROOT%\%ROOT_NAME%_STRUCTURE.txt"

echo %ROOT_NAME%/> "%OUTFILE%"

call :mapdir "%ROOT%" "" >> "%OUTFILE%"

type "%OUTFILE%"
echo.
echo --- Saved to: %OUTFILE% ---

endlocal
exit /b 0


:mapdir
setlocal enabledelayedexpansion
set "DIR=%~1"
set "PREFIX=%~2"

:: collect entries, skip excluded folders and hidden items
set "count=0"
for /f "delims=" %%E in ('dir /b /a "%DIR%" 2^>nul') do (
    set "skip=0"
    for %%X in (__pycache__ .git .vscode .idea node_modules .mypy_cache .pytest_cache venv .venv env .env .tox dist build) do (
        if /i "%%E"=="%%X" set "skip=1"
    )
    if "!skip!"=="0" (
        set /a count+=1
        set "entry_!count!=%%E"
    )
)

set "idx=0"
for /l %%I in (1,1,!count!) do (
    set /a idx=%%I
    set "name=!entry_%%I!"
    if %%I==!count! (
        set "connector=└── "
        set "extension=    "
    ) else (
        set "connector=├── "
        set "extension=│   "
    )

    if exist "%DIR%\!name!\*" (
        echo !PREFIX!!connector!!name!/
        call :mapdir "%DIR%\!name!" "!PREFIX!!extension!"
    ) else (
        echo !PREFIX!!connector!!name!
    )
)

endlocal
exit /b 0
