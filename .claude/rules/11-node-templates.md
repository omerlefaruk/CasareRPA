---
description: Code templates for common node types
paths:
  - src/casare_rpa/nodes/**
  - src/casare_rpa/presentation/canvas/visual_nodes/**
  - tests/nodes/**
  - .brain/docs/node-checklist.md
  - .brain/docs/node-templates-*.md
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

See `.brain/docs/node-templates-core.md` for full Playwright template.

## Desktop Node Template

See `.brain/docs/node-templates-core.md` for full UIAutomation template.
