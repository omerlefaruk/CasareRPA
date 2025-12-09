# Variable System - Code Reference Guide

## Core Files with Line Numbers

### 1. Main Resolution Engine
**File**: `src/casare_rpa/domain/services/variable_resolver.py`

| What | Line Range | What It Does |
|------|------------|------------|
| `VARIABLE_PATTERN` regex | 16-17 | Matches `{{variable}}` syntax |
| `_resolve_nested_path()` | 30-94 | Resolves "node.output" style paths |
| `resolve_variables()` | 97-187 | **Main function** - replaces variables with values |
| `resolve_dict_variables()` | 190-216 | Resolves all strings in a dict |
| `extract_variable_names()` | 219-236 | Gets list of variable names in string |
| `has_variables()` | 239-252 | Quick check for `{{` in string |

**Key Code**:
```python
# Lines 97-187
def resolve_variables(value: Any, variables: Dict[str, Any]) -> Any:
    """Replace {{variable_name}} patterns with actual values."""
    if not isinstance(value, str):
        return value  # Only strings are processed

    if "{{" not in value:
        return value  # Fast path

    # Check if entire value is single {{variable}}
    single_var_match = SINGLE_VAR_PATTERN.match(value.strip())
    if single_var_match:
        var_path = single_var_match.group(1)
        if var_path in variables:
            return variables[var_path]  # Type preserved
        # Try nested path
        resolved = _resolve_nested_path(var_path, variables)
        if resolved is not None:
            return resolved
        return value  # Keep if not found

    # Multiple variables or text - do string replacement
    return VARIABLE_PATTERN.sub(replace_match, value)
```

---

### 2. Presentation Layer - Variable Picker
**File**: `src/casare_rpa/presentation/canvas/ui/widgets/variable_picker.py` (1887 lines)

| Class | Lines | Purpose |
|-------|-------|---------|
| `VariableInfo` | 224-278 | Data class for variable metadata |
| `VariableProvider` | 285-759 | Aggregates all available variables |
| `HighlightDelegate` | 767-792 | Custom delegate for selection highlight |
| `VariablePickerPopup` | 800-1280 | Modal popup showing variable tree |
| `VariableButton` | 1287-1312 | The `{x}` button |
| `VariableAwareLineEdit` | 1319-1874 | Text input with variable support |

#### VariableButton
```python
# Lines 1287-1312
class VariableButton(QPushButton):
    """Small '{x}' button that appears on hover for variable insertion."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("{x}", parent)
        self.setFixedSize(22, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Insert variable (Ctrl+Space)")
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self) -> None:
        self.clicked_for_popup.emit()
```

#### VariableAwareLineEdit - Insert Variable
```python
# Lines 1589-1612
def insert_variable(self, var_text: str) -> None:
    """
    Insert variable text at cursor position.

    Examples:
    - Input: var_text = "{{Send Hotkey.success}}"
    - Result: Field contains "{{Send Hotkey.success}}"
    """
    cursor_pos = self.cursorPosition()
    current_text = self.text()

    # Check if we should replace {{ prefix
    if cursor_pos >= 2 and current_text[cursor_pos - 2 : cursor_pos] == "{{":
        new_text = (
            current_text[: cursor_pos - 2] + var_text + current_text[cursor_pos:]
        )
        self.setText(new_text)
        self.setCursorPosition(cursor_pos - 2 + len(var_text))
    else:
        self.insert(var_text)
```

#### VariableAwareLineEdit - Drag and Drop
```python
# Lines 1447-1483
def dropEvent(self, event) -> None:
    """Handle drop - insert variable at cursor position."""
    import json as json_module

    mime_data = event.mimeData()
    variable_text = None

    # Try custom MIME type first
    if mime_data.hasFormat(self.VARIABLE_MIME_TYPE):
        try:
            data_bytes = mime_data.data(self.VARIABLE_MIME_TYPE)
            data_str = bytes(data_bytes).decode("utf-8")
            data = json_module.loads(data_str)
            variable_text = data.get("variable", "")
        except Exception as e:
            logger.debug(f"Failed to parse variable drag data: {e}")

    # Fall back to plain text
    if not variable_text and mime_data.hasText():
        text = mime_data.text()
        if text.startswith("{{") and text.endswith("}}"):
            variable_text = text

    if variable_text:
        self.insert_variable(variable_text)
        self.variable_inserted.emit(variable_text)
        event.acceptProposedAction()
    else:
        event.ignore()
```

