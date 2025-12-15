# Node Templates

Quick-start templates for common node types.

## Browser Node Template
```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.nodes.browser import BrowserBaseNode, get_page_from_context

@node_schema(
    PropertyDef("selector", PropertyType.SELECTOR, essential=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@executable_node
class MyBrowserNode(BrowserBaseNode):
    """Browser automation node."""

    NODE_NAME = "My Browser Node"

    async def execute(self, context):
        page = await get_page_from_context(context)
        selector = self.get_property("selector")
        # Implementation
        return {"success": True}
```

## Desktop Node Template
```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
    PropertyDef("window_title", PropertyType.STRING, essential=True),
)
@executable_node
class MyDesktopNode(BaseNode):
    """Desktop automation node."""

    NODE_NAME = "My Desktop Node"

    async def execute(self, context):
        import uiautomation as auto
        window_title = self.get_property("window_title")
        # Implementation
        return {"success": True}
```

## Data Node Template
```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
    PropertyDef("input_data", PropertyType.ANY, essential=True),
)
@executable_node
class MyDataNode(BaseNode):
    """Data transformation node."""

    NODE_NAME = "My Data Node"

    async def execute(self, context):
        data = context.resolve_value(self.get_property("input_data"))
        # Transform data
        return {"output": transformed_data}
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
