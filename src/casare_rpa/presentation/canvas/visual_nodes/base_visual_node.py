"""
Base Visual Node for CasareRPA.

This module provides the base VisualNode class to avoid circular imports.
"""

from functools import partial
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from casare_rpa.domain.schemas.property_schema import PropertyDef

from NodeGraphQt import BaseNode as NodeGraphQtBaseNode
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor

from casare_rpa.domain.entities.base_node import BaseNode as CasareBaseNode
from casare_rpa.domain.port_type_system import (
    PortTypeRegistry,
    get_port_type_registry,
)
from casare_rpa.domain.schemas import NodeSchema, PropertyType
from casare_rpa.domain.value_objects.types import DataType, PortType
from casare_rpa.presentation.canvas.graph.custom_node_item import CasareNodeItem

from ..theme import THEME, TOKENS


def _hex_to_qcolor(hex_color: str) -> QColor:
    """Convert hex color string to QColor."""
    return QColor(hex_color)


# VSCode Dark+ color scheme for nodes
# Node body should be slightly lighter than canvas to be visible
UNIFIED_NODE_COLOR = _hex_to_qcolor(THEME.bg_node)  # VSCode sidebar background


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
        self._casare_node: CasareBaseNode | None = None
        self._schema_widget_source: type[CasareBaseNode] | None = None

        # Last execution output data (for output inspector popup)
        # Updated by ExecutionController after node execution completes
        self._last_output: dict[str, Any] | None = None

        # Port type registry for typed connections
        self._port_types: dict[str, DataType | None] = {}
        self._type_registry: PortTypeRegistry = get_port_type_registry()

        # Collapse state - collapsed by default for cleaner canvas
        self._collapsed: bool = True

        # Set node colors with category-based accents
        self._apply_category_colors()

        # Configure selection colors - VSCode selection style
        sel_color = _hex_to_qcolor(THEME.bg_selected)
        self.model.selected_color = (sel_color.red(), sel_color.green(), sel_color.blue(), 128)

        focus_color = _hex_to_qcolor(THEME.primary)
        self.model.selected_border_color = (
            focus_color.red(),
            focus_color.green(),
            focus_color.blue(),
            255,
        )

        # Set temporary icon (will be updated with actual icons later)
        # Use file path for model.icon (required for JSON serialization in copy/paste)
        icon_path = self._create_temp_icon()
        self.model.icon = icon_path

        # Create and initialize node properties
        self.create_property("node_id", "")
        self.create_property("status", "idle")
        self.create_property("_is_running", False)
        self.create_property("_is_completed", False)
        self.create_property("_disabled", False)  # Disabled nodes are skipped during execution

        # Auto-create linked CasareRPA node
        # This ensures every visual node has a CasareRPA node regardless of how it was created
        self._auto_create_casare_node()

        # Setup ports for this node type
        self.setup_ports()

        # Setup custom widgets defined by subclasses
        self.setup_widgets()

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

        # Get category color (with fallback to theme)
        default_color = _hex_to_qcolor(THEME.border)
        category_color = CATEGORY_COLORS.get(self.NODE_CATEGORY, default_color)

        # Use theme node background color
        node_bg = _hex_to_qcolor(THEME.bg_node)
        self.model.color = (node_bg.red(), node_bg.green(), node_bg.blue(), 255)

        # Category-colored border (use theme or category colors)
        # Slightly darker for subtlety
        border_r = int(category_color.red() * 0.8)
        border_g = int(category_color.green() * 0.8)
        border_b = int(category_color.blue() * 0.8)
        self.model.border_color = (border_r, border_g, border_b, 255)

        # Use theme text color
        text_color = _hex_to_qcolor(THEME.text_primary)
        self.model.text_color = (text_color.red(), text_color.green(), text_color.blue(), 255)

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

    def add_custom_widget(
        self, widget: Any, widget_type: str | None = None, tab: str | None = None
    ) -> None:
        """
        Add a custom widget to the node.

        Override to automatically connect VariableAwareLineEdit expand signals
        to the expression editor popup. This ensures all widgets with an
        expand button (File Path, Directory Path, Selector, etc.) work correctly.

        Args:
            widget: The widget to add
            widget_type: Optional widget type
            tab: Optional tab name
        """
        super().add_custom_widget(widget, widget_type=widget_type, tab=tab)

        # Install tab navigation for widget parameters
        # Use QTimer to defer until after all widgets are added
        from PySide6.QtCore import QTimer

        from casare_rpa.presentation.canvas.graph.tab_navigation import install_tab_navigation

        QTimer.singleShot(0, lambda: install_tab_navigation(self))

        # Check for VariableAwareLineEdit and connect expand signal
        # Use duck typing to detect compatible widgets
        if hasattr(widget, "_line_edit"):
            line_edit = widget._line_edit
            # Check if it has the expand_clicked signal
            if hasattr(line_edit, "expand_clicked"):
                # Retrieve widget name safely (NodeBaseWidget uses get_name())
                widget_name = "unknown"
                if hasattr(widget, "get_name"):
                    widget_name = widget.get_name()
                elif hasattr(widget, "name"):
                    widget_name = widget.name
                elif hasattr(widget, "_name"):
                    widget_name = widget._name

                # Get property def (attached by _add_variable_aware_text_input) or create default
                property_def = getattr(widget, "_property_def", None)
                if property_def is None:
                    from casare_rpa.domain.schemas import PropertyDef, PropertyType

                    # Create default property def based on widget metadata
                    label = getattr(widget, "label", widget_name)

                    # Infer type from widget class name if possible
                    widget_type = widget.__class__.__name__
                    prop_type = PropertyType.STRING
                    if "Selector" in widget_type:
                        prop_type = PropertyType.SELECTOR
                    elif "File" in widget_type:
                        prop_type = PropertyType.FILE_PATH
                    elif "Directory" in widget_type:
                        prop_type = PropertyType.DIRECTORY_PATH

                    property_def = PropertyDef(
                        name=widget_name,
                        type=prop_type,
                        label=label,
                    )

                # Connect signal, reusing handler to avoid disconnect warnings.
                handler_attr = "_casare_expand_clicked_handler"
                previous_handler = getattr(line_edit, handler_attr, None)
                if previous_handler is not None:
                    try:
                        line_edit.expand_clicked.disconnect(previous_handler)
                    except (TypeError, RuntimeError):
                        pass

                new_handler = partial(self._open_expression_editor, widget_name, property_def)
                setattr(line_edit, handler_attr, new_handler)
                line_edit.expand_clicked.connect(new_handler)

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

    def get_port_type(self, port_name: str) -> DataType | None:
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
        tab: str | None = None,
        tooltip: str | None = None,
        property_def: Optional["PropertyDef"] = None,
    ) -> Any:
        """
        Add a text input widget with variable picker and expand button integration.

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
            property_def: Property definition for expression editor type detection

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
                show_expand_button=True,
            )

            if widget:
                # Store property def for add_custom_widget to use
                widget._property_def = property_def

                # Add the widget to the node (this will trigger signal connection via add_custom_widget override)
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
        for _prop_name, widget in self.widgets().items():
            # Check if it's a LineEdit widget
            if hasattr(widget, "get_custom_widget"):
                custom_widget = widget.get_custom_widget()
                if hasattr(custom_widget, "setStyleSheet"):
                    # Apply theme-based styling for text inputs
                    custom_widget.setStyleSheet(f"""
                        QLineEdit {{
                            background: {THEME.bg_component};
                            border: 1px solid {THEME.border};
                            border-radius: {TOKENS.radius.sm}px;
                            color: {THEME.text_primary};
                            padding: 2px;
                            selection-background-color: {THEME.bg_selected};
                        }}
                        QLineEdit:focus {{
                            background: {THEME.bg_elevated};
                            border: 1px solid {THEME.border_focus};
                        }}
                    """)

    # =========================================================================
    # EXPRESSION EDITOR INTEGRATION
    # =========================================================================

    def _open_expression_editor(self, property_name: str, property_def: "PropertyDef") -> None:
        """
        Open expression editor popup for a property.

        Args:
            property_name: Name of the property
            property_def: Property definition with type info
        """
        from loguru import logger

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            ExpressionEditorPopup,
        )
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.editor_factory import (
            EditorFactory,
        )

        logger.debug(f"Opening expression editor for property: {property_name}")

        # Determine node type for overrides
        node_type = self.__class__.__name__

        # Create appropriate editor using factory (handles overrides and defaults)
        editor = EditorFactory.create_for_property_type(
            property_type=property_def.type.name
            if hasattr(property_def.type, "name")
            else str(property_def.type),
            node_type=node_type,
            property_name=property_name,
            parent=None,
        )

        # Get current value - prioritize widget value as it's the source of truth
        current_value = None
        widget = self.get_widget(property_name)

        if widget:
            logger.debug(f"Widget found for {property_name}: {widget}")
            if hasattr(widget, "get_value"):
                try:
                    current_value = widget.get_value()
                    logger.debug(f"Retrieved value from widget {property_name}: '{current_value}'")
                except Exception as e:
                    logger.debug(f"Could not get value from widget {property_name}: {e}")
            else:
                logger.debug(f"Widget {property_name} has no get_value method")
        else:
            logger.debug(f"No widget found for {property_name}")

        # Fallback to property value if widget value is unavailable
        if current_value is None:
            current_value = self.get_property(property_name) or ""
            logger.debug(f"Used fallback property value for {property_name}: '{current_value}'")

        # Create popup
        popup = ExpressionEditorPopup(parent=None)  # Top-level window

        # Set the editor
        popup.set_editor(editor)

        # Set node context for autocomplete
        if hasattr(editor, "set_node_context"):
            editor.set_node_context(self.get_property("node_id"), self.graph)

        # Set title with property name
        popup.set_title(f"Edit: {property_def.label or property_name}")

        # Set initial value
        popup.set_value(str(current_value))

        # Connect accepted signal to update property
        popup.accepted.connect(partial(self._on_expression_editor_accepted, property_name))

        # Position near widget
        if widget:
            # Try to get global position from widget
            try:
                # Get the internal QLineEdit or similar widget for positioning
                internal_widget = None
                if hasattr(widget, "get_custom_widget"):
                    internal_widget = widget.get_custom_widget()
                elif hasattr(widget, "widget"):
                    internal_widget = widget.widget()

                if internal_widget and hasattr(internal_widget, "mapToGlobal"):
                    global_pos = internal_widget.mapToGlobal(QPoint(0, internal_widget.height()))
                    popup.show_at_position(global_pos)
                    logger.debug(f"Expression editor opened for {property_name}")
                    return
            except Exception as e:
                logger.debug(f"Could not position popup near widget: {e}")

        # Fallback: show at screen center
        popup.show()
        logger.debug(f"Expression editor opened for {property_name} (center)")

    def _on_expression_editor_accepted(self, property_name: str, value: str) -> None:
        """
        Handle expression editor value acceptance.

        Args:
            property_name: Name of the property being edited
            value: New value from the editor
        """
        from loguru import logger

        logger.debug(f"Expression editor accepted for {property_name}: {len(value)} chars")
        self.set_property(property_name, value)

    def get_casare_node(self) -> CasareBaseNode | None:
        """
        Get the underlying CasareRPA node instance.

        Returns:
            CasareRPA node instance or None
        """
        return self._casare_node

    def set_casare_node(self, node: CasareBaseNode) -> None:
        """
        Set the underlying CasareRPA node instance.

        Also triggers widget creation from schema if not already done.
        This handles the case where the visual node is created before
        the casare node is linked (common in node factories).

        Args:
            node: CasareRPA node instance
        """
        self._casare_node = node
        self.set_property("node_id", node.node_id)

        # Create widgets from schema now that casare_node is available
        # This is needed because _auto_create_widgets_from_schema() in __init__
        # may have been skipped when _casare_node was None
        self._auto_create_widgets_from_schema()

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
            from loguru import logger

            from ..graph.node_registry import get_casare_node_mapping, get_node_factory

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

            logger.warning(f"_auto_create_casare_node failed for {type(self).__name__}: {e}")

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

        If the CasareNode class has a __node_schema__ attribute (from @properties decorator),
        this method automatically creates widgets matching the schema properties.

        This provides a declarative way to define node properties once and have both
        the config and UI generated automatically.

        Note: Widgets created in setup_widgets() take precedence over schema widgets.
        Visual nodes can set SKIP_SCHEMA_WIDGETS = True to disable this entirely.
        """
        # Allow visual nodes to opt-out of schema-based widget generation
        if getattr(self, "SKIP_SCHEMA_WIDGETS", False):
            return

        if not self._casare_node:
            return  # No casare node yet
        if self._schema_widget_source is self._casare_node.__class__:
            return

        # Get schema from casare node class
        schema: NodeSchema | None = getattr(self._casare_node.__class__, "__node_schema__", None)
        if not schema:
            return  # No schema, use manual widget definitions
        self._schema_widget_source = self._casare_node.__class__

        # Get existing widget names (created in setup_widgets)
        existing_widgets = set(self.widgets().keys())

        # Generate widgets from schema
        for prop_def in schema.properties:
            # Skip if widget already exists (created in setup_widgets)
            if prop_def.name in existing_widgets:
                continue

            # CRITICAL FIX: Also check if property already exists in the model
            # This prevents "property already exists" errors if called multiple times
            if self.has_property(prop_def.name):
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
                # Use variable-aware text input with {x} and ... buttons
                self._add_variable_aware_text_input(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    text=str(prop_def.default) if prop_def.default is not None else "",
                    placeholder_text=prop_def.placeholder,
                    tab=prop_def.tab,
                    tooltip=prop_def.tooltip,
                    property_def=prop_def,
                )

            elif prop_def.type == PropertyType.INTEGER:
                # Use int input if available, otherwise text input with validation
                try:
                    self.add_int_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        value=int(prop_def.default) if prop_def.default is not None else 0,
                        tab=prop_def.tab,
                    )
                except AttributeError:
                    # Fallback to variable-aware text input if add_int_input doesn't exist
                    self._add_variable_aware_text_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        text=str(prop_def.default) if prop_def.default is not None else "0",
                        tab=prop_def.tab,
                        tooltip=prop_def.tooltip,
                        property_def=prop_def,
                    )

            elif prop_def.type == PropertyType.FLOAT:
                # Use float input if available, otherwise text input
                try:
                    self.add_float_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        value=float(prop_def.default) if prop_def.default is not None else 0.0,
                        tab=prop_def.tab,
                    )
                except AttributeError:
                    self._add_variable_aware_text_input(
                        prop_def.name,
                        prop_def.label or prop_def.name,
                        text=str(prop_def.default) if prop_def.default is not None else "0.0",
                        tab=prop_def.tab,
                        tooltip=prop_def.tooltip,
                        property_def=prop_def,
                    )

            elif prop_def.type == PropertyType.BOOLEAN:
                self.add_checkbox(
                    prop_def.name,
                    prop_def.label or prop_def.name,
                    state=bool(prop_def.default) if prop_def.default is not None else False,
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
                    if prop_def.default is not None and prop_def.default in prop_def.choices:
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
                    property_def=prop_def,
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
                    property_def=prop_def,
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
                    property_def=prop_def,
                )

            # Other types (DATE, TIME, COLOR, etc.) can be added later with specialized widgets

    def ensure_casare_node(self) -> CasareBaseNode | None:
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

    def update_execution_time(self, time_seconds: float | None) -> None:
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
        """Update widget visibility based on collapse state and essential flags.

        CRITICAL: Calls prepareGeometryChange() on the view before changing visibility
        to ensure Qt's scene cache is properly invalidated for geometry changes.
        """
        from loguru import logger

        if not self._casare_node:
            return

        # CRITICAL: Notify Qt scene that geometry will change before modifying visibility
        # This prevents rendering artifacts when panning/scrolling after collapse state changes
        if hasattr(self.view, "prepareGeometryChange"):
            self.view.prepareGeometryChange()

        # Get schema from casare node class
        schema: NodeSchema | None = getattr(self._casare_node.__class__, "__node_schema__", None)
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

        schema: NodeSchema | None = getattr(self._casare_node.__class__, "__node_schema__", None)
        if not schema:
            return []

        return schema.get_essential_properties()

    def _get_visible_properties(self) -> list:
        """
        Get properties that should be visible based on current config.

        Filters properties by:
        - Visibility level (excludes internal)
        - Conditional display (display_when/hidden_when)

        Returns:
            List of PropertyDef that should be rendered
        """

        if not self._casare_node:
            return []

        if not hasattr(self._casare_node, "__node_schema__"):
            return []

        schema = self._casare_node.__class__.__node_schema__
        visible: list = []

        for prop in schema.get_sorted_properties():
            # Skip internal properties (never displayed)
            if prop.visibility == "internal":
                continue
            # Check conditional display rules
            if not schema.should_display(prop.name, self._casare_node.config):
                continue
            visible.append(prop)

        return visible

    # =========================================================================
    # OUTPUT INSPECTOR METHODS
    # =========================================================================

    def get_last_output(self) -> dict[str, Any] | None:
        """
        Get the last execution output data.

        This data is populated by ExecutionController after node execution
        completes and is used by the Node Output Inspector popup.

        Returns:
            Dictionary of output port name -> value, or None if not executed
        """
        return self._last_output

    def set_last_output(self, output: dict[str, Any] | None) -> None:
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

    def _safe_create_property(
        self, name: str, value: Any, widget_type: int = 0, tab: str | None = None
    ) -> None:
        """
        Safely create a property only if it doesn't already exist.

        Args:
            name: Property name
            value: Initial value
            widget_type: Widget type enum (0=HIDDEN, 1=LINE_EDIT, etc.)
            tab: Optional tab name
        """
        if not self.has_property(name):
            self.create_property(name, value, widget_type=widget_type, tab=tab)
