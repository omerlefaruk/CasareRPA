# Example Tests - Learning by Doing

These tests serve as **executable documentation** for AI agents and developers.

## Quick Start

```bash
# See all available examples
pytest tests/examples/ --collect-only

# Run all examples with verbose output
pytest tests/examples/ -v

# Run specific example
pytest tests/examples/test_node_creation_example.py -v
```

## Available Examples

| File | Topic | Key Concepts |
|------|-------|--------------|
| `test_node_creation_example.py` | Creating new nodes | @node, @properties, ports, execute(), 3-scenario testing |
| `test_event_handling_example.py` | Event system | DomainEvent, EventBus, pub/sub, handlers |

## How to Use These Examples

### For AI Agents

1. **Read the file header** - Contains AI-HINT and AI-CONTEXT markers
2. **Copy the pattern** - Each file is designed to be copied and adapted
3. **Follow the STEP comments** - Numbered steps guide you through the process
4. **Check the USAGE NOTES** - End of each file has quick reference

### For New Developers

1. Run the tests to see them work
2. Read the code comments
3. Modify and re-run to experiment
4. Copy to your actual test file when ready

## Pattern Reference

### 3-Scenario Test Pattern

Every node should have at least three test types:

```python
class TestMyNode:
    async def test_success_scenario(self):
        """Normal operation with valid input."""
        ...

    async def test_error_scenario(self):
        """How the node handles errors."""
        ...

    async def test_edge_case_scenario(self):
        """Boundary conditions (empty, null, limits)."""
        ...
```

### Event Handler Pattern

```python
@pytest.fixture
def event_bus():
    reset_event_bus()  # Clean slate
    return get_event_bus()

def test_event_flow(event_bus):
    results = []
    event_bus.subscribe(MyEvent, lambda e: results.append(e))
    event_bus.publish(MyEvent(...))
    assert len(results) == 1
```

### Mock Resource Pattern

```python
@pytest.fixture
def mock_page():
    """For browser nodes."""
    page = AsyncMock()
    page.query_selector = AsyncMock(return_value=element)
    return page

@pytest.fixture
def execution_context(mock_page):
    context = MagicMock()
    context.resources = {"page": mock_page}
    return context
```

## Adding New Examples

When adding a new example:

1. Create `test_{topic}_example.py`
2. Add header with AI-HINT and AI-CONTEXT
3. Use numbered STEP comments
4. Include working test code
5. Add USAGE NOTES at the end
6. Update this README

## Related Documentation

- `.brain/decisions/add-node.md` - Full node creation guide
- `.brain/decisions/fix-bug.md` - Debugging guide
- `.brain/systemPatterns.md` - Architecture patterns
- `.brain/errors.md` - Error codes and handling
