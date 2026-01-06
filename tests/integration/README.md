# Integration Tests (Desktop)

High-level integration tests for CasareRPA that validate core end-to-end behavior across real modules.

## Purpose

These tests fill the gap between unit tests (fast, mocked) and manual testing. They validate:

- **Persistence + File I/O**: JSON save/load, project storage, index management
- **Use Case Orchestration**: Real use cases with real repositories
- **State Transitions**: Workflow lifecycle, variable resolution
- **Error Recovery**: Invalid inputs, missing files, corrupt data

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/ -v -m integration

# Run specific test file
pytest tests/integration/test_project_lifecycle.py -v

# Run with coverage
pytest tests/integration/ -v -m integration --cov=src/casare_rpa --cov-report=html

# Run in parallel (pytest-xdist)
pytest tests/integration/ -v -m integration -n auto

# Run with verbose output
pytest tests/integration/ -vvs -m integration
```

## CI Configuration

These tests are designed to run in CI environments:

- **Fast**: Target < 2-4 minutes for full suite
- **Deterministic**: No flaky timing, no sleep() waits
- **Isolated**: All file I/O redirected to temp directories
- **Headless**: Qt runs in offscreen mode (`QT_QPA_PLATFORM=offscreen`)

```yaml
# Example GitHub Actions step
- name: Run integration tests
  run: |
    pytest tests/integration/ -v -m integration --tb=short
```

## Test Structure

```
tests/integration/
├── __init__.py                    # Package init
├── conftest.py                     # Shared fixtures (sandbox, repos)
├── test_project_lifecycle.py      # Project CRUD operations
├── test_workflow_serialization.py # Workflow save/load roundtrip
├── test_variable_resolution.py    # Variable scopes and resolution
├── test_project_index.py          # Projects index management
├── test_workflow_validation.py    # Workflow validation rules
├── test_unit_of_work_events.py    # Domain events & UoW
└── test_simple_execution.py       # Basic node execution (no external deps)
```

## Fixtures

### `integration_sandbox`
Isolated temporary directory for test file operations.

### `sandbox_config`
Dictionary with sandboxed path constants (projects_dir, workflows_dir, etc.).

### `sandbox_project_repository`
Real `FileSystemProjectRepository` with sandboxed storage.

### `fresh_event_bus`
Clean `EventBus` instance for each test (no event leakage).

### `sample_workflow` / `sample_project`
Factory functions for test data.

## Writing New Tests

1. **Use `@pytest.mark.integration` decorator**
2. **Accept sandbox fixtures** for file I/O
3. **Use real modules** (no mocks unless testing external boundaries)
4. **Test both success and error paths**
5. **Clean up resources** (tmp_path handles this automatically)

Example:

```python
import pytest
from casare_rpa.application.use_cases import CreateProjectUseCase

@pytest.mark.integration
@pytest.mark.asyncio
async def test_my_feature(sandbox_config):
    # Arrange: Set up test data
    use_case = CreateProjectUseCase(repository)

    # Act: Execute the feature
    result = await use_case.execute(name="Test", path=test_path)

    # Assert: Verify results
    assert result.success is True
    assert (test_path / "project.json").exists()
```

## External Boundaries (What to Mock)

| Boundary | Strategy |
|----------|----------|
| OS file dialogs | Use direct file paths (no dialogs in tests) |
| Network requests | Skip or use adapter-level mocks |
| Browser (Playwright) | Skip `@pytest.mark.browser` tests |
| Paid APIs | Never call in integration tests |

## Test Coverage Goals

| Area | Target |
|------|--------|
| Project CRUD | 100% |
| Workflow I/O | 100% |
| Variable resolution | 90%+ |
| Validation rules | 80%+ |
| Domain events | 90%+ |
| Simple execution | 80%+ |
