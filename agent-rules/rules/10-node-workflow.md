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
2. `@node(category="category")` decorator
3. `@properties` with property definitions
4. Tests in `tests/nodes/`

### Template
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("input", PropertyType.STRING, required=True),
)
@node(category="my_category")
class MyNode(BaseNode):
    """One-line description."""

    async def execute(self, context):
        # 1. Get raw parameter
        raw_val = self.get_parameter("input")

        # 2. Resolve templates (MANDATORY)
        val = context.resolve_value(raw_val)

        # 3. Implementation
        return self.success_result({"result": f"Processed {val}"})
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
