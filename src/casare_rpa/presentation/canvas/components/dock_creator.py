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
    from ..ui.panels.node_library_panel import NodeLibraryPanel
    from ..ui.widgets.execution_timeline import ExecutionTimeline
    from ..ui.debug_panel import DebugPanel
    from ..debugger.debug_controller import DebugController


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

    def create_node_library_panel(self) -> "NodeLibraryPanel":
        """
        Create the Node Library Panel for browsing and adding nodes.

        Features:
        - Tree view of all nodes organized by category
        - Search/filter functionality
        - Drag-and-drop to canvas
        - Double-click to create at center

        Returns:
            Created NodeLibraryPanel instance
        """
        from ..ui.panels.node_library_panel import NodeLibraryPanel

        mw = self._main_window
        node_library = NodeLibraryPanel(mw)

        # Connect signals
        node_library.node_requested.connect(mw._on_node_library_create)

        # Add to main window (left side)
        mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, node_library)

        # Connect dock state changes to auto-save
        node_library.dockLocationChanged.connect(mw._schedule_ui_state_save)
        node_library.visibilityChanged.connect(mw._schedule_ui_state_save)
        node_library.topLevelChanged.connect(mw._schedule_ui_state_save)

        # Add toggle action to View menu
        try:
            view_menu = self._find_view_menu()
            if view_menu:
                toggle_action = node_library.toggleViewAction()
                toggle_action.setText("&Node Library")
                toggle_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
                view_menu.addAction(toggle_action)
                mw.action_toggle_node_library = toggle_action
        except RuntimeError as e:
            logger.warning(f"Could not add Node Library to View menu: {e}")

        # Initially visible
        node_library.show()

        logger.info("Node Library Panel created")
        return node_library

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
