# Command Testing Playbook

**For:** `/implement-feature`, `/implement-node`, `/fix-feature` agents
**Updated:** 2025-12-14

This file describes how agent commands should integrate with CasareRPA's test infrastructure and quality systems.

---

## Pre-Implementation Checklist

Before starting ANY implementation:

- [ ] Read `.brain/context/current.md` - Session state
- [ ] Check relevant `_index.md` file (nodes, domain, etc.)
- [ ] Review `.brain/decisions/[task].md` - Decision tree
- [ ] Scan `tests/examples/` for similar patterns
- [ ] Identify test category (domain, nodes, infrastructure, etc.)

---

## Per-Layer Test Guidelines

### Domain Layer (tests/domain/)

**Rule:** NO mocks. Use real domain objects.

```python
# ✅ CORRECT - Tests domain logic with real objects
def test_property_def_auto_labeling():
    from casare_rpa.domain.schemas.property_schema import PropertyDef, PropertyType

    prop = PropertyDef(name="user_email", type=PropertyType.STRING)
    assert prop.label == "User Email"  # Auto-generated

# ❌ WRONG - Mocking domain objects
def test_property_def_auto_labeling():
    mock_prop = MagicMock()
    mock_prop.label = "User Email"
    assert mock_prop.label == "User Email"  # Defeats the purpose
```

**Test file pattern:**
```
tests/domain/test_[feature].py
├── imports (domain objects only)
├── class TestFeature:
│   ├── test_happy_path
│   ├── test_sad_path
│   └── test_edge_case
└── No fixtures needed (simple dataclasses)
```

### Application Layer (tests/application/)

**Rule:** Mock infrastructure only. Use real domain objects.

```python
# ✅ CORRECT - Real domain, mock infrastructure
@pytest.mark.asyncio
async def test_workflow_executor_handles_error():
    from casare_rpa.application.execute_workflow import ExecuteWorkflowUseCase
    from casare_rpa.domain.entities import Workflow, Node

    # Real domain objects
    workflow = Workflow(id="wf1", name="Test", nodes=[])

    # Mock infrastructure
    mock_repo = AsyncMock()
    mock_repo.get_workflow.return_value = workflow

    use_case = ExecuteWorkflowUseCase(repository=mock_repo)
    result = await use_case.execute("wf1")

    assert result["success"] is True
    mock_repo.get_workflow.assert_awaited_once_with("wf1")
```

### Infrastructure Layer (tests/infrastructure/)

**Rule:** Mock ALL external APIs (Playwright, HTTP, files, etc.)

```python
# ✅ CORRECT - Mock all external dependencies
@pytest.mark.asyncio
async def test_http_node_connection():
    from casare_rpa.infrastructure.http import UnifiedHttpClient

    # Mock the HTTP response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response

        client = UnifiedHttpClient()
        result = await client.get("https://api.example.com")

        assert result == {"result": "success"}
```

### Nodes Layer (tests/nodes/)

**Rule:** Mock file I/O, HTTP, browser automation. Use real execution context.

```python
# ✅ CORRECT - Mock external, use real context
def test_file_system_super_node_read(temp_test_file, execution_context):
    from casare_rpa.nodes.file.super_node import FileSystemSuperNode

    node = FileSystemSuperNode()
    result = node.execute(
        action="read",
        file_path=str(temp_test_file),
        context=execution_context
    )

    assert result["success"] is True
    assert result["content"] == "Hello, World!"
```

### Presentation Layer (tests/presentation/)

**Rule:** Mock Qt components. Test node/mixin logic with minimal Qt interaction.

```python
# ✅ CORRECT - Mock Qt, test mixin logic
from unittest.mock import MagicMock, patch

def test_super_node_mixin_creates_ports():
    from casare_rpa.presentation.canvas.visual_nodes.mixins import SuperNodeMixin

    # Mock Qt base class
    with patch.object(SuperNodeMixin, 'add_port'):
        mixin = SuperNodeMixin()
        mixin.create_ports_from_schema(actions=["read", "write"])

        # Verify ports created
        assert mixin.add_port.call_count == 2
```

