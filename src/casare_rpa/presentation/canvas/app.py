"""
Main application class with qasync integration (Refactored).

This module provides the CasareRPAApp class which integrates
PySide6 with asyncio using qasync for async workflow execution.

Reduced from 3,112 lines to ~400 lines by extracting components.
"""

import sys
import asyncio

# Apply QFont fix FIRST - before any Qt widget imports that might create fonts
from PySide6.QtGui import QFont

_original_setPointSize = QFont.setPointSize


def _safe_setPointSize(self, size: int) -> None:
    """Guard against invalid point sizes (-1, 0)."""
    if size <= 0:
        size = 9
    _original_setPointSize(self, size)


QFont.setPointSize = _safe_setPointSize

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop
from loguru import logger

from casare_rpa.config import setup_logging, APP_NAME
from casare_rpa.nodes.file.file_security import (
    validate_path_security,
    PathSecurityError,
)
from casare_rpa.presentation.canvas.main_window import MainWindow
from casare_rpa.presentation.canvas.graph.node_graph_widget import NodeGraphWidget
from casare_rpa.presentation.canvas.controllers import (
    WorkflowController,
    ExecutionController,
    NodeController,
    SelectorController,
    PreferencesController,
    AutosaveController,
)
from casare_rpa.utils.playwright_setup import ensure_playwright_ready


