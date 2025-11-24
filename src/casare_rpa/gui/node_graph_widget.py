"""
Node graph widget wrapper for NodeGraphQt integration.

This module provides a wrapper around NodeGraphQt's NodeGraph
to integrate it with the PySide6 application.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QPen, QPainter, QPainterPath, QColor, QKeyEvent
from PySide6.QtCore import Qt, QObject, QEvent
from NodeGraphQt import NodeGraph
from NodeGraphQt.qgraphics.node_base import NodeItem

from ..utils.config import GUI_THEME
from .auto_connect import AutoConnectManager


class TooltipBlocker(QObject):
    """Event filter to block tooltips."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ToolTip:
            return True
        return False


# Monkey-patch NodeItem to use thicker selection border and rounded corners
_original_paint = NodeItem.paint

def _patched_paint(self, painter, option, widget):
    """Custom paint with thicker yellow border and rounded corners."""
    # Temporarily clear selection for child items to prevent dotted boxes
    option_copy = option.__class__(option)
    option_copy.state &= ~option_copy.state.State_Selected
    
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    # Get bounding rect
    rect = self.boundingRect()
    
    # Determine colors
    bg_color = QColor(*self.color)
    border_color = QColor(*self.border_color)
    
    if self.selected:
        # Thicker yellow border when selected (3px instead of 1.2px)
        border_width = 3.0
        border_color = QColor(255, 215, 0, 255)  # Bright yellow
        # Keep background the same (no overlay)
    else:
        border_width = 1.0
    
    # Create rounded rectangle path with 8px radius
    radius = 8.0
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    
    # Fill background
    painter.fillPath(path, bg_color)
    
    # Draw border
    pen = QPen(border_color, border_width)
    pen.setCosmetic(self.viewer().get_zoom() < 0.0)
    painter.strokePath(path, pen)
    
    painter.restore()
    
    # Draw child items (ports, text, widgets) without selection indicators
    for child in self.childItems():
        if child.isVisible():
            painter.save()
            painter.translate(child.pos())
            child.paint(painter, option_copy, widget)  # Use option without selection state
            painter.restore()

NodeItem.paint = _patched_paint





