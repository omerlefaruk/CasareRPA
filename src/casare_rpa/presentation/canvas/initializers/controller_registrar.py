"""
Controller registration and wiring for MainWindow.

Extracts controller instantiation, initialization, and signal/slot
connections from MainWindow to improve separation of concerns.

Usage:
    registrar = ControllerRegistrar(main_window)
    registrar.register_all()

    # When app.py sets external controllers:
    registrar.set_external_controllers(
        workflow_controller,
        execution_controller,
        node_controller,
        selector_controller
    )
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Slot

if TYPE_CHECKING:
    from ..controllers import (
        ExecutionController,
        NodeController,
        SelectorController,
        WorkflowController,
    )
    from ..main_window import MainWindow


class ControllerRegistrar:
    """
    Handles controller registration and wiring for MainWindow.

    Responsibilities:
    - Instantiate MainWindow-specific controllers
    - Initialize controllers in correct order
    - Wire signal/slot connections between controllers and MainWindow
    - Manage external controller injection (from app.py)
    - Handle controller cleanup

    Controller Categories:
    1. MainWindow-specific: Created and owned by MainWindow
       - ConnectionController, PanelController, MenuController
       - EventBusController, ViewportController
       - UIStateController, ProjectController, RobotController

    2. External: Created by app.py and injected
       - WorkflowController, ExecutionController, NodeController
       - SelectorController
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the registrar.

        Args:
            main_window: The MainWindow instance to register controllers for
        """
        self._main_window = main_window
        self._controllers_initialized = False

    def register_all(self) -> None:
        """
        Register and initialize all MainWindow-specific controllers.

        Controllers are instantiated, then initialized in order.
        External controllers (workflow, execution, node) are set to None
        and must be injected later via set_external_controllers().
        """
        if self._controllers_initialized:
            logger.warning("Controllers already registered")
            return

        mw = self._main_window

        # Import controllers here to avoid circular imports
        from ..controllers import (
            ConnectionController,
            EventBusController,
            MenuController,
            PanelController,
            ProjectAutosaveController,
            ProjectController,
            RobotController,
            UIStateController,
            ViewportController,
        )

        # Instantiate MainWindow-specific controllers
        mw._connection_controller = ConnectionController(mw)
        mw._panel_controller = PanelController(mw)
        mw._menu_controller = MenuController(mw)
        mw._event_bus_controller = EventBusController(mw)
        mw._viewport_controller = ViewportController(mw)
        mw._ui_state_controller = UIStateController(mw)
        mw._project_controller = ProjectController(mw)
        mw._robot_controller = RobotController(mw)
        mw._project_autosave_controller = ProjectAutosaveController(mw)

        # External controllers - set to None, injected later
        mw._workflow_controller = None
        mw._execution_controller = None
        mw._node_controller = None

        # Initialize controllers in order
        self._initialize_controllers()

        self._controllers_initialized = True

    def _initialize_controllers(self) -> None:
        """Initialize all MainWindow-specific controllers in order."""
        mw = self._main_window

        # Initialize in dependency order
        # EventBus first (others may subscribe to events)
        mw._event_bus_controller.initialize()

        # UI-related controllers
        mw._connection_controller.initialize()
        mw._panel_controller.initialize()
        mw._menu_controller.initialize()
        mw._viewport_controller.initialize()

        # Feature controllers
        mw._ui_state_controller.initialize()
        mw._project_controller.initialize()
        mw._robot_controller.initialize()
        mw._project_autosave_controller.initialize()

        # Connect project autosave signals
        self._connect_project_autosave_signals()

    def _connect_project_autosave_signals(self) -> None:
        """Connect project controller signals to autosave controller."""
        mw = self._main_window

        if not mw._project_controller or not mw._project_autosave_controller:
            return

        # When a project is opened, register it with autosave
        mw._project_controller.project_opened.connect(self._on_project_opened_for_autosave)
        mw._project_controller.project_closed.connect(self._on_project_closed_for_autosave)

    @Slot(object)
    def _on_project_opened_for_autosave(self, project) -> None:
        """Handle project opened - register with autosave controller."""
        mw = self._main_window
        if mw._project_autosave_controller and project:
            # Get project path from project entity via property
            project_path = getattr(project, "path", None)
            if project_path:
                mw._project_autosave_controller.set_project(project, project_path)
                logger.info(f"Project autosave enabled: {project_path}")

    @Slot()
    def _on_project_closed_for_autosave(self) -> None:
        """Handle project closed - clear autosave controller."""
        mw = self._main_window
        if mw._project_autosave_controller:
            mw._project_autosave_controller.clear_project()

    def set_external_controllers(
        self,
        workflow_controller: "WorkflowController",
        execution_controller: "ExecutionController",
        node_controller: "NodeController",
        selector_controller: Optional["SelectorController"] = None,
    ) -> None:
        """
        Set externally created controllers (from app.py).

        These controllers are created by app.py because they need
        access to components not available during MainWindow init.

        Args:
            workflow_controller: Manages workflow lifecycle
            execution_controller: Manages workflow execution
            node_controller: Manages node operations
            selector_controller: Optional selector/picker controller
        """
        mw = self._main_window

        mw._workflow_controller = workflow_controller
        mw._execution_controller = execution_controller
        mw._node_controller = node_controller
        mw._selector_controller = selector_controller

        # Connect signals now that external controllers are available
        self._connect_controller_signals()

        # Re-enable actions now that controllers are set
        mw._update_actions()

    def _connect_controller_signals(self) -> None:
        """
        Wire signal/slot connections between controllers and MainWindow.

        This connects:
        - Workflow controller signals to MainWindow signals
        - Execution controller signals to UI state updates
        - Node controller signals to logging/debugging
        - Panel controller signals to UI feedback
        """

        logger.debug("Connecting controller signals...")

        # WorkflowController signals
        self._connect_workflow_signals()

        # ExecutionController signals
        self._connect_execution_signals()

        # NodeController signals
        self._connect_node_signals()

        # PanelController signals
        self._connect_panel_signals()

        logger.debug("Controller signals connected")

    def _connect_workflow_signals(self) -> None:
        """Connect WorkflowController signals to MainWindow."""
        mw = self._main_window
        wc = mw._workflow_controller

        if not wc:
            return

        wc.workflow_created.connect(self._on_workflow_created)
        wc.workflow_loaded.connect(self._on_workflow_loaded)
        wc.workflow_saved.connect(self._on_workflow_saved)
        wc.workflow_imported.connect(self._on_workflow_imported)
        wc.workflow_imported_json.connect(self._on_workflow_imported_json)
        wc.workflow_exported.connect(self._on_workflow_exported)
        wc.current_file_changed.connect(self._on_current_file_changed)
        wc.modified_changed.connect(self._on_modified_changed)

    def _connect_execution_signals(self) -> None:
        """Connect ExecutionController signals to MainWindow UI updates."""
        mw = self._main_window
        ec = mw._execution_controller

        if not ec:
            return

        ec.execution_started.connect(self._on_execution_started)
        ec.execution_paused.connect(self._on_execution_paused)
        ec.execution_resumed.connect(self._on_execution_resumed)
        ec.execution_stopped.connect(self._on_execution_stopped)
        ec.execution_completed.connect(self._on_execution_completed)
        ec.execution_error.connect(self._on_execution_error)
        ec.run_to_node_requested.connect(self._on_run_to_node_requested)
        ec.run_single_node_requested.connect(self._on_run_single_node_requested)

    def _connect_node_signals(self) -> None:
        """Connect NodeController signals for logging/debugging."""
        mw = self._main_window
        nc = mw._node_controller

        if not nc:
            return

        nc.node_selected.connect(self._on_node_selected)
        nc.node_deselected.connect(self._on_node_deselected)

    def _connect_panel_signals(self) -> None:
        """Connect PanelController signals."""
        mw = self._main_window
        pc = mw._panel_controller

        if not pc:
            return

        pc.bottom_panel_toggled.connect(self._on_bottom_panel_toggled)

    # Signal handlers - Workflow signals
    @Slot()
    def _on_workflow_created(self) -> None:
        """Handle workflow created signal."""
        self._main_window.workflow_new.emit()

    @Slot(str)
    def _on_workflow_loaded(self, path: str) -> None:
        """Handle workflow loaded signal."""
        self._main_window.workflow_open.emit(path)

    @Slot(str)
    def _on_workflow_saved(self, path: str) -> None:
        """Handle workflow saved signal."""
        logger.info(f"Workflow saved: {path}")

    @Slot(str)
    def _on_workflow_imported(self, path: str) -> None:
        """Handle workflow imported signal."""
        self._main_window.workflow_import.emit(path)

    @Slot(str)
    def _on_workflow_imported_json(self, json_str: str) -> None:
        """Handle workflow imported from JSON signal."""
        self._main_window.workflow_import_json.emit(json_str)

    @Slot(str)
    def _on_workflow_exported(self, path: str) -> None:
        """Handle workflow exported signal."""
        self._main_window.workflow_export_selected.emit(path)

    @Slot(object)
    def _on_current_file_changed(self, file: Path | None) -> None:
        """Handle current file change."""
        pass  # Reserved for future window title updates

    @Slot(bool)
    def _on_modified_changed(self, modified: bool) -> None:
        """Handle modified state change."""
        pass  # Reserved for future window title updates

    # Signal handlers - Execution signals
    @Slot()
    def _on_execution_started(self) -> None:
        """Update UI when execution starts."""
        mw = self._main_window
        mw.action_run.setEnabled(False)
        mw.action_pause.setEnabled(True)
        mw.action_pause.setChecked(False)
        mw.action_stop.setEnabled(True)
        mw.statusBar().showMessage("Workflow execution started...", 0)

    @Slot()
    def _on_execution_paused(self) -> None:
        """Update UI when execution is paused."""
        logger.info("Execution paused")

    @Slot()
    def _on_execution_resumed(self) -> None:
        """Update UI when execution is resumed."""
        logger.info("Execution resumed")

    @Slot()
    def _on_execution_stopped(self) -> None:
        """Update UI when execution is stopped."""
        mw = self._main_window
        mw.action_run.setEnabled(True)
        mw.action_pause.setEnabled(False)
        mw.action_stop.setEnabled(False)
        mw.statusBar().showMessage("Workflow execution stopped", 3000)

    @Slot()
    def _on_execution_completed(self) -> None:
        """Update UI when execution completes."""
        mw = self._main_window
        mw.action_run.setEnabled(True)
        mw.action_pause.setEnabled(False)
        mw.action_stop.setEnabled(False)
        mw.statusBar().showMessage("Workflow execution completed", 3000)

    @Slot(str)
    def _on_execution_error(self, error: str) -> None:
        """Update UI when execution encounters an error."""
        mw = self._main_window
        mw.action_run.setEnabled(True)
        mw.action_pause.setEnabled(False)
        mw.action_stop.setEnabled(False)
        mw.statusBar().showMessage(f"Execution error: {error}", 5000)

    @Slot(str)
    def _on_run_to_node_requested(self, node_id: str) -> None:
        """Handle run to node requested signal."""
        self._main_window.workflow_run_to_node.emit(node_id)

    @Slot(str)
    def _on_run_single_node_requested(self, node_id: str) -> None:
        """Handle run single node requested signal."""
        self._main_window.workflow_run_single_node.emit(node_id)

    # Signal handlers - Node signals
    @Slot(str)
    def _on_node_selected(self, node_id: str) -> None:
        """Handle node selected signal."""
        logger.debug(f"Node selected: {node_id}")

    @Slot(str)
    def _on_node_deselected(self, node_id: str) -> None:
        """Handle node deselected signal."""
        logger.debug(f"Node deselected: {node_id}")

    # Signal handlers - Panel signals
    @Slot(bool)
    def _on_bottom_panel_toggled(self, visible: bool) -> None:
        """Handle bottom panel toggled signal."""
        logger.debug(f"Bottom panel toggled: {visible}")

    def cleanup_all(self) -> None:
        """
        Clean up all controllers.

        Called during MainWindow close event.
        """
        mw = self._main_window

        logger.info("Cleaning up controllers...")

        controllers = [
            mw._workflow_controller,
            mw._execution_controller,
            mw._node_controller,
            mw._selector_controller,
            mw._connection_controller,
            mw._panel_controller,
            mw._menu_controller,
            mw._event_bus_controller,
            mw._viewport_controller,
            mw._ui_state_controller,
            mw._project_controller,
            mw._robot_controller,
            getattr(mw, "_project_autosave_controller", None),
        ]

        for controller in controllers:
            if controller:
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error(
                        f"Error cleaning up controller {controller.__class__.__name__}: {e}"
                    )

        self._controllers_initialized = False
        logger.info("Controllers cleaned up")
