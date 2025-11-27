"""
Drag-and-drop management component.

This component handles drag-and-drop functionality for importing workflows:
- File drag-drop support
- JSON data drag-drop
- Workflow import at drop position
"""

from typing import TYPE_CHECKING
from pathlib import Path
from loguru import logger

from .base_component import BaseComponent

if TYPE_CHECKING:
    from ..main_window import MainWindow


class DragDropComponent(BaseComponent):
    """
    Manages drag-and-drop functionality.

    Responsibilities:
    - Setup drag-drop handlers
    - Import workflows at drop position
    - Handle file and JSON data drops
    """

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)

    def _do_initialize(self) -> None:
        """Initialize the drag-drop component."""
        self._setup_drag_drop_import()
        logger.info("DragDropComponent initialized")

    def _setup_drag_drop_import(self) -> None:
        """
        Setup drag-and-drop support for importing workflow JSON files.

        Allows users to drag .json workflow files directly onto the canvas
        to import nodes at the drop position.
        """
        from ..workflow.workflow_import import import_workflow_data
        from ..graph.node_factory import get_node_factory

        def on_import_file(file_path: str, position: tuple) -> None:
            """Handle file drop."""
            try:
                import orjson

                logger.info(f"Importing dropped file: {file_path}")

                # Load workflow data
                data = orjson.loads(Path(file_path).read_bytes())

                # Prepare for import (remap IDs and position at drop location)
                prepared_data, id_mapping = import_workflow_data(
                    self.node_graph.graph,
                    get_node_factory(),
                    data,
                    drop_position=position,
                )

                # Create nodes from prepared data
                self._load_workflow_merge(prepared_data)

                self._main_window.set_modified(True)
                self._main_window.show_status(
                    f"Imported {len(prepared_data.get('nodes', {}))} nodes from {Path(file_path).name}",
                    5000,
                )
            except Exception as e:
                logger.exception(f"Failed to import dropped file: {e}")
                self._main_window.show_status(f"Error importing file: {str(e)}", 5000)

        def on_import_data(data: dict, position: tuple) -> None:
            """Handle JSON data drop."""
            try:
                logger.info("Importing dropped JSON data")

                # Prepare for import (remap IDs and position at drop location)
                prepared_data, id_mapping = import_workflow_data(
                    self.node_graph.graph,
                    get_node_factory(),
                    data,
                    drop_position=position,
                )

                # Create nodes from prepared data
                self._load_workflow_merge(prepared_data)

                self._main_window.set_modified(True)
                self._main_window.show_status(
                    f"Imported {len(prepared_data.get('nodes', {}))} nodes", 5000
                )
            except Exception as e:
                logger.exception(f"Failed to import dropped JSON: {e}")
                self._main_window.show_status(f"Error importing JSON: {str(e)}", 5000)

        # Set callbacks and enable drag-drop
        self.node_graph.set_import_file_callback(on_import_file)
        self.node_graph.set_import_callback(on_import_data)
        self.node_graph.setup_drag_drop()

    def _load_workflow_merge(self, workflow_data: dict) -> None:
        """
        Load workflow data into graph without clearing existing nodes (merge mode).

        Args:
            workflow_data: Prepared workflow data with remapped IDs
        """
        from ..graph.node_registry import get_node_factory

        graph = self.node_graph.graph
        factory = get_node_factory()

        # Create nodes
        for node_id, node_data in workflow_data.get("nodes", {}).items():
            try:
                visual_node = self._create_visual_node_from_data(
                    graph, node_data, factory
                )
                if visual_node:
                    logger.debug(f"Created node {node_id} during import")
            except Exception as e:
                logger.error(f"Failed to create node {node_id}: {e}")

        # Create connections (implementation would continue...)
        logger.info(f"Merged {len(workflow_data.get('nodes', {}))} nodes into graph")

    def _create_visual_node_from_data(self, graph, node_data: dict, factory):
        """
        Create a visual node from node data.

        Args:
            graph: NodeGraph instance
            node_data: Node data dictionary
            factory: Node factory instance

        Returns:
            Created visual node or None
        """
        from ..graph.node_registry import (
            get_identifier_for_type,
            get_casare_class_for_type,
        )

        node_type = node_data.get("node_type")
        node_id = node_data.get("node_id")

        # Get identifier for creating visual node
        identifier = get_identifier_for_type(node_type)
        if not identifier:
            logger.warning(f"Unknown node type '{node_type}' for node {node_id}")
            return None

        # Create visual node
        visual_node = graph.create_node(identifier)
        if not visual_node:
            logger.error(f"Failed to create visual node for {node_id}")
            return None

        # Create CasareRPA node
        casare_class = get_casare_class_for_type(node_type)
        if casare_class:
            try:
                casare_node = casare_class(node_id, node_data.get("config", {}))
                visual_node.set_casare_node(casare_node)
            except Exception as e:
                logger.error(f"Failed to create CasareRPA node for {node_id}: {e}")

        # Restore widget values
        config = node_data.get("config", {})
        widgets = visual_node.widgets()
        for widget_name, widget in widgets.items():
            if widget_name in config:
                try:
                    widget.set_value(config[widget_name])
                except Exception as e:
                    logger.warning(
                        f"Failed to restore widget {node_id}.{widget_name}: {e}"
                    )

        # Set position
        pos = node_data.get("position", {})
        if "x" in pos and "y" in pos:
            visual_node.set_pos(pos["x"], pos["y"])

        # Set name
        name = node_data.get("name")
        if name:
            visual_node.set_name(name)

        return visual_node

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.debug("DragDropComponent cleaned up")
