# Node Templates

Quick-start templates for common node types.

## Browser Node Template
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
