"""
Subflow Visual Nodes for CasareRPA.

Provides the visual representation for subflow nodes on the canvas.
A SubflowNode encapsulates a reusable workflow fragment.
"""

from typing import Optional, Dict, Any, List

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.subflow_node_item import SubflowNodeItem
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.theme import THEME


# =============================================================================
# Promoted Parameter Widget with Variable Picker + Editable Label
# =============================================================================


def _get_promoted_param_style() -> str:
    """Get the styled stylesheet for promoted parameter inputs."""
    return f"""
QLineEdit {{
    background: {THEME.bg_medium};
    border: 1px solid {THEME.border_light};
    border-radius: 3px;
    color: {THEME.text_primary};
    padding: 2px 28px 2px 4px;
    selection-background-color: {THEME.accent_primary}99;
}}
QLineEdit:focus {{
    background: {THEME.bg_lighter};
    border: 1px solid {THEME.accent_primary};
}}
"""


def _get_editable_label_style() -> str:
    """Get the styled stylesheet for editable labels."""
    return f"""
QLabel {{
    color: {THEME.text_secondary};
    font-size: 11px;
    padding: 2px 0px;
}}
QLabel:hover {{
    color: {THEME.text_primary};
    text-decoration: underline;
}}
"""


class EditableLabel(QLabel):
    """
    Label that can be double-clicked to rename.

    Emits renamed signal when user finishes editing.
    """

    renamed = Signal(str, str)  # (old_name, new_name)

    def __init__(self, text: str, param_name: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._param_name = param_name
        self._editing = False
        self._line_edit: Optional[QLineEdit] = None
        self.setStyleSheet(_get_editable_label_style())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Double-click to rename")

    def mouseDoubleClickEvent(self, event):
        """Start editing on double-click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_editing()
        else:
            super().mouseDoubleClickEvent(event)

    def _start_editing(self):
        """Replace label with line edit for renaming."""
        if self._editing:
            return
        self._editing = True

        # Create inline editor
        self._line_edit = QLineEdit(self.text(), self.parent())
        self._line_edit.setStyleSheet("""
            QLineEdit {
                background: #3c3c50;
                border: 1px solid #0078d4;
                border-radius: 3px;
                color: #ffffff;
                padding: 2px 4px;
                font-size: 11px;
            }
        """)
        self._line_edit.setFixedWidth(self.width() + 40)
        self._line_edit.move(self.pos())
        self._line_edit.show()
        self._line_edit.setFocus()
        self._line_edit.selectAll()

        # Connect signals
        self._line_edit.editingFinished.connect(self._finish_editing)
        self._line_edit.returnPressed.connect(self._finish_editing)

        # Hide label while editing
        self.hide()

    def _finish_editing(self):
        """Finish editing and update label."""
        if not self._editing or not self._line_edit:
            return

        new_text = self._line_edit.text().strip()
        old_text = self.text()

        if new_text and new_text != old_text:
            self.setText(new_text)
            self.renamed.emit(self._param_name, new_text)

        # Cleanup
        self._line_edit.deleteLater()
        self._line_edit = None
        self._editing = False
        self.show()


class VisualSubflowNode(VisualNode):
    """
    Visual node representing a subflow (reusable workflow fragment).

    This node dynamically configures its ports based on the loaded subflow
    definition. It shows a distinctive visual style to indicate it contains
    an embedded workflow.
    """

    __identifier__ = "casare_rpa.subflows"
    NODE_NAME = "Subflow"
    NODE_CATEGORY = "subflows"

    def __init__(self) -> None:
        """Initialize the subflow visual node with custom SubflowNodeItem."""
        # Use SubflowNodeItem for dashed border, gear button, expand button
        super().__init__(qgraphics_item=SubflowNodeItem)

        # Internal properties stored as instance variables (no widgets)
        self._internal_subflow_id = ""
        self._internal_subflow_path = ""
        self._internal_subflow_name = ""
        self._internal_node_count = 0

        # Track if subflow has been configured
        self._subflow_configured = False

        # Reference to the Subflow entity
        self._subflow_entity = None

        # Apply distinctive styling for subflows
        self._apply_subflow_styling()

        # Remove any auto-created widgets for internal properties
        self._hide_internal_property_widgets()

        # Ensure back-reference from view to node for button clicks
        if hasattr(self, "view") and self.view is not None:
            self.view._node = self

    def _ensure_property(self, name: str, default_value, hidden: bool = False) -> None:
        """
        Create property only if it doesn't already exist.

        Args:
            name: Property name
            default_value: Default value
            hidden: If True, don't create a widget for this property
        """
        try:
            # Check if property exists
            if name not in self.model.custom_properties:
                if hidden:
                    # Create property without widget (widget_type=0 means HIDDEN)
                    self._safe_create_property(name, default_value, widget_type=0)
                else:
                    self._safe_create_property(name, default_value)
        except Exception:
            # Fallback: try to create and ignore if exists
            try:
                if hidden:
                    self._safe_create_property(name, default_value, widget_type=0)
                else:
                    self._safe_create_property(name, default_value)
            except Exception:
                pass  # Property already exists

    def set_property(self, name: str, value, push_undo: bool = True) -> None:
        """
        Override set_property to handle internal properties and display name.

        This ensures internal properties are stored as instance variables
        (no widgets created) while still updating the backing casare_node's
        config for execution.
        """
        # Handle internal properties - store as instance variables, not as visible widgets
        if name == "subflow_id":
            self._internal_subflow_id = value
            # Also update casare_node config for execution
            if hasattr(self, "_casare_node") and self._casare_node:
                self._casare_node.config["subflow_id"] = value
            return
        elif name == "subflow_path":
            self._internal_subflow_path = value
            # Also update casare_node config for execution
            if hasattr(self, "_casare_node") and self._casare_node:
                self._casare_node.config["subflow_path"] = value
            return
        elif name == "subflow_name":
            self._internal_subflow_name = value
            self.set_name(f"Subflow: {value}")
            return
        elif name == "node_count":
            self._internal_node_count = value
            return

        super().set_property(name, value, push_undo)

    def get_property(self, name: str):
        """
        Override get_property to handle internal properties.
        """
        # Handle internal properties
        if name == "subflow_id":
            return self._internal_subflow_id
        elif name == "subflow_path":
            return self._internal_subflow_path
        elif name == "subflow_name":
            return self._internal_subflow_name
        elif name == "node_count":
            return self._internal_node_count

        return super().get_property(name)

    def setup_ports(self) -> None:
        """
        Setup default ports.

        Dynamic ports are added when configure_from_subflow() is called.
        """
        # Default exec ports
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("error")

    def configure_from_subflow(self, subflow) -> None:
        """
        Configure node ports and properties from a Subflow entity.

        Adds input/output ports matching the subflow's interface.

        Args:
            subflow: The Subflow entity to configure from
        """
        if self._subflow_configured:
            logger.debug(f"Subflow already configured: {subflow.name}")
            return

        try:
            self._subflow_configured = True

            # Store reference to subflow entity
            self._subflow_entity = subflow

            # Set properties
            self.set_property("subflow_id", subflow.id)
            self.set_property("subflow_name", subflow.name)

            # Calculate and set node count
            node_count = len(subflow.nodes) if hasattr(subflow, "nodes") else 0
            self.set_property("node_count", node_count)

            # Update view with node count for badge display
            if hasattr(self, "view") and self.view is not None:
                if hasattr(self.view, "set_node_count"):
                    self.view.set_node_count(node_count)
                # Ensure back-reference for button clicks
                self.view._node = self

            # Update display name
            self.set_name(f"Subflow: {subflow.name}")

            # Add input ports from subflow
            # SubflowPort now uses DataType enum directly instead of port_type string
            for port in subflow.inputs:
                # Normalize data_type (handles DataType enum or legacy string)
                data_type = self._normalize_data_type(port.data_type)
                self.add_typed_input(port.name, data_type)

            # Add output ports from subflow
            for port in subflow.outputs:
                # Normalize data_type (handles DataType enum or legacy string)
                data_type = self._normalize_data_type(port.data_type)
                self.add_typed_output(port.name, data_type)

            # Re-configure port colors
            self._configure_port_colors()

            # Add widgets for promoted parameters
            if hasattr(subflow, "parameters") and subflow.parameters:
                self._add_promoted_parameter_widgets(subflow.parameters)

            # Update casare node if available
            casare_node = self.get_casare_node()
            if casare_node and hasattr(casare_node, "configure_from_subflow"):
                casare_node.configure_from_subflow(subflow)

            # Hide internal property widgets (ensure they're not visible after config)
            self._hide_internal_property_widgets()

            logger.info(
                f"Configured VisualSubflowNode from subflow '{subflow.name}': "
                f"{len(subflow.inputs)} inputs, {len(subflow.outputs)} outputs, "
                f"{len(subflow.parameters)} parameters"
            )

        except Exception as e:
            logger.error(f"Failed to configure subflow visual node: {e}")

    def _normalize_data_type(self, data_type) -> DataType:
        """
        Normalize data type to DataType enum.

        Handles both DataType enum values and legacy string formats.

        Args:
            data_type: DataType enum, string like "STRING", or None

        Returns:
            Corresponding DataType enum value
        """
        # Already a DataType enum
        if isinstance(data_type, DataType):
            return data_type

        # None or empty - default to ANY
        if not data_type:
            return DataType.ANY

        # Legacy string format
        if isinstance(data_type, str):
            type_map = {
                "STRING": DataType.STRING,
                "INTEGER": DataType.INTEGER,
                "FLOAT": DataType.FLOAT,
                "BOOLEAN": DataType.BOOLEAN,
                "LIST": DataType.LIST,
                "DICT": DataType.DICT,
                "OBJECT": DataType.OBJECT,
                "ANY": DataType.ANY,
                "PAGE": DataType.PAGE,
                "ELEMENT": DataType.ELEMENT,
                "BROWSER": DataType.BROWSER,
            }
            return type_map.get(data_type.upper(), DataType.ANY)

        return DataType.ANY

    def _parse_data_type(self, type_str: Optional[str]) -> DataType:
        """
        Parse data type string to DataType enum.

        DEPRECATED: Use _normalize_data_type() instead.

        Args:
            type_str: Type string like "STRING", "INTEGER", etc.

        Returns:
            Corresponding DataType enum value
        """
        return self._normalize_data_type(type_str)

    def _auto_create_widgets_from_schema(self) -> None:
        """
        Override to skip creating widgets for internal subflow properties.

        The SubflowNode schema defines subflow_id and subflow_path, but these
        should not be visible to users - they are internal properties stored
        as instance variables.
        """
        # Internal properties that should NOT have widgets
        internal_props = {"subflow_id", "subflow_path", "subflow_name", "node_count"}

        if not self._casare_node:
            return

        from casare_rpa.domain.schemas import NodeSchema

        schema: NodeSchema = getattr(
            self._casare_node.__class__, "__node_schema__", None
        )
        if not schema:
            return

        # Filter out internal properties and create widgets for the rest
        for prop_def in schema.properties:
            if prop_def.name in internal_props:
                # Skip internal properties - they're stored as instance variables
                continue

            # Call parent implementation for non-internal properties
            # (but we don't have any other properties in SubflowNode schema)
            # Promoted parameters are added separately via _add_promoted_parameter_widgets()

    def _apply_subflow_styling(self) -> None:
        """Apply distinctive visual styling for subflow nodes."""
        try:
            # Use a distinctive color for subflows (purple/magenta)
            # This helps users identify subflow nodes at a glance
            self.set_color(75, 50, 100)  # Deep purple background

            # Set border color
            self.model.border_color = (180, 100, 200, 255)  # Light purple border

            # Update category on view for header coloring
            if hasattr(self, "view") and self.view is not None:
                if hasattr(self.view, "set_category"):
                    self.view.set_category("subflows")

        except Exception as e:
            logger.debug(f"Could not apply subflow styling: {e}")

    def _hide_internal_property_widgets(self) -> None:
        """
        Remove/hide widgets for internal properties.

        These properties (subflow_id, subflow_path, etc.) should not be
        visible to users - they are for internal use only.
        """
        # List of internal properties that should not have widgets
        internal_props = ["subflow_id", "subflow_path", "subflow_name", "node_count"]

        try:
            # Try to remove widgets from NodeGraphQt model
            if hasattr(self, "model") and self.model:
                # Remove from custom_properties if they exist
                for prop_name in internal_props:
                    if prop_name in self.model.custom_properties:
                        del self.model.custom_properties[prop_name]
                    # Also try removing from _custom_prop_widgets if NodeGraphQt uses that
                    if hasattr(self.model, "_custom_prop_widgets"):
                        if prop_name in self.model._custom_prop_widgets:
                            del self.model._custom_prop_widgets[prop_name]

            # Try to hide widgets from view if they exist
            if hasattr(self, "view") and self.view:
                # NodeGraphQt stores widgets in the view's properties widget
                if hasattr(self.view, "_properties_widget"):
                    props_widget = self.view._properties_widget
                    if props_widget:
                        for prop_name in internal_props:
                            # Try to find and hide widget by name
                            widget = props_widget.findChild(type(None), prop_name)
                            if widget:
                                widget.hide()

        except Exception as e:
            logger.debug(f"Could not hide internal property widgets: {e}")

    def _add_promoted_parameter_widgets(self, parameters: List) -> None:
        """
        Add input widgets for promoted parameters.

        Creates widgets based on property_type, allowing users to configure
        internal node properties from the subflow interface.

        Features:
        - VariableAwareLineEdit with {x} button for variable insertion
        - Double-click label to rename parameter
        - Dark background styling (#3c3c50)

        Args:
            parameters: List of SubflowParameter instances
        """
        from casare_rpa.domain.schemas.property_types import PropertyType

        logger.info(f"Adding {len(parameters)} promoted parameter widgets")

        # First, remove any existing promoted parameter properties to avoid conflicts
        # This handles re-promotion or migration from old naming scheme
        for param in parameters:
            try:
                if hasattr(self, "model") and self.model:
                    if param.name in self.model.custom_properties:
                        del self.model.custom_properties[param.name]
                        logger.debug(f"Removed existing property: {param.name}")
            except Exception as e:
                logger.debug(f"Could not remove existing property {param.name}: {e}")

        for param in parameters:
            try:
                # Get property type
                prop_type = param.property_type
                if isinstance(prop_type, str):
                    try:
                        prop_type = PropertyType(prop_type)
                    except ValueError:
                        prop_type = PropertyType.STRING

                # Create appropriate widget based on type
                label = param.label or param.display_name

                # Get value with precedence:
                # 1. SubflowNode's own config (user-set value on the subflow instance)
                # 2. Internal node's current value from subflow entity
                # 3. Parameter default value
                value = param.default_value

                # First, try to get from internal node's data in subflow entity
                if self._subflow_entity and param.internal_node_id:
                    internal_node_data = self._subflow_entity.nodes.get(
                        param.internal_node_id, {}
                    )
                    # Try different keys for properties
                    properties = (
                        internal_node_data.get("properties", {})
                        or internal_node_data.get("config", {})
                        or internal_node_data.get("custom", {})
                    )
                    internal_val = properties.get(param.internal_property_name)
                    if internal_val is not None:
                        value = internal_val

                # Then, check if user has overridden on this SubflowNode instance
                if hasattr(self, "_casare_node") and self._casare_node:
                    config_val = self._casare_node.config.get(param.name)
                    if config_val is not None:
                        value = config_val

                logger.debug(
                    f"Creating widget for: {param.name}, type={prop_type}, label={label}, value={value}"
                )

                if prop_type == PropertyType.BOOLEAN:
                    self.add_checkbox(
                        param.name,
                        label="",  # No group box title
                        text=label,  # Text next to checkbox
                        state=bool(value) if value else False,
                    )
                elif prop_type == PropertyType.CHOICE and param.choices:
                    self.add_combo_menu(
                        param.name,
                        label,
                        items=param.choices,
                    )
                else:
                    # STRING, INTEGER, FLOAT, FILE_PATH - use VariableAwareLineEdit
                    placeholder = ""
                    if prop_type == PropertyType.FILE_PATH:
                        placeholder = "File path..."
                    elif hasattr(param, "placeholder") and param.placeholder:
                        placeholder = param.placeholder

                    self._add_variable_aware_widget(
                        param.name,
                        label,
                        text=str(value) if value is not None else "",
                        placeholder_text=placeholder,
                    )

                logger.info(
                    f"Added widget for promoted parameter: {param.name} ({prop_type})"
                )

            except Exception as e:
                logger.error(
                    f"Failed to add widget for parameter '{param.name}': {e}",
                    exc_info=True,
                )

        # Trigger visual refresh
        if hasattr(self, "view") and self.view is not None:
            self.view.update()

    def _add_variable_aware_widget(
        self,
        name: str,
        label: str,
        text: str = "",
        placeholder_text: str = "",
    ) -> None:
        """
        Add a promoted parameter widget with variable picker support.

        Uses the base class _add_variable_aware_text_input method which properly
        creates and attaches VariableAwareLineEdit widgets with {x} button.

        Features:
        - {x} button for variable picker
        - Dark background styling (#3c3c50)

        Args:
            name: Property name
            label: Display label
            text: Initial text value
            placeholder_text: Placeholder when empty
        """
        # Use base class method that properly handles VariableAwareLineEdit
        widget = self._add_variable_aware_text_input(
            name=name,
            label=label,
            text=text,
            placeholder_text=placeholder_text,
            tab="Properties",
        )

        # Apply promoted param styling (darker background)
        if widget:
            try:
                if hasattr(widget, "_line_edit") and widget._line_edit:
                    widget._line_edit.setStyleSheet(PROMOTED_PARAM_STYLE)
                elif hasattr(widget, "get_custom_widget"):
                    custom = widget.get_custom_widget()
                    if custom:
                        custom.setStyleSheet(PROMOTED_PARAM_STYLE)
            except Exception as e:
                logger.debug(f"Could not apply styling to widget: {e}")

    def _setup_editable_label(self, widget, param_name: str, label_text: str) -> None:
        """
        Replace standard label with EditableLabel for double-click rename.

        Args:
            widget: NodeBaseWidget to modify
            param_name: Parameter name for tracking renames
            label_text: Current label text
        """
        try:
            # Find the label widget in NodeBaseWidget
            if hasattr(widget, "_label") and widget._label:
                old_label = widget._label
                parent = old_label.parent()

                # Create editable label
                editable = EditableLabel(label_text, param_name, parent)

                # Connect rename signal
                editable.renamed.connect(
                    lambda pname, new_label: self._on_param_label_renamed(
                        pname, new_label
                    )
                )

                # Replace in layout
                layout = parent.layout() if parent else None
                if layout:
                    idx = layout.indexOf(old_label)
                    if idx >= 0:
                        layout.removeWidget(old_label)
                        old_label.hide()
                        layout.insertWidget(idx, editable)

                widget._label = editable
        except Exception as e:
            logger.debug(f"Could not setup editable label: {e}")

    def _on_param_label_renamed(self, param_name: str, new_label: str) -> None:
        """
        Handle parameter label rename.

        Updates the promoted parameter's display label.

        Args:
            param_name: Internal parameter name
            new_label: New display label
        """
        try:
            if self._subflow_entity and self._subflow_entity.parameters:
                for param in self._subflow_entity.parameters:
                    if param.name == param_name:
                        param.label = new_label
                        logger.info(
                            f"Renamed parameter '{param_name}' label to '{new_label}'"
                        )
                        break

            # Mark workflow as modified
            if hasattr(self, "view") and self.view:
                self.view.update()
        except Exception as e:
            logger.debug(f"Could not handle label rename: {e}")

    def load_subflow(self) -> bool:
        """
        Load the subflow from file and configure node.

        Returns:
            True if subflow was loaded successfully
        """
        if self._subflow_configured:
            return True

        subflow_path = self.get_property("subflow_path")
        if not subflow_path:
            logger.warning("No subflow path configured")
            return False

        try:
            from casare_rpa.domain.entities.subflow import Subflow

            subflow = Subflow.load_from_file(subflow_path)
            self.configure_from_subflow(subflow)
            return True

        except Exception as e:
            logger.error(f"Failed to load subflow from {subflow_path}: {e}")
            return False

    def _try_load_subflow_entity(self) -> bool:
        """
        Try to load the subflow entity from file path property.

        This is used for lazy loading when _subflow_entity is needed
        but wasn't set during workflow deserialization.

        Returns:
            True if subflow entity was loaded successfully
        """
        if self._subflow_entity:
            return True

        subflow_path = self.get_property("subflow_path")
        subflow_id = self.get_property("subflow_id")

        if not subflow_path and not subflow_id:
            logger.debug("No subflow path or ID available for loading")
            return False

        try:
            from casare_rpa.domain.entities.subflow import Subflow

            if subflow_path:
                # Try loading from file path
                import os

                if os.path.exists(subflow_path):
                    self._subflow_entity = Subflow.load_from_file(subflow_path)
                    logger.debug(f"Loaded subflow entity from path: {subflow_path}")
                    return True
                else:
                    logger.warning(f"Subflow file not found: {subflow_path}")

            if subflow_id:
                # Try loading from workflows/subflows/ directory by ID
                import os

                base_dir = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(os.path.dirname(__file__))
                                )
                            )
                        )
                    )
                )
                subflows_dir = os.path.join(base_dir, "workflows", "subflows")

                # Search for subflow file matching ID
                if os.path.exists(subflows_dir):
                    for filename in os.listdir(subflows_dir):
                        if filename.endswith(".json"):
                            filepath = os.path.join(subflows_dir, filename)
                            try:
                                subflow = Subflow.load_from_file(filepath)
                                if subflow.id == subflow_id:
                                    self._subflow_entity = subflow
                                    # Update path for future use
                                    self.set_property(
                                        "subflow_path", filepath, push_undo=False
                                    )
                                    logger.debug(f"Found subflow by ID in: {filepath}")
                                    return True
                            except Exception:
                                continue

            return False

        except Exception as e:
            logger.error(f"Failed to load subflow entity: {e}")
            return False

    @property
    def subflow_id(self) -> str:
        """Get the subflow ID."""
        return self.get_property("subflow_id") or ""

    @property
    def subflow_name(self) -> str:
        """Get the subflow name."""
        return self.get_property("subflow_name") or ""

    @property
    def subflow_path(self) -> str:
        """Get the subflow file path."""
        return self.get_property("subflow_path") or ""

    def on_input_connected(self, in_port, out_port) -> None:
        """
        Called when an input port is connected.

        Override to handle connection events if needed.

        Args:
            in_port: The input port that was connected to
            out_port: The output port that connected to the input
        """
        pass

    def on_input_disconnected(self, in_port, out_port) -> None:
        """
        Called when an input port is disconnected.

        Override to handle disconnection events if needed.

        Args:
            in_port: The input port that was disconnected
            out_port: The output port that was disconnected
        """
        pass

    # =========================================================================
    # Subflow Actions (for SubflowNodeItem buttons)
    # =========================================================================

    def expand_subflow(self) -> None:
        """
        Request to expand/edit this subflow.

        Called when user clicks the expand button on SubflowNodeItem.
        """
        subflow_id = self.get_property("subflow_id")
        if subflow_id:
            logger.info(f"Expand subflow requested: {subflow_id}")
            # TODO: Emit signal or call canvas method to open subflow editor

    def promote_parameters(self) -> None:
        """
        Open the Parameter Promotion Dialog to configure promoted parameters.

        Allows users to select which internal node properties should be
        exposed at the subflow level for external configuration.
        """
        from casare_rpa.presentation.canvas.ui.dialogs.parameter_promotion_dialog import (
            show_parameter_promotion_dialog,
        )

        # Lazy load subflow entity if not already loaded
        if not self._subflow_entity:
            if not self._try_load_subflow_entity():
                logger.warning("Cannot promote parameters: No subflow entity loaded")
                return

        # Get node schemas from registry for better property discovery
        node_schemas = self._get_internal_node_schemas()

        # Show dialog
        promoted_params = show_parameter_promotion_dialog(
            self._subflow_entity,
            node_schemas=node_schemas,
            parent=None,
        )

        logger.info(f"Dialog returned: {promoted_params}")

        if promoted_params is not None:
            logger.info(f"Processing {len(promoted_params)} promoted parameters")

            # Update subflow with new parameters
            self._subflow_entity.parameters = promoted_params

            # Save updated subflow to file
            try:
                subflow_path = self.get_property("subflow_path")
                logger.debug(f"Subflow path: {subflow_path}")

                if subflow_path:
                    self._subflow_entity.save_to_file(subflow_path)
                    logger.info(
                        f"Saved {len(promoted_params)} promoted parameters to subflow '{self._subflow_entity.name}'"
                    )
                else:
                    logger.warning("No subflow_path available - cannot save")

                # Add widgets for newly promoted parameters
                if promoted_params:
                    logger.info(f"Adding widgets for {len(promoted_params)} parameters")
                    for i, p in enumerate(promoted_params):
                        logger.debug(
                            f"  Param {i}: name={p.name}, display_name={p.display_name}, type={p.property_type}"
                        )
                    self._add_promoted_parameter_widgets(promoted_params)
                else:
                    logger.warning("No promoted params to add widgets for")

                # Also update casare_node if available
                casare_node = self.get_casare_node()
                if casare_node and hasattr(casare_node, "configure_from_subflow"):
                    casare_node.configure_from_subflow(self._subflow_entity)

            except Exception as e:
                logger.error(f"Failed to save promoted parameters: {e}", exc_info=True)
        else:
            logger.info("Dialog was cancelled (returned None)")

    def _get_internal_node_schemas(self) -> Dict[str, Any]:
        """
        Get schemas for internal nodes to enable better property discovery.

        Returns:
            Dict mapping node_type -> NodeSchema
        """
        schemas: Dict[str, Any] = {}

        if not self._subflow_entity:
            return schemas

        try:
            from casare_rpa.nodes import get_node_class

            for node_id, node_data in self._subflow_entity.nodes.items():
                node_type = (
                    node_data.get("type")
                    or node_data.get("node_type")
                    or node_data.get("type_", "").split(".")[-1]
                )

                if node_type and node_type not in schemas:
                    node_class = get_node_class(node_type)
                    if node_class and hasattr(node_class, "__node_schema__"):
                        schemas[node_type] = node_class.__node_schema__

        except Exception as e:
            logger.debug(f"Could not load node schemas: {e}")

        return schemas


# Backward compatibility alias
SubflowVisualNode = VisualSubflowNode
