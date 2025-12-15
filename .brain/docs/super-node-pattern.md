# Super Node Pattern

Super Nodes are consolidated action-based nodes that replace multiple atomic nodes with a single configurable node. They provide dynamic port management and conditional widget visibility based on action selection.

## Overview

### What Are Super Nodes?

A Super Node consolidates multiple related operations into a single node with an action dropdown. When the user selects an action:

1. **Ports change** - Input/output ports are dynamically added/removed
2. **Widgets change** - Properties panel shows only relevant fields

**Benefits:**
- Reduces node palette clutter (12 file operations become 1 node)
- Provides consistent UX across related operations
- Simplifies workflow canvas (fewer nodes, cleaner connections)

### Architecture

Super Nodes span three layers:

| Layer | Component | Purpose |
|-------|-----------|---------|
| Domain | `DynamicPortSchema`, `ActionPortConfig`, `PortDef` | Define port configurations per action |
| Domain | Node class with `@properties` decorator | Define conditional properties via `display_when` |
| Presentation | `SuperNodeMixin` | Handle dynamic port/widget management |
| Presentation | Visual node class | Bridge domain node to canvas |

## Key Components

### 1. DynamicPortSchema (Domain Layer)

Defines which ports should exist for each action.

**Location:** `src/casare_rpa/domain/value_objects/dynamic_port_config.py`

```python
from casare_rpa.domain.value_objects.dynamic_port_config import (
    PortDef,
    ActionPortConfig,
    DynamicPortSchema,
)
from casare_rpa.domain.value_objects.types import DataType

# Create schema
MY_PORT_SCHEMA = DynamicPortSchema()

# Register port config for "Read" action
MY_PORT_SCHEMA.register(
    "Read",
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("content", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Register port config for "Write" action
MY_PORT_SCHEMA.register(
    "Write",
    ActionPortConfig.create(
        inputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("content", DataType.STRING),
        ],
        outputs=[
            PortDef("bytes_written", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)
```

**Classes:**

| Class | Purpose |
|-------|---------|
| `PortDef` | Single port definition (name, data_type, required, label) |
| `ActionPortConfig` | Collection of inputs/outputs for one action |
| `DynamicPortSchema` | Registry mapping action names to configs |

### 2. PropertyDef display_when/hidden_when (Domain Layer)

Controls widget visibility based on current configuration.

**Location:** `src/casare_rpa/domain/schemas/property_schema.py`

```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType

# Define actions that need specific properties
READ_ACTIONS = ["Read File"]
WRITE_ACTIONS = ["Write File", "Append File"]

@node(category="file")
@properties(
    # Action selector (always visible, essential)
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default="Read File",
        choices=["Read File", "Write File", "Append File"],
        essential=True,
        order=0,
    ),
    # Only show for read action
    PropertyDef(
        "max_size",
        PropertyType.INTEGER,
        default=0,
        label="Max Size (bytes)",
        order=10,
        display_when={"action": READ_ACTIONS},  # Show when action is in list
    ),
    # Only show for write actions
    PropertyDef(
        "content",
        PropertyType.TEXT,
        label="Content",
        order=20,
        display_when={"action": WRITE_ACTIONS},
    ),
    # Hide for specific action (inverse of display_when)
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        order=30,
        hidden_when={"action": ["Binary Read"]},  # Hide when action matches
    ),
)
class MySuperNode(BaseNode):
    pass
```

**PropertyDef Fields for Conditional Display:**

| Field | Type | Purpose |
|-------|------|---------|
| `display_when` | `Dict[str, Any]` | Show only when other properties match these values |
| `hidden_when` | `Dict[str, Any]` | Hide when other properties match these values |
| `essential` | `bool` | If True, visible when node is collapsed |
| `order` | `int` | Sort order (lower = displayed first) |

**Condition Evaluation:**
- `display_when`: ALL conditions must match for property to show
- `hidden_when`: ANY condition match hides the property
- Values can be single items or lists (list = any match)

### 3. SuperNodeMixin (Presentation Layer)

Handles dynamic port management and widget filtering.

**Location:** `src/casare_rpa/presentation/canvas/visual_nodes/mixins/super_node_mixin.py`

