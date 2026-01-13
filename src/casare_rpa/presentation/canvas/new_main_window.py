"""
NewMainWindow v2 - Dock-Only Workspace for UX Redesign (Phase 4).

Epic 4.1: Dock-only IDE workspace with:
- Placeholder dock widgets (left, right, bottom)
- Layout persistence via QSettings
- No floating docks (dock-only enforcement)
- Corner behavior and dock nesting

Epic 8.1: Complete NewMainWindow integration with all v2 components:
- ToolbarV2 (primary actions)
- StatusBarV2 (execution status, zoom)
- MenuBarV2 (6-menu structure)
- ActionManagerV2 (centralized action/shortcut management)

See: docs/UX_REDESIGN_PLAN.md Phase 4 Epic 4.1, Epic 8.1
"""

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDockWidget, QLabel, QMainWindow, QVBoxLayout, QWidget

from casare_rpa.utils.config import APP_NAME, APP_VERSION

from .theme_system import THEME_V2, TOKENS_V2

# Type checker: NewMainWindow implements IMainWindow
if TYPE_CHECKING:
    from .interfaces import IMainWindow

    _MainWindowProtocol = IMainWindow
else:
    _MainWindowProtocol = object

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.controllers.selector_controller import (
        SelectorController,
    )
else:
    # Runtime import for selector_controller (used in type hints at runtime)
    try:
        from casare_rpa.presentation.canvas.controllers.selector_controller import (
            SelectorController,
        )
    except ImportError:
        SelectorController = None  # type: ignore

# Lazy imports for v2 search components (created on demand)
_node_search_v2 = None


def _get_node_search_v2():
    """Lazy import of NodeSearchV2."""
    global _node_search_v2
    if _node_search_v2 is None:
        from casare_rpa.presentation.canvas.ui.widgets.popups import NodeSearchV2
        _node_search_v2 = NodeSearchV2
    return _node_search_v2


def _get_signal_coordinator():
    """Lazy import of SignalCoordinator."""
    from casare_rpa.presentation.canvas.coordinators import SignalCoordinator
    return SignalCoordinator


