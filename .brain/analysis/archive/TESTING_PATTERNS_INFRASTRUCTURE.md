# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Testing Patterns for Infrastructure Layer - CasareRPA

**Date:** 2025-12-14
**Status:** Comprehensive Analysis Complete
**Test Coverage:** 22 test files across 6 major areas

---

## Executive Summary

CasareRPA has a well-structured testing infrastructure across domain, infrastructure, nodes, and examples layers. Key patterns include:
- **Fixture-based testing** with PyTest (conftest.py files across 3 areas)
- **Async testing** with pytest-asyncio marked with `@pytest.mark.asyncio`
- **Mocking infrastructure** using `MagicMock` and `AsyncMock` for external dependencies
- **No workflow loader tests** found (gap identified)
- **Example-driven testing** for patterns and best practices
- **Domain-focused tests** with NO mocking (pure logic)

---

## Test File Locations & Counts

```
tests/
├── domain/                          # 2 files - Pure domain logic
│   ├── test_property_schema.py
│   └── test_dynamic_port_config.py
├── examples/                        # 2 files - Pattern examples
│   ├── test_event_handling_example.py
│   └── test_node_creation_example.py
├── infrastructure/                  # 5 files - External integrations
│   └── ai/
│       ├── conftest.py              # Fixtures for AI tests
│       ├── test_page_analyzer.py
│       ├── test_playwright_mcp.py
│       ├── test_url_detection.py
│       └── test_imports.py
├── nodes/                           # 10+ files - Node implementations
│   ├── file/
│   │   ├── conftest.py              # File I/O fixtures
│   │   ├── test_file_system_super_node.py (1092 lines!)
│   │   └── test_structured_data_super_node.py
│   └── google/
│       ├── conftest.py              # Google Drive fixtures
│       ├── test_drive_download_nodes.py
│       └── test_drive_config_sync.py
└── presentation/                    # 1 file - UI/visual tests
    └── test_super_node_mixin.py

Total: 22 test files
```

---

## 1. Fixture Patterns (Conftest Files)

### Location & Purpose

Three `conftest.py` files provide shared fixtures:

#### 1.1 Infrastructure AI Fixtures
**File:** `tests/infrastructure/ai/conftest.py` (111 lines)

**Purpose:** Mock page snapshots from accessibility trees

**Fixtures Provided:**
```python
@pytest.fixture
def login_page_snapshot() -> str
    # Mock login form with username, password, buttons

@pytest.fixture
def table_page_snapshot() -> str
    # Mock data table with headers and buttons

@pytest.fixture
def nav_page_snapshot() -> str
    # Mock navigation structure

@pytest.fixture
def dropdown_page_snapshot() -> str
    # Mock form with dropdowns, checkboxes, buttons

@pytest.fixture
def empty_snapshot() -> str
    # Empty snapshot for edge case testing

@pytest.fixture
def complex_page_snapshot() -> str
    # Multi-form registration page with nested elements

@pytest.fixture
def sample_page_dict() -> Dict[str, Any]
    # Page context as dict for MCP mocking
```

**Pattern:** String-based mock data (NOT complex objects)

---

#### 1.2 File Operations Fixtures
**File:** `tests/nodes/file/conftest.py` (124 lines)

**Purpose:** Temporary file system fixtures for file node testing

**Fixtures Provided:**
```python
@pytest.fixture
def execution_context() -> ExecutionContext
    # Real ExecutionContext with test workflow name and empty variables

@pytest.fixture
def mock_context() -> MagicMock
    # MagicMock spec=ExecutionContext with resolve_value stubbed

@pytest.fixture
def temp_test_file(tmp_path: Path) -> Path
    # Creates temp file: test_file.txt with "Hello, World!"

@pytest.fixture
def temp_csv_file(tmp_path: Path) -> Path
    # Creates CSV: test_data.csv with 3 rows of sample data

@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path
    # Creates JSON: test_data.json with nested structure

@pytest.fixture
def temp_image_file(tmp_path: Path) -> Path
    # Creates PNG image: test_image.png (10x10 red)

@pytest.fixture
def temp_directory(tmp_path: Path) -> Path
    # Creates directory tree:
    #   - file1.txt, file2.txt, data.json
    #   - subdir/nested.txt

@pytest.fixture
def temp_zip_file(tmp_path: Path, temp_directory: Path) -> Path
    # Creates ZIP archive from temp_directory
```

**Pattern:** Real files + directories using pytest's `tmp_path`

---

#### 1.3 Google Drive Fixtures
**File:** `tests/nodes/google/conftest.py` (122 lines)

**Purpose:** Mock Google Drive API objects and clients

