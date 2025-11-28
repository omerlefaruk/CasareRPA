"""
Main application window for CasareRPA.

This module provides the MainWindow class which serves as the primary
GUI container for the RPA platform.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QSettings, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QToolBar,
    QStatusBar,
    QMessageBox,
    QFileDialog,
    QDockWidget,
    QDialog,
)

from ..utils.config import (
    APP_NAME,
    APP_VERSION,
    WORKFLOWS_DIR,
    GUI_WINDOW_WIDTH,
    GUI_WINDOW_HEIGHT,
)
from ..utils.hotkey_settings import get_hotkey_settings
from .graph.minimap import Minimap
from ..presentation.canvas.component_factory import ComponentFactory
from loguru import logger

# Import controllers for MVC architecture
from ..presentation.canvas.controllers import (
    WorkflowController,
    ExecutionController,
    NodeController,
    ConnectionController,
    PanelController,
    MenuController,
    EventBusController,
    ViewportController,
    SchedulingController,
    TriggerController,
    UIStateController,
)


class MainWindow(QMainWindow):
    """
    Main application window for CasareRPA.

    Provides the primary UI container with menu bar, toolbar, status bar,
    and central widget area for the node graph editor.

    Signals:
        workflow_new: Emitted when user requests new workflow
        workflow_new_from_template: Emitted when user selects a template (TemplateInfo)
        workflow_open: Emitted when user requests to open workflow (str: file path)
        workflow_save: Emitted when user requests to save workflow
        workflow_save_as: Emitted when user requests save as (str: file path)
        workflow_run: Emitted when user requests to run workflow
        workflow_pause: Emitted when user requests to pause workflow
        workflow_resume: Emitted when user requests to resume workflow
        workflow_stop: Emitted when user requests to stop workflow
    """

    workflow_new = Signal()
    workflow_new_from_template = Signal(object)  # TemplateInfo
    workflow_open = Signal(str)
    workflow_save = Signal()
    workflow_save_as = Signal(str)
    workflow_import = Signal(str)  # Import/merge workflow from file path
    workflow_import_json = Signal(str)  # Import/merge workflow from JSON string
    workflow_export_selected = Signal(str)  # Export selected nodes to file path
    workflow_run = Signal()
    workflow_run_to_node = Signal(str)  # Run to selected node ID (F4)
    workflow_run_single_node = Signal(str)  # Run only selected node (F5)
    workflow_pause = Signal()
    workflow_resume = Signal()
    workflow_stop = Signal()
    preferences_saved = Signal()  # Emitted when preferences are saved
    trigger_workflow_requested = (
        Signal()
    )  # Emitted when a trigger wants to run the workflow

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main window.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Hotkey settings
        self._hotkey_settings = get_hotkey_settings()

        # Minimap overlay
        self._minimap: Optional[Minimap] = None
        self._central_widget: Optional[QWidget] = None

        # Debug components
        self._debug_toolbar: Optional["DebugToolbar"] = None

        # Validation components (timer and settings for auto-validation)
        self._validation_timer: Optional["QTimer"] = None
        self._auto_validate: bool = True  # Enable real-time validation
        self._workflow_data_provider: Optional[callable] = (
            None  # Callback to get workflow data
        )

        # Bottom panel dock (unified panel with Variables, Output, Log, Validation tabs)
        self._bottom_panel: Optional["BottomPanelDock"] = None

        # Variable Inspector dock (shows real-time variable values during execution)
        self._variable_inspector_dock: Optional["VariableInspectorDock"] = None

        # Properties panel (right dock for selected node properties)
        self._properties_panel: Optional["PropertiesPanel"] = None

        # Command palette (DEFERRED tier - lazy loaded)
        self._command_palette: Optional["CommandPalette"] = None

        # === 3-TIER LOADING STATE ===
        # Track whether normal-tier components have been loaded
        self._normal_components_loaded: bool = False

        # DEFERRED tier - dialogs created on first use via ComponentFactory
        self._preferences_dialog: Optional["QDialog"] = None
        self._desktop_selector_builder: Optional["QDialog"] = None
        self._performance_dashboard: Optional["QDialog"] = None

        # Controllers (MVC architecture)
        self._workflow_controller: Optional[WorkflowController] = None
        self._execution_controller: Optional[ExecutionController] = None
        self._node_controller: Optional[NodeController] = None
        self._connection_controller: Optional[ConnectionController] = None
        self._panel_controller: Optional[PanelController] = None
        self._menu_controller: Optional[MenuController] = None
        self._event_bus_controller: Optional[EventBusController] = None
        self._viewport_controller: Optional[ViewportController] = None
        self._scheduling_controller: Optional[SchedulingController] = None
        self._trigger_controller: Optional[TriggerController] = None
        self._ui_state_controller: Optional[UIStateController] = None

        # === CRITICAL TIER (immediate) ===
        # These components are required for basic UI rendering
        self._setup_window()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()

        # Initialize controllers after critical UI is set up
        self._init_controllers()

        # Set initial state
        # Window title will be updated by WorkflowController via signal
        self._update_actions()

        logger.debug("MainWindow: Critical tier initialization complete")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT)

        # Enable high-DPI support
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)

        # Apply unified dark theme stylesheet
        from casare_rpa.canvas.theme import get_canvas_stylesheet

        self.setStyleSheet(get_canvas_stylesheet())

    def _create_actions(self) -> None:
        """Create actions for menus and toolbar."""
        # File actions
        self.action_new = QAction("&New Workflow", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.setStatusTip("Create a new workflow")
        self.action_new.triggered.connect(self._on_new_workflow)

        self.action_new_from_template = QAction("New from &Template...", self)
        self.action_new_from_template.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.action_new_from_template.setStatusTip(
            "Create a new workflow from a template"
        )
        self.action_new_from_template.triggered.connect(self._on_new_from_template)

        self.action_open = QAction("&Open Workflow...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.setStatusTip("Open an existing workflow")
        self.action_open.triggered.connect(self._on_open_workflow)

        self.action_import = QAction("&Import Workflow...", self)
        self.action_import.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.action_import.setStatusTip(
            "Import nodes from another workflow into current workflow"
        )
        self.action_import.triggered.connect(self._on_import_workflow)

        self.action_export_selected = QAction("&Export Selected Nodes...", self)
        self.action_export_selected.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.action_export_selected.setStatusTip(
            "Export selected nodes to a workflow file"
        )
        self.action_export_selected.triggered.connect(self._on_export_selected)

        self.action_save = QAction("&Save Workflow", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.setStatusTip("Save the current workflow")
        self.action_save.triggered.connect(self._on_save_workflow)

        self.action_save_as = QAction("Save Workflow &As...", self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.setStatusTip("Save the workflow with a new name")
        self.action_save_as.triggered.connect(self._on_save_as_workflow)

        self.action_save_to_scenario = QAction("Save to &Scenario", self)
        self.action_save_to_scenario.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_save_to_scenario.setStatusTip(
            "Save current workflow to the open scenario"
        )
        # Connection set in app.py since it needs CasareRPAApp instance

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_exit.setStatusTip("Exit the application")
        self.action_exit.triggered.connect(self.close)

        # Find action
        self.action_find_node = QAction("&Find Node...", self)
        self.action_find_node.setShortcut(QKeySequence.StandardKey.Find)
        self.action_find_node.setStatusTip("Search for nodes in the canvas (Ctrl+F)")
        self.action_find_node.triggered.connect(self._on_find_node)

        # Edit actions
        self.action_undo = QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.setStatusTip("Undo the last action")
        self.action_undo.setEnabled(False)

        self.action_redo = QAction("&Redo", self)
        self.action_redo.setShortcuts(
            [QKeySequence.StandardKey.Redo, QKeySequence("Ctrl+Shift+Z")]
        )
        self.action_redo.setStatusTip(
            "Redo the last undone action (Ctrl+Y or Ctrl+Shift+Z)"
        )
        self.action_redo.setEnabled(False)

        self.action_delete = QAction("&Delete", self)
        self.action_delete.setShortcut(QKeySequence("X"))
        self.action_delete.setStatusTip("Delete selected nodes")

        self.action_cut = QAction("Cu&t", self)
        self.action_cut.setShortcut(QKeySequence.StandardKey.Cut)
        self.action_cut.setStatusTip("Cut selected nodes")

        self.action_copy = QAction("&Copy", self)
        self.action_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.action_copy.setStatusTip("Copy selected nodes")

        self.action_paste = QAction("&Paste", self)
        self.action_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.action_paste.setStatusTip("Paste nodes")

        self.action_duplicate = QAction("D&uplicate", self)
        self.action_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        self.action_duplicate.setStatusTip("Duplicate selected nodes")

        self.action_paste_workflow = QAction("Paste Workflow JSON", self)
        self.action_paste_workflow.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.action_paste_workflow.setStatusTip(
            "Paste workflow JSON from clipboard and import nodes"
        )
        self.action_paste_workflow.triggered.connect(self._on_paste_workflow)

        self.action_select_all = QAction("Select &All", self)
        self.action_select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.action_select_all.setStatusTip("Select all nodes")

        self.action_deselect_all = QAction("Deselect All", self)
        self.action_deselect_all.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.action_deselect_all.setStatusTip("Deselect all nodes")

        # Quick node selection
        self.action_select_nearest = QAction("Select &Nearest Node", self)
        self.action_select_nearest.setShortcut(QKeySequence("2"))
        self.action_select_nearest.setStatusTip(
            "Select the nearest node to mouse cursor (2)"
        )
        self.action_select_nearest.triggered.connect(self._on_select_nearest_node)

        # Disable/bypass node
        self.action_toggle_disable = QAction("&Disable Node", self)
        self.action_toggle_disable.setShortcut(QKeySequence("4"))
        self.action_toggle_disable.setStatusTip(
            "Disable/enable selected node - inputs bypass to outputs (4)"
        )
        self.action_toggle_disable.triggered.connect(self._on_toggle_disable_node)

        self.action_preferences = QAction("&Preferences...", self)
        self.action_preferences.setShortcut(QKeySequence("Ctrl+,"))
        self.action_preferences.setStatusTip("Configure application preferences")
        self.action_preferences.triggered.connect(self._on_preferences)

        # View actions
        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.action_zoom_in.setStatusTip("Zoom in")

        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.action_zoom_out.setStatusTip("Zoom out")

        self.action_zoom_reset = QAction("&Reset Zoom", self)
        self.action_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        self.action_zoom_reset.setStatusTip("Reset zoom to 100%")

        self.action_fit_view = QAction("&Fit to View", self)
        self.action_fit_view.setShortcut(QKeySequence("Ctrl+F"))
        self.action_fit_view.setStatusTip("Fit all nodes in view")

        self.action_toggle_bottom_panel = QAction("&Bottom Panel", self)
        self.action_toggle_bottom_panel.setShortcut(QKeySequence("Ctrl+`"))
        self.action_toggle_bottom_panel.setCheckable(True)
        self.action_toggle_bottom_panel.setStatusTip(
            "Show/hide bottom panel (Variables, Output, Log, Validation)"
        )
        self.action_toggle_bottom_panel.triggered.connect(self._on_toggle_bottom_panel)

        self.action_toggle_variable_inspector = QAction("Variable &Inspector", self)
        self.action_toggle_variable_inspector.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.action_toggle_variable_inspector.setCheckable(True)
        self.action_toggle_variable_inspector.setStatusTip(
            "Show/hide variable inspector (real-time variable values)"
        )
        self.action_toggle_variable_inspector.triggered.connect(
            self._on_toggle_variable_inspector
        )

        self.action_validate = QAction("&Validate Workflow", self)
        self.action_validate.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.action_validate.setStatusTip("Validate current workflow")
        self.action_validate.triggered.connect(lambda: self.validate_current_workflow())

        self.action_toggle_minimap = QAction("&Minimap", self)
        self.action_toggle_minimap.setShortcut(QKeySequence("Ctrl+M"))
        self.action_toggle_minimap.setCheckable(True)
        self.action_toggle_minimap.setStatusTip("Show/hide minimap overview (Ctrl+M)")
        self.action_toggle_minimap.triggered.connect(self._on_toggle_minimap)

        self.action_auto_connect = QAction("&Auto-Connect Nodes", self)
        self.action_auto_connect.setCheckable(True)
        self.action_auto_connect.setChecked(True)  # Enabled by default
        self.action_auto_connect.setStatusTip(
            "Automatically suggest connections while dragging nodes (right-click to connect/disconnect)"
        )
        self.action_auto_connect.triggered.connect(self._on_toggle_auto_connect)

        # Workflow actions with Unicode icons
        self.action_run = QAction("▶ Run", self)
        self.action_run.setShortcut(QKeySequence("F3"))
        self.action_run.setStatusTip("Execute the entire workflow (F3)")
        self.action_run.triggered.connect(self._on_run_workflow)

        self.action_run_to_node = QAction("▷ To Node", self)
        self.action_run_to_node.setShortcut(QKeySequence("F4"))
        self.action_run_to_node.setStatusTip(
            "Execute workflow up to selected node (F4)"
        )
        self.action_run_to_node.triggered.connect(self._on_run_to_node)

        self.action_run_single_node = QAction("⊙ This Node", self)
        self.action_run_single_node.setShortcut(QKeySequence("F5"))
        self.action_run_single_node.setStatusTip(
            "Re-run only the selected node with existing inputs (F5)"
        )
        self.action_run_single_node.triggered.connect(self._on_run_single_node)

        self.action_pause = QAction("⏸ Pause", self)
        self.action_pause.setShortcut(QKeySequence("F6"))
        self.action_pause.setStatusTip("Pause/Resume workflow execution (F6)")
        self.action_pause.setEnabled(False)
        self.action_pause.setCheckable(True)
        self.action_pause.triggered.connect(self._on_pause_workflow)

        self.action_stop = QAction("■ Stop", self)
        self.action_stop.setShortcut(QKeySequence("F7"))
        self.action_stop.setStatusTip("Stop workflow execution (F7)")
        self.action_stop.setEnabled(False)
        self.action_stop.triggered.connect(self._on_stop_workflow)

        # Schedule actions
        self.action_schedule = QAction("&Schedule Workflow...", self)
        self.action_schedule.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self.action_schedule.setStatusTip(
            "Schedule this workflow to run automatically (Ctrl+Shift+H)"
        )
        self.action_schedule.triggered.connect(self._on_schedule_workflow)

        self.action_manage_schedules = QAction("&Manage Schedules...", self)
        self.action_manage_schedules.setStatusTip(
            "View and manage all scheduled workflows"
        )
        self.action_manage_schedules.triggered.connect(self._on_manage_schedules)

        # Tools actions with Unicode icons
        self.action_pick_selector = QAction("⌖ Pick", self)
        self.action_pick_selector.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_pick_selector.setStatusTip(
            "Pick an element from the browser (Ctrl+Shift+S)"
        )
        self.action_pick_selector.setEnabled(False)  # Enabled when browser is running
        self.action_pick_selector.triggered.connect(self._on_pick_selector)

        self.action_record_workflow = QAction("⏺ Record", self)
        self.action_record_workflow.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self.action_record_workflow.setStatusTip(
            "Record browser interactions as workflow (Ctrl+Shift+R)"
        )
        self.action_record_workflow.setCheckable(True)
        self.action_record_workflow.setEnabled(False)  # Enabled when browser is running
        self.action_record_workflow.triggered.connect(self._on_toggle_recording)

        self.action_hotkey_manager = QAction("&Keyboard Shortcuts...", self)
        self.action_hotkey_manager.setShortcut(QKeySequence("Ctrl+K, Ctrl+S"))
        self.action_hotkey_manager.setStatusTip("View and customize keyboard shortcuts")
        self.action_hotkey_manager.triggered.connect(self._on_open_hotkey_manager)

        self.action_desktop_selector_builder = QAction(
            "🎯 Desktop Selector Builder", self
        )
        self.action_desktop_selector_builder.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.action_desktop_selector_builder.setStatusTip(
            "Build desktop element selectors visually (Ctrl+Shift+D)"
        )
        self.action_desktop_selector_builder.triggered.connect(
            self._on_open_desktop_selector_builder
        )

        self.action_create_frame = QAction("📋 Create Frame", self)
        self.action_create_frame.setShortcut(QKeySequence("Shift+W"))
        self.action_create_frame.setStatusTip(
            "Create a frame around selected nodes (Shift+W)"
        )
        self.action_create_frame.triggered.connect(self._on_create_frame)

        self.action_performance_dashboard = QAction("📊 Performance Dashboard", self)
        self.action_performance_dashboard.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.action_performance_dashboard.setStatusTip(
            "View performance metrics and statistics (Ctrl+Shift+P)"
        )
        self.action_performance_dashboard.triggered.connect(
            self._on_open_performance_dashboard
        )

        # Command palette action
        self.action_command_palette = QAction("Command Palette...", self)
        self.action_command_palette.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.action_command_palette.setStatusTip(
            "Open command palette to search actions (Ctrl+Shift+P)"
        )
        self.action_command_palette.triggered.connect(self._on_open_command_palette)

        # Help actions
        self.action_about = QAction("&About", self)
        self.action_about.setStatusTip("About CasareRPA")
        self.action_about.triggered.connect(self._on_about)

        # Apply saved hotkeys
        self._load_hotkeys()

    def _load_hotkeys(self) -> None:
        """Load and apply saved hotkeys to actions."""
        action_map = {
            "new": self.action_new,
            "open": self.action_open,
            "save": self.action_save,
            "save_as": self.action_save_as,
            "exit": self.action_exit,
            "undo": self.action_undo,
            "redo": self.action_redo,
            "cut": self.action_cut,
            "copy": self.action_copy,
            "paste": self.action_paste,
            "delete": self.action_delete,
            "select_all": self.action_select_all,
            "deselect_all": self.action_deselect_all,
            "zoom_in": self.action_zoom_in,
            "zoom_out": self.action_zoom_out,
            "zoom_reset": self.action_zoom_reset,
            "fit_view": self.action_fit_view,
            "run": self.action_run,
            "pause": self.action_pause,
            "stop": self.action_stop,
            "create_frame": self.action_create_frame,
            "hotkey_manager": self.action_hotkey_manager,
        }

        for action_name, action in action_map.items():
            shortcuts = self._hotkey_settings.get_shortcuts(action_name)
            if shortcuts:
                sequences = [QKeySequence(s) for s in shortcuts]
                action.setShortcuts(sequences)

    def _create_menus(self) -> None:
        """Create menu bar and menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_new_from_template)
        file_menu.addSeparator()
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_import)
        file_menu.addAction(self.action_export_selected)

        # Recent Files submenu
        self._recent_files_menu = file_menu.addMenu("Recent Files")
        # Note: Recent files menu will be populated by MenuController after initialization

        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addAction(self.action_save_to_scenario)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_cut)
        edit_menu.addAction(self.action_copy)
        edit_menu.addAction(self.action_paste)
        edit_menu.addAction(self.action_duplicate)
        edit_menu.addAction(self.action_paste_workflow)
        edit_menu.addAction(self.action_delete)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_select_all)
        edit_menu.addAction(self.action_deselect_all)
        edit_menu.addAction(self.action_select_nearest)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_toggle_disable)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_find_node)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_preferences)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_reset)
        view_menu.addSeparator()
        view_menu.addAction(self.action_fit_view)
        view_menu.addSeparator()
        view_menu.addAction(self.action_auto_connect)
        view_menu.addSeparator()

        # Panels submenu
        panels_menu = view_menu.addMenu("&Panels")
        panels_menu.addAction(self.action_toggle_bottom_panel)
        panels_menu.addAction(self.action_toggle_variable_inspector)
        panels_menu.addAction(self.action_toggle_minimap)

        # Workflow menu
        workflow_menu = menubar.addMenu("&Workflow")
        workflow_menu.addAction(self.action_validate)
        workflow_menu.addSeparator()
        workflow_menu.addAction(self.action_run)
        workflow_menu.addAction(self.action_run_to_node)
        workflow_menu.addAction(self.action_run_single_node)
        workflow_menu.addSeparator()
        workflow_menu.addAction(self.action_pause)
        workflow_menu.addAction(self.action_stop)
        workflow_menu.addSeparator()
        workflow_menu.addAction(self.action_schedule)
        workflow_menu.addAction(self.action_manage_schedules)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.action_pick_selector)
        tools_menu.addAction(self.action_record_workflow)
        tools_menu.addSeparator()
        tools_menu.addAction(self.action_desktop_selector_builder)
        tools_menu.addAction(self.action_create_frame)
        tools_menu.addSeparator()
        tools_menu.addAction(self.action_performance_dashboard)
        tools_menu.addSeparator()
        tools_menu.addAction(self.action_hotkey_manager)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.action_about)

    def _create_toolbar(self) -> None:
        """Create unified compact toolbar with execution and debug controls."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        # Style the toolbar for a modern compact look
        toolbar.setStyleSheet("""
            QToolBar {
                background: #2b2b2b;
                border: none;
                spacing: 2px;
                padding: 2px 4px;
            }
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QToolButton:hover {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
            }
            QToolButton:pressed {
                background: #4a4a4a;
            }
            QToolButton:checked {
                background: #4a6a8a;
                border: 1px solid #5a7a9a;
            }
            QToolButton:disabled {
                color: #666666;
            }
            QToolBar::separator {
                background: #4a4a4a;
                width: 1px;
                margin: 4px 6px;
            }
        """)

        # === Execution Controls ===
        toolbar.addAction(self.action_run)
        toolbar.addAction(self.action_run_to_node)
        toolbar.addAction(self.action_run_single_node)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)

        toolbar.addSeparator()

        # === Browser Tools ===
        toolbar.addAction(self.action_pick_selector)
        toolbar.addAction(self.action_record_workflow)

        self.addToolBar(toolbar)
        self._main_toolbar = toolbar

    def _create_status_bar(self) -> None:
        """Create enhanced status bar with zoom, node count, and quick toggles."""
        from PySide6.QtWidgets import QLabel, QPushButton

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Style the status bar
        status_bar.setStyleSheet("""
            QStatusBar {
                background: #2b2b2b;
                color: #e0e0e0;
                border-top: 1px solid #3d3d3d;
            }
            QStatusBar::item {
                border: none;
            }
            QLabel {
                color: #a0a0a0;
                padding: 0 8px;
            }
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px 6px;
                color: #a0a0a0;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #3d3d3d;
                color: #e0e0e0;
            }
            QPushButton:checked {
                background: #4a6a8a;
                color: #ffffff;
            }
        """)

        # Zoom indicator
        self._zoom_label = QLabel("100%")
        self._zoom_label.setToolTip("Current zoom level")
        status_bar.addPermanentWidget(self._zoom_label)

        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #4a4a4a;")
        status_bar.addPermanentWidget(sep1)

        # Node count
        self._node_count_label = QLabel("Nodes: 0")
        self._node_count_label.setToolTip("Number of nodes in workflow")
        status_bar.addPermanentWidget(self._node_count_label)

        # Separator
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #4a4a4a;")
        status_bar.addPermanentWidget(sep2)

        # Quick tab toggles
        self._btn_variables = QPushButton("Vars")
        self._btn_variables.setCheckable(True)
        self._btn_variables.setToolTip("Toggle Variables tab")
        self._btn_variables.clicked.connect(lambda: self._toggle_panel_tab("variables"))
        status_bar.addPermanentWidget(self._btn_variables)

        self._btn_output = QPushButton("Out")
        self._btn_output.setCheckable(True)
        self._btn_output.setToolTip("Toggle Output tab")
        self._btn_output.clicked.connect(lambda: self._toggle_panel_tab("output"))
        status_bar.addPermanentWidget(self._btn_output)

        self._btn_log = QPushButton("Log")
        self._btn_log.setCheckable(True)
        self._btn_log.setToolTip("Toggle Log tab")
        self._btn_log.clicked.connect(lambda: self._toggle_panel_tab("log"))
        status_bar.addPermanentWidget(self._btn_log)

        self._btn_validation = QPushButton("Valid")
        self._btn_validation.setCheckable(True)
        self._btn_validation.setToolTip("Toggle Validation tab")
        self._btn_validation.clicked.connect(
            lambda: self._toggle_panel_tab("validation")
        )
        status_bar.addPermanentWidget(self._btn_validation)

        # Separator
        sep3 = QLabel("|")
        sep3.setStyleSheet("color: #4a4a4a;")
        status_bar.addPermanentWidget(sep3)

        # Execution status indicator
        self._exec_status_label = QLabel("● Ready")
        self._exec_status_label.setStyleSheet("color: #4CAF50;")  # Green
        self._exec_status_label.setToolTip("Workflow execution status")
        status_bar.addPermanentWidget(self._exec_status_label)

        status_bar.showMessage("Ready", 3000)

    def _toggle_panel_tab(self, tab_name: str) -> None:
        """Toggle bottom panel to specific tab.

        Delegates to PanelController.toggle_panel_tab().
        """
        if self._panel_controller:
            self._panel_controller.toggle_panel_tab(tab_name)
            self._update_status_bar_buttons()

    def _update_status_bar_buttons(self) -> None:
        """Update status bar button states.

        Delegates to PanelController.update_status_bar_buttons().
        """
        if self._panel_controller:
            self._panel_controller.update_status_bar_buttons()

    def update_zoom_display(self, zoom_percent: float) -> None:
        """Update the zoom level display in status bar - delegate to ViewportController."""
        if self._viewport_controller:
            self._viewport_controller.update_zoom_display(zoom_percent)
        elif hasattr(self, "_zoom_label"):
            self._zoom_label.setText(f"{int(zoom_percent)}%")

    def update_node_count(self, count: int) -> None:
        """Update the node count display in status bar."""
        if hasattr(self, "_node_count_label"):
            self._node_count_label.setText(f"Nodes: {count}")

    def set_execution_status(self, status: str) -> None:
        """
        Update execution status indicator.

        Args:
            status: One of 'ready', 'running', 'paused', 'error', 'success'
        """
        if not hasattr(self, "_exec_status_label"):
            return

        status_config = {
            "ready": ("● Ready", "#4CAF50"),  # Green
            "running": ("● Running", "#FFA500"),  # Orange
            "paused": ("● Paused", "#2196F3"),  # Blue
            "error": ("● Error", "#f44336"),  # Red
            "success": ("✓ Complete", "#4CAF50"),  # Green
        }
        text, color = status_config.get(status, ("● Ready", "#4CAF50"))
        self._exec_status_label.setText(text)
        self._exec_status_label.setStyleSheet(f"color: {color};")

    def _get_or_create_command_palette(self) -> "CommandPalette":
        """
        Lazy-load command palette (DEFERRED tier).

        Returns:
            CommandPalette instance, created on first access.
        """
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

        # Register File actions
        self._command_palette.register_action(
            self.action_new, "File", "Create new workflow"
        )
        self._command_palette.register_action(
            self.action_new_from_template, "File", "Create from template"
        )
        self._command_palette.register_action(
            self.action_open, "File", "Open existing workflow"
        )
        self._command_palette.register_action(
            self.action_import, "File", "Import nodes from another workflow"
        )
        self._command_palette.register_action(
            self.action_export_selected, "File", "Export selected nodes to file"
        )
        self._command_palette.register_action(
            self.action_save, "File", "Save current workflow"
        )
        self._command_palette.register_action(
            self.action_save_as, "File", "Save with new name"
        )

        # Register Edit actions
        self._command_palette.register_action(self.action_undo, "Edit")
        self._command_palette.register_action(self.action_redo, "Edit")
        self._command_palette.register_action(self.action_cut, "Edit")
        self._command_palette.register_action(self.action_copy, "Edit")
        self._command_palette.register_action(self.action_paste, "Edit")
        self._command_palette.register_action(
            self.action_paste_workflow, "Edit", "Paste workflow JSON from clipboard"
        )
        self._command_palette.register_action(self.action_delete, "Edit")
        self._command_palette.register_action(self.action_select_all, "Edit")

        # Register View actions
        self._command_palette.register_action(self.action_zoom_in, "View")
        self._command_palette.register_action(self.action_zoom_out, "View")
        self._command_palette.register_action(self.action_zoom_reset, "View")
        self._command_palette.register_action(self.action_fit_view, "View")
        self._command_palette.register_action(self.action_toggle_bottom_panel, "View")
        self._command_palette.register_action(self.action_toggle_minimap, "View")

        # Register Workflow actions
        self._command_palette.register_action(
            self.action_run, "Workflow", "Execute workflow"
        )
        self._command_palette.register_action(
            self.action_run_to_node, "Workflow", "Run to selected node"
        )
        self._command_palette.register_action(
            self.action_pause, "Workflow", "Pause execution"
        )
        self._command_palette.register_action(
            self.action_stop, "Workflow", "Stop execution"
        )
        self._command_palette.register_action(
            self.action_validate, "Workflow", "Validate workflow"
        )

        # Register Tools actions
        self._command_palette.register_action(self.action_pick_selector, "Tools")
        self._command_palette.register_action(self.action_record_workflow, "Tools")
        self._command_palette.register_action(self.action_create_frame, "Tools")
        self._command_palette.register_action(self.action_hotkey_manager, "Tools")

    def _setup_validation_timer(self) -> None:
        """Setup validation timer for debounced real-time validation."""
        from PySide6.QtCore import QTimer

        self._validation_timer = QTimer(self)
        self._validation_timer.setSingleShot(True)
        self._validation_timer.setInterval(500)  # 500ms debounce
        self._validation_timer.timeout.connect(self._do_deferred_validation)

    def _create_bottom_panel(self) -> None:
        """Create the unified bottom panel with Variables, Output, Log, Validation tabs."""
        from .panels import BottomPanelDock

        self._bottom_panel = BottomPanelDock(self)

        # Connect signals
        self._bottom_panel.validation_requested.connect(self._on_validate_workflow)
        self._bottom_panel.issue_clicked.connect(self._on_validation_issue_clicked)
        self._bottom_panel.navigate_to_node.connect(self._on_navigate_to_node)
        self._bottom_panel.variables_changed.connect(self._on_panel_variables_changed)

        # Connect trigger signals
        self._bottom_panel.trigger_add_requested.connect(self._on_trigger_add_requested)
        self._bottom_panel.trigger_edit_requested.connect(
            self._on_trigger_edit_requested
        )
        self._bottom_panel.trigger_delete_requested.connect(
            self._on_trigger_delete_requested
        )
        self._bottom_panel.trigger_toggle_requested.connect(
            self._on_trigger_toggle_requested
        )
        self._bottom_panel.trigger_run_requested.connect(self._on_trigger_run_requested)

        # Add to main window
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._bottom_panel)

        # Connect dock state changes to auto-save
        self._bottom_panel.dockLocationChanged.connect(self._schedule_ui_state_save)
        self._bottom_panel.visibilityChanged.connect(self._schedule_ui_state_save)
        self._bottom_panel.topLevelChanged.connect(self._schedule_ui_state_save)

        # Initially visible
        self._bottom_panel.show()
        self.action_toggle_bottom_panel.setChecked(True)

        logger.info("Bottom panel created with Variables, Output, Log, Validation tabs")

    def _create_variable_inspector_dock(self) -> None:
        """Create the Variable Inspector dock for real-time variable values."""
        from .panels.variable_inspector_dock import VariableInspectorDock

        self._variable_inspector_dock = VariableInspectorDock(self)

        # Add to main window (bottom area, will be tabified or split with bottom panel)
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self._variable_inspector_dock
        )

        # Split dock horizontally with bottom panel (side-by-side)
        if self._bottom_panel:
            self.splitDockWidget(
                self._bottom_panel,
                self._variable_inspector_dock,
                Qt.Orientation.Horizontal,
            )

        # Connect dock state changes to auto-save
        self._variable_inspector_dock.dockLocationChanged.connect(
            self._schedule_ui_state_save
        )
        self._variable_inspector_dock.visibilityChanged.connect(
            self._schedule_ui_state_save
        )
        self._variable_inspector_dock.topLevelChanged.connect(
            self._schedule_ui_state_save
        )

        # Initially hidden (user can show via View menu)
        self._variable_inspector_dock.hide()
        self.action_toggle_variable_inspector.setChecked(False)

        logger.info("Variable Inspector dock created")

    def _on_toggle_variable_inspector(self, checked: bool) -> None:
        """Handle toggle variable inspector action.

        Delegates to PanelController.
        """
        if self._panel_controller:
            if checked:
                self._panel_controller.show_variable_inspector()
            else:
                self._panel_controller.hide_variable_inspector()

    def _create_properties_panel(self) -> None:
        """Create the properties panel for selected node editing."""
        from .panels.properties_panel import PropertiesPanel

        self._properties_panel = PropertiesPanel(self)

        # Connect property changes to mark workflow as modified
        self._properties_panel.property_changed.connect(self._on_property_panel_changed)

        # Add to main window (right side)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self._properties_panel
        )

        # Connect dock state changes to auto-save
        self._properties_panel.dockLocationChanged.connect(self._schedule_ui_state_save)
        self._properties_panel.visibilityChanged.connect(self._schedule_ui_state_save)
        self._properties_panel.topLevelChanged.connect(self._schedule_ui_state_save)

        # Add toggle action to View menu
        view_menu = None
        for action in self.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        if view_menu:
            self.action_toggle_properties = self._properties_panel.toggleViewAction()
            self.action_toggle_properties.setText("&Properties Panel")
            self.action_toggle_properties.setShortcut(QKeySequence("Ctrl+P"))
            view_menu.addAction(self.action_toggle_properties)

        logger.info("Properties panel created")

    def _create_execution_timeline_dock(self) -> None:
        """Create the Execution Timeline dock for visualizing workflow execution."""
        from .execution.execution_timeline import ExecutionTimeline

        self._execution_timeline = ExecutionTimeline(self)

        # Create dock widget
        self._execution_timeline_dock = QDockWidget("Execution Timeline", self)
        self._execution_timeline_dock.setObjectName("ExecutionTimelineDock")
        self._execution_timeline_dock.setWidget(self._execution_timeline)
        self._execution_timeline_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        # Add to main window (bottom area)
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self._execution_timeline_dock
        )

        # Connect dock state changes to auto-save
        self._execution_timeline_dock.dockLocationChanged.connect(
            self._schedule_ui_state_save
        )
        self._execution_timeline_dock.visibilityChanged.connect(
            self._schedule_ui_state_save
        )
        self._execution_timeline_dock.topLevelChanged.connect(
            self._schedule_ui_state_save
        )

        # Tabify with variable inspector if exists
        if hasattr(self, "_variable_inspector_dock") and self._variable_inspector_dock:
            self.tabifyDockWidget(
                self._variable_inspector_dock, self._execution_timeline_dock
            )

        # Add toggle action to View menu
        view_menu = None
        for action in self.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        if view_menu:
            self.action_toggle_timeline = (
                self._execution_timeline_dock.toggleViewAction()
            )
            self.action_toggle_timeline.setText("&Execution Timeline")
            view_menu.addAction(self.action_toggle_timeline)

        # Connect node clicked signal
        self._execution_timeline.node_clicked.connect(self._select_node_by_id)

        # Initially hidden
        self._execution_timeline_dock.hide()

        logger.info("Execution Timeline dock created")

    @property
    def execution_timeline(self) -> Optional["ExecutionTimeline"]:
        """The execution timeline widget."""
        return getattr(self, "_execution_timeline", None)

    # Backward-compatible getter
    def get_execution_timeline(self) -> Optional["ExecutionTimeline"]:
        return self.execution_timeline

    @property
    def properties_panel(self) -> Optional["PropertiesPanel"]:
        """The properties panel."""
        return self._properties_panel

    # Backward-compatible getter
    def get_properties_panel(self) -> Optional["PropertiesPanel"]:
        return self.properties_panel

    def update_properties_panel(self, node) -> None:
        """
        Update the properties panel with the selected node.

        Args:
            node: The selected node, or None to clear
        """
        if self._properties_panel:
            self._properties_panel.set_node(node)

    def _on_property_panel_changed(self, node_id: str, prop_name: str, value) -> None:
        """Handle property change from properties panel."""
        self.set_modified(True)
        logger.debug(f"Property changed via panel: {node_id}.{prop_name} = {value}")

    def ensure_normal_components_loaded(self) -> None:
        """
        Ensure NORMAL tier components are loaded.

        Call this before accessing normal tier components if they
        might be accessed before showEvent (e.g., during programmatic setup).
        This is idempotent - safe to call multiple times.
        """
        if not self._normal_components_loaded:
            self._load_normal_components()

    @property
    def bottom_panel(self) -> Optional["BottomPanelDock"]:
        """The bottom panel dock."""
        return self._bottom_panel

    # Backward-compatible getter
    def get_bottom_panel(self) -> Optional["BottomPanelDock"]:
        return self.bottom_panel

    @Slot()
    def trigger_workflow_run(self) -> None:
        """
        Slot to trigger workflow run from a trigger.

        This is called from the trigger runner when a trigger fires.
        It emits the trigger_workflow_requested signal which the app handles.
        """
        logger.debug("Trigger requested workflow run")
        self.trigger_workflow_requested.emit()

    def show_bottom_panel(self) -> None:
        """Show the bottom panel.

        Delegates to PanelController.show_bottom_panel().
        """
        if self._panel_controller:
            self._panel_controller.show_bottom_panel()

    def hide_bottom_panel(self) -> None:
        """Hide the bottom panel.

        Delegates to PanelController.hide_bottom_panel().
        """
        if self._panel_controller:
            self._panel_controller.hide_bottom_panel()

    def _on_toggle_bottom_panel(self, checked: bool) -> None:
        """Handle bottom panel toggle.

        Delegates to PanelController.
        """
        if self._panel_controller:
            if checked:
                self._panel_controller.show_bottom_panel()
            else:
                self._panel_controller.hide_bottom_panel()

    def _on_navigate_to_node(self, node_id: str) -> None:
        """Handle navigation to a node from bottom panel."""
        self._select_node_by_id(node_id)

    def _on_panel_variables_changed(self, variables: dict) -> None:
        """Handle variables changed from bottom panel."""
        # Mark workflow as modified
        self.set_modified(True)
        logger.debug(f"Variables updated: {len(variables)} variables")

    # ==================== Trigger Handlers ====================
    # Note: These methods now delegate to TriggerController.
    # The controller connects directly to bottom panel signals during initialization,
    # so these methods are kept for backward compatibility and API consistency.

    def _on_trigger_add_requested(self) -> None:
        """Handle request to add a new trigger - delegate to TriggerController."""
        if self._trigger_controller:
            self._trigger_controller.add_trigger()

    def _on_trigger_edit_requested(self, trigger_config: dict) -> None:
        """Handle request to edit an existing trigger - delegate to TriggerController."""
        if self._trigger_controller:
            self._trigger_controller.edit_trigger(trigger_config)

    def _on_trigger_delete_requested(self, trigger_id: str) -> None:
        """Handle request to delete a trigger - delegate to TriggerController."""
        if self._trigger_controller:
            self._trigger_controller.delete_trigger(trigger_id)

    def _on_trigger_toggle_requested(self, trigger_id: str, enabled: bool) -> None:
        """Handle request to toggle trigger enabled state - delegate to TriggerController."""
        if self._trigger_controller:
            self._trigger_controller.toggle_trigger(trigger_id, enabled)

    def _on_trigger_run_requested(self, trigger_id: str) -> None:
        """Handle request to manually run a trigger - delegate to TriggerController."""
        if self._trigger_controller:
            self._trigger_controller.run_trigger(trigger_id)

    def get_trigger_controller(self) -> Optional[TriggerController]:
        """
        Get the trigger controller.

        Returns:
            TriggerController instance or None
        """
        return self._trigger_controller

    @property
    def validation_panel(self):
        """The validation tab from bottom panel."""
        return self._bottom_panel.get_validation_tab() if self._bottom_panel else None

    # Backward-compatible getter
    def get_validation_panel(self):
        return self.validation_panel

    def show_validation_panel(self) -> None:
        """Show the bottom panel and switch to validation tab."""
        if self._bottom_panel:
            self._bottom_panel.show_validation_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    def hide_validation_panel(self) -> None:
        """Hide the bottom panel."""
        if self._bottom_panel:
            self._bottom_panel.hide()
            self.action_toggle_bottom_panel.setChecked(False)

    # ==================== Component Access (Properties + Getters) ====================

    @property
    def graph(self):
        """The node graph widget."""
        return (
            self._central_widget.graph
            if self._central_widget and hasattr(self._central_widget, "graph")
            else None
        )

    @property
    def workflow_runner(self):
        """The workflow runner for execution control."""
        return getattr(self, "_workflow_runner", None)

    @property
    def project_manager(self):
        """The project manager."""
        return getattr(self, "_project_manager", None)

    @property
    def node_registry(self):
        """The node registry."""
        return getattr(self, "_node_registry", None)

    @property
    def command_palette(self):
        """The command palette (lazy-loaded on first access)."""
        return self._get_or_create_command_palette()

    @property
    def recent_files_menu(self):
        """The recent files menu."""
        return getattr(self, "_recent_files_menu", None)

    @property
    def minimap(self):
        """The minimap widget."""
        return self._minimap

    @property
    def variable_inspector_dock(self):
        """The variable inspector dock."""
        return self._variable_inspector_dock

    @property
    def node_controller(self):
        """The node controller."""
        return getattr(self, "_node_controller", None)

    @property
    def viewport_controller(self):
        """The viewport controller."""
        return getattr(self, "_viewport_controller", None)

    @property
    def scheduling_controller(self):
        """The scheduling controller."""
        return getattr(self, "_scheduling_controller", None)

    # Backward-compatible getters (deprecated - use properties instead)
    def get_graph(self):
        return self.graph

    def get_workflow_runner(self):
        return self.workflow_runner

    def get_project_manager(self):
        return self.project_manager

    def get_node_registry(self):
        return self.node_registry

    def get_command_palette(self):
        return self.command_palette

    def get_recent_files_menu(self):
        return self.recent_files_menu

    def get_minimap(self):
        return self.minimap

    def get_variable_inspector_dock(self):
        return self.variable_inspector_dock

    def get_node_controller(self):
        return self.node_controller

    def get_viewport_controller(self):
        return self.viewport_controller

    def get_scheduling_controller(self):
        return self.scheduling_controller

    def show_status(self, message: str, duration: int = 3000) -> None:
        """Show status message in the statusBar."""
        if self.statusBar():
            self.statusBar().showMessage(message, duration)

    def _on_validate_workflow(self) -> None:
        """Handle validation request from panel."""
        self.validate_current_workflow()

    def _on_validation_issue_clicked(self, location: str) -> None:
        """Handle clicking on a validation issue to select the relevant node."""
        if location and location.startswith("node:"):
            self._select_node_by_id(location.split(":", 1)[1])

    def _select_node_by_id(self, node_id: str) -> None:
        """Select a node by ID in the graph."""
        if not self._central_widget or not hasattr(self._central_widget, "graph"):
            return

        try:
            graph = self._central_widget.graph
            # Clear current selection
            graph.clear_selection()

            # Find and select the node
            for node in graph.all_nodes():
                if node.id() == node_id or getattr(node, "node_id", None) == node_id:
                    node.set_selected(True)
                    # Center view on node
                    graph.fit_to_selection()
                    break
        except Exception as e:
            logger.debug(f"Could not select node {node_id}: {e}")

    def validate_current_workflow(self, show_panel: bool = True) -> "ValidationResult":
        """Validate the current workflow and update the validation panel."""
        from casare_rpa.domain.validation import validate_workflow, ValidationResult

        # Get workflow data from the canvas
        workflow_data = self._get_workflow_data()

        if workflow_data is None:
            # Empty workflow
            result = ValidationResult()
            result.add_warning(
                "EMPTY_WORKFLOW",
                "Workflow is empty",
                suggestion="Add some nodes to the workflow",
            )
        else:
            result = validate_workflow(workflow_data)

        # Update validation tab in bottom panel
        validation_tab = self.get_validation_panel()
        if validation_tab:
            validation_tab.set_result(result)

        if show_panel:
            self.show_validation_panel()

        # Update status bar
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
        """Get the current workflow data as a dictionary."""
        if self._workflow_data_provider:
            try:
                return self._workflow_data_provider()
            except Exception as e:
                logger.debug(f"Workflow data provider failed: {e}")
        return None

    def set_workflow_data_provider(self, provider: callable) -> None:
        """Set a callback to provide workflow data for validation."""
        self._workflow_data_provider = provider

    def on_workflow_changed(self) -> None:
        """Trigger debounced real-time validation when workflow is modified."""
        if self._auto_validate and self._validation_timer:
            self._validation_timer.start()

    def _do_deferred_validation(self) -> None:
        """Perform deferred validation after debounce timeout."""
        # Only update if bottom panel is visible
        if self._bottom_panel and self._bottom_panel.isVisible():
            self.validate_current_workflow(show_panel=False)
        else:
            # Still validate but don't show panel
            result = self.validate_current_workflow(show_panel=False)
            # Update status bar with result
            if not result.is_valid:
                self.statusBar().showMessage(
                    f"Validation: {result.error_count} error(s)", 0
                )

    def set_auto_validate(self, enabled: bool) -> None:
        """Enable or disable real-time validation."""
        self._auto_validate = enabled
        if not enabled and self._validation_timer:
            self._validation_timer.stop()

    def is_auto_validate_enabled(self) -> bool:
        """Check if auto-validation is enabled."""
        return self._auto_validate

    def get_log_viewer(self):
        """Get the log tab from bottom panel."""
        return self._bottom_panel.get_log_tab() if self._bottom_panel else None

    def show_log_viewer(self) -> None:
        """Show the bottom panel and switch to log tab."""
        if self._bottom_panel:
            self._bottom_panel.show_log_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    def hide_log_viewer(self) -> None:
        """Hide the bottom panel."""
        if self._bottom_panel:
            self._bottom_panel.hide()
            self.action_toggle_bottom_panel.setChecked(False)

    def _create_minimap(self, node_graph) -> None:
        """Create minimap overlay widget - delegate to ViewportController."""
        if self._viewport_controller:
            self._viewport_controller.create_minimap(node_graph)
        else:
            # Fallback during initialization before controller is ready
            if self._central_widget:
                self._minimap = Minimap(node_graph, self._central_widget)
                self._minimap.setVisible(False)
                self._position_minimap()

    def _position_minimap(self) -> None:
        """Position minimap at bottom-left of central widget."""
        if self._viewport_controller:
            self._viewport_controller.position_minimap()
        elif self._minimap and self._central_widget:
            # Fallback during initialization
            margin = 10
            x = margin
            y = self._central_widget.height() - self._minimap.height() - margin
            self._minimap.move(x, y)
            self._minimap.raise_()

    def show_minimap(self) -> None:
        """Show the minimap - delegate to ViewportController."""
        if self._viewport_controller:
            self._viewport_controller.show_minimap()
        elif self._minimap:
            self._minimap.setVisible(True)
            self._position_minimap()

    def hide_minimap(self) -> None:
        """Hide the minimap - delegate to ViewportController."""
        if self._viewport_controller:
            self._viewport_controller.hide_minimap()
        elif self._minimap:
            self._minimap.setVisible(False)

    def _on_toggle_minimap(self, checked: bool) -> None:
        """Handle minimap toggle - delegate to ViewportController."""
        if self._viewport_controller:
            self._viewport_controller.toggle_minimap(checked)
        elif checked:
            self.show_minimap()
        else:
            self.hide_minimap()

    def resizeEvent(self, event):
        """Handle window resize to reposition minimap."""
        super().resizeEvent(event)
        self._position_minimap()

    def showEvent(self, event) -> None:
        """
        Handle window show event.

        Loads NORMAL tier components on first show to improve startup time.
        Components are loaded via QTimer.singleShot to ensure the UI is
        responsive before heavy initialization.
        """
        super().showEvent(event)
        if not self._normal_components_loaded:
            # Defer normal tier loading to after the window is visible
            QTimer.singleShot(100, self._load_normal_components)

    def _load_normal_components(self) -> None:
        """
        Load NORMAL tier components after window is shown.

        These components are visible by default but can be deferred
        to improve perceived startup time.
        """
        if self._normal_components_loaded:
            return

        import time

        start_time = time.perf_counter()

        logger.debug("MainWindow: Loading normal tier components...")

        # Create panels and docks
        self._create_bottom_panel()
        self._create_variable_inspector_dock()
        self._create_properties_panel()
        self._create_execution_timeline_dock()
        self._create_debug_components()
        self._setup_validation_timer()

        # Mark as loaded
        self._normal_components_loaded = True

        # Restore UI state from previous session (via UIStateController)
        if self._ui_state_controller:
            self._ui_state_controller.restore_state()

        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(f"MainWindow: Normal tier components loaded in {elapsed:.2f}ms")

    def set_central_widget(self, widget: QWidget) -> None:
        """Set the central widget (typically the node graph)."""
        self._central_widget = widget
        self.setCentralWidget(widget)
        if hasattr(widget, "graph"):
            self._create_minimap(widget.graph)

    def set_modified(self, modified: bool) -> None:
        """Set the modified state - delegates to WorkflowController."""
        if self._workflow_controller:
            self._workflow_controller.set_modified(modified)
        if modified:
            self.on_workflow_changed()

    def is_modified(self) -> bool:
        """Check if the workflow has unsaved changes."""
        return (
            self._workflow_controller.is_modified
            if self._workflow_controller
            else False
        )

    def set_current_file(self, file_path: Optional[Path]) -> None:
        """Set the current workflow file path - delegates to WorkflowController."""
        if self._workflow_controller:
            self._workflow_controller.set_current_file(file_path)

    def get_current_file(self) -> Optional[Path]:
        """Get the current workflow file path."""
        return (
            self._workflow_controller.current_file
            if self._workflow_controller
            else None
        )

    def _update_actions(self) -> None:
        """Update action states based on current state."""
        # Save action enabled only if modified
        if self._workflow_controller:
            self.action_save.setEnabled(self._workflow_controller.is_modified)
        else:
            self.action_save.setEnabled(False)

    def _on_new_workflow(self) -> None:
        """Handle new workflow request - delegate to WorkflowController."""
        self._workflow_controller.new_workflow()

    def _on_new_from_template(self) -> None:
        """Handle new from template request - delegate to WorkflowController."""
        self._workflow_controller.new_from_template()

    def _on_open_workflow(self) -> None:
        """Handle open workflow request - delegate to WorkflowController."""
        self._workflow_controller.open_workflow()

    def _on_import_workflow(self) -> None:
        """Handle import workflow request - delegate to WorkflowController."""
        self._workflow_controller.import_workflow()

    def _on_export_selected(self) -> None:
        """Handle export selected nodes request - delegate to WorkflowController."""
        self._workflow_controller.export_selected_nodes()

    def _on_paste_workflow(self) -> None:
        """Handle paste workflow JSON from clipboard - delegate to WorkflowController."""
        if self._workflow_controller:
            self._workflow_controller.paste_workflow()

    def _on_preferences(self) -> None:
        """Handle preferences dialog request - delegate to MenuController."""
        self._menu_controller.open_preferences()

    def _on_save_workflow(self) -> None:
        """Handle save workflow request - delegate to WorkflowController."""
        self._workflow_controller.save_workflow()

    def _on_save_as_workflow(self) -> None:
        """Handle save as workflow request - delegate to WorkflowController."""
        self._workflow_controller.save_workflow_as()

    def _on_run_workflow(self) -> None:
        """Handle run workflow request (F3) - delegate to ExecutionController."""
        self._execution_controller.run_workflow()

    def _on_run_to_node(self) -> None:
        """Handle run to selected node request (F4) - delegate to ExecutionController."""
        self._execution_controller.run_to_node()

    def _on_run_single_node(self) -> None:
        """Handle run single selected node request (F5) - delegate to ExecutionController."""
        self._execution_controller.run_single_node()

    def _on_pause_workflow(self, checked: bool) -> None:
        """Handle pause/resume workflow request - delegate to ExecutionController."""
        self._execution_controller.toggle_pause(checked)

    def _on_stop_workflow(self) -> None:
        """Handle stop workflow request - delegate to ExecutionController."""
        self._execution_controller.stop_workflow()

    def _on_select_nearest_node(self) -> None:
        """Select the nearest node to mouse cursor (hotkey 2)."""
        if self._node_controller:
            self._node_controller.select_nearest_node()

    def _on_toggle_disable_node(self) -> None:
        """Toggle disable state on nearest node (hotkey 4)."""
        if self._node_controller:
            self._node_controller.toggle_disable_node()

    def _on_open_hotkey_manager(self) -> None:
        """Open the hotkey manager dialog - delegate to MenuController."""
        self._menu_controller.open_hotkey_manager()

    def _on_toggle_auto_connect(self, checked: bool) -> None:
        """Handle auto-connect toggle."""
        # This will be connected by the app when the node graph is available
        pass

    def _on_open_performance_dashboard(self) -> None:
        """Open the performance dashboard dialog - delegate to MenuController."""
        self._menu_controller.open_performance_dashboard()

    def _on_open_command_palette(self) -> None:
        """Open the command palette dialog - delegate to MenuController."""
        self._menu_controller.open_command_palette()

    def _on_find_node(self) -> None:
        """Open the node search dialog (Ctrl+F)."""
        if self._node_controller:
            self._node_controller.find_node()

    def _on_open_recent_file(self, path: str) -> None:
        """Open a recent file - delegate to MenuController."""
        if self._menu_controller:
            self._menu_controller.open_recent_file(path)

    def _on_clear_recent_files(self) -> None:
        """Clear the recent files list - delegate to MenuController."""
        if self._menu_controller:
            self._menu_controller.clear_recent_files()

    def add_to_recent_files(self, file_path) -> None:
        """Add a file to the recent files list - delegate to MenuController."""
        if self._menu_controller:
            self._menu_controller.add_recent_file(file_path)

    def _on_about(self) -> None:
        """Show about dialog - delegate to MenuController."""
        if self._menu_controller:
            self._menu_controller.show_about_dialog()

    def _create_debug_components(self) -> None:
        """Create debug toolbar."""
        from .panels.debug_toolbar import DebugToolbar

        # Create debug toolbar
        self._debug_toolbar = DebugToolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._debug_toolbar)

        # Add view menu option for debug toolbar
        view_menu = None
        for action in self.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        if view_menu:
            view_menu.addSeparator()
            view_menu.addAction(self._debug_toolbar.toggleViewAction())

    def get_debug_toolbar(self) -> Optional["DebugToolbar"]:
        """Get the debug toolbar."""
        return self._debug_toolbar if hasattr(self, "_debug_toolbar") else None

    def get_variable_inspector(self):
        """Get the Variable Inspector dock."""
        return self._variable_inspector_dock

    def show_variable_inspector(self) -> None:
        """Show the Variable Inspector dock."""
        if self._panel_controller:
            self._panel_controller.show_variable_inspector()

    def get_execution_history_viewer(self):
        """Get the history tab from bottom panel."""
        return self._bottom_panel.get_history_tab() if self._bottom_panel else None

    def show_execution_history(self) -> None:
        """Show the bottom panel and switch to history tab."""
        if self._bottom_panel:
            self._bottom_panel.show_history_tab()
            self.action_toggle_bottom_panel.setChecked(True)

    def _on_pick_selector(self) -> None:
        """Handle pick selector action."""
        # This will be connected in app.py to trigger selector mode
        pass

    def _on_toggle_recording(self, checked: bool) -> None:
        """Handle recording mode toggle."""
        # This will be connected in app.py to start/stop recording
        pass

    def _on_open_desktop_selector_builder(self) -> None:
        """Open the Desktop Selector Builder dialog - delegate to MenuController."""
        if self._menu_controller:
            self._menu_controller.show_desktop_selector_builder()

    def _on_create_frame(self) -> None:
        """Create a frame around selected nodes - delegate to ViewportController."""
        if self._viewport_controller:
            self._viewport_controller.create_frame()

    def set_browser_running(self, running: bool) -> None:
        """Enable/disable browser-dependent actions."""
        self.action_pick_selector.setEnabled(running)
        self.action_record_workflow.setEnabled(running)

    def _on_schedule_workflow(self) -> None:
        """Handle schedule workflow action - delegate to SchedulingController."""
        if self._scheduling_controller:
            self._scheduling_controller.schedule_workflow()

    def _on_manage_schedules(self) -> None:
        """Handle manage schedules action - delegate to SchedulingController."""
        if self._scheduling_controller:
            self._scheduling_controller.manage_schedules()

    def _on_run_scheduled_workflow(self, schedule) -> None:
        """Run a scheduled workflow immediately - delegate to SchedulingController."""
        if self._scheduling_controller:
            self._scheduling_controller.run_scheduled_workflow(schedule)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self._workflow_controller.check_unsaved_changes():
            # Save UI state before closing (via UIStateController)
            if self._ui_state_controller:
                self._ui_state_controller.save_state()

            # Clean up controllers before closing
            self._cleanup_controllers()

            event.accept()
        else:
            event.ignore()

    def _cleanup_controllers(self) -> None:
        """Clean up all controllers and cached components."""
        logger.info("Cleaning up controllers...")

        controllers = [
            self._workflow_controller,
            self._execution_controller,
            self._node_controller,
            self._connection_controller,
            self._panel_controller,
            self._menu_controller,
            self._event_bus_controller,
            self._viewport_controller,
            self._scheduling_controller,
            self._trigger_controller,
            self._ui_state_controller,
        ]

        for controller in controllers:
            if controller:
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error(
                        f"Error cleaning up controller {controller.__class__.__name__}: {e}"
                    )

        # Clear ComponentFactory cache
        ComponentFactory.clear()

        logger.info("Controllers cleaned up")

    # ==================== UI State Persistence ====================
    # Delegated to UIStateController

    def reset_ui_state(self) -> None:
        """Reset/clear all saved UI state settings - delegate to UIStateController."""
        if self._ui_state_controller:
            self._ui_state_controller.reset_state()

    def get_ui_state_controller(self) -> Optional["UIStateController"]:
        """
        Get the UI state controller.

        Returns:
            UIStateController instance or None
        """
        return self._ui_state_controller

    def _init_controllers(self) -> None:
        """Initialize all controllers for MVC architecture."""
        logger.info("Initializing controllers...")

        # Create controllers
        self._workflow_controller = WorkflowController(self)
        self._execution_controller = ExecutionController(self)
        self._node_controller = NodeController(self)
        self._connection_controller = ConnectionController(self)
        self._panel_controller = PanelController(self)
        self._menu_controller = MenuController(self)
        self._event_bus_controller = EventBusController(self)
        self._viewport_controller = ViewportController(self)
        self._scheduling_controller = SchedulingController(self)
        self._trigger_controller = TriggerController(self)
        self._ui_state_controller = UIStateController(self)

        # Initialize each controller
        self._workflow_controller.initialize()
        self._execution_controller.initialize()
        self._node_controller.initialize()
        self._connection_controller.initialize()
        self._panel_controller.initialize()
        self._menu_controller.initialize()
        self._event_bus_controller.initialize()
        self._viewport_controller.initialize()
        self._scheduling_controller.initialize()
        self._trigger_controller.initialize()
        self._ui_state_controller.initialize()

        # Connect controller signals to MainWindow
        self._connect_controller_signals()

        logger.info("Controllers initialized successfully")

    def _connect_controller_signals(self) -> None:
        """Connect controller signals to MainWindow handlers and other controllers."""
        logger.debug("Connecting controller signals...")

        # Workflow controller signals
        self._workflow_controller.workflow_created.connect(
            lambda: self.workflow_new.emit()
        )
        self._workflow_controller.workflow_loaded.connect(
            lambda path: self.workflow_open.emit(path)
        )
        self._workflow_controller.workflow_saved.connect(
            lambda path: logger.info(f"Workflow saved: {path}")
        )
        self._workflow_controller.workflow_imported.connect(
            lambda path: self.workflow_import.emit(path)
        )
        self._workflow_controller.workflow_imported_json.connect(
            lambda json_str: self.workflow_import_json.emit(json_str)
        )
        self._workflow_controller.workflow_exported.connect(
            lambda path: self.workflow_export_selected.emit(path)
        )
        self._workflow_controller.current_file_changed.connect(
            lambda file: self._on_current_file_changed(file)
        )
        self._workflow_controller.modified_changed.connect(
            lambda modified: self._on_modified_changed(modified)
        )

        # Execution controller signals
        self._execution_controller.execution_started.connect(
            lambda: self._on_execution_started()
        )
        self._execution_controller.execution_paused.connect(
            lambda: logger.info("Execution paused")
        )
        self._execution_controller.execution_resumed.connect(
            lambda: logger.info("Execution resumed")
        )
        self._execution_controller.execution_stopped.connect(
            lambda: self._on_execution_stopped()
        )
        self._execution_controller.execution_completed.connect(
            lambda: self._on_execution_completed()
        )
        self._execution_controller.execution_error.connect(
            lambda error: self._on_execution_error(error)
        )
        self._execution_controller.run_to_node_requested.connect(
            lambda node_id: self.workflow_run_to_node.emit(node_id)
        )
        self._execution_controller.run_single_node_requested.connect(
            lambda node_id: self.workflow_run_single_node.emit(node_id)
        )

        # Node controller signals
        self._node_controller.node_selected.connect(
            lambda node_id: logger.debug(f"Node selected: {node_id}")
        )
        self._node_controller.node_deselected.connect(
            lambda node_id: logger.debug(f"Node deselected: {node_id}")
        )

        # Panel controller signals
        self._panel_controller.bottom_panel_toggled.connect(
            lambda visible: logger.debug(f"Bottom panel toggled: {visible}")
        )

        logger.debug("Controller signals connected")

    def _on_current_file_changed(self, file: Optional[Path]) -> None:
        """Handle current file changed from WorkflowController."""
        # Update window title and other UI elements as needed
        pass

    def _on_modified_changed(self, modified: bool) -> None:
        """Handle modified state changed from WorkflowController."""
        # Update UI to reflect modified state as needed
        pass

    def _on_execution_started(self) -> None:
        """Handle execution started from ExecutionController."""
        self.action_run.setEnabled(False)
        self.action_run_to_node.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(True)
        self.statusBar().showMessage("Workflow execution started...", 0)

    def _on_execution_stopped(self) -> None:
        """Handle execution stopped from ExecutionController."""
        self.action_run.setEnabled(True)
        self.action_run_to_node.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution stopped", 3000)

    def _on_execution_completed(self) -> None:
        """Handle execution completed from ExecutionController."""
        self.action_run.setEnabled(True)
        self.action_run_to_node.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution completed", 3000)

    def _on_execution_error(self, error: str) -> None:
        """Handle execution error from ExecutionController."""
        self.action_run.setEnabled(True)
        self.action_run_to_node.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage(f"Execution error: {error}", 5000)

    def _schedule_ui_state_save(self) -> None:
        """Schedule UI state save - delegate to UIStateController."""
        if self._ui_state_controller:
            self._ui_state_controller.schedule_auto_save()
