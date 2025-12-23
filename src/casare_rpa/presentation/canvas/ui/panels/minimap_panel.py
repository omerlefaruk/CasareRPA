"""
Minimap Panel UI Component.

Provides a bird's-eye view of the workflow graph with viewport indicator.
Extracted from canvas/graph/minimap.py for reusability.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor

from loguru import logger


class MinimapChangeTracker:
    """
    Tracks changes to determine when minimap needs update.

    Uses event sourcing pattern to reduce unnecessary redraws.
    """

    def __init__(self, viewport_tolerance: float = 2.0) -> None:
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
        if self._dirty:
            return True

        if node_count != self._last_node_count:
            return True

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
        """
        Check if two rectangles are approximately equal.

        Args:
            r1: First rectangle
            r2: Second rectangle

        Returns:
            True if rectangles are approximately equal
        """
        tolerance = self._viewport_tolerance
        return (
            abs(r1.x() - r2.x()) < tolerance
            and abs(r1.y() - r2.y()) < tolerance
            and abs(r1.width() - r2.width()) < tolerance
            and abs(r1.height() - r2.height()) < tolerance
        )


class MinimapView(QGraphicsView):
    """
    Custom QGraphicsView for minimap display.

    Provides a simplified view of the workflow graph.
    """

    viewport_clicked = Signal(QPointF)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize minimap view.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setInteractive(False)

        # Create scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Viewport indicator
        self._viewport_rect = None

    def mousePressEvent(self, event):
        """
        Handle mouse press to navigate.

        Args:
            event: Mouse event
        """
        scene_pos = self.mapToScene(event.pos())
        self.viewport_clicked.emit(scene_pos)
        super().mousePressEvent(event)

    def set_viewport_rect(self, rect: QRectF) -> None:
        """
        Set the viewport indicator rectangle.

        Args:
            rect: Viewport rectangle in scene coordinates
        """
        self._viewport_rect = rect
        self.viewport().update()

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw viewport indicator overlay.

        Args:
            painter: QPainter instance
            rect: Scene rectangle to draw
        """
        if self._viewport_rect:
            painter.setPen(QPen(QColor("#5a8a9a"), 2))
            painter.setBrush(QBrush(QColor(90, 138, 154, 50)))
            painter.drawRect(self._viewport_rect)


class MinimapPanel(QWidget):
    """
    Minimap panel widget for workflow overview.

    Features:
    - Bird's-eye view of entire workflow
    - Viewport indicator
    - Click to navigate
    - Auto-scaling

    Signals:
        viewport_clicked: Emitted when user clicks on minimap (QPointF: scene_pos)
    """

    viewport_clicked = Signal(QPointF)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize minimap panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._graph_view = None
        self._change_tracker = MinimapChangeTracker()
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(200)  # Update every 200ms
        self._update_timer.timeout.connect(self._on_update_timer)

        self._setup_ui()
        self._apply_styles()

        logger.debug("MinimapPanel initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Minimap view
        self._minimap_view = MinimapView(self)
        self._minimap_view.viewport_clicked.connect(self._on_viewport_clicked)
        self._minimap_view.setFixedSize(200, 150)

        layout.addWidget(self._minimap_view)

    def _apply_styles(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)

    def set_graph_view(self, graph_view) -> None:
        """
        Set the main graph view to track.

        Args:
            graph_view: NodeGraphQt view instance
        """
        self._graph_view = graph_view
        self._change_tracker.mark_dirty()
        self._update_timer.start()
        logger.debug("Minimap graph view set")

    def update_minimap(self) -> None:
        """Update minimap display."""
        if not self._graph_view:
            return

        try:
            # Get graph scene
            scene = self._graph_view.scene()
            if not scene:
                return

            # Get scene bounds
            scene_rect = scene.itemsBoundingRect()
            if scene_rect.isEmpty():
                return

            # Get viewport rect
            viewport_rect = self._graph_view.mapToScene(
                self._graph_view.viewport().rect()
            ).boundingRect()

            # Check if update needed
            node_count = len([item for item in scene.items() if hasattr(item, "node")])
            if not self._change_tracker.should_update(viewport_rect, node_count):
                return

            # Update minimap scene
            self._minimap_view._scene.clear()

            # Draw nodes as small rectangles
            for item in scene.items():
                if hasattr(item, "node"):
                    node_rect = item.boundingRect()
                    pos = item.scenePos()
                    rect = QRectF(
                        pos.x(),
                        pos.y(),
                        node_rect.width() * 0.5,
                        node_rect.height() * 0.5,
                    )
                    self._minimap_view._scene.addRect(
                        rect, QPen(QColor("#4a4a4a")), QBrush(QColor("#3d3d3d"))
                    )

            # Draw connections
            for item in scene.items():
                if hasattr(item, "draw_path"):
                    path = item.path()
                    self._minimap_view._scene.addPath(path, QPen(QColor("#2d2d2d"), 0.5))

            # Fit in view
            self._minimap_view.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)

            # Update viewport indicator
            self._minimap_view.set_viewport_rect(viewport_rect)

            # Mark update complete
            self._change_tracker.commit_update(viewport_rect, node_count)

        except Exception as e:
            logger.error(f"Failed to update minimap: {e}")

    def mark_dirty(self) -> None:
        """Mark minimap as needing update."""
        self._change_tracker.mark_dirty()

    def _on_update_timer(self) -> None:
        """Handle update timer."""
        self.update_minimap()

    def _on_viewport_clicked(self, scene_pos: QPointF) -> None:
        """
        Handle viewport click.

        Args:
            scene_pos: Clicked position in scene coordinates
        """
        self.viewport_clicked.emit(scene_pos)
        logger.debug(f"Minimap clicked at: {scene_pos}")

    def showEvent(self, event) -> None:
        """
        Handle show event.

        Args:
            event: Show event
        """
        super().showEvent(event)
        self._update_timer.start()

    def hideEvent(self, event) -> None:
        """
        Handle hide event.

        Args:
            event: Hide event
        """
        super().hideEvent(event)
        self._update_timer.stop()