**Key Classes:**
```python
@dataclass
class MockDriveFile:
    """Mock object mimicking GoogleDriveClient response."""
    id: str
    name: str
    mime_type: str
    size: int | None = None
    created_time: str | None = None
    modified_time: str | None = None
    parents: list[str]
    web_view_link: str | None = None
    web_content_link: str | None = None
    shared: bool = False
    # ... more fields
```

**Fixtures:**
```python
@pytest.fixture
def execution_context() -> ExecutionContext
    # Real ExecutionContext (same pattern as file tests)

@pytest.fixture
def mock_drive_client() -> MagicMock
    # MagicMock with async methods:
    # - download_file(file_id, dest_path) -> Path
    # - list_files() -> (files[], page_token)
    # - upload_file() -> MockDriveFile

@pytest.fixture
def sample_drive_files() -> list[MockDriveFile]
    # 3 sample files: PDF, XLSX, PNG with realistic metadata

@pytest.fixture
def sample_google_workspace_files() -> list[MockDriveFile]
    # Google Docs/Sheets (MIME types starting with application/vnd.google-apps.*)
    # Used for testing exclusion in batch operations

@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path
    # Temporary download directory
```

**Pattern:** Dataclass mocks + MagicMock for async clients

---

## 2. Mocking Patterns

### Pattern A: ExecutionContext - Real vs Mock

**Option 1: Real ExecutionContext (Preferred)**
```python
from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext

@pytest.fixture
def execution_context() -> ExecutionContext:
    """Real context - good for integration-like tests."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )
```

**Option 2: Mock ExecutionContext**
```python
from unittest.mock import MagicMock

@pytest.fixture
def mock_context() -> MagicMock:
    """Mock context - good for unit tests with custom behavior."""
    context = MagicMock(spec=ExecutionContext)
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.variables = {}
    context.resources = {}
    return context
```

**When to use:**
- **Real:** Node execution tests, port value passing
- **Mock:** Single method testing, custom error injection

---

### Pattern B: AsyncMock for Async Methods

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_drive_client() -> MagicMock:
    client = MagicMock()

    # Option 1: Simple async mock
    client.download_file = AsyncMock(return_value=Path("/dest.pdf"))

    # Option 2: Mock with side effect
    async def mock_download(file_id: str, destination_path: str) -> Path:
        return Path(destination_path)

    client.download_file = AsyncMock(side_effect=mock_download)

    # Option 3: Tuple return (list files pattern)
    client.list_files = AsyncMock(return_value=([], None))

    return client
```

---

### Pattern C: File I/O Mocking (Avoided)

**CasareRPA Strategy:** Use real temporary files instead of mocking file I/O

```python
# GOOD - Use tmp_path
def test_read_file(tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello")
    # Now test with real file

# AVOID - Mocking pathlib
@patch('pathlib.Path.write_text')
def test_read_file(mock_write):
    # Brittle - breaks with implementation changes
```

---

## 3. Pytest Configuration

**File:** `pyproject.toml` (pytest section at line 149-160)

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]                              # Root test directory
python_files = ["test_*.py"]                       # Test file pattern
python_classes = ["Test*"]                         # Test class pattern
python_functions = ["test_*"]                      # Test method pattern
addopts = "-v --tb=short --cov=casare_rpa --cov-fail-under=75"
asyncio_mode = "auto"                              # Auto detect async tests
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
]
```

**Key Config Points:**
- **asyncio_mode = "auto"** - Automatically runs tests marked with `@pytest.mark.asyncio`
- **cov-fail-under=75** - CI fails if coverage drops below 75%
- **--tb=short** - Concise tracebacks for quick debugging

---

### Dev Dependencies for Testing

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",              # Test framework
    "pytest-asyncio>=0.21.1",     # Async test support
    "pytest-qt>=4.3.1",           # PySide6 widget testing
    "pytest-cov>=4.0.0",          # Coverage reporting
    "pytest-benchmark>=4.0.0",    # Performance benchmarking (available but not used)
    "black>=23.12.0",             # Code formatting
    "mypy>=1.7.1",                # Type checking
    "ruff>=0.1.0",                # Linting
    "pip-audit>=2.6.0",           # Security auditing
]
```

---

## 4. Test Structure Patterns

### Pattern A: Async Node Test

**From:** `tests/nodes/file/test_file_system_super_node.py`

```python
import pytest
from pathlib import Path
from casare_rpa.nodes.file.super_node import FileSystemSuperNode
from casare_rpa.domain.value_objects.types import DataType

