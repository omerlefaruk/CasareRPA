"""
Process Map Widget for CasareRPA.

Visual representation of discovered process models using QGraphicsView.
Displays activities as nodes, transitions as edges with frequency labels.
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QWidget,
)

from loguru import logger

from casare_rpa.presentation.canvas.theme import THEME


class ActivityNode(QGraphicsRectItem):
    """
    Graphical representation of an activity in the process map.

    Displays activity name, type, and performance metrics.
    Color-coded based on performance (bottlenecks in red).
    """

    def __init__(
        self,
        node_id: str,
        node_type: str,
        x: float,
        y: float,
        width: float = 120,
        height: float = 50,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize activity node."""
        super().__init__(x, y, width, height, parent)
        self.node_id = node_id
        self.node_type = node_type
        self.is_entry = False
        self.is_exit = False
        self.is_bottleneck = False
        self.avg_duration_ms = 0.0
        self.frequency = 0

        self._setup_appearance()
        self._create_label()

    def _setup_appearance(self) -> None:
        """Set up visual appearance."""
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setBrush(QBrush(QColor(THEME.bg_node)))
        self.setPen(QPen(QColor(THEME.border), 2))
        self.setZValue(10)

    def _create_label(self) -> None:
        """Create text label for the node."""
        self._label = QGraphicsSimpleTextItem(self.node_type, self)
        self._label.setFont(QFont("Segoe UI", 9))
        self._label.setBrush(QBrush(QColor(THEME.text_primary)))

        # Center the label
        label_rect = self._label.boundingRect()
        node_rect = self.rect()
        x = node_rect.x() + (node_rect.width() - label_rect.width()) / 2
        y = node_rect.y() + (node_rect.height() - label_rect.height()) / 2
        self._label.setPos(x, y)

    def set_entry_node(self, is_entry: bool) -> None:
        """Mark as entry node with special styling."""
        self.is_entry = is_entry
        if is_entry:
            self.setPen(QPen(QColor(THEME.status_success), 3))

    def set_exit_node(self, is_exit: bool) -> None:
        """Mark as exit node with special styling."""
        self.is_exit = is_exit
        if is_exit:
            self.setPen(QPen(QColor(THEME.status_info), 3))

    def set_bottleneck(self, is_bottleneck: bool) -> None:
        """Mark as bottleneck with red styling."""
        self.is_bottleneck = is_bottleneck
        if is_bottleneck:
            self.setBrush(QBrush(QColor(THEME.status_error).darker(150)))
            self.setPen(QPen(QColor(THEME.status_error), 3))

    def set_metrics(self, avg_duration_ms: float, frequency: int) -> None:
        """Set performance metrics."""
        self.avg_duration_ms = avg_duration_ms
        self.frequency = frequency


