# Node Development

## Modern Node Standard (2025)

All nodes MUST follow the **Schema-Driven Logic** pattern:

| Requirement | Pattern | Notes |
|-------------|---------|-------|
| Schema | `@properties(PropertyDef(...))` | Defines configuration schema |
| Value Access | `self.get_parameter(name, default)` | Dual-source: port → config fallback |
| Ports | `add_input_port(name, DataType.X)` | Explicit DataType (ANY is valid) |
| No Legacy | Never use `self.config.get()` | Use get_parameter() instead |

**Modernization Audit:** Run `python scripts/audit_node_modernization.py`

## Workflow: Plan → Search → Implement

### 1. PLAN
Define atomic operation:
```
Node: [Name]Node
Category: browser|desktop|data|http|system|control_flow|variable
Purpose: [One sentence]
Inputs: [port: DataType]
Outputs: [port: DataType]
```

### 2. SEARCH (MANDATORY)
```
1. Read nodes/_index.md           # Find category
2. Grep nodes/registry_data.py    # Check NODE_REGISTRY
3. Decision:
   ├── Exists? → Use it
   ├── Similar? → Enhance it (add PropertyDef)
   └── Nothing? → Create new
```

### 3. IMPLEMENT
See `.brain/docs/node-templates.md` for full templates.

**8-step checklist** (`.brain/docs/node-checklist.md`):
1. `@node` decorator
2. `@properties` with PropertyDef (REQUIRED - even empty `@properties()`)
3. Use `get_parameter()` for optional properties
4. Visual node class
5. Unit tests
6. Export from `__init__.py`
7. Add to `NODE_REGISTRY`
8. Add to `NODE_TYPE_MAP`

## Test Rules
- Tests: domain node logic in `tests/domain/` should have no mocks; use `tests/nodes/` fixtures for node behavior.

## Node Registration
- Register nodes in `src/casare_rpa/nodes/registry_data.py`.
- Keep `PropertyDef` schemas consistent with visual node widgets.

## Atomic Design Principles

**Single Responsibility**:
```python
# GOOD                    # BAD
ClickElementNode          ClickAndTypeNode
TypeTextNode              FillFormNode (too much)
```

**Configurable Behavior**:
```python
# GOOD: Options
@properties(
    PropertyDef("clear_first", BOOLEAN, default=True),
)
class TypeTextNode: ...

# BAD: Hardcoded
class TypeTextAndPressEnterNode: ...
```

## Port Definition (CRITICAL)

### Data Ports
```python
# CORRECT - 2 args: name, DataType
self.add_input_port("url", DataType.STRING)
self.add_output_port("result", DataType.DICT)

# WRONG - Never use PortType for data ports
self.add_input_port("url", PortType.INPUT, DataType.STRING)  # NO!
```

### Exec Ports
```python
# CORRECT - Use dedicated methods
self.add_exec_input("exec_in")
self.add_exec_output("exec_out")

# WRONG - Never use add_input_port for exec ports
self.add_input_port("exec_in", PortType.EXEC_INPUT)   # NO!
self.add_output_port("exec_out", PortType.EXEC_OUTPUT)  # NO!
```

### Port Method Signatures
| Method | Arguments | Use |
|--------|-----------|-----|
| `add_input_port` | `(name, DataType, label?, required?)` | Data inputs |
| `add_output_port` | `(name, DataType, label?, required?)` | Data outputs |
| `add_exec_input` | `(name?)` | Execution flow in |
| `add_exec_output` | `(name?)` | Execution flow out |

## Categories
| Category | Base Class | Context |
|----------|------------|---------|
| browser | BrowserBaseNode | PlaywrightPage |
| desktop | DesktopNodeBase | DesktopContext |
| data | BaseNode | None |
| http | BaseNode | UnifiedHttpClient |
| system | BaseNode | None |
| control_flow | BaseNode | None |
| variable | BaseNode | ExecutionContext |

## Workflow Layout
```
Y=100:  [Tooltip1]     [Tooltip2]     (parallel branch)
Y=300:  [Start]→[Node1]→[Node2]→[End] (main flow)
X:      100    400     700     1000   (300px spacing)
```

**Non-blocking nodes** (Tooltip, Log, Debug): Always parallel branch
**Blocking nodes** (InputDialog, MessageBox): Sequential

## PropertyDef Types
| Type | Use |
|------|-----|
| STRING | Single-line text |
| TEXT | Multi-line |
| INTEGER | Whole numbers |
| FLOAT | Decimals |
| BOOLEAN | True/False |
| CHOICE | Dropdown |
| JSON | Structured data |
| FILE_PATH | File picker |
| SELECTOR | CSS/XPath |
