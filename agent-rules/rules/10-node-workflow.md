---
description: Node development workflow and templates
---

# Node Workflow

## Modern Node Standard (2025)

**Schema-Driven Logic** - All 430+ nodes follow this pattern:

<<<<<<< HEAD
**Priority:**
1. Use existing node → Done
2. Modify existing node → Minimal change
3. Create new node → Last resort

## Phase 3: IMPLEMENT

### File Location
| Category | Directory |
|----------|-----------|
| Browser | `nodes/browser/` |
| Desktop | `nodes/desktop_nodes/` |
| Data | `nodes/data/` |
| Control Flow | `nodes/control_flow/` |
| System | `nodes/system/` |

### Required Components
1. Node class extending `BaseNode`
2. `@node(category="category")` decorator
3. `@properties` with property definitions
4. Tests in `tests/nodes/`

### Template
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("input", PropertyType.STRING, required=True),
)
@node(category="my_category")
class MyNode(BaseNode):
    """One-line description."""

    async def execute(self, context):
        # 1. Get raw parameter
        raw_val = self.get_parameter("input")

        # 2. Resolve templates (MANDATORY)
        val = context.resolve_value(raw_val)

        # 3. Implementation
        return self.success_result({"result": f"Processed {val}"})
=======
```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),  # optional
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        # MODERN: get_parameter() checks port first, then config
        url = self.get_parameter("url")           # required - from port
        timeout = self.get_parameter("timeout", 30000)  # optional - port or config

        # LEGACY (DON'T USE): self.config.get("timeout", 30000)
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
```

**When to use get_parameter():**
- Optional properties (have defaults) → MUST use `get_parameter()`
- Required properties (connection-only) → `get_input_value()` is fine

## Plan -> Search -> Implement

**Always follow this workflow for nodes:**

1. **PLAN**: Define atomic operation (one node = one responsibility)
2. **SEARCH**: Check existing nodes first (`src/casare_rpa/nodes/_index.md`, `NODE_REGISTRY`)
3. **IMPLEMENT**: Use existing -> Modify existing -> Create new (last resort)

## Node Categories

| Category | Path | Description |
|----------|------|-------------|
| Browser | `src/casare_rpa/nodes/browser/` | Web automation (Playwright) |
| Desktop | `src/casare_rpa/nodes/desktop_nodes/` | Windows UI automation |
| File | `src/casare_rpa/nodes/file/` | File system operations |
| Data | `src/casare_rpa/nodes/data/` | Data transformation |
| Flow | `src/casare_rpa/nodes/control_flow/` | Control flow |
| Google | `src/casare_rpa/nodes/google/` | Google services |
| HTTP | `src/casare_rpa/nodes/http/` | HTTP/API calls |

## Port Rules

- Use add_exec_input()/add_exec_output() - NEVER add_input_port(name, PortType.EXEC_*)
- Data ports: `add_input_port(name, DataType.X)` - ANY is valid for polymorphic ports
- One node = one atomic operation

## Registration

1. Add to nodes/{category}/__init__.py
2. Register in `NODE_REGISTRY` (`src/casare_rpa/nodes/registry_data.py`)
3. Add visual node to `src/casare_rpa/presentation/canvas/visual_nodes/{category}/`
4. Register in `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`
