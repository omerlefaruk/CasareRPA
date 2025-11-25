"""
Main application window for CasareRPA.

This module provides the MainWindow class which serves as the primary
GUI container for the RPA platform.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal, QSettings, QByteArray, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QMenuBar,
    QMenu,
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
from .minimap import Minimap
from .visual_nodes import VisualSnippetNode
from loguru import logger


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
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main window.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        # Window properties
        self._current_file: Optional[Path] = None
        self._is_modified: bool = False
        
        # Hotkey settings
        self._hotkey_settings = get_hotkey_settings()
        
        # Minimap overlay
        self._minimap: Optional[Minimap] = None
        self._central_widget: Optional[QWidget] = None
        
        # Debug components
        self._debug_toolbar: Optional['DebugToolbar'] = None

        # Validation components (timer and settings for auto-validation)
        self._validation_timer: Optional['QTimer'] = None
        self._auto_validate: bool = True  # Enable real-time validation
        self._workflow_data_provider: Optional[callable] = None  # Callback to get workflow data

        # Bottom panel dock (unified panel with Variables, Output, Log, Validation tabs)
        self._bottom_panel: Optional['BottomPanelDock'] = None

        # Variable Inspector dock (shows real-time variable values during execution)
        self._variable_inspector_dock: Optional['VariableInspectorDock'] = None

        # Properties panel (right dock for selected node properties)
        self._properties_panel: Optional['PropertiesPanel'] = None

        # Breadcrumb navigation bar
        self._breadcrumb_bar: Optional['BreadcrumbBar'] = None

        # Command palette
        self._command_palette: Optional['CommandPalette'] = None

        # Setup window
        self._setup_window()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_breadcrumb_bar()
        self._create_status_bar()
        self._create_bottom_panel()
        self._create_variable_inspector_dock()
        self._create_properties_panel()
        self._create_execution_timeline_dock()
        self._create_debug_components()
        self._create_command_palette()
        self._setup_validation_timer()
        
        # Set initial state
        self._update_window_title()
        self._update_actions()

        # Setup UI state persistence
        self._settings = QSettings("CasareRPA", "Canvas")
        self._state_save_timer = QTimer(self)
        self._state_save_timer.setSingleShot(True)
        self._state_save_timer.timeout.connect(self._save_ui_state)

        # Restore UI state from previous session
        self._restore_ui_state()

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
        self.action_new_from_template.setStatusTip("Create a new workflow from a template")
        self.action_new_from_template.triggered.connect(self._on_new_from_template)
        
        self.action_open = QAction("&Open Workflow...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.setStatusTip("Open an existing workflow")
        self.action_open.triggered.connect(self._on_open_workflow)

        self.action_import = QAction("&Import Workflow...", self)
        self.action_import.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.action_import.setStatusTip("Import nodes from another workflow into current workflow")
        self.action_import.triggered.connect(self._on_import_workflow)

        self.action_export_selected = QAction("&Export Selected Nodes...", self)
        self.action_export_selected.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.action_export_selected.setStatusTip("Export selected nodes to a workflow file")
        self.action_export_selected.triggered.connect(self._on_export_selected)

        self.action_save = QAction("&Save Workflow", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.setStatusTip("Save the current workflow")
        self.action_save.triggered.connect(self._on_save_workflow)
        
        self.action_save_as = QAction("Save Workflow &As...", self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.setStatusTip("Save the workflow with a new name")
        self.action_save_as.triggered.connect(self._on_save_as_workflow)
        
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
        self.action_redo.setShortcuts([QKeySequence.StandardKey.Redo, QKeySequence("Ctrl+Shift+Z")])
        self.action_redo.setStatusTip("Redo the last undone action (Ctrl+Y or Ctrl+Shift+Z)")
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
        self.action_paste_workflow.setStatusTip("Paste workflow JSON from clipboard and import nodes")
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
        self.action_select_nearest.setStatusTip("Select the nearest node to mouse cursor (2)")
        self.action_select_nearest.triggered.connect(self._on_select_nearest_node)

        # Disable/bypass node
        self.action_toggle_disable = QAction("&Disable Node", self)
        self.action_toggle_disable.setShortcut(QKeySequence("4"))
        self.action_toggle_disable.setStatusTip("Disable/enable selected node - inputs bypass to outputs (4)")
        self.action_toggle_disable.triggered.connect(self._on_toggle_disable_node)

        # Snippet actions
        self.action_create_snippet = QAction("Create &Snippet from Selection...", self)
        self.action_create_snippet.setShortcut(QKeySequence("Ctrl+Shift+G"))
        self.action_create_snippet.setStatusTip("Create a reusable snippet from selected nodes (Ctrl+Shift+G)")
        self.action_create_snippet.triggered.connect(self._on_create_snippet)

        self.action_snippet_library = QAction("Snippet &Library...", self)
        self.action_snippet_library.setShortcut(QKeySequence("Ctrl+Shift+L"))
        self.action_snippet_library.setStatusTip("Browse and insert snippets from library (Ctrl+Shift+L)")
        self.action_snippet_library.triggered.connect(self._on_open_snippet_library)


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
        self.action_toggle_bottom_panel.setStatusTip("Show/hide bottom panel (Variables, Output, Log, Validation)")
        self.action_toggle_bottom_panel.triggered.connect(self._on_toggle_bottom_panel)

        self.action_toggle_variable_inspector = QAction("Variable &Inspector", self)
        self.action_toggle_variable_inspector.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.action_toggle_variable_inspector.setCheckable(True)
        self.action_toggle_variable_inspector.setStatusTip("Show/hide variable inspector (real-time variable values)")
        self.action_toggle_variable_inspector.triggered.connect(self._on_toggle_variable_inspector)

        self.action_toggle_navigation = QAction("Snippet &Navigation", self)
        self.action_toggle_navigation.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.action_toggle_navigation.setCheckable(True)
        self.action_toggle_navigation.setChecked(True)  # Shown by default
        self.action_toggle_navigation.setStatusTip("Show/hide snippet navigation breadcrumb and drop zone")
        self.action_toggle_navigation.triggered.connect(self._on_toggle_navigation)

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
        self.action_auto_connect.setStatusTip("Automatically suggest connections while dragging nodes (right-click to connect/disconnect)")
        self.action_auto_connect.triggered.connect(self._on_toggle_auto_connect)
        
        # Workflow actions with Unicode icons
        self.action_run = QAction("▶ Run", self)
        self.action_run.setShortcut(QKeySequence("F3"))
        self.action_run.setStatusTip("Execute the entire workflow (F3)")
        self.action_run.triggered.connect(self._on_run_workflow)

        self.action_run_to_node = QAction("▷ To Node", self)
        self.action_run_to_node.setShortcut(QKeySequence("F4"))
        self.action_run_to_node.setStatusTip("Execute workflow up to selected node (F4)")
        self.action_run_to_node.triggered.connect(self._on_run_to_node)

        self.action_run_single_node = QAction("⊙ This Node", self)
        self.action_run_single_node.setShortcut(QKeySequence("F5"))
        self.action_run_single_node.setStatusTip("Re-run only the selected node with existing inputs (F5)")
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
        self.action_schedule.setStatusTip("Schedule this workflow to run automatically (Ctrl+Shift+H)")
        self.action_schedule.triggered.connect(self._on_schedule_workflow)

        self.action_manage_schedules = QAction("&Manage Schedules...", self)
        self.action_manage_schedules.setStatusTip("View and manage all scheduled workflows")
        self.action_manage_schedules.triggered.connect(self._on_manage_schedules)

        # Tools actions with Unicode icons
        self.action_pick_selector = QAction("⌖ Pick", self)
        self.action_pick_selector.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_pick_selector.setStatusTip("Pick an element from the browser (Ctrl+Shift+S)")
        self.action_pick_selector.setEnabled(False)  # Enabled when browser is running
        self.action_pick_selector.triggered.connect(self._on_pick_selector)

        self.action_record_workflow = QAction("⏺ Record", self)
        self.action_record_workflow.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self.action_record_workflow.setStatusTip("Record browser interactions as workflow (Ctrl+Shift+R)")
        self.action_record_workflow.setCheckable(True)
        self.action_record_workflow.setEnabled(False)  # Enabled when browser is running
        self.action_record_workflow.triggered.connect(self._on_toggle_recording)
        
        self.action_hotkey_manager = QAction("&Keyboard Shortcuts...", self)
        self.action_hotkey_manager.setShortcut(QKeySequence("Ctrl+K, Ctrl+S"))
        self.action_hotkey_manager.setStatusTip("View and customize keyboard shortcuts")
        self.action_hotkey_manager.triggered.connect(self._on_open_hotkey_manager)

        self.action_desktop_selector_builder = QAction("🎯 Desktop Selector Builder", self)
        self.action_desktop_selector_builder.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.action_desktop_selector_builder.setStatusTip("Build desktop element selectors visually (Ctrl+Shift+D)")
        self.action_desktop_selector_builder.triggered.connect(self._on_open_desktop_selector_builder)

        self.action_create_frame = QAction("📋 Create Frame", self)
        self.action_create_frame.setShortcut(QKeySequence("Shift+W"))
        self.action_create_frame.setStatusTip("Create a frame around selected nodes (Shift+W)")
        self.action_create_frame.triggered.connect(self._on_create_frame)

        self.action_performance_dashboard = QAction("📊 Performance Dashboard", self)
        self.action_performance_dashboard.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.action_performance_dashboard.setStatusTip("View performance metrics and statistics (Ctrl+Shift+P)")
        self.action_performance_dashboard.triggered.connect(self._on_open_performance_dashboard)

        # Command palette action
        self.action_command_palette = QAction("Command Palette...", self)
        self.action_command_palette.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.action_command_palette.setStatusTip("Open command palette to search actions (Ctrl+Shift+P)")
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
        self._update_recent_files_menu()

        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
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
        edit_menu.addAction(self.action_create_snippet)
        edit_menu.addAction(self.action_snippet_library)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_find_node)

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
        view_menu.addAction(self.action_toggle_bottom_panel)
        view_menu.addAction(self.action_toggle_variable_inspector)
        view_menu.addAction(self.action_toggle_navigation)
        view_menu.addAction(self.action_toggle_minimap)

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

    def _create_breadcrumb_bar(self) -> None:
        """Create the breadcrumb navigation bar below the toolbar."""
        from .breadcrumb_bar import BreadcrumbBar

        self._breadcrumb_bar = BreadcrumbBar(self)

        # Create a toolbar to hold the breadcrumb bar
        breadcrumb_toolbar = QToolBar("Breadcrumb")
        breadcrumb_toolbar.setObjectName("BreadcrumbToolbar")
        breadcrumb_toolbar.setMovable(False)
        breadcrumb_toolbar.setFloatable(False)
        breadcrumb_toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)

        # Add breadcrumb widget
        breadcrumb_toolbar.addWidget(self._breadcrumb_bar)

        # Style to remove toolbar chrome
        breadcrumb_toolbar.setStyleSheet("""
            QToolBar {
                background: #2b2b2b;
                border: none;
                padding: 0;
                margin: 0;
            }
        """)

        # Add below main toolbar
        self.addToolBarBreak()
        self.addToolBar(breadcrumb_toolbar)

        # Connect signals
        self._breadcrumb_bar.workflow_clicked.connect(self._on_breadcrumb_workflow_clicked)
        self._breadcrumb_bar.node_clicked.connect(self._on_breadcrumb_node_clicked)

        logger.debug("Breadcrumb bar created")

    def _on_breadcrumb_workflow_clicked(self) -> None:
        """Handle workflow breadcrumb click - center view on all nodes."""
        if self._central_widget and hasattr(self._central_widget, 'center_on_nodes'):
            self._central_widget.center_on_nodes()

    def _on_breadcrumb_node_clicked(self, node_id: str) -> None:
        """Handle node breadcrumb click - select and center on node."""
        self._select_node_by_id(node_id)

    def get_breadcrumb_bar(self) -> Optional['BreadcrumbBar']:
        """Get the breadcrumb navigation bar."""
        return self._breadcrumb_bar

    def update_breadcrumb_node(self, node_name: Optional[str], node_id: Optional[str] = None) -> None:
        """
        Update the breadcrumb bar with selected node info.

        Args:
            node_name: Name of selected node, or None to clear
            node_id: ID of selected node
        """
        if self._breadcrumb_bar:
            self._breadcrumb_bar.set_selected_node(node_name, node_id)

    def _create_status_bar(self) -> None:
        """Create enhanced status bar with zoom, node count, and quick toggles."""
        from PySide6.QtWidgets import QLabel, QPushButton, QHBoxLayout, QWidget

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
        self._btn_validation.clicked.connect(lambda: self._toggle_panel_tab("validation"))
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
        """Toggle bottom panel to specific tab."""
        if self._bottom_panel:
            if self._bottom_panel.isVisible():
                # Switch to tab or hide if already on that tab
                current_idx = self._bottom_panel._tab_widget.currentIndex()
                tab_map = {"variables": 0, "output": 1, "log": 2, "validation": 3, "history": 4}
                target_idx = tab_map.get(tab_name, 0)
                if current_idx == target_idx:
                    self._bottom_panel.hide()
                else:
                    self._bottom_panel._tab_widget.setCurrentIndex(target_idx)
            else:
                self._bottom_panel.show()
                tab_map = {"variables": 0, "output": 1, "log": 2, "validation": 3, "history": 4}
                self._bottom_panel._tab_widget.setCurrentIndex(tab_map.get(tab_name, 0))
            self._update_status_bar_buttons()

    def _update_status_bar_buttons(self) -> None:
        """Update status bar button states."""
        if not self._bottom_panel:
            return
        visible = self._bottom_panel.isVisible()
        current_idx = self._bottom_panel._tab_widget.currentIndex() if visible else -1
        self._btn_variables.setChecked(visible and current_idx == 0)
        self._btn_output.setChecked(visible and current_idx == 1)
        self._btn_log.setChecked(visible and current_idx == 2)
        self._btn_validation.setChecked(visible and current_idx == 3)

    def update_zoom_display(self, zoom_percent: float) -> None:
        """Update the zoom level display in status bar."""
        if hasattr(self, '_zoom_label'):
            self._zoom_label.setText(f"{int(zoom_percent)}%")

    def update_node_count(self, count: int) -> None:
        """Update the node count display in status bar."""
        if hasattr(self, '_node_count_label'):
            self._node_count_label.setText(f"Nodes: {count}")

    def set_execution_status(self, status: str) -> None:
        """
        Update execution status indicator.

        Args:
            status: One of 'ready', 'running', 'paused', 'error', 'success'
        """
        if not hasattr(self, '_exec_status_label'):
            return

        status_config = {
            "ready": ("● Ready", "#4CAF50"),      # Green
            "running": ("● Running", "#FFA500"),   # Orange
            "paused": ("● Paused", "#2196F3"),     # Blue
            "error": ("● Error", "#f44336"),       # Red
            "success": ("✓ Complete", "#4CAF50"),  # Green
        }
        text, color = status_config.get(status, ("● Ready", "#4CAF50"))
        self._exec_status_label.setText(text)
        self._exec_status_label.setStyleSheet(f"color: {color};")

    def _create_command_palette(self) -> None:
        """Create and populate the command palette."""
        from .command_palette import CommandPalette

        self._command_palette = CommandPalette(self)

        # Register File actions
        self._command_palette.register_action(self.action_new, "File", "Create new workflow")
        self._command_palette.register_action(self.action_new_from_template, "File", "Create from template")
        self._command_palette.register_action(self.action_open, "File", "Open existing workflow")
        self._command_palette.register_action(self.action_import, "File", "Import nodes from another workflow")
        self._command_palette.register_action(self.action_export_selected, "File", "Export selected nodes to file")
        self._command_palette.register_action(self.action_save, "File", "Save current workflow")
        self._command_palette.register_action(self.action_save_as, "File", "Save with new name")

        # Register Edit actions
        self._command_palette.register_action(self.action_undo, "Edit")
        self._command_palette.register_action(self.action_redo, "Edit")
        self._command_palette.register_action(self.action_cut, "Edit")
        self._command_palette.register_action(self.action_copy, "Edit")
        self._command_palette.register_action(self.action_paste, "Edit")
        self._command_palette.register_action(self.action_paste_workflow, "Edit", "Paste workflow JSON from clipboard")
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
        self._command_palette.register_action(self.action_run, "Workflow", "Execute workflow")
        self._command_palette.register_action(self.action_run_to_node, "Workflow", "Run to selected node")
        self._command_palette.register_action(self.action_pause, "Workflow", "Pause execution")
        self._command_palette.register_action(self.action_stop, "Workflow", "Stop execution")
        self._command_palette.register_action(self.action_validate, "Workflow", "Validate workflow")

        # Register Tools actions
        self._command_palette.register_action(self.action_pick_selector, "Tools")
        self._command_palette.register_action(self.action_record_workflow, "Tools")
        self._command_palette.register_action(self.action_create_frame, "Tools")
        self._command_palette.register_action(self.action_hotkey_manager, "Tools")

        logger.debug("Command palette created with actions")

    def _setup_validation_timer(self) -> None:
        """Setup validation timer for debounced real-time validation."""
        from PySide6.QtCore import QTimer
        self._validation_timer = QTimer(self)
        self._validation_timer.setSingleShot(True)
        self._validation_timer.setInterval(500)  # 500ms debounce
        self._validation_timer.timeout.connect(self._do_deferred_validation)

    def _create_bottom_panel(self) -> None:
        """Create the unified bottom panel with Variables, Output, Log, Validation tabs."""
        from .bottom_panel import BottomPanelDock

        self._bottom_panel = BottomPanelDock(self)

        # Connect signals
        self._bottom_panel.validation_requested.connect(self._on_validate_workflow)
        self._bottom_panel.issue_clicked.connect(self._on_validation_issue_clicked)
        self._bottom_panel.navigate_to_node.connect(self._on_navigate_to_node)
        self._bottom_panel.variables_changed.connect(self._on_panel_variables_changed)

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
        from .variable_inspector_dock import VariableInspectorDock

        self._variable_inspector_dock = VariableInspectorDock(self)

        # Add to main window (bottom area, will be tabified or split with bottom panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._variable_inspector_dock)

        # Split dock horizontally with bottom panel (side-by-side)
        if self._bottom_panel:
            self.splitDockWidget(self._bottom_panel, self._variable_inspector_dock, Qt.Orientation.Horizontal)

        # Connect dock state changes to auto-save
        self._variable_inspector_dock.dockLocationChanged.connect(self._schedule_ui_state_save)
        self._variable_inspector_dock.visibilityChanged.connect(self._schedule_ui_state_save)
        self._variable_inspector_dock.topLevelChanged.connect(self._schedule_ui_state_save)

        # Initially hidden (user can show via View menu)
        self._variable_inspector_dock.hide()
        self.action_toggle_variable_inspector.setChecked(False)

        logger.info("Variable Inspector dock created")

    def _on_toggle_variable_inspector(self, checked: bool) -> None:
        """Handle toggle variable inspector action."""
        if self._variable_inspector_dock:
            if checked:
                self._variable_inspector_dock.show()
            else:
                self._variable_inspector_dock.hide()

    def _on_toggle_navigation(self, checked: bool) -> None:
        """Handle toggle snippet navigation UI action."""
        if hasattr(self, '_central_widget') and hasattr(self._central_widget, '_snippet_breadcrumb'):
            self._central_widget._snippet_breadcrumb.setVisible(checked)

        # Note: Drop zone visibility is controlled by navigation depth
        # It will auto-show/hide based on whether we're inside a snippet

        logger.info(f"Snippet navigation UI {'shown' if checked else 'hidden'}")

    def _create_properties_panel(self) -> None:
        """Create the properties panel for selected node editing."""
        from .properties_panel import PropertiesPanel

        self._properties_panel = PropertiesPanel(self)

        # Connect property changes to mark workflow as modified
        self._properties_panel.property_changed.connect(self._on_property_panel_changed)

        # Add to main window (right side)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._properties_panel)

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
        from .execution_timeline import ExecutionTimeline

        self._execution_timeline = ExecutionTimeline(self)

        # Create dock widget
        self._execution_timeline_dock = QDockWidget("Execution Timeline", self)
        self._execution_timeline_dock.setObjectName("ExecutionTimelineDock")
        self._execution_timeline_dock.setWidget(self._execution_timeline)
        self._execution_timeline_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        # Add to main window (bottom area)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._execution_timeline_dock)

        # Connect dock state changes to auto-save
        self._execution_timeline_dock.dockLocationChanged.connect(self._schedule_ui_state_save)
        self._execution_timeline_dock.visibilityChanged.connect(self._schedule_ui_state_save)
        self._execution_timeline_dock.topLevelChanged.connect(self._schedule_ui_state_save)

        # Tabify with variable inspector if exists
        if hasattr(self, '_variable_inspector_dock') and self._variable_inspector_dock:
            self.tabifyDockWidget(self._variable_inspector_dock, self._execution_timeline_dock)

        # Add toggle action to View menu
        view_menu = None
        for action in self.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        if view_menu:
            self.action_toggle_timeline = self._execution_timeline_dock.toggleViewAction()
            self.action_toggle_timeline.setText("&Execution Timeline")
            view_menu.addAction(self.action_toggle_timeline)

        # Connect node clicked signal
        self._execution_timeline.node_clicked.connect(self._select_node_by_id)

        # Initially hidden
        self._execution_timeline_dock.hide()

        logger.info("Execution Timeline dock created")

    def get_execution_timeline(self) -> Optional['ExecutionTimeline']:
        """Get the execution timeline widget."""
        return getattr(self, '_execution_timeline', None)

    def get_properties_panel(self) -> Optional['PropertiesPanel']:
        """
        Get the properties panel.

        Returns:
            PropertiesPanel instance or None
        """
        return self._properties_panel

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

    def get_bottom_panel(self) -> Optional['BottomPanelDock']:
        """
        Get the bottom panel dock.

        Returns:
            BottomPanelDock instance or None
        """
        return self._bottom_panel

    def show_bottom_panel(self) -> None:
        """Show the bottom panel."""
        if self._bottom_panel:
            self._bottom_panel.show()
            self.action_toggle_bottom_panel.setChecked(True)

    def hide_bottom_panel(self) -> None:
        """Hide the bottom panel."""
        if self._bottom_panel:
            self._bottom_panel.hide()
            self.action_toggle_bottom_panel.setChecked(False)

    def _on_toggle_bottom_panel(self, checked: bool) -> None:
        """Handle bottom panel toggle."""
        if checked:
            self.show_bottom_panel()
        else:
            self.hide_bottom_panel()

    def _on_navigate_to_node(self, node_id: str) -> None:
        """Handle navigation to a node from bottom panel."""
        self._select_node_by_id(node_id)

    def _on_panel_variables_changed(self, variables: dict) -> None:
        """Handle variables changed from bottom panel."""
        # Mark workflow as modified
        self.set_modified(True)
        logger.debug(f"Variables updated: {len(variables)} variables")

    def get_validation_panel(self):
        """
        Get the validation tab from bottom panel.

        Returns:
            ValidationTab instance or None
        """
        if self._bottom_panel:
            return self._bottom_panel.get_validation_tab()
        return None

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

    def _on_validate_workflow(self) -> None:
        """Handle validation request from panel."""
        self.validate_current_workflow()

    def _on_validation_issue_clicked(self, location: str) -> None:
        """
        Handle clicking on a validation issue.

        Args:
            location: Issue location string (e.g., "node:abc123")
        """
        # Try to select the node in the graph
        if location and location.startswith("node:"):
            node_id = location.split(":", 1)[1]
            self._select_node_by_id(node_id)

    def _select_node_by_id(self, node_id: str) -> None:
        """Select a node by ID in the graph."""
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            return

        try:
            graph = self._central_widget.graph
            # Clear current selection
            graph.clear_selection()

            # Find and select the node
            for node in graph.all_nodes():
                if node.id() == node_id or getattr(node, 'node_id', None) == node_id:
                    node.set_selected(True)
                    # Center view on node
                    graph.fit_to_selection()
                    break
        except Exception as e:
            logger.debug(f"Could not select node {node_id}: {e}")

    def validate_current_workflow(self, show_panel: bool = True) -> 'ValidationResult':
        """
        Validate the current workflow and update the validation panel.

        Args:
            show_panel: Whether to show the validation panel

        Returns:
            ValidationResult from validation
        """
        from ..core.validation import validate_workflow, ValidationResult

        # Get workflow data from the canvas
        workflow_data = self._get_workflow_data()

        if workflow_data is None:
            # Empty workflow
            result = ValidationResult()
            result.add_warning(
                "EMPTY_WORKFLOW",
                "Workflow is empty",
                suggestion="Add some nodes to the workflow"
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
        """
        Get the current workflow data as a dictionary.

        Returns:
            Workflow data dictionary or None
        """
        # Use the workflow data provider callback if set (by app.py)
        if self._workflow_data_provider:
            try:
                return self._workflow_data_provider()
            except Exception as e:
                logger.debug(f"Workflow data provider failed: {e}")
                return None

        # Fallback - return None if no provider set
        return None

    def set_workflow_data_provider(self, provider: callable) -> None:
        """
        Set a callback to provide workflow data for validation.

        Args:
            provider: Callable that returns workflow data dict
        """
        self._workflow_data_provider = provider

    def on_workflow_changed(self) -> None:
        """
        Called when the workflow is modified.
        Triggers debounced real-time validation if enabled.

        This method should be called from app.py when:
        - Nodes are added/deleted
        - Connections are made/broken
        - Node properties change
        """
        if self._auto_validate and self._validation_timer:
            # Restart the debounce timer
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
        """
        Enable or disable real-time validation.

        Args:
            enabled: Whether to enable auto-validation
        """
        self._auto_validate = enabled
        if not enabled and self._validation_timer:
            self._validation_timer.stop()

    def is_auto_validate_enabled(self) -> bool:
        """Check if auto-validation is enabled."""
        return self._auto_validate

    def get_log_viewer(self):
        """
        Get the log tab from bottom panel.

        Returns:
            LogTab instance or None
        """
        if self._bottom_panel:
            return self._bottom_panel.get_log_tab()
        return None

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
        """Create minimap overlay widget."""
        # Create minimap as overlay on central widget
        if self._central_widget:
            self._minimap = Minimap(node_graph, self._central_widget)
            self._minimap.setVisible(False)  # Initially hidden
            self._position_minimap()
    
    def _position_minimap(self) -> None:
        """Position minimap at bottom-left of central widget."""
        if self._minimap and self._central_widget:
            # Position at bottom-left with 10px margin
            margin = 10
            x = margin
            y = self._central_widget.height() - self._minimap.height() - margin
            self._minimap.move(x, y)
            self._minimap.raise_()  # Ensure it's on top
    
    def show_minimap(self) -> None:
        """Show the minimap."""
        if self._minimap:
            self._minimap.setVisible(True)
            self._position_minimap()
    
    def hide_minimap(self) -> None:
        """Hide the minimap."""
        if self._minimap:
            self._minimap.setVisible(False)
    
    def _on_toggle_minimap(self, checked: bool) -> None:
        """Handle minimap toggle."""
        if checked:
            self.show_minimap()
        else:
            self.hide_minimap()
    
    def resizeEvent(self, event):
        """Handle window resize to reposition minimap."""
        super().resizeEvent(event)
        self._position_minimap()
    
    def set_central_widget(self, widget: QWidget) -> None:
        """
        Set the central widget (typically the node graph).
        
        Args:
            widget: Widget to display in the central area
        """
        self._central_widget = widget
        self.setCentralWidget(widget)
        
        # Initialize minimap if widget is a node graph
        if hasattr(widget, 'graph'):
            self._create_minimap(widget.graph)
    
    def set_modified(self, modified: bool) -> None:
        """
        Set the modified state of the workflow.

        Args:
            modified: Whether the workflow has unsaved changes
        """
        self._is_modified = modified
        self._update_window_title()

        # Update breadcrumb bar
        if self._breadcrumb_bar:
            self._breadcrumb_bar.set_modified(modified)

        # Trigger real-time validation when workflow is modified
        if modified:
            self.on_workflow_changed()
    
    def is_modified(self) -> bool:
        """
        Check if the workflow has unsaved changes.
        
        Returns:
            True if workflow is modified
        """
        return self._is_modified
    
    def set_current_file(self, file_path: Optional[Path]) -> None:
        """
        Set the current workflow file path.

        Args:
            file_path: Path to the workflow file, or None for new workflow
        """
        self._current_file = file_path
        self._update_window_title()

        # Update breadcrumb bar
        if self._breadcrumb_bar:
            self._breadcrumb_bar.set_workflow_file(file_path)
    
    def get_current_file(self) -> Optional[Path]:
        """
        Get the current workflow file path.
        
        Returns:
            Path to current file, or None if no file
        """
        return self._current_file
    
    def _update_window_title(self) -> None:
        """Update window title with current file and modified state."""
        title = APP_NAME
        
        if self._current_file:
            title = f"{self._current_file.name} - {APP_NAME}"
        else:
            title = f"Untitled - {APP_NAME}"
        
        if self._is_modified:
            title = f"*{title}"
        
        self.setWindowTitle(title)
    
    def _update_actions(self) -> None:
        """Update action states based on current state."""
        # Save action enabled only if modified
        self.action_save.setEnabled(self._is_modified)
    
    def _on_new_workflow(self) -> None:
        """Handle new workflow request."""
        if self._check_unsaved_changes():
            self.workflow_new.emit()
            self.set_current_file(None)
            self.set_modified(False)
            self.statusBar().showMessage("New workflow created", 3000)
    
    def _on_new_from_template(self) -> None:
        """Handle new from template request."""
        from .template_browser import show_template_browser
        
        if not self._check_unsaved_changes():
            return
        
        # Show template browser
        template = show_template_browser(self)
        if template:
            # Emit signal with template info (app.py will handle loading)
            self.statusBar().showMessage(f"Loading template: {template.name}...", 3000)
            self.workflow_new_from_template.emit(template)
    
    def _on_open_workflow(self) -> None:
        """Handle open workflow request."""
        if not self._check_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Workflow",
            str(WORKFLOWS_DIR),
            "Workflow Files (*.json);;All Files (*.*)"
        )

        if file_path:
            self.workflow_open.emit(file_path)
            self.set_current_file(Path(file_path))
            self.set_modified(False)
            self.statusBar().showMessage(f"Opened: {Path(file_path).name}", 3000)

            # Validate after opening and show panel if issues found
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._validate_after_open)
    
    def _on_import_workflow(self) -> None:
        """Handle import workflow request."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Workflow",
            str(WORKFLOWS_DIR),
            "Workflow Files (*.json);;All Files (*.*)"
        )

        if file_path:
            self.workflow_import.emit(file_path)
            self.statusBar().showMessage(f"Importing: {Path(file_path).name}...", 3000)

    def _on_export_selected(self) -> None:
        """Handle export selected nodes request."""
        # Check if any nodes are selected
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            self.statusBar().showMessage("No graph available", 3000)
            return

        graph = self._central_widget.graph
        selected_nodes = graph.selected_nodes()

        if not selected_nodes:
            QMessageBox.information(
                self,
                "Export Selected Nodes",
                "Please select one or more nodes to export."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Selected Nodes",
            str(WORKFLOWS_DIR / "exported_nodes.json"),
            "Workflow Files (*.json);;All Files (*.*)"
        )

        if file_path:
            self.workflow_export_selected.emit(file_path)
            self.statusBar().showMessage(f"Exporting {len(selected_nodes)} nodes...", 3000)

    def _on_paste_workflow(self) -> None:
        """Handle paste workflow JSON from clipboard."""
        from PySide6.QtWidgets import QApplication
        import orjson

        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            self.statusBar().showMessage("Clipboard is empty", 3000)
            return

        # Try to parse as JSON
        try:
            data = orjson.loads(text)

            # Basic validation - should have nodes key
            if "nodes" not in data:
                QMessageBox.warning(
                    self,
                    "Invalid Workflow JSON",
                    "The clipboard content does not appear to be a valid workflow.\n"
                    "Expected a JSON object with a 'nodes' key."
                )
                return
        except Exception as e:
            QMessageBox.warning(
                self,
                "Invalid JSON",
                f"The clipboard content is not valid JSON.\n\nError: {str(e)}"
            )
            return

    def _on_create_snippet(self) -> None:
        """Handle create snippet from selection request."""
        from .snippet_creator_dialog import SnippetCreatorDialog
        from ..core.workflow_schema import NodeConnection

        # Get selected nodes from the graph
        graph = self._central_widget.graph
        selected_nodes = graph.selected_nodes()

        if not selected_nodes:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select nodes to create a snippet.\n\n"
                "Select multiple nodes by dragging a selection box or holding Shift while clicking nodes."
            )
            return

        # Extract connections from the visual graph
        all_connections = []
        for visual_node in graph.all_nodes():
            # Get the CasareRPA node to access node_id
            casare_node = visual_node.get_casare_node()
            if not casare_node:
                continue

            source_node_id = casare_node.node_id

            # Get output connections
            for output_port in visual_node.output_ports():
                for connected_port in output_port.connected_ports():
                    target_visual_node = connected_port.node()
                    target_casare_node = target_visual_node.get_casare_node()
                    if not target_casare_node:
                        continue

                    connection = NodeConnection(
                        source_node=source_node_id,
                        source_port=output_port.name(),
                        target_node=target_casare_node.node_id,
                        target_port=connected_port.name()
                    )
                    all_connections.append(connection)

        # Open snippet creator dialog
        dialog = SnippetCreatorDialog(
            selected_visual_nodes=selected_nodes,
            all_connections=all_connections,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info(f"Snippet created successfully from {len(selected_nodes)} nodes")
            self.statusBar().showMessage("Snippet created and saved to library", 3000)
        else:
            logger.info("Snippet creation cancelled")

    def _on_open_snippet_library(self) -> None:
        """Handle open snippet library browser request."""
        from .snippet_browser_dialog import SnippetBrowserDialog

        # Open snippet browser dialog
        dialog = SnippetBrowserDialog(parent=self)

        # Connect signal to handle snippet insertion
        dialog.snippet_insert_requested.connect(self._on_snippet_insert_requested)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info("Snippet insertion completed")
        else:
            logger.info("Snippet browser closed without insertion")

    def _on_snippet_insert_requested(self, snippet_definition, is_collapsed: bool):
        """
        Handle snippet insertion into the canvas.

        Args:
            snippet_definition: SnippetDefinition to insert
            is_collapsed: Whether to insert as collapsed node or expanded
        """
        from .workflow_import import WorkflowImporter

        logger.info(
            f"Inserting snippet '{snippet_definition.name}' "
            f"({'collapsed' if is_collapsed else 'expanded'})"
        )

        if is_collapsed:
            # Insert as a single collapsed SnippetNode
            from ..nodes.snippet_node import SnippetNode
            from ..utils.id_generator import generate_node_id

            # Create visual node at center of view
            graph = self._central_widget.graph
            view_center = graph.viewer().sceneRect().center()

            # Create SnippetNode visual node
            visual_node = graph.create_node(
                f"{VisualSnippetNode.__identifier__}.{VisualSnippetNode.__name__}",
                pos=[view_center.x(), view_center.y()]
            )

            if not visual_node:
                QMessageBox.critical(
                    self,
                    "Insert Failed",
                    "Failed to create snippet node.\n\n"
                    "Make sure VisualSnippetNode is properly registered."
                )
                return

            # Create casare SnippetNode instance
            node_id = generate_node_id("SnippetNode")
            config = {
                "snippet_id": snippet_definition.snippet_id,
                "snippet_name": snippet_definition.name,
            }

            casare_node = SnippetNode(node_id, config=config)

            # Load snippet definition
            casare_node.set_snippet_definition(snippet_definition)

            # Link visual and casare nodes
            visual_node._casare_node = casare_node
            visual_node.set_property("node_id", node_id)

            # Update visual node display name
            visual_node.set_name(snippet_definition.name)

            # Set snippet info in visual node widgets
            if hasattr(visual_node, "view"):
                snippet_name_widget = visual_node.view.get_widget("snippet_name")
                if snippet_name_widget:
                    snippet_name_widget.set_value(snippet_definition.name)

                snippet_version_widget = visual_node.view.get_widget("snippet_version")
                if snippet_version_widget:
                    snippet_version_widget.set_value(snippet_definition.version)

            self.statusBar().showMessage(
                f"Inserted snippet '{snippet_definition.name}' as collapsed node",
                3000
            )
            logger.info(f"Created collapsed snippet node: {snippet_definition.name}")
        else:
            # Insert as expanded nodes (inline)
            # Convert snippet to workflow-like structure
            workflow_data = {
                "nodes": snippet_definition.nodes,
                "connections": [conn.to_dict() for conn in snippet_definition.connections],
            }

            # Use WorkflowImporter to import nodes with ID remapping
            graph = self._central_widget.graph
            importer = WorkflowImporter(graph)
            imported_nodes = importer.import_workflow_data(
                workflow_data,
                offset_x=100,  # Offset from current view
                offset_y=100,
            )

            self.statusBar().showMessage(
                f"Inserted {len(imported_nodes)} nodes from snippet '{snippet_definition.name}'",
                3000
            )

    def _on_save_workflow(self) -> None:
        """Handle save workflow request."""
        # Validate before saving
        if not self._check_validation_before_save():
            return

        if self._current_file:
            self.workflow_save.emit()
            self.set_modified(False)
            self.statusBar().showMessage(f"Saved: {self._current_file.name}", 3000)
        else:
            self._on_save_as_workflow()

    def _on_save_as_workflow(self) -> None:
        """Handle save as workflow request."""
        # Validate before saving
        if not self._check_validation_before_save():
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workflow As",
            str(WORKFLOWS_DIR),
            "Workflow Files (*.json);;All Files (*.*)"
        )

        if file_path:
            self.workflow_save_as.emit(file_path)
            self.set_current_file(Path(file_path))
            self.set_modified(False)
            self.statusBar().showMessage(f"Saved as: {Path(file_path).name}", 3000)
    
    def _on_run_workflow(self) -> None:
        """Handle run workflow request (F3)."""
        # Validate before running - block if errors
        if not self._check_validation_before_run():
            return

        self.workflow_run.emit()
        self.action_run.setEnabled(False)
        self.action_run_to_node.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(True)
        self.statusBar().showMessage("Workflow execution started...", 0)

    def _on_run_to_node(self) -> None:
        """Handle run to selected node request (F4)."""
        # Get selected node from the graph
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            self._on_run_workflow()  # Fallback to full run
            return

        graph = self._central_widget.graph
        selected_nodes = graph.selected_nodes()

        # If no node is selected, fall back to full workflow run
        if not selected_nodes:
            self.statusBar().showMessage("No node selected - running full workflow", 3000)
            self._on_run_workflow()
            return

        # Get the first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            self.statusBar().showMessage("Selected node has no ID - running full workflow", 3000)
            self._on_run_workflow()
            return

        # Validate before running
        if not self._check_validation_before_run():
            return

        # Get the node name for display
        node_name = target_node.name() if hasattr(target_node, 'name') else target_node_id

        # Emit signal with target node ID
        self.workflow_run_to_node.emit(target_node_id)
        self.action_run.setEnabled(False)
        self.action_run_to_node.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(True)
        self.statusBar().showMessage(f"Running to node: {node_name}...", 0)

    def _on_run_single_node(self) -> None:
        """Handle run single selected node request (F5)."""
        # Get selected node from the graph
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            self.statusBar().showMessage("No graph available", 3000)
            return

        graph = self._central_widget.graph
        selected_nodes = graph.selected_nodes()

        # If no node is selected, show message
        if not selected_nodes:
            self.statusBar().showMessage("No node selected - select a node to run", 3000)
            return

        # Get the first selected node's ID
        target_node = selected_nodes[0]
        target_node_id = target_node.get_property("node_id")

        if not target_node_id:
            self.statusBar().showMessage("Selected node has no ID", 3000)
            return

        # Get the node name for display
        node_name = target_node.name() if hasattr(target_node, 'name') else target_node_id

        # Emit signal with target node ID
        self.workflow_run_single_node.emit(target_node_id)
        self.statusBar().showMessage(f"Running node: {node_name}...", 0)

    def _on_pause_workflow(self, checked: bool) -> None:
        """Handle pause/resume workflow request."""
        if checked:
            self.workflow_pause.emit()
            self.statusBar().showMessage("Workflow paused", 0)
        else:
            self.workflow_resume.emit()
            self.statusBar().showMessage("Workflow resumed...", 0)
    
    def _on_stop_workflow(self) -> None:
        """Handle stop workflow request."""
        self.workflow_stop.emit()
        self.action_run.setEnabled(True)
        self.action_run_to_node.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution stopped", 3000)

    def _on_select_nearest_node(self) -> None:
        """Select the nearest node to the current mouse cursor position (hotkey 2)."""
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            return

        graph = self._central_widget.graph
        viewer = graph.viewer()
        if not viewer:
            return

        # Get mouse position in scene coordinates
        from PySide6.QtGui import QCursor
        global_pos = QCursor.pos()
        view_pos = viewer.mapFromGlobal(global_pos)
        scene_pos = viewer.mapToScene(view_pos)

        # Find nearest node
        all_nodes = graph.all_nodes()
        if not all_nodes:
            self.statusBar().showMessage("No nodes in graph", 2000)
            return

        nearest_node = None
        min_distance = float('inf')

        for node in all_nodes:
            node_pos = node.pos()
            # Calculate distance from mouse to node center
            dx = scene_pos.x() - node_pos[0]
            dy = scene_pos.y() - node_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        if nearest_node:
            # Clear current selection and select the nearest node
            graph.clear_selection()
            nearest_node.set_selected(True)
            node_name = nearest_node.name() if hasattr(nearest_node, 'name') else "Node"
            self.statusBar().showMessage(f"Selected: {node_name}", 2000)

    def _on_toggle_disable_node(self) -> None:
        """Toggle disable state on nearest node to mouse (hotkey 4). Disabled nodes are bypassed during execution."""
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            return

        graph = self._central_widget.graph
        viewer = graph.viewer()
        if not viewer:
            return

        # Get mouse position in scene coordinates
        from PySide6.QtGui import QCursor
        global_pos = QCursor.pos()
        view_pos = viewer.mapFromGlobal(global_pos)
        scene_pos = viewer.mapToScene(view_pos)

        # Find nearest node to mouse
        all_nodes = graph.all_nodes()
        if not all_nodes:
            self.statusBar().showMessage("No nodes in graph", 2000)
            return

        nearest_node = None
        min_distance = float('inf')

        for node in all_nodes:
            node_pos = node.pos()
            dx = scene_pos.x() - node_pos[0]
            dy = scene_pos.y() - node_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        if not nearest_node:
            return

        # Select and toggle disable on the nearest node
        graph.clear_selection()
        nearest_node.set_selected(True)

        # Toggle disable state on the nearest node
        casare_node = nearest_node.get_casare_node() if hasattr(nearest_node, 'get_casare_node') else None

        if casare_node:
            # Toggle the disabled state
            current_disabled = casare_node.config.get("_disabled", False)
            new_disabled = not current_disabled
            casare_node.config["_disabled"] = new_disabled

            # Update visual appearance
            if hasattr(nearest_node, 'view') and nearest_node.view:
                if new_disabled:
                    # Make node semi-transparent when disabled
                    nearest_node.view.setOpacity(0.4)
                else:
                    nearest_node.view.setOpacity(1.0)

            node_name = nearest_node.name() if hasattr(nearest_node, 'name') else "Node"
            state = "disabled" if new_disabled else "enabled"
            self.statusBar().showMessage(f"{node_name} {state}", 2000)

    def _on_open_hotkey_manager(self) -> None:
        """Open the hotkey manager dialog."""
        from .hotkey_manager import HotkeyManagerDialog
        
        # Collect all actions
        actions = {
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
            "run_to_node": self.action_run_to_node,
            "pause": self.action_pause,
            "stop": self.action_stop,
            "hotkey_manager": self.action_hotkey_manager,
        }
        
        dialog = HotkeyManagerDialog(actions, self)
        dialog.exec()
    
    def _on_toggle_auto_connect(self, checked: bool) -> None:
        """Handle auto-connect toggle."""
        # This will be connected by the app when the node graph is available
        pass

    def _on_open_performance_dashboard(self) -> None:
        """Open the performance dashboard dialog."""
        from .performance_dashboard import PerformanceDashboardDialog

        dialog = PerformanceDashboardDialog(self)
        dialog.exec()

    def _on_open_command_palette(self) -> None:
        """Open the command palette dialog."""
        if self._command_palette:
            self._command_palette.show_palette()

    def _on_find_node(self) -> None:
        """Open the node search dialog (Ctrl+F)."""
        if not self._central_widget or not hasattr(self._central_widget, 'graph'):
            self.statusBar().showMessage("No graph available", 3000)
            return

        from .node_search import NodeSearchDialog
        dialog = NodeSearchDialog(self._central_widget.graph, self)
        dialog.show_search()

    def _update_recent_files_menu(self) -> None:
        """Update the recent files submenu."""
        from .recent_files import get_recent_files_manager

        self._recent_files_menu.clear()
        manager = get_recent_files_manager()
        recent = manager.get_recent_files()

        if not recent:
            action = self._recent_files_menu.addAction("(No recent files)")
            action.setEnabled(False)
            return

        for i, file_info in enumerate(recent[:10]):
            path = file_info["path"]
            name = file_info["name"]
            action = self._recent_files_menu.addAction(f"&{i+1}. {name}")
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._on_open_recent_file(p))

        self._recent_files_menu.addSeparator()
        clear_action = self._recent_files_menu.addAction("Clear Recent Files")
        clear_action.triggered.connect(self._on_clear_recent_files)

    def _on_open_recent_file(self, path: str) -> None:
        """Open a recent file."""
        from pathlib import Path
        if not self._check_unsaved_changes():
            return

        file_path = Path(path)
        if file_path.exists():
            self.workflow_open.emit(str(file_path))
            self.set_current_file(file_path)
            self.set_modified(False)
            self.statusBar().showMessage(f"Opened: {file_path.name}", 3000)
        else:
            QMessageBox.warning(self, "File Not Found", f"File not found:\n{path}")
            # Remove from recent files
            from .recent_files import get_recent_files_manager
            manager = get_recent_files_manager()
            manager.remove_file(file_path)
            self._update_recent_files_menu()

    def _on_clear_recent_files(self) -> None:
        """Clear the recent files list."""
        from .recent_files import get_recent_files_manager
        manager = get_recent_files_manager()
        manager.clear()
        self._update_recent_files_menu()
        self.statusBar().showMessage("Recent files cleared", 3000)

    def add_to_recent_files(self, file_path) -> None:
        """Add a file to the recent files list."""
        from .recent_files import get_recent_files_manager
        from pathlib import Path
        manager = get_recent_files_manager()
        manager.add_file(Path(file_path) if isinstance(file_path, str) else file_path)
        self._update_recent_files_menu()

    def _on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>Windows Desktop RPA Platform</p>"
            f"<p>Visual workflow automation with node-based editor</p>"
            f"<p>Built with PySide6, NodeGraphQt, and Playwright</p>"
        )
    
    def _check_unsaved_changes(self) -> bool:
        """
        Check for unsaved changes and prompt user.
        
        Returns:
            True if it's safe to proceed, False if user cancelled
        """
        if not self._is_modified:
            return True
        
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The workflow has unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if reply == QMessageBox.StandardButton.Save:
            self._on_save_workflow()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

    def _validate_after_open(self) -> None:
        """Validate workflow after opening and show warnings if issues found."""
        result = self.validate_current_workflow(show_panel=False)

        if not result.is_valid:
            # Show error dialog for blocking issues
            QMessageBox.warning(
                self,
                "Validation Issues",
                f"The opened workflow has {result.error_count} error(s) and "
                f"{result.warning_count} warning(s).\n\n"
                "Please review the validation panel for details.",
            )
            self.show_validation_panel()
        elif result.warning_count > 0:
            # Just show the panel for warnings
            self.show_validation_panel()

    def _check_validation_before_save(self) -> bool:
        """
        Check validation before saving. Warn about issues but allow saving.

        Returns:
            True if save should proceed, False to cancel
        """
        result = self.validate_current_workflow(show_panel=False)

        if not result.is_valid:
            # Show warning but allow saving
            reply = QMessageBox.warning(
                self,
                "Validation Issues",
                f"The workflow has {result.error_count} error(s).\n\n"
                "Do you want to save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                self.show_validation_panel()
                return False

        return True

    def _check_validation_before_run(self) -> bool:
        """
        Check validation before running. Block execution if there are errors.

        Returns:
            True if run should proceed, False to block
        """
        result = self.validate_current_workflow(show_panel=False)

        if not result.is_valid:
            # Block execution if there are errors
            QMessageBox.critical(
                self,
                "Cannot Run Workflow",
                f"The workflow has {result.error_count} validation error(s) "
                "that must be fixed before running.\n\n"
                "Please review the validation panel for details.",
            )
            self.show_validation_panel()
            return False

        if result.warning_count > 0:
            # Warn but allow running
            reply = QMessageBox.warning(
                self,
                "Validation Warnings",
                f"The workflow has {result.warning_count} warning(s).\n\n"
                "Do you want to run anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.No:
                self.show_validation_panel()
                return False

        return True

    def _create_debug_components(self) -> None:
        """Create debug toolbar."""
        from .debug_toolbar import DebugToolbar

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
    
    def get_debug_toolbar(self) -> Optional['DebugToolbar']:
        """
        Get the debug toolbar.

        Returns:
            DebugToolbar instance or None
        """
        return self._debug_toolbar if hasattr(self, '_debug_toolbar') else None

    def get_variable_inspector(self):
        """
        Get the Variable Inspector dock for real-time variable values.

        Returns:
            VariableInspectorDock instance or None
        """
        return self._variable_inspector_dock

    def show_variable_inspector(self) -> None:
        """Show the Variable Inspector dock."""
        if self._variable_inspector_dock:
            self._variable_inspector_dock.show()
            self.action_toggle_variable_inspector.setChecked(True)

    def get_execution_history_viewer(self):
        """
        Get the history tab from bottom panel.

        Returns:
            HistoryTab instance or None
        """
        if self._bottom_panel:
            return self._bottom_panel.get_history_tab()
        return None

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
        """Open the Desktop Selector Builder dialog."""
        try:
            from .desktop_selector_builder import DesktopSelectorBuilder

            dialog = DesktopSelectorBuilder(parent=self)

            if dialog.exec():
                selector = dialog.get_selected_selector()
                if selector:
                    logger.info(f"Selector selected from builder: {selector}")
                    # User can copy selector from here

        except Exception as e:
            logger.error(f"Failed to open desktop selector builder: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Desktop Selector Builder:\n{str(e)}"
            )

    def _on_create_frame(self) -> None:
        """Create a frame around selected nodes."""
        try:
            from .node_frame import group_selected_nodes, create_frame, NodeFrame

            # Get the node graph from central widget
            if not self._central_widget or not hasattr(self._central_widget, 'graph'):
                logger.warning("Node graph not available")
                return

            graph = self._central_widget.graph
            viewer = graph.viewer()
            selected_nodes = graph.selected_nodes()

            # Set graph reference for all frames
            NodeFrame.set_graph(graph)

            if selected_nodes:
                # Group selected nodes
                frame = group_selected_nodes(viewer, "Group", selected_nodes)
                if frame:
                    logger.info(f"Created frame around {len(selected_nodes)} nodes")
            else:
                # Create empty frame at center
                frame = create_frame(
                    viewer,
                    title="Frame",
                    color_name="blue",
                    position=(0, 0),
                    size=(400, 300),
                    graph=graph
                )
                logger.info("Created empty frame")

        except Exception as e:
            logger.error(f"Failed to create frame: {e}")
            QMessageBox.warning(
                self,
                "Create Frame",
                f"Failed to create frame:\n{str(e)}"
            )

    def set_browser_running(self, running: bool) -> None:
        """
        Enable/disable browser-dependent actions.

        Args:
            running: True if browser is running
        """
        self.action_pick_selector.setEnabled(running)
        self.action_record_workflow.setEnabled(running)

    def _on_schedule_workflow(self) -> None:
        """Handle schedule workflow action."""
        from .schedule_dialog import ScheduleDialog, WorkflowSchedule
        from .schedule_storage import get_schedule_storage

        # Check if workflow is saved
        if not self._current_file:
            reply = QMessageBox.question(
                self,
                "Save Required",
                "The workflow must be saved before scheduling. Save now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_save_as_workflow()
                if not self._current_file:
                    return  # User cancelled save
            else:
                return

        # Get workflow name
        workflow_name = self._current_file.stem if self._current_file else "Untitled"

        # Show schedule dialog
        dialog = ScheduleDialog(
            workflow_path=self._current_file,
            workflow_name=workflow_name,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_schedule:
            # Save the schedule
            storage = get_schedule_storage()
            if storage.save_schedule(dialog.result_schedule):
                self.statusBar().showMessage(
                    f"Schedule created: {dialog.result_schedule.name}",
                    5000
                )
                logger.info(f"Workflow scheduled: {dialog.result_schedule.name}")
            else:
                QMessageBox.warning(
                    self,
                    "Schedule Error",
                    "Failed to save schedule"
                )

    def _on_manage_schedules(self) -> None:
        """Handle manage schedules action."""
        from .schedule_dialog import ScheduleManagerDialog
        from .schedule_storage import get_schedule_storage

        storage = get_schedule_storage()
        schedules = storage.get_all_schedules()

        dialog = ScheduleManagerDialog(schedules, parent=self)
        dialog.schedule_changed.connect(lambda: self._save_all_schedules(dialog))
        dialog.run_schedule.connect(self._on_run_scheduled_workflow)

        dialog.exec()

    def _save_all_schedules(self, dialog) -> None:
        """Save all schedules from manager dialog."""
        from .schedule_storage import get_schedule_storage

        storage = get_schedule_storage()
        storage.save_all_schedules(dialog.get_schedules())
        self.statusBar().showMessage("Schedules updated", 3000)

    def _on_run_scheduled_workflow(self, schedule) -> None:
        """Run a scheduled workflow immediately."""
        from pathlib import Path

        workflow_path = Path(schedule.workflow_path)
        if not workflow_path.exists():
            QMessageBox.warning(
                self,
                "Workflow Not Found",
                f"The scheduled workflow could not be found:\n{workflow_path}"
            )
            return

        # Ask user if they want to open and run the workflow
        reply = QMessageBox.question(
            self,
            "Run Scheduled Workflow",
            f"Open and run '{schedule.workflow_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Check for unsaved changes
            if self._check_unsaved_changes():
                # Open the workflow
                self.workflow_open.emit(str(workflow_path))
                self.set_current_file(workflow_path)
                self.set_modified(False)
                # Run it
                self._on_run_workflow()

    def closeEvent(self, event) -> None:
        """
        Handle window close event.

        Args:
            event: Close event
        """
        if self._check_unsaved_changes():
            # Save UI state before closing
            self._save_ui_state()
            event.accept()
        else:
            event.ignore()

    # ==================== UI State Persistence ====================

    def _save_ui_state(self) -> None:
        """Save current UI state (window geometry, dock positions, etc.)."""
        try:
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("windowState", self.saveState())

            # Save dock visibility states
            if self._bottom_panel:
                self._settings.setValue("bottomPanelVisible", self._bottom_panel.isVisible())
                self._settings.setValue("bottomPanelTab", self._bottom_panel._tab_widget.currentIndex())

            if self._variable_inspector_dock:
                self._settings.setValue("variableInspectorVisible", self._variable_inspector_dock.isVisible())

            if self._properties_panel:
                self._settings.setValue("propertiesPanelVisible", self._properties_panel.isVisible())

            # Save execution timeline visibility
            if hasattr(self, '_execution_timeline_dock') and self._execution_timeline_dock:
                self._settings.setValue("executionTimelineVisible", self._execution_timeline_dock.isVisible())

            # Save minimap visibility
            if hasattr(self, '_minimap') and self._minimap:
                self._settings.setValue("minimapVisible", self._minimap.isVisible())

            self._settings.sync()
            logger.debug("UI state saved")
        except Exception as e:
            logger.warning(f"Failed to save UI state: {e}")

    def reset_ui_state(self) -> None:
        """Reset/clear all saved UI state settings."""
        try:
            self._settings.clear()
            self._settings.sync()
            logger.info("UI state settings cleared")
        except Exception as e:
            logger.warning(f"Failed to clear UI state: {e}")

    def _restore_ui_state(self) -> None:
        """Restore UI state from previous session."""
        try:
            # Skip restore on first run or if settings are empty
            if not self._settings.contains("geometry"):
                logger.debug("No saved UI state found, using defaults")
                return

            # Restore window geometry
            geometry = self._settings.value("geometry")
            if geometry:
                try:
                    self.restoreGeometry(geometry)
                except Exception:
                    pass  # Ignore invalid geometry

            # Restore window state (dock positions)
            state = self._settings.value("windowState")
            if state:
                try:
                    self.restoreState(state)
                except Exception:
                    pass  # Ignore invalid state

            # Restore dock visibility states
            if self._bottom_panel:
                visible = self._settings.value("bottomPanelVisible", True, type=bool)
                self._bottom_panel.setVisible(visible)
                self.action_toggle_bottom_panel.setChecked(visible)

                tab_index = self._settings.value("bottomPanelTab", 0, type=int)
                self._bottom_panel._tab_widget.setCurrentIndex(tab_index)

            if self._variable_inspector_dock:
                visible = self._settings.value("variableInspectorVisible", False, type=bool)
                self._variable_inspector_dock.setVisible(visible)
                self.action_toggle_variable_inspector.setChecked(visible)

            if self._properties_panel:
                visible = self._settings.value("propertiesPanelVisible", True, type=bool)
                self._properties_panel.setVisible(visible)

            # Restore execution timeline visibility
            if hasattr(self, '_execution_timeline_dock') and self._execution_timeline_dock:
                visible = self._settings.value("executionTimelineVisible", False, type=bool)
                self._execution_timeline_dock.setVisible(visible)
                if hasattr(self, 'action_toggle_timeline'):
                    self.action_toggle_timeline.setChecked(visible)

            # Restore minimap visibility
            if hasattr(self, '_minimap') and self._minimap:
                visible = self._settings.value("minimapVisible", False, type=bool)
                self._minimap.setVisible(visible)
                if hasattr(self, 'action_toggle_minimap'):
                    self.action_toggle_minimap.setChecked(visible)

            logger.debug("UI state restored from previous session")
        except Exception as e:
            logger.warning(f"Failed to restore UI state: {e}")

    def _schedule_ui_state_save(self) -> None:
        """Schedule UI state save (debounced to avoid too frequent saves)."""
        # Check if timer exists (it's created after dock widgets)
        if hasattr(self, '_state_save_timer') and self._state_save_timer:
            # Restart the timer - this provides debouncing
            self._state_save_timer.start(1000)  # Save after 1 second of inactivity
