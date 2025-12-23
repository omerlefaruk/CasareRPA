<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# Testing Patterns for CasareRPA Integration Nodes

Comprehensive guide for testing integration nodes (Google, HTTP, etc.) in CasareRPA based on existing codebase patterns.

## Quick Summary

- **Test Location**: `tests/infrastructure/{module_name}/`
- **Pytest Config**: Coverage requirement 75%+, async support enabled
- **Async Support**: Pytest-asyncio with `@pytest.mark.asyncio` decorator
- **Mocking**: unittest.mock (AsyncMock for async clients, Mock for sync resources)
- **Key Fixture Pattern**: conftest.py with reusable mock data

## File Structure

### Test Directory Layout
```
tests/
├── infrastructure/
│   ├── ai/                    # AI/ML integration tests
│   │   ├── conftest.py       # Shared fixtures (mock snapshots, page data)
│   │   ├── test_imports.py   # Module/class import verification
│   │   ├── test_page_analyzer.py
│   │   ├── test_playwright_mcp.py
│   │   └── test_url_detection.py
│   └── (future: google/, http/, etc.)
```

### Pytest Configuration
**File**: `pyproject.toml`
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --cov=casare_rpa --cov-fail-under=75"
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
]
```

**Run tests**:
```bash
pytest tests/ -v                           # Run all tests
pytest tests/infrastructure/ai/ -v         # Run module tests
pytest tests/ -m "not slow" -v            # Exclude slow tests
pytest tests/ --cov=casare_rpa            # With coverage report
```

---

## ExecutionContext Setup (For Node Testing)

### Location
`src/casare_rpa/infrastructure/execution/execution_context.py`

### Key Features for Testing

```python
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import ExecutionMode

# Basic initialization
context = ExecutionContext(
    workflow_name="Test Workflow",
    mode=ExecutionMode.NORMAL,
    initial_variables={"api_key": "test-key", "user_id": "123"}
)

# Access/set variables
context.set_variable("result", {"status": "success"})
value = context.get_variable("api_key")
has_var = context.has_variable("result")

# Execution flow control
context.set_current_node(NodeId("node-1"))
context.add_error(NodeId("node-1"), "Connection failed")
context.stop_execution()

# Resource storage
context.resources["http_client"] = mock_client
context.resources["credential_provider"] = mock_provider
```

### Interface Protocol
**File**: `src/casare_rpa/domain/interfaces/execution_context.py`

The `IExecutionContext` protocol defines:
- **Variables**: `set_variable()`, `get_variable()`, `has_variable()`, `resolve_value()`
- **Execution**: `set_current_node()`, `add_error()`, `stop_execution()`, `mark_completed()`
- **Browser** (optional): `get_active_page()`, `set_active_page()`, `get_page()`
- **Resources**: `resources` dict for storing/retrieving shared objects

---

## Fixture Patterns

### Pattern 1: Conftest.py with Mock Data

**File**: `tests/infrastructure/ai/conftest.py`

```python
import pytest
from typing import Dict, Any

# Define mock data constants at module level
MOCK_LOGIN_PAGE_SNAPSHOT = """- WebArea "Login Page" [ref=root]:
  - form [ref=form1]:
    - textbox "Username" [ref=e1]
    - textbox "Password" [ref=e2]
    - button "Login" [ref=e3]:"""

@pytest.fixture
def login_page_snapshot() -> str:
    """Return mock login page snapshot."""
    return MOCK_LOGIN_PAGE_SNAPSHOT

@pytest.fixture
def sample_page_dict() -> Dict[str, Any]:
    """Return sample page context as dict."""
    return {
        "url": "https://example.com/login",
        "title": "Example Login",
        "snapshot": MOCK_LOGIN_PAGE_SNAPSHOT,
    }
```

**Usage in tests**:
```python
def test_analyze_page(self, login_page_snapshot: str):
    """Test function receives fixture as parameter."""
    context = PageAnalyzer().analyze_snapshot(login_page_snapshot)
    assert len(context.forms) >= 1
