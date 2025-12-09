# CasareRPA Variable System - Complete Exploration Report

## Executive Summary

The CasareRPA variable system uses a **two-phase resolution model**:

1. **Design-Time (Presentation)**: Variables are displayed and inserted via UI widgets using the `{{variableName}}` syntax
2. **Runtime (Application/Domain)**: Variables are actually resolved using `resolve_variables()` function before nodes execute

**KEY GAP IDENTIFIED**: Variables in node config values are NOT automatically resolved. They display as literal `{{var}}` unless explicitly resolved by the node's execute() method or via input ports.

---

## 1. How the MMB (Middle Mouse Button) Menu Works

### Current Implementation
**Status**: Not found in the codebase. The system uses a **variable button (`{x}`)** instead.

### The Variable Button Pattern
Located in: `presentation/canvas/ui/widgets/variable_picker.py`

**VariableButton Class** (lines 1287-1312):
```python
class VariableButton(QPushButton):
    """Small '{x}' button that appears on hover for variable insertion."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("{x}", parent)
        self.setFixedSize(22, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Insert variable (Ctrl+Space)")
```

**Trigger Methods**:
1. **Click the `{x}` button** → Opens VariablePickerPopup
2. **Ctrl+Space** → Opens VariablePickerPopup (keyboard shortcut)
3. **Drag from Output Inspector** → Drops variable via drag-and-drop

---

## 2. How Variables Are Inserted Into Input Parameter Widgets

### Flow: Dragging a Variable to a Widget

#### Step 1: Variable Picker Popup Shows Available Variables
**VariablePickerPopup** (line 800+):
- Shows hierarchical tree of variables grouped by source:
  - **VARIABLES** - Workflow variables from VariablesTab
  - **FROM: NodeName** - Output ports from upstream connected nodes
  - **SYSTEM** - System variables ($currentDate, $currentTime, etc.)

#### Step 2: User Selects Variable from Popup
**Selection Handler** (line 1168-1175):
```python
def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
    var = item.data(0, Qt.ItemDataRole.UserRole)
    if var and isinstance(var, VariableInfo):
        # Emits: variable_selected(str) with insertion text like "{{varName}}"
        self.variable_selected.emit(var.insertion_text)
        self.close()
```

#### Step 3: Variable Text Is Inserted Into Widget
**VariableAwareLineEdit.insert_variable()** (line 1589-1612):
```python
def insert_variable(self, var_text: str) -> None:
    """
    Insert variable text at cursor position.

    Examples:
    - Input: var_text = "{{Send Hotkey.success}}"
    - Cursor at end of field
    - Result: Field now contains "{{Send Hotkey.success}}"
    """
    cursor_pos = self.cursorPosition()
    current_text = self.text()

    # If cursor is right after "{{", replace that prefix
    if cursor_pos >= 2 and current_text[cursor_pos - 2 : cursor_pos] == "{{":
        new_text = (
            current_text[: cursor_pos - 2] + var_text + current_text[cursor_pos:]
        )
        self.setText(new_text)
    else:
        # Simple insert at cursor position
        self.insert(var_text)
```

### Drag-and-Drop Support
**VariableAwareLineEdit.dropEvent()** (line 1447-1483):
```python
def dropEvent(self, event) -> None:
    """Handle drop - insert variable at cursor position."""
    mime_data = event.mimeData()
    variable_text = None

    # Try custom MIME type first (from Node Output Inspector)
    if mime_data.hasFormat(self.VARIABLE_MIME_TYPE):
        data_bytes = mime_data.data(self.VARIABLE_MIME_TYPE)
        data_str = bytes(data_bytes).decode("utf-8")
        data = json_module.loads(data_str)
        variable_text = data.get("variable", "")

    # Fall back to plain text
    if not variable_text and mime_data.hasText():
        text = mime_data.text()
        if text.startswith("{{") and text.endswith("}}"):
            variable_text = text

    if variable_text:
        self.insert_variable(variable_text)
        self.variable_inserted.emit(variable_text)
```

### Which Widgets Support Variables?
1. **VariableAwareLineEdit** - Text input with variable picker button
2. **SelectorInputWidget** - For selector/xpath properties
3. **ValidatedInputWidget** - Text input with validation
4. **File path, credential, and other input widgets**

---

## 3. Where Variable Resolution Happens

