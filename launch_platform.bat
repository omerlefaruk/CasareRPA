@echo off
echo ========================================================
echo Starting CasareRPA Platform (Windows Terminal Tabs)
echo ========================================================

:: Change to script directory
cd /d "%~dp0"

:: Check for venv
if not exist .venv (
    echo Virtual environment not found! Please run setup first.
    pause
    exit /b 1
)

:: Set the persistent tunnel URL
set CASARE_API_URL=https://api.casare.net

:: Check for cloudflared
where cloudflared >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] cloudflared not found in PATH.
    echo Cloudflare tunnel will not start.
    echo.
    echo Launching without tunnel...
    wt -w 0 nt --title "Orchestrator" -d . cmd /k ".\.venv\Scripts\python.exe manage.py orchestrator start --dev" ^; nt --title "Robot Agent" -d . cmd /k ".\.venv\Scripts\python.exe manage.py robot start" ^; nt --title "Canvas" -d . cmd /k ".\.venv\Scripts\python.exe manage.py canvas"
    goto :done
)

echo.
echo Tunnel URL: https://api.casare.net
echo.
echo Launching in Windows Terminal with Cloudflare Tunnel...

:: Launch 4 tabs: Tunnel, Orchestrator, Robot Agent, Canvas
wt -w 0 nt --title "Tunnel" -d . cmd /k "cloudflared tunnel run casare-rpa" ^; nt --title "Orchestrator" -d . cmd /k ".\.venv\Scripts\python.exe manage.py orchestrator start --dev" ^; nt --title "Robot" -d . cmd /k ".\.venv\Scripts\python.exe manage.py robot start" ^; nt --title "Canvas" -d . cmd /k ".\.venv\Scripts\python.exe manage.py canvas"

:done
echo.
echo Platform launched!
pause
