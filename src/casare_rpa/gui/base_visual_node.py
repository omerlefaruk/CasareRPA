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
        
        # Set node colors to match reference image
        # Dark background with dark gray border
        self.set_color(45, 45, 45)  # Dark node background
        self.model.border_color = (68, 68, 68, 255)  # Dark gray border
        self.model.text_color = (220, 220, 220, 255)  # Light gray text
        
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
    
    def _create_temp_icon(self) -> str:
        """Create a temporary icon placeholder."""
        # Create a simple colored square as placeholder
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a rounded square with category color
        category_colors = {
            'basic': QColor(100, 181, 246),     # Light blue
            'browser': QColor(156, 39, 176),    # Purple
            'navigation': QColor(66, 165, 245),  # Blue
            'interaction': QColor(255, 167, 38), # Orange
            'data': QColor(102, 187, 106),       # Green
            'wait': QColor(255, 202, 40),        # Yellow
            'variable': QColor(171, 71, 188),    # Deep purple
        }
        
        color = category_colors.get(self.NODE_CATEGORY, QColor(158, 158, 158))
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(2, 2, size-4, size-4, 4, 4)
        painter.end()
        
        # Save to temp file and return path
        import tempfile
        import os
        temp_path = os.path.join(tempfile.gettempdir(), f"casare_icon_{id(self)}.png")
        pixmap.save(temp_path, "PNG")
        return temp_path
    
    def setup_ports(self) -> None:
        """
        Setup node ports.
        
        Override this method in subclasses to define ports.
        """
        pass
    
    def _configure_port_colors(self) -> None:
        """Configure different colors for input and output ports."""
        # Input ports (left side) - Cyan/Teal
        for port in self.input_ports():
            port.color = (100, 181, 246, 255)  # Light blue
            port.border_color = (66, 165, 245, 255)  # Darker blue border
        
        # Output ports (right side) - Orange/Amber
        for port in self.output_ports():
            port.color = (255, 167, 38, 255)  # Orange
            port.border_color = (251, 140, 0, 255)  # Darker orange border
    
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
                            background: rgba(60, 60, 80, 180);
                            border: 1px solid rgb(80, 80, 100);
                            border-radius: 3px;
                            color: rgba(230, 230, 230, 255);
                            padding: 2px;
                            selection-background-color: rgba(100, 150, 200, 150);
                        }
                        QLineEdit:focus {
                            background: rgba(70, 70, 90, 200);
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