### Design-Time vs Runtime Resolution

#### Design-Time (Presentation Layer)
- Variables display as literal text `{{varName}}` in node properties
- No resolution occurs - this is just text storage
- The variable picker only helps with **insertion**, not resolution

#### Runtime (Domain Layer) - THE ACTUAL RESOLUTION
**Location**: `domain/services/variable_resolver.py` (lines 97-187)

**Key Function**: `resolve_variables(value, variables)`
```python
def resolve_variables(value: Any, variables: Dict[str, Any]) -> Any:
    """
    Replace {{variable_name}} patterns with actual values from variables dict.

    Type Preservation:
    - Single {{variable}} → returns original type (bool, int, dict, etc.)
    - Text around variable → returns string with interpolated value

    Examples:
        resolve_variables("https://{{website}}", {"website": "google.com"})
        → "https://google.com"

        resolve_variables("{{is_valid}}", {"is_valid": True})
        → True  (type preserved)
    """
    # Fast path: no variables to resolve
    if "{{" not in value:
        return value

    # Check if entire value is a single variable reference
    # Pre-compiled pattern: ^\{\{\s*([...]*)\s*\}\}$
    single_var_match = SINGLE_VAR_PATTERN.match(value.strip())
    if single_var_match:
        var_path = single_var_match.group(1)

        # Try direct lookup: variables["varName"]
        if var_path in variables:
            return variables[var_path]  # Type preserved

        # Try nested path: "node.output" or "data.field[0].name"
        resolved = _resolve_nested_path(var_path, variables)
        if resolved is not None:
            return resolved

        # Variable not found - return original string
        return value

    # Multiple variables or text around variable
    # Do string replacement: "Hello {{name}}" → "Hello World"
    return VARIABLE_PATTERN.sub(replace_match, value)
```

### Where resolve_variables() Is Called

#### 1. **Execution State Resolve** (domain/entities/execution_state.py:192-214)
```python
def resolve_value(self, value: Any) -> Any:
    """
    Resolve {{variable_name}} patterns in a value.

    Used during workflow execution to resolve node parameters.
    """
    from casare_rpa.domain.variable_resolver import resolve_variables
    return resolve_variables(value, self.variables)
```

#### 2. **Variable Nodes** (nodes/variable_nodes.py)
```python
# In SetVariableNode.execute():
value = resolve_variables(value, context.variables)
context.set_variable(name, value)
```

#### 3. **Environment Management** (application/use_cases/environment_management.py:465)
```python
variables = EnvironmentStorage.resolve_variables_with_inheritance(...)
```

### CRITICAL GAP: Where Variables Are NOT Resolved

**Problem**: Variables in node config are stored as literal strings like `"{{varName}}"` and NOT automatically resolved.

**Flow**:
1. User enters `{{website}}` in "URL" field of LaunchBrowser node
2. Node config gets: `{"url": "{{website}}"}`
3. During execution, node calls: `url = self.get_parameter("url")`
4. Returns: `"{{website}}"` (LITERAL STRING, NOT RESOLVED)
5. Playwright receives: `"https://{{website}}/"` (BROKEN URL)

**Solution Required**: Nodes must explicitly call `context.resolve_value()` before using config values:
```python
# Current (WRONG):
url = self.get_parameter("url")  # Returns "{{website}}"

# Correct:
url = self.get_parameter("url")  # Returns "{{website}}"
url = context.resolve_value(url)  # Returns "google.com"
```

---

## 4. Variable Resolver Architecture

### Application Layer: `application/use_cases/variable_resolver.py`

**VariableResolver Class** (lines 58-412):
```python
class VariableResolver:
    """
    Resolves and transfers data between nodes.

    Two main responsibilities:
    1. Transfer data from source output ports to target input ports
    2. Validate output ports have values after execution
    """

    def transfer_data(self, connection) -> None:
        """Transfer from source_node.output_port → target_node.input_port"""
        source_node = self._get_node(connection.source_node)
        target_node = self._get_node(connection.target_node)

        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)

        # Set it on target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)

    def transfer_inputs_to_node(self, node_id: str) -> None:
        """
        Transfer all input data to a node from connected sources.
        Called BEFORE node executes.
        """
        for connection in self._incoming_connections.get(node_id, []):
            self.transfer_data(connection)
```

