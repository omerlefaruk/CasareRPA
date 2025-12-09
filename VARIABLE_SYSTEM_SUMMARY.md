# Variable System - Quick Reference

## 1. Variable Insertion (Design-Time)

**How variables get into node config**:
1. User enters text in a node property (e.g., "URL" field in LaunchBrowser)
2. Clicks the `{x}` variable button or presses Ctrl+Space
3. **VariablePickerPopup** appears showing available variables
4. User selects a variable (e.g., "website")
5. **VariableAwareLineEdit.insert_variable()** inserts `{{website}}` into the field
6. Node config saves: `{"url": "{{website}}"}`

**Files involved**:
- `presentation/canvas/ui/widgets/variable_picker.py` - UI components
- `presentation/canvas/ui/dialogs/node_properties_dialog.py` - Properties dialog

## 2. Variable Resolution (Runtime)

**How variables are resolved during execution**:
1. Workflow starts, ExecuteWorkflowUseCase initializes variables dict
2. For each node execution:
   - Node calls `self.get_parameter("url")` → returns `"{{website}}"`
   - **CRITICAL**: Node must call `context.resolve_value(url)` to resolve
   - `resolve_value()` calls `resolve_variables("{{website}}", variables_dict)`
   - Function returns actual value (e.g., `"google.com"`)

**Files involved**:
- `domain/services/variable_resolver.py` - `resolve_variables()` function
- `domain/entities/execution_state.py` - `resolve_value()` method
- Individual nodes - must call `context.resolve_value()` in `execute()`

## 3. Where Variables Come From

**VariableProvider sources** (lines 348-391):
```
Variables Dict
├─ Workflow Variables (VariablesTab in bottom panel)
├─ Node Output Variables (from upstream connected nodes)
└─ System Variables ($currentDate, $currentTime, $timestamp, $currentDateTime)
```

## 4. The Critical Gap

**PROBLEM**: Variables in node config are NOT automatically resolved.

```python
# What currently happens:
url = node.get_parameter("url")  # Returns "{{website}}"
await page.goto(url)  # BROKEN: tries to open "{{website}}" literally

# What should happen:
url = node.get_parameter("url")  # Returns "{{website}}"
url = context.resolve_value(url)  # Returns "google.com"
await page.goto(url)  # WORKS
```

**Why this gap exists**:
- `get_parameter()` is synchronous, `context` only available in async `execute()`
- No automatic resolution means every node must handle it manually
- This is error-prone and inconsistent across the codebase

## 5. File Locations

### Core Variable Resolution
- **`domain/services/variable_resolver.py`** - Main resolution logic
  - `resolve_variables(value, variables_dict)` - Core function
  - `_resolve_nested_path(path, variables)` - Handles "node.output" syntax
  - Supports: `{{var}}`, `{{node.output}}`, `{{data[0].name}}`, etc.

### Variable Picker UI
- **`presentation/canvas/ui/widgets/variable_picker.py`** (1887 lines)
  - `VariablePickerPopup` - Modal showing available variables
  - `VariableProvider` - Aggregates workflow + node + system variables
  - `VariableAwareLineEdit` - Text input with variable button
  - `VariableButton` - The `{x}` button that opens picker
  - `VariableInfo` - Data class for variable metadata

### Application-Level Variable Management
- **`application/use_cases/variable_resolver.py`** (592 lines)
  - `VariableResolver` - Transfers data between connected ports
  - `TryCatchErrorHandler` - Captures errors in try-catch blocks

### Runtime State
- **`domain/entities/execution_state.py`**
  - `ExecutionState.resolve_value(value)` - Calls domain resolver
  - Stores `variables` dict during execution

## 6. Variable Types Supported

| Syntax | Example | Resolves To |
|--------|---------|------------|
| Simple variable | `{{website}}` | Value of variable |
| Nested path | `{{node.output}}` | Access nested dict/object |
| List indexing | `{{items[0]}}` | First item in list |
| Complex path | `{{data.users[0].name}}` | Deep navigation |
| Multiple vars | `{{host}}/{{path}}` | String interpolation |
| With text | `https://{{url}}/api` | String with interpolated value |

## 7. How to Use Variables in a Node

```python
async def execute(self, context: IExecutionContext) -> ExecutionResult:
    # Get parameter (may contain {{variable}})
    url = self.get_parameter("url")

    # IMPORTANT: Resolve variables
    url = context.resolve_value(url)

    # Now safe to use
    result = await do_something(url)

    return {"success": True, "data": {"result": result}}
```

## 8. Testing Variable Resolution

```python
from casare_rpa.domain.services.variable_resolver import resolve_variables

# Simple variable
assert resolve_variables("{{x}}", {"x": 42}) == 42

# Nested path
assert resolve_variables("{{obj.key}}", {"obj": {"key": "value"}}) == "value"

# String interpolation
assert resolve_variables("Hello {{name}}", {"name": "World"}) == "Hello World"

# Unresolved variable (preserved)
assert resolve_variables("{{missing}}", {}) == "{{missing}}"
```

## 9. Key Classes Reference

| Class | Location | Purpose |
|-------|----------|---------|
| `VariablePickerPopup` | variable_picker.py:800 | Modal for selecting variables |
| `VariableProvider` | variable_picker.py:285 | Aggregates available variables |
| `VariableAwareLineEdit` | variable_picker.py:1319 | Text input with picker button |
| `VariableButton` | variable_picker.py:1287 | The `{x}` insertion button |
| `VariableInfo` | variable_picker.py:224 | Variable metadata (name, type, source) |
| `VariableResolver` | application/use_cases/variable_resolver.py:58 | Port-to-port data transfer |
| `ExecutionState` | domain/entities/execution_state.py:17 | Runtime variable storage |

## 10. Design-Time vs Runtime

### Design-Time (When editing workflow)
- User inserts `{{website}}` via variable picker
- Stored literally in node config as string
- NO resolution happens
- Display shows: `"{{website}}"`

### Runtime (When executing workflow)
- ExecutionState has variables dict: `{"website": "google.com", ...}`
- Node calls `context.resolve_value("{{website}}")`
- Function replaces with actual value
- Node receives: `"google.com"`

## 11. Drag-and-Drop Support

**VariableAwareLineEdit** accepts drops from:
- MIME type: `application/x-casare-variable` (from Node Output Inspector)
- Plain text: `{{variableName}}` format

Example:
```python
# Drop handler in VariableAwareLineEdit.dropEvent()
variable_text = mime_data.data("application/x-casare-variable")
self.insert_variable(variable_text)  # Inserts at cursor position
```

## 12. Common Mistakes

### ❌ Don't Do This
```python
# In node's execute():
url = self.get_parameter("url")
result = await browser.goto(url)  # FAILS if url contains {{variable}}
```

### ✅ Do This
```python
# In node's execute():
url = self.get_parameter("url")
url = context.resolve_value(url)  # ← RESOLVES variables
result = await browser.goto(url)  # WORKS
```

---

**Bottom Line**: Variables are a two-phase system:
1. **Presentation** - User inserts `{{varName}}` into config
2. **Runtime** - Node calls `context.resolve_value()` to get actual value
