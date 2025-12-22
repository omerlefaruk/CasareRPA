# CasareRPA Testing & Quality Infrastructure Guide

**Updated:** 2025-12-14
**Scope:** Testing infrastructure, quality tools, documentation patterns
**Purpose:** Guide for agents/commands leveraging test patterns and quality systems

---

## 1. Test Infrastructure Overview

### 1.1 Test Discovery & Organization

**Test Root:** `tests/`
**Test Count:** 365 tests across 14 test files
**Configuration:** `pyproject.toml` pytest section

**Test Categories:**

| Category | Location | Purpose | Count |
|----------|----------|---------|-------|
| **Domain Tests** | `tests/domain/` | Entity, value object, schema tests | ~50+ |
| **Node Tests** | `tests/nodes/` | File, Google Drive nodes | ~80+ |
| **Example Tests** | `tests/examples/` | Template/reference tests | ~20 |
| **Infrastructure Tests** | `tests/infrastructure/ai/` | AI, HTTP, LLM tests | ~30+ |
| **Performance Tests** | `tests/performance/` | Workflow loading benchmarks | ~70 |
| **Presentation Tests** | `tests/presentation/` | Visual node, super node tests | ~15+ |

### 1.2 Test Command Quick Reference

```bash
# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/domain/ -v                          # Domain layer
pytest tests/nodes/ -v                           # Node tests
pytest tests/performance/ -v                     # Performance benchmarks
pytest tests/infrastructure/ai/ -v               # AI/LLM tests

# Run with filters
pytest tests/ -k "performance" -v                # By keyword
pytest tests/ -m "slow" -v                       # By marker
pytest tests/ -m "not slow" -v                   # Exclude slow tests

# Run with coverage
pytest tests/ --cov=casare_rpa --cov-report=html

# Run specific test
pytest tests/performance/test_workflow_loading.py::TestWorkflowSkeleton::test_create_skeleton_with_defaults -v

# Pytest markers (defined in pyproject.toml)
# Available: slow, integration, e2e
```

### 1.3 Pytest Configuration

**File:** `pyproject.toml` [tool.pytest.ini_options]

```toml
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

**Key Settings:**
- **Coverage Threshold:** 75% minimum (`--cov-fail-under=75`)
- **Async Mode:** Auto (auto-discovers async tests)
- **Output:** Verbose with short traceback
- **Plugins:** pytest-asyncio, pytest-qt, pytest-benchmark, pytest-cov

---

## 2. Test Patterns & Mocking Strategy

### 2.1 Layer-Specific Mocking Rules

**Source:** `.brain/docs/tdd-guide.md`

| Layer | Scope | Mocks | Example |
|-------|-------|-------|---------|
| **Domain** | `tests/domain/` | NONE (use real objects) | Real `PropertyDef`, `DataType`, entities |
| **Application** | `tests/application/` | Infrastructure only | Mock HTTP clients, persistence, etc. |
| **Infrastructure** | `tests/infrastructure/` | ALL external APIs | Mock Playwright, UIAutomation, win32 |
| **Nodes** | `tests/nodes/` | Same as infrastructure | Mock file I/O, APIs, browser automation |
| **Presentation** | `tests/presentation/` | Heavy Qt components | Mock QMainWindow, QApplication, Qt signals |

### 2.2 What to Mock vs. Real

**Always Mock:**
```python
# External libraries and APIs
from unittest.mock import MagicMock, AsyncMock, patch

# Playwright
mock_page = MagicMock()
mock_browser = AsyncMock()

# UIAutomation
mock_control = MagicMock()

# win32 APIs
with patch("win32gui.FindWindow"):
    ...

# Async HTTP
mock_http_client = AsyncMock()
mock_response = AsyncMock()
mock_response.json.return_value = {"key": "value"}

# File I/O
with patch("aiofiles.open"):
    ...

# PIL/Image operations
with patch("PIL.Image.open"):
    ...

