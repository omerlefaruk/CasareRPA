# Node Development Rules

**Modern Node Standard 2025 - 430+ nodes.**

## Schema-Driven Logic (MANDATORY)

```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")  # required
        timeout = self.get_parameter("timeout", 30000)  # optional
```

## Requirements

| Requirement | Pattern |
|-------------|---------|
| Schema | `@properties(PropertyDef(...))` |
| Value Access | `self.get_parameter(name, default)` |
| Ports | `add_input_port(name, DataType.X)` |
| Legacy | Never use `self.config.get()` |

## Port Definition

```python
# Data ports - 2 args: name, DataType
self.add_input_port("url", DataType.STRING)
self.add_output_port("result", DataType.DICT)

# Exec ports - use dedicated methods
self.add_exec_input("exec_in")
self.add_exec_output("exec_out")
```

## Workflow: Plan -> Search -> Implement

1. **PLAN**: Define atomic operation
2. **SEARCH**: Check `@_index.md`, `@registry_data.py`
3. **IMPLEMENT**: Use existing → Modify → Create new

## Registration Checklist

1. Export in `@{category}/__init__.py`
2. Register in `@registry_data.py`
3. Add to `NODE_TYPE_MAP` in `@/utils/workflow/workflow_loader.py`
4. Create visual node in `@/presentation/canvas/visual_nodes/{category}/`
5. Register in `@/presentation/canvas/visual_nodes/__init__.py`

## Categories

| Category | Base Class | Context |
|----------|------------|---------|
| browser | BrowserBaseNode | PlaywrightPage |
| desktop | DesktopNodeBase | DesktopContext |
| data | BaseNode | None |
| http | BaseNode | UnifiedHttpClient |
| system | BaseNode | None |

## Audit

Run `python scripts/audit_node_modernization.py` → target 98%+

## Cross-References

- Domain base: `../domain/_index.md`
- Visual nodes: `../presentation/canvas/visual_nodes/_index.md`
- Root guide: `../../../../CLAUDE.md`
