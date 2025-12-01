# CasareRPA Project Rules: Authoritative Reference

**Last Updated:** 2025-11-30
**Version:** 1.0 (Baseline for v3 Clean DDD Architecture)

---

## 1. Code Standards

### 1.1 General Principles
- **BE EXTREMELY CONCISE**: Sacrifice grammar. No flowery prose.
- **NO TIME ESTIMATES**: Never provide effort/complexity ratings.
- **AUTO-IMPORTS**: Add missing imports without asking.
- **TERSE OUTPUT**: Skip preamble ("Here is the code"), just show the block.
- **READABLE CODE**: Comments only for "why", never "what" (code is self-documenting).

### 1.2 Naming Conventions
| Category | Style | Example |
|----------|-------|---------|
| Classes | PascalCase | `ExecutionOrchestrator`, `ClickElementNode` |
| Functions/Methods | snake_case | `execute_workflow()`, `get_by_id()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private members | _leading_underscore | `_internal_state`, `_cache` |
| Type vars | PascalCase | `T`, `NodeType` |

### 1.3 Type Hints (Python 3.12+)
**REQUIRED** for all public APIs:
```python
from typing import Optional, Dict, Any
from casare_rpa.core.types import NodeId, PortId

def execute_node(
    node_id: NodeId,
    context: ExecutionContext,
    timeout: int = 5000
) -> Dict[str, Any]:
    """Execute a single node in a workflow."""
    ...
```

**Rules:**
- Use `Optional[T]` instead of `T | None` (compatibility)
- Use `Dict[K, V]` not `dict[K, V]` (stdlib)
- Private/internal functions: type hints optional

### 1.4 Code Formatting
- **Line Length:** 100 characters max
- **Indentation:** 4 spaces (not tabs)
- **Imports:** Alphabetical within groups
  ```python
  # Standard library
  import json
  from pathlib import Path

  # Third-party
  import aiohttp
  from loguru import logger

  # Local
  from casare_rpa.domain.workflow import Workflow
  from casare_rpa.infrastructure.persistence import WorkflowRepository
  ```
- **Format Tool:** Ruff (auto-run in CI, informational)

---

## 2. Architecture Rules

### 2.1 Clean DDD Layers

```
Presentation (GUI) → Application (Use Cases) → Domain (Entities/VOs)
                           ↓
                   Infrastructure (Adapters)
```

**Dependency Flow:** ONLY this direction. NO reverse dependencies.

### 2.2 Layer Definitions & Responsibilities

#### **Domain Layer** (`src/casare_rpa/domain/`)
- **Responsibility:** Pure business logic, no external dependencies
- **Contains:**
  - Entities (Workflow, Node, ExecutionState)
  - Value Objects (NodeId, PortId, DataType, ExecutionStatus)
  - Domain Services (pure logic orchestration)
  - Exceptions (custom domain errors)
- **Rules:**
  - NO imports from `infrastructure`, `presentation`, `application`
  - NO I/O operations (sync or async)
  - NO external library calls (except dataclasses, typing)
  - State changes via methods, not property assignment
- **Invariants:** Enforce via constructors/methods

**Example:**
```python
# src/casare_rpa/domain/workflow.py
from dataclasses import dataclass
from casare_rpa.domain.node import Node, NodeId

@dataclass(frozen=True)
class NodeId:
    """Value Object: Node identifier."""
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("NodeId cannot be empty")

class Workflow:
    """Entity: Represents a workflow with nodes and edges."""

    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description
        self._nodes: Dict[NodeId, Node] = {}

    def add_node(self, node: Node) -> None:
        """Add node to workflow. Raises if duplicate."""
        if node.id in self._nodes:
            raise DuplicateNodeError(f"Node {node.id} already exists")
        self._nodes[node.id] = node

    @property
    def nodes(self) -> list[Node]:
        return list(self._nodes.values())
```

#### **Application Layer** (`src/casare_rpa/application/`)
- **Responsibility:** Use case orchestration, transaction management
- **Contains:**
  - Use Cases (classes implementing specific workflows)
  - DTOs (Data Transfer Objects for requests/responses)
  - Interfaces (abstract adapters for Infrastructure)
  - Exceptions (use case errors)
- **Rules:**
  - Import from `domain` (always)
  - Import from `infrastructure` ONLY via dependency injection
  - Coordinate domain services + infrastructure
  - Handle errors, logging, metrics
  - Async by default (await infrastructure calls)
- **Signature:** `async def execute(...) -> UseCaseResponse`

**Example:**
```python
# src/casare_rpa/application/execute_workflow.py
from casare_rpa.domain.workflow import Workflow, WorkflowId
from casare_rpa.infrastructure.persistence import WorkflowRepository
from casare_rpa.infrastructure.execution import ExecutionEngine

