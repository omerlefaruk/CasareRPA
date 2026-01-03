"""
ActionManagerV2 - Centralized action/shortcut management for NewMainWindow.

Epic 1.2: ActionManagerV2 - Centralized Action/Shortcut Management
- Single source of truth for 63 application actions
- Persistent shortcut customization via QSettings (IniFormat)
- THEME_V2/TOKENS_V2 styling only (no hardcoded colors)
- Compatible with IMainWindow interface protocol
- Support for action state updates (enable/disable)

Usage:
    from casare_rpa.presentation.canvas.ui.chrome import ActionManagerV2

    manager = ActionManagerV2(main_window)
    manager.register_all_actions()

    # Get action by name
    action = manager.get_action("run")
    if action:
        action.triggered.connect(handle_run)

    # Enable/disable actions by category
    manager.enable_category(ActionCategory.RUN)
    manager.disable_category(ActionCategory.EDIT)

    # Customize shortcuts
    manager.set_shortcut("run", "Ctrl+R")

See: .brain/plans/epic-1-2-action-manager-v2-20251230.md
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.interfaces import IMainWindow


def _get_shortcuts_settings_path() -> Path:
    """Get the path for shortcuts settings file."""
    from casare_rpa.utils.config import CONFIG_DIR

    return CONFIG_DIR / "shortcuts.ini"


class ActionCategory(Enum):
    """
    Action categories for batch enable/disable operations.

    Categories group related actions for state management:
    - FILE: New, Open, Save, Exit
    - EDIT: Undo, Redo, Cut, Copy, Paste, Delete
    - VIEW: Zoom, Pan, Minimap, Focus
    - RUN: Execute, Pause, Stop, Restart
    - NODE: Create, Delete, Connect, Layout
    - PANEL: Toggle panels, docks
    - AUTOMATION: Record, Pick, Validate
    - HELP: Docs, Preferences, About
    - PROJECT: Project manager
    - CREDENTIALS: Credential manager
    - PERFORMANCE: Dashboard, high-perf mode
    - AI: AI assistant
    """

    FILE = auto()
    EDIT = auto()
    VIEW = auto()
    RUN = auto()
    NODE = auto()
    PANEL = auto()
    AUTOMATION = auto()
    HELP = auto()
    PROJECT = auto()
    CREDENTIALS = auto()
    PERFORMANCE = auto()
    AI = auto()


# Default shortcuts for all actions (VS Code-like standards)
DEFAULT_SHORTCUTS: dict[str, str | list[str]] = {
    # === FILE ===
    "new": QKeySequence.StandardKey.New,
    "open": QKeySequence.StandardKey.Open,
    "reload": "Ctrl+Shift+R",
    "save": QKeySequence.StandardKey.Save,
    "save_as": QKeySequence.StandardKey.SaveAs,
    "exit": QKeySequence.StandardKey.Quit,
    "save_layout": "Ctrl+Shift+L",
    "reset_layout": None,
    # === EDIT ===
    "undo": QKeySequence.StandardKey.Undo,
    "redo": [QKeySequence.StandardKey.Redo, "Ctrl+Shift+Z"],
    "cut": QKeySequence.StandardKey.Cut,
    "copy": QKeySequence.StandardKey.Copy,
    "paste": QKeySequence.StandardKey.Paste,
    "duplicate": "Ctrl+D",
    "delete": "Del",
    "select_all": QKeySequence.StandardKey.SelectAll,
    "find_node": QKeySequence.StandardKey.Find,
    "rename_node": "F2",
    # === VIEW ===
    "focus_view": "F",
    "home_all": "G",
    "toggle_minimap": "Ctrl+M",
    "zoom_in": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "zoom_reset": "Ctrl+0",
    "toggle_panel": "6",
    "toggle_side_panel": "7",
    "fleet_dashboard": "Ctrl+Shift+F",
    # === RUN ===
    "run": "F5",
    "run_all": "Shift+F3",
    "pause": "F6",
    "stop": "F7",
    "restart": "F8",
    "run_to_node": "Ctrl+F4",
    "run_single_node": "Ctrl+F10",
    "start_listening": "F9",
    "stop_listening": "Shift+F9",
    # === NODE ===
    "toggle_collapse": "1",
    "select_nearest": "2",
    "get_exec_out": "3",
    "toggle_disable": "4",
    "disable_all_selected": "5",
    "toggle_cache": "Ctrl+K",
    "create_frame": "Shift+W",
    "auto_connect": "Ctrl+Shift+A",
    "toggle_grid_snap": "Ctrl+Shift+G",
    "auto_layout": "Ctrl+L",
    "layout_selection": None,
    "quick_node_mode": "Ctrl+Shift+Q",
    "quick_node_config": "Ctrl+Alt+Q",
    # === AUTOMATION ===
    "validate": "Ctrl+B",
    "record_workflow": "Ctrl+R",
    "pick_selector": "Ctrl+Shift+E",
    "desktop_selector_builder": "Ctrl+Shift+D",
    # === HELP ===
    "documentation": "F1",
    "keyboard_shortcuts": ["Ctrl+K", "Ctrl+S"],
    "preferences": "Ctrl+,",
    "check_updates": None,
    "about": None,
    # === PROJECT ===
    "project_manager": "Ctrl+Shift+P",
    # === CREDENTIALS ===
    "credential_manager": "Ctrl+Alt+C",
    # === PERFORMANCE ===
    "performance_dashboard": "Ctrl+Alt+P",
    "high_performance_mode": None,
    # === AI ===
    "ai_assistant": "Ctrl+Shift+G",
}


class ActionManagerV2(QObject):
    """
    Centralized action and keyboard shortcut manager for NewMainWindow v2.

    Responsibilities:
    - Register all QAction instances with defaults
    - Load/save custom shortcuts via QSettings
    - Provide action lookup by name
    - Batch enable/disable actions by category
    - Emit signal on shortcut changes

    Signals:
        shortcut_changed: Emitted when a shortcut is customized
            Args:
                action_name: Name of the action with changed shortcut
                old_shortcut: Previous shortcut string
                new_shortcut: New shortcut string

    Attributes:
        categories: Maps action names to ActionCategory for batch operations
    """

    # Signals
    shortcut_changed = Signal(str, str, str)  # action_name, old_shortcut, new_shortcut

    # Settings keys
    _SETTINGS_GROUP = "shortcuts"
    _VERSION_KEY = "version"
    _CURRENT_VERSION = 1

    def __init__(self, main_window: IMainWindow) -> None:
        """
        Initialize action manager.

        Args:
            main_window: IMainWindow implementation (NewMainWindow or MainWindow)
        """
        super().__init__()
        self._main_window: IMainWindow = main_window
        self._actions: dict[str, QAction] = {}
        self._categories: dict[str, ActionCategory] = {}

        # QSettings for persistence (IniFormat with explicit file path)
        settings_path = _get_shortcuts_settings_path()
        self._settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

        # Track registered shortcuts for conflict detection
        self._custom_shortcuts: dict[str, str] = {}

        logger.debug("ActionManagerV2 initialized")

    def register_all_actions(self) -> None:
        """
        Register all 63 application actions with defaults.

        Creates QActions for all standard operations and adds them
        to the main window for global shortcut handling.

        Actions must be connected to handlers after registration.
        """
        # === FILE ACTIONS ===
        self._register_action(
            name="new",
            text="&New Workflow",
            shortcut=DEFAULT_SHORTCUTS["new"],
            status_tip="Create a new workflow (Ctrl+N)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="open",
            text="&Open...",
            shortcut=DEFAULT_SHORTCUTS["open"],
            status_tip="Open an existing workflow (Ctrl+O)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="reload",
            text="&Reload",
            shortcut=DEFAULT_SHORTCUTS["reload"],
            status_tip="Reload current workflow from disk (Ctrl+Shift+R)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="save",
            text="&Save",
            shortcut=DEFAULT_SHORTCUTS["save"],
            status_tip="Save the current workflow (Ctrl+S)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="save_as",
            text="Save &As...",
            shortcut=DEFAULT_SHORTCUTS["save_as"],
            status_tip="Save the workflow with a new name (Ctrl+Shift+S)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="exit",
            text="E&xit",
            shortcut=DEFAULT_SHORTCUTS["exit"],
            status_tip="Exit the application (Ctrl+Q)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="save_layout",
            text="Save &Layout",
            shortcut=DEFAULT_SHORTCUTS["save_layout"],
            status_tip="Save current UI layout (Ctrl+Shift+L)",
            category=ActionCategory.FILE,
        )

        self._register_action(
            name="reset_layout",
            text="Reset &Default Layout",
            shortcut=DEFAULT_SHORTCUTS["reset_layout"],
            status_tip="Reset UI layout to factory defaults",
            category=ActionCategory.FILE,
        )

        # === EDIT ACTIONS ===
        self._register_action(
            name="undo",
            text="&Undo",
            shortcut=DEFAULT_SHORTCUTS["undo"],
            status_tip="Undo the last action (Ctrl+Z)",
            category=ActionCategory.EDIT,
            enabled=False,
        )

        self._register_action(
            name="redo",
            text="&Redo",
            shortcut=DEFAULT_SHORTCUTS["redo"],
            status_tip="Redo the last undone action (Ctrl+Y)",
            category=ActionCategory.EDIT,
            enabled=False,
        )

        self._register_action(
            name="cut",
            text="Cu&t",
            shortcut=DEFAULT_SHORTCUTS["cut"],
            status_tip="Cut selected nodes (Ctrl+X)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="copy",
            text="&Copy",
            shortcut=DEFAULT_SHORTCUTS["copy"],
            status_tip="Copy selected nodes (Ctrl+C)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="paste",
            text="&Paste",
            shortcut=DEFAULT_SHORTCUTS["paste"],
            status_tip="Paste nodes (Ctrl+V)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="duplicate",
            text="D&uplicate",
            shortcut=DEFAULT_SHORTCUTS["duplicate"],
            status_tip="Duplicate selected nodes (Ctrl+D)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="delete",
            text="&Delete",
            shortcut=DEFAULT_SHORTCUTS["delete"],
            status_tip="Delete selected nodes (Del)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="select_all",
            text="Select &All",
            shortcut=DEFAULT_SHORTCUTS["select_all"],
            status_tip="Select all nodes (Ctrl+A)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="find_node",
            text="&Find Node...",
            shortcut=DEFAULT_SHORTCUTS["find_node"],
            status_tip="Search for nodes in the canvas (Ctrl+F)",
            category=ActionCategory.EDIT,
        )

        self._register_action(
            name="rename_node",
            text="&Rename Node",
            shortcut=DEFAULT_SHORTCUTS["rename_node"],
            status_tip="Rename selected node (F2)",
            category=ActionCategory.EDIT,
        )

        # === VIEW ACTIONS ===
        self._register_action(
            name="focus_view",
            text="&Focus View",
            shortcut=DEFAULT_SHORTCUTS["focus_view"],
            status_tip="Zoom to selected node and center it (F)",
            category=ActionCategory.VIEW,
        )

        self._register_action(
            name="home_all",
            text="&Home All",
            shortcut=DEFAULT_SHORTCUTS["home_all"],
            status_tip="Fit all nodes in view (G)",
            category=ActionCategory.VIEW,
        )

        self._register_action(
            name="toggle_minimap",
            text="&Minimap",
            shortcut=DEFAULT_SHORTCUTS["toggle_minimap"],
            status_tip="Show/hide minimap overview (Ctrl+M)",
            category=ActionCategory.VIEW,
            checkable=True,
        )

        self._register_action(
            name="zoom_in",
            text="Zoom &In",
            shortcut=DEFAULT_SHORTCUTS["zoom_in"],
            status_tip="Zoom in (Ctrl++)",
            category=ActionCategory.VIEW,
        )

        self._register_action(
            name="zoom_out",
            text="Zoom &Out",
            shortcut=DEFAULT_SHORTCUTS["zoom_out"],
            status_tip="Zoom out (Ctrl+-)",
            category=ActionCategory.VIEW,
        )

        self._register_action(
            name="zoom_reset",
            text="Zoom &Reset",
            shortcut=DEFAULT_SHORTCUTS["zoom_reset"],
            status_tip="Reset zoom to 100% (Ctrl+0)",
            category=ActionCategory.VIEW,
        )

        self._register_action(
            name="toggle_panel",
            text="Toggle &Panel",
            shortcut=DEFAULT_SHORTCUTS["toggle_panel"],
            status_tip="Show/hide bottom panel (6)",
            category=ActionCategory.VIEW,
            checkable=True,
        )

        self._register_action(
            name="toggle_side_panel",
            text="Toggle Side &Panel",
            shortcut=DEFAULT_SHORTCUTS["toggle_side_panel"],
            status_tip="Show/hide unified side panel (7)",
            category=ActionCategory.VIEW,
            checkable=True,
        )

        self._register_action(
            name="fleet_dashboard",
            text="&Fleet Dashboard",
            shortcut=DEFAULT_SHORTCUTS["fleet_dashboard"],
            status_tip="Open fleet management dashboard (Ctrl+Shift+F)",
            category=ActionCategory.VIEW,
        )

        # === RUN ACTIONS ===
        self._register_action(
            name="run",
            text="Run",
            shortcut=DEFAULT_SHORTCUTS["run"],
            status_tip="Execute the workflow (F5)",
            category=ActionCategory.RUN,
        )

        self._register_action(
            name="run_all",
            text="Run All Workflows",
            shortcut=DEFAULT_SHORTCUTS["run_all"],
            status_tip="Execute all workflows on canvas concurrently (Shift+F3)",
            category=ActionCategory.RUN,
        )

        self._register_action(
            name="pause",
            text="Pause",
            shortcut=DEFAULT_SHORTCUTS["pause"],
            status_tip="Pause workflow execution (F6)",
            category=ActionCategory.RUN,
            enabled=False,
            checkable=True,
        )

        self._register_action(
            name="stop",
            text="Stop",
            shortcut=DEFAULT_SHORTCUTS["stop"],
            status_tip="Stop workflow execution (F7)",
            category=ActionCategory.RUN,
            enabled=False,
        )

        self._register_action(
            name="restart",
            text="Restart",
            shortcut=DEFAULT_SHORTCUTS["restart"],
            status_tip="Restart workflow - stop, reset, and run fresh (F8)",
            category=ActionCategory.RUN,
        )

        self._register_action(
            name="run_to_node",
            text="Run To Node",
            shortcut=DEFAULT_SHORTCUTS["run_to_node"],
            status_tip="Execute workflow up to selected node (Ctrl+F4)",
            category=ActionCategory.RUN,
        )

        self._register_action(
            name="run_single_node",
            text="Run This Node",
            shortcut=DEFAULT_SHORTCUTS["run_single_node"],
            status_tip="Re-run only the selected node (Ctrl+F10)",
            category=ActionCategory.RUN,
        )

        self._register_action(
            name="start_listening",
            text="Start Listening",
            shortcut=DEFAULT_SHORTCUTS["start_listening"],
            status_tip="Start listening for trigger events (F9)",
            category=ActionCategory.RUN,
        )

        self._register_action(
            name="stop_listening",
            text="Stop Listening",
            shortcut=DEFAULT_SHORTCUTS["stop_listening"],
            status_tip="Stop listening for trigger events (Shift+F9)",
            category=ActionCategory.RUN,
            enabled=False,
        )

        # === NODE ACTIONS ===
        self._register_action(
            name="toggle_collapse",
            text="&Collapse/Expand Nearest",
            shortcut=DEFAULT_SHORTCUTS["toggle_collapse"],
            status_tip="Collapse/expand nearest node to mouse cursor (1)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="select_nearest",
            text="Select &Nearest Node",
            shortcut=DEFAULT_SHORTCUTS["select_nearest"],
            status_tip="Select the nearest node to mouse cursor (2)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="get_exec_out",
            text="Get &Exec Out",
            shortcut=DEFAULT_SHORTCUTS["get_exec_out"],
            status_tip="Get nearest node's exec_out port (3)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="toggle_disable",
            text="&Disable Node",
            shortcut=DEFAULT_SHORTCUTS["toggle_disable"],
            status_tip="Disable/enable nearest node to mouse (4)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="disable_all_selected",
            text="Disable All &Selected",
            shortcut=DEFAULT_SHORTCUTS["disable_all_selected"],
            status_tip="Disable/enable all selected nodes (5)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="toggle_cache",
            text="Toggle &Cache",
            shortcut=DEFAULT_SHORTCUTS["toggle_cache"],
            status_tip="Enable/disable caching on nearest node (Ctrl+K)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="create_frame",
            text="Create &Frame",
            shortcut=DEFAULT_SHORTCUTS["create_frame"],
            status_tip="Create a frame around selected nodes (Shift+W)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="auto_connect",
            text="Auto-&Connect",
            shortcut=DEFAULT_SHORTCUTS["auto_connect"],
            status_tip="Auto-suggest connections when dragging nodes (Ctrl+Shift+A)",
            category=ActionCategory.NODE,
            checkable=True,
            checked=True,  # Enabled by default
        )

        self._register_action(
            name="toggle_grid_snap",
            text="Snap to &Grid",
            shortcut=DEFAULT_SHORTCUTS["toggle_grid_snap"],
            status_tip="Toggle snap-to-grid mode (Ctrl+Shift+G)",
            category=ActionCategory.NODE,
            checkable=True,
            checked=True,  # Enabled by default
        )

        self._register_action(
            name="auto_layout",
            text="Auto-&Layout",
            shortcut=DEFAULT_SHORTCUTS["auto_layout"],
            status_tip="Automatically arrange all nodes (Ctrl+L)",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="layout_selection",
            text="Layout &Selection",
            shortcut=DEFAULT_SHORTCUTS["layout_selection"],
            status_tip="Automatically arrange selected nodes",
            category=ActionCategory.NODE,
        )

        self._register_action(
            name="quick_node_mode",
            text="&Quick Node Mode",
            shortcut=DEFAULT_SHORTCUTS["quick_node_mode"],
            status_tip="Toggle hotkey-based quick node creation (Ctrl+Shift+Q)",
            category=ActionCategory.NODE,
            checkable=True,
            checked=True,  # Sync with QuickNodeManager
        )

        self._register_action(
            name="quick_node_config",
            text="Quick Node &Hotkeys...",
            shortcut=DEFAULT_SHORTCUTS["quick_node_config"],
            status_tip="Configure quick node hotkey bindings (Ctrl+Alt+Q)",
            category=ActionCategory.NODE,
        )

        # === AUTOMATION ACTIONS ===
        self._register_action(
            name="validate",
            text="&Validate",
            shortcut=DEFAULT_SHORTCUTS["validate"],
            status_tip="Validate current workflow (Ctrl+B)",
            category=ActionCategory.AUTOMATION,
        )

        self._register_action(
            name="record_workflow",
            text="Record &Browser",
            shortcut=DEFAULT_SHORTCUTS["record_workflow"],
            status_tip="Record browser interactions as workflow (Ctrl+R)",
            category=ActionCategory.AUTOMATION,
            enabled=False,
            checkable=True,
        )

        self._register_action(
            name="pick_selector",
            text="Pick &Element",
            shortcut=DEFAULT_SHORTCUTS["pick_selector"],
            status_tip="Pick element (Browser, Desktop, OCR, Image) (Ctrl+Shift+E)",
            category=ActionCategory.AUTOMATION,
        )

        self._register_action(
            name="desktop_selector_builder",
            text="Pick &Desktop Element",
            shortcut=DEFAULT_SHORTCUTS["desktop_selector_builder"],
            status_tip="Pick desktop element (legacy) (Ctrl+Shift+D)",
            category=ActionCategory.AUTOMATION,
        )

        # === HELP ACTIONS ===
        self._register_action(
            name="documentation",
            text="&Documentation",
            shortcut=DEFAULT_SHORTCUTS["documentation"],
            status_tip="Open documentation in browser (F1)",
            category=ActionCategory.HELP,
        )

        self._register_action(
            name="keyboard_shortcuts",
            text="&Keyboard Shortcuts...",
            shortcut=DEFAULT_SHORTCUTS["keyboard_shortcuts"],
            status_tip="View and edit keyboard shortcuts (Ctrl+K, Ctrl+S)",
            category=ActionCategory.HELP,
        )

        self._register_action(
            name="preferences",
            text="&Preferences...",
            shortcut=DEFAULT_SHORTCUTS["preferences"],
            status_tip="Configure application preferences (Ctrl+,)",
            category=ActionCategory.HELP,
        )

        self._register_action(
            name="check_updates",
            text="Check for &Updates",
            shortcut=DEFAULT_SHORTCUTS["check_updates"],
            status_tip="Check for application updates",
            category=ActionCategory.HELP,
        )

        self._register_action(
            name="about",
            text="&About",
            shortcut=DEFAULT_SHORTCUTS["about"],
            status_tip="About CasareRPA",
            category=ActionCategory.HELP,
        )

        # === PROJECT ACTIONS ===
        self._register_action(
            name="project_manager",
            text="&Project Manager...",
            shortcut=DEFAULT_SHORTCUTS["project_manager"],
            status_tip="Open project manager (Ctrl+Shift+P)",
            category=ActionCategory.PROJECT,
        )

        # === CREDENTIALS ACTIONS ===
        self._register_action(
            name="credential_manager",
            text="&Credentials...",
            shortcut=DEFAULT_SHORTCUTS["credential_manager"],
            status_tip="Manage API keys and credentials (Ctrl+Alt+C)",
            category=ActionCategory.CREDENTIALS,
        )

        # === PERFORMANCE ACTIONS ===
        self._register_action(
            name="performance_dashboard",
            text="Performance Dashboard",
            shortcut=DEFAULT_SHORTCUTS["performance_dashboard"],
            status_tip="View performance metrics and statistics (Ctrl+Alt+P)",
            category=ActionCategory.PERFORMANCE,
        )

        self._register_action(
            name="high_performance_mode",
            text="&High Performance Mode",
            shortcut=DEFAULT_SHORTCUTS["high_performance_mode"],
            status_tip="Force simplified rendering for large workflows",
            category=ActionCategory.PERFORMANCE,
            checkable=True,
        )

        # === AI ACTIONS ===
        self._register_action(
            name="ai_assistant",
            text="AI &Assistant",
            shortcut=DEFAULT_SHORTCUTS["ai_assistant"],
            status_tip="Open AI-powered workflow generation assistant (Ctrl+Shift+G)",
            category=ActionCategory.AI,
            checkable=True,
        )

        # Load custom shortcuts from QSettings
        self._load_custom_shortcuts()

        logger.info(f"ActionManagerV2: Registered {len(self._actions)} actions")

    def _register_action(
        self,
        name: str,
        text: str,
        shortcut: QKeySequence.StandardKey | str | list[str] | None,
        status_tip: str = "",
        category: ActionCategory = ActionCategory.HELP,
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False,
    ) -> QAction:
        """
        Create and register a QAction.

        Args:
            name: Internal action name for lookup
            text: Display text (use & for accelerator)
            shortcut: Keyboard shortcut(s)
            status_tip: Status bar tip
            category: Action category for batch operations
            enabled: Initial enabled state
            checkable: Whether action is checkable
            checked: Initial checked state (for checkable actions)

        Returns:
            Created QAction
        """
        # Get parent widget from main window
        parent: QWidget | None = (
            getattr(self._main_window, "centralWidget", lambda: None)() or self._main_window
        )  # type: ignore

        action = QAction(text, parent)

        # Set shortcut(s)
        self._set_action_shortcut(action, shortcut)

        if status_tip:
            action.setStatusTip(status_tip)

        action.setEnabled(enabled)
        action.setCheckable(checkable)

        if checkable:
            action.setChecked(checked)

        # Add action to main window for global shortcut handling
        if hasattr(self._main_window, "addAction"):
            self._main_window.addAction(action)  # type: ignore

        self._actions[name] = action
        self._categories[name] = category

        return action

    def _set_action_shortcut(
        self,
        action: QAction,
        shortcut: QKeySequence.StandardKey | str | list[str] | None,
    ) -> None:
        """Set shortcut(s) on an action."""
        if shortcut is None:
            return

        if isinstance(shortcut, list):
            # Multiple shortcuts
            sequences = [self._to_key_sequence(s) for s in shortcut]
            action.setShortcuts(sequences)
        else:
            # Single shortcut
            action.setShortcut(self._to_key_sequence(shortcut))

    def _to_key_sequence(self, shortcut: QKeySequence.StandardKey | str) -> QKeySequence:
        """Convert shortcut to QKeySequence."""
        if isinstance(shortcut, QKeySequence.StandardKey):
            return QKeySequence(shortcut)
        return QKeySequence(shortcut)

    def _load_custom_shortcuts(self) -> None:
        """Load custom shortcuts from QSettings."""
        self._settings.beginGroup(self._SETTINGS_GROUP)

        # Check version
        version = self._settings.value(self._VERSION_KEY, 0, int)
        if version > self._CURRENT_VERSION:
            logger.warning(
                f"Shortcut version {version} > current {self._CURRENT_VERSION}, using defaults"
            )

        for name in self._actions:
            custom_shortcut = self._settings.value(name, "", str)
            if custom_shortcut:
                self._custom_shortcuts[name] = custom_shortcut
                self._actions[name].setShortcut(QKeySequence(custom_shortcut))

        self._settings.endGroup()

        if self._custom_shortcuts:
            logger.debug(f"Loaded {len(self._custom_shortcuts)} custom shortcuts")

    def _save_custom_shortcuts(self) -> None:
        """Save custom shortcuts to QSettings."""
        self._settings.beginGroup(self._SETTINGS_GROUP)
        self._settings.setValue(self._VERSION_KEY, self._CURRENT_VERSION)

        for name, shortcut in self._custom_shortcuts.items():
            self._settings.setValue(name, shortcut)

        self._settings.endGroup()
        logger.debug(f"Saved {len(self._custom_shortcuts)} custom shortcuts")

    def get_action(self, name: str) -> QAction | None:
        """
        Get action by name.

        Args:
            name: Action name

        Returns:
            QAction or None if not found
        """
        return self._actions.get(name)

    def get_all_actions(self) -> dict[str, QAction]:
        """
        Get all registered actions.

        Returns:
            Dictionary of action name to QAction (copy)
        """
        return self._actions.copy()

    def get_actions_by_category(self, category: ActionCategory) -> dict[str, QAction]:
        """
        Get all actions in a category.

        Args:
            category: Action category filter

        Returns:
            Dictionary of action name to QAction in the category
        """
        return {
            name: action
            for name, action in self._actions.items()
            if self._categories.get(name) == category
        }

    def set_shortcut(self, name: str, shortcut: str) -> bool:
        """
        Set a custom shortcut for an action.

        Args:
            name: Action name
            shortcut: New shortcut string (empty to reset)

        Returns:
            True if shortcut was set, False if action not found
        """
        action = self._actions.get(name)
        if not action:
            logger.warning(f"Action '{name}' not found for shortcut change")
            return False

        # Get old shortcut for signal
        old_shortcut = action.shortcut().toString()

        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            self._custom_shortcuts[name] = shortcut
        else:
            # Reset to default
            default_shortcut = DEFAULT_SHORTCUTS.get(name)
            if default_shortcut:
                self._set_action_shortcut(action, default_shortcut)
            self._custom_shortcuts.pop(name, None)

        # Save and emit signal
        self._save_custom_shortcuts()
        self.shortcut_changed.emit(name, old_shortcut, shortcut)

        logger.debug(f"Shortcut changed: {name} -> {shortcut}")
        return True

    def get_shortcut(self, name: str) -> str:
        """
        Get current shortcut for an action.

        Args:
            name: Action name

        Returns:
            Current shortcut string (empty if none or action not found)
        """
        action = self._actions.get(name)
        if not action:
            return ""
        return action.shortcut().toString()

    def get_default_shortcut(self, name: str) -> str | list[str] | None:
        """
        Get default shortcut for an action.

        Args:
            name: Action name

        Returns:
            Default shortcut (str, list of str, or None)
        """
        default = DEFAULT_SHORTCUTS.get(name)
        if default is None:
            return None
        if isinstance(default, QKeySequence.StandardKey):
            # Convert to string for display
            seq = QKeySequence(default)
            return seq.toString()
        return default

    def reset_shortcuts(self) -> None:
        """Reset all shortcuts to defaults."""
        for name, action in self._actions.items():
            default_shortcut = DEFAULT_SHORTCUTS.get(name)
            if default_shortcut:
                self._set_action_shortcut(action, default_shortcut)

        # Clear custom shortcuts
        old_custom = self._custom_shortcuts.copy()
        self._custom_shortcuts.clear()

        # Clear settings
        self._settings.beginGroup(self._SETTINGS_GROUP)
        self._settings.remove("")
        self._settings.endGroup()

        logger.info(f"Reset {len(old_custom)} shortcuts to defaults")

    def enable_category(self, category: ActionCategory) -> None:
        """
        Enable all actions in a category.

        Args:
            category: Action category to enable
        """
        for name, action in self._actions.items():
            if self._categories.get(name) == category:
                action.setEnabled(True)
        logger.debug(f"Enabled category: {category.name}")

    def disable_category(self, category: ActionCategory) -> None:
        """
        Disable all actions in a category.

        Args:
            category: Action category to disable
        """
        for name, action in self._actions.items():
            if self._categories.get(name) == category:
                action.setEnabled(False)
        logger.debug(f"Disabled category: {category.name}")

    def set_action_enabled(self, name: str, enabled: bool) -> bool:
        """
        Enable/disable a specific action.

        Args:
            name: Action name
            enabled: True to enable, False to disable

        Returns:
            True if action was found and updated
        """
        action = self._actions.get(name)
        if not action:
            return False
        action.setEnabled(enabled)
        return True

    def set_action_checked(self, name: str, checked: bool) -> bool:
        """
        Set checked state for a checkable action.

        Args:
            name: Action name
            checked: Checked state

        Returns:
            True if action was found and updated
        """
        action = self._actions.get(name)
        if not action or not action.isCheckable():
            return False
        action.setChecked(checked)
        return True

    def connect_handler(self, name: str, handler: Callable[[], None]) -> bool:
        """
        Connect a handler to an action's triggered signal.

        Args:
            name: Action name
            handler: Callable to connect

        Returns:
            True if connected, False if action not found
        """
        action = self._actions.get(name)
        if not action:
            return False
        action.triggered.connect(handler)
        return True

    def connect_slot(
        self,
        name: str,
        slot: Callable[[], None],
        checkable_handler: Callable[[bool], None] | None = None,
    ) -> bool:
        """
        Connect a PySide6 @Slot decorated method to an action.

        Args:
            name: Action name
            slot: Slot method to connect
            checkable_handler: Optional handler for checkable actions (receives bool)

        Returns:
            True if connected, False if action not found
        """
        action = self._actions.get(name)
        if not action:
            return False

        if action.isCheckable() and checkable_handler:
            # For checkable actions, connect to the bool signal
            # Use partial with default argument instead of lambda
            action.triggered.connect(partial(checkable_handler, checked=False))
        else:
            action.triggered.connect(slot)

        return True

    def get_all_categories(self) -> set[ActionCategory]:
        """
        Get all categories used by registered actions.

        Returns:
            Set of ActionCategory values
        """
        return set(self._categories.values())

    def export_shortcuts(self) -> dict[str, str]:
        """
        Export all current shortcuts for display/import.

        Returns:
            Dictionary mapping action names to current shortcut strings
        """
        return {name: action.shortcut().toString() for name, action in self._actions.items()}

    def import_shortcuts(self, shortcuts: dict[str, str]) -> int:
        """
        Import shortcuts from a dictionary.

        Args:
            shortcuts: Dictionary of action name to shortcut string

        Returns:
            Number of shortcuts imported
        """
        count = 0
        for name, shortcut in shortcuts.items():
            if name in self._actions:
                self.set_shortcut(name, shortcut)
                count += 1
        return count


# Convenience function for getting an action from a main window
def get_action(main_window: IMainWindow, name: str) -> QAction | None:
    """
    Get an action by name from the main window's action manager.

    This is a convenience function for accessing actions when
    you don't have direct access to the ActionManagerV2 instance.

    Args:
        main_window: IMainWindow implementation
        name: Action name

    Returns:
        QAction or None if not found
    """
    manager = getattr(main_window, "_action_manager_v2", None)
    if manager and isinstance(manager, ActionManagerV2):
        return manager.get_action(name)

    # Fall back to legacy action_manager (v1)
    manager_legacy = getattr(main_window, "_action_manager", None)
    if manager_legacy:
        return manager_legacy.get_action(name)

    return None
