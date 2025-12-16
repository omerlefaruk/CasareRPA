$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

Write-Host "Starting CasareRPA..."

# Check environment
if (Test-Path ".venv\Scripts\activate.bat") {
    $activate = ".venv\Scripts\activate.bat"
} else {
    Write-Host "Warning: .venv not found."
    $activate = ""
}

# Construct command wrapper
function Get-Cmd($script) {
    if ($activate) {
        return "cmd /k `"call $activate && python $script`""
    } else {
        return "cmd /k `"python $script`""
    }
}

function Get-Mod($module) {
    if ($activate) {
        return "cmd /k `"call $activate && python -m $module`""
    } else {
        return "cmd /k `"python -m $module`""
    }
}

# Try to find Windows Terminal
if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
    Write-Host "Launching in Windows Terminal tabs..."

    $cmdOrch = Get-Cmd "manage.py orchestrator start --dev"
    $cmdRobot = Get-Mod "casare_rpa.robot.tray_icon"
    $cmdCanvas = Get-Cmd "manage.py canvas"

    # Escape quotes for argument list
    # wt syntax: nt -d . [command] ; nt ...
    # We use single quotes for PS string, double quotes for internal

    $args = "-w 0 " +
            "nt --title 'Orchestrator' -d . $cmdOrch ; " +
            "nt --title 'Robot' -d . $cmdRobot ; " +
            "nt --title 'Canvas' -d . $cmdCanvas"

    # Add Tunnel if cloudflared is installed
    if (Get-Command cloudflared.exe -ErrorAction SilentlyContinue) {
        $tunnelName = $Env:CASARE_CLOUDFLARE_TUNNEL_NAME
        if (-not $tunnelName) { $tunnelName = "casare-rpa" }

        Write-Host "Adding Tunnel tab ($tunnelName)..."
        $cmdTunnel = "cmd /k `"cloudflared tunnel run $tunnelName`""
        $args += " ; nt --title 'Tunnel' -d . $cmdTunnel"
    } else {
        Write-Host "cloudflared not found, skipping Tunnel tab."
    }

    Start-Process wt.exe -ArgumentList $args
} else {
    Write-Host "Windows Terminal not found. Launching legacy windows..."
    if ($activate) {
        cmd /c "call $activate && python -m casare_rpa.launcher"
    } else {
        python -m casare_rpa.launcher
    }
}