---

## Implementation Workflow

### Step 1: Write Tests First (TDD)

**For NEW features:**
```python
# tests/[category]/test_new_feature.py
"""Tests for New Feature."""

import pytest

class TestNewFeature:
    """Test new feature."""

    def test_happy_path(self):
        """SUCCESS: Feature works normally."""
        # Arrange
        # Act
        # Assert
```

**For BUG FIXES (characterization test):**
```python
# tests/[category]/test_existing_feature.py - ADD to existing file
def test_bug_is_fixed():
    """REGRESSION: Issue #123 - Feature X was broken."""
    # Characterize the bug
    result = buggy_function()
    assert result is not None  # Was returning None
```

### Step 2: Run Tests (Red Phase)

```bash
# Expect failure
pytest tests/[category]/test_new_feature.py -v
# Should FAIL: No implementation yet
```

### Step 3: Implement Code (Green Phase)

- Follow layer rules (no domain imports in presentation, etc.)
- Use `.brain/projectRules.md` for style
- Reference `.brain/systemPatterns.md` for architecture
- Copy patterns from `tests/examples/`

### Step 4: Run Tests Again

```bash
# Expect passing
pytest tests/[category]/test_new_feature.py -v
# Should PASS now
```

### Step 5: Verify Coverage

```bash
# Check coverage for changed code
pytest tests/[category]/ --cov=casare_rpa.[module] --cov-report=term-missing
# Must be >= 75% overall
```

### Step 6: Run Full Suite

```bash
# Ensure no regressions
pytest tests/ -v --cov=casare_rpa --cov-fail-under=75
# All must PASS
```

### Step 7: Quality Checks

```bash
# Format and lint
pre-commit run --all-files

# Verify no errors in modified files
ruff check --fix src/casare_rpa/[modified_path]/
```

---

## Test File Template by Category

### Domain Test Template

```python
"""
Tests for [Domain Feature].

Pure domain logic tests. NO mocks, NO fixtures.

Run: pytest tests/domain/test_[feature].py -v
"""

import pytest
from casare_rpa.domain.schemas import PropertyDef, PropertyType


class TestPropertyDefValidation:
    """Test PropertyDef validation logic."""

    def test_auto_label_converts_snake_case(self):
        """SUCCESS: snake_case converted to Title Case."""
        prop = PropertyDef(
            name="my_property",
            type=PropertyType.STRING
        )
        assert prop.label == "My Property"

    def test_required_property_has_no_default(self):
        """VALIDATION: Required property fails without default."""
        with pytest.raises(ValueError):
            PropertyDef(
                name="required",
                type=PropertyType.STRING,
                required=True,
                default=None  # Invalid
            )


class TestPropertyDefEdgeCases:
    """Edge case tests."""

    def test_empty_property_name(self):
        """EDGE: Empty name raises error."""
        with pytest.raises(ValueError):
            PropertyDef(name="", type=PropertyType.STRING)

    def test_very_long_name(self):
        """EDGE: Long name handled correctly."""
        long_name = "a" * 1000
        prop = PropertyDef(name=long_name, type=PropertyType.STRING)
        assert len(prop.name) == 1000
```

### Node Test Template

