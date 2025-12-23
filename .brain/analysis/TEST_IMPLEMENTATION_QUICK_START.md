<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# Test Implementation Quick Start

Fast reference for implementing tests for integration nodes in CasareRPA.

## 5-Minute Overview

### What You'll Create
1. **conftest.py** - Reusable fixtures and mock data
2. **test_imports.py** - Verify module/class imports
3. **test_{node_name}.py** - Node functionality tests

### File Locations
```
tests/infrastructure/{module_name}/
├── conftest.py                    # Fixtures
├── test_imports.py                # Import tests
├── test_{node_name}_node.py      # Node execution tests
└── test_{other_node}.py          # Additional nodes
```

### Pytest Configuration
Already in `pyproject.toml`:
- asyncio_mode = "auto" (async tests work automatically)
- cov-fail-under=75 (coverage requirement)
- testpaths = ["tests"]

---

## Copy-Paste Template: conftest.py

```python
"""
Pytest fixtures for {Module Name} integration tests.
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock

# ============================================================================
# Mock Response Data
# ============================================================================

MOCK_RESPONSE_SUCCESS = {
    "status": 200,
    "id": "test_id_123",
    "name": "Test Item",
}

MOCK_ERROR_RESPONSE = {
    "status": 400,
    "error": "Invalid request",
}

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def execution_context():
    """Create test execution context."""
    from casare_rpa.infrastructure.execution import ExecutionContext
    from casare_rpa.domain.value_objects.types import ExecutionMode

    return ExecutionContext(
        workflow_name="Test {Module}",
        mode=ExecutionMode.NORMAL,
        initial_variables={"test_var": "value"}
    )


@pytest.fixture
def mock_client():
    """Mock external API client."""
    mock = AsyncMock()
    mock.authenticate = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=MOCK_RESPONSE_SUCCESS)
    mock.post = AsyncMock(return_value=MOCK_RESPONSE_SUCCESS)
    return mock
```

---

## Copy-Paste Template: test_imports.py

```python
"""
Import verification tests for {Module Name} integration.
"""

import pytest


class TestModuleImports:
    """Tests for module imports."""

    def test_import_main_node(self):
        """Should import main node class."""
        from casare_rpa.nodes.{module}.{node_file} import {NodeClass}
        assert {NodeClass} is not None

    def test_import_client(self):
        """Should import API client."""
        from casare_rpa.infrastructure.resources.{client_module} import {ClientClass}
        assert {ClientClass} is not None

    def test_import_errors(self):
        """Should import error classes."""
        from casare_rpa.infrastructure.resources.{client_module} import (
            {ErrorClass1},
            {ErrorClass2},
        )
        assert {ErrorClass1} is not None
        assert {ErrorClass2} is not None

    def test_node_has_execute_method(self):
        """Should have execute method."""
        from casare_rpa.nodes.{module}.{node_file} import {NodeClass}
        import inspect

        node = {NodeClass}("test_node")
        assert hasattr(node, "execute")
        assert inspect.iscoroutinefunction(node.execute)
```

---

## Copy-Paste Template: test_node.py

```python
"""
Tests for {NodeClass}.
"""

import pytest
from unittest.mock import patch, AsyncMock

from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.{module}.{file} import {NodeClass}


class TestNodeInit:
    """Tests for node initialization."""

    def test_node_initialization(self):
        """Should initialize node correctly."""
        node = {NodeClass}("node_1")

        assert node.node_id == "node_1"
        assert node.NODE_TYPE == "{node_type}"

    def test_node_has_input_ports(self):
        """Should have required input ports."""
        node = {NodeClass}("node_1")

        assert node.get_input_port("input_name") is not None


class TestNodeExecution:
    """Tests for node execution."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        execution_context: ExecutionContext,
        mock_client: AsyncMock,
    ):
        """Should execute successfully."""
        # Setup
        node = {NodeClass}("node_1")
        node.set_input("param", "value")

        # Mock client
        with patch(
            "casare_rpa.nodes.{module}.{file}.{ClientClass}"
        ) as MockClient:
            MockClient.return_value = mock_client

            # Execute
            result = await node.execute(execution_context)

        # Assert
        assert result["success"] is True
        assert "output" in result

    @pytest.mark.asyncio
    async def test_execute_error(
        self,
        execution_context: ExecutionContext,
        mock_client: AsyncMock,
    ):
        """Should handle errors."""
        # Setup
        node = {NodeClass}("node_1")
        node.set_input("param", "invalid")

        # Mock error
        with patch(
            "casare_rpa.nodes.{module}.{file}.{ClientClass}"
        ) as MockClient:
            MockClient.return_value = mock_client
            mock_client.some_method.side_effect = Exception("API Error")

            # Execute
            result = await node.execute(execution_context)

        # Assert
        assert result["success"] is False
        assert "error" in result
```

