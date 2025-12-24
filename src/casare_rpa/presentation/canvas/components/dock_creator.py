"""
Dock widget creator for MainWindow.

Centralizes creation of dock widgets (panels).
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

if TYPE_CHECKING:
    from ..controllers.robot_controller import RobotController
    from ..debugger.debug_controller import DebugController
    from ..main_window import MainWindow
    from ..ui.debug_panel import DebugPanel
    from ..ui.panels import (
        BottomPanelDock,
        BreakpointsPanel,
        CredentialsPanel,
        ProjectExplorerPanel,
        SidePanelDock,
    )
    from ..ui.panels.analytics_panel import AnalyticsPanel
    from ..ui.panels.process_mining_panel import ProcessMiningPanel
    from ..ui.panels.robot_picker_panel import RobotPickerPanel
    from ..ui.widgets.ai_assistant import AIAssistantDock


class DockCreator:
    """
    Creates dock widgets for MainWindow.

    Responsibilities:
    - Create bottom panel dock
    - Create side panel dock (Debug, Process Mining, Robot Picker, Analytics)
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
        bottom_panel.repair_requested.connect(mw._on_repair_workflow)
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

        return bottom_panel

    def create_side_panel(
        self,
        debug_controller: Optional["DebugController"] = None,
        robot_controller: Optional["RobotController"] = None,
    ) -> "SidePanelDock":
        """
        Create the unified Side Panel with Debug, Process Mining, Robot Picker, Analytics tabs.

        Args:
            debug_controller: Optional debug controller for integration
            robot_controller: Optional robot controller for integration

        Returns:
            Created SidePanelDock instance
        """
        from ..ui.panels import SidePanelDock

        mw = self._main_window
        side_panel = SidePanelDock(mw, debug_controller, robot_controller)

        # Connect signals
        side_panel.navigate_to_node.connect(mw._on_navigate_to_node)
        side_panel.step_over_requested.connect(mw._on_debug_step_over)
        side_panel.step_into_requested.connect(mw._on_debug_step_into)
        side_panel.step_out_requested.connect(mw._on_debug_step_out)
        side_panel.continue_requested.connect(mw._on_debug_continue)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, side_panel)

        # Connect dock state changes to auto-save
        side_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
        side_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
        side_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Connect to robot controller for analytics URL updates
        if robot_controller:
            robot_controller.connection_status_changed.connect(
                lambda connected: self._update_side_panel_analytics_url(side_panel, connected)
            )

        # Add toggle action to View menu with hotkey 7
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = side_panel.toggleViewAction()
                toggle_action.setText("&Side Panel")
                toggle_action.setShortcut(QKeySequence("7"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_side_panel = toggle_action

                # Add explicit Profiling toggle if available
                if hasattr(side_panel, "get_profiling_tab") and side_panel.get_profiling_tab():
                    profiling_action = view_menu.addAction("Show &Profiling")
                    profiling_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
                    profiling_action.triggered.connect(mw._panel_manager.show_profiling_tab)
                    mw.action_show_profiling = profiling_action
        except RuntimeError as e:
            logger.warning(f"Could not add Side Panel to View menu: {e}")

        # Initially hidden
        side_panel.hide()

        return side_panel

    def _update_side_panel_analytics_url(
        self, side_panel: "SidePanelDock", connected: bool
    ) -> None:
        """Update side panel analytics URL when robot controller connects."""
        if not connected:
            return

        mw = self._main_window
        if hasattr(mw, "_robot_controller") and mw._robot_controller:
            url = mw._robot_controller.orchestrator_url
            if url:
                side_panel.set_analytics_api_url(url)
                logger.debug(f"Side panel analytics URL updated to: {url}")

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

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, debug_panel)

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

        return analytics_panel

    def _update_analytics_url(self, analytics_panel: "AnalyticsPanel", connected: bool) -> None:
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

    def create_project_explorer_panel(self) -> "ProjectExplorerPanel":
        """
        Create the Project Explorer Panel for folder hierarchy.

        Features:
        - VS Code-style tree view
        - Folder creation, renaming, deletion
        - Project drag-drop organization
        - Double-click to open project

        Returns:
            Created ProjectExplorerPanel instance
        """
        from ..ui.panels import ProjectExplorerPanel

        mw = self._main_window
        project_explorer = ProjectExplorerPanel(mw)

        # Connect signals
        if hasattr(mw, "_on_project_opened"):
            project_explorer.project_opened.connect(mw._on_project_opened)
        if hasattr(mw, "_on_project_selected"):
            project_explorer.project_selected.connect(mw._on_project_selected)

        # Add to main window (left side)
        mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, project_explorer)

        # Connect dock state changes to auto-save
        if hasattr(mw, "_schedule_ui_state_save"):
            project_explorer.dockLocationChanged.connect(mw._schedule_ui_state_save)
            project_explorer.visibilityChanged.connect(mw._schedule_ui_state_save)
            project_explorer.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = project_explorer.toggleViewAction()
                toggle_action.setText("&Project Explorer")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_project_explorer = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Project Explorer to View menu: {e}")

        # Initially hidden
        project_explorer.hide()

        return project_explorer

    def create_credentials_panel(self) -> "CredentialsPanel":
        """
        Create the Credentials Panel for global credentials management.

        Features:
        - View credential aliases (not values)
        - Add/Edit/Delete credentials
        - Test connection for API keys
        - Context menu actions

        Returns:
            Created CredentialsPanel instance
        """
        from ..ui.panels import CredentialsPanel

        mw = self._main_window
        credentials_panel = CredentialsPanel(mw)

        # Connect signals
        if hasattr(mw, "_on_credential_updated"):
            credentials_panel.credential_updated.connect(mw._on_credential_updated)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, credentials_panel)

        # Connect dock state changes to auto-save
        if hasattr(mw, "_schedule_ui_state_save"):
            credentials_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
            credentials_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
            credentials_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = credentials_panel.toggleViewAction()
                toggle_action.setText("&Credentials Panel")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_credentials_panel = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Credentials Panel to View menu: {e}")

        # Initially hidden
        credentials_panel.hide()

        return credentials_panel

    def create_ai_assistant_panel(self) -> "AIAssistantDock":
        """
        Create the AI Assistant Panel for AI-powered workflow generation.

        Features:
        - Natural language to workflow JSON conversion
        - Structural validation before preview
        - Append/Replace workflow modes
        - Multi-provider support (Anthropic/OpenAI)

        Returns:
            Created AIAssistantDock instance
        """
        from ..ui.widgets.ai_assistant import AIAssistantDock

        mw = self._main_window
        ai_assistant = AIAssistantDock(mw)

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, ai_assistant)

        # Connect dock state changes to auto-save
        if hasattr(mw, "_schedule_ui_state_save"):
            ai_assistant.dockLocationChanged.connect(mw._schedule_ui_state_save)
            ai_assistant.visibilityChanged.connect(mw._schedule_ui_state_save)
            ai_assistant.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu with shortcut
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = ai_assistant.toggleViewAction()
                toggle_action.setText("AI &Assistant")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+G"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_ai_assistant = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add AI Assistant to View menu: {e}")

        # Initially hidden
        ai_assistant.hide()

        return ai_assistant

    def create_breakpoints_panel(
        self, debug_controller: Optional["DebugController"] = None
    ) -> "BreakpointsPanel":
        """
        Create the Breakpoints Panel for managing workflow breakpoints.

        Features:
        - List view of all breakpoints with type, node, condition, hit count
        - Enable/disable individual breakpoints or all at once
        - Context menu for edit, delete, go to node actions
        - Double-click to edit condition
        - Click to navigate to node on canvas

        Args:
            debug_controller: Optional debug controller for integration

        Returns:
            Created BreakpointsPanel instance
        """
        from ..ui.panels import BreakpointsPanel

        mw = self._main_window
        breakpoints_panel = BreakpointsPanel(mw, debug_controller)

        # Connect signals
        breakpoints_panel.navigate_to_node.connect(mw._on_navigate_to_node)
        breakpoints_panel.edit_breakpoint.connect(
            lambda node_id: self._on_edit_breakpoint(breakpoints_panel, node_id)
        )

        # Add to main window (right side)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, breakpoints_panel)

        # Connect dock state changes to auto-save
        if hasattr(mw, "_schedule_ui_state_save"):
            breakpoints_panel.dockLocationChanged.connect(mw._schedule_ui_state_save)
            breakpoints_panel.visibilityChanged.connect(mw._schedule_ui_state_save)
            breakpoints_panel.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu with shortcut (Ctrl+B)
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = breakpoints_panel.toggleViewAction()
                toggle_action.setText("&Breakpoints Panel")
                toggle_action.setShortcut(QKeySequence("Ctrl+B"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_breakpoints_panel = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Breakpoints Panel to View menu: {e}")

        # Initially hidden
        breakpoints_panel.hide()

        return breakpoints_panel

    def _on_edit_breakpoint(self, panel: "BreakpointsPanel", node_id: str) -> None:
        """
        Handle edit breakpoint request from panel.

        Args:
            panel: The breakpoints panel
            node_id: ID of the node to edit breakpoint for
        """
        from ..ui.dialogs import show_breakpoint_edit_dialog

        mw = self._main_window
        debug_controller = getattr(mw, "_debug_controller", None)
        if not debug_controller:
            return

        breakpoint = debug_controller.get_breakpoint(node_id)
        result = show_breakpoint_edit_dialog(
            parent=mw,
            node_id=node_id,
            breakpoint=breakpoint,
            debug_controller=debug_controller,
        )

        if result:
            # Remove old breakpoint and add new one with updated settings
            debug_controller.remove_breakpoint(node_id)
            debug_controller.add_breakpoint(
                node_id=result["node_id"],
                breakpoint_type=result["breakpoint_type"],
                condition=result.get("condition"),
                hit_count_target=result.get("hit_count_target", 1),
                log_message=result.get("log_message"),
            )
            panel.refresh_breakpoints()
