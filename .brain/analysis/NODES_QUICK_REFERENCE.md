<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# Node Development Quick Reference

Fast lookup for common patterns, patterns to follow, and gotchas.

## Node Implementation Checklist

### 1. Basic Setup
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult, NodeStatus

@node(category="my_category")  # REQUIRED: declares node, makes it discoverable
@properties(                     # REQUIRED: defines input parameters
    PropertyDef("param1", PropertyType.STRING, default="", required=True),
    PropertyDef("param2", PropertyType.INTEGER, default=10),
)
class MyNode(BaseNode):
    """Node docstring."""

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "My Node"
        self.node_type = "MyNode"

    def _define_ports(self) -> None:
        """Define input/output ports."""
        self.add_input_port("input_port", DataType.STRING)
        self.add_output_port("output_port", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute node logic."""
        self.status = NodeStatus.RUNNING
        try:
            # Node logic
            result = self.get_parameter("param1")
            self.set_output_value("output_port", result)
            self.status = NodeStatus.SUCCESS
            return {"success": True, "next_nodes": []}
        except Exception as e:
            logger.error(f"Node failed: {e}")
            self.status = NodeStatus.FAILED
            return {"success": False, "error": str(e), "next_nodes": []}
```

### 2. Execution Ports (Control Flow)
```python
# MODERN PATTERN (preferred, ~96 nodes):
self.add_exec_input("exec_in")              # Add execution input port
self.add_exec_output("success")             # Add execution output port
self.add_exec_output("error")

# OLD PATTERN (358+ nodes, still works but inconsistent):
self.add_input_port("exec_in", DataType.EXEC)
self.add_output_port("success", DataType.EXEC)
```
**Status:** Both work, but prefer `add_exec_input/output()` for new nodes.

### 3. Error Handling ✅ (Best Practice)
```python
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    self.status = NodeStatus.RUNNING
    try:
        # Validate inputs
        param = self.get_parameter("param")
        if not param:
            self.status = NodeStatus.FAILED
            logger.error("Parameter 'param' is required")
            return {"success": False, "error": "Parameter required"}

        # Execute logic
        result = await do_operation(param)

        # Set outputs
        self.set_output_value("result", result)

        self.status = NodeStatus.SUCCESS
        logger.info(f"Node {self.node_id} completed successfully")
        return {"success": True, "next_nodes": []}

    except SpecificException as e:
        # Handle specific exceptions
        logger.error(f"Operation failed: {e}")
        self.status = NodeStatus.FAILED
        return {"success": False, "error": str(e)}
    except Exception as e:
        # Catch-all for unexpected errors
        logger.critical(f"Unexpected error in {self.node_type}: {e}", exc_info=True)
        self.status = NodeStatus.FAILED
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
```

**Key Points:**
- ✅ Always catch specific exceptions first
- ✅ Log at appropriate level (debug, info, warning, error, critical)
- ✅ Use `exc_info=True` only for critical/unexpected errors
- ✅ Set `self.status` to indicate result
- ✅ Return structured ExecutionResult

### 4. Property Definitions

```python
@properties(
    # Required text input
    PropertyDef(
        "name",                           # Key (used in get_parameter)
        PropertyType.STRING,              # Type
        required=True,                    # Must be provided
        label="Name",                     # UI label
        tooltip="User's full name",       # Help text
        placeholder="John Doe",           # Hint
    ),

    # Optional with default
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=5000,                     # Default value
        min_value=100,                    # Validation
        max_value=60000,
        label="Timeout (ms)",
    ),

    # Choice/dropdown
    PropertyDef(
        "method",
        PropertyType.CHOICE,
        choices=["GET", "POST", "PUT"],
        default="GET",
        label="HTTP Method",
    ),

    # Boolean
    PropertyDef(
        "verify_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Verify SSL Certificate",
    ),

    # JSON
    PropertyDef(
        "headers",
        PropertyType.JSON,
        default='{"Content-Type": "application/json"}',
        label="HTTP Headers",
    ),

    # Selector (special CSS/XPath)
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        required=True,
        label="Element Selector",
        placeholder="#button-id or //button[@name='submit']",
    ),
)
```

**Common PropertyTypes:**
- STRING, INTEGER, FLOAT, BOOLEAN
- CHOICE (with choices=[...])
- JSON, CODE
- SELECTOR (CSS/XPath for elements)
- FILE, DIRECTORY, COLOR
- DATE, TIME, DATETIME

### 5. Input/Output Ports

```python
def _define_ports(self) -> None:
    # Execution flow
    self.add_exec_input("exec_in")
    self.add_exec_output("success")
    self.add_exec_output("error")

    # Data inputs
    self.add_input_port("data", DataType.STRING)
    self.add_input_port("items", DataType.LIST, required=False)

    # Data outputs
    self.add_output_port("result", DataType.STRING)
    self.add_output_port("count", DataType.INTEGER)
    self.add_output_port("items", DataType.LIST)
```

**Common DataTypes:**
- ANY, STRING, INTEGER, FLOAT, BOOLEAN
- LIST, DICT, OBJECT
- EXEC (for control flow)
- FILE, IMAGE, BYTES
- CREDENTIAL

### 6. Get/Set Values in Execute

```python
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    # Get parameter value (from @properties)
    param = self.get_parameter("param_name", default="fallback")

    # Get input port value (connected from previous node)
    data = self.get_input_value("input_port")

    # Set output port value
    self.set_output_value("output_port", result)

    # Work with context variables
    context.variables["my_var"] = value
    value = context.variables.get("my_var")

    # Context features
    workflow_id = context.workflow_id
    execution_id = context.execution_id
    robot_id = context.robot_id
    timestamp = context.timestamp
```

### 7. Inheritance Patterns

**For Browser Nodes:**
```python
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode

@node(category="browser")
@properties(...)
class MyBrowserNode(BrowserBaseNode):
    """BrowserBaseNode provides:
    - get_page(context) - Get active page or from input port
    - get_normalized_selector(context) - CSS/XPath normalization
    - Screenshot on failure
    - Retry logic via retry_operation()
    """

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        page = self.get_page(context)
        selector = self.get_normalized_selector(context)
        await page.click(selector)
```

**For Desktop Nodes:**
```python
from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase

@node(category="desktop")
@properties(...)
class MyDesktopNode(DesktopNodeBase):
    """DesktopNodeBase provides:
    - get_desktop_context(context)
    - Standard error handling
    - Retry support
    """
    pass
```

**For Google Nodes:**
```python
from casare_rpa.nodes.google.google_base import GoogleBaseNode

@node(category="google")
@properties(...)
class MyGoogleNode(GoogleBaseNode):
    """GoogleBaseNode provides:
    - OAuth token management
    - API client access
    - Credential handling
    """

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        service = await self.get_service("drive", "v3")  # Get API service
```

**For LLM Nodes:**
```python
from casare_rpa.nodes.llm.llm_base import LLMBaseNode

class MyLLMNode(LLMBaseNode):
    """LLMBaseNode provides:
    - Model/temperature/max_tokens parameters
    - Common input/output ports
    - LLM resource management
    """

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        response = await manager.completion(prompt=prompt)
```

### 8. Registering Nodes

**1. Add to registry_data.py:**
```python
# In src/casare_rpa/nodes/registry_data.py
NODE_REGISTRY = {
    # ... existing entries ...
    "MyNode": "my_module",  # or ("my_module", "ActualClassName")
}
```

**2. Export from __init__.py:**
```python
# In src/casare_rpa/nodes/__init__.py or subpackage __init__.py
# Lazy loading handles the rest - no explicit imports needed
```

**3. Verify with:**
```python
from casare_rpa.nodes import MyNode
node = MyNode("node_123")
```

### 9. Common Gotchas

❌ **DON'T:**
```python
# Hardcoded colors - use THEME
widget.setStyleSheet("background: #1a1a2e")

# Lambda in signal - use functools.partial
button.clicked.connect(lambda: self.do_thing(arg))

# Silent exceptions
try:
    result = operation()
except:
    pass

# Old exec port pattern (works but inconsistent)
self.add_input_port("exec_in", PortType.EXEC_INPUT)

# Domain importing infrastructure
from casare_rpa.infrastructure.execution import ExecutionContext  # Wrong

# Raw httpx - use UnifiedHttpClient
response = await httpx.get(url)

# Untyped events
bus.publish({"type": "node_done"})  # Wrong

# Not logging errors
except Exception:
    return {"success": False}
```

✅ **DO:**
```python
# Use THEME
from casare_rpa.presentation.canvas.ui.theme import THEME
widget.setStyleSheet(f"background: {THEME['bg_primary']}")

# Named method for signals
@Slot()
def on_button_clicked(self):
    self.do_thing(arg)
button.clicked.connect(self.on_button_clicked)

# Or use functools.partial
from functools import partial
button.clicked.connect(partial(self.do_thing, arg))

# Proper exception handling
try:
    result = await operation()
except SpecificError as e:
    logger.error(f"Specific error: {e}")
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)

# Modern exec ports
self.add_exec_input("exec_in")
self.add_exec_output("success")

# Proper imports (domain layer safe)
from casare_rpa.domain.entities.base_node import BaseNode

# Use UnifiedHttpClient
from casare_rpa.infrastructure.http_client import UnifiedHttpClient
client = UnifiedHttpClient()
response = await client.get(url)

# Typed events
from casare_rpa.domain.events import NodeCompleted
bus.publish(NodeCompleted(node_id="x", node_type="Y", execution_time_ms=100))

# Always log errors
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return {"success": False, "error": str(e)}
```

---

## Category-Specific Patterns

### Browser Nodes

```python
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_TIMEOUT, BROWSER_SELECTOR_STRICT, BROWSER_RETRY_COUNT, ...
)

@node(category="browser")
@properties(
    PropertyDef("selector", PropertyType.SELECTOR, required=True),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
)
class MyBrowserNode(BrowserBaseNode):
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        page = self.get_page(context)
        selector = self.get_normalized_selector(context)
        # Use retry_operation for resilience
        await self.retry_operation(
            lambda: page.click(selector),
            retry_count=safe_int(self.get_parameter("retry_count", 3)),
            retry_interval=safe_int(self.get_parameter("retry_interval", 1000)) / 1000,
        )
```

### File Operation Nodes

```python
from casare_rpa.nodes.file.file_security import validate_path_security, PathSecurityError

@node(category="file")
@properties(
    PropertyDef("file_path", PropertyType.STRING, required=True),
    PropertyDef("allow_dangerous_paths", PropertyType.BOOLEAN, default=False),
)
class MyFileNode(BaseNode):
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        file_path = self.get_parameter("file_path")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        # Always validate paths
        try:
            validate_path_security(file_path, allow_dangerous=allow_dangerous)
        except PathSecurityError as e:
            return {"success": False, "error": str(e)}

        # Use pathlib for path operations
        from pathlib import Path
        path = Path(file_path)
```

### Data Operation Nodes

```python
@node(category="data")
@properties(
    PropertyDef("list_var", PropertyType.STRING, required=True),
    PropertyDef("index", PropertyType.INTEGER, default=0),
)
class MyListNode(BaseNode):
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        list_var = self.get_parameter("list_var")
        items = context.variables.get(list_var, [])

        # Type validation
        if not isinstance(items, list):
            return {"success": False, "error": f"Expected list, got {type(items).__name__}"}

        # Boundary checking
        idx = self.get_parameter("index", 0)
        if idx < 0 or idx >= len(items):
            return {"success": False, "error": f"Index {idx} out of range"}
```

### Control Flow Nodes

```python
@node(category="control_flow")
@properties(
    PropertyDef("expression", PropertyType.STRING, required=True),
)
class MyConditionNode(BaseNode):
    def _define_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("true")
        self.add_exec_output("false")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        expr = self.get_parameter("expression")

        # Use safe_eval for expressions
        from casare_rpa.utils.security.safe_eval import safe_eval, is_safe_expression

        if not is_safe_expression(expr):
            return {"success": False, "error": f"Unsafe expression: {expr}"}

        try:
            result = safe_eval(expr, context.variables)
            output = "true" if result else "false"
            return {"success": True, "next_nodes": [output]}
        except Exception as e:
            return {"success": False, "error": f"Evaluation failed: {e}"}
```

---

## Testing Nodes

```python
import pytest
from casare_rpa.nodes.my_module import MyNode
from casare_rpa.infrastructure.execution import ExecutionContext

@pytest.mark.asyncio
async def test_my_node_success():
    # Setup
    node = MyNode("test_node", config={"param": "value"})
    context = ExecutionContext(workflow_id="test", robot_id="test_robot")

    # Execute
    result = await node.execute(context)

    # Assert
    assert result["success"] is True
    assert node.status == NodeStatus.SUCCESS

@pytest.mark.asyncio
async def test_my_node_error():
    node = MyNode("test_node", config={})  # Missing required param
    context = ExecutionContext(workflow_id="test", robot_id="test_robot")

    result = await node.execute(context)

    assert result["success"] is False
    assert node.status == NodeStatus.FAILED
```

---

## Performance Tips

1. **Use lazy imports** for heavy dependencies
   ```python
   async def execute(self, context):
       import playwright  # Only import when needed
       page = self.get_page(context)
   ```

2. **Cache expensive operations** in context
   ```python
   cache_key = f"{self.node_id}_data"
   if cache_key in context.variables:
       data = context.variables[cache_key]
   else:
       data = await fetch_expensive_data()
       context.variables[cache_key] = data
   ```

3. **Use connection pooling** for databases/HTTP
   ```python
   # HTTP uses UnifiedHttpClient with pooling built-in
   # Database nodes should reuse connections
   ```

4. **Avoid blocking operations** on main thread
   ```python
   # ✅ Use async
   result = await async_operation()

   # ❌ Don't block
   result = blocking_operation()
   ```

---

## Logging Best Practice

```python
from loguru import logger

# Use appropriate levels
logger.debug(f"Debug info: {var}")          # Development/tracing
logger.info(f"Node {id} started")           # Normal flow
logger.warning(f"Unexpected value: {val}")  # Recoverable issue
logger.error(f"Operation failed: {err}")    # Error but node completes
logger.critical(f"Fatal error: {err}", exc_info=True)  # Node cannot complete
```

---

**Last Updated:** 2025-12-14
**For Questions:** See NODES_COMPREHENSIVE_ANALYSIS.md
