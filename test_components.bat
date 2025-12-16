@echo off
REM Quick test launcher - Just check if components work
echo ============================================================
echo  CasareRPA Platform - Component Test
echo ============================================================
echo.

cd /d "%~dp0"

if not exist .venv (
    echo Virtual environment not found!
    pause
    exit /b 1
)

echo Testing platform components...
echo.

call .venv\Scripts\activate.bat

echo 1. Testing Service Registry...
python -c "from casare_rpa.infrastructure.services import get_service_registry; print('   ✓ Service registry OK')"
if errorlevel 1 goto :error

echo 2. Testing Auto-Discovery...
python -c "from casare_rpa.robot.auto_discovery import get_auto_discovery; print('   ✓ Auto-discovery OK')"
if errorlevel 1 goto :error

echo 3. Testing Launcher Module...
python -c "from casare_rpa.launcher import PlatformLauncher; print('   ✓ Launcher module OK')"
if errorlevel 1 goto :error

echo.
echo ============================================================
echo ✅ All components working!
echo ============================================================
echo.
echo To start platform (requires database setup):
echo   launch.bat
echo.
echo To check service health:
echo   python test_platform.py
echo.
pause
exit /b 0

:error
echo.
echo ❌ Component test failed!
pause
exit /b 1
