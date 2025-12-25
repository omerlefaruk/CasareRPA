# Decision Tree: Adding a New Node

## Modern Node Standard (2025)

**All nodes MUST follow Schema-Driven Logic:**
- `@properties()` decorator (REQUIRED - even if empty)
- `get_parameter()` for optional properties
- Explicit DataType on all ports (ANY is valid)
- NO `self.config.get()` calls

**Audit compliance:** `python scripts/audit_node_modernization.py`

## Quick Decision

```
Is this a browser/Playwright node?
├─ YES → Extend BrowserBaseNode (see Step 2a)
└─ NO → Is it a desktop/UI automation node?
    ├─ YES → Extend DesktopNodeBase (see Step 2b)
    └─ NO → Extend BaseNode directly (see Step 2c)
```

---

## Step 1: Check Existing Nodes First

**CRITICAL**: Search before creating!

```bash
# Search for similar functionality
search_codebase "your node description"
Grep: "YourKeyword" --path nodes/
```

**Check these locations:**
- `nodes/_index.md` - Full node registry
- `nodes/{category}/` - Category-specific nodes
- Similar nodes in other categories

---

## Step 2: Create Node Class

### 2a: Browser Node (Playwright)

```python
# File: nodes/browser/my_browser_node.py
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.nodes.browser import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
)

@properties(
    PropertyDef("selector", PropertyType.SELECTOR, essential=True),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
)
@node(category="browser")
class MyBrowserNode(BrowserBaseNode):
    """AI-HINT: Browser node using Playwright. Requires page from context."""

    NODE_NAME = "My Browser Node"

    def _define_ports(self):
        self.add_page_passthrough_ports()  # page_in → page_out
        self.add_selector_input_port()      # selector input
        self.add_output_port("result", DataType.STRING, "Result")

    async def execute(self, context):
        try:
            page = self.get_page(context)
            # MODERN: get_parameter() for dual-source access
            selector = self.get_normalized_selector(self.get_parameter("selector"))
            timeout = self.get_parameter("timeout", 30000)

            # Your Playwright logic here
            result = await page.text_content(selector)

            self.set_output_value("result", result)
            return self.success_result({"result": result})
        except Exception as e:
            return self.error_result(e)
```

### 2b: Desktop Node (UIAutomation)

```python
# File: nodes/desktop_nodes/my_desktop_node.py
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects import DataType

@properties(
    PropertyDef("window_title", PropertyType.STRING, essential=True),
    PropertyDef("timeout", PropertyType.FLOAT, default=5.0),
)
@node(category="desktop")
class MyDesktopNode(BaseNode):
    """AI-HINT: Desktop node using UIAutomation. Windows-only."""

    NODE_NAME = "My Desktop Node"

    def _define_ports(self):
        self.add_exec_input()
        self.add_exec_output()
        self.add_output_port("element", DataType.ANY, "Found element")

    async def execute(self, context):
        try:
            # MODERN: get_parameter() for dual-source access
            window_title = self.get_parameter("window_title")
            timeout = self.get_parameter("timeout", 5.0)
            window_title = self.get_parameter("window_title")
            # UIAutomation logic here
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 2c: Generic Node

```python
# File: nodes/{category}/my_node.py
from casare_rpa.domain import node, properties
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects import DataType

@properties(
    PropertyDef("param1", PropertyType.STRING, default="", essential=True),
    PropertyDef("param2", PropertyType.INTEGER, default=10),
)
@node(category="custom")
class MyNode(BaseNode):
    """AI-HINT: Generic node. Pure logic, no external dependencies."""

    NODE_NAME = "My Node"

    def _define_ports(self):
        self.add_exec_input()
        self.add_exec_output()
        self.add_input_port("input", DataType.STRING, "Input value")
        self.add_output_port("output", DataType.STRING, "Output value")

    async def execute(self, context):
        try:
            param1 = self.get_parameter("param1")
            input_val = self.get_input_value("input")

            result = f"{param1}: {input_val}"

            self.set_output_value("output", result)
            return {"success": True, "data": {"output": result}}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## Step 3: Register Node

**File**: `nodes/__init__.py`

Add to `_NODE_REGISTRY`:

```python
_NODE_REGISTRY = {
    # ... existing entries ...
    "MyNode": "my_node",  # module name without .py
    "MyBrowserNode": "browser.my_browser_node",
}
```

---

## Step 4: Create Visual Node

**File**: `presentation/canvas/visual_nodes/{category}/my_node.py`

```python
from casare_rpa.presentation.canvas.visual_nodes.base import VisualNodeBase
from casare_rpa.nodes.{category}.my_node import MyNode

class VisualMyNode(VisualNodeBase):
    """Visual representation of MyNode on canvas."""

    NODE_CLASS = MyNode
    CATEGORY = "Custom"
    ICON = "custom_icon"  # From resources/icons/

    def __init__(self, node_id: str, **kwargs):
        super().__init__(node_id, MyNode, **kwargs)
```

**Register in**: `presentation/canvas/visual_nodes/{category}/__init__.py`

---

## Step 5: Add Tests

**File**: `tests/nodes/{category}/test_my_node.py`

```python
import pytest
from casare_rpa.nodes.{category}.my_node import MyNode

@pytest.mark.asyncio
async def test_my_node_success(execution_context):
    """SUCCESS: Normal operation."""
    node = MyNode(node_id="test", config={"param1": "value"})
    execution_context.variables["input"] = "test_input"

    result = await node.execute(execution_context)

    assert result["success"] is True
    assert "output" in result.get("data", {})

@pytest.mark.asyncio
async def test_my_node_error(execution_context):
    """ERROR: Invalid input handling."""
    node = MyNode(node_id="test", config={"param1": ""})

    result = await node.execute(execution_context)

    # Should handle gracefully, not crash
    assert "error" in result or result["success"] is True

@pytest.mark.asyncio
async def test_my_node_edge_case(execution_context):
    """EDGE: Empty/null inputs."""
    node = MyNode(node_id="test", config={})

    result = await node.execute(execution_context)

    # Should not crash on missing config
    assert isinstance(result, dict)
```

---

## Step 6: Update Indexes

1. **Update `nodes/_index.md`** - Add to node list
2. **Update `nodes/{category}/_index.md`** - Add to category
3. **Update `presentation/canvas/visual_nodes/_index.md`** - Add visual node

---

## Checklist

- [ ] Searched for existing similar nodes
- [ ] Created node class with `@node` and `@properties`
- [ ] Used `add_exec_input()`/`add_exec_output()` for exec ports
- [ ] Registered in `_NODE_REGISTRY`
- [ ] Created visual node class
- [ ] Added 3-scenario tests (success, error, edge)
- [ ] Updated _index.md files
- [ ] No hardcoded colors (use THEME)
- [ ] No raw httpx/aiohttp (use UnifiedHttpClient)
- [ ] All external calls wrapped in try/except

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `add_input_port("exec_in", PortType.EXEC_INPUT)` | Use `add_exec_input()` |
| Hardcoded colors `#FF0000` | Use `THEME.error` |
| Missing `@Slot` on signal handlers | Add `@Slot(type)` decorator |
| Lambda in signal connection | Use `functools.partial` or named method |
| Raw `httpx.get()` | Use `UnifiedHttpClient` |

---

*See also: `.brain/docs/node-templates-core.md`, `.brain/docs/node-checklist.md`*
