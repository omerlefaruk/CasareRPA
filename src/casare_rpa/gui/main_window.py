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
)

from ..utils.config import (
    APP_NAME,
    APP_VERSION,
    WORKFLOWS_DIR,
    GUI_WINDOW_WIDTH,
    GUI_WINDOW_HEIGHT,
)


class MainWindow(QMainWindow):
    """
    Main application window for CasareRPA.
    
    Provides the primary UI container with menu bar, toolbar, status bar,
    and central widget area for the node graph editor.
    
    Signals:
        workflow_new: Emitted when user requests new workflow
        workflow_open: Emitted when user requests to open workflow (str: file path)
        workflow_save: Emitted when user requests to save workflow
        workflow_save_as: Emitted when user requests save as (str: file path)
        workflow_run: Emitted when user requests to run workflow
        workflow_stop: Emitted when user requests to stop workflow
    """
    
    workflow_new = Signal()
    workflow_open = Signal(str)
    workflow_save = Signal()
    workflow_save_as = Signal(str)
    workflow_run = Signal()
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
        
        # Setup window
        self._setup_window()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        
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
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.setStatusTip("Redo the last undone action")
        self.action_redo.setEnabled(False)
        
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
        
        # Workflow actions
        self.action_run = QAction("&Run Workflow", self)
        self.action_run.setShortcut(QKeySequence("F5"))
        self.action_run.setStatusTip("Execute the workflow")
        self.action_run.triggered.connect(self._on_run_workflow)
        
        self.action_stop = QAction("&Stop Workflow", self)
        self.action_stop.setShortcut(QKeySequence("Shift+F5"))
        self.action_stop.setStatusTip("Stop workflow execution")
        self.action_stop.setEnabled(False)
        self.action_stop.triggered.connect(self._on_stop_workflow)
        
        # Help actions
        self.action_about = QAction("&About", self)
        self.action_about.setStatusTip("About CasareRPA")
        self.action_about.triggered.connect(self._on_about)
    
    def _create_menus(self) -> None:
        """Create menu bar and menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_new)
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
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_reset)
        view_menu.addSeparator()
        view_menu.addAction(self.action_fit_view)
        
        # Workflow menu
        workflow_menu = menubar.addMenu("&Workflow")
        workflow_menu.addAction(self.action_run)
        workflow_menu.addAction(self.action_stop)
        
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
        toolbar.addAction(self.action_stop)
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
    
    def set_central_widget(self, widget: QWidget) -> None:
        """
        Set the central widget (typically the node graph).
        
        Args:
            widget: Widget to display in the central area
        """
        self.setCentralWidget(widget)
    
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
        self.action_stop.setEnabled(True)
        self.statusBar().showMessage("Workflow execution started...", 0)
    
    def _on_stop_workflow(self) -> None:
        """Handle stop workflow request."""
        self.workflow_stop.emit()
        self.action_run.setEnabled(True)
        self.action_stop.setEnabled(False)
        self.statusBar().showMessage("Workflow execution stopped", 3000)
    
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
