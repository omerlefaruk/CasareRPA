# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Test Patterns Summary - File Reference Guide

Complete index of testing patterns and existing test files in CasareRPA.

## Existing Test Files (Reference)

### AI/ML Integration Tests
**Directory**: `tests/infrastructure/ai/`

| File | Lines | Purpose | Key Patterns |
|------|-------|---------|--------------|
| **conftest.py** | 111 | Fixture definitions | Mock data constants, @pytest.fixture decorators |
| **test_imports.py** | 345 | Module import verification | Class/function existence checks, type hints |
| **test_page_analyzer.py** | 531 | Page analyzer functionality | Multiple test classes per feature, assertion patterns |
| **test_playwright_mcp.py** | 492 | MCP client tests | AsyncMock, patch patterns, context managers |
| **test_url_detection.py** | Varies | URL pattern detection | Regex testing, edge cases |

### Architecture

```
tests/
├── infrastructure/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── conftest.py              ← REFERENCE: Mock data + fixtures
│   │   ├── test_imports.py          ← REFERENCE: Import pattern
│   │   ├── test_page_analyzer.py    ← REFERENCE: Execution tests
│   │   ├── test_playwright_mcp.py   ← REFERENCE: AsyncMock pattern
│   │   └── test_url_detection.py
│   └── (future: google/, http/, etc.)
```

---

## Fixture Patterns Reference

### Location: `tests/infrastructure/ai/conftest.py`

**Pattern 1: Mock Data Constants**
```python
# Define at module level (lines 9-64)
MOCK_LOGIN_PAGE_SNAPSHOT = """- WebArea "Login Page" [ref=root]:
  - form [ref=form1]:
    - textbox "Username" [ref=e1]
    ...
```

**Pattern 2: Simple Fixture**
```python
# Lines 67-70
@pytest.fixture
def login_page_snapshot() -> str:
    """Return mock login page snapshot."""
    return MOCK_LOGIN_PAGE_SNAPSHOT
```

**Pattern 3: Complex Fixture**
```python
# Lines 103-110
@pytest.fixture
def sample_page_dict() -> Dict[str, Any]:
    """Return sample page context as dict for MCP mock."""
    return {
        "url": "https://example.com/login",
        "title": "Example Login",
        "snapshot": MOCK_LOGIN_PAGE_SNAPSHOT,
    }
```

---

## Test Class Organization

### Location: `tests/infrastructure/ai/test_page_analyzer.py`

**Pattern: Group tests by feature (Class-based)**

```python
# Lines 32-60
class TestPageAnalyzerEmptySnapshot:
    """Tests for empty/missing snapshot handling."""

    def test_analyze_empty_snapshot_returns_empty_context(self, empty_snapshot: str):
        """Empty snapshot should return empty PageContext with no errors."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(empty_snapshot, url="", title="")
        assert context.is_empty() is True

    def test_analyze_none_snapshot_returns_empty_context(self):
        """None/empty string snapshot should not raise errors."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot("", url="", title="")
        assert context.is_empty() is True
```

**Organization Benefits**:
- One class per feature/scenario
- Clear docstrings
- Fixtures passed as parameters
- Related assertions grouped

---

## Async Test Pattern

### Location: `tests/infrastructure/ai/test_playwright_mcp.py`

**Pattern 1: Basic Async Test**
```python
# Lines 129-141
@pytest.mark.asyncio
async def test_start_without_npx_fails_gracefully(self, client):
    """Should handle missing npx gracefully."""
    client._npx_path = "/nonexistent/path/npx"

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=FileNotFoundError("npx not found"),
    ):
        result = await client.start()

    assert result is False
    assert client._initialized is False
```

**Pattern 2: AsyncMock with Patch**
```python
# Lines 179-192
@pytest.mark.asyncio
async def test_navigate_calls_correct_tool(self, initialized_client):
    """Should call browser_navigate tool with URL."""
    with patch.object(
        initialized_client, "call_tool", new_callable=AsyncMock
    ) as mock_call:
        mock_call.return_value = MCPToolResult(success=True, content=[])

        result = await initialized_client.navigate("https://example.com")

        mock_call.assert_called_once()
        call_args = mock_call.call_args
        assert call_args[0][0] == "browser_navigate"
        assert call_args[0][1]["url"] == "https://example.com"
```

**Pattern 3: Async Context Manager Test**
```python
# Lines 317-330
@pytest.mark.asyncio
async def test_context_manager_starts_and_stops(self):
    """Should start on enter and stop on exit."""
    client = PlaywrightMCPClient(headless=True)

    with patch.object(client, "start", new_callable=AsyncMock) as mock_start:
        with patch.object(client, "stop", new_callable=AsyncMock) as mock_stop:
            mock_start.return_value = True

            async with client as c:
                mock_start.assert_called_once()
                assert c is client

            mock_stop.assert_called_once()
```