# Database
mock_repo = AsyncMock()
await mock_repo.save()
```

**Prefer Real:**
```python
# Domain layer - always use real instances
from casare_rpa.domain.schemas.property_schema import PropertyDef, PropertyType
prop = PropertyDef("name", PropertyType.STRING, default="")

# Value objects
from casare_rpa.domain.value_objects.types import ExecutionMode
mode = ExecutionMode.NORMAL

# Entities
from casare_rpa.domain.entities.base_node import BaseNode

# Domain services (pure logic)
from casare_rpa.domain.services import WorkflowValidator
```

### 2.3 Fixture Patterns

**Global Fixtures** (no root conftest - fixtures are module-scoped):

| Module | Fixtures | Purpose |
|--------|----------|---------|
| `tests/performance/conftest.py` | `execution_context`, `mock_context`, `small_workflow_data`, `medium_workflow_data`, `large_workflow_data` | Workflow testing |
| `tests/nodes/file/conftest.py` | `execution_context`, `mock_context`, `temp_test_file`, `temp_csv_file`, `temp_json_file`, `temp_directory` | File operations |
| `tests/nodes/google/conftest.py` | Google-specific fixtures | Google Drive testing |
| `tests/infrastructure/ai/conftest.py` | AI/LLM-specific fixtures | AI assistant testing |

**Fixture Usage Pattern:**

```python
# tests/performance/conftest.py example
@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )

@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock execution context."""
    context = MagicMock(spec=ExecutionContext)
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.variables = {}
    context.resources = {}
    return context

# In test file
def test_something(execution_context):
    # Use real context
    assert execution_context.workflow_name == "TestWorkflow"

def test_mock_something(mock_context):
    # Use mock context
    mock_context.resolve_value("test_value")
    mock_context.resolve_value.assert_called_once_with("test_value")
```

### 2.4 Async Testing Pattern

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_execution(execution_context):
    """Test async node execution."""
    # Create async mock
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.json.return_value = {"result": "success"}
    mock_client.get.return_value = mock_response

    # Execute
    result = await mock_client.get("https://api.example.com")
    data = await result.json()

    # Assert
    assert data["result"] == "success"
    mock_client.get.assert_awaited_once_with("https://api.example.com")
```

---

## 3. Specific Test Categories

### 3.1 Domain Tests (`tests/domain/`)

**Purpose:** Test pure business logic, value objects, entities (NO mocks)

**Files:**
- `test_dynamic_port_config.py` - Port definitions for Super Nodes (27 tests)
- `test_property_schema.py` - Node property schema system (30+ tests)

**Example Test Structure:**

```python
# tests/domain/test_property_schema.py
class TestPropertyDef:
    """Tests for PropertyDef dataclass."""

    def test_create_minimal_property(self) -> None:
        """SUCCESS: Create PropertyDef with minimal arguments."""
        prop = PropertyDef(name="test", type=PropertyType.STRING)

        assert prop.name == "test"
        assert prop.type == PropertyType.STRING

    def test_auto_label_generation(self) -> None:
        """SUCCESS: snake_case names auto-convert to Title Case."""
        prop = PropertyDef(
            name="my_long_property_name",
            type=PropertyType.STRING
        )
        assert prop.label == "My Long Property Name"
```

**Key Pattern:** Use descriptive test names with outcome prefixes (SUCCESS, FAILURE, EDGE_CASE)

### 3.2 Example Tests (`tests/examples/`)

**Purpose:** Reference/template tests for agents/developers

**Files:**
- `test_node_creation_example.py` - Complete node creation walkthrough
- `test_event_handling_example.py` - Event bus usage pattern

**Includes:**
- Step-by-step imports and setup
- AI-HINT and AI-CONTEXT comments for LLM guidance
- Complete working examples
- Documentation inline with code

**Command Leverage:** Agents can copy patterns from these tests when implementing new nodes

### 3.3 Performance Tests (`tests/performance/`)

**Purpose:** Workflow loading benchmarks and optimization validation

**File:** `tests/performance/test_workflow_loading.py` (70+ tests)

**Test Classes:**
```
TestWorkflowSkeleton          # Lightweight metadata loading
TestIncrementalLoader         # Two-phase loading (skeleton + full)
TestNodeInstancePool          # Object pooling for node reuse
TestWorkflowLoading           # Full workflow loading benchmarks
TestParallelInstantiation     # Multi-threaded node instantiation
TestStreamingDecompression    # gzip/zstd decompression
TestWorkflowCaching           # LRU caching for repeated loads
```

**Performance Assertion Pattern:**

```python
import time
from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

def test_skeleton_loading_performance(medium_workflow_data):
    """Verify skeleton loading is fast (< 10ms)."""
    loader = IncrementalLoader()

    start = time.perf_counter()
    skeleton = loader.load_skeleton(medium_workflow_data)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.01  # 10ms threshold
    assert skeleton.node_count == 50
```

**Command Leverage:** Performance tests validate optimization PRs; agents can extend with new benchmarks

### 3.4 Node Tests (`tests/nodes/`)

**Purpose:** Test specific node implementations with mocked external dependencies

**Subdirectories:**
- `tests/nodes/file/` - File system operations (2 Super Node tests)
- `tests/nodes/google/` - Google Drive integration (2 tests)

**Fixture Pattern:**

```python
# tests/nodes/file/conftest.py
@pytest.fixture
def temp_test_file(tmp_path: Path) -> Path:
    """Create a temporary test file with content."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Hello, World!", encoding="utf-8")
    return test_file

