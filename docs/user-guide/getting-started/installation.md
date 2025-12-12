# Installation Guide

This guide walks you through installing CasareRPA on your Windows computer.

## System Requirements

Before installing CasareRPA, ensure your system meets these requirements:

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Operating System | Windows 10 (64-bit) | Windows 11 (64-bit) |
| Python | 3.12+ | 3.12.x |
| RAM | 8 GB | 16 GB |
| Disk Space | 2 GB | 5 GB |
| Display | 1280x720 | 1920x1080 |

> **Note:** CasareRPA is designed specifically for Windows. macOS and Linux are not supported.

## Prerequisites

### 1. Install Python 3.12+

If Python is not already installed:

1. Download Python 3.12 from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important:** Check "Add Python to PATH" during installation
4. Click "Install Now"

To verify installation, open Command Prompt and run:

```cmd
python --version
```

You should see `Python 3.12.x` or higher.

### 2. Install Git (Optional)

Git is recommended for cloning the repository:

1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer with default settings

## Installation Steps

### Step 1: Get CasareRPA

**Option A: Clone with Git**

```cmd
git clone https://github.com/your-org/casare-rpa.git
cd casare-rpa
```

**Option B: Download ZIP**

1. Download the CasareRPA ZIP file
2. Extract to a folder (e.g., `C:\CasareRPA`)
3. Open Command Prompt and navigate to the folder:

```cmd
cd C:\CasareRPA
```

### Step 2: Create Virtual Environment (Recommended)

Creating a virtual environment keeps CasareRPA dependencies isolated:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` at the start of your command prompt.

### Step 3: Install CasareRPA

Install CasareRPA in development mode:

```cmd
pip install -e .
```

This installs all required dependencies:
- **PySide6** - Qt-based user interface
- **Playwright** - Browser automation
- **NodeGraphQt** - Visual node editor
- **And more...**

> **Note:** This may take several minutes on first install.

### Step 4: Install Playwright Browsers

CasareRPA uses Playwright for browser automation. Install the browser binaries:

```cmd
playwright install
```

This downloads Chromium, Firefox, and WebKit browsers.

## Running CasareRPA

After installation, start CasareRPA with:

```cmd
python run.py
```

Or use the CLI:

```cmd
casare canvas
```

[Screenshot: CasareRPA Canvas main window opening for the first time]

## Setup Wizard

On first launch, CasareRPA displays a setup wizard that helps you configure:

1. **Project Location** - Where to store your workflows
2. **Browser Settings** - Default browser type and headless mode
3. **API Keys** - Optional AI assistant configuration
4. **Theme** - Light or dark interface theme

[Screenshot: Setup wizard first screen]

You can access these settings later from **Edit > Preferences**.

## Verifying Installation

To confirm CasareRPA is working correctly:

1. Launch CasareRPA with `python run.py`
2. The Canvas window should open
3. The Node Palette (left panel) should show available nodes
4. Try dragging a **Start** node onto the canvas

[Screenshot: Dragging Start node onto canvas]

If these steps work, your installation is successful.

## Quick Verification Commands

Run these commands to verify components are installed:

```cmd
# Check Python version
python --version

# Check PySide6
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"

# Check Playwright
python -c "import playwright; print('Playwright OK')"

# Check CasareRPA
python -c "import casare_rpa; print('CasareRPA OK')"
```

All commands should complete without errors.

## Troubleshooting Common Issues

### "Python is not recognized"

**Cause:** Python is not in your system PATH.

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or add Python manually to PATH:
   - Search "Environment Variables" in Windows
   - Edit PATH variable
   - Add `C:\Users\<YourName>\AppData\Local\Programs\Python\Python312`

### "pip install fails with permission error"

**Cause:** Installing to system Python without admin rights.

**Solution:** Use a virtual environment (Step 2) or run Command Prompt as Administrator.

### "Module not found: PySide6"

**Cause:** Dependencies not installed or wrong Python environment.

**Solution:**
1. Ensure virtual environment is activated: `.venv\Scripts\activate`
2. Reinstall: `pip install -e .`

### "Playwright browser launch fails"

**Cause:** Browser binaries not installed.

**Solution:**
```cmd
playwright install chromium
```

### "Canvas window is blank or frozen"

**Cause:** Graphics driver issue with OpenGL.

**Solution:**
1. Update your graphics drivers
2. Try running with software rendering:
   ```cmd
   set QT_QUICK_BACKEND=software
   python run.py
   ```

### "ImportError on startup"

**Cause:** Missing or incompatible dependencies.

**Solution:**
```cmd
pip install --upgrade pip
pip install -e . --force-reinstall
```

## Uninstalling CasareRPA

To remove CasareRPA:

1. Delete the CasareRPA folder
2. Optionally, uninstall Playwright browsers:
   ```cmd
   playwright uninstall
   ```

## Next Steps

Now that CasareRPA is installed, continue to:

- [Creating Your First Workflow](first-workflow.md) - Build a simple automation
- [Canvas Overview](canvas-overview.md) - Learn the interface
- [Quickstart Examples](quickstart-examples.md) - Try example workflows

---

> **Need Help?** If you encounter issues not covered here, check the project's GitHub Issues or documentation.