---

## Step-by-Step: Creating Your First Test

### Step 1: Create Directory
```bash
mkdir -p tests/infrastructure/mymodule
touch tests/infrastructure/mymodule/__init__.py
```

### Step 2: Create conftest.py
```bash
touch tests/infrastructure/mymodule/conftest.py
```
Copy from template above, replace placeholders.

### Step 3: Create test_imports.py
```bash
touch tests/infrastructure/mymodule/test_imports.py
```
Copy from template above, replace placeholders.

### Step 4: Create test_{node}.py
```bash
touch tests/infrastructure/mymodule/test_{node_name}_node.py
```
Copy from template above, replace placeholders.

### Step 5: Run Tests
```bash
pytest tests/infrastructure/mymodule/ -v
```

---

## Common Patterns Quick Reference

### Pattern 1: Basic Async Test with Mock
```python
@pytest.mark.asyncio
async def test_execute(self, execution_context, mock_client):
    node = MyNode("node_1")

    with patch("path.to.Client") as MockClient:
        MockClient.return_value = mock_client
        result = await node.execute(execution_context)

    assert result["success"] is True
```

### Pattern 2: Test Error Handling
```python
@pytest.mark.asyncio
async def test_auth_error(self, execution_context, mock_client):
    from module import AuthError

    with patch("path.to.Client") as MockClient:
        MockClient.return_value = mock_client
        mock_client.method.side_effect = AuthError("Invalid token")

        result = await node.execute(execution_context)

    assert result["success"] is False
    assert "auth" in result["error"].lower()
```

### Pattern 3: Test with Input Variables
```python
@pytest.mark.asyncio
async def test_with_variables(self, execution_context, mock_client):
    # Pre-set variables in context
    execution_context.set_variable("api_key", "secret123")

    node = MyNode("node_1")
    node.set_input("credential", "{{api_key}}")

    with patch("path.to.Client") as MockClient:
        result = await node.execute(execution_context)

    assert result["success"] is True
```

### Pattern 4: Test Multiple Scenarios in Class
```python
class TestMyNode:
    """Group related tests."""

    @pytest.mark.asyncio
    async def test_success_path(self, execution_context, mock_client):
        """Normal execution."""
        ...

    @pytest.mark.asyncio
    async def test_error_path(self, execution_context, mock_client):
        """Error handling."""
        ...

    @pytest.mark.asyncio
    async def test_edge_case(self, execution_context, mock_client):
        """Edge case."""
        ...
```

---

## ExecutionContext Quick Ref

```python
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import ExecutionMode

# Create
context = ExecutionContext(
    workflow_name="Test",
    mode=ExecutionMode.NORMAL,
    initial_variables={"key": "value"}
)

# Set/Get Variables
context.set_variable("name", "value")
value = context.get_variable("name")
has = context.has_variable("name")

# Resources Storage
context.resources["client"] = mock_client
client = context.resources["client"]

# Execution Flow
context.set_current_node(NodeId("n1"))
context.add_error(NodeId("n1"), "Error message")
context.stop_execution()
```

---

## AsyncMock Quick Ref

