@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo CasareRPA Launcher (Separate Windows Mode)
echo ============================================
echo.

:: Check for virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at .venv
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

echo Starting components in separate windows...
echo.

:: Start Orchestrator
echo [1/3] Starting Orchestrator...
start "CasareRPA Orchestrator" cmd /k "call .venv\Scripts\activate.bat && python manage.py orchestrator start --dev"
timeout /t 3 /nobreak >nul

:: Start Robot
echo [2/3] Starting Robot Agent...
start "CasareRPA Robot" cmd /k "call .venv\Scripts\activate.bat && python -m casare_rpa.robot.tray_icon"
timeout /t 2 /nobreak >nul

:: Start Canvas
echo [3/3] Starting Canvas UI...
start "CasareRPA Canvas" cmd /k "call .venv\Scripts\activate.bat && python manage.py canvas"

echo.
echo ============================================
echo All components launched!
echo ============================================
echo.
echo You should see 3 command windows:
echo   - Orchestrator (API Server)
echo   - Robot (Background Agent)
echo   - Canvas (UI Designer)
echo.
echo To stop: Close each window or press Ctrl+C
echo.
pause
