# System Patterns - CasareRPA Quick Reference

## 1. Clean DDD Architecture

### Layer Flow
```
Presentation → Application → Domain ← Infrastructure
     (UI)        (Use Cases)    (Logic)    (External APIs)
```

### Layer Rules
| Layer | Purpose | Dependencies | Mocking Strategy |
|-------|---------|--------------|------------------|
| **Domain** | Pure business logic, entities, value objects | NONE | NO mocks (test with real VOs/Entities) |
| **Application** | Use case orchestration, coordination | Domain (required) | Mock infrastructure only |
| **Infrastructure** | API adapters, persistence, resources | None (interfaces) | Mock ALL external APIs (Playwright, UIAutomation, win32) |
| **Presentation** | UI, Canvas, Controllers, EventBus | Application (required) | Mock heavy Qt components (qasync + complexity) |

### Dependency Direction
- Presentation depends on Application (one-way)
- Application depends on Domain (one-way)
- Infrastructure depends on Domain interfaces (one-way)
- Infrastructure does NOT depend on Presentation
- Domain depends on NOTHING

### File Structure
```
src/casare_rpa/
├── domain/           # Pure entities, value objects, services
├── application/      # Use cases, orchestrators
├── infrastructure/   # Adapters, resource managers, persistence
├── presentation/     # Qt widgets, Canvas, Controllers
├── nodes/            # Executable node implementations
└── core/             # Shared types, enums, exceptions
```

## 2. Node Implementation Pattern

### BaseNode Structure
```python
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.core.types import ExecutionContext, ExecutionResult
from casare_rpa.domain.value_objects import Port, DataType, PropertyDef, PropertyType
from casare_rpa.nodes.decorators import executable_node, node_schema

@executable_node
@node_schema(PropertyDef("param1", PropertyType.STRING, default=""))
class MyCustomNode(BaseNode):
    NODE_NAME = "My Custom Node"
    CATEGORY = "custom"

    def _define_ports(self) -> None:
        # Input ports
        self.add_input_port("input", DataType.STRING, "Input text")
        # Output ports
        self.add_output_port("output", DataType.STRING, "Output text")
        # Execution ports (control flow)
        self.add_input_port("exec_in", DataType.EXECUTION, "Execute")
        self.add_output_port("exec_out", DataType.EXECUTION, "Continue")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            # Get parameter from node properties
            param_value = self.get_parameter("param1")

            # Get input port value
            input_value = self.get_input_value("input")

            # Perform logic
            result = perform_operation(input_value, param_value)

            # Set output port value
            self.set_output_value("output", result)

            # Update execution context (optional)
            context.variables["my_var"] = result

            return {"success": True, "data": {"output": result}}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "MY_ERROR_CODE"
            }
```

### Port Types
- **DataType.STRING** - Text values
- **DataType.INTEGER** - Whole numbers
- **DataType.BOOLEAN** - True/False
- **DataType.OBJECT** - Complex objects
- **DataType.ARRAY** - Lists of items
- **DataType.EXECUTION** - Control flow (start/end)
- **DataType.ANY** - Accepts anything (polymorphic)

### Decorators
```python
@executable_node          # Registers node in registry
@node_schema(...)         # Defines configurable properties
@async_node               # For async-only nodes (if needed)
```

## 2.5 BrowserBaseNode Pattern (Browser Nodes)

All Playwright-based browser nodes extend `BrowserBaseNode` for consistent:
- Page access from context
- Selector normalization (XPath, CSS, ARIA)
- Retry logic
- Screenshot on failure

### Location
```
src/casare_rpa/nodes/browser/
├── __init__.py           # Package exports
├── browser_base.py       # BrowserBaseNode base class
└── property_constants.py # Reusable PropertyDef constants
```

