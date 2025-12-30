"""
Connection management controller.

Handles all connection-related operations:
- Connection creation and deletion
- Connection validation
- Port compatibility checking
- Auto-connect mode
"""


from loguru import logger
from PySide6.QtCore import Signal

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

from ..interfaces import IMainWindow


class ConnectionController(BaseController):
    """
    Manages connections between nodes in the workflow graph.

    Single Responsibility: Connection lifecycle and validation.

    Signals:
        connection_created: Emitted when a connection is created (str: source_id, str: target_id)
        connection_deleted: Emitted when a connection is deleted (str: source_id, str: target_id)
        connection_validation_error: Emitted when connection validation fails (str: error_message)
        auto_connect_toggled: Emitted when auto-connect mode changes (bool: enabled)
    """

    # Signals
    connection_created = Signal(str, str)  # source_id, target_id
    connection_deleted = Signal(str, str)  # source_id, target_id
    connection_validation_error = Signal(str)  # error_message
    auto_connect_toggled = Signal(bool)  # enabled

    def __init__(self, main_window: "IMainWindow"):
        """Initialize connection controller."""
        super().__init__(main_window)
        self._auto_connect_enabled = False

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("ConnectionController cleanup")

    def create_connection(
        self,
        source_node_id: str,
        source_port: str,
        target_node_id: str,
        target_port: str,
    ) -> bool:
        """
        Create a connection between two nodes.

        Args:
            source_node_id: ID of source node
            source_port: Name of source port
            target_node_id: ID of target node
            target_port: Name of target port

        Returns:
            True if connection was created, False if validation failed
        """
        logger.debug(
            f"Creating connection: {source_node_id}.{source_port} -> {target_node_id}.{target_port}"
        )

        # Validate connection
        is_valid, error_message = self.validate_connection(
            source_node_id, source_port, target_node_id, target_port
        )

        if not is_valid:
            logger.warning(f"Connection validation failed: {error_message}")
            self.connection_validation_error.emit(error_message)
            return False

        # Connection creation is handled by NodeGraphQt
        # This controller just tracks the state and validates
        self.connection_created.emit(source_node_id, target_node_id)

        logger.info(f"Connection created: {source_node_id} -> {target_node_id}")
        return True

    def delete_connection(self, source_node_id: str, target_node_id: str) -> None:
        """
        Delete a connection between two nodes.

        Args:
            source_node_id: ID of source node
            target_node_id: ID of target node
        """
        logger.debug(f"Deleting connection: {source_node_id} -> {target_node_id}")

        # Connection deletion is handled by NodeGraphQt
        # This controller just tracks the state
        self.connection_deleted.emit(source_node_id, target_node_id)

        logger.info(f"Connection deleted: {source_node_id} -> {target_node_id}")

    def validate_connection(
        self,
        source_node_id: str,
        source_port: str,
        target_node_id: str,
        target_port: str,
    ) -> tuple[bool, str | None]:
        """
        Validate a connection before creation.

        Args:
            source_node_id: ID of source node
            source_port: Name of source port
            target_node_id: ID of target node
            target_port: Name of target port

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Prevent self-connections
        if source_node_id == target_node_id:
            return False, "Cannot connect a node to itself"

        # Additional validation logic would go here:
        # - Check port types compatibility
        # - Check for circular dependencies
        # - Check if connection already exists
        # - Validate data flow direction

        return True, None

    def toggle_auto_connect(self, enabled: bool) -> None:
        """
        Toggle auto-connect mode.

        Args:
            enabled: True to enable auto-connect, False to disable
        """
        logger.info(f"Auto-connect mode: {enabled}")

        self._auto_connect_enabled = enabled
        self.auto_connect_toggled.emit(enabled)

        # Update graph's auto-connection behavior
        graph = self._get_graph()
        if graph and hasattr(graph, "set_acyclic"):
            # Auto-connect typically works with acyclic graphs
            graph.set_acyclic(enabled)

    @property
    def auto_connect_enabled(self) -> bool:
        """Check if auto-connect mode is enabled."""
        return self._auto_connect_enabled

    def _get_graph(self):
        """
        Get the node graph from central widget.

        Returns:
            NodeGraph instance or None if not available
        """
        return self.main_window.get_graph()
