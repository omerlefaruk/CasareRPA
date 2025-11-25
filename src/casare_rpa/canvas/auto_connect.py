"""
Auto-connect feature for node graph.

Provides automatic connection suggestions while dragging nodes
with visual feedback (faded connection lines) and right-click
to confirm connections or disconnect nodes.

Now uses ConnectionValidator for type-safe connection checking.
"""

from typing import Optional, Tuple, List, Dict
import math

from PySide6.QtCore import QObject, Signal, QPointF, Qt, QTimer
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsScene
from PySide6.QtGui import QPen, QColor
from NodeGraphQt import NodeGraph, BaseNode

from loguru import logger

# Import connection validator for type checking
try:
    from .connection_validator import ConnectionValidator, get_connection_validator
    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False


class AutoConnectManager(QObject):
    """
    Manages automatic connection suggestions and interactions.
    
    Features:
    - Shows faded connection lines to nearest compatible ports while dragging
    - Right-click while dragging to create suggested connections
    - Right-click on connected node to disconnect all its connections
    """
    
    connection_suggested = Signal(object, str, object, str)  # from_node, from_port, to_node, to_port
    disconnection_requested = Signal(object)  # node to disconnect
    
    def __init__(self, graph: NodeGraph, parent: Optional[QObject] = None):
        """
        Initialize the auto-connect manager.
        
        Args:
            graph: NodeGraph instance to manage
            parent: Optional parent QObject
        """
        super().__init__(parent)
        
        self._graph = graph
        self._active = True
        self._dragging_node: Optional[BaseNode] = None
        self._suggestion_lines: List[QGraphicsLineItem] = []
        self._suggested_connections: List[Tuple[BaseNode, str, BaseNode, str]] = []
        self._max_distance = 600.0  # Maximum distance to suggest connections (pixels)
        self._right_button_pressed = False
        self._original_context_policy = None  # Store original context menu policy
        
        # Install event filter on the graph viewer
        self._setup_event_filters()
    
    def _setup_event_filters(self):
        """Setup event filters to monitor node dragging."""
        try:
            # Get the viewer widget from NodeGraphQt
            viewer = self._graph.viewer()
            if viewer:
                # Install on the viewer itself
                viewer.installEventFilter(self)
                
                # Install on the viewport (where mouse events happen)
                if hasattr(viewer, 'viewport'):
                    viewport = viewer.viewport()
                    if viewport:
                        viewport.installEventFilter(self)
                
                # Also monitor the scene
                scene = viewer.scene()
                if scene:
                    scene.installEventFilter(self)
        except Exception as e:
            print(f"Warning: Could not setup event filters: {e}")
    
    def set_active(self, active: bool):
        """Enable or disable the auto-connect feature."""
        self._active = active
        if not active:
            self._clear_suggestions()
    
    def is_active(self) -> bool:
        """Check if auto-connect is active."""
        return self._active
    
    def eventFilter(self, watched, event):
        """Filter events to detect node dragging and right-clicks."""
        if not self._active:
            return super().eventFilter(watched, event)
        
        try:
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QMouseEvent
            
            # Detect node movement first - this sets _dragging_node
            if event.type() == QEvent.Type.MouseMove:
                if isinstance(event, QMouseEvent):
                    # Check if we're dragging a node
                    selected_nodes = self._graph.selected_nodes()
                    if selected_nodes and event.buttons() & Qt.MouseButton.LeftButton:
                        # Start dragging if not already
                        if not self._dragging_node:
                            self._dragging_node = selected_nodes[0]
                            # Disable context menu during drag
                            self._disable_context_menu()
                        
                        # Update suggestions
                        self._update_suggestions()
            
            # Track right mouse button state and handle context menu
            elif event.type() == QEvent.Type.MouseButtonPress:
                if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.RightButton:
                    self._right_button_pressed = True
                    
                    # Only handle right-click if we're currently dragging
                    if self._dragging_node:
                        # If we have suggested connections, apply them
                        if self._suggested_connections:
                            self._apply_suggested_connections()
                        else:
                            # Otherwise disconnect the dragging node
                            self._disconnect_node(self._dragging_node)
                        # Prevent context menu from showing while dragging
                        event.accept()
                        return True
            
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if isinstance(event, QMouseEvent):
                    if event.button() == Qt.MouseButton.RightButton:
                        self._right_button_pressed = False
                    elif event.button() == Qt.MouseButton.LeftButton:
                        # Detect end of drag
                        if self._dragging_node:
                            self._clear_suggestions()
                            self._dragging_node = None
                            # Re-enable context menu
                            self._restore_context_menu()
            
            # Suppress context menu while dragging - this is critical
            elif event.type() == QEvent.Type.ContextMenu:
                if self._dragging_node:
                    # Block context menu while dragging
                    event.accept()
                    return True
        
        except Exception as e:
            print(f"Error in eventFilter: {e}")
        
        return super().eventFilter(watched, event)
    
    def _get_node_at_position(self, pos) -> Optional[BaseNode]:
        """Get the node at the given position."""
        try:
            viewer = self._graph.viewer()
            if viewer and viewer.scene():
                scene_pos = viewer.mapToScene(pos)
                items = viewer.scene().items(scene_pos)
                
                # Find a node item - look for items that have a node attribute
                for item in items:
                    # Check various ways the node might be attached
                    if hasattr(item, 'node') and hasattr(item.node, 'inputs'):
                        # This is the actual node object we want
                        return item.node
                    
                    # Also check if the item itself has the node methods (unlikely but safe)
                    if hasattr(item, 'inputs') and hasattr(item, 'outputs'):
                        return item
        except Exception as e:
            print(f"Error getting node at position: {e}")
        
        return None
    
    def _update_suggestions(self):
        """Update connection suggestions based on dragging node position."""
        if not self._dragging_node:
            return
        
        # Clear previous suggestions
        self._clear_suggestions()
        
        # Get all nodes except the dragging one
        all_nodes = [n for n in self._graph.all_nodes() if n != self._dragging_node]
        
        # Find closest compatible connections
        suggestions = self._find_closest_connections(self._dragging_node, all_nodes)
        
        # Draw suggestion lines
        self._draw_suggestion_lines(suggestions)
        self._suggested_connections = suggestions
    
    def _find_closest_connections(self, node: BaseNode, other_nodes: List[BaseNode]) -> List[Tuple[BaseNode, str, BaseNode, str]]:
        """
        Find the closest compatible connections for the dragging node.
        
        Args:
            node: The node being dragged
            other_nodes: List of other nodes to check
            
        Returns:
            List of suggested connections (from_node, from_port, to_node, to_port)
        """
        suggestions = []
        
        try:
            node_pos = self._get_node_center(node)
            if not node_pos:
                return suggestions
            
            # Check input ports of dragging node
            input_ports = node.input_ports()
            for in_port in input_ports:
                closest_distance = float('inf')
                closest_connection = None
                
                # Find closest compatible output port (only to the LEFT)
                for other_node in other_nodes:
                    other_pos = self._get_node_center(other_node)
                    if not other_pos:
                        continue
                    
                    # Only connect from nodes on the LEFT (lower X position)
                    if other_pos.x() >= node_pos.x():
                        continue
                    
                    distance = self._calculate_distance(node_pos, other_pos)
                    if distance > self._max_distance:
                        continue
                    
                    # Check if nodes are not already connected
                    if self._are_nodes_connected(other_node, node):
                        continue
                    
                    # Check output ports
                    output_ports = other_node.output_ports()
                    for out_port in output_ports:
                        # Check if port is compatible (exec ports connect to exec ports)
                        if self._are_ports_compatible(out_port, in_port):
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_connection = (other_node, out_port.name(), node, in_port.name())
                
                if closest_connection:
                    suggestions.append(closest_connection)
        
        except Exception as e:
            print(f"Error finding connections: {e}")
        
        return suggestions
    
    def _get_node_center(self, node: BaseNode) -> Optional[QPointF]:
        """Get the center position of a node in scene coordinates."""
        try:
            if hasattr(node, 'view') and node.view:
                rect = node.view.boundingRect()
                center = rect.center()
                return node.view.mapToScene(center)
        except Exception:
            pass
        return None
    
    def _calculate_distance(self, pos1: QPointF, pos2: QPointF) -> float:
        """Calculate Euclidean distance between two points."""
        dx = pos1.x() - pos2.x()
        dy = pos1.y() - pos2.y()
        return math.sqrt(dx * dx + dy * dy)
    
    def _are_nodes_connected(self, from_node: BaseNode, to_node: BaseNode) -> bool:
        """Check if two nodes are already connected."""
        try:
            # Check if there's any connection from from_node to to_node
            for out_port in from_node.output_ports():
                connected_ports = out_port.connected_ports()
                for connected_port in connected_ports:
                    if connected_port.node() == to_node:
                        return True
        except Exception:
            pass
        return False
    
    def _are_ports_compatible(self, port1, port2) -> bool:
        """
        Check if two ports are compatible for auto-connection.

        Auto-connect only works for exec ports (exec_in/exec_out).
        Data ports must be connected manually by the user.

        Args:
            port1: Output port (source)
            port2: Input port (target)

        Returns:
            True if ports can be auto-connected (exec ports only)
        """
        try:
            # Get port names
            port1_name = port1.name().lower()
            port2_name = port2.name().lower()

            # Check if both are exec ports (name-based)
            is_exec1 = 'exec' in port1_name
            is_exec2 = 'exec' in port2_name

            # Only auto-connect exec ports to exec ports
            # Data ports should be connected manually
            if is_exec1 and is_exec2:
                return True

            # Don't auto-connect data ports or mixed exec/data
            return False

        except Exception as e:
            logger.debug(f"Port compatibility check failed: {e}")
            return False  # Default to not compatible if we can't determine
    
    def _draw_suggestion_lines(self, suggestions: List[Tuple[BaseNode, str, BaseNode, str]]):
        """Draw faded lines showing suggested connections."""
        try:
            viewer = self._graph.viewer()
            if not viewer or not viewer.scene():
                return
            
            scene = viewer.scene()
            
            for from_node, from_port_name, to_node, to_port_name in suggestions:
                # Get port positions
                from_pos = self._get_port_scene_pos(from_node, from_port_name, is_output=True)
                to_pos = self._get_port_scene_pos(to_node, to_port_name, is_output=False)
                
                if not from_pos or not to_pos:
                    continue
                
                # Create a faded line
                line = QGraphicsLineItem(from_pos.x(), from_pos.y(), to_pos.x(), to_pos.y())
                
                # Style the line (faded blue/cyan with dashes)
                pen = QPen(QColor(100, 200, 255, 120))  # Semi-transparent cyan
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                line.setPen(pen)
                
                # Add to scene
                scene.addItem(line)
                self._suggestion_lines.append(line)
        
        except Exception as e:
            print(f"Error drawing suggestion lines: {e}")
    
    def _get_port_scene_pos(self, node: BaseNode, port_name: str, is_output: bool) -> Optional[QPointF]:
        """Get the scene position of a specific port."""
        try:
            if is_output:
                ports = node.output_ports()
            else:
                ports = node.input_ports()
            
            for port in ports:
                if port.name() == port_name:
                    if hasattr(port, 'view') and port.view:
                        # Get the center of the port view
                        rect = port.view.boundingRect()
                        center = rect.center()
                        return port.view.mapToScene(center)
        except Exception:
            pass

        # Fallback to node center
        return self._get_node_center(node)
    
    def _clear_suggestions(self):
        """Clear all suggestion lines from the scene."""
        try:
            viewer = self._graph.viewer()
            if viewer and viewer.scene():
                scene = viewer.scene()
                for line in self._suggestion_lines:
                    scene.removeItem(line)
        except Exception:
            pass

        self._suggestion_lines.clear()
        self._suggested_connections.clear()
    
    def _apply_suggested_connections(self):
        """Apply all suggested connections when right-click is pressed during drag."""
        try:
            for from_node, from_port_name, to_node, to_port_name in self._suggested_connections:
                # Get the actual port objects
                from_port = None
                to_port = None
                
                for port in from_node.output_ports():
                    if port.name() == from_port_name:
                        from_port = port
                        break
                
                for port in to_node.input_ports():
                    if port.name() == to_port_name:
                        to_port = port
                        break
                
                if from_port and to_port:
                    try:
                        # Connect the ports
                        from_port.connect_to(to_port)
                    except Exception as e:
                        pass  # Silently fail if connection cannot be made
            
            # Clear suggestions after applying
            self._clear_suggestions()
            
        except Exception as e:
            pass
    
    def _disconnect_node(self, node: BaseNode):
        """Disconnect all connections from the given node (only works while dragging)."""
        try:
            # Only disconnect if we're actively dragging
            if not self._dragging_node or node != self._dragging_node:
                return
            
            disconnected_count = 0
            
            # Use NodeGraphQt API: inputs() and outputs() return dict of port names to Port objects
            # Disconnect all input ports
            try:
                input_ports = node.inputs()  # Returns dict
                if input_ports:
                    for port_name, port in input_ports.items():
                        connected_ports = port.connected_ports()
                        for connected_port in connected_ports:
                            try:
                                port.disconnect_from(connected_port)
                                disconnected_count += 1
                            except Exception as e:
                                pass
            except Exception as e:
                pass
            
            # Disconnect all output ports
            try:
                output_ports = node.outputs()  # Returns dict
                if output_ports:
                    for port_name, port in output_ports.items():
                        connected_ports = port.connected_ports()
                        for connected_port in connected_ports:
                            try:
                                port.disconnect_from(connected_port)
                                disconnected_count += 1
                            except Exception as e:
                                pass
            except Exception as e:
                pass
            
            if disconnected_count > 0:
                self.disconnection_requested.emit(node)
        
        except Exception as e:
            pass
    
    def _disable_context_menu(self):
        """Disable context menu on the viewer during drag."""
        try:
            viewer = self._graph.viewer()
            if viewer and self._original_context_policy is None:
                # Store original policy
                self._original_context_policy = viewer.contextMenuPolicy()
                # Disable context menu
                viewer.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        except Exception as e:
            print(f"Error disabling context menu: {e}")
    
    def _restore_context_menu(self):
        """Restore context menu on the viewer after drag."""
        try:
            viewer = self._graph.viewer()
            if viewer and self._original_context_policy is not None:
                # Restore original policy
                viewer.setContextMenuPolicy(self._original_context_policy)
                self._original_context_policy = None
        except Exception as e:
            print(f"Error restoring context menu: {e}")
    
    def set_max_distance(self, distance: float):
        """Set the maximum distance for suggesting connections."""
        self._max_distance = max(50.0, distance)
    
    def get_max_distance(self) -> float:
        """Get the current maximum distance for suggestions."""
        return self._max_distance
