# Node Registration Checklist

Complete these 8 steps when adding a new node to CasareRPA.

## Step 1: Create Node Implementation

File: `src/casare_rpa/nodes/{category}/{node_name}_node.py`

- Use `@properties()` decorator (required, even if empty)
- Use `get_parameter()` for optional properties
- Use `add_exec_input()/add_exec_output()` for flow ports
- Use `add_input_port(name, DataType.X)` for data ports
- Include proper error handling with loguru

## Step 2: Create Visual Node Wrapper

File: `src/casare_rpa/presentation/canvas/visual_nodes/{category}/{node_name}_visual.py`

```python
from NodeGraphQt import BaseNode as GraphNode
from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node

class Visual{NodeName}Node(GraphNode):
    """Visual wrapper for {NodeName}Node."""
    __identifier__ = 'casare_rpa'
    NODE_NAME = '{Node Display Name}'

    def __init__(self):
        super().__init__()
        self.logic_node = {NodeName}Node()
        # Create visual ports matching logic node
```

## Step 3: Export from Category Module

File: `src/casare_rpa/nodes/{category}/__init__.py`

```python
from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node

__all__ = ['{NodeName}Node', ...]
```

## Step 4: Register in NODE_REGISTRY

File: `src/casare_rpa/nodes/registry_data.py`

```python
NODE_REGISTRY = {
    ...
    '{node_id}': {
        'class': {NodeName}Node,
        'name': '{Node Display Name}',
        'category': '{category}',
    },
    ...
}
```

## Step 5: Add to NODE_TYPE_MAP

File: `src/casare_rpa/utils/workflow/workflow_loader.py`

```python
NODE_TYPE_MAP = {
    ...
    '{node_id}': {NodeName}Node,
    ...
}
```

## Step 6: Register Visual Node

File: `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`

```python
from .{category}.{node_name}_visual import Visual{NodeName}Node

# Register in NODE_CLASSES or import in module
```

## Step 7: Create Tests

File: `tests/nodes/{category}/test_{node_name}_node.py`

- Use pytest fixtures for node and mock_context
- Test initialization, ports, success/failure paths
- Mock external resources (browser, desktop)
- Minimum 10 tests recommended

## Step 8: Update Documentation

- Update category _index.md with new node
- Add example usage if needed
- Run `python scripts/sync_agent_guides.py` if patterns changed

## Verification

```bash
# Verify node loads
python -c "from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node; print('OK')"

# Run tests
pytest tests/nodes/{category}/test_{node_name}_node.py -v

# Verify registry
python -c "from casare_rpa.nodes.registry_data import NODE_REGISTRY; print('{node_id}' in NODE_REGISTRY)"
```
