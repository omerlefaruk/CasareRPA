# CasareRPA Internals

Deep dives into CasareRPA's internal subsystems for advanced developers and contributors.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Execution Engine](execution-engine.md) | Workflow execution pipeline |
| [Browser Integration](browser-integration.md) | Playwright browser management |
| [Desktop Integration](desktop-integration.md) | Windows UI automation internals |
| [HTTP Client](http-client.md) | UnifiedHttpClient implementation |

---

## Subsystem Overview

### Execution Engine

The execution engine orchestrates workflow execution:

```
┌─────────────────────────────────────────────────────────┐
│                   Execution Engine                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Parser    │→ │  Validator  │→ │  Executor   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         ↓                                    ↓          │
│  ┌─────────────┐                    ┌─────────────┐    │
│  │  DAG Build  │                    │ Event Emit  │    │
│  └─────────────┘                    └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Key Components:**
- **WorkflowExecutor**: Main execution orchestrator
- **NodeExecutor**: Individual node execution
- **ExecutionContext**: Runtime state and variables
- **EventBus**: Execution event publishing

### Browser Integration

Playwright-based browser automation:

```python
# Browser pool management
from casare_rpa.infrastructure.browser import BrowserPool

async with BrowserPool() as pool:
    page = await pool.acquire()
    await page.goto("https://example.com")
    await pool.release(page)
```

**Features:**
- Connection pooling
- Self-healing selectors
- Screenshot on error
- Network interception

### Desktop Integration

Windows UI automation via multiple backends:

| Backend | Use Case |
|---------|----------|
| **pywinauto** | Win32/UIA controls |
| **pyautogui** | Mouse/keyboard simulation |
| **win32gui** | Window management |

### HTTP Client

UnifiedHttpClient provides resilient HTTP:

```python
from casare_rpa.infrastructure.http import UnifiedHttpClient

async with UnifiedHttpClient() as client:
    response = await client.get("https://api.example.com/data")
```

**Features:**
- Automatic retries
- Rate limiting
- Request/response logging
- OAuth integration

---

## Internal APIs

### ExecutionContext

```python
class ExecutionContext:
    workflow_id: str
    variables: dict[str, Any]

    def get_variable(self, name: str) -> Any
    def set_variable(self, name: str, value: Any)
    def resolve_expression(self, expr: str) -> Any
```

### EventBus

```python
from casare_rpa.domain.events import get_event_bus

bus = get_event_bus()
bus.subscribe(NodeCompleted, handler)
bus.publish(NodeCompleted(...))
```

---

## Performance Considerations

| Subsystem | Bottleneck | Mitigation |
|-----------|------------|------------|
| Browser | Page creation | Connection pooling |
| Desktop | Element lookup | Caching, smart selectors |
| HTTP | Network latency | Connection reuse, async |
| Execution | Large workflows | Parallel execution |

---

## Related Documentation

- [Architecture Overview](../architecture/overview.md)
- [Event Bus API](../api-reference/event-bus.md)
- [Creating Nodes](../extending/creating-nodes.md)
