# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Testing Quick Reference - CasareRPA

## Test File Organization

```
tests/
├── domain/                    # Pure logic tests (NO mocks)
│   ├── test_property_schema.py
│   └── test_dynamic_port_config.py
├── infrastructure/ai/         # External API tests (mock snapshots)
│   ├── conftest.py
│   ├── test_page_analyzer.py
│   ├── test_playwright_mcp.py
│   └── test_url_detection.py
├── nodes/file/               # File operation tests (real tmp files)
│   ├── conftest.py
│   ├── test_file_system_super_node.py  (1092 lines!)
│   └── test_structured_data_super_node.py
├── nodes/google/             # Google Drive tests (mock client)
│   ├── conftest.py
│   ├── test_drive_download_nodes.py
│   └── test_drive_config_sync.py
├── examples/                 # Best practice examples
│   ├── test_event_handling_example.py
│   └── test_node_creation_example.py
└── presentation/             # UI tests (minimal)
    └── test_super_node_mixin.py
```

---

## Available Fixtures by Category

### ExecutionContext Fixtures
```python
execution_context: ExecutionContext     # Real - most tests
mock_context: MagicMock                 # Mock - specialized
```

**Location:** `tests/nodes/file/conftest.py`, `tests/nodes/google/conftest.py`

### File System Fixtures (tmp_path-based)
```python
temp_test_file          # Text file: "Hello, World!" (13 bytes)
temp_csv_file           # CSV with 3 rows
temp_json_file          # JSON nested dict
temp_image_file         # PNG image (10x10 red)
temp_directory          # Tree: 3 files + subdir
temp_zip_file           # ZIP of temp_directory
```

**Location:** `tests/nodes/file/conftest.py`

### Page Analysis Fixtures (string snapshots)
```python
login_page_snapshot          # Form: username, password
table_page_snapshot          # Table with headers
nav_page_snapshot            # Navigation menu
dropdown_page_snapshot       # Form controls
empty_snapshot               # Edge case: empty string
complex_page_snapshot        # Multi-form registration
sample_page_dict             # Dict representation
```

**Location:** `tests/infrastructure/ai/conftest.py`

### Google Drive Fixtures (mock objects)
```python
mock_drive_client            # AsyncMock GoogleDriveClient
sample_drive_files           # 3 MockDriveFile objects
sample_google_workspace_files  # Google Docs/Sheets (skip test)
tmp_download_dir             # Temp download directory
```

**Location:** `tests/nodes/google/conftest.py`

---

## Running Tests

### Quick Commands
```bash
pytest tests/                              # All tests
pytest tests/domain/                       # Domain layer only
pytest tests/nodes/file/                   # File nodes only
pytest tests/ -v                           # Verbose
pytest tests/ --cov=casare_rpa             # With coverage
pytest tests/ -k "read_file"               # Match pattern
pytest tests/ -m "not slow"                # Skip slow tests
```

### With Coverage Report
```bash
pytest tests/ --cov=casare_rpa --cov-report=html
# Opens htmlcov/index.html in browser
```

---

## Test Structure Template

```python
"""
Tests for [module].

Run: pytest tests/[path]/test_xxx.py -v
"""

import pytest
from casare_rpa.infrastructure.execution import ExecutionContext

class TestFeature:
    """Tests for [feature name]."""

    @pytest.mark.asyncio
    async def test_feature_success(self, execution_context, temp_test_file):
        """SUCCESS: Normal operation works."""
        # ARRANGE
        node = MyNode("id", config={"key": "value"})

        # ACT
        result = await node.execute(execution_context)

        # ASSERT
        assert result["success"] is True
        assert node.get_output_value("output") == expected
```

**Pattern:**
- Class-based: `class TestXxx:`
- Method prefix: `def test_xxx_yyy():`
- Async marker: `@pytest.mark.asyncio` for async methods
- AAA: Arrange, Act, Assert
- Comment paths: SUCCESS, SAD PATH, EDGE CASE, SECURITY

---

## Mock Quick Guide

### When to Use Real vs Mock

| Scenario | Use | Pattern |
|----------|-----|---------|
| ExecutionContext | **Real** | `ExecutionContext(workflow_name="X", ...)` |
| File I/O | **Real tmp_path** | `tmp_path / "file.txt"` |
| External API | **Mock Client** | `MagicMock()` |
| Async API | **AsyncMock** | `AsyncMock(return_value=X)` |
| Domain Logic | **No mock** | Direct instantiation |

### ExecutionContext - Real
```python
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import ExecutionMode

context = ExecutionContext(
    workflow_name="TestWorkflow",
    mode=ExecutionMode.NORMAL,
    initial_variables={},
)
```

### ExecutionContext - Mock
```python
from unittest.mock import MagicMock

context = MagicMock(spec=ExecutionContext)
context.resolve_value = MagicMock(side_effect=lambda x: x)
context.variables = {}
context.resources = {}
```

### Async Method Mock
```python
from unittest.mock import AsyncMock

client = MagicMock()
client.download_file = AsyncMock(return_value=Path("/dest.pdf"))

# Or with side effect
async def mock_download(file_id: str, dest: str) -> Path:
    return Path(dest)

client.download_file = AsyncMock(side_effect=mock_download)
```