#### VariableProvider - Get All Variables
```python
# Lines 348-391
def get_all_variables(
    self,
    current_node_id: Optional[str] = None,
    graph: Optional[Any] = None,
) -> List[VariableInfo]:
    """Get all available variables."""
    variables: List[VariableInfo] = []

    # 1. Add custom/workflow variables
    variables.extend(self._custom_variables.values())

    # 2. Get variables from bottom panel VariablesTab
    panel_vars = self._get_panel_variables()
    variables.extend(panel_vars)

    # 3. Try workflow controller (legacy support)
    if self._workflow_controller and not panel_vars:
        try:
            wf_vars = self._get_workflow_controller_variables()
            variables.extend(wf_vars)
        except Exception as e:
            logger.debug(f"Could not get workflow controller variables: {e}")

    # 4. Get upstream node output variables
    if current_node_id and graph:
        try:
            upstream_vars = self.get_node_output_variables(current_node_id, graph)
            variables.extend(upstream_vars)
        except Exception as e:
            logger.debug(f"Could not get upstream node variables: {e}")

    # 5. Add system variables
    variables.extend(self._get_system_variables())

    return variables
```

#### VariableProvider - Get Node Output Variables
```python
# Lines 461-536
def get_node_output_variables(
    self,
    current_node_id: str,
    graph: Any,
) -> List[VariableInfo]:
    """Get output variables from upstream connected nodes."""
    if not graph:
        return []

    variables: List[VariableInfo] = []

    try:
        # Find the current node
        current_node = None
        for node in graph.all_nodes():
            node_id = node.id() if hasattr(node, "id") else None
            prop_id = (
                node.get_property("node_id")
                if hasattr(node, "get_property")
                else None
            )
            if node_id == current_node_id or prop_id == current_node_id:
                current_node = node
                break

        if not current_node:
            return []

        # Find all upstream nodes
        upstream_nodes = self._get_upstream_nodes(current_node, set())

        # Get output ports from each upstream node
        for upstream_node in upstream_nodes:
            node_name = (
                upstream_node.name()
                if hasattr(upstream_node, "name")
                else "Unknown"
            )

            for port in upstream_node.output_ports():
                port_name = port.name()

                # Skip exec ports
                if self._is_exec_port(port_name, upstream_node):
                    continue

                # Get port data type
                data_type = self._get_port_data_type(port_name, upstream_node)

                var_info = VariableInfo(
                    name=port_name,
                    var_type=data_type,
                    source=f"node:{node_name}",
                    value=None,  # Runtime value not available at design time
                    path=f"{node_name}.{port_name}",  # ← Key for nested access
                )

                variables.append(var_info)

    except Exception as e:
        logger.debug(f"Error getting upstream node variables: {e}")

    return variables
```

---

### 3. Runtime Execution - Variable Resolution
**File**: `src/casare_rpa/domain/entities/execution_state.py`

```python
# Lines 192-214
def resolve_value(self, value: Any) -> Any:
    """
    Resolve {{variable_name}} patterns in a value.

    This enables UiPath/Power Automate style variable substitution.
    """
    from casare_rpa.domain.variable_resolver import resolve_variables

    return resolve_variables(value, self.variables)
```

---

### 4. Application Layer - Data Transfer Between Nodes
**File**: `src/casare_rpa/application/use_cases/variable_resolver.py`

| Class/Method | Lines | Purpose |
|-------|-------|---------|
| `VariableResolver.__init__()` | 102-121 | Initialize with pre-built connection index |
| `transfer_data()` | 138-178 | Transfer from source port to target port |
| `transfer_inputs_to_node()` | 180-197 | Transfer all inputs before node executes |
| `TryCatchErrorHandler.capture_error()` | 441-483 | Capture error in try block |

```python
# Lines 138-178
def transfer_data(self, connection: Any) -> None:
    """Transfer data from source port to target port."""
    try:
        source_node = self._get_node(connection.source_node)
        target_node = self._get_node(connection.target_node)
    except ValueError:
        return  # Node not found

    # OUTPUT -> INPUT: Read from source, write to target
    value = source_node.get_output_value(connection.source_port)

    if value is not None:
        target_node.set_input_value(connection.target_port, value)

        # DEBUG LOGGING
        if "exec" not in connection.source_port.lower():
            logger.info(
                f"Data: {connection.source_port} -> {connection.target_port} = {repr(value)[:80]}"
            )
    else:
        # WARNING: Missing data might indicate upstream node bug
        if "exec" not in connection.source_port.lower():
            logger.warning(
                f"Data transfer skipped: source node {source_node.node_id} "
                f"({type(source_node).__name__}) port '{connection.source_port}' has no value"
            )
```

---

### 5. Node Implementation - Getting Parameters
**File**: `src/casare_rpa/domain/entities/base_node.py`