class TestReadFileAction:
    """Tests for Read File action."""

    @pytest.mark.asyncio  # Enable async/await
    async def test_read_file_success(
        self,
        execution_context,      # Fixture injection
        temp_test_file: Path    # Fixture injection
    ) -> None:
        """SUCCESS: Read existing text file."""
        # ARRANGE
        node = FileSystemSuperNode(
            "test_read",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": str(temp_test_file),
                "encoding": "utf-8",
                "allow_dangerous_paths": True,
            }
        )

        # ACT
        result = await node.execute(execution_context)

        # ASSERT
        assert result["success"] is True
        assert node.get_output_value("content") == "Hello, World!"
        assert node.get_output_value("size") == 13
```

**Pattern Checklist:**
- ✓ Class-based tests (TestXxx)
- ✓ Descriptive method names (test_xxx_yyy)
- ✓ `@pytest.mark.asyncio` for async methods
- ✓ AAA pattern (Arrange, Act, Assert)
- ✓ Fixture injection via parameters
- ✓ Comments marking test paths (SUCCESS, SAD PATH, EDGE CASE)

---

### Pattern B: Setup Helper Functions

```python
def setup_action_ports(node: FileSystemSuperNode, action: str) -> None:
    """
    Setup output ports for a specific action.

    In production, the visual layer handles dynamic port management.
    For testing, we manually add the required ports.
    """
    config = FILE_SYSTEM_PORT_SCHEMA.get_config(action)
    if config:
        for port_def in config.outputs:
            if port_def.name not in node.output_ports:
                node.add_output_port(port_def.name, port_def.data_type)
```

**Usage:**
```python
async def test_write_file_success(self, execution_context, tmp_path):
    node = FileSystemSuperNode("test_write", config={...})
    setup_action_ports(node, FileSystemAction.WRITE.value)  # Setup ports
    result = await node.execute(execution_context)
```

---

### Pattern C: Event System Testing

**From:** `tests/examples/test_event_handling_example.py`

```python
@pytest.fixture
def event_bus():
    """Reset event bus before each test."""
    reset_event_bus()  # Clean slate
    return get_event_bus()

@pytest.fixture
def collector():
    """Create fresh event collector."""
    return ExampleEventCollector()

class TestEventPublishSubscribe:
    def test_subscribe_and_publish_single_event(self, event_bus, collector):
        # Arrange - subscribe
        event_bus.subscribe(ExampleTaskStarted, collector.on_task_started)

        # Act - publish
        event = ExampleTaskStarted(
            task_id="task_1",
            task_name="Example Task",
            priority=2
        )
        event_bus.publish(event)

        # Assert
        assert collector.started_count == 1
        assert len(collector.events) == 1
```

**Key Points:**
- Reset bus fixture prevents test pollution
- Event handlers collect events for assertions
- Multiple handlers can subscribe to same event type

---

### Pattern D: Domain Tests (No Mocking)

**From:** `tests/domain/test_property_schema.py`

```python
class TestPropertyDef:
    """Tests for PropertyDef dataclass."""

    def test_create_minimal_property(self) -> None:
        """Test creating PropertyDef with minimal arguments."""
        # Pure logic test - NO fixtures, NO mocking
        prop = PropertyDef(name="test", type=PropertyType.STRING)

        assert prop.name == "test"
        assert prop.type == PropertyType.STRING
        assert prop.default is None
        assert prop.label == "Test"  # Auto-generated from snake_case
        assert prop.essential is False
```

**Philosophy:**
- Domain layer tests focus on business logic
- No external dependencies needed
- No mocking or fixtures
- Fast and deterministic

---

## 5. Test Categories & Coverage

### By Layer

| Layer | Test Count | Location | Pattern |
|-------|-----------|----------|---------|
| **Domain** | 2 | `tests/domain/` | No mocking, pure logic |
| **Infrastructure** | 5 | `tests/infrastructure/ai/` | Mock snapshots, string data |
| **Nodes** | 10+ | `tests/nodes/{file,google}/` | Async, real temp files, mocks clients |
| **Examples** | 2 | `tests/examples/` | Best practice demonstrations |
| **Presentation** | 1 | `tests/presentation/` | Widget/UI testing (minimal) |

### By Aspect

| Aspect | Status | Notes |
|--------|--------|-------|
| **Workflow Loading** | NO TESTS FOUND | Gap: No `test_workflow_loader.py` |
| **File I/O** | EXTENSIVE | 450+ lines in test_file_system_super_node.py |
| **Google Drive API** | COMPREHENSIVE | Download, batch, sync operations |
| **AI Infrastructure** | GOOD | Page analysis, URL detection, MCP |
| **Performance/Benchmarks** | AVAILABLE BUT UNUSED | pytest-benchmark in dependencies |
| **Event System** | EXAMPLE-DRIVEN | test_event_handling_example.py |

---

## 6. Missing Patterns & Gaps

### Gap 1: No Workflow Loader Tests
**Expected:** `tests/utils/test_workflow_loader.py` or `tests/infrastructure/test_workflow_loader.py`

**Current Impact:**
- Workflow deserialization untested
- No regression detection for schema changes
- Workflow serialization layer has no unit tests

**Recommended Fixtures:**
```python
@pytest.fixture
def sample_workflow_json() -> dict:
    """Minimal valid workflow JSON."""
    return {
        "workflow_id": "test_wf_001",
        "name": "Test Workflow",
        "nodes": [
            {"node_id": "n1", "node_type": "ReadFileNode", "config": {...}},
        ],
        "connections": [...],
    }

