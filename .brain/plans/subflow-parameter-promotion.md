# Subflow Parameter Promotion

## Goal
Allow users to expose internal node parameters at the subflow level, so they can configure nodes without diving into the subflow.

## Current State
- `SubflowPort` has `internal_node_id` and `internal_port_name` - designed for PORT exposure
- Node parameters use `PropertyDef` via `@node_schema` decorator
- No mechanism exists to promote CONFIG PARAMETERS (not ports) to subflow interface

## Key Distinction
- **Ports**: Data flow between nodes (already supported via SubflowPort)
- **Parameters**: Node configuration (url, timeout, selector, etc.) - NOT exposed currently

---

## Open Questions - RESOLVED

### 1. Naming conflicts: What if two internal nodes have same property name?

**Resolution**: Use QUALIFIED naming with optional alias.

```python
# Default: Automatic qualified name
"navigate_123_url"  # {short_node_id}_{property_name}

# User can override with explicit alias
"login_url"  # Custom alias set during promotion
```

**Storage**: Store both `qualified_name` (for uniqueness) and `display_name` (alias):
```python
@dataclass
class SubflowParameter:
    name: str                    # Unique qualified name (node_id_property)
    display_name: str            # User-facing alias (can be same as name)
    ...
```

### 2. Nested subflows: Can A expose B's promoted params?

**Resolution**: YES - with controlled chaining.

When subflow A contains subflow B:
1. A can expose B's promoted parameters
2. Creates a CHAIN reference: `A.param -> B.param -> B.internal_node.property`
3. Max chain depth = 2 (A exposes B's param, but B cannot expose C's promoted param)

**Storage**: Use `chain` field for nested promotion:
```python
@dataclass
class SubflowParameter:
    ...
    chain: Optional[List[str]] = None  # ["subflow_b_id", "param_name"] for nested
```

### 3. Default override: Should subflow default override node default?

**Resolution**: Use PRECEDENCE chain (highest priority first):

1. Value set on SubflowNode instance (user input at usage site)
2. SubflowParameter.default_value (defined during promotion)
3. Internal node's PropertyDef.default (original default)

This allows:
- Subflow author to set reasonable defaults for their context
- User to override when using the subflow

### 4. Validation: Re-validate when promoted param changes data type?

**Resolution**: NO type changes allowed after promotion.

- Promoted parameters LOCK their type from source PropertyDef
- If internal node schema changes type, promotion becomes INVALID
- Validation surfaces this as WARNING in subflow editor
- User must re-promote or fix internal node

---

## Proposed Solution

### 1. Domain Layer Changes

