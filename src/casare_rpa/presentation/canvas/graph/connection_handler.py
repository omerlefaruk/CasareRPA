"""
Connection handling module for NodeGraphWidget.

Extracts connection-related logic from NodeGraphWidget for better maintainability.
Handles:
- Connection validation and blocking invalid connections
- Pipe registration/unregistration with viewport culler
- Orphaned pipe cleanup
- Control flow frame propagation
- Auto-connection of new nodes
- SetVariable creation from output ports
"""

from typing import TYPE_CHECKING, Optional, Set

from PySide6.QtCore import Signal, QObject

from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph
    from casare_rpa.presentation.canvas.graph.viewport_culling import (
        ViewportCullingManager,
    )
    from casare_rpa.presentation.canvas.connections.connection_validator import (
        ConnectionValidator,
    )


class ConnectionHandler(QObject):
    """
    Handles connection-related operations for the node graph.

    Extracted from NodeGraphWidget to improve code organization and testability.
    """

    # Signal emitted when an invalid connection is blocked
    connection_blocked = Signal(str)

    def __init__(
        self,
        graph: "NodeGraph",
        culler: "ViewportCullingManager",
        validator: Optional["ConnectionValidator"] = None,
    ):
        """
        Initialize connection handler.

        Args:
            graph: The NodeGraph instance
            culler: The viewport culling manager
            validator: Optional connection validator for type checking
        """
        super().__init__()
        self._graph = graph
        self._culler = culler
        self._validator = validator

    def setup_validation(self) -> None:
        """Setup connection validation hooks."""
        if not self._validator:
            return

        try:
            if hasattr(self._graph, "port_connected"):
                self._graph.port_connected.connect(self._on_port_connected)
                logger.debug("Connection validation enabled")
        except Exception as e:
            logger.warning(f"Could not setup connection validation: {e}")

    def _on_port_connected(self, input_port, output_port) -> None:
        """
        Handle port connection event and validate connection types.

        Args:
            input_port: The input (target) port
            output_port: The output (source) port
        """
        if not self._validator:
            return

        try:
            source_node = output_port.node()
            target_node = input_port.node()

            if not hasattr(source_node, "get_port_type") or not hasattr(
                target_node, "get_port_type"
            ):
                return  # Can't validate

            validation = self._validator.validate_connection(
                source_node, output_port.name(), target_node, input_port.name()
            )

            if not validation.is_valid:
                logger.warning(f"Connection blocked: {validation.message}")

                try:
                    output_port.disconnect_from(
                        input_port, push_undo=False, emit_signal=False
                    )
                except Exception as e:
                    logger.error(f"Failed to disconnect invalid connection: {e}")

                self.connection_blocked.emit(validation.message)

        except Exception as e:
            logger.debug(f"Connection validation error: {e}")

    def on_pipe_created(self, input_port, output_port) -> None:
        """
        Register newly created pipe with culler and propagate control flow frames.

        Args:
            input_port: The input port
            output_port: The output port
        """
        try:
            source_node = None
            target_node = None

            if hasattr(output_port, "connected_pipes"):
                for pipe in output_port.connected_pipes():
                    if (
                        pipe
                        and hasattr(pipe, "input_port")
                        and pipe.input_port() == input_port
                    ):
                        source_node = output_port.node()
                        target_node = input_port.node()
                        if source_node and target_node:
                            pipe_id = f"{source_node.id}:{output_port.name()}>{target_node.id}:{input_port.name()}"
                            self._culler.register_pipe(
                                pipe_id, source_node.id, target_node.id, pipe
                            )
                        break

            # Propagate control flow frame
            if source_node and target_node:
                self._propagate_control_flow_frame(source_node, target_node)

        except Exception as e:
            logger.debug(f"Could not register pipe for culling: {e}")

    def on_pipe_deleted(self, input_port, output_port) -> None:
        """
        Unregister deleted pipe from culler.

        Args:
            input_port: The input port
            output_port: The output port
        """
        try:
            source_node = output_port.node() if output_port else None
            target_node = input_port.node() if input_port else None
            if source_node and target_node:
                pipe_id = f"{source_node.id}:{output_port.name()}>{target_node.id}:{input_port.name()}"
                self._culler.unregister_pipe(pipe_id)
        except Exception as e:
            logger.debug(f"Could not unregister pipe from culling: {e}")

    def _propagate_control_flow_frame(self, source_node, target_node) -> None:
        """
        Propagate control flow frame membership when nodes are connected.

        Args:
            source_node: The source node of the connection
            target_node: The target node of the connection
        """
        try:
            source_frame = getattr(source_node, "control_flow_frame", None)
            target_frame = getattr(target_node, "control_flow_frame", None)

            frame = source_frame or target_frame
            if not frame:
                return

            if not frame.scene():
                return

            if source_frame and not target_frame:
                frame.add_node(target_node)
                target_node.control_flow_frame = frame
                logger.debug(
                    f"Added {target_node.name()} to control flow frame '{frame.frame_title}'"
                )
            elif target_frame and not source_frame:
                frame.add_node(source_node)
                source_node.control_flow_frame = frame
                logger.debug(
                    f"Added {source_node.name()} to control flow frame '{frame.frame_title}'"
                )

            if hasattr(frame, "_check_node_bounds"):
                frame._check_node_bounds()

        except Exception as e:
            logger.debug(f"Could not propagate control flow frame: {e}")

    def cleanup_orphaned_pipes(self, deleted_node_ids: list) -> None:
        """
        Clean up orphaned pipes after node deletion.

        Args:
            deleted_node_ids: List of deleted node IDs
        """
        try:
            viewer = self._graph.viewer()
            if not viewer:
                return

            scene = viewer.scene()
            if not scene:
                return

            deleted_ids = set(deleted_node_ids)

            from NodeGraphQt.qgraphics.pipe import PipeItem

            orphaned_pipes = []
            for item in scene.items():
                if not isinstance(item, PipeItem):
                    continue

                if not hasattr(item, "input_port") or not hasattr(item, "output_port"):
                    continue

                is_orphaned = self._check_pipe_orphaned(item, deleted_ids)
                if is_orphaned:
                    orphaned_pipes.append(item)

            self._remove_orphaned_pipes(scene, orphaned_pipes)

            if orphaned_pipes:
                logger.debug(f"Cleaned up {len(orphaned_pipes)} orphaned pipe(s)")

        except Exception as e:
            logger.debug(f"Error during orphaned pipe cleanup: {e}")

    def _check_pipe_orphaned(self, pipe, deleted_ids: Set[str]) -> bool:
        """
        Check if a pipe is orphaned (either endpoint missing/invalid).

        Args:
            pipe: The pipe item to check
            deleted_ids: Set of deleted node IDs

        Returns:
            True if pipe is orphaned
        """
        input_port = pipe.input_port
        if input_port is None:
            return True
        elif hasattr(input_port, "node") and input_port.node:
            node = input_port.node
            if hasattr(node, "id") and node.id in deleted_ids:
                return True
            elif not node.scene():
                return True

        output_port = pipe.output_port
        if output_port is None:
            return True
        elif hasattr(output_port, "node") and output_port.node:
            node = output_port.node
            if hasattr(node, "id") and node.id in deleted_ids:
                return True
            elif not node.scene():
                return True

        return False

    def _remove_orphaned_pipes(self, scene, orphaned_pipes: list) -> None:
        """
        Remove orphaned pipes from the scene.

        Args:
            scene: The graphics scene
            orphaned_pipes: List of orphaned pipe items
        """
        for pipe in orphaned_pipes:
            try:
                if pipe.input_port and hasattr(pipe.input_port, "connected_pipes"):
                    try:
                        if pipe in pipe.input_port.connected_pipes:
                            pipe.input_port.remove_pipe(pipe)
                    except (ValueError, AttributeError):
                        pass

                if pipe.output_port and hasattr(pipe.output_port, "connected_pipes"):
                    try:
                        if pipe in pipe.output_port.connected_pipes:
                            pipe.output_port.remove_pipe(pipe)
                    except (ValueError, AttributeError):
                        pass

                if pipe.scene():
                    scene.removeItem(pipe)

                self._culler.unregister_pipe(id(pipe))

                logger.debug(f"Cleaned up orphaned pipe: {pipe}")
            except Exception as e:
                logger.debug(f"Error cleaning up orphaned pipe: {e}")

    def show_connection_search(
        self, source_port, scene_pos, node_created_handler
    ) -> None:
        """
        Show node context menu and setup auto-connect for created node.

        Args:
            source_port: The port that was dragged from
            scene_pos: Scene position where connection was released
            node_created_handler: Callback to handle auto-connection
        """
        context_menu = self._graph.get_context_menu("graph")
        if not context_menu or not context_menu.qmenu:
            logger.warning("Context menu not available")
            return

        context_menu.qmenu._initial_scene_pos = scene_pos

        handler_executed = [False]

        def on_node_created(node):
            if handler_executed[0]:
                return
            handler_executed[0] = True
            try:
                node_created_handler(node, source_port)
            except Exception as e:
                logger.error(f"Failed to auto-connect node: {e}")

        if hasattr(self._graph, "node_created"):
            self._graph.node_created.connect(on_node_created)

        viewer = self._graph.viewer()
        view_pos = viewer.mapFromScene(scene_pos)
        global_pos = viewer.mapToGlobal(view_pos)

        try:
            context_menu.qmenu.exec(global_pos)
        finally:
            try:
                self._graph.node_created.disconnect(on_node_created)
            except (RuntimeError, TypeError):
                pass