class ExecuteWorkflowUseCase:
    """Execute a workflow end-to-end."""

    def __init__(
        self,
        repository: WorkflowRepository,
        engine: ExecutionEngine
    ):
        self._repository = repository
        self._engine = engine

    async def execute(self, workflow_id: WorkflowId) -> ExecutionResult:
        """Execute workflow by ID."""
        workflow = await self._repository.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        result = await self._engine.execute(workflow)
        await self._repository.save_execution(result)
        return result
```

#### **Infrastructure Layer** (`src/casare_rpa/infrastructure/`)
- **Responsibility:** Implement domain interfaces, adapt external APIs
- **Contains:**
  - Adapters (Playwright, UIAutomation, Databases, HTTP)
  - Repositories (persistence implementations)
  - Resource Managers (browser contexts, DB connections)
  - Configuration
- **Rules:**
  - Import from `domain` + `application` (interfaces)
  - Import from external libraries (Playwright, asyncpg, etc.)
  - Implement application interfaces/protocols
  - Handle retries, connection pooling, resource cleanup
  - All I/O here (Playwright, DB, HTTP, win32)
- **Exception Handling:** Translate external errors to domain exceptions

**Example:**
```python
# src/casare_rpa/infrastructure/persistence/workflow_repository.py
from playwright.async_api import Browser
from casare_rpa.domain.workflow import Workflow, WorkflowId
from casare_rpa.application.interfaces import IWorkflowRepository

class PlaywrightWorkflowRepository(IWorkflowRepository):
    """Implement workflow repository using Playwright."""

    def __init__(self, browser: Browser):
        self._browser = browser

    async def get_by_id(self, workflow_id: WorkflowId) -> Optional[Workflow]:
        """Fetch workflow from database via Playwright."""
        try:
            page = await self._browser.new_page()
            # Navigate, extract, parse
            workflow = Workflow(name="...", description="...")
            return workflow
        except Exception as e:
            raise RepositoryError(f"Failed to fetch workflow: {e}") from e
```

#### **Presentation Layer** (`src/casare_rpa/presentation/`)
- **Responsibility:** UI/UX, user interaction, event handling
- **Contains:**
  - Main Window, Canvas (NodeGraphQt)
  - Controllers (coordinate UI + Application)
  - EventBus (pub/sub for loose coupling)
  - Widgets, Dialogs
- **Rules:**
  - Import from `application` (Use Cases)
  - DO NOT import from `infrastructure`
  - Async operations via qasync (Qt event loop + asyncio)
  - Emit events for side effects, don't call services directly
- **Event Pattern:** Emit EventBus events → Controllers listen → call Use Cases

**Example:**
```python
# src/casare_rpa/presentation/controllers/workflow_controller.py
from casare_rpa.application.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.presentation.event_bus import EventBus

class WorkflowController:
    """Controller: Bind UI events to Use Cases."""

    def __init__(
        self,
        execute_use_case: ExecuteWorkflowUseCase,
        event_bus: EventBus
    ):
        self._use_case = execute_use_case
        self._event_bus = event_bus

    async def save_workflow(self, workflow_data: Dict) -> None:
        """Save workflow via Use Case, emit event on success."""
        try:
            result = await self._use_case.execute(workflow_data)
            self._event_bus.emit("workflow.saved", result)
        except Exception as e:
            self._event_bus.emit("workflow.error", {"error": str(e)})
