@echo off
REM ============================================================
REM CasareRPA Robot Installer Builder - One Click Build
REM ============================================================
REM
REM This creates: dist\CasareRPA-Robot-3.0.0-Setup.exe
REM Pre-configured for your Supabase project
REM
REM Requirements:
REM   - Python 3.12+
REM   - NSIS (optional, for .exe installer)
REM
REM ============================================================

echo.
echo ============================================================
echo  CasareRPA Robot Installer Builder
echo ============================================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.12+ first.
    pause
    exit /b 1
)

REM Run PowerShell build script
echo Running build script...
echo.

powershell -ExecutionPolicy Bypass -File "installer\build_robot.ps1" -SkipTests

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  BUILD COMPLETE
echo ============================================================
echo.
echo Output: dist\CasareRPA-Robot-3.0.0-Setup.exe
echo.
echo Next: Copy installer to your VM and run it.
echo.

pause