### Using BrowserBaseNode
```python
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_SELECTOR_STRICT,
)

@node_schema(
    PropertyDef("selector", PropertyType.SELECTOR, ...),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
@executable_node
class MyBrowserNode(BrowserBaseNode):
    def __init__(self, node_id: str, name: str = "My Node", **kwargs):
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "MyBrowserNode"

    def _define_ports(self):
        self.add_page_passthrough_ports()  # page in/out
        self.add_selector_input_port()      # selector input

    async def execute(self, context):
        try:
            page = self.get_page(context)           # From base
            selector = self.get_normalized_selector(context)  # From base

            async def perform_action():
                await page.click(selector)
                return True

            result = await retry_operation(...)
            if result.success:
                return self.success_result({"selector": selector})

            await self.screenshot_on_failure(page, "action_fail")  # From base
            raise result.last_error

        except Exception as e:
            return self.error_result(e)  # From base
```

### Common PropertyDef Constants
| Constant | Type | Default | Purpose |
|----------|------|---------|---------|
| `BROWSER_TIMEOUT` | INTEGER | 30000ms | Max wait time |
| `BROWSER_RETRY_COUNT` | INTEGER | 0 | Retry attempts |
| `BROWSER_RETRY_INTERVAL` | INTEGER | 1000ms | Delay between retries |
| `BROWSER_SCREENSHOT_ON_FAIL` | BOOLEAN | False | Take screenshot on error |
| `BROWSER_SCREENSHOT_PATH` | FILE_PATH | "" | Screenshot save path |
| `BROWSER_SELECTOR_STRICT` | BOOLEAN | False | Require single match |
| `BROWSER_WAIT_UNTIL` | CHOICE | "load" | Navigation wait state |
| `BROWSER_ELEMENT_STATE` | CHOICE | "visible" | Element state to wait for |

### BrowserBaseNode Helper Methods
- `get_page(context)` - Get page from port or context
- `get_normalized_selector(context)` - Resolve vars + normalize
- `execute_with_retry(operation, ...)` - Retry wrapper
- `screenshot_on_failure(page, prefix)` - Conditional screenshot
- `highlight_if_enabled(page, selector)` - Debug highlighting
- `add_page_passthrough_ports()` - Add page in/out ports
- `add_selector_input_port()` - Add selector input port
- `success_result(data)` - Build success ExecutionResult
- `error_result(error)` - Build error ExecutionResult

## 3. Testing Patterns by Layer

### Domain Tests (NO mocks)
```python
# Location: tests/domain/
# Mocks: NONE - use real domain objects
# Type: Unit tests

class TestWorkflow:
    def test_add_node_success(self):
        # Arrange: Create real domain objects
        workflow = Workflow(name="test", description="")
        node = Node(id=NodeId("node1"), type="start")

        # Act
        workflow.add_node(node)

        # Assert on behavior
        assert len(workflow.nodes) == 1
        assert workflow.nodes[0].id == NodeId("node1")

    def test_add_duplicate_node_raises_error(self):
        workflow = Workflow(name="test", description="")
        node = Node(id=NodeId("node1"), type="start")
        workflow.add_node(node)

        with pytest.raises(DuplicateNodeError):
            workflow.add_node(node)
```

### Application Tests (Mock Infrastructure)
```python
# Location: tests/application/
# Mocks: Infrastructure only (repos, adapters, external APIs)
# Type: Integration tests

@pytest.mark.asyncio
async def test_execute_workflow_saves_result(mocker):
    # Arrange: Mock infrastructure, use REAL domain
    mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
    mock_repo.get_by_id.return_value = Workflow(name="test")

    orchestrator = ExecutionOrchestrator(repository=mock_repo)

    # Act
    result = await orchestrator.execute(workflow_id=WorkflowId("wf1"))

    # Assert on behavior
    assert result.status == ExecutionStatus.COMPLETED
    mock_repo.save_execution.assert_awaited_once()
```

