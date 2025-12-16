@echo off
setlocal
cd /d "%~dp0"

echo Launching CasareRPA...

:: Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "launch.ps1"
) else (
    echo PowerShell not found. Using fallback launcher.
    if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
    python -m casare_rpa.launcher
)

if %ERRORLEVEL% NEQ 0 pause
