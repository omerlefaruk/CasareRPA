<#
.SYNOPSIS
    Build script for CasareRPA Windows Installer

.DESCRIPTION
    Automates the build process for CasareRPA client installer:
    1. Installs/updates dependencies
    2. Runs PyInstaller to create executable
    3. Compiles NSIS installer
    4. Signs executable (if certificate available)

.PARAMETER Configuration
    Build configuration: Debug or Release (default: Release)

.PARAMETER IncludeBrowsers
    Include Playwright browsers in the installer (adds ~200MB)

.PARAMETER SignExecutable
    Sign the executable with code signing certificate

.PARAMETER CertificatePath
    Path to code signing certificate (.pfx)

.PARAMETER CertificatePassword
    Password for code signing certificate

.PARAMETER SkipTests
    Skip running tests before build

.PARAMETER Clean
    Clean build directories before building

.EXAMPLE
    .\build.ps1
    Build installer with default settings

.EXAMPLE
    .\build.ps1 -IncludeBrowsers -SignExecutable -CertificatePath "cert.pfx"
    Build with browsers and code signing

.NOTES
    Requirements:
    - Python 3.12+
    - PyInstaller
    - NSIS (Nullsoft Scriptable Install System)
    - (Optional) signtool.exe for code signing
#>

param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",

    [switch]$IncludeBrowsers,

    [switch]$SignExecutable,

    [string]$CertificatePath,

    [SecureString]$CertificatePassword,

    [switch]$SkipTests,

    [switch]$Clean
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName
$SrcDir = Join-Path $ProjectRoot "src"
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$InstallerDir = $ScriptDir
$AssetsDir = Join-Path $InstallerDir "assets"

# Version from pyproject.toml
$PyProjectPath = Join-Path $ProjectRoot "pyproject.toml"
$Version = "3.0.0"
if (Test-Path $PyProjectPath) {
    $Content = Get-Content $PyProjectPath -Raw
    if ($Content -match 'version\s*=\s*"([^"]+)"') {
        $Version = $Matches[1]
    }
}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "CasareRPA Installer Build Script" -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Cyan
Write-Host "Configuration: $Configuration" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Functions
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

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Test-Command {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# Check prerequisites
Write-Step "Checking Prerequisites"

# Python
if (-not (Test-Command "python")) {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}
$PythonVersion = python --version 2>&1
Write-Info "Python: $PythonVersion"

# Check Python version
$PythonVersionNum = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$PythonVersionNum -lt [version]"3.12") {
    Write-Error "Python 3.12 or higher is required (found $PythonVersionNum)"
    exit 1
}

# PyInstaller
if (-not (Test-Command "pyinstaller")) {
    Write-Warning "PyInstaller not found, installing..."
    pip install pyinstaller
}
Write-Info "PyInstaller: $(pyinstaller --version)"

# NSIS
$NsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
if (-not (Test-Path $NsisPath)) {
    $NsisPath = "C:\Program Files\NSIS\makensis.exe"
}
if (-not (Test-Path $NsisPath)) {
    # Try to find in PATH
    $NsisPath = (Get-Command "makensis" -ErrorAction SilentlyContinue).Source
}
if (-not $NsisPath -or -not (Test-Path $NsisPath)) {
    Write-Warning "NSIS not found. NSIS installer will not be built."
    Write-Warning "Download NSIS from: https://nsis.sourceforge.io/"
    $NsisPath = $null
} else {
    Write-Info "NSIS: $NsisPath"
}

# Clean if requested
if ($Clean) {
    Write-Step "Cleaning Build Directories"

    if (Test-Path $DistDir) {
        Write-Info "Removing $DistDir"
        Remove-Item -Recurse -Force $DistDir
    }
    if (Test-Path $BuildDir) {
        Write-Info "Removing $BuildDir"
        Remove-Item -Recurse -Force $BuildDir
    }
}

# Create directories
Write-Step "Creating Build Directories"
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
Write-Info "Created: $DistDir"
Write-Info "Created: $BuildDir"