**New: `SubflowParameter` dataclass** in `domain/entities/subflow.py`
```python
from dataclasses import dataclass, field
from typing import Any, List, Optional

from casare_rpa.domain.schemas.property_types import PropertyType


@dataclass
class SubflowParameter:
    """
    Definition of a promoted parameter exposed at the subflow level.

    Maps a subflow-level parameter to an internal node's configuration property.
    Allows users to configure internal nodes without opening the subflow editor.
    """

    # Identity
    name: str                          # Unique qualified name (e.g., "navigate_123_url")
    display_name: str                  # User-facing label (e.g., "Login URL")

    # Mapping to internal node
    internal_node_id: str              # Which internal node owns this property
    internal_property_name: str        # Property name on the internal node

    # Type info (locked from source PropertyDef)
    property_type: PropertyType        # STRING, INTEGER, FILE_PATH, etc.

    # Value handling
    default_value: Any = None          # Override for internal node's default

    # UI configuration
    label: str = ""                    # UI label (falls back to display_name)
    description: str = ""              # Tooltip text
    placeholder: str = ""              # Placeholder for input widgets

    # Validation
    required: bool = False             # Whether value must be provided
    min_value: Optional[float] = None  # For numeric types
    max_value: Optional[float] = None  # For numeric types
    choices: Optional[List[str]] = None  # For CHOICE type

    # Nested subflow chaining
    chain: Optional[List[str]] = None  # For nested promotion: ["subflow_id", "param_name"]

    def __post_init__(self) -> None:
        """Validate and set defaults after initialization."""
        if not self.label:
            self.label = self.display_name

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "internal_node_id": self.internal_node_id,
            "internal_property_name": self.internal_property_name,
            "property_type": self.property_type.value if isinstance(self.property_type, PropertyType) else self.property_type,
            "default_value": self.default_value,
            "label": self.label,
            "description": self.description,
            "placeholder": self.placeholder,
            "required": self.required,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "choices": self.choices,
            "chain": self.chain,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SubflowParameter":
        """Create from dictionary."""
        property_type_str = data.get("property_type", "string")
        try:
            property_type = PropertyType(property_type_str) if isinstance(property_type_str, str) else property_type_str
        except ValueError:
            property_type = PropertyType.STRING

        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", data.get("name", "")),
            internal_node_id=data.get("internal_node_id", ""),
            internal_property_name=data.get("internal_property_name", ""),
            property_type=property_type,
            default_value=data.get("default_value"),
            label=data.get("label", ""),
            description=data.get("description", ""),
            placeholder=data.get("placeholder", ""),
            required=data.get("required", False),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            choices=data.get("choices"),
            chain=data.get("chain"),
        )

    def to_property_def(self) -> "PropertyDef":
        """
        Convert to PropertyDef for widget generation.

        Returns:
            PropertyDef matching this parameter's configuration
        """
        from casare_rpa.domain.schemas.property_schema import PropertyDef

        return PropertyDef(
            name=self.name,
            type=self.property_type,
            default=self.default_value,
            label=self.label or self.display_name,
            placeholder=self.placeholder,
            choices=self.choices,
            tooltip=self.description,
            required=self.required,
            min_value=self.min_value,
            max_value=self.max_value,
        )
```

**Extend `Subflow` dataclass**:
```python
@dataclass
class Subflow:
    ...
    # Add new field
    parameters: List[SubflowParameter] = field(default_factory=list)

    def add_parameter(self, param: SubflowParameter) -> None:
        """Add a promoted parameter to the subflow."""
        if any(p.name == param.name for p in self.parameters):
            raise ValueError(f"Parameter '{param.name}' already exists")
        self.parameters.append(param)
        self._touch()

    def remove_parameter(self, param_name: str) -> bool:
        """Remove a promoted parameter by name."""
        for i, param in enumerate(self.parameters):
            if param.name == param_name:
                self.parameters.pop(i)
                self._touch()
                return True
        return False

    def get_parameter(self, param_name: str) -> Optional[SubflowParameter]:
        """Get a promoted parameter by name."""
        for param in self.parameters:
            if param.name == param_name:
                return param
        return None

    def validate_parameters(self) -> List[str]:
        """
        Validate that all promoted parameters still reference valid internal nodes.

        Returns:
            List of warning messages for invalid parameters
        """
        warnings = []
        for param in self.parameters:
            if param.internal_node_id not in self.nodes:
                warnings.append(
                    f"Parameter '{param.display_name}' references missing node '{param.internal_node_id}'"
                )
        return warnings
```

Update `to_dict()` and `from_dict()`:
```python
def to_dict(self) -> Dict[str, Any]:
    return {
        ...
        "parameters": [p.to_dict() for p in self.parameters],
    }

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Subflow":
    ...
    parameters = [
        SubflowParameter.from_dict(p)
        for p in data.get("parameters", [])
    ]
    ...
```

### 2. Execution Layer Changes

**`SubflowExecutor._inject_promoted_parameters()`**:
```python
def _inject_promoted_parameters(
    self,
    subflow: Subflow,
    param_values: Dict[str, Any],
    context: ExecutionContext,
) -> None:
    """
    Inject promoted parameter values into internal nodes before execution.

    Args:
        subflow: Subflow being executed
        param_values: Values for promoted parameters (from SubflowNode config)
        context: Execution context for variable resolution
    """
    for param in subflow.parameters:
        # Determine value with precedence: user input > subflow default > node default
        value = param_values.get(param.name)
        if value is None:
            value = param.default_value

        if value is None:
            continue  # No value to inject, let node use its own default

        # Handle variable references
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            value = context.get_variable(var_name, value)

        # Handle nested subflow chains
        if param.chain:
            # param.chain = ["nested_subflow_id", "nested_param_name"]
            # Will be resolved during nested subflow execution
            context.set_variable(f"_promoted_{param.name}", value)
            continue

        # Get internal node and inject value into its config
        internal_node_id = param.internal_node_id
        if internal_node_id in self._node_instances:
            node = self._node_instances[internal_node_id]
            node.config[param.internal_property_name] = value
            logger.debug(
                f"Injected promoted param '{param.display_name}' = {repr(value)[:50]} "
                f"into {internal_node_id}.{param.internal_property_name}"
            )
        else:
            # Node not yet instantiated - store in context for lazy injection
            context.set_variable(
                f"_promoted_{internal_node_id}_{param.internal_property_name}",
                value
            )
```