### Infrastructure Tests (Mock External APIs)
```python
# Location: tests/infrastructure/ or tests/nodes/
# Mocks: Playwright, UIAutomation, win32, HTTP, DB
# Type: Unit tests with mocks

@pytest.mark.asyncio
async def test_click_element_success(execution_context, mock_page):
    # Arrange
    node = ClickElementNode(selector="#btn", timeout=5000)
    mock_element = AsyncMock()
    mock_page.query_selector.return_value = mock_element
    execution_context.resources["page"] = mock_page

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is True
    mock_element.click.assert_awaited_once()
```

### Node Tests (3-Scenario Pattern)
```python
# Location: tests/nodes/{category}/
# Mocks: Category-specific fixtures (mock_page, MockUIControl, etc.)
# Pattern: SUCCESS, ERROR, EDGE_CASE

@pytest.mark.asyncio
async def test_node_success(execution_context, mock_page):
    # Arrange: SUCCESS scenario
    node = MyNode(param="valid")
    execution_context.resources["page"] = mock_page

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is True
    assert execution_context.variables.get("output") is not None

@pytest.mark.asyncio
async def test_node_error_handling(execution_context, mock_page):
    # Arrange: ERROR scenario
    node = MyNode(param="invalid")
    mock_page.query_selector.side_effect = Exception("Element not found")
    execution_context.resources["page"] = mock_page

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_node_edge_case(execution_context, mock_page):
    # Arrange: EDGE_CASE scenario
    node = MyNode(param="")
    execution_context.resources["page"] = mock_page

    # Act
    result = await node.execute(execution_context)

    # Assert - edge case handling
    assert result["success"] is True  # Handles gracefully
```

### Chain Tests (Real Nodes + Mock I/O)
```python
# Location: tests/nodes/chain/
# Mocks: Only external I/O (Playwright, win32, HTTP)
# Nodes: REAL implementation

@pytest.mark.asyncio
async def test_simple_chain(chain_executor):
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(SetVariableNode(name="x", value=42), id="set") \
        .add(EndNode(), id="end") \
        .connect_sequential() \
        .build()

    result = await chain_executor.execute(chain)

    assert result.status == ExecutionStatus.COMPLETED
    assert result.context.variables["x"] == 42

@pytest.mark.asyncio
async def test_branching_chain(chain_executor):
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(IfNode(condition="x > 10"), id="if") \
        .add(SetVariableNode(name="result", value="big"), id="true_branch") \
        .add(SetVariableNode(name="result", value="small"), id="false_branch") \
        .add(EndNode(), id="end") \
        .connect("start", "if") \
        .connect("if.true", "true_branch") \
        .connect("if.false", "false_branch") \
        .connect(["true_branch", "false_branch"], "end") \
        .build()

    result = await chain_executor.execute(chain, variables={"x": 15})
    assert result.context.variables["result"] == "big"
```

## 4. Fixture Locations Table

| Category | Location | Key Fixtures | Usage |
|----------|----------|--------------|-------|
| **Global** | `tests/conftest.py` | `execution_context`, `mock_execution_context` | All tests, all layers |
| **Browser** | `tests/nodes/browser/conftest.py` | `mock_page`, `mock_browser`, `mock_browser_context`, `mock_element` | Browser nodes, Playwright tests |
| **Desktop** | `tests/nodes/desktop/conftest.py` | `MockUIControl`, `MockDesktopElement`, `mock_win32`, `mock_automation` | Desktop nodes, UIAutomation tests |
| **HTTP** | `tests/nodes/http/conftest.py` | `mock_session`, `create_mock_response()` | HTTP nodes, API tests |
| **Chain** | `tests/nodes/chain/conftest.py` | `chain_executor`, `workflow_builder`, `execution_context` | Workflow chains, integration tests |
| **Canvas** | `tests/presentation/canvas/conftest.py` | `mock_graph`, `visual_node_factory`, `qtbot` | Canvas UI, visual connection tests |
| **Domain** | None (no fixtures needed) | N/A | Use real domain objects |