class CasareRPAApp:
    """
    Main application class integrating Qt with asyncio (Refactored).

    Uses qasync to bridge PySide6's event loop with Python's asyncio,
    enabling async workflows with Playwright to run within the Qt application.

    Responsibilities:
    - Qt application initialization
    - Component lifecycle management with explicit dependency ordering
    - Event loop integration
    - Signal routing

    Business logic delegated to controllers:
    - WorkflowController: New/Open/Save/Template operations
    - ExecutionController: Workflow execution and debugging
    - NodeController: Node type registration (no dependencies)
    - SelectorController: Element selector integration
    - PreferencesController: Settings management
    - AutosaveController: Automatic saving

    Note: Triggers are now visual nodes on the canvas (not a background system).

    Component Initialization Order:
    1. NodeRegistryComponent - Must be first (registers all node types)
    2. All other components - Depend on node registry being initialized
    """

    def __init__(self) -> None:
        """Initialize the application."""
        # Setup logging
        setup_logging()

        # Setup Qt application
        self._setup_qt_application()

        # Check for Playwright browsers
        ensure_playwright_ready(show_gui=True, parent=None)

        # Create main window and node graph
        self._create_ui()

        # Initialize components in dependency order
        self._initialize_components()

        # Connect component signals
        self._connect_components()

        # Connect UI signals
        self._connect_ui_signals()

    def _setup_qt_application(self) -> None:
        """Setup Qt application and event loop."""
        # Enable high-DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # Create Qt application
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)

        # Create qasync event loop
        self._loop = QEventLoop(self._app)
        asyncio.set_event_loop(self._loop)

    def _create_ui(self) -> None:
        """Create main window and central widget."""
        # Create main window
        self._main_window = MainWindow()

        # Create node graph widget
        self._node_graph = NodeGraphWidget()

        # Set node graph as central widget
        self._main_window.set_central_widget(self._node_graph)

        # Create workflow serializer and deserializer
        from .serialization.workflow_serializer import WorkflowSerializer
        from .serialization.workflow_deserializer import WorkflowDeserializer
        from .execution.canvas_workflow_runner import CanvasWorkflowRunner

        self._serializer = WorkflowSerializer(
            self._node_graph.graph,  # NodeGraphQt NodeGraph instance
            self._main_window,
        )

        self._deserializer = WorkflowDeserializer(
            self._node_graph.graph,
            self._main_window,
        )

        # Set as data provider for validation
        self._main_window.set_workflow_data_provider(self._serializer.serialize)

        # Create workflow runner
        from casare_rpa.domain.events import get_event_bus

        self._workflow_runner = CanvasWorkflowRunner(
            self._serializer, get_event_bus(), self._main_window
        )

        logger.debug("Workflow serializer and runner initialized")

    def _initialize_components(self) -> None:
        """
        Initialize all application controllers in dependency order.

        Initialization Order (Critical):
        1. NodeController - MUST be first
           - Registers all node types with NodeGraphQt
           - Other controllers may need registered nodes during initialization

        2. All other controllers - Can be initialized in any order
           - They all depend on node registry being ready
           - No cross-dependencies between these controllers

        Raises:
            RuntimeError: If controller initialization fails
        """
        # Phase 1: Node registry (foundation - no dependencies)
        self._node_controller = NodeController(self._main_window)
        self._node_controller.initialize()
        logger.debug("Node registry initialized - all node types registered")

        # Phase 2: All other controllers (depend on node registry)
        logger.debug("Phase 2: Initializing application controllers...")

        # Workflow - handles file operations and drag-drop
        self._workflow_controller = WorkflowController(self._main_window)

        # Execution - handles workflow running
        self._execution_controller = ExecutionController(self._main_window)

        # Selector - handles element selection
        self._selector_controller = SelectorController(self._main_window)

        # Preferences - handles settings
        self._preferences_controller = PreferencesController(self._main_window)

        # Autosave - handles automatic saving
        self._autosave_controller = AutosaveController(self._main_window)

        # Note: Triggers are now visual nodes on the canvas

        # Initialize all phase 2 controllers
        phase_2_controllers = [
            self._workflow_controller,
            self._execution_controller,
            self._selector_controller,
            self._preferences_controller,
            self._autosave_controller,
        ]

        for controller in phase_2_controllers:
            try:
                controller.initialize()
                logger.debug(f"{controller.__class__.__name__} initialized")
            except Exception as e:
                error_msg = f"Failed to initialize {controller.__class__.__name__}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

        # Configure execution controller with workflow runner AFTER initialization
        self._execution_controller.set_workflow_runner(self._workflow_runner)

        # Inject configured controllers into MainWindow
        # This ensures MainWindow uses the same instances that were configured above
        self._main_window.set_controllers(
            workflow_controller=self._workflow_controller,
            execution_controller=self._execution_controller,
            node_controller=self._node_controller,
            selector_controller=self._selector_controller,
        )

    def _connect_components(self) -> None:
        """Connect controller signals for inter-controller communication."""
        # Controllers are already connected to main_window signals and EventBus internally
        # Additional cross-component connections can be added here if needed

        # Connect workflow save/load signals to actual file operations
        self._workflow_controller.workflow_saved.connect(self._on_workflow_save)
        self._workflow_controller.workflow_loaded.connect(self._on_workflow_load)
        self._workflow_controller.workflow_created.connect(self._on_workflow_new)

        # Connect main_window workflow_open signal (emitted from recent files, etc.)
        self._main_window.workflow_open.connect(self._on_workflow_load)

        # Connect project controller scenario_opened signal to load workflow
        project_controller = self._main_window.get_project_controller()
        if project_controller:
            project_controller.scenario_opened.connect(self._on_scenario_opened)

        # Connect save as scenario signal
        self._main_window.save_as_scenario_requested.connect(self._on_save_as_scenario)

        logger.debug("Component signals connected")

    def _connect_ui_signals(self) -> None:
        """Connect UI-level signals."""
        graph = self._node_graph.graph
        undo_stack = graph.undo_stack()

        # Edit operations - connect to NodeGraphQt undo stack
        self._main_window.action_undo.setEnabled(True)
        self._main_window.action_redo.setEnabled(True)
        self._main_window.action_undo.triggered.connect(undo_stack.undo)
        self._main_window.action_redo.triggered.connect(undo_stack.redo)

        # Connect undo stack signals to update action states
        undo_stack.canUndoChanged.connect(self._main_window.action_undo.setEnabled)
        undo_stack.canRedoChanged.connect(self._main_window.action_redo.setEnabled)

        # Track modification state using cleanChanged signal
        # cleanChanged(False) = stack is dirty (has unsaved changes)
        # cleanChanged(True) = stack is clean (at saved state)
        undo_stack.cleanChanged.connect(
            lambda is_clean: self._main_window.set_modified(not is_clean)
        )

        # Store reference to mark clean after save
        self._undo_stack = undo_stack

        # Other edit operations
        self._main_window.action_delete.triggered.connect(self._on_delete_selected)
        self._main_window.action_cut.triggered.connect(graph.cut_nodes)
        self._main_window.action_copy.triggered.connect(graph.copy_nodes)
        self._main_window.action_paste.triggered.connect(self._on_paste_nodes)
        self._main_window.action_duplicate.triggered.connect(self._on_duplicate_nodes)
        self._main_window.action_select_all.triggered.connect(graph.select_all)

        logger.debug("UI signals connected")

    def _get_all_controllers(self) -> list:
        """
        Get all initialized controllers.

        Returns:
            List of all controller instances
        """
        return [
            self._node_controller,
            self._workflow_controller,
            self._execution_controller,
            self._selector_controller,
            self._preferences_controller,
            self._autosave_controller,
        ]

    def _on_delete_selected(self) -> None:
        """Delete selected nodes and frames."""
        graph = self._node_graph.graph

        # Delete selected nodes first
        graph.delete_nodes(graph.selected_nodes())

        # Delete selected frames
        from .graph.node_frame import NodeFrame

        scene = graph.viewer().scene()
        for item in scene.selectedItems():
            if isinstance(item, NodeFrame):
                scene.removeItem(item)

    def _on_paste_nodes(self) -> None:
        """Paste nodes and regenerate IDs to avoid duplicates."""
        graph = self._node_graph.graph
        graph.paste_nodes()

        # Regenerate IDs for all pasted nodes (selected after paste)
        pasted_nodes = graph.selected_nodes()
        if pasted_nodes:
            self._regenerate_node_ids(pasted_nodes)

    def _on_duplicate_nodes(self) -> None:
        """Duplicate the selected nodes at mouse cursor position."""
        graph = self._node_graph.graph
        viewer = graph.viewer()

        # Check if there are selected nodes
        if not graph.selected_nodes():
            return

        # Get mouse cursor position in scene coordinates
        cursor_pos = viewer.cursor().pos()
        scene_pos = viewer.mapToScene(viewer.mapFromGlobal(cursor_pos))

        # Copy and paste
        graph.copy_nodes()
        graph.paste_nodes()

        # Get the newly pasted nodes
        pasted_nodes = graph.selected_nodes()
        if not pasted_nodes:
            return

        # CRITICAL: Regenerate IDs for pasted nodes to avoid duplicates
        # NodeGraphQt's add_node (used by paste) doesn't emit node_created signal,
        # so the paste hook in node_graph_widget.py doesn't trigger
        self._regenerate_node_ids(pasted_nodes)

        # Calculate bounding box center of pasted nodes
        min_x = min(node.pos()[0] for node in pasted_nodes)
        min_y = min(node.pos()[1] for node in pasted_nodes)
        max_x = max(
            node.pos()[0] + node.view.boundingRect().width() for node in pasted_nodes
        )
        max_y = max(
            node.pos()[1] + node.view.boundingRect().height() for node in pasted_nodes
        )
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Calculate offset to center nodes at cursor position
        offset_x = scene_pos.x() - center_x
        offset_y = scene_pos.y() - center_y

        # Move pasted nodes to cursor position (centered)
        for node in pasted_nodes:
            current_pos = node.pos()
            node.set_pos(current_pos[0] + offset_x, current_pos[1] + offset_y)

    def _regenerate_node_ids(self, nodes: list) -> None:
        """
        Regenerate unique IDs for pasted/duplicated nodes.

        NodeGraphQt's paste uses add_node which doesn't emit node_created signal,
        so this method must be called explicitly after paste operations.

        Args:
            nodes: List of pasted nodes that need new IDs
        """
        from casare_rpa.utils.id_generator import generate_node_id

        for node in nodes:
            # Skip nodes without casare_node (visual-only like comments)
            if not hasattr(node, "get_casare_node"):
                continue

            casare_node = node.get_casare_node()
            if not casare_node:
                # Try to create one if missing
                if hasattr(node, "_auto_create_casare_node"):
                    node._auto_create_casare_node()
                    casare_node = node.get_casare_node()
                if not casare_node:
                    continue

            # Generate new unique ID
            node_type = (
                getattr(casare_node, "node_type", None) or type(casare_node).__name__
            )
            old_id = casare_node.node_id
            new_id = generate_node_id(node_type)

            # Update both casare_node and visual property
            casare_node.node_id = new_id
            node.set_property("node_id", new_id)

            logger.debug(f"Regenerated node ID: {old_id} -> {new_id}")

    def _on_debug_mode_toggled(self, enabled: bool) -> None:
        """Handle debug mode toggle."""
        logger.info(f"Debug mode {'enabled' if enabled else 'disabled'}")

    def _on_step_mode_toggled(self, enabled: bool) -> None:
        """Handle step mode toggle."""
        logger.info(f"Step mode {'enabled' if enabled else 'disabled'}")

    def _on_debug_step(self) -> None:
        """Handle debug step request."""
        # Delegate to execution controller
        if hasattr(self._execution_controller, "_workflow_runner"):
            runner = self._execution_controller._workflow_runner
            if runner and runner.debug_mode:
                runner.step()

    def _on_debug_continue(self) -> None:
        """Handle debug continue request."""
        # Delegate to execution controller
        if hasattr(self._execution_controller, "_workflow_runner"):
            runner = self._execution_controller._workflow_runner
            if runner and runner.debug_mode:
                runner.continue_execution()

    # =========================================================================
    # WORKFLOW SAVE/LOAD HANDLERS
    # =========================================================================

    def _on_workflow_save(self, file_path: str) -> None:
        """
        Handle workflow save - serialize graph and write to file.

        Args:
            file_path: Path to save workflow to
        """
        import orjson
        from pathlib import Path
        from PySide6.QtWidgets import QMessageBox

        try:
            logger.info(f"Saving workflow to: {file_path}")

            # SECURITY: Validate path before writing to prevent saving to
            # system directories or unauthorized locations
            try:
                validated_path = validate_path_security(
                    file_path, operation="save_workflow"
                )
            except PathSecurityError as e:
                logger.error(f"Security violation saving workflow: {e}")
                QMessageBox.critical(
                    self._main_window,
                    "Save Error",
                    f"Cannot save to this location:\n{e}",
                )
                return

            # Serialize the graph
            workflow_data = self._serializer.serialize()

            # Write to file
            path = Path(validated_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "wb") as f:
                # Use orjson for fast JSON writing with pretty formatting
                f.write(orjson.dumps(workflow_data, option=orjson.OPT_INDENT_2))

            logger.info(f"Workflow saved successfully: {path.name}")
            self._main_window.show_status(f"Saved: {path.name}", 3000)

            # Mark undo stack as clean (at saved state)
            if hasattr(self, "_undo_stack") and self._undo_stack:
                self._undo_stack.setClean()

        except Exception as e:
            logger.exception(f"Failed to save workflow: {e}")
            QMessageBox.critical(
                self._main_window,
                "Save Error",
                f"Failed to save workflow:\n{e}",
            )

    def _on_workflow_load(self, file_path: str) -> None:
        """
        Handle workflow load - read file and deserialize into graph.

        Args:
            file_path: Path to workflow file
        """
        from pathlib import Path

        try:
            logger.info(f"Loading workflow from: {file_path}")

            # Load using deserializer
            success = self._deserializer.load_from_file(file_path)

            if success:
                logger.info("Workflow loaded successfully")
                self._main_window.show_status(f"Loaded: {Path(file_path).name}", 3000)
                # Mark undo stack as clean after load
                if hasattr(self, "_undo_stack") and self._undo_stack:
                    self._undo_stack.setClean()
            else:
                logger.error("Failed to load workflow")
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self._main_window,
                    "Load Error",
                    f"Failed to load workflow from:\n{file_path}",
                )

        except Exception as e:
            logger.exception(f"Failed to load workflow: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self._main_window,
                "Load Error",
                f"Failed to load workflow:\n{e}",
            )

    def _on_workflow_new(self) -> None:
        """Handle new workflow - clear the graph."""
        try:
            logger.info("Creating new workflow")
            self._node_graph.graph.clear_session()
            # Mark undo stack as clean for new workflow
            if hasattr(self, "_undo_stack") and self._undo_stack:
                self._undo_stack.setClean()
            logger.info("Graph cleared for new workflow")
        except Exception as e:
            logger.exception(f"Failed to clear graph: {e}")

    def _on_scenario_opened(self, project_path: str, scenario_path: str) -> None:
        """
        Handle scenario open - read scenario file and load embedded workflow.

        Args:
            project_path: Path to project folder
            scenario_path: Path to scenario JSON file
        """
        import orjson
        from pathlib import Path
        from PySide6.QtWidgets import QMessageBox

        try:
            logger.info(f"Loading scenario workflow from: {scenario_path}")

            path = Path(scenario_path)
            if not path.exists():
                logger.error(f"Scenario file not found: {scenario_path}")
                QMessageBox.warning(
                    self._main_window,
                    "Load Error",
                    f"Scenario file not found:\n{scenario_path}",
                )
                return

            # Read scenario JSON
            with open(path, "rb") as f:
                scenario_data = orjson.loads(f.read())

            # Extract workflow - handle both scenario format and direct workflow format
            # Scenario format: {"id": "...", "workflow": {...nodes, connections...}}
            # Direct workflow format: {"nodes": {...}, "connections": [...]}
            if "workflow" in scenario_data and isinstance(
                scenario_data["workflow"], dict
            ):
                # Scenario format with embedded workflow
                workflow = scenario_data["workflow"]
            elif "nodes" in scenario_data:
                # Direct workflow format - use the entire file as workflow
                workflow = scenario_data
            else:
                logger.warning(f"Scenario has no workflow data: {scenario_path}")
                QMessageBox.warning(
                    self._main_window,
                    "Load Warning",
                    "Scenario has no workflow data to display.",
                )
                return

            # Deserialize workflow onto canvas
            success = self._deserializer.deserialize(workflow)

            if success:
                # Get name from scenario format or metadata format
                scenario_name = (
                    scenario_data.get("name")
                    or scenario_data.get("metadata", {}).get("name")
                    or path.stem
                )
                logger.info(f"Scenario workflow loaded: {scenario_name}")
                self._main_window.show_status(f"Loaded scenario: {scenario_name}", 3000)
                # Mark undo stack as clean after load
                if hasattr(self, "_undo_stack") and self._undo_stack:
                    self._undo_stack.setClean()
            else:
                logger.error("Failed to load scenario workflow")
                QMessageBox.warning(
                    self._main_window,
                    "Load Error",
                    f"Failed to load scenario workflow from:\n{scenario_path}",
                )

        except orjson.JSONDecodeError as e:
            logger.error(f"Invalid JSON in scenario file: {e}")
            QMessageBox.critical(
                self._main_window,
                "Load Error",
                f"Invalid JSON in scenario file:\n{e}",
            )
        except Exception as e:
            logger.exception(f"Failed to load scenario: {e}")
            QMessageBox.critical(
                self._main_window,
                "Load Error",
                f"Failed to load scenario:\n{e}",
            )

    def _on_save_as_scenario(self) -> None:
        """
        Handle save as scenario - show dialog and save workflow in scenario format.

        Scenario format wraps the workflow data in a scenario structure with
        id, name, project_id, and the workflow itself.
        """
        import orjson
        import uuid
        from pathlib import Path
        from datetime import datetime
        from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

        try:
            # Get scenario name from user
            name, ok = QInputDialog.getText(
                self._main_window,
                "Save as Scenario",
                "Scenario name:",
                text="New Scenario",
            )
            if not ok or not name.strip():
                return

            name = name.strip()

            # Get project controller to find current project
            project_controller = self._main_window.get_project_controller()
            current_project = (
                project_controller.current_project if project_controller else None
            )

            # Determine default save directory
            if current_project and current_project.path:
                scenarios_dir = Path(current_project.path) / "scenarios"
                scenarios_dir.mkdir(exist_ok=True)
                default_path = scenarios_dir / f"{name}.json"
            else:
                default_path = Path.home() / f"{name}.json"

            # Show save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self._main_window,
                "Save as Scenario",
                str(default_path),
                "Scenario Files (*.json);;All Files (*)",
            )

            if not file_path:
                return

            logger.info(f"Saving scenario to: {file_path}")

            # Serialize current workflow
            workflow_data = self._serializer.serialize()

            # Create scenario structure
            scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
            project_id = current_project.id if current_project else ""
            now = datetime.now()

            scenario_data = {
                "$schema_version": "1.0.0",
                "id": scenario_id,
                "name": name,
                "project_id": project_id,
                "description": "",
                "created_at": now.isoformat(),
                "modified_at": now.isoformat(),
                "tags": [],
                "workflow": workflow_data,
                "variable_values": {},
                "credential_bindings": {},
                "execution_settings": {
                    "timeout": 120,
                    "retry_count": 0,
                    "stop_on_error": True,
                },
                "triggers": [],
            }

            # Write to file
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "wb") as f:
                f.write(orjson.dumps(scenario_data, option=orjson.OPT_INDENT_2))

            logger.info(f"Scenario saved successfully: {name}")
            self._main_window.show_status(f"Saved scenario: {name}", 3000)

            # Mark undo stack as clean
            if hasattr(self, "_undo_stack") and self._undo_stack:
                self._undo_stack.setClean()

        except Exception as e:
            logger.exception(f"Failed to save scenario: {e}")
            QMessageBox.critical(
                self._main_window,
                "Save Error",
                f"Failed to save scenario:\n{e}",
            )

    # Public API for getting controllers
    def get_workflow_controller(self) -> WorkflowController:
        """Get the workflow controller."""
        return self._workflow_controller

    def get_execution_controller(self) -> ExecutionController:
        """Get the execution controller."""
        return self._execution_controller

    def get_node_controller(self) -> NodeController:
        """Get the node controller."""
        return self._node_controller

    def get_selector_controller(self) -> SelectorController:
        """Get the selector controller."""
        return self._selector_controller

    def get_preferences_controller(self) -> PreferencesController:
        """Get the preferences controller."""
        return self._preferences_controller

    def get_autosave_controller(self) -> AutosaveController:
        """Get the autosave controller."""
        return self._autosave_controller

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Application exit code
        """
        self._main_window.show()

        with self._loop:
            exit_code = self._loop.run_forever()

        logger.info(f"Application exited with code {exit_code}")
        return exit_code if isinstance(exit_code, int) else 0

    async def run_async(self) -> int:
        """
        Run the application asynchronously.

        This method allows the application to be started from
        an async context if needed.

        Returns:
            Application exit code
        """
        logger.info("Starting application (async)")
        self._main_window.show()
        return 0

    def cleanup(self) -> None:
        """Cleanup all controllers."""
        logger.info("Cleaning up application")
        for controller in self._get_all_controllers():
            try:
                controller.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {controller.__class__.__name__}: {e}")


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Application exit code
    """
    app = CasareRPAApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
