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

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from ..controllers import (
        WorkflowController,
        ExecutionController,
        NodeController,
        ConnectionController,
        PanelController,
        MenuController,
        EventBusController,
        ViewportController,
        UIStateController,
        SelectorController,
        ProjectController,
        RobotController,
    )


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
            PanelController,
            MenuController,
            EventBusController,
            ViewportController,
            UIStateController,
            ProjectController,
            RobotController,
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
        mw = self._main_window

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

        wc.workflow_created.connect(lambda: mw.workflow_new.emit())
        wc.workflow_loaded.connect(lambda path: mw.workflow_open.emit(path))
        wc.workflow_saved.connect(lambda path: logger.info(f"Workflow saved: {path}"))
        wc.workflow_imported.connect(lambda path: mw.workflow_import.emit(path))
        wc.workflow_imported_json.connect(
            lambda json_str: mw.workflow_import_json.emit(json_str)
        )
        wc.workflow_exported.connect(
            lambda path: mw.workflow_export_selected.emit(path)
        )
        wc.current_file_changed.connect(
            lambda file: self._on_current_file_changed(file)
        )
        wc.modified_changed.connect(
            lambda modified: self._on_modified_changed(modified)
        )

    def _connect_execution_signals(self) -> None:
        """Connect ExecutionController signals to MainWindow UI updates."""
        mw = self._main_window
        ec = mw._execution_controller

        if not ec:
            return

        ec.execution_started.connect(lambda: self._on_execution_started())
        ec.execution_paused.connect(lambda: logger.info("Execution paused"))
        ec.execution_resumed.connect(lambda: logger.info("Execution resumed"))
        ec.execution_stopped.connect(lambda: self._on_execution_stopped())
        ec.execution_completed.connect(lambda: self._on_execution_completed())
        ec.execution_error.connect(lambda error: self._on_execution_error(error))
        ec.run_to_node_requested.connect(
            lambda node_id: mw.workflow_run_to_node.emit(node_id)
        )
        ec.run_single_node_requested.connect(
            lambda node_id: mw.workflow_run_single_node.emit(node_id)
        )

    def _connect_node_signals(self) -> None:
        """Connect NodeController signals for logging/debugging."""
        mw = self._main_window
        nc = mw._node_controller

        if not nc:
            return

        nc.node_selected.connect(
            lambda node_id: logger.debug(f"Node selected: {node_id}")
        )
        nc.node_deselected.connect(
            lambda node_id: logger.debug(f"Node deselected: {node_id}")
        )

    def _connect_panel_signals(self) -> None:
        """Connect PanelController signals."""
        mw = self._main_window
        pc = mw._panel_controller

        if not pc:
            return

        pc.bottom_panel_toggled.connect(
            lambda visible: logger.debug(f"Bottom panel toggled: {visible}")
        )

    # Signal handlers
    def _on_current_file_changed(self, file: Optional[Path]) -> None:
        """Handle current file change."""
        pass  # Reserved for future window title updates

    def _on_modified_changed(self, modified: bool) -> None:
        """Handle modified state change."""
        pass  # Reserved for future window title updates

    def _on_execution_started(self) -> None:
        """Update UI when execution starts."""
        mw = self._main_window
        mw.action_run.setEnabled(False)
        mw.action_pause.setEnabled(True)
        mw.action_pause.setChecked(False)
        mw.action_stop.setEnabled(True)
        mw.statusBar().showMessage("Workflow execution started...", 0)

    def _on_execution_stopped(self) -> None:
        """Update UI when execution is stopped."""
        mw = self._main_window
        mw.action_run.setEnabled(True)
        mw.action_pause.setEnabled(False)
        mw.action_stop.setEnabled(False)
        mw.statusBar().showMessage("Workflow execution stopped", 3000)

    def _on_execution_completed(self) -> None:
        """Update UI when execution completes."""
        mw = self._main_window
        mw.action_run.setEnabled(True)
        mw.action_pause.setEnabled(False)
        mw.action_stop.setEnabled(False)
        mw.statusBar().showMessage("Workflow execution completed", 3000)

    def _on_execution_error(self, error: str) -> None:
        """Update UI when execution encounters an error."""
        mw = self._main_window
        mw.action_run.setEnabled(True)
        mw.action_pause.setEnabled(False)
        mw.action_stop.setEnabled(False)
        mw.statusBar().showMessage(f"Execution error: {error}", 5000)

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
