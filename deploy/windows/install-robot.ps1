<#
.SYNOPSIS
    CasareRPA Windows Robot Agent Installer

.DESCRIPTION
    Installs and configures the CasareRPA robot agent on Windows.
    Supports both interactive and silent installation modes.

.PARAMETER ControlPlaneUrl
    WebSocket URL of the CasareRPA control plane (required)

.PARAMETER RobotName
    Human-readable name for this robot (default: hostname)

.PARAMETER RobotId
    Unique robot identifier (auto-generated if not provided)

.PARAMETER InstallDir
    Installation directory (default: C:\CasareRPA)

.PARAMETER CertsDir
    Directory for mTLS certificates (default: InstallDir\certs)

.PARAMETER PythonVersion
    Python version to install (default: 3.12.0)

.PARAMETER Silent
    Run in silent mode (no prompts)

.PARAMETER InstallAsService
    Install robot agent as Windows service

.EXAMPLE
    .\install-robot.ps1 -ControlPlaneUrl "wss://api.casarerpa.com/ws/robot" -RobotName "Office-Robot-01"

.EXAMPLE
    .\install-robot.ps1 -ControlPlaneUrl "wss://api.casarerpa.com/ws/robot" -Silent -InstallAsService
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ControlPlaneUrl,

    [string]$RobotName = $env:COMPUTERNAME,

    [string]$RobotId = "",

    [string]$InstallDir = "C:\CasareRPA",

    [string]$CertsDir = "",

    [string]$PythonVersion = "3.12.0",

    [switch]$Silent,

    [switch]$InstallAsService
)

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$PYTHON_URL = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
$CASARE_RPA_VERSION = "3.0.0"
$SERVICE_NAME = "CasareRPARobot"
$SERVICE_DISPLAY_NAME = "CasareRPA Robot Agent"

if ([string]::IsNullOrEmpty($CertsDir)) {
    $CertsDir = Join-Path $InstallDir "certs"
}

# ============================================================================
# Functions
# ============================================================================

