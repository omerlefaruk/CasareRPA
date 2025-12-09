# TDD Guide

## Philosophy
- **Test-First** for NEW features
- **Test-After** for BUGS (characterization tests)

## Layer Rules
| Layer | Mocks | Location |
|-------|-------|----------|
| Domain | None (real objects) | tests/domain/ |
| Application | Infrastructure only | tests/application/ |
| Infrastructure | ALL external APIs | tests/nodes/ |
| Presentation | Heavy Qt components | tests/presentation/ |

## Red-Green-Refactor Cycle
1. **Red:** Write failing test. Run: `pytest path/to/test.py::test_name -v`
2. **Green:** Write minimal code to pass
3. **Refactor:** Clean code, tests still pass
4. **Commit:** `git add tests/ src/ && git commit -m "feat: description"`

## Async Testing Rules
```python
# Mark async tests
@pytest.mark.asyncio
async def test_something():
    ...

# Use AsyncMock for async calls
mock_repo = AsyncMock()
await mock_repo.save()
mock_repo.save.assert_awaited_once()
```

## Mocking Strategy

### Always Mock
- Playwright (Page, Browser, BrowserContext)
- UIAutomation (Control, Pattern, Element)
- win32 APIs (win32gui, win32con, ctypes)
- UnifiedHttpClient (infrastructure/http/) - Mock the client, not raw httpx/aiohttp
- Database connections (asyncpg, aiomysql)
- File system I/O (aiofiles)
- PIL/Image operations
- External processes (subprocess)
- Qt heavy components (QMainWindow, QApplication)

### Prefer Real
- Domain entities (Workflow, Node, ExecutionState)
- Value objects (NodeId, PortId, DataType)
- Domain interfaces (INode, IExecutionContext as test doubles)
- Domain services (pure logic)
- Simple data structures (dict, list, dataclasses)

## Test Fixtures

| Scope | File | Fixtures |
|-------|------|----------|
| Global | tests/conftest.py | execution_context, mock_execution_context |
| Browser | tests/nodes/browser/conftest.py | mock_page, mock_browser |
| Desktop | tests/nodes/desktop/conftest.py | MockUIControl, mock_win32 |
| HTTP | tests/infrastructure/http/conftest.py | mock_http_client, mock_response |
| Domain | tests/domain/interfaces/conftest.py | mock_node, mock_context |

### HTTP Client Mocking
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_http_node(execution_context):
    with patch("casare_rpa.infrastructure.http.UnifiedHttpClient") as MockClient:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "test"}
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client

        node = MyHttpNode(url="https://api.example.com")
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_client.get.assert_awaited_once()
```

## Node Test Template
```python
@pytest.mark.asyncio
async def test_node_success(execution_context, category_fixtures):
    # Arrange
    node = SomeNode(param1="value")
    # Setup mocks

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is True

@pytest.mark.asyncio
async def test_node_error(execution_context, category_fixtures):
    # Arrange: Configure to fail
    node = SomeNode(param1="invalid")

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is False
    assert "error" in result
```

## Quality Standards

### Assertions
- One logical assertion per test
- Assert on BEHAVIOR, not implementation
- Use descriptive messages: `assert x, "reason"`

### Isolation
- Tests independent (order doesn't matter)
- No shared state
- Use fixtures for setup

### Avoid Flaky Tests
```python
# Bad
await asyncio.sleep(1)

# Good
await wait_for_condition(lambda: resource.is_ready(), timeout=5)
```

## Commands

```bash
# Run all
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=casare_rpa --cov-report=term

# Fast (skip slow)
pytest tests/ -v -m "not slow"

# Debug
pytest tests/path/test.py::test_name -vv -s
pytest tests/ -x  # Stop on first failure
pytest tests/ --pdb  # Debugger on failure
```

## Coverage Targets
| Layer | Target |
|-------|--------|
| Domain | 90%+ |
| Application | 85%+ |
| Infrastructure | 70%+ |
| Presentation | 50%+ |
| Nodes | 80%+ |

## Markers
```python
@pytest.mark.slow        # Long-running
@pytest.mark.integration # Integration tests
@pytest.mark.e2e         # End-to-end
@pytest.mark.ui          # UI/Qt tests (require display)
```

## Domain Interface Testing

Test against INode protocol for dependency inversion:
```python
from casare_rpa.domain.interfaces import INode, IExecutionContext

def test_node_implements_protocol():
    node = MyNode()
    assert isinstance(node, INode)  # Protocol check
    assert hasattr(node, "execute")
    assert hasattr(node, "get_parameter")
```