### Fixture Decision Tree
```
Used in 3+ test files?
├─ YES: Specific to category?
│   ├─ YES: tests/{category}/conftest.py
│   └─ NO: tests/conftest.py
└─ NO: Used in 2+ tests in same file?
    ├─ YES: Fixture at top of test file
    └─ NO: Inline in test (no fixture needed)
```

## 5. Async Testing Patterns

### Async Test Structure
```python
@pytest.mark.asyncio
async def test_async_operation():
    # Use AsyncMock for async functions
    mock_repo = AsyncMock(spec=WorkflowRepository)
    mock_repo.get_by_id.return_value = Workflow(name="test")

    # Act
    result = await mock_repo.get_by_id("wf1")

    # Assert with async assertions
    mock_repo.get_by_id.assert_awaited_once()
```

### Mock vs AsyncMock Decision
```python
# WRONG - Mock for async function
mock_repo = Mock()
await mock_repo.save()  # Won't work properly

# RIGHT - AsyncMock for async function
mock_repo = AsyncMock()
await mock_repo.save()  # Works correctly
mock_repo.save.assert_awaited_once()
```

### Async Context Managers
```python
@pytest.mark.asyncio
async def test_browser_context_manager():
    mock_browser = AsyncMock()
    manager = BrowserResourceManager()
    manager._browser = mock_browser

    async with manager.get_context() as ctx:
        assert ctx is not None

    mock_browser.new_context.assert_awaited_once()
```

## 6. Error Handling Patterns

### Expected Exception Testing
```python
def test_invalid_input_raises_error():
    with pytest.raises(DuplicateNodeError):
        workflow.add_node(duplicate_node)

def test_invalid_connection_raises_error():
    with pytest.raises(IncompatiblePortTypesError):
        port_string.connect_to(port_integer)
```

### Execution Result Error Pattern
```python
@pytest.mark.asyncio
async def test_node_returns_error_result(execution_context):
    node = MyNode(param="invalid")

    result = await node.execute(execution_context)

    # Nodes should NOT raise; return error in result
    assert result["success"] is False
    assert "error" in result
    assert "error_code" in result
```

### Error Dictionary Format
```python
# Standard node error response
{
    "success": False,
    "error": "Human-readable error message",
    "error_code": "ERR_SELECTOR_NOT_FOUND",
    "context": {
        "attempted_selector": "#btn",
        "page_title": "Login Page"
    }
}
```

## 7. Common Import Patterns

### Domain Imports
```python
from casare_rpa.domain.entities.workflow import Workflow
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.value_objects import Port, DataType, PortType, NodeId
from casare_rpa.domain.services.workflow_validator import WorkflowValidator
```

### Application Imports
```python
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.application.orchestrators.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.core.types import ExecutionContext, ExecutionResult, ExecutionStatus
```

### Infrastructure Imports
```python
from casare_rpa.infrastructure.resources.browser_resource_manager import BrowserResourceManager
from casare_rpa.infrastructure.persistence.workflow_repository import WorkflowRepository
from casare_rpa.infrastructure.adapters.playwright_adapter import PlaywrightAdapter
```

### Node Implementation Imports
```python
from casare_rpa.nodes.decorators import executable_node, node_schema
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.core.types import ExecutionContext, ExecutionResult
from casare_rpa.domain.value_objects import PropertyDef, PropertyType
```

### Test Imports
```python
# Standard pytest
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Project fixtures
from tests.conftest import execution_context
from tests.nodes.browser.conftest import mock_page, mock_browser
```

## 8. Agent Patterns for Parallel Execution

### Consolidated Agents (19 → 11)
| Agent | Purpose | Permission |
|-------|---------|------------|
| `explore` | Codebase exploration, file search | read-only |
| `architect` | Implementation, nodes, system design | read-write |
| `quality` | Tests, performance, stress tests | read-write |
| `reviewer` | Code review gate (MANDATORY) | read-only |
| `security` | Security audits | read-only |
| `docs` | Documentation | read-write |
| `refactor` | Code cleanup, DRY | read-write |
| `ui` | Canvas UI design | read-write |
| `integrations` | External APIs | read-write |
| `researcher` | Research, migrations | read-only |
| `pm` | Product scope | read-only |

