"""
MenuBarV2 - Menu bar for NewMainWindow with THEME_V2 styling.

Epic 2.1: Menu bar integration for NewMainWindow
- Standard menu structure (File, Edit, View, Run, Tools, Help)
- THEME_V2 colors (Cursor-like dark theme)
- Icons optional; primary icons live in ToolbarV2
- Action signals matching NewMainWindow workflow signals

Epic 1.3: Dynamic recent files management
- set_recent_files(files): Update recent files list
- add_recent_file(path): Add single file to recent list
- clear_recent_files(): Clear all recent files
- Numbered shortcuts (Ctrl+1 to Ctrl+9, Ctrl+0 for 10th)

Menu Structure:
- File: New, Open, Reload, Save, Save As, Recent Files, Project Manager, Exit
- Edit: Undo, Redo, Cut, Copy, Paste, Duplicate, Delete, Select All, Find Node, Rename Node, Auto Layout, Layout Selection, Snap to Grid
- View: Panel, Side Panel, Minimap, High Performance Mode, Fleet Dashboard, Performance Dashboard, Credentials, Save Layout, Reset Layout
- Run: Run, Run All, Pause, Stop, Restart, Run To Node, Run Single Node, Start Listening, Stop Listening
- Tools: Validate, Record Browser, Pick Element, Pick Desktop, Create Frame, Auto Connect, Quick Node Mode, Quick Node Config, Preferences
- Help: Documentation, Keyboard Shortcuts, Check Updates, About

See: docs/UX_REDESIGN_PLAN.md Phase 4 Epic 2.1, Epic 1.3
"""

import os
from collections.abc import Callable
from functools import partial
from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar, QWidget

from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon


class MenuBarV2(QMenuBar):
    """
    V2 menu bar with THEME_V2 styling.

    Features:
    - Standard menu structure (File/Edit/View/Run/Tools/Help)
    - Optional icons on menu items (see CASARE_MENU_ICONS)
    - Keyboard shortcuts for all actions
    - Action signals for integration with controllers
    - Recent files menu placeholder
    """

    # Core workflow signals (must match MainWindow/NewMainWindow)
    new_requested = Signal()
    open_requested = Signal(str)
    reload_requested = Signal()
    save_requested = Signal()
    save_as_requested = Signal(str)
    exit_requested = Signal()

    # Edit signals
    undo_requested = Signal()
    redo_requested = Signal()
    cut_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()
    duplicate_requested = Signal()
    delete_requested = Signal()
    select_all_requested = Signal()
    find_node_requested = Signal()
    rename_node_requested = Signal()
    auto_layout_requested = Signal()
    layout_selection_requested = Signal()
    toggle_grid_snap_requested = Signal(bool)

    # View signals
    toggle_panel_requested = Signal(bool)
    toggle_side_panel_requested = Signal(bool)
    toggle_minimap_requested = Signal(bool)
    high_performance_mode_requested = Signal(bool)
    fleet_dashboard_requested = Signal()
    performance_dashboard_requested = Signal()
    credential_manager_requested = Signal()
    save_layout_requested = Signal()
    reset_layout_requested = Signal()

    # Run signals
    run_requested = Signal()
    run_all_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    restart_requested = Signal()
    run_to_node_requested = Signal()
    run_single_node_requested = Signal()
    start_listening_requested = Signal()
    stop_listening_requested = Signal()

    # Automation signals
    validate_requested = Signal()
    record_workflow_requested = Signal(bool)
    pick_selector_requested = Signal()
    pick_desktop_selector_requested = Signal()
    create_frame_requested = Signal()
    toggle_auto_connect_requested = Signal(bool)
    quick_node_mode_requested = Signal(bool)
    quick_node_config_requested = Signal()

    # Help signals
    documentation_requested = Signal()
    keyboard_shortcuts_requested = Signal()
    preferences_requested = Signal()
    check_updates_requested = Signal()
    about_requested = Signal()

    # Project signals
    project_manager_requested = Signal()

    # Icon name mapping for menu items
    _MENU_ICON_MAP: dict[str, str] = {
        # File menu
        "new": "file",
        "open": "folder-open",
        "reload": "refresh",
        "save": "save",
        "save_as": "save",
        "project_manager": "folder",
        "exit": "x",
        # Edit menu
        "undo": "undo",
        "redo": "redo",
        "cut": "scissors",
        "copy": "copy",
        "paste": "clipboard",
        "duplicate": "copy",
        "delete": "trash",
        "select_all": "check",
        "find_node": "search",
        "rename_node": "edit",
        "auto_layout": "branch",
        "layout_selection": "layout",
        "toggle_grid_snap": "grid",
        # View menu
        "toggle_panel": "panel-bottom",
        "toggle_side_panel": "panel-right",
        "toggle_minimap": "eye",
        "high_performance_mode": "activity",
        "fleet_dashboard": "database",
        "performance_dashboard": "bar-chart",
        "credential_manager": "lock",
        "save_layout": "save",
        "reset_layout": "refresh",
        # Run menu
        "run": "play",
        "run_all": "play",
        "pause": "pause",
        "stop": "stop",
        "restart": "refresh",
        "run_to_node": "play",
        "run_single_node": "play",
        "start_listening": "play",
        "stop_listening": "stop",
        # Automation menu
        "validate": "check",
        "record_workflow": "circle",
        "pick_selector": "cursor",
        "pick_desktop_selector": "cursor",
        "create_frame": "plus",
        "auto_connect": "link",
        "quick_node_mode": "plus",
        "quick_node_config": "settings",
        # Help menu
        "documentation": "file",
        "keyboard_shortcuts": "keyboard",
        "preferences": "settings",
        "check_updates": "refresh",
        "about": "info",
    }

    # Maximum number of recent files to display (Epic 1.3)
    _MAX_RECENT_FILES = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the menu bar v2.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setObjectName("MenuBarV2")

        # Conventional desktop apps typically rely on a toolbar for icon-heavy
        # affordances and keep menu items mostly text-based.
        self._show_icons_in_menus = os.getenv("CASARE_MENU_ICONS", "0").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # Recent files storage (Epic 1.3)
        self._recent_files_list: list[str] = []

        # Recent files menu (placeholder for future implementation)       
        self._recent_files_menu: QMenu | None = None

        # View menu reference (for dynamic item addition)
        self._view_menu: QMenu | None = None

        # Cached actions for state syncing
        self._quick_node_mode_action: QAction | None = None
        self._actions_by_name: dict[str, QAction] = {}

        self._create_menus()

        logger.debug(
            "MenuBarV2 initialized (File/Edit/View/Run/Tools/Help, icons=%s)",
            self._show_icons_in_menus,
        )

    def _create_action(
        self,
        name: str,
        text: str,
        shortcut: QKeySequence | str | None = None,
        status_tip: str = "",
        checkable: bool = False,
        checked: bool = False,
        icon_name: str | None = None,
    ) -> QAction:
        """
        Create a QAction with IconProviderV2 icon.

        Args:
            name: Internal action name for icon lookup
            text: Display text
            shortcut: Keyboard shortcut
            status_tip: Status bar tip
            checkable: Whether action is checkable
            checked: Initial checked state (for checkable actions)
            icon_name: Override icon name (defaults to _MENU_ICON_MAP lookup)

        Returns:
            Created QAction
        """
        action = QAction(text, self)
        # Keep a stable reference for shortcut editing.
        self._actions_by_name[name] = action

        # Set shortcut
        if shortcut:
            if isinstance(shortcut, str):
                action.setShortcut(shortcut)
            else:
                action.setShortcut(shortcut)

        if status_tip:
            action.setStatusTip(status_tip)

        action.setCheckable(checkable)
        if checkable:
            action.setChecked(checked)

        # Optional icon from IconProviderV2 (primary icon affordances live in the toolbar)
        icon_key = icon_name or self._MENU_ICON_MAP.get(name)
        if icon_key and self._show_icons_in_menus:
            action.setIcon(get_icon(icon_key, size=16))

        # Register action for shortcut handling without adding it as a visible
        # top-level menu-bar item (QMenuBar displays actions added to itself).
        parent = self.parentWidget()
        if parent is not None:
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            parent.addAction(action)

        return action

    def get_actions(self) -> dict[str, QAction]:
        """Return all menu actions keyed by internal name."""
        return dict(self._actions_by_name)

    def _add_menu_item(
        self,
        menu: QMenu,
        name: str,
        text: str,
        shortcut: QKeySequence | str | None = None,
        status_tip: str = "",
        checkable: bool = False,
        checked: bool = False,
        icon_name: str | None = None,
        slot: Callable[[], None] | None = None,
    ) -> QAction:
        """
        Add an action to a menu and optionally connect to slot.

        Args:
            menu: Parent menu
            name: Internal action name
            text: Display text
            shortcut: Keyboard shortcut
            status_tip: Status bar tip
            checkable: Whether action is checkable
            checked: Initial checked state
            icon_name: Override icon name
            slot: Slot to connect (uses @Slot decorator methods)

        Returns:
            Created QAction
        """
        action = self._create_action(
            name, text, shortcut, status_tip, checkable, checked, icon_name
        )
        menu.addAction(action)

        if slot:
            action.triggered.connect(slot)

        return action

    def _create_menus(self) -> None:
        """Create the standard menu bar."""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_run_menu()
        self._create_tools_menu()
        self._create_help_menu()

    def _mark_menu(self, menu: QMenu, *, level: str) -> None:
        menu.setProperty("menuLevel", level)

    def _create_file_menu(self) -> None:
        """Create File menu with file operations."""
        file_menu = self.addMenu("&File")
        self._mark_menu(file_menu, level="top")

        workflow_menu = file_menu.addMenu("&Workflow")
        self._mark_menu(workflow_menu, level="sub")
        self._add_menu_item(
            workflow_menu,
            "new",
            "&New Workflow",
            QKeySequence.StandardKey.New,
            "Create a new workflow",
            slot=self._on_new,
        )
        self._add_menu_item(
            workflow_menu,
            "open",
            "&Open...",
            QKeySequence.StandardKey.Open,
            "Open an existing workflow",
            slot=self._on_open,
        )
        self._add_menu_item(
            workflow_menu,
            "reload",
            "&Reload",
            QKeySequence("Ctrl+Shift+R"),
            "Reload current workflow from disk",
            slot=self._on_reload,
        )

        # Recent Files submenu (populated by controller)
        self._recent_files_menu = file_menu.addMenu("Open &Recent")        
        if self._recent_files_menu is not None:
            self._mark_menu(self._recent_files_menu, level="sub")

        save_menu = file_menu.addMenu("&Save")
        self._mark_menu(save_menu, level="sub")
        self._add_menu_item(
            save_menu,
            "save",
            "&Save",
            QKeySequence.StandardKey.Save,
            "Save the current workflow",
            slot=self._on_save,
        )
        self._add_menu_item(
            save_menu,
            "save_as",
            "Save &As...",
            QKeySequence.StandardKey.SaveAs,
            "Save the workflow with a new name",
            slot=self._on_save_as,
        )

        project_menu = file_menu.addMenu("&Project")
        self._mark_menu(project_menu, level="sub")
        self._add_menu_item(
            project_menu,
            "project_manager",
            "&Project Manager...",
            QKeySequence("Ctrl+Shift+P"),
            "Open project manager",
            slot=self._on_project_manager,
        )

        file_menu.addSeparator()

        # Exit
        self._add_menu_item(
            file_menu,
            "exit",
            "E&xit",
            QKeySequence.StandardKey.Quit,
            "Exit the application",
            slot=self._on_exit,
        )

    def _create_edit_menu(self) -> None:
        """Create Edit menu with editing operations."""
        edit_menu = self.addMenu("&Edit")
        self._mark_menu(edit_menu, level="top")

        history_menu = edit_menu.addMenu("&History")
        self._mark_menu(history_menu, level="sub")
        self._add_menu_item(
            history_menu,
            "undo",
            "&Undo",
            QKeySequence.StandardKey.Undo,
            "Undo the last action",
            slot=self._on_undo,
        )

        self._add_menu_item(
            history_menu,
            "redo",
            "&Redo",
            QKeySequence.StandardKey.Redo,
            "Redo the last undone action",
            slot=self._on_redo,
        )

        clipboard_menu = edit_menu.addMenu("&Clipboard")
        self._mark_menu(clipboard_menu, level="sub")
        self._add_menu_item(
            clipboard_menu,
            "cut",
            "Cu&t",
            QKeySequence.StandardKey.Cut,
            "Cut selected nodes",
            slot=self._on_cut,
        )

        self._add_menu_item(
            clipboard_menu,
            "copy",
            "&Copy",
            QKeySequence.StandardKey.Copy,
            "Copy selected nodes",
            slot=self._on_copy,
        )

        self._add_menu_item(
            clipboard_menu,
            "paste",
            "&Paste",
            QKeySequence.StandardKey.Paste,
            "Paste nodes",
            slot=self._on_paste,
        )

        self._add_menu_item(
            clipboard_menu,
            "duplicate",
            "D&uplicate",
            QKeySequence("Ctrl+D"),
            "Duplicate selected nodes",
            slot=self._on_duplicate,
        )

        selection_menu = edit_menu.addMenu("&Selection")
        self._mark_menu(selection_menu, level="sub")
        self._add_menu_item(
            selection_menu,
            "select_all",
            "Select &All",
            QKeySequence.StandardKey.SelectAll,
            "Select all nodes",
            slot=self._on_select_all,
        )
        self._add_menu_item(
            selection_menu,
            "delete",
            "&Delete",
            QKeySequence("Del"),
            "Delete selected nodes",
            slot=self._on_delete,
        )
        self._add_menu_item(
            selection_menu,
            "rename_node",
            "&Rename Node",
            QKeySequence("F2"),
            "Rename selected node",
            slot=self._on_rename_node,
        )

        search_menu = edit_menu.addMenu("&Search")
        self._mark_menu(search_menu, level="sub")
        self._add_menu_item(
            search_menu,
            "find_node",
            "&Find Node...",
            QKeySequence.StandardKey.Find,
            "Search for nodes in the canvas",
            slot=self._on_find_node,
        )

        layout_menu = edit_menu.addMenu("&Layout")
        self._mark_menu(layout_menu, level="sub")
        self._add_menu_item(
            layout_menu,
            "auto_layout",
            "Auto-&Layout",
            QKeySequence("Ctrl+L"),
            "Automatically arrange all nodes",
            slot=self._on_auto_layout,
        )

        self._add_menu_item(
            layout_menu,
            "layout_selection",
            "Layout &Selection",
            None,
            "Automatically arrange selected nodes",
            slot=self._on_layout_selection,
        )

        self._add_menu_item(
            layout_menu,
            "toggle_grid_snap",
            "Snap to &Grid",
            QKeySequence("Ctrl+Shift+G"),
            "Toggle snap-to-grid mode",
            checkable=True,
            checked=True,
            slot=self._on_toggle_grid_snap,
        )

    def _create_view_menu(self) -> None:
        """Create View menu with view options."""
        view_menu = self.addMenu("&View")
        self._mark_menu(view_menu, level="top")
        self._view_menu = view_menu

        panels_menu = view_menu.addMenu("&Panels")
        self._mark_menu(panels_menu, level="sub")
        self._add_menu_item(
            panels_menu,
            "toggle_panel",
            "Toggle &Panel",
            QKeySequence("6"),
            "Show/hide bottom panel",
            checkable=True,
            slot=self._on_toggle_panel,
        )

        self._add_menu_item(
            panels_menu,
            "toggle_side_panel",
            "Toggle Side &Panel",
            QKeySequence("7"),
            "Show/hide unified side panel",
            checkable=True,
            slot=self._on_toggle_side_panel,
        )

        navigation_menu = view_menu.addMenu("&Navigation")
        self._mark_menu(navigation_menu, level="sub")
        self._add_menu_item(
            navigation_menu,
            "toggle_minimap",
            "&Minimap",
            QKeySequence("Ctrl+M"),
            "Show/hide minimap overview",
            checkable=True,
            slot=self._on_toggle_minimap,
        )

        performance_menu = view_menu.addMenu("&Performance")
        self._mark_menu(performance_menu, level="sub")
        self._add_menu_item(
            performance_menu,
            "high_performance_mode",
            "&High Performance Mode",
            None,
            "Force simplified rendering for large workflows",
            checkable=True,
            slot=self._on_high_performance_mode,
        )

        dashboards_menu = view_menu.addMenu("&Dashboards")
        self._mark_menu(dashboards_menu, level="sub")
        self._add_menu_item(
            dashboards_menu,
            "fleet_dashboard",
            "&Fleet Dashboard",
            QKeySequence("Ctrl+Shift+F"),
            "Open fleet management dashboard",
            slot=self._on_fleet_dashboard,
        )

        self._add_menu_item(
            dashboards_menu,
            "performance_dashboard",
            "Performance Dashboard",
            QKeySequence("Ctrl+Alt+P"),
            "View performance metrics",
            slot=self._on_performance_dashboard,
        )

        credentials_menu = view_menu.addMenu("&Credentials")
        self._mark_menu(credentials_menu, level="sub")
        self._add_menu_item(
            credentials_menu,
            "credential_manager",
            "&Credentials...",
            QKeySequence("Ctrl+Alt+C"),
            "Manage API keys and credentials",
            slot=self._on_credential_manager,
        )

        layout_menu = view_menu.addMenu("&Layout")
        self._mark_menu(layout_menu, level="sub")
        self._add_menu_item(
            layout_menu,
            "save_layout",
            "Save &Layout",
            QKeySequence("Ctrl+Shift+L"),
            "Save current UI layout",
            slot=self._on_save_layout,
        )

        self._add_menu_item(
            layout_menu,
            "reset_layout",
            "Reset &Default Layout",
            None,
            "Reset UI layout to factory defaults",
            slot=self._on_reset_layout,
        )

    def _create_run_menu(self) -> None:
        """Create Run menu with execution controls."""
        run_menu = self.addMenu("&Run")
        self._mark_menu(run_menu, level="top")

        execution_menu = run_menu.addMenu("&Execution")
        self._mark_menu(execution_menu, level="sub")
        self._add_menu_item(
            execution_menu,
            "run",
            "Run",
            QKeySequence("F3"),
            "Execute the workflow",
            slot=self._on_run,
        )

        self._add_menu_item(
            execution_menu,
            "run_all",
            "Run All Workflows",
            QKeySequence("Ctrl+Shift+F3"),
            "Execute all workflows concurrently",
            slot=self._on_run_all,
        )

        self._add_menu_item(
            execution_menu,
            "pause",
            "Pause",
            QKeySequence("F6"),
            "Pause workflow execution",
            checkable=True,
            slot=self._on_pause,
        )

        self._add_menu_item(
            execution_menu,
            "stop",
            "Stop",
            QKeySequence("Shift+F3"),
            "Stop workflow execution",
            slot=self._on_stop,
        )

        self._add_menu_item(
            execution_menu,
            "restart",
            "Restart",
            QKeySequence("F8"),
            "Restart workflow",
            slot=self._on_restart,
        )

        debug_menu = run_menu.addMenu("&Debug")
        self._mark_menu(debug_menu, level="sub")
        self._add_menu_item(
            debug_menu,
            "run_to_node",
            "Run To Node",
            QKeySequence("F4"),
            "Execute workflow up to selected node",
            slot=self._on_run_to_node,
        )

        self._add_menu_item(
            debug_menu,
            "run_single_node",
            "Run This Node",
            QKeySequence("F5"),
            "Re-run only the selected node",
            slot=self._on_run_single_node,
        )

        listening_menu = run_menu.addMenu("&Listening")
        self._mark_menu(listening_menu, level="sub")
        self._add_menu_item(
            listening_menu,
            "start_listening",
            "Start Listening",
            QKeySequence("F9"),
            "Start listening for trigger events",
            slot=self._on_start_listening,
        )

        self._add_menu_item(
            listening_menu,
            "stop_listening",
            "Stop Listening",
            QKeySequence("Shift+F9"),
            "Stop listening for trigger events",
            slot=self._on_stop_listening,
        )

    def _create_tools_menu(self) -> None:
        """Create Tools menu with automation and configuration."""
        tools_menu = self.addMenu("&Tools")
        self._mark_menu(tools_menu, level="top")

        validation_menu = tools_menu.addMenu("&Validation")
        self._mark_menu(validation_menu, level="sub")
        self._add_menu_item(
            validation_menu,
            "validate",
            "&Validate",
            QKeySequence("Ctrl+B"),
            "Validate current workflow",
            slot=self._on_validate,
        )

        recording_menu = tools_menu.addMenu("&Recording")
        self._mark_menu(recording_menu, level="sub")
        self._add_menu_item(
            recording_menu,
            "record_workflow",
            "Record &Browser",
            QKeySequence("Ctrl+R"),
            "Record browser interactions as workflow",
            checkable=True,
            slot=self._on_record_workflow,
        )

        picking_menu = tools_menu.addMenu("&Picking")
        self._mark_menu(picking_menu, level="sub")
        self._add_menu_item(
            picking_menu,
            "pick_selector",
            "Pick &Element",
            QKeySequence("Ctrl+Shift+E"),
            "Pick element (Browser, Desktop, OCR, Image)",
            slot=self._on_pick_selector,
        )

        self._add_menu_item(
            picking_menu,
            "pick_desktop_selector",
            "Pick &Desktop Element",
            QKeySequence("Ctrl+Shift+D"),
            "Pick desktop element",
            slot=self._on_pick_desktop_selector,
        )

        canvas_menu = tools_menu.addMenu("&Canvas")
        self._mark_menu(canvas_menu, level="sub")
        self._add_menu_item(
            canvas_menu,
            "create_frame",
            "Create &Frame",
            QKeySequence("Shift+W"),
            "Create a frame (around selection, or empty if nothing is selected)",
            slot=self._on_create_frame,
        )

        self._add_menu_item(
            canvas_menu,
            "auto_connect",
            "Auto-&Connect",
            QKeySequence("Ctrl+Shift+A"),
            "Auto-suggest connections when dragging nodes",
            checkable=True,
            checked=True,
            slot=self._on_auto_connect,
        )

        quick_node_menu = tools_menu.addMenu("&Quick Node")
        self._mark_menu(quick_node_menu, level="sub")
        self._quick_node_mode_action = self._add_menu_item(
            quick_node_menu,
            "quick_node_mode",
            "&Quick Node Mode",
            QKeySequence("Ctrl+Shift+Q"),
            "Toggle hotkey-based quick node creation",
            checkable=True,
            checked=True,
            slot=self._on_quick_node_mode,
        )

        self._add_menu_item(
            quick_node_menu,
            "quick_node_config",
            "Quick Node &Hotkeys...",
            QKeySequence("Ctrl+Alt+Q"),
            "Configure quick node hotkey bindings",
            slot=self._on_quick_node_config,
        )

        options_menu = tools_menu.addMenu("&Options")
        self._mark_menu(options_menu, level="sub")
        self._add_menu_item(
            options_menu,
            "preferences",
            "&Preferences...",
            QKeySequence("Ctrl+,"),
            "Configure application preferences",
            slot=self._on_preferences,
        )

    def set_quick_node_mode_checked(self, checked: bool) -> None:
        """Sync the Quick Node Mode menu check state from external source."""
        if self._quick_node_mode_action is not None:
            self._quick_node_mode_action.setChecked(bool(checked))

    def _create_help_menu(self) -> None:
        """Create Help menu with help and options."""
        help_menu = self.addMenu("&Help")
        self._mark_menu(help_menu, level="top")

        resources_menu = help_menu.addMenu("&Resources")
        self._mark_menu(resources_menu, level="sub")
        self._add_menu_item(
            resources_menu,
            "documentation",
            "&Documentation",
            QKeySequence("F1"),
            "Open documentation in browser",
            slot=self._on_documentation,
        )

        self._add_menu_item(
            resources_menu,
            "keyboard_shortcuts",
            "&Keyboard Shortcuts...",
            QKeySequence("Ctrl+K, Ctrl+S"),
            "View and edit keyboard shortcuts",
            slot=self._on_keyboard_shortcuts,
        )

        updates_menu = help_menu.addMenu("&Updates")
        self._mark_menu(updates_menu, level="sub")
        self._add_menu_item(
            updates_menu,
            "check_updates",
            "Check for &Updates",
            None,
            "Check for application updates",
            slot=self._on_check_updates,
        )

        about_menu = help_menu.addMenu("&About")
        self._mark_menu(about_menu, level="sub")
        self._add_menu_item(
            about_menu,
            "about",
            "&About",
            None,
            "About CasareRPA",
            slot=self._on_about,
        )

    # ==================== File Slots ====================

    @Slot()
    def _on_new(self) -> None:
        """Handle new workflow request."""
        logger.debug("Menu: New workflow requested")
        self.new_requested.emit()

    @Slot()
    def _on_open(self) -> None:
        """Handle open workflow request."""
        logger.debug("Menu: Open workflow requested")
        self.open_requested.emit("")  # Path filled by file dialog

    @Slot()
    def _on_reload(self) -> None:
        """Handle reload workflow request."""
        logger.debug("Menu: Reload workflow requested")
        self.reload_requested.emit()

    @Slot()
    def _on_save(self) -> None:
        """Handle save workflow request."""
        logger.debug("Menu: Save workflow requested")
        self.save_requested.emit()

    @Slot()
    def _on_save_as(self) -> None:
        """Handle save as workflow request."""
        logger.debug("Menu: Save as workflow requested")
        self.save_as_requested.emit("")  # Path filled by file dialog

    @Slot()
    def _on_project_manager(self) -> None:
        """Handle project manager request."""
        logger.debug("Menu: Project manager requested")
        self.project_manager_requested.emit()

    @Slot()
    def _on_exit(self) -> None:
        """Handle exit request."""
        logger.debug("Menu: Exit requested")
        self.exit_requested.emit()

    # ==================== Edit Slots ====================

    @Slot()
    def _on_undo(self) -> None:
        """Handle undo request."""
        logger.debug("Menu: Undo requested")
        self.undo_requested.emit()

    @Slot()
    def _on_redo(self) -> None:
        """Handle redo request."""
        logger.debug("Menu: Redo requested")
        self.redo_requested.emit()

    @Slot()
    def _on_cut(self) -> None:
        """Handle cut request."""
        logger.debug("Menu: Cut requested")
        self.cut_requested.emit()

    @Slot()
    def _on_copy(self) -> None:
        """Handle copy request."""
        logger.debug("Menu: Copy requested")
        self.copy_requested.emit()

    @Slot()
    def _on_paste(self) -> None:
        """Handle paste request."""
        logger.debug("Menu: Paste requested")
        self.paste_requested.emit()

    @Slot()
    def _on_duplicate(self) -> None:
        """Handle duplicate request."""
        logger.debug("Menu: Duplicate requested")
        self.duplicate_requested.emit()

    @Slot()
    def _on_delete(self) -> None:
        """Handle delete request."""
        logger.debug("Menu: Delete requested")
        self.delete_requested.emit()

    @Slot()
    def _on_select_all(self) -> None:
        """Handle select all request."""
        logger.debug("Menu: Select all requested")
        self.select_all_requested.emit()

    @Slot()
    def _on_find_node(self) -> None:
        """Handle find node request."""
        logger.debug("Menu: Find node requested")
        self.find_node_requested.emit()

    @Slot()
    def _on_rename_node(self) -> None:
        """Handle rename node request."""
        logger.debug("Menu: Rename node requested")
        self.rename_node_requested.emit()

    @Slot()
    def _on_auto_layout(self) -> None:
        """Handle auto layout request."""
        logger.debug("Menu: Auto layout requested")
        self.auto_layout_requested.emit()

    @Slot()
    def _on_layout_selection(self) -> None:
        """Handle layout selection request."""
        logger.debug("Menu: Layout selection requested")
        self.layout_selection_requested.emit()

    @Slot()
    def _on_toggle_grid_snap(self, checked: bool) -> None:
        """Handle toggle grid snap request."""
        logger.debug(f"Menu: Toggle grid snap: {checked}")
        self.toggle_grid_snap_requested.emit(checked)

    # ==================== View Slots ====================

    @Slot()
    def _on_toggle_panel(self, checked: bool) -> None:
        """Handle toggle panel request."""
        logger.debug(f"Menu: Toggle panel: {checked}")
        self.toggle_panel_requested.emit(checked)

    @Slot()
    def _on_toggle_side_panel(self, checked: bool) -> None:
        """Handle toggle side panel request."""
        logger.debug(f"Menu: Toggle side panel: {checked}")
        self.toggle_side_panel_requested.emit(checked)

    @Slot()
    def _on_toggle_minimap(self, checked: bool) -> None:
        """Handle toggle minimap request."""
        logger.debug(f"Menu: Toggle minimap: {checked}")
        self.toggle_minimap_requested.emit(checked)

    @Slot()
    def _on_high_performance_mode(self, checked: bool) -> None:
        """Handle high performance mode request."""
        logger.debug(f"Menu: High performance mode: {checked}")
        self.high_performance_mode_requested.emit(checked)

    @Slot()
    def _on_fleet_dashboard(self) -> None:
        """Handle fleet dashboard request."""
        logger.debug("Menu: Fleet dashboard requested")
        self.fleet_dashboard_requested.emit()

    @Slot()
    def _on_performance_dashboard(self) -> None:
        """Handle performance dashboard request."""
        logger.debug("Menu: Performance dashboard requested")
        self.performance_dashboard_requested.emit()

    @Slot()
    def _on_credential_manager(self) -> None:
        """Handle credential manager request."""
        logger.debug("Menu: Credential manager requested")
        self.credential_manager_requested.emit()

    @Slot()
    def _on_save_layout(self) -> None:
        """Handle save layout request."""
        logger.debug("Menu: Save layout requested")
        self.save_layout_requested.emit()

    @Slot()
    def _on_reset_layout(self) -> None:
        """Handle reset layout request."""
        logger.debug("Menu: Reset layout requested")
        self.reset_layout_requested.emit()

    # ==================== Run Slots ====================

    @Slot()
    def _on_run(self) -> None:
        """Handle run request."""
        logger.debug("Menu: Run requested")
        self.run_requested.emit()

    @Slot()
    def _on_run_all(self) -> None:
        """Handle run all request."""
        logger.debug("Menu: Run all requested")
        self.run_all_requested.emit()

    @Slot()
    def _on_pause(self, checked: bool) -> None:
        """Handle pause request."""
        logger.debug(f"Menu: Pause: {checked}")
        self.pause_requested.emit()

    @Slot()
    def _on_stop(self) -> None:
        """Handle stop request."""
        logger.debug("Menu: Stop requested")
        self.stop_requested.emit()

    @Slot()
    def _on_restart(self) -> None:
        """Handle restart request."""
        logger.debug("Menu: Restart requested")
        self.restart_requested.emit()

    @Slot()
    def _on_run_to_node(self) -> None:
        """Handle run to node request."""
        logger.debug("Menu: Run to node requested")
        self.run_to_node_requested.emit()

    @Slot()
    def _on_run_single_node(self) -> None:
        """Handle run single node request."""
        logger.debug("Menu: Run single node requested")
        self.run_single_node_requested.emit()

    @Slot()
    def _on_start_listening(self) -> None:
        """Handle start listening request."""
        logger.debug("Menu: Start listening requested")
        self.start_listening_requested.emit()

    @Slot()
    def _on_stop_listening(self) -> None:
        """Handle stop listening request."""
        logger.debug("Menu: Stop listening requested")
        self.stop_listening_requested.emit()

    # ==================== Automation Slots ====================

    @Slot()
    def _on_validate(self) -> None:
        """Handle validate request."""
        logger.debug("Menu: Validate requested")
        self.validate_requested.emit()

    @Slot()
    def _on_record_workflow(self, checked: bool) -> None:
        """Handle record workflow request."""
        logger.debug(f"Menu: Record workflow: {checked}")
        self.record_workflow_requested.emit(checked)

    @Slot()
    def _on_pick_selector(self) -> None:
        """Handle pick selector request."""
        logger.debug("Menu: Pick selector requested")
        self.pick_selector_requested.emit()

    @Slot()
    def _on_pick_desktop_selector(self) -> None:
        """Handle pick desktop selector request."""
        logger.debug("Menu: Pick desktop selector requested")
        self.pick_desktop_selector_requested.emit()

    @Slot()
    def _on_create_frame(self) -> None:
        """Handle create frame request."""
        logger.debug("Menu: Create frame requested")
        self.create_frame_requested.emit()

    @Slot()
    def _on_auto_connect(self, checked: bool) -> None:
        """Handle auto connect request."""
        logger.debug(f"Menu: Auto connect: {checked}")
        self.toggle_auto_connect_requested.emit(checked)

    @Slot()
    def _on_quick_node_mode(self, checked: bool) -> None:
        """Handle quick node mode request."""
        logger.debug(f"Menu: Quick node mode: {checked}")
        self.quick_node_mode_requested.emit(checked)

    @Slot()
    def _on_quick_node_config(self) -> None:
        """Handle quick node config request."""
        logger.debug("Menu: Quick node config requested")
        self.quick_node_config_requested.emit()

    # ==================== Help Slots ====================

    @Slot()
    def _on_documentation(self) -> None:
        """Handle documentation request."""
        logger.debug("Menu: Documentation requested")
        self.documentation_requested.emit()

    @Slot()
    def _on_keyboard_shortcuts(self) -> None:
        """Handle keyboard shortcuts request."""
        logger.debug("Menu: Keyboard shortcuts requested")
        self.keyboard_shortcuts_requested.emit()

    @Slot()
    def _on_preferences(self) -> None:
        """Handle preferences request."""
        logger.debug("Menu: Preferences requested")
        self.preferences_requested.emit()

    @Slot()
    def _on_check_updates(self) -> None:
        """Handle check updates request."""
        logger.debug("Menu: Check updates requested")
        self.check_updates_requested.emit()

    @Slot()
    def _on_about(self) -> None:
        """Handle about request."""
        logger.debug("Menu: About requested")
        self.about_requested.emit()

    # ==================== Public API ====================

    def get_recent_files_menu(self) -> QMenu | None:
        """Return the recent files menu for population by controller."""
        return self._recent_files_menu

    def get_view_menu(self) -> QMenu | None:
        """Return the view menu for dynamic item addition."""
        return self._view_menu

    def set_undo_enabled(self, enabled: bool) -> None:
        """Set undo action enabled state."""
        for action in self.actions():
            if action.text() == "&Undo":
                action.setEnabled(enabled)
                break

    def set_redo_enabled(self, enabled: bool) -> None:
        """Set redo action enabled state."""
        for action in self.actions():
            if action.text() == "&Redo":
                action.setEnabled(enabled)
                break

    def set_execution_state(self, is_running: bool, is_paused: bool = False) -> None:
        """
        Update menu action states based on execution state.

        Args:
            is_running: Whether workflow is executing
            is_paused: Whether workflow is paused
        """
        # Disable file operations during execution
        can_edit = not is_running
        for action in self.actions():
            text = action.text()
            if text in ("&New Workflow", "&Open...", "&Save", "Save &As..."):
                action.setEnabled(can_edit)

        # Update run/stop states
        for action in self.actions():
            text = action.text()
            if text == "Run":
                action.setEnabled(not is_running)
            elif text == "Stop":
                action.setEnabled(is_running)
            elif text == "Pause":
                action.setEnabled(is_running and not is_paused)
                if is_paused:
                    action.setChecked(False)

    # ==================== Recent Files Management (Epic 1.3) ====================

    def set_recent_files(self, files: list[str]) -> None:
        """
        Set the recent files list and update the menu.

        Args:
            files: List of file paths (most recent first)
        """
        self._recent_files_list = files[: self._MAX_RECENT_FILES]
        self._update_recent_files_menu()
        logger.debug(f"Recent files updated: {len(self._recent_files_list)} files")

    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to add
        """
        # Normalize the path for consistent comparison
        normalized_path = str(Path(file_path).resolve())
        
        # Remove if already exists (compare normalized paths), then insert at front
        self._recent_files_list = [
            f for f in self._recent_files_list 
            if str(Path(f).resolve()) != normalized_path
        ]
        self._recent_files_list.insert(0, normalized_path)

        # Trim to max
        self._recent_files_list = self._recent_files_list[: self._MAX_RECENT_FILES]
        self._update_recent_files_menu()

        logger.debug(f"Added to recent files: {file_path}")

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._recent_files_list.clear()
        self._update_recent_files_menu()
        logger.debug("Recent files cleared")

    def _update_recent_files_menu(self) -> None:
        """Update the recent files menu with current file list."""
        if self._recent_files_menu is None:
            return

        # Clear existing items
        self._recent_files_menu.clear()

        if not self._recent_files_list:
            self._recent_files_menu.setEnabled(False)
            return

        self._recent_files_menu.setEnabled(True)

        # Add file actions (with numbered shortcuts 1-9, then 0 for 10th)
        for i, file_path in enumerate(self._recent_files_list):
            # Use 1-9 for first 9, then 0 for 10th
            if i < 9:
                shortcut_key = str(i + 1)
                shortcut = QKeySequence(f"Ctrl+{shortcut_key}")
            elif i == 9:
                shortcut_key = "0"
                shortcut = QKeySequence("Ctrl+0")
            else:
                shortcut = QKeySequence()

            # Extract filename for display
            display_name = Path(file_path).name
            text = f"&{shortcut_key} {display_name}"

            action = QAction(text, self)
            action.setToolTip(str(file_path))
            action.setShortcut(shortcut)
            action.setData(file_path)

            # Connect to signal using partial instead of lambda
            action.triggered.connect(partial(self._on_recent_file_clicked, file_path))

            self._recent_files_menu.addAction(action)

        # Add clear separator and action
        if self._recent_files_list:
            self._recent_files_menu.addSeparator()
            clear_action = QAction("Clear Recent", self)
            clear_action.triggered.connect(self.clear_recent_files)
            self._recent_files_menu.addAction(clear_action)

    def _on_recent_file_clicked(self, file_path: str) -> None:
        """
        Handle recent file menu item click.

        Args:
            file_path: Path to the recent file
        """
        logger.debug(f"Recent file clicked: {file_path}")
        self.open_requested.emit(file_path)