```

### Pattern 2: AsyncMock Fixtures

**File**: `tests/infrastructure/ai/test_playwright_mcp.py`

```python
@pytest.fixture
def mock_process(self):
    """Create mock subprocess for MCP communication."""
    process = AsyncMock()
    process.stdin = AsyncMock()
    process.stdout = AsyncMock()
    process.stderr = AsyncMock()
    process.returncode = None
    process.terminate = Mock()
    process.kill = Mock()
    process.wait = AsyncMock()
    return process

@pytest.fixture
def initialized_client(self):
    """Create client that appears initialized."""
    client = PlaywrightMCPClient(headless=True)
    client._initialized = True
    client._process = Mock()
    client._process.stdin = AsyncMock()
    return client
```

### Pattern 3: Execution Context Fixture (For Node Tests)

Proposed pattern for Google/HTTP node tests:

```python
@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="Test Workflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={
            "api_key": "test-key",
            "user_id": "test-user-123"
        }
    )

@pytest.fixture
def mock_google_client(mocker):
    """Mock the GoogleAPIClient."""
    mock = AsyncMock(spec=GoogleAPIClient)
    mock.authenticate = AsyncMock(return_value=True)
    mock.list_files = AsyncMock(return_value=[
        {"id": "file1", "name": "test.pdf", "mimeType": "application/pdf"},
        {"id": "file2", "name": "data.xlsx", "mimeType": "application/vnd.ms-excel"},
    ])
    return mock
```

---

## Async Test Pattern

### Basic Async Test

**File**: `tests/infrastructure/ai/test_playwright_mcp.py`

```python
import pytest

class TestPlaywrightMCPClientHighLevelMethods:
    """Tests for high-level browser automation methods."""

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

**Key Points**:
- Use `@pytest.mark.asyncio` decorator for async tests
- Use `AsyncMock()` for async method mocks
- Use `patch.object()` with `new_callable=AsyncMock` for method patching
- Use `await` when calling async methods in tests

### Async Context Manager Test

```python
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

## Mocking Patterns

### Pattern 1: Mock External API Client

**For Google API**:
```python
from unittest.mock import AsyncMock, Mock
import pytest

@pytest.fixture
def mock_google_client():
    """Mock GoogleAPIClient."""
    client = AsyncMock()
    client.authenticate = AsyncMock(return_value=True)
    client.list_files = AsyncMock(return_value=[
        {"id": "file1", "name": "test.pdf"}
    ])
    client.download_file = AsyncMock(return_value=b"file content")
    client.upload_file = AsyncMock(return_value={"id": "new_file_id"})
    return client
```

**For HTTP Client**:
```python
@pytest.fixture
def mock_http_client():
    """Mock UnifiedHttpClient."""
    client = AsyncMock()
    client.get = AsyncMock(return_value={
        "status": 200,
        "body": {"data": "test"}
    })
    client.post = AsyncMock(return_value={
        "status": 201,
        "body": {"id": "123"}
    })
    return client
```

### Pattern 2: Patch Import Path

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_fetch_page_context_success(self):
    """Should return page context dict on success."""
    mock_nav_result = MCPToolResult(success=True, content=[])

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

        result = await fetch_page_context("https://example.com")
```

### Pattern 3: Mock with Side Effects

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_error_handling(self, client):
    """Should handle exceptions gracefully."""
    client._initialized = True
    client._process = Mock()
    client._process.stdin = AsyncMock()

    # Simulate network error
    with patch.object(
        client, "_send_request",
        side_effect=ConnectionError("Network failed")
    ):
        result = await client.call_tool("test_tool", {})

    assert result.success is False
    assert "failed" in result.error.lower()
```

---

## Test Organization

### Test Class Structure

**File**: `tests/infrastructure/ai/test_page_analyzer.py`

```python
class TestPageAnalyzerEmptySnapshot:
    """Tests for empty/missing snapshot handling."""

    def test_analyze_empty_snapshot_returns_empty_context(self, empty_snapshot: str):
        """Empty snapshot should return empty PageContext."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(empty_snapshot, url="", title="")

        assert context.is_empty() is True
        assert context.forms == []

    def test_analyze_none_snapshot_returns_empty_context(self):
        """None/empty string snapshot should not raise errors."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot("", url="", title="")

        assert context.is_empty() is True