### Parallel Exploration (PLAN Phase)
```python
# Launch 1-3 explore agents to analyze codebase simultaneously
Task(subagent_type="explore", prompt="Find existing Node implementations in nodes/")
Task(subagent_type="explore", prompt="Find test patterns in tests/nodes/")
Task(subagent_type="explore", prompt="Find domain entity patterns in domain/")
```

### Implementation Chain (MANDATORY)
```python
# Step 1: Implement
Task(subagent_type="architect", prompt="Implement MyCustomNode logic")

# Step 2: Test (after implementation completes)
Task(subagent_type="quality", prompt="Create 3-scenario test suite")

# Step 3: Review (MANDATORY after tests)
Task(subagent_type="reviewer", prompt="Review MyCustomNode implementation")

# If reviewer returns ISSUES:
#   → Task(subagent_type="architect", prompt="Fix issues: {issue_list}")
#   → Task(subagent_type="quality", prompt="Re-run affected tests")
#   → Task(subagent_type="reviewer", prompt="Re-review changes")
#   → Loop until APPROVED
```

### Parallel Support Tasks
```python
# Can run in parallel with implementation chain:
Task(subagent_type="docs", prompt="Document node API reference")
Task(subagent_type="security", prompt="Security review of new node")
```

### Full Pipeline Example
```
PLAN → IMPLEMENT → TEST → REVIEW → QA → APPROVAL → DOCS
         ↑                    │
         └── (if ISSUES) ─────┘

# Phase 1: PLAN (sequential)
- Create .brain/plans/{feature}.md
- Launch 1-3 explore agents (parallel) → wait for findings
- STOP for user approval

# Phase 2: IMPLEMENT
- architect: Node implementation

# Phase 3: TEST (after implement)
- quality: Test suite (test, perf, stress modes)

# Phase 4: REVIEW (MANDATORY after test)
- reviewer: Code review gate
- If ISSUES → return to IMPLEMENT with feedback
- If APPROVED → proceed to QA

# Phase 5: QA (sequential)
- pytest tests/ -v
- ruff check src/

# Phase 6: APPROVAL (human gate)
- Show diff + test results
- STOP for "Ship it"

# Phase 7: DOCS (sequential)
- Update .brain/activeContext.md
- Update .brain/systemPatterns.md (if new patterns)
```

### Refactoring Flow (Same Review Loop)
```python
Task(subagent_type="refactor", prompt="Extract {component}")
Task(subagent_type="quality", prompt="Verify tests still pass")
Task(subagent_type="reviewer", prompt="Review refactoring")
# Loop if ISSUES
```

## 9. Mocking Strategy Quick Reference

### Always Mock (External APIs)
- Playwright: Page, Browser, BrowserContext
- UIAutomation: Control, Pattern, Element
- win32 APIs: win32gui, win32con, ctypes
- HTTP: aiohttp.ClientSession, httpx
- Database: asyncpg, aiomysql connections
- File I/O: aiofiles, pathlib (large files)
- Images: PIL operations
- Processes: subprocess

### Prefer Real (Domain Logic)
- Domain entities: Workflow, Node, ExecutionState
- Value objects: NodeId, PortId, DataType
- Domain services: Pure logic, no I/O
- Simple structures: dict, list, dataclasses

### Context Dependent
- ExecutionContext: Use fixture from conftest.py
- Event bus: Mock for unit tests, real for integration
- Resource managers: Mock external resources, real manager logic

### Realistic Mock Example
```python
# GOOD: Behavioral mock
class MockUIControl:
    def __init__(self, name="Button", control_type="Button"):
        self.Name = name
        self.ControlType = control_type
        self._enabled = True

    def GetCurrentPropertyValue(self, property_id):
        if property_id == 30003:  # IsEnabled
            return self._enabled
        raise PropertyNotSupported()

# BAD: Stub that doesn't behave like real API
mock = Mock()
mock.Name = "Button"  # Doesn't validate like real API
```

