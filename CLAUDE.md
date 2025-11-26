# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CasareRPA is a Windows Desktop RPA (Robotic Process Automation) platform with a visual node-based workflow editor. It enables web and desktop automation through a drag-and-drop interface built with PySide6 and NodeGraphQt.

**Current Status**: Production-ready with 140+ automation nodes, 1255+ tests, and comprehensive trigger system.

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

# Install dependencies (editable mode)
pip install -e .

# Install Playwright browsers (required for web automation)
playwright install chromium
```

## Build Executables (PyInstaller)

```powershell
# Canvas (main visual editor)
pyinstaller --noconsole --noconfirm --name "CasareRPA-Canvas" \
  --add-data "src/casare_rpa;casare_rpa" \
  --hidden-import=PySide6.QtSvg \
  --hidden-import=PySide6.QtWidgets \
  --hidden-import=PySide6.QtGui \
  --hidden-import=PySide6.QtCore \
  --hidden-import=loguru \
  --hidden-import=psutil \
  --hidden-import=qasync \
  --hidden-import=NodeGraphQt \
  --hidden-import=Qt \
  --hidden-import=orjson \
  --hidden-import=playwright \
  --hidden-import=playwright.async_api \
  --hidden-import=playwright.sync_api \
  --hidden-import=uiautomation \
  --clean run.py

# Robot (headless executor)
pyinstaller --name="CasareRPA-Robot" --windowed --paths=src \
  --hidden-import=casare_rpa.robot \
  --hidden-import=casare_rpa.utils \
  --hidden-import=playwright \
  --hidden-import=PySide6 \
  --hidden-import=qasync \
  --hidden-import=loguru \
  --hidden-import=orjson \
  --hidden-import=psutil \
  --hidden-import=supabase \
  --onedir --clean src/casare_rpa/robot/tray_icon.py

# Orchestrator (workflow manager)
pyinstaller --name="CasareRPA-Orchestrator" --windowed --paths=src \
  --hidden-import=casare_rpa.orchestrator \
  --hidden-import=casare_rpa.utils \
  --hidden-import=PySide6 \
  --hidden-import=qasync \
  --hidden-import=loguru \
  --hidden-import=orjson \
  --hidden-import=playwright \
  --hidden-import=supabase \
  --onedir --clean src/casare_rpa/orchestrator/main_window.py
```

## Architecture

The codebase follows a modular architecture with three main applications:

### Applications
- **Canvas** (`src/casare_rpa/canvas/`): Main visual workflow editor with NodeGraphQt integration
- **Robot** (`src/casare_rpa/robot/`): Headless workflow executor with system tray icon
- **Orchestrator** (`src/casare_rpa/orchestrator/`): Workflow management, scheduling, and multi-robot coordination

### Core Modules
- **`core/`**: Base classes (`BaseNode`), schemas, execution context, port type system, trigger schemas
- **`nodes/`**: 140+ node implementations across 27 categories (browser, control flow, data operations, error handling, desktop, file, HTTP, database, email, etc.)
- **`canvas/`**: PySide6 UI components including visual node wrappers, minimap, debug toolbar, trigger management, project panel
- **`runner/`**: Workflow execution engine, graph traversal, debug manager
- **`triggers/`**: Event-driven trigger system (scheduled, webhook, file watch, email, etc.)
- **`project/`**: Project management (projects, scenarios, workflows hierarchy)
- **`scheduler/`**: APScheduler-based workflow scheduling with execution history
- **`desktop/`**: Windows desktop automation using `uiautomation` library
- **`recorder/`**: Action recording functionality
- **`utils/`**: Configuration, logging (loguru), hotkeys, fuzzy search, connection pooling, performance metrics

### Node Categories (140+ nodes)
| Category | Count | Description |
|----------|-------|-------------|
| Basic | 3 | Start, End, Comment |
| Browser | 5 | Launch, Close, NewTab, etc. |
| Navigation | 4 | GoToURL, Back, Forward, Refresh |
| Interaction | 3 | Click, Type, Select |
| Data Extraction | 3 | ExtractText, GetAttribute, Screenshot |
| Wait | 3 | Wait, WaitForElement, WaitForNavigation |
| Variables | 3 | SetVar, GetVar, Increment |
| Control Flow | 8 | If, For, While, Switch, Break, Continue |
| Error Handling | 10 | Try/Catch, Retry, Throw, Assert, etc. |
| Data Operations | 23 | String, Math, List, Dict, JSON |
| File System | 16 | Read, Write, CSV, JSON, ZIP |
| HTTP/REST | 12 | GET, POST, PUT, PATCH, DELETE, Auth |
| Database | 10 | Connect, Query, Transaction |
| Email | 8 | Send, Read, Filter, Attachments |
| System | 13 | Clipboard, Dialogs, Services |
| Text | 14 | Split, Replace, Trim, Case, etc. |
| DateTime | 7 | Now, Format, Parse, Add, Diff |
| Random | 5 | Number, Choice, String, UUID |
| XML | 8 | Parse, XPath, Convert |
| PDF | 6 | Read, Merge, Split, Extract |
| FTP | 10 | Connect, Upload, Download, List |
| Scripts | 5 | Python, JavaScript, PowerShell |
| Desktop | 50+ | Application, Window, Element, Mouse, Keyboard, Office |

### Key Patterns

1. **Async-First Architecture**
   - All Playwright operations must be async (use `async/await`)
   - DesktopContext supports async context management
   - Qt event loop integrates with asyncio via `qasync`

2. **Node Structure**
   - Logic class in `nodes/` (inherits from `BaseNode`)
   - Visual wrapper in `canvas/visual_nodes/` (inherits from `BaseVisualNode`)
   - Lazy loading via `nodes/__init__.py`

3. **Trigger System** (Registry-based)
   - `triggers/base.py`: BaseTrigger abstract class, TriggerEvent dataclass
   - `triggers/registry.py`: Dynamic trigger type registration
   - `triggers/manager.py`: Central coordination, event routing
   - 10 trigger types: Manual, Scheduled, Webhook, FileWatch, Email, AppEvent, Form, Chat, Error, WorkflowCall

4. **Project Hierarchy**
   - Projects contain Scenarios
   - Scenarios contain Workflows
   - Hierarchical variable/credential scoping

5. **Connection Pooling**
   - `utils/browser_pool.py`: Browser context pooling
   - `utils/database_pool.py`: Database connection pooling
   - `utils/http_session_pool.py`: HTTP session pooling

6. **Persistence**
   - Workflows saved as JSON in `workflows/` directory
   - Projects saved in `~/.casare_rpa/projects/`
   - Schedules saved in `~/.casare_rpa/canvas/schedules.json`
   - Triggers persisted with workflow files

## Technology Stack

- **Python 3.12+** with strict type hints
- **PySide6** for GUI
- **NodeGraphQt** for node-based editor
- **Playwright** for web automation
- **uiautomation** for Windows desktop automation
- **qasync** for Qt + asyncio bridge
- **orjson** for fast JSON serialization
- **loguru** for logging
- **APScheduler** for workflow scheduling
- **aiohttp** for async HTTP
- **asyncpg/aiomysql** for async database connections

## Testing

- **Total Tests**: 1255+
- **Test Coverage**: All node types, UI components, triggers, scheduler, performance
- **Run Tests**: `pytest tests/ -v`
- **With Coverage**: `pytest --cov=casare_rpa tests/`

## Development Status

Phases 1-8 complete. Currently adding advanced features:
- Trigger system (10 types implemented)
- Project management system
- Performance optimization with connection pooling
- Performance dashboard UI

See `DEVELOPMENT_ROADMAP.md` for full details.