@pytest.fixture
def workflow_file(tmp_path: Path, sample_workflow_json):
    """Workflow saved as JSON file."""
    wf_path = tmp_path / "workflow.json"
    wf_path.write_text(json.dumps(sample_workflow_json))
    return wf_path
```

---

### Gap 2: No Serialization Tests
**Missing:** Tests for `WorkflowSerializer` and deserialization

**Impact:**
- Schema evolution could break existing workflows silently
- Port type changes untested
- Node registry changes have no safety net

---

### Gap 3: No Performance Benchmarks
**Available:** `pytest-benchmark` is in dev dependencies

**Suggested Use Cases:**
```python
@pytest.mark.benchmark
def test_large_workflow_load_performance(benchmark, large_workflow_file):
    """Benchmark loading a 500-node workflow."""
    def load():
        return WorkflowLoader.load(large_workflow_file)

    result = benchmark(load)
    assert result.stats.mean < 0.5  # Must load in <500ms
```

---

### Gap 4: Minimal Presentation/UI Tests
**Current:** Only 1 test file in `tests/presentation/`

**Available:** `pytest-qt>=4.3.1` for PySide6 widget testing

**Opportunity:**
- Canvas component tests
- Visual node rendering tests
- Signal/slot connection tests

---

## 7. Test Execution Guide

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Categories
```bash
pytest tests/domain/              # Domain logic only
pytest tests/nodes/file/          # File node tests
pytest tests/infrastructure/ai/   # AI infrastructure tests
pytest tests/examples/            # Pattern examples
```

### Run with Coverage
```bash
pytest tests/ --cov=casare_rpa --cov-report=html
```

### Run Only Async Tests
```bash
pytest tests/ -k "asyncio" -v
```

### Skip Slow Tests
```bash
pytest tests/ -m "not slow" -v
```

### Generate Coverage Report
```bash
pytest tests/ --cov=casare_rpa --cov-report=term-missing
```

---

## 8. Fixture Quick Reference

### ExecutionContext Fixtures

```python
# Real execution context
execution_context: ExecutionContext  # From conftest
    - workflow_name: "TestWorkflow"
    - mode: ExecutionMode.NORMAL
    - variables: {}

# Mock execution context
mock_context: MagicMock  # From conftest
    - resolve_value(): returns input unchanged
    - variables: dict
    - resources: dict
```

### File System Fixtures

```python
temp_test_file          # Single text file (13 bytes)
temp_csv_file           # CSV with 3 data rows
temp_json_file          # JSON with nested structure
temp_image_file         # PNG image (10x10)
temp_directory          # Tree: 3 files + 1 subdir
temp_zip_file           # ZIP archive of temp_directory
```

### Page Analysis Fixtures

```python
login_page_snapshot     # Form with username/password
table_page_snapshot     # Table with headers
nav_page_snapshot       # Navigation menu
dropdown_page_snapshot  # Form controls (dropdown, checkbox)
empty_snapshot          # Empty string (edge case)
complex_page_snapshot   # Multi-form registration page
sample_page_dict        # Dict representation of page context
```

### Google Drive Fixtures

```python
execution_context       # Real ExecutionContext
mock_drive_client       # MagicMock GoogleDriveClient
sample_drive_files      # 3 MockDriveFile objects
sample_google_workspace_files  # Google Docs/Sheets (excluded)
tmp_download_dir        # Temporary download directory
```

---

## 9. Mocking Strategy Checklist

### Before Writing a Mock:
- [ ] Is there a real fixture available? (Use it first)
- [ ] Does the code need to handle async? (Use AsyncMock)
- [ ] Is it a file/directory? (Use tmp_path, not @patch)
- [ ] Is it an external API? (Mock the client, not individual methods)
- [ ] Need to inject errors? (Use side_effect or raise in mock)

### Best Practices:
- ✓ Use `spec=RealClass` to prevent misspelled attributes
- ✓ Use `side_effect` for complex behavior
- ✓ Use `assert_called_once_with()` to verify calls
- ✓ Reset mocks between tests if using class-level fixtures
- ✓ Document why a mock is needed (comment in fixture)

---

## 10. Test Documentation Patterns

### Pattern: Comment-Based Test Paths
```python
class TestFileOperations:
    """Tests for file operations."""

    @pytest.mark.asyncio
    async def test_read_file_success(self, ...):
        """SUCCESS: Read existing text file."""
        # ^ This indicates happy path test

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, ...):
        """SAD PATH: File does not exist."""
        # ^ This indicates error/exception path

    @pytest.mark.asyncio
    async def test_read_file_empty(self, ...):
        """EDGE CASE: Empty file."""
        # ^ This indicates boundary condition
