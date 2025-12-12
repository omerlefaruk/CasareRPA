"""Visual nodes for variable category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.ui.theme import TYPE_COLORS


# Map variable_type choices to TYPE_COLORS keys
TYPE_NAME_MAP = {
    "String": "String",
    "Boolean": "Boolean",
    "Int32": "Integer",
    "Float": "Float",
    "Object": "Dict",
    "Array": "List",
    "List": "List",
    "Dict": "Dict",
    "FilePath": "String",
    "DataTable": "DataTable",
}


class VisualSetVariableNode(VisualNode):
    """Visual representation of SetVariableNode."""

    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Set Variable"
    NODE_CATEGORY = "variable"

    def __init__(self) -> None:
        """Initialize set variable node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on SetVariableNode
        # Add value widget manually using custom wrapper (PropertyType.ANY not auto-generated)
        self._setup_value_widget()
        # Don't collapse - users need to see the value input
        # Must be called after widgets are added
        self._collapsed = True  # Reset to allow set_collapsed to work
        self.set_collapsed(False)

    def _setup_value_widget(self) -> None:
        """
        Set up the value input widget using the custom styled wrapper.

        Uses VariableAwareLineEdit wrapper for theme consistency and
        connects to variable_type changes for dynamic border coloring.
        """
        # Use the variable-aware text input method from base class
        # This creates a properly styled widget with variable picker integration
        self._add_variable_aware_text_input(
            name="default_value",
            label="Value",
            text="",
            placeholder_text="Enter value...",
            tab="properties",
            tooltip="Default value if no input provided",
        )

        # Store reference to the value widget for dynamic styling
        self._value_widget = self.get_widget("default_value")

        # Apply initial type-based styling
        self._update_value_input_style("String")

    def setup_widgets(self) -> None:
        """
        Setup custom widgets for this node.

        Connects the variable_type dropdown to update value input styling.
        Called during node initialization after ports are created.
        """
        super().setup_widgets()

        # Connect variable_type changes to update styling
        # This is called after _auto_create_widgets_from_schema creates the dropdown
        # Use deferred connection since combo widget isn't created yet
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._connect_type_change_signal)

    def _connect_type_change_signal(self) -> None:
        """Connect variable_type combo box signal to style updater."""
        try:
            # Get the variable_type combo widget
            type_widget = self.get_widget("variable_type")
            if type_widget and hasattr(type_widget, "get_custom_widget"):
                combo = type_widget.get_custom_widget()
                if combo and hasattr(combo, "currentTextChanged"):
                    combo.currentTextChanged.connect(self._on_variable_type_changed)
                    # Apply initial styling based on current selection
                    current_type = combo.currentText()
                    if current_type:
                        self._update_value_input_style(current_type)
        except Exception:
            pass  # Widget not yet available, styling will use default

    def _on_variable_type_changed(self, type_text: str) -> None:
        """
        Handle variable_type dropdown changes.

        Updates the value input border color based on the selected type.

        Args:
            type_text: Selected type from dropdown (String, Boolean, Int32, etc.)
        """
        self._update_value_input_style(type_text)

    def _update_value_input_style(self, type_text: str) -> None:
        """
        Update value input widget styling based on variable type.

        Applies a type-colored border to provide visual feedback about
        the expected data type for the value.

        Args:
            type_text: Variable type string from dropdown
        """
        if not self._value_widget:
            return

        # Map type_text to TYPE_COLORS key
        color_key = TYPE_NAME_MAP.get(type_text, "Any")
        color_hex = TYPE_COLORS.get(color_key, TYPE_COLORS["Any"])

        try:
            # Get the actual line edit widget
            custom_widget = None
            if hasattr(self._value_widget, "get_custom_widget"):
                custom_widget = self._value_widget.get_custom_widget()
            elif hasattr(self._value_widget, "_line_edit"):
                custom_widget = self._value_widget._line_edit

            if custom_widget and hasattr(custom_widget, "setStyleSheet"):
                # Apply type-colored border with theme-consistent styling
                custom_widget.setStyleSheet(f"""
                    QLineEdit {{
                        background: #18181b; /* Zinc 900 */
                        border: 2px solid {color_hex};
                        border-radius: 4px;
                        color: #f4f4f5; /* Zinc 100 */
                        padding: 4px 28px 4px 8px;
                        selection-background-color: #4338ca; /* Indigo 700 */
                    }}
                    QLineEdit:focus {{
                        background: #27272a; /* Zinc 800 */
                        border: 2px solid {color_hex};
                        box-shadow: 0 0 0 2px {color_hex}40;
                    }}
                """)
        except Exception:
            pass  # Silently fail if widget not ready

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("value", DataType.ANY)
        self.add_typed_input("variable_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)


class VisualGetVariableNode(VisualNode):
    """Visual representation of GetVariableNode."""

    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Get Variable"
    NODE_CATEGORY = "variable"

    def __init__(self) -> None:
        """Initialize get variable node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on GetVariableNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("variable_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)


class VisualIncrementVariableNode(VisualNode):
    """Visual representation of IncrementVariableNode."""

    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Increment Variable"
    NODE_CATEGORY = "variable"

    def __init__(self) -> None:
        """Initialize increment variable node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on IncrementVariableNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("variable_name", DataType.STRING)
        self.add_typed_input("increment", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.FLOAT)


# Control Flow Nodes