function Write-Banner {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  CasareRPA Robot Agent Installer v$CASARE_RPA_VERSION" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Gray
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[!] ERROR: $Message" -ForegroundColor Red
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Python {
    Write-Step "Checking Python installation..."

    $pythonPath = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonPath) {
        $version = & python --version 2>&1
        Write-Info "Python found: $version"

        # Check if version is 3.12+
        if ($version -match "3\.1[2-9]|3\.[2-9][0-9]") {
            Write-Info "Python version is compatible"
            return
        }
    }

    Write-Step "Installing Python $PythonVersion..."
    $installerPath = Join-Path $env:TEMP "python-installer.exe"

    try {
        Invoke-WebRequest -Uri $PYTHON_URL -OutFile $installerPath
        Write-Info "Downloaded Python installer"

        # Silent install with PATH update
        Start-Process -FilePath $installerPath -ArgumentList `
            "/quiet", `
            "InstallAllUsers=1", `
            "PrependPath=1", `
            "Include_pip=1", `
            "Include_test=0" `
            -Wait -NoNewWindow

        Write-Info "Python installed successfully"

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
                    [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
    finally {
        if (Test-Path $installerPath) {
            Remove-Item $installerPath -Force
        }
    }
}

function Create-InstallDirectory {
    Write-Step "Creating installation directory..."

    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        Write-Info "Created: $InstallDir"
    }
    else {
        Write-Info "Directory exists: $InstallDir"
    }

    # Create subdirectories
    $subdirs = @("certs", "logs", "data", "config")
    foreach ($dir in $subdirs) {
        $path = Join-Path $InstallDir $dir
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
    Write-Info "Created subdirectories: $($subdirs -join ', ')"
}

function Create-VirtualEnvironment {
    Write-Step "Creating Python virtual environment..."

    $venvPath = Join-Path $InstallDir "venv"

    if (Test-Path $venvPath) {
        Write-Info "Virtual environment exists, recreating..."
        Remove-Item $venvPath -Recurse -Force
    }

    & python -m venv $venvPath
    Write-Info "Created virtual environment: $venvPath"

    return $venvPath
}

function Install-CasareRPA {
    param([string]$VenvPath)

    Write-Step "Installing CasareRPA..."

    $pipPath = Join-Path $VenvPath "Scripts\pip.exe"

    # Upgrade pip
    & $pipPath install --upgrade pip

    # Install CasareRPA
    & $pipPath install casare-rpa

    # Install additional dependencies for robot agent
    & $pipPath install websockets cryptography pywin32

    Write-Info "CasareRPA installed successfully"
}

function Create-Configuration {
    Write-Step "Creating robot configuration..."

    $configPath = Join-Path $InstallDir "config\robot.json"

    # Generate robot ID if not provided
    if ([string]::IsNullOrEmpty($RobotId)) {
        $RobotId = "robot-" + [guid]::NewGuid().ToString().Substring(0, 12)
    }

    $config = @{
        control_plane_url = $ControlPlaneUrl
        robot_id = $RobotId
        robot_name = $RobotName
        certs_dir = $CertsDir
        capabilities = @{
            robot_type = "desktop"
            browser_types = @("chromium", "firefox")
            desktop_supported = $true
            max_concurrent_jobs = 1
            tags = @()
            os_info = "Windows $([System.Environment]::OSVersion.Version.ToString())"
            memory_mb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB)
            cpu_cores = (Get-CimInstance Win32_Processor).NumberOfCores
        }
        heartbeat_interval = 30
        log_level = "INFO"
        log_dir = Join-Path $InstallDir "logs"
    }

    $config | ConvertTo-Json -Depth 5 | Out-File -FilePath $configPath -Encoding UTF8
    Write-Info "Configuration saved: $configPath"
    Write-Info "Robot ID: $RobotId"
}

function Create-RunScript {
    Write-Step "Creating run script..."

    $scriptPath = Join-Path $InstallDir "run-robot.ps1"
    $venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
    $configPath = Join-Path $InstallDir "config\robot.json"

    $scriptContent = @"
# CasareRPA Robot Agent Runner
`$ErrorActionPreference = "Stop"

`$pythonPath = "$venvPython"
`$configPath = "$configPath"

Write-Host "Starting CasareRPA Robot Agent..."
Write-Host "Config: `$configPath"

& `$pythonPath -m casare_rpa.infrastructure.execution.distributed_robot --config `$configPath
"@

    $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8
    Write-Info "Run script created: $scriptPath"
}

function Install-WindowsService {
    Write-Step "Installing Windows service..."

    $venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
    $configPath = Join-Path $InstallDir "config\robot.json"

    # Check if NSSM is available or use native sc.exe
    $nssmPath = Get-Command nssm -ErrorAction SilentlyContinue

    if ($nssmPath) {
        # Use NSSM for better service management
        & nssm install $SERVICE_NAME $venvPython
        & nssm set $SERVICE_NAME AppParameters "-m casare_rpa.infrastructure.execution.distributed_robot --config `"$configPath`""
        & nssm set $SERVICE_NAME DisplayName $SERVICE_DISPLAY_NAME
        & nssm set $SERVICE_NAME Description "CasareRPA Robot Agent for desktop automation"
        & nssm set $SERVICE_NAME Start SERVICE_AUTO_START
        & nssm set $SERVICE_NAME AppStdout (Join-Path $InstallDir "logs\service-stdout.log")
        & nssm set $SERVICE_NAME AppStderr (Join-Path $InstallDir "logs\service-stderr.log")

        Write-Info "Service installed using NSSM"
    }
    else {
        # Create a wrapper script for native service
        $wrapperPath = Join-Path $InstallDir "service-wrapper.ps1"
        $wrapperContent = @"
`$pythonPath = "$venvPython"
`$configPath = "$configPath"
& `$pythonPath -m casare_rpa.infrastructure.execution.distributed_robot --config `$configPath
"@
        $wrapperContent | Out-File -FilePath $wrapperPath -Encoding UTF8

        # Use sc.exe to create service (requires additional work for proper service wrapper)
        Write-Info "NSSM not found. For proper Windows service installation, please install NSSM:"
        Write-Info "  choco install nssm"
        Write-Info "Or use Task Scheduler to run the robot at startup."
    }
}

function Create-TaskSchedulerEntry {
    Write-Step "Creating Task Scheduler entry for auto-start..."

    $taskName = "CasareRPARobot"
    $scriptPath = Join-Path $InstallDir "run-robot.ps1"

    # Remove existing task if present
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # Create action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

    # Create trigger (at logon)
    $trigger = New-ScheduledTaskTrigger -AtLogOn

    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    # Register task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "CasareRPA Robot Agent auto-start" `
        -RunLevel Highest | Out-Null

    Write-Info "Task Scheduler entry created: $taskName"
}

function Show-Summary {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installation Directory: $InstallDir" -ForegroundColor White
    Write-Host "Robot Name:            $RobotName" -ForegroundColor White
    Write-Host "Control Plane:         $ControlPlaneUrl" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Place your mTLS certificates in: $CertsDir" -ForegroundColor Gray
    Write-Host "     - ca.crt     (CA certificate)" -ForegroundColor Gray
    Write-Host "     - robot.crt  (Client certificate)" -ForegroundColor Gray
    Write-Host "     - robot.key  (Client private key)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Start the robot agent:" -ForegroundColor Gray
    Write-Host "     & `"$InstallDir\run-robot.ps1`"" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Or run as Windows service (requires NSSM):" -ForegroundColor Gray
    Write-Host "     net start $SERVICE_NAME" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================================
# Main
# ============================================================================

Write-Banner

# Check administrator privileges
if (-not (Test-Administrator)) {
    if (-not $Silent) {
        Write-Error-Message "This installer requires administrator privileges."
        Write-Host "Please run PowerShell as Administrator and try again."
        exit 1
    }
}

# Confirm installation
if (-not $Silent) {
    Write-Host "This will install CasareRPA Robot Agent with the following settings:"
    Write-Host ""
    Write-Host "  Control Plane URL: $ControlPlaneUrl"
    Write-Host "  Robot Name:        $RobotName"
    Write-Host "  Install Directory: $InstallDir"
    Write-Host ""

    $confirm = Read-Host "Continue? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Installation cancelled."
        exit 0
    }
}

try {
    # Step 1: Install Python if needed
    Install-Python

    # Step 2: Create installation directory
    Create-InstallDirectory

    # Step 3: Create virtual environment
    $venvPath = Create-VirtualEnvironment

    # Step 4: Install CasareRPA
    Install-CasareRPA -VenvPath $venvPath

    # Step 5: Create configuration
    Create-Configuration

    # Step 6: Create run script
    Create-RunScript

    # Step 7: Install as service or create scheduled task
    if ($InstallAsService) {
        Install-WindowsService
    }
    else {
        Create-TaskSchedulerEntry
    }

    # Show summary
    Show-Summary
}
catch {
    Write-Error-Message $_.Exception.Message
    Write-Host ""
    Write-Host "Installation failed. Please check the error above and try again."
    exit 1
}
