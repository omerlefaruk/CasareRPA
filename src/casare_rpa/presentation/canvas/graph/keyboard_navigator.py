"""
Keyboard navigation for node graph.

Provides arrow key navigation between connected nodes:
- Right: Follow output connection to next node
- Left: Follow input connection to previous node
- Up/Down: Navigate to sibling nodes (parallel branches)
- Home: Jump to Start node
- End: Jump to End node
- Tab: Cycle through all nodes
- Enter: Edit selected node (open properties)
- Delete: Delete selected node
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class KeyboardNavigator:
    """
    Keyboard navigation controller for the node graph.

    Enables arrow key navigation between connected nodes,
    with spatial awareness for parallel branches.
    """

    def __init__(self, graph: "NodeGraph") -> None:
        """
        Initialize keyboard navigator.

        Args:
            graph: NodeGraph instance to navigate
        """
        self._graph = graph
        self._current_node_id: Optional[str] = None
        self._node_cycle_index: int = 0

    @property
    def current_node_id(self) -> Optional[str]:
        """Get the currently focused node ID."""
        return self._current_node_id

    def set_current_node(self, node_id: Optional[str]) -> None:
        """
        Set the currently focused node.

        Args:
            node_id: Node ID to focus, or None to clear focus
        """
        self._current_node_id = node_id

    def navigate(self, direction: str) -> bool:
        """
        Navigate in the specified direction.

        Args:
            direction: One of "up", "down", "left", "right"

        Returns:
            True if navigation was successful
        """
        if not self._current_node_id:
            return self._select_start_node()

        next_node = self._find_next_node(direction)
        if next_node:
            self._select_and_focus(next_node)
            return True

        return False

    def navigate_home(self) -> bool:
        """
        Navigate to the Start node.

        Returns:
            True if Start node found and selected
        """
        start_node = self._find_start_node()
        if start_node:
            self._select_and_focus(start_node)
            return True
        return False

    def navigate_end(self) -> bool:
        """
        Navigate to the End node.

        Returns:
            True if End node found and selected
        """
        end_node = self._find_end_node()
        if end_node:
            self._select_and_focus(end_node)
            return True
        return False

    def cycle_next(self) -> bool:
        """
        Cycle to next node in the graph (Tab).

        Returns:
            True if navigation was successful
        """
        nodes = self._graph.all_nodes()
        if not nodes:
            return False

        self._node_cycle_index = (self._node_cycle_index + 1) % len(nodes)
        node = nodes[self._node_cycle_index]
        self._select_and_focus(node)
        return True

    def cycle_previous(self) -> bool:
        """
        Cycle to previous node in the graph (Shift+Tab).

        Returns:
            True if navigation was successful
        """
        nodes = self._graph.all_nodes()
        if not nodes:
            return False

        self._node_cycle_index = (self._node_cycle_index - 1) % len(nodes)
        node = nodes[self._node_cycle_index]
        self._select_and_focus(node)
        return True

    def _select_start_node(self) -> bool:
        """
        Select the first suitable node to start navigation.

        Priority:
        1. Currently selected node
        2. Start node (StartNode type)
        3. First node with no input connections
        4. First node in graph

        Returns:
            True if a node was selected
        """
        # Check for currently selected node
        selected = self._graph.selected_nodes()
        if selected:
            node = selected[0]
            self._current_node_id = node.id
            return True

        # Find Start node
        start_node = self._find_start_node()
        if start_node:
            self._select_and_focus(start_node)
            return True

        # Find first node with no inputs
        for node in self._graph.all_nodes():
            input_ports = node.input_ports()
            has_connections = False
            for port in input_ports:
                if port.connected_ports():
                    has_connections = True
                    break
            if not has_connections:
                self._select_and_focus(node)
                return True

        # Fallback to first node
        nodes = self._graph.all_nodes()
        if nodes:
            self._select_and_focus(nodes[0])
            return True

        return False

    def _find_start_node(self):
        """Find the Start node in the graph."""
        for node in self._graph.all_nodes():
            node_type = type(node).__name__.lower()
            identifier = getattr(node, "__identifier__", "").lower()
            if "start" in node_type or "start" in identifier:
                return node
        return None

    def _find_end_node(self):
        """Find the End node in the graph."""
        for node in self._graph.all_nodes():
            node_type = type(node).__name__.lower()
            identifier = getattr(node, "__identifier__", "").lower()
            if "end" in node_type or "end" in identifier:
                return node
        return None

    def _get_current_node(self):
        """Get the current node object from its ID."""
        if not self._current_node_id:
            return None

        for node in self._graph.all_nodes():
            if node.id == self._current_node_id:
                return node
        return None

    def _find_next_node(self, direction: str):
        """
        Find the next node in the given direction.

        Args:
            direction: Navigation direction

        Returns:
            Next node or None
        """
        current = self._get_current_node()
        if not current:
            return None

        if direction == "right":
            return self._find_output_connected_node(current)
        elif direction == "left":
            return self._find_input_connected_node(current)
        elif direction in ("up", "down"):
            return self._find_sibling_node(current, direction)

        return None

    def _find_output_connected_node(self, current):
        """
        Find node connected to current node's output.

        Priority:
        1. Exec output connection
        2. First data output connection
        3. Spatially closest node to the right
        """
        output_ports = current.output_ports()

        # Look for exec port first
        for port in output_ports:
            port_name = port.name().lower()
            if "exec" in port_name or "out" == port_name:
                connected = port.connected_ports()
                if connected:
                    return connected[0].node()

        # Any connected output
        for port in output_ports:
            connected = port.connected_ports()
            if connected:
                return connected[0].node()

        # Spatial fallback: nearest node to the right
        return self._find_nearest_spatial_node(current, "right")

    def _find_input_connected_node(self, current):
        """
        Find node connected to current node's input.

        Priority:
        1. Exec input connection
        2. First data input connection
        3. Spatially closest node to the left
        """
        input_ports = current.input_ports()

        # Look for exec port first
        for port in input_ports:
            port_name = port.name().lower()
            if "exec" in port_name or "in" == port_name:
                connected = port.connected_ports()
                if connected:
                    return connected[0].node()

        # Any connected input
        for port in input_ports:
            connected = port.connected_ports()
            if connected:
                return connected[0].node()

        # Spatial fallback: nearest node to the left
        return self._find_nearest_spatial_node(current, "left")

    def _find_sibling_node(self, current, direction: str):
        """
        Find sibling node (parallel branch) in up/down direction.

        Looks for nodes:
        - At similar X position (same column)
        - Connected to the same parent or child
        - Above or below current node

        Args:
            current: Current node
            direction: "up" or "down"
        """
        current_pos = current.pos()
        current_x, current_y = current_pos

        # Find siblings: nodes at similar X position
        candidates = []
        for node in self._graph.all_nodes():
            if node.id == current.id:
                continue

            pos = node.pos()
            node_x, node_y = pos

            # Check if in same column (within 150px tolerance)
            if abs(node_x - current_x) > 150:
                continue

            # Check direction
            if direction == "up" and node_y >= current_y:
                continue
            if direction == "down" and node_y <= current_y:
                continue

            distance = abs(node_y - current_y)
            candidates.append((distance, node))

        if not candidates:
            return None

        # Sort by distance and return closest
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _find_nearest_spatial_node(self, current, direction: str):
        """
        Find spatially nearest node in a direction.

        Args:
            current: Current node
            direction: "left", "right", "up", or "down"
        """
        current_pos = current.pos()
        current_x, current_y = current_pos

        candidates = []
        for node in self._graph.all_nodes():
            if node.id == current.id:
                continue

            pos = node.pos()
            node_x, node_y = pos

            # Filter by direction
            if direction == "right" and node_x <= current_x:
                continue
            if direction == "left" and node_x >= current_x:
                continue
            if direction == "up" and node_y >= current_y:
                continue
            if direction == "down" and node_y <= current_y:
                continue

            # Calculate distance
            dx = node_x - current_x
            dy = node_y - current_y
            distance = (dx * dx + dy * dy) ** 0.5

            candidates.append((distance, node))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _select_and_focus(self, node) -> None:
        """
        Select node and center view on it.

        Args:
            node: Node to select and focus
        """
        try:
            # Clear existing selection
            self._graph.clear_selection()

            # Select the node
            node.set_selected(True)

            # Update current node tracking
            self._current_node_id = node.id

            # Update cycle index
            all_nodes = self._graph.all_nodes()
            try:
                self._node_cycle_index = all_nodes.index(node)
            except ValueError:
                pass

            # Center view on node
            self._graph.center_on([node])

            logger.debug(f"Keyboard nav: selected {node.name()}")

        except Exception as e:
            logger.debug(f"Could not select node: {e}")

    def get_accessible_description(self, node) -> str:
        """
        Get accessibility description for a node.

        Args:
            node: Node to describe

        Returns:
            Human-readable description for screen readers
        """
        try:
            name = node.name()
            node_type = type(node).__name__
            pos = node.pos()

            # Count connections
            input_count = sum(1 for p in node.input_ports() for _ in p.connected_ports())
            output_count = sum(1 for p in node.output_ports() for _ in p.connected_ports())

            return (
                f"{name}, {node_type}, "
                f"position {int(pos[0])}, {int(pos[1])}, "
                f"{input_count} inputs, {output_count} outputs"
            )
        except Exception:
            return "Node"