# In test
def test_read_file_node(temp_test_file):
    """Test FileSystemSuperNode read action."""
    node = FileSystemSuperNode()
    result = node.execute(action="read", file_path=str(temp_test_file))
    assert result["success"] is True
    assert result["content"] == "Hello, World!"
```

### 3.5 Infrastructure Tests (`tests/infrastructure/ai/`)

**Purpose:** Test AI assistant, page analysis, MCP integration

**Files:**
- `test_imports.py` - Module import validation
- `test_page_analyzer.py` - Web page analysis
- `test_playwright_mcp.py` - MCP server integration
- `test_url_detection.py` - URL extraction from pages

### 3.6 Presentation Tests (`tests/presentation/`)

**Purpose:** Test visual nodes, super node mixins (minimal - heavy Qt mocking)

**File:** `test_super_node_mixin.py` - SuperNodeMixin dynamic port creation

---

## 4. Quality Tools Configuration

### 4.1 Linting & Formatting

**Tool:** Ruff (Fast Python linter/formatter)

**Configuration:** `.pre-commit-config.yaml`

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.4
  hooks:
    - id: ruff
      args:
        - --fix
        - --exit-non-zero-on-fix
        - --ignore=E402,F401,F821,F841
    - id: ruff-format
```

**Active Ignores:**
- `E402` - Module import not at top (~90 errors)
- `F401` - Unused imports (~10 errors)
- `F821` - Undefined name (6 errors)
- `F841` - Unused variable (2 errors)

**Running Ruff:**
```bash
# Run linter with auto-fix
ruff check --fix src/

# Run formatter
ruff format src/

# Via pre-commit
pre-commit run ruff --all-files
```

### 4.2 Type Checking (MyPy - DISABLED)

**Status:** Disabled - 2945 errors across 118 files

**Configuration:** In `.pre-commit-config.yaml` (commented out)

**Issue:** Needs systematic cleanup before incrementally enabling

**Future Plan:** Enable per-file starting with clean architecture layers (domain, application)

### 4.3 Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

**Hooks Enabled:**

