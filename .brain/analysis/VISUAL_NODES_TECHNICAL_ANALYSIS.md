# Visual Nodes Technical Analysis

**Deep technical dive into visual node architecture, patterns, and implementation details.**

---

## Architecture Overview

### Three-Layer Visual Node System

```
┌─────────────────────────────────────────────────────────┐
│         Presentation Layer (Canvas UI)                  │
│  NodeGraphQt Graphics Items, Visual Rendering           │
└──────────────────┬──────────────────────────────────────┘
                   │ Uses
┌──────────────────▼──────────────────────────────────────┐
│         Visual Node Layer (presentation/)               │
│  VisualNode Classes, Port Setup, Widget Management      │
│  424 node implementations across 21 categories          │
└──────────────────┬──────────────────────────────────────┘
                   │ Maps to
┌──────────────────▼──────────────────────────────────────┐
│         Logic Node Layer (domain + nodes/)              │
│  BaseNode Classes, Execution Logic, Schema Definition   │
│  435 nodes with @properties and @node decorators        │
└─────────────────────────────────────────────────────────┘
```

### Class Hierarchy

```
NodeGraphQt.BaseNode
    │
    └── VisualNode (base_visual_node.py)
            │
            ├── [Regular Visual Nodes] (27 categories)
            │   ├── VisualLaunchBrowserNode
            │   ├── VisualClickElementNode
            │   ├── VisualIfNode
            │   └── ... (421 more)
            │
            └── SuperNodeMixin (for dynamic ports)
                    │
                    ├── VisualFileSystemSuperNode
                    ├── VisualStructuredDataSuperNode
                    ├── VisualWindowSuperNode
                    └── VisualTextSuperNode
```

---

## Visual Node Base Class

### VisualNode Core (base_visual_node.py)

**Location:** `src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py`
**Lines:** ~1222
**Key Responsibility:** Bridge between NodeGraphQt and CasareRPA domain

#### Class Attributes (Required)

```python
class VisualNode(NodeGraphQtBaseNode):
    __identifier__: str = "casare_rpa"           # Package identifier
    NODE_NAME: str = "Visual Node"               # Display name
    NODE_CATEGORY: str = "basic"                 # Canvas category

    # Class variables for styling
    _collapsed: bool = True                      # Collapsed by default
    UNIFIED_NODE_COLOR = QColor(37, 37, 38)    # VSCode dark theme
```

#### Instance Variables

```python
def __init__(self):
    self._casare_node: Optional[BaseNode]       # Reference to logic node
    self._last_output: Optional[Dict]           # Execution result data
    self._port_types: Dict[str, DataType]      # Port type registry
    self._type_registry: PortTypeRegistry       # Type system
    self._collapsed: bool                        # Collapse state
```

#### Key Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `setup_ports()` | Define exec/data ports | `add_exec_input("exec_in")` |
| `setup_widgets()` | Create custom UI widgets | `add_custom_widget(TextInput)` |
| `_auto_create_widgets_from_schema()` | Generate from `@properties` | Auto-called if schema exists |
| `_apply_category_colors()` | Set node color by category | Maps category to color |
| `set_collapsed()` | Hide non-essential widgets | Performance optimization |
| `toggle_collapse()` | Toggle visibility | User interaction |
| `update_status()` | Visual execution feedback | Green border during run |

#### Port Management

```python
# Execution ports
self.add_exec_input("exec_in")                  # Flow input
self.add_exec_output("exec_out")                # Flow output

# Typed data ports (strong type checking)
self.add_typed_input("url", DataType.STRING)
self.add_typed_output("page", DataType.PAGE)

# Custom widgets
widget = NodeStringLineEdit("name")
self.add_custom_widget(widget)
```

---

## Widget Auto-Generation System

### Decorator-Based Port/Widget Creation

**Flow:**
1. Domain node decorated with `@node` and `@properties`
2. Decorators create `__node_schema__` attribute
3. VisualNode.__init__() detects schema
4. `_auto_create_widgets_from_schema()` generates UI

### Example: LaunchBrowserNode

**Domain Definition:**
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node(category="browser")
@properties(
    PropertyDef("url", PropertyType.STRING, default="https://example.com"),
    PropertyDef("headless", PropertyType.BOOLEAN, default=True),
)
class LaunchBrowserNode(BaseNode):
    async def execute(self, context):
        url = self.properties["url"]
        headless = self.properties["headless"]
        # ... launch logic ...
