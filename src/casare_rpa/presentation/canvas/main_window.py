"""
Main application window for CasareRPA.

This module provides the MainWindow class which serves as the primary
GUI container for the RPA platform.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QDockWidget,
)

from ...utils.config import (
    APP_NAME,
    APP_VERSION,
    GUI_WINDOW_WIDTH,
    GUI_WINDOW_HEIGHT,
)
from .graph.minimap import Minimap
from .component_factory import ComponentFactory
from .components import (
    ActionManager,
    MenuBuilder,
    ToolbarBuilder,
    StatusBarManager,
    DockCreator,
)
from loguru import logger

# Import controllers for MVC architecture
from .controllers import (
    WorkflowController,
    ExecutionController,
    NodeController,
    ConnectionController,
    PanelController,
    MenuController,
    EventBusController,
    ViewportController,
    SchedulingController,
    UIStateController,
    SelectorController,
    ProjectController,
)


class MainWindow(QMainWindow):
    """
    Main application window for CasareRPA.

    Provides the primary UI container with menu bar, toolbar, status bar,
    and central widget area for the node graph editor.

    Signals:
        workflow_new: Emitted when user requests new workflow
        workflow_new_from_template: Emitted when user selects a template (TemplateInfo)
        workflow_open: Emitted when user requests to open workflow (str: file path)
        workflow_save: Emitted when user requests to save workflow
        workflow_save_as: Emitted when user requests save as (str: file path)
        workflow_run: Emitted when user requests to run workflow
        workflow_pause: Emitted when user requests to pause workflow
        workflow_resume: Emitted when user requests to resume workflow
        workflow_stop: Emitted when user requests to stop workflow
    """

    workflow_new = Signal()
    workflow_new_from_template = Signal(object)  # TemplateInfo
    workflow_open = Signal(str)
    workflow_save = Signal()
    workflow_save_as = Signal(str)
    workflow_import = Signal(str)
    workflow_import_json = Signal(str)
    workflow_export_selected = Signal(str)
    workflow_run = Signal()
    workflow_run_to_node = Signal(str)
    workflow_run_single_node = Signal(str)
    workflow_pause = Signal()
    workflow_resume = Signal()
    workflow_stop = Signal()
    preferences_saved = Signal()
    trigger_workflow_requested = Signal()
    save_as_scenario_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main window.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Minimap overlay
        self._minimap: Optional[Minimap] = None
        self._central_widget: Optional[QWidget] = None

        # Debug components
        self._debug_toolbar: Optional["DebugToolbar"] = None

        # Validation components
        self._validation_timer: Optional["QTimer"] = None
        self._auto_validate: bool = True
        self._workflow_data_provider: Optional[callable] = None

        # Panels and docks
        self._bottom_panel: Optional["BottomPanelDock"] = None
        self._variable_inspector_dock: Optional["VariableInspectorDock"] = None
        self._properties_panel: Optional["PropertiesPanel"] = None
        self._debug_panel: Optional["DebugPanel"] = None
        self._node_library_panel: Optional["NodeLibraryPanel"] = None
        self._command_palette: Optional["CommandPalette"] = None

        # 3-tier loading state
        self._normal_components_loaded: bool = False

        # DEFERRED tier dialogs
        self._preferences_dialog: Optional["QDialog"] = None
        self._desktop_selector_builder: Optional["QDialog"] = None
        self._performance_dashboard: Optional["QDialog"] = None

        # Controllers (MVC architecture)
        self._workflow_controller: Optional[WorkflowController] = None
        self._execution_controller: Optional[ExecutionController] = None
        self._node_controller: Optional[NodeController] = None
        self._connection_controller: Optional[ConnectionController] = None
        self._panel_controller: Optional[PanelController] = None
        self._menu_controller: Optional[MenuController] = None
        self._event_bus_controller: Optional[EventBusController] = None
        self._viewport_controller: Optional[ViewportController] = None
        self._scheduling_controller: Optional[SchedulingController] = None
        self._ui_state_controller: Optional[UIStateController] = None
        self._selector_controller: Optional[SelectorController] = None
        self._project_controller: Optional[ProjectController] = None

        # Component managers (extracted from MainWindow)
        self._action_manager = ActionManager(self)
        self._menu_builder = MenuBuilder(self)
        self._toolbar_builder = ToolbarBuilder(self)
        self._status_bar_manager = StatusBarManager(self)
        self._dock_creator = DockCreator(self)

        # === CRITICAL TIER (immediate) ===
        self._setup_window()
        self._action_manager.create_actions()
        self._menu_builder.create_menus()
        self._toolbar_builder.create_toolbar()
        self._status_bar_manager.create_status_bar()

        # Initialize controllers after critical UI
        self._init_controllers()
        self._update_actions()

        logger.debug("MainWindow: Critical tier initialization complete")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)

        from casare_rpa.presentation.canvas.theme import get_canvas_stylesheet

        self.setStyleSheet(get_canvas_stylesheet())

    # ==================== Status Bar Methods (delegated) ====================

    def update_zoom_display(self, zoom_percent: float) -> None:
        """Update the zoom level display in status bar."""
        if self._viewport_controller:
            self._viewport_controller.update_zoom_display(zoom_percent)
        else:
            self._status_bar_manager.update_zoom_display(zoom_percent)

    def update_node_count(self, count: int) -> None:
        """Update the node count display in status bar."""
        self._status_bar_manager.update_node_count(count)

    def set_execution_status(self, status: str) -> None:
        """Update execution status indicator."""
        self._status_bar_manager.set_execution_status(status)

    def _toggle_panel_tab(self, tab_name: str) -> None:
        """Toggle bottom panel to specific tab."""
        if self._panel_controller:
            self._panel_controller.toggle_panel_tab(tab_name)
            self._status_bar_manager.update_button_states()

    def _update_status_bar_buttons(self) -> None:
        """Update status bar button states."""
        self._status_bar_manager.update_button_states()

    # ==================== Command Palette ====================

    def _get_or_create_command_palette(self) -> "CommandPalette":
        """Lazy-load command palette (DEFERRED tier)."""
        if self._command_palette is None:
            from .search.command_palette import CommandPalette

            self._command_palette = ComponentFactory.get_or_create(
                "command_palette", lambda: CommandPalette(self)
            )
            self._register_command_palette_actions()
            logger.debug("Command palette lazy-loaded")

        return self._command_palette

    def _register_command_palette_actions(self) -> None:
        """Register all actions with the command palette."""
        if not self._command_palette:
            return

        cp = self._command_palette
        cp.register_action(self.action_new, "File", "Create new workflow")
        cp.register_action(self.action_open, "File", "Open existing workflow")
        cp.register_action(self.action_save, "File", "Save current workflow")
        cp.register_action(self.action_save_as, "File", "Save with new name")
        cp.register_action(self.action_undo, "Edit")
        cp.register_action(self.action_redo, "Edit")
        cp.register_action(self.action_cut, "Edit")
        cp.register_action(self.action_copy, "Edit")
        cp.register_action(self.action_paste, "Edit")
        cp.register_action(self.action_delete, "Edit")
        cp.register_action(self.action_select_all, "Edit")
        cp.register_action(self.action_find_node, "Edit")
        cp.register_action(self.action_zoom_in, "View")
        cp.register_action(self.action_zoom_out, "View")
        cp.register_action(self.action_zoom_reset, "View")
        cp.register_action(self.action_fit_view, "View")
        cp.register_action(self.action_toggle_bottom_panel, "View")
        cp.register_action(self.action_toggle_minimap, "View")
        cp.register_action(self.action_run, "Run", "Execute workflow")
        cp.register_action(self.action_pause, "Run", "Pause execution")
        cp.register_action(self.action_stop, "Run", "Stop execution")
        cp.register_action(self.action_debug, "Run", "Debug workflow")
        cp.register_action(self.action_validate, "Automation", "Validate workflow")
        cp.register_action(self.action_record_workflow, "Automation", "Record actions")
        cp.register_action(
            self.action_pick_selector, "Automation", "Pick browser element"
        )
        cp.register_action(
            self.action_desktop_selector_builder, "Automation", "Pick desktop element"
        )
        cp.register_action(self.action_schedule, "Automation", "Schedule workflow")

    # ==================== Normal Tier Loading ====================

    def _setup_validation_timer(self) -> None:
        """Setup validation timer for debounced real-time validation."""
        self._validation_timer = QTimer(self)
        self._validation_timer.setSingleShot(True)
        self._validation_timer.setInterval(500)
        self._validation_timer.timeout.connect(self._do_deferred_validation)

    def _create_debug_components(self) -> None:
        """Create debug toolbar and debug panel."""
        from .ui.toolbars.debug_toolbar import DebugToolbar

        self._debug_toolbar = DebugToolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._debug_toolbar)

        # Connect debug toolbar signals
        self._debug_toolbar.debug_mode_toggled.connect(self._on_debug_mode_toggled)
        self._debug_toolbar.step_requested.connect(self._on_debug_step_over)
        self._debug_toolbar.continue_requested.connect(self._on_debug_continue)
        self._debug_toolbar.stop_requested.connect(self._on_stop_workflow)
        self._debug_toolbar.toggle_breakpoint_requested.connect(
            self._on_toggle_breakpoint
        )
        self._debug_toolbar.clear_breakpoints_requested.connect(
            self._on_clear_breakpoints
        )

        # Create debug panel (Call Stack, Watch, Breakpoints)
        self._debug_panel = self._dock_creator.create_debug_panel()

        try:
            view_menu = self._find_view_menu()
            if view_menu:
                view_menu.addSeparator()
                view_menu.addAction(self._debug_toolbar.toggleViewAction())
        except RuntimeError:
            pass  # View menu already deleted

    def _find_view_menu(self):
        """Get the View menu (stored reference or fallback search)."""
        # Use stored reference if available
        if hasattr(self, "_view_menu") and self._view_menu is not None:
            try:
                _ = self._view_menu.title()
                return self._view_menu
            except RuntimeError:
                pass
        # Fallback: search menu bar
        for action in self.menuBar().actions():
            if action.text() == "&View":
                return action.menu()
        return None

    def ensure_normal_components_loaded(self) -> None:
        """Ensure NORMAL tier components are loaded (idempotent)."""
        if not self._normal_components_loaded:
            self._load_normal_components()

    def showEvent(self, event) -> None:
        """Handle window show event - load NORMAL tier components."""
        super().showEvent(event)
        if not self._normal_components_loaded:
            QTimer.singleShot(100, self._load_normal_components)

    def _load_normal_components(self) -> None:
        """Load NORMAL tier components after window is shown."""
        if self._normal_components_loaded:
            return

        import time

        start_time = time.perf_counter()

        logger.debug("MainWindow: Loading normal tier components...")

        # Create panels and docks via DockCreator
        self._node_library_panel = self._dock_creator.create_node_library_panel()
        self._bottom_panel = self._dock_creator.create_bottom_panel()
        self._variable_inspector_dock = (
            self._dock_creator.create_variable_inspector_dock()
        )
        self._properties_panel = self._dock_creator.create_properties_panel()
        dock, timeline = self._dock_creator.create_execution_timeline_dock()
        self._execution_timeline_dock = dock
        self._execution_timeline = timeline

        self._create_debug_components()
        self._setup_validation_timer()

        self._normal_components_loaded = True

        if self._ui_state_controller:
            self._ui_state_controller.restore_state()

        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(f"MainWindow: Normal tier components loaded in {elapsed:.2f}ms")

    # ==================== Panel Toggle Handlers ====================

    def _on_toggle_variable_inspector(self, checked: bool) -> None:
        """Handle toggle variable inspector action."""
        if self._panel_controller:
            if checked:
                self._panel_controller.show_variable_inspector()
            else:
                self._panel_controller.hide_variable_inspector()

    def _on_toggle_bottom_panel(self, checked: bool) -> None:
        """Handle bottom panel toggle."""
        if self._panel_controller:
            if checked:
                self._panel_controller.show_bottom_panel()
            else:
                self._panel_controller.hide_bottom_panel()

    def _on_toggle_properties(self, checked: bool) -> None:
        """Handle properties panel toggle."""
        if self._panel_controller:
            self._panel_controller.toggle_properties_panel(checked)

    def _on_toggle_minimap(self, checked: bool) -> None:
        """Handle minimap toggle."""
        if self._viewport_controller:
            self._viewport_controller.toggle_minimap(checked)
        elif checked:
            self.show_minimap()
        else:
            self.hide_minimap()

    # ==================== Panel Access ====================

    @property
    def bottom_panel(self) -> Optional["BottomPanelDock"]:
        return self._bottom_panel

    def get_bottom_panel(self) -> Optional["BottomPanelDock"]:
        return self.bottom_panel

    @property
    def properties_panel(self) -> Optional["PropertiesPanel"]:
        return self._properties_panel

    def get_properties_panel(self) -> Optional["PropertiesPanel"]:
        return self.properties_panel

    @property
    def execution_timeline(self) -> Optional["ExecutionTimeline"]:
        return getattr(self, "_execution_timeline", None)

    def get_execution_timeline(self) -> Optional["ExecutionTimeline"]:
        return self.execution_timeline

    @property
    def validation_panel(self):
        return self._bottom_panel.get_validation_tab() if self._bottom_panel else None

    def get_validation_panel(self):
        return self.validation_panel

    # ==================== Panel Show/Hide ====================

    def show_bottom_panel(self) -> None:
        if self._panel_controller:
            self._panel_controller.show_bottom_panel()

    def hide_bottom_panel(self) -> None:
        if self._panel_controller:
            self._panel_controller.hide_bottom_panel()

    def show_validation_panel(self) -> None:
        if self._bottom_panel:
            self._bottom_panel.show_validation_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    def hide_validation_panel(self) -> None:
        if self._bottom_panel:
            self._bottom_panel.hide()
            self.action_toggle_bottom_panel.setChecked(False)

    def show_log_viewer(self) -> None:
        if self._bottom_panel:
            self._bottom_panel.show_log_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    def hide_log_viewer(self) -> None:
        if self._bottom_panel:
            self._bottom_panel.hide()
            self.action_toggle_bottom_panel.setChecked(False)

    def show_variable_inspector(self) -> None:
        if self._panel_controller:
            self._panel_controller.show_variable_inspector()

    def show_execution_history(self) -> None:
        if self._bottom_panel:
            self._bottom_panel.show_history_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    # ==================== Properties Panel ====================

    def update_properties_panel(self, node) -> None:
        if self._properties_panel:
            self._properties_panel.set_node(node)

    def _on_property_panel_changed(self, node_id: str, prop_name: str, value) -> None:
        self.set_modified(True)
        logger.debug(f"Property changed via panel: {node_id}.{prop_name} = {value}")

        graph = self.get_graph()
        if graph:
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    casare_node = (
                        visual_node.get_casare_node()
                        if hasattr(visual_node, "get_casare_node")
                        else None
                    )
                    if casare_node and hasattr(casare_node, "config"):
                        casare_node.config[prop_name] = value
                        logger.debug(
                            f"Updated casare_node.config['{prop_name}'] = {value}"
                        )
                    break

    # ==================== Trigger Handlers ====================
    # Note: Triggers are now visual nodes on the canvas.
    # The trigger_workflow_requested signal can still be used for
    # programmatic workflow execution triggered by visual trigger nodes.

    @Slot()
    def trigger_workflow_run(self) -> None:
        """Handle workflow run request from visual trigger node."""
        logger.debug("Trigger requested workflow run")
        self.trigger_workflow_requested.emit()

    # ==================== Navigation ====================

    def _on_navigate_to_node(self, node_id: str) -> None:
        self._select_node_by_id(node_id)

    def _on_panel_variables_changed(self, variables: dict) -> None:
        self.set_modified(True)
        logger.debug(f"Variables updated: {len(variables)} variables")

    def _select_node_by_id(self, node_id: str) -> None:
        if not self._central_widget or not hasattr(self._central_widget, "graph"):
            return

        try:
            graph = self._central_widget.graph
            graph.clear_selection()
            for node in graph.all_nodes():
                if node.id() == node_id or getattr(node, "node_id", None) == node_id:
                    node.set_selected(True)
                    graph.fit_to_selection()
                    break
        except Exception as e:
            logger.debug(f"Could not select node {node_id}: {e}")

    # ==================== Validation ====================

    def _on_validate_workflow(self) -> None:
        self.validate_current_workflow()

    def _on_validation_issue_clicked(self, location: str) -> None:
        if location and location.startswith("node:"):
            self._select_node_by_id(location.split(":", 1)[1])

    def validate_current_workflow(self, show_panel: bool = True) -> "ValidationResult":
        from casare_rpa.domain.validation import validate_workflow, ValidationResult

        workflow_data = self._get_workflow_data()

        if workflow_data is None:
            result = ValidationResult()
            result.add_warning(
                "EMPTY_WORKFLOW",
                "Workflow is empty",
                suggestion="Add some nodes to the workflow",
            )
        else:
            result = validate_workflow(workflow_data)

        validation_tab = self.get_validation_panel()
        if validation_tab:
            validation_tab.set_result(result)

        if show_panel:
            self.show_validation_panel()

        if result.is_valid:
            if result.warning_count > 0:
                self.statusBar().showMessage(
                    f"Validation: {result.warning_count} warning(s)", 5000
                )
            else:
                self.statusBar().showMessage("Validation: OK", 3000)
        else:
            self.statusBar().showMessage(
                f"Validation: {result.error_count} error(s)", 5000
            )

        return result

    def _get_workflow_data(self) -> Optional[dict]:
        if self._workflow_data_provider:
            try:
                return self._workflow_data_provider()
            except Exception as e:
                logger.debug(f"Workflow data provider failed: {e}")
        return None

    def set_workflow_data_provider(self, provider: callable) -> None:
        self._workflow_data_provider = provider

    def on_workflow_changed(self) -> None:
        if self._auto_validate and self._validation_timer:
            self._validation_timer.start()

    def _do_deferred_validation(self) -> None:
        if self._bottom_panel and self._bottom_panel.isVisible():
            self.validate_current_workflow(show_panel=False)
        else:
            result = self.validate_current_workflow(show_panel=False)
            if not result.is_valid:
                self.statusBar().showMessage(
                    f"Validation: {result.error_count} error(s)", 0
                )

    def set_auto_validate(self, enabled: bool) -> None:
        self._auto_validate = enabled
        if not enabled and self._validation_timer:
            self._validation_timer.stop()

    def is_auto_validate_enabled(self) -> bool:
        return self._auto_validate

    def get_log_viewer(self):
        return self._bottom_panel.get_log_tab() if self._bottom_panel else None

    # ==================== Minimap ====================

    def _create_minimap(self, node_graph) -> None:
        if self._viewport_controller:
            self._viewport_controller.create_minimap(node_graph)
        elif self._central_widget:
            self._minimap = Minimap(node_graph, self._central_widget)
            self._minimap.setVisible(False)
            self._position_minimap()

    def _position_minimap(self) -> None:
        if self._viewport_controller:
            self._viewport_controller.position_minimap()
        elif self._minimap and self._central_widget:
            margin = 10
            x = margin
            y = self._central_widget.height() - self._minimap.height() - margin
            self._minimap.move(x, y)
            self._minimap.raise_()

    def show_minimap(self) -> None:
        if self._viewport_controller:
            self._viewport_controller.show_minimap()
        elif self._minimap:
            self._minimap.setVisible(True)
            self._position_minimap()

    def hide_minimap(self) -> None:
        if self._viewport_controller:
            self._viewport_controller.hide_minimap()
        elif self._minimap:
            self._minimap.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_minimap()

    # ==================== Component Access ====================

    @property
    def graph(self):
        return (
            self._central_widget.graph
            if self._central_widget and hasattr(self._central_widget, "graph")
            else None
        )

    @property
    def workflow_runner(self):
        return getattr(self, "_workflow_runner", None)

    @property
    def node_registry(self):
        return getattr(self, "_node_registry", None)

    @property
    def command_palette(self):
        return self._get_or_create_command_palette()

    @property
    def recent_files_menu(self):
        return getattr(self, "_recent_files_menu", None)

    @property
    def minimap(self):
        return self._minimap

    @property
    def variable_inspector_dock(self):
        return self._variable_inspector_dock

    @property
    def node_controller(self):
        return getattr(self, "_node_controller", None)

    @property
    def viewport_controller(self):
        return getattr(self, "_viewport_controller", None)

    @property
    def scheduling_controller(self):
        return getattr(self, "_scheduling_controller", None)

    # Backward-compatible getters
    def get_graph(self):
        return self.graph

    def get_workflow_runner(self):
        return self.workflow_runner

    def get_node_registry(self):
        return self.node_registry

    def get_command_palette(self):
        return self.command_palette

    def get_recent_files_menu(self):
        return self.recent_files_menu

    def get_minimap(self):
        return self.minimap

    def get_variable_inspector_dock(self):
        return self.variable_inspector_dock

    def get_node_controller(self):
        return self.node_controller

    def get_viewport_controller(self):
        return self.viewport_controller

    def get_scheduling_controller(self):
        return self.scheduling_controller

    def get_project_controller(self):
        return self._project_controller

    def get_debug_toolbar(self) -> Optional["DebugToolbar"]:
        return self._debug_toolbar if hasattr(self, "_debug_toolbar") else None

    def get_variable_inspector(self):
        return self._variable_inspector_dock

    def get_execution_history_viewer(self):
        return self._bottom_panel.get_history_tab() if self._bottom_panel else None

    def show_status(self, message: str, duration: int = 3000) -> None:
        if self.statusBar():
            self.statusBar().showMessage(message, duration)

    # ==================== Central Widget ====================

    def set_central_widget(self, widget: QWidget) -> None:
        self._central_widget = widget
        self.setCentralWidget(widget)
        if hasattr(widget, "graph"):
            self._create_minimap(widget.graph)

    # ==================== Workflow State ====================

    def set_modified(self, modified: bool) -> None:
        if self._workflow_controller:
            self._workflow_controller.set_modified(modified)
        if modified:
            self.on_workflow_changed()

    def is_modified(self) -> bool:
        return (
            self._workflow_controller.is_modified
            if self._workflow_controller
            else False
        )

    def set_current_file(self, file_path: Optional[Path]) -> None:
        if self._workflow_controller:
            self._workflow_controller.set_current_file(file_path)

    def get_current_file(self) -> Optional[Path]:
        return (
            self._workflow_controller.current_file
            if self._workflow_controller
            else None
        )

    def _update_actions(self) -> None:
        """Update action enabled states based on controller availability."""
        has_workflow = self._workflow_controller is not None
        has_execution = self._execution_controller is not None

        # File actions - enabled when workflow controller is available
        if hasattr(self, "action_save"):
            if has_workflow:
                self.action_save.setEnabled(self._workflow_controller.is_modified)
            else:
                self.action_save.setEnabled(False)
        if hasattr(self, "action_save_as"):
            self.action_save_as.setEnabled(has_workflow)

        # Execution actions - enabled when execution controller is available
        if hasattr(self, "action_run"):
            self.action_run.setEnabled(has_execution)
        if hasattr(self, "action_pause"):
            self.action_pause.setEnabled(has_execution)
        if hasattr(self, "action_stop"):
            self.action_stop.setEnabled(has_execution)
        if hasattr(self, "action_debug"):
            self.action_debug.setEnabled(has_execution)

    # ==================== Action Handlers ====================

    def _on_new_workflow(self) -> None:
        self._workflow_controller.new_workflow()

    def _on_new_from_template(self) -> None:
        self._workflow_controller.new_from_template()

    def _on_open_workflow(self) -> None:
        self._workflow_controller.open_workflow()

    def _on_import_workflow(self) -> None:
        self._workflow_controller.import_workflow()

    def _on_export_selected(self) -> None:
        self._workflow_controller.export_selected_nodes()

    def _on_paste_workflow(self) -> None:
        if self._workflow_controller:
            self._workflow_controller.paste_workflow()

    def _on_preferences(self) -> None:
        self._menu_controller.open_preferences()

    def _on_save_workflow(self) -> None:
        if self._workflow_controller:
            self._workflow_controller.save_workflow()
        else:
            logger.warning("Cannot save: workflow controller not initialized")

    def _on_save_as_workflow(self) -> None:
        if self._workflow_controller:
            self._workflow_controller.save_workflow_as()

    def _on_save_as_scenario(self) -> None:
        """Handle save as scenario action - emits signal for app.py to handle."""
        self.save_as_scenario_requested.emit()

    def _on_run_workflow(self) -> None:
        if self._execution_controller:
            self._execution_controller.run_workflow()

    def _on_run_to_node(self) -> None:
        if self._execution_controller:
            self._execution_controller.run_to_node()

    def _on_run_single_node(self) -> None:
        if self._execution_controller:
            self._execution_controller.run_single_node()

    def _on_run_local(self) -> None:
        if self._workflow_controller:
            import asyncio

            asyncio.create_task(self._workflow_controller.run_local())

    def _on_run_on_robot(self) -> None:
        if self._workflow_controller:
            import asyncio

            asyncio.create_task(self._workflow_controller.run_on_robot())

    def _on_submit(self) -> None:
        if self._workflow_controller:
            import asyncio

            asyncio.create_task(self._workflow_controller.submit_for_internet_robots())

    def _on_pause_workflow(self, checked: bool) -> None:
        if self._execution_controller:
            self._execution_controller.toggle_pause(checked)

    def _on_stop_workflow(self) -> None:
        if self._execution_controller:
            self._execution_controller.stop_workflow()

    def _on_start_listening(self) -> None:
        """Start listening for trigger events (F9)."""
        if self._execution_controller:
            self._execution_controller.start_trigger_listening()
            # Update action states
            if hasattr(self, "action_start_listening"):
                self.action_start_listening.setEnabled(False)
            if hasattr(self, "action_stop_listening"):
                self.action_stop_listening.setEnabled(True)

    def _on_stop_listening(self) -> None:
        """Stop listening for trigger events (Shift+F9)."""
        if self._execution_controller:
            self._execution_controller.stop_trigger_listening()
            # Update action states
            if hasattr(self, "action_start_listening"):
                self.action_start_listening.setEnabled(True)
            if hasattr(self, "action_stop_listening"):
                self.action_stop_listening.setEnabled(False)

    def _on_debug_workflow(self) -> None:
        if self._execution_controller:
            self._execution_controller.debug_workflow()

    def _on_debug_mode_toggled(self, enabled: bool) -> None:
        """Handle debug mode toggle."""
        if self._execution_controller:
            self._execution_controller.set_debug_mode(enabled)
        if self._debug_panel:
            if enabled:
                self._debug_panel.show()
            else:
                self._debug_panel.hide()
        logger.debug(f"Debug mode {'enabled' if enabled else 'disabled'}")

    def _on_debug_step_over(self) -> None:
        """Handle step over request in debug mode."""
        if self._execution_controller:
            self._execution_controller.step_over()

    def _on_debug_step_into(self) -> None:
        """Handle step into request in debug mode."""
        if self._execution_controller:
            self._execution_controller.step_into()

    def _on_debug_step_out(self) -> None:
        """Handle step out request in debug mode."""
        if self._execution_controller:
            self._execution_controller.step_out()

    def _on_debug_continue(self) -> None:
        """Handle continue request in debug mode."""
        if self._execution_controller:
            self._execution_controller.continue_execution()

    def _on_toggle_breakpoint(self) -> None:
        """Handle toggle breakpoint on selected node."""
        if self._node_controller:
            selected = self._node_controller.get_selected_nodes()
            if selected:
                node_id = selected[0]
                if self._execution_controller:
                    self._execution_controller.toggle_breakpoint(node_id)

    def _on_clear_breakpoints(self) -> None:
        """Handle clear all breakpoints."""
        if self._execution_controller:
            self._execution_controller.clear_breakpoints()

    def _on_node_library_create(self, node_type: str, identifier: str) -> None:
        """Handle node creation request from node library panel."""
        if self._node_controller:
            # Create node at canvas center
            self._node_controller.create_node_at_center(node_type, identifier)
            logger.debug(f"Created node from library: {node_type}")

    def _on_select_nearest_node(self) -> None:
        if self._node_controller:
            self._node_controller.select_nearest_node()

    def _on_toggle_disable_node(self) -> None:
        if self._node_controller:
            self._node_controller.toggle_disable_node()

    def _on_disable_all_selected(self) -> None:
        if self._node_controller:
            self._node_controller.disable_all_selected()

    def _on_toggle_panel(self, checked: bool) -> None:
        """Toggle bottom panel visibility (hotkey 6)."""
        if self._panel_controller:
            if checked:
                self._panel_controller.show_bottom_panel()
            else:
                self._panel_controller.hide_bottom_panel()
        elif self._bottom_panel:
            if checked:
                self._bottom_panel.show()
            else:
                self._bottom_panel.hide()

    def _on_get_exec_out(self) -> None:
        """Get nearest node's exec_out port (hotkey 3)."""
        if self._node_controller:
            self._node_controller.get_nearest_exec_out()

    def _on_open_hotkey_manager(self) -> None:
        self._menu_controller.open_hotkey_manager()

    def _on_toggle_auto_connect(self, checked: bool) -> None:
        pass

    def _on_open_performance_dashboard(self) -> None:
        self._menu_controller.open_performance_dashboard()

    def _on_open_command_palette(self) -> None:
        self._menu_controller.open_command_palette()

    def _on_find_node(self) -> None:
        if self._node_controller:
            self._node_controller.find_node()

    def _on_open_recent_file(self, path: str) -> None:
        if self._menu_controller:
            self._menu_controller.open_recent_file(path)

    def _on_clear_recent_files(self) -> None:
        if self._menu_controller:
            self._menu_controller.clear_recent_files()

    def add_to_recent_files(self, file_path) -> None:
        if self._menu_controller:
            self._menu_controller.add_recent_file(file_path)

    def _on_about(self) -> None:
        if self._menu_controller:
            self._menu_controller.show_about_dialog()

    def _on_show_documentation(self) -> None:
        if self._menu_controller:
            self._menu_controller.show_documentation()

    def _on_show_keyboard_shortcuts(self) -> None:
        if self._menu_controller:
            self._menu_controller.show_keyboard_shortcuts()

    def _on_check_updates(self) -> None:
        if self._menu_controller:
            self._menu_controller.check_for_updates()

    def _on_save_ui_layout(self) -> None:
        """Save current UI layout (window positions, panel sizes, dock states)."""
        if self._ui_state_controller:
            self._ui_state_controller.save_state()
            self.show_status("UI layout saved", 3000)
        else:
            logger.warning("Cannot save UI layout: controller not initialized")

    def _on_pick_selector(self) -> None:
        if self._selector_controller:
            import asyncio

            asyncio.create_task(self._selector_controller.start_picker())

    def _on_toggle_recording(self, checked: bool) -> None:
        if self._selector_controller:
            if checked:
                import asyncio

                asyncio.create_task(self._selector_controller.start_recording())
            else:
                self._selector_controller.stop_recording()

    def _on_open_desktop_selector_builder(self) -> None:
        if self._menu_controller:
            self._menu_controller.show_desktop_selector_builder()

    def _on_create_frame(self) -> None:
        if self._viewport_controller:
            self._viewport_controller.create_frame()

    def set_browser_running(self, running: bool) -> None:
        self.action_pick_selector.setEnabled(running)
        self.action_record_workflow.setEnabled(running)

    def _on_schedule_workflow(self) -> None:
        if self._scheduling_controller:
            self._scheduling_controller.schedule_workflow()

    def _on_manage_schedules(self) -> None:
        if self._scheduling_controller:
            self._scheduling_controller.manage_schedules()

    def _on_run_scheduled_workflow(self, schedule) -> None:
        if self._scheduling_controller:
            self._scheduling_controller.run_scheduled_workflow(schedule)

    # ==================== Project Management ====================

    def _on_project_manager(self) -> None:
        """Open the project manager dialog."""
        if self._project_controller:
            self._project_controller.show_project_manager()

    # ==================== Window Events ====================

    def closeEvent(self, event) -> None:
        if self._workflow_controller.check_unsaved_changes():
            if self._ui_state_controller:
                self._ui_state_controller.save_state()
            self._cleanup_controllers()
            event.accept()
        else:
            event.ignore()

    def _cleanup_controllers(self) -> None:
        logger.info("Cleaning up controllers...")

        controllers = [
            self._workflow_controller,
            self._execution_controller,
            self._node_controller,
            self._connection_controller,
            self._panel_controller,
            self._menu_controller,
            self._event_bus_controller,
            self._viewport_controller,
            self._scheduling_controller,
            self._ui_state_controller,
            self._project_controller,
        ]

        for controller in controllers:
            if controller:
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error(
                        f"Error cleaning up controller {controller.__class__.__name__}: {e}"
                    )

        ComponentFactory.clear()
        logger.info("Controllers cleaned up")

    # ==================== UI State ====================

    def reset_ui_state(self) -> None:
        if self._ui_state_controller:
            self._ui_state_controller.reset_state()

    def get_ui_state_controller(self) -> Optional["UIStateController"]:
        return self._ui_state_controller

    def _schedule_ui_state_save(self) -> None:
        if self._ui_state_controller:
            self._ui_state_controller.schedule_auto_save()

    # ==================== Controller Initialization ====================

    def _init_controllers(self) -> None:
        logger.info("Initializing MainWindow-specific controllers...")

        self._connection_controller = ConnectionController(self)
        self._panel_controller = PanelController(self)
        self._menu_controller = MenuController(self)
        self._event_bus_controller = EventBusController(self)
        self._viewport_controller = ViewportController(self)
        self._scheduling_controller = SchedulingController(self)
        self._ui_state_controller = UIStateController(self)
        self._project_controller = ProjectController(self)

        self._workflow_controller = None
        self._execution_controller = None
        self._node_controller = None

        self._connection_controller.initialize()
        self._panel_controller.initialize()
        self._menu_controller.initialize()
        self._event_bus_controller.initialize()
        self._viewport_controller.initialize()
        self._scheduling_controller.initialize()
        self._ui_state_controller.initialize()
        self._project_controller.initialize()

        logger.info("MainWindow-specific controllers initialized successfully")

    def set_controllers(
        self,
        workflow_controller,
        execution_controller,
        node_controller,
        selector_controller: Optional[SelectorController] = None,
    ) -> None:
        self._workflow_controller = workflow_controller
        self._execution_controller = execution_controller
        self._node_controller = node_controller
        self._selector_controller = selector_controller

        self._connect_controller_signals()
        self._update_actions()  # Re-enable actions now that controllers are set
        logger.info("Controllers injected and connected to MainWindow")

    def _connect_controller_signals(self) -> None:
        logger.debug("Connecting controller signals...")

        self._workflow_controller.workflow_created.connect(
            lambda: self.workflow_new.emit()
        )
        self._workflow_controller.workflow_loaded.connect(
            lambda path: self.workflow_open.emit(path)
        )
        self._workflow_controller.workflow_saved.connect(
            lambda path: logger.info(f"Workflow saved: {path}")
        )
        self._workflow_controller.workflow_imported.connect(
            lambda path: self.workflow_import.emit(path)
        )
        self._workflow_controller.workflow_imported_json.connect(
            lambda json_str: self.workflow_import_json.emit(json_str)
        )
        self._workflow_controller.workflow_exported.connect(
            lambda path: self.workflow_export_selected.emit(path)
        )
        self._workflow_controller.current_file_changed.connect(
            lambda file: self._on_current_file_changed(file)
        )
        self._workflow_controller.modified_changed.connect(
            lambda modified: self._on_modified_changed(modified)
        )

        self._execution_controller.execution_started.connect(
            lambda: self._on_execution_started()
        )
        self._execution_controller.execution_paused.connect(
            lambda: logger.info("Execution paused")
        )
        self._execution_controller.execution_resumed.connect(
            lambda: logger.info("Execution resumed")
        )
        self._execution_controller.execution_stopped.connect(
            lambda: self._on_execution_stopped()
        )
        self._execution_controller.execution_completed.connect(
            lambda: self._on_execution_completed()
        )
        self._execution_controller.execution_error.connect(
            lambda error: self._on_execution_error(error)
        )
        self._execution_controller.run_to_node_requested.connect(
            lambda node_id: self.workflow_run_to_node.emit(node_id)
        )
        self._execution_controller.run_single_node_requested.connect(
            lambda node_id: self.workflow_run_single_node.emit(node_id)
        )

        self._node_controller.node_selected.connect(
            lambda node_id: logger.debug(f"Node selected: {node_id}")
        )
        self._node_controller.node_deselected.connect(
            lambda node_id: logger.debug(f"Node deselected: {node_id}")
        )

        self._panel_controller.bottom_panel_toggled.connect(
            lambda visible: logger.debug(f"Bottom panel toggled: {visible}")
        )

        logger.debug("Controller signals connected")

    def _on_current_file_changed(self, file: Optional[Path]) -> None:
        pass

    def _on_modified_changed(self, modified: bool) -> None:
        pass

    def _on_execution_started(self) -> None:
        self.action_run.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(True)
        self.statusBar().showMessage("Workflow execution started...", 0)

    def _on_execution_stopped(self) -> None:
        self.action_run.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution stopped", 3000)

    def _on_execution_completed(self) -> None:
        self.action_run.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution completed", 3000)

    def _on_execution_error(self, error: str) -> None:
        self.action_run.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage(f"Execution error: {error}", 5000)
