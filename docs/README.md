# CasareRPA Documentation

Technical reference documentation for the CasareRPA Windows Desktop RPA Platform.

## Documentation Index

### Architecture

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System overview, module structure, data flow, patterns |

### Application References

| Document | Description |
|----------|-------------|
| [CANVAS_REFERENCE.md](CANVAS_REFERENCE.md) | Visual workflow editor - UI components, node system, selectors |
| [ROBOT_REFERENCE.md](ROBOT_REFERENCE.md) | Executor agent - resilience patterns, checkpointing, offline queue |
| [ORCHESTRATOR_REFERENCE.md](ORCHESTRATOR_REFERENCE.md) | Job management - scheduling, dispatching, cloud integration |

### API & Nodes

| Document | Description |
|----------|-------------|
| [API_REFERENCE.md](API_REFERENCE.md) | Core types, BaseNode interface, ExecutionContext, events |
| [NODE_REFERENCE.md](NODE_REFERENCE.md) | All 35+ node types - browser, desktop, control flow, data |

## Quick Links

### Getting Started
- Run the application: `python run.py`
- Run tests: `pytest tests/ -v`
- Install dependencies: `pip install -e .`

### Build Executables
See [CLAUDE.md](../CLAUDE.md) for PyInstaller build commands.

### Development Status
See [DEVELOPMENT_ROADMAP.md](../DEVELOPMENT_ROADMAP.md) for current progress.

## Three Applications

```
+------------------+      +------------------+      +------------------+
|     CANVAS       |      |   ORCHESTRATOR   |      |      ROBOT       |
|  (Visual Editor) |----->| (Job Management) |----->| (Executor Agent) |
+------------------+      +------------------+      +------------------+
```

| App | Entry Point | Purpose |
|-----|-------------|---------|
| Canvas | `run.py` | Design workflows visually |
| Robot | `robot/tray_icon.py` | Execute workflows headlessly |
| Orchestrator | `orchestrator/main_window.py` | Manage robots and schedules |

## Technology Stack

- **Python 3.12+** - Core language
- **PySide6** - GUI framework
- **NodeGraphQt** - Node-based editor
- **Playwright** - Web automation
- **uiautomation** - Desktop automation
- **Supabase** - Cloud backend
- **qasync** - Qt + asyncio bridge
