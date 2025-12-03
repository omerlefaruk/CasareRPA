"""
Composite Node Creator for CasareRPA Canvas.

Handles creation of composite nodes that spawn multiple paired nodes:
- For Loop (Start + End)
- While Loop (Start + End)
- Try/Catch/Finally (3 nodes)

Follows Single Responsibility Principle - handles composite node creation only.
"""

from typing import Optional, Tuple, TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, QTimer

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class CompositeNodeCreator(QObject):
    """
    Creates composite nodes that consist of multiple paired nodes.

    Handles the creation of:
    - For Loop: Creates ForLoopStart + ForLoopEnd with automatic pairing
    - While Loop: Creates WhileLoopStart + WhileLoopEnd with automatic pairing
    - Try/Catch/Finally: Creates 3 nodes with automatic pairing

    Usage:
        creator = CompositeNodeCreator(graph)
        creator.handle_composite_node(composite_marker_node)
    """

    # Default spacing between paired nodes
    HORIZONTAL_SPACING = 600
    TRY_CATCH_SPACING = 450

    def __init__(self, graph: "NodeGraph", parent: Optional[QObject] = None) -> None:
        """
        Initialize composite node creator.

        Args:
            graph: The NodeGraphQt NodeGraph instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph = graph

    @property
    def graph(self) -> "NodeGraph":
        """Get the underlying graph."""
        return self._graph

    def handle_composite_node(self, composite_node) -> None:
        """
        Handle creation of composite nodes (e.g., For Loop creates Start + End).

        Replaces the marker composite node with the actual nodes it represents,
        connects them together, and sets up pairing.

        Args:
            composite_node: The composite marker node that was created
        """
        # Get position of composite node
        pos = composite_node.pos()
        x, y = pos[0], pos[1]

        # Get the node name for logging
        node_name = (
            composite_node.NODE_NAME
            if hasattr(composite_node, "NODE_NAME")
            else "Composite"
        )

        # Schedule deletion and replacement (must be done after current event)
        def replace_composite():
            try:
                logger.debug(
                    f"Replacing composite marker '{node_name}' with actual nodes at ({x}, {y})"
                )
                # Delete the marker composite node
                self._graph.delete_node(composite_node)

                # Handle specific composite types
                if node_name == "For Loop":
                    self.create_for_loop_pair(x, y)
                elif node_name == "While Loop":
                    self.create_while_loop_pair(x, y)
                elif node_name == "Try/Catch/Finally":
                    self.create_try_catch_finally(x, y)
                else:
                    logger.warning(f"Unknown composite node type: {node_name}")

            except Exception as e:
                logger.error(
                    f"Failed to handle composite node creation: {e}", exc_info=True
                )

        # Use QTimer to defer the replacement
        QTimer.singleShot(0, replace_composite)

    def create_for_loop_pair(self, x: float, y: float) -> Optional[Tuple]:
        """
        Create a For Loop Start + End pair at the given position.

        Layout: Side-by-side with large spacing for workflow nodes
            ForLoopStart (x, y) -------- ForLoopEnd (x + 600, y)

        Args:
            x: X position for the start node
            y: Y position for the start node

        Returns:
            Tuple of (start_node, end_node) or None if creation failed
        """
        try:
            # Create For Loop Start node
            start_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualForLoopStartNode", pos=[x, y]
            )

            # Create For Loop End node (side-by-side with large spacing)
            end_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualForLoopEndNode",
                pos=[x + self.HORIZONTAL_SPACING, y],
            )

            if start_node and end_node:
                self._setup_loop_pairing(start_node, end_node, "For Loop")
                return (start_node, end_node)

            return None

        except Exception as e:
            logger.error(f"Failed to create For Loop pair: {e}")
            return None

    def create_while_loop_pair(self, x: float, y: float) -> Optional[Tuple]:
        """
        Create a While Loop Start + End pair at the given position.

        Layout: Side-by-side with large spacing for workflow nodes
            WhileLoopStart (x, y) -------- WhileLoopEnd (x + 600, y)

        Args:
            x: X position for the start node
            y: Y position for the start node

        Returns:
            Tuple of (start_node, end_node) or None if creation failed
        """
        try:
            # Create While Loop Start node
            start_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualWhileLoopStartNode", pos=[x, y]
            )

            # Create While Loop End node (side-by-side with large spacing)
            end_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualWhileLoopEndNode",
                pos=[x + self.HORIZONTAL_SPACING, y],
            )

            if start_node and end_node:
                self._setup_loop_pairing(start_node, end_node, "While Loop")
                return (start_node, end_node)

            return None

        except Exception as e:
            logger.error(f"Failed to create While Loop pair: {e}")
            return None

    def _setup_loop_pairing(self, start_node, end_node, loop_type: str) -> None:
        """
        Set up pairing between loop start and end nodes.

        Args:
            start_node: The loop start node
            end_node: The loop end node
            loop_type: "For Loop" or "While Loop" for logging
        """
        # Get node IDs
        start_id = start_node.get_property("node_id")
        end_id = end_node.get_property("node_id")

        # Set up pairing on visual nodes
        start_node.paired_end_id = end_id
        end_node.paired_start_id = start_id

        # Set up pairing on CasareRPA nodes
        start_casare = (
            start_node.get_casare_node()
            if hasattr(start_node, "get_casare_node")
            else None
        )
        end_casare = (
            end_node.get_casare_node() if hasattr(end_node, "get_casare_node") else None
        )

        if end_casare and hasattr(end_casare, "set_paired_start"):
            end_casare.set_paired_start(start_id)

        # Connect Start.body -> End.exec_in
        start_body_port = start_node.get_output("body")
        end_exec_in_port = end_node.get_input("exec_in")

        if start_body_port and end_exec_in_port:
            start_body_port.connect_to(end_exec_in_port)
            logger.debug(f"Connected {loop_type} Start.body -> {loop_type} End.exec_in")

        logger.info(f"Created {loop_type} pair: Start={start_id}, End={end_id}")

    def create_try_catch_finally(self, x: float, y: float) -> Optional[Tuple]:
        """
        Create a Try/Catch/Finally block with three nodes side-by-side.

        Layout: Side-by-side with large spacing for workflow nodes
            Try (x, y) -------- Catch (x + 450, y) -------- Finally (x + 900, y)

        IDs are automatically paired - no user configuration needed.

        Args:
            x: X position for the Try node
            y: Y position for the Try node

        Returns:
            Tuple of (try_node, catch_node, finally_node) or None if creation failed
        """
        try:
            # Create Try node
            try_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualTryNode", pos=[x, y]
            )

            # Create Catch node (side-by-side with large spacing)
            catch_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualCatchNode",
                pos=[x + self.TRY_CATCH_SPACING, y],
            )

            # Create Finally node (side-by-side with large spacing)
            finally_node = self._graph.create_node(
                "casare_rpa.control_flow.VisualFinallyNode",
                pos=[x + self.TRY_CATCH_SPACING * 2, y],
            )

            if try_node and catch_node and finally_node:
                self._setup_try_catch_pairing(try_node, catch_node, finally_node)
                return (try_node, catch_node, finally_node)

            return None

        except Exception as e:
            logger.error(
                f"Failed to create Try/Catch/Finally block: {e}", exc_info=True
            )
            return None

    def _setup_try_catch_pairing(self, try_node, catch_node, finally_node) -> None:
        """
        Set up pairing between try/catch/finally nodes.

        Args:
            try_node: The try node
            catch_node: The catch node
            finally_node: The finally node
        """
        # Get node IDs
        try_id = try_node.get_property("node_id")
        catch_id = catch_node.get_property("node_id")
        finally_id = finally_node.get_property("node_id")

        # Set up automatic pairing on visual nodes
        try_node.paired_catch_id = catch_id
        try_node.paired_finally_id = finally_id
        catch_node.paired_try_id = try_id
        catch_node.paired_finally_id = finally_id
        finally_node.paired_try_id = try_id

        # Set up pairing on CasareRPA logic nodes
        try_casare = (
            try_node.get_casare_node() if hasattr(try_node, "get_casare_node") else None
        )
        catch_casare = (
            catch_node.get_casare_node()
            if hasattr(catch_node, "get_casare_node")
            else None
        )
        finally_casare = (
            finally_node.get_casare_node()
            if hasattr(finally_node, "get_casare_node")
            else None
        )

        if try_casare:
            try_casare.paired_catch_id = catch_id
            try_casare.paired_finally_id = finally_id

        if catch_casare and hasattr(catch_casare, "set_paired_try"):
            catch_casare.set_paired_try(try_id)
            catch_casare.paired_finally_id = finally_id

        if finally_casare and hasattr(finally_casare, "set_paired_try"):
            finally_casare.set_paired_try(try_id)

        # Connect Try.exec_out -> Catch.exec_in
        try_exec_out = try_node.get_output("exec_out")
        catch_exec_in = catch_node.get_input("exec_in")
        if try_exec_out and catch_exec_in:
            try_exec_out.connect_to(catch_exec_in)
            logger.debug("Connected Try.exec_out -> Catch.exec_in")

        # Connect Catch.catch_body -> Finally.exec_in
        catch_body_port = catch_node.get_output("catch_body")
        finally_exec_in = finally_node.get_input("exec_in")
        if catch_body_port and finally_exec_in:
            catch_body_port.connect_to(finally_exec_in)
            logger.debug("Connected Catch.catch_body -> Finally.exec_in")

        logger.info(
            f"Created Try/Catch/Finally block: Try={try_id}, "
            f"Catch={catch_id}, Finally={finally_id}"
        )
