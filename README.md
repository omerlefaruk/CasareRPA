# 🤖 CasareRPA - Windows Desktop RPA Platform

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython/)
[![Playwright](https://img.shields.io/badge/automation-Playwright-orange.svg)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

## 📋 Overview

**CasareRPA** is a high-performance, visual desktop RPA (Robotic Process Automation) platform built for Windows. It enables users to create powerful web automation workflows using an intuitive drag-and-drop node-based interface—no coding required.

### ✨ Key Features

- 🎨 **Visual Workflow Designer** - Drag-and-drop node-based editor powered by NodeGraphQt
- 🌐 **Modern Web Automation** - Fast, reliable browser automation using Microsoft Playwright
- ⚡ **Async Performance** - Non-blocking execution with qasync integration
- 🏗️ **Modular Architecture** - Decoupled designer and execution engine
- 📊 **High-Performance Logging** - Real-time execution logs with loguru
- 💾 **Fast Serialization** - Workflow save/load using orjson
- 🖥️ **Windows Optimized** - High-DPI support and native performance

---

## 🏗️ Architecture

```
CasareRPA/
├── src/casare_rpa/
│   ├── core/           # Base classes, schemas, and abstractions
│   ├── nodes/          # Node implementations (OpenBrowser, Click, etc.)
│   ├── gui/            # PySide6 UI components and windows
│   ├── runner/         # Execution engine and graph interpreter
│   └── utils/          # Configuration, logging, helpers
├── workflows/          # Saved workflow JSON files
├── logs/               # Application and execution logs
├── tests/              # Unit and integration tests
└── docs/               # Documentation
```

### 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.12+ | Core language |
| **GUI Framework** | PySide6 | Modern Qt-based interface |
| **Visual Logic** | NodeGraphQt | Node-based workflow editor |
| **Web Automation** | Playwright | Browser automation engine |
| **Async Bridge** | qasync | Qt + asyncio integration |
| **Serialization** | orjson | High-performance JSON |
| **Logging** | loguru | Advanced structured logging |

---

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.12 or higher**
- **pip** (Python package manager)

### Installation

1. **Clone the repository:**
```powershell
git clone https://github.com/yourusername/casare-rpa.git
cd casare-rpa
```

2. **Create a virtual environment:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

4. **Install Playwright browsers:**
```powershell
playwright install chromium
```

5. **Run the application:**
```powershell
python -m casare_rpa.main
```

---

## 📖 Development Guide

### Project Structure

#### **`src/casare_rpa/core/`**
Contains base classes and core abstractions:
- `BaseNode` - Abstract base class for all automation nodes
- `WorkflowSchema` - JSON schema definitions
- `ExecutionContext` - Runtime context and variable management

#### **`src/casare_rpa/nodes/`**
Node implementations for automation tasks:
- Browser nodes (Open, Close, Navigate)
- Interaction nodes (Click, Type, Select)
- Data nodes (GetText, GetAttribute, Screenshot)
- Control flow nodes (If, Loop, Wait)

#### **`src/casare_rpa/gui/`**
PySide6 GUI components:
- `MainWindow` - Primary application window
- `NodeEditor` - NodeGraphQt integration
- `PropertiesPanel` - Node configuration UI
- `LogViewer` - Execution log display

#### **`src/casare_rpa/runner/`**
Execution engine:
- `WorkflowRunner` - Interprets and executes workflow graphs
- `ExecutionEngine` - Manages node execution order
- `PlaywrightManager` - Handles browser lifecycle

#### **`src/casare_rpa/utils/`**
Utilities and configuration:
- `config.py` - Application settings and constants
- `logger.py` - Logging configuration
- `helpers.py` - Shared utility functions

### Configuration

Edit `src/casare_rpa/utils/config.py` to customize:
- Log retention and rotation
- Browser settings (headless, viewport size)
- Execution timeouts
- UI preferences

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=casare_rpa

# Run specific test file
pytest tests/test_foundation.py
```

---

## 🎯 Development Phases

### ✅ Phase 1: Foundation & Setup (Current)
- [x] Project structure
- [x] Dependency configuration
- [x] Logging setup
- [x] Documentation

### 🔄 Phase 2: Core Architecture (Next)
- [ ] BaseNode abstract class
- [ ] Workflow schema definition
- [ ] Basic runner structure
- [ ] Event system

### 📅 Phase 3: GUI Foundation
- [ ] PySide6 main window
- [ ] NodeGraphQt integration
- [ ] Async bridge (qasync)
- [ ] Basic toolbar

### 📅 Phase 4: Web Automation Nodes
- [ ] Playwright integration
- [ ] Core automation nodes
- [ ] Node property panels

### 📅 Phase 5: Execution Engine
- [ ] Complete runner implementation
- [ ] Graph traversal
- [ ] Error handling

### 📅 Phase 6: Advanced Features
- [ ] Workflow save/load
- [ ] Variable management
- [ ] Debugging tools

### 📅 Phase 7: Polish & Optimization
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Distribution packaging

---

## 🛠️ Code Style & Guidelines

### Type Hinting
All functions must use strict type hints:
```python
from typing import Optional, List, Dict, Any

def process_node(node_id: str, config: Dict[str, Any]) -> Optional[str]:
    """Process a workflow node."""
    pass
```

### Error Handling
Use robust try/except blocks with logging:
```python
from loguru import logger

try:
    result = execute_node()
except Exception as e:
    logger.error(f"Node execution failed: {e}")
    raise
```

### Async/Await
All Playwright operations must be async:
```python
async def click_element(page: Page, selector: str) -> None:
    await page.click(selector)
```

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please follow the development guidelines and submit pull requests for review.

---

## 📧 Contact

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ using Python, PySide6, and Playwright**
