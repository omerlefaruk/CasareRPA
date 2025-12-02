<#
.SYNOPSIS
    Build CasareRPA Robot Agent Installer (Lightweight VM Deployment)

.DESCRIPTION
    Creates a standalone robot installer for VM deployment:
    1. Builds robot-only executable with PyInstaller
    2. Creates NSIS installer with pre-configured Supabase settings
    3. Output: dist/CasareRPA-Robot-3.0.0-Setup.exe

.PARAMETER SkipTests
    Skip running tests before build

.PARAMETER Clean
    Clean build directories before building

.EXAMPLE
    .\build_robot.ps1
    Build robot installer with default settings

.EXAMPLE
    .\build_robot.ps1 -Clean -SkipTests
    Clean build without tests (fastest)
#>

param(
    [switch]$SkipTests,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName
$SrcDir = Join-Path $ProjectRoot "src"
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$InstallerDir = $ScriptDir
$AssetsDir = Join-Path $InstallerDir "assets"

# Version
$Version = "3.0.0"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " CasareRPA Robot Installer Builder" -ForegroundColor Cyan
Write-Host " Version: $Version" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[STEP] $Message" -ForegroundColor Green
    Write-Host "-" * 50 -ForegroundColor DarkGray
}

function Write-Info {
    param([string]$Message)
    Write-Host "       $Message" -ForegroundColor Gray
}

# Check prerequisites
Write-Step "Checking Prerequisites"

# Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    exit 1
}
$PythonVersion = python --version 2>&1
Write-Info "Python: $PythonVersion"

# PyInstaller
if (-not (Get-Command "pyinstaller" -ErrorAction SilentlyContinue)) {
    Write-Host "[WARN] PyInstaller not found, installing..." -ForegroundColor Yellow
    pip install pyinstaller
}
Write-Info "PyInstaller: $(pyinstaller --version)"

# NSIS
$NsisPath = @(
    "C:\Program Files (x86)\NSIS\makensis.exe",
    "C:\Program Files\NSIS\makensis.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $NsisPath) {
    $NsisPath = (Get-Command "makensis" -ErrorAction SilentlyContinue).Source
}

if (-not $NsisPath) {
    Write-Host "[WARN] NSIS not found. Installer will not be built." -ForegroundColor Yellow
    Write-Host "       Download from: https://nsis.sourceforge.io/" -ForegroundColor Yellow
} else {
    Write-Info "NSIS: $NsisPath"
}

# Clean if requested
if ($Clean) {
    Write-Step "Cleaning Build Directories"
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    Write-Info "Cleaned"
}

# Create directories
Write-Step "Creating Build Directories"
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Force -Path $AssetsDir | Out-Null

# Create placeholder assets if missing
$IconPath = Join-Path $AssetsDir "casarerpa.ico"
if (-not (Test-Path $IconPath)) {
    Write-Info "Creating placeholder icon..."
    $IconBytes = [byte[]]@(0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x10, 0x10, 0x00, 0x00, 0x01, 0x00, 0x20, 0x00, 0x28, 0x01, 0x00, 0x00, 0x16, 0x00, 0x00, 0x00)
    [System.IO.File]::WriteAllBytes($IconPath, $IconBytes)
}

$LicensePath = Join-Path $AssetsDir "LICENSE.txt"
if (-not (Test-Path $LicensePath)) {
    $ProjectLicense = Join-Path $ProjectRoot "LICENSE"
    if (Test-Path $ProjectLicense) {
        Copy-Item $ProjectLicense $LicensePath
    } else {
        "MIT License`n`nCopyright (c) 2024 CasareRPA Team" | Out-File $LicensePath
    }
    Write-Info "Created LICENSE.txt"
}

# Install dependencies
Write-Step "Installing Dependencies"
Push-Location $ProjectRoot
try {
    pip install -e . --quiet
    pip install pyinstaller --quiet
    Write-Info "Dependencies installed"
} finally {
    Pop-Location
}

# Build with PyInstaller
Write-Step "Building Robot Executable"

$SpecFile = Join-Path $InstallerDir "casarerpa_robot.spec"
if (-not (Test-Path $SpecFile)) {
    Write-Host "[ERROR] Spec file not found: $SpecFile" -ForegroundColor Red
    exit 1
}

Push-Location $ProjectRoot
try {
    $PyInstallerArgs = @(
        $SpecFile,
        "--distpath", $DistDir,
        "--workpath", $BuildDir,
        "--noconfirm"
    )

    Write-Info "Running: pyinstaller $($PyInstallerArgs -join ' ')"
    & pyinstaller @PyInstallerArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] PyInstaller build failed" -ForegroundColor Red
        exit 1
    }

    Write-Info "PyInstaller build completed"
} finally {
    Pop-Location
}

# Verify build
$AppDir = Join-Path $DistDir "CasareRPA-Robot"
$ExePath = Join-Path $AppDir "CasareRPA-Robot.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "[ERROR] Executable not found: $ExePath" -ForegroundColor Red
    exit 1
}

$ExeSize = (Get-Item $ExePath).Length / 1MB
Write-Info "Executable: $ExePath ($([math]::Round($ExeSize, 2)) MB)"

# Build NSIS installer
if ($NsisPath) {
    Write-Step "Building NSIS Installer"

    $NsiFile = Join-Path $InstallerDir "casarerpa_robot.nsi"
    if (Test-Path $NsiFile) {
        Push-Location $InstallerDir
        try {
            $NsisArgs = @(
                "/DDIST_DIR=$AppDir",
                "/V3",
                $NsiFile
            )

            Write-Info "Running: makensis $($NsisArgs -join ' ')"
            & $NsisPath @NsisArgs

            if ($LASTEXITCODE -eq 0) {
                Write-Info "NSIS installer built successfully"
            } else {
                Write-Host "[WARN] NSIS build returned error code $LASTEXITCODE" -ForegroundColor Yellow
            }
        } finally {
            Pop-Location
        }
    }
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BUILD COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Output files:" -ForegroundColor White
Write-Host "  Executable:   $ExePath" -ForegroundColor Gray

$InstallerFile = Join-Path $DistDir "CasareRPA-Robot-$Version-Setup.exe"
if (Test-Path $InstallerFile) {
    $InstallerSize = (Get-Item $InstallerFile).Length / 1MB
    Write-Host "  Installer:    $InstallerFile ($([math]::Round($InstallerSize, 2)) MB)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Deploy to VM:" -ForegroundColor White
Write-Host "  1. Copy installer to VM" -ForegroundColor Gray
Write-Host "  2. Run installer, enter:" -ForegroundColor Gray
Write-Host "     - Database password: (your Supabase password)" -ForegroundColor Gray
Write-Host "     - API key: crpa_xxxxx (from setup)" -ForegroundColor Gray
Write-Host "  3. Robot starts automatically" -ForegroundColor Gray
Write-Host ""
