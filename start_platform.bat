@echo off
REM ===================================================================
REM CasareRPA Enterprise Platform - Windows Startup Script
REM ===================================================================
REM Starts all platform components in Windows Terminal tabs
REM
REM Components:
REM   1. Orchestrator API (FastAPI) - Port 8000
REM   2. Monitoring Dashboard (React/Vite) - Port 5173
REM   3. Canvas Designer (optional)
REM   4. Robot Agent (optional)
REM
REM Prerequisites:
REM   - Windows Terminal installed (wt.exe)
REM   - Python 3.12+ with casare_rpa installed
REM   - Node.js 18+ with monitoring-dashboard dependencies installed
REM   - PostgreSQL 15+ running (or set USE_MEMORY_QUEUE=true)
REM ===================================================================

echo.
echo ========================================
echo  CasareRPA Enterprise Platform
echo ========================================
echo.

REM Check if Windows Terminal is available
where wt >nul 2>&1
if errorlevel 1 (
    echo [WARN] Windows Terminal not found. Falling back to separate windows.
    goto :legacy_start
)

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

REM Check node_modules for dashboard
if not exist "monitoring-dashboard\node_modules" (
    echo [WARN] node_modules not found. Installing dependencies...
    cd monitoring-dashboard
    call npm install
    cd ..
    if errorlevel 1 (
        echo [ERROR] Failed to install dashboard dependencies
        pause
        exit /b 1
    )
)

echo Starting platform with Windows Terminal tabs...
echo.

REM Ask which components to start
set /p START_CANVAS="Include Canvas Designer? (y/n): "
set /p START_ROBOT="Include Robot Agent? (y/n): "

REM Build Windows Terminal command with tabs
set WT_CMD=wt -w 0 new-tab --title "Orchestrator API" -d "%CD%" cmd /k "python -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000"

set WT_CMD=%WT_CMD% ; new-tab --title "Dashboard" -d "%CD%\monitoring-dashboard" cmd /k "npm run dev"

if /i "%START_CANVAS%"=="y" (
    set WT_CMD=%WT_CMD% ; new-tab --title "Canvas" -d "%CD%" cmd /k "python run.py"
)

if /i "%START_ROBOT%"=="y" (
    set WT_CMD=%WT_CMD% ; new-tab --title "Robot" -d "%CD%" cmd /k "python -m casare_rpa.robot.cli start"
)

REM Launch Windows Terminal with all tabs
%WT_CMD%

echo.
echo ========================================
echo  Platform Started Successfully!
echo ========================================
echo.
echo Orchestrator API:       http://localhost:8000
echo   - API Docs:           http://localhost:8000/docs
echo.
echo Monitoring Dashboard:   http://localhost:5173
echo.
if /i "%START_CANVAS%"=="y" echo Canvas Designer:        Started in tab
if /i "%START_ROBOT%"=="y" echo Robot Agent:            Started in tab
echo.
echo All components running in Windows Terminal tabs.
echo.
pause
exit /b 0

:legacy_start
REM Fallback to separate windows if Windows Terminal not available
echo Using legacy mode (separate windows)...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    pause
    exit /b 1
)

echo [1/2] Starting Orchestrator API (port 8000)...
start "CasareRPA Orchestrator API" cmd /k "python -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Monitoring Dashboard (port 5173)...
cd monitoring-dashboard
if not exist node_modules (
    echo [INFO] Installing dependencies...
    call npm install
)
start "CasareRPA Monitoring Dashboard" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo  Platform Started!
echo ========================================
echo.
echo Orchestrator API:       http://localhost:8000
echo Monitoring Dashboard:   http://localhost:5173
echo.
set /p START_CANVAS="Start Canvas Designer? (y/n): "
if /i "%START_CANVAS%"=="y" (
    start "CasareRPA Canvas" cmd /k "python run.py"
)
echo.
pause
