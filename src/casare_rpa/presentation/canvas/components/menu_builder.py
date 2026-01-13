"""
Menu builder for MainWindow menu bar.

Centralizes menu creation and structure.
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenu

from casare_rpa.presentation.canvas.ui.icons import (
    get_icon_v2_or_legacy,
)

if TYPE_CHECKING:
    from ..main_window import MainWindow


class MenuBuilder:
    """
    Builds the menu bar structure for MainWindow.

    Responsibilities:
    - Create menu bar with 6 menus
    - Organize actions into logical groups
    - Handle recent files menu
    - Set v2 icons on menu items (Epic 2.2)
    """

    # Icon name mapping for menu items (Epic 2.2)
    _MENU_ICON_MAP = {
        # File menu
        "action_new": "file",
        "action_open": "folder",
        "action_reload": "refresh",
        "action_save": "save",
        "action_save_as": "save",
        "action_project_manager": "folder",
        "action_exit": "close",
        # Edit menu
        "action_undo": "undo",
        "action_redo": "redo",
        "action_cut": "cut",
        "action_copy": "copy",
        "action_paste": "paste",
        "action_duplicate": "copy",
        "action_delete": "trash",
        "action_select_all": "check",
        "action_find_node": "search",
        "action_rename_node": "edit",
        "action_auto_layout": "branch",
        "action_layout_selection": "check",
        "action_toggle_grid_snap": "grid",
        # View menu
        "action_toggle_panel": "panel-bottom",
        "action_toggle_side_panel": "panel-right",
        "action_toggle_minimap": "eye",
        "action_high_performance_mode": "activity",
        "action_fleet_dashboard": "database",
        "action_performance_dashboard": "bar-chart",
        "action_credential_manager": "lock",
        "action_save_layout": "save",
        "action_reset_layout": "refresh",
        # Run menu
        "action_run": "play",
        "action_run_all": "play",
        "action_pause": "pause",
        "action_stop": "stop",
        "action_restart": "refresh",
        "action_run_to_node": "play",
        "action_run_single_node": "play",
        "action_start_listening": "play",
        "action_stop_listening": "stop",
        # Automation menu
        "action_validate": "check",
        "action_record_workflow": "circle",
        "action_pick_selector": "cursor",
        "action_desktop_selector_builder": "cursor",
        "action_create_frame": "plus",
        "action_auto_connect": "link",
        "action_quick_node_mode": "plus",
        "action_quick_node_config": "settings",
        # Help menu
        "action_documentation": "file",
        "action_keyboard_shortcuts": "keyboard",
        "action_preferences": "settings",
        "action_check_updates": "refresh",
        "action_about": "info",
    }

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize menu builder.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

    def _set_menu_icon(self, action, icon_name: str | None = None) -> None:
        """Set v2 icon on a menu action."""
        # Skip if action already has an icon
        if not action.icon().isNull():
            return

        # Use provided icon name or look up in mapping
        if icon_name is None:
            action_name = getattr(action, "text", "").lower().replace(" ", "_")
            icon_name = self._MENU_ICON_MAP.get(f"action_{action_name}")

        if icon_name:
            action.setIcon(get_icon_v2_or_legacy(icon_name, size=16))

    def create_menus(self) -> None:
        """Create menu bar and all menus (6-menu structure)."""
        mw = self._main_window
        menubar = mw.menuBar()

        self._create_file_menu(menubar, mw)
        self._create_edit_menu(menubar, mw)
        self._create_view_menu(menubar, mw)
        self._create_run_menu(menubar, mw)
        self._create_automation_menu(menubar, mw)
        self._create_help_menu(menubar, mw)

        # Set v2 icons on all menu items after menus are created (v2 mandatory)
        self._set_all_menu_icons(menubar)

    def _set_all_menu_icons(self, menubar) -> None:
        """Set v2 icons on all menu items."""
        for i in range(menubar.actions().__len__()):
            menu = menubar.actions()[i].menu()
            if menu:
                for action in menu.actions():
                    self._set_menu_icon(action)

    def _create_file_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create File menu with logical groupings.

        Groups:
        - New/Open/Recent (file access)
        - Save operations
        - Project management
        - Migration utilities
        - Exit (destructive, always last)
        """
        file_menu = menubar.addMenu("&File")

        # --- File Access ---
        file_menu.addAction(mw.action_new)
        file_menu.addAction(mw.action_open)
        file_menu.addAction(mw.action_reload)
        mw._recent_files_menu = file_menu.addMenu("Recent Files")

        file_menu.addSeparator()

        # --- Save Operations ---
        file_menu.addAction(mw.action_save)
        file_menu.addAction(mw.action_save_as)

        file_menu.addSeparator()

        # --- Project Management ---
        file_menu.addAction(mw.action_project_manager)

        file_menu.addSeparator()

        # --- Exit (destructive action, always last) ---
        file_menu.addAction(mw.action_exit)

        return file_menu

    def _create_edit_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Edit menu with logical groupings.

        Groups:
        - History (undo/redo)
        - Clipboard (cut/copy/paste/duplicate)
        - Destructive (delete)
        - Selection and search
        - Layout and alignment
        """
        edit_menu = menubar.addMenu("&Edit")

        # --- History Operations ---
        edit_menu.addAction(mw.action_undo)
        edit_menu.addAction(mw.action_redo)
        edit_menu.addAction(mw.action_reload)

        edit_menu.addSeparator()

        # --- Clipboard Operations ---
        edit_menu.addAction(mw.action_cut)
        edit_menu.addAction(mw.action_copy)
        edit_menu.addAction(mw.action_paste)
        edit_menu.addAction(mw.action_duplicate)

        edit_menu.addSeparator()

        # --- Destructive Operations (separated for safety) ---
        edit_menu.addAction(mw.action_delete)

        edit_menu.addSeparator()

        # --- Selection and Search ---
        edit_menu.addAction(mw.action_select_all)
        edit_menu.addAction(mw.action_find_node)
        edit_menu.addAction(mw.action_rename_node)

        edit_menu.addSeparator()

        # --- Layout and Alignment ---
        edit_menu.addAction(mw.action_auto_layout)
        edit_menu.addAction(mw.action_layout_selection)
        edit_menu.addAction(mw.action_toggle_grid_snap)

        return edit_menu

    def _create_view_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create View menu with logical groupings.

        Groups:
        - Panel visibility toggles
        - Minimap toggle
        - Performance settings
        - Dashboards (external views)
        """
        view_menu = menubar.addMenu("&View")

        # --- Panels ---
        view_menu.addAction(mw.action_toggle_panel)
        view_menu.addAction(mw.action_toggle_side_panel)

        view_menu.addSeparator()

        # --- Minimap ---
        view_menu.addAction(mw.action_toggle_minimap)

        view_menu.addSeparator()

        # --- Performance Settings ---
        view_menu.addAction(mw.action_high_performance_mode)

        view_menu.addSeparator()

        # --- Dashboards (open new windows/views) ---
        view_menu.addAction(mw.action_fleet_dashboard)
        view_menu.addAction(mw.action_performance_dashboard)

        view_menu.addSeparator()

        # --- Credentials Management ---
        view_menu.addAction(mw.action_credential_manager)

        # --- Layout ---
        view_menu.addSeparator()
        view_menu.addAction(mw.action_save_layout)
        view_menu.addAction(mw.action_reset_layout)

        # Store reference on MainWindow for DockCreator access
        mw._view_menu = view_menu
        return view_menu

    def _create_run_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Run menu with logical groupings.

        Groups:
        - Primary execution (Run/Pause/Stop)
        - Partial execution (Run To Node, Run This Node)
        - Trigger listening (Start/Stop Listening)
        """
        run_menu = menubar.addMenu("&Run")

        # --- Primary Execution Controls ---
        run_menu.addAction(mw.action_run)
        run_menu.addAction(mw.action_run_all)
        run_menu.addAction(mw.action_pause)
        run_menu.addAction(mw.action_stop)
        run_menu.addAction(mw.action_restart)

        run_menu.addSeparator()

        # --- Partial/Debug Execution ---
        run_menu.addAction(mw.action_run_to_node)
        run_menu.addAction(mw.action_run_single_node)

        run_menu.addSeparator()

        # --- Trigger Listening (event-driven execution) ---
        run_menu.addAction(mw.action_start_listening)
        run_menu.addAction(mw.action_stop_listening)

        return run_menu

    def _create_automation_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Automation menu with logical groupings.

        Groups:
        - Validation (workflow checks)
        - Recording (capture user actions)
        - Element picking (selector tools)
        - Canvas organization (frames, auto-connect)
        """
        automation_menu = menubar.addMenu("&Automation")

        # --- Validation ---
        automation_menu.addAction(mw.action_validate)

        automation_menu.addSeparator()

        # --- Recording ---
        automation_menu.addAction(mw.action_record_workflow)

        automation_menu.addSeparator()

        # --- Element Picking (selector tools) ---
        automation_menu.addAction(mw.action_pick_selector)
        automation_menu.addAction(mw.action_desktop_selector_builder)

        automation_menu.addSeparator()

        # --- Canvas Organization ---
        automation_menu.addAction(mw.action_create_frame)
        automation_menu.addAction(mw.action_auto_connect)

        automation_menu.addSeparator()

        # --- Quick Node Creation ---
        automation_menu.addAction(mw.action_quick_node_mode)
        automation_menu.addAction(mw.action_quick_node_config)

        return automation_menu

    def _create_help_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Help menu with logical groupings.

        Groups:
        - Documentation and learning
        - Settings and configuration
        - Application info (updates, about)
        """
        help_menu = menubar.addMenu("&Help")

        # --- Documentation and Learning ---
        help_menu.addAction(mw.action_documentation)
        help_menu.addAction(mw.action_keyboard_shortcuts)

        help_menu.addSeparator()

        # --- Settings ---
        help_menu.addAction(mw.action_preferences)

        help_menu.addSeparator()

        # --- Application Info ---
        help_menu.addAction(mw.action_check_updates)
        help_menu.addAction(mw.action_about)

        return help_menu