## 10. Code Templates

### New Node Template
```python
from casare_rpa.nodes.decorators import executable_node, node_schema
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.core.types import ExecutionContext, ExecutionResult
from casare_rpa.domain.value_objects import PropertyDef, PropertyType

@executable_node
@node_schema(PropertyDef("param1", PropertyType.STRING, default=""))
class MyCustomNode(BaseNode):
    NODE_NAME = "My Custom Node"
    CATEGORY = "custom"

    def _define_ports(self) -> None:
        self.add_input_port("input", DataType.STRING, "Input")
        self.add_output_port("output", DataType.STRING, "Output")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            param = self.get_parameter("param1")
            input_val = self.get_input_value("input")
            result = process(input_val, param)
            self.set_output_value("output", result)
            return {"success": True, "data": {"output": result}}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### Node Test Template
```python
@pytest.mark.asyncio
async def test_my_node_success(execution_context):
    node = MyCustomNode(node_id="test", config={"param1": "value"})
    execution_context.variables["input"] = "test_input"

    result = await node.execute(execution_context)

    assert result["success"] is True
    assert execution_context.variables.get("output") == expected

@pytest.mark.asyncio
async def test_my_node_error(execution_context):
    node = MyCustomNode(node_id="test", config={"param1": "invalid"})

    result = await node.execute(execution_context)

    assert result["success"] is False
    assert "error" in result
```

### Chain Test Template
```python
@pytest.mark.asyncio
async def test_my_chain(chain_executor):
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(MyNode1(), id="n1") \
        .add(MyNode2(), id="n2") \
        .connect_sequential() \
        .build()

    result = await chain_executor.execute(chain)

    assert result.status == ExecutionStatus.COMPLETED
```

## 11. Event Bus Pattern

### Two Event Bus Systems

| System | Location | Purpose | Features |
|--------|----------|---------|----------|
| **Domain** | `domain/events.py` | Execution events (Robot/Orchestrator) | Simple, sync, `emit()`, no Qt deps |
| **Presentation** | `presentation/canvas/events/` | UI events (Canvas) | Thread-safe, caching, metrics, Qt bridge |

### Event Naming Convention
Format: `{SCOPE}_{ACTION}_{STATE?}`
- **Scopes**: NODE, WORKFLOW, EXECUTION, CONNECTION, PORT, VARIABLE, PROJECT, TRIGGER
- **Actions**: START, COMPLETE, FAIL, SKIP, CREATE, ADD, UPDATE, REMOVE
- **States**: _ED (completed), _ING (in-progress)

### Usage Patterns

**Domain EventBus (Simple):**
```python
from casare_rpa.domain.events import get_event_bus, Event
from casare_rpa.domain.value_objects.types import EventType

event_bus = get_event_bus()

# Subscribe
event_bus.subscribe(EventType.NODE_COMPLETED, handler)

# Emit (convenience method)
event_bus.emit(EventType.NODE_STARTED, {"node_id": "n1"}, node_id="n1")
```

**Presentation EventBus (Rich):**
```python
from casare_rpa.presentation.canvas.events import (
    EventBus, Event, EventType, EventPriority, EventFilter,
    start_domain_bridge,
)
from casare_rpa.presentation.canvas.events.event_contracts import NodeAddedData

event_bus = EventBus()

# Type-safe event data
data: NodeAddedData = {"node_id": "n1", "node_type": "ClickElementNode"}
event = Event(type=EventType.NODE_ADDED, source="Controller", data=data)
event_bus.publish(event)

# Filtered subscription
filter = EventFilter(categories=[EventCategory.EXECUTION])
event_bus.subscribe_filtered(filter, handler)

