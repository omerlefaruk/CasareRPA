"""
Main application window for CasareRPA.

This module provides the MainWindow class which serves as the primary
GUI container for the RPA platform.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal
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
    workflow_run = Signal()
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
        
        # Log viewer dock
        self._log_dock: Optional[QDockWidget] = None
        
        # Minimap overlay
        self._minimap: Optional[Minimap] = None
        self._central_widget: Optional[QWidget] = None
        
        # Debug components
        self._debug_toolbar: Optional['DebugToolbar'] = None
        self._variable_inspector: Optional['VariableInspectorPanel'] = None
        self._execution_history: Optional['ExecutionHistoryViewer'] = None
        
        # Setup window
        self._setup_window()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._create_log_viewer()
        self._create_debug_components()
        
        # Set initial state
        self._update_window_title()
        self._update_actions()
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT)
        
        # Enable high-DPI support
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        
        # Apply dark theme stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QMenuBar {
                background-color: #3c3f41;
                color: #bbbbbb;
                border-bottom: 1px solid #1e1e1e;
            }
            QMenuBar::item:selected {
                background-color: #4b6eaf;
            }
            QMenu {
                background-color: #3c3f41;
                color: #bbbbbb;
                border: 1px solid #1e1e1e;
            }
            QMenu::item:selected {
                background-color: #4b6eaf;
            }
            QToolBar {
                background-color: #3c3f41;
                border: none;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #4b6eaf;
                border-radius: 3px;
            }
            QStatusBar {
                background-color: #3c3f41;
                color: #bbbbbb;
                border-top: 1px solid #1e1e1e;
            }
        """)
    
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
        
        self.action_select_all = QAction("Select &All", self)
        self.action_select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.action_select_all.setStatusTip("Select all nodes")
        
        self.action_deselect_all = QAction("Deselect All", self)
        self.action_deselect_all.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.action_deselect_all.setStatusTip("Deselect all nodes")
        
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
        
        self.action_toggle_log = QAction("Execution &Log", self)
        self.action_toggle_log.setShortcut(QKeySequence("Ctrl+L"))
        self.action_toggle_log.setCheckable(True)
        self.action_toggle_log.setStatusTip("Show/hide execution log viewer")
        self.action_toggle_log.triggered.connect(self._on_toggle_log)
        
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
        
        # Workflow actions
        self.action_run = QAction("&Run Workflow", self)
        self.action_run.setShortcut(QKeySequence("F5"))
        self.action_run.setStatusTip("Execute the workflow (F5)")
        self.action_run.triggered.connect(self._on_run_workflow)
        
        self.action_pause = QAction("&Pause Workflow", self)
        self.action_pause.setShortcut(QKeySequence("F6"))
        self.action_pause.setStatusTip("Pause/Resume workflow execution (F6)")
        self.action_pause.setEnabled(False)
        self.action_pause.setCheckable(True)
        self.action_pause.triggered.connect(self._on_pause_workflow)
        
        self.action_stop = QAction("&Stop Workflow", self)
        self.action_stop.setShortcut(QKeySequence("F7"))
        self.action_stop.setStatusTip("Stop workflow execution (F7)")
        self.action_stop.setEnabled(False)
        self.action_stop.triggered.connect(self._on_stop_workflow)
        
        # Tools actions
        self.action_pick_selector = QAction("🎯 Pick Element Selector", self)
        self.action_pick_selector.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_pick_selector.setStatusTip("Pick an element from the browser (Ctrl+Shift+S)")
        self.action_pick_selector.setEnabled(False)  # Enabled when browser is running
        self.action_pick_selector.triggered.connect(self._on_pick_selector)
        
        self.action_record_workflow = QAction("⏺ Record Workflow", self)
        self.action_record_workflow.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self.action_record_workflow.setStatusTip("Record browser interactions as workflow (Ctrl+Shift+R)")
        self.action_record_workflow.setCheckable(True)
        self.action_record_workflow.setEnabled(False)  # Enabled when browser is running
        self.action_record_workflow.triggered.connect(self._on_toggle_recording)
        
        self.action_hotkey_manager = QAction("&Keyboard Shortcuts...", self)
        self.action_hotkey_manager.setShortcut(QKeySequence("Ctrl+K, Ctrl+S"))
        self.action_hotkey_manager.setStatusTip("View and customize keyboard shortcuts")
        self.action_hotkey_manager.triggered.connect(self._on_open_hotkey_manager)
        
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
        edit_menu.addAction(self.action_delete)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_select_all)
        edit_menu.addAction(self.action_deselect_all)
        
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
        view_menu.addAction(self.action_toggle_log)
        view_menu.addAction(self.action_toggle_minimap)
        
        # Workflow menu
        workflow_menu = menubar.addMenu("&Workflow")
        workflow_menu.addAction(self.action_run)
        workflow_menu.addAction(self.action_pause)
        workflow_menu.addAction(self.action_stop)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.action_pick_selector)
        tools_menu.addAction(self.action_record_workflow)
        tools_menu.addSeparator()
        tools_menu.addAction(self.action_hotkey_manager)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.action_about)
    
    def _create_toolbar(self) -> None:
        """Create toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # Add actions to toolbar
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_undo)
        toolbar.addAction(self.action_redo)
        toolbar.addSeparator()
        toolbar.addAction(self.action_run)
        toolbar.addAction(self.action_pause)
        toolbar.addAction(self.action_stop)
        toolbar.addSeparator()
        toolbar.addAction(self.action_pick_selector)
        toolbar.addAction(self.action_record_workflow)
        toolbar.addSeparator()
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        toolbar.addAction(self.action_zoom_reset)
        
        self.addToolBar(toolbar)
    
    def _create_status_bar(self) -> None:
        """Create status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready", 3000)
    
    def _create_log_viewer(self) -> None:
        """Create execution log viewer as dockable widget."""
        from .log_viewer import ExecutionLogViewer
        
        # Create dock widget
        self._log_dock = QDockWidget("Execution Log", self)
        self._log_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Create log viewer widget
        self._log_viewer = ExecutionLogViewer()
        self._log_dock.setWidget(self._log_viewer)
        
        # Add to main window (bottom by default)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._log_dock)
        
        # Initially hidden
        self._log_dock.hide()
    
    def get_log_viewer(self) -> Optional['ExecutionLogViewer']:
        """
        Get the execution log viewer.
        
        Returns:
            ExecutionLogViewer instance or None
        """
        return self._log_viewer if hasattr(self, '_log_viewer') else None
    
    def show_log_viewer(self) -> None:
        """Show the execution log viewer."""
        if self._log_dock:
            self._log_dock.show()
    
    def hide_log_viewer(self) -> None:
        """Hide the execution log viewer."""
        if self._log_dock:
            self._log_dock.hide()
    
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
    
    def _on_save_workflow(self) -> None:
        """Handle save workflow request."""
        if self._current_file:
            self.workflow_save.emit()
            self.set_modified(False)
            self.statusBar().showMessage(f"Saved: {self._current_file.name}", 3000)
        else:
            self._on_save_as_workflow()
    
    def _on_save_as_workflow(self) -> None:
        """Handle save as workflow request."""
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
        """Handle run workflow request."""
        self.workflow_run.emit()
        self.action_run.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(True)
        self.statusBar().showMessage("Workflow execution started...", 0)
    
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
        self.action_pause.setEnabled(False)
        self.action_pause.setChecked(False)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution stopped", 3000)
    
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
            "pause": self.action_pause,
            "stop": self.action_stop,
            "hotkey_manager": self.action_hotkey_manager,
        }
        
        dialog = HotkeyManagerDialog(actions, self)
        dialog.exec()
    
    def _on_toggle_log(self, checked: bool) -> None:
        """Handle log viewer toggle."""
        if checked:
            self.show_log_viewer()
        else:
            self.hide_log_viewer()
    
    def _on_toggle_auto_connect(self, checked: bool) -> None:
        """Handle auto-connect toggle."""
        # This will be connected by the app when the node graph is available
        pass
    
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
    
    def _create_debug_components(self) -> None:
        """Create debug toolbar and panels."""
        from .debug_toolbar import DebugToolbar
        from .variable_inspector import VariableInspectorPanel
        from .execution_history_viewer import ExecutionHistoryViewer
        
        # Create debug toolbar
        self._debug_toolbar = DebugToolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._debug_toolbar)
        
        # Create variable inspector panel
        self._variable_inspector = VariableInspectorPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._variable_inspector)
        self._variable_inspector.hide()  # Hidden by default
        
        # Create execution history viewer
        self._execution_history = ExecutionHistoryViewer(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._execution_history)
        self._execution_history.hide()  # Hidden by default
        
        # Add view menu options for debug panels
        view_menu = None
        for action in self.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break
        
        if view_menu:
            view_menu.addSeparator()
            view_menu.addAction(self._debug_toolbar.toggleViewAction())
            view_menu.addAction(self._variable_inspector.toggleViewAction())
            view_menu.addAction(self._execution_history.toggleViewAction())
    
    def get_debug_toolbar(self) -> Optional['DebugToolbar']:
        """
        Get the debug toolbar.
        
        Returns:
            DebugToolbar instance or None
        """
        return self._debug_toolbar if hasattr(self, '_debug_toolbar') else None
    
    def get_variable_inspector(self) -> Optional['VariableInspectorPanel']:
        """
        Get the variable inspector panel.
        
        Returns:
            VariableInspectorPanel instance or None
        """
        return self._variable_inspector if hasattr(self, '_variable_inspector') else None
    
    def get_execution_history_viewer(self) -> Optional['ExecutionHistoryViewer']:
        """
        Get the execution history viewer.
        
        Returns:
            ExecutionHistoryViewer instance or None
        """
        return self._execution_history if hasattr(self, '_execution_history') else None
    
    def _on_pick_selector(self) -> None:
        """Handle pick selector action."""
        # This will be connected in app.py to trigger selector mode
        pass
    
    def _on_toggle_recording(self, checked: bool) -> None:
        """Handle recording mode toggle."""
        # This will be connected in app.py to start/stop recording
        pass
    
    def set_browser_running(self, running: bool) -> None:
        """
        Enable/disable browser-dependent actions.
        
        Args:
            running: True if browser is running
        """
        self.action_pick_selector.setEnabled(running)
        self.action_record_workflow.setEnabled(running)
    
    def closeEvent(self, event) -> None:
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        if self._check_unsaved_changes():
            event.accept()
        else:
            event.ignore()
