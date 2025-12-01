# Testing Infrastructure Plan

## Status: COMPLETE

Testing infrastructure for CasareRPA has been fully implemented. All foundational fixtures and utilities are in place and ready for test development.

---

## Brain Context References

- **Active Context**: `.brain/activeContext.md` - Current state of testing efforts
- **Project Rules**: `.brain/projectRules.md` - Architecture and development guidelines
- **System Patterns**: `.brain/systemPatterns.md` - Testing patterns and conventions

---

## Overview

The testing infrastructure provides a comprehensive foundation for developing tests across all layers of CasareRPA. Built on pytest with async support (pytest-asyncio, pytest-qt), it includes:

### What Was Implemented

#### 1. Chain Testing Infrastructure
- **WorkflowBuilder** (fluent API): Construct multi-node workflows for integration tests
  - Chainable API for adding nodes and connections
  - Auto-sequential connection mode for linear workflows
  - Port-level granularity for complex data flows

- **ChainExecutor** (execution engine): Execute node chains with real node implementations
  - Proper execution context management
  - Data flow tracking between connected ports
  - Timeout protection and error capture
  - Stop-on-error mode for fast failure detection

- **ChainExecutionResult** (result object): Detailed execution reporting
  - Success/failure status with error messages
  - Execution path tracking (nodes_executed)
  - Variable snapshots at completion
  - Per-node result inspection

#### 2. Connection & Integration Testing
- **Integration conftest** (`tests/integration/conftest.py`): Cross-layer fixtures
  - Real ExecutionContext instances
  - Shared workflow helpers
  - Test database fixtures (where applicable)

#### 3. Visual Testing Fixtures
- **Presentation fixtures** (`tests/presentation/canvas/conftest.py`)
  - Qt widget test utilities (qtbot-based)
  - Canvas mock helpers
  - NodeGraphQt visualization fixtures

#### 4. Performance Benchmarking
- **Performance conftest** (`tests/performance/conftest.py`)
  - Timer context manager for code block timing
  - Workflow generators:
    - `create_linear_chain(n)` - n SetVariable nodes in sequence
    - `create_branching_workflow(depth)` - If/Else branching at specified depth
    - `create_variable_operations_workflow(sets, gets)` - Variable set/get patterns
  - ExecutionContext factory for perf test isolation

---

## Test Locations Table

| Category | Path | Purpose | Fixtures |
|----------|------|---------|----------|
| **Global** | `tests/conftest.py` | Base fixtures for all tests | `execution_context`, `execution_context_with_variables`, `mock_execution_context` |
| **Domain** | `tests/domain/` | Entity/VO/Service unit tests | Global fixtures only (no mocks) |
| **Application** | `tests/application/` | Use case orchestration tests | Global fixtures + mocked infrastructure |
| **Infrastructure** | `tests/infrastructure/` | Adapter/resource tests | Mocked external APIs (Playwright, UIAutomation, etc.) |
| **Nodes** | `tests/nodes/` | Node category tests | Category-specific fixtures (see below) |
| **Nodes - Browser** | `tests/nodes/browser/` | Playwright-based nodes | `mock_page`, `mock_browser`, `mock_browser_context` |
| **Nodes - Desktop** | `tests/nodes/desktop/` | UIAutomation-based nodes | `MockUIControl`, `mock_win32`, desktop-specific fixtures |
| **Nodes - Chain** | `tests/nodes/chain/` | Multi-node workflow tests | `workflow_builder`, `chain_executor` |
| **Nodes - HTTP** | `tests/nodes/conftest.py` | REST/HTTP nodes | `create_mock_response()`, `create_mock_session()` |
| **Presentation** | `tests/presentation/` | Qt controller tests | Canvas/widget fixtures, `qtbot` |
| **Integration** | `tests/integration/` | Cross-layer workflows | Real context + mocked I/O |
| **Performance** | `tests/performance/` | Benchmark tests | `execution_context`, workflow generators, `timer` |
| **Desktop Managers** | `tests/desktop/managers/` | Win32 API tests | UIAutomation mocks, win32 stubs |