```

**Convention:**
- `SUCCESS:` - Normal operation works
- `SAD PATH:` - Expected failure (input validation, not found)
- `EDGE CASE:` - Boundary conditions (empty, very large, special chars)
- `SECURITY:` - Security-related tests
- No prefix - General/utility tests

---

## 11. Integration with CI/CD

**Current Setup (from pyproject.toml):**
```
pytest tests/ \
  -v \
  --tb=short \
  --cov=casare_rpa \
  --cov-fail-under=75
```

**CI Expectations:**
- All tests must pass
- Coverage must stay >= 75%
- Test output captured for debugging
- Async tests run in "auto" mode

---

## 12. Recommended Next Steps

### Priority 1: Add Workflow Loader Tests
```
tests/utils/test_workflow_loader.py      # For WorkflowLoader
tests/infrastructure/test_serializer.py   # For WorkflowSerializer
```

### Priority 2: Add Performance Benchmarks
```
tests/benchmarks/
├── test_workflow_load_performance.py
├── test_node_execution_performance.py
└── test_event_system_performance.py
```

### Priority 3: Expand Presentation Tests
```
tests/presentation/
├── test_canvas_widget.py
├── test_visual_node_rendering.py
└── test_signal_connections.py
```

### Priority 4: Add Integration Tests
```
tests/integration/
├── test_workflow_execution_e2e.py
├── test_robot_communication.py
└── test_orchestrator_scheduling.py
```

---

## 13. Example Test Template

Use this template for new test files:

```python
"""
Tests for [module name].

AI-HINT: [What to copy from this test]
AI-CONTEXT: [When to use this pattern]

Run: pytest tests/[path]/test_xxx.py -v
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# =============================================================================
# IMPORTS - Organize by category
# =============================================================================

from casare_rpa.domain.entities import BaseNode
from casare_rpa.infrastructure.execution import ExecutionContext


# =============================================================================
# FIXTURES - Shared test data
# =============================================================================

@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


# =============================================================================
# TEST CLASSES - Grouped by feature
# =============================================================================

class TestFeatureA:
    """Tests for Feature A."""

    @pytest.mark.asyncio
    async def test_feature_a_success(self, execution_context) -> None:
        """SUCCESS: Feature A works normally."""
        # ARRANGE
        node = MyNode("test_node")

        # ACT
        result = await node.execute(execution_context)

        # ASSERT
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_feature_a_error(self, execution_context) -> None:
        """SAD PATH: Feature A handles missing input."""
        # ARRANGE, ACT, ASSERT...
        pass


class TestFeatureB:
    """Tests for Feature B."""

    def test_feature_b_pure_logic(self) -> None:
        """Pure domain logic - no async needed."""
        # ARRANGE, ACT, ASSERT...
        pass
```

---

## 14. Key Statistics

| Metric | Value |
|--------|-------|
| Total Test Files | 22 |
| Async Test Methods | 50+ |
| Fixture Files | 3 (conftest.py) |
| Largest Test File | test_file_system_super_node.py (1092 lines) |
| Min Coverage Required | 75% |
| Test Framework | pytest 7.4.3+ |
| Async Support | pytest-asyncio 0.21.1+ |
| CI Mode | asyncio_mode = "auto" |

---

## Summary

CasareRPA's testing infrastructure is:
- **Well-organized** with conftest.py files at strategic locations
- **Async-native** using pytest-asyncio with automatic detection
- **Fixture-heavy** using real files (tmp_path) instead of mocks where possible
- **Documentation-rich** with inline examples in tests/examples/
- **Gaps present** - notably missing workflow loader and serialization tests
- **Ready for expansion** with benchmarking and integration tests

All patterns follow pytest best practices and are consistent across the codebase.