class TransitionEdge(QGraphicsPathItem):
    """
    Graphical representation of a transition between activities.

    Displays frequency label and arrow direction.
    Line width scales with frequency.
    """

    def __init__(
        self,
        source_node: ActivityNode,
        target_node: ActivityNode,
        frequency: int,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """Initialize transition edge."""
        super().__init__(parent)
        self.source_node = source_node
        self.target_node = target_node
        self.frequency = frequency
        self.avg_duration_ms = 0.0
        self.error_rate = 0.0

        self._label: Optional[QGraphicsSimpleTextItem] = None
        self._arrow: Optional[QGraphicsPolygonItem] = None

        self._setup_appearance()
        self._update_path()

    def _setup_appearance(self) -> None:
        """Set up visual appearance."""
        # Line width scales with frequency (min 1, max 5)
        width = min(5, max(1, self.frequency / 10))
        self.setPen(QPen(QColor(THEME.accent_secondary), width))
        self.setZValue(5)

    def _update_path(self) -> None:
        """Update the edge path between nodes."""
        source_rect = self.source_node.sceneBoundingRect()
        target_rect = self.target_node.sceneBoundingRect()

        # Calculate connection points (center of node edges)
        source_center = source_rect.center()
        target_center = target_rect.center()

        # Determine which edge to connect from/to
        dx = target_center.x() - source_center.x()
        dy = target_center.y() - source_center.y()

        if abs(dx) > abs(dy):
            # Horizontal connection
            if dx > 0:
                start = QPointF(source_rect.right(), source_center.y())
                end = QPointF(target_rect.left(), target_center.y())
            else:
                start = QPointF(source_rect.left(), source_center.y())
                end = QPointF(target_rect.right(), target_center.y())
        else:
            # Vertical connection
            if dy > 0:
                start = QPointF(source_center.x(), source_rect.bottom())
                end = QPointF(target_center.x(), target_rect.top())
            else:
                start = QPointF(source_center.x(), source_rect.top())
                end = QPointF(target_center.x(), target_rect.bottom())

        # Create path
        path = QPainterPath()
        path.moveTo(start)
        path.lineTo(end)
        self.setPath(path)

        # Create arrowhead
        self._create_arrowhead(start, end)

        # Create frequency label
        self._create_label(start, end)

    def _create_arrowhead(self, start: QPointF, end: QPointF) -> None:
        """Create arrowhead at the end of the edge."""
        if self._arrow:
            self.scene().removeItem(self._arrow) if self.scene() else None

        # Calculate angle
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)

        # Arrowhead size
        arrow_size = 10

        # Calculate arrowhead points
        p1 = QPointF(
            end.x() - arrow_size * math.cos(angle - math.pi / 6),
            end.y() - arrow_size * math.sin(angle - math.pi / 6),
        )
        p2 = QPointF(
            end.x() - arrow_size * math.cos(angle + math.pi / 6),
            end.y() - arrow_size * math.sin(angle + math.pi / 6),
        )

        self._arrow_polygon = QPolygonF([end, p1, p2])

    def _create_label(self, start: QPointF, end: QPointF) -> None:
        """Create frequency label on the edge."""
        if self._label and self.scene():
            self.scene().removeItem(self._label)

        mid_x = (start.x() + end.x()) / 2
        mid_y = (start.y() + end.y()) / 2

        self._label = QGraphicsSimpleTextItem(str(self.frequency))
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setBrush(QBrush(QColor(THEME.text_secondary)))
        self._label.setPos(mid_x + 5, mid_y - 10)
        self._label.setZValue(15)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Paint the edge with arrowhead."""
        super().paint(painter, option, widget)

        # Draw arrowhead
        if hasattr(self, "_arrow_polygon"):
            painter.setBrush(QBrush(QColor(THEME.accent_secondary)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(self._arrow_polygon)

    def set_metrics(self, avg_duration_ms: float, error_rate: float) -> None:
        """Set performance metrics."""
        self.avg_duration_ms = avg_duration_ms
        self.error_rate = error_rate


class ProcessMapWidget(QGraphicsView):
    """
    Widget for visualizing discovered process models.

    Features:
    - Displays activities as nodes
    - Shows transitions with frequency
    - Color-codes bottlenecks in red
    - Highlights entry/exit nodes
    - Interactive: click node for details
    - Pan and zoom support

    Signals:
        node_clicked: Emitted when node is clicked (str: node_id)
        edge_clicked: Emitted when edge is clicked (str: source, str: target)
    """

    node_clicked = Signal(str)
    edge_clicked = Signal(str, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the process map widget."""
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._nodes: Dict[str, ActivityNode] = {}
        self._edges: List[TransitionEdge] = []
        self._model_data: Optional[Dict[str, Any]] = None

        self._setup_view()
        self._apply_styles()

        logger.debug("ProcessMapWidget initialized")

    def _setup_view(self) -> None:
        """Configure view settings."""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _apply_styles(self) -> None:
        """Apply visual styling."""
        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {THEME.bg_canvas};
                border: 1px solid {THEME.border_dark};
            }}
        """)
        self._scene.setBackgroundBrush(QBrush(QColor(THEME.bg_canvas)))

    def visualize_model(self, model: Dict[str, Any]) -> None:
        """
        Visualize a process model.

        Args:
            model: Process model data with nodes, edges, entry/exit nodes
        """
        self._scene.clear()
        self._nodes.clear()
        self._edges.clear()
        self._model_data = model

        if not model:
            return

        nodes = model.get("nodes", [])
        if isinstance(nodes, set):
            nodes = list(nodes)
        edges = model.get("edges", {})
        entry_nodes = set(model.get("entry_nodes", []))
        exit_nodes = set(model.get("exit_nodes", []))
        set(model.get("loop_nodes", []))
        node_types = model.get("node_types", {})

        # Layout nodes in a grid
        positions = self._calculate_layout(nodes, edges)

        # Create node graphics
        for node_id in nodes:
            node_type = node_types.get(node_id, node_id)
            x, y = positions.get(node_id, (0, 0))

            node_item = ActivityNode(node_id, node_type, x, y)
            node_item.set_entry_node(node_id in entry_nodes)
            node_item.set_exit_node(node_id in exit_nodes)

            self._scene.addItem(node_item)
            self._nodes[node_id] = node_item

        # Create edge graphics
        for source, targets in edges.items():
            if source not in self._nodes:
                continue
            source_node = self._nodes[source]

            for target, edge_data in targets.items():
                if target not in self._nodes:
                    continue
                target_node = self._nodes[target]

                freq = (
                    edge_data.frequency
                    if hasattr(edge_data, "frequency")
                    else edge_data.get("frequency", 1)
                )
                edge_item = TransitionEdge(source_node, target_node, freq)

                # Add label to scene
                if edge_item._label:
                    self._scene.addItem(edge_item._label)

                self._scene.addItem(edge_item)
                self._edges.append(edge_item)

        # Fit view to content
        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        logger.debug(
            f"Visualized process model with {len(nodes)} nodes and {len(self._edges)} edges"
        )

    def _calculate_layout(
        self, nodes: List[str], edges: Dict[str, Any]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate node positions using a simple layered layout.

        Args:
            nodes: List of node IDs
            edges: Edge dictionary

        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if not nodes:
            return {}

        positions = {}
        node_width = 140
        node_height = 70
        h_spacing = 80
        v_spacing = 50

        # Build adjacency for topological sort
        in_degree = {n: 0 for n in nodes}
        for source, targets in edges.items():
            for target in targets:
                if target in in_degree:
                    in_degree[target] += 1

        # Group nodes by layer (BFS-like)
        layers: List[List[str]] = []
        remaining = set(nodes)
        current_layer = [n for n in nodes if in_degree[n] == 0]

        if not current_layer:
            current_layer = [nodes[0]] if nodes else []

        while current_layer:
            layers.append(current_layer)
            remaining -= set(current_layer)

            next_layer = []
            for node in current_layer:
                if node in edges:
                    for target in edges[node]:
                        if target in remaining:
                            next_layer.append(target)
                            remaining.discard(target)

            current_layer = list(set(next_layer))

        # Add remaining nodes
        if remaining:
            layers.append(list(remaining))

        # Position nodes by layer
        y = 0
        for layer in layers:
            x = 0
            for node_id in layer:
                positions[node_id] = (x, y)
                x += node_width + h_spacing
            y += node_height + v_spacing

        return positions

    def highlight_bottlenecks(self, bottleneck_nodes: Set[str]) -> None:
        """
        Highlight bottleneck nodes in the visualization.

        Args:
            bottleneck_nodes: Set of node IDs that are bottlenecks
        """
        for node_id, node_item in self._nodes.items():
            node_item.set_bottleneck(node_id in bottleneck_nodes)

    def highlight_path(self, path: List[str]) -> None:
        """
        Highlight a specific execution path.

        Args:
            path: Ordered list of node IDs in the path
        """
        # Reset all edges
        for edge in self._edges:
            edge.setPen(QPen(QColor(THEME.accent_secondary), 2))

        # Highlight path edges
        path_set = set(zip(path[:-1], path[1:]))
        for edge in self._edges:
            key = (edge.source_node.node_id, edge.target_node.node_id)
            if key in path_set:
                edge.setPen(QPen(QColor(THEME.status_success), 4))

    def clear_highlights(self) -> None:
        """Clear all highlights."""
        for node_item in self._nodes.values():
            node_item.set_bottleneck(False)
            node_item.setBrush(QBrush(QColor(THEME.bg_node)))
            node_item.setPen(QPen(QColor(THEME.border), 2))

        for edge in self._edges:
            edge.setPen(QPen(QColor(THEME.accent_secondary), 2))

    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for zooming."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for node/edge selection."""
        super().mousePressEvent(event)

        item = self.itemAt(event.pos())
        if isinstance(item, ActivityNode):
            self.node_clicked.emit(item.node_id)
        elif isinstance(item, TransitionEdge):
            self.edge_clicked.emit(item.source_node.node_id, item.target_node.node_id)

    def fit_view(self) -> None:
        """Fit view to show all content."""
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def get_model_data(self) -> Optional[Dict[str, Any]]:
        """Get the current model data."""
        return self._model_data

    def cleanup(self) -> None:
        """Clean up resources."""
        self._scene.clear()
        self._nodes.clear()
        self._edges.clear()
        logger.debug("ProcessMapWidget cleaned up")


__all__ = ["ProcessMapWidget", "ActivityNode", "TransitionEdge"]
