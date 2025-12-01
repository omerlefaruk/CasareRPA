# 🤖 CasareRPA - Enterprise Windows RPA Platform

[![CI Pipeline](https://github.com/omerlefaruk/CasareRPA/workflows/CI%20Pipeline/badge.svg)](https://github.com/omerlefaruk/CasareRPA/actions)
[![Tests](https://img.shields.io/badge/tests-3480%2B%20passing-success)](https://github.com/omerlefaruk/CasareRPA/actions)
[![codecov](https://codecov.io/gh/omerlefaruk/CasareRPA/branch/main/graph/badge.svg)](https://codecov.io/gh/omerlefaruk/CasareRPA)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/badge/linting-ruff-orange.svg)](https://github.com/astral-sh/ruff)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython/)
[![Playwright](https://img.shields.io/badge/automation-Playwright-orange.svg)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

## 📋 Overview

**CasareRPA** is an enterprise-grade, visual desktop RPA (Robotic Process Automation) platform for Windows. Create powerful web and desktop automation workflows using an intuitive drag-and-drop node-based interface—no coding required.

### ✨ Key Features

- 🎨 **Visual Workflow Designer** - Drag-and-drop node-based editor with 240+ automation nodes
- 🌐 **Web Automation** - Browser automation using Microsoft Playwright
- 🖥️ **Desktop Automation** - Windows UI automation via UIAutomation
- ⚡ **Async Execution** - Non-blocking execution with qasync integration
- 🏗️ **Clean Architecture** - Domain-Driven Design with layered architecture
- 🔄 **Distributed Execution** - Robot agents with job queue and orchestration
- 📊 **Monitoring Dashboard** - Real-time metrics via FastAPI + React
- 🔒 **Enterprise Security** - Input validation, parameterized queries, secure logging
- 🔐 **OAuth 2.0 Support** - Complete OAuth flows with PKCE, token exchange, and introspection
- 🐛 **Advanced Debugging** - Debug panel with call stack, watch expressions, breakpoints
- 📚 **Node Library Panel** - Searchable tree view of all nodes with drag-and-drop

---

## 🏗️ Architecture

CasareRPA follows **Clean Architecture** with Domain-Driven Design:

```
src/casare_rpa/
├── domain/             # Core business logic (entities, value objects, services)
├── application/        # Use cases and orchestration
├── infrastructure/     # External integrations (Playwright, DB, API)
├── presentation/       # UI components (Canvas, Controllers, Panels)
├── nodes/              # 240+ automation nodes (browser, desktop, data, etc.)
├── robot/              # Distributed execution agent
├── triggers/           # Event triggers (scheduled, webhook, file watch)
└── utils/              # Configuration, logging, helpers
```

### 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.12+ | Core language |
| **GUI Framework** | PySide6 | Qt-based visual designer |
| **Visual Logic** | NodeGraphQt | Node-based workflow editor |
| **Web Automation** | Playwright | Browser automation |
| **Desktop Automation** | UIAutomation | Windows UI control |
| **API Framework** | FastAPI | REST API + WebSocket |
| **Database** | PostgreSQL | Job queue, persistence |
| **Dashboard** | React + Vite | Monitoring UI |
| **Async Bridge** | qasync | Qt + asyncio integration |
| **Serialization** | orjson | High-performance JSON |
| **Logging** | loguru | Structured logging |

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

#### **`src/casare_rpa/domain/`**
Core business logic (no external dependencies):
- `entities/` - Workflow, Project, ExecutionState
- `value_objects/` - DataType, Port, ExecutionResult
- `services/` - ExecutionOrchestrator, ProjectContext

#### **`src/casare_rpa/application/`**
Use cases and orchestration:
- `use_cases/` - ExecuteWorkflowUseCase
- `orchestrator/` - OrchestratorEngine, services

#### **`src/casare_rpa/infrastructure/`**
External integrations:
- `orchestrator/api/` - FastAPI REST + WebSocket endpoints
- `resources/` - BrowserResourceManager
- `persistence/` - ProjectStorage, repositories
- `security/` - Input validators, workflow schema validation

#### **`src/casare_rpa/presentation/`**
UI components:
- `canvas/` - MainWindow, Controllers, Visual Nodes
- `orchestrator/` - Dashboard panels, views, widgets

#### **`src/casare_rpa/nodes/`**
240+ automation nodes across categories:
- Browser (navigate, click, type, extract)
- Desktop (window, element, keyboard, mouse)
- Data (JSON, XML, CSV, PDF, text operations)
- Control flow (if, loop, switch, try-catch)
- System (file, clipboard, process, services)

### Running the Application

```powershell
# Run Canvas Designer
python run.py

# Run Robot Agent
python -m casare_rpa.robot start

# Run Orchestrator API
python -m casare_rpa.infrastructure.orchestrator.api.main
```

### Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=casare_rpa

# Run specific layer tests
pytest tests/domain/ -v
pytest tests/nodes/ -v
```

---

## 🎯 Current Status

### ✅ Completed
- [x] Clean Architecture (Domain, Application, Infrastructure, Presentation)
- [x] Visual workflow designer with 240+ nodes
- [x] Browser automation (Playwright)
- [x] Desktop automation (UIAutomation)
- [x] Trigger system (scheduled, webhook, file watch)
- [x] Orchestrator with job queue
- [x] Robot distributed execution
- [x] Monitoring dashboard (FastAPI + React)
- [x] 3,480+ tests with comprehensive coverage
- [x] **OAuth 2.0 nodes** - Authorization, token exchange, callback server, introspection
- [x] **Debug panel** - Call stack, watch expressions, breakpoints, REPL console
- [x] **Node library panel** - Searchable tree with drag-and-drop
- [x] **VS Code-like shortcuts** - F5 run, F9 breakpoint, F10 step over
- [x] **Toolbar icons** - Theme-aware Qt standard icons

### 🔄 In Progress
- [ ] Multi-robot coordination
- [ ] Resource pooling (browser, DB, HTTP)
- [ ] Self-healing selectors (Tier 2+)
- [ ] Cloud deployment

---

## 🛠️ Code Style

- **Type hints**: All functions use strict type annotations
- **Async/await**: All I/O operations are async
- **Linting**: Ruff for fast Python linting
- **Formatting**: Black code style
- **Testing**: TDD approach with pytest

---

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/api/REST_API_REFERENCE.md)
- [Contributing](docs/development/CONTRIBUTING.md)
- [Security](docs/security/SECURITY_ARCHITECTURE.md)

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

**Built with Python, PySide6, Playwright, and FastAPI**
