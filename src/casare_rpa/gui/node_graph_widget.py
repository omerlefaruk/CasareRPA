"""
Node graph widget wrapper for NodeGraphQt integration.

This module provides a wrapper around NodeGraphQt's NodeGraph
to integrate it with the PySide6 application.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout
from NodeGraphQt import NodeGraph

from ..utils.config import GUI_THEME
from .auto_connect import AutoConnectManager


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
    
    def _setup_graph(self) -> None:
        """Configure the node graph settings and appearance."""
        # Set graph background color to match image (very dark gray, almost black)
        self._graph.set_background_color(35, 35, 35)  # #232323
        
        # Set grid styling
        self._graph.set_grid_mode(1)  # Show grid
        
        # Set graph properties
        self._graph.set_pipe_style(2)  # Curved pipes
    
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