### File I/O (Don't Mock - Use tmp_path)
```python
# GOOD
def test_read_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    result = node.read(test_file)
    assert result == "content"

# AVOID
@patch('pathlib.Path.write_text')
def test_read_file(mock_write):
    # Brittle - breaks with implementation changes
    pass
```

---

## Pytest Configuration

From `pyproject.toml`:
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

**Key Points:**
- `asyncio_mode = "auto"` - Auto detects async tests
- `cov-fail-under=75` - CI fails if coverage < 75%
- `--tb=short` - Concise tracebacks

---

## Common Patterns

### Node Execution Test
```python
@pytest.mark.asyncio
async def test_node_execute(execution_context, temp_test_file):
    """Test node execution."""
    node = FileSystemSuperNode(
        "test_id",
        config={"action": "Read File", "file_path": str(temp_test_file)}
    )

    result = await node.execute(execution_context)

    assert result["success"] is True
    assert "content" in result["data"]
```

### Event System Test
```python
@pytest.fixture
def event_bus():
    reset_event_bus()
    return get_event_bus()

def test_event_publish(event_bus):
    """Test event publishing."""
    collected = []

    event_bus.subscribe(MyEvent, lambda e: collected.append(e))
    event_bus.publish(MyEvent(field="value"))

    assert len(collected) == 1
    assert collected[0].field == "value"
```

### Pure Domain Test (No Mocks)
```python
def test_property_def_creation():
    """Test property definition."""
    prop = PropertyDef(
        name="test_prop",
        type=PropertyType.STRING,
        default="default_value"
    )

    assert prop.name == "test_prop"
    assert prop.label == "Test Prop"  # Auto-generated
```

---

## Test File Sizes & Complexity

| File | Lines | Complexity | Category |
|------|-------|-----------|----------|
| test_file_system_super_node.py | 1092 | Very High | 12 actions tested |
| test_page_analyzer.py | 531 | High | Comprehensive snapshot parsing |
| test_event_handling_example.py | 317 | Medium | 5 event system patterns |
| test_property_schema.py | ~200 | Low | Pure domain logic |
| test_drive_download_nodes.py | ~150 | Medium | 3 download node variants |

---

## Gaps to Fill

### 1. No Workflow Loader Tests
**Missing:** `tests/utils/test_workflow_loader.py`

**Impact:** Deserialization untested, no regression detection

### 2. No Serialization Tests
**Missing:** `tests/infrastructure/test_serializer.py`

**Impact:** Schema evolution could break silently

### 3. No Performance Benchmarks
**Available:** pytest-benchmark dependency installed

**Opportunity:** Load time benchmarks for large workflows

### 4. Minimal UI Tests
**Available:** pytest-qt dependency installed

**Opportunity:** Canvas component testing

---

## Dev Dependencies

```toml
pytest>=7.4.3              # Test framework
pytest-asyncio>=0.21.1     # Async/await support
pytest-qt>=4.3.1           # PySide6 widget testing
pytest-cov>=4.0.0          # Coverage reports
pytest-benchmark>=4.0.0    # Performance benchmarking (unused)
```

---

## Fixture Dependency Chain

```
tmp_path (pytest built-in)
    ├── temp_test_file
    ├── temp_csv_file
    ├── temp_json_file
    ├── temp_image_file
    ├── temp_directory
    └── temp_zip_file (depends on temp_directory)

execution_context
    └── Used by all node tests

mock_drive_client
    └── Used by Google Drive tests

Event Bus
    └── reset_event_bus() before each test
```

---

## Best Practices Checklist

Before committing tests:
- [ ] Use `@pytest.mark.asyncio` for async methods
- [ ] Use real files (tmp_path), not mocked file I/O
- [ ] Use `spec=RealClass` for MagicMock to catch typos
- [ ] Use fixture parameters, not setUp/tearDown
- [ ] Use AAA pattern (Arrange, Act, Assert)
- [ ] Add docstring with SUCCESS/SAD PATH/EDGE CASE
- [ ] Verify mocks with `assert_called_once_with()`
- [ ] Reset event bus in fixture, not in test
- [ ] Keep test names descriptive: `test_xxx_yyy_zzz()`
- [ ] Target 75%+ code coverage

---

## Quick Help

**How to add a new test fixture?**
1. Locate appropriate conftest.py (or create one in same directory)
2. Add `@pytest.fixture` function
3. Return test data
4. Reference fixture as parameter in test methods

**How to test async code?**
1. Add `@pytest.mark.asyncio` decorator
2. Make test method `async def`
3. Use `await` for async calls
4. pytest-asyncio auto-detects with `asyncio_mode = "auto"`

**How to mock an async method?**
```python
from unittest.mock import AsyncMock

mock_obj.async_method = AsyncMock(return_value=X)
# or
AsyncMock(side_effect=async_function)
```

**How to test with temporary files?**
```python
def test_something(tmp_path):
    test_file = tmp_path / "name.txt"
    test_file.write_text("content")
    # test code uses test_file
```

**How to verify a mock was called?**
```python
mock_obj.method.assert_called_once()
mock_obj.method.assert_called_once_with(arg1, arg2)
mock_obj.method.assert_called_with(arg1, arg2)
mock_obj.method.assert_not_called()
```

---

**Last Updated:** 2025-12-14
**Status:** Complete Analysis
**Test Coverage:** 22 files, 50+ async tests, 75%+ code coverage
