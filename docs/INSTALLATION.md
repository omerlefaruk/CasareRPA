# CasareRPA Installation Guide

This guide covers installation of CasareRPA on Windows systems.

## System Requirements

### Minimum Requirements
- **Operating System:** Windows 10 (64-bit) or Windows 11
- **Python:** 3.12 or higher
- **RAM:** 4 GB (8 GB recommended)
- **Disk Space:** 2 GB free space
- **Display:** 1280x720 minimum resolution

### Recommended Requirements
- **RAM:** 16 GB for complex workflows
- **SSD:** For better performance with large workflows
- **Display:** 1920x1080 or higher for comfortable editing

## Installation Methods

### Method 1: Development Installation (Recommended for Developers)

1. **Clone the Repository**
   ```powershell
   git clone https://github.com/yourusername/casare-rpa.git
   cd casare-rpa
   ```

2. **Create Virtual Environment**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install in Editable Mode**
   ```powershell
   pip install -e .
   ```

4. **Install Playwright Browsers**
   ```powershell
   playwright install chromium
   # Optional: Install all browsers
   playwright install
   ```

5. **Run the Application**
   ```powershell
   python run.py
   ```

### Method 2: Package Installation

```powershell
pip install casare-rpa
playwright install chromium
```

### Method 3: Windows Installer (Coming Soon)

A standalone Windows installer will be available for non-technical users.

## Dependencies Overview

### Core Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | >=6.6.0 | GUI framework |
| NodeGraphQt | >=0.6.30 | Node graph editor |
| playwright | >=1.40.0 | Browser automation |
| qasync | >=0.27.0 | Qt + asyncio bridge |
| orjson | >=3.9.10 | Fast JSON serialization |
| loguru | >=0.7.2 | Logging |
| psutil | >=5.9.0 | Process monitoring |
| uiautomation | >=2.0.20 | Windows desktop automation |
| supabase | >=2.0.0 | Backend integration |
| python-dotenv | >=1.0.0 | Environment variables |
| hvac | >=2.1.0 | HashiCorp Vault client |

### Development Dependencies
```powershell
pip install -e ".[dev]"
```
- pytest, pytest-asyncio, pytest-qt for testing
- black for code formatting
- mypy for type checking

## Post-Installation Setup

### 1. Verify Installation

```powershell
# Check Python version
python --version  # Should be 3.12+

# Check Playwright installation
playwright --version

# Run tests to verify everything works
pytest tests/ -v --tb=short
```

### 2. First Launch

```powershell
python run.py
```

The Canvas (visual workflow editor) should open.

### 3. Configure Credentials (Optional)

For enterprise use with HashiCorp Vault:

1. Set environment variables in `.env`:
   ```
   VAULT_ADDR=https://your-vault-server:8200
   VAULT_TOKEN=your-token
   ```

2. Or use the Credential Manager in the application.

## Troubleshooting

### Common Issues

#### Issue: "No module named 'PySide6'"
**Solution:** Install PySide6 manually:
```powershell
pip install PySide6 PySide6-Addons
```

#### Issue: "qt.qpa.plugin: Could not find the Qt platform plugin"
**Solution:** Set the QT_QPA_PLATFORM_PLUGIN_PATH:
```powershell
$env:QT_QPA_PLATFORM_PLUGIN_PATH = "$env:VIRTUAL_ENV\Lib\site-packages\PySide6\plugins\platforms"
python run.py
```

#### Issue: "playwright._impl._errors.Error: Executable doesn't exist"
**Solution:** Install Playwright browsers:
```powershell
playwright install chromium
# If that fails, try:
python -m playwright install chromium
```

#### Issue: "ModuleNotFoundError: No module named 'casare_rpa'"
**Solution:** Install in editable mode from the project root:
```powershell
cd C:\path\to\casare-rpa
pip install -e .
```

#### Issue: Browser automation tests fail
**Solution:** Ensure browsers are installed and up to date:
```powershell
playwright install --with-deps chromium
```

#### Issue: Desktop automation not working
**Solution:**
1. Run as Administrator (some UI elements require elevated permissions)
2. Verify uiautomation is installed:
   ```powershell
   pip install uiautomation
   ```

#### Issue: "PermissionError" when accessing files
**Solution:**
1. Check if the file is locked by another process
2. Run PowerShell/Terminal as Administrator
3. Verify the path is within allowed directories

#### Issue: High memory usage
**Solution:**
1. Close unused browser tabs in the workflow
2. Reduce concurrent workflow executions
3. Enable viewport culling for large workflows (enabled by default)

### Logging

Logs are stored in:
- Windows: `%USERPROFILE%\.casare_rpa\logs\`

To enable debug logging:
```python
from loguru import logger
logger.add("debug.log", level="DEBUG")
```

### Getting Help

1. Check the [ERROR_CODES.md](./ERROR_CODES.md) for error solutions
2. Review the [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) guide
3. Open an issue on GitHub with:
   - Python version (`python --version`)
   - Windows version
   - Full error traceback
   - Steps to reproduce

## Upgrading

### From Source
```powershell
cd casare-rpa
git pull
pip install -e . --upgrade
playwright install chromium
```

### From pip
```powershell
pip install --upgrade casare-rpa
playwright install chromium
```

## Uninstallation

### Remove Package
```powershell
pip uninstall casare-rpa
```

### Remove Playwright Browsers
```powershell
playwright uninstall --all
```

### Remove User Data
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.casare_rpa"
```

## Building from Source

### Build Executables with PyInstaller

**Canvas (Main Editor):**
```powershell
pyinstaller --noconsole --noconfirm --name "CasareRPA-Canvas" `
  --add-data "src/casare_rpa;casare_rpa" `
  --hidden-import=PySide6.QtSvg `
  --hidden-import=PySide6.QtWidgets `
  --hidden-import=PySide6.QtGui `
  --hidden-import=PySide6.QtCore `
  --hidden-import=loguru `
  --hidden-import=psutil `
  --hidden-import=qasync `
  --hidden-import=NodeGraphQt `
  --hidden-import=Qt `
  --hidden-import=orjson `
  --hidden-import=playwright `
  --hidden-import=playwright.async_api `
  --hidden-import=playwright.sync_api `
  --hidden-import=uiautomation `
  --clean run.py
```

**Robot (Headless Executor):**
```powershell
pyinstaller --name="CasareRPA-Robot" --windowed --paths=src `
  --hidden-import=casare_rpa.robot `
  --hidden-import=casare_rpa.utils `
  --hidden-import=playwright `
  --hidden-import=PySide6 `
  --hidden-import=qasync `
  --hidden-import=loguru `
  --hidden-import=orjson `
  --hidden-import=psutil `
  --hidden-import=supabase `
  --onedir --clean src/casare_rpa/robot/tray_icon.py
```

**Orchestrator (Workflow Manager):**
```powershell
pyinstaller --name="CasareRPA-Orchestrator" --windowed --paths=src `
  --hidden-import=casare_rpa.orchestrator `
  --hidden-import=casare_rpa.utils `
  --hidden-import=PySide6 `
  --hidden-import=qasync `
  --hidden-import=loguru `
  --hidden-import=orjson `
  --hidden-import=playwright `
  --hidden-import=supabase `
  --onedir --clean src/casare_rpa/orchestrator/main_window.py
```

Executables will be created in the `dist/` directory.