```python
# Lines 226-256
def get_parameter(self, name: str, default: Any = None) -> Any:
    """
    Get parameter value from port (runtime) or config (design-time).

    Dual-source pattern:
    - Port: Runtime value from connection
    - Config: Design-time value from properties panel

    Prefers port value over config value.

    NOTE: Does NOT resolve {{variable}} syntax!
    Nodes must call context.resolve_value() manually.
    """
    # Check port first (runtime value from connection)
    port_value = self.get_input_value(name)
    if port_value is not None:
        return port_value

    # Fallback to config (design-time value from properties panel)
    return self.config.get(name, default)
```

---

### 6. Example Node Usage - Variable Nodes
**File**: `src/casare_rpa/nodes/variable_nodes.py`

```python
# Lines 110-120 (SetVariableNode example)
async def execute(self, context: IExecutionContext) -> ExecutionResult:
    """Set a variable in the execution context."""
    name = self.get_parameter("name")
    value = self.get_parameter("value")

    # CORRECT: Resolve variables in value
    value = resolve_variables(value, context.variables)

    # Store in context
    context.set_variable(name, value)

    return {"success": True, "data": {"variable_set": name}}
```

---

## Quick Reference: Where to Find Things

### I want to...

**Add a variable to the picker**
→ `VariableProvider.add_variable()` (line 336)
→ Set up in MainWindow initialization

**Insert a variable from popup**
→ `VariablePickerPopup._on_item_clicked()` (line 1168)
→ Emits `variable_selected` signal with `{{varName}}`

**Resolve variables in a node**
→ Call `context.resolve_value(value)` in node's `execute()` method
→ Or import and call `resolve_variables(value, context.variables)` directly

**Check if string has variables**
→ Import `has_variables()` from `domain/services/variable_resolver.py`
→ Example: `if has_variables(url): ...`

**Extract variable names from string**
→ Import `extract_variable_names()` from `domain/services/variable_resolver.py`
→ Returns: `["var1", "var2"]` from `"{{var1}}/{{var2}}"`

**Make a widget accept variables**
→ Use `VariableAwareLineEdit` instead of plain `QLineEdit`
→ Or use `_replace_widget_with_variable_aware()` to convert existing widget

**Handle nested variable paths**
→ `_resolve_nested_path()` (line 30 in variable_resolver.py)
→ Handles: `"node.output"`, `"data[0].field"`, `"obj.nested.deep"`

---

## Pattern Regex Reference

```python
# Main pattern (line 16-18)
VARIABLE_PATTERN = re.compile(
    r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}"
)

# Single variable detection (line 25-27)
SINGLE_VAR_PATTERN = re.compile(
    r"^\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}$"
)

# Path segment parsing (line 21)
PATH_SEGMENT_PATTERN = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_]*)|\[(\d+)\]")
```

---

## Type Preservation Examples

```python
from casare_rpa.domain.services.variable_resolver import resolve_variables

variables = {
    "count": 42,
    "name": "John",
    "active": True,
    "data": {"key": "value"},
    "items": ["a", "b", "c"]
}

# Single variable → Original type preserved
resolve_variables("{{count}}", variables)  # → 42 (int)
resolve_variables("{{active}}", variables)  # → True (bool)
resolve_variables("{{data}}", variables)  # → {"key": "value"} (dict)

# Text around variable → String returned
resolve_variables("Count: {{count}}", variables)  # → "Count: 42" (str)
resolve_variables("{{count}} items", variables)  # → "42 items" (str)

# Multiple variables → String returned
resolve_variables("{{name}}/{{count}}", variables)  # → "John/42" (str)

# Nested path → Actual value
resolve_variables("{{data.key}}", variables)  # → "value" (str)
resolve_variables("{{items[0]}}", variables)  # → "a" (str)

# Unresolved → Preserved
resolve_variables("{{missing}}", variables)  # → "{{missing}}" (str)
```

---

## Complete Execution Flow

```
1. Design-Time
   User clicks {x} button
   ↓
   VariablePickerPopup.show()
   ↓
   User selects "website"
   ↓
   VariablePickerPopup.variable_selected.emit("{{website}}")
   ↓
   VariableAwareLineEdit.insert_variable("{{website}}")
   ↓
   Field now contains: "{{website}}"
   ↓
   User clicks OK
   ↓
   Node config saved: {"url": "{{website}}"}

2. Runtime
   ExecuteWorkflowUseCase.execute()
   ↓
   Initialize: context.variables = {"website": "google.com"}
   ↓
   NodeExecutor.execute(LaunchBrowserNode)
   ↓
   LaunchBrowserNode.execute(context):
     url = self.get_parameter("url")  # → "{{website}}"
     url = context.resolve_value(url)  # → "google.com"
     await page.goto(url)  # Opens google.com
```
