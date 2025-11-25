# CasareRPA Installer Build System

This directory contains the installer build scripts and configurations for CasareRPA.

## Directory Structure

```
installer/
├── inno/                    # Inno Setup files (Developer Installer)
│   ├── casarerpa-dev.iss   # Main Inno Setup script
│   ├── banner.bmp          # Wizard banner image (164x314 pixels)
│   ├── wizard.bmp          # Small wizard image (55x58 pixels)
│   └── icon.ico            # Application icon
├── wix/                     # WiX files (Robot MSI - coming soon)
│   ├── Product.wxs         # Main WiX source
│   ├── Service.wxs         # Windows Service component
│   └── Variables.wxi       # Build variables
├── output/                  # Build output directory
├── build_dev_installer.py  # Developer installer build script
└── build_robot_msi.ps1     # Robot MSI build script (coming soon)
```

## Prerequisites

1. **Python 3.12+** with dependencies installed
2. **PyInstaller**: `pip install pyinstaller`
3. **Inno Setup 6**: Download from https://jrsoftware.org/isdl.php
4. **WiX Toolset** (for MSI): Download from https://wixtoolset.org/

## Building the Developer Installer

```powershell
# Full build (PyInstaller + Inno Setup)
python installer/build_dev_installer.py

# Skip PyInstaller if dist/ already built
python installer/build_dev_installer.py --skip-pyinstaller

# Custom version
python installer/build_dev_installer.py --version 1.0.0

# Sign executables (requires code signing certificate)
python installer/build_dev_installer.py --sign
```

## Required Images

Before building, you need to create the following images:

### banner.bmp (164x314 pixels)
- Displayed on the left side of installer wizard pages
- Should contain CasareRPA branding
- Format: BMP, 24-bit color

### wizard.bmp (55x58 pixels)
- Small icon displayed in wizard header
- Usually contains the application icon
- Format: BMP, 24-bit color

### icon.ico
- Application icon (multi-resolution)
- Should include: 16x16, 32x32, 48x48, 256x256 sizes
- Format: ICO

## Installation Types

The developer installer supports multiple installation types:

| Type | Components | Use Case |
|------|------------|----------|
| Full | Canvas + Orchestrator + Robot | Developers |
| Compact | Canvas only | Workflow designers |
| Robot Only | Robot only | Client PCs |
| Custom | User selects | Flexible deployment |

## Output

Built installers are placed in `installer/output/`:
- `CasareRPA-Setup-{version}.exe` - Developer installer
- `CasareRPA-Robot-{version}.msi` - Robot MSI (coming soon)

## Silent Installation

```powershell
# Install all components silently
CasareRPA-Setup-1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES

# Install Canvas only
CasareRPA-Setup-1.0.0.exe /VERYSILENT /COMPONENTS="canvas"

# Install Robot only
CasareRPA-Setup-1.0.0.exe /VERYSILENT /COMPONENTS="robot"
```
