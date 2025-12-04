"""
Dock widget creator for MainWindow.

Centralizes creation of dock widgets (panels).
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDockWidget

from loguru import logger

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from ..ui.panels import BottomPanelDock
    from ..ui.panels.variable_inspector_dock import VariableInspectorDock
    from ..ui.panels.properties_panel import PropertiesPanel
    from ..ui.panels.process_mining_panel import ProcessMiningPanel
    from ..ui.panels.analytics_panel import AnalyticsPanel
    from ..ui.panels.robot_picker_panel import RobotPickerPanel
    from ..ui.widgets.execution_timeline import ExecutionTimeline
    from ..ui.debug_panel import DebugPanel
    from ..debugger.debug_controller import DebugController
    from ..controllers.robot_controller import RobotController


class DockCreator:
    """
    Creates dock widgets for MainWindow.

    Responsibilities:
    - Create bottom panel dock
    - Create variable inspector dock
    - Create properties panel
    - Create execution timeline dock
    - Connect dock signals
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize dock creator.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

    def create_bottom_panel(self) -> "BottomPanelDock":
        """
        Create the unified bottom panel with Variables, Output, Log, Validation tabs.

        Returns:
            Created BottomPanelDock instance
        """
        from ..ui.panels import BottomPanelDock

        mw = self._main_window
        bottom_panel = BottomPanelDock(mw)

        # Connect signals
        bottom_panel.validation_requested.connect(mw._on_validate_workflow)
        bottom_panel.issue_clicked.connect(mw._on_validation_issue_clicked)
        bottom_panel.navigate_to_node.connect(mw._on_navigate_to_node)
        bottom_panel.variables_changed.connect(mw._on_panel_variables_changed)

        # Note: Triggers are now visual nodes on the canvas (not UI signals)

        # Add to main window
        mw.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_panel)

        # Connect dock state changes to auto-save
        bottom_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        bottom_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        bottom_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Initially visible
        bottom_panel.show()
        mw.action_toggle_bottom_panel.setChecked(True)

        logger.info("Bottom panel created with Variables, Output, Log, Validation tabs")
        return bottom_panel

    def create_variable_inspector_dock(self) -> "VariableInspectorDock":
        """
        Create the Variable Inspector dock for real-time variable values.

        Returns:
            Created VariableInspectorDock instance
        """
        from ..ui.panels.variable_inspector_dock import VariableInspectorDock

        mw = self._main_window
        variable_inspector_dock = VariableInspectorDock(mw)

        # Add to main window (bottom area)
        mw.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, variable_inspector_dock
        )

        # Split dock horizontally with bottom panel (side-by-side)
        if mw._bottom_panel:
            mw.splitDockWidget(
                mw._bottom_panel,
                variable_inspector_dock,
                Qt.Orientation.Horizontal,
            )

        # Connect dock state changes to auto-save
        variable_inspector_dock.dockLocationChanged.connect(mw._schedule_ui_state_save)
        variable_inspector_dock.visibilityChanged.connect(mw._schedule_ui_state_save)
        variable_inspector_dock.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Initially hidden
        variable_inspector_dock.hide()
        mw.action_toggle_variable_inspector.setChecked(False)

        logger.info("Variable Inspector dock created")
        return variable_inspector_dock

    def create_properties_panel(self) -> "PropertiesPanel":
        """
        Create the properties panel for selected node editing.

        Returns:
            Created PropertiesPanel instance
        """
        from ..ui.panels.properties_panel import PropertiesPanel

        mw = self._main_window
        properties_panel = PropertiesPanel(mw)

        # Connect property changes to mark workflow as modified
        properties_panel.property_changed.connect(mw._on_property_panel_changed)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, properties_panel)

        # Connect dock state changes to auto-save
        properties_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        properties_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        properties_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = properties_panel.toggleViewAction()
                toggle_action.setText("&Properties Panel")
                toggle_action.setShortcut(QKeySequence("Ctrl+P"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_properties = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Properties Panel to View menu: {e}")

        logger.info("Properties panel created")
        return properties_panel

    def create_execution_timeline_dock(
        self,
    ) -> tuple[QDockWidget, "ExecutionTimeline"]:
        """
        Create the Execution Timeline dock for visualizing workflow execution.

        Returns:
            Tuple of (QDockWidget, ExecutionTimeline)
        """
        from ..ui.widgets.execution_timeline import ExecutionTimeline

        mw = self._main_window
        execution_timeline = ExecutionTimeline(mw)

        # Create dock widget
        execution_timeline_dock = QDockWidget("Execution Timeline", mw)
        execution_timeline_dock.setObjectName("ExecutionTimelineDock")
        execution_timeline_dock.setWidget(execution_timeline)
        execution_timeline_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        # Add to main window (bottom area)
        mw.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, execution_timeline_dock
        )

        # Connect dock state changes to auto-save
        execution_timeline_dock.dockLocationChanged.connect(mw._schedule_ui_state_save)
        execution_timeline_dock.visibilityChanged.connect(mw._schedule_ui_state_save)
        execution_timeline_dock.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Tabify with variable inspector if exists
        if mw._variable_inspector_dock:
            mw.tabifyDockWidget(mw._variable_inspector_dock, execution_timeline_dock)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = execution_timeline_dock.toggleViewAction()
                toggle_action.setText("&Execution Timeline")
                view_menu.addAction(toggle_action)
                mw.action_toggle_timeline = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Execution Timeline to View menu: {e}")

        # Connect node clicked signal
        execution_timeline.node_clicked.connect(mw._select_node_by_id)

        # Initially hidden
        execution_timeline_dock.hide()

        logger.info("Execution Timeline dock created")
        return execution_timeline_dock, execution_timeline

    def create_debug_panel(
        self, debug_controller: Optional["DebugController"] = None
    ) -> "DebugPanel":
        """
        Create the Debug Panel dock for debugging workflow execution.

        Features:
        - Call Stack visualization
        - Watch Expressions
        - Breakpoint management
        - REPL console
        - Execution snapshots

        Args:
            debug_controller: Optional debug controller for integration

        Returns:
            Created DebugPanel instance
        """
        from ..ui.debug_panel import DebugPanel

        mw = self._main_window
        debug_panel = DebugPanel(mw, debug_controller)

        # Connect signals
        debug_panel.navigate_to_node.connect(mw._on_navigate_to_node)
        debug_panel.step_over_requested.connect(mw._on_debug_step_over)
        debug_panel.step_into_requested.connect(mw._on_debug_step_into)
        debug_panel.step_out_requested.connect(mw._on_debug_step_out)
        debug_panel.continue_requested.connect(mw._on_debug_continue)

        # Add to main window (right side, below properties panel)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, debug_panel)

        # Tabify with properties panel if exists
        if mw._properties_panel:
            mw.tabifyDockWidget(mw._properties_panel, debug_panel)

        # Connect dock state changes to auto-save
        debug_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        debug_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        debug_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = debug_panel.toggleViewAction()
                toggle_action.setText("&Debug Panel")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_debug_panel = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Debug Panel to View menu: {e}")

        # Initially hidden (activate with Ctrl+F5 or menu)
        debug_panel.hide()

        logger.info("Debug Panel created with Call Stack, Watch, Breakpoints tabs")
        return debug_panel

    def create_process_mining_panel(self) -> "ProcessMiningPanel":
        """
        Create the Process Mining Panel for AI-powered process discovery.

        Features:
        - Process Discovery: Build process models from execution logs
        - Variant Analysis: See different execution paths
        - Conformance Checking: Compare actual vs expected
        - Optimization Insights: AI-generated recommendations

        Returns:
            Created ProcessMiningPanel instance
        """
        from ..ui.panels.process_mining_panel import ProcessMiningPanel

        mw = self._main_window
        process_mining_panel = ProcessMiningPanel(mw)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, process_mining_panel)

        # Tabify with properties panel if exists
        if mw._properties_panel:
            mw.tabifyDockWidget(mw._properties_panel, process_mining_panel)

        # Connect dock state changes to auto-save
        process_mining_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        process_mining_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        process_mining_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = process_mining_panel.toggleViewAction()
                toggle_action.setText("Process &Mining")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+M"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_process_mining = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Process Mining Panel to View menu: {e}")

        # Initially hidden
        process_mining_panel.hide()

        logger.info(
            "Process Mining Panel created with Discovery, Variants, Insights tabs"
        )
        return process_mining_panel

    def create_robot_picker_panel(
        self, robot_controller: Optional["RobotController"] = None
    ) -> "RobotPickerPanel":
        """
        Create the Robot Picker Panel for selecting robots and execution mode.

        Features:
        - Execution mode toggle: Local vs Cloud
        - Tree view of available robots with status indicators
        - Robot filtering by capability
        - Refresh button to update robot list

        Args:
            robot_controller: Optional robot controller for integration

        Returns:
            Created RobotPickerPanel instance
        """
        from ..ui.panels.robot_picker_panel import RobotPickerPanel

        mw = self._main_window
        robot_picker = RobotPickerPanel(mw)

        # Connect to robot controller if provided
        if robot_controller:
            robot_controller.set_panel(robot_picker)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, robot_picker)

        # Tabify with properties panel if exists
        if mw._properties_panel:
            mw.tabifyDockWidget(mw._properties_panel, robot_picker)

        # Connect dock state changes to auto-save
        robot_picker.dockLocationChanged.connect(mw._schedule_ui_state_save)
        robot_picker.visibilityChanged.connect(mw._schedule_ui_state_save)
        robot_picker.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = robot_picker.toggleViewAction()
                toggle_action.setText("&Robot Picker")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_robot_picker = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Robot Picker to View menu: {e}")

        # Initially hidden (show when user enables cloud execution)
        robot_picker.hide()

        logger.info("Robot Picker Panel created")
        return robot_picker

    def create_analytics_panel(self) -> "AnalyticsPanel":
        """
        Create the Analytics Panel for bottleneck detection and execution analysis.

        Connects to the Orchestrator REST API for:
        - Bottleneck Detection: Identify slow/failing nodes
        - Execution Analysis: Trends, patterns, insights
        - Timeline visualization

        Returns:
            Created AnalyticsPanel instance
        """
        from ..ui.panels.analytics_panel import AnalyticsPanel

        mw = self._main_window
        analytics_panel = AnalyticsPanel(mw)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, analytics_panel)

        # Tabify with properties panel if exists
        if mw._properties_panel:
            mw.tabifyDockWidget(mw._properties_panel, analytics_panel)

        # Connect dock state changes to auto-save
        analytics_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        analytics_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        analytics_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Connect to robot controller to update URL when connected
        if hasattr(mw, "_robot_controller") and mw._robot_controller:
            mw._robot_controller.connection_status_changed.connect(
                lambda connected: self._update_analytics_url(analytics_panel, connected)
            )

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = analytics_panel.toggleViewAction()
                toggle_action.setText("&Analytics Panel")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_analytics = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Analytics Panel to View menu: {e}")

        # Initially hidden
        analytics_panel.hide()

        logger.info(
            "Analytics Panel created with Bottlenecks, Execution, Timeline tabs"
        )
        return analytics_panel

    def _update_analytics_url(
        self, analytics_panel: "AnalyticsPanel", connected: bool
    ) -> None:
        """Update analytics panel URL when robot controller connects."""
        if not connected:
            return

        mw = self._main_window
        if hasattr(mw, "_robot_controller") and mw._robot_controller:
            url = mw._robot_controller.orchestrator_url
            if url:
                analytics_panel.set_api_url(url)
                logger.debug(f"Analytics panel URL updated to: {url}")

    def _find_view_menu(self):
        """Get the View menu from MainWindow (stored reference)."""
        mw = self._main_window
        # Use stored reference if available (more reliable than searching)
        if hasattr(mw, "_view_menu") and mw._view_menu is not None:
            try:
                # Verify the menu is still valid by accessing a property
                _ = mw._view_menu.title()
                return mw._view_menu
            except RuntimeError:
                # Menu was deleted, fall through to search
                pass
        # Fallback: search menu bar
        for action in mw.menuBar().actions():
            if action.text() == "&View":
                return action.menu()
        return None