```

### 2.3 Module Structure
```
src/casare_rpa/
├── domain/                    # Pure business logic
│   ├── workflow.py
│   ├── node.py
│   ├── execution_state.py
│   └── exceptions.py
├── application/              # Use cases
│   ├── execute_workflow.py
│   ├── interfaces.py         # Abstract repositories
│   └── dto/
├── infrastructure/           # Adapters, persistence
│   ├── persistence/          # Repositories
│   ├── execution/           # Execution engines
│   ├── adapters/            # External APIs
│   └── resources/           # Resource managers
├── presentation/            # UI
│   ├── main_window.py
│   ├── controllers/
│   ├── event_bus.py
│   └── widgets/
├── nodes/                   # Node implementations
│   ├── browser/
│   ├── desktop/
│   └── base.py
├── core/                    # Shared utilities
│   ├── types.py            # Type definitions
│   ├── constants.py
│   └── config.py
└── __init__.py
```

### 2.4 Dependency Injection
- Use constructor injection (not global singletons)
- Container managed by `Application` (main entry point)
- Avoid circular dependencies by injecting interfaces

---

## 3. Testing Rules by Layer

### 3.1 Domain Layer Tests
**Location:** `tests/domain/`
**Principle:** NO mocks. Pure logic with real domain objects.

| Aspect | Rule |
|--------|------|
| **Mocks** | NEVER |
| **Fixtures** | Real domain objects |
| **Async** | No async tests (domain is sync) |
| **Coverage Target** | 90%+ |

**Template:**
```python
# tests/domain/test_workflow.py
class TestWorkflow:
    def test_add_node_success(self):
        """Adding a valid node increments count."""
        workflow = Workflow(name="test", description="")
        node = Node(id=NodeId("n1"), type="start")

        workflow.add_node(node)

        assert len(workflow.nodes) == 1
        assert workflow.nodes[0].id == NodeId("n1")

    def test_add_duplicate_node_raises_error(self):
        """Adding same node twice raises DuplicateNodeError."""
        workflow = Workflow(name="test", description="")
        node = Node(id=NodeId("n1"), type="start")
        workflow.add_node(node)

        with pytest.raises(DuplicateNodeError):
            workflow.add_node(node)
```

### 3.2 Application Layer Tests
**Location:** `tests/application/`
**Principle:** Mock infrastructure, real domain objects.

| Aspect | Rule |
|--------|------|
| **Mocks** | Infrastructure only (repos, adapters) |
| **Fixtures** | Real domain objects, AsyncMock for async deps |
| **Async** | @pytest.mark.asyncio |
| **Coverage Target** | 85%+ |

**Template:**
```python
# tests/application/test_execute_workflow.py
@pytest.mark.asyncio
async def test_execute_workflow_saves_result(mocker):
    # Arrange: Mock infrastructure
    mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
    mock_repo.get_by_id.return_value = Workflow(name="test")

    orchestrator = ExecutionOrchestrator(repository=mock_repo)

    # Act
    result = await orchestrator.execute(WorkflowId("wf1"))

    # Assert
    assert result.status == ExecutionStatus.COMPLETED
    mock_repo.save_execution.assert_awaited_once()
```

### 3.3 Infrastructure Layer Tests
**Location:** `tests/infrastructure/` or `tests/nodes/`
**Principle:** Mock ALL external APIs (Playwright, UIAutomation, DB, HTTP).

| Aspect | Rule |
|--------|------|
| **Mocks** | External APIs (Playwright, win32, DB, HTTP) |
| **Fixtures** | Use category fixtures (browser, desktop, http) |
| **Async** | @pytest.mark.asyncio |
| **Coverage Target** | 70%+ |

**Fixture Locations:**
- `tests/conftest.py` - Global fixtures (execution_context, mock_execution_context)
- `tests/nodes/browser/conftest.py` - Browser mocks (mock_page, mock_browser)
- `tests/nodes/desktop/conftest.py` - Desktop mocks (MockUIControl, MockDesktopElement)
- `tests/nodes/conftest.py` - HTTP mocks (create_mock_response)

**Template:**
```python
# tests/infrastructure/persistence/test_workflow_repository.py
@pytest.mark.asyncio
async def test_get_workflow_by_id(mocker):
    # Arrange: Mock Playwright
    mock_page = mocker.AsyncMock()
    mock_page.text_content.return_value = '{"name": "test"}'

    repository = WorkflowRepository(page=mock_page)

    # Act
    workflow = await repository.get_by_id(WorkflowId("wf1"))

    # Assert
    assert workflow.name == "test"
    mock_page.goto.assert_awaited_once()
```

### 3.4 Presentation Layer Tests
**Location:** `tests/presentation/`
**Principle:** Controller/logic testing. Minimal Qt widget testing.

| Aspect | Rule |
|--------|------|
| **Mocks** | Heavy Qt components, Use Cases |
| **Fixtures** | qtbot (pytest-qt) |
| **Async** | Avoid (Qt event loop complexity) |
| **Coverage Target** | 50%+ (Qt testing difficult) |

**Template:**
```python
# tests/presentation/test_workflow_controller.py
def test_save_workflow_updates_model(qtbot, mocker):
    # Arrange: Mock Use Case
    mock_use_case = mocker.Mock(spec=SaveWorkflowUseCase)
    controller = WorkflowController(save_use_case=mock_use_case)

    # Act
    controller.save_workflow(workflow_data={...})

    # Assert
    mock_use_case.execute.assert_called_once()
