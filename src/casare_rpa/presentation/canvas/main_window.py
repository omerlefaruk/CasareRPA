"""
Main application window for CasareRPA.

This module provides the MainWindow class which serves as the primary
GUI container for the RPA platform.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QTextEdit,
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

        # === CRITICAL TIER (immediate) ===
        self._setup_window()
        self._action_manager.create_actions()
        self._quick_node_manager.create_actions()  # Hotkey-based node creation
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

    def _on_toggle_bottom_panel(self, checked: bool) -> None:
        """Handle bottom panel toggle."""
        if self._panel_controller:
            if checked:
                self._panel_controller.show_bottom_panel()
            else:
                self._panel_controller.hide_bottom_panel()

    def _on_focus_view(self) -> None:
        """Focus view: zoom to selected node and center it (F)."""
        if self._is_text_widget_focused():
            return
        if self._viewport_controller:
            self._viewport_controller.focus_view()

    def _on_home_all(self) -> None:
        """Home all: fit all nodes in view (G)."""
        if self._is_text_widget_focused():
            return
        if self._viewport_controller:
            self._viewport_controller.home_all()

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

    def show_execution_history(self) -> None:
        if self._bottom_panel:
            self._bottom_panel.show_history_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    # ==================== Property Change Handler ====================

    def _on_property_panel_changed(self, node_id: str, prop_name: str, value) -> None:
        self.set_modified(True)

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

    def _on_repair_workflow(self) -> None:
        """
        Repair workflow issues detected by validation.

        Currently handles:
        - DUPLICATE_NODE_ID: Regenerates unique IDs for duplicate nodes
        """
        from casare_rpa.utils.id_generator import generate_node_id

        if not self._central_widget or not hasattr(self._central_widget, "graph"):
            logger.warning("Cannot repair: no graph available")
            return

        graph = self._central_widget.graph
        all_nodes = graph.all_nodes()

        # Build mapping of node_id -> list of visual nodes with that ID
        node_id_to_visual_nodes = {}
        for visual_node in all_nodes:
            node_id = visual_node.get_property("node_id")
            if not node_id:
                continue
            if node_id not in node_id_to_visual_nodes:
                node_id_to_visual_nodes[node_id] = []
            node_id_to_visual_nodes[node_id].append(visual_node)

        # Find and fix duplicates
        repairs_made = 0
        for node_id, visual_nodes in node_id_to_visual_nodes.items():
            if len(visual_nodes) <= 1:
                continue  # Not a duplicate

            # Keep the first node with its ID, regenerate IDs for the rest
            for visual_node in visual_nodes[1:]:
                # Get casare_node if available
                casare_node = (
                    visual_node.get_casare_node()
                    if hasattr(visual_node, "get_casare_node")
                    else None
                )

                # Determine node type for ID generation
                if casare_node:
                    node_type = (
                        getattr(casare_node, "node_type", None)
                        or type(casare_node).__name__
                    )
                else:
                    # Try to extract from node_id (e.g., "TypeTextNode_abc123" -> "TypeTextNode")
                    node_type = node_id.rsplit("_", 1)[0] if "_" in node_id else "Node"

                # Generate new unique ID
                new_id = generate_node_id(node_type)

                # Update visual node property
                visual_node.set_property("node_id", new_id)

                # Update casare_node if it exists
                if casare_node:
                    casare_node.node_id = new_id

                logger.info(
                    f"Repaired duplicate node ID: {node_id} -> {new_id} "
                    f"(node: {visual_node.name()})"
                )
                repairs_made += 1

        # Show result
        if repairs_made > 0:
            self.set_modified(True)
            self.statusBar().showMessage(
                f"Repaired {repairs_made} duplicate node ID(s)", 5000
            )
            # Re-run validation to show the fix worked
            self.validate_current_workflow()
        else:
            self.statusBar().showMessage("No repairs needed", 3000)

    def _check_duplicate_node_ids_on_graph(self, result: "ValidationResult") -> None:
        """
        Check for duplicate node_ids directly on the visual graph.

        This is necessary because the WorkflowSerializer uses node_id as dict keys,
        so duplicate node_ids would overwrite each other and not be visible
        in the serialized workflow data.

        Args:
            result: ValidationResult to add issues to
        """
        if not self._central_widget or not hasattr(self._central_widget, "graph"):
            return

        graph = self._central_widget.graph
        all_nodes = graph.all_nodes()

        # Build mapping of node_id -> list of visual nodes with that ID
        node_id_to_nodes = {}
        for visual_node in all_nodes:
            node_id = visual_node.get_property("node_id")
            if not node_id:
                continue
            if node_id not in node_id_to_nodes:
                node_id_to_nodes[node_id] = []
            node_id_to_nodes[node_id].append(visual_node)

        # Find and report duplicates
        for node_id, visual_nodes in node_id_to_nodes.items():
            if len(visual_nodes) <= 1:
                continue  # Not a duplicate

            # Get node names for error message
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

        # CRITICAL: Check for duplicate node_ids directly on the visual graph
        # The serializer uses node_id as dict key, so duplicates get overwritten
        # and would be invisible to the standard validation
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
    def node_controller(self):
        return getattr(self, "_node_controller", None)

    @property
    def viewport_controller(self):
        return getattr(self, "_viewport_controller", None)

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
        return self._robot_picker_panel

    def get_robot_picker_panel(self):
        return self._robot_picker_panel

    @property
    def process_mining_panel(self):
        return self._process_mining_panel

    def get_process_mining_panel(self):
        return self._process_mining_panel

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

    def _on_migrate_workflow(self) -> None:
        """Handle migrate workflow action - opens migration dialog."""
        if not self._workflow_controller:
            logger.warning("Cannot migrate: workflow controller not initialized")
            return

        # Get current workflow's version history
        version_history = self._workflow_controller.get_version_history()
        if not version_history:
            from PySide6.QtWidgets import QMessageBox

            msg = QMessageBox(self)
            msg.setWindowTitle("Migration Not Available")
            msg.setText("This workflow has no version history.")
            msg.setInformativeText(
                "Save the workflow first to create an initial version."
            )
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStyleSheet(self._get_message_box_style())
            msg.exec()
            return

        # Check if there are enough versions
        versions = version_history.list_versions()
        if len(versions) < 2:
            from PySide6.QtWidgets import QMessageBox

            msg = QMessageBox(self)
            msg.setWindowTitle("Migration Not Available")
            msg.setText("Migration requires at least 2 versions.")
            msg.setInformativeText(f"Current workflow has {len(versions)} version(s).")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStyleSheet(self._get_message_box_style())
            msg.exec()
            return

        # Show migration dialog
        from casare_rpa.presentation.canvas.ui.dialogs import show_migration_dialog

        result = show_migration_dialog(version_history, self)
        if result and result.success and result.migrated_data:
            logger.info(
                f"Migration completed: {result.from_version} → {result.to_version}"
            )
            # Optionally reload the workflow with migrated data
            # self._workflow_controller.reload_from_data(result.migrated_data)

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

    def _is_text_widget_focused(self) -> bool:
        """Check if a text input widget has focus (for numpad shortcut suppression)."""
        focus_widget = QApplication.focusWidget()
        return isinstance(focus_widget, (QLineEdit, QTextEdit))

    def _on_select_nearest_node(self) -> None:
        if self._is_text_widget_focused():
            return
        if self._node_controller:
            self._node_controller.select_nearest_node()

    def _on_toggle_collapse_nearest(self) -> None:
        """Toggle collapse/expand on nearest node (hotkey 1)."""
        if self._is_text_widget_focused():
            return
        if self._node_controller:
            self._node_controller.toggle_collapse_nearest_node()

    def _on_toggle_disable_node(self) -> None:
        if self._is_text_widget_focused():
            return
        if self._node_controller:
            self._node_controller.toggle_disable_node()

    def _on_disable_all_selected(self) -> None:
        if self._is_text_widget_focused():
            return
        if self._node_controller:
            self._node_controller.disable_all_selected()

    def _on_rename_node(self) -> None:
        """Rename selected node (F2)."""
        if self._is_text_widget_focused():
            return
        graph = self.graph
        if not graph:
            return
        selected = graph.selected_nodes()
        if not selected:
            self.show_status("No node selected", 2000)
            return
        node = selected[0]
        current_name = node.name() if hasattr(node, "name") else "Node"
        from PySide6.QtWidgets import QInputDialog

        new_name, ok = QInputDialog.getText(
            self, "Rename Node", "Enter new name:", text=current_name
        )
        if ok and new_name and new_name != current_name:
            node.set_name(new_name)
            self.show_status(f"Renamed to: {new_name}", 2000)

    def _on_toggle_panel(self, checked: bool) -> None:
        """Toggle bottom panel visibility (hotkey 6)."""
        if self._is_text_widget_focused():
            return
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
        if self._is_text_widget_focused():
            return
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

    def _on_toggle_quick_node_mode(self, checked: bool) -> None:
        """
        Toggle quick node creation mode.

        When enabled, single letter hotkeys create nodes at cursor position.
        For example: 'b' creates Launch Browser, 'c' creates Click Element.

        Args:
            checked: True to enable quick node mode, False to disable
        """
        if self._quick_node_manager:
            self._quick_node_manager.set_enabled(checked)

        # Save preference
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            settings.set("canvas.quick_node_mode", checked)
        except Exception as e:
            logger.debug(f"Could not save quick node mode preference: {e}")

        # Show status feedback
        status = "enabled" if checked else "disabled"
        self.show_status(
            f"Quick node mode {status} (press letter keys to create nodes)", 2500
        )
        logger.debug(f"Quick node mode: {status}")

    def get_quick_node_manager(self) -> "QuickNodeManager":
        """Get the quick node manager instance."""
        return self._quick_node_manager

    def _on_open_quick_node_config(self) -> None:
        """Open the Quick Node Hotkey Configuration dialog."""
        from .ui.dialogs import QuickNodeConfigDialog

        dialog = QuickNodeConfigDialog(self._quick_node_manager, self)
        dialog.exec()

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
        """Legacy handler - delegates to unified picker."""
        self._on_pick_element()

    def _on_pick_element(self) -> None:
        """Show unified element selector dialog (browser mode by default)."""
        if self._selector_controller:
            self._selector_controller.show_unified_selector_dialog(
                target_node=None,
                target_property="selector",
                initial_mode="browser",
            )

    def _on_pick_element_desktop(self) -> None:
        """Show unified element selector dialog with desktop mode."""
        if self._selector_controller:
            self._selector_controller.show_unified_selector_dialog(
                target_node=None,
                target_property="selector",
                initial_mode="desktop",
            )

    def _on_toggle_browser_recording(self, checked: bool) -> None:
        """Toggle browser recording mode using BrowserRecorder."""
        import asyncio

        if checked:
            asyncio.create_task(self._start_browser_recording())
        else:
            asyncio.create_task(self._stop_browser_recording())

    async def _start_browser_recording(self) -> None:
        """Start recording browser interactions."""
        try:
            # Get browser page from selector controller (set when browser launches)
            page = None
            if self._selector_controller:
                page = self._selector_controller.get_browser_page()

            if not page:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Recording Error",
                    "No browser page available. Please run a workflow with Open Browser first.",
                )
                self.action_record_workflow.setChecked(False)
                return

            # Create recorder
            from casare_rpa.infrastructure.browser import BrowserRecorder

            self._browser_recorder = BrowserRecorder(page)

            # Set callback for when Escape is pressed in browser
            def on_stop_from_browser():
                # Schedule stop on Qt main thread
                from PySide6.QtCore import QTimer

                QTimer.singleShot(0, self._on_recording_stop_requested)

            self._browser_recorder.set_callbacks(
                on_recording_stopped=on_stop_from_browser
            )

            await self._browser_recorder.start_recording()

            # Show recording panel if available
            self._show_recording_panel()

            logger.info("Browser recording started")

        except Exception as e:
            logger.error(f"Failed to start browser recording: {e}")
            self.action_record_workflow.setChecked(False)

    def _on_recording_stop_requested(self) -> None:
        """Handle stop request from browser (Escape pressed)."""
        # Guard against double calls
        if getattr(self, "_recording_stop_in_progress", False):
            return
        self._recording_stop_in_progress = True

        logger.info("Recording stop requested from browser")
        # Uncheck button visually and directly call stop handler
        self.action_record_workflow.blockSignals(True)
        self.action_record_workflow.setChecked(False)
        self.action_record_workflow.blockSignals(False)
        # Directly call the toggle handler
        self._on_toggle_browser_recording(False)

    async def _stop_browser_recording(self) -> None:
        """Stop browser recording and convert to workflow."""
        try:
            if not hasattr(self, "_browser_recorder") or not self._browser_recorder:
                return

            # Grab recorder and clear immediately to prevent double calls
            recorder = self._browser_recorder
            self._browser_recorder = None

            actions = await recorder.stop_recording()

            if actions:
                # Convert to workflow nodes
                from casare_rpa.infrastructure.browser import BrowserWorkflowGenerator

                workflow_data = BrowserWorkflowGenerator.generate_workflow_data(actions)
                nodes = workflow_data.get("nodes", [])

                if nodes:
                    # Show review dialog
                    from casare_rpa.presentation.canvas.ui.dialogs import (
                        RecordingReviewDialog,
                    )

                    dialog = RecordingReviewDialog(nodes, parent=self)
                    dialog.accepted_with_data.connect(
                        self._on_recording_review_accepted
                    )
                    dialog.exec()

            logger.info(f"Recording stopped: {len(actions) if actions else 0} actions")

        except Exception as e:
            logger.error(f"Failed to stop browser recording: {e}")
        finally:
            # Reset the stop guard flag
            self._recording_stop_in_progress = False

    def _show_recording_panel(self) -> None:
        """Show the browser recording panel."""
        # Recording panel can be shown as a dock widget
        # For now, just log - panel integration is optional
        logger.debug("Recording panel: recording in progress...")

    def _on_recording_review_accepted(
        self, nodes_data: list, include_waits: bool
    ) -> None:
        """Handle accepted recording review - create nodes on canvas."""
        if not nodes_data:
            return

        # Build final nodes list, optionally inserting Wait nodes
        final_nodes = []
        connections = []

        for i, node in enumerate(nodes_data):
            node_id = node.get("id", f"action_{i+1}")
            final_nodes.append(node)

            # Add wait node after each action (except last) if enabled
            if include_waits and i < len(nodes_data) - 1:
                # Wait time stored in config.wait_after by the dialog
                wait_time = node.get("config", {}).get("wait_after", 500)
                if wait_time > 0:
                    wait_id = f"wait_{i+1}"
                    final_nodes.append(
                        {
                            "id": wait_id,
                            "type": "WaitNode",
                            "name": f"Wait {wait_time}ms",
                            "config": {"duration": wait_time},
                        }
                    )
                    # Connect action -> wait
                    connections.append(
                        {
                            "from_node": node_id,
                            "from_port": "exec_out",
                            "to_node": wait_id,
                            "to_port": "exec_in",
                        }
                    )
                    # Next action connects from wait
                    next_node = nodes_data[i + 1]
                    next_id = next_node.get("id", f"action_{i+2}")
                    connections.append(
                        {
                            "from_node": wait_id,
                            "from_port": "exec_out",
                            "to_node": next_id,
                            "to_port": "exec_in",
                        }
                    )
            elif i < len(nodes_data) - 1:
                # Direct connection without wait
                next_node = nodes_data[i + 1]
                next_id = next_node.get("id", f"action_{i+2}")
                connections.append(
                    {
                        "from_node": node_id,
                        "from_port": "exec_out",
                        "to_node": next_id,
                        "to_port": "exec_in",
                    }
                )

        workflow_data = {"nodes": final_nodes, "connections": connections}
        self._create_workflow_from_recording(workflow_data)

    def _create_workflow_from_recording(self, workflow_data: dict) -> None:
        """Add recorded browser actions to canvas, connected to Launch Browser."""
        graph = self.get_graph()
        if not graph:
            return

        NODE_TYPE_MAP = {
            "ClickElementNode": "casare_rpa.interaction.VisualClickElementNode",
            "TypeTextNode": "casare_rpa.interaction.VisualTypeTextNode",
            "PressEnterNode": "casare_rpa.interaction.VisualTypeTextNode",  # Uses TypeText with press_enter_after
            "SelectDropdownNode": "casare_rpa.interaction.VisualSelectDropdownNode",
            "SelectOptionNode": "casare_rpa.interaction.VisualSelectDropdownNode",
            "CheckboxNode": "casare_rpa.desktop.VisualCheckCheckboxNode",
            "SendHotKeyNode": "casare_rpa.desktop.VisualSendHotKeyNode",
            "WaitNode": "casare_rpa.wait.VisualWaitNode",
        }

        nodes_data = workflow_data.get("nodes", [])
        connections_data = workflow_data.get("connections", [])
        if not nodes_data:
            return

        # Find Launch Browser node to position after and connect to
        launch_browser_node = None
        start_x, start_y = 500, 200
        for node in graph.all_nodes():
            if "LaunchBrowser" in node.type_ or "Launch Browser" in node.name():
                launch_browser_node = node
                pos = node.pos()
                start_x = pos[0] + 400  # Start after Launch Browser
                start_y = pos[1]
                break

        created_nodes = {}
        current_x = start_x
        first_node = None
        NODE_SPACING = 450  # ~350px node width + 100px gap

        # Create nodes
        for node_data in nodes_data:
            node_type = node_data.get("type")
            visual_type = NODE_TYPE_MAP.get(node_type)
            if not visual_type:
                continue

            node = graph.create_node(visual_type, pos=[current_x, start_y])
            if node:
                created_nodes[node_data["id"]] = node
                if first_node is None:
                    first_node = node
                # Apply config
                for key, value in node_data.get("config", {}).items():
                    try:
                        node.set_property(key, value)
                    except Exception:
                        pass
                # Special handling for PressEnter
                if node_type == "PressEnterNode":
                    try:
                        node.set_property("text", "")
                        node.set_property("press_enter_after", True)
                    except Exception:
                        pass
                current_x += NODE_SPACING

        # Connect to Launch Browser first
        if launch_browser_node and first_node:
            try:
                # Connect exec
                lb_exec = launch_browser_node.get_output("exec_out")
                first_exec = first_node.get_input("exec_in")
                if lb_exec and first_exec:
                    lb_exec.connect_to(first_exec)
                # Connect page
                lb_page = launch_browser_node.get_output("page")
                first_page = first_node.get_input("page")
                if lb_page and first_page:
                    lb_page.connect_to(first_page)
            except Exception:
                pass

        # Connect recorded nodes to each other
        for conn in connections_data:
            from_node = created_nodes.get(conn.get("from_node"))
            to_node = created_nodes.get(conn.get("to_node"))
            if from_node and to_node:
                try:
                    out_port = from_node.get_output(conn.get("from_port", "exec_out"))
                    in_port = to_node.get_input(conn.get("to_port", "exec_in"))
                    if out_port and in_port:
                        out_port.connect_to(in_port)
                except Exception:
                    pass

        # Select and center
        if created_nodes:
            graph.clear_selection()
            for node in created_nodes.values():
                node.set_selected(True)
            if hasattr(graph, "fit_to_selection"):
                graph.fit_to_selection()
            logger.info(f"Added {len(created_nodes)} nodes")

    def _on_open_desktop_selector_builder(self) -> None:
        """Legacy handler - delegates to unified picker desktop tab."""
        self._on_pick_element_desktop()

    def _on_create_frame(self) -> None:
        if self._viewport_controller:
            self._viewport_controller.create_frame()

    def set_browser_running(self, running: bool) -> None:
        # Unified picker always enabled (works for desktop, OCR, image too)
        # Only browser tab and recording need browser running
        self.action_record_workflow.setEnabled(running)

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

    def _get_message_box_style(self) -> str:
        """Get standard QMessageBox stylesheet matching UI Explorer."""
        return """
            QMessageBox {
                background: #252526;
            }
            QMessageBox QLabel {
                color: #D4D4D4;
                font-size: 12px;
            }
            QPushButton {
                background: #2D2D30;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 0 16px;
                color: #D4D4D4;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #2A2D2E;
                border-color: #007ACC;
                color: white;
            }
            QPushButton:default {
                background: #007ACC;
                border-color: #007ACC;
                color: white;
            }
            QPushButton:default:hover {
                background: #1177BB;
            }
        """

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
