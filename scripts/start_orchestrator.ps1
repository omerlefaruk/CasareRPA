# CasareRPA Orchestrator Startup Script
# Starts all services + Cloudflare Tunnel (optional)
#
# Usage:
#   .\scripts\start_orchestrator.ps1                    # Local only (API + WebSocket)
#   .\scripts\start_orchestrator.ps1 -WithTunnel        # With Cloudflare Tunnel
#   .\scripts\start_orchestrator.ps1 -WithTunnel -Prod  # Production mode
#   .\scripts\start_orchestrator.ps1 -ApiOnly           # Only start FastAPI

param(
    [switch]$WithTunnel,   # Start cloudflared tunnel
    [switch]$Prod,         # Use production environment variables
    [switch]$ApiOnly,      # Only start FastAPI (no WebSocket server)
    [string]$TunnelName = "casare-rpa"  # Cloudflare tunnel name
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   CasareRPA Orchestrator Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Load production environment variables
if ($Prod) {
    Write-Host "[ENV] Loading production configuration..." -ForegroundColor Yellow
    $env:CASARE_API_URL = "https://api.casare.net"
    $env:CASARE_WEBHOOK_URL = "https://webhooks.casare.net"
    $env:CASARE_ROBOT_WS_URL = "wss://robots.casare.net"
    Write-Host "  API:      $env:CASARE_API_URL" -ForegroundColor Gray
    Write-Host "  Webhooks: $env:CASARE_WEBHOOK_URL" -ForegroundColor Gray
    Write-Host "  Robots:   $env:CASARE_ROBOT_WS_URL" -ForegroundColor Gray
} else {
    Write-Host "[ENV] Using local development configuration" -ForegroundColor Yellow
    Write-Host "  API:      http://localhost:8000" -ForegroundColor Gray
    Write-Host "  Webhooks: http://localhost:8766" -ForegroundColor Gray
    Write-Host "  Robots:   ws://localhost:8765" -ForegroundColor Gray
}
Write-Host ""

# Start Cloudflare Tunnel in background
$tunnelProcess = $null
if ($WithTunnel) {
    Write-Host "[TUNNEL] Starting Cloudflare Tunnel '$TunnelName'..." -ForegroundColor Green

    # Check if cloudflared is installed
    $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
    if (-not $cloudflared) {
        Write-Host "[ERROR] cloudflared not found. Install with: winget install Cloudflare.cloudflared" -ForegroundColor Red
        exit 1
    }

    # Start tunnel in background
    $tunnelProcess = Start-Process -FilePath "cloudflared" `
        -ArgumentList "tunnel", "run", $TunnelName `
        -WindowStyle Minimized `
        -PassThru

    Write-Host "  Tunnel PID: $($tunnelProcess.Id)" -ForegroundColor Gray
    Write-Host "  Waiting for tunnel to connect..." -ForegroundColor Gray
    Start-Sleep -Seconds 3

    if ($tunnelProcess.HasExited) {
        Write-Host "[ERROR] Tunnel failed to start. Check cloudflared configuration." -ForegroundColor Red
        exit 1
    }

    Write-Host "[TUNNEL] Connected!" -ForegroundColor Green
    Write-Host "  Public URLs:" -ForegroundColor Gray
    Write-Host "    - https://api.casare.net" -ForegroundColor Cyan
    Write-Host "    - https://webhooks.casare.net" -ForegroundColor Cyan
    Write-Host "    - wss://robots.casare.net" -ForegroundColor Cyan
}
Write-Host ""

# Start FastAPI server
Write-Host "[API] Starting FastAPI server on port 8000..." -ForegroundColor Green
Set-Location $ProjectRoot

try {
    # Run uvicorn directly (this will block)
    python -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000
}
catch {
    Write-Host ""
    Write-Host "[ERROR] API server failed: $_" -ForegroundColor Red
}
finally {
    # Cleanup tunnel on exit
    if ($tunnelProcess -and -not $tunnelProcess.HasExited) {
        Write-Host ""
        Write-Host "[TUNNEL] Stopping Cloudflare Tunnel..." -ForegroundColor Yellow
        Stop-Process -Id $tunnelProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[TUNNEL] Stopped" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[DONE] CasareRPA shutdown complete" -ForegroundColor Cyan
