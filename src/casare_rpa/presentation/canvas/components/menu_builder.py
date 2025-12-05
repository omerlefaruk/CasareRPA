"""
Menu builder for MainWindow menu bar.

Centralizes menu creation and structure.
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenu

if TYPE_CHECKING:
    from ..main_window import MainWindow


class MenuBuilder:
    """
    Builds the menu bar structure for MainWindow.

    Responsibilities:
    - Create menu bar with 6 menus
    - Organize actions into logical groups
    - Handle recent files menu
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize menu builder.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

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
        mw._recent_files_menu = file_menu.addMenu("Recent Files")

        file_menu.addSeparator()

        # --- Save Operations ---
        file_menu.addAction(mw.action_save)
        file_menu.addAction(mw.action_save_as)
        file_menu.addAction(mw.action_save_as_scenario)

        file_menu.addSeparator()

        # --- Project Management ---
        file_menu.addAction(mw.action_project_manager)

        file_menu.addSeparator()

        # --- Migration Utilities ---
        file_menu.addAction(mw.action_migrate_workflow)

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
        """
        edit_menu = menubar.addMenu("&Edit")

        # --- History Operations ---
        edit_menu.addAction(mw.action_undo)
        edit_menu.addAction(mw.action_redo)

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

        return edit_menu

    def _create_view_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create View menu with logical groupings.

        Groups:
        - Panel toggles (core UI panels)
        - Layout management
        - Dashboards (external views)
        """
        view_menu = menubar.addMenu("&View")

        # --- Panels Submenu ---
        panels_menu = view_menu.addMenu("&Panels")
        panels_menu.addAction(mw.action_toggle_bottom_panel)
        panels_menu.addSeparator()
        panels_menu.addAction(mw.action_toggle_minimap)

        view_menu.addSeparator()

        # --- Layout Management ---
        view_menu.addAction(mw.action_save_layout)

        view_menu.addSeparator()

        # --- Dashboards (open new windows/views) ---
        view_menu.addAction(mw.action_fleet_dashboard)
        view_menu.addAction(mw.action_performance_dashboard)

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

        # --- Settings and Configuration ---
        help_menu.addAction(mw.action_credential_manager)
        help_menu.addAction(mw.action_preferences)

        help_menu.addSeparator()

        # --- Application Info ---
        help_menu.addAction(mw.action_check_updates)
        help_menu.addAction(mw.action_about)

        return help_menu
