# CasareRPA - Project Overview

## Purpose
High-performance Windows Desktop RPA Platform with visual node-based workflow editor and clean architecture.

## Tech Stack
- **Language**: Python 3.12+
- **GUI**: PySide6 (Qt6), NodeGraphQt
- **Browser Automation**: Playwright 1.50+
- **Architecture**: DDD 2025 (Domain-Driven Design)
- **Async**: qasync for Qt event loop integration
- **Testing**: pytest, pytest-asyncio, pytest-qt
- **Linting**: ruff, black, mypy
- **Logging**: loguru
- **Desktop Automation**: uiautomation, pywin32
- **AI Integration**: anthropic, langchain, litellm

## Three Applications
1. **Canvas** (Designer): `src/casare_rpa/presentation/canvas/` - Visual workflow editor
2. **Robot** (Executor): `src/casare_rpa/infrastructure/robot/` - Headless runner
3. **Orchestrator** (Manager): `src/casare_rpa/infrastructure/orchestrator/` - Workflow scheduler

## Directory Structure
```
src/casare_rpa/
├── domain/              # Pure logic, entities, aggregates, events
├── application/         # Use cases, queries (CQRS)
├── infrastructure/      # Persistence, HTTP, adapters
│   ├── robot/          # Executor
│   └── orchestrator/   # Scheduler
├── presentation/        # UI, controllers
│   └── canvas/         # Visual editor
├── nodes/              # Node implementations (430+ nodes)
└── triggers/           # Workflow triggers
```

## Key Index Files (Read First!)
- `src/casare_rpa/nodes/_index.md` - Node registry
- `src/casare_rpa/presentation/canvas/visual_nodes/_index.md` - Visual nodes
- `src/casare_rpa/domain/_index.md` - Core entities, events
- `src/casare_rpa/presentation/canvas/_index.md` - Canvas overview

## Key Patterns
| Pattern | Location |
|---------|----------|
| EventBus | `domain/events.py` - `get_event_bus()` singleton |
| Typed Events | `domain/events/*.py` - Frozen dataclass events |
| Aggregates | `domain/aggregates/workflow.py` |
| Unit of Work | `infrastructure/persistence/unit_of_work.py` |
| UnifiedHttpClient | `infrastructure/http/` |
| Theme | `presentation/canvas/theme.py` - Use `THEME.*` only |

## Node System (Schema-Driven)
All 430+ nodes use:
```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")  # required
        timeout = self.get_parameter("timeout", 30000)  # optional (port->config)
```

NEVER use `self.config.get()` - use `get_parameter()` instead.
