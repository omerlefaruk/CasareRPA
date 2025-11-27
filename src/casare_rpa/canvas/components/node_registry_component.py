"""
Node registry management component.

This component handles node type registration and discovery:
- Node type registration with graph
- Node factory integration
- Visual node mapping
"""

from typing import TYPE_CHECKING
from loguru import logger

from .base_component import BaseComponent
from ..graph.node_registry import get_node_registry, get_casare_node_mapping

if TYPE_CHECKING:
    from ..main_window import MainWindow


class NodeRegistryComponent(BaseComponent):
    """
    Manages node type registration.

    Responsibilities:
    - Node type registration
    - Node factory management
    - Visual node mapping
    - Node discovery
    """

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)

    def _do_initialize(self) -> None:
        """Initialize the node registry component."""
        # Register nodes with the graph
        node_registry = get_node_registry()
        node_registry.register_all_nodes(self.node_graph.graph)
        logger.info("Registered all node types with graph")

        # Pre-build node mapping to avoid delay on first node creation
        get_casare_node_mapping()
        logger.info("Pre-built node mapping cache")

        logger.info("NodeRegistryComponent initialized")

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.debug("NodeRegistryComponent cleaned up")
