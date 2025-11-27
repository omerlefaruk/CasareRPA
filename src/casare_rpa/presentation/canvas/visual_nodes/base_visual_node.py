"""
Base Visual Node for CasareRPA.

This module provides the base VisualNode class to avoid circular imports.
"""

from typing import Type, Optional, Any, Dict
from NodeGraphQt import BaseNode as NodeGraphQtBaseNode
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush
from PySide6.QtCore import Qt, QSize

from casare_rpa.core.base_node import BaseNode as CasareBaseNode
from casare_rpa.core.types import PortType, DataType
from casare_rpa.core.port_type_system import PortTypeRegistry, get_port_type_registry
from casare_rpa.canvas.graph.custom_node_item import CasareNodeItem
from loguru import logger

# VSCode Dark+ color scheme for nodes
# Node body should be slightly lighter than canvas (#1E1E1E) to be visible
UNIFIED_NODE_COLOR = QColor(37, 37, 38)  # VSCode sidebar background - #252526

class VisualNode(NodeGraphQtBaseNode):
    """
    Base class for visual nodes in NodeGraphQt.
    
    Bridges CasareRPA BaseNode with NodeGraphQt visual representation.
    """
    
    # Class attributes for node metadata
    __identifier__ = "casare_rpa"
    NODE_NAME = "Visual Node"
    NODE_CATEGORY = "basic"
    
    def __init__(self) -> None:
        """Initialize visual node."""
        # Pass CasareNodeItem as the graphics item class for custom rendering
        super().__init__(qgraphics_item=CasareNodeItem)

        # Reference to the underlying CasareRPA node
        self._casare_node: Optional[CasareBaseNode] = None

        # Port type registry for typed connections
        self._port_types: Dict[str, Optional[DataType]] = {}
        self._type_registry: PortTypeRegistry = get_port_type_registry()

        # Set node colors with category-based accents
        self._apply_category_colors()
        
        # Configure selection colors - VSCode selection style
        self.model.selected_color = (38, 79, 120, 128)  # VSCode editor selection (#264F78) with transparency
        self.model.selected_border_color = (0, 122, 204, 255)  # VSCode focus border (#007ACC)
        
        # Set temporary icon (will be updated with actual icons later)
        # Use file path for model.icon (required for JSON serialization in copy/paste)
        icon_path = self._create_temp_icon()
        self.model.icon = icon_path
        
        # Create and initialize node properties
        self.create_property("node_id", "")
        self.create_property("status", "idle")
        self.create_property("_is_running", False)
        self.create_property("_is_completed", False)
        
        # Auto-create linked CasareRPA node
        # This ensures every visual node has a CasareRPA node regardless of how it was created
        self._auto_create_casare_node()
        
        # Setup ports for this node type
        self.setup_ports()
        
        # Configure port colors after ports are created
        self._configure_port_colors()
        
        # Style text input widgets after they're created
        self._style_text_inputs()

    def _apply_category_colors(self) -> None:
        """Apply VSCode Dark+ category-based colors to the node."""
        from ..graph.node_icons import get_node_color, CATEGORY_COLORS

        # Get category color
        category_color = CATEGORY_COLORS.get(self.NODE_CATEGORY, QColor(62, 62, 66))

        # VSCode sidebar background for all nodes (#252526)
        self.set_color(37, 37, 38)

        # Category-colored border (use VSCode syntax colors)
        # Slightly darker for subtlety
        border_r = int(category_color.red() * 0.8)
        border_g = int(category_color.green() * 0.8)
        border_b = int(category_color.blue() * 0.8)
        self.model.border_color = (border_r, border_g, border_b, 255)

        # VSCode text color (#D4D4D4)
        self.model.text_color = (212, 212, 212, 255)

    def _create_temp_icon(self) -> str:
        """
        Create a professional icon for this node type.
        Returns cached file path for NodeGraphQt model.icon (required for JSON serialization).
        The file is only generated once per node type thanks to path caching.
        """
        from ..graph.node_icons import get_cached_node_icon_path

        # Use the node name to get the appropriate icon path
        node_name = self.NODE_NAME
        return get_cached_node_icon_path(node_name, size=24)
    
    def setup_ports(self) -> None:
        """
        Setup node ports.
        
        Override this method in subclasses to define ports.
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

        Args:
            name: Port name (default: "exec_in")
        """
        self.add_input(name)
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
            "exec_in", "exec_out", "exec",
            "loop_body", "completed",  # Loop node exec outputs
            "true", "false",  # If/Branch node exec outputs
            "then", "else",  # Alternative if/branch names
            "on_success", "on_error", "on_finally",  # Error handling
            "body", "done", "finish", "next",  # Other common exec names
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
    
    def _style_text_inputs(self) -> None:
        """Apply custom styling to text input widgets for better visibility."""
        # Get all widgets in this node
        for prop_name, widget in self.widgets().items():
            # Check if it's a LineEdit widget
            if hasattr(widget, 'get_custom_widget'):
                custom_widget = widget.get_custom_widget()
                if hasattr(custom_widget, 'setStyleSheet'):
                    # Apply a more visible background color for text inputs
                    custom_widget.setStyleSheet("""
                        QLineEdit {
                            background: rgb(60, 60, 80);
                            border: 1px solid rgb(80, 80, 100);
                            border-radius: 3px;
                            color: rgba(230, 230, 230, 255);
                            padding: 2px;
                            selection-background-color: rgba(100, 150, 200, 150);
                        }
                        QLineEdit:focus {
                            background: rgb(70, 70, 90);
                            border: 1px solid rgb(100, 150, 200);
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
    
    def _auto_create_casare_node(self) -> None:
        """
        Automatically create and link CasareRPA node.
        Called during __init__ to ensure every visual node has a backing CasareRPA node.
        Handles all creation scenarios: menu, copy/paste, undo/redo, workflow loading.
        """
        if self._casare_node is not None:
            return  # Already has a node
        
        try:
            # Import here to avoid circular dependency
            from ..graph.node_registry import get_node_factory
            factory = get_node_factory()
            
            # Create the CasareRPA node
            casare_node = factory.create_casare_node(self)
            if casare_node:
                # Node is already linked via factory.create_casare_node -> set_casare_node
                pass
        except Exception:
            # Silently fail during initialization - node will be created later if needed
            # This handles cases where factory isn't ready yet (e.g., during testing)
            pass
    
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
            if hasattr(self.view, 'set_running'):
                self.view.set_running(True)
        elif status == "success":
            # Show checkmark, restore normal border
            self.set_property("_is_running", False)
            self.set_property("_is_completed", True)
            self.model.border_color = (68, 68, 68, 255)  # Normal border
            if hasattr(self.view, 'set_running'):
                self.view.set_running(False)
            if hasattr(self.view, 'set_completed'):
                self.view.set_completed(True)
            if hasattr(self.view, 'set_error'):
                self.view.set_error(False)
        elif status == "error":
            # Show error state with icon (keep dark background, red border + error icon)
            self.set_property("_is_running", False)
            self.set_property("_is_completed", False)
            self.set_color(45, 45, 45)  # Keep dark background - icon shows error
            self.model.border_color = (244, 67, 54, 255)  # Red border
            if hasattr(self.view, 'set_running'):
                self.view.set_running(False)
            if hasattr(self.view, 'set_completed'):
                self.view.set_completed(False)
            if hasattr(self.view, 'set_error'):
                self.view.set_error(True)
        else:  # idle
            # Restore default appearance
            self.set_property("_is_running", False)
            self.set_property("_is_completed", False)
            self.set_color(45, 45, 45)  # Dark background
            self.model.border_color = (68, 68, 68, 255)  # Normal border
            if hasattr(self.view, 'set_running'):
                self.view.set_running(False)
            if hasattr(self.view, 'set_completed'):
                self.view.set_completed(False)
            if hasattr(self.view, 'set_error'):
                self.view.set_error(False)

    def update_execution_time(self, time_seconds: Optional[float]) -> None:
        """
        Update the displayed execution time.

        Args:
            time_seconds: Execution time in seconds, or None to clear
        """
        if hasattr(self.view, 'set_execution_time'):
            self.view.set_execution_time(time_seconds)