```python
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
    SuperNodeMixin,
)

class VisualMySuperNode(SuperNodeMixin, VisualNode):
    """Visual representation with dynamic ports."""

    __identifier__ = "casare_rpa.mypackage"
    NODE_NAME = "My Super Node"
    NODE_CATEGORY = "mypackage/super"
    CASARE_NODE_CLASS = "MySuperNode"

    # Link to domain port schema
    DYNAMIC_PORT_SCHEMA = MY_PORT_SCHEMA

    def __init__(self) -> None:
        super().__init__()
        self.set_port_deletion_allowed(True)  # Required for dynamic ports

    def get_node_class(self) -> type:
        """Return the domain node class."""
        return MySuperNode

    def setup_ports(self) -> None:
        """Setup initial ports (default action)."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        # Default ports for first action
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_output("content", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)

    def setup_widgets(self) -> None:
        """Setup widgets and connect action listener."""
        super().setup_widgets()
        self._setup_action_listener()  # From SuperNodeMixin
```

**SuperNodeMixin Methods:**

| Method | Purpose |
|--------|---------|
| `_setup_action_listener()` | Connect action dropdown to port refresh |
| `_on_action_changed(action)` | Handle action change - refresh ports and widgets |
| `_clear_dynamic_ports()` | Remove all non-exec ports |
| `_create_ports_from_config(config)` | Create ports from ActionPortConfig |
| `_filter_widgets_for_action(action)` | Show/hide widgets based on display_when |
| `get_current_action()` | Get currently selected action string |

## Step-by-Step Guide: Creating a New Super Node

### Step 1: Define Actions Enum

```python
# src/casare_rpa/nodes/mypackage/super_node.py

from enum import Enum

class MyAction(str, Enum):
    """Actions available in MySuperNode."""
    READ = "Read Data"
    WRITE = "Write Data"
    DELETE = "Delete Data"
```

### Step 2: Create Port Schema

```python
from casare_rpa.domain.value_objects.dynamic_port_config import (
    PortDef, ActionPortConfig, DynamicPortSchema,
)
from casare_rpa.domain.value_objects.types import DataType

MY_PORT_SCHEMA = DynamicPortSchema()

MY_PORT_SCHEMA.register(
    MyAction.READ.value,
    ActionPortConfig.create(
        inputs=[PortDef("path", DataType.STRING)],
        outputs=[
            PortDef("data", DataType.ANY),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

MY_PORT_SCHEMA.register(
    MyAction.WRITE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("path", DataType.STRING),
            PortDef("data", DataType.ANY),
        ],
        outputs=[PortDef("success", DataType.BOOLEAN)],
    ),
)

MY_PORT_SCHEMA.register(
    MyAction.DELETE.value,
    ActionPortConfig.create(
        inputs=[PortDef("path", DataType.STRING)],
        outputs=[PortDef("success", DataType.BOOLEAN)],
    ),
)
```

### Step 3: Define Action Lists for display_when

```python
# Actions that need 'path' input
PATH_ACTIONS = [a.value for a in MyAction]  # All actions

# Actions that need 'data' input
DATA_INPUT_ACTIONS = [MyAction.WRITE.value]

# Actions that support validation
VALIDATION_ACTIONS = [MyAction.WRITE.value, MyAction.READ.value]
```

### Step 4: Create Domain Node with @properties

```python
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import NodeStatus, DataType, ExecutionResult

@node(category="mypackage")
@properties(
    # ESSENTIAL: Action selector (always visible)
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=MyAction.READ.value,
        label="Action",
        tooltip="Operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in MyAction],
    ),
    # Path input (all actions)
    PropertyDef(
        "path",
        PropertyType.STRING,
        label="Path",
        order=10,
        display_when={"action": PATH_ACTIONS},
    ),
    # Data input (write only)
    PropertyDef(
        "data",
        PropertyType.JSON,
        label="Data",
        order=20,
        display_when={"action": DATA_INPUT_ACTIONS},
    ),
    # Validation option (read/write only)
    PropertyDef(
        "validate",
        PropertyType.BOOLEAN,
        default=True,
        label="Validate",
        order=30,
        display_when={"action": VALIDATION_ACTIONS},
    ),
)
class MySuperNode(BaseNode):
    """Super Node for data operations."""

    def __init__(self, node_id: str, name: str = "My Super", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MySuperNode"

    def _define_ports(self) -> None:
        """Define default ports (overridden by visual layer)."""
        self.add_input_port("path", DataType.STRING)
        self.add_output_port("data", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected action."""
        action = self.get_parameter("action", MyAction.READ.value)

        handlers = {
            MyAction.READ.value: self._execute_read,
            MyAction.WRITE.value: self._execute_write,
            MyAction.DELETE.value: self._execute_delete,
        }

        handler = handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        return await handler(context)

    async def _execute_read(self, context) -> ExecutionResult:
        # Implementation...
        pass

    async def _execute_write(self, context) -> ExecutionResult:
        # Implementation...
        pass

    async def _execute_delete(self, context) -> ExecutionResult:
        # Implementation...
        pass
```

