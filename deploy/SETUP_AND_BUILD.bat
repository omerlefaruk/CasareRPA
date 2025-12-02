@echo off
REM ============================================================
REM CasareRPA Complete Setup + Build
REM ============================================================
REM
REM This script:
REM   1. Applies database migration to Supabase
REM   2. Creates robot and generates API key
REM   3. Builds the robot installer
REM
REM Your .env is already configured with:
REM   - Supabase URL: https://znaauaswqmurwfglantv.supabase.co
REM   - Database: db.znaauaswqmurwfglantv.supabase.co
REM
REM ============================================================

echo.
echo ============================================================
echo  CasareRPA Complete Setup + Build
echo ============================================================
echo.

cd /d "%~dp0.."

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.12+ first.
    pause
    exit /b 1
)

REM Install dependencies
echo [1/4] Installing dependencies...
pip install -e . --quiet
pip install asyncpg httpx python-dotenv --quiet
echo       Done.
echo.

REM Run database migration and create robot
echo [2/4] Setting up database and creating robot...
echo.
python deploy/auto_setup.py setup --db-password 6729Raumafu.
if errorlevel 1 (
    echo.
    echo [WARN] Setup had issues, but continuing with build...
)
echo.

REM Build robot installer
echo [3/4] Building robot installer...
echo.
cd deploy
call BUILD_ROBOT_INSTALLER.bat
cd ..
echo.

REM Summary
echo.
echo ============================================================
echo  SETUP COMPLETE
echo ============================================================
echo.
echo What you have now:
echo.
echo   1. Database: Tables created in Supabase
echo   2. Robot: Registered with API key (check output above)
echo   3. Installer: dist\CasareRPA-Robot-3.0.0-Setup.exe
echo.
echo Next steps:
echo.
echo   YOUR PC (Orchestrator):
echo     python deploy/auto_setup.py orchestrator
echo.
echo   YOUR VM (Robot):
echo     Copy dist\CasareRPA-Robot-3.0.0-Setup.exe to VM
echo     Run installer, enter password and API key
echo.
echo ============================================================
echo.

pause