---

## Mock Patterns Reference

### Pattern 1: AsyncMock Fixture

**Location**: `tests/infrastructure/ai/test_playwright_mcp.py` lines 111-122

```python
@pytest.fixture
def mock_process(self):
    """Create mock subprocess."""
    process = AsyncMock()
    process.stdin = AsyncMock()
    process.stdout = AsyncMock()
    process.stderr = AsyncMock()
    process.returncode = None
    process.terminate = Mock()
    process.kill = Mock()
    process.wait = AsyncMock()
    return process
```

**Usage Pattern**:
```python
def test_something(self, mock_process):
    # Use mock_process as if it were a real subprocess
    assert mock_process.stdin is not None
```

### Pattern 2: Patch with Return Value

**Location**: `tests/infrastructure/ai/test_playwright_mcp.py` lines 368-388

```python
with patch(
    "casare_rpa.infrastructure.ai.playwright_mcp.PlaywrightMCPClient",
    autospec=True,
) as MockClient:
    mock_instance = AsyncMock()
    MockClient.return_value = mock_instance

    # Mock async context manager
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=None)

    mock_instance.navigate = AsyncMock(return_value=mock_nav_result)
    mock_instance.wait_for = AsyncMock(return_value=mock_wait_result)

    result = await fetch_page_context("https://example.com")
```

### Pattern 3: Patch with Side Effect

**Location**: `tests/infrastructure/ai/test_playwright_mcp.py` lines 457-465

```python
@pytest.mark.asyncio
async def test_start_general_exception(self, client):
    """Should handle general exceptions during start."""
    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=Exception("Unknown error")
    ):
        result = await client.start()

    assert result is False
```

---

## Error Handling Test Pattern

### Location: `tests/infrastructure/ai/test_playwright_mcp.py`

**Pattern: Test Error Scenarios**
```python
# Lines 449-481
class TestMCPErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create client for error testing."""
        return PlaywrightMCPClient(headless=True)

    @pytest.mark.asyncio
    async def test_start_general_exception(self, client):
        """Should handle general exceptions during start."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=Exception("Unknown error")
        ):
            result = await client.start()

        assert result is False

    @pytest.mark.asyncio
    async def test_call_tool_exception(self, client):
        """Should handle exceptions during tool call."""
        client._initialized = True
        client._process = Mock()
        client._process.stdin = AsyncMock()

        with patch.object(
            client, "_send_request",
            side_effect=Exception("Request failed")
        ):
            result = await client.call_tool("test_tool", {})

        assert result.success is False
        assert "failed" in result.error.lower()
```

---

## Import Verification Test Pattern

### Location: `tests/infrastructure/ai/test_imports.py`

**Pattern: Verify Imports**
```python
# Lines 18-49
class TestPlaywrightMCPImports:
    """Tests for playwright_mcp module imports."""

    def test_import_playwright_mcp_module(self):
        """Should import playwright_mcp module without errors."""
        from casare_rpa.infrastructure.ai import playwright_mcp
        assert playwright_mcp is not None

    def test_import_playwright_mcp_client(self):
        """Should import PlaywrightMCPClient class."""
        from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient
        assert PlaywrightMCPClient is not None
        assert callable(PlaywrightMCPClient)

    def test_playwright_mcp_client_has_expected_methods(self):
        """Should have all expected public methods."""
        from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

        client = PlaywrightMCPClient()

        # Lifecycle methods
        assert hasattr(client, "start")
        assert hasattr(client, "stop")
```

---

## Node Testing Pattern (For Google/HTTP nodes)

### ExecutionContext Setup

**Location**: `src/casare_rpa/infrastructure/execution/execution_context.py`

```python
# From GOOGLE_NODE_TEST_EXAMPLE.md conftest.py

@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context with Google credentials."""
    return ExecutionContext(
        workflow_name="Test Google Workflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={
            "credential_id": "test_cred_123",
            "api_key": "test_api_key",
        },
    )
```

### Node Execution Test

```python
# From GOOGLE_NODE_TEST_EXAMPLE.md test_drive_upload_node.py

@pytest.mark.asyncio
async def test_upload_file_success(
    self,
    execution_context: ExecutionContext,
    mock_google_drive_client: AsyncMock,
    upload_response,
):
    """Should successfully upload file to Drive."""
    # Setup
    node = DriveUploadFileNode("upload_node_1")
    node.set_input("file_path", "/tmp/test_file.pdf")
    node.set_input("folder_id", "folder_123")

    # Mock
    with patch(
        "casare_rpa.nodes.google.google_base.GoogleDriveClient"
    ) as MockClient:
        MockClient.return_value = mock_google_drive_client

        # Execute
        result = await node.execute(execution_context)

    # Assert
    assert result["success"] is True
    assert result["file_id"] == "new_file_id_123"
```

