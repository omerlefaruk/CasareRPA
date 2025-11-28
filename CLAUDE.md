# CLAUDE.md

- In all interactions and commit messages, be extremely concise and sacrifice grammar for the sake of concision.

## Estimation time
Never mention about estimated effort: Days and complexity ratings for each phase

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CasareRPA is a Windows Desktop RPA (Robotic Process Automation) platform with a visual node-based workflow editor. It enables web and desktop automation through a drag-and-drop interface built with PySide6 and NodeGraphQt.

**Current Status**: Production-ready with 140+ automation nodes, 1255+ tests, and comprehensive trigger system.

## Build & Run Commands

```powershell
# Run the application
python run.py

# Install dependencies (editable mode)
pip install -e .

## Architecture

CasareRPA follows **Clean Architecture** with Domain-Driven Design (DDD) principles:

### Layers

**Domain Layer** (`domain/`) - Pure business logic, zero dependencies
- **Entities**: Workflow, WorkflowMetadata, Node, Connection, ExecutionState, Project, Scenario
- **Value Objects**: DataType, Port, ExecutionResult, ExecutionStatus
- **Services**: ExecutionOrchestrator (routing), ProjectContext (variable resolution)
- No framework dependencies, 100% testable

**Application Layer** (`application/`) - Use cases and orchestration
- **Use Cases**: ExecuteWorkflowUseCase (coordinates domain + infrastructure)
- Depends on domain layer only
- Entry points for business operations

**Infrastructure Layer** (`infrastructure/`) - External integrations
- **Resources**: BrowserResourceManager (Playwright), DesktopResourceManager (UIAutomation)
- **Persistence**: ProjectStorage, WorkflowStorage (file system)
- **Adapters**: Wrappers for external libraries
- Implements domain interfaces

**Presentation Layer** (`presentation/`) - UI and user interaction
- **Canvas**: MainWindow + 9 controllers + 9 components + 16 UI components
- **Visual Nodes**: 141 nodes organized in 12 categories
- **EventBus**: 115+ event types for loose coupling
- Depends on application layer

### Directory Structure

```
src/casare_rpa/
├── domain/              # Pure business logic
│   ├── entities/        # Workflow, Project, ExecutionState
│   ├── services/        # ExecutionOrchestrator, ProjectContext
│   ├── value_objects/   # Port, DataType, ExecutionResult
│   └── repositories/    # Interfaces (no implementations)
│
├── application/         # Use cases
│   └── use_cases/       # ExecuteWorkflowUseCase
│
├── infrastructure/      # External integrations
│   ├── resources/       # Browser, Desktop managers
│   ├── persistence/     # File storage
│   └── adapters/        # External library wrappers
│
├── presentation/        # UI layer
│   └── canvas/          # Main application
│       ├── main_window.py       # UI coordination (~1,200 lines)
│       ├── controllers/         # 9 controllers (~2,500 lines)
│       ├── components/          # 9 components (~1,600 lines)
│       ├── ui/                  # 16 UI components (~5,000 lines)
│       ├── visual_nodes/        # 141 nodes by category
│       └── graph/               # NodeGraphQt integration
│
├── nodes/               # 242 node implementations (27 categories)
├── runner/              # Compatibility wrapper (deprecated)
└── core/                # Compatibility layer (v3.0 removal)
```

### Dependency Flow

```
Presentation → Application → Domain ← Infrastructure
```

**Rules**:
- Dependencies point inward only
- Domain has zero external dependencies
- Infrastructure implements domain interfaces
- Presentation coordinates via application layer

### Key Patterns

1. **Controller Pattern**: MainWindow delegates to 9 specialized controllers
2. **Component Pattern**: CasareRPAApp composed of 9 feature components
3. **EventBus**: Pub/sub for loose coupling (115+ event types)
4. **Use Case Pattern**: Application layer coordinates domain + infrastructure
5. **Repository Pattern**: Domain defines interfaces, infrastructure implements
6. **Value Objects**: Immutable data containers (Port, ExecutionResult)
7. **Async-First**: All Playwright operations async, Qt + asyncio via qasync
8. **Trigger System**: Registry-based (10 types: Manual, Scheduled, Webhook, FileWatch, Email, AppEvent, Form, Chat, Error, WorkflowCall)
9. **Connection Pooling**: Browser, database, HTTP session pooling
10. **Project Hierarchy**: Projects → Scenarios → Workflows with hierarchical scoping

### Node Categories (242 nodes across 27 categories)
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

**Current Coverage**: 525 tests, 60% node coverage (target: 100% by v3.0)

### Test Organization

```
tests/
├── nodes/                # Node execution tests
│   ├── desktop/         # 48 desktop automation nodes
│   ├── browser/         # 18 browser automation nodes
│   └── ...              # 27 node categories total
│
├── presentation/         # UI layer tests
│   └── canvas/
│       ├── controllers/ # 127 controller tests
│       ├── components/  # 42 component tests
│       └── ui/          # 74 UI widget tests
│
├── domain/              # Domain layer tests
│   ├── entities/        # Entity tests
│   └── services/        # Service tests
│
├── application/         # Application layer tests
│   └── use_cases/       # Use case tests
│
└── integration/         # End-to-end tests
```

### Running Tests

```powershell
# All tests
pytest tests/ -v

# Specific category
pytest tests/nodes/desktop/ -v

# With coverage
pytest --cov=casare_rpa tests/

# Controllers only
pytest tests/presentation/canvas/controllers/ -v

# Domain layer only
pytest tests/domain/ -v
```

### Test Metrics
- **Total Tests**: 525 (target: 1,400+ by v3.0)
- **Node Coverage**: 60% (145/242 nodes tested)
- **Presentation**: ~80% coverage
- **Domain**: 100% coverage
- **Application**: 100% coverage

## Development Status

Phases 1-8 complete. Currently adding advanced features:
- Trigger system (10 types implemented)
- Project management system
- Performance optimization with connection pooling
- Performance dashboard UI

## Refactoring Status

CasareRPA is undergoing a major refactoring to clean architecture (v2.x → v3.0).

### Completed (v2.1)
- ✅ Visual nodes organized (3,793 → 141 nodes in 26 files)
- ✅ Domain layer created (15 files, 3,201 lines)
- ✅ Infrastructure layer created (3 files, 673 lines)
- ✅ Application layer created (ExecuteWorkflowUseCase)
- ✅ WorkflowRunner refactored (1,404 → 518 lines wrapper)
- ✅ Controllers extracted (9 controllers, 2,500 lines)
- ✅ Components extracted (9 components, 1,600 lines)
- ✅ UI components library (16 components, 5,000 lines)
- ✅ EventBus system (115+ event types)
- ✅ CI/CD pipeline (GitHub Actions)

### In Progress (Week 4-7)
- 🔄 MainWindow controller integration (31% → 100%)
- 🔄 Test coverage expansion (17% → 60% → 100%)
- 🔄 Domain/Application layer tests
- 🔄 Performance optimization

### v3.0 Breaking Changes (TBD)
- Remove `core/` compatibility layer
- Remove `visual_nodes.py` (4,285 lines deprecated)
- Update all imports to use `domain/` directly
- Remove deprecation warnings

See [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) for complete details.

## Plans

- At the end of each plan, give me list of unresolved questions to answer, if any. Make the questions extremely consie. Sacrifice grammar for the sake of concision.
