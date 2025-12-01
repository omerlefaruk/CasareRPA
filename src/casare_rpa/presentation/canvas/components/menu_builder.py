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
        """Create File menu (8 items)."""
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(mw.action_new)
        file_menu.addAction(mw.action_open)
        mw._recent_files_menu = file_menu.addMenu("Recent Files")
        file_menu.addSeparator()
        file_menu.addAction(mw.action_save)
        file_menu.addAction(mw.action_save_as)
        file_menu.addAction(mw.action_save_as_scenario)
        file_menu.addSeparator()
        file_menu.addAction(mw.action_exit)
        return file_menu

    def _create_edit_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Edit menu (10 items)."""
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(mw.action_undo)
        edit_menu.addAction(mw.action_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(mw.action_cut)
        edit_menu.addAction(mw.action_copy)
        edit_menu.addAction(mw.action_paste)
        edit_menu.addAction(mw.action_duplicate)
        edit_menu.addAction(mw.action_delete)
        edit_menu.addSeparator()
        edit_menu.addAction(mw.action_select_all)
        edit_menu.addAction(mw.action_find_node)
        return edit_menu

    def _create_view_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create View menu (8 items)."""
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(mw.action_zoom_in)
        view_menu.addAction(mw.action_zoom_out)
        view_menu.addAction(mw.action_zoom_reset)
        view_menu.addAction(mw.action_fit_view)
        view_menu.addSeparator()
        view_menu.addAction(mw.action_toggle_properties)
        view_menu.addAction(mw.action_toggle_variable_inspector)
        view_menu.addAction(mw.action_toggle_bottom_panel)
        view_menu.addAction(mw.action_toggle_minimap)
        # Store reference on MainWindow for DockCreator access
        mw._view_menu = view_menu
        return view_menu

    def _create_run_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Run menu (6 items)."""
        run_menu = menubar.addMenu("&Run")
        run_menu.addAction(mw.action_run)
        run_menu.addAction(mw.action_pause)
        run_menu.addAction(mw.action_stop)
        run_menu.addSeparator()
        run_menu.addAction(mw.action_debug)
        run_menu.addSeparator()
        run_menu.addAction(mw.action_start_listening)
        run_menu.addAction(mw.action_stop_listening)
        return run_menu

    def _create_automation_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Automation menu (6 items)."""
        automation_menu = menubar.addMenu("&Automation")
        automation_menu.addAction(mw.action_validate)
        automation_menu.addSeparator()
        automation_menu.addAction(mw.action_record_workflow)
        automation_menu.addAction(mw.action_pick_selector)
        automation_menu.addAction(mw.action_desktop_selector_builder)
        automation_menu.addSeparator()
        automation_menu.addAction(mw.action_schedule)
        return automation_menu

    def _create_help_menu(self, menubar, mw: "MainWindow") -> QMenu:
        """Create Help menu (5 items)."""
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(mw.action_documentation)
        help_menu.addAction(mw.action_keyboard_shortcuts)
        help_menu.addSeparator()
        help_menu.addAction(mw.action_preferences)
        help_menu.addAction(mw.action_check_updates)
        help_menu.addAction(mw.action_about)
        return help_menu
