# Node Development Workflow

## Overview
Creating nodes follows a strict Plan → Search → Implement workflow.

## Phase 1: PLAN
Define the node's atomic operation:
- **One node = One responsibility**
- Clear inputs and outputs
- Define error cases

## Phase 2: SEARCH
Before creating new nodes:
1. Check `nodes/_index.md` for existing nodes
2. Search `_NODE_REGISTRY` in `nodes/__init__.py`
3. Look for similar patterns in existing nodes

**Priority:**
1. Use existing node → Done
2. Modify existing node → Minimal change
3. Create new node → Last resort

## Phase 3: IMPLEMENT

### File Location
| Category | Directory |
|----------|-----------|
| Browser | `nodes/browser/` |
| Desktop | `nodes/desktop_nodes/` |
| Data | `nodes/data/` |
| Control Flow | `nodes/control_flow/` |
| System | `nodes/system/` |

### Required Components
1. Node class extending `BaseNode`
2. `@executable_node` decorator
3. `@node_schema` with properties
4. Tests in `tests/nodes/`

### Template
```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
    PropertyDef("input", PropertyType.STRING, essential=True),
)
@executable_node
class MyNode(BaseNode):
    """One-line description."""

    NODE_NAME = "My Node"

    async def execute(self, context):
        # Implementation
        return {"result": "value"}
```

## Phase 4: REGISTER
Add to `_NODE_REGISTRY` in `nodes/__init__.py`:
```python
"MyNode": "my_module",
```

## Phase 5: TEST
Create tests in `tests/nodes/`:
```python
@pytest.mark.asyncio
async def test_my_node(execution_context):
    node = MyNode("test-id")
    result = await node.execute(execution_context)
    assert result["result"] == "value"
```
