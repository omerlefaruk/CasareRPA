@echo off
REM ===================================================================
REM CasareRPA Enterprise Platform - Windows Startup Script
REM ===================================================================
REM Starts all platform components in separate command windows
REM
REM Components:
REM   1. Orchestrator API (FastAPI) - Port 8000
REM   2. Monitoring Dashboard (React/Vite) - Port 5173
REM   3. Robot Agent (optional - run manually if needed)
REM
REM Prerequisites:
REM   - Python 3.12+ with casare_rpa installed
REM   - Node.js 18+ with monitoring-dashboard dependencies installed
REM   - PostgreSQL 15+ running (or set USE_MEMORY_QUEUE=true)
REM ===================================================================

echo.
echo ========================================
echo  CasareRPA Enterprise Platform
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.12+
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

echo [1/2] Starting Orchestrator API (port 8000)...
start "CasareRPA Orchestrator API" cmd /k "python -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000"

REM Wait 3 seconds for API to start
timeout /t 3 /nobreak >nul

echo [2/2] Starting Monitoring Dashboard (port 5173)...
cd monitoring-dashboard
if not exist node_modules (
    echo [WARN] node_modules not found. Run 'npm install' first in monitoring-dashboard/
    echo [INFO] Attempting to install dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        cd ..
        pause
        exit /b 1
    )
)

start "CasareRPA Monitoring Dashboard" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo  Platform Started Successfully!
echo ========================================
echo.
echo Orchestrator API:       http://localhost:8000
echo   - Health Check:       http://localhost:8000/health
echo   - API Docs:           http://localhost:8000/docs
echo.
echo Monitoring Dashboard:   http://localhost:5173
echo   - Real-time updates via WebSocket
echo.
echo Canvas Designer:        Run 'python run.py' separately
echo Robot Agent:            Run 'python -m casare_rpa.robot.cli start' separately
echo.
echo ========================================
echo  Optional: Start Canvas Designer
echo ========================================
echo.
set /p START_CANVAS="Start Canvas Designer now? (y/n): "
if /i "%START_CANVAS%"=="y" (
    echo Starting Canvas Designer...
    start "CasareRPA Canvas Designer" cmd /k "python run.py"
) else (
    echo Skipped Canvas Designer. Run 'python run.py' when ready.
)

echo.
echo Press any key to show Robot Agent start command...
pause >nul
echo.
echo ========================================
echo  To Start Robot Agent:
echo ========================================
echo.
echo   python -m casare_rpa.robot.cli start
echo.
echo   (Run this in a separate terminal when ready)
echo.
pause
