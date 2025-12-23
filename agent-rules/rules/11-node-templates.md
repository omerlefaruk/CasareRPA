---
description: Code templates for common node types
---

# Node Templates

## Modern Node Standard (2025)

All templates use **Schema-Driven Logic**:
- `@properties()` decorator (required, even if empty)
- `get_parameter()` for optional properties
- Explicit `DataType` on all ports (ANY is valid)

## Quick Template

```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType

@properties(
    PropertyDef("my_option", PropertyType.STRING, default="value"),
)
@node(category="mycategory")
class MyNode(BaseNode):
    def _define_ports(self):
        self.add_input_port("input_data", DataType.STRING)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context):
        # MODERN: dual-source access (port -> config fallback)
        my_option = self.get_parameter("my_option", "value")
        input_data = self.get_input_value("input_data")

        # ... node logic ...

        self.set_output_value("result", result)
        return {"success": True, "next_nodes": ["exec_out"]}
```

## Browser Node Template
<<<<<<< HEAD
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.nodes.browser.base import BrowserBaseNode, get_page_from_context

@properties(
    PropertyDef("selector", PropertyType.SELECTOR, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyBrowserNode(BrowserBaseNode):
    """Browser automation node."""

    async def execute(self, context):
        page = await get_page_from_context(context)
        # 1. Get raw property
        raw_selector = self.get_parameter("selector")

        # 2. Resolve template (CRITICAL)
        selector = context.resolve_value(raw_selector)

        # Implementation
        return self.success_result({"success": True})
```

## Desktop Node Template
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("window_title", PropertyType.STRING, required=True),
)
@node(category="desktop")
class MyDesktopNode(BaseNode):
    """Desktop automation node."""

    async def execute(self, context):
        import uiautomation as auto
        # 1. Resolve window title
        raw_title = self.get_parameter("window_title")
        window_title = context.resolve_value(raw_title)

        # Implementation
        return self.success_result({"success": True})
```

## Data Node Template
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("input_data", PropertyType.ANY, required=True),
)
@node(category="data")
class MyDataNode(BaseNode):
    """Data transformation node."""

    async def execute(self, context):
        # 1. Get and resolve
        raw_data = self.get_parameter("input_data")
        data = context.resolve_value(raw_data)

        # 2. Transform data
        # transformed_data = ...
        return self.success_result({"output": data})
```

## Test Template
```python
import pytest
from casare_rpa.nodes import MyNode

@pytest.mark.asyncio
async def test_my_node_success(execution_context):
    node = MyNode("test-id")
    node.set_property("input", "value")
    result = await node.execute(execution_context)
    assert result["success"] is True

@pytest.mark.asyncio
async def test_my_node_error(execution_context):
    node = MyNode("test-id")
    node.set_property("input", "")
    with pytest.raises(ValueError):
        await node.execute(execution_context)
```
=======

See `.brain/docs/node-templates.md` for full Playwright template.

## Desktop Node Template

See `.brain/docs/node-templates.md` for full UIAutomation template.
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
