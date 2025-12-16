@echo off
echo ========================================================
echo Starting CasareRPA Platform (Windows Terminal Tabs)
echo ========================================================

:: Non-interactive test mode (no wt tabs)
if /I "%~1"=="--test" goto :test

:: Change to script directory
cd /d "%~dp0"

:: Check for venv
if not exist .venv (
    echo Virtual environment not found! Please run setup first.
    pause
    exit /b 1
)

:: Ensure CasareRPA client config exists (needed for Canvas Fleet Dashboard)
set "CONFIG_DIR=%APPDATA%\CasareRPA"
set "CONFIG_FILE=%CONFIG_DIR%\config.yaml"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%CONFIG_FILE%" (
    echo Creating default CasareRPA config at %CONFIG_FILE%...
    (
        echo orchestrator:
        echo   url: wss://api.casare.net/ws
        echo   api_key: ""
        echo first_run_complete: true
    ) > "%CONFIG_FILE%"
)

:: Set the persistent tunnel URL
if "%CASARE_API_URL%"=="" set CASARE_API_URL=https://api.casare.net

:: Cloudflare named tunnel. Override by setting CASARE_CLOUDFLARE_TUNNEL_NAME.
:: Default matches the local cloudflared config on this machine.
if "%CASARE_CLOUDFLARE_TUNNEL_NAME%"=="" set CASARE_CLOUDFLARE_TUNNEL_NAME=casare-rpa

:: Start local orchestrator (origin for the Cloudflare tunnel) unless explicitly disabled.
if "%CASARE_START_ORCHESTRATOR%"=="" set CASARE_START_ORCHESTRATOR=1

:: If ORCHESTRATOR_API_KEY isn't set, try to load it from .env
if "%ORCHESTRATOR_API_KEY%"=="" (
    if exist "%~dp0.env" (
        for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%~dp0.env") do (
            if /I "%%A"=="ORCHESTRATOR_API_KEY" set ORCHESTRATOR_API_KEY=%%B
        )
    )
)

:: Force Canvas to use the Orchestrator API (remote control plane)
:: If you have a custom Orchestrator API URL, set ORCHESTRATOR_URL before running this script.
if "%ORCHESTRATOR_URL%"=="" set ORCHESTRATOR_URL=%CASARE_API_URL%

echo.
echo Orchestrator API URL: %ORCHESTRATOR_URL%
echo CASARE_API_URL:       %CASARE_API_URL%
echo Cloudflare tunnel:    %CASARE_CLOUDFLARE_TUNNEL_NAME%
echo Start orchestrator:   %CASARE_START_ORCHESTRATOR%
echo.
echo Launching in Windows Terminal (API-only mode)...

:: Launch tabs: Cloudflare Tunnel, (optional) Orchestrator, Robot (Tray), Robot Logs, Canvas
:: Tunnel is optional at runtime (warn if cloudflared missing)
where cloudflared >nul 2>nul
if errorlevel 1 (
    echo [WARN] cloudflared not found in PATH. Tunnel tab will show an error.
)

if "%CASARE_START_ORCHESTRATOR%"=="1" (
    wt -w 0 nt --title "Cloudflare Tunnel" -d . cmd /k "cloudflared tunnel run %CASARE_CLOUDFLARE_TUNNEL_NAME%" ^; ^
       nt --title "Orchestrator" -d . cmd /k "set ROBOT_AUTH_ENABLED=false && .\.venv\Scripts\python.exe manage.py orchestrator start --dev" ^; ^
       nt --title "Robot (Tray)" -d . cmd /k "timeout /t 3 /nobreak >nul && .\.venv\Scripts\python.exe -m casare_rpa.robot.tray_icon" ^; ^
       nt --title "Robot Logs" -d . cmd /k "timeout /t 3 /nobreak >nul && .\.venv\Scripts\python.exe manage.py robot logs --follow" ^; ^
       nt --title "Canvas" -d . cmd /k ".\.venv\Scripts\python.exe manage.py canvas"
) else (
    wt -w 0 nt --title "Cloudflare Tunnel" -d . cmd /k "cloudflared tunnel run %CASARE_CLOUDFLARE_TUNNEL_NAME%" ^; ^
       nt --title "Robot (Tray)" -d . cmd /k "timeout /t 3 /nobreak >nul && .\.venv\Scripts\python.exe -m casare_rpa.robot.tray_icon" ^; ^
       nt --title "Robot Logs" -d . cmd /k "timeout /t 3 /nobreak >nul && .\.venv\Scripts\python.exe manage.py robot logs --follow" ^; ^
       nt --title "Canvas" -d . cmd /k ".\.venv\Scripts\python.exe manage.py canvas"
)

