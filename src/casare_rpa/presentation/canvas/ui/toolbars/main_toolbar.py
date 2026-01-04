"""
Main Toolbar UI Component.

Provides primary workflow actions (new, open, save, run, etc.).

Epic 7.5: Migrated to THEME_V2/TOKENS_V2 design system.
- Uses THEME_V2/TOKENS_V2 for all styling
- Uses icon_v2 singleton for Lucide SVG icons
- Zero hardcoded colors
- Zero animations/shadows
"""

from loguru import logger
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QToolBar, QWidget

# Epic 7.5: Migrated to v2 design system
from casare_rpa.presentation.canvas.theme import (
    TOKENS_V2,
    get_toolbar_styles_v2,
    icon_v2,
)


class MainToolbar(QToolBar):
    """
    Main toolbar for workflow operations.

    Features:
    - New workflow
    - Open workflow
    - Save workflow
    - Run workflow
    - Pause/Resume
    - Stop
    - Undo/Redo

    Signals:
        new_requested: Emitted when user requests new workflow
        open_requested: Emitted when user requests to open workflow
        save_requested: Emitted when user requests to save workflow
        save_as_requested: Emitted when user requests save as
        run_requested: Emitted when user requests to run workflow
        pause_requested: Emitted when user requests to pause workflow
        resume_requested: Emitted when user requests to resume workflow
        stop_requested: Emitted when user requests to stop workflow
        undo_requested: Emitted when user requests undo
        redo_requested: Emitted when user requests redo
    """

    new_requested = Signal()
    open_requested = Signal()
    save_requested = Signal()
    save_as_requested = Signal()
    run_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    stop_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the main toolbar.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Main", parent)

        self.setObjectName("MainToolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(
            QSize(TOKENS_V2.sizes.toolbar_icon_size, TOKENS_V2.sizes.toolbar_icon_size)
        )

        self._is_running = False
        self._is_paused = False

        self._create_actions()
        self._update_actions_state()
        self._apply_styles()

        logger.debug("MainToolbar initialized")

    def _create_actions(self) -> None:
        """Create toolbar actions with icons using icon_v2."""
        # File operations
        self.action_new = QAction(icon_v2.get_icon("file-plus", size=20), "New", self)
        self.action_new.setToolTip("Create new workflow (Ctrl+N)")
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self._on_new)
        self.addAction(self.action_new)

        self.action_open = QAction(icon_v2.get_icon("folder-open", size=20), "Open", self)
        self.action_open.setToolTip("Open workflow (Ctrl+O)")
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self._on_open)
        self.addAction(self.action_open)

        self.action_save = QAction(icon_v2.get_icon("save", size=20), "Save", self)
        self.action_save.setToolTip("Save workflow (Ctrl+S)")
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self._on_save)
        self.addAction(self.action_save)

        self.action_save_as = QAction(icon_v2.get_icon("save-all", size=20), "Save As", self)
        self.action_save_as.setToolTip("Save workflow as (Ctrl+Shift+S)")
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.triggered.connect(self._on_save_as)
        self.addAction(self.action_save_as)

        self.addSeparator()

        # Edit operations
        self.action_undo = QAction(icon_v2.get_icon("undo-2", size=20), "Undo", self)
        self.action_undo.setToolTip("Undo (Ctrl+Z)")
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.triggered.connect(self._on_undo)
        self.addAction(self.action_undo)

        self.action_redo = QAction(icon_v2.get_icon("redo-2", size=20), "Redo", self)
        self.action_redo.setToolTip("Redo (Ctrl+Y)")
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.triggered.connect(self._on_redo)
        self.addAction(self.action_redo)

        self.addSeparator()

        # Execution operations
        self.action_run = QAction(icon_v2.get_icon("play", size=20, state="accent"), "Run", self)
        self.action_run.setToolTip("Run workflow (F5)")
        self.action_run.setShortcut("F5")  # Standardized: F5 = Run/Continue
        self.action_run.triggered.connect(self._on_run)
        self.addAction(self.action_run)

        self.action_pause = QAction(icon_v2.get_icon("pause", size=20), "Pause", self)
        self.action_pause.setToolTip("Pause workflow execution")
        self.action_pause.triggered.connect(self._on_pause)
        self.addAction(self.action_pause)

        self.action_resume = QAction(icon_v2.get_icon("play", size=20), "Resume", self)
        self.action_resume.setToolTip("Resume workflow execution")
        self.action_resume.triggered.connect(self._on_resume)
        self.action_resume.setVisible(False)
        self.addAction(self.action_resume)

        self.action_stop = QAction(icon_v2.get_icon("square", size=20), "Stop", self)
        self.action_stop.setToolTip("Stop workflow execution (Shift+F5)")
        self.action_stop.setShortcut("Shift+F5")
        self.action_stop.triggered.connect(self._on_stop)
        self.addAction(self.action_stop)

    def _apply_styles(self) -> None:
        """Apply v2 dark theme using THEME_V2/TOKENS_V2 and get_toolbar_styles_v2()."""
        # Use the standardized v2 toolbar styles
        self.setStyleSheet(get_toolbar_styles_v2())

    def _update_actions_state(self) -> None:
        """Update action states based on execution state."""
        # Disable file operations during execution
        can_edit = not self._is_running
        self.action_new.setEnabled(can_edit)
        self.action_open.setEnabled(can_edit)

        # Execution controls
        self.action_run.setEnabled(not self._is_running)
        self.action_stop.setEnabled(self._is_running)

        # Pause/Resume toggle
        if self._is_paused:
            self.action_pause.setVisible(False)
            self.action_resume.setVisible(True)
        else:
            self.action_pause.setVisible(True)
            self.action_resume.setVisible(False)

        self.action_pause.setEnabled(self._is_running and not self._is_paused)
        self.action_resume.setEnabled(self._is_running and self._is_paused)

    def _on_new(self) -> None:
        """Handle new action."""
        logger.debug("New workflow requested")
        self.new_requested.emit()

    def _on_open(self) -> None:
        """Handle open action."""
        logger.debug("Open workflow requested")
        self.open_requested.emit()

    def _on_save(self) -> None:
        """Handle save action."""
        logger.debug("Save workflow requested")
        self.save_requested.emit()

    def _on_save_as(self) -> None:
        """Handle save as action."""
        logger.debug("Save as workflow requested")
        self.save_as_requested.emit()

    def _on_undo(self) -> None:
        """Handle undo action."""
        logger.debug("Undo requested")
        self.undo_requested.emit()

    def _on_redo(self) -> None:
        """Handle redo action."""
        logger.debug("Redo requested")
        self.redo_requested.emit()

    def _on_run(self) -> None:
        """Handle run action."""
        logger.debug("Run workflow requested")
        self.run_requested.emit()

    def _on_pause(self) -> None:
        """Handle pause action."""
        logger.debug("Pause workflow requested")
        self.pause_requested.emit()

    def _on_resume(self) -> None:
        """Handle resume action."""
        logger.debug("Resume workflow requested")
        self.resume_requested.emit()

    def _on_stop(self) -> None:
        """Handle stop action."""
        logger.debug("Stop workflow requested")
        self.stop_requested.emit()

    def set_execution_state(self, is_running: bool, is_paused: bool = False) -> None:
        """
        Update toolbar based on execution state.

        Args:
            is_running: Whether workflow is currently executing
            is_paused: Whether workflow is paused
        """
        self._is_running = is_running
        self._is_paused = is_paused
        self._update_actions_state()

    def set_undo_enabled(self, enabled: bool) -> None:
        """
        Set undo action enabled state.

        Args:
            enabled: Whether undo is available
        """
        self.action_undo.setEnabled(enabled)

    def set_redo_enabled(self, enabled: bool) -> None:
        """
        Set redo action enabled state.

        Args:
            enabled: Whether redo is available
        """
        self.action_redo.setEnabled(enabled)
