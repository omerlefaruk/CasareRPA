"""
Viewport Culling Manager for CasareRPA Canvas.

Implements spatial partitioning for efficient visibility queries in large
workflows (100+ nodes). Uses a grid-based spatial hash for O(1) lookups.

References:
- "Designing Data-Intensive Applications" by Kleppmann - Partitioning
- Qt Graphics View Framework - Viewport optimization patterns
"""

from collections import defaultdict
from functools import partial
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger
from PySide6.QtCore import QObject, QRectF, Signal

from casare_rpa.presentation.canvas.telemetry import log_canvas_event

# ============================================================================
# SPATIAL HASH
# ============================================================================


class SpatialHash:
    """
    Grid-based spatial hash for efficient spatial queries.

    Divides the scene into cells and tracks which nodes occupy each cell.
    Supports fast queries for nodes within a rectangular region.
    """

    def __init__(self, cell_size: int = 500):
        """
        Initialize the spatial hash.

        Args:
            cell_size: Size of each grid cell in scene units (pixels)
        """
        self._cell_size = cell_size
        # Map from cell coordinates to set of node IDs in that cell
        self._cells: dict[tuple[int, int], set[str]] = defaultdict(set)
        # Map from node ID to the cells it occupies
        self._node_cells: dict[str, set[tuple[int, int]]] = {}

    def clear(self) -> None:
        """Clear all nodes from the spatial hash."""
        self._cells.clear()
        self._node_cells.clear()

    def insert(self, node_id: str, rect: QRectF) -> None:
        """
        Insert or update a node in the spatial hash.

        Args:
            node_id: Unique identifier for the node
            rect: Bounding rectangle of the node in scene coordinates
        """
        # Remove from old cells if exists
        self.remove(node_id)

        # Calculate which cells the rect overlaps
        new_cells = self._get_cells_for_rect(rect)

        # Add to new cells
        self._node_cells[node_id] = new_cells
        for cell in new_cells:
            self._cells[cell].add(node_id)

    def remove(self, node_id: str) -> None:
        """
        Remove a node from the spatial hash.

        Args:
            node_id: Unique identifier for the node
        """
        if node_id not in self._node_cells:
            return

        # Remove from all cells it was in
        for cell in self._node_cells[node_id]:
            self._cells[cell].discard(node_id)
            # Clean up empty cells
            if not self._cells[cell]:
                del self._cells[cell]

        del self._node_cells[node_id]

    def query(self, rect: QRectF) -> set[str]:
        """
        Query for all nodes that may intersect with the given rectangle.

        Args:
            rect: Query rectangle in scene coordinates

        Returns:
            Set of node IDs that may intersect (may include false positives)
        """
        cells = self._get_cells_for_rect(rect)
        result = set()
        for cell in cells:
            result.update(self._cells.get(cell, set()))
        return result

    def _get_cells_for_rect(self, rect: QRectF) -> set[tuple[int, int]]:
        """
        Calculate which cells a rectangle overlaps.

        Args:
            rect: Rectangle in scene coordinates

        Returns:
            Set of (x, y) cell coordinates
        """
        if rect.isEmpty():
            return set()

        # Calculate cell range
        x1 = int(rect.left() // self._cell_size)
        x2 = int(rect.right() // self._cell_size)
        y1 = int(rect.top() // self._cell_size)
        y2 = int(rect.bottom() // self._cell_size)

        cells = set()
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                cells.add((x, y))

        return cells

    @property
    def node_count(self) -> int:
        """Get the number of nodes in the spatial hash."""
        return len(self._node_cells)

    @property
    def cell_count(self) -> int:
        """Get the number of active cells."""
        return len(self._cells)


# ============================================================================
# VIEWPORT CULLING MANAGER
# ============================================================================


class ViewportCullingManager(QObject):
    """
    Manages visibility culling for large node graphs.

    Tracks node positions in a spatial hash and provides efficient
    queries for nodes visible within the current viewport.

    Features:
    - Spatial partitioning with configurable cell size
    - Margin-based culling (keep nodes slightly outside viewport)
    - Visibility state tracking to minimize show/hide calls
    - Pipe culling (hide connections to hidden nodes)

    Usage:
        culling = ViewportCullingManager(graph_widget)
        culling.update_viewport(viewport_rect)  # Call on pan/zoom
    """

    # Signal emitted when visibility changes
    visibility_changed = Signal(set, set)  # (visible_ids, hidden_ids)

    def __init__(self, cell_size: int = 500, margin: int = 1000, parent: QObject | None = None):
        """
        Initialize the viewport culling manager.

        Args:
            cell_size: Size of spatial hash cells (larger = fewer cells)
            margin: Extra margin around viewport for culling (default 1000 for smoother panning)
            parent: Optional parent QObject
        """
        super().__init__(parent)

        self._spatial_hash = SpatialHash(cell_size)
        self._margin = margin

        # Track visibility state
        self._visible_nodes: set[str] = set()
        self._all_nodes: set[str] = set()

        # Track node items for show/hide
        self._node_items: dict[str, object] = {}

        # Track pipes (connections) for culling
        # Maps pipe_id -> (source_node_id, target_node_id, pipe_item)
        self._pipes: dict[str, tuple[str, str, object]] = {}

        # Culling enabled flag
        self._enabled = True

        # Statistics
        self._stats = {
            "total_nodes": 0,
            "visible_nodes": 0,
            "total_pipes": 0,
            "visible_pipes": 0,
            "last_update_ms": 0,
        }

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable culling.

        When disabled, all nodes remain visible.

        Args:
            enabled: Whether culling should be active
        """
        self._enabled = enabled
        if not enabled:
            # Show all nodes and pipes
            self._show_all_nodes()
            self._show_all_pipes()

    def is_enabled(self) -> bool:
        """Check if culling is enabled."""
        return self._enabled

    def register_node(self, node_id: str, node_item: object, rect: QRectF) -> None:
        """
        Register a node with the culling manager.

        Args:
            node_id: Unique identifier for the node
            node_item: The QGraphicsItem for the node
            rect: Bounding rectangle in scene coordinates
        """
        self._all_nodes.add(node_id)
        self._node_items[node_id] = node_item
        self._spatial_hash.insert(node_id, rect)
        self._stats["total_nodes"] = len(self._all_nodes)

    def unregister_node(self, node_id: str) -> None:
        """
        Remove a node from the culling manager.

        Args:
            node_id: Unique identifier for the node
        """
        self._all_nodes.discard(node_id)
        self._visible_nodes.discard(node_id)
        self._node_items.pop(node_id, None)
        self._spatial_hash.remove(node_id)
        self._stats["total_nodes"] = len(self._all_nodes)

    def update_node_position(self, node_id: str, rect: QRectF) -> None:
        """
        Update a node's position in the spatial hash.

        Call this when a node is moved.

        Args:
            node_id: Unique identifier for the node
            rect: New bounding rectangle in scene coordinates
        """
        if node_id in self._all_nodes:
            self._spatial_hash.insert(node_id, rect)

    def register_pipe(
        self, pipe_id: str, source_node_id: str, target_node_id: str, pipe_item: object
    ) -> None:
        """
        Register a pipe (connection) for visibility culling.

        Pipes are shown only when both source and target nodes are visible.

        Args:
            pipe_id: Unique identifier for the pipe
            source_node_id: ID of the source node
            target_node_id: ID of the target node
            pipe_item: The QGraphicsItem for the pipe
        """
        self._pipes[pipe_id] = (source_node_id, target_node_id, pipe_item)
        self._stats["total_pipes"] = len(self._pipes)

    def unregister_pipe(self, pipe_id: str) -> None:
        """
        Remove a pipe from the culling manager.

        Args:
            pipe_id: Unique identifier for the pipe
        """
        self._pipes.pop(pipe_id, None)
        self._stats["total_pipes"] = len(self._pipes)

    def update_viewport(self, viewport_rect: QRectF) -> tuple[set[str], set[str]]:
        """
        Update visibility based on the current viewport.

        Args:
            viewport_rect: Current viewport rectangle in scene coordinates

        Returns:
            Tuple of (newly_visible_ids, newly_hidden_ids)
        """
        if not self._enabled:
            return set(), set()

        import time

        start = time.perf_counter()

        # Expand viewport by margin
        expanded_rect = viewport_rect.adjusted(
            -self._margin, -self._margin, self._margin, self._margin
        )

        # Query for potentially visible nodes
        potentially_visible = self._spatial_hash.query(expanded_rect)

        # Calculate deltas
        newly_visible = potentially_visible - self._visible_nodes
        newly_hidden = self._visible_nodes - potentially_visible

        # Update visibility state
        self._visible_nodes = potentially_visible.copy()

        # Apply visibility changes
        self._apply_visibility_changes(newly_visible, newly_hidden)

        # Update pipe visibility
        # Pass expanded_rect to check intersection for pipes
        visible_pipes = self._update_pipe_visibility(expanded_rect)

        # Update stats
        elapsed = (time.perf_counter() - start) * 1000
        self._stats["visible_nodes"] = len(self._visible_nodes)
        self._stats["visible_pipes"] = visible_pipes
        self._stats["last_update_ms"] = elapsed

        # Emit signal if there were changes
        if newly_visible or newly_hidden:
            self.visibility_changed.emit(newly_visible, newly_hidden)
            log_canvas_event(
                "viewport_cull_update",
                newly_visible=len(newly_visible),
                newly_hidden=len(newly_hidden),
                visible_nodes=len(self._visible_nodes),
                total_nodes=len(self._all_nodes),
            )

        return newly_visible, newly_hidden

    def _apply_visibility_changes(self, show_ids: set[str], hide_ids: set[str]) -> None:
        """
        Apply visibility changes to node items.

        Args:
            show_ids: Node IDs to show
            hide_ids: Node IDs to hide
        """
        for node_id in show_ids:
            item = self._node_items.get(node_id)
            if item and hasattr(item, "setVisible") and hasattr(item, "scene"):
                # Only modify visibility if item still belongs to a scene
                # This prevents Qt sendEvent warnings for orphaned items
                if item.scene() is not None:
                    item.setVisible(True)

        for node_id in hide_ids:
            item = self._node_items.get(node_id)
            if item and hasattr(item, "setVisible") and hasattr(item, "scene"):
                # Only modify visibility if item still belongs to a scene
                # This prevents Qt sendEvent warnings for orphaned items
                if item.scene() is not None:
                    item.setVisible(False)

    def _update_pipe_visibility(self, viewport_rect: QRectF) -> int:
        """
        Update visibility of pipes based on viewport intersection.

        FIXED: Previously only showed pipe if BOTH nodes were visible.
        Now shows pipe if it intersects the viewport rect, or if EITHER
        node is visible as a fallback.

        Args:
            viewport_rect: The expanded viewport rectangle to check against

        Returns:
            Number of visible pipes
        """
        visible_count = 0
        for pipe_id, (source_id, target_id, pipe_item) in self._pipes.items():
            should_be_visible = False

            # Check 1: Intersection with viewport (Most accurate)
            if (
                pipe_item
                and hasattr(pipe_item, "sceneBoundingRect")
                and hasattr(pipe_item, "scene")
                and pipe_item.scene() is not None
            ):
                # If pipe has a valid scene rect, check intersection
                # We use the expanded rect (with margin) to ensure smooth panning
                if pipe_item.sceneBoundingRect().intersects(viewport_rect):
                    should_be_visible = True

            # Check 2: Fallback to node visibility if intersection check fails/unavailable
            # Relaxed condition: Visible if EITHER source OR target is visible
            # (Old logic was AND, which caused long wires to disappear)
            if not should_be_visible:
                should_be_visible = (
                    source_id in self._visible_nodes or target_id in self._visible_nodes
                )

            if pipe_item and hasattr(pipe_item, "setVisible") and hasattr(pipe_item, "scene"):
                if pipe_item.scene() is not None:
                    pipe_item.setVisible(should_be_visible)

            if should_be_visible:
                visible_count += 1

        return visible_count

    def _show_all_pipes(self) -> None:
        """Show all pipes (used when culling is disabled)."""
        for pipe_id, (_, _, pipe_item) in self._pipes.items():
            if pipe_item and hasattr(pipe_item, "setVisible") and hasattr(pipe_item, "scene"):
                if pipe_item.scene() is not None:
                    pipe_item.setVisible(True)

    def _show_all_nodes(self) -> None:
        """Show all nodes (used when culling is disabled)."""
        for node_id, item in self._node_items.items():
            if item and hasattr(item, "setVisible") and hasattr(item, "scene"):
                # Only modify visibility if item still belongs to a scene
                if item.scene() is not None:
                    item.setVisible(True)
        self._visible_nodes = self._all_nodes.copy()

    def get_visible_nodes(self) -> set[str]:
        """Get the set of currently visible node IDs."""
        return self._visible_nodes.copy()

    def get_stats(self) -> dict:
        """Get culling statistics."""
        return self._stats.copy()

    def clear(self) -> None:
        """Clear all nodes and pipes from the culling manager."""
        self._spatial_hash.clear()
        self._visible_nodes.clear()
        self._all_nodes.clear()
        self._node_items.clear()
        self._pipes.clear()
        self._stats["total_nodes"] = 0
        self._stats["visible_nodes"] = 0
        self._stats["total_pipes"] = 0
        self._stats["visible_pipes"] = 0


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================


def create_viewport_culler_for_graph(
    graph_widget, cell_size: int = 500, margin: int = 1000
) -> ViewportCullingManager:
    """
    Create and integrate a ViewportCullingManager with a NodeGraphWidget.

    Args:
        graph_widget: The NodeGraphWidget to optimize
        cell_size: Spatial hash cell size
        margin: Viewport margin for culling

    Returns:
        Configured ViewportCullingManager
    """
    culler = ViewportCullingManager(cell_size, margin)

    # Register existing nodes
    try:
        graph = graph_widget.graph
        for node in graph.all_nodes():
            if hasattr(node, "view") and node.view:
                rect = node.view.sceneBoundingRect()
                culler.register_node(node.id, node.view, rect)
    except Exception as e:
        logger.warning(f"Could not register existing nodes for culling: {e}")

    # Connect signals for node changes
    try:
        graph = graph_widget.graph
        graph.node_created.connect(partial(_on_node_created, culler))
        graph.nodes_deleted.connect(partial(_on_nodes_deleted, culler))
    except Exception as e:
        logger.warning(f"Could not connect node signals for culling: {e}")

    return culler


def _on_node_created(culler: ViewportCullingManager, node) -> None:
    """Handle node creation event."""
    try:
        if hasattr(node, "view") and node.view:
            rect = node.view.sceneBoundingRect()
            culler.register_node(node.id, node.view, rect)
    except Exception as e:
        logger.debug(f"Error registering new node for culling: {e}")


def _on_nodes_deleted(culler: ViewportCullingManager, node_ids: list[str]) -> None:
    """Handle node deletion event."""
    try:
        for node_id in node_ids:
            culler.unregister_node(node_id)
    except Exception as e:
        logger.debug(f"Error unregistering deleted nodes from culling: {e}")