### Step 5: Create Visual Node

```python
# src/casare_rpa/presentation/canvas/visual_nodes/mypackage/super_nodes.py

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
    SuperNodeMixin,
)
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.mypackage.super_node import (
    MySuperNode,
    MyAction,
    MY_PORT_SCHEMA,
)


class VisualMySuperNode(SuperNodeMixin, VisualNode):
    """Visual representation of MySuperNode."""

    __identifier__ = "casare_rpa.mypackage"
    NODE_NAME = "My Super"
    NODE_CATEGORY = "mypackage/super"
    CASARE_NODE_CLASS = "MySuperNode"

    DYNAMIC_PORT_SCHEMA = MY_PORT_SCHEMA

    def __init__(self) -> None:
        super().__init__()
        self.set_port_deletion_allowed(True)

    def get_node_class(self) -> type:
        return MySuperNode

    def setup_ports(self) -> None:
        """Setup ports for default action (Read)."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_input("path", DataType.STRING)
        self.add_typed_output("data", DataType.ANY)
        self.add_typed_output("success", DataType.BOOLEAN)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._setup_action_listener()


__all__ = ["VisualMySuperNode"]
```

### Step 6: Register the Nodes

**Domain node registry** (`src/casare_rpa/nodes/__init__.py`):
```python
_NODE_REGISTRY = {
    # ... existing nodes ...
    "MySuperNode": "mypackage.super_node",
}
```

**Visual node registry** (`src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`):
```python
_VISUAL_NODE_REGISTRY = {
    # ... existing nodes ...
    "VisualMySuperNode": "mypackage.super_nodes",
}
```

## Existing Super Nodes

### FileSystemSuperNode

**Location:** `src/casare_rpa/nodes/file/super_node.py`

**Actions (12):**
- Read File, Write File, Append File
- Delete File, Copy File, Move File
- File Exists, Get File Size, Get File Info
- Create Directory, List Files, List Directory

### StructuredDataSuperNode

**Location:** `src/casare_rpa/nodes/file/super_node.py`

**Actions (7):**
- Read CSV, Write CSV
- Read JSON, Write JSON
- Zip Files, Unzip Files
- Image Convert

## Best Practices

1. **Essential action property**: Always mark the action dropdown as `essential=True` so it remains visible when collapsed

2. **Order properties logically**: Use `order` field to group related properties (action=0, inputs=10-19, options=20-29, etc.)

3. **Use action lists**: Define `XXXX_ACTIONS` lists for `display_when` to avoid repeating action names

4. **Default to first action**: Set default ports in `setup_ports()` to match the first action in the dropdown

5. **Enable port deletion**: Call `self.set_port_deletion_allowed(True)` in visual node `__init__`

6. **Handle errors gracefully**: Wrap action handlers in try/except and set output `success` port accordingly

7. **Security validation**: Use path security validation for file operations

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Ports not changing | Missing `_setup_action_listener()` | Call in `setup_widgets()` |
| Widgets not filtering | Schema not found | Ensure node has `__node_schema__` (via @properties) |
| Segfault on action change | Port deletion not allowed | Call `set_port_deletion_allowed(True)` |
| Action widget not found | `setup_widgets()` called before widgets exist | Mixin uses QTimer.singleShot to defer |

## Related Documentation

- [Node Development Guide](.brain/docs/node-templates.md)
- [PropertyDef Reference](../../../src/casare_rpa/domain/schemas/property_schema.py)
- [DynamicPortConfig](../../../src/casare_rpa/domain/value_objects/dynamic_port_config.py)
- [SuperNodeMixin](../../../src/casare_rpa/presentation/canvas/visual_nodes/mixins/super_node_mixin.py)