```python
from unittest.mock import AsyncMock, Mock

# Create async mock
mock = AsyncMock()

# Setup return values
mock.method = AsyncMock(return_value="result")

# Setup side effects (errors)
mock.method.side_effect = Exception("Error")

# Check calls
mock.method.assert_called_once()
mock.method.assert_called_with("arg")
assert mock.method.called

# Get call args
call_args = mock.method.call_args
```

---

## Mocking Patterns Quick Ref

### Patch Import Path
```python
with patch("module.path.ClassName") as MockClass:
    MockClass.return_value = mock_instance
    # Code that uses ClassName
```

### Patch Object Method
```python
with patch.object(obj, "method", new_callable=AsyncMock) as mock_method:
    mock_method.return_value = "result"
    # Code that calls obj.method()
```

### Patch with Side Effect
```python
with patch("module.path.function") as mock_func:
    mock_func.side_effect = ValueError("Error")
    # Code that calls function()
```

---

## Running Tests

### Basic Commands
```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/infrastructure/mymodule/ -v

# Specific file
pytest tests/infrastructure/mymodule/test_node.py -v

# Specific test
pytest tests/infrastructure/mymodule/test_node.py::TestNode::test_method -v

# With coverage
pytest tests/ --cov=casare_rpa --cov-report=html

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -v -s
```

### Coverage Check
```bash
# Generate report
pytest tests/ --cov=casare_rpa --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=casare_rpa --cov-report=html
# Opens: htmlcov/index.html
```

---

## Checklist: Before Submitting Tests

- [ ] Created conftest.py with fixtures
- [ ] Created test_imports.py (verify module loads)
- [ ] Created test_{node}.py with execution tests
- [ ] All async methods use @pytest.mark.asyncio
- [ ] All external clients are AsyncMock
- [ ] Tests for success path
- [ ] Tests for error paths (auth, network, validation)
- [ ] Tests for edge cases (empty input, None values, etc.)
- [ ] ExecutionContext properly initialized with variables
- [ ] Coverage report shows 75%+ coverage
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No warnings or errors

---

## Troubleshooting

### Error: "object is not awaitable"
**Solution**: Use @pytest.mark.asyncio on the test method

```python
# WRONG
def test_async_code():
    result = await node.execute(context)

# CORRECT
@pytest.mark.asyncio
async def test_async_code():
    result = await node.execute(context)
```

### Error: "AsyncMock object has no attribute..."
**Solution**: Create AsyncMock with spec or set attributes explicitly

```python
# Works
mock = AsyncMock()
mock.method = AsyncMock(return_value="result")

# Also works
mock = AsyncMock(spec=RealClass)
```

### Error: "Module not found"
**Solution**: Check patch path matches import location

```python
# If node imports: from module.client import Client
# Then patch: "module.client.Client"
with patch("module.client.Client") as Mock:
    ...
```

### Error: "Test passed but coverage < 75%"
**Solution**: Add tests for uncovered lines

```bash
# Show uncovered lines
pytest tests/ --cov=casare_rpa --cov-report=term-missing

# HTML report with line numbers
pytest tests/ --cov=casare_rpa --cov-report=html
```

---

## Next Steps

1. **Review existing tests**: Check `tests/infrastructure/ai/` for reference
2. **Create fixtures**: Copy conftest.py template, customize
3. **Write import tests**: Verify all classes import correctly
4. **Write execution tests**: Test success and error paths
5. **Run tests**: `pytest tests/ -v --cov`
6. **Check coverage**: `pytest tests/ --cov --cov-report=html`
7. **Refine**: Add tests for edge cases until 75%+ coverage
8. **Submit**: All tests passing, coverage good

---

## Resources

- **TESTING_PATTERNS.md** - Comprehensive guide (this document's expanded version)
- **GOOGLE_NODE_TEST_EXAMPLE.md** - Full working examples for Google nodes
- **pyproject.toml** - Pytest configuration
- **tests/infrastructure/ai/** - Real examples to learn from