**Update `execute()` method**:
```python
async def execute(
    self,
    subflow: Subflow,
    inputs: Dict[str, Any],
    context: ExecutionContext,
    param_values: Optional[Dict[str, Any]] = None,  # NEW: promoted parameter values
) -> SubflowExecutionResult:
    ...
    # After creating internal_context, inject promoted parameters
    if param_values:
        self._inject_promoted_parameters(subflow, param_values, internal_context)
    ...
```

### 3. SubflowNode Changes

**Dynamic property generation** in `configure_from_subflow()`:
```python
def configure_from_subflow(self, subflow: Subflow) -> None:
    """Configure node from subflow definition including promoted parameters."""
    ...

    # Generate PropertyDefs from promoted parameters
    self._promoted_property_defs = []
    for param in subflow.parameters:
        prop_def = param.to_property_def()
        self._promoted_property_defs.append(prop_def)

        # Store default in config if not already set
        if param.name not in self.config:
            self.config[param.name] = param.default_value

def get_promoted_properties(self) -> List[PropertyDef]:
    """Get list of promoted property definitions for widget generation."""
    return getattr(self, "_promoted_property_defs", [])
```

**Update `execute()` to pass promoted values**:
```python
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    ...
    # Collect promoted parameter values from config
    param_values = {}
    if self._subflow:
        for param in self._subflow.parameters:
            if param.name in self.config:
                param_values[param.name] = self.config[param.name]

    # Execute with SubflowExecutor
    executor = SubflowExecutor()
    result = await executor.execute(
        subflow_data,
        inputs,
        context,
        param_values=param_values  # Pass promoted values
    )
    ...
```

### 4. Presentation Layer - SubflowVisualNode

**Widget generation for promoted parameters**:
```python
def configure_from_subflow(self, subflow) -> None:
    """Configure visual node including promoted parameter widgets."""
    ...

    # Add widgets for promoted parameters
    self._add_promoted_parameter_widgets(subflow.parameters)

def _add_promoted_parameter_widgets(self, parameters: List[SubflowParameter]) -> None:
    """
    Add input widgets for promoted parameters.

    Creates widgets based on property_type, mirroring how regular
    node properties generate widgets.
    """
    from casare_rpa.presentation.canvas.graph.node_widgets import (
        create_widget_for_property,
    )

    for param in parameters:
        prop_def = param.to_property_def()

        try:
            # Create widget using standard factory
            widget = create_widget_for_property(prop_def)
            if widget:
                self.add_custom_widget(
                    widget,
                    param.name,
                    tab="parameters"  # Separate tab for promoted params
                )

                # Set initial value from config
                if hasattr(self, "_casare_node") and self._casare_node:
                    value = self._casare_node.config.get(param.name, param.default_value)
                    if hasattr(widget, "set_value"):
                        widget.set_value(value)
        except Exception as e:
            logger.warning(f"Failed to create widget for param '{param.name}': {e}")
```

### 5. Parameter Promotion Dialog

**New File**: `presentation/canvas/ui/dialogs/parameter_promotion_dialog.py`

