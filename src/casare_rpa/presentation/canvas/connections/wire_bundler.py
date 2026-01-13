"""
Wire bundling system for CasareRPA canvas.

Groups 3+ parallel connections between the same node pair into a single
visual bundle with a count badge. Reduces visual clutter in complex workflows.

Features:
- Automatic bundling of 3+ wires between same node pairs
- Thick bundled wire with count badge at midpoint
- Hover to expand and show individual connections
- Click badge to select all bundled connections
"""

from collections import defaultdict

from loguru import logger
from NodeGraphQt import NodeGraph
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QStyleOptionGraphicsItem,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME

# ============================================================================
# BUNDLE VISUAL CONSTANTS
# ============================================================================

# Minimum wires needed to form a bundle
MIN_BUNDLE_SIZE = 3

# Bundle wire thickness
_BUNDLE_WIRE_THICKNESS = 4.0
_BUNDLE_WIRE_HOVER_THICKNESS = 5.0
_INDIVIDUAL_WIRE_OFFSET = 3.0  # Spacing between expanded wires

# Badge styling
_BADGE_FONT_SIZE = 10
_BADGE_PADDING_H = 4  # Horizontal padding
_BADGE_PADDING_V = 2  # Vertical padding
_BADGE_RADIUS = 4  # Corner radius


def _get_bundle_wire_color() -> QColor:
    """Get bundle wire color from theme."""
    return QColor(THEME.text_muted)


def _get_bundle_wire_hover_color() -> QColor:
    """Get bundle wire hover color from theme."""
    return QColor(THEME.text_secondary)


def _get_badge_bg_color() -> QColor:
    """Get badge background color from theme."""
    return QColor(THEME.bg_surface)


def _get_badge_text_color() -> QColor:
    """Get badge text color from theme."""
    return QColor(THEME.text_primary)


def _get_badge_border_color() -> QColor:
    """Get badge border color from theme."""
    return QColor(THEME.border_light)