---

## Pytest Configuration

### Location: `pyproject.toml`

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --cov=casare_rpa --cov-fail-under=75"
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
]
```

**Key Settings**:
- `asyncio_mode = "auto"` - Makes @pytest.mark.asyncio optional (but still use it for clarity)
- `cov-fail-under=75` - Tests must achieve 75%+ coverage
- `testpaths = ["tests"]` - Only tests/ directory is tested
- `python_files = ["test_*.py"]` - Must name files test_*.py

---

## File Mapping: Where to Find Things

| What | Where | Lines |
|------|-------|-------|
| Mock data examples | `tests/infrastructure/ai/conftest.py` | 9-111 |
| Fixture patterns | `tests/infrastructure/ai/conftest.py` | 67-110 |
| Test class organization | `tests/infrastructure/ai/test_page_analyzer.py` | 32-109 |
| Async test pattern | `tests/infrastructure/ai/test_playwright_mcp.py` | 129-141 |
| AsyncMock fixture | `tests/infrastructure/ai/test_playwright_mcp.py` | 111-122 |
| Patch with return value | `tests/infrastructure/ai/test_playwright_mcp.py` | 368-388 |
| Patch with side effect | `tests/infrastructure/ai/test_playwright_mcp.py` | 457-465 |
| Error handling tests | `tests/infrastructure/ai/test_playwright_mcp.py` | 449-481 |
| Import verification | `tests/infrastructure/ai/test_imports.py` | 18-49 |
| ExecutionContext interface | `src/casare_rpa/domain/interfaces/execution_context.py` | 29-268 |
| ExecutionContext impl | `src/casare_rpa/infrastructure/execution/execution_context.py` | 34-130 |
| Google base node | `src/casare_rpa/nodes/google/google_base.py` | 1-150 |
| Drive upload node | `src/casare_rpa/nodes/google/drive/drive_files.py` | 98-200 |
| Pytest config | `pyproject.toml` | [tool.pytest.ini_options] |

---

## Quick Pattern Index

| Pattern | File | Lines | Purpose |
|---------|------|-------|---------|
| Mock constants | conftest.py | 9-64 | Reusable test data |
| Simple fixture | conftest.py | 67-70 | Return mock data |
| Complex fixture | conftest.py | 103-110 | Return dict with mock data |
| AsyncMock fixture | test_playwright_mcp.py | 111-122 | Mock async client |
| Test class | test_page_analyzer.py | 32-60 | Group related tests |
| Async test | test_playwright_mcp.py | 129-141 | Use @pytest.mark.asyncio |
| Patch object method | test_playwright_mcp.py | 179-192 | Mock instance method |
| Patch import | test_playwright_mcp.py | 368-388 | Mock class import |
| Side effect | test_playwright_mcp.py | 457-465 | Simulate errors |
| Error handling | test_playwright_mcp.py | 449-481 | Test error paths |
| Import tests | test_imports.py | 18-49 | Verify modules load |

---

## Document References

| Document | Purpose | Audience |
|----------|---------|----------|
| **TESTING_PATTERNS.md** | Complete testing guide | Detailed reference |
| **TEST_IMPLEMENTATION_QUICK_START.md** | Copy-paste templates | Quick implementation |
| **GOOGLE_NODE_TEST_EXAMPLE.md** | Full working examples | Real implementation guide |
| **TEST_PATTERNS_SUMMARY.md** | This document | File mapping & index |

---

## How to Use This Guide

### I Want to...

**Understand async testing**
→ Read `TESTING_PATTERNS.md` section "Async Test Pattern" + look at `test_playwright_mcp.py` lines 129-141

**Create tests for a new node**
→ Start with `TEST_IMPLEMENTATION_QUICK_START.md` templates + copy from `GOOGLE_NODE_TEST_EXAMPLE.md`

**Find a specific pattern**
→ Use the "Quick Pattern Index" table above to locate file and lines

**Copy fixture code**
→ Go to `tests/infrastructure/ai/conftest.py` and adapt lines shown in "Fixture Patterns Reference"

**Understand mocking**
→ Read "Mock Patterns Reference" section and examine lines in `test_playwright_mcp.py`

---

## Summary Statistics

**Existing Tests**:
- Total test files: 5 (in infrastructure/ai/)
- Total test lines: ~2,000
- Total test methods: 100+
- Coverage requirement: 75%+

**Key Technologies**:
- pytest: 6.0+
- pytest-asyncio: 0.20+
- unittest.mock: AsyncMock, patch
- Python: 3.12+

**Architecture**:
- Domain Layer: Pure logic (ExecutionContext interface)
- Infrastructure Layer: Concrete implementations (ExecutionContext, clients)
- Application Layer: Use cases and orchestration
- Presentation Layer: Qt UI (not tested here)
