"""
Signal Bridge for MainWindow Controller Connections.

This module provides a bridge class that connects controller signals
to MainWindow handlers and other controllers. Extracts ~400 lines
of signal/slot connection code from MainWindow.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow
    from casare_rpa.presentation.canvas.controllers import (
        ConnectionController,
        EventBusController,
        ExecutionController,
        MenuController,
        NodeController,
        PanelController,
        UIStateController,
        ViewportController,
        WorkflowController,
    )


class ControllerSignalBridge(QObject):
    """
    Bridge that connects controller signals to MainWindow handlers.

    This class centralizes all signal/slot connections between controllers
    and the MainWindow, reducing code in MainWindow and making the
    signal flow easier to understand and maintain.

    The bridge is responsible for:
    - Connecting workflow controller signals (new, open, save, etc.)
    - Connecting execution controller signals (start, pause, stop, etc.)
    - Connecting node controller signals (select, deselect, etc.)
    - Connecting panel controller signals (toggle, show, hide, etc.)
    - Forwarding events between controllers when needed

    Example:
        bridge = ControllerSignalBridge(main_window)
        bridge.connect_all_controllers(
            workflow_controller,
            execution_controller,
            node_controller,
            ...
        )
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the signal bridge.

        Args:
            main_window: Parent MainWindow instance
        """
        super().__init__(main_window)
        self._main_window = main_window

    def connect_all_controllers(
        self,
        workflow_controller: Optional["WorkflowController"] = None,
        execution_controller: Optional["ExecutionController"] = None,
        node_controller: Optional["NodeController"] = None,
        connection_controller: Optional["ConnectionController"] = None,
        panel_controller: Optional["PanelController"] = None,
        menu_controller: Optional["MenuController"] = None,
        event_bus_controller: Optional["EventBusController"] = None,
        viewport_controller: Optional["ViewportController"] = None,
        ui_state_controller: Optional["UIStateController"] = None,
    ) -> None:
        """
        Connect all controller signals to MainWindow handlers.

        Args:
            workflow_controller: Workflow management controller
            execution_controller: Workflow execution controller
            node_controller: Node management controller
            connection_controller: Connection management controller
            panel_controller: Panel/dock management controller
            menu_controller: Menu/dialog management controller
            event_bus_controller: EventBus integration controller
            viewport_controller: Viewport/zoom management controller
            ui_state_controller: UI state persistence controller

        Note: Triggers and scheduling are now visual nodes on the canvas
              and handled via orchestrator API (not controllers).
        """
        logger.debug("ControllerSignalBridge: Connecting controller signals...")

        if workflow_controller:
            self._connect_workflow_controller(workflow_controller)

        if execution_controller:
            self._connect_execution_controller(execution_controller)

        if node_controller:
            self._connect_node_controller(node_controller)

        if panel_controller:
            self._connect_panel_controller(panel_controller)

        logger.debug("ControllerSignalBridge: Controller signals connected")

    def _connect_workflow_controller(self, controller: "WorkflowController") -> None:
        """
        Connect WorkflowController signals to MainWindow handlers.

        Args:
            controller: WorkflowController instance
        """
        mw = self._main_window

        # Workflow lifecycle signals
        controller.workflow_created.connect(lambda: mw.workflow_new.emit())

        controller.workflow_loaded.connect(lambda path: mw.workflow_open.emit(path))

        controller.workflow_saved.connect(
            lambda path: logger.info(f"Workflow saved: {path}")
        )

        controller.workflow_imported.connect(lambda path: mw.workflow_import.emit(path))

        controller.workflow_imported_json.connect(
            lambda json_str: mw.workflow_import_json.emit(json_str)
        )

        controller.workflow_exported.connect(
            lambda path: mw.workflow_export_selected.emit(path)
        )

        # File state signals
        controller.current_file_changed.connect(self._on_current_file_changed)
        controller.modified_changed.connect(self._on_modified_changed)

        logger.debug("ControllerSignalBridge: WorkflowController connected")

    def _connect_execution_controller(self, controller: "ExecutionController") -> None:
        """
        Connect ExecutionController signals to MainWindow handlers.

        Args:
            controller: ExecutionController instance
        """
        mw = self._main_window

        # Execution lifecycle signals
        controller.execution_started.connect(self._on_execution_started)
        controller.execution_paused.connect(lambda: logger.info("Execution paused"))
        controller.execution_resumed.connect(lambda: logger.info("Execution resumed"))
        controller.execution_stopped.connect(self._on_execution_stopped)
        controller.execution_completed.connect(self._on_execution_completed)
        controller.execution_error.connect(self._on_execution_error)

        # Partial execution signals
        controller.run_to_node_requested.connect(
            lambda node_id: mw.workflow_run_to_node.emit(node_id)
        )
        controller.run_single_node_requested.connect(
            lambda node_id: mw.workflow_run_single_node.emit(node_id)
        )

        logger.debug("ControllerSignalBridge: ExecutionController connected")

    def _connect_node_controller(self, controller: "NodeController") -> None:
        """
        Connect NodeController signals to MainWindow handlers.

        Args:
            controller: NodeController instance
        """
        # Node selection signals are now connected but without debug logging
        # to avoid performance overhead on every selection change
        pass

    def _connect_panel_controller(self, controller: "PanelController") -> None:
        """
        Connect PanelController signals to MainWindow handlers.

        Args:
            controller: PanelController instance
        """
        # Panel visibility signals
        controller.bottom_panel_toggled.connect(
            lambda visible: logger.debug(f"Bottom panel toggled: {visible}")
        )

        logger.debug("ControllerSignalBridge: PanelController connected")

    def _on_current_file_changed(self, file) -> None:
        """
        Handle current file changed from WorkflowController.

        Args:
            file: New file path or None
        """
        # Window title is updated by WorkflowController directly
        pass

    def _on_modified_changed(self, modified: bool) -> None:
        """
        Handle modified state changed from WorkflowController.

        Args:
            modified: Whether workflow has unsaved changes
        """
        # UI state is updated by WorkflowController directly
        pass

    def _on_execution_started(self) -> None:
        """Handle execution started from ExecutionController."""
        mw = self._main_window
        actions = getattr(mw, "_action_factory", None)

        if actions:
            actions.set_actions_enabled(["run", "run_to_node"], False)
            actions.set_actions_enabled(["pause", "stop"], True)

            pause_action = actions.get_action("pause")
            if pause_action:
                pause_action.setChecked(False)
        else:
            # Fallback to direct action access
            mw.action_run.setEnabled(False)
            mw.action_pause.setEnabled(True)
            mw.action_pause.setChecked(False)
            mw.action_stop.setEnabled(True)

        mw.statusBar().showMessage("Workflow execution started...", 0)

    def _on_execution_stopped(self) -> None:
        """Handle execution stopped from ExecutionController."""
        mw = self._main_window
        actions = getattr(mw, "_action_factory", None)

        if actions:
            actions.set_actions_enabled(["run"], True)
            actions.set_actions_enabled(["pause", "stop"], False)
        else:
            mw.action_run.setEnabled(True)
            mw.action_pause.setEnabled(False)
            mw.action_stop.setEnabled(False)

        mw.statusBar().showMessage("Workflow execution stopped", 3000)

    def _on_execution_completed(self) -> None:
        """Handle execution completed from ExecutionController."""
        mw = self._main_window
        actions = getattr(mw, "_action_factory", None)

        if actions:
            actions.set_actions_enabled(["run"], True)
            actions.set_actions_enabled(["pause", "stop"], False)
        else:
            mw.action_run.setEnabled(True)
            mw.action_pause.setEnabled(False)
            mw.action_stop.setEnabled(False)

        mw.statusBar().showMessage("Workflow execution completed", 3000)

    def _on_execution_error(self, error: str) -> None:
        """
        Handle execution error from ExecutionController.

        Args:
            error: Error message
        """
        mw = self._main_window
        actions = getattr(mw, "_action_factory", None)

        if actions:
            actions.set_actions_enabled(["run"], True)
            actions.set_actions_enabled(["pause", "stop"], False)
        else:
            mw.action_run.setEnabled(True)
            mw.action_pause.setEnabled(False)
            mw.action_stop.setEnabled(False)

        mw.statusBar().showMessage(f"Execution error: {error}", 5000)


class BottomPanelSignalBridge(QObject):
    """
    Bridge that connects BottomPanel signals to MainWindow handlers.

    Handles variable changes and validation requests from the bottom panel dock widget.

    Note: Triggers are now visual nodes on the canvas (not managed via bottom panel).
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the bottom panel signal bridge.

        Args:
            main_window: Parent MainWindow instance
        """
        super().__init__(main_window)
        self._main_window = main_window

    def connect_bottom_panel(self, panel) -> None:
        """
        Connect BottomPanelDock signals to MainWindow handlers.

        Args:
            panel: BottomPanelDock instance
        """
        mw = self._main_window

        # Validation signals
        panel.validation_requested.connect(mw._on_validate_workflow)
        panel.issue_clicked.connect(mw._on_validation_issue_clicked)
        panel.navigate_to_node.connect(mw._on_navigate_to_node)
        panel.variables_changed.connect(mw._on_panel_variables_changed)

        # Note: Triggers are now visual nodes on the canvas

        # Dock state signals for auto-save
        panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        logger.debug("BottomPanelSignalBridge: BottomPanel connected")

    def connect_execution_timeline(self, timeline, dock) -> None:
        """
        Connect ExecutionTimeline signals to MainWindow handlers.

        Args:
            timeline: ExecutionTimeline widget
            dock: QDockWidget containing the timeline
        """
        mw = self._main_window

        # Node clicked signal
        timeline.node_clicked.connect(mw._select_node_by_id)

        # Dock state signals for auto-save
        dock.dockLocationChanged.connect(mw._schedule_ui_state_save)
        dock.visibilityChanged.connect(mw._schedule_ui_state_save)
        dock.topLevelChanged.connect(mw._schedule_ui_state_save)

        logger.debug("BottomPanelSignalBridge: ExecutionTimeline connected")