class TestPageAnalyzerFormExtraction:
    """Tests for form and form field extraction."""

    def test_analyze_form_extraction(self, login_page_snapshot: str):
        """Should extract forms with their fields correctly."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(login_page_snapshot)

        assert len(context.forms) == 1


class TestPageAnalyzerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_snapshot_does_not_crash(self):
        """Should handle malformed snapshot gracefully."""
        malformed = "This is not a valid snapshot"
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(malformed)

        assert isinstance(context, PageContext)
```

**Best Practices**:
- One test class per feature/component
- Descriptive class names with "Test" prefix
- Docstring for each test method
- Arrange-Act-Assert pattern
- One assertion focus per test (or closely related assertions)

---

## Import Verification Tests

**File**: `tests/infrastructure/ai/test_imports.py`

```python
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

        # High-level methods
        assert hasattr(client, "navigate")
        assert hasattr(client, "get_snapshot")
```

---

## Specific Patterns for Integration Nodes

### For Google Nodes

**Proposed**: `tests/infrastructure/google/`

```python
import pytest
from unittest.mock import AsyncMock, patch
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.google.drive_files import DriveUploadFileNode
from casare_rpa.domain.value_objects.types import ExecutionMode

class TestDriveUploadFileNode:
    """Tests for DriveUploadFileNode."""

    @pytest.fixture
    def execution_context(self):
        """Create a test execution context."""
        return ExecutionContext(
            workflow_name="Test Drive Upload",
            mode=ExecutionMode.NORMAL,
            initial_variables={"credential_id": "test-cred"}
        )

    @pytest.fixture
    def mock_google_client(self):
        """Mock GoogleDriveClient."""
        mock = AsyncMock()
        mock.upload_file = AsyncMock(return_value={
            "id": "uploaded_file_id",
            "name": "test.pdf",
            "webViewLink": "https://drive.google.com/..."
        })
        return mock

    @pytest.mark.asyncio
    async def test_upload_file_success(self, execution_context, mock_google_client):
        """Should upload file and return file ID."""
        # Create node
        node = DriveUploadFileNode("node-1")

        # Set inputs
        node.set_input("file_path", "/path/to/test.pdf")
        node.set_input("folder_id", "folder_123")

        # Mock the client
        with patch("casare_rpa.nodes.google.drive_files.GoogleDriveClient") as MockClient:
            MockClient.return_value = mock_google_client

            # Execute
            result = await node.execute(execution_context)

        # Assert
        assert result["success"] is True
        assert result["file_id"] == "uploaded_file_id"
        assert result["name"] == "test.pdf"
        assert mock_google_client.upload_file.called

    @pytest.mark.asyncio
    async def test_upload_file_invalid_path(self, execution_context):
        """Should handle invalid file path."""
        node = DriveUploadFileNode("node-1")
        node.set_input("file_path", "/nonexistent/file.pdf")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
```

### For HTTP Nodes

**Proposed**: `tests/infrastructure/http/`

```python
import pytest
from unittest.mock import AsyncMock, patch
from casare_rpa.nodes.http.http_request_node import HttpRequestNode
from casare_rpa.infrastructure.execution import ExecutionContext

class TestHttpRequestNode:
    """Tests for HttpRequestNode."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(workflow_name="Test HTTP")

    @pytest.fixture
    def mock_http_client(self):
        """Mock UnifiedHttpClient."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value={
            "status": 200,
            "body": {"data": "test"}
        })
        return mock

    @pytest.mark.asyncio
    async def test_http_get_request(self, execution_context, mock_http_client):
        """Should execute HTTP GET request."""
        node = HttpRequestNode("node-1")
        node.set_input("method", "GET")
        node.set_input("url", "https://api.example.com/data")

        with patch("casare_rpa.nodes.http.http_request_node.UnifiedHttpClient") as MockClient:
            MockClient.return_value = mock_http_client

            result = await node.execute(execution_context)

        assert result["status"] == 200
        assert result["body"]["data"] == "test"

    @pytest.mark.asyncio
    async def test_http_post_with_json(self, execution_context, mock_http_client):
        """Should POST with JSON payload."""
        mock_http_client.post = AsyncMock(return_value={
            "status": 201,
            "body": {"id": "123"}
        })

        node = HttpRequestNode("node-1")
        node.set_input("method", "POST")
        node.set_input("url", "https://api.example.com/items")
        node.set_input("payload", {"name": "test"})

        with patch("casare_rpa.nodes.http.http_request_node.UnifiedHttpClient") as MockClient:
            MockClient.return_value = mock_http_client

            result = await node.execute(execution_context)

        assert result["status"] == 201
        mock_http_client.post.assert_called_once()
```

---

## Error Handling Tests

**Pattern**: Test error scenarios and recovery

```python
class TestGoogleNodeErrorHandling:
    """Tests for error handling in Google nodes."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, execution_context):
        """Should handle authentication errors gracefully."""
        from casare_rpa.infrastructure.resources.google_client import GoogleAuthError

        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(side_effect=GoogleAuthError("Invalid token"))

        node = DriveUploadFileNode("node-1")
        node.set_input("file_path", "/path/to/file.pdf")

        with patch("casare_rpa.nodes.google.google_base.GoogleAPIClient") as MockClient:
            MockClient.return_value = mock_client
            result = await node.execute(execution_context)

        assert result["success"] is False
        assert "auth" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_quota_exceeded(self, execution_context):
        """Should handle API quota exceeded."""
        from casare_rpa.infrastructure.resources.google_client import GoogleQuotaError

        mock_client = AsyncMock()
        mock_client.list_files = AsyncMock(
            side_effect=GoogleQuotaError("Quota exceeded", retry_after=60)
        )

        node = DriveListFilesNode("node-1")

        with patch("casare_rpa.nodes.google.drive_folders.GoogleDriveClient") as MockClient:
            MockClient.return_value = mock_client
            result = await node.execute(execution_context)

        assert result["success"] is False
        assert "quota" in result["error"].lower()
