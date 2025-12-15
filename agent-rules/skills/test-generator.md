# Test Generator Skill

Generate tests for code automatically.

## Usage
Invoke when writing tests for new or existing code.

## Template
```python
import pytest
from casare_rpa.nodes import {NodeName}

@pytest.fixture
def node():
    return {NodeName}("test-id")

@pytest.mark.asyncio
async def test_{node_name}_success(node, execution_context):
    """Test successful execution."""
    node.set_property("input", "valid_value")
    result = await node.execute(execution_context)
    assert result["success"] is True

@pytest.mark.asyncio
async def test_{node_name}_invalid_input(node, execution_context):
    """Test error handling."""
    node.set_property("input", "")
    with pytest.raises(ValueError):
        await node.execute(execution_context)

@pytest.mark.asyncio
async def test_{node_name}_edge_case(node, execution_context):
    """Test edge cases."""
    # Test boundary conditions
    pass
```

## Best Practices
- Use fixtures from `conftest.py`
- Test happy path first
- Cover error cases
- Test edge cases