| Hook | Purpose |
|------|---------|
| `trailing-whitespace` | Remove trailing spaces |
| `end-of-file-fixer` | Ensure single newline at EOF |
| `check-yaml` | Validate YAML syntax |
| `check-json` | Validate JSON syntax |
| `check-added-large-files` | Prevent files > 1MB |
| `check-merge-conflict` | Detect merge conflict markers |
| `debug-statements` | Find `breakpoint()`, `pdb` |
| `ruff` | Linting with auto-fix |
| `ruff-format` | Code formatting |

**Installation & Usage:**

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on staged files (automatic on git commit)
git commit  # Hooks run automatically
```

### 4.4 GitHub Actions / CI/CD

**Status:** Not yet configured
**Recommendation:** Add workflow to run:
1. `pytest tests/ --cov=casare_rpa --cov-fail-under=75`
2. `pre-commit run --all-files`
3. `ruff check src/ --fix` (non-blocking)

### 4.5 Code Coverage

**Threshold:** 75% minimum (enforced)

**Running Coverage:**
```bash
# Generate HTML coverage report
pytest tests/ --cov=casare_rpa --cov-report=html
# Open htmlcov/index.html in browser

# Show coverage summary
pytest tests/ --cov=casare_rpa --cov-report=term-missing

# Fail if below threshold
pytest tests/ --cov=casare_rpa --cov-fail-under=75
```

---

## 5. Documentation Structure (.brain/ Directory)

### 5.1 Directory Organization

```
.brain/
├── context/              # Session state
│   ├── current.md        # Active session (25-100 lines)
│   ├── recent.md         # Recently worked on
│   └── archive/          # Historical sessions
├── decisions/            # Decision trees
│   ├── _index.md         # Navigation
│   ├── add-node.md       # "How to add a node?"
│   ├── add-feature.md    # "How to add UI/API?"
│   ├── fix-bug.md        # "How to debug?"
│   └── modify-execution.md
├── docs/                 # Reference documentation
│   ├── node-templates.md # Node implementation templates
│   ├── node-checklist.md # Node dev checklist
│   ├── tdd-guide.md      # Testing patterns
│   ├── ui-standards.md   # UI/Canvas rules
│   ├── widget-rules.md   # Widget development
│   ├── trigger-checklist.md
│   └── super-node-pattern.md
├── plans/                # Research & planning
│   ├── comprehensive-qa-plan.md
│   ├── workflow-loading-optimization.md
│   └── ~30 other plans
├── projectRules.md       # Authoritative coding rules
├── systemPatterns.md     # Architecture patterns
├── symbols.md            # Symbol registry
├── dependencies.md       # Dependency map
├── errors.md            # Error catalog
└── performance-baseline.md
```

### 5.2 Key Documentation Files

| File | Purpose | When to Use |
|------|---------|------------|
| `.brain/context/current.md` | Session state tracker | START of session - read first (25 lines) |
| `.brain/decisions/_index.md` | Navigation hub | "What do I need to do?" |
| `.brain/decisions/add-node.md` | Node creation guide | Creating new automation nodes |
| `.brain/decisions/add-feature.md` | Feature guide | Adding UI/API/business logic |
| `.brain/decisions/fix-bug.md` | Debugging guide | "What's broken and why?" |
| `.brain/docs/node-checklist.md` | Implementation checklist | Verify node completeness |
| `.brain/docs/tdd-guide.md` | Testing philosophy | Writing tests |
| `.brain/projectRules.md` | Authoritative standards | Code style, architecture rules |
| `.brain/systemPatterns.md` | Architecture reference | How components connect |
| `.brain/symbols.md` | Symbol locations | Find class/function definitions |
| `.brain/errors.md` | Error catalog | Decode error codes |
| `.brain/dependencies.md` | Import graph | Understand impact of changes |

### 5.3 Decision Tree Patterns

**Location:** `.brain/decisions/` - 4 files

**Structure:** Each decision file follows this pattern:

```markdown
# [Task] Decision Tree

## Quick Reference
- **When to use:** [Condition]
- **Related files:** [List of files]
- **Key commands:** [bash/pytest commands]