```

### 3.5 Node Tests
**Location:** `tests/nodes/{category}/`
**Principle:** Test 3 scenarios (SUCCESS, ERROR, EDGE_CASES). Use category fixtures.

| Aspect | Rule |
|--------|------|
| **Mocks** | External resources only |
| **Fixtures** | execution_context, category-specific mocks |
| **Async** | @pytest.mark.asyncio |
| **Coverage Target** | 80%+ |

**Test Scenarios:**
1. **SUCCESS:** Node executes normally, returns expected result
2. **ERROR:** Node handles exceptions gracefully
3. **EDGE_CASES:** Timeout, missing params, invalid input

**Template:**
```python
# tests/nodes/browser/test_click_element_node.py
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

@pytest.mark.asyncio
async def test_click_element_timeout(execution_context, mock_page):
    # Arrange
    node = ClickElementNode(selector="#missing", timeout=100)
    mock_page.query_selector.return_value = None
    execution_context.resources["page"] = mock_page

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is False
    assert "timeout" in result.get("error", "").lower()
```

---

## 4. Mocking Rules (Decision Table)

### 4.1 Always Mock (External APIs)
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

### 4.2 Never Mock (Domain & Pure Logic)
| Category | Items | Why |
|----------|-------|-----|
| **Domain Entities** | Workflow, Node, ExecutionState, RunContext | Pure logic, fast, deterministic |
| **Value Objects** | NodeId, PortId, DataType, ExecutionStatus | Immutable, fast, logic-focused |
| **Domain Services** | Pure functions, orchestration logic | No side effects, no I/O |
| **Standard Data Structures** | dict, list, dataclass, tuple | Built-in, no behavior to mock |

### 4.3 Context Dependent (Infrastructure)
| Item | Mock If | Real If | Rule |
|------|---------|---------|------|
| **ExecutionContext** | Has external deps | Pure logic | Use fixture from conftest.py |
| **Event Bus** | Unit testing logic | Integration testing | Mock for unit, real for E2E |
| **Resource Managers** | Testing client code | Testing manager itself | Mock external APIs, real manager |
| **Connection Pools** | Testing retry logic | Testing initialization | Mock connections, real pool |

### 4.4 Realistic Mocks (Not Just Stubs)
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

    def FindAll(self, scope, condition):
        # Simulate finding children
        return []
```

**Bad Example (Stub):**
```python
# DON'T DO THIS
mock_control = Mock()
mock_control.Name = "Button"  # Just returns value, no behavior
```

---

## 5. Async Testing Rules

### 5.1 Decision Tree
```
Is the function async def?
├─ YES
│  ├─ Mark test: @pytest.mark.asyncio
│  ├─ Mock with: AsyncMock()
│  └─ Assert with: assert_awaited_once()
└─ NO
   ├─ Regular def test_*()
   ├─ Mock with: Mock()
   └─ Assert with: assert_called_once()
```

### 5.2 Common Patterns

**Async Function Test:**
```python
@pytest.mark.asyncio
async def test_execute_workflow_async():
    orchestrator = ExecutionOrchestrator()
    result = await orchestrator.execute(workflow_id)
    assert result.status == ExecutionStatus.COMPLETED
```

**Mock Async Call:**
```python
@pytest.mark.asyncio
async def test_repository_saves(mocker):
    mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
    mock_repo.save.return_value = WorkflowId("wf1")

    result = await mock_repo.save(workflow)

    assert result == WorkflowId("wf1")
    mock_repo.save.assert_awaited_once()
```

**Async Context Manager:**
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

### 5.3 Common Mistakes
| Mistake | Problem | Fix |
|---------|---------|-----|
| `mock = Mock()` for async function | Won't track awaits | Use `AsyncMock()` |
| `await mock.method()` without AsyncMock | Fails | Create with `AsyncMock()` |
| No `@pytest.mark.asyncio` | Test runs sync, hangs | Add decorator |
| `mock.assert_called_once()` on async | Wrong assertion | Use `mock.assert_awaited_once()` |

---

## 6. Agent Protocol (Multi-Agent Coordination)

### 6.1 Brain Updates
After completing major tasks, update `.brain/` files:

| File | When | What |
|------|------|------|
| **activeContext.md** | After PLAN/BUILD phase | Current focus, blockers, decisions |
| **systemPatterns.md** | When discovering new pattern | Document reusable patterns found |
| **projectRules.md** | When rules change | Update this file (read-only outside main) |

**Update Commands:**
```bash
# After architecture decision
claude --context "Update .brain/activeContext.md with new decision"

# After discovering pattern
claude --context "Document pattern in .brain/systemPatterns.md"
```

### 6.2 Planning Protocol
1. **Create Plan File:** `.brain/plans/{feature}.md`
   ```markdown
   # Feature: {Name}

   ## Goal
   [What are we building?]

   ## Design
   [How? Diagrams/pseudocode]

   ## Tasks
   - [ ] Task 1
   - [ ] Task 2

   ## Unresolved Questions
   - Q: ?
   ```

2. **Launch Explore Agents (1-3 parallel):** Research, document findings
3. **User Approval:** Wait for sign-off before BUILD
4. **Execute in Parallel:** Up to 10 agents for implementation
5. **QA Phase:** Test + integration testing
6. **Documentation:** Generate user guides + API docs

### 6.3 State Machine
```
┌─────────┐     approval      ┌───────┐     QA      ┌──────┐
│  PLAN   ├──────────────────>│ BUILD ├───────────>│  QA  │
└─────────┘                   └───────┘            └──────┘
                                                        │
                                                    approval
                                                        │
                                                        v
                                                    ┌────────┐
                                                    │  DOCS  │
                                                    └────────┘
```

**Transitions:**
- PLAN → BUILD: Requires user approval of design
- BUILD → QA: All tasks completed
- QA → DOCS: Tests passing
- DOCS → END: Documentation complete

---

## 7. Worktree Protocol (Multi-Instance Work)

Use Git worktrees for parallel feature development:

### 7.1 Create Isolated Worktree
```bash
# From main repo directory
git worktree add -b feat/{name} ../{name} main

# Example
git worktree add -b feat/node-versioning ../node-versioning main
```

### 7.2 Work in Worktree
```bash
cd ../{name}
python run.py
pytest tests/
# Make changes...
git add . && git commit -m "feat: description"
```

### 7.3 Merge Back to Main
```bash
# In main repo
git checkout main
git merge feat/{name}
git push origin main

# Cleanup worktree
git worktree remove ../{name}
```

### 7.4 Rules
- **One worktree per agent** (no interference)
- **Base all on `main`** (always up-to-date)
- **Commit naming:** `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- **No force pushes** (respect other agents)
- **Clean up after merge** (remove worktree)

---

## 8. Command Reference

### 8.1 Development Commands
| Task | Command | Notes |
|------|---------|-------|
| **Run App** | `python run.py` | Launch Canvas + Robot |
| **Install** | `pip install -e .` | Development install (editable) |
| **Test (Fast)** | `pytest tests/ -v -m "not slow"` | Unit + fast integration |
| **Test (Full)** | `pytest tests/ -v` | All tests including slow |
| **Test (Coverage)** | `pytest tests/ -v --cov=casare_rpa --cov-report=html` | Generate coverage report |
| **Test (Perf)** | `pytest tests/performance/ -v -m slow` | Performance benchmarks |
| **Test (Single)** | `pytest tests/path/test_file.py::test_name -vv -s` | Single test with output |
| **Test (First Fail)** | `pytest tests/ -x` | Stop on first failure |
| **Test (Debugger)** | `pytest tests/ --pdb` | Drop into debugger on fail |

### 8.2 Code Quality
| Task | Command | Purpose |
|------|---------|---------|
| **Lint** | `ruff check src/ tests/` | Check code style |
| **Format** | `ruff format src/ tests/` | Auto-format code |
| **Type Check** | `mypy src/` | Static type analysis |
| **Coverage Report** | Open `htmlcov/index.html` | View coverage visually |

### 8.3 Git Workflow
| Task | Command | Notes |
|------|---------|-------|
| **Status** | `git status` | See changes |
| **Diff** | `git diff` | Staged changes |
| **Log** | `git log --oneline -10` | Recent commits |
| **Commit** | `git add . && git commit -m "..."` | Always after tests pass |
| **Push** | `git push origin {branch}` | Push to remote |

### 8.4 Quick Tests (TDD Cycle)
```bash
# Red: Write failing test
pytest tests/path/test_file.py::test_name -vv

# Green: Implement + Run
pytest tests/path/test_file.py::test_name -v