```

**Visual Representation:**
```python
class VisualLaunchBrowserNode(VisualNode):
    __identifier__ = "casare_rpa.browser"
    NODE_NAME = "Launch Browser"
    NODE_CATEGORY = "browser/launch"

    def __init__(self):
        super().__init__()
        # Widgets auto-generated from @properties above
        # No manual add_custom_widget() needed

    def setup_ports(self):
        # Ports are derived from @properties output schema
        self.add_exec_input("exec_in")
        self.add_typed_input("url", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("browser", DataType.BROWSER)
```

**Result in Canvas:**
- String input widget for URL auto-generated
- Boolean checkbox for headless auto-generated
- Ports match schema automatically

### Manual Widget Handling (5% of nodes)

For nodes without `@properties` or needing custom UI:

```python
class VisualClickElementNode(VisualNode):
    def __init__(self):
        super().__init__()
        # Manual widget creation (necessary for complex UI)
        selector_widget = NodeSelectorWidget("selector")
        self._replace_widget(selector_widget)  # Avoid duplicates

    def setup_ports(self):
        self.add_exec_input("exec_in")
        self.add_typed_input("selector", DataType.SELECTOR)
        self.add_exec_output("exec_out")
```

**Helper Function - _replace_widget:**
```python
def _replace_widget(node: VisualNode, widget) -> None:
    """Replace auto-generated widget with custom one."""
    prop_name = widget._name
    # Remove existing property if auto-generated
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
    # Now safely add custom widget
    node.add_custom_widget(widget)
```

---

## Port Type System

### DataType Enum

**Location:** `domain/value_objects/types.py`

```python
class DataType(Enum):
    # Primitive types
    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"

    # Collections
    LIST = "list"
    DICT = "dict"
    ARRAY = "array"
    TABLE = "table"

    # Domain types
    BROWSER = "browser"
    PAGE = "page"
    ELEMENT = "element"
    SPREADSHEET = "spreadsheet"

    # Control flow
    EXEC_INPUT = "exec_in"
    EXEC_OUTPUT = "exec_out"

    # Special
    DYNAMIC = "dynamic"      # Any type
    ANY = "any"              # Alias for dynamic
    OBJECT = "object"        # Generic object
```

### PortType Enumeration

```python
class PortType(Enum):
    # Input/Output designation
    INPUT = "input"
    OUTPUT = "output"

    # Execution flow
    EXEC_INPUT = "exec_input"
    EXEC_OUTPUT = "exec_output"

    # Combination
    DATA_INPUT = "data_input"
    DATA_OUTPUT = "data_output"
```

### Port Type Registry

**Maintains type information for validation:**

```python
class PortTypeRegistry:
    def get_port_type(port_name: str) -> Optional[DataType]:
        """Look up port's declared type."""

    def validate_connection(source: Port, dest: Port) -> bool:
        """Ensure connection type compatibility."""
        # Returns False if incompatible types
```

---

## Lazy Loading Registry System

### Architecture

**Registry Files:**
- `visual_nodes/__init__.py` - Visual node registry
- `nodes/registry_data.py` - Logic node registry
- `graph/node_registry.py` - Factory and mapping

### _VISUAL_NODE_REGISTRY

**Location:** `visual_nodes/__init__.py`
**Type:** `Dict[str, str]`
**Purpose:** Map visual class name to lazy-load module path

```python
_VISUAL_NODE_REGISTRY: Dict[str, str] = {
    # Basic (3 nodes)
    "VisualStartNode": "basic.nodes",
    "VisualEndNode": "basic.nodes",
    "VisualCommentNode": "basic.nodes",

    # Browser (26 nodes)
    "VisualLaunchBrowserNode": "browser.nodes",
    "VisualClickElementNode": "browser.nodes",
    # ... 424 total entries ...
}
```

### NODE_REGISTRY

**Location:** `nodes/registry_data.py`
**Type:** `Dict[str, Union[str, Tuple[str, str]]]`
**Purpose:** Map logic class name to module path

```python
NODE_REGISTRY: Dict[str, Union[str, Tuple[str, str]]] = {
    # Standard reference
    "LaunchBrowserNode": "browser.lifecycle",

    # With class name alias
    "HttpRequestNodeNew": ("http.http_basic", "HttpRequestNode"),
}
```

### NodeFactory (node_registry.py)

**Key Functions:**

```python
def get_visual_node_class(name: str) -> Type[VisualNode]:
    """Load visual node class on-demand."""
    module_path = _VISUAL_NODE_REGISTRY[name]
    module = importlib.import_module(f"casare_rpa.presentation.canvas.visual_nodes.{module_path}")
    return getattr(module, name)

def create_visual_node_instance(visual_class: Type[VisualNode]) -> VisualNode:
    """Instantiate visual node."""
    return visual_class()

def get_casare_node_mapping() -> Dict[Type[VisualNode], Type[BaseNode]]:
    """Auto-discover visual→logic mapping."""
    # Uses CASARE_NODE_CLASS attribute on visual nodes
    # No manual registry needed!
```

### Caching Strategy

**Disk Cache Location:** `~/.casare_rpa/cache/node_mapping_cache.json`

```python
{
    "version": "1.0",
    "registry_hash": "a1b2c3d4e5f6",  # Detects registry changes
    "mapping": {
        "VisualLaunchBrowserNode": "LaunchBrowserNode",
        "VisualClickElementNode": "ClickElementNode",
        # ... 424 entries ...
    }
}
```

**Invalidation:** When `_get_registry_hash()` detects changes

---

## Super Node Architecture

### SuperNodeMixin

**Location:** `mixins/super_node_mixin.py`
**Purpose:** Enable dynamic port management for action-based nodes

#### Mechanism

1. **Action Selection:** Dropdown widget selects operation
2. **Schema Lookup:** Retrieves port definition from `DynamicPortSchema`
3. **Port Creation:** Dynamically creates ports based on action
4. **Widget Visibility:** Shows/hides fields based on action

#### Class Definition

```python
class SuperNodeMixin:
    """Mixin for nodes with dynamic ports based on action selection."""

    def _on_action_changed(self, new_action: str) -> None:
        """Called when action dropdown changes."""
        # 1. Remove old ports
        self._remove_dynamic_ports()

        # 2. Get schema for new action
        schema = self._get_action_schema(new_action)

        # 3. Create new ports
        for port_def in schema.inputs:
            self.add_typed_input(port_def.name, port_def.type)
        for port_def in schema.outputs:
            self.add_typed_output(port_def.name, port_def.type)

        # 4. Update widget visibility
        self._update_widget_visibility(new_action)
```

### FileSystemSuperNode Example

**Consolidates:** 12 file operations into 1 node

```python
class VisualFileSystemSuperNode(SuperNodeMixin, VisualNode):
    """Dynamic file operations based on action selection."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "File System"
    NODE_CATEGORY = "file_operations"

    # Actions defined in domain node's DynamicPortSchema
    ACTIONS = {
        "read_file": PortSchema(inputs=["path"], outputs=["content"]),
        "write_file": PortSchema(inputs=["path", "content"], outputs=["success"]),
        "append_file": PortSchema(inputs=["path", "content"], outputs=["success"]),
        "delete_file": PortSchema(inputs=["path"], outputs=["success"]),
        "copy_file": PortSchema(inputs=["source", "dest"], outputs=["success"]),
        # ... 7 more actions ...
    }

    def setup_ports(self):
        # SuperNodeMixin handles dynamic port creation
        super().setup_ports()
```

**User Experience:**
- Single node in palette
- Dropdown to select operation
- Ports/widgets update automatically
- Schema-driven (no hardcoding)

---

## Category Organization Patterns

### Standard Single-File Pattern

```
category/
├── __init__.py
│   └── exports: __all__ = [list of visual node classes]
│              _CATEGORY_REGISTRY = {...}
│
└── nodes.py
    ├── DocString: "Visual nodes for [category]"
    ├── Helper Functions (if any)
    ├── class Visual[Name1]Node(VisualNode): ...
    ├── class Visual[Name2]Node(VisualNode): ...
    └── # ... more classes ...
```

**Files Using This Pattern:**
- basic/, browser/, control_flow/, database/, email/
- error_handling/, document/, office_automation/
- rest_api/, scripts/, variable/, workflow/

### Multi-Service Split Pattern (Google)

```
google/
├── __init__.py
│   └── imports and re-exports from all service files
│
├── calendar_nodes.py    (12 nodes)
├── docs_nodes.py        (8 nodes)
├── drive_nodes.py       (17 nodes)
├── gmail_nodes.py       (21 nodes)
└── sheets_nodes.py      (21 nodes)
```

**Advantages:**
- Each file ~300-400 lines (readable)
- Service-aligned organization
- Easy to find specific functionality
- Reduces merge conflicts

### Multi-Type Split Pattern (Messaging)

```
messaging/
├── __init__.py
│
├── nodes.py (4 nodes)
│   └── Common/base nodes
│
├── telegram_action_nodes.py (5 nodes)
│   └── Telegram-specific advanced ops
│
└── whatsapp_nodes.py (7 nodes)
    └── WhatsApp-specific operations
```

**Rationale:** Type-specific behavior separation

### Super Node Pattern

```
category/
├── __init__.py
│   └── imports from both nodes.py and super_nodes.py
│
├── nodes.py (regular atomic nodes)
│   ├── VisualReadFileNode
│   ├── VisualWriteFileNode
│   └── ... ~30 more atomic nodes ...
│
└── super_nodes.py
    ├── VisualFileSystemSuperNode (consolidates 12)
    ├── VisualStructuredDataSuperNode (consolidates 7)
    └── # Future: other super nodes ...
```

---

## Port Naming Conventions

### Execution Ports (Flow Control)

**Standard Names:**
- Input: `exec_in`, `exec_input`, `in`
- Output: `exec_out`, `exec_output`, `out`

**Consistency:** 99% use `exec_in` / `exec_out`

### Data Input Ports

**Parameter Convention:**
```
Single Input:      "input", "data", "param"
Specific Domain:   "url", "selector", "text", "path"
Modifying Input:   "value", "count", "index"
Condition Input:   "condition", "threshold"
Template Input:    "template", "pattern", "format"
```

### Data Output Ports

**Result Convention:**
```
Primary Output:    "output", "result", "data"
Domain-Specific:   "page", "browser", "spreadsheet"
Status Signals:    "success", "found", "exists", "valid"
Count/Size:        "count", "size", "length"
Plural Results:    "items", "rows", "records", "pages"
```

### Example: TableScraperNode

```python
def setup_ports(self):
    self.add_exec_input("exec_in")

    # Inputs
    self.add_typed_input("page", DataType.PAGE)
    self.add_typed_input("selector", DataType.SELECTOR)
    self.add_typed_input("mode", DataType.STRING)

    # Outputs
    self.add_exec_output("exec_out")
    self.add_typed_output("table", DataType.TABLE)      # Primary
    self.add_typed_output("rows", DataType.LIST)        # Plural
    self.add_typed_output("row_count", DataType.INTEGER) # Count
    self.add_typed_output("success", DataType.BOOLEAN)  # Status
```

---

## Performance Optimizations

### Lazy Loading

**Startup Performance:**
- Without lazy loading: Load 424 node classes at startup (~5 seconds)
- With lazy loading: Load 8 essential nodes (~1.5 seconds)
- **Saving:** 3.5 seconds (~70% improvement)

**Essential Nodes (8):**
```python
ESSENTIAL_NODE_NAMES = [
    "VisualStartNode",
    "VisualEndNode",
    "VisualCommentNode",
    "VisualIfNode",
    "VisualForLoopNode",
    "VisualMessageBoxNode",
    "VisualSetVariableNode",
    "VisualGetVariableNode",
]
```

### Disk Caching

**Cache File:** `~/.casare_rpa/cache/node_mapping_cache.json`
**Content:** Pre-computed visual→logic mappings

**Cache Validation:**
1. Version check (invalidate if format changes)
2. Registry hash check (invalidate if nodes added/removed)
3. Fallback to recompute if invalid

### Collapse State Optimization

**Purpose:** Hide non-essential ports/widgets when collapsed

```python
class VisualNode:
    _collapsed: bool = True  # Collapsed by default for cleaner canvas

    def set_collapsed(self, collapsed: bool):
        """Hide non-essential widgets when collapsed."""
        # Hides custom properties, shows only essential ports
        # Reduces visual clutter on large graphs
```

---

## Color & Styling System

### Category-Based Colors

```python
def _apply_category_colors(self):
    """Set node color by category."""
    category_colors = {
        "basic": (100, 120, 140),           # Blue-gray
        "browser": (80, 160, 200),          # Light blue
        "control_flow": (150, 100, 180),    # Purple
        "data_operations": (180, 120, 80),  # Orange
        "desktop_automation": (120, 180, 100), # Green
        # ... more categories ...
    }
    self.set_color(*category_colors.get(category, (100, 100, 100)))
```

### Selection Colors (VSCode Theme)

```python
self.model.selected_color = (38, 79, 120, 128)      # VSCode editor selection
self.model.selected_border_color = (0, 122, 204, 255) # VSCode accent
```

### Node Body Color

```python
UNIFIED_NODE_COLOR = QColor(37, 37, 38)  # VSCode sidebar (#252526)
# Slightly lighter than canvas background (#1E1E1E) for visibility
```

---

## Error Handling & Validation

### Type System Validation

**At Connection Time:**
```python
def validate_connection(source_port: Port, dest_port: Port) -> bool:
    """Ensure compatible types."""
    source_type = source_port.data_type
    dest_type = dest_port.data_type

    # Same type always OK
    if source_type == dest_type:
        return True

    # DYNAMIC type accepts anything
    if dest_type == DataType.DYNAMIC:
        return True

    # Check type compatibility matrix
    return is_type_compatible(source_type, dest_type)
```

### Port Creation Validation

```python
def add_typed_input(name: str, data_type: DataType):
    """Create typed input port with validation."""
    if not isinstance(data_type, DataType):
        raise ValueError(f"Invalid DataType: {data_type}")

    port = self._add_port(name, PortType.INPUT)
    port.data_type = data_type
    return port
```

---

## Testing Architecture

### Test Organization

```
tests/
├── presentation/
│   └── canvas/
│       └── visual_nodes/
│           ├── test_base_visual_node.py
│           ├── test_[category]/
│           │   ├── test_browser_nodes.py
│           │   ├── test_control_flow_nodes.py
│           │   └── ... more ...
│           └── test_super_nodes.py
```

### Test Patterns

```python
class TestVisualClickElementNode:
    """Test visual node functionality."""

    def test_class_attributes(self):
        """Verify required attributes present."""
        assert hasattr(VisualClickElementNode, '__identifier__')
        assert hasattr(VisualClickElementNode, 'NODE_NAME')
        assert hasattr(VisualClickElementNode, 'NODE_CATEGORY')

    def test_port_setup(self):
        """Verify ports created correctly."""
        node = VisualClickElementNode()
        # Check exec ports
        assert node.get_input_port('exec_in') is not None
        # Check data ports
        assert node.get_input_port('selector') is not None
        assert node.get_input_port('selector').data_type == DataType.SELECTOR

    def test_widget_generation(self):
        """Verify widgets auto-generated from schema."""
        node = VisualClickElementNode()
        # Should have selector widget (from @properties)
        assert 'selector' in node.model.custom_properties
```

---

## Migration & Refactoring Guide

### Migrating Nodes to @properties

**Before (Manual Widgets):**
```python
class VisualClickElementNode(VisualNode):
    def __init__(self):
        super().__init__()
        # Manually add widget
        widget = SelectorWidget("selector")
        self.add_custom_widget(widget)

    def setup_ports(self):
        self.add_typed_input("selector", DataType.SELECTOR)
```

**After (@properties):**
```python
# In logic node (domain/nodes/browser/...):
@node(category="browser")
@properties(
    PropertyDef("selector", PropertyType.SELECTOR, essential=True),
)
class ClickElementNode(BaseNode):
    async def execute(self, context):
        selector = self.properties["selector"]
        # ... logic ...

# In visual node (simplified):
class VisualClickElementNode(VisualNode):
    __identifier__ = "casare_rpa.browser"
    NODE_NAME = "Click Element"
    NODE_CATEGORY = "browser/interaction"

    # No __init__ needed - widgets auto-generated!

    def setup_ports(self):
        self.add_typed_input("selector", DataType.SELECTOR)
```

**Benefits:**
- Reduces code duplication
- Centralizes UI definition
- Automatic consistency
- Easier maintenance

---

## Auto-Discovery System

### CASARE_NODE_CLASS Attribute

**How It Works:**

```python
# Visual node declares mapping
class VisualLaunchBrowserNode(VisualNode):
    CASARE_NODE_CLASS = "LaunchBrowserNode"  # Class name in domain
    # Optional: CASARE_NODE_MODULE = "browser.lifecycle"

# Factory auto-discovers
def build_node_mapping():
    for visual_class in get_all_visual_node_classes():
        if hasattr(visual_class, 'CASARE_NODE_CLASS'):
            logic_class_name = visual_class.CASARE_NODE_CLASS
            logic_class = import_from_registry(logic_class_name)
            MAPPING[visual_class] = logic_class
```

**No Manual Registry Update Needed** - Magic!

---

## Summary: Technical Strengths

1. **Clean Separation:** Visual ← Mapping → Logic
2. **Auto-Generation:** `@properties` → ports/widgets
3. **Type Safety:** DataType enum + validation
4. **Lazy Loading:** Performance optimization (70% faster startup)
5. **Super Nodes:** Dynamic ports for consolidation
6. **Consistency:** Template-based, auto-discovery
7. **Caching:** Disk cache + memory caching
8. **Modularity:** 21 categories + splitting patterns
9. **Extensibility:** Clear patterns for new nodes
10. **Theming:** VSCode color scheme + category colors
