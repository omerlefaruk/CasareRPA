# Mocking Rules

**Part of:** `.brain/projectRules.md` | **See also:** `testing.md`

## Always Mock (External APIs)

| Category | Items | Why |
|----------|-------|-----|
| **Browser APIs** | Playwright Page, Browser, BrowserContext, Frame | Heavy I/O, slow, non-deterministic |
| **Desktop APIs** | UIAutomation Control, Pattern, Element | OS-specific, requires running GUI |
| **Windows APIs** | win32gui, win32con, ctypes, pywinauto | System-level, risky, OS-specific |
| **HTTP Clients** | aiohttp.ClientSession, httpx.AsyncClient | Network I/O, slow, external |
| **Databases** | asyncpg.Connection, aiomysql.Cursor | Network I/O, slow, state-dependent |
| **File I/O** | aiofiles, pathlib (large files), os module | Slow, system-dependent |
| **Image Processing** | PIL/Image.open, cv2 | CPU-intensive, non-deterministic |
| **External Processes** | subprocess, os.system | Unpredictable, system-dependent |

## Never Mock (Domain & Pure Logic)

| Category | Items | Why |
|----------|-------|-----|
| **Domain Entities** | Workflow, Node, ExecutionState, RunContext | Pure logic, fast, deterministic |
| **Value Objects** | NodeId, PortId, DataType, ExecutionStatus | Immutable, fast, logic-focused |
| **Domain Services** | Pure functions, orchestration logic | No side effects, no I/O |
| **Standard Data Structures** | dict, list, dataclass, tuple | Built-in, no behavior to mock |

## Context Dependent (Infrastructure)

| Item | Mock If | Real If | Rule |
|------|---------|---------|------|
| **ExecutionContext** | Has external deps | Pure logic | Use fixture from conftest.py |
| **Event Bus** | Unit testing logic | Integration testing | Mock for unit, real for E2E |
| **Resource Managers** | Testing client code | Testing manager itself | Mock external APIs, real manager |
| **Connection Pools** | Testing retry logic | Testing initialization | Mock connections, real pool |

## Realistic Mocks (Not Just Stubs)

**Principle:** Mocks should BEHAVE like real objects, not just return values.

**Good Example (Behavioral Mock):**
```python
class MockUIControl:
    """Realistic UIAutomation control mock."""

    def __init__(self, name="Button", control_type="Button", enabled=True):
        self.Name = name
        self.ControlType = control_type
        self._enabled = enabled

    def GetCurrentPropertyValue(self, property_id: int):
        if property_id == 30003:  # IsEnabled property
            return self._enabled
        if property_id == 30005:  # Name property
            return self.Name
        raise UIA_PropertyNotSupported(f"Property {property_id} not supported")
```

**Bad Example (Stub):**
```python
# DON'T DO THIS
mock_control = Mock()
mock_control.Name = "Button"  # Just returns value, no behavior
```