```python
"""
Parameter Promotion Dialog for Subflow Editor.

Allows users to select which internal node properties to expose
at the subflow level for external configuration.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QCheckBox, QFormLayout,
    QDialogButtonBox, QGroupBox, QComboBox, QMessageBox,
)
from PySide6.QtCore import Qt

from loguru import logger

from casare_rpa.domain.entities.subflow import Subflow, SubflowParameter
from casare_rpa.domain.schemas.property_types import PropertyType


class ParameterPromotionDialog(QDialog):
    """
    Dialog for promoting internal node parameters to subflow level.

    Features:
    - Tree view of internal nodes and their properties
    - Checkbox to select properties for promotion
    - Alias input for user-friendly names
    - Default value override
    - Preview of promoted parameters
    """

    def __init__(
        self,
        subflow: Subflow,
        node_schemas: Dict[str, Any],  # node_id -> schema with properties
        parent=None,
    ):
        super().__init__(parent)
        self.subflow = subflow
        self.node_schemas = node_schemas

        # Track selections: {qualified_name: SubflowParameter}
        self._selections: Dict[str, SubflowParameter] = {}

        # Populate existing promoted params
        for param in subflow.parameters:
            self._selections[param.name] = param

        self._setup_ui()
        self._populate_tree()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Promote Parameters to Subflow")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select properties from internal nodes to expose at the subflow level.\n"
            "Users can then configure these properties without opening the subflow."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Split view: tree on left, config on right
        split_layout = QHBoxLayout()

        # Left: Tree of nodes and properties
        tree_group = QGroupBox("Internal Nodes")
        tree_layout = QVBoxLayout(tree_group)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Property", "Type", "Current Value"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 100)
        self.tree.itemChanged.connect(self._on_item_changed)
        tree_layout.addWidget(self.tree)

        split_layout.addWidget(tree_group, stretch=2)

        # Right: Configuration for selected parameter
        config_group = QGroupBox("Parameter Configuration")
        self.config_layout = QFormLayout(config_group)

        self.alias_input = QLineEdit()
        self.alias_input.setPlaceholderText("User-friendly name")
        self.config_layout.addRow("Display Name:", self.alias_input)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Tooltip description")
        self.config_layout.addRow("Description:", self.description_input)

        self.default_input = QLineEdit()
        self.default_input.setPlaceholderText("Override default value")
        self.config_layout.addRow("Default Value:", self.default_input)

        self.required_check = QCheckBox("Required")
        self.config_layout.addRow("", self.required_check)

        split_layout.addWidget(config_group, stretch=1)

        layout.addLayout(split_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_tree(self) -> None:
        """Populate tree with internal nodes and their properties."""
        self.tree.clear()

        for node_id, node_data in self.subflow.nodes.items():
            node_type = node_data.get("node_type") or node_data.get("type_", "")
            node_name = node_data.get("name", node_type)

            # Create node item
            node_item = QTreeWidgetItem([node_name, "", ""])
            node_item.setData(0, Qt.ItemDataRole.UserRole, {"node_id": node_id})
            node_item.setFlags(node_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

            # Get schema for this node type
            schema = self.node_schemas.get(node_type)
            if not schema:
                # Try to get properties from node_data directly
                properties = node_data.get("properties", node_data.get("custom", {}))
                self._add_properties_from_dict(node_item, node_id, properties)
            else:
                self._add_properties_from_schema(node_item, node_id, schema, node_data)

            self.tree.addTopLevelItem(node_item)
            node_item.setExpanded(True)

    def _add_properties_from_schema(
        self,
        parent_item: QTreeWidgetItem,
        node_id: str,
        schema: Any,
        node_data: dict,
    ) -> None:
        """Add property items from node schema."""
        if not hasattr(schema, "properties"):
            return

        config = node_data.get("properties", node_data.get("custom", {}))

        for prop_def in schema.properties:
            qualified_name = f"{node_id[:8]}_{prop_def.name}"
            current_value = config.get(prop_def.name, prop_def.default)

            prop_item = QTreeWidgetItem([
                prop_def.name,
                prop_def.type.value if hasattr(prop_def.type, "value") else str(prop_def.type),
                str(current_value)[:30] if current_value else "",
            ])
            prop_item.setFlags(prop_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            prop_item.setCheckState(0, Qt.CheckState.Unchecked)

            # Check if already promoted
            if qualified_name in self._selections:
                prop_item.setCheckState(0, Qt.CheckState.Checked)

            prop_item.setData(0, Qt.ItemDataRole.UserRole, {
                "node_id": node_id,
                "property_name": prop_def.name,
                "property_type": prop_def.type,
                "default_value": prop_def.default,
                "qualified_name": qualified_name,
            })

            parent_item.addChild(prop_item)

    def _add_properties_from_dict(
        self,
        parent_item: QTreeWidgetItem,
        node_id: str,
        properties: dict,
    ) -> None:
        """Add property items from dictionary (fallback)."""
        for prop_name, prop_value in properties.items():
            if prop_name.startswith("_"):
                continue

            qualified_name = f"{node_id[:8]}_{prop_name}"

            # Infer type from value
            if isinstance(prop_value, bool):
                prop_type = PropertyType.BOOLEAN
            elif isinstance(prop_value, int):
                prop_type = PropertyType.INTEGER
            elif isinstance(prop_value, float):
                prop_type = PropertyType.FLOAT
            else:
                prop_type = PropertyType.STRING

            prop_item = QTreeWidgetItem([
                prop_name,
                prop_type.value,
                str(prop_value)[:30] if prop_value else "",
            ])
            prop_item.setFlags(prop_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            prop_item.setCheckState(0, Qt.CheckState.Unchecked)

            if qualified_name in self._selections:
                prop_item.setCheckState(0, Qt.CheckState.Checked)

            prop_item.setData(0, Qt.ItemDataRole.UserRole, {
                "node_id": node_id,
                "property_name": prop_name,
                "property_type": prop_type,
                "default_value": prop_value,
                "qualified_name": qualified_name,
            })

            parent_item.addChild(prop_item)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle checkbox state changes."""
        if column != 0:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or "property_name" not in data:
            return

        qualified_name = data["qualified_name"]

        if item.checkState(0) == Qt.CheckState.Checked:
            # Add to selections
            param = SubflowParameter(
                name=qualified_name,
                display_name=data["property_name"].replace("_", " ").title(),
                internal_node_id=data["node_id"],
                internal_property_name=data["property_name"],
                property_type=data["property_type"],
                default_value=data["default_value"],
            )
            self._selections[qualified_name] = param

            # Update config panel
            self.alias_input.setText(param.display_name)
            self.default_input.setText(str(param.default_value) if param.default_value else "")
        else:
            # Remove from selections
            self._selections.pop(qualified_name, None)

    def get_promoted_parameters(self) -> List[SubflowParameter]:
        """Get the list of promoted parameters."""
        # Apply any pending edits
        return list(self._selections.values())
```

