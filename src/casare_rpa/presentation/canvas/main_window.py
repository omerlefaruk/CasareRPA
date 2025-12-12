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
    QuickNodeManager,
)
from .coordinators import SignalCoordinator
from .managers import PanelManager
from .initializers import UIComponentInitializer, ControllerRegistrar
from loguru import logger

# Import controllers for type hints
from .controllers import SelectorController


class MainWindow(QMainWindow):
    """
    Main application window for CasareRPA.

    Provides the primary UI container with menu bar, toolbar, status bar,
    and central widget area for the node graph editor.

    Architecture:
    - SignalCoordinator: Handles all action callbacks and event routing
    - PanelManager: Manages panel visibility and layout
    - ControllerRegistrar: Initializes and wires controllers
    - UIComponentInitializer: Handles tiered component loading
    - Component managers: ActionManager, MenuBuilder, ToolbarBuilder, etc.

    Signals:
        workflow_new: Emitted when user requests new workflow
        workflow_open: Emitted when user requests to open workflow (str: file path)
        workflow_save: Emitted when user requests to save workflow
        workflow_save_as: Emitted when user requests save as (str: file path)
        workflow_run: Emitted when user requests to run workflow
        workflow_pause: Emitted when user requests to pause workflow
        workflow_resume: Emitted when user requests to resume workflow
        workflow_stop: Emitted when user requests to stop workflow
    """

    workflow_new = Signal()
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
        self._side_panel = None
        self._debug_panel: Optional["DebugPanel"] = None
        self._process_mining_panel = None
        self._robot_picker_panel = None
        self._analytics_panel = None
        self._command_palette: Optional["CommandPalette"] = None
        self._ai_assistant_panel: Optional["AIAssistantDock"] = None
        self._credentials_panel = None

        # 3-tier loading state
        self._normal_components_loaded: bool = False

        # Auto-connect feature state
        self._auto_connect_enabled: bool = True

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
        self._quick_node_manager = QuickNodeManager(self)
        self._ui_initializer = UIComponentInitializer(self)
        self._controller_registrar = ControllerRegistrar(self)

        # Coordinators and Managers (extracted from MainWindow)
        self._signal_coordinator = SignalCoordinator(self)
        self._panel_manager = PanelManager(self)

        # === CRITICAL TIER (immediate) ===
        self._setup_window()
        self._action_manager.create_actions()
        self._quick_node_manager.create_actions()
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

        self.setCorner(
            Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setCorner(
            Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.BottomDockWidgetArea
        )

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

    @Slot(str)
    def _toggle_panel_tab(self, tab_name: str) -> None:
        """Toggle bottom panel to specific tab."""
        self._panel_manager.toggle_panel_tab(tab_name)

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
        cp.register_action(self.action_toggle_minimap, "View")
        cp.register_action(self.action_run, "Run", "Execute workflow")
        cp.register_action(self.action_pause, "Run", "Pause execution")
        cp.register_action(self.action_stop, "Run", "Stop execution")
        cp.register_action(self.action_restart, "Run", "Restart workflow")
        cp.register_action(self.action_validate, "Automation", "Validate workflow")
        cp.register_action(self.action_record_workflow, "Automation", "Record actions")
        cp.register_action(
            self.action_pick_selector, "Automation", "Pick browser element"
        )
        cp.register_action(
            self.action_desktop_selector_builder, "Automation", "Pick desktop element"
        )

    # ==================== Normal Tier Loading ====================

    def _find_view_menu(self):
        """Get the View menu (stored reference or fallback search)."""
        if hasattr(self, "_view_menu") and self._view_menu is not None:
            try:
                _ = self._view_menu.title()
                return self._view_menu
            except RuntimeError:
                pass
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

    # ==================== Panel Toggle Handlers (delegated) ====================

    @Slot()
    def _on_focus_view(self) -> None:
        """Focus view: zoom to selected node and center it (F)."""
        self._signal_coordinator.on_focus_view()

    @Slot()
    def _on_home_all(self) -> None:
        """Home all: fit all nodes in view (G)."""
        self._signal_coordinator.on_home_all()

    @Slot(bool)
    def _on_toggle_minimap(self, checked: bool) -> None:
        """Handle minimap toggle."""
        self._signal_coordinator.on_toggle_minimap(checked)

    # ==================== Panel Access (delegated to PanelManager) ====================

    @property
    def bottom_panel(self) -> Optional["BottomPanelDock"]:
        return self._panel_manager.bottom_panel

    def get_bottom_panel(self) -> Optional["BottomPanelDock"]:
        return self._panel_manager.get_bottom_panel()

    @property
    def side_panel(self):
        return self._panel_manager.side_panel

    def get_side_panel(self):
        return self._panel_manager.get_side_panel()

    @property
    def validation_panel(self):
        return self._panel_manager.validation_panel

    def get_validation_panel(self):
        return self._panel_manager.get_validation_panel()

    # ==================== Panel Show/Hide (delegated) ====================

    def show_bottom_panel(self) -> None:
        self._panel_manager.show_bottom_panel()

    def hide_bottom_panel(self) -> None:
        self._panel_manager.hide_bottom_panel()

    def show_side_panel(self) -> None:
        self._panel_manager.show_side_panel()

    def hide_side_panel(self) -> None:
        self._panel_manager.hide_side_panel()

    def show_debug_tab(self) -> None:
        self._panel_manager.show_debug_tab()

    def show_analytics_tab(self) -> None:
        self._panel_manager.show_analytics_tab()

    def show_validation_panel(self) -> None:
        self._panel_manager.show_validation_panel()

    def hide_validation_panel(self) -> None:
        self._panel_manager.hide_validation_panel()

    def show_log_viewer(self) -> None:
        self._panel_manager.show_log_viewer()

    def hide_log_viewer(self) -> None:
        self._panel_manager.hide_log_viewer()

    def show_execution_history(self) -> None:
        self._panel_manager.show_execution_history()

    # ==================== Property Change Handler ====================

    @Slot(str, str, object)
    def _on_property_panel_changed(self, node_id: str, prop_name: str, value) -> None:
        self._signal_coordinator.on_property_panel_changed(node_id, prop_name, value)

    # ==================== Trigger Handlers ====================

    @Slot()
    def trigger_workflow_run(self) -> None:
        """Handle workflow run request from visual trigger node."""
        logger.debug("Trigger requested workflow run")
        self.trigger_workflow_requested.emit()

    # ==================== Navigation ====================

    @Slot(str)
    def _on_navigate_to_node(self, node_id: str) -> None:
        logger.info(f"MainWindow._on_navigate_to_node received: {node_id}")
        self._signal_coordinator.on_navigate_to_node(node_id)

    @Slot(dict)
    def _on_panel_variables_changed(self, variables: dict) -> None:
        self._signal_coordinator.on_panel_variables_changed(variables)

    def _select_node_by_id(self, node_id: str) -> None:
        self._signal_coordinator._select_node_by_id(node_id)

    # ==================== Validation ====================

    @Slot()
    def _on_validate_workflow(self) -> None:
        self._signal_coordinator.on_validate_workflow()

    @Slot(str)
    def _on_validation_issue_clicked(self, location: str) -> None:
        self._signal_coordinator.on_validation_issue_clicked(location)

    @Slot()
    def _on_repair_workflow(self) -> None:
        """Repair workflow issues detected by validation."""
        from casare_rpa.utils.id_generator import generate_node_id

        if not self._central_widget or not hasattr(self._central_widget, "graph"):
            logger.warning("Cannot repair: no graph available")
            return

        graph = self._central_widget.graph
        all_nodes = graph.all_nodes()

        node_id_to_visual_nodes = {}
        for visual_node in all_nodes:
            node_id = visual_node.get_property("node_id")
            if not node_id:
                continue
            if node_id not in node_id_to_visual_nodes:
                node_id_to_visual_nodes[node_id] = []
            node_id_to_visual_nodes[node_id].append(visual_node)

        repairs_made = 0
        for node_id, visual_nodes in node_id_to_visual_nodes.items():
            if len(visual_nodes) <= 1:
                continue

            for visual_node in visual_nodes[1:]:
                casare_node = (
                    visual_node.get_casare_node()
                    if hasattr(visual_node, "get_casare_node")
                    else None
                )

                if casare_node:
                    node_type = (
                        getattr(casare_node, "node_type", None)
                        or type(casare_node).__name__
                    )
                else:
                    node_type = node_id.rsplit("_", 1)[0] if "_" in node_id else "Node"

                new_id = generate_node_id(node_type)
                visual_node.set_property("node_id", new_id)

                if casare_node:
                    casare_node.node_id = new_id

                logger.info(
                    f"Repaired duplicate node ID: {node_id} -> {new_id} "
                    f"(node: {visual_node.name()})"
                )
                repairs_made += 1

        if repairs_made > 0:
            self.set_modified(True)
            self.statusBar().showMessage(
                f"Repaired {repairs_made} duplicate node ID(s)", 5000
            )
            self.validate_current_workflow()
        else:
            self.statusBar().showMessage("No repairs needed", 3000)

    def _check_duplicate_node_ids_on_graph(self, result: "ValidationResult") -> None:
        """Check for duplicate node_ids directly on the visual graph."""
        if not self._central_widget or not hasattr(self._central_widget, "graph"):
            return

        graph = self._central_widget.graph
        all_nodes = graph.all_nodes()

        node_id_to_nodes = {}
        for visual_node in all_nodes:
            node_id = visual_node.get_property("node_id")
            if not node_id:
                continue
            if node_id not in node_id_to_nodes:
                node_id_to_nodes[node_id] = []
            node_id_to_nodes[node_id].append(visual_node)

        for node_id, visual_nodes in node_id_to_nodes.items():
            if len(visual_nodes) <= 1:
                continue

            node_names = [n.name() for n in visual_nodes[:5]]
            names_str = ", ".join(node_names)
            if len(visual_nodes) > 5:
                names_str += f" (+{len(visual_nodes) - 5} more)"

            result.add_error(
                "DUPLICATE_NODE_ID",
                f"Duplicate node_id '{node_id}' in {len(visual_nodes)} nodes: {names_str}",
                location=f"node:{node_id}",
                suggestion="Use 'Repair' button to auto-fix duplicate IDs",
            )

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

        self._check_duplicate_node_ids_on_graph(result)

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
        return self._panel_manager.get_log_viewer()

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
    def node_controller(self):
        return getattr(self, "_node_controller", None)

    @property
    def viewport_controller(self):
        return getattr(self, "_viewport_controller", None)

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

    def get_node_controller(self):
        return self.node_controller

    def get_viewport_controller(self):
        return self.viewport_controller

    def get_project_controller(self):
        return self._project_controller

    def get_robot_controller(self):
        return self._robot_controller

    @property
    def robot_picker_panel(self):
        return self._panel_manager.robot_picker_panel

    def get_robot_picker_panel(self):
        return self._panel_manager.get_robot_picker_panel()

    @property
    def process_mining_panel(self):
        return self._panel_manager.process_mining_panel

    def get_process_mining_panel(self):
        return self._panel_manager.get_process_mining_panel()

    def get_execution_history_viewer(self):
        return self._panel_manager.get_execution_history_viewer()

    @property
    def ai_assistant_panel(self):
        return self._ai_assistant_panel

    def get_ai_assistant_panel(self):
        return self._ai_assistant_panel

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

        self._load_auto_connect_preference()

    def _load_auto_connect_preference(self) -> None:
        """Load auto-connect preference from settings and apply to graph widget."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            self._auto_connect_enabled = settings.get("canvas.auto_connect", True)

            if self._central_widget and hasattr(
                self._central_widget, "set_auto_connect_enabled"
            ):
                self._central_widget.set_auto_connect_enabled(
                    self._auto_connect_enabled
                )
                logger.debug(
                    f"Auto-connect preference loaded: {self._auto_connect_enabled}"
                )

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

        if hasattr(self, "action_save"):
            if has_workflow:
                self.action_save.setEnabled(self._workflow_controller.is_modified)
            else:
                self.action_save.setEnabled(False)
        if hasattr(self, "action_save_as"):
            self.action_save_as.setEnabled(has_workflow)

        if hasattr(self, "action_run"):
            self.action_run.setEnabled(has_execution)
        if hasattr(self, "action_pause"):
            self.action_pause.setEnabled(has_execution)
        if hasattr(self, "action_stop"):
            self.action_stop.setEnabled(has_execution)
        if hasattr(self, "action_debug"):
            self.action_debug.setEnabled(has_execution)

    # ==================== Action Handlers (delegated to SignalCoordinator) ====================

    @Slot()
    def _on_new_workflow(self) -> None:
        self._signal_coordinator.on_new_workflow()

    @Slot()
    def _on_open_workflow(self) -> None:
        self._signal_coordinator.on_open_workflow()

    @Slot()
    def _on_import_workflow(self) -> None:
        self._signal_coordinator.on_import_workflow()

    @Slot()
    def _on_export_selected(self) -> None:
        self._signal_coordinator.on_export_selected()

    @Slot()
    def _on_paste_workflow(self) -> None:
        self._signal_coordinator.on_paste_workflow()

    @Slot()
    def _on_preferences(self) -> None:
        self._signal_coordinator.on_preferences()

    @Slot()
    def _on_save_workflow(self) -> None:
        self._signal_coordinator.on_save_workflow()

    @Slot()
    def _on_save_as_workflow(self) -> None:
        self._signal_coordinator.on_save_as_workflow()

    @Slot()
    def _on_save_as_scenario(self) -> None:
        self._signal_coordinator.on_save_as_scenario()

    @Slot()
    def _on_run_workflow(self) -> None:
        self._signal_coordinator.on_run_workflow()

    @Slot()
    def _on_run_to_node(self) -> None:
        self._signal_coordinator.on_run_to_node()

    @Slot()
    def _on_run_single_node(self) -> None:
        self._signal_coordinator.on_run_single_node()

    @Slot()
    def _on_run_all_workflows(self) -> None:
        self._signal_coordinator.on_run_all_workflows()

    @Slot()
    def _on_run_local(self) -> None:
        self._signal_coordinator.on_run_local()

    @Slot()
    def _on_run_on_robot(self) -> None:
        self._signal_coordinator.on_run_on_robot()

    @Slot()
    def _on_submit(self) -> None:
        self._signal_coordinator.on_submit()

    @Slot(bool)
    def _on_pause_workflow(self, checked: bool) -> None:
        self._signal_coordinator.on_pause_workflow(checked)

    @Slot()
    def _on_stop_workflow(self) -> None:
        self._signal_coordinator.on_stop_workflow()

    @Slot()
    def _on_restart_workflow(self) -> None:
        self._signal_coordinator.on_restart_workflow()

    @Slot()
    def _on_start_listening(self) -> None:
        self._signal_coordinator.on_start_listening()

    @Slot()
    def _on_stop_listening(self) -> None:
        self._signal_coordinator.on_stop_listening()

    @Slot()
    def _on_debug_workflow(self) -> None:
        self._signal_coordinator.on_debug_workflow()

    @Slot(bool)
    def _on_debug_mode_toggled(self, enabled: bool) -> None:
        self._signal_coordinator.on_debug_mode_toggled(enabled)

    @Slot()
    def _on_debug_step_over(self) -> None:
        self._signal_coordinator.on_debug_step_over()

    @Slot()
    def _on_debug_step_into(self) -> None:
        self._signal_coordinator.on_debug_step_into()

    @Slot()
    def _on_debug_step_out(self) -> None:
        self._signal_coordinator.on_debug_step_out()

    @Slot()
    def _on_debug_continue(self) -> None:
        self._signal_coordinator.on_debug_continue()

    @Slot()
    def _on_toggle_breakpoint(self) -> None:
        self._signal_coordinator.on_toggle_breakpoint()

    @Slot()
    def _on_clear_breakpoints(self) -> None:
        self._signal_coordinator.on_clear_breakpoints()

    @Slot()
    def _on_select_nearest_node(self) -> None:
        self._signal_coordinator.on_select_nearest_node()

    @Slot()
    def _on_toggle_collapse_nearest(self) -> None:
        self._signal_coordinator.on_toggle_collapse_nearest()

    @Slot()
    def _on_toggle_disable_node(self) -> None:
        self._signal_coordinator.on_toggle_disable_node()

    @Slot()
    def _on_disable_all_selected(self) -> None:
        self._signal_coordinator.on_disable_all_selected()

    @Slot()
    def _on_rename_node(self) -> None:
        self._signal_coordinator.on_rename_node()

    @Slot(bool)
    def _on_toggle_panel(self, checked: bool) -> None:
        self._panel_manager.toggle_bottom_panel(checked)

    @Slot()
    def _on_get_exec_out(self) -> None:
        self._signal_coordinator.on_get_exec_out()

    @Slot()
    def _on_open_hotkey_manager(self) -> None:
        self._signal_coordinator.on_open_hotkey_manager()

    @Slot(bool)
    def _on_toggle_auto_connect(self, checked: bool) -> None:
        self._signal_coordinator.on_toggle_auto_connect(checked)

    @Slot(bool)
    def _on_toggle_high_performance_mode(self, checked: bool) -> None:
        self._signal_coordinator.on_toggle_high_performance_mode(checked)

    @Slot(bool)
    def _on_toggle_quick_node_mode(self, checked: bool) -> None:
        self._signal_coordinator.on_toggle_quick_node_mode(checked)

    def get_quick_node_manager(self) -> "QuickNodeManager":
        return self._quick_node_manager

    @Slot()
    def _on_open_quick_node_config(self) -> None:
        self._signal_coordinator.on_open_quick_node_config()

    @Slot()
    def _on_open_performance_dashboard(self) -> None:
        self._signal_coordinator.on_open_performance_dashboard()

    @Slot()
    def _on_open_command_palette(self) -> None:
        self._signal_coordinator.on_open_command_palette()

    @Slot()
    def _on_find_node(self) -> None:
        self._signal_coordinator.on_find_node()

    @Slot(str)
    def _on_open_recent_file(self, path: str) -> None:
        self._signal_coordinator.on_open_recent_file(path)

    @Slot()
    def _on_clear_recent_files(self) -> None:
        self._signal_coordinator.on_clear_recent_files()

    def add_to_recent_files(self, file_path) -> None:
        if self._menu_controller:
            self._menu_controller.add_recent_file(file_path)

    @Slot()
    def _on_about(self) -> None:
        self._signal_coordinator.on_about()

    @Slot()
    def _on_show_documentation(self) -> None:
        self._signal_coordinator.on_show_documentation()

    @Slot()
    def _on_show_keyboard_shortcuts(self) -> None:
        self._signal_coordinator.on_show_keyboard_shortcuts()

    @Slot()
    def _on_check_updates(self) -> None:
        self._signal_coordinator.on_check_updates()

    @Slot()
    def _on_save_ui_layout(self) -> None:
        self._signal_coordinator.on_save_ui_layout()

    @Slot()
    def _on_pick_selector(self) -> None:
        self._signal_coordinator.on_pick_selector()

    @Slot()
    def _on_pick_element(self) -> None:
        self._signal_coordinator.on_pick_element()

    @Slot()
    def _on_pick_element_desktop(self) -> None:
        self._signal_coordinator.on_pick_element_desktop()

    @Slot(bool)
    def _on_toggle_browser_recording(self, checked: bool) -> None:
        self._signal_coordinator.on_toggle_browser_recording(checked)

    @Slot()
    def _on_open_desktop_selector_builder(self) -> None:
        self._signal_coordinator.on_open_desktop_selector_builder()

    @Slot()
    def _on_create_frame(self) -> None:
        self._signal_coordinator.on_create_frame()

    def set_browser_running(self, running: bool) -> None:
        self.action_record_workflow.setEnabled(running)

    # ==================== Project Management (delegated) ====================

    @Slot()
    def _on_project_manager(self) -> None:
        self._signal_coordinator.on_project_manager()

    @Slot(str)
    def _on_project_opened(self, project_id: str) -> None:
        self._signal_coordinator.on_project_opened(project_id)

    @Slot(str)
    def _on_project_selected(self, project_id: str) -> None:
        self._signal_coordinator.on_project_selected(project_id)

    @Slot(str)
    def _on_credential_updated(self, credential_id: str) -> None:
        self._signal_coordinator.on_credential_updated(credential_id)

    @Slot()
    def _on_open_credential_manager(self) -> None:
        """Open the Credential Manager dialog."""
        self._signal_coordinator.on_open_credential_manager()

    # ==================== Fleet Dashboard ====================

    @Slot()
    def _on_fleet_dashboard(self) -> None:
        self._signal_coordinator.on_fleet_dashboard()

    @Slot(bool)
    def _on_toggle_ai_assistant(self, checked: bool) -> None:
        """Toggle AI Assistant panel visibility."""
        if self._ai_assistant_panel is None:
            # Lazy-load the AI Assistant panel
            self._ai_assistant_panel = self._dock_creator.create_ai_assistant_panel()
            # Connect signals if needed
            if hasattr(self, "_signal_coordinator"):
                # Connect workflow ready (auto-emitted after validation)
                self._ai_assistant_panel.workflow_ready.connect(
                    self._signal_coordinator.on_ai_workflow_ready
                )
                # Connect append requested (emitted when user clicks "Append to canvas")
                self._ai_assistant_panel.append_requested.connect(
                    self._signal_coordinator.on_ai_workflow_ready
                )

        if checked:
            self._ai_assistant_panel.show()
        else:
            self._ai_assistant_panel.hide()

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

        # Clean up signal coordinator (disconnect tracked signals)
        if self._signal_coordinator:
            self._signal_coordinator.cleanup()

        if self._ui_initializer:
            self._ui_initializer.cleanup()

        if self._side_panel:
            self._side_panel.cleanup()

        ComponentFactory.clear()

    def _get_message_box_style(self) -> str:
        """Get standard QMessageBox stylesheet from Theme."""
        from casare_rpa.presentation.canvas.ui.theme import Theme

        return Theme.message_box_style()

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

    # ==================== Layout and Alignment Actions ====================

    @Slot()
    def _on_auto_layout(self) -> None:
        """Handle auto-layout action."""
        self._signal_coordinator.on_auto_layout()

    @Slot()
    def _on_layout_selection(self) -> None:
        """Handle layout selection action."""
        self._signal_coordinator.on_layout_selection()

    @Slot(bool)
    def _on_toggle_grid_snap(self, checked: bool) -> None:
        """Handle toggle grid snap action."""
        self._signal_coordinator.on_toggle_grid_snap(checked)
