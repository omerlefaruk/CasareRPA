# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CasareRPA is a Windows Desktop RPA (Robotic Process Automation) platform with a visual node-based workflow editor. It enables web and desktop automation through a drag-and-drop interface built with PySide6 and NodeGraphQt.

## Build & Run Commands

```powershell
# Run the application
python run.py

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_control_flow.py -v

# Run tests with coverage
pytest --cov=casare_rpa tests/

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for web automation)
playwright install chromium
```

## Build Executables (PyInstaller)

```powershell
# Canvas (main visual editor)
pyinstaller --noconsole --noconfirm --name "CasareRPA-Canvas" --add-data "src/casare_rpa;casare_rpa" --hidden-import=PySide6.QtSvg --hidden-import=PySide6.QtWidgets --hidden-import=PySide6.QtGui --hidden-import=PySide6.QtCore --hidden-import=loguru --hidden-import=psutil --hidden-import=qasync --hidden-import=NodeGraphQt --hidden-import=Qt --hidden-import=orjson --hidden-import=playwright --hidden-import=uiautomation --clean run.py

# Robot (headless executor)
pyinstaller --name="CasareRPA-Robot" --windowed --paths=src --hidden-import=casare_rpa.robot --hidden-import=casare_rpa.utils --hidden-import=playwright --hidden-import=PySide6 --hidden-import=qasync --onedir --clean src/casare_rpa/robot/tray_icon.py

# Orchestrator (workflow manager)
pyinstaller --name="CasareRPA-Orchestrator" --windowed --paths=src --hidden-import=casare_rpa.orchestrator --hidden-import=casare_rpa.utils --hidden-import=PySide6 --hidden-import=qasync --onedir --clean src/casare_rpa/orchestrator/main_window.py
```

## Architecture

The codebase follows a modular architecture with three main applications:

### Applications
- **Canvas** (`src/casare_rpa/canvas/`): Main visual workflow editor with NodeGraphQt integration
- **Robot** (`src/casare_rpa/robot/`): Headless workflow executor with system tray icon
- **Orchestrator** (`src/casare_rpa/orchestrator/`): Workflow management and scheduling UI

### Core Modules
- **`core/`**: Base classes (`BaseNode`), schemas, and execution context
- **`nodes/`**: Node implementations (browser, control flow, data operations, error handling, desktop)
- **`gui/`**: PySide6 UI components including visual node wrappers, minimap, debug toolbar
- **`runner/`**: Workflow execution engine, graph traversal, debug manager
- **`desktop/`**: Windows desktop automation using `uiautomation` library
- **`recorder/`**: Action recording functionality
- **`utils/`**: Configuration, logging (loguru), hotkeys, fuzzy search

### Key Patterns
- All Playwright operations must be async (use `async/await`)
- Nodes have two parts: logic class in `nodes/` and visual wrapper in `gui/visual_nodes/`
- Qt event loop integrates with asyncio via `qasync`
- Workflows are saved as JSON in `workflows/` directory

## Technology Stack

- **Python 3.12+** with strict type hints
- **PySide6** for GUI
- **NodeGraphQt** for node-based editor
- **Playwright** for web automation
- **uiautomation** for Windows desktop automation
- **qasync** for Qt + asyncio bridge
- **orjson** for fast JSON serialization
- **loguru** for logging

## Development Status

Phases 1-6 complete. Currently in Phase 7: Windows Desktop Automation (see `DEVELOPMENT_ROADMAP.md` for details).