### 6. Serialization Format

**Subflow JSON** with parameters:
```json
{
  "$schema_version": "1.1.0",
  "id": "subflow_abc123",
  "name": "Login Sequence",
  "version": "1.0.0",
  "inputs": [...],
  "outputs": [...],
  "parameters": [
    {
      "name": "navigate_123_url",
      "display_name": "Login URL",
      "internal_node_id": "navigate_123",
      "internal_property_name": "url",
      "property_type": "string",
      "default_value": "https://example.com/login",
      "label": "Login URL",
      "description": "URL to navigate to for login",
      "placeholder": "https://...",
      "required": true,
      "min_value": null,
      "max_value": null,
      "choices": null,
      "chain": null
    },
    {
      "name": "type_456_text",
      "display_name": "Username",
      "internal_node_id": "type_456",
      "internal_property_name": "text",
      "property_type": "string",
      "default_value": "",
      "label": "Username",
      "description": "Username to enter",
      "placeholder": "",
      "required": true,
      "min_value": null,
      "max_value": null,
      "choices": null,
      "chain": null
    }
  ],
  "nodes": {...},
  "connections": [...]
}
```

---

## Implementation Order

### Phase 1: Domain Layer (Foundation)
1. Add `SubflowParameter` dataclass to `domain/entities/subflow.py`
2. Extend `Subflow` with `parameters` field and helper methods
3. Update `to_dict()` / `from_dict()` for serialization
4. Add `validate_parameters()` method

**Files Modified:**
- `src/casare_rpa/domain/entities/subflow.py`

