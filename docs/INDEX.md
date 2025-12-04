# CasareRPA Documentation

Welcome to the comprehensive documentation for **CasareRPA** - an enterprise Windows Desktop RPA platform with a visual node-based workflow editor and distributed execution.

## Quick Stats

| Metric | Count |
|--------|-------|
| **Automation Nodes** | 405 |
| **Node Categories** | 33 |
| **Python Files** | 720 |
| **Lines of Code** | 33,262 |
| **API Classes** | 1,445 |
| **Total Functions** | 10,015 |

## What is CasareRPA?

CasareRPA is an enterprise-grade RPA platform enabling Web (Playwright) and Desktop (UIAutomation) automation via drag-and-drop visual programming. Built on Clean Architecture (DDD) principles with distributed execution capabilities.

### Key Features

- **Visual Workflow Editor** - PySide6 + NodeGraphQt drag-and-drop canvas
- **Browser Automation** - Playwright (Chromium, Firefox, WebKit)
- **Desktop Automation** - Windows UIAutomation and Win32 APIs
- **Google Integration** - Calendar, Docs, Gmail, Sheets, Drive (116 nodes)
- **Messaging** - Telegram and WhatsApp platforms
- **AI/ML Nodes** - Multi-provider LLM integration via LiteLLM
- **Distributed Execution** - Robot agents with PostgreSQL job queue (PgQueuer)
- **Real-time Monitoring** - React dashboard with WebSocket updates
- **REST API** - FastAPI orchestrator with Swagger docs
- **Scheduling** - Cron-based workflow scheduling

### Enterprise Architecture

```
┌────────────┐   REST API    ┌─────────────────┐
│   Canvas   │──────────────→│ Orchestrator API│
│  (PySide6) │               │   (FastAPI)     │
└────────────┘               └────────┬────────┘
                                      │ PostgreSQL
                                      │ (PgQueuer)
                                      ▼
┌──────────────┐  WebSocket  ┌──────────────────┐
│  Monitoring  │◄────────────│   Robot Agent    │
│  Dashboard   │             │  (Distributed)   │
│   (React)    │             └──────────────────┘
└──────────────┘
```

## Documentation Sections

### Getting Started

- [Installation](getting-started/installation.md)
- [First Workflow](getting-started/first-workflow.md)
- [Core Concepts](getting-started/concepts.md)

### Node Reference (405 nodes)

Complete documentation for all automation nodes:

| Category | Nodes | Description |
|----------|-------|-------------|
| [Basic](nodes/basic/index.md) | 3 | Start, End, Comment |
| [Browser](nodes/browser/index.md) | 6 | Web automation with Playwright |
| [Desktop](nodes/desktop_nodes/index.md) | 48 | Windows desktop automation |
| [Control Flow](nodes/control-flow/index.md) | 12 | If, Loop, Switch, Try/Catch |
| [Data Operations](nodes/data/index.md) | 3 | Data extraction |
| [Dict Operations](nodes/dict/index.md) | 12 | Dictionary manipulation |
| [List Operations](nodes/list/index.md) | 14 | List/array operations |
| [File Operations](nodes/file/index.md) | 18 | File I/O, CSV, JSON, XML |
| [Database](nodes/database/index.md) | 10 | SQL operations |
| [Email](nodes/email/index.md) | 8 | SMTP/IMAP |
| [HTTP/REST](nodes/http/index.md) | 12 | API requests |
| [Google](nodes/google/index.md) | 116 | Calendar, Docs, Gmail, Sheets, Drive |
| [Messaging](nodes/messaging/index.md) | 18 | Telegram, WhatsApp |
| [Triggers](nodes/trigger_nodes/index.md) | 18 | Workflow triggers |
| [Error Handling](nodes/error-handling/index.md) | 37 | Try/Catch, Retry, Recovery |
| [Scripts](nodes/script/index.md) | 5 | Python/JavaScript execution |

[View All 33 Categories](nodes/index.md)

### API Reference

| Layer | Modules | Classes | Description |
|-------|---------|---------|-------------|
| [Domain](api/domain/index.md) | 55 | 118 | Pure business logic |
| [Application](api/application/index.md) | 37 | 120 | Use cases |
| [Infrastructure](api/infrastructure/index.md) | 128 | 576 | External integrations |
| [Presentation](api/presentation/index.md) | 162 | 631 | UI components |

[View Full API Reference](api/index.md)

### Orchestrator REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workflows` | POST | Submit workflow for execution |
| `/api/v1/workflows/{id}` | GET | Get workflow details |
| `/api/v1/schedules` | POST | Create cron schedule |
| `/api/v1/jobs` | GET | List job queue |
| `/api/v1/robots` | GET | List connected robots |
| `/api/v1/analytics/bottlenecks` | GET | Bottleneck detection |
| `/ws/live-jobs` | WS | Real-time job updates |

[View Orchestrator API Reference](api/infrastructure/orchestrator-api.md)

### User Guides

- [Browser Automation](guides/browser-automation.md) - Web scraping and interaction
- [Desktop Automation](guides/desktop-automation.md) - Windows UI automation
- [Google Integration](guides/google-integration.md) - Google Workspace APIs
- [Error Handling](guides/error-handling.md) - Resilient workflows
- [Data Processing](guides/data-processing.md) - CSV, JSON, Excel
- [Scheduling](guides/scheduling.md) - Cron-based execution
- [Deployment](guides/deployment.md) - Production deployment

### Function Inventory

Complete codebase audit for dead code analysis:

- [Inventory Overview](inventory/index.md) - 10,015 functions, 2,095 classes
- [Unused Functions](inventory/unused-functions.md) - **1,807 potentially unused**
- [Cross References](inventory/cross-references.md) - Call graph analysis

### Reference

- [Data Types](reference/data-types.md)
- [Port Types](reference/port-types.md)
- [Error Codes](reference/error-codes.md)
- [Keyboard Shortcuts](reference/keyboard-shortcuts.md)

## Architecture

CasareRPA follows Clean Architecture (DDD):

```
Presentation → Application → Domain ← Infrastructure
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.12+ | Core runtime |
| GUI | PySide6 | Desktop application |
| Graph Editor | NodeGraphQt | Node canvas |
| Browser | Playwright | Web automation |
| Desktop | UIAutomation | Windows automation |
| API Server | FastAPI | REST/WebSocket |
| Job Queue | PgQueuer | PostgreSQL-based queue |
| Dashboard | React 19 + Vite | Monitoring UI |
| Async | qasync | Qt + asyncio bridge |

## Execution Modes

| Mode | Shortcut | Description |
|------|----------|-------------|
| **Run Local** | F8 | Execute in Canvas process |
| **Run on Robot** | Ctrl+F5 | Submit to LAN robot |
| **Submit** | Ctrl+Shift+F5 | Queue for internet robots |

## Quick Start

```bash
# Start platform (API + Dashboard)
start_platform.bat    # Windows
./start_dev.sh        # Linux/Mac

# Start Canvas Designer
python run.py

# Start Robot Agent (optional)
python -m casare_rpa.robot.cli start
```

**URLs:**
- Canvas Designer: Desktop application
- Orchestrator API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Monitoring Dashboard: http://localhost:5173

## Version

- Documentation: 3.2.0
- Platform Version: v3.1.0
- Last Updated: 2025-12-04