---

## Fixture Summary Table

### Global Fixtures (tests/conftest.py)

| Fixture | Returns | Purpose | Usage |
|---------|---------|---------|-------|
| `execution_context` | Mock | Basic execution context for generic node tests | Any test needing variable storage |
| `execution_context_with_variables` | Mock | Pre-populated with test variables | Tests needing initial state |
| `mock_execution_context` | Mock | Alias for compatibility | Legacy test support |

### Node Fixtures (tests/nodes/)

#### Browser Category (tests/nodes/browser/conftest.py)
| Fixture | Returns | Purpose |
|---------|---------|---------|
| `mock_page` | AsyncMock | Playwright Page object |
| `mock_browser` | AsyncMock | Playwright Browser object |
| `mock_browser_context` | AsyncMock | Playwright BrowserContext |

#### Desktop Category (tests/nodes/desktop/conftest.py)
| Fixture | Returns | Purpose |
|---------|---------|---------|
| `MockUIControl` | Class | Behavioral mock for UIAutomation Control |
| `mock_win32` | Patch | Mocks win32gui, win32con, ctypes |
| `mock_element` | Mock | Generic desktop element |

#### HTTP/Common (tests/nodes/conftest.py)
| Helper | Returns | Purpose |
|--------|---------|---------|
| `create_mock_response()` | AsyncMock | Configurable aiohttp response |
| `create_mock_session()` | MagicMock | aiohttp ClientSession with response |
| `mock_aiohttp_response` | AsyncMock | Fixture wrapper for responses |

#### Chain Testing (tests/nodes/chain/conftest.py)
| Fixture | Returns | Purpose |
|---------|---------|---------|
| `workflow_builder` | WorkflowBuilder | Fluent workflow construction API |
| `chain_executor` | ChainExecutor | Multi-node execution engine |

### Integration Fixtures (tests/integration/conftest.py)
| Fixture | Returns | Purpose |
|---------|---------|---------|
| `execution_context` | ExecutionContext | Real context (not mock) |
| Various workflow helpers | Factory functions | Pre-built test workflows |

### Performance Fixtures (tests/performance/conftest.py)
| Fixture/Helper | Returns | Purpose |
|----------------|---------|---------|
| `execution_context` | ExecutionContext | Fresh context per test |
| `create_linear_chain(n)` | WorkflowSchema | n sequential SetVariable nodes |
| `create_branching_workflow(depth)` | WorkflowSchema | If/Else branching at depth |
| `create_variable_operations_workflow(sets, gets)` | WorkflowSchema | Variable set/get operations |
| `timer` | Timer class | Context manager for timing |

### Presentation Fixtures (tests/presentation/canvas/conftest.py)
| Fixture | Returns | Purpose |
|---------|---------|---------|
| Canvas/widget fixtures | Various | Qt component mocks for visual tests |

---

## How to Run Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Category
```bash
# Domain layer (pure logic, no mocks)
pytest tests/domain/ -v

# Application layer (with mocked infrastructure)
pytest tests/application/ -v

# Node tests (category-specific)
pytest tests/nodes/ -v
pytest tests/nodes/browser/ -v
pytest tests/nodes/desktop/ -v

# Integration tests (real context + mocked I/O)
pytest tests/integration/ -v

# Performance benchmarks
pytest tests/performance/ -v --benchmark-only
```

### Run Specific Test
```bash
pytest tests/nodes/browser/test_navigate_node.py::test_navigate_success -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=casare_rpa --cov-report=term --cov-report=html
```

### Run with Markers
```bash
# Skip slow/integration tests
pytest tests/ -v -m "not slow"

# Only integration tests
pytest tests/ -v -m "integration"

# Only E2E tests
pytest tests/ -v -m "e2e"
```

### Debug Options
```bash
# Show print statements and log output
pytest tests/path/test_file.py -v -s

# Stop on first failure
pytest tests/ -x

# Drop into pdb on failure
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l

# Verbose output with all details
pytest tests/ -vv
```

---

## Example Usage Patterns