### Phase 2: Execution Layer (Core Logic)
1. Add `_inject_promoted_parameters()` to `SubflowExecutor`
2. Update `execute()` signature to accept `param_values`
3. Handle variable resolution in parameter injection

**Files Modified:**
- `src/casare_rpa/application/use_cases/subflow_executor.py`

### Phase 3: Node Layer (SubflowNode)
1. Add `get_promoted_properties()` method
2. Update `configure_from_subflow()` to build property defs
3. Update `execute()` to collect and pass promoted values

**Files Modified:**
- `src/casare_rpa/nodes/subflow_node.py`

### Phase 4: Presentation Layer (Visual)
1. Update `SubflowVisualNode.configure_from_subflow()` to add widgets
2. Add `_add_promoted_parameter_widgets()` method
3. Add widget factory integration

**Files Modified:**
- `src/casare_rpa/presentation/canvas/visual_nodes/subflow_visual_node.py`
- `src/casare_rpa/presentation/canvas/visual_nodes/subflows/nodes.py`

### Phase 5: Dialog (UI for Promotion)
1. Create `ParameterPromotionDialog` class
2. Add tree view for node/property selection
3. Add configuration panel for aliases and defaults
4. Integrate with subflow editor context menu

**Files Created:**
- `src/casare_rpa/presentation/canvas/ui/dialogs/parameter_promotion_dialog.py`

### Phase 6: Integration & Testing
1. Add "Promote Parameters" action to subflow editor
2. Wire dialog to save promoted params to subflow
3. Test end-to-end flow

---

## Files Summary

### Modified Files
| File | Changes |
|------|---------|
| `domain/entities/subflow.py` | Add SubflowParameter, extend Subflow |
| `application/use_cases/subflow_executor.py` | Inject promoted params before execution |
| `nodes/subflow_node.py` | Dynamic property creation from subflow.parameters |
| `presentation/canvas/visual_nodes/subflow_visual_node.py` | Widget generation for parameters |
| `presentation/canvas/visual_nodes/subflows/nodes.py` | Same widget generation |

### New Files
| File | Purpose |
|------|---------|
| `presentation/canvas/ui/dialogs/parameter_promotion_dialog.py` | UI for selecting params to promote |

---

## Edge Cases

### 1. Same property name on multiple nodes
**Scenario**: Two NavigateNodes both have `url` property.
**Handling**: Qualified names prevent collision: `navigate_123_url` vs `navigate_456_url`.
**User can set distinct display names**: "Login URL" vs "Dashboard URL".

### 2. Nested subflow parameter chaining
**Scenario**: Subflow A contains Subflow B. B has promoted param `login_url`. A wants to expose it.
**Handling**:
- A's parameter has `chain: ["subflow_b_id", "login_url"]`
- During A's execution, value is stored as `_promoted_login_url`
- When B executes, B's executor reads from context and injects

### 3. Type compatibility
**Scenario**: Internal node changes property from STRING to INTEGER.
**Handling**:
- `validate_parameters()` checks if internal node still exists
- Type mismatch detected during serialization/deserialization
- Warning surfaced in subflow editor
- User must re-promote or update internal node

### 4. Deleted internal node
**Scenario**: User deletes internal node that has promoted parameters.
**Handling**:
- `validate_parameters()` returns warning
- Promoted parameter marked as ORPHANED
- Dialog shows warning, user can remove orphaned params

### 5. Variable references
**Scenario**: User enters `${workflow.url}` as promoted parameter value.
**Handling**:
- Value stored as-is in SubflowNode.config
- Resolved during `_inject_promoted_parameters()` using context
- Supports both literal values and variable references

---

## Acceptance Criteria

1. **Promote Parameter**: User can select internal node properties and promote them to subflow interface
2. **Configure at Usage**: When using SubflowNode, user sees widgets for promoted parameters
3. **Values Injected**: Promoted values correctly override internal node configs during execution
4. **Serialization**: Promoted parameters saved/loaded correctly from subflow JSON
5. **Validation**: Orphaned/invalid promotions detected and reported
6. **Nested Support**: Subflows containing subflows can chain parameter promotion (depth=2)

---

*Last Updated: 2025-12-08*
