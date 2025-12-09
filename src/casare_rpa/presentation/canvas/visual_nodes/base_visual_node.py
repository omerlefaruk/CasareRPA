"""
Base Visual Node for CasareRPA.

This module provides the base VisualNode class to avoid circular imports.
"""

from typing import Optional, Dict, Any
from NodeGraphQt import BaseNode as NodeGraphQtBaseNode
from PySide6.QtGui import QColor

from casare_rpa.domain.entities.base_node import BaseNode as CasareBaseNode
from casare_rpa.domain.value_objects.types import PortType, DataType
from casare_rpa.application.services.port_type_service import (
    PortTypeRegistry,
    get_port_type_registry,
)
from casare_rpa.domain.schemas import PropertyType, NodeSchema
from casare_rpa.presentation.canvas.graph.custom_node_item import CasareNodeItem

# Premium Dark color scheme for node body
# Matches CanvasThemeColors.bg_node (#27272a / Zinc 800)
UNIFIED_NODE_COLOR = QColor(39, 39, 42)


class VisualNode(NodeGraphQtBaseNode):
    """
    Base class for visual nodes in NodeGraphQt.

    Bridges CasareRPA BaseNode with NodeGraphQt visual representation.
    """

    # Class attributes for node metadata
    __identifier__ = "casare_rpa"
    NODE_NAME = "Visual Node"
    NODE_CATEGORY = "basic"

    def __init__(self, qgraphics_item=None) -> None:
        """
        Initialize visual node.

        Args:
            qgraphics_item: Optional custom graphics item class. Defaults to CasareNodeItem.
        """
        # Pass graphics item class for custom rendering
        item_class = qgraphics_item if qgraphics_item is not None else CasareNodeItem
        super().__init__(qgraphics_item=item_class)

        # Ensure back-reference from view to node (needed for collapse button)
        if hasattr(self, "view") and self.view is not None:
            self.view._node = self

        # Reference to the underlying CasareRPA node
        self._casare_node: Optional[CasareBaseNode] = None

        # Last execution output data (for output inspector popup)
        # Updated by ExecutionController after node execution completes
        self._last_output: Optional[Dict[str, Any]] = None

        # Port type registry for typed connections
        self._port_types: Dict[str, Optional[DataType]] = {}
        self._type_registry: PortTypeRegistry = get_port_type_registry()

        # Collapse state - collapsed by default for cleaner canvas
        self._collapsed: bool = True

        # Set node colors with category-based accents
        self._apply_category_colors()

        # Configure selection colors - Premium Indigo Theme
        self.model.selected_color = (
            55,
            48,
            163,
            255,
        )  # Indigo 800 (#3730a3) for selection background
        self.model.selected_border_color = (
            99,
            102,
            241,
            255,
        )  # Indigo 500 (#6366f1) for focus border

        # Set temporary icon (will be updated with actual icons later)
        # Use file path for model.icon (required for JSON serialization in copy/paste)
        icon_path = self._create_temp_icon()
        self.model.icon = icon_path

        # Create and initialize node properties
        self.create_property("node_id", "")
        self.create_property("status", "idle")
        self.create_property("_is_running", False)
        self.create_property("_is_completed", False)
        self.create_property(
            "_disabled", False
        )  # Disabled nodes are skipped during execution

        # Auto-create linked CasareRPA node
        # This ensures every visual node has a CasareRPA node regardless of how it was created
        self._auto_create_casare_node()

        # Setup ports for this node type
        self.setup_ports()

        # Setup custom widgets defined by subclasses
        self.setup_widgets()

        # Auto-create widgets from schema if available
        self._auto_create_widgets_from_schema()

        # Configure port colors after ports are created
        self._configure_port_colors()

        # Style text input widgets after they're created
        self._style_text_inputs()

        # Apply initial collapsed state (hide non-essential widgets and update view)
        if self._collapsed:
            self._update_widget_visibility()
            # Also sync view's collapse state and trigger layout
            if hasattr(self.view, "set_collapsed"):
                self.view.set_collapsed(True)
            if hasattr(self.view, "post_init"):
                self.view.post_init()

    def _apply_category_colors(self) -> None:
        """Apply VSCode Dark+ category-based colors to the node."""
        from casare_rpa.presentation.canvas.graph.node_icons import CATEGORY_COLORS

        # Get category color
        category_color = CATEGORY_COLORS.get(self.NODE_CATEGORY, QColor(62, 62, 66))

        # Unified Node Body Color (Zinc 800)
        self.set_color(39, 39, 42)

        # Category-colored border (Vibrant but professional)
        # Use slightly desaturated values for professional look
        self.model.border_color = (
            category_color.red(),
            category_color.green(),
            category_color.blue(),
            255,
        )

        # Primary Text Color (Zinc 100 - #f4f4f5)
        self.model.text_color = (244, 244, 245, 255)

        # Set category on view for header coloring
        if hasattr(self, "view") and self.view is not None:
            if hasattr(self.view, "set_category"):
                self.view.set_category(self.NODE_CATEGORY)

    def _create_temp_icon(self) -> str:
        """
        Create a professional icon for this node type.
        Returns cached file path for NodeGraphQt model.icon (required for JSON serialization).
        The file is only generated once per node type thanks to path caching.
        """
        from casare_rpa.presentation.canvas.graph.node_icons import (
            get_cached_node_icon_path,
        )

        # Use the node name to get the appropriate icon path
        node_name = self.NODE_NAME
        return get_cached_node_icon_path(node_name, size=24)

    def setup_ports(self) -> None:
        """
        Setup node ports.

        Override this method in subclasses to define ports.
        """
        pass

    def setup_widgets(self) -> None:
        """
        Setup custom widgets for this node.

        Override this method in subclasses to add custom widgets like
        file pickers, credential selectors, or cascading dropdowns.

        Note: This is called BEFORE _auto_create_widgets_from_schema(),
        so custom widgets can override schema-based widgets.
        """
        pass

    def _configure_port_colors(self) -> None:
        """Configure port colors based on data type."""
        # Apply type-based colors to input ports
        for port in self.input_ports():
            port_name = port.name()
            data_type = self._port_types.get(port_name)

            if data_type is None:
                # Exec port - use white
                color = self._type_registry.get_exec_color()
            else:
                # Data port - use type color
                color = self._type_registry.get_type_color(data_type)

            port.color = color
            # Slightly darker border
            port.border_color = (
                max(0, color[0] - 30),
                max(0, color[1] - 30),
                max(0, color[2] - 30),
                255,
            )

        # Apply type-based colors to output ports
        for port in self.output_ports():
            port_name = port.name()
            data_type = self._port_types.get(port_name)

            if data_type is None:
                # Exec port - use white
                color = self._type_registry.get_exec_color()
            else:
                # Data port - use type color
                color = self._type_registry.get_type_color(data_type)

            port.color = color
            # Slightly darker border
            port.border_color = (
                max(0, color[0] - 30),
                max(0, color[1] - 30),
                max(0, color[2] - 30),
                255,
            )

    # =========================================================================
    # TYPED PORT METHODS
    # =========================================================================

    def add_typed_input(self, name: str, data_type: DataType = DataType.ANY) -> None:
        """
        Add an input port with type information.

        Args:
            name: Port name
            data_type: The DataType for this port
        """
        self.add_input(name)
        self._port_types[name] = data_type

    def add_typed_output(self, name: str, data_type: DataType = DataType.ANY) -> None:
        """
        Add an output port with type information.

        Args:
            name: Port name
            data_type: The DataType for this port
        """
        self.add_output(name)
        self._port_types[name] = data_type

    def add_exec_input(self, name: str = "exec_in") -> None:
        """
        Add an execution flow input port.

        Exec ports use None as their type marker.
        Exec inputs accept multiple connections to support merging execution paths.

        Args:
            name: Port name (default: "exec_in")
        """
        self.add_input(name, multi_input=True)
        self._port_types[name] = None  # None marks exec ports

    def add_exec_output(self, name: str = "exec_out") -> None:
        """
        Add an execution flow output port.

        Exec ports use None as their type marker.

        Args:
            name: Port name (default: "exec_out")
        """
        self.add_output(name)
        self._port_types[name] = None  # None marks exec ports

    def get_port_type(self, port_name: str) -> Optional[DataType]:
        """
        Get the DataType for a port.

        Args:
            port_name: Name of the port

        Returns:
            DataType if it's a data port, None if it's an exec port
        """
        # Check if explicitly registered
        if port_name in self._port_types:
            return self._port_types[port_name]

        # Check if it's an exec port by name pattern
        port_lower = port_name.lower()
        exec_port_names = {
            "exec_in",
            "exec_out",
            "exec",
            "loop_body",
            "completed",  # Loop node exec outputs
            "true",
            "false",  # If/Branch node exec outputs
            "then",
            "else",  # Alternative if/branch names
            "on_success",
            "on_error",
            "on_finally",  # Error handling
            "body",
            "done",
            "finish",
            "next",  # Other common exec names
        }
        if port_lower in exec_port_names or "exec" in port_lower:
            return None  # Exec port

        # Default to ANY for unknown data ports
        return DataType.ANY

    def is_exec_port(self, port_name: str) -> bool:
        """
        Check if a port is an execution flow port.

        Args:
            port_name: Name of the port

        Returns:
            True if this is an execution port
        """
        # Check explicit type first
        if port_name in self._port_types:
            return self._port_types[port_name] is None

        # Fall back to name-based detection
        return "exec" in port_name.lower()

    def sync_types_from_casare_node(self) -> None:
        """
        Propagate type information from the linked CasareRPA node.

        Call this after the CasareRPA node is set to automatically
        populate port type information.
        """
        if not self._casare_node:
            return

        # Sync input port types
        input_ports = getattr(self._casare_node, "input_ports", {})
        for name, port in input_ports.items():
            if name not in self._port_types:
                port_type = getattr(port, "port_type", None)
                is_exec = port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT)
                if is_exec:
                    self._port_types[name] = None
                else:
                    self._port_types[name] = getattr(port, "data_type", DataType.ANY)

        # Sync output port types
        output_ports = getattr(self._casare_node, "output_ports", {})
        for name, port in output_ports.items():
            if name not in self._port_types:
                port_type = getattr(port, "port_type", None)
                is_exec = port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT)
                if is_exec:
                    self._port_types[name] = None
                else:
                    self._port_types[name] = getattr(port, "data_type", DataType.ANY)

        # Re-apply port colors now that we have type info
        self._configure_port_colors()

    def _add_variable_aware_text_input(
        self,
        name: str,
        label: str,
        text: str = "",
        placeholder_text: str = "",
        tab: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> Any:
        """
        Add a text input widget with variable picker integration.

        PERFORMANCE: Uses direct creation via create_variable_text_widget() when
        available, avoiding the two-step create+replace pattern. This reduces
        widget instantiation overhead and DOM operations.

        Args:
            name: Property name
            label: Display label
            text: Initial text value
            placeholder_text: Placeholder text when empty
            tab: Tab name for grouping (optional)
            tooltip: Tooltip text (optional)

        Returns:
            The created widget
        """
        # PERFORMANCE: Try direct creation path first
        # This creates VariableAwareLineEdit directly in a NodeBaseWidget,
        # avoiding the create standard widget + replace internal QLineEdit pattern
        try:
            from casare_rpa.presentation.canvas.graph.node_widgets import (
                create_variable_text_widget,
            )

            widget = create_variable_text_widget(
                name=name,
                label=label,
                text=text,
                placeholder_text=placeholder_text,
                tooltip=tooltip or "",
            )

            if widget:
                # Add the widget to the node
                self.add_custom_widget(widget, tab=tab)
                widget.setParentItem(self.view)
                return widget

        except ImportError:
            pass  # Fall back to standard approach
        except Exception:
            pass  # Fall back to standard approach

        # FALLBACK: Standard approach - create text input and return
        # Used when direct creation fails or isn't available
        self.add_text_input(
            name,
            label,
            text=text,
            placeholder_text=placeholder_text,
            tab=tab,
            tooltip=tooltip,
        )

        return self.get_widget(name)

    def _style_text_inputs(self) -> None:
        """Apply custom styling to text input widgets for better visibility."""
        # Get all widgets in this node
        for prop_name, widget in self.widgets().items():
            # Check if it's a LineEdit widget
            if hasattr(widget, "get_custom_widget"):
                custom_widget = widget.get_custom_widget()
                if hasattr(custom_widget, "setStyleSheet"):
                    # Apply a more visible background color for text inputs
                    # Apply a more visible background color for text inputs
                    # Matching Premium Dark theme input_bg and borders
                    custom_widget.setStyleSheet("""
                        QLineEdit {
                            background: #18181b; /* Zinc 900 */
                            border: 1px solid #3f3f46; /* Zinc 700 */
                            border-radius: 4px;
                            color: #f4f4f5; /* Zinc 100 */
                            padding: 4px 8px;
                            selection-background-color: #4338ca; /* Indigo 700 */
                        }
                        QLineEdit:focus {
                            background: #27272a; /* Zinc 800 */
                            border: 1px solid #6366f1; /* Indigo 500 */
                        }
                    """)

    def get_casare_node(self) -> Optional[CasareBaseNode]:
        """
        Get the underlying CasareRPA node instance.

        Returns:
            CasareRPA node instance or None
        """
        return self._casare_node

    def set_casare_node(self, node: CasareBaseNode) -> None:
        """
        Set the underlying CasareRPA node instance.

        Args:
            node: CasareRPA node instance
        """
        self._casare_node = node
        self.set_property("node_id", node.node_id)

    def set_property(self, name: str, value, push_undo: bool = True) -> None:
        """
        Override set_property to also sync to casare_node.config.

        This ensures widget values are synced in real-time to the domain node's
        config dict, which is used during workflow execution.

        Args:
            name: Property name
            value: Property value
            push_undo: Whether to push to undo stack (default: True)
        """
        # Call parent implementation first
        super().set_property(name, value, push_undo)

        # CRITICAL: Also sync to casare_node.config for execution
        # Without this, widget values only go to model.custom_properties
        # but execution reads from casare_node.config
        if self._casare_node is not None and hasattr(self._casare_node, "config"):
            # Skip internal/meta properties
            if not name.startswith("_") and name not in (
                "node_id",
                "name",
                "color",
                "pos",
                "disabled",
                "selected",
                "visible",
                "width",
                "height",
                "status",
            ):
                self._casare_node.config[name] = value

    def _auto_create_casare_node(self) -> None:
        """
        Automatically create and link CasareRPA node.
        Called during __init__ to ensure every visual node has a backing CasareRPA node.
        Handles all creation scenarios: menu, copy/paste, undo/redo, workflow loading.

        Note: For paste/duplicate operations, NodeGraphQt restores properties AFTER
        __init__ completes. The paste hook in node_graph_widget.py handles regenerating
        duplicate node_ids via a deferred check.
        """
        if self._casare_node is not None:
            return  # Already has a node

        try:
            # Import here to avoid circular dependency
            from ..graph.node_registry import get_node_factory, get_casare_node_mapping
            from loguru import logger

            # Check if this visual node type has a casare_node mapping
            mapping = get_casare_node_mapping()
            if type(self) not in mapping:
                # Visual-only node (e.g., comment, sticky note) - no casare_node needed
                return

            factory = get_node_factory()

            # Create the CasareRPA node
            casare_node = factory.create_casare_node(self)
            if casare_node:
                # Node is already linked via factory.create_casare_node -> set_casare_node
                # Sync visual node properties to casare_node.config
                self._sync_properties_to_casare_node(casare_node)
            else:
                # Log error but don't crash - paste hook will try to create later
                from loguru import logger

                logger.warning(
                    f"_auto_create_casare_node: factory returned None for {type(self).__name__}"
                )
        except ImportError:
            # Factory not ready yet (e.g., during testing or early initialization)
            # The paste hook will handle creating the casare_node later
            pass
        except Exception as e:
            # Log the error for debugging but don't crash
            from loguru import logger

            logger.warning(
                f"_auto_create_casare_node failed for {type(self).__name__}: {e}"
            )

    def _sync_properties_to_casare_node(self, casare_node) -> None:
        """
        Sync visual node properties to casare_node.config.

        This ensures that custom properties defined in the visual node
        (via create_property) are available in casare_node.config for execution.

        Args:
            casare_node: The CasareRPA node to sync properties to
        """
        try:
            # Get all custom properties from visual node model
            if not hasattr(self, "model") or self.model is None:
                return

            model = self.model
            custom_props = list(model.custom_properties.keys()) if model else []

            for prop_name in custom_props:
                # Skip internal/meta properties
                if prop_name.startswith("_") or prop_name in (
                    "node_id",
                    "name",
                    "color",
                    "pos",
                    "disabled",
                    "selected",
                    "visible",
                    "width",
                    "height",
                ):
                    continue

                try:
                    prop_value = self.get_property(prop_name)
                    if prop_value is not None:
                        # Sync to casare_node config
                        casare_node.config[prop_name] = prop_value
                except Exception:
                    pass  # Property access failed, skip
        except Exception:
            pass  # Silently fail during initialization

    def _auto_create_widgets_from_schema(self) -> None:
        """
        Auto-generate widgets from linked CasareNode schema.

        If the CasareNode class has a __node_schema__ attribute (from @node_schema decorator),
        this method automatically creates widgets matching the schema properties.

        This provides a declarative way to define node properties once and have both
        the config and UI generated automatically.

        Note: Widgets created in setup_widgets() take precedence over schema widgets.
        """
        if not self._casare_node:
            return  # No casare node yet

        # Get schema from casare node class
        schema: Optional[NodeSchema] = getattr(
            self._casare_node.__class__, "__node_schema__", None
        )
        if not schema:
            return  # No schema, use manual widget definitions

        # Get existing widget names (created in setup_widgets)
        existing_widgets = set(self.widgets().keys())

        # Generate widgets from schema
        for prop_def in schema.properties:
            # Skip if widget already exists (created in setup_widgets)
            if prop_def.name in existing_widgets:
                continue
            # Custom widget class override
            if prop_def.widget_class:
                # Custom widgets need special handling - skip for now
                # Subclasses can override this method to handle custom widgets
                continue

            # Standard widget types
            # Special handling for image_template property (uses element picker)
            if prop_def.name == "image_template":
                from casare_rpa.presentation.canvas.graph.node_widgets import (
                    NodeSelectorWidget,
                )

                widget = NodeSelectorWidget(
                    name=prop_def.name,
                    label=prop_def.label or "Image Template",
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder="Pick element to capture image...",
                )
                if widget:
                    self.add_custom_widget(widget)
                    widget.setParentItem(self.view)
                    if hasattr(widget, "set_node_ref"):
                        widget.set_node_ref(self)

            elif prop_def.type == PropertyType.STRING:
                # Use variable-aware text input with {x} button for variable insertion
                self._add_variable_aware_text_input(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder_text=prop_def.placeholder,
                    tab=prop_def.tab,
                    tooltip=prop_def.tooltip,
                )

            elif prop_def.type == PropertyType.INTEGER:
                # Use int input if available, otherwise text input with validation
                try:
                    self.add_int_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        value=int(prop_def.default)
                        if prop_def.default is not None
                        else 0,
                        tab=prop_def.tab,
                    )
                except AttributeError:
                    # Fallback to variable-aware text input if add_int_input doesn't exist
                    self._add_variable_aware_text_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        text=str(prop_def.default)
                        if prop_def.default is not None
                        else "0",
                        tab=prop_def.tab,
                        tooltip=prop_def.tooltip,
                    )

            elif prop_def.type == PropertyType.FLOAT:
                # Use float input if available, otherwise text input
                try:
                    self.add_float_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        value=float(prop_def.default)
                        if prop_def.default is not None
                        else 0.0,
                        tab=prop_def.tab,
                    )
                except AttributeError:
                    self._add_variable_aware_text_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        text=str(prop_def.default)
                        if prop_def.default is not None
                        else "0.0",
                        tab=prop_def.tab,
                        tooltip=prop_def.tooltip,
                    )

            elif prop_def.type == PropertyType.BOOLEAN:
                self.add_checkbox(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    state=bool(prop_def.default)
                    if prop_def.default is not None
                    else False,
                    tab=prop_def.tab,
                )

            elif prop_def.type == PropertyType.CHOICE:
                if prop_def.choices:
                    self.add_combo_menu(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        items=prop_def.choices,
                        tab=prop_def.tab,
                    )
                    # Set default value
                    if (
                        prop_def.default is not None
                        and prop_def.default in prop_def.choices
                    ):
                        self.set_property(prop_def.name, prop_def.default)

            elif prop_def.type == PropertyType.FILE_PATH:
                # File path uses variable-aware text input
                self._add_variable_aware_text_input(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder_text=prop_def.placeholder or "Select file...",
                    tab=prop_def.tab,
                    tooltip=prop_def.tooltip,
                )

            elif prop_def.type == PropertyType.DIRECTORY_PATH:
                # Directory path uses variable-aware text input
                self._add_variable_aware_text_input(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder_text=prop_def.placeholder or "Select directory...",
                    tab=prop_def.tab,
                    tooltip=prop_def.tooltip,
                )

            elif prop_def.type == PropertyType.SELECTOR:
                # Selector type uses special widget with picker button
                from casare_rpa.presentation.canvas.graph.node_widgets import (
                    NodeSelectorWidget,
                )

                widget = NodeSelectorWidget(
                    name=prop_def.name,
                    label=prop_def.label or prop_def.name,
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder=prop_def.placeholder or "Enter selector or click ...",
                )
                if widget:
                    self.add_custom_widget(widget)
                    widget.setParentItem(self.view)
                    # Set node reference for picker dialog
                    if hasattr(widget, "set_node_ref"):
                        widget.set_node_ref(self)

            elif prop_def.type in (
                PropertyType.TEXT,
                PropertyType.CODE,
                PropertyType.JSON,
            ):
                # These types use variable-aware text input (multi-line in future)
                self._add_variable_aware_text_input(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder_text=prop_def.placeholder,
                    tab=prop_def.tab,
                    tooltip=prop_def.tooltip,
                )

            # Other types (DATE, TIME, COLOR, etc.) can be added later with specialized widgets

    def ensure_casare_node(self) -> Optional[CasareBaseNode]:
        """
        Ensure this visual node has a CasareRPA node, creating one if necessary.
        Use this before any operation that requires the CasareRPA node.

        Returns:
            The CasareRPA node instance, or None if creation failed
        """
        if self._casare_node is None:
            self._auto_create_casare_node()
        return self._casare_node

    def update_status(self, status: str) -> None:
        """
        Update node visual status.

        Args:
            status: Node status (idle, running, success, error)
        """
        self.set_property("status", status)

        # Update visual indicators based on status
        if status == "running":
            # Show animated yellow dotted border
            self.set_property("_is_running", True)
            self.set_property("_is_completed", False)
            self.model.border_color = (255, 215, 0, 255)  # Bright yellow
            # Trigger custom paint for animation
            if hasattr(self.view, "set_running"):
                self.view.set_running(True)
        elif status == "success":
            # Show checkmark, restore normal border
            self.set_property("_is_running", False)
            self.set_property("_is_completed", True)
            self.model.border_color = (68, 68, 68, 255)  # Normal border
            if hasattr(self.view, "set_running"):
                self.view.set_running(False)
            if hasattr(self.view, "set_completed"):
                self.view.set_completed(True)
            if hasattr(self.view, "set_error"):
                self.view.set_error(False)
        elif status == "error":
            # Show error state with icon (keep dark background, red border + error icon)
            self.set_property("_is_running", False)
            self.set_property("_is_completed", False)
            self.set_color(45, 45, 45)  # Keep dark background - icon shows error
            self.model.border_color = (244, 67, 54, 255)  # Red border
            if hasattr(self.view, "set_running"):
                self.view.set_running(False)
            if hasattr(self.view, "set_completed"):
                self.view.set_completed(False)
            if hasattr(self.view, "set_error"):
                self.view.set_error(True)
        else:  # idle
            # Restore default appearance
            self.set_property("_is_running", False)
            self.set_property("_is_completed", False)
            self.set_color(45, 45, 45)  # Dark background
            self.model.border_color = (68, 68, 68, 255)  # Normal border
            if hasattr(self.view, "set_running"):
                self.view.set_running(False)
            if hasattr(self.view, "set_completed"):
                self.view.set_completed(False)
            if hasattr(self.view, "set_error"):
                self.view.set_error(False)

    def update_execution_time(self, time_seconds: Optional[float]) -> None:
        """
        Update the displayed execution time.

        Args:
            time_seconds: Execution time in seconds, or None to clear
        """
        if hasattr(self.view, "set_execution_time"):
            self.view.set_execution_time(time_seconds)

    # =========================================================================
    # COLLAPSE / EXPAND METHODS
    # =========================================================================

    @property
    def is_collapsed(self) -> bool:
        """Check if node is collapsed."""
        return self._collapsed

    def toggle_collapse(self) -> None:
        """Toggle collapsed state."""
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        """
        Set collapsed state and update widget visibility.

        When collapsed, only essential properties are shown.
        Non-essential properties are hidden.

        Args:
            collapsed: True to collapse, False to expand
        """
        if self._collapsed == collapsed:
            return

        self._collapsed = collapsed

        # Update widget visibility based on schema
        self._update_widget_visibility()

        # Update collapse button in view
        if hasattr(self.view, "set_collapsed"):
            self.view.set_collapsed(collapsed)

        # Trigger layout update
        if hasattr(self.view, "post_init"):
            self.view.post_init()

    def _update_widget_visibility(self) -> None:
        """Update widget visibility based on collapse state and essential flags."""
        from loguru import logger

        if not self._casare_node:
            return

        # Get schema from casare node class
        schema: Optional[NodeSchema] = getattr(
            self._casare_node.__class__, "__node_schema__", None
        )
        if not schema:
            return

        # Get essential property names
        essential_props = set(schema.get_essential_properties())

        # Update visibility for each widget
        all_widgets = self.widgets()
        for prop_name, widget in all_widgets.items():
            # Skip internal properties
            if prop_name.startswith("_"):
                continue

            # Determine if this widget should be visible
            if self._collapsed:
                # When collapsed, only show essential properties
                should_show = prop_name in essential_props
            else:
                # When expanded, show all properties
                should_show = True

            # Set widget visibility
            try:
                # CRITICAL FIX: Sync widget value before hiding
                # Qt's editingFinished signal only fires on Enter/focus-loss, not when
                # setVisible(False) is called. Force sync to prevent data loss.
                if not should_show and widget.isVisible():
                    # Widget is about to be hidden - sync its current value first
                    if hasattr(widget, "on_value_changed"):
                        widget.on_value_changed()

                widget.setVisible(should_show)
            except Exception as e:
                logger.debug(f"Could not set visibility for widget {prop_name}: {e}")

    def get_essential_property_names(self) -> list:
        """
        Get list of essential property names for this node.

        Returns:
            List of property names marked as essential in schema
        """
        if not self._casare_node:
            return []

        schema: Optional[NodeSchema] = getattr(
            self._casare_node.__class__, "__node_schema__", None
        )
        if not schema:
            return []

        return schema.get_essential_properties()

    # =========================================================================
    # OUTPUT INSPECTOR METHODS
    # =========================================================================

    def get_last_output(self) -> Optional[Dict[str, Any]]:
        """
        Get the last execution output data.

        This data is populated by ExecutionController after node execution
        completes and is used by the Node Output Inspector popup.

        Returns:
            Dictionary of output port name -> value, or None if not executed
        """
        return self._last_output

    def set_last_output(self, output: Optional[Dict[str, Any]]) -> None:
        """
        Set the last execution output data.

        Called by ExecutionController after node execution completes.

        Args:
            output: Dictionary of output port name -> value
        """
        self._last_output = output

    def clear_last_output(self) -> None:
        """Clear the last execution output data."""
        self._last_output = None