class WireBundler(QObject):
    """
    Manager class that tracks and groups connections into bundles.

    Analyzes all connections in the graph and groups connections between
    the same node pairs. When 3+ connections exist between two nodes,
    they are rendered as a single bundled wire with a count badge.

    Signals:
        bundles_updated: Emitted when bundle groupings change
    """

    bundles_updated = Signal()

    def __init__(self, graph: NodeGraph, parent: QObject | None = None):
        """
        Initialize the wire bundler.

        Args:
            graph: NodeGraph instance to monitor
            parent: Optional parent QObject
        """
        super().__init__(parent)

        self._graph = graph
        self._enabled = True

        # Bundle storage: (source_node_id, target_node_id) -> list of pipe items
        self._bundles: dict[tuple[str, str], list[object]] = defaultdict(list)

        # Track which pipes are hidden (part of a bundle, not the primary)
        self._hidden_pipes: set[object] = set()

        # Track bundled pipe items we've created
        self._bundle_items: dict[tuple[str, str], BundledPipeItem] = {}

        # Debounce timer for bundle updates
        self._update_timer: QTimer | None = None

        # Connect to graph signals
        self._setup_signals()

    def _setup_signals(self) -> None:
        """Connect to graph signals for automatic bundle updates."""
        try:
            if hasattr(self._graph, "port_connected"):
                self._graph.port_connected.connect(self._on_connection_changed)
            if hasattr(self._graph, "port_disconnected"):
                self._graph.port_disconnected.connect(self._on_connection_changed)
            if hasattr(self._graph, "session_changed"):
                self._graph.session_changed.connect(self._on_session_changed)
        except Exception as e:
            logger.warning(f"Could not connect bundler signals: {e}")

    def _on_connection_changed(self, *args) -> None:
        """Handle connection change - schedule bundle update."""
        self._schedule_update()

    def _on_session_changed(self, *args) -> None:
        """Handle session change - clear and rebuild bundles."""
        self.clear()
        self._schedule_update()

    def _schedule_update(self) -> None:
        """Schedule a debounced bundle update."""
        if self._update_timer is None:
            self._update_timer = QTimer(self)
            self._update_timer.setSingleShot(True)
            self._update_timer.timeout.connect(self.update_bundles)

        # Restart timer (debounce)
        self._update_timer.start(50)  # 50ms debounce

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable wire bundling.

        Args:
            enabled: Whether bundling should be active
        """
        self._enabled = enabled
        if enabled:
            self.update_bundles()
        else:
            self._show_all_pipes()
            self._remove_bundle_items()

    def is_enabled(self) -> bool:
        """Check if wire bundling is enabled."""
        return self._enabled

    def clear(self) -> None:
        """Clear all bundle data and show all pipes."""
        self._show_all_pipes()
        self._remove_bundle_items()
        self._bundles.clear()
        self._hidden_pipes.clear()

    def _show_all_pipes(self) -> None:
        """Show all hidden pipes."""
        for pipe in self._hidden_pipes:
            try:
                if hasattr(pipe, "setVisible"):
                    pipe.setVisible(True)
            except Exception:
                pass
        self._hidden_pipes.clear()

    def _remove_bundle_items(self) -> None:
        """Remove all bundled pipe items from the scene."""
        viewer = self._graph.viewer()
        if not viewer or not viewer.scene():
            return

        scene = viewer.scene()
        for _bundle_key, bundle_item in list(self._bundle_items.items()):
            try:
                scene.removeItem(bundle_item)
            except Exception:
                pass
        self._bundle_items.clear()

    def update_bundles(self) -> None:
        """
        Analyze all connections and group into bundles.

        Scans all connections in the graph and groups those between
        the same node pairs. Creates bundle items for groups of 3+.
        """
        if not self._enabled:
            return

        # First, show all pipes and clear old bundle items
        self._show_all_pipes()
        self._remove_bundle_items()
        self._bundles.clear()

        # Collect all pipes grouped by node pair
        all_nodes = self._graph.all_nodes()

        for node in all_nodes:
            try:
                # Check output ports for connections
                for port in node.output_ports():
                    if not hasattr(port, "view") or not port.view:
                        continue

                    # Get connected pipes from port view
                    if hasattr(port.view, "connected_pipes"):
                        pipes = port.view.connected_pipes()
                        for pipe in pipes:
                            if not pipe:
                                continue

                            # Get source and target node IDs
                            source_node_id = node.id
                            target_node_id = self._get_target_node_id(pipe)

                            if source_node_id and target_node_id:
                                key = (source_node_id, target_node_id)
                                self._bundles[key].append(pipe)
            except Exception as e:
                logger.debug(f"Error collecting pipes from node: {e}")

        # Process bundles - hide secondary pipes and create bundle items
        self._process_bundles()

        self.bundles_updated.emit()

    def _get_target_node_id(self, pipe) -> str | None:
        """
        Get the target node ID from a pipe item.

        Args:
            pipe: Pipe item to query

        Returns:
            Target node ID or None
        """
        try:
            if hasattr(pipe, "input_port") and callable(pipe.input_port):
                input_port = pipe.input_port()
                if input_port and hasattr(input_port, "node"):
                    target_node = input_port.node()
                    if target_node:
                        return target_node.id
        except Exception:
            pass
        return None

    def _process_bundles(self) -> None:
        """Process bundle groups - hide secondary pipes and create bundle items."""
        viewer = self._graph.viewer()
        if not viewer or not viewer.scene():
            return

        scene = viewer.scene()

        for bundle_key, pipes in self._bundles.items():
            if len(pipes) < MIN_BUNDLE_SIZE:
                # Not enough pipes to bundle
                continue

            # Hide all pipes except first (primary)
            primary_pipe = pipes[0]
            for pipe in pipes[1:]:
                try:
                    if hasattr(pipe, "setVisible"):
                        pipe.setVisible(False)
                        self._hidden_pipes.add(pipe)
                except Exception:
                    pass

            # Create bundle item for this group
            try:
                bundle_item = BundledPipeItem(pipes, self)
                scene.addItem(bundle_item)
                self._bundle_items[bundle_key] = bundle_item

                # Hide the primary pipe too - bundle item replaces it
                if hasattr(primary_pipe, "setVisible"):
                    primary_pipe.setVisible(False)
                    self._hidden_pipes.add(primary_pipe)
            except Exception as e:
                logger.debug(f"Error creating bundle item: {e}")

    def get_bundle_for_pipe(self, pipe) -> list[object] | None:
        """
        Get the bundle containing this pipe, if any.

        Args:
            pipe: Pipe item to query

        Returns:
            List of pipes in the bundle, or None if not bundled
        """
        for _bundle_key, pipes in self._bundles.items():
            if pipe in pipes and len(pipes) >= MIN_BUNDLE_SIZE:
                return pipes
        return None

    def should_hide_pipe(self, pipe) -> bool:
        """
        Check if a pipe should be hidden (part of bundle, not primary).

        Args:
            pipe: Pipe item to check

        Returns:
            True if pipe should be hidden
        """
        return pipe in self._hidden_pipes

    def get_bundle_count(self, source_node_id: str, target_node_id: str) -> int:
        """
        Get the number of connections in a bundle.

        Args:
            source_node_id: Source node ID
            target_node_id: Target node ID

        Returns:
            Number of connections, or 0 if not bundled
        """
        key = (source_node_id, target_node_id)
        return len(self._bundles.get(key, []))

    def select_bundle(self, source_node_id: str, target_node_id: str) -> None:
        """
        Select all connections in a bundle.

        Args:
            source_node_id: Source node ID
            target_node_id: Target node ID
        """
        key = (source_node_id, target_node_id)
        pipes = self._bundles.get(key, [])

        # Clear existing selection
        viewer = self._graph.viewer()
        if viewer:
            viewer.clearSelection()

        # Select all pipes in the bundle
        for pipe in pipes:
            try:
                if hasattr(pipe, "setSelected"):
                    pipe.setSelected(True)
            except Exception:
                pass


class BundledPipeItem(QGraphicsObject):
    """
    Graphics item representing a bundle of connections.

    Renders as a thick wire with a count badge. On hover, expands
    to show individual connections with slight offsets.
    """

    def __init__(self, pipes: list[object], bundler: WireBundler, parent: QGraphicsItem = None):
        """
        Initialize the bundled pipe item.

        Args:
            pipes: List of pipe items in this bundle
            bundler: Parent WireBundler instance
            parent: Optional parent graphics item
        """
        super().__init__(parent)

        self._pipes = pipes
        self._bundler = bundler
        self._expanded = False
        self._hovered = False

        # Get source/target node IDs for badge click handling
        self._source_node_id: str | None = None
        self._target_node_id: str | None = None
        self._extract_node_ids()

        # Cache the path from first pipe
        self._cached_path = None
        self._update_path()

        # Enable hover events
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        # Cache font for badge
        self._badge_font = QFont("Segoe UI", _BADGE_FONT_SIZE)

    def _extract_node_ids(self) -> None:
        """Extract source and target node IDs from the first pipe."""
        if not self._pipes:
            return

        pipe = self._pipes[0]
        try:
            # Get source node ID
            if hasattr(pipe, "output_port") and callable(pipe.output_port):
                output_port = pipe.output_port()
                if output_port and hasattr(output_port, "node"):
                    source_node = output_port.node()
                    if source_node:
                        self._source_node_id = source_node.id

            # Get target node ID
            if hasattr(pipe, "input_port") and callable(pipe.input_port):
                input_port = pipe.input_port()
                if input_port and hasattr(input_port, "node"):
                    target_node = input_port.node()
                    if target_node:
                        self._target_node_id = target_node.id
        except Exception:
            pass

    def _update_path(self) -> None:
        """Update the cached path from the primary pipe."""
        if not self._pipes:
            return

        primary_pipe = self._pipes[0]
        try:
            if hasattr(primary_pipe, "path") and callable(primary_pipe.path):
                self._cached_path = primary_pipe.path()
        except Exception:
            self._cached_path = None

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of this item."""
        if not self._cached_path or self._cached_path.isEmpty():
            return QRectF(0, 0, 100, 100)

        # Expand bounding rect to include badge
        rect = self._cached_path.boundingRect()
        expanded = rect.adjusted(-20, -20, 20, 20)
        return expanded

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """
        Paint the bundled pipe.

        In collapsed state: thick wire with count badge
        In expanded state: individual wires with offsets
        """
        if not self._cached_path or self._cached_path.isEmpty():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._expanded:
            self._paint_expanded(painter)
        else:
            self._paint_collapsed(painter)

    def _paint_collapsed(self, painter: QPainter) -> None:
        """Paint the collapsed bundle (thick wire + badge)."""
        # Draw thick bundled wire
        wire_color = _get_bundle_wire_hover_color() if self._hovered else _get_bundle_wire_color()
        thickness = _BUNDLE_WIRE_HOVER_THICKNESS if self._hovered else _BUNDLE_WIRE_THICKNESS

        pen = QPen(wire_color, thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(self._cached_path)

        # Draw count badge at midpoint
        self._draw_badge(painter)

    def _paint_expanded(self, painter: QPainter) -> None:
        """Paint the expanded bundle (individual wires with offsets)."""
        if not self._cached_path or self._cached_path.isEmpty():
            return

        count = len(self._pipes)
        if count == 0:
            return

        # Calculate the perpendicular offset direction
        # We'll fan out the wires from the center
        try:
            # Get start and end points
            start = self._cached_path.pointAtPercent(0)
            end = self._cached_path.pointAtPercent(1)

            # Calculate perpendicular direction
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            length = (dx * dx + dy * dy) ** 0.5
            if length > 0:
                perp_x = -dy / length
                perp_y = dx / length
            else:
                perp_x, perp_y = 0, 1

            # Draw each pipe with offset
            for i, pipe in enumerate(self._pipes):
                # Calculate offset from center
                offset_index = i - (count - 1) / 2.0
                offset = offset_index * _INDIVIDUAL_WIRE_OFFSET

                # Get the wire color from the pipe if available
                if hasattr(pipe, "_get_wire_color") and callable(pipe._get_wire_color):
                    wire_color = pipe._get_wire_color()
                else:
                    wire_color = _get_bundle_wire_color()

                # Get thickness
                if hasattr(pipe, "_get_wire_thickness") and callable(pipe._get_wire_thickness):
                    thickness = pipe._get_wire_thickness()
                else:
                    thickness = 1.5

                pen = QPen(wire_color, thickness)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)

                # Draw offset path
                offset_path = self._cached_path.translated(offset * perp_x, offset * perp_y)
                painter.drawPath(offset_path)

        except Exception as e:
            logger.debug(f"Error painting expanded bundle: {e}")
            # Fallback to collapsed view
            self._paint_collapsed(painter)

    def _draw_badge(self, painter: QPainter) -> None:
        """Draw the count badge at the wire midpoint."""
        if self._cached_path.isEmpty():
            return

        count = len(self._pipes)
        badge_text = str(count)

        # Get midpoint
        try:
            mid = self._cached_path.pointAtPercent(0.5)
        except Exception:
            return

        # Calculate text size
        painter.setFont(self._badge_font)
        fm = QFontMetrics(self._badge_font)
        text_rect = fm.boundingRect(badge_text)

        # Calculate badge rect
        badge_width = text_rect.width() + _BADGE_PADDING_H * 2
        badge_height = text_rect.height() + _BADGE_PADDING_V * 2

        badge_rect = QRectF(
            mid.x() - badge_width / 2,
            mid.y() - badge_height / 2,
            badge_width,
            badge_height,
        )

        # Draw badge background
        painter.setBrush(QBrush(_get_badge_bg_color()))
        painter.setPen(QPen(_get_badge_border_color(), 1))
        painter.drawRoundedRect(badge_rect, _BADGE_RADIUS, _BADGE_RADIUS)

        # Draw badge text
        painter.setPen(QPen(_get_badge_text_color()))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter - expand to show individual wires."""
        self._hovered = True
        self._expanded = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave - collapse back to bundled view."""
        self._hovered = False
        self._expanded = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press - select all bundled connections."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on the badge
            if self._is_badge_click(event.pos()):
                self._select_all_connections()
                event.accept()
                return

        super().mousePressEvent(event)

    def _is_badge_click(self, pos: QPointF) -> bool:
        """Check if the click position is on the badge."""
        if self._cached_path.isEmpty():
            return False

        try:
            mid = self._cached_path.pointAtPercent(0.5)
            fm = QFontMetrics(self._badge_font)
            badge_text = str(len(self._pipes))
            text_rect = fm.boundingRect(badge_text)

            badge_width = text_rect.width() + _BADGE_PADDING_H * 2
            badge_height = text_rect.height() + _BADGE_PADDING_V * 2

            badge_rect = QRectF(
                mid.x() - badge_width / 2,
                mid.y() - badge_height / 2,
                badge_width,
                badge_height,
            )

            # Expand hit area slightly for easier clicking
            hit_rect = badge_rect.adjusted(-5, -5, 5, 5)
            return hit_rect.contains(pos)

        except Exception:
            return False

    def _select_all_connections(self) -> None:
        """Select all connections in this bundle."""
        if self._source_node_id and self._target_node_id:
            self._bundler.select_bundle(self._source_node_id, self._target_node_id)

    def refresh_path(self) -> None:
        """Refresh the cached path (call when nodes move)."""
        self._update_path()
        self.update()


# ============================================================================
# MODULE-LEVEL FUNCTIONS
# ============================================================================


_wire_bundler_instance: WireBundler | None = None


def get_wire_bundler() -> WireBundler | None:
    """
    Get the global wire bundler instance.

    Returns:
        WireBundler instance or None if not initialized
    """
    return _wire_bundler_instance


def set_wire_bundler(bundler: WireBundler | None) -> None:
    """
    Set the global wire bundler instance.

    Args:
        bundler: WireBundler instance to set as global
    """
    global _wire_bundler_instance
    _wire_bundler_instance = bundler