class NodeGraphWidget(QWidget):
    """
    Widget wrapper for NodeGraphQt's NodeGraph.
    
    Provides a Qt widget container for the node graph editor
    with custom styling and configuration.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the node graph widget.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        # Create node graph
        self._graph = NodeGraph()
        
        # Configure graph
        self._setup_graph()
        
        # Create auto-connect manager
        self._auto_connect = AutoConnectManager(self._graph, self)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._graph.widget)
        
        self.setLayout(layout)
        
        # Install event filter on graph viewer to capture Tab key for context menu
        self._graph.viewer().installEventFilter(self)
        
        # Install tooltip blocker
        self._tooltip_blocker = TooltipBlocker()
        self._graph.viewer().installEventFilter(self._tooltip_blocker)
        self._graph.viewer().viewport().installEventFilter(self._tooltip_blocker)
        
        # Fix MMB panning over items
        self._fix_mmb_panning()
    
    def _fix_mmb_panning(self):
        """
        Monkey-patch the viewer's mousePressEvent to allow panning with MMB
        even when hovering over items (nodes, ports, etc).
        """
        viewer = self._graph.viewer()
        ViewerClass = viewer.__class__
        
        # Only patch once
        if getattr(ViewerClass, '_patched_mmb', False):
            return
            
        original_mouse_press = ViewerClass.mousePressEvent
        
        def patched_mouse_press(viewer_self, event):
            # Call the original method first
            original_mouse_press(viewer_self, event)
            
            # If MMB was pressed, force MMB_state to True.
            # The original method sets MMB_state = False if it detects nodes under the cursor,
            # preventing panning. We override this behavior here to ensure MMB always pans.
            if event.button() == Qt.MouseButton.MiddleButton:
                viewer_self.MMB_state = True
        
        ViewerClass.mousePressEvent = patched_mouse_press
        ViewerClass._patched_mmb = True

    def _setup_graph(self) -> None:
        """Configure the node graph settings and appearance."""
        # Set graph background color to match image (very dark gray, almost black)
        self._graph.set_background_color(35, 35, 35)  # #232323
        
        # Set grid styling
        self._graph.set_grid_mode(1)  # Show grid
        
        # Set graph properties
        self._graph.set_pipe_style(1)  # Curved pipes (CURVED = 1, not 2)
        
        # Configure selection and connection colors
        # Get the viewer to apply custom colors
        viewer = self._graph.viewer()
        
        # Set selection colors - transparent overlay, thick yellow border
        if hasattr(viewer, '_node_sel_color'):
            viewer._node_sel_color = (0, 0, 0, 0)  # Transparent selection overlay
        if hasattr(viewer, '_node_sel_border_color'):
            viewer._node_sel_border_color = (255, 215, 0, 255)  # Bright yellow border
        
        # Set pipe colors - light gray curved lines
        if hasattr(viewer, '_pipe_color'):
            viewer._pipe_color = (100, 100, 100, 255)  # Gray pipes
        if hasattr(viewer, '_live_pipe_color'):
            viewer._live_pipe_color = (100, 100, 100, 255)  # Gray when dragging
        
        # Configure port colors to differentiate input/output
        # Input ports (left side) - cyan/teal color
        # Output ports (right side) - orange/amber color
        from NodeGraphQt.constants import PortEnum
        # Override the default port colors through the viewer
        if hasattr(viewer, '_port_color'):
            viewer._port_color = (100, 181, 246, 255)  # Light blue for ports
        if hasattr(viewer, '_port_border_color'):
            viewer._port_border_color = (66, 165, 245, 255)  # Darker blue border
    
    @property
    def graph(self) -> NodeGraph:
        """
        Get the underlying NodeGraph instance.
        
        Returns:
            NodeGraph instance
        """
        return self._graph
    
    def clear_graph(self) -> None:
        """Clear all nodes and connections from the graph."""
        self._graph.clear_session()
    
    def fit_to_selection(self) -> None:
        """Fit the view to the selected nodes."""
        self._graph.fit_to_selection()
    
    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self._graph.reset_zoom()
    
    def zoom_in(self) -> None:
        """Zoom in the graph view."""
        current_zoom = self._graph.get_zoom()
        self._graph.set_zoom(current_zoom + 0.1)
    
    def zoom_out(self) -> None:
        """Zoom out the graph view."""
        current_zoom = self._graph.get_zoom()
        self._graph.set_zoom(current_zoom - 0.1)
    
    def center_on_nodes(self) -> None:
        """Center the view on all nodes."""
        nodes = self._graph.all_nodes()
        if nodes:
            self._graph.center_on(nodes)
    
    def get_selected_nodes(self) -> list:
        """
        Get the currently selected nodes.
        
        Returns:
            List of selected node objects
        """
        return self._graph.selected_nodes()
    
    def clear_selection(self) -> None:
        """Clear node selection."""
        self._graph.clear_selection()
    
    @property
    def auto_connect(self) -> AutoConnectManager:
        """
        Get the auto-connect manager.
        
        Returns:
            AutoConnectManager instance
        """
        return self._auto_connect
    
    def set_auto_connect_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the auto-connect feature.
        
        Args:
            enabled: Whether to enable auto-connect
        """
        self._auto_connect.set_active(enabled)
    
    def is_auto_connect_enabled(self) -> bool:
        """
        Check if auto-connect is enabled.
        
        Returns:
            True if auto-connect is enabled
        """
        return self._auto_connect.is_active()
    
    def set_auto_connect_distance(self, distance: float) -> None:
        """
        Set the maximum distance for auto-connect suggestions.
        
        Args:
            distance: Maximum distance in pixels
        """
        self._auto_connect.set_max_distance(distance)
    
    def eventFilter(self, obj, event):
        """
        Event filter to capture Tab key press to show context menu.
        
        Args:
            obj: Object that received the event
            event: The event
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type() == event.Type.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key.Key_Tab:
                # Show context menu at cursor position
                viewer = self._graph.viewer()
                cursor_pos = viewer.cursor().pos()
                
                # Get the context menu and show it
                context_menu = self._graph.get_context_menu('graph')
                if context_menu and context_menu.qmenu:
                    context_menu.qmenu.exec(cursor_pos)
                
                return True  # Event handled
        
        return super().eventFilter(obj, event)