### Writing Domain Tests (no mocks)
```python
# tests/domain/entities/test_workflow.py
from casare_rpa.domain.entities.workflow import Workflow
from casare_rpa.domain.value_objects.types import NodeId

class TestWorkflow:
    def test_add_node_success(self):
        workflow = Workflow(name="test", description="")
        node = Node(id=NodeId("node1"), type="start")

        workflow.add_node(node)

        assert len(workflow.nodes) == 1
```

### Writing Application Tests (mocked infrastructure)
```python
# tests/application/use_cases/test_execute_workflow.py
import pytest

@pytest.mark.asyncio
async def test_execute_workflow(mocker):
    mock_repo = mocker.AsyncMock(spec=WorkflowRepository)
    mock_repo.get_by_id.return_value = Workflow(name="test")

    orchestrator = ExecutionOrchestrator(repository=mock_repo)
    result = await orchestrator.execute(workflow_id=WorkflowId("wf1"))

    assert result.status == ExecutionStatus.COMPLETED
    mock_repo.save_execution.assert_awaited_once()
```

### Writing Node Tests (category-specific fixtures)
```python
# tests/nodes/browser/test_click_element_node.py
import pytest

@pytest.mark.asyncio
async def test_click_element_success(execution_context, mock_page):
    node = ClickElementNode(selector="#btn", timeout=5000)
    mock_element = AsyncMock()
    mock_page.query_selector.return_value = mock_element
    execution_context.resources["page"] = mock_page

    result = await node.execute(execution_context)

    assert result["success"] is True
    mock_element.click.assert_awaited_once()
```

### Writing Chain/Integration Tests
```python
# tests/integration/test_workflow_chain.py
import pytest

@pytest.mark.asyncio
async def test_set_and_get_variable_chain(workflow_builder, chain_executor):
    workflow = (
        workflow_builder
        .add(StartNode("start"))
        .add(SetVariableNode("set_x", config={"name": "x", "value": 10}))
        .add(GetVariableNode("get_x", config={"name": "x"}))
        .add(EndNode("end"))
        .connect_sequential()
        .build()
    )

    result = await chain_executor.execute(workflow)

    assert result.success
    assert result.final_variables["x"] == 10
```

### Writing Performance Tests
```python
# tests/performance/test_execution_speed.py
import pytest

@pytest.mark.slow
def test_linear_chain_100_nodes(benchmark):
    workflow = create_linear_chain(100)
    orchestrator = ExecutionOrchestrator()

    result = benchmark(orchestrator.execute, workflow)

    assert result.status == ExecutionStatus.COMPLETED
```

---

## Next Steps

1. **Write Domain Layer Tests** (no mocks needed)
   - Entity behavior tests
   - Value object validation tests
   - Service orchestration tests
   - Target: 90%+ coverage

2. **Write Application Layer Tests** (mock infrastructure)
   - Use case execution tests
   - Error handling tests
   - Transaction coordination tests
   - Target: 85%+ coverage

3. **Write Node Category Tests** (use category fixtures)
   - Browser nodes: Navigate, Click, FillText, etc.
   - Desktop nodes: FindWindow, Click, TypeText, etc.
   - Control flow: If, Loop, Switch, etc.
   - Variable nodes: Set, Get, Calculate, etc.
   - Target: 80%+ coverage

4. **Write Integration Tests** (real context + mocked I/O)
   - Multi-node workflow execution
   - Data flow between connected nodes
   - Error propagation and recovery
   - Resource cleanup on completion
   - Use `workflow_builder` + `chain_executor`

5. **Add Performance Benchmarks**
   - Linear workflow execution time
   - Branching workflow branching overhead
   - Variable operations throughput
   - Memory usage under load
   - Use workflow generators from `performance/conftest.py`

6. **Presentation Layer Tests** (minimal, Qt complexity)
   - Canvas controller logic
   - Event handling
   - Save/load operations
   - Target: 50%+ coverage (Qt UI is hard to test)

---

## Key Design Principles

