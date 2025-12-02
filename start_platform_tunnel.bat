@echo off
REM ===================================================================
REM CasareRPA Enterprise Platform - With Cloudflare Tunnel
REM ===================================================================
REM Starts all platform components + Cloudflare Tunnel for remote access
REM
REM Components:
REM   1. Cloudflare Tunnel (casare-rpa) - Remote access
REM   2. Orchestrator API (FastAPI) - Port 8000 -> api.casare.net
REM   3. Monitoring Dashboard (React/Vite) - Port 5173
REM   4. Canvas Designer (optional)
REM   5. Robot Agent (optional)
REM
REM Prerequisites:
REM   - cloudflared installed (winget install Cloudflare.cloudflared)
REM   - Windows Terminal installed (wt.exe)
REM   - Python 3.12+ with casare_rpa installed
REM   - Node.js 18+ with monitoring-dashboard dependencies installed
REM ===================================================================

echo.
echo ========================================
echo  CasareRPA Enterprise Platform
echo  With Cloudflare Tunnel
echo ========================================
echo.

REM Check if cloudflared is available
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo [ERROR] cloudflared not found!
    echo Install with: winget install Cloudflare.cloudflared
    pause
    exit /b 1
)

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

REM Kill any existing process on port 8000
echo [INFO] Checking for existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo [INFO] Killing process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Build Windows Terminal command with tabs - ALL components
REM Tab 1: Cloudflare Tunnel
set WT_CMD=wt -w 0 new-tab --title "Cloudflare Tunnel" -d "%CD%" cmd /k "cloudflared tunnel run casare-rpa"

REM Tab 2: Orchestrator API (loads .env automatically)
set WT_CMD=%WT_CMD% ; new-tab --title "Orchestrator API" -d "%CD%" cmd /k "python -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000"

REM Tab 3: Dashboard
set WT_CMD=%WT_CMD% ; new-tab --title "Dashboard" -d "%CD%\monitoring-dashboard" cmd /k "npm run dev"

REM Tab 4: Canvas Designer
set WT_CMD=%WT_CMD% ; new-tab --title "Canvas" -d "%CD%" cmd /k "python run.py"

REM Launch Windows Terminal with all tabs
%WT_CMD%

echo.
echo ========================================
echo  Platform Started Successfully!
echo ========================================
echo.
echo Cloudflare Tunnel:      ACTIVE
echo.
echo LOCAL URLs:
echo   Orchestrator API:     http://localhost:8000
echo   API Docs:             http://localhost:8000/docs
echo   Dashboard:            http://localhost:5173
echo.
echo PUBLIC URLs (via Tunnel):
echo   API:                  https://api.casare.net
echo   Webhooks:             https://webhooks.casare.net
echo   Robots WebSocket:     wss://robots.casare.net
echo.
echo Canvas Designer:        Started in tab
echo.
echo All components running in Windows Terminal tabs.
echo.
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

REM Kill any existing process on port 8000
echo [INFO] Checking for existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo [INFO] Killing process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [1/4] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run casare-rpa"

timeout /t 3 /nobreak >nul

echo [2/4] Starting Orchestrator API (port 8000)...
start "CasareRPA Orchestrator API" cmd /k "python -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [3/4] Starting Monitoring Dashboard (port 5173)...
cd monitoring-dashboard
if not exist node_modules (
    echo [INFO] Installing dependencies...
    call npm install
)
start "CasareRPA Monitoring Dashboard" cmd /k "npm run dev"
cd ..

timeout /t 2 /nobreak >nul

echo [4/4] Starting Canvas Designer...
start "CasareRPA Canvas" cmd /k "python run.py"

echo.
echo ========================================
echo  Platform Started!
echo ========================================
echo.
echo LOCAL URLs:
echo   Orchestrator API:     http://localhost:8000
echo   Dashboard:            http://localhost:5173
echo.
echo PUBLIC URLs (via Tunnel):
echo   API:                  https://api.casare.net
echo   Webhooks:             https://webhooks.casare.net
echo   Robots WebSocket:     wss://robots.casare.net
echo.
echo Canvas Designer:        Started
echo.
