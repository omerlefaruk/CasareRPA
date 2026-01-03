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
- MenuBarV2 (standard menus)
- ActionManagerV2 (centralized action/shortcut management)

See: docs/UX_REDESIGN_PLAN.md Phase 4 Epic 4.1, Epic 8.1
"""

import importlib
import os
import subprocess
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import (
    QFileSystemWatcher,
    QPointF,
    QSettings,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget

from casare_rpa.utils.config import APP_NAME, APP_VERSION

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
    - MenuBarV2: standard menu structure (File, Edit, View, Run, Tools, Help)
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

        # Quick Node hotkeys (single-key node creation on canvas)
        from casare_rpa.presentation.canvas.managers import QuickNodeManager

        self._quick_node_manager = QuickNodeManager()

        # Central widget storage
        self._central_widget: QWidget | None = None
        self._minimap_panel: Any | None = None

        # Qt actions expected by app.py/controllers (undo/copy/paste/etc.)
        self._qt_actions: dict[str, QAction] = {}
        self._setup_qt_actions()

        # Auto-connect state (matches action_manager_v2 auto_connect action)
        self._auto_connect_enabled: bool = True

        # Workflow data provider for validation
        self._workflow_data_provider: Callable | None = None

        # Execution state (for dev restart safety)
        self._execution_status: str = "ready"

        # Dev auto reload (optional)
        self._dev_fs_watcher: QFileSystemWatcher | None = None
        self._dev_auto_reload_timer: QTimer | None = None

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
        from .coordinators.signal_coordinator import SignalCoordinator

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

        # Dev auto reload (optional)
        self._setup_dev_auto_reload()

        logger.info("NewMainWindow v2 dock-only workspace initialized")

    def _setup_qt_actions(self) -> None:
        """
        Create persistent QAction objects expected by app/controllers.

        app.py wires these actions to the NodeGraphQt undo stack and edit ops.
        MenuBarV2/ToolbarV2 emit their own signals; NewMainWindow bridges those
        signals to these QActions (or directly to controllers).
        """

        def _make(name: str, *, checkable: bool = False) -> None:
            action = QAction(name.replace("_", " ").title(), self)
            if checkable:
                action.setCheckable(True)
            self._qt_actions[name] = action

        _make("undo")
        _make("redo")
        _make("delete")
        _make("cut")
        _make("copy")
        _make("paste")
        _make("duplicate")
        _make("select_all")
        _make("save")
        _make("save_as")
        _make("run")
        _make("stop")
        _make("pause", checkable=True)

    def _setup_dev_auto_reload(self) -> None:
        """
        Dev-only auto reload.

        - CASARE_DEV_AUTO_RELOAD=styles: automatically reapply v2 stylesheet on file changes
        - CASARE_DEV_AUTO_RELOAD=restart: automatically restart app on file changes
        """
        mode_raw = os.getenv("CASARE_DEV_AUTO_RELOAD", "").strip().lower()
        if not mode_raw:
            return

        mode = mode_raw
        if mode in {"1", "true", "on", "yes", "styles", "style"}:
            mode = "styles"
        elif mode in {"restart", "reboot", "full"}:
            mode = "restart"
        else:
            logger.warning(f"Unknown CASARE_DEV_AUTO_RELOAD mode: {mode_raw}")
            return

        debounce_ms_raw = os.getenv("CASARE_DEV_AUTO_RELOAD_DEBOUNCE_MS", "").strip()
        try:
            debounce_ms = int(debounce_ms_raw) if debounce_ms_raw else 250
        except Exception:
            debounce_ms = 250

        self._dev_auto_reload_timer = QTimer(self)
        self._dev_auto_reload_timer.setSingleShot(True)
        self._dev_auto_reload_timer.setInterval(max(50, debounce_ms))

        def _trigger() -> None:
            if mode == "styles":
                self._on_dev_reload_ui()
                return

            # restart
            if self._execution_status in {"running", "paused"}:
                self.show_status("Dev auto-restart skipped (workflow running)", 2000)
                return

            self._on_dev_restart_app()

        self._dev_auto_reload_timer.timeout.connect(_trigger)

        def _on_fs_change(_: str) -> None:
            if self._dev_auto_reload_timer is None:
                return
            self._dev_auto_reload_timer.start()

        watcher = QFileSystemWatcher(self)

        # Watch canvas source tree (recursive dirs) and icons dir for quick feedback.
        repo_root = Path(__file__).resolve().parents[4]
        watch_roots = [
            repo_root / "src" / "casare_rpa" / "presentation" / "canvas",
            repo_root / "src" / "casare_rpa" / "resources" / "icons",
        ]

        watch_dirs: list[str] = []
        for root in watch_roots:
            if not root.exists():
                continue
            watch_dirs.append(str(root))
            # QFileSystemWatcher is not recursive; add subdirectories too.
            for p in root.rglob("*"):
                if p.is_dir():
                    watch_dirs.append(str(p))

        # Avoid crashing on extremely large watch sets
        max_dirs = 500
        if len(watch_dirs) > max_dirs:
            watch_dirs = watch_dirs[:max_dirs]

        if watch_dirs:
            watcher.addPaths(watch_dirs)
            watcher.directoryChanged.connect(_on_fs_change)
            watcher.fileChanged.connect(_on_fs_change)
            self._dev_fs_watcher = watcher
            logger.info(
                f"Dev auto reload enabled: mode={mode}, debounce_ms={debounce_ms}, watched_dirs={len(watch_dirs)}"
            )
            self.show_status(f"Dev auto reload: {mode}", 3000)

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1200, 800)

        # Apply v2 theme (TOKENS_V2, THEME_V2 - dark-only, compact)
        from casare_rpa.presentation.canvas.theme import (
            get_canvas_stylesheet_v2,
        )

        self.setStyleSheet(get_canvas_stylesheet_v2())

    def _setup_chrome(self) -> None:
        """
        Create v2 menu bar, toolbar and status bar.

        Epic 2.1: Menu Bar Integration
        - MenuBarV2 with standard menu structure (File, Edit, View, Run, Tools, Help)

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
        try:
            if hasattr(self._menu_bar, "set_quick_node_mode_checked"):
                self._menu_bar.set_quick_node_mode_checked(
                    self._quick_node_manager.is_enabled()
                )
        except Exception:
            pass

        # Create toolbar
        self._toolbar = ToolbarV2(self)
        self.addToolBar(self._toolbar)
        self._connect_toolbar_signals()

        # Create status bar
        self._status_bar = StatusBarV2(self)
        self.setStatusBar(self._status_bar)

        # Apply any saved custom shortcuts after actions exist.
        self._apply_saved_shortcuts()

        logger.debug("NewMainWindow: v2 chrome initialized (menu, toolbar, status bar)")

    def _get_shortcut_actions(self) -> dict[str, QAction]:
        actions: dict[str, QAction] = {}

        # Menu bar actions (includes Find Node / Preferences / etc.)       
        if self._menu_bar and hasattr(self._menu_bar, "get_actions"):      
            try:
                actions.update(self._menu_bar.get_actions())  # type: ignore[attr-defined]
            except Exception:
                pass

        # Toolbar actions are primarily for click affordances.
        # To avoid Qt "Ambiguous shortcut overload" issues, the menu bar is the
        # single source of truth for shortcuts when an action exists in both places.
        if self._toolbar:
            for key in (
                "new",
                "open",
                "save",
                "save_as",
                "cut",
                "copy",
                "paste",
                "undo",
                "redo",
                "duplicate",
                "delete",
                "run",
                "stop",
                "record_workflow",
                "keyboard_shortcuts",
            ):
                attr = f"action_{key}" if key != "record_workflow" else "action_record"
                action = getattr(self._toolbar, attr, None)
                if isinstance(action, QAction):
                    actions.setdefault(key, action)

        return actions

    def _apply_saved_shortcuts(self) -> None:
        """Apply user-custom shortcuts from SettingsManager to known actions."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            raw = settings.get("ui.custom_shortcuts", {}) or {}
            if not isinstance(raw, dict):
                return

            actions = self._get_shortcut_actions()
            for name, shortcuts in raw.items():
                action = actions.get(name)
                if action is None:
                    continue
                if not isinstance(shortcuts, list):
                    continue
                strs = [str(s) for s in shortcuts if isinstance(s, str) and s]
                if not strs:
                    action.setShortcut("")
                    continue
                action.setShortcuts([QKeySequence(s) for s in strs])
        except Exception as e:
            logger.debug(f"Failed to apply saved shortcuts: {e}")

    def _connect_toolbar_signals(self) -> None:
        """Connect toolbar signals to NewMainWindow handlers."""        
        if not self._toolbar:
            return

        toolbar = self._toolbar
        toolbar.new_requested.connect(self._on_menu_new)
        toolbar.open_requested.connect(partial(self._on_menu_open_requested, ""))
        toolbar.save_requested.connect(self._on_menu_save)
        toolbar.save_as_requested.connect(partial(self._on_menu_save_as_requested, ""))
        toolbar.run_requested.connect(self._on_menu_run)
        toolbar.pause_requested.connect(self._on_menu_pause_toggle)
        toolbar.stop_requested.connect(self._on_menu_stop)
        toolbar.record_requested.connect(self._on_menu_record_workflow)
        toolbar.undo_requested.connect(self._on_undo_requested)
        toolbar.redo_requested.connect(self._on_redo_requested)
        toolbar.cut_requested.connect(self._on_menu_cut)
        toolbar.copy_requested.connect(self._on_menu_copy)
        toolbar.paste_requested.connect(self._on_menu_paste)
        toolbar.duplicate_requested.connect(self._on_menu_duplicate)
        toolbar.delete_requested.connect(self._on_menu_delete)
        if hasattr(toolbar, "keyboard_shortcuts_requested"):
            toolbar.keyboard_shortcuts_requested.connect(self._on_menu_keyboard_shortcuts)  # type: ignore[attr-defined]
        toolbar.dev_reload_ui_requested.connect(self._on_dev_reload_ui)
        toolbar.dev_restart_app_requested.connect(self._on_dev_restart_app)

        logger.debug("NewMainWindow: toolbar signals connected")

    @Slot()
    def _on_dev_reload_ui(self) -> None:
        """Dev: reload the v2 stylesheet so theme/QSS edits show without restart."""
        try:
            from PySide6.QtWidgets import QApplication

            from casare_rpa.presentation.canvas.theme import icons_v2, styles_v2, tokens_v2

            importlib.invalidate_caches()
            importlib.reload(tokens_v2)
            importlib.reload(styles_v2)

            # Clear icon cache so icon SVG tweaks can be picked up too
            try:
                icons_v2.IconProviderV2._icon_cache.clear()  # type: ignore[attr-defined]
            except Exception:
                pass

            app = QApplication.instance()
            if app is None:
                return

            app.setStyleSheet(styles_v2.get_canvas_stylesheet_v2())

            # Force style refresh for existing widgets
            for w in QApplication.allWidgets():
                try:
                    w.style().unpolish(w)
                    w.style().polish(w)
                    w.update()
                except Exception:
                    continue

            self.show_status("UI styles reloaded", 2000)
        except Exception as e:
            logger.warning(f"Dev UI reload failed: {e}")
            self.show_status("UI reload failed", 3000)

    @Slot()
    def _on_dev_restart_app(self) -> None:
        """Dev: restart app process to pick up Python code changes."""
        try:
            subprocess.Popen([sys.executable, *sys.argv], cwd=str(Path.cwd()))
        except Exception as e:
            logger.warning(f"Dev restart failed: {e}")
            self.show_status("Restart failed", 3000)
            return

        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _connect_menu_signals(self) -> None:
        """
        Connect menu bar signals to NewMainWindow handlers.

        Epic 2.1: Wire all menu actions to controllers/workflow signals.
        Most actions delegate to controllers; file/run actions emit signals.
        """
        if not self._menu_bar:
            return

        mb = self._menu_bar

        # File menu - delegate to workflow controller
        mb.new_requested.connect(self._on_menu_new)
        mb.open_requested.connect(self._on_menu_open_requested)
        mb.reload_requested.connect(self._on_menu_reload)
        mb.save_requested.connect(self._on_menu_save)
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
        mb.high_performance_mode_requested.connect(self._on_menu_high_performance_mode)
        mb.fleet_dashboard_requested.connect(self._on_menu_fleet_dashboard)
        mb.performance_dashboard_requested.connect(self._on_menu_performance_dashboard)
        mb.credential_manager_requested.connect(self._on_menu_credential_manager)
        mb.save_layout_requested.connect(self.save_layout)
        mb.reset_layout_requested.connect(self.reset_layout)

        # Run menu - delegate to execution controller
        mb.run_requested.connect(self._on_menu_run)
        mb.run_all_requested.connect(self._on_menu_run_all)
        mb.pause_requested.connect(self._on_menu_pause_toggle)
        mb.stop_requested.connect(self._on_menu_stop)
        mb.restart_requested.connect(self._on_menu_restart)
        mb.run_to_node_requested.connect(self._on_menu_run_to_node)      
        mb.run_single_node_requested.connect(self._on_menu_run_single_node)
        mb.start_listening_requested.connect(self._on_menu_start_listening)
        mb.stop_listening_requested.connect(self._on_menu_stop_listening)

        # Tools menu - delegate to automation/tools
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
        try:
            self.action_undo.trigger()
        except Exception:
            return

    @Slot()
    def _on_redo_requested(self) -> None:
        """Handle redo request from toolbar/menu."""
        try:
            self.action_redo.trigger()
        except Exception:
            return

    # ==================== Menu Slot Handlers (Epic 2.1) ====================
    # These handlers are called from menu actions when controllers are available

    @Slot()
    def _on_menu_reload(self) -> None:
        """Handle reload from menu."""
        if self._workflow_controller:
            self._workflow_controller.reload_workflow()

    @Slot()
    def _on_menu_project_manager(self) -> None:
        """Handle project manager from menu."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs import ProjectManagerDialog

            dialog = ProjectManagerDialog(parent=self)
            dialog.exec()
        except Exception as e:
            logger.warning(f"Failed to open Project Manager: {e}")
            self.show_status("Project manager failed to open", 3000)

    @Slot()
    def _on_menu_new(self) -> None:
        """Handle new workflow request."""
        if self._workflow_controller:
            self._workflow_controller.new_workflow()
        else:
            self.show_status("Workflow controller not ready", 3000)

    @Slot()
    def _on_menu_save(self) -> None:
        """Handle save workflow request."""
        if self._workflow_controller:
            self._workflow_controller.save_workflow()
        else:
            self.show_status("Workflow controller not ready", 3000)

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
                if self._workflow_controller:
                    self._workflow_controller.open_workflow_path(path)
                else:
                    self.workflow_open.emit(path)
        else:
            # Direct open from recent files
            if self._workflow_controller:
                self._workflow_controller.open_workflow_path(file_path)
            else:
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
                if self._workflow_controller:
                    self._workflow_controller.save_workflow_path(path)
                else:
                    self.workflow_save_as.emit(path)
        else:
            if self._workflow_controller:
                self._workflow_controller.save_workflow_path(file_path)
            else:
                self.workflow_save_as.emit(file_path)

    @Slot()
    def _on_menu_cut(self) -> None:
        """Handle cut from menu."""
        try:
            self.action_cut.trigger()
        except Exception:
            return

    @Slot()
    def _on_menu_copy(self) -> None:
        """Handle copy from menu."""
        try:
            self.action_copy.trigger()
        except Exception:
            return

    @Slot()
    def _on_menu_paste(self) -> None:
        """Handle paste from menu."""
        try:
            self.action_paste.trigger()
        except Exception:
            return

    @Slot()
    def _on_menu_duplicate(self) -> None:
        """Handle duplicate from menu."""
        try:
            self.action_duplicate.trigger()
        except Exception:
            return

    @Slot()
    def _on_menu_delete(self) -> None:
        """Handle delete from menu."""
        try:
            self.action_delete.trigger()
        except Exception:
            return

    @Slot()
    def _on_menu_select_all(self) -> None:
        """Handle select all from menu."""
        try:
            self.action_select_all.trigger()
        except Exception:
            return

    @Slot()
    def _on_menu_find_node(self) -> None:
        """Handle find node from menu."""
        self._show_node_search()

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
        self.show_minimap(checked)

    @Slot()
    def _on_menu_high_performance_mode(self, checked: bool) -> None:
        """Handle high performance mode from menu."""
        widget = self._central_widget
        if widget and hasattr(widget, "set_high_performance_mode"):
            widget.set_high_performance_mode(checked)  # type: ignore[attr-defined]

    @Slot()
    def _on_menu_fleet_dashboard(self) -> None:
        """Handle fleet dashboard from menu."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs import FleetDashboardDialog

            dialog = FleetDashboardDialog(parent=self)
            dialog.exec()
        except Exception as e:
            logger.warning(f"Failed to open Fleet Dashboard: {e}")
            self.show_status("Fleet dashboard failed to open", 3000)

    @Slot()
    def _on_menu_performance_dashboard(self) -> None:
        """Handle performance dashboard from menu."""
        try:
            from casare_rpa.presentation.canvas.ui.widgets.performance_dashboard import (
                PerformanceDashboardDialog,
            )

            dialog = PerformanceDashboardDialog(self)
            dialog.exec()
        except Exception as e:
            logger.warning(f"Failed to open Performance Dashboard: {e}")
            self.show_status("Performance dashboard failed to open", 3000)

    @Slot()
    def _on_menu_credential_manager(self) -> None:
        """Handle credential manager from menu."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs import CredentialManagerDialog

            dialog = CredentialManagerDialog(parent=self)
            dialog.exec()
        except Exception as e:
            logger.warning(f"Failed to open Credential Manager: {e}")
            self.show_status("Credential manager failed to open", 3000)

    @Slot()
    def _on_menu_restart(self) -> None:
        """Handle restart from menu."""
        if self._execution_controller:
            self._execution_controller.restart_workflow()

    @Slot()
    def _on_menu_run(self) -> None:
        """Handle run workflow request."""
        if self._execution_controller:
            self._execution_controller.run_workflow()
        else:
            self.show_status("Execution controller not ready", 3000)

    @Slot()
    def _on_menu_run_all(self) -> None:
        """Handle run all workflows request."""
        if self._execution_controller:
            self._execution_controller.run_all_workflows()
        else:
            self.show_status("Execution controller not ready", 3000)

    @Slot()
    def _on_menu_stop(self) -> None:
        """Handle stop workflow request."""
        if self._execution_controller:
            self._execution_controller.stop_workflow()
        else:
            self.show_status("Execution controller not ready", 3000)

    @Slot()
    def _on_menu_pause_toggle(self) -> None:
        """Handle pause/resume toggle request."""
        if not self._execution_controller:
            self.show_status("Execution controller not ready", 3000)
            return

        try:
            if getattr(self._execution_controller, "is_paused", False):
                self._execution_controller.resume_workflow()
            else:
                self._execution_controller.pause_workflow()
        except Exception:
            logger.exception("Pause/resume failed")
            self.show_status("Pause/resume failed", 3000)

    @Slot()
    def _on_menu_run_to_node(self) -> None:
        """Handle run to node from menu."""
        if self._execution_controller:
            self._execution_controller.run_to_node()

    @Slot()
    def _on_menu_run_single_node(self) -> None:
        """Handle run single node from menu."""
        if self._execution_controller:
            self._execution_controller.run_single_node()

    @Slot()
    def _on_menu_start_listening(self) -> None:
        """Handle start listening from menu."""
        if self._execution_controller:
            self._execution_controller.start_trigger_listening()

    @Slot()
    def _on_menu_stop_listening(self) -> None:
        """Handle stop listening from menu."""
        if self._execution_controller:
            self._execution_controller.stop_trigger_listening()

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
        widget = self._central_widget
        if widget and hasattr(widget, "create_frame_from_selection"):
            created = widget.create_frame_from_selection()  # type: ignore[attr-defined]
            if not created:
                self.show_status("Select nodes to create a frame", 2000)

    @Slot(bool)
    def _on_menu_toggle_auto_connect(self, checked: bool) -> None:        
        """Handle toggle auto connect from menu."""
        # Store auto-connect state
        self._auto_connect_enabled = checked
        try:
            widget = self._central_widget
            if widget and hasattr(widget, "set_auto_connect_enabled"):
                widget.set_auto_connect_enabled(checked)  # type: ignore[attr-defined]
        except Exception:
            pass
        self.show_status(f"Auto-connect: {'enabled' if checked else 'disabled'}")

    @Slot(bool)
    def _on_menu_quick_node_mode(self, checked: bool) -> None:
        """Handle quick node mode from menu."""
        try:
            self._quick_node_manager.set_enabled(checked)
        except Exception:
            pass
        status = "enabled" if checked else "disabled"
        self.show_status(f"Quick node mode {status} (press letter keys to create nodes)", 2500)

    @Slot()
    def _on_menu_quick_node_config(self) -> None:
        """Handle quick node config from menu."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs import QuickNodeConfigDialog

            dialog = QuickNodeConfigDialog(self._quick_node_manager, self)
            dialog.exec()
        except Exception as e:
            logger.warning(f"Failed to open Quick Node Hotkeys dialog: {e}")
            self.show_status("Quick node hotkeys dialog failed to open", 3000)

    @Slot()
    def _on_menu_documentation(self) -> None:
        """Handle documentation from menu."""
        import webbrowser

        webbrowser.open("https://casarerpa.com/docs")

    @Slot()
    def _on_menu_keyboard_shortcuts(self) -> None:
        """Handle keyboard shortcuts from menu."""
        try:
            from casare_rpa.presentation.canvas.ui.toolbars.hotkey_manager import (
                HotkeyManagerDialog,
            )
            from casare_rpa.utils.settings_manager import get_settings_manager

            actions = self._get_shortcut_actions()
            dialog = HotkeyManagerDialog(actions, self)
            if dialog.exec():
                # Persist current shortcuts for next launch.
                payload: dict[str, list[str]] = {}
                for name, action in actions.items():
                    shortcuts = [s.toString() for s in action.shortcuts() if s.toString()]
                    payload[name] = shortcuts

                get_settings_manager().set("ui.custom_shortcuts", payload)
        except Exception as e:
            logger.warning(f"Failed to open Keyboard Shortcuts dialog: {e}")
            self.show_status("Keyboard shortcuts dialog failed to open", 3000)

    @Slot()
    def _on_menu_preferences(self) -> None:
        """Handle preferences from menu."""
        try:
            from PySide6.QtWidgets import QDialog

            from casare_rpa.presentation.canvas.ui.dialogs.preferences_dialog import (
                PreferencesDialog,
            )
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings_manager = get_settings_manager()
            current_prefs = self._get_all_preferences(settings_manager)

            dialog = PreferencesDialog(preferences=current_prefs, parent=self)
            dialog.preferences_changed.connect(
                lambda prefs: self._save_preferences(settings_manager, prefs)
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.preferences_saved.emit()
        except Exception as e:
            logger.warning(f"Failed to open Preferences dialog: {e}")
            self.show_status("Preferences dialog failed to open", 3000)

    def _get_all_preferences(self, settings_manager) -> dict:
        """Collect preferences for PreferencesDialog from SettingsManager."""
        return {
            # General
            "theme": settings_manager.get("ui.theme", "Dark"),
            "language": settings_manager.get("general.language", "English"),
            "restore_session": settings_manager.get("general.restore_session", True),
            "check_updates": settings_manager.get("general.check_updates", True),
            # Autosave
            "autosave_enabled": settings_manager.get("autosave.enabled", True),
            "autosave_interval": settings_manager.get("autosave.interval_minutes", 5),
            "create_backups": settings_manager.get("autosave.create_backups", True),
            "max_backups": settings_manager.get("autosave.max_backups", 5),
            # Editor
            "show_grid": settings_manager.get("editor.show_grid", True),
            "snap_to_grid": settings_manager.get("editor.snap_to_grid", True),
            "grid_size": settings_manager.get("editor.grid_size", 20),
            "auto_align": settings_manager.get("editor.auto_align", False),
            "show_node_ids": settings_manager.get("editor.show_node_ids", False),
            "connection_style": settings_manager.get("editor.connection_style", "Curved"),
            "show_port_labels": settings_manager.get("editor.show_port_labels", True),
            # Performance
            "enable_antialiasing": settings_manager.get("performance.antialiasing", True),
            "enable_shadows": settings_manager.get("performance.shadows", False),
            "fps_limit": settings_manager.get("performance.fps_limit", 60),
            "max_undo_steps": settings_manager.get("performance.max_undo_steps", 100),
            "cache_size": settings_manager.get("performance.cache_size_mb", 200),
            # AI
            "ai_settings": {
                "provider": settings_manager.get("ai.provider", "Google"),
                "model": settings_manager.get("ai.model", "models/gemini-flash-latest"),
                "credential_id": settings_manager.get("ai.credential_id", "auto"),
            },
        }

    def _save_preferences(self, settings_manager, prefs: dict) -> None:
        """Persist PreferencesDialog output back to SettingsManager."""
        # General
        settings_manager.set("ui.theme", prefs.get("theme", "Dark"))
        settings_manager.set("general.language", prefs.get("language", "English"))
        settings_manager.set("general.restore_session", prefs.get("restore_session", True))
        settings_manager.set("general.check_updates", prefs.get("check_updates", True))

        # Autosave
        settings_manager.set("autosave.enabled", prefs.get("autosave_enabled", True))
        settings_manager.set("autosave.interval_minutes", prefs.get("autosave_interval", 5))
        settings_manager.set("autosave.create_backups", prefs.get("create_backups", True))
        settings_manager.set("autosave.max_backups", prefs.get("max_backups", 5))

        # Editor
        settings_manager.set("editor.show_grid", prefs.get("show_grid", True))
        settings_manager.set("editor.snap_to_grid", prefs.get("snap_to_grid", True))
        settings_manager.set("editor.grid_size", prefs.get("grid_size", 20))
        settings_manager.set("editor.auto_align", prefs.get("auto_align", False))
        settings_manager.set("editor.show_node_ids", prefs.get("show_node_ids", False))
        settings_manager.set("editor.connection_style", prefs.get("connection_style", "Curved"))
        settings_manager.set("editor.show_port_labels", prefs.get("show_port_labels", True))

        # Performance
        settings_manager.set(
            "performance.antialiasing",
            prefs.get("enable_antialiasing", True),
        )
        settings_manager.set("performance.shadows", prefs.get("enable_shadows", False))
        settings_manager.set("performance.fps_limit", prefs.get("fps_limit", 60))
        settings_manager.set("performance.max_undo_steps", prefs.get("max_undo_steps", 100))
        settings_manager.set("performance.cache_size_mb", prefs.get("cache_size", 200))

        # AI
        ai_settings = prefs.get("ai_settings") or {}
        if isinstance(ai_settings, dict):
            if "provider" in ai_settings:
                settings_manager.set("ai.provider", ai_settings.get("provider"))
            if "model" in ai_settings:
                settings_manager.set("ai.model", ai_settings.get("model"))
            if "credential_id" in ai_settings:
                settings_manager.set("ai.credential_id", ai_settings.get("credential_id"))

    @Slot()
    def _on_menu_check_updates(self) -> None:
        """Handle check updates from menu."""
        try:
            import webbrowser

            # Default to GitHub releases; app updates are distributed via releases/builds.
            webbrowser.open("https://github.com/omerlefaruk/CasareRPA/releases")
            self.show_status("Opened releases page", 2000)
        except Exception as e:
            logger.warning(f"Failed to open releases page: {e}")
            self.show_status("Could not open releases page", 3000)

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
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.BottomDockWidgetArea)

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
        # Ctrl+F is handled by MenuBarV2's "Find Node" action (StandardKey.Find).
        # Defining a second Ctrl+F binding here causes ambiguous shortcut overloads in Qt.

        # Keep these as attributes so Qt doesn't GC them.
        self._focus_view_shortcut = QShortcut(
            QKeySequence("F"),
            self,
            self._on_shortcut_focus_view,
            context=Qt.ShortcutContext.WindowShortcut,
        )
        self._home_all_shortcut = QShortcut(
            QKeySequence("Home"),
            self,
            self._on_shortcut_home_all,
            context=Qt.ShortcutContext.WindowShortcut,
        )

        logger.debug("NewMainWindow: keyboard shortcuts ready (Ctrl+F via menu action)")

    def _is_text_input_focused(self) -> bool:
        try:
            from PySide6.QtWidgets import (
                QApplication,
                QComboBox,
                QLineEdit,
                QPlainTextEdit,
                QSpinBox,
                QTextEdit,
            )

            w = QApplication.focusWidget()
            return isinstance(
                w, (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox)
            )
        except Exception:
            return False

    @Slot()
    def _on_shortcut_focus_view(self) -> None:
        if self._is_text_input_focused():
            return

        widget = self._central_widget
        if not widget:
            return

        try:
            graph = getattr(widget, "graph", None)
            selected = list(graph.selected_nodes() or []) if graph else []
        except Exception:
            selected = []

        if selected and hasattr(widget, "focus_view"):
            widget.focus_view()  # type: ignore[attr-defined]
            return

        if hasattr(widget, "home_all"):
            widget.home_all()  # type: ignore[attr-defined]

    @Slot()
    def _on_shortcut_home_all(self) -> None:
        if self._is_text_input_focused():
            return

        widget = self._central_widget
        if widget and hasattr(widget, "home_all"):
            widget.home_all()  # type: ignore[attr-defined]

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
        try:
            if hasattr(widget, "set_auto_connect_enabled"):
                widget.set_auto_connect_enabled(self._auto_connect_enabled)  # type: ignore[attr-defined]
        except Exception:
            pass
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

        # Wire node controller signals (guarded for tests/mocks)
        if self._node_controller and hasattr(self._node_controller, "node_selected"):
            self._node_controller.node_selected.connect(self._on_node_selected)
        if self._node_controller and hasattr(self._node_controller, "node_deselected"):
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

        if self._workflow_controller:
            self._workflow_controller.set_modified(modified)

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

    def get_quick_node_manager(self) -> Any:
        """Return the Quick Node manager for single-key node creation."""
        return self._quick_node_manager

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

    def validate_current_workflow(self, show_panel: bool = True) -> tuple[bool, list[str]]:
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
        self._execution_status = status
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

    # ==================== QAction Properties ====================
    # These are accessed by app.py/controllers for signal connections/state.

    @property
    def action_undo(self) -> QAction:
        return self._qt_actions["undo"]

    @property
    def action_redo(self) -> QAction:
        return self._qt_actions["redo"]

    @property
    def action_delete(self) -> QAction:
        return self._qt_actions["delete"]

    @property
    def action_cut(self) -> QAction:
        return self._qt_actions["cut"]

    @property
    def action_copy(self) -> QAction:
        return self._qt_actions["copy"]

    @property
    def action_paste(self) -> QAction:
        return self._qt_actions["paste"]

    @property
    def action_duplicate(self) -> QAction:
        return self._qt_actions["duplicate"]

    @property
    def action_select_all(self) -> QAction:
        return self._qt_actions["select_all"]

    @property
    def action_save(self) -> QAction:
        return self._qt_actions["save"]

    @property
    def action_save_as(self) -> QAction:
        return self._qt_actions["save_as"]

    @property
    def action_run(self) -> QAction:
        return self._qt_actions["run"]

    @property
    def action_stop(self) -> QAction:
        return self._qt_actions["stop"]

    @property
    def action_pause(self) -> QAction:
        return self._qt_actions["pause"]

    # ==================== Missing IMainWindow Protocol Methods ====================
    # Stub implementations for type safety with IMainWindow protocol

    def show_side_panel(self, index: int = 0) -> None:
        """Show the side panel (stub for Phase 4)."""
        pass

    def show_minimap(self, visible: bool = True) -> None:
        """Show/hide the graph minimap overlay."""
        try:
            if not self._central_widget:
                return

            if self._minimap_panel is None:
                from casare_rpa.presentation.canvas.ui.panels.minimap_panel import (
                    MinimapPanel,
                )

                self._minimap_panel = MinimapPanel(parent=self._central_widget)
                self._minimap_panel.setVisible(False)

                graph = self.get_graph()
                if graph is not None and hasattr(graph, "viewer"):
                    self._minimap_panel.set_graph_view(graph.viewer())

                self._minimap_panel.viewport_clicked.connect(self._on_minimap_clicked)

            self._minimap_panel.setVisible(bool(visible))
            if visible:
                self._position_minimap()
                try:
                    self._minimap_panel.mark_dirty()
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"show_minimap failed: {e}")

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
        """Return the minimap widget (if created)."""
        return self._minimap_panel

    @Slot(QPointF)
    def _on_minimap_clicked(self, scene_pos: QPointF) -> None:
        """Center the main graph view on a minimap click."""
        try:
            graph = self.get_graph()
            if graph is None or not hasattr(graph, "viewer"):
                return
            viewer = graph.viewer()
            viewer.centerOn(scene_pos)
        except Exception as e:
            logger.debug(f"Minimap click handler failed: {e}")

    def _position_minimap(self) -> None:
        """Position minimap at bottom-left of central widget."""
        if not self._central_widget or not self._minimap_panel:
            return
        margin = 12
        x = margin
        y = max(margin, self._central_widget.height() - self._minimap_panel.height() - margin)
        self._minimap_panel.move(x, y)
        self._minimap_panel.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_minimap()

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

