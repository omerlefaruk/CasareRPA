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
    FleetDashboardManager,
)
from .initializers import UIComponentInitializer, ControllerRegistrar
from loguru import logger

# Import controllers for type hints
from .controllers import SelectorController


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
    workflow_run_all = Signal()  # Run all workflows concurrently (Shift+F3)
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

        # Validation components
        self._validation_timer: Optional["QTimer"] = None
        self._auto_validate: bool = True
        self._workflow_data_provider: Optional[callable] = None

        # Panels and docks
        self._bottom_panel: Optional["BottomPanelDock"] = None
        self._variable_inspector_dock: Optional["VariableInspectorDock"] = None
        self._properties_panel: Optional["PropertiesPanel"] = None
        self._debug_panel: Optional["DebugPanel"] = None
        self._process_mining_panel = None  # ProcessMiningPanel
        self._robot_picker_panel = None  # RobotPickerPanel
        self._command_palette: Optional["CommandPalette"] = None

        # 3-tier loading state
        self._normal_components_loaded: bool = False

        # Auto-connect feature state
        self._auto_connect_enabled: bool = True  # Enabled by default

        # DEFERRED tier dialogs
        self._preferences_dialog: Optional["QDialog"] = None
        self._desktop_selector_builder: Optional["QDialog"] = None
        self._performance_dashboard: Optional["QDialog"] = None
        self._fleet_dashboard_dialog: Optional["QDialog"] = None

        # Controllers (MVC architecture) - initialized by ControllerRegistrar
        self._workflow_controller = None
        self._execution_controller = None
        self._node_controller = None
        self._connection_controller = None
        self._panel_controller = None
        self._menu_controller = None
        self._event_bus_controller = None
        self._viewport_controller = None
        self._scheduling_controller = None
        self._ui_state_controller = None
        self._selector_controller: Optional[SelectorController] = None
        self._project_controller = None
        self._robot_controller = None

        # Component managers (extracted from MainWindow)
        self._action_manager = ActionManager(self)
        self._menu_builder = MenuBuilder(self)
        self._toolbar_builder = ToolbarBuilder(self)
        self._status_bar_manager = StatusBarManager(self)
        self._dock_creator = DockCreator(self)
        self._fleet_dashboard_manager = FleetDashboardManager(self)
        self._ui_initializer = UIComponentInitializer(self)
        self._controller_registrar = ControllerRegistrar(self)

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
        self._ui_initializer.ensure_normal_components_loaded()
        self._normal_components_loaded = self._ui_initializer.is_normal_loaded

    def showEvent(self, event) -> None:
        """Handle window show event - load NORMAL tier components."""
        super().showEvent(event)
        if not self._ui_initializer.is_normal_loaded:
            self._ui_initializer.schedule_deferred_load(100)

    def _load_normal_components(self) -> None:
        """Load NORMAL tier components after window is shown."""
        self._ui_initializer.load_normal_components()
        self._normal_components_loaded = self._ui_initializer.is_normal_loaded

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

    def get_robot_controller(self):
        return self._robot_controller

    @property
    def robot_picker_panel(self):
        return self._robot_picker_panel

    def get_robot_picker_panel(self):
        return self._robot_picker_panel

    @property
    def process_mining_panel(self):
        return self._process_mining_panel

    def get_process_mining_panel(self):
        return self._process_mining_panel

    def get_variable_inspector(self):
        return self._variable_inspector_dock

    def get_execution_history_viewer(self):
        return self._bottom_panel.get_history_tab() if self._bottom_panel else None

    def is_auto_connect_enabled(self) -> bool:
        """Check if auto-connect mode is enabled."""
        return self._auto_connect_enabled

    def show_status(self, message: str, duration: int = 3000) -> None:
        if self.statusBar():
            self.statusBar().showMessage(message, duration)

    # ==================== Central Widget ====================

    def set_central_widget(self, widget: QWidget) -> None:
        self._central_widget = widget
        self.setCentralWidget(widget)
        if hasattr(widget, "graph"):
            self._create_minimap(widget.graph)

        # Load and apply auto-connect preference
        self._load_auto_connect_preference()

    def _load_auto_connect_preference(self) -> None:
        """Load auto-connect preference from settings and apply to graph widget."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            # Default to True (enabled) if not set
            self._auto_connect_enabled = settings.get("canvas.auto_connect", True)

            # Apply to graph widget if available
            if self._central_widget and hasattr(
                self._central_widget, "set_auto_connect_enabled"
            ):
                self._central_widget.set_auto_connect_enabled(
                    self._auto_connect_enabled
                )
                logger.debug(
                    f"Auto-connect preference loaded: {self._auto_connect_enabled}"
                )

            # Update action state if action exists
            if hasattr(self, "action_auto_connect"):
                self.action_auto_connect.setChecked(self._auto_connect_enabled)
        except Exception as e:
            logger.debug(f"Could not load auto-connect preference: {e}")

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

    def _on_run_all_workflows(self) -> None:
        """Run all workflows on canvas concurrently (Shift+F3)."""
        if self._execution_controller:
            self._execution_controller.run_all_workflows()

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
        """
        Toggle auto-connect mode for node connections.

        When enabled, the canvas will automatically suggest connections
        when a node is dragged near compatible ports (exec ports only).
        Right-click while dragging confirms the suggested connections.

        Args:
            checked: True to enable auto-connect, False to disable
        """
        # Store setting on instance
        self._auto_connect_enabled = checked

        # Update graph widget if available
        graph_widget = self._central_widget
        if graph_widget and hasattr(graph_widget, "set_auto_connect_enabled"):
            graph_widget.set_auto_connect_enabled(checked)
            logger.debug(f"Auto-connect set on graph widget: {checked}")

        # Save preference using settings manager
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            settings.set("canvas.auto_connect", checked)
        except Exception as e:
            logger.debug(f"Could not save auto-connect preference: {e}")

        # Show status feedback
        status = "enabled" if checked else "disabled"
        self.show_status(f"Auto-connect {status}", 2000)
        logger.debug(f"Auto-connect mode: {status}")

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
            import asyncio

            if checked:
                asyncio.create_task(self._selector_controller.start_recording())
            else:
                asyncio.create_task(self._selector_controller.stop_recording())

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

    # ==================== Credential Management ====================

    def _on_credential_manager(self) -> None:
        """Open the credential manager dialog."""
        from casare_rpa.presentation.canvas.ui.dialogs import CredentialManagerDialog

        dialog = CredentialManagerDialog(self)
        dialog.credentials_changed.connect(self._on_credentials_changed)
        dialog.exec()

    def _on_credentials_changed(self) -> None:
        """Handle credential changes."""
        # Notify any components that need to refresh credential lists
        logger.info("Credentials updated")

    # ==================== Fleet Dashboard ====================

    def _on_fleet_dashboard(self) -> None:
        """Open the fleet management dashboard dialog (delegated to manager)."""
        self._fleet_dashboard_manager.open_dashboard()

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
        """Clean up all controllers via registrar."""
        self._controller_registrar.cleanup_all()

        # Cleanup UI initializer
        if self._ui_initializer:
            self._ui_initializer.cleanup()

        ComponentFactory.clear()

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
        """Initialize MainWindow-specific controllers via registrar."""
        self._controller_registrar.register_all()

    def set_controllers(
        self,
        workflow_controller,
        execution_controller,
        node_controller,
        selector_controller: Optional[SelectorController] = None,
    ) -> None:
        """Set externally created controllers (from app.py) via registrar."""
        self._controller_registrar.set_external_controllers(
            workflow_controller,
            execution_controller,
            node_controller,
            selector_controller,
        )

    # Signal handlers are now in ControllerRegistrar