class NewMainWindow(QMainWindow, _MainWindowProtocol):  # type: ignore[misc]
    """
    NewMainWindow v2 - Dock-only workspace implementation.

    Phase 4 (Epic 4.1): Dock-only workspace with placeholder panels.
    Future phases will populate docks with actual panels:
    - Left: Project Explorer
    - Right: Properties/Inspector
    - Bottom: Output/Logs

    Epic 8.1: Complete v2 chrome integration
    - ToolbarV2: Primary workflow actions (new, open, save, run, stop)
    - StatusBarV2: Execution status, zoom display
    - MenuBarV2: 6-menu structure (File, Edit, View, Run, Automation, Help)
    - ActionManagerV2: Centralized action and shortcut management

    Key features:
    - Dock-only (no floating) - enforced via setFeatures()
    - Layout persistence (save/restore/reset)
    - Corner behavior for bottom docks
    - Dock nesting enabled
    - THEME_V2/TOKENS_V2 styling throughout
    """

    # Settings keys for layout persistence
    _KEY_GEOMETRY = "geometry"
    _KEY_WINDOW_STATE = "windowState"
    _KEY_LAYOUT_VERSION = "layoutVersion"

    # Current layout version
    _CURRENT_LAYOUT_VERSION = 1

    # Auto-save delay for layout changes (ms)
    _AUTO_SAVE_DELAY_MS = 500

    # Workflow signals (must match MainWindow for app.py compatibility)
    workflow_new = Signal()
    workflow_open = Signal(str)
    workflow_save = Signal()
    workflow_save_as = Signal(str)
    workflow_import = Signal(str)
    workflow_import_json = Signal(str)
    workflow_export_selected = Signal(str)
    workflow_run = Signal()
    workflow_run_all = Signal()
    workflow_run_to_node = Signal(str)
    workflow_run_single_node = Signal(str)
    workflow_pause = Signal()
    workflow_resume = Signal()
    workflow_stop = Signal()
    preferences_saved = Signal()
    trigger_workflow_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the new main window (v2 dock-only workspace)."""
        super().__init__(parent)

        # Central widget storage
        self._central_widget: QWidget | None = None

        # Auto-connect state (matches action_manager_v2 auto_connect action)
        self._auto_connect_enabled: bool = True

        # Workflow data provider for validation
        self._workflow_data_provider: Callable | None = None

        # Controller stubs (will be populated in set_controllers)
        self._workflow_controller = None
        self._execution_controller = None
        self._node_controller = None
        self._selector_controller: SelectorController | None = None
        self._project_controller = None
        self._robot_controller = None

        # Dock widgets
        self._left_dock: QDockWidget | None = None
        self._right_dock: QDockWidget | None = None
        self._bottom_dock: QDockWidget | None = None

        # Chrome components (Epic 4.2, Epic 2.1, Epic 8.1)
        self._toolbar: Any | None = None
        self._status_bar: Any | None = None
        self._menu_bar: Any | None = None
        self._action_manager: Any | None = None  # Epic 8.1: ActionManagerV2
        self._signal_coordinator: Any = None

        # Search popups (Epic 5.3)
        # NOTE: Command palette removed per decision log (2025-12-30)
        self._node_search: Any | None = None

        # Layout persistence
        self._settings: QSettings | None = None
        self._auto_save_timer: QTimer | None = None
        self._pending_save: bool = False

        self._setup_window()
        self._setup_chrome()
        
        # Initialize coordinators
        SignalCoordinator = _get_signal_coordinator()
        self._signal_coordinator = SignalCoordinator(self)
        
        self._setup_docks()
        self._setup_keyboard_shortcuts()
        self._setup_layout_persistence()

        # Load recent files (Epic 8.3)
        self._load_recent_files()

        # Phase 5: Additional state
        self._current_file: Path | None = None
        self._auto_validate: bool = True
        self._validation_timer: QTimer | None = None

        logger.info("NewMainWindow v2 dock-only workspace initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} [V2 UI]")
        self.resize(1200, 800)

        # Apply v2 theme (TOKENS_V2, THEME_V2 - dark-only, compact)
        from casare_rpa.presentation.canvas.theme_system import (
            get_canvas_stylesheet_v2,
        )

        self.setStyleSheet(get_canvas_stylesheet_v2())

    def _setup_chrome(self) -> None:
        """
        Create v2 menu bar, toolbar and status bar.

        Epic 2.1: Menu Bar Integration
        - MenuBarV2 with 6-menu structure (File, Edit, View, Run, Automation, Help)

        Epic 4.2: Chrome - Top Toolbar + Status Bar v2
        - ToolbarV2 with workflow actions
        - StatusBarV2 with execution status and zoom display
        """
        from casare_rpa.presentation.canvas.ui.chrome import (
            MenuBarV2,
            StatusBarV2,
            ToolbarV2,
        )

        # Create menu bar (Epic 2.1)
        self._menu_bar = MenuBarV2(self)
        self.setMenuBar(self._menu_bar)
        self._connect_menu_signals()

        # Create toolbar
        self._toolbar = ToolbarV2(self)
        self.addToolBar(self._toolbar)
        self._connect_toolbar_signals()

        # Create status bar
        self._status_bar = StatusBarV2(self)
        self.setStatusBar(self._status_bar)

        logger.debug("NewMainWindow: v2 chrome initialized (menu, toolbar, status bar)")

    def _connect_toolbar_signals(self) -> None:
        """Connect toolbar signals to NewMainWindow workflow signals."""
        if not self._toolbar:
            return

        toolbar = self._toolbar
        toolbar.new_requested.connect(self.workflow_new.emit)
        toolbar.open_requested.connect(self.workflow_open.emit)
        toolbar.save_requested.connect(self.workflow_save.emit)
        toolbar.save_as_requested.connect(self.workflow_save_as.emit)
        toolbar.run_requested.connect(self.workflow_run.emit)
        toolbar.pause_requested.connect(self.workflow_pause.emit)
        toolbar.stop_requested.connect(self.workflow_stop.emit)
        toolbar.record_requested.connect(self._on_menu_record_workflow)
        toolbar.undo_requested.connect(self._on_undo_requested)
        toolbar.redo_requested.connect(self._on_redo_requested)

        logger.debug("NewMainWindow: toolbar signals connected")

    def _connect_menu_signals(self) -> None:
        """
        Connect menu bar signals to NewMainWindow handlers.

        Epic 2.1: Wire all menu actions to controllers/workflow signals.
        Most actions delegate to controllers; file/run actions emit signals.
        """
        if not self._menu_bar:
            return

        mb = self._menu_bar

        # File menu - connect to workflow signals
        mb.new_requested.connect(self.workflow_new.emit)
        mb.open_requested.connect(self._on_menu_open_requested)
        mb.reload_requested.connect(self._on_menu_reload)
        mb.save_requested.connect(self.workflow_save.emit)
        mb.save_as_requested.connect(self._on_menu_save_as_requested)
        mb.exit_requested.connect(self.close)
        mb.project_manager_requested.connect(self._on_menu_project_manager)

        # Edit menu - delegate to controllers
        mb.undo_requested.connect(self._on_undo_requested)
        mb.redo_requested.connect(self._on_redo_requested)
        mb.cut_requested.connect(self._on_menu_cut)
        mb.copy_requested.connect(self._on_menu_copy)
        mb.paste_requested.connect(self._on_menu_paste)
        mb.duplicate_requested.connect(self._on_menu_duplicate)
        mb.delete_requested.connect(self._on_menu_delete)
        mb.select_all_requested.connect(self._on_menu_select_all)
        mb.find_node_requested.connect(self._on_menu_find_node)
        mb.rename_node_requested.connect(self._on_menu_rename_node)
        mb.auto_layout_requested.connect(self._on_menu_auto_layout)
        mb.layout_selection_requested.connect(self._on_menu_layout_selection)
        mb.toggle_grid_snap_requested.connect(self._on_menu_toggle_grid_snap)

        # View menu - delegate to view/controller methods
        mb.toggle_panel_requested.connect(self._on_menu_toggle_panel)
        mb.toggle_side_panel_requested.connect(self._on_menu_toggle_side_panel)
        mb.toggle_minimap_requested.connect(self._on_menu_toggle_minimap)
        mb.high_performance_mode_requested.connect(
            self._on_menu_high_performance_mode
        )
        mb.fleet_dashboard_requested.connect(self._on_menu_fleet_dashboard)
        mb.performance_dashboard_requested.connect(
            self._on_menu_performance_dashboard
        )
        mb.credential_manager_requested.connect(self._on_menu_credential_manager)
        mb.save_layout_requested.connect(self.save_layout)
        mb.reset_layout_requested.connect(self.reset_layout)

        # Run menu - connect to workflow signals
        mb.run_requested.connect(self.workflow_run.emit)
        mb.run_all_requested.connect(self.workflow_run_all.emit)
        mb.pause_requested.connect(self.workflow_pause.emit)
        mb.stop_requested.connect(self.workflow_stop.emit)
        mb.restart_requested.connect(self._on_menu_restart)
        mb.run_to_node_requested.connect(self._on_menu_run_to_node)
        mb.run_single_node_requested.connect(self._on_menu_run_single_node)
        mb.start_listening_requested.connect(self._on_menu_start_listening)
        mb.stop_listening_requested.connect(self._on_menu_stop_listening)

        # Automation menu - delegate to automation tools
        mb.validate_requested.connect(self._on_menu_validate)
        mb.record_workflow_requested.connect(self._on_menu_record_workflow)
        mb.pick_selector_requested.connect(self._on_menu_pick_selector)
        mb.pick_desktop_selector_requested.connect(self._on_menu_pick_desktop_selector)
        mb.create_frame_requested.connect(self._on_menu_create_frame)
        mb.toggle_auto_connect_requested.connect(self._on_menu_toggle_auto_connect)
        mb.quick_node_mode_requested.connect(self._on_menu_quick_node_mode)
        mb.quick_node_config_requested.connect(self._on_menu_quick_node_config)

        # Help menu - delegate to help dialogs
        mb.documentation_requested.connect(self._on_menu_documentation)
        mb.keyboard_shortcuts_requested.connect(self._on_menu_keyboard_shortcuts)
        mb.preferences_requested.connect(self._on_menu_preferences)
        mb.check_updates_requested.connect(self._on_menu_check_updates)
        mb.about_requested.connect(self._on_menu_about)

        logger.debug("NewMainWindow: menu signals connected")

    @Slot()
    def _on_undo_requested(self) -> None:
        """Handle undo request from toolbar/menu."""
        # Emit undo on workflow controller if available
        if self._workflow_controller and hasattr(self._workflow_controller, "undo"):
            self._workflow_controller.undo()

    @Slot()
    def _on_redo_requested(self) -> None:
        """Handle redo request from toolbar/menu."""
        # Emit redo on workflow controller if available
        if self._workflow_controller and hasattr(self._workflow_controller, "redo"):
            self._workflow_controller.redo()

    # ==================== Menu Slot Handlers (Epic 2.1) ====================
    # These handlers are called from menu actions when controllers are available

    @Slot()
    def _on_menu_reload(self) -> None:
        """Handle reload from menu."""
        if self._workflow_controller:
            self._workflow_controller.reload()

    @Slot()
    def _on_menu_project_manager(self) -> None:
        """Handle project manager from menu."""
        if self._project_controller:
            # Open project manager dialog
            self.show_status("Project manager - coming soon")

    @Slot(str)
    def _on_menu_open_requested(self, file_path: str) -> None:
        """
        Handle open workflow request from menu.

        Epic 8.3: Receives file path from recent files menu or open dialog.
        Empty string triggers file dialog; actual path opens directly.

        Args:
            file_path: Path to workflow file (empty string shows dialog)
        """
        if not file_path:
            # Show file dialog
            from PySide6.QtWidgets import QFileDialog

            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Workflow",
                "",
                "Workflow Files (*.json);;All Files (*)",
            )
            if path:
                self.workflow_open.emit(path)
        else:
            # Direct open from recent files
            self.workflow_open.emit(file_path)

    @Slot(str)
    def _on_menu_save_as_requested(self, file_path: str) -> None:
        """
        Handle save as request from menu.

        Args:
            file_path: Path to save to (empty string shows dialog)
        """
        if not file_path:
            from PySide6.QtWidgets import QFileDialog

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Workflow As",
                "",
                "Workflow Files (*.json);;All Files (*)",
            )
            if path:
                self.workflow_save_as.emit(path)
        else:
            self.workflow_save_as.emit(file_path)

    @Slot()
    def _on_menu_cut(self) -> None:
        """Handle cut from menu."""
        if self._node_controller:
            self._node_controller.cut_selected()

    @Slot()
    def _on_menu_copy(self) -> None:
        """Handle copy from menu."""
        if self._node_controller:
            self._node_controller.copy_selected()

    @Slot()
    def _on_menu_paste(self) -> None:
        """Handle paste from menu."""
        if self._node_controller:
            self._node_controller.paste()

    @Slot()
    def _on_menu_duplicate(self) -> None:
        """Handle duplicate from menu."""
        if self._node_controller:
            self._node_controller.duplicate_selected()

    @Slot()
    def _on_menu_delete(self) -> None:
        """Handle delete from menu."""
        if self._node_controller:
            self._node_controller.delete_selected()

    @Slot()
    def _on_menu_select_all(self) -> None:
        """Handle select all from menu."""
        graph = self.get_graph()
        if graph:
            graph.select_all_nodes()

    @Slot()
    def _on_menu_find_node(self) -> None:
        """Handle find node from menu."""
        # TODO: Implement find node dialog
        self.show_status("Find node - coming soon")

    @Slot()
    def _on_menu_rename_node(self) -> None:
        """Handle rename node from menu."""
        if self._node_controller:
            self._node_controller.rename_selected()

    @Slot()
    def _on_menu_auto_layout(self) -> None:
        """Handle auto layout from menu."""
        graph = self.get_graph()
        if graph and hasattr(graph, "auto_layout"):
            graph.auto_layout()

    @Slot()
    def _on_menu_layout_selection(self) -> None:
        """Handle layout selection from menu."""
        graph = self.get_graph()
        if graph and hasattr(graph, "layout_selection"):
            graph.layout_selection()

    @Slot()
    def _on_menu_toggle_grid_snap(self, checked: bool) -> None:
        """Handle toggle grid snap from menu."""
        graph = self.get_graph()
        if graph and hasattr(graph, "set_grid_snap_enabled"):
            graph.set_grid_snap_enabled(checked)

    @Slot()
    def _on_menu_toggle_panel(self, checked: bool) -> None:
        """Handle toggle panel from menu."""
        if self._bottom_dock:
            self._bottom_dock.setVisible(checked)

    @Slot()
    def _on_menu_toggle_side_panel(self, checked: bool) -> None:
        """Handle toggle side panel from menu."""
        if self._right_dock:
            self._right_dock.setVisible(checked)

    @Slot()
    def _on_menu_toggle_minimap(self, checked: bool) -> None:
        """Handle toggle minimap from menu."""
        # TODO: Implement minimap toggle
        self.show_status("Minimap - coming soon")

    @Slot()
    def _on_menu_high_performance_mode(self, checked: bool) -> None:
        """Handle high performance mode from menu."""
        graph = self.get_graph()
        if graph and hasattr(graph, "set_high_performance_mode"):
            graph.set_high_performance_mode(checked)

    @Slot()
    def _on_menu_fleet_dashboard(self) -> None:
        """Handle fleet dashboard from menu."""
        self.show_status("Fleet dashboard - coming soon")

    @Slot()
    def _on_menu_performance_dashboard(self) -> None:
        """Handle performance dashboard from menu."""
        self.show_status("Performance dashboard - coming soon")

    @Slot()
    def _on_menu_credential_manager(self) -> None:
        """Handle credential manager from menu."""
        self.show_status("Credential manager - coming soon")

    @Slot()
    def _on_menu_restart(self) -> None:
        """Handle restart from menu."""
        if self._execution_controller:
            self._execution_controller.restart_workflow()

    @Slot()
    def _on_menu_run_to_node(self) -> None:
        """Handle run to node from menu."""
        if self._execution_controller:
            self._execution_controller.run_to_selected_node()

    @Slot()
    def _on_menu_run_single_node(self) -> None:
        """Handle run single node from menu."""
        if self._execution_controller:
            self._execution_controller.run_selected_node()

    @Slot()
    def _on_menu_start_listening(self) -> None:
        """Handle start listening from menu."""
        if self._execution_controller:
            self._execution_controller.start_listening()

    @Slot()
    def _on_menu_stop_listening(self) -> None:
        """Handle stop listening from menu."""
        if self._execution_controller:
            self._execution_controller.stop_listening()

    @Slot()
    def _on_menu_validate(self) -> None:
        """Handle validate from menu."""
        self.validate_current_workflow()

    @Slot(bool)
    def _on_menu_record_workflow(self, checked: bool) -> None:
        """Handle record workflow from menu."""
        if self._signal_coordinator:
            self._signal_coordinator.on_toggle_browser_recording(checked)
        else:
            self.show_status("Browser recording - signal coordinator not ready")

    @Slot()
    def _on_menu_pick_selector(self) -> None:
        """Handle pick selector from menu."""
        if self._selector_controller:
            self._selector_controller.pick_element()

    @Slot()
    def _on_menu_pick_desktop_selector(self) -> None:
        """Handle pick desktop selector from menu."""
        if self._selector_controller:
            self._selector_controller.pick_desktop_element()

    @Slot()
    def _on_menu_create_frame(self) -> None:
        """Handle create frame from menu."""
        graph = self.get_graph()
        if graph and hasattr(graph, "create_frame_from_selection"):
            graph.create_frame_from_selection()

    @Slot()
    def _on_menu_toggle_auto_connect(self, checked: bool) -> None:
        """Handle toggle auto connect from menu."""
        # Store auto-connect state
        self._auto_connect_enabled = checked
        self.show_status(f"Auto-connect: {'enabled' if checked else 'disabled'}")

    @Slot()
    def _on_menu_quick_node_mode(self, checked: bool) -> None:
        """Handle quick node mode from menu."""
        self.show_status(f"Quick node mode: {'enabled' if checked else 'disabled'}")

    @Slot()
    def _on_menu_quick_node_config(self) -> None:
        """Handle quick node config from menu."""
        self.show_status("Quick node config - coming soon")

    @Slot()
    def _on_menu_documentation(self) -> None:
        """Handle documentation from menu."""
        import webbrowser

        webbrowser.open("https://casarerpa.com/docs")

    @Slot()
    def _on_menu_keyboard_shortcuts(self) -> None:
        """Handle keyboard shortcuts from menu."""
        self.show_status("Keyboard shortcuts - coming soon")

    @Slot()
    def _on_menu_preferences(self) -> None:
        """Handle preferences from menu."""
        self.show_status("Preferences - coming soon")

    @Slot()
    def _on_menu_check_updates(self) -> None:
        """Handle check updates from menu."""
        self.show_status("Check updates - coming soon")

    @Slot()
    def _on_menu_about(self) -> None:
        """Handle about from menu."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "About CasareRPA",
            f"{APP_NAME}\nVersion: {APP_VERSION}\n\nV2 UI - Dock-only workspace",
        )

    def _setup_docks(self) -> None:
        """
        Create dock-only layout with real functional panels.

        Populates:
        - Left: Project Explorer (v2)
        - Right: Properties/Inspector (v2)
        - Bottom: Output/Logs/Variables (v2)

        Docks are configured as dock-only (no floating) via setFeatures().
        """
        from casare_rpa.presentation.canvas.ui.panels import (
            BottomPanelDock,
            ProjectExplorerPanel,
            PropertiesPanel,
            SidePanelDock,
        )

        # Enable dock nesting for complex layouts
        self.setDockNestingEnabled(True)

        # Force bottom docks to use bottom corners (prevents odd layouts)
        self.setCorner(
            Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setCorner(
            Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.BottomDockWidgetArea
        )

        # 1. Left Dock: Project Explorer
        self._project_explorer = ProjectExplorerPanel(self)
        self._project_explorer.setObjectName("leftDock")
        self._project_explorer.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._project_explorer)
        self._left_dock = self._project_explorer

        # 2. Right Dock: Properties
        self._properties_panel = PropertiesPanel(self)
        self._properties_panel.setObjectName("rightDock")
        self._properties_panel.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._properties_panel)
        self._right_dock = self._properties_panel

        # 3. Bottom Dock: Tabbed Panel (Variables, Output, Log, etc.)
        self._bottom_panel = BottomPanelDock(self)
        self._bottom_panel.setObjectName("bottomDock")
        self._bottom_panel.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._bottom_panel)
        self._bottom_dock = self._bottom_panel

        # 4. Side Panel (Debug, Analytics, etc.) - Tabified with Properties
        self._side_panel = SidePanelDock(self)
        self._side_panel.setObjectName("sideDock")
        self._side_panel.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._side_panel)
        self.tabifyDockWidget(self._properties_panel, self._side_panel)

        # Set initial visibility (all hidden per default, except maybe Project Explorer)
        self._project_explorer.setVisible(False)
        self._properties_panel.setVisible(False)
        self._bottom_panel.setVisible(False)
        self._side_panel.setVisible(False)

        # Connect state changes to auto-save
        for dock in [self._left_dock, self._right_dock, self._bottom_dock, self._side_panel]:
            dock.dockLocationChanged.connect(self._schedule_layout_save)
            dock.visibilityChanged.connect(self._schedule_layout_save)

        # Wire up panel signals
        self._wire_panel_signals()

        logger.debug("NewMainWindow: functional dock widgets created")

    def _wire_panel_signals(self) -> None:
        """Connect panel signals to window/controller handlers."""
        # Project Explorer
        self._project_explorer.project_opened.connect(self.workflow_open.emit)
        self._project_explorer.project_selected.connect(self._on_project_selected)

        # Properties Panel
        self._properties_panel.property_changed.connect(self._on_property_edited)

        # Bottom Panel
        self._bottom_panel.navigate_to_node.connect(self._on_navigate_to_node)
        self._bottom_panel.variables_changed.connect(self._on_variables_changed)

    @Slot(str)
    def _on_project_selected(self, project_id: str) -> None:
        """Handle project selection in explorer."""
        logger.debug(f"Project selected: {project_id}")
        # Could update window title or status
        # self.show_status(f"Project: {project_id}")

    @Slot(str, dict)
    def _on_property_edited(self, node_id: str, new_properties: dict[str, Any]) -> None:
        """Handle property edits from the PropertiesPanel."""
        logger.debug(f"Property edited for node {node_id}: {new_properties}")
        if self._node_controller:
            # Delegate to node controller to apply changes and create undo command
            self._node_controller.update_node_properties(node_id, new_properties)
            self.set_modified(True)

    @Slot(str)
    def _on_navigate_to_node(self, node_id: str) -> None:
        """Navigate and center view on a specific node."""
        logger.debug(f"Navigating to node: {node_id}")
        graph = self.get_graph()
        if graph:
            node = graph.get_node_by_id(node_id)
            if node:
                graph.center_on([node])
                graph.select_node(node)

    @Slot(list)
    def _on_variables_changed(self, variables: list[dict[str, Any]]) -> None:
        """Handle variable changes from the bottom panel."""
        logger.debug(f"Variables changed: {len(variables)} variables")
        # TODO: Implement variable synchronization via WorkflowController
        # For now, just mark modified
        self.set_modified(True)

    @Slot(str)
    def _on_node_selected(self, node_id: str) -> None:
        """Handle node selection - update properties panel."""
        logger.debug(f"Node selected: {node_id}")
        
        graph = self.get_graph()
        if not graph:
            return
            
        # Find node in graph
        all_nodes = graph.all_nodes()
        target_node = None
        for node in all_nodes:
            if node.get_property("node_id") == node_id:
                target_node = node
                break
                
        if target_node:
            # Extract properties
            props = {}
            # Get all properties from visual node
            for key in target_node.properties().keys():
                props[key] = target_node.get_property(key)
                
            # Update panel
            if hasattr(self, "_properties_panel") and self._properties_panel:
                self._properties_panel.set_node_properties(node_id, props)
                
            # If side panel profiling tab exists, highlight entry
            if hasattr(self, "_side_panel") and self._side_panel:
                profiling = self._side_panel.get_profiling_tab()
                if profiling and hasattr(profiling, "select_entry"):
                    profiling.select_entry(node_id)

    @Slot(str)
    def _on_node_deselected(self, node_id: str) -> None:
        """Handle node deselection."""
        logger.debug(f"Node deselected: {node_id}")
        if hasattr(self, "_properties_panel") and self._properties_panel:
            self._properties_panel.clear()

    def _setup_keyboard_shortcuts(self) -> None:
        """
        Setup keyboard shortcuts for v2 search popups.

        Epic 5.3: NodeSearchV2 keyboard binding:
        - Ctrl+F: Node Search

        NOTE: Command palette (Ctrl+Shift+P) removed per decision log (2025-12-30)
        """
        # Ctrl+F: Node Search
        self._node_search_shortcut = QShortcut(
            QKeySequence("Ctrl+F"),
            self,
            partial(self._show_node_search),
            context=Qt.ShortcutContext.WidgetShortcut,
        )

        logger.debug("NewMainWindow: keyboard shortcut configured (Ctrl+F)")

    # ==================== Search Popups (Epic 5.3) ====================
    # NOTE: Command palette removed per decision log (2025-12-30)

    @Slot()
    def _show_node_search(self) -> None:
        """Show the node search popup."""
        NodeSearchV2 = _get_node_search_v2()

        # Get graph instance
        graph = self.get_graph()
        if graph is None:
            self.show_status("No graph available for node search")
            return

        if self._node_search is None:
            self._node_search = NodeSearchV2(graph=graph, parent=self)
            # Connect signal to focus selected node
            self._node_search.node_selected.connect(self._on_node_search_selected)

        self._node_search.show_search()

    @Slot(str)
    def _on_node_search_selected(self, node_id: str) -> None:
        """Handle node selection from search popup."""
        logger.debug(f"Node search selected: {node_id}")
        # Node is already centered by the popup itself



    def _trigger_open_dialog(self) -> None:
        """Trigger open file dialog."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Workflow",
            "",
            "Workflow Files (*.json);;All Files (*)",
        )
        if file_path:
            self.workflow_open.emit(file_path)

    def _setup_layout_persistence(self) -> None:
        """Setup QSettings and timer for layout auto-save."""
        self._settings = QSettings("CasareRPA", "CanvasV2")

        # Create auto-save timer (debounced)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._on_auto_save_timeout)

        logger.debug("NewMainWindow: layout persistence initialized")

    @Slot()
    def _on_auto_save_timeout(self) -> None:
        """Handle auto-save timer timeout."""
        if self._pending_save:
            self.save_layout()

    @Slot()
    def _schedule_layout_save(self) -> None:
        """
        Schedule an automatic layout save.

        Uses debouncing to avoid excessive saves when multiple
        dock state changes occur in quick succession.
        """
        if self._auto_save_timer:
            self._pending_save = True
            self._auto_save_timer.start(self._AUTO_SAVE_DELAY_MS)

    # ==================== Layout Persistence ====================

    def save_layout(self) -> None:
        """
        Save window geometry and dock state to QSettings.

        Persists:
        - Window geometry (size, position)
        - Window state (dock positions, sizes, visibility)
        - Layout version (for compatibility)
        """
        if not self._settings:
            logger.warning("Cannot save layout: settings not initialized")
            return

        try:
            self._settings.setValue(self._KEY_GEOMETRY, self.saveGeometry())
            self._settings.setValue(self._KEY_WINDOW_STATE, self.saveState())
            self._settings.setValue(self._KEY_LAYOUT_VERSION, self._CURRENT_LAYOUT_VERSION)
            self._settings.sync()

            self._pending_save = False
            logger.debug("Layout saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save layout: {e}")

    def restore_layout(self) -> None:
        """
        Restore window geometry and dock state from QSettings.

        Handles version compatibility and falls back to defaults
        if saved state is invalid or version mismatch.
        """
        if not self._settings:
            logger.warning("Cannot restore layout: settings not initialized")
            return

        try:
            # Check version compatibility
            saved_version = self._settings.value(self._KEY_LAYOUT_VERSION, 0, type=int)
            if saved_version != self._CURRENT_LAYOUT_VERSION:
                logger.info(
                    f"Layout version mismatch ({saved_version} vs "
                    f"{self._CURRENT_LAYOUT_VERSION}), using defaults"
                )
                return

            # Restore geometry
            geometry = self._settings.value(self._KEY_GEOMETRY)
            if geometry:
                self.restoreGeometry(geometry)

            # Restore window state (docks, toolbars, etc.)
            state = self._settings.value(self._KEY_WINDOW_STATE)
            if state:
                if not self.restoreState(state):
                    logger.warning("Failed to restore window state, using defaults")
                    return

            logger.debug("Layout restored from previous session")
        except Exception as e:
            logger.warning(f"Failed to restore layout: {e}")

    def reset_layout(self) -> None:
        """
        Reset to default layout.

        Clears all saved layout settings and restores
        dock widgets to their default positions and visibility.
        """
        if not self._settings:
            logger.warning("Cannot reset layout: settings not initialized")
            return

        try:
            # Clear settings
            self._settings.remove(self._KEY_GEOMETRY)
            self._settings.remove(self._KEY_WINDOW_STATE)
            self._settings.remove(self._KEY_LAYOUT_VERSION)
            self._settings.sync()

            # Reset dock widgets to default state (all hidden)
            if self._left_dock:
                self._left_dock.setVisible(False)
            if self._right_dock:
                self._right_dock.setVisible(False)
            if self._bottom_dock:
                self._bottom_dock.setVisible(False)

            # Re-setup default dock arrangement
            self._setup_docks()

            logger.info("Layout reset to defaults")
        except Exception as e:
            logger.warning(f"Failed to reset layout: {e}")

    # ==================== Required Interface Methods ====================
    # These methods are called by app.py and must exist to avoid crashes

    def set_central_widget(self, widget: QWidget) -> None:
        """Set the node graph widget as central widget."""
        self._central_widget = widget
        self.setCentralWidget(widget)
        logger.debug("NewMainWindow: central widget set")

    def set_controllers(
        self,
        workflow_controller: Any,
        execution_controller: Any,
        node_controller: Any,
        project_controller: Any | None = None,
        robot_controller: Any | None = None,
        selector_controller: "SelectorController | None" = None,
        preferences_controller: Any | None = None,
    ) -> None:
        """Store controller references and wire cross-controller signals."""
        self._workflow_controller = workflow_controller
        self._execution_controller = execution_controller
        self._node_controller = node_controller
        self._project_controller = project_controller
        self._robot_controller = robot_controller
        self._selector_controller = selector_controller
        self._preferences_controller = preferences_controller

        # Wire node controller signals
        if self._node_controller:
            self._node_controller.node_selected.connect(self._on_node_selected)
            self._node_controller.node_deselected.connect(self._on_node_deselected)

        logger.debug("NewMainWindow: controllers stored and wired")

    def set_workflow_data_provider(self, provider: Callable) -> None:
        """Store workflow data provider for validation (stub for Phase 4)."""
        self._workflow_data_provider = provider

    def set_modified(self, modified: bool) -> None:
        """Track workflow modified state."""
        self._modified = modified
        if self._current_file:
            modified_marker = "*" if modified else ""
            self.setWindowTitle(f"{APP_NAME} - {self._current_file.name}{modified_marker} [V2 UI]")
        
        if modified and self._workflow_controller:
            self._workflow_controller.set_modified(True)

    def is_modified(self) -> bool:
        """Check if the workflow has been modified."""
        return getattr(self, "_modified", False)

    def show_status(self, message: str, duration: int = 3000) -> None:
        """Show status message."""
        if self._status_bar:
            self._status_bar.show_message(f"[V2] {message}", duration)
        logger.debug(f"NewMainWindow status: {message}")

    def get_project_controller(self) -> Any:
        """Return project controller (stub for Phase 4)."""
        return self._project_controller

    def get_robot_controller(self) -> Any:
        """Return robot controller (stub for Phase 4)."""
        return self._robot_controller

    # ==================== Required Methods for Controllers ====================
    # These methods are called by WorkflowController and other controllers

    def get_graph(self) -> Any:
        """
        Return the node graph instance.

        Returns the graph from the central widget (NodeGraphWidget.graph).
        The NodeGraphWidget is set as central widget by app.py.
        """
        if self._central_widget and hasattr(self._central_widget, "graph"):
            return self._central_widget.graph
        return None

    def get_bottom_panel(self) -> Any:
        """Return the bottom panel instance."""
        return self._bottom_panel

    def get_log_viewer(self) -> Any:
        """Return the log viewer widget from bottom panel."""
        return self._bottom_panel.get_log_tab() if self._bottom_panel else None

    def get_current_file(self) -> Path | None:
        """
        Return the current workflow file path.
        """
        return self._current_file

    def set_current_file(self, file_path: Path | str | None) -> None:
        """
        Set the current workflow file path.
        """
        if file_path is None:
            self._current_file = None
        else:
            from pathlib import Path
            self._current_file = Path(file_path)
            # Update window title
            self.setWindowTitle(f"{APP_NAME} - {self._current_file.name} [V2 UI]")

    # ==================== Recent Files (Epic 8.3) ====================

    def add_to_recent_files(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Epic 8.3: Integrates RecentFilesManager with MenuBarV2.
        - Persists to disk via RecentFilesManager
        - Updates MenuBarV2 recent files menu

        Args:
            file_path: Path to add to recent files
        """
        from pathlib import Path

        from casare_rpa.application.workflow import get_recent_files_manager

        try:
            path = Path(file_path)
            # Add to persistent storage
            manager = get_recent_files_manager()
            manager.add_file(path)

            # Update menu bar
            if self._menu_bar and hasattr(self._menu_bar, "add_recent_file"):
                self._menu_bar.add_recent_file(file_path)

            logger.debug(f"Added to recent files: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to add to recent files: {e}")

    def _load_recent_files(self) -> None:
        """
        Load recent files from storage and populate menu bar.

        Epic 8.3: Called during initialization to populate the recent files menu.
        """
        from casare_rpa.application.workflow import get_recent_files_manager

        try:
            manager = get_recent_files_manager()
            recent = manager.get_recent_files()

            # Extract file paths (manager returns dicts with 'path' key)
            file_paths = [f["path"] for f in recent]

            # Update menu bar
            if self._menu_bar and hasattr(self._menu_bar, "set_recent_files"):
                self._menu_bar.set_recent_files(file_paths)

            logger.debug(f"Loaded {len(file_paths)} recent files")
        except Exception as e:
            logger.warning(f"Failed to load recent files: {e}")

    def validate_current_workflow(
        self, show_panel: bool = True
    ) -> tuple[bool, list[str]]:
        """
        Validate the current workflow.
        """
        from casare_rpa.domain.validation import validate_workflow

        workflow_data = self._get_workflow_data()
        if workflow_data is None:
            return False, ["Workflow is empty"]

        result = validate_workflow(workflow_data)

        # Update validation tab in bottom panel if it exists
        if self._bottom_panel:
            # BottomPanelDock has a validation tab (accessible via get_validation_tab)
            validation_tab = self._bottom_panel.get_validation_tab()
            if validation_tab:
                validation_tab.set_result(result)

        if show_panel and self._bottom_panel:
            self._bottom_panel.show_validation()

        # Format return for protocol
        errors = [err.message for err in result.errors]
        return result.is_valid, errors

    def _get_workflow_data(self) -> dict | None:
        """
        Get serialized workflow data via provider.
        """
        if self._workflow_data_provider:
            try:
                return self._workflow_data_provider()
            except Exception as e:
                logger.debug(f"Workflow data provider failed: {e}")
        return None

    # ==================== Chrome Proxy Methods (Epic 4.2) ====================
    # Proxy methods for toolbar and status bar access

    def set_execution_state(self, is_running: bool, is_paused: bool = False) -> None:
        """
        Update toolbar based on execution state.

        Args:
            is_running: Whether workflow is currently executing
            is_paused: Whether workflow is paused
        """
        if self._toolbar:
            self._toolbar.set_execution_state(is_running, is_paused)

    def set_execution_status(self, status: str) -> None:
        """
        Update status bar execution status.

        Args:
            status: One of 'ready', 'running', 'paused', 'error', 'success'
        """
        if self._status_bar:
            self._status_bar.set_execution_status(status)

    def set_undo_enabled(self, enabled: bool) -> None:
        """
        Set undo action enabled state.

        Args:
            enabled: Whether undo is available
        """
        if self._toolbar:
            self._toolbar.set_undo_enabled(enabled)
        # TODO: Update menu bar action state too

    def set_redo_enabled(self, enabled: bool) -> None:
        """
        Set redo action enabled state.

        Args:
            enabled: Whether redo is available
        """
        if self._toolbar:
            self._toolbar.set_redo_enabled(enabled)
        # TODO: Update menu bar action state too

    def update_zoom(self, zoom_percent: float) -> None:
        """
        Update zoom display.

        Args:
            zoom_percent: Current zoom percentage (e.g., 100.0 for 100%)
        """
        if self._status_bar:
            self._status_bar.set_zoom(zoom_percent)

    # ==================== Stub Action Properties ====================
    # These are accessed by app.py for signal connections

    @property
    def action_undo(self) -> Any:
        """Stub undo action for signal connection."""
        return self._create_stub_action("undo")

    @property
    def action_redo(self) -> Any:
        """Stub redo action for signal connection."""
        return self._create_stub_action("redo")

    @property
    def action_delete(self) -> Any:
        """Stub delete action for signal connection."""
        return self._create_stub_action("delete")

    @property
    def action_cut(self) -> Any:
        """Stub cut action for signal connection."""
        return self._create_stub_action("cut")

    @property
    def action_copy(self) -> Any:
        """Stub copy action for signal connection."""
        return self._create_stub_action("copy")

    @property
    def action_paste(self) -> Any:
        """Stub paste action for signal connection."""
        return self._create_stub_action("paste")

    @property
    def action_duplicate(self) -> Any:
        """Stub duplicate action for signal connection."""
        return self._create_stub_action("duplicate")

    @property
    def action_select_all(self) -> Any:
        """Stub select_all action for signal connection."""
        return self._create_stub_action("select_all")

    @property
    def action_save(self) -> Any:
        """Stub save action for signal connection."""
        return self._create_stub_action("save")

    @property
    def action_save_as(self) -> Any:
        """Stub save_as action for signal connection."""
        return self._create_stub_action("save_as")

    @property
    def action_run(self) -> Any:
        """Stub run action for signal connection."""
        return self._create_stub_action("run")

    @property
    def action_stop(self) -> Any:
        """Stub stop action for signal connection."""
        return self._create_stub_action("stop")

    @property
    def action_pause(self) -> Any:
        """Stub pause action for signal connection."""
        return self._create_stub_action("pause")

    # ==================== Missing IMainWindow Protocol Methods ====================
    # Stub implementations for type safety with IMainWindow protocol

    def set_current_file(self, file_path: str) -> None:
        """Set the current workflow file path (stub for Phase 4)."""
        pass

    def show_side_panel(self, index: int = 0) -> None:
        """Show the side panel (stub for Phase 4)."""
        pass

    def show_minimap(self, visible: bool = True) -> None:
        """Show the graph minimap (stub for Phase 4)."""
        pass

    def show_debug_tab(self, index: int = 0) -> None:
        """Show the debug tab in bottom panel (stub for Phase 4)."""
        pass

    def show_analytics_tab(self, index: int = 0) -> None:
        """Show the analytics tab in bottom panel (stub for Phase 4)."""
        pass

    def show_execution_history(self) -> None:
        """Show the execution history panel (stub for Phase 4)."""
        pass

    def show_validation_panel(self) -> None:
        """Show the validation panel (stub for Phase 4)."""
        pass

    def show_bottom_panel(self) -> None:
        """Show the bottom panel (stub for Phase 4)."""
        pass

    def show_log_viewer(self) -> None:
        """Show the log viewer panel (stub for Phase 4)."""
        pass

    def set_browser_running(self, running: bool) -> None:
        """Update browser running state indicator."""
        # Toolbar has recording action that could be enabled/disabled
        if self._toolbar:
            self._toolbar.set_recording_enabled(running)

    def get_side_panel(self) -> Any:
        """Return the side panel widget."""
        return self._side_panel

    def get_minimap(self) -> Any:
        """Return the minimap widget (stub for Phase 4)."""
        return None

    def get_node_controller(self) -> Any:
        """Return the node controller (stub for Phase 4)."""
        return self._node_controller

    def get_viewport_controller(self) -> Any:
        """Return the viewport controller (stub for Phase 4)."""
        return None

    def get_ui_state_controller(self) -> Any:
        """Return the UI state controller (stub for Phase 4)."""
        return None

    def get_workflow_data(self) -> dict | None:
        """Return serialized workflow data (stub for Phase 4)."""
        return self._get_workflow_data()

    def set_auto_validate(self, enabled: bool) -> None:
        """Enable/disable automatic workflow validation (stub for Phase 4)."""
        pass

    def get_workflow_runner(self) -> Any:
        """Return the workflow runner instance (stub for Phase 4)."""
        return None

    def get_node_registry(self) -> dict:
        """Return the node registry."""
        if self._node_controller:
            return self._node_controller.get_registry()
        return {}

    def get_recent_files_menu(self) -> Any:
        """
        Return the recent files menu.

        Epic 8.3: Returns MenuBarV2's recent files menu for controller access.
        """
        if self._menu_bar and hasattr(self._menu_bar, "get_recent_files_menu"):
            return self._menu_bar.get_recent_files_menu()
        return None

    def get_ai_assistant_panel(self) -> Any:
        """Return the AI assistant panel."""
        # TODO: Implement AI assistant panel in V2
        return None

    def get_robot_picker_panel(self) -> Any:
        """Return the robot picker panel."""
        return None

    def get_process_mining_panel(self) -> Any:
        """Return the process mining panel."""
        return None

    def get_execution_history_viewer(self) -> Any:
        """Return the execution history viewer."""
        return None

    def get_validation_panel(self) -> Any:
        """Return the validation tab from bottom panel."""
        return self._bottom_panel.get_validation_tab() if self._bottom_panel else None

    def get_robot_controller(self) -> Any:
        """Return the robot controller."""
        return self._robot_controller

    def get_viewport_controller(self) -> Any:
        """Return the viewport controller."""
        return None

    def get_ui_state_controller(self) -> Any:
        """Return the UI state controller."""
        return None

    def is_modified(self) -> bool:
        """Check if the workflow has been modified (stub for Phase 4)."""
        return False

    def is_auto_connect_enabled(self) -> bool:
        """Check if auto-connect is enabled."""
        return self._auto_connect_enabled

    def _create_stub_action(self, name: str) -> Any:
        """Create a stub action object with triggered signal."""
        from PySide6.QtCore import QObject

        class StubAction(QObject):
            triggered = Signal()

            def __init__(self, action_name: str):
                super().__init__()
                self._name = action_name

            def setEnabled(self, enabled: bool):
                pass  # Stub

        if not hasattr(self, f"_stub_action_{name}"):
            setattr(self, f"_stub_action_{name}", StubAction(name))
        return getattr(self, f"_stub_action_{name}")

    # ==================== Variables & Preferences Access ====================
    # Epic 4.4: Interface-compliant accessors for serialization

    def get_variables(self) -> dict[str, Any]:
        """
        Get workflow variables from the bottom panel.

        Returns:
            Dict mapping variable name to variable data.
        """
        if hasattr(self, "_bottom_panel") and self._bottom_panel:
            return self._bottom_panel.get_variables()
        return {}

    def set_variables(self, variables: dict[str, Any]) -> None:
        """
        Set workflow variables in the bottom panel.

        Args:
            variables: Dict of variables to set.
        """
        if hasattr(self, "_bottom_panel") and self._bottom_panel:
            self._bottom_panel.set_variables(variables)
            logger.debug(f"Variables set in bottom panel: {len(variables)}")

    def get_preferences(self) -> dict[str, Any]:
        """
        Get application preferences from the preferences controller.

        Returns:
            Preferences dictionary.
        """
        if hasattr(self, "_preferences_controller") and self._preferences_controller:
            return self._preferences_controller.get_settings()
        return {}

    # ==================== Window Close Event ====================

    def closeEvent(self, event: Any) -> None:
        """Handle window close - save layout before closing."""
        # Save layout before closing
        if self._pending_save:
            self.save_layout()
        else:
            # Final save on close
            self.save_layout()

        if self._signal_coordinator:
            self._signal_coordinator.cleanup()

        event.accept()
        logger.info("NewMainWindow v2 closed")