# Start domain bridge (in MainWindow init)
bridge = start_domain_bridge()
```

### Domain-to-Presentation Bridge
```python
# Maps domain events to presentation events
from casare_rpa.presentation.canvas.events import DomainEventBridge

bridge = DomainEventBridge()
bridge.start()  # Subscribe to domain events
# ...
bridge.stop()   # Cleanup
```

### Event Contracts (TypedDict)
```python
from casare_rpa.presentation.canvas.events.event_contracts import (
    NodeExecutionStartedData,
    WorkflowSavedData,
    ExecutionCompletedData,
)

# Type-safe event creation
data: NodeExecutionStartedData = {
    "node_id": "node_123",
    "node_type": "ClickElementNode",
    "node_name": "Click Login"
}
```

---
**Quick Commands:**
- Run tests: `pytest tests/ -v`
- Run single test: `pytest tests/path/test_file.py::test_name -vv -s`
- Coverage: `pytest tests/ -v --cov=casare_rpa`
- Lint: `ruff check src/`
- Type check: `mypy src/`

**Key Files:**
- Patterns: `.brain/systemPatterns.md` (this file)
- Session context: `.brain/activeContext.md`
- Coding standards: `.brain/projectRules.md`
- Feature plans: `.brain/plans/{feature}.md`

## 12. UnifiedHttpClient Pattern (2025-12-09)

### Composable Resilience
```python
from casare_rpa.infrastructure.http import UnifiedHttpClient, HttpClientConfig

# Configure resilience patterns
config = HttpClientConfig(
    max_retries=3,
    retry_base_delay=1.0,
    circuit_breaker_threshold=5,
    circuit_breaker_reset_timeout=60,
    rate_limit_requests=100,
    rate_limit_period=60,
    max_connections=10,
    timeout=30,
)

# Use client with automatic resilience
async with UnifiedHttpClient(config) as client:
    response = await client.get("https://api.example.com/data")
```

### Components
| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **Rate Limiter** | Token bucket algorithm | `rate_limit_requests`, `rate_limit_period` |
| **Circuit Breaker** | Fail-fast on repeated errors | `circuit_breaker_threshold`, `circuit_breaker_reset_timeout` |
| **Retry Logic** | Exponential backoff | `max_retries`, `retry_base_delay` |
| **Session Pool** | Connection reuse | `max_connections` |
| **SSRF Protection** | URL validation | Built-in (blocks private IPs) |

### Request Statistics
```python
stats = client.get_stats()
# RequestStats(total=100, success=95, failed=5, avg_latency_ms=150.5)
```

---

## 13. Domain Interface Pattern (2025-12-09)

### Problem
Application layer was importing directly from Infrastructure (ExecutionContext), violating Clean DDD.

### Solution
Domain layer defines Protocol interfaces; Infrastructure implements them.

```python
# domain/interfaces/execution_context.py
from typing import Protocol, Any, Optional

class IExecutionContext(Protocol):
    """Protocol for execution context - Application depends on this."""

    @property
    def variables(self) -> dict[str, Any]: ...

    @property
    def resources(self) -> dict[str, Any]: ...

    async def get_page(self) -> Any: ...

    async def execute_parallel(self, tasks: list) -> list: ...

# infrastructure/execution/execution_context.py
class ExecutionContext:
    """Concrete implementation - Infrastructure provides this."""
    # Implements IExecutionContext protocol
```

### Dependency Flow
```
Application Layer
       |
       v (depends on abstraction)
Domain Interfaces (IExecutionContext, IFolderStorage, etc.)
       ^
       | (implements)
