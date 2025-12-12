# CasareRPA

Windows RPA platform | Python 3.12 | PySide6 | Playwright | DDD 2025 Architecture

## Quick Commands
```bash
python run.py                              # Run app
pytest tests/ -v                           # Tests
pip install -e .                           # Dev install
python scripts/index_codebase_qdrant.py    # Re-index for semantic search
```

## Search Strategy (Qdrant vs Grep)

| Use Case | Tool | Why |
|----------|------|-----|
| Explore patterns/architecture | **qdrant-find** | Semantic, finds related concepts |
| Understand how X works | **qdrant-find** | Returns full context chunks |
| Find exact symbol/string | **Grep** | Faster, precise matches |
| Find specific class/function | **Grep** | Direct name lookup |

### Qdrant (Semantic Search) - ~500ms
```
qdrant-find: "browser automation pattern"    # Finds BrowserBaseNode + related
qdrant-find: "error handling implementation" # Finds retry, recovery, handlers
```
- Returns rich context (full functions/classes)
- Finds conceptually related code (no exact match needed)
- Best for: exploration, understanding, unfamiliar code

### Grep (Exact Search) - ~260ms
```
Grep: "BrowserBaseNode"     # Find exact class references
Grep: "def execute"         # Find method definitions
```
- Faster for known symbols
- Precise line-level matches
- Best for: refactoring, finding usages, known targets

### Decision Flow
1. **Don't know what to look for?** → `qdrant-find`
2. **Know exact name/symbol?** → `Grep`
3. **Exploring new area?** → `qdrant-find` first, then `Grep` for specifics

## Core Rules (Non-Negotiable)

1. **INDEX-FIRST**: Read `_index.md` before grep/glob. See `.claude/rules/01-core.md`
2. **PARALLEL**: Launch independent agents/reads in ONE message block
3. **SEARCH BEFORE CREATE**: Check existing code before writing new
4. **NO SILENT FAILURES**: Wrap external calls in try/except, use loguru
5. **THEME.* ONLY**: No hardcoded colors - use `THEME.bg_darkest`, `THEME.text_primary`, etc.
6. **UnifiedHttpClient**: No raw httpx/aiohttp
7. **@Slot ALWAYS**: All signal handlers need `@Slot(types)` decorator - see `.claude/rules/ui/signal-slot-rules.md`
8. **NO LAMBDAS**: Use named methods or `functools.partial` for signal connections
9. **TYPED EVENTS**: Use typed domain events - see DDD 2025 section
10. **EXEC PORTS**: Use `add_exec_input()`/`add_exec_output()` - NEVER `add_input_port(name, PortType.EXEC_*)`

## DDD 2025 Architecture

### Layers
| Layer | Path | Dependencies |
|-------|------|--------------|
| Domain | `domain/` | None |
| Application | `application/` | Domain |
| Infrastructure | `infrastructure/` | Domain, App |
| Presentation | `presentation/` | All |

### Key Patterns
| Pattern | Location | Usage |
|---------|----------|-------|
| **Typed Events** | `domain/events/` | `NodeCompleted`, `WorkflowStarted` (frozen dataclasses) |
| **EventBus** | `domain/events.py` | `get_event_bus()` singleton |
| **Aggregates** | `domain/aggregates/` | `Workflow` aggregate root |
| **Unit of Work** | `infrastructure/persistence/unit_of_work.py` | Transaction + event publishing |
| **CQRS Queries** | `application/queries/` | Read-optimized DTOs |
| **Qt Event Bridge** | `presentation/canvas/coordinators/event_bridge.py` | Domain→Qt signals |

### Typed Events Quick Reference
```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

bus = get_event_bus()
bus.subscribe(NodeCompleted, handler)
bus.publish(NodeCompleted(node_id="x", node_type="Y", execution_time_ms=100))
```

### Event Classes
| Event | Attributes |
|-------|------------|
| `NodeStarted` | node_id, node_type, workflow_id |
| `NodeCompleted` | node_id, node_type, workflow_id, execution_time_ms |
| `NodeFailed` | node_id, node_type, error_code, error_message, is_retryable |
| `WorkflowStarted` | workflow_id, workflow_name, total_nodes |
| `WorkflowCompleted` | workflow_id, execution_time_ms, nodes_executed |
| `WorkflowFailed` | workflow_id, failed_node_id, error_message |

Full list: `domain/events/__init__.py`

### Node Decorators
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node(category="browser")
@properties(
    PropertyDef("selector", PropertyType.SELECTOR, essential=True),
)
class MyNode(BaseNode):
    pass
```

## Key Indexes (P0 - Always Check First)
- `nodes/_index.md` - Node registry
- `presentation/canvas/visual_nodes/_index.md` - Visual nodes
- `domain/_index.md` - Core entities, aggregates, events
- `.brain/context/current.md` - Session state

## Rules Reference
| Topic | File |
|-------|------|
| Core workflow & standards | `.claude/rules/01-core.md` |
| Architecture & DDD patterns | `.claude/rules/02-architecture.md` |
| Node development | `.claude/rules/03-nodes.md` |
| DDD Events reference | `.claude/rules/04-ddd-events.md` |

### Path-Specific (auto-loaded)
| Scope | File |
|-------|------|
| UI/Presentation | `.claude/rules/ui/theme-rules.md` |
| Signal/Slot patterns | `.claude/rules/ui/signal-slot-rules.md` |
| Node files | `.claude/rules/nodes/node-registration.md` |

## On-Demand Docs (Load When Needed)
- `.brain/docs/node-templates.md` - Full node templates
- `.brain/docs/node-checklist.md` - Node implementation steps
- `.brain/projectRules.md` - Full coding standards
- `.brain/systemPatterns.md` - Architecture patterns
