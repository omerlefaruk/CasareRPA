"""
CasareRPA - Validation Rules Module

Contains validation rules, constraints, and helper functions for connection parsing
and port type checking.
"""

from typing import Any

# ============================================================================
# UNIFIED CONNECTION PARSING
# ============================================================================


def parse_connection(conn: dict[str, Any]) -> dict[str, str] | None:
    """
    Parse a connection from any format into a normalized structure.

    Handles:
    - Format 1: {"source_node": "...", "source_port": "...", "target_node": "...", "target_port": "..."}
    - Format 2: {"out": ["node_id", "port"], "in": ["node_id", "port"]}

    Returns:
        Normalized dict with source_node, source_port, target_node, target_port
        or None if parsing fails
    """
    if "source_node" in conn:
        return {
            "source_node": conn.get("source_node", ""),
            "source_port": conn.get("source_port", ""),
            "target_node": conn.get("target_node", ""),
            "target_port": conn.get("target_port", ""),
        }
    elif "out" in conn and "in" in conn:
        out_data = conn.get("out", [])
        in_data = conn.get("in", [])
        if len(out_data) >= 2 and len(in_data) >= 2:
            return {
                "source_node": out_data[0],
                "source_port": out_data[1],
                "target_node": in_data[0],
                "target_port": in_data[1],
            }
    return None


def is_exec_port(port_name: str) -> bool:
    """Check if a port name indicates an execution flow port."""
    if not port_name:
        return False
    # Port names with leading/trailing whitespace are malformed - reject them
    if port_name != port_name.strip():
        return False
    port_lower = port_name.lower()
    exec_port_names = {
        "exec_in",
        "exec_out",
        "exec",
        "loop_body",
        "completed",
        "true",
        "false",
        "then",
        "else",
        "on_success",
        "on_error",
        "on_finally",
        "body",
        "done",
        "finish",
        "next",
    }
    return port_lower in exec_port_names or "exec" in port_lower


def is_exec_input_port(port_name: str) -> bool:
    """Check if a port is an execution INPUT port (receives exec flow)."""
    if not port_name:
        return False
    port_lower = port_name.lower()
    # These ports receive execution flow (are targets of exec connections)
    exec_input_names = {
        "exec_in",
        "exec",
        "loop_body",  # ForLoop body input
        "true",
        "false",  # If/Branch inputs
        "then",
        "else",
        "on_success",
        "on_error",
        "on_finally",
        "body",
    }
    return port_lower in exec_input_names or port_lower == "exec_in"


# ============================================================================
# GRAPH ANALYSIS
# ============================================================================


def has_circular_dependency(
    nodes: dict[str, Any],
    connections: list[dict[str, Any]],
) -> bool:
    """Check for circular dependencies using iterative DFS on exec connections.

    Uses an iterative approach (stack-based) instead of recursion to avoid
    RecursionError on large workflows (500+ nodes).
    """

    # Build adjacency list (only exec connections for flow)
    graph: dict[str, list[str]] = {node_id: [] for node_id in nodes}

    for conn in connections:
        parsed = parse_connection(conn)
        if not parsed:
            continue

        source = parsed["source_node"]
        source_port = parsed["source_port"]
        target = parsed["target_node"]

        # Only consider execution flow connections
        if source in graph and is_exec_port(source_port):
            graph[source].append(target)

    # Iterative DFS with explicit stack for cycle detection
    # States: 0=unvisited, 1=in recursion stack, 2=finished
    state: dict[str, int] = {node_id: 0 for node_id in nodes}

    for start_node in nodes:
        if state[start_node] != 0:
            continue

        # Stack entries: (node, iterator over neighbors, is_entering)
        # is_entering=True means we just entered, False means backtracking
        stack: list = [(start_node, iter(graph.get(start_node, [])), True)]

        while stack:
            node, neighbors_iter, is_entering = stack.pop()

            if is_entering:
                if state[node] == 1:
                    # Back edge found - cycle detected
                    return True
                if state[node] == 2:
                    # Already fully processed
                    continue

                # Mark as in recursion stack
                state[node] = 1
                # Push backtrack marker
                stack.append((node, neighbors_iter, False))

                # Process all neighbors
                for neighbor in neighbors_iter:
                    if neighbor in graph:
                        if state[neighbor] == 1:
                            # Back edge - cycle
                            return True
                        if state[neighbor] == 0:
                            stack.append((neighbor, iter(graph.get(neighbor, [])), True))
            else:
                # Backtracking - mark as finished
                state[node] = 2

    return False


def find_entry_points_and_reachable(
    nodes: dict[str, Any],
    connections: list[dict[str, Any]],
) -> tuple[list[str], set[str]]:
    """
    Find workflow entry points and all reachable nodes.

    Entry points are nodes that:
    1. Are named/typed as StartNode, OR
    2. Have no incoming exec connections

    Returns:
        Tuple of (entry_point_ids, reachable_node_ids)
    """

    # Build adjacency list for BFS traversal (ALL connections, not just exec)
    graph: dict[str, list[str]] = {node_id: [] for node_id in nodes}

    # Track which nodes have incoming exec connections
    nodes_with_exec_input: set[str] = set()
    # Track which nodes have outgoing connections (are part of a flow)
    nodes_with_outgoing: set[str] = set()

    for conn in connections:
        parsed = parse_connection(conn)
        if not parsed:
            continue

        source = parsed["source_node"]
        target = parsed["target_node"]
        target_port = parsed["target_port"]

        # Add edge to graph (all connections for reachability)
        if source in graph:
            graph[source].append(target)
            nodes_with_outgoing.add(source)

        # Track nodes receiving exec input
        if is_exec_input_port(target_port):
            nodes_with_exec_input.add(target)

    # Find entry points:
    # 1. Explicit StartNode types
    # 2. Nodes without incoming exec connections that ARE part of the flow
    #    (have outgoing connections)
    entry_points: list[str] = []

    for node_id, node_data in nodes.items():
        # Skip hidden/auto nodes when determining entry points
        if node_id.startswith("__"):
            # But auto_start IS an entry point
            if node_id == "__auto_start__":
                entry_points.append(node_id)
            continue

        # Get node type
        node_type = ""
        if isinstance(node_data, dict):
            node_type = node_data.get("node_type", "")

        # StartNode is always an entry point
        if node_type == "StartNode":
            entry_points.append(node_id)
        # Other nodes without incoming exec are entry points ONLY if they
        # have outgoing connections (are part of a workflow flow)
        elif node_id not in nodes_with_exec_input and node_id in nodes_with_outgoing:
            entry_points.append(node_id)

    # If still no entry points, use all nodes (degenerate case)
    if not entry_points:
        entry_points = list(nodes.keys())

    # BFS from entry points to find all reachable nodes
    reachable: set[str] = set()
    queue = list(entry_points)

    while queue:
        current = queue.pop(0)
        if current in reachable:
            continue
        reachable.add(current)

        for neighbor in graph.get(current, []):
            if neighbor not in reachable:
                queue.append(neighbor)

    return entry_points, reachable


__all__ = [
    # Public API (no underscore)
    "parse_connection",
    "is_exec_port",
    "is_exec_input_port",
    "has_circular_dependency",
    "find_entry_points_and_reachable",
]