:done
echo.
echo Platform launched!
pause

goto :eof

:test
echo ========================================================
echo launch_platform.bat --test
echo ========================================================

:: Ensure defaults are applied in test mode too
if "%CASARE_API_URL%"=="" set CASARE_API_URL=https://api.casare.net
if "%ORCHESTRATOR_URL%"=="" set ORCHESTRATOR_URL=%CASARE_API_URL%
if "%CASARE_CLOUDFLARE_TUNNEL_NAME%"=="" set CASARE_CLOUDFLARE_TUNNEL_NAME=casare-rpa
if "%CASARE_START_ORCHESTRATOR%"=="" set CASARE_START_ORCHESTRATOR=1

:: Load ORCHESTRATOR_API_KEY from .env if not set
if "%ORCHESTRATOR_API_KEY%"=="" (
    if exist "%~dp0.env" (
        for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%~dp0.env") do (
            if /I "%%A"=="ORCHESTRATOR_API_KEY" set ORCHESTRATOR_API_KEY=%%B
        )
    )
)

echo.
echo ORCHESTRATOR_URL: %ORCHESTRATOR_URL%
echo CASARE_API_URL:   %CASARE_API_URL%
echo Tunnel name:      %CASARE_CLOUDFLARE_TUNNEL_NAME%
echo Start orchestrator: %CASARE_START_ORCHESTRATOR%
if "%ORCHESTRATOR_API_KEY%"=="" (
    echo ORCHESTRATOR_API_KEY: ^(not set^)
) else (
    echo ORCHESTRATOR_API_KEY: ^(set^)
)
echo.
echo Probing Orchestrator API for robots...
set "PROBE_FILE=%TEMP%\casare_orchestrator_probe.py"
> "%PROBE_FILE%" echo import os
>> "%PROBE_FILE%" echo import asyncio
>> "%PROBE_FILE%" echo from casare_rpa.infrastructure.orchestrator.client import OrchestratorClient, OrchestratorConfig
>> "%PROBE_FILE%" echo.
>> "%PROBE_FILE%" echo async def main() -^> None:
>> "%PROBE_FILE%" echo     url = os.getenv("ORCHESTRATOR_URL") or os.getenv("CASARE_API_URL") or "https://api.casare.net"
>> "%PROBE_FILE%" echo     api_key = os.getenv("ORCHESTRATOR_API_KEY")
>> "%PROBE_FILE%" echo     ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
>> "%PROBE_FILE%" echo     print("Resolved ORCHESTRATOR_URL =", url)
>> "%PROBE_FILE%" echo     print("ORCHESTRATOR_API_KEY set =", bool(api_key))
>> "%PROBE_FILE%" echo     client = OrchestratorClient(OrchestratorConfig(base_url=url, ws_url=ws_url, api_key=api_key))
>> "%PROBE_FILE%" echo     try:
>> "%PROBE_FILE%" echo         ok = await client.connect()
>> "%PROBE_FILE%" echo         print("Health check:", "OK" if ok else "FAILED")
>> "%PROBE_FILE%" echo         robots = await client.get_robots()
>> "%PROBE_FILE%" echo         print("Robots:", len(robots))
>> "%PROBE_FILE%" echo         for r in robots[:10]:
>> "%PROBE_FILE%" echo             print("-", r.id, r.name, getattr(r, "status", None), getattr(r, "environment", None))
>> "%PROBE_FILE%" echo     except Exception as e:
>> "%PROBE_FILE%" echo         print("ERROR:", type(e).__name__, str(e)[:400])
>> "%PROBE_FILE%" echo     finally:
>> "%PROBE_FILE%" echo         try:
>> "%PROBE_FILE%" echo             await client.disconnect()
>> "%PROBE_FILE%" echo         except Exception:
>> "%PROBE_FILE%" echo             pass
>> "%PROBE_FILE%" echo.
>> "%PROBE_FILE%" echo asyncio.run(main())
"%~dp0\.venv\Scripts\python.exe" "%PROBE_FILE%"
del "%PROBE_FILE%" >nul 2>nul
echo.
echo Done.
exit /b 0
