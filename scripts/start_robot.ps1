# CasareRPA Robot Client Startup Script
# Connects to orchestrator (local or via Cloudflare Tunnel)
#
# Usage:
#   .\scripts\start_robot.ps1                                    # Connect to local
#   .\scripts\start_robot.ps1 -Remote                            # Connect via tunnel
#   .\scripts\start_robot.ps1 -Remote -Token "your-token"        # With auth token
#   .\scripts\start_robot.ps1 -Url "wss://custom.example.com"    # Custom URL

param(
    [switch]$Remote,       # Use Cloudflare Tunnel URLs (wss://robots.casare.net)
    [string]$Url,          # Custom orchestrator WebSocket URL
    [string]$Token,        # Robot authentication token
    [string]$RobotName     # Custom robot name
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   CasareRPA Robot Client Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Determine orchestrator URL
if ($Url) {
    $orchestratorUrl = $Url
} elseif ($Remote) {
    $orchestratorUrl = "wss://robots.casare.net"
} else {
    $orchestratorUrl = "ws://localhost:8765"
}

Write-Host "[CONFIG] Robot Configuration" -ForegroundColor Yellow
Write-Host "  Orchestrator: $orchestratorUrl" -ForegroundColor Gray

# Set environment variables
$env:CASARE_ROBOT_WS_URL = $orchestratorUrl

if ($Token) {
    $env:CASARE_ROBOT_TOKEN = $Token
    Write-Host "  Auth Token:   [SET]" -ForegroundColor Gray
} else {
    Write-Host "  Auth Token:   [NOT SET]" -ForegroundColor Gray
}

if ($RobotName) {
    $env:CASARE_ROBOT_NAME = $RobotName
    Write-Host "  Robot Name:   $RobotName" -ForegroundColor Gray
}

Write-Host ""

# Check connection type
if ($orchestratorUrl.StartsWith("wss://")) {
    Write-Host "[SECURE] Using secure WebSocket (WSS) connection" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Using unencrypted WebSocket (WS) connection" -ForegroundColor Yellow
}
Write-Host ""

# Start robot client
Write-Host "[ROBOT] Connecting to orchestrator..." -ForegroundColor Green
Set-Location $ProjectRoot

try {
    python -m casare_rpa.robot_client
}
catch {
    Write-Host ""
    Write-Host "[ERROR] Robot client failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[DONE] Robot client shutdown" -ForegroundColor Cyan