Infrastructure Layer (ExecutionContext, FolderStorage, etc.)
```

### Available Interfaces
- `IExecutionContext` - Workflow execution state
- `IFolderStorage` - Project folder persistence
- `IEnvironmentStorage` - Environment config persistence
- `ITemplateStorage` - Project template loading

---

## 14. SignalCoordinator Pattern (2025-12-09)

### Purpose
Extracted from MainWindow to handle action callbacks and controller delegation.

### Location
`src/casare_rpa/presentation/canvas/coordinators/signal_coordinator.py`

### Responsibilities
| Method Category | Examples |
|-----------------|----------|
| **Workflow Actions** | `new_workflow()`, `open_workflow()`, `save_workflow()` |
| **Execution Actions** | `start_execution()`, `stop_execution()`, `pause_execution()` |
| **Debug Actions** | `toggle_debug_mode()`, `step_over()`, `step_into()` |
| **Node Actions** | `copy_nodes()`, `paste_nodes()`, `delete_nodes()` |
| **View Actions** | `zoom_in()`, `zoom_out()`, `fit_view()` |
| **Mode Toggles** | `toggle_edit_mode()`, `toggle_run_mode()` |

### Usage
```python
class MainWindow(QMainWindow):
    def __init__(self):
        self._signal_coordinator = SignalCoordinator(self)

        # Connect toolbar actions
        self.run_action.triggered.connect(
            self._signal_coordinator.start_execution
        )
```

---

## 15. PanelManager Pattern (2025-12-09)

### Purpose
Extracted from MainWindow to manage panel visibility and tab switching.

### Location
`src/casare_rpa/presentation/canvas/managers/panel_manager.py`

### Responsibilities
| Method | Purpose |
|--------|---------|
| `show_bottom_panel()` | Show bottom panel area |
| `hide_bottom_panel()` | Hide bottom panel area |
| `toggle_bottom_panel()` | Toggle visibility |
| `switch_to_tab(name)` | Switch to named tab |
| `get_panel(name)` | Get panel widget by name |
| `toggle_side_panel()` | Toggle node palette |
| `show_debug_panel()` | Show debug tab |

### Panel Registry
```python
# Register panels at startup
self._panel_manager.register_panel("output", output_panel)
self._panel_manager.register_panel("variables", variables_panel)
self._panel_manager.register_panel("debug", debug_panel)
```

---

## 16. Theme System Pattern (2025-12-09)

### Problem
Hardcoded colors scattered throughout codebase, inconsistent UI.

### Solution
Centralized THEME constants with semantic naming.

### Location
`src/casare_rpa/presentation/canvas/theme.py`

### Usage
```python
from casare_rpa.presentation.canvas.theme import THEME

# Widget styling
widget.setStyleSheet(f"""
    background-color: {THEME['background']};
    color: {THEME['text']};
    border: 1px solid {THEME['border']};
""")

# Port colors (semantic)
wire_color = THEME['port_colors']['string']  # Blue
wire_color = THEME['port_colors']['integer']  # Green
wire_color = THEME['port_colors']['execution']  # White
```

### THEME Keys
| Category | Keys |
|----------|------|
| **Base** | `background`, `foreground`, `text`, `border` |
| **Accent** | `accent`, `accent_hover`, `accent_disabled` |
| **Status** | `success`, `warning`, `error`, `info` |
| **Ports** | `port_colors` dict with DataType keys |
| **Node** | `node_bg`, `node_border`, `node_selected` |

---

## 17. SSRF Protection Pattern (2025-12-09)

### Problem
HTTP nodes could be used to access internal network resources.

### Solution
URL validation in UnifiedHttpClient blocks private IP ranges.

### Protected Ranges
- `127.0.0.0/8` - Loopback
- `10.0.0.0/8` - Private Class A
- `172.16.0.0/12` - Private Class B
- `192.168.0.0/16` - Private Class C
- `169.254.0.0/16` - Link-local
- `::1` - IPv6 loopback
- `fc00::/7` - IPv6 private

### Validation
```python
# Automatic in UnifiedHttpClient
await client.get("http://192.168.1.1/admin")  # Raises SSRFBlockedError

# Manual check
from casare_rpa.infrastructure.http.security import is_ssrf_safe
if not is_ssrf_safe(url):
    raise SecurityError("SSRF blocked")
```

---

*Last updated: 2025-12-09*
