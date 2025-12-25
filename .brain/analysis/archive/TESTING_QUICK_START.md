# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# CasareRPA Testing Quick Start Card

**Use this when:** Writing tests, debugging failures, validating changes
**Full docs:** See `QUALITY_AND_TEST_INFRASTRUCTURE.md`

---

## Test Execution

```bash
# Quick validation (run on branch)
pytest tests/ -v --tb=short

# Full validation (before commit)
pytest tests/ -v --cov=casare_rpa --cov-fail-under=75

# Specific test type
pytest tests/domain/ -v          # Domain layer (no mocks)
pytest tests/nodes/ -v           # Node implementations
pytest tests/performance/ -v     # Performance benchmarks

# Debug failing test
pytest tests/path/test_file.py::TestClass::test_method -vv -s
```

---

## Test Structure (Copy-Paste Template)

```python
"""
Tests for [Feature Name].

This test suite covers [what is tested]:
- Feature A: [description]
- Feature B: [description]

Test Philosophy:
- Happy path: Normal operation
- Sad path: Expected failures
- Edge cases: Boundary conditions

Run: pytest tests/category/test_file.py -v
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

# Import your code
from casare_rpa.domain.entities import YourClass


class TestYourFeature:
    """Test group for related functionality."""

    def test_happy_path(self):
        """SUCCESS: Normal operation works."""
        obj = YourClass(arg1="value")
        result = obj.do_something()
        assert result is True

    def test_sad_path(self):
        """FAILURE: Expected error handling."""
        obj = YourClass(arg1="")  # Invalid
        with pytest.raises(ValueError):
            obj.do_something()

    def test_edge_case(self):
        """EDGE: Boundary condition."""
        obj = YourClass(arg1=None)
        result = obj.do_something()
        assert result is None  # Graceful handling


# Async tests
class TestAsyncFeature:
    """Test async operations."""

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """SUCCESS: Async method completes."""
        mock = AsyncMock()
        mock.fetch.return_value = {"data": "result"}

        result = await mock.fetch()

        assert result["data"] == "result"
        mock.fetch.assert_awaited_once()
```

---

## Mocking Quick Reference

**Domain Layer (NO mocks):**
```python
from casare_rpa.domain.schemas.property_schema import PropertyDef, PropertyType

# Real object - no mocking
prop = PropertyDef("name", PropertyType.STRING, default="test")
assert prop.name == "name"
```

**Infrastructure Layer (Mock external APIs):**
```python
from unittest.mock import AsyncMock, MagicMock

# Mock HTTP client
mock_client = AsyncMock()
mock_response = AsyncMock()
mock_response.json.return_value = {"result": "success"}
mock_client.get.return_value = mock_response

# Mock Playwright
mock_page = MagicMock()
mock_page.click = MagicMock()

# Mock file I/O
with patch("aiofiles.open") as mock_open:
    mock_file = AsyncMock()
    mock_open.return_value.__aenter__.return_value = mock_file
    # Test code here
```

---

## Using Fixtures

**From conftest.py:**
```python
# Import fixtures automatically (no import needed)
def test_with_fixture(temp_test_file):
    """temp_test_file provided by conftest.py fixture."""
    assert temp_test_file.exists()
    content = temp_test_file.read_text()
    assert "Hello, World!" in content
```

**Common Fixtures:**
- `execution_context` - ExecutionContext instance
- `mock_context` - Mocked execution context
- `temp_test_file`, `temp_csv_file`, `temp_json_file` - Temporary files
- `temp_directory` - Temp directory with files
- `small_workflow_data`, `medium_workflow_data`, `large_workflow_data` - Workflow fixtures
- `temp_workflow_file` - Serialized workflow file

---

## Performance Tests

```python
import time

def test_operation_is_fast():
    """Verify operation completes within time budget."""
    start = time.perf_counter()
    result = expensive_operation()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.01  # 10ms threshold
    assert result is not None
```

---

## Coverage Requirements

**Minimum:** 75% (enforced)

```bash
# Check coverage
pytest tests/ --cov=casare_rpa --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=casare_rpa --cov-report=html
# Open: htmlcov/index.html
```

---

## Pre-commit Hooks

```bash
# Install once
pre-commit install

# Run manually (before commit)
pre-commit run --all-files

# Automatic on: git commit
```

**Hooks included:**
- Trailing whitespace removal
- YAML/JSON validation
- Ruff linting + auto-fix
- Code formatting