## Step 1: [First Decision Point]
- Option A → leads to Step 2
- Option B → leads to Step 3

## Step 2: [Implement Path A]
- Sub-step 1
- Sub-step 2
- Links to `.brain/docs/` reference files

## Examples
- Real example from codebase
- Copy-paste ready code
```

**Usage Pattern:**
```
User asks: "I need to add a file reader node"
  ↓
Agent reads: .brain/decisions/add-node.md
  ↓
Agent follows: Step 1 → Step 2 → Step 3 decision tree
  ↓
Agent references: .brain/docs/node-templates.md (copy template)
  ↓
Agent checks: .brain/docs/node-checklist.md (verify completeness)
```

### 5.4 Index Files (`_index.md` Pattern)

**Key Index Files:**

| Path | Lines | Purpose |
|------|-------|---------|
| `src/casare_rpa/nodes/_index.md` | 150+ | Node registry with categories |
| `src/casare_rpa/presentation/canvas/visual_nodes/_index.md` | 200+ | Visual node implementations |
| `src/casare_rpa/domain/_index.md` | 100+ | Domain entities, value objects |
| `src/casare_rpa/application/_index.md` | 80+ | Use cases, orchestrators |
| `src/casare_rpa/infrastructure/_index.md` | 100+ | Adapters, resources |
| `.brain/decisions/_index.md` | 80 | Decision tree navigation |

**Index Format:**
```markdown
# [Directory] Index

Quick navigation and count for component discovery.

## Categories

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| ComponentA | file.py | 150 | Description |

## Quick Stats
- Total files: X
- Total lines: Y
- Last updated: date
```

### 5.5 Planning & Research Files

**Location:** `.brain/plans/` - ~30 research documents

**Categories:**
- Performance optimization
- QA and testing improvements
- UI/Canvas enhancements
- AI/ML integration
- Security and credentials
- Database connectivity

**Format:** Research findings → implementation recommendations

---

## 6. How Commands Leverage This Infrastructure

### 6.1 `/implement-node` Command Integration

**Recommended Flow:**

```
1. Read `.brain/context/current.md` - Session state
2. Check `src/casare_rpa/nodes/_index.md` - What nodes exist?
3. Read `.brain/decisions/add-node.md` - Decision tree
4. Copy template from `.brain/docs/node-templates.md`
5. Follow checklist from `.brain/docs/node-checklist.md`
6. Create tests based on `tests/examples/test_node_creation_example.py`
7. Validate with `.brain/docs/tdd-guide.md` mocking rules
8. Update `nodes/_index.md` and context file
```

### 6.2 `/implement-feature` Command Integration

```
1. Read `.brain/decisions/add-feature.md` - Decision tree
2. Check layer dependencies in `.brain/systemPatterns.md`
3. Reference `.brain/projectRules.md` for coding standards
4. Write tests first per `.brain/docs/tdd-guide.md`
5. Use fixtures from relevant `conftest.py`
6. Update `.brain/context/current.md` with progress
```

### 6.3 `/fix-feature` Command Integration

```
1. Read `.brain/decisions/fix-bug.md` - Debugging guide
2. Check `.brain/errors.md` - Known error patterns
3. Trace dependencies via `.brain/dependencies.md`
4. Create characterization test (test-after)
5. Fix implementation
6. Run full test suite: pytest tests/ -v
7. Check coverage: pytest tests/ --cov --cov-fail-under=75
```

### 6.4 Test Running in Commands

**Quick validation:**
```bash
# Run relevant tests for changes
pytest tests/nodes/file/ -v        # If modifying file nodes
pytest tests/performance/ -v       # If modifying workflow loading
pytest tests/domain/ -v            # If modifying domain layer

