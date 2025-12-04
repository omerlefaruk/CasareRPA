"""
Action manager for MainWindow QActions.

Centralizes creation and management of all QAction instances.
"""

from typing import TYPE_CHECKING, Dict, Optional

from PySide6.QtGui import QAction, QKeySequence

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ActionManager:
    """
    Manages QAction creation and hotkey configuration.

    Responsibilities:
    - Create all QActions for menus and toolbars
    - Load and apply saved hotkey settings
    - Provide action lookup by name
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize action manager.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window
        self._actions: Dict[str, QAction] = {}

    def create_actions(self) -> None:
        """Create all actions for menus and toolbar."""
        mw = self._main_window

        # === FILE ACTIONS ===
        mw.action_new = self._create_action(
            "new",
            "&New Workflow",
            QKeySequence.StandardKey.New,
            "Create a new workflow",
            mw._on_new_workflow,
        )

        mw.action_open = self._create_action(
            "open",
            "&Open...",
            QKeySequence.StandardKey.Open,
            "Open an existing workflow",
            mw._on_open_workflow,
        )

        mw.action_save = self._create_action(
            "save",
            "&Save",
            QKeySequence.StandardKey.Save,
            "Save the current workflow",
            mw._on_save_workflow,
        )

        mw.action_save_as = self._create_action(
            "save_as",
            "Save &As...",
            QKeySequence.StandardKey.SaveAs,
            "Save the workflow with a new name",
            mw._on_save_as_workflow,
        )

        mw.action_save_as_scenario = self._create_action(
            "save_as_scenario",
            "Save as S&cenario...",
            QKeySequence("Ctrl+Shift+S"),
            "Save the workflow as a scenario in a project",
            mw._on_save_as_scenario,
        )

        mw.action_exit = self._create_action(
            "exit",
            "E&xit",
            QKeySequence.StandardKey.Quit,
            "Exit the application",
            mw.close,
        )

        # === EDIT ACTIONS ===
        mw.action_undo = self._create_action(
            "undo",
            "&Undo",
            QKeySequence.StandardKey.Undo,
            "Undo the last action",
            enabled=False,
        )

        mw.action_redo = self._create_action(
            "redo",
            "&Redo",
            QKeySequence.StandardKey.Redo,
            "Redo the last undone action",
            enabled=False,
        )
        mw.action_redo.setShortcuts(
            [QKeySequence.StandardKey.Redo, QKeySequence("Ctrl+Shift+Z")]
        )

        mw.action_cut = self._create_action(
            "cut", "Cu&t", QKeySequence.StandardKey.Cut, "Cut selected nodes"
        )

        mw.action_copy = self._create_action(
            "copy", "&Copy", QKeySequence.StandardKey.Copy, "Copy selected nodes"
        )

        mw.action_paste = self._create_action(
            "paste", "&Paste", QKeySequence.StandardKey.Paste, "Paste nodes"
        )

        mw.action_duplicate = self._create_action(
            "duplicate",
            "D&uplicate",
            QKeySequence("Ctrl+D"),
            "Duplicate selected nodes",
        )

        mw.action_delete = self._create_action(
            "delete", "&Delete", QKeySequence("Del"), "Delete selected nodes"
        )

        mw.action_select_all = self._create_action(
            "select_all",
            "Select &All",
            QKeySequence.StandardKey.SelectAll,
            "Select all nodes",
        )

        mw.action_find_node = self._create_action(
            "find_node",
            "&Find Node...",
            QKeySequence.StandardKey.Find,
            "Search for nodes in the canvas",
            mw._on_find_node,
        )

        # === NUMPAD HOTKEYS ===
        mw.action_get_exec_out = self._create_action(
            "get_exec_out",
            "Get &Exec Out",
            QKeySequence("3"),
            "Get nearest node's exec_out port (3)",
            mw._on_get_exec_out,
        )

        mw.action_disable_all_selected = self._create_action(
            "disable_all_selected",
            "Disable All &Selected",
            QKeySequence("5"),
            "Disable/enable all selected nodes (5)",
            mw._on_disable_all_selected,
        )

        mw.action_toggle_panel = self._create_action(
            "toggle_panel",
            "Toggle &Panel",
            QKeySequence("6"),
            "Show/hide bottom panel (6)",
            mw._on_toggle_panel,
            checkable=True,
        )

        # === VIEW ACTIONS ===
        mw.action_toggle_properties = self._create_action(
            "toggle_properties",
            "&Properties Panel",
            QKeySequence("Ctrl+P"),
            "Show/hide properties panel",
            mw._on_toggle_properties,
            checkable=True,
        )

        mw.action_toggle_variable_inspector = self._create_action(
            "toggle_variable_inspector",
            "&Variables Panel",
            QKeySequence("Ctrl+Shift+V"),
            "Show/hide variables panel",
            mw._on_toggle_variable_inspector,
            checkable=True,
        )

        mw.action_toggle_bottom_panel = self._create_action(
            "toggle_bottom_panel",
            "&Output Panel",
            QKeySequence("Ctrl+`"),
            "Show/hide output panel",
            mw._on_toggle_bottom_panel,
            checkable=True,
        )

        mw.action_toggle_minimap = self._create_action(
            "toggle_minimap",
            "&Minimap",
            QKeySequence("Ctrl+M"),
            "Show/hide minimap overview",
            mw._on_toggle_minimap,
            checkable=True,
        )

        mw.action_fleet_dashboard = self._create_action(
            "fleet_dashboard",
            "&Fleet Dashboard",
            QKeySequence("Ctrl+Shift+F"),
            "Open fleet management dashboard",
            mw._on_fleet_dashboard,
        )

        # === RUN ACTIONS ===
        # Standardized shortcuts (VS Code-like):
        # F5 = Run/Continue, F6 = Pause, F7 = Stop
        # F9 = Toggle breakpoint, Ctrl+F5 = Debug mode
        # F10 = Step over, F11 = Step into (future)
        mw.action_run = self._create_action(
            "run",
            "Run",
            QKeySequence("F5"),
            "Execute the workflow (F5)",
            mw._on_run_workflow,
        )

        mw.action_run_all = self._create_action(
            "run_all",
            "Run All Workflows",
            QKeySequence("Shift+F3"),
            "Execute all workflows on canvas concurrently (Shift+F3)",
            mw._on_run_all_workflows,
        )

        mw.action_pause = self._create_action(
            "pause",
            "Pause",
            QKeySequence("F6"),
            "Pause workflow execution (F6)",
            mw._on_pause_workflow,
            enabled=False,
            checkable=True,
        )

        mw.action_stop = self._create_action(
            "stop",
            "Stop",
            QKeySequence("F7"),
            "Stop workflow execution (F7)",
            mw._on_stop_workflow,
            enabled=False,
        )

        mw.action_start_listening = self._create_action(
            "start_listening",
            "Start Listening",
            QKeySequence("F9"),
            "Start listening for trigger events (F9)",
            mw._on_start_listening,
        )

        mw.action_stop_listening = self._create_action(
            "stop_listening",
            "Stop Listening",
            QKeySequence("Shift+F9"),
            "Stop listening for trigger events (Shift+F9)",
            mw._on_stop_listening,
            enabled=False,
        )

        # === AUTOMATION ACTIONS ===
        mw.action_validate = self._create_action(
            "validate",
            "&Validate",
            QKeySequence("Ctrl+B"),
            "Validate current workflow",
            lambda: mw.validate_current_workflow(),
        )

        mw.action_record_workflow = self._create_action(
            "record_workflow",
            "&Record Actions",
            QKeySequence("Ctrl+R"),
            "Record browser interactions",
            mw._on_toggle_recording,
            enabled=False,
            checkable=True,
        )

        mw.action_pick_selector = self._create_action(
            "pick_selector",
            "Pick &Browser Element",
            QKeySequence("Ctrl+Shift+E"),
            "Pick an element from the browser",
            mw._on_pick_selector,
            enabled=False,
        )

        mw.action_desktop_selector_builder = self._create_action(
            "desktop_selector_builder",
            "Pick &Desktop Element",
            QKeySequence("Ctrl+Shift+D"),
            "Build desktop element selectors",
            mw._on_open_desktop_selector_builder,
        )

        mw.action_create_frame = self._create_action(
            "create_frame",
            "Create &Frame",
            QKeySequence("Shift+W"),
            "Create a frame around selected nodes",
            mw._on_create_frame,
        )

        mw.action_auto_connect = self._create_action(
            "auto_connect",
            "Auto-&Connect",
            QKeySequence("Ctrl+Shift+A"),
            "Auto-suggest connections when dragging nodes (Ctrl+Shift+A)",
            mw._on_toggle_auto_connect,
            checkable=True,
        )
        mw.action_auto_connect.setChecked(True)  # Enabled by default

        # === HELP ACTIONS ===
        mw.action_documentation = self._create_action(
            "documentation",
            "&Documentation",
            QKeySequence("F1"),
            "Open documentation in browser",
            mw._on_show_documentation,
        )

        mw.action_keyboard_shortcuts = self._create_action(
            "keyboard_shortcuts",
            "&Keyboard Shortcuts...",
            QKeySequence("Ctrl+K, Ctrl+S"),
            "View and edit keyboard shortcuts",
            mw._on_open_hotkey_manager,
        )

        mw.action_preferences = self._create_action(
            "preferences",
            "&Preferences...",
            QKeySequence("Ctrl+,"),
            "Configure application preferences",
            mw._on_preferences,
        )

        mw.action_check_updates = self._create_action(
            "check_updates",
            "Check for &Updates",
            None,
            "Check for application updates",
            mw._on_check_updates,
        )

        mw.action_about = self._create_action(
            "about", "&About", None, "About CasareRPA", mw._on_about
        )

        # === LAYOUT ACTIONS ===
        mw.action_save_layout = self._create_action(
            "save_layout",
            "Save &Layout",
            QKeySequence("Ctrl+Shift+L"),
            "Save current UI layout (window positions, panel sizes)",
            mw._on_save_ui_layout,
        )

        # === PROJECT ACTIONS ===
        mw.action_project_manager = self._create_action(
            "project_manager",
            "&Project Manager...",
            QKeySequence("Ctrl+Shift+P"),
            "Open project manager",
            mw._on_project_manager,
        )

        # === CREDENTIAL ACTIONS ===
        mw.action_credential_manager = self._create_action(
            "credential_manager",
            "&Credential Manager...",
            QKeySequence("Ctrl+Shift+K"),
            "Manage API keys and credentials",
            mw._on_credential_manager,
        )

        # === PERFORMANCE ACTIONS ===
        mw.action_performance_dashboard = self._create_action(
            "performance_dashboard",
            "Performance Dashboard",
            QKeySequence("Ctrl+Alt+P"),
            "View performance metrics and statistics",
            mw._on_open_performance_dashboard,
        )

        # Apply saved hotkeys
        self._load_hotkeys()

    def _create_action(
        self,
        name: str,
        text: str,
        shortcut: Optional[QKeySequence] = None,
        status_tip: str = "",
        handler=None,
        enabled: bool = True,
        checkable: bool = False,
    ) -> QAction:
        """
        Create and register a QAction.

        Args:
            name: Internal action name for lookup
            text: Display text
            shortcut: Keyboard shortcut
            status_tip: Status bar tip
            handler: Slot to connect to triggered signal
            enabled: Initial enabled state
            checkable: Whether action is checkable

        Returns:
            Created QAction
        """
        action = QAction(text, self._main_window)
        if shortcut:
            action.setShortcut(shortcut)
        if status_tip:
            action.setStatusTip(status_tip)
        if handler:
            action.triggered.connect(handler)
        action.setEnabled(enabled)
        action.setCheckable(checkable)

        # Add action to main window so shortcuts work globally
        self._main_window.addAction(action)

        self._actions[name] = action
        return action

    def _load_hotkeys(self) -> None:
        """Load and apply saved hotkeys to actions."""
        from casare_rpa.utils.hotkey_settings import get_hotkey_settings

        hotkey_settings = get_hotkey_settings()
        mw = self._main_window

        action_map = {
            "new": mw.action_new,
            "open": mw.action_open,
            "save": mw.action_save,
            "save_as": mw.action_save_as,
            "exit": mw.action_exit,
            "undo": mw.action_undo,
            "redo": mw.action_redo,
            "cut": mw.action_cut,
            "copy": mw.action_copy,
            "paste": mw.action_paste,
            "delete": mw.action_delete,
            "select_all": mw.action_select_all,
            "run": mw.action_run,
            "pause": mw.action_pause,
            "stop": mw.action_stop,
            "create_frame": mw.action_create_frame,
            "auto_connect": mw.action_auto_connect,
            "get_exec_out": mw.action_get_exec_out,
            "disable_all_selected": mw.action_disable_all_selected,
            "toggle_panel": mw.action_toggle_panel,
        }

        for action_name, action in action_map.items():
            shortcuts = hotkey_settings.get_shortcuts(action_name)
            if shortcuts:
                sequences = [QKeySequence(s) for s in shortcuts]
                action.setShortcuts(sequences)

    def get_action(self, name: str) -> Optional[QAction]:
        """
        Get action by name.

        Args:
            name: Action name

        Returns:
            QAction or None if not found
        """
        return self._actions.get(name)

    def get_all_actions(self) -> Dict[str, QAction]:
        """
        Get all registered actions.

        Returns:
            Dictionary of action name to QAction
        """
        return self._actions.copy()
