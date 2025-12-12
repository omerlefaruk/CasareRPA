# Testing Guide

This guide covers testing practices for CasareRPA, including TDD workflow, test structure, and mocking strategies.

## Philosophy

- **Test-First** for NEW features (Red-Green-Refactor)
- **Test-After** for BUGS (characterization tests to capture behavior)
- **Tests are documentation** - Show how code is meant to be used

## Test Structure Overview

```
tests/
├── conftest.py              # Global fixtures
├── domain/                  # Domain layer tests (no mocks)
│   ├── entities/
│   ├── services/
│   └── value_objects/
├── application/             # Use case tests (mock infrastructure)
│   ├── use_cases/
│   └── services/
├── infrastructure/          # Adapter tests (mock external APIs)
│   ├── persistence/
│   ├── http/
│   └── browser/
├── nodes/                   # Node tests by category
│   ├── browser/
│   ├── desktop/
│   └── conftest.py          # Shared node fixtures
├── presentation/            # UI tests (mock heavy Qt components)
│   └── canvas/
└── e2e/                     # End-to-end tests
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/ -v

# Run fast tests (skip slow)
pytest tests/ -v -m "not slow"

# Run with coverage
pytest tests/ -v --cov=casare_rpa --cov-report=term

# Run with HTML coverage report
pytest tests/ -v --cov=casare_rpa --cov-report=html
# Then open htmlcov/index.html

# Run single test
pytest tests/path/test_file.py::test_name -vv -s

# Stop on first failure
pytest tests/ -x

# Debug on failure
pytest tests/ --pdb
```

### Test Markers

```python
@pytest.mark.slow        # Long-running tests
@pytest.mark.integration # Integration tests
@pytest.mark.e2e         # End-to-end tests
@pytest.mark.ui          # UI/Qt tests (require display)
```

Run by marker:

```bash
# Run only slow tests
pytest tests/ -m slow

# Skip slow tests
pytest tests/ -m "not slow"

# Run integration tests
pytest tests/ -m integration
```

## Red-Green-Refactor Cycle (TDD)

### 1. Red: Write a Failing Test

```bash
pytest tests/path/test_file.py::test_name -v
# Expected: FAILED
```

```python
def test_workflow_validates_name():
    """Workflow requires non-empty name."""
    with pytest.raises(ValueError, match="name required"):
        Workflow(name="", description="test")
```

### 2. Green: Write Minimal Code to Pass

```python
class Workflow:
    def __init__(self, name: str, description: str = ""):
        if not name:
            raise ValueError("name required")
        self._name = name
```

```bash
pytest tests/path/test_file.py::test_name -v
# Expected: PASSED
```

### 3. Refactor: Clean Up

Keep tests passing while improving code structure.

```bash
pytest tests/ -v
# Expected: All PASSED
```

### 4. Commit

```bash
git add tests/ src/
git commit -m "feat: add workflow name validation"
```

## Layer-Specific Testing Rules

### Domain Layer Tests

**Location:** `tests/domain/`
**Principle:** NO mocks. Pure logic with real domain objects.

| Aspect | Rule |
|--------|------|
| Mocks | NEVER |
| Fixtures | Real domain objects |
| Async | No async tests (domain is sync) |
| Coverage | 90%+ |

```python
# tests/domain/test_workflow.py
class TestWorkflow:
    def test_add_node_success(self):
        """Adding a valid node increments count."""
        workflow = Workflow(name="test")
        node = Node(id=NodeId("n1"), type="start")

        workflow.add_node(node)

        assert len(workflow.nodes) == 1
        assert workflow.nodes[0].id == NodeId("n1")

    def test_add_duplicate_node_raises_error(self):
        """Adding same node twice raises DuplicateNodeError."""
        workflow = Workflow(name="test")
        node = Node(id=NodeId("n1"), type="start")
        workflow.add_node(node)

        with pytest.raises(DuplicateNodeError):
            workflow.add_node(node)
```

### Application Layer Tests

**Location:** `tests/application/`
**Principle:** Mock infrastructure, use real domain objects.

| Aspect | Rule |
|--------|------|
| Mocks | Infrastructure only (repos, adapters) |
| Fixtures | Real domain objects, AsyncMock for async deps |
| Async | `@pytest.mark.asyncio` |
| Coverage | 85%+ |