```python
"""
Tests for [Node Name].

Tests node implementation with fixture-provided context.

Run: pytest tests/nodes/[category]/test_[node].py -v
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestFileSystemSuperNode:
    """Test FileSystemSuperNode actions."""

    def test_read_file_action(self, temp_test_file, execution_context):
        """SUCCESS: Read file and return content."""
        from casare_rpa.nodes.file.super_node import FileSystemSuperNode

        node = FileSystemSuperNode()
        result = node.execute(
            action="read",
            file_path=str(temp_test_file),
            context=execution_context
        )

        assert result["success"] is True
        assert "Hello, World!" in result["content"]

    def test_write_file_creates_new_file(self, tmp_path, execution_context):
        """SUCCESS: Write creates new file with content."""
        from casare_rpa.nodes.file.super_node import FileSystemSuperNode

        output_file = tmp_path / "output.txt"
        node = FileSystemSuperNode()

        result = node.execute(
            action="write",
            file_path=str(output_file),
            content="Test content",
            context=execution_context
        )

        assert result["success"] is True
        assert output_file.read_text() == "Test content"

    def test_read_nonexistent_file_fails(self, tmp_path, execution_context):
        """FAILURE: Reading missing file raises error."""
        from casare_rpa.nodes.file.super_node import FileSystemSuperNode

        missing_file = tmp_path / "missing.txt"
        node = FileSystemSuperNode()

        result = node.execute(
            action="read",
            file_path=str(missing_file),
            context=execution_context
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()
```

### Infrastructure Test Template

```python
"""
Tests for [Infrastructure Component].

Mock all external APIs (HTTP, files, etc.).

Run: pytest tests/infrastructure/test_[component].py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestUnifiedHttpClient:
    """Test HTTP client with mocked aiohttp."""

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """SUCCESS: GET request returns parsed response."""
        from casare_rpa.infrastructure.http import UnifiedHttpClient

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"key": "value"}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            client = UnifiedHttpClient()
            result = await client.get("https://api.example.com/data")

            assert result == {"key": "value"}
            mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_timeout_raises_error(self):
        """FAILURE: Request timeout handled gracefully."""
        from casare_rpa.infrastructure.http import UnifiedHttpClient
        from asyncio import TimeoutError

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = TimeoutError()

            client = UnifiedHttpClient()

            with pytest.raises(TimeoutError):
                await client.get("https://api.example.com/data")
```

---

## Test Data & Fixtures Strategy

### Global Fixtures (in conftest.py)

**Location:** `tests/[category]/conftest.py`

**Pattern:**
```python
# tests/nodes/file/conftest.py
import pytest
from pathlib import Path
from casare_rpa.infrastructure.execution import ExecutionContext

@pytest.fixture
def execution_context():
    """Provide real execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )

@pytest.fixture
def temp_test_file(tmp_path: Path) -> Path:
    """Provide temp file with content."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    return test_file
```

**Usage:** Fixtures automatically available in same `tests/[category]/` directory

### Workflow Test Data

**Pattern:**
```python
@pytest.fixture
def small_workflow_data():
    """Workflow with 10 nodes."""
    return {
        "metadata": {"name": "SmallWorkflow"},
        "nodes": {...},
        "connections": [...],
    }

@pytest.fixture
def medium_workflow_data():
    """Workflow with 50 nodes."""
    return _generate_workflow_data(50, "MediumWorkflow")
```

**Location:** `tests/performance/conftest.py`

---

## Common Pitfalls & How to Avoid Them

### Pitfall 1: Mocking Domain Objects

**Problem:**
```python
# ❌ WRONG
def test_property_schema():
    mock_prop = MagicMock()
    mock_prop.name = "test"
    # Not testing real behavior!
```

**Solution:**
```python
# ✅ CORRECT
def test_property_schema():
    prop = PropertyDef(name="test", type=PropertyType.STRING)
    # Tests real behavior
```

### Pitfall 2: Not Mocking External APIs

**Problem:**
```python
# ❌ WRONG - Makes real network call!
@pytest.mark.asyncio
async def test_api_integration():
    response = await aiohttp.ClientSession().get("https://api.example.com")
    # Tests actual API, slow, flaky
```

**Solution:**
```python
# ✅ CORRECT - Mocked HTTP
@pytest.mark.asyncio
async def test_api_integration():
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_get.return_value.__aenter__.return_value = mock_response
        # Fast, deterministic test
```

### Pitfall 3: Importing from Wrong Layer

**Problem:**
```python
# ❌ WRONG - Domain test using infrastructure
from casare_rpa.infrastructure.http import UnifiedHttpClient

def test_domain_feature():
    client = UnifiedHttpClient()  # Why? Domain doesn't need this!
```

