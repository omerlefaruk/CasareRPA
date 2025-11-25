"""
Base Visual Node for CasareRPA.

This module provides the base VisualNode class to avoid circular imports.
"""

from typing import Type, Optional, Any, Dict
from NodeGraphQt import BaseNode as NodeGraphQtBaseNode
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush
from PySide6.QtCore import Qt, QSize

from ..core.base_node import BaseNode as CasareBaseNode
from ..core.types import PortType, DataType
from ..core.port_type_system import PortTypeRegistry, get_port_type_registry
from loguru import logger

# Unified color scheme for all nodes matching the image colors
# Using dark teal/gray with cyan accent border (matches reference image)
UNIFIED_NODE_COLOR = QColor(52, 58, 64)  # Dark gray node body - #343a40

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
        super().__init__()

        # Reference to the underlying CasareRPA node
        self._casare_node: Optional[CasareBaseNode] = None

        # Port type registry for typed connections
        self._port_types: Dict[str, Optional[DataType]] = {}
        self._type_registry: PortTypeRegistry = get_port_type_registry()

        # Set node colors with category-based accents
        self._apply_category_colors()
        
        # Configure selection colors - transparent overlay, yellow border
        self.model.selected_color = (0, 0, 0, 0)  # Transparent selection overlay (no body color change)
        self.model.selected_border_color = (255, 215, 0, 255)  # Bright yellow border when selected
        
        # Set temporary icon (will be updated with actual icons later)
        icon_pixmap = self._create_temp_icon()
        self.model.icon = icon_pixmap
        
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
        """Apply category-based colors to the node."""
        from .node_icons import get_node_color, CATEGORY_COLORS

        # Get category color
        category_color = CATEGORY_COLORS.get(self.NODE_CATEGORY, QColor(68, 68, 68))

        # Dark background (same for all nodes)
        self.set_color(45, 45, 45)

        # Category-colored border (subtle accent)
        # Use darker/more subtle version of category color for border
        border_r = int(category_color.red() * 0.7)
        border_g = int(category_color.green() * 0.7)
        border_b = int(category_color.blue() * 0.7)
        self.model.border_color = (border_r, border_g, border_b, 255)

        # Light gray text
        self.model.text_color = (220, 220, 220, 255)

    def _create_temp_icon(self) -> str:
        """Create a professional icon for this node type."""
        from .node_icons import get_cached_node_icon

        # Use the node name to get the appropriate icon
        node_name = self.NODE_NAME
        return get_cached_node_icon(node_name, size=24)
    
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
            DataType if it's a data port, None if it's an exec port or unknown
        """
        return self._port_types.get(port_name, DataType.ANY)

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
            from .node_registry import get_node_factory
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
        elif status == "error":
            # Show error state (red background)
            self.set_property("_is_running", False)
            self.set_property("_is_completed", False)
            self.set_color(244, 67, 54)  # Red background
            self.model.border_color = (244, 67, 54, 255)  # Red border
            if hasattr(self.view, 'set_running'):
                self.view.set_running(False)
            if hasattr(self.view, 'set_completed'):
                self.view.set_completed(False)
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
