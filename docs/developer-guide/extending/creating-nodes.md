# Creating Nodes

This guide covers how to create new executable nodes for CasareRPA. Nodes are the building blocks of workflows - each performs a single atomic operation.

## Node Architecture Overview

CasareRPA nodes follow a three-layer architecture:

| Layer | Class | Location | Purpose |
|-------|-------|----------|---------|
| Domain | `BaseNode` subclass | `nodes/{category}/` | Business logic and execution |
| Presentation | `VisualNode` subclass | `visual_nodes/{category}/` | Canvas rendering and widgets |
| Schema | `@properties` decorator | Applied to domain class | Property definitions |

The `@node` decorator automatically adds `exec_in` and `exec_out` ports to enable workflow execution flow.

## 7-Step Implementation Checklist

Every new node must complete all steps:

1. Apply `@node` decorator (adds exec ports)
2. Apply `@properties` decorator (defines property schema)
3. Create reusable PropertyDef constants (if shared)
4. Create visual node class
5. Write unit tests
6. Export from `__init__.py` files
7. Register in `NODE_REGISTRY`

## Step 1: Define the Node Class

Create your node in the appropriate category directory under `src/casare_rpa/nodes/`.

```python
"""
My Custom Node

Performs a single atomic operation.
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode


@node(
    name="My Operation",
    category="mycategory",
    description="Performs my custom operation",
    retries=0,  # Optional: retry count on failure
    retry_delay=1.0,  # Optional: seconds between retries
)
@properties(
    PropertyDef(
        "input_value",
        PropertyType.STRING,
        required=True,
        label="Input Value",
        tooltip="The value to process",
        essential=True,  # Visible when node is collapsed
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        label="Timeout (ms)",
        tab="advanced",
    ),
)
class MyOperationNode(BaseNode):
    """
    Performs my custom operation on input data.

    Config:
        input_value: The value to process (required)
        timeout: Operation timeout in milliseconds (default: 30000)

    Outputs:
        result: The processed result
        success: Whether operation succeeded
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "My Operation",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "MyOperationNode"

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the operation."""
        # Get property values - checks port first, then config
        input_value = self.get_parameter("input_value", context)
        timeout = self.get_parameter("timeout", context)

        if not input_value:
            raise ValueError("Input value is required")

        logger.info(f"[{self.name}] Processing: {input_value}")

        try:
            # Your atomic operation here
            result = input_value.upper()

            return {
                "success": True,
                "data": {
                    "result": result,
                    "success": True,
                },
            }

        except Exception as e:
            logger.error(f"[{self.name}] Operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
```

### Key Points

- **`@node` decorator**: Adds `exec_in`/`exec_out` ports and attaches metadata
- **`@properties` decorator**: Defines the property schema for auto-widget generation
- **`get_parameter()`**: Always use this to get values - it checks port connections first, then falls back to config
- **Async execute**: All node execution is async to support Playwright and other async operations

## Step 2: PropertyDef Types

The `PropertyType` enum defines available property types:

| Type | Description | Example |
|------|-------------|---------|
| `STRING` | Single-line text | `"https://example.com"` |
| `TEXT` | Multi-line text area | `"Line 1\nLine 2"` |
| `INTEGER` | Whole numbers | `30000` |
| `FLOAT` | Decimal numbers | `5.0` |
| `BOOLEAN` | True/False checkbox | `True` |
| `CHOICE` | Dropdown selection | `"GET"` from `["GET", "POST"]` |
| `MULTI_CHOICE` | Multiple selection | `["option1", "option2"]` |
| `JSON` | JSON object editor | `{"key": "value"}` |
| `FILE_PATH` | File picker | `"C:/data/file.txt"` |
| `DIRECTORY_PATH` | Folder picker | `"C:/data/"` |
| `CODE` | Code editor | `"x = 1 + 2"` |
| `SELECTOR` | CSS/XPath selector | `"#submit-btn"` |
| `COLOR` | Color picker | `"#ff0000"` |
| `DATE` | Date picker | `"2025-01-15"` |
| `TIME` | Time picker | `"14:30:00"` |
| `DATETIME` | DateTime picker | `"2025-01-15T14:30:00"` |

### PropertyDef Options