**TryCatchErrorHandler Class** (lines 414-591):
```python
class TryCatchErrorHandler:
    """
    Handles try-catch block error capture and routing.

    When error occurs inside try block:
    1. capture_error() stores it in try_state variable
    2. TryEndNode checks for errors
    3. Routes to CatchNode if error exists
    """

    def capture_error(
        self, error_msg: str, error_type: str, exception: Exception
    ) -> bool:
        """Check if inside try block and capture error if so."""
        # Look for active try_state variable
        for key, value in list(self.context.variables.items()):
            if key.endswith("_try_state") and isinstance(value, dict):
                # Store error details for CatchNode to access
                value["error"] = True
                value["error_type"] = error_type
                value["error_message"] = error_msg
                value["stack_trace"] = stack_trace
                return True
        return False
```

### Domain Layer: `domain/services/variable_resolver.py`

**Core Functions**:
1. `resolve_variables(value, variables)` - Main resolution engine
2. `_resolve_nested_path(path, variables)` - Handles "node.output" syntax
3. `resolve_dict_variables(data, variables)` - Resolves all strings in a dict
4. `extract_variable_names(value)` - Gets list of variable names in string
5. `has_variables(value)` - Quick check if string contains variables

**Nested Path Resolution** (lines 30-94):
```python
def _resolve_nested_path(path: str, variables: Dict[str, Any]) -> Any:
    """
    Resolve paths like "read.content" or "users[0].name".

    Examples:
        path = "node_output.field"
        variables = {"node_output": {"field": "value"}}
        → "value"

        path = "items[0].name"
        variables = {"items": [{"name": "Item1"}]}
        → "Item1"
    """
    # Split root from path: "read.content" → root="read", remainder=".content"
    # Navigate using regex: \.([key]) or \[(\d+)\]
    # Handles both dict access and list indexing
```

---

## 5. Variable Picker Widget Deep Dive

### VariableProvider (lines 285-759)
**Responsibility**: Aggregate all available variables for the picker popup

**Data Sources**:
1. **Workflow Variables** - From VariablesTab in bottom panel
2. **Node Output Variables** - From upstream connected nodes
3. **System Variables** - Date, time, timestamp

**Key Methods**:
```python
def get_all_variables(
    self,
    current_node_id: Optional[str] = None,
    graph: Optional[Any] = None,
) -> List[VariableInfo]:
    """
    Get all available variables.

    Combines:
    - Custom/workflow variables from _get_panel_variables()
    - Upstream node outputs from get_node_output_variables()
    - System variables from _get_system_variables()
    """

def get_node_output_variables(
    self,
    current_node_id: str,
    graph: Any,
) -> List[VariableInfo]:
    """
    Get output variables from upstream connected nodes.

    Traverses execution flow backwards to find nodes connecting via exec_in port.
    Returns VariableInfo for each output port of those nodes.
    """
    # Find current node in graph
    current_node = graph.all_nodes() where node_id matches

    # Recursively find upstream nodes via _get_upstream_nodes()
    upstream_nodes = self._get_upstream_nodes(current_node, set())

    # Collect output ports from each upstream node
    for upstream_node in upstream_nodes:
        for port in upstream_node.output_ports():
            # Skip exec ports (flow control only)
            if self._is_exec_port(port_name):
                continue

            # Get port data type and create VariableInfo
            var_info = VariableInfo(
                name=port_name,
                var_type=data_type,
                source=f"node:{node_name}",
                path=f"{node_name}.{port_name}",  # ← For "node.output" syntax
            )
```

### VariableInfo (lines 224-278)
```python
@dataclass
class VariableInfo:
    """Information about a variable available for insertion."""

    name: str                           # e.g., "success"
    var_type: str = "Any"              # Type badge: String, Integer, Boolean, etc.
    source: str = "workflow"            # Where variable comes from
    value: Optional[Any] = None         # Current value for preview
    children: List["VariableInfo"] = field(default_factory=list)  # For dicts/lists
    path: Optional[str] = None          # Full path: "data.name" for nested
    is_expandable: bool = False         # Can expand dict/list

    @property
    def insertion_text(self) -> str:
        """Get the text to insert (wrapped in {{ }})."""
        return f"{{{{{self.display_name}}}}}"  # e.g., "{{Send Hotkey.success}}"
```

### VariablePickerPopup (lines 800-1280)
**UI Component**: Modal popup showing variable tree