```python
# tests/application/test_execute_workflow.py
@pytest.mark.asyncio
async def test_execute_workflow_saves_result(mocker):
    # Arrange: Mock infrastructure
    mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
    mock_repo.get_by_id.return_value = Workflow(name="test")

    use_case = ExecuteWorkflowUseCase(repository=mock_repo)

    # Act
    result = await use_case.execute(WorkflowId("wf1"))

    # Assert
    assert result.status == ExecutionStatus.COMPLETED
    mock_repo.save_execution.assert_awaited_once()
```

### Infrastructure Layer Tests

**Location:** `tests/infrastructure/` or `tests/nodes/`
**Principle:** Mock ALL external APIs (Playwright, UIAutomation, DB, HTTP).

| Aspect | Rule |
|--------|------|
| Mocks | External APIs (Playwright, win32, DB, HTTP) |
| Fixtures | Use category fixtures |
| Async | `@pytest.mark.asyncio` |
| Coverage | 70%+ |

```python
# tests/infrastructure/http/test_unified_http_client.py
@pytest.mark.asyncio
async def test_http_get_success(mocker):
    with patch("casare_rpa.infrastructure.http.UnifiedHttpClient") as MockClient:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "test"}
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client

        async with UnifiedHttpClient() as client:
            response = await client.get("https://api.example.com")

        assert response.json() == {"data": "test"}
        mock_client.get.assert_awaited_once()
```

### Node Tests

**Location:** `tests/nodes/{category}/`
**Principle:** Test 3 scenarios: SUCCESS, ERROR, EDGE_CASES.

| Aspect | Rule |
|--------|------|
| Mocks | External resources only |
| Fixtures | execution_context, category-specific mocks |
| Async | `@pytest.mark.asyncio` |
| Coverage | 80%+ |

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

### Presentation Layer Tests

**Location:** `tests/presentation/`
**Principle:** Controller/logic testing. Minimal Qt widget testing.

| Aspect | Rule |
|--------|------|
| Mocks | Heavy Qt components, Use Cases |
| Fixtures | qtbot (pytest-qt) |
| Async | Avoid (Qt event loop complexity) |
| Coverage | 50%+ |

```python
# tests/presentation/test_workflow_controller.py
def test_save_workflow_calls_use_case(qtbot, mocker):
    # Arrange
    mock_use_case = mocker.Mock(spec=SaveWorkflowUseCase)
    controller = WorkflowController(save_use_case=mock_use_case)

    # Act
    controller.save_workflow(workflow_data={"name": "test"})

    # Assert
    mock_use_case.execute.assert_called_once()
```

## Mocking Strategy

### Always Mock (External APIs)

| Category | Items |
|----------|-------|
| Browser APIs | Playwright Page, Browser, BrowserContext, Frame |
| Desktop APIs | UIAutomation Control, Pattern, Element |
| Windows APIs | win32gui, win32con, ctypes, pywinauto |
| HTTP Clients | aiohttp.ClientSession, httpx.AsyncClient, UnifiedHttpClient |
| Databases | asyncpg.Connection, aiomysql.Cursor |
| File I/O | aiofiles, pathlib (large files) |
| Image Processing | PIL/Image.open, cv2 |
| External Processes | subprocess, os.system |

### Never Mock (Domain & Pure Logic)

| Category | Items |
|----------|-------|
| Domain Entities | Workflow, Node, ExecutionState, RunContext |
| Value Objects | NodeId, PortId, DataType, ExecutionStatus |
| Domain Services | Pure functions, orchestration logic |
| Standard Data | dict, list, dataclass, tuple |

### Realistic Mocks

Mocks should **behave** like real objects, not just return values.

```python
# GOOD: Behavioral mock
class MockUIControl:
    """Realistic UIAutomation control mock."""

    def __init__(self, name="Button", control_type="Button", enabled=True):
        self.Name = name
        self.ControlType = control_type
        self._enabled = enabled

    def GetCurrentPropertyValue(self, property_id: int):
        if property_id == 30003:  # IsEnabled
            return self._enabled
        if property_id == 30005:  # Name
            return self.Name
        raise PropertyNotSupported(f"Property {property_id}")


# BAD: Stub (just returns values)
mock_control = Mock()
mock_control.Name = "Button"  # No behavior!
```

