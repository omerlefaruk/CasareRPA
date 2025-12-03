# CasareRPA Platform Launcher with Cloudflare Tunnel
# This script starts the tunnel first, captures the URL, then launches other components

$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  CasareRPA Platform Launcher (with Cloudflare Tunnel)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Check for venv
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found! Please run setup first." -ForegroundColor Red
    exit 1
}

# Check for cloudflared
$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "[ERROR] cloudflared not found in PATH." -ForegroundColor Red
    Write-Host "Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation"
    Write-Host ""
    Write-Host "Falling back to localhost-only mode..."

    # Launch without tunnel
    Start-Process wt -ArgumentList @(
        "-w", "0",
        "nt", "--title", "Orchestrator", "-d", ".", "cmd", "/k", ".\.venv\Scripts\python.exe manage.py orchestrator start --dev",
        ";", "nt", "--title", "Robot Agent", "-d", ".", "cmd", "/k", ".\.venv\Scripts\python.exe manage.py robot start",
        ";", "nt", "--title", "Canvas", "-d", ".", "cmd", "/k", ".\.venv\Scripts\python.exe manage.py canvas"
    )
    exit 0
}

Write-Host "[1/4] Starting Cloudflare Tunnel..." -ForegroundColor Yellow

# Start cloudflared and capture URL
$tunnelJob = Start-Job -ScriptBlock {
    $output = & cloudflared tunnel --url http://localhost:8000 2>&1
    $output
}

# Wait for tunnel URL (appears in stderr output)
$tunnelUrl = $null
$timeout = 30
$elapsed = 0

Write-Host "      Waiting for tunnel URL..." -ForegroundColor Gray

while ($elapsed -lt $timeout -and -not $tunnelUrl) {
    Start-Sleep -Milliseconds 500
    $elapsed += 0.5

    # Check job output
    $jobOutput = Receive-Job -Job $tunnelJob -ErrorAction SilentlyContinue
    if ($jobOutput) {
        foreach ($line in $jobOutput) {
            $lineStr = $line.ToString()
            # Look for the tunnel URL in output
            if ($lineStr -match "https://[a-zA-Z0-9\-]+\.trycloudflare\.com") {
                $tunnelUrl = $Matches[0]
                break
            }
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "[ERROR] Failed to get tunnel URL after ${timeout}s" -ForegroundColor Red
    Write-Host "Falling back to localhost..."
    Stop-Job -Job $tunnelJob -ErrorAction SilentlyContinue
    Remove-Job -Job $tunnelJob -Force -ErrorAction SilentlyContinue
    $tunnelUrl = "http://localhost:8000"
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  TUNNEL URL: $tunnelUrl" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

# Set environment variable for child processes
$env:CASARE_API_URL = $tunnelUrl

Write-Host "[2/4] Starting Orchestrator API (--dev mode)..." -ForegroundColor Yellow
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "manage.py", "orchestrator", "start", "--dev" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "[3/4] Starting Robot Agent..." -ForegroundColor Yellow
$env:CASARE_API_URL = $tunnelUrl
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "manage.py", "robot", "start" -WindowStyle Normal -Environment @{CASARE_API_URL=$tunnelUrl}

Start-Sleep -Seconds 1

Write-Host "[4/4] Starting Canvas Designer..." -ForegroundColor Yellow
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "manage.py", "canvas" -WindowStyle Normal -Environment @{CASARE_API_URL=$tunnelUrl}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  All components started!" -ForegroundColor Cyan
Write-Host "  Tunnel URL: $tunnelUrl" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel (other components will keep running)"
Write-Host ""

# Keep tunnel running in foreground
Wait-Job -Job $tunnelJob