**Solution:**
```python
# ✅ CORRECT - Domain test with domain objects only
from casare_rpa.domain.schemas import PropertyDef

def test_domain_feature():
    prop = PropertyDef(name="x", type=PropertyType.STRING)
```

### Pitfall 4: Missing Async Marker

**Problem:**
```python
# ❌ WRONG - Async test without marker
def test_async_operation():
    await some_async_function()  # Will fail!
```

**Solution:**
```python
# ✅ CORRECT - Mark async tests
@pytest.mark.asyncio
async def test_async_operation():
    await some_async_function()  # Works!
```

---

## Quality Gates (Pre-Commit Checklist)

Before creating a commit:

```bash
# 1. All tests pass
pytest tests/ -v
# Should see: "====== [X] passed in [Y]s ======"

# 2. Coverage meets threshold
pytest tests/ --cov=casare_rpa --cov-fail-under=75
# Should NOT see: "FAILED due to coverage being below 75%"

# 3. Pre-commit passes
pre-commit run --all-files
# Should see: "Passed" for all hooks

# 4. No type errors (check manually, MyPy disabled)
# Review: .brain/projectRules.md type hints
```

**If any gate fails:**
- Fix the issue
- Re-run gate
- Only commit when ALL pass

---

## Commit Message Template

When creating commits with tests:

```
[Scope]: [Brief Description]

[Body - explain why, not what]

Test Coverage:
- tests/domain/test_x.py - 3 new tests
- tests/nodes/test_y.py - 2 updated tests

Coverage: [X%] (meets 75% threshold)
CI: pre-commit passed

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Integration with Command Agents

### For `/implement-node` Command:

```python
1. Read .brain/decisions/add-node.md
2. Create tests/nodes/[category]/test_[node].py
3. Use conftest fixture pattern from tests/nodes/[category]/conftest.py
4. Copy template from TESTING_QUICK_START.md
5. Write tests for:
   - Port definition (_define_ports)
   - Property schema (@properties)
   - Execute method (happy/sad/edge cases)
6. Run: pytest tests/nodes/[category]/ --cov
7. Update tests/nodes/_index.md with new test count
```

### For `/implement-feature` Command:

```python
1. Read .brain/decisions/add-feature.md
2. Identify layer (domain/app/infra/presentation)
3. Create tests/[layer]/test_[feature].py
4. Follow layer-specific rules (see "Per-Layer Test Guidelines")
5. Write tests BEFORE implementation
6. Run: pytest tests/ -v --cov --cov-fail-under=75
7. Update .brain/context/current.md with test counts
```

### For `/fix-feature` Command:

```python
1. Read .brain/decisions/fix-bug.md
2. Create characterization test (test-after pattern)
3. Add to tests/[category]/test_existing_feature.py
4. Fix implementation
5. Verify test now passes
6. Run: pytest tests/ -v --cov --cov-fail-under=75
7. Document fix in .brain/context/current.md
```

---

## Quick Reference: What Tests Should Look Like

### By Outcome

- **SUCCESS:** "Feature works correctly" - Happy path
- **FAILURE:** "Feature handles errors" - Expected failures
- **EDGE:** "Feature handles boundaries" - Corner cases
- **REGRESSION:** "Bug is fixed" - Characterization tests

### By Test Type

- **Unit:** Single function/method in isolation
- **Integration:** Multiple components together
- **Performance:** Timing assertions for critical paths
- **E2E:** Full workflow from start to finish

### By Layer

- **Domain:** Real objects, no mocks, simple dataclasses
- **Application:** Real domain + mocked infrastructure
- **Infrastructure:** All external APIs mocked
- **Nodes:** Real execution context + mocked external APIs
- **Presentation:** Mocked Qt + tested logic

---

**Last Updated:** 2025-12-14
**Used By:** Agent commands (`/implement-feature`, `/implement-node`, `/fix-feature`)