**Features**:
- Search box with fuzzy matching
- Hierarchical tree grouped by source
- Type badges (T for String, # for Integer, etc.)
- Keyboard navigation (arrows, Enter, Escape)
- Click-outside-to-close
- Value preview tooltips

**Fuzzy Matching** (lines 163-216):
```python
def fuzzy_match(pattern: str, text: str) -> tuple[bool, int]:
    """
    Fuzzy matching with scoring.

    Scoring (higher = better match):
    - Exact match: 1000
    - Starts with: 500 + length
    - Contains: 200 + position
    - Fuzzy (all chars in order): 100 + consecutive bonus
    """
```

### VariableAwareLineEdit (lines 1319-1874)
**Enhanced Text Input** with variable insertion

**Features**:
- Variable button (`{x}`) always visible
- Ctrl+Space opens picker
- Drag-and-drop from Node Output Inspector
- Inline validation with visual feedback
- Custom validators support

**Validation** (lines 1638-1783):
```python
def add_validator(self, validator) -> None:
    """
    Add validator for inline validation.

    Validators called on editingFinished.
    First failure stops validation.

    Example validator:
    def url_validator(value: str) -> ValidationResult:
        if not value.startswith("http"):
            return ValidationResult.invalid("Must be HTTP(S) URL")
        return ValidationResult.valid()
    """

def _set_validation_visual(self, status: str, message: str) -> None:
    """
    Update visual state based on validation status.
    - Valid: Normal border
    - Invalid: Red border
    - Warning: Orange border
    """
```

---

## 6. Integration with Input Widgets

### Widgets That Support Variables

#### 1. **SelectorInputWidget** (`presentation/canvas/ui/widgets/selector_input_widget.py`)
```python
class SelectorInputWidget(QWidget):
    """QLineEdit with UI Explorer button for selector properties."""

    # Supports properties: selector, xpath, css_selector, anchor_selector, etc.
    # When value contains "{{var}}", it displays literally
    # No automatic resolution at design-time
```

#### 2. **ValidatedInputWidget** (`presentation/canvas/ui/widgets/validated_input.py`)
```python
class ValidatedInputWidget(QWidget):
    """
    Container with validation message display.

    Layout:
    [Input Widget]
    [Validation message]
    """

    def add_validator(self, validator: ValidatorFunc) -> None:
        """Add custom validation logic."""
```

#### 3. **VariableEditorWidget** (mentioned in file list)
- For editing workflow variables definitions
- Not for variable insertion into node properties

### Node Properties Dialog
**Location**: `presentation/canvas/ui/dialogs/node_properties_dialog.py`

- Creates property widgets for node config values
- Properties can contain `{{variable}}` syntax
- NO automatic resolution when displaying values
- Values are stored as-is and passed to node execution

---

## 7. Complete Variable Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  DESIGN-TIME (User Editing Workflow in Canvas)              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User: Right-click LaunchBrowser node → "Properties"        │
│         ↓                                                    │
│  NodePropertiesDialog shows property widgets                │
│    ├─ "url" field currently shows: "{{website}}"           │
│    └─ User clicks variable button {x}                      │
│         ↓                                                    │
│  VariablePickerPopup appears showing:                      │
│    ├─ VARIABLES                                            │
│    │   └─ website: String                                  │
│    ├─ FROM: JsonParser                                     │
│    │   └─ result: Dict                                     │
│    └─ SYSTEM                                               │
│        └─ $currentDate: String                             │
│                                                              │
│  User selects "website"                                     │
│         ↓                                                    │
│  VariableAwareLineEdit.insert_variable("{{website}}")       │
│  Field now shows: "{{website}}"                            │
│                                                              │
│  User clicks OK                                             │
│         ↓                                                    │
│  Node config saved: {"url": "{{website}}"}                 │
│  (NO RESOLUTION HAPPENS HERE)                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  RUNTIME (Workflow Execution)                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ExecuteWorkflowUseCase.execute()                           │
│    ├─ Create ExecutionContext with initial variables       │
│    ├─ Set context.variables = {"website": "google.com"} ← KEY
│    └─ Start node execution loop                            │
│                                                              │
│  NodeExecutor.execute(LaunchBrowserNode)                    │
│    ├─ Validate node                                        │
│    ├─ Call node.execute(context)                           │
│    │                                                        │
│    └─ LaunchBrowserNode.execute(context):                  │
│         ├─ url = self.get_parameter("url")                 │
│         │   → Returns: "{{website}}" (STILL LITERAL)       │
│         │                                                  │
│         ├─ url = context.resolve_value(url)  ← NEEDED!    │
│         │   → resolve_variables("{{website}}", variables)  │
│         │   → Finds: variables["website"] = "google.com"  │
│         │   → Returns: "google.com"                        │
│         │                                                  │
│         └─ await playwright_page.goto(url)                 │
│             Opens: google.com  ✓ WORKS                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Variable Resolution Pattern Details

### Pattern Syntax Supported

**File**: `domain/services/variable_resolver.py:16-17`

```python
# Regex pattern matches:
VARIABLE_PATTERN = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}"

# Supports:
{{variable}}                 # Simple: variables["variable"]
{{node.output}}              # Nested path: variables["node"]["output"]
{{data.nested.path}}         # Deep nesting
{{list[0]}}                  # List indexing
{{dict.key[0].nested}}       # Complex paths
{{ variable }}               # Whitespace allowed
```

### Type Preservation

```python
# Single variable → TYPE PRESERVED
resolve_variables("{{is_valid}}", {"is_valid": True})
→ True  (boolean, not string "True")

resolve_variables("{{count}}", {"count": 42})
→ 42  (integer, not string "42")

resolve_variables("{{data}}", {"data": {"key": "value"}})
→ {"key": "value"}  (dict, not stringified)

# Text around variable → STRING RETURNED
resolve_variables("Count: {{count}}", {"count": 42})
→ "Count: 42"  (string, because of surrounding text)

resolve_variables("{{url}}/path", {"url": "https://example.com"})
→ "https://example.com/path"  (string)
```

---

## 9. Key Architecture Gaps & Design Issues

### Gap 1: No Automatic Variable Resolution in Node Config

**Problem**:
- Variables in node config display as literal `{{var}}` during execution
- Each node must manually call `context.resolve_value()` on config values
- This is error-prone and leads to nodes showing literal variable syntax

**Current Status**:
- ✗ Not implemented in BaseNode.get_parameter()
- ✓ Properly implemented when data flows via ports (VariableResolver.transfer_data())
- ✓ Some nodes handle it correctly (e.g., SetVariableNode)
- ✗ Many nodes likely skip this step

**Solution**:
```python
# In BaseNode.get_parameter(), auto-resolve config values:
def get_parameter(self, name: str, default: Any = None) -> Any:
    # Check port first (already transferred if via connection)
    port_value = self.get_input_value(name)
    if port_value is not None:
        return port_value

    # Get from config
    config_value = self.config.get(name, default)

    # MISSING: No automatic resolution
    # Should be: return context.resolve_value(config_value)
    # But context is not available here (architectural issue)

    return config_value
```

### Gap 2: Nodes Don't Have Access to ExecutionContext During get_parameter()

**Problem**:
- `get_parameter()` is a synchronous method in BaseNode
- ExecutionContext is only available in `execute()` method
- Therefore, config values cannot be resolved in get_parameter()

**Current Workaround**:
Each node's `execute()` must manually resolve:
```python
async def execute(self, context: IExecutionContext) -> ExecutionResult:
    # Pattern used by variable-aware nodes:
    url = self.get_parameter("url")
    url = context.resolve_value(url)  ← Manual resolution
    # ... rest of execution
```

### Gap 3: Variable Display Shows Literal Syntax

**Issue**:
- When viewing node properties, variables show as `{{varName}}`
- This looks like an error to users
- No visual feedback that this will be resolved at runtime

**Better UX**:
- Show "(variable)" badge next to field
- Or show resolved value in tooltip
- Or highlight with special styling

---

## 10. Complete File Map

### Presentation Layer
| File | Purpose | Key Classes |
|------|---------|-------------|
| `presentation/canvas/ui/widgets/variable_picker.py` | Variable picker UI | VariablePickerPopup, VariableProvider, VariableButton, VariableAwareLineEdit |
| `presentation/canvas/ui/widgets/validated_input.py` | Validated input fields | ValidatedLineEdit, ValidatedInputWidget |
| `presentation/canvas/ui/widgets/selector_input_widget.py` | Selector picker | SelectorInputWidget |
| `presentation/canvas/ui/dialogs/node_properties_dialog.py` | Node properties UI | NodePropertiesDialog |

### Application Layer
| File | Purpose | Key Classes |
|------|---------|-------------|
| `application/use_cases/variable_resolver.py` | Runtime variable/data transfer | VariableResolver, TryCatchErrorHandler |
| `application/use_cases/execute_workflow.py` | Workflow orchestration | ExecuteWorkflowUseCase |
| `application/use_cases/node_executor.py` | Node execution lifecycle | NodeExecutor, NodeExecutorWithTryCatch |

### Domain Layer
| File | Purpose | Key Functions |
|------|---------|-------------|
| `domain/services/variable_resolver.py` | Core variable resolution | resolve_variables(), _resolve_nested_path(), resolve_dict_variables() |
| `domain/entities/execution_state.py` | Runtime state & variable storage | ExecutionState.resolve_value() |
| `domain/entities/base_node.py` | Base node class | BaseNode.get_parameter() |

### Infrastructure Layer
| File | Purpose |
|------|---------|
| `infrastructure/execution/context.py` | Execution context with resources |

---

## 11. Testing & Validation

### Variable Resolution Tests
```python
# Test file location (if it exists):
# tests/domain/services/test_variable_resolver.py

# Test cases to verify:
def test_simple_variable_resolution():
    assert resolve_variables("{{x}}", {"x": 42}) == 42

def test_nested_path_resolution():
    assert resolve_variables("{{node.output}}",
                            {"node": {"output": "value"}}) == "value"

def test_list_indexing():
    assert resolve_variables("{{items[0]}}",
                            {"items": ["first", "second"]}) == "first"

def test_string_interpolation():
    assert resolve_variables("Hello {{name}}",
                            {"name": "World"}) == "Hello World"

def test_unresolved_variable_preserved():
    # When variable not found, keep original syntax
    assert resolve_variables("{{missing}}", {}) == "{{missing}}"
```

### Variable Picker Tests
```python
# Should test:
1. Fuzzy matching logic
2. Upstream node detection
3. Variable grouping by source
4. Nested variable expansion
5. Drag-and-drop MIME handling
6. Keyboard navigation (up/down/enter/escape)
```

---

## 12. Recommendations for Variable Display

### Add Visual Feedback for Variables in Config

```python
# In VariableAwareLineEdit.insert_variable():
# When variable is inserted, optionally:
1. Show a tooltip with resolved value
2. Add background highlight
3. Show special styling (italic or color)
```

### Auto-Resolve at Display Time

```python
# In NodePropertiesDialog:
# When showing config values, resolve them for display:

def _load_properties(self):
    for key, value in self.properties.items():
        if isinstance(value, str) and "{{" in value:
            # Display: "{{website}}" with tooltip "→ google.com"
            resolved = self.context.resolve_value(value)
            self._display_value_with_resolution_hint(key, value, resolved)
```

### Validation for Unresolvable Variables

```python
# In VariableAwareLineEdit._run_validation():
# When editing finishes, check if variable exists:

def _validate_variables(self, value: str) -> ValidationResult:
    variables = self._provider.get_all_variables()
    var_names = extract_variable_names(value)

    for var_name in var_names:
        if var_name not in variables:
            return ValidationResult.warning(
                f"Variable '{var_name}' not found - will use literal value"
            )

    return ValidationResult.valid()
```

---

## Summary

### Variable System in 3 Layers

1. **Presentation** (variable_picker.py)
   - Shows available variables
   - Allows insertion via popup or drag-drop
   - Displays literal `{{varName}}` in widgets

2. **Application** (variable_resolver.py)
   - Transfers data between connected ports
   - Captures try-catch errors
   - Provides *_safe() variants for error handling

3. **Domain** (domain/services/variable_resolver.py)
   - `resolve_variables()` - The core resolution engine
   - Supports nested paths, list indexing
   - Type-preserving for single variables

### Critical Issue
**Variables in node config are NOT automatically resolved.**
Nodes must call `context.resolve_value(config_value)` manually in execute().

### File Structure
- **Pick variables**: Use VariablePickerPopup + VariableAwareLineEdit
- **Resolve at runtime**: Call context.resolve_value() in execute()
- **Validate during design**: Check variable names exist in VariableProvider
