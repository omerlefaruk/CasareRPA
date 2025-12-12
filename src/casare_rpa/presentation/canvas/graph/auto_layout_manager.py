"""
Auto-layout manager for automatic node arrangement.

Implements a layered (Sugiyama-style) layout algorithm for
organizing workflow nodes in a readable, hierarchical arrangement.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any

from PySide6.QtCore import QObject, QPointF, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import QGraphicsItem

from loguru import logger


class LayoutDirection(Enum):
    """Layout direction options."""

    LEFT_TO_RIGHT = "LR"
    TOP_TO_BOTTOM = "TB"
    RIGHT_TO_LEFT = "RL"
    BOTTOM_TO_TOP = "BT"


@dataclass
class LayoutOptions:
    """
    Configuration options for auto-layout.

    Attributes:
        direction: Flow direction of the layout
        node_spacing_h: Horizontal spacing between nodes in same layer
        node_spacing_v: Vertical spacing between nodes in same layer
        layer_spacing: Spacing between layers
        align_to_start: Whether to align nodes to start node position
        animate: Whether to animate node transitions
        animation_duration: Duration of animation in milliseconds
    """

    direction: LayoutDirection = LayoutDirection.LEFT_TO_RIGHT
    node_spacing_h: int = 60
    node_spacing_v: int = 40
    layer_spacing: int = 200
    align_to_start: bool = True
    animate: bool = True
    animation_duration: int = 300


@dataclass
class LayoutNode:
    """
    Internal representation of a node for layout calculations.

    Attributes:
        node_id: Unique identifier
        item: Reference to the QGraphicsItem
        width: Node width
        height: Node height
        layer: Assigned layer (computed)
        position: Position within layer (computed)
        x: Final X coordinate (computed)
        y: Final Y coordinate (computed)
    """

    node_id: str
    item: Any  # NodeItem or similar
    width: float = 200
    height: float = 100
    layer: int = -1
    position: int = 0
    x: float = 0
    y: float = 0
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)


@dataclass
class LayoutEdge:
    """
    Internal representation of an edge for layout calculations.

    Attributes:
        source_id: Source node ID
        target_id: Target node ID
        is_exec: Whether this is an execution flow edge
    """

    source_id: str
    target_id: str
    is_exec: bool = False


class AutoLayoutManager(QObject):
    """
    Manages automatic layout of nodes in a workflow graph.

    Implements a layered graph drawing algorithm:
    1. Assign nodes to layers (topological sort)
    2. Order nodes within layers (minimize crossings)
    3. Assign coordinates (spacing, alignment)
    4. Optionally animate transition

    Usage:
        manager = AutoLayoutManager(graph)
        positions = manager.layout_workflow(direction="LR")

        # Or with selection only
        positions = manager.layout_selection(selected_nodes)
    """

    # Signal emitted when layout completes
    layout_completed = Signal()

    # Signal emitted for each node position update (for animation)
    node_position_changed = Signal(str, float, float)  # node_id, x, y

    def __init__(self, graph: Any = None, parent: Optional[QObject] = None) -> None:
        """
        Initialize the auto-layout manager.

        Args:
            graph: NodeGraph instance (optional, can set later)
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph = graph
        self._options = LayoutOptions()
        self._animations: List[QPropertyAnimation] = []
        self._pending_animations = 0

    def set_graph(self, graph: Any) -> None:
        """Set the graph instance."""
        self._graph = graph

    @property
    def options(self) -> LayoutOptions:
        """Get current layout options."""
        return self._options

    def set_options(self, options: LayoutOptions) -> None:
        """Set layout options."""
        self._options = options

    def layout_workflow(
        self,
        nodes: Optional[List[Any]] = None,
        connections: Optional[List[Any]] = None,
        direction: Optional[str] = None,
        animate: Optional[bool] = None,
    ) -> Dict[str, QPointF]:
        """
        Layout all or specified nodes in the workflow.

        Args:
            nodes: List of node items (uses all nodes if None)
            connections: List of connections (uses all if None)
            direction: Override layout direction ("LR", "TB", "RL", "BT")
            animate: Override animation setting

        Returns:
            Dictionary mapping node_id to new QPointF position
        """
        if self._graph is None:
            logger.warning("No graph set for auto-layout")
            return {}

        # Get nodes and connections
        if nodes is None:
            nodes = self._graph.all_nodes()
        if connections is None:
            connections = self._get_all_connections()

        if not nodes:
            return {}

        # Apply direction override
        if direction:
            try:
                self._options.direction = LayoutDirection(direction)
            except ValueError:
                logger.warning(f"Invalid layout direction: {direction}")

        # Apply animation override
        if animate is not None:
            self._options.animate = animate

        # Build internal graph representation
        layout_nodes, layout_edges = self._build_layout_graph(nodes, connections)

        if not layout_nodes:
            return {}

        # Execute layout algorithm
        positions = self._compute_layout(layout_nodes, layout_edges)

        # Apply positions (with or without animation)
        self._apply_positions(layout_nodes, positions)

        return positions

    def layout_selection(
        self,
        selected_nodes: List[Any],
        direction: Optional[str] = None,
        animate: Optional[bool] = None,
    ) -> Dict[str, QPointF]:
        """
        Layout only the selected nodes.

        Maintains relative positions of unselected nodes.

        Args:
            selected_nodes: List of selected node items
            direction: Override layout direction
            animate: Override animation setting

        Returns:
            Dictionary mapping node_id to new QPointF position
        """
        if not selected_nodes:
            return {}

        # Get connections between selected nodes only
        selected_ids = {self._get_node_id(n) for n in selected_nodes}
        connections = self._get_connections_between(selected_ids)

        return self.layout_workflow(
            nodes=selected_nodes,
            connections=connections,
            direction=direction,
            animate=animate,
        )

    def _get_all_connections(self) -> List[Tuple[str, str, bool]]:
        """
        Get all connections from the graph.

        Returns:
            List of (source_id, target_id, is_exec) tuples
        """
        connections = []
        try:
            for node in self._graph.all_nodes():
                node_id = self._get_node_id(node)
                for port in node.output_ports():
                    port_type = getattr(port, "data_type", "exec")
                    is_exec = port_type.lower() == "exec" or port.name().lower() in (
                        "exec_out",
                        "exec",
                    )
                    for connected_port in port.connected_ports():
                        target_node = connected_port.node()
                        target_id = self._get_node_id(target_node)
                        connections.append((node_id, target_id, is_exec))
        except Exception as e:
            logger.debug(f"Error getting connections: {e}")
        return connections

    def _get_connections_between(
        self, node_ids: Set[str]
    ) -> List[Tuple[str, str, bool]]:
        """Get connections where both endpoints are in the given set."""
        all_connections = self._get_all_connections()
        return [
            (src, tgt, is_exec)
            for src, tgt, is_exec in all_connections
            if src in node_ids and tgt in node_ids
        ]

    def _get_node_id(self, node: Any) -> str:
        """Extract node ID from a node object."""
        if hasattr(node, "id"):
            return str(node.id)
        if hasattr(node, "get_property"):
            try:
                return node.get_property("node_id") or str(id(node))
            except Exception:
                pass
        return str(id(node))

    def _build_layout_graph(
        self, nodes: List[Any], connections: List[Tuple[str, str, bool]]
    ) -> Tuple[Dict[str, LayoutNode], List[LayoutEdge]]:
        """
        Build internal graph representation for layout.

        Args:
            nodes: List of node items
            connections: List of (source_id, target_id, is_exec) tuples

        Returns:
            Tuple of (layout_nodes dict, layout_edges list)
        """
        layout_nodes: Dict[str, LayoutNode] = {}
        layout_edges: List[LayoutEdge] = []

        # Create layout nodes
        for node in nodes:
            node_id = self._get_node_id(node)
            try:
                # Get node dimensions
                if hasattr(node, "view") and node.view:
                    rect = node.view.boundingRect()
                    width = rect.width()
                    height = rect.height()
                else:
                    width = 200
                    height = 100

                layout_nodes[node_id] = LayoutNode(
                    node_id=node_id, item=node, width=width, height=height
                )
            except Exception as e:
                logger.debug(f"Error creating layout node: {e}")
                layout_nodes[node_id] = LayoutNode(node_id=node_id, item=node)

        # Create layout edges and build adjacency
        node_ids = set(layout_nodes.keys())
        for source_id, target_id, is_exec in connections:
            if source_id in node_ids and target_id in node_ids:
                layout_edges.append(
                    LayoutEdge(
                        source_id=source_id, target_id=target_id, is_exec=is_exec
                    )
                )
                layout_nodes[source_id].successors.append(target_id)
                layout_nodes[target_id].predecessors.append(source_id)

        return layout_nodes, layout_edges

    def _compute_layout(
        self, nodes: Dict[str, LayoutNode], edges: List[LayoutEdge]
    ) -> Dict[str, QPointF]:
        """
        Compute node positions using layered layout algorithm.

        Steps:
        1. Assign layers via topological sort
        2. Order nodes within layers
        3. Compute final coordinates

        Args:
            nodes: Dictionary of layout nodes
            edges: List of layout edges

        Returns:
            Dictionary mapping node_id to QPointF position
        """
        if not nodes:
            return {}

        # Step 1: Assign layers
        self._assign_layers(nodes)

        # Step 2: Order nodes within layers
        layers = self._group_by_layer(nodes)
        self._order_within_layers(nodes, layers)

        # Step 3: Compute coordinates
        positions = self._compute_coordinates(nodes, layers)

        return positions

    def _assign_layers(self, nodes: Dict[str, LayoutNode]) -> None:
        """
        Assign layers to nodes using longest-path algorithm.

        Nodes with no predecessors go to layer 0.
        Each other node is placed in the layer after its latest predecessor.
        """
        # Find root nodes (no predecessors in this subgraph)
        roots = [nid for nid, node in nodes.items() if not node.predecessors]

        if not roots:
            # Handle cycles: pick arbitrary start
            roots = [next(iter(nodes.keys()))]

        # BFS to assign layers
        visited: Set[str] = set()
        queue = deque(roots)

        # Initialize root layers
        for root in roots:
            nodes[root].layer = 0
            visited.add(root)

        while queue:
            node_id = queue.popleft()
            current_layer = nodes[node_id].layer

            for succ_id in nodes[node_id].successors:
                if succ_id not in nodes:
                    continue

                # Assign successor to layer after current
                new_layer = current_layer + 1
                if nodes[succ_id].layer < new_layer:
                    nodes[succ_id].layer = new_layer

                if succ_id not in visited:
                    visited.add(succ_id)
                    queue.append(succ_id)

        # Handle unvisited nodes (disconnected components)
        for node_id, node in nodes.items():
            if node.layer == -1:
                node.layer = 0

    def _group_by_layer(self, nodes: Dict[str, LayoutNode]) -> Dict[int, List[str]]:
        """Group nodes by their assigned layer."""
        layers: Dict[int, List[str]] = defaultdict(list)
        for node_id, node in nodes.items():
            layers[node.layer].append(node_id)
        return dict(layers)

    def _order_within_layers(
        self, nodes: Dict[str, LayoutNode], layers: Dict[int, List[str]]
    ) -> None:
        """
        Order nodes within each layer to minimize edge crossings.

        Uses barycenter heuristic: position node based on average
        position of connected nodes in adjacent layers.
        """
        # Sort layers by index
        layer_indices = sorted(layers.keys())

        if not layer_indices:
            return

        # Initial order based on original positions
        for layer_idx in layer_indices:
            layer_nodes = layers[layer_idx]
            layer_nodes.sort(key=lambda nid: self._get_original_position(nodes[nid]))
            for pos, nid in enumerate(layer_nodes):
                nodes[nid].position = pos

        # Multiple passes to improve ordering
        for _ in range(4):
            # Forward pass
            for i in range(1, len(layer_indices)):
                layer_idx = layer_indices[i]
                self._order_layer_by_barycenter(nodes, layers, layer_idx, i - 1)

            # Backward pass
            for i in range(len(layer_indices) - 2, -1, -1):
                layer_idx = layer_indices[i]
                self._order_layer_by_barycenter(nodes, layers, layer_idx, i + 1)

    def _get_original_position(self, node: LayoutNode) -> float:
        """Get original Y position of a node for initial ordering."""
        try:
            if hasattr(node.item, "pos"):
                pos = node.item.pos()
                if callable(pos):
                    return pos()[1]
                return pos.y()
        except Exception:
            pass
        return 0

    def _order_layer_by_barycenter(
        self,
        nodes: Dict[str, LayoutNode],
        layers: Dict[int, List[str]],
        layer_idx: int,
        ref_layer_idx: int,
    ) -> None:
        """Order nodes in a layer based on barycenter of adjacent layer."""
        if layer_idx not in layers:
            return

        layer_nodes = layers[layer_idx]
        ref_layer = layers.get(ref_layer_idx, [])

        if not ref_layer:
            return

        # Create position lookup for reference layer
        ref_positions = {nid: pos for pos, nid in enumerate(ref_layer)}

        # Calculate barycenter for each node
        barycenters: Dict[str, float] = {}
        for nid in layer_nodes:
            node = nodes[nid]
            connected = node.predecessors + node.successors
            connected_in_ref = [c for c in connected if c in ref_positions]

            if connected_in_ref:
                avg = sum(ref_positions[c] for c in connected_in_ref) / len(
                    connected_in_ref
                )
                barycenters[nid] = avg
            else:
                barycenters[nid] = node.position

        # Sort by barycenter
        layer_nodes.sort(key=lambda nid: barycenters[nid])

        # Update positions
        for pos, nid in enumerate(layer_nodes):
            nodes[nid].position = pos

    def _compute_coordinates(
        self, nodes: Dict[str, LayoutNode], layers: Dict[int, List[str]]
    ) -> Dict[str, QPointF]:
        """
        Compute final X, Y coordinates for each node.

        Args:
            nodes: Dictionary of layout nodes
            layers: Dictionary mapping layer index to node IDs

        Returns:
            Dictionary mapping node_id to QPointF position
        """
        positions: Dict[str, QPointF] = {}
        direction = self._options.direction

        # Determine base position from start node or (0, 0)
        base_x, base_y = 0.0, 0.0
        if self._options.align_to_start and layers.get(0):
            first_node_id = layers[0][0]
            first_node = nodes[first_node_id]
            try:
                if hasattr(first_node.item, "pos"):
                    pos = first_node.item.pos()
                    if callable(pos):
                        base_x, base_y = pos()
                    else:
                        base_x, base_y = pos.x(), pos.y()
            except Exception:
                pass

        # Compute positions based on direction
        layer_indices = sorted(layers.keys())

        for layer_idx in layer_indices:
            layer_nodes = layers[layer_idx]

            # Calculate layer position
            if direction == LayoutDirection.LEFT_TO_RIGHT:
                layer_x = base_x + layer_idx * self._options.layer_spacing
                for pos, nid in enumerate(layer_nodes):
                    node = nodes[nid]
                    y = base_y + pos * (node.height + self._options.node_spacing_v)
                    node.x = layer_x
                    node.y = y
                    positions[nid] = QPointF(layer_x, y)

            elif direction == LayoutDirection.TOP_TO_BOTTOM:
                layer_y = base_y + layer_idx * self._options.layer_spacing
                for pos, nid in enumerate(layer_nodes):
                    node = nodes[nid]
                    x = base_x + pos * (node.width + self._options.node_spacing_h)
                    node.x = x
                    node.y = layer_y
                    positions[nid] = QPointF(x, layer_y)

            elif direction == LayoutDirection.RIGHT_TO_LEFT:
                layer_x = base_x - layer_idx * self._options.layer_spacing
                for pos, nid in enumerate(layer_nodes):
                    node = nodes[nid]
                    y = base_y + pos * (node.height + self._options.node_spacing_v)
                    node.x = layer_x
                    node.y = y
                    positions[nid] = QPointF(layer_x, y)

            elif direction == LayoutDirection.BOTTOM_TO_TOP:
                layer_y = base_y - layer_idx * self._options.layer_spacing
                for pos, nid in enumerate(layer_nodes):
                    node = nodes[nid]
                    x = base_x + pos * (node.width + self._options.node_spacing_h)
                    node.x = x
                    node.y = layer_y
                    positions[nid] = QPointF(x, layer_y)

        return positions

    def _apply_positions(
        self, nodes: Dict[str, LayoutNode], positions: Dict[str, QPointF]
    ) -> None:
        """
        Apply computed positions to nodes.

        Args:
            nodes: Dictionary of layout nodes
            positions: Dictionary mapping node_id to QPointF
        """
        # Stop any running animations
        self._stop_animations()

        if self._options.animate:
            self._animate_positions(nodes, positions)
        else:
            self._set_positions_immediate(nodes, positions)

        self.layout_completed.emit()

    def _set_positions_immediate(
        self, nodes: Dict[str, LayoutNode], positions: Dict[str, QPointF]
    ) -> None:
        """Set node positions immediately without animation."""
        for node_id, pos in positions.items():
            if node_id not in nodes:
                continue

            node = nodes[node_id]
            try:
                if hasattr(node.item, "set_pos"):
                    node.item.set_pos(pos.x(), pos.y())
                elif hasattr(node.item, "setPos"):
                    node.item.setPos(pos)
            except Exception as e:
                logger.debug(f"Error setting node position: {e}")

            self.node_position_changed.emit(node_id, pos.x(), pos.y())

    def _animate_positions(
        self, nodes: Dict[str, LayoutNode], positions: Dict[str, QPointF]
    ) -> None:
        """Animate nodes to their new positions."""
        self._pending_animations = len(positions)

        for node_id, target_pos in positions.items():
            if node_id not in nodes:
                self._pending_animations -= 1
                continue

            node = nodes[node_id]
            item = node.item

            try:
                # Get view item for animation
                view_item = item.view if hasattr(item, "view") else item

                if not isinstance(view_item, QGraphicsItem):
                    # Can't animate non-graphics items
                    if hasattr(item, "set_pos"):
                        item.set_pos(target_pos.x(), target_pos.y())
                    self._pending_animations -= 1
                    continue

                # Create position animation
                animation = QPropertyAnimation(view_item, b"pos")
                animation.setDuration(self._options.animation_duration)
                animation.setStartValue(view_item.pos())
                animation.setEndValue(target_pos)
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)

                # Track completion
                animation.finished.connect(
                    lambda nid=node_id,
                    x=target_pos.x(),
                    y=target_pos.y(): self._on_animation_finished(nid, x, y)
                )

                self._animations.append(animation)
                animation.start()

            except Exception as e:
                logger.debug(f"Error animating node {node_id}: {e}")
                self._pending_animations -= 1

    def _on_animation_finished(self, node_id: str, x: float, y: float) -> None:
        """Handle animation completion for a node."""
        self._pending_animations -= 1
        self.node_position_changed.emit(node_id, x, y)

    def _stop_animations(self) -> None:
        """Stop all running animations."""
        for anim in self._animations:
            if anim.state() == QPropertyAnimation.State.Running:
                anim.stop()
        self._animations.clear()
        self._pending_animations = 0

    def is_animating(self) -> bool:
        """Check if layout animation is in progress."""
        return self._pending_animations > 0


# Module-level singleton
_auto_layout_manager: Optional[AutoLayoutManager] = None


def get_auto_layout_manager() -> AutoLayoutManager:
    """Get the global AutoLayoutManager instance."""
    global _auto_layout_manager
    if _auto_layout_manager is None:
        _auto_layout_manager = AutoLayoutManager()
    return _auto_layout_manager


def set_auto_layout_manager(manager: AutoLayoutManager) -> None:
    """Set the global AutoLayoutManager instance."""
    global _auto_layout_manager
    _auto_layout_manager = manager