# Install dependencies
Write-Step "Installing Dependencies"
Push-Location $ProjectRoot
try {
    pip install -e . --quiet
    Write-Info "Dependencies installed"
} finally {
    Pop-Location
}

# Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Step "Running Tests"
    Push-Location $ProjectRoot
    try {
        $TestResult = pytest tests/ -v --tb=short -q 2>&1
        $TestExitCode = $LASTEXITCODE

        if ($TestExitCode -ne 0) {
            Write-Warning "Some tests failed. Build will continue."
            Write-Info "Test output saved to: $BuildDir\test-results.log"
            $TestResult | Out-File "$BuildDir\test-results.log"
        } else {
            Write-Info "All tests passed"
        }
    } catch {
        Write-Warning "Test execution error: $_"
    } finally {
        Pop-Location
    }
} else {
    Write-Info "Tests skipped (-SkipTests)"
}

# Create assets if missing
Write-Step "Checking Assets"

# Create placeholder icon if missing
$IconPath = Join-Path $AssetsDir "casarerpa.ico"
if (-not (Test-Path $IconPath)) {
    Write-Info "Creating placeholder icon"
    # Create a simple ICO file header (empty icon)
    $IconBytes = [byte[]]@(
        0x00, 0x00,  # Reserved
        0x01, 0x00,  # Image type (1 = ICO)
        0x01, 0x00,  # Number of images
        # Image entry (16x16, 256 colors)
        0x10, 0x10,  # Width, Height
        0x00,        # Colors (0 = >256)
        0x00,        # Reserved
        0x01, 0x00,  # Color planes
        0x20, 0x00,  # Bits per pixel
        0x28, 0x01, 0x00, 0x00,  # Size of image data
        0x16, 0x00, 0x00, 0x00   # Offset to image data
    )
    New-Item -ItemType Directory -Force -Path $AssetsDir | Out-Null
    [System.IO.File]::WriteAllBytes($IconPath, $IconBytes)
    Write-Warning "Created placeholder icon - replace with actual icon before release"
}

# Create placeholder license
$LicensePath = Join-Path $AssetsDir "LICENSE.txt"
if (-not (Test-Path $LicensePath)) {
    $ProjectLicense = Join-Path $ProjectRoot "LICENSE"
    if (Test-Path $ProjectLicense) {
        Copy-Item $ProjectLicense $LicensePath
        Write-Info "Copied LICENSE to assets"
    } else {
        # Create MIT license
        $MitLicense = @"
MIT License

Copyright (c) 2024 CasareRPA Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@
        $MitLicense | Out-File -FilePath $LicensePath -Encoding UTF8
        Write-Info "Created MIT LICENSE"
    }
}

# Create placeholder banner images (164x314 for welcome, 150x57 for header)
$BannerPath = Join-Path $AssetsDir "installer-banner.bmp"
if (-not (Test-Path $BannerPath)) {
    Write-Warning "installer-banner.bmp not found - NSIS may show blank banner"
    Write-Info "Create 164x314 BMP image for welcome page banner"
}

$HeaderPath = Join-Path $AssetsDir "installer-header.bmp"
if (-not (Test-Path $HeaderPath)) {
    Write-Warning "installer-header.bmp not found - NSIS may show blank header"
    Write-Info "Create 150x57 BMP image for header"
}

# Run PyInstaller
Write-Step "Building Executable with PyInstaller"

$SpecFile = Join-Path $InstallerDir "casarerpa.spec"
if (-not (Test-Path $SpecFile)) {
    Write-Error "Spec file not found: $SpecFile"
    exit 1
}

# Set environment variable for including browsers
if ($IncludeBrowsers) {
    $env:CASARE_INCLUDE_BROWSERS = "1"
    Write-Info "Browser inclusion: ENABLED (adds ~200MB)"
} else {
    $env:CASARE_INCLUDE_BROWSERS = "0"
    Write-Info "Browser inclusion: DISABLED"
}