```

---

## Running Tests

### Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/infrastructure/ai/ -v

# Run specific test class
pytest tests/infrastructure/ai/test_playwright_mcp.py::TestPlaywrightMCPClientInit -v

# Run specific test method
pytest tests/infrastructure/ai/test_playwright_mcp.py::TestPlaywrightMCPClientInit::test_default_initialization -v

# Run with coverage
pytest tests/ --cov=casare_rpa --cov-report=html

# Run excluding slow tests
pytest tests/ -m "not slow" -v

# Run only integration tests
pytest tests/ -m "integration" -v

# Run with detailed output
pytest tests/ -vv --tb=long

# Run with stop-on-first-failure
pytest tests/ -x -v
```

### Coverage Requirements

Current project requirement: **75%+ coverage**

```bash
# Check coverage by file
pytest tests/ --cov=casare_rpa --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=casare_rpa --cov-report=html
# Opens: htmlcov/index.html
```

---

## Key Testing Files Reference

| File | Purpose | Lines | Key Patterns |
|------|---------|-------|--------------|
| `tests/infrastructure/ai/conftest.py` | Fixtures & mock data | 111 | Snapshot fixtures, dicts for mocking |
| `tests/infrastructure/ai/test_page_analyzer.py` | Page analysis tests | 531 | Multiple test classes per feature |
| `tests/infrastructure/ai/test_playwright_mcp.py` | MCP client tests | 492 | AsyncMock, patch, context managers |
| `tests/infrastructure/ai/test_imports.py` | Import verification | 345 | Module/class/method existence tests |
| `tests/infrastructure/ai/test_url_detection.py` | URL pattern tests | Various | Pattern matching, edge cases |

---

## Summary: Testing Checklist

When implementing tests for a new integration node:

- [ ] Create `tests/infrastructure/{module}/conftest.py` with fixtures
- [ ] Create mock data constants for API responses
- [ ] Create `TestImports` class for module verification
- [ ] Create `Test{NodeName}` class for node functionality
- [ ] Use `ExecutionContext` for node execution setup
- [ ] Mock external API clients with `AsyncMock`
- [ ] Test success path with mocked responses
- [ ] Test error paths (auth errors, network errors, validation errors)
- [ ] Test edge cases (empty inputs, malformed data, etc.)
- [ ] Use `@pytest.mark.asyncio` for async tests
- [ ] Target 75%+ code coverage
- [ ] Run tests: `pytest tests/ -v --cov=casare_rpa`