# Run full suite before commit
pytest tests/ -v --cov --cov-fail-under=75
pre-commit run --all-files
```

---

## 7. Quality Metrics & Baselines

### 7.1 Test Coverage

**Current Status:**
- **Threshold:** 75% minimum (enforced)
- **Current Coverage:** ~75-80% (estimated)
- **Tracked Files:** All under `src/casare_rpa/`

**Improvement Areas:**
- Infrastructure layer - Some cloud adapters untested
- Presentation layer - Qt heavy components skipped
- Nodes layer - Desktop automation mocking needed

### 7.2 Performance Baselines

**File:** `.brain/performance-baseline.md`

**Key Metrics:**
- Workflow loading: Small (10 nodes) < 50ms, Medium (50 nodes) < 100ms
- Skeleton loading: < 10ms for any size
- Node instantiation: < 2ms per node (pooled)
- Search indexing: < 500ms for full codebase

### 7.3 Code Quality Metrics

**Linting:** Ruff (enabled with selective ignores)
**Type Checking:** MyPy (disabled - 2945 errors to fix)
**Formatting:** Black/Ruff (enforced)

---

## 8. Common Testing Tasks

### 8.1 Add Test for New Feature

```bash
# 1. Create test file
touch tests/[category]/test_new_feature.py

# 2. Write test using conftest fixtures
# Use patterns from tests/examples/test_node_creation_example.py

# 3. Run and validate
pytest tests/[category]/test_new_feature.py -v

# 4. Check coverage
pytest tests/[category]/ --cov --cov-report=term-missing
```

### 8.2 Debug Failing Test

```bash
# 1. Run with full output
pytest tests/[path]/test_file.py::test_name -vv -s

# 2. Add breakpoint (will be caught by pre-commit)
import pdb; pdb.set_trace()

# 3. Run with pdb
pytest tests/[path]/test_file.py::test_name --pdb

# 4. Check mocking - verify fixtures in conftest
```

### 8.3 Performance Regression Check

```bash
# Run performance tests
pytest tests/performance/ -v --benchmark-only

# Or specific benchmark
pytest tests/performance/test_workflow_loading.py::test_skeleton_loading_performance -v
```

---

## 9. Summary for Agent Commands

### Commands Should:

1. **Before Making Changes:**
   - Read `.brain/context/current.md` (Session state)
   - Check relevant `_index.md` file
   - Look for existing patterns in `tests/examples/`

2. **When Writing Code:**
   - Follow `.brain/projectRules.md` (Authoritative)
   - Reference `.brain/systemPatterns.md` (Architecture)
   - Use decision trees in `.brain/decisions/`

3. **When Testing:**
   - Use mocking rules from `.brain/docs/tdd-guide.md`
   - Copy fixture patterns from `tests/[category]/conftest.py`
   - Follow assertion patterns from `tests/examples/`
   - Run: `pytest tests/ -v --cov --cov-fail-under=75`

4. **When Documenting:**
   - Update relevant `_index.md` file
   - Add entry to `.brain/context/current.md`
   - Link from `.brain/decisions/` if applicable

5. **Before Committing:**
   - Run full test suite: `pytest tests/ -v`
   - Run pre-commit: `pre-commit run --all-files`
   - Verify coverage: `--cov-fail-under=75`

---

## 10. Quick Command Reference

**Test Execution:**
```bash
pytest tests/ -v                                # All tests
pytest tests/domain/ -v                         # Domain layer only
pytest tests/performance/ -v                    # Performance tests
pytest tests/ -k "skeleton" -v                  # By keyword
pytest tests/ -m "not slow" -v                  # Exclude slow tests
pytest tests/ --cov --cov-fail-under=75        # With coverage
```

**Quality Checks:**
```bash
pre-commit run --all-files                      # All hooks
ruff check --fix src/                           # Linting
ruff format src/                                # Formatting
```

**Documentation Navigation:**
```
Start here: .brain/context/current.md
Need to add something? → .brain/decisions/
Need reference docs? → .brain/docs/
Find symbols? → .brain/symbols.md
Understanding error? → .brain/errors.md
```

---

**Generated:** 2025-12-14
**Next Update:** When test infrastructure changes materially