Push-Location $ProjectRoot
try {
    $PyInstallerArgs = @(
        $SpecFile,
        "--distpath", $DistDir,
        "--workpath", $BuildDir,
        "--noconfirm"
    )

    if ($Configuration -eq "Debug") {
        $PyInstallerArgs += "--debug=all"
    }

    Write-Info "Running: pyinstaller $($PyInstallerArgs -join ' ')"
    & pyinstaller @PyInstallerArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller build failed"
        exit 1
    }

    Write-Info "PyInstaller build completed"
} finally {
    Pop-Location
}

# Verify build output
$AppDir = Join-Path $DistDir "CasareRPA"
if (-not (Test-Path $AppDir)) {
    Write-Error "Build output not found: $AppDir"
    exit 1
}

$ExePath = Join-Path $AppDir "CasareRPA.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "Executable not found: $ExePath"
    exit 1
}

Write-Info "Build output: $AppDir"
$ExeSize = (Get-Item $ExePath).Length / 1MB
Write-Info "Executable size: $([math]::Round($ExeSize, 2)) MB"

# Sign executable (if requested)
if ($SignExecutable) {
    Write-Step "Signing Executable"

    if (-not $CertificatePath) {
        Write-Warning "No certificate path provided, skipping signing"
    } elseif (-not (Test-Path $CertificatePath)) {
        Write-Warning "Certificate not found: $CertificatePath"
    } else {
        $SignToolPath = (Get-Command "signtool" -ErrorAction SilentlyContinue).Source
        if (-not $SignToolPath) {
            # Try Windows SDK locations
            $SdkPaths = @(
                "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
                "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
            )
            foreach ($Path in $SdkPaths) {
                if (Test-Path $Path) {
                    $SignToolPath = $Path
                    break
                }
            }
        }

        if (-not $SignToolPath) {
            Write-Warning "signtool.exe not found. Install Windows SDK to enable signing."
        } else {
            Write-Info "Using signtool: $SignToolPath"

            $SignArgs = @(
                "sign",
                "/f", $CertificatePath,
                "/t", "http://timestamp.digicert.com",
                "/d", "CasareRPA",
                "/fd", "SHA256"
            )

            if ($CertificatePassword) {
                $PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
                    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($CertificatePassword)
                )
                $SignArgs += "/p"
                $SignArgs += $PlainPassword
            }

            $SignArgs += $ExePath

            & $SignToolPath @SignArgs

            if ($LASTEXITCODE -eq 0) {
                Write-Info "Executable signed successfully"
            } else {
                Write-Warning "Signing failed - continuing without signature"
            }
        }
    }
}

# Build NSIS installer
if ($NsisPath) {
    Write-Step "Building NSIS Installer"

    $NsiFile = Join-Path $InstallerDir "casarerpa.nsi"
    if (-not (Test-Path $NsiFile)) {
        Write-Error "NSIS script not found: $NsiFile"
    } else {
        Push-Location $InstallerDir
        try {
            $NsisArgs = @(
                "/DDIST_DIR=$AppDir",
                "/V3",  # Verbose level 3
                $NsiFile
            )

            Write-Info "Running: makensis $($NsisArgs -join ' ')"
            & $NsisPath @NsisArgs

            if ($LASTEXITCODE -ne 0) {
                Write-Warning "NSIS build failed - installer may be incomplete"
            } else {
                Write-Info "NSIS installer built successfully"
            }
        } finally {
            Pop-Location
        }
    }
}

# Summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "BUILD COMPLETE" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

Write-Host "Output files:" -ForegroundColor White
Write-Host "  Application: $AppDir" -ForegroundColor Gray

$InstallerFile = Join-Path $DistDir "CasareRPA-$Version-Setup.exe"
if (Test-Path $InstallerFile) {
    $InstallerSize = (Get-Item $InstallerFile).Length / 1MB
    Write-Host "  Installer:   $InstallerFile ($([math]::Round($InstallerSize, 2)) MB)" -ForegroundColor Gray
} else {
    Write-Host "  Installer:   (not built - NSIS required)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Test the application: $ExePath" -ForegroundColor Gray
Write-Host "  2. Run the installer to verify installation" -ForegroundColor Gray
Write-Host "  3. Sign the installer before distribution (if not already)" -ForegroundColor Gray
Write-Host ""
