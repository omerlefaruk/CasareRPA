---
paths:
  - tests/**/*.py
---

# Testing Standards

## Test Framework

Use pytest with fixtures from `tests/conftest.py`.

## Test Organization

| Layer | Strategy | Location |
|-------|----------|----------|
| Domain | No mocks - pure logic | `tests/domain/` |
| Application | Mock infrastructure | `tests/application/` |
| Infrastructure | Mock external services | `tests/infrastructure/` |
| Presentation | Mock heavy Qt pieces | `tests/presentation/` |

## Domain Tests (Pure Logic)

```python
# No external dependencies - test business logic directly
def test_workflow_add_node():
    workflow = Workflow(id=WorkflowId.generate(), name="Test")
    node_id = workflow.add_node("ClickNode", Position(100, 200))
    assert node_id is not None
    events = workflow.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], NodeAdded)
```

## Node Tests

```python
@pytest.fixture
def node():
    return ClickElementNode()

@pytest.mark.asyncio
async def test_execute_success(node, mock_page):
    result = await node.execute(mock_context)
    assert result["success"] is True
```

## Headless Qt Testing

`QT_QPA_PLATFORM=offscreen` is set in `tests/conftest.py` for CI/headless runs.

## Async Tests

Use `@pytest.mark.asyncio` for async test functions.

## Fixtures

Key fixtures in `tests/conftest.py`:
- `mock_page` - Playwright page mock
- `mock_context` - Execution context mock
- `event_bus` - EventBus instance

## Coverage

Run: `pytest tests/ --cov=src/casare_rpa --cov-report=html`

## References

- `.brain/systemPatterns.md` - Domain test patterns
- `.brain/projectRules.md` - Testing standards
- `docs/developer-guide/contributing/testing.md` - Full guide
