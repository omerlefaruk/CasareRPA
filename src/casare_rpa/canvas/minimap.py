"""
Minimap widget for the node graph.

Provides a bird's-eye view of the entire node graph with viewport indicator.
Overlays on the bottom-left corner of the canvas.

Now uses event-driven updates for better performance with large workflows.

References:
- "Designing Data-Intensive Applications" by Kleppmann - Event Sourcing
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from NodeGraphQt import NodeGraph

from loguru import logger


# ============================================================================
# CHANGE TRACKER (Event Sourcing Pattern)
# ============================================================================


class MinimapChangeTracker:
    """
    Tracks changes to determine when minimap needs update.

    Uses event sourcing pattern - only update when something changed.
    This reduces CPU usage significantly for large workflows.
    """

    def __init__(self, viewport_tolerance: float = 2.0):
        """
        Initialize change tracker.

        Args:
            viewport_tolerance: Tolerance for viewport position changes
        """
        self._dirty = True
        self._last_viewport_rect = QRectF()
        self._last_node_count = 0
        self._viewport_tolerance = viewport_tolerance

    def mark_dirty(self) -> None:
        """Mark state as dirty - requires update."""
        self._dirty = True

    def should_update(self, current_viewport: QRectF, node_count: int) -> bool:
        """
        Check if minimap needs redraw.

        Args:
            current_viewport: Current viewport rectangle
            node_count: Number of nodes in the graph

        Returns:
            True if update is needed
        """
        # Dirty flag set
        if self._dirty:
            return True

        # Node count changed
        if node_count != self._last_node_count:
            return True

        # Viewport moved significantly
        if not self._rects_equal(current_viewport, self._last_viewport_rect):
            return True

        return False

    def commit_update(self, viewport: QRectF, node_count: int) -> None:
        """
        Mark current state as rendered.

        Args:
            viewport: Current viewport rectangle
            node_count: Number of nodes
        """
        self._last_viewport_rect = QRectF(viewport)
        self._last_node_count = node_count
        self._dirty = False

    def _rects_equal(self, r1: QRectF, r2: QRectF) -> bool:
        """Check if two rectangles are approximately equal."""
        tolerance = self._viewport_tolerance
        return (
            abs(r1.x() - r2.x()) < tolerance
            and abs(r1.y() - r2.y()) < tolerance
            and abs(r1.width() - r2.width()) < tolerance
            and abs(r1.height() - r2.height()) < tolerance
        )


class MinimapView(QGraphicsView):
    """Custom QGraphicsView for minimap display."""
    
    viewport_clicked = Signal(QPointF)  # Emitted when user clicks on minimap
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize minimap view."""
        super().__init__(parent)
        
        # Create scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Configure view
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Disable interactive features - we handle mouse events manually
        self.setInteractive(False)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        self.setStyleSheet("""
            MinimapView {
                background-color: rgba(26, 26, 26, 200);
                border: 2px solid #555;
                border-radius: 6px;
            }
        """)
        
        # Minimap state
        self._node_rects = []  # List of (QRectF, color) tuples
        self._viewport_rect = QRectF()
        self._graph_bounds = QRectF()
        self._dragging = False
        
    def mousePressEvent(self, event):
        """Handle mouse press to navigate main view."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            # Map click position to scene coordinates
            scene_pos = self.mapToScene(event.pos())
            self.viewport_clicked.emit(scene_pos)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse drag to navigate main view."""
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.viewport_clicked.emit(scene_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)
    
    def update_minimap(self, node_rects, viewport_rect, graph_bounds):
        """
        Update minimap display.
        
        Args:
            node_rects: List of (QRectF, QColor) for each node
            viewport_rect: QRectF of visible viewport in scene coords
            graph_bounds: QRectF of entire graph bounds
        """
        self._node_rects = node_rects
        self._viewport_rect = viewport_rect
        self._graph_bounds = graph_bounds
        
        # Update scene rect
        if not graph_bounds.isEmpty():
            # Add padding
            padded_bounds = graph_bounds.adjusted(-50, -50, 50, 50)
            self._scene.setSceneRect(padded_bounds)
            self.fitInView(padded_bounds, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Trigger repaint
        self._scene.update()
        self.viewport().update()
    
    def drawForeground(self, painter, rect):
        """Draw minimap content."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw nodes
        for node_rect, color in self._node_rects:
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(80, 80, 80), 0.5))
            painter.drawRect(node_rect)
        
        # Draw viewport rectangle
        if not self._viewport_rect.isEmpty():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 215, 0), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(self._viewport_rect)


class Minimap(QWidget):
    """
    Minimap widget showing overview of node graph.

    Displays nodes as colored rectangles and shows current viewport.
    Clicking on minimap navigates the main view.

    Now uses event-driven updates for better performance:
    - Connects to node_created/nodes_deleted signals
    - Only updates when viewport or nodes change
    - Reduced timer interval (200ms instead of 100ms)
    """

    def __init__(self, node_graph: NodeGraph, parent: Optional[QWidget] = None):
        """
        Initialize minimap.

        Args:
            node_graph: NodeGraph instance to display
            parent: Parent widget
        """
        super().__init__(parent)

        self._node_graph = node_graph
        self._viewer = node_graph.viewer()

        # Create change tracker for event-driven updates
        self._change_tracker = MinimapChangeTracker()

        # Create minimap view
        self._minimap_view = MinimapView(self)
        self._minimap_view.viewport_clicked.connect(self._on_minimap_clicked)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._minimap_view)
        self.setLayout(layout)

        # Set fixed size (smaller)
        self.setFixedSize(200, 140)

        # Connect to graph signals for event-driven updates
        self._connect_signals()

        # Update timer (reduced interval - now just a fallback for viewport changes)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._check_and_update)
        self._update_timer.start(200)  # Reduced from 100ms to 200ms

        # Statistics for performance monitoring
        self._update_count = 0
        self._skip_count = 0

        # Initial update
        self._update_minimap()

    def _connect_signals(self) -> None:
        """Connect to graph signals for event-driven updates."""
        try:
            # Node created - mark dirty
            self._node_graph.node_created.connect(self._on_node_changed)

            # Nodes deleted - mark dirty
            self._node_graph.nodes_deleted.connect(self._on_nodes_changed)

            logger.debug("Minimap connected to graph signals for event-driven updates")
        except Exception as e:
            logger.warning(f"Could not connect minimap to graph signals: {e}")

    def _on_node_changed(self, node) -> None:
        """Handle node creation event."""
        self._change_tracker.mark_dirty()

    def _on_nodes_changed(self, node_ids) -> None:
        """Handle node deletion event."""
        self._change_tracker.mark_dirty()

    def _check_and_update(self) -> None:
        """Check if update is needed and perform if so."""
        if not self.isVisible():
            return

        # Get current state
        viewer_scene = self._viewer.scene()
        if not viewer_scene:
            return

        viewport_rect = self._viewer.mapToScene(
            self._viewer.viewport().rect()
        ).boundingRect()
        node_count = len(self._node_graph.all_nodes())

        # Only update if something changed
        if self._change_tracker.should_update(viewport_rect, node_count):
            self._update_minimap()
            self._change_tracker.commit_update(viewport_rect, node_count)
            self._update_count += 1
        else:
            self._skip_count += 1

    def mark_dirty(self) -> None:
        """Manually mark minimap as needing update."""
        self._change_tracker.mark_dirty()

    def get_stats(self) -> dict:
        """Get update statistics."""
        return {
            "updates": self._update_count,
            "skips": self._skip_count,
            "efficiency": (
                self._skip_count / max(1, self._update_count + self._skip_count) * 100
            ),
        }
    
    def _update_minimap(self):
        """Update minimap content."""
        # Get viewer's scene rect (what's actually visible considering zoom)
        viewer_scene = self._viewer.scene()
        if not viewer_scene:
            return
            
        # Get all nodes and their positions
        node_rects = []
        for node in self._node_graph.all_nodes():
            # Get node position and size
            pos = node.pos()
            
            # Get actual node size from view
            try:
                view_node = node.view
                if hasattr(view_node, 'boundingRect'):
                    bounds = view_node.boundingRect()
                    width = bounds.width()
                    height = bounds.height()
                else:
                    width = 200
                    height = 80
            except:
                width = 200
                height = 80
            
            rect = QRectF(pos[0], pos[1], width, height)
            
            # Get node color
            color = QColor(80, 120, 180)  # Default blue-gray
            if hasattr(node, 'model') and hasattr(node.model, 'color'):
                r, g, b, a = node.model.color
                color = QColor(r, g, b, a)
            
            node_rects.append((rect, color))
        
        # Get the actual visible viewport area in scene coordinates
        # This accounts for zoom level - when zoomed out, this rect is LARGER
        viewport_rect = self._viewer.mapToScene(self._viewer.viewport().rect()).boundingRect()
        
        # Calculate graph bounds (union of all nodes)
        if node_rects:
            graph_bounds = node_rects[0][0]
            for rect, _ in node_rects:
                graph_bounds = graph_bounds.united(rect)
            # Expand bounds to include viewport for better visualization
            graph_bounds = graph_bounds.united(viewport_rect)
        else:
            graph_bounds = viewport_rect if not viewport_rect.isEmpty() else QRectF(0, 0, 1000, 1000)
        
        # Update minimap view
        self._minimap_view.update_minimap(node_rects, viewport_rect, graph_bounds)
    
    def _on_minimap_clicked(self, scene_pos: QPointF):
        """
        Handle minimap click to navigate main view.
        
        Args:
            scene_pos: Position clicked in scene coordinates
        """
        # Center the main view on this position
        self._viewer.centerOn(scene_pos.x(), scene_pos.y())
    
    def set_update_interval(self, interval_ms: int):
        """
        Set minimap update interval.
        
        Args:
            interval_ms: Update interval in milliseconds
        """
        self._update_timer.setInterval(interval_ms)
    
    def set_visible(self, visible: bool):
        """
        Show or hide minimap.
        
        Args:
            visible: True to show, False to hide
        """
        super().setVisible(visible)
        if visible:
            self._update_minimap()