## Async Testing

### Mark Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

### Use AsyncMock

```python
@pytest.mark.asyncio
async def test_repository_saves(mocker):
    mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
    mock_repo.save.return_value = WorkflowId("wf1")

    result = await mock_repo.save(workflow)

    assert result == WorkflowId("wf1")
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

### Common Async Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `Mock()` for async | Won't track awaits | Use `AsyncMock()` |
| No `@pytest.mark.asyncio` | Test runs sync, hangs | Add decorator |
| `assert_called_once()` on async | Wrong assertion | Use `assert_awaited_once()` |

## Test Fixtures

### Global Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def execution_context() -> ExecutionContext:
    """Fresh ExecutionContext for each test."""
    return ExecutionContext(variables={}, resources={})

@pytest.fixture
def mock_execution_context(mocker) -> ExecutionContext:
    """ExecutionContext with mocked resources."""
    context = ExecutionContext(variables={}, resources={})
    context.resources["page"] = mocker.AsyncMock()
    context.resources["browser"] = mocker.AsyncMock()
    return context
```

### Browser Fixtures (`tests/nodes/browser/conftest.py`)

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

### Desktop Fixtures (`tests/nodes/desktop/conftest.py`)

```python
@pytest.fixture
def mock_ui_element():
    """Mock desktop UI element."""
    return MockUIControl(name="TestButton", control_type="Button")
```

### Discover Available Fixtures

```bash
# List all fixtures
pytest --fixtures tests/

# Fixtures for specific directory
pytest --fixtures tests/nodes/browser/
```

## Coverage Targets

| Layer | Target |
|-------|--------|
| Domain | 90%+ |
| Application | 85%+ |
| Infrastructure | 70%+ |
| Presentation | 50%+ |
| Nodes | 80%+ |

Check coverage:

```bash
pytest tests/ -v --cov=casare_rpa --cov-report=term

# HTML report
pytest tests/ -v --cov=casare_rpa --cov-report=html
```

## Quality Standards

### Assertions

- One logical assertion per test
- Assert on BEHAVIOR, not implementation
- Use descriptive messages: `assert x, "reason"`

### Isolation

- Tests must be independent (order doesn't matter)
- No shared state between tests
- Use fixtures for setup

### Avoid Flaky Tests

```python
# BAD: Time-based wait
await asyncio.sleep(1)

# GOOD: Condition-based wait
await wait_for_condition(lambda: resource.is_ready(), timeout=5)
```

## Debug Commands

```bash
# Show all print statements
pytest tests/ -s

# Very verbose output
pytest tests/ -vv

# Show local variables on failure
pytest tests/ -l

# Stop on first failure
pytest tests/ -x

# Rerun last failures
pytest tests/ --lf

# Debug on failure
pytest tests/ --pdb --tb=short
```

## Node Test Template

Use this template for all new node tests:

```python
"""Tests for SomeNode."""
import pytest
from unittest.mock import AsyncMock

from casare_rpa.nodes.category import SomeNode


class TestSomeNode:
    """Test suite for SomeNode."""

    @pytest.mark.asyncio
    async def test_success_case(self, execution_context, category_fixtures):
        """Describe expected success behavior."""
        # Arrange
        node = SomeNode(param1="value")
        # Setup mocks...

        # Act
        result = await node.execute(execution_context)

        # Assert
        assert result["success"] is True
        assert "output" in result

    @pytest.mark.asyncio
    async def test_error_handling(self, execution_context, category_fixtures):
        """Describe expected error behavior."""
        # Arrange: Configure to fail
        node = SomeNode(param1="invalid")

        # Act
        result = await node.execute(execution_context)

        # Assert
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_edge_case(self, execution_context, category_fixtures):
        """Describe edge case behavior."""
        # Arrange
        node = SomeNode(param1="edge_value")

        # Act
        result = await node.execute(execution_context)

        # Assert
        # Verify edge case handling
```

## Related Documentation

- [Coding Standards](coding-standards.md) - Style guidelines
- [Pull Request Guidelines](pull-requests.md) - PR requirements
- `.brain/docs/tdd-guide.md` - Full TDD reference

---

**Questions?** Check `.brain/docs/tdd-guide.md` for detailed patterns.
