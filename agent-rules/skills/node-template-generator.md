# Node Template Generator Skill

Generate node scaffolding quickly.

## Basic Template
```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
    PropertyDef("input", PropertyType.STRING, essential=True, placeholder="Enter value..."),
)
@executable_node
class {NodeName}(BaseNode):
    """{Description}"""

    NODE_NAME = "{Display Name}"

    async def execute(self, context):
        input_value = context.resolve_value(self.get_property("input"))

        # Implementation here

        return {"result": output_value}
```

## Add to Registry
In `nodes/__init__.py`:
```python
"{NodeName}": "{module_name}",
```

## Create Visual Node
In `presentation/canvas/visual_nodes/`:
```python
from casare_rpa.nodes import {NodeName}
# Visual node implementation
```
