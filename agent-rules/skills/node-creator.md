# Node Creator Skill

Complete workflow for creating new automation nodes.

## Node Anatomy

```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult, NodeStatus

@properties(
    PropertyDef(
        "input_value",
        PropertyType.STRING,
        required=True,
        label="Input Value"
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        label="Timeout (s)"
    ),
)
@node(category="my_category")
class MyCustomNode(BaseNode):
    """Node description for AI and documentation."""

    def __init__(self, node_id: str, name: str = "My Custom Node", **kwargs) -> None:
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "MyCustomNode"

    def _define_ports(self) -> None:
        # Execution flow is handled by BaseNode implicitly or explicitly
        # Data ports:
        self.add_input_port("data_in", DataType.ANY)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            # 1. Get raw value from port or config
            raw_input = self.get_parameter("input_value")

            # 2. RESOLVE TEMPLATES (CRITICAL)
            # This ensures {{node.port}} syntax works in your node
            input_val = context.resolve_value(raw_input)

            # ... implementation ...

            self.set_output_value("result", f"Processed: {input_val}")
            return self.success_result({"success": True})
        except Exception as e:
            return self.error_result(e)
```

## Property Types

| Type | Python | Use Case |
|:---|:---|:---|
| `STRING` | str | Text input |
| `INTEGER` | int | Numbers |
| `BOOLEAN` | bool | Flags |
| `FLOAT` | float | Decimals |
| `CODE` | str | Code editor |
| `SELECTOR` | str | CSS/XPath selector |
| `CHOICE` | str | Dropdown selection |

## Visual Node (UI)

Visual nodes are now separate from backend nodes.

```python
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType

class VisualMyCustomNode(VisualNode):
    __identifier__ = "casare_rpa.my_category"
    NODE_NAME = "My Custom Node"
    NODE_CATEGORY = "my_category/sub_category"
    CASARE_NODE_CLASS = "MyCustomNode"  # Must match backend class name

    def __init__(self) -> None:
        super().__init__()
        # Widgets are auto-generated from @properties by default

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("data_in", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
```

## Registration (CRITICAL)

You must register both the backend and visual nodes in their respective registries.

1. **Backend Registry:** `src/casare_rpa/nodes/registry_data.py`
2. **Visual Registry:** `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`

## File Locations

| Layer | Path |
|:---|:---|
| Backend Node | `src/casare_rpa/nodes/{category}/` |
| Backend Registry | `src/casare_rpa/nodes/registry_data.py` |
| Visual Node | `src/casare_rpa/presentation/canvas/visual_nodes/{category}/` |
| Visual Registry | `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py` |
| Tests | `tests/nodes/test_{node_name}.py` |

## Checklist

- [ ] Backend node with `@node` and `@properties`
- [ ] Ports defined in `_define_ports`
- [ ] Async `execute` method
- [ ] Backend node registered in `registry_data.py`
- [ ] Visual node class inheriting `VisualNode`
- [ ] Visual ports match backend ports
- [ ] Visual node registered in `visual_nodes/__init__.py`
- [ ] Unit tests
