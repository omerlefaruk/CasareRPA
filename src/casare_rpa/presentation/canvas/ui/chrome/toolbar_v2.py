"""
ToolbarV2 - Primary toolbar for NewMainWindow with THEME_V2 styling.

Epic 4.2: Chrome - Top Toolbar + Status Bar v2
- Main toolbar with workflow actions
- THEME_V2 colors (Cursor-like dark theme)
- IconProviderV2 icons with accent state for Run/Stop

Signals:
    new_requested: Emitted when user requests new workflow
    open_requested: Emitted when user requests to open workflow
    save_requested: Emitted when user requests to save workflow
    save_as_requested: Emitted when user requests save as
    run_requested: Emitted when user requests to run workflow
    pause_requested: Emitted when user requests to pause workflow
    stop_requested: Emitted when user requests to stop workflow
    undo_requested: Emitted when user requests undo
    redo_requested: Emitted when user requests redo

See: docs/UX_REDESIGN_PLAN.md Phase 4 Epic 4.2
"""

from loguru import logger
from PySide6.QtCore import QSize, Signal, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QToolBar, QWidget

from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon
from casare_rpa.presentation.canvas.theme_system.tokens_v2 import TOKENS_V2


class ToolbarV2(QToolBar):
    """
    V2 toolbar with THEME_V2 styling and IconProviderV2 icons.

    Features:
    - File operations: New, Open, Save, Save As
    - Edit operations: Undo, Redo
    - Execution operations: Run, Pause, Stop
    - Accent color (blue) for Run/Stop buttons
    - Keyboard shortcuts for all actions
    - Execution state management
    """

    # Signals (must match NewMainWindow workflow signals)
    new_requested = Signal()
    open_requested = Signal()
    save_requested = Signal()
    save_as_requested = Signal()
    run_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()
    record_requested = Signal(bool)
    # Dev mode signals (always visible for quick iteration)
    dev_reload_ui_requested = Signal()
    dev_restart_app_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the toolbar v2.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Main", parent)

        self.setObjectName("ToolbarV2")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(TOKENS_V2.sizes.icon_md, TOKENS_V2.sizes.icon_md))

        # Execution state tracking
        self._is_running = False
        self._is_paused = False

        self._create_actions()
        self._update_actions_state()

        logger.debug("ToolbarV2 initialized")

    def _create_actions(self) -> None:
        """Create toolbar actions with IconProviderV2 icons."""
        # File operations
        self.action_new = QAction(get_icon("file", size=20), "New", self)
        self.action_new.setToolTip("Create new workflow (Ctrl+N)")
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self._on_new)
        self.addAction(self.action_new)

        self.action_open = QAction(get_icon("folder-open", size=20), "Open", self)
        self.action_open.setToolTip("Open workflow (Ctrl+O)")
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self._on_open)
        self.addAction(self.action_open)

        self.action_save = QAction(get_icon("save", size=20), "Save", self)
        self.action_save.setToolTip("Save workflow (Ctrl+S)")
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self._on_save)
        self.addAction(self.action_save)

        self.action_save_as = QAction(get_icon("save", size=20), "Save As", self)
        self.action_save_as.setToolTip("Save workflow as (Ctrl+Shift+S)")
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.triggered.connect(self._on_save_as)
        self.addAction(self.action_save_as)

        self.addSeparator()

        # Edit operations
        self.action_undo = QAction(get_icon("undo", size=20), "Undo", self)
        self.action_undo.setToolTip("Undo (Ctrl+Z)")
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.triggered.connect(self._on_undo)
        self.addAction(self.action_undo)

        self.action_redo = QAction(get_icon("redo", size=20), "Redo", self)
        self.action_redo.setToolTip("Redo (Ctrl+Y)")
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.triggered.connect(self._on_redo)
        self.addAction(self.action_redo)

        self.addSeparator()

        # Execution operations - use accent color (blue)
        self.action_run = QAction(get_icon("play", size=20, state="accent"), "Run", self)
        self.action_run.setToolTip("Run workflow (F5)")
        self.action_run.setShortcut("F5")
        self.action_run.triggered.connect(self._on_run)
        self.addAction(self.action_run)

        self.action_pause = QAction(get_icon("pause", size=20), "Pause", self)
        self.action_pause.setToolTip("Pause workflow execution")
        self.action_pause.triggered.connect(self._on_pause)
        self.addAction(self.action_pause)

        self.action_stop = QAction(get_icon("stop", size=20, state="accent"), "Stop", self)
        self.action_stop.setToolTip("Stop workflow execution (Shift+F5)")
        self.action_stop.setShortcut("Shift+F5")
        self.action_stop.triggered.connect(self._on_stop)
        self.addAction(self.action_stop)

        self.addSeparator()

        # Recording operation
        self.action_record = QAction(get_icon("circle", size=20), "Record", self)
        self.action_record.setToolTip("Record browser interactions (Ctrl+R)")
        self.action_record.setShortcut("Ctrl+R")
        self.action_record.setCheckable(True)
        self.action_record.triggered.connect(self._on_record)
        self.addAction(self.action_record)

        self.addSeparator()

        # Dev mode buttons (always visible for quick iteration)
        self.action_dev_reload = QAction(get_icon("refresh", size=20), "Reload UI", self)
        self.action_dev_reload.setToolTip("Reload UI styles without restart (Ctrl+Shift+U)")
        self.action_dev_reload.setShortcut("Ctrl+Shift+U")
        self.action_dev_reload.triggered.connect(self._on_dev_reload_ui)
        self.addAction(self.action_dev_reload)

        self.action_dev_restart = QAction(get_icon("power", size=20), "Restart", self)
        self.action_dev_restart.setToolTip("Restart application (Ctrl+Shift+Q)")
        self.action_dev_restart.setShortcut("Ctrl+Shift+Q")
        self.action_dev_restart.triggered.connect(self._on_dev_restart_app)
        self.addAction(self.action_dev_restart)

    def _update_actions_state(self) -> None:
        """
        Update action states based on execution state.

        - Disables file operations during execution
        - Disables run during execution
        - Enables stop only during execution
        - Toggles pause/resume visibility
        """
        # Disable file operations during execution
        can_edit = not self._is_running
        self.action_new.setEnabled(can_edit)
        self.action_open.setEnabled(can_edit)
        self.action_save.setEnabled(can_edit)
        self.action_save_as.setEnabled(can_edit)
        self.action_record.setEnabled(can_edit)

        # Execution controls
        self.action_run.setEnabled(not self._is_running)
        self.action_stop.setEnabled(self._is_running)

        # Pause/Resume toggle - pause visible when running and not paused
        self.action_pause.setEnabled(self._is_running and not self._is_paused)

    @Slot()
    def _on_new(self) -> None:
        """Handle new action."""
        logger.debug("New workflow requested")
        self.new_requested.emit()

    @Slot()
    def _on_open(self) -> None:
        """Handle open action."""
        logger.debug("Open workflow requested")
        self.open_requested.emit()

    @Slot()
    def _on_save(self) -> None:
        """Handle save action."""
        logger.debug("Save workflow requested")
        self.save_requested.emit()

    @Slot()
    def _on_save_as(self) -> None:
        """Handle save as action."""
        logger.debug("Save as workflow requested")
        self.save_as_requested.emit()

    @Slot()
    def _on_undo(self) -> None:
        """Handle undo action."""
        logger.debug("Undo requested")
        self.undo_requested.emit()

    @Slot()
    def _on_redo(self) -> None:
        """Handle redo action."""
        logger.debug("Redo requested")
        self.redo_requested.emit()

    @Slot()
    def _on_run(self) -> None:
        """Handle run action."""
        logger.debug("Run workflow requested")
        self.run_requested.emit()

    @Slot()
    def _on_pause(self) -> None:
        """Handle pause action."""
        logger.debug("Pause workflow requested")
        self.pause_requested.emit()

    @Slot()
    def _on_stop(self) -> None:
        """Handle stop action."""
        logger.debug("Stop workflow requested")
        self.stop_requested.emit()

    @Slot(bool)
    def _on_record(self, checked: bool) -> None:
        """Handle record action."""
        logger.debug(f"Record browser requested: {checked}")
        # This will be connected to NewMainWindow's _on_menu_record_workflow or similar
        self.record_requested.emit(checked)

    @Slot()
    def _on_dev_reload_ui(self) -> None:
        """Handle dev reload UI action."""
        logger.debug("Dev reload UI requested")
        self.dev_reload_ui_requested.emit()

    @Slot()
    def _on_dev_restart_app(self) -> None:
        """Handle dev restart app action."""
        logger.debug("Dev restart app requested")
        self.dev_restart_app_requested.emit()

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
        logger.debug(f"ToolbarV2 execution state updated: running={is_running}, paused={is_paused}")

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

    def set_recording_enabled(self, enabled: bool) -> None:
        """Update recording action state."""
        self.action_record.setEnabled(enabled)

    def set_recording_active(self, active: bool) -> None:
        """Update recording action checked state."""
        self.action_record.setChecked(active)