# Refactor + Full Suite
pytest tests/ -v

# Commit
git add tests/ src/ && git commit -m "feat: description"
```

---

## 9. Testing Checklist (TDD Cycle)

### 9.1 Before Committing
- [ ] Red phase: Test fails with clear error
- [ ] Green phase: Implementation passes test
- [ ] All related tests pass: `pytest tests/ -v`
- [ ] Coverage meets target (see Layer Rules section)
- [ ] No console warnings/errors
- [ ] Code is readable (naming, structure)

### 9.2 Commit Checklist
- [ ] Tests written first (for features) or after (for bugs)
- [ ] All tests pass locally
- [ ] Commit message is clear: `feat: add feature` or `fix: issue`
- [ ] No debug code (console.log, pdb, breakpoints)
- [ ] No commented-out code
- [ ] Imports are clean (no unused)

### 9.3 PR Checklist
- [ ] Feature complete + tested
- [ ] Documentation updated (docstrings, README)
- [ ] No breaking changes (or documented)
- [ ] Performance considered (async where needed)
- [ ] Error handling comprehensive
- [ ] Related tests passing on CI

---

## 10. Fixture Locations & Organization

### 10.1 Global Fixtures
**File:** `tests/conftest.py`

```python
@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create fresh ExecutionContext for each test."""
    return ExecutionContext(variables={}, resources={})

@pytest.fixture
def mock_execution_context(mocker) -> ExecutionContext:
    """ExecutionContext with mocked resources."""
    context = ExecutionContext(variables={}, resources={})
    context.resources["page"] = mocker.AsyncMock()
    context.resources["browser"] = mocker.AsyncMock()
    return context
```

### 10.2 Browser Category Fixtures
**File:** `tests/nodes/browser/conftest.py`

```python
@pytest.fixture
def mock_page(mocker):
    """Mock Playwright Page object."""
    mock = mocker.AsyncMock(spec=Page)
    mock.goto = mocker.AsyncMock()
    mock.query_selector = mocker.AsyncMock()
    return mock

@pytest.fixture
def mock_browser(mocker):
    """Mock Playwright Browser object."""
    return mocker.AsyncMock(spec=Browser)
```

### 10.3 Desktop Category Fixtures
**File:** `tests/nodes/desktop/conftest.py`

```python
class MockUIControl:
    """Realistic UIAutomation control."""
    def __init__(self, name="Button", control_type="Button"):
        self.Name = name
        self.ControlType = control_type

    def GetCurrentPropertyValue(self, prop_id: int):
        if prop_id == 30005:  # Name
            return self.Name
        raise PropertyNotSupported()

@pytest.fixture
def mock_ui_element():
    """Mock desktop UI element."""
    return MockUIControl(name="TestButton")
```

### 10.4 Fixture Discovery
```bash
# List all available fixtures
pytest --fixtures tests/

# Show fixtures for specific file
pytest --fixtures tests/nodes/browser/
```

---

## 11. Error Handling Standards

### 11.1 Exception Hierarchy
```
Exception
├── CasareRPAError (base)
│   ├── DomainError
│   │   ├── WorkflowValidationError
│   │   ├── DuplicateNodeError
│   │   └── NodeExecutionError
│   ├── ApplicationError
│   │   ├── WorkflowNotFoundError
│   │   ├── ExecutionFailedError
│   │   └── InvalidInputError
│   └── InfrastructureError
│       ├── RepositoryError
│       ├── ResourceNotAvailableError
│       └── ExternalServiceError
└── ...
```

### 11.2 Exception Handling Pattern
```python
# Domain: Raise domain-specific errors
if not self._name:
    raise WorkflowValidationError("Workflow name required")

# Application: Catch + translate
try:
    workflow = await self._repository.get(workflow_id)
except RepositoryError as e:
    raise ApplicationError(f"Failed to fetch workflow: {e}") from e

# Infrastructure: Catch external errors
try:
    response = await client.get(url)
except aiohttp.ClientError as e:
    raise ExternalServiceError(f"HTTP error: {e}") from e

# Presentation: Log + show to user
try:
    await use_case.execute()
except CasareRPAError as e:
    logger.error(f"Operation failed: {e}")
    self._event_bus.emit("error", {"message": str(e)})
```

---

## 12. Documentation Standards

### 12.1 Docstring Format (Google Style)
```python
def execute_node(
    node_id: NodeId,
    context: ExecutionContext,
    timeout: int = 5000
) -> Dict[str, Any]:
    """Execute a single node in a workflow.

    Executes the node identified by node_id within the given execution
    context. Respects the provided timeout for the operation.

    Args:
        node_id: Unique identifier of the node to execute.
        context: Current execution context with variables and resources.
        timeout: Maximum execution time in milliseconds. Defaults to 5000.

    Returns:
        Dictionary with keys:
            - success (bool): Whether execution succeeded
            - result (Any): Node output value
            - error (str): Error message if failed

    Raises:
        NodeNotFoundError: If node_id does not exist in workflow.
        ExecutionTimeoutError: If execution exceeds timeout.
        NodeExecutionError: If node execution fails.

    Example:
        >>> context = ExecutionContext(variables={}, resources={})
        >>> result = await execute_node(NodeId("n1"), context)
        >>> print(result["success"])
        True
    """
    ...
```

### 12.2 Inline Comments
- Only for "why", never "what" (code is self-documenting)
- Use sparingly

```python
# Good: Explains why
# Use exponential backoff to avoid overwhelming the service
retry_delay = min(2 ** attempt, 300)

# Bad: Explains what (code is already clear)
# Increment retry_delay
retry_delay = min(2 ** attempt, 300)
```

### 12.3 README Structure
1. **Project Overview** - What is CasareRPA?
2. **Quick Start** - Install + run in 5 minutes
3. **Architecture** - Layer diagram + responsibility
4. **Development** - Setup, testing, contributing
5. **API Reference** - Link to docs/
6. **FAQ** - Common issues

---

## 13. Performance Optimization Rules

### 13.1 When to Optimize
- **After profiling** (never guess)
- **For critical paths** (workflow execution, node setup)
- **For resource-intensive ops** (image processing, large loops)
- **Algorithmic improvements** (O(n²) → O(n log n))

### 13.2 Async Best Practices
```python
# Good: Concurrent execution
tasks = [execute_node(n, ctx) for n in nodes]
results = await asyncio.gather(*tasks)

# Bad: Sequential (slow)
results = [await execute_node(n, ctx) for n in nodes]
```

### 13.3 Resource Pooling
```python
# Good: Reuse connections
pool = ConnectionPool(max_size=10)
async with pool.get() as conn:
    await conn.execute(query)

# Bad: New connection per operation
conn = await create_connection()
await conn.execute(query)
await conn.close()
```

### 13.4 Profiling Command
```bash
# Profile execution
python -m cProfile -s cumulative run.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler script.py
```

---

## 14. Security Considerations

### 14.1 Input Validation
```python
# Always validate user input
def create_workflow(name: str) -> Workflow:
    if not name or len(name) > 255:
        raise ValidationError("Name must be 1-255 characters")
    return Workflow(name=name, description="")
```

### 14.2 Secrets Management
- NO hardcoded secrets in code
- Use environment variables or `.env` (never commit)
- Validate in CI/pre-commit hooks

### 14.3 Dependency Security
```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Update security patches
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

---

## 15. Quick Reference Tables

### 15.1 Test Command Cheat Sheet
```bash
# Discover tests
pytest --collect-only tests/

# Run with markers
pytest tests/ -m slow
pytest tests/ -m "not slow"

# Show test output
pytest tests/ -s -vv

# Debug
pytest tests/ --pdb --tb=short
```

### 15.2 Commit Message Format
```
feat: add login node for web automation
fix: resolve timeout on element click
refactor: extract node execution logic
test: add coverage for workflow validation
docs: update API reference for Orchestrator

# Detailed message (when needed)
feat: add login node for web automation

- Supports username/password input
- Handles 2FA via OTP
- Integrates with secure credential storage
- Adds 2 new tests (success, error cases)
```

### 15.3 Branch Naming
| Prefix | Example | Purpose |
|--------|---------|---------|
| `feat/` | `feat/node-versioning` | New feature |
| `fix/` | `fix/selector-timeout` | Bug fix |
| `refactor/` | `refactor/execution-engine` | Code restructure |
| `docs/` | `docs/api-reference` | Documentation |
| `test/` | `test/node-coverage` | Test improvements |

---

## 16. Troubleshooting

### 16.1 Common Issues
| Problem | Cause | Solution |
|---------|-------|----------|
| Test hangs | Missing `@pytest.mark.asyncio` | Add decorator to async tests |
| Flaky tests | Timing dependencies | Use event/signal waits, not sleep |
| Import errors | Circular dependency | Check layer rules, use interfaces |
| Mock not tracking calls | Using `Mock()` for async | Use `AsyncMock()` instead |

### 16.2 Debug Flags
```bash
# Show all print statements
pytest tests/ -s

# Very verbose output
pytest tests/ -vv

# Show local variables on failure
pytest tests/ -l

# Stop on first failure
pytest tests/ -x

# Last 5 failures
pytest tests/ --lf --maxfail=5
```

---

## 17. Release Checklist

Before releasing a new version:

- [ ] All tests passing (CI green)
- [ ] Coverage meets targets
- [ ] CHANGELOG.md updated
- [ ] Version bumped (semver)
- [ ] Documentation current
- [ ] No debug code
- [ ] No security vulnerabilities (safety check)
- [ ] Performance benchmarks acceptable
- [ ] Breaking changes documented
- [ ] Migration guide (if needed)

---

## Appendix A: Layer Dependency Diagram

```
┌─────────────────────────────────────┐
│         Presentation (UI)           │
│  MainWindow, Canvas, Controllers    │
│  EventBus, Widgets, Dialogs         │
└────────────┬────────────────────────┘
             │ depends on
             v
┌─────────────────────────────────────┐
│     Application (Use Cases)         │
│  ExecuteWorkflow, SaveWorkflow      │
│  DTOs, Interfaces, Orchestration    │
└────────────┬──────────┬─────────────┘
             │ depends  │ depends
             │ on       │ on
             v          v
┌──────────────────┐  ┌──────────────────────┐
│  Domain (Logic)  │  │  Infrastructure      │
│  Entities, VOs,  │  │  Repositories,       │
│  Services        │  │  Adapters, Resources │
│  NO deps!        │  │  (implements Domain) │
└──────────────────┘  └──────────────────────┘
```

---

## Appendix B: File Template Checklist

### B.1 New Domain Class
```python
"""Module docstring: Purpose of this module."""
from dataclasses import dataclass
from typing import Optional, List

class MyEntity:
    """Entity: Brief description."""

    def __init__(self, name: str):
        """Initialize entity."""
        if not name:
            raise ValueError("name required")
        self._name = name

    @property
    def name(self) -> str:
        """Entity name."""
        return self._name

    def do_something(self) -> None:
        """Perform action on entity."""
        pass
```

### B.2 New Application Use Case
```python
"""Module docstring."""
from casare_rpa.domain.workflow import Workflow, WorkflowId
from casare_rpa.infrastructure.persistence import WorkflowRepository

class MyUseCase:
    """Use Case: Brief description."""

    def __init__(self, repository: WorkflowRepository):
        self._repository = repository

    async def execute(self, workflow_id: WorkflowId) -> dict:
        """Execute use case."""
        workflow = await self._repository.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError()
        return {"success": True}
```

### B.3 New Infrastructure Adapter
```python
"""Module docstring."""
from casare_rpa.application.interfaces import IWorkflowRepository
from casare_rpa.domain.workflow import Workflow, WorkflowId

class MyRepository(IWorkflowRepository):
    """Repository: Implements IWorkflowRepository."""

    async def get_by_id(self, workflow_id: WorkflowId) -> Optional[Workflow]:
        """Fetch workflow by ID."""
        try:
            # External API call
            return Workflow(name="...")
        except Exception as e:
            raise RepositoryError(f"Failed to fetch: {e}") from e
```

### B.4 New Test
```python
"""Test module docstring."""
import pytest
from unittest.mock import AsyncMock, Mock
from casare_rpa.domain.workflow import Workflow, WorkflowId

class TestMyClass:
    """Test class: What is being tested."""

    def test_success_case(self):
        """Describes expected behavior in success case."""
        # Arrange
        obj = MyClass(param="value")

        # Act
        result = obj.do_something()

        # Assert
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_success(self, mocker):
        """Describes expected behavior for async operations."""
        # Arrange
        mock_repo = mocker.AsyncMock()
        mock_repo.get_by_id.return_value = Workflow(name="test")
        use_case = MyUseCase(repository=mock_repo)

        # Act
        result = await use_case.execute(WorkflowId("wf1"))

        # Assert
        assert result["success"] is True
        mock_repo.get_by_id.assert_awaited_once()
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-30 | Initial baseline - Clean DDD architecture, comprehensive testing rules |

---

**Status:** AUTHORITATIVE. This document supersedes all other standards documentation.
**Maintainer:** CasareRPA Technical Writing Team
**Last Review:** 2025-11-30