### Fixture Organization
- **Global** (`tests/conftest.py`): Used by 3+ tests across categories
- **Category** (`tests/nodes/*/conftest.py`): Specific to browser/desktop/etc.
- **Test-file-local**: Fixtures used by only 1-2 tests in a file

### Mocking Strategy
- **Always mock**: Playwright, UIAutomation, win32, HTTP, DB, file I/O, subprocess
- **Prefer real**: Domain entities, VOs, pure logic
- **Context-dependent**: ExecutionContext (real for integration, mock for unit)

### Test Isolation
- Each test is independent (order doesn't matter)
- No shared state between tests
- Fixtures create fresh instances per test
- Mocks automatically reset between tests

### Async Testing
- Mark async tests with `@pytest.mark.asyncio`
- Use `AsyncMock()` for async functions, `Mock()` for sync
- Assert with `assert_awaited_once()` for async calls

---

## File Locations

All testing infrastructure files:

| File | Lines | Purpose |
|------|-------|---------|
| `tests/conftest.py` | ~120 | Global fixtures: execution_context variants |
| `tests/nodes/conftest.py` | ~100 | HTTP helpers: create_mock_response, create_mock_session |
| `tests/nodes/browser/conftest.py` | 181 | Browser fixtures: mock_page, mock_browser |
| `tests/nodes/desktop/conftest.py` | 495 | Desktop fixtures: MockUIControl, mock_win32 |
| `tests/nodes/chain/conftest.py` | 850 | Chain testing: WorkflowBuilder, ChainExecutor |
| `tests/performance/conftest.py` | 240 | Perf fixtures: workflow generators, timer |
| `tests/integration/conftest.py` | 331 | Real context + integration helpers |
| `tests/desktop/managers/conftest.py` | TBD | Desktop manager mocks |
| `tests/presentation/canvas/conftest.py` | TBD | Canvas/Qt fixtures |
| `tests/robot/conftest.py` | TBD | Robot runner fixtures |
| `tests/infrastructure/observability/conftest.py` | TBD | Observability fixtures |

**Total testing infrastructure**: 3,691 lines of fixtures and utilities

---

## Notes for Test Writers

### When to Use Each Fixture

| Scenario | Fixture | Example |
|----------|---------|---------|
| Generic node test | `execution_context` | Testing variable storage, basic logic |
| Node with initial variables | `execution_context_with_variables` | Testing defaults, fallbacks |
| Browser node test | `mock_page` + `mock_browser` | Playwright Click, Navigate, etc. |
| Desktop node test | `MockUIControl` + `mock_win32` | UIAutomation FindWindow, etc. |
| HTTP node test | `create_mock_response()` | REST GET/POST requests |
| Multi-node workflow | `workflow_builder` + `chain_executor` | Integration testing |
| Performance testing | `create_linear_chain(n)` | Speed benchmarks |

### Common Pitfalls to Avoid

1. **Don't use Mock for async functions**
   - Wrong: `mock_repo = Mock()` then `await mock_repo.save()`
   - Right: `mock_repo = AsyncMock()` then `await mock_repo.save()`

2. **Don't test internal implementation**
   - Wrong: `assert workflow._nodes_dict["node1"] is not None`
   - Right: `assert len(workflow.nodes) == 1`

3. **Don't sleep in async tests**
   - Wrong: `await asyncio.sleep(1)`
   - Right: Use condition waits or signal-based timing

4. **Don't share state between tests**
   - Wrong: Test A sets global variable, Test B relies on it
   - Right: Each test uses fixtures to create fresh instances

5. **Don't mock too much in integration tests**
   - Wrong: Mock both WorkflowRepository AND ExecutionOrchestrator
   - Right: Mock only external I/O (files, HTTP, subprocess)

---

## Status Summary

- **Infrastructure**: COMPLETE
- **Global Fixtures**: COMPLETE
- **Node Category Fixtures**: COMPLETE
- **Chain Testing API**: COMPLETE
- **Performance Benchmarking**: COMPLETE
- **Integration Testing**: COMPLETE

All fixtures are tested and documented. Ready for test development across all layers.
