"""
Action Factory for MainWindow.

This module provides a factory class for creating and configuring QActions
used in the MainWindow's menus, toolbar, and keyboard shortcuts.

Extracts ~400 lines of action creation code from MainWindow to improve
maintainability and reduce MainWindow's line count.
"""

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QKeySequence

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.canvas.main_window import MainWindow


class ActionFactory(QObject):
    """
    Factory for creating and managing MainWindow actions.

    This class centralizes all QAction creation, configuration, and
    hotkey loading for the MainWindow. It reduces code duplication
    and makes action management more maintainable.

    Attributes:
        actions: Dictionary of action_name -> QAction
        main_window: Reference to parent MainWindow

    Example:
        factory = ActionFactory(main_window)
        factory.create_all_actions()
        factory.load_hotkeys(hotkey_settings)

        # Access actions
        run_action = factory.actions["run"]
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the action factory.

        Args:
            main_window: Parent MainWindow instance
        """
        super().__init__(main_window)
        self._main_window = main_window
        self._actions: Dict[str, QAction] = {}

    @property
    def actions(self) -> Dict[str, QAction]:
        """Dictionary of all created actions."""
        return self._actions

    def create_all_actions(self) -> None:
        """Create all actions for the MainWindow."""
        self._create_file_actions()
        self._create_edit_actions()
        self._create_view_actions()
        self._create_workflow_actions()
        self._create_tool_actions()
        self._create_help_actions()

        logger.debug(f"ActionFactory: Created {len(self._actions)} actions")

    def _create_action(
        self,
        name: str,
        text: str,
        shortcut: Optional[str] = None,
        status_tip: Optional[str] = None,
        triggered: Optional[Callable] = None,
        checkable: bool = False,
        checked: bool = False,
        enabled: bool = True,
    ) -> QAction:
        """
        Create and register a QAction.

        Args:
            name: Internal action name for lookup
            text: Display text for the action
            shortcut: Keyboard shortcut (e.g., "Ctrl+S")
            status_tip: Status bar tooltip
            triggered: Callback function when action is triggered
            checkable: Whether action is checkable
            checked: Initial checked state
            enabled: Initial enabled state

        Returns:
            The created QAction
        """
        action = QAction(text, self._main_window)

        if shortcut:
            action.setShortcut(QKeySequence(shortcut))

        if status_tip:
            action.setStatusTip(status_tip)

        if triggered:
            action.triggered.connect(triggered)

        action.setCheckable(checkable)
        action.setChecked(checked)
        action.setEnabled(enabled)

        self._actions[name] = action
        return action

    def _create_file_actions(self) -> None:
        """Create File menu actions."""
        mw = self._main_window

        self._create_action(
            "new",
            "&New Workflow",
            shortcut=None,  # Uses StandardKey
            status_tip="Create a new workflow",
            triggered=mw._on_new_workflow,
        )
        self._actions["new"].setShortcut(QKeySequence.StandardKey.New)

        self._create_action(
            "new_from_template",
            "New from &Template...",
            shortcut="Ctrl+Shift+N",
            status_tip="Create a new workflow from a template",
            triggered=mw._on_new_from_template,
        )

        self._create_action(
            "open",
            "&Open Workflow...",
            shortcut=None,
            status_tip="Open an existing workflow",
            triggered=mw._on_open_workflow,
        )
        self._actions["open"].setShortcut(QKeySequence.StandardKey.Open)

        self._create_action(
            "import",
            "&Import Workflow...",
            shortcut="Ctrl+Shift+I",
            status_tip="Import nodes from another workflow into current workflow",
            triggered=mw._on_import_workflow,
        )

        self._create_action(
            "export_selected",
            "&Export Selected Nodes...",
            shortcut="Ctrl+Shift+E",
            status_tip="Export selected nodes to a workflow file",
            triggered=mw._on_export_selected,
        )

        self._create_action(
            "save",
            "&Save Workflow",
            shortcut=None,
            status_tip="Save the current workflow",
            triggered=mw._on_save_workflow,
        )
        self._actions["save"].setShortcut(QKeySequence.StandardKey.Save)

        self._create_action(
            "save_as",
            "Save Workflow &As...",
            shortcut=None,
            status_tip="Save the workflow with a new name",
            triggered=mw._on_save_as_workflow,
        )
        self._actions["save_as"].setShortcut(QKeySequence.StandardKey.SaveAs)

        self._create_action(
            "save_to_scenario",
            "Save to &Scenario",
            shortcut="Ctrl+Shift+S",
            status_tip="Save current workflow to the open scenario",
        )

        self._create_action(
            "exit",
            "E&xit",
            shortcut=None,
            status_tip="Exit the application",
            triggered=mw.close,
        )
        self._actions["exit"].setShortcut(QKeySequence.StandardKey.Quit)

    def _create_edit_actions(self) -> None:
        """Create Edit menu actions."""
        mw = self._main_window

        self._create_action(
            "find_node",
            "&Find Node...",
            shortcut=None,
            status_tip="Search for nodes in the canvas (Ctrl+F)",
            triggered=mw._on_find_node,
        )
        self._actions["find_node"].setShortcut(QKeySequence.StandardKey.Find)

        self._create_action(
            "undo",
            "&Undo",
            shortcut=None,
            status_tip="Undo the last action",
            enabled=False,
        )
        self._actions["undo"].setShortcut(QKeySequence.StandardKey.Undo)

        self._create_action(
            "redo",
            "&Redo",
            status_tip="Redo the last undone action (Ctrl+Y or Ctrl+Shift+Z)",
            enabled=False,
        )
        self._actions["redo"].setShortcuts(
            [QKeySequence.StandardKey.Redo, QKeySequence("Ctrl+Shift+Z")]
        )

        self._create_action(
            "delete",
            "&Delete",
            shortcut="X",
            status_tip="Delete selected nodes",
        )

        self._create_action(
            "cut",
            "Cu&t",
            shortcut=None,
            status_tip="Cut selected nodes",
        )
        self._actions["cut"].setShortcut(QKeySequence.StandardKey.Cut)

        self._create_action(
            "copy",
            "&Copy",
            shortcut=None,
            status_tip="Copy selected nodes",
        )
        self._actions["copy"].setShortcut(QKeySequence.StandardKey.Copy)

        self._create_action(
            "paste",
            "&Paste",
            shortcut=None,
            status_tip="Paste nodes",
        )
        self._actions["paste"].setShortcut(QKeySequence.StandardKey.Paste)

        self._create_action(
            "duplicate",
            "D&uplicate",
            shortcut="Ctrl+D",
            status_tip="Duplicate selected nodes",
        )

        self._create_action(
            "paste_workflow",
            "Paste Workflow JSON",
            shortcut="Ctrl+Shift+V",
            status_tip="Paste workflow JSON from clipboard and import nodes",
            triggered=mw._on_paste_workflow,
        )

        self._create_action(
            "select_all",
            "Select &All",
            shortcut=None,
            status_tip="Select all nodes",
        )
        self._actions["select_all"].setShortcut(QKeySequence.StandardKey.SelectAll)

        self._create_action(
            "deselect_all",
            "Deselect All",
            shortcut="Ctrl+Shift+A",
            status_tip="Deselect all nodes",
        )

        self._create_action(
            "select_nearest",
            "Select &Nearest Node",
            shortcut="2",
            status_tip="Select the nearest node to mouse cursor (2)",
            triggered=mw._on_select_nearest_node,
        )

        self._create_action(
            "toggle_disable",
            "&Disable Node",
            shortcut="4",
            status_tip="Disable/enable selected node - inputs bypass to outputs (4)",
            triggered=mw._on_toggle_disable_node,
        )

        self._create_action(
            "preferences",
            "&Preferences...",
            shortcut="Ctrl+,",
            status_tip="Configure application preferences",
            triggered=mw._on_preferences,
        )

    def _create_view_actions(self) -> None:
        """Create View menu actions."""
        mw = self._main_window

        self._create_action(
            "zoom_in",
            "Zoom &In",
            shortcut=None,
            status_tip="Zoom in",
        )
        self._actions["zoom_in"].setShortcut(QKeySequence.StandardKey.ZoomIn)

        self._create_action(
            "zoom_out",
            "Zoom &Out",
            shortcut=None,
            status_tip="Zoom out",
        )
        self._actions["zoom_out"].setShortcut(QKeySequence.StandardKey.ZoomOut)

        self._create_action(
            "zoom_reset",
            "&Reset Zoom",
            shortcut="Ctrl+0",
            status_tip="Reset zoom to 100%",
        )

        self._create_action(
            "fit_view",
            "&Fit to View",
            shortcut="Ctrl+F",
            status_tip="Fit all nodes in view",
        )

        self._create_action(
            "toggle_bottom_panel",
            "&Bottom Panel",
            shortcut="Ctrl+`",
            status_tip="Show/hide bottom panel (Variables, Output, Log, Validation)",
            triggered=mw._on_toggle_bottom_panel,
            checkable=True,
        )

        self._create_action(
            "toggle_variable_inspector",
            "Variable &Inspector",
            shortcut="Ctrl+Shift+V",
            status_tip="Show/hide variable inspector (real-time variable values)",
            triggered=mw._on_toggle_variable_inspector,
            checkable=True,
        )

        self._create_action(
            "validate",
            "&Validate Workflow",
            shortcut="Ctrl+Shift+B",
            status_tip="Validate current workflow",
            triggered=lambda: mw.validate_current_workflow(),
        )

        self._create_action(
            "toggle_minimap",
            "&Minimap",
            shortcut="Ctrl+M",
            status_tip="Show/hide minimap overview (Ctrl+M)",
            triggered=mw._on_toggle_minimap,
            checkable=True,
        )

        self._create_action(
            "auto_connect",
            "&Auto-Connect Nodes",
            status_tip=(
                "Automatically suggest connections while dragging nodes "
                "(right-click to connect/disconnect)"
            ),
            triggered=mw._on_toggle_auto_connect,
            checkable=True,
            checked=True,
        )

    def _create_workflow_actions(self) -> None:
        """Create Workflow menu actions."""
        mw = self._main_window

        self._create_action(
            "run",
            "\u25b6 Run",  # Unicode play symbol
            shortcut="F3",
            status_tip="Execute the entire workflow (F3)",
            triggered=mw._on_run_workflow,
        )

        self._create_action(
            "run_to_node",
            "\u25b7 To Node",  # Unicode play outline
            shortcut="F4",
            status_tip="Execute workflow up to selected node (F4)",
            triggered=mw._on_run_to_node,
        )

        self._create_action(
            "run_single_node",
            "\u2299 This Node",  # Unicode circled dot
            shortcut="F5",
            status_tip="Re-run only the selected node with existing inputs (F5)",
            triggered=mw._on_run_single_node,
        )

        self._create_action(
            "pause",
            "\u23f8 Pause",  # Unicode pause symbol
            shortcut="F6",
            status_tip="Pause/Resume workflow execution (F6)",
            triggered=mw._on_pause_workflow,
            checkable=True,
            enabled=False,
        )

        self._create_action(
            "stop",
            "\u25a0 Stop",  # Unicode stop symbol
            shortcut="F7",
            status_tip="Stop workflow execution (F7)",
            triggered=mw._on_stop_workflow,
            enabled=False,
        )

        self._create_action(
            "schedule",
            "&Schedule Workflow...",
            shortcut="Ctrl+Shift+H",
            status_tip="Schedule this workflow to run automatically (Ctrl+Shift+H)",
            triggered=mw._on_schedule_workflow,
        )

        self._create_action(
            "manage_schedules",
            "&Manage Schedules...",
            status_tip="View and manage all scheduled workflows",
            triggered=mw._on_manage_schedules,
        )

    def _create_tool_actions(self) -> None:
        """Create Tools menu actions."""
        mw = self._main_window

        self._create_action(
            "pick_selector",
            "\u2316 Pick",  # Unicode target
            shortcut="Ctrl+Shift+S",
            status_tip="Pick an element from the browser (Ctrl+Shift+S)",
            triggered=mw._on_pick_selector,
            enabled=False,
        )

        self._create_action(
            "record_workflow",
            "\u23fa Record",  # Unicode record symbol
            shortcut="Ctrl+Shift+R",
            status_tip="Record browser interactions as workflow (Ctrl+Shift+R)",
            triggered=mw._on_toggle_recording,
            checkable=True,
            enabled=False,
        )

        self._create_action(
            "hotkey_manager",
            "&Keyboard Shortcuts...",
            shortcut="Ctrl+K, Ctrl+S",
            status_tip="View and customize keyboard shortcuts",
            triggered=mw._on_open_hotkey_manager,
        )

        self._create_action(
            "desktop_selector_builder",
            "\U0001f3af Desktop Selector Builder",  # Target emoji
            shortcut="Ctrl+Shift+D",
            status_tip="Build desktop element selectors visually (Ctrl+Shift+D)",
            triggered=mw._on_open_desktop_selector_builder,
        )

        self._create_action(
            "create_frame",
            "\U0001f4cb Create Frame",  # Clipboard emoji
            shortcut="Shift+W",
            status_tip="Create a frame around selected nodes (Shift+W)",
            triggered=mw._on_create_frame,
        )

        self._create_action(
            "performance_dashboard",
            "\U0001f4ca Performance Dashboard",  # Chart emoji
            shortcut="Ctrl+Shift+P",
            status_tip="View performance metrics and statistics (Ctrl+Shift+P)",
            triggered=mw._on_open_performance_dashboard,
        )

        self._create_action(
            "command_palette",
            "Command Palette...",
            shortcut="Ctrl+Shift+P",
            status_tip="Open command palette to search actions (Ctrl+Shift+P)",
            triggered=mw._on_open_command_palette,
        )

    def _create_help_actions(self) -> None:
        """Create Help menu actions."""
        mw = self._main_window

        self._create_action(
            "about",
            "&About",
            status_tip="About CasareRPA",
            triggered=mw._on_about,
        )

    def load_hotkeys(self, hotkey_settings) -> None:
        """
        Load saved hotkeys and apply them to actions.

        Args:
            hotkey_settings: HotkeySettings instance with saved shortcuts
        """
        hotkey_action_map = {
            "new": "new",
            "open": "open",
            "save": "save",
            "save_as": "save_as",
            "exit": "exit",
            "undo": "undo",
            "redo": "redo",
            "cut": "cut",
            "copy": "copy",
            "paste": "paste",
            "delete": "delete",
            "select_all": "select_all",
            "deselect_all": "deselect_all",
            "zoom_in": "zoom_in",
            "zoom_out": "zoom_out",
            "zoom_reset": "zoom_reset",
            "fit_view": "fit_view",
            "run": "run",
            "pause": "pause",
            "stop": "stop",
            "create_frame": "create_frame",
            "hotkey_manager": "hotkey_manager",
        }

        for hotkey_name, action_name in hotkey_action_map.items():
            if action_name in self._actions:
                shortcuts = hotkey_settings.get_shortcuts(hotkey_name)
                if shortcuts:
                    sequences = [QKeySequence(s) for s in shortcuts]
                    self._actions[action_name].setShortcuts(sequences)

        logger.debug("ActionFactory: Hotkeys loaded")

    def get_action(self, name: str) -> Optional[QAction]:
        """
        Get action by name.

        Args:
            name: Action name

        Returns:
            QAction or None if not found
        """
        return self._actions.get(name)

    def set_actions_enabled(self, action_names: List[str], enabled: bool) -> None:
        """
        Enable or disable multiple actions at once.

        Args:
            action_names: List of action names to modify
            enabled: Whether to enable or disable
        """
        for name in action_names:
            if name in self._actions:
                self._actions[name].setEnabled(enabled)