```python
PropertyDef(
    name="my_property",           # Property name (config key)
    type=PropertyType.STRING,     # Property type
    default="",                   # Default value
    label="My Property",          # UI label (auto-generated if None)
    placeholder="Enter value...", # Placeholder text
    tooltip="Help text",          # Tooltip on hover
    required=True,                # Validation flag
    essential=True,               # Visible when collapsed
    tab="properties",             # Tab grouping: "connection", "properties", "advanced"
    order=1,                      # Sort order (lower first)
    min_value=0,                  # Numeric minimum
    max_value=100,                # Numeric maximum
    choices=["A", "B", "C"],      # For CHOICE type
    pattern=r"^\d+$",             # Regex validation for STRING
    visibility="normal",          # "essential", "normal", "advanced", "internal"
)
```

## Step 3: Base Classes

Choose the appropriate base class for your node category:

### BaseNode - Standard Nodes

```python
from casare_rpa.domain.entities.base_node import BaseNode

class MyNode(BaseNode):
    async def execute(self, context: Any) -> Dict[str, Any]:
        # Standard node implementation
        pass
```

### BrowserBaseNode - Browser Automation

For web automation with Playwright:

```python
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_SELECTOR,
    BROWSER_TIMEOUT,
)

@properties(BROWSER_SELECTOR, BROWSER_TIMEOUT)
@node(category="browser")
class MyBrowserNode(BrowserBaseNode):
    async def execute(self, context: Any) -> Dict[str, Any]:
        page = self.get_page(context)
        selector = self.normalize_selector(self.get_parameter("selector", context))

        locator = page.locator(selector)
        await locator.wait_for(state="visible")

        # Browser operation here
        result = await locator.text_content()

        return self.success_result(page=page, result=result)
```

### DesktopNodeBase - Desktop Automation

For Windows UI automation:

```python
from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    SELECTOR_PROP,
    TIMEOUT_PROP,
)

@properties(SELECTOR_PROP, TIMEOUT_PROP)
@node(category="desktop")
class MyDesktopNode(DesktopNodeBase):
    async def execute(self, context: Any) -> Dict[str, Any]:
        window = self.get_input_value("window")
        desktop_ctx = self.get_desktop_context(context)

        # Desktop operation here
        element = window.find_child(selector)
        result = element.get_text()

        return self.success_result(result=result)
```

### GoogleBaseNode - Google Services

For Google Workspace APIs:

```python
from casare_rpa.nodes.google.google_base import GoogleBaseNode

@node(category="google")
class MySheetsNode(GoogleBaseNode):
    async def execute(self, context: Any) -> Dict[str, Any]:
        credential_name = self.get_parameter("credential_name", context)
        creds = self.get_credentials(credential_name)

        # Google API operation here
        service = build("sheets", "v4", credentials=creds)

        return self.success_result(data=result)
```

## Step 4: Visual Node Class

Create the visual representation in `presentation/canvas/visual_nodes/{category}/nodes.py`:

```python
"""Visual node for MyOperationNode."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualMyOperationNode(VisualNode):
    """Visual representation of MyOperationNode."""

    __identifier__ = "casare_rpa.mycategory"
    NODE_NAME = "My Operation"
    NODE_CATEGORY = "mycategory"
    # CASARE_NODE_CLASS is auto-derived: VisualMyOperationNode -> MyOperationNode

    def __init__(self) -> None:
        super().__init__()
        # Widgets are auto-generated from @properties decorator
        # Only add custom widgets here if absolutely necessary
```

> **Important**: Do NOT manually add widgets for properties already defined in `@properties`. The decorator auto-generates widgets. Adding them again causes `NodePropertyError: "property already exists"`.

### When to Add Custom Widgets

Only add widgets manually when:

1. You need a file/directory picker (replaces auto-generated text input)
2. You need cascading dropdowns (dependent selections)
3. You need completely custom UI

```python
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
)

class VisualFileReadNode(VisualNode):
    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read File"
    NODE_CATEGORY = "file"

    def __init__(self) -> None:
        super().__init__()
        # Replace auto-generated text input with file picker
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File",
                file_filter="All Files (*.*)",
                placeholder="Select file...",
            ),
        )
```

## Step 5: Unit Tests

Create tests in `tests/nodes/{category}/test_{module}.py`:

```python
"""Tests for MyOperationNode."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from casare_rpa.nodes.mycategory.my_operation_node import MyOperationNode


class TestMyOperationNode:
    """Test suite for MyOperationNode."""

    @pytest.fixture
    def node(self):
        """Create a node instance for testing."""
        return MyOperationNode(
            node_id="test-node",
            config={"input_value": "test"},
        )

    @pytest.fixture
    def mock_context(self):
        """Create a mock execution context."""
        context = MagicMock()
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_execute_success(self, node, mock_context):
        """Test successful execution."""
        result = await node.execute(mock_context)

        assert result["success"] is True
        assert result["data"]["result"] == "TEST"

    @pytest.mark.asyncio
    async def test_execute_missing_input(self, mock_context):
        """Test error when input is missing."""
        node = MyOperationNode(node_id="test", config={})

        with pytest.raises(ValueError, match="Input value is required"):
            await node.execute(mock_context)

    @pytest.mark.asyncio
    async def test_execute_with_port_value(self, node, mock_context):
        """Test that port value overrides config."""
        # Simulate connected port
        node._input_values = {"input_value": "from_port"}

        result = await node.execute(mock_context)

        assert result["data"]["result"] == "FROM_PORT"
```

## Step 6: Export from __init__.py

### Logic Node Export

In `src/casare_rpa/nodes/mycategory/__init__.py`:

```python
"""My Category nodes."""

from .my_operation_node import MyOperationNode

__all__ = ["MyOperationNode"]
```

### Visual Node Export

In `src/casare_rpa/presentation/canvas/visual_nodes/mycategory/__init__.py`:

```python
"""Visual nodes for My Category."""

from .nodes import VisualMyOperationNode

__all__ = ["VisualMyOperationNode"]
```

**Critical**: Also export from the main visual nodes package.

In `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`:

```python
# Add to imports
from .mycategory import VisualMyOperationNode

# Add to __all__
__all__ = [
    # ... existing exports ...
    "VisualMyOperationNode",
]
```

Without this export, the node will not appear in the canvas palette.

## Step 7: Register in NODE_REGISTRY

In `src/casare_rpa/nodes/registry_data.py`, add to the registry:

```python
NODE_REGISTRY = {
    # ... existing nodes ...

    # Simple registration: class name matches key
    "MyOperationNode": "mycategory.my_operation_node",

    # Tuple registration: when class name differs
    "AliasName": ("mycategory.my_operation_node", "MyOperationNode"),
}
```

The registry uses lazy loading - nodes are only imported when first accessed.

## Common Property Constants

Reuse existing constants for consistency:

### Browser Constants

```python
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_SELECTOR,
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_WAIT_UNTIL,
)
```

### Desktop Constants

```python
from casare_rpa.nodes.desktop_nodes.properties import (
    SELECTOR_PROP,
    TIMEOUT_PROP,
    TIMEOUT_LONG_PROP,
    THROW_ON_NOT_FOUND_PROP,
    SIMULATE_PROP,
)
```

## Atomic Design Principles

### Single Responsibility

Each node should do exactly one thing:

```python
# GOOD - Single operation
class ClickElementNode: ...
class TypeTextNode: ...
class WaitForElementNode: ...

# BAD - Multiple operations
class ClickAndTypeNode: ...
class FillFormNode: ...  # Too broad
```

### Configurable Behavior

Use properties for options instead of creating variations:

```python
# GOOD - Options via properties
@properties(
    PropertyDef("clear_first", PropertyType.BOOLEAN, default=True),
    PropertyDef("press_enter", PropertyType.BOOLEAN, default=False),
)
class TypeTextNode: ...

# BAD - Multiple node variants
class TypeTextAndClearNode: ...
class TypeTextAndPressEnterNode: ...
```

## Error Handling

All external calls should be wrapped in try/except:

```python
async def execute(self, context: Any) -> Dict[str, Any]:
    try:
        # Operation
        result = await self.perform_operation()
        return self.success_result(result=result)

    except TimeoutError as e:
        logger.warning(f"[{self.name}] Timeout: {e}")
        return self.error_result(f"Operation timed out: {e}")

    except Exception as e:
        logger.error(f"[{self.name}] Failed: {e}")
        raise  # Re-raise for error handling nodes to catch
```

## HTTP Nodes

For HTTP operations, always use `UnifiedHttpClient`:

```python
from casare_rpa.infrastructure.http import UnifiedHttpClient

async def execute(self, context: Any) -> Dict[str, Any]:
    async with UnifiedHttpClient() as client:
        response = await client.get(url, timeout=timeout)
        data = await response.json()
    return self.success_result(data=data)
```

`UnifiedHttpClient` provides:
- Connection pooling (max 10 sessions)
- Retry with exponential backoff (3 retries)
- Rate limiting (10 req/sec per domain)
- Circuit breaker (5 failures triggers break)
- SSRF protection (blocks localhost/private IPs)

## Next Steps

- [Creating Triggers](creating-triggers.md) - For workflow entry points
- [Visual Nodes](visual-nodes.md) - Custom UI rendering
- [Custom Widgets](custom-widgets.md) - Property widget development