---

## Common Test Patterns

### Pattern 1: Domain Entity Test (Real Objects)
```python
from casare_rpa.domain.schemas.property_schema import PropertyDef, PropertyType

def test_property_def():
    """Test domain value object - use real instance."""
    prop = PropertyDef(
        name="url",
        type=PropertyType.STRING,
        required=True,
        label="Website URL"
    )
    assert prop.name == "url"
    assert prop.required is True
```

### Pattern 2: Node Test (With Mocks)
```python
from casare_rpa.nodes.file.super_node import FileSystemSuperNode
from pathlib import Path
from unittest.mock import patch

def test_read_file_node(temp_test_file):
    """Test node with mocked context."""
    node = FileSystemSuperNode()

    result = node.execute(
        action="read",
        file_path=str(temp_test_file)
    )

    assert result["success"] is True
    assert result["content"] == "Hello, World!"
```

### Pattern 3: Async Operation Test
```python
@pytest.mark.asyncio
async def test_async_workflow_loading():
    """Test async operation with mocked client."""
    from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

    loader = IncrementalLoader()
    skeleton = loader.load_skeleton(minimal_workflow_data)

    assert skeleton.name == "TestWorkflow"
    assert skeleton.node_count == 1
```

### Pattern 4: Parametrized Tests
```python
@pytest.mark.parametrize("input_val,expected", [
    ("text", "TEXT"),
    ("another", "ANOTHER"),
    ("", ""),
])
def test_transform_with_params(input_val, expected):
    """Test multiple inputs efficiently."""
    result = transform_to_uppercase(input_val)
    assert result == expected
```

---

## Test Categories in Codebase

| Category | Location | What to Test |
|----------|----------|--------------|
| **Domain** | `tests/domain/` | Entities, value objects, services (NO mocks) |
| **Nodes** | `tests/nodes/` | Node implementations (mock external APIs) |
| **Performance** | `tests/performance/` | Workflow loading, optimization timing |
| **Examples** | `tests/examples/` | Reference implementations (copy these patterns) |
| **Infrastructure** | `tests/infrastructure/` | AI, HTTP, cloud adapters (mock ALL externals) |
| **Presentation** | `tests/presentation/` | Visual nodes (mock Qt components) |

---

## Debugging Failed Tests

```bash
# Step 1: Run with full output
pytest tests/path/test_file.py::test_name -vv -s

# Step 2: Use pdb debugger
pytest tests/path/test_file.py::test_name --pdb
# Or add to code:
# import pdb; pdb.set_trace()

# Step 3: Check fixtures
# Look at: tests/[category]/conftest.py

# Step 4: Check mocking
# Verify mock.assert_called_once(), mock.assert_awaited()

# Step 5: Run related tests
pytest tests/path/test_file.py -v -k "test_name"
```

---

## Decision Tree: Should I Mock This?

```
Is this external to the domain layer?
├─ YES → Mock it (Playwright, HTTP, files, win32, etc.)
└─ NO
    └─ Is it a domain entity/value object?
        ├─ YES → Use real instance
        └─ NO
            └─ Is it application orchestration?
                ├─ YES → Mock infrastructure, not domain
                └─ NO → Use judgment + check conftest patterns
```

---

## Quick File Locations

```
Test templates:           tests/examples/test_node_creation_example.py
Mocking patterns:         .brain/docs/tdd-guide.md
Node checklist:           .brain/docs/node-checklist.md
Common test fixtures:     tests/[category]/conftest.py
Project test config:      pyproject.toml [tool.pytest.ini_options]
Pre-commit hooks:         .pre-commit-config.yaml
Quality tools:            QUALITY_AND_TEST_INFRASTRUCTURE.md (this dir)
```

---

## One-Liners for Common Tasks

```bash
# Run tests matching pattern
pytest tests/ -k "workflow" -v

# Run non-slow tests
pytest tests/ -m "not slow" -v

# List all test markers
pytest --markers

# Run with minimal output
pytest tests/ -q

# Generate JUnit XML (for CI)
pytest tests/ --junit-xml=test-results.xml

# Run with timeout per test
pytest tests/ --timeout=10

# Show slowest 10 tests
pytest tests/ --durations=10

# Run test and keep output on screen
pytest tests/path/test.py::test_name -s
```

---

**Last Updated:** 2025-12-14
**Related:** `QUALITY_AND_TEST_INFRASTRUCTURE.md` (full reference)
