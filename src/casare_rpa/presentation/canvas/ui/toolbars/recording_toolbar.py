"""
Recording Toolbar UI Component.

Provides recording controls for desktop and browser action recording.

Epic 7.6 Migration: Migrated to THEME_V2/TOKENS_V2 styling.
"""

from loguru import logger
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QToolBar, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2, icon_v2


class RecordingToolbar(QToolBar):
    """
    Toolbar for workflow recording operations.

    Features:
    - Record Desktop button (red circle icon)
    - Record Browser button (globe icon)
    - Stop Recording button (square icon)
    - Pause/Resume button
    - Recording status indicator
    - Action counter display

    Signals:
        record_desktop_requested: Emitted when user wants to record desktop
        record_browser_requested: Emitted when user wants to record browser
        stop_recording_requested: Emitted when user wants to stop recording
        pause_recording_requested: Emitted when user wants to pause recording
        resume_recording_requested: Emitted when user wants to resume recording
    """

    record_desktop_requested = Signal()
    record_browser_requested = Signal()
    stop_recording_requested = Signal()
    pause_recording_requested = Signal()
    resume_recording_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the recording toolbar.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Recording", parent)

        self.setObjectName("RecordingToolbar")
        self.setMovable(False)
        self.setFloatable(False)

        self._is_recording = False
        self._is_paused = False
        self._recording_type: str | None = None
        self._action_count = 0
        self._recording_seconds = 0

        self._duration_timer = QTimer(self)
        self._duration_timer.timeout.connect(self._update_duration)
        self._duration_timer.setInterval(1000)

        self._create_actions()
        self._update_actions_state()
        self._apply_styles()

        logger.debug("RecordingToolbar initialized")

    def _create_actions(self) -> None:
        """Create toolbar actions with icons."""
        # Record Desktop action
        self.action_record_desktop = QAction("Record Desktop", self)
        self.action_record_desktop.setToolTip("Start recording desktop actions (mouse, keyboard)")
        self.action_record_desktop.triggered.connect(self._on_record_desktop)
        self.addAction(self.action_record_desktop)

        # Record Browser action
        self.action_record_browser = QAction("Record Browser", self)
        self.action_record_browser.setToolTip(
            "Start recording browser actions (clicks, navigation, input)"
        )
        self.action_record_browser.triggered.connect(self._on_record_browser)
        self.addAction(self.action_record_browser)

        self.addSeparator()

        # Pause/Resume action
        self.action_pause = QAction(icon_v2("pause", size=20), "Pause", self)
        self.action_pause.setToolTip("Pause recording")
        self.action_pause.triggered.connect(self._on_pause)
        self.addAction(self.action_pause)

        self.action_resume = QAction(icon_v2("play", size=20), "Resume", self)
        self.action_resume.setToolTip("Resume recording")
        self.action_resume.triggered.connect(self._on_resume)
        self.action_resume.setVisible(False)
        self.addAction(self.action_resume)

        # Stop Recording action
        self.action_stop = QAction(icon_v2("stop", size=20), "Stop", self)
        self.action_stop.setToolTip("Stop recording (Esc)")
        self.action_stop.triggered.connect(self._on_stop)
        self.addAction(self.action_stop)

        self.addSeparator()

        # Status indicator
        self._status_indicator = QLabel()
        self._status_indicator.setFixedSize(
            TOKENS_V2.sizes.badge_width, TOKENS_V2.sizes.badge_height
        )
        self._status_indicator.setStyleSheet(
            f"background-color: {THEME_V2.text_muted}; border-radius: {TOKENS_V2.radius.full}px;"
        )
        self.addWidget(self._status_indicator)

        # Duration label
        self._duration_label = QLabel(" 00:00 ")
        self._duration_label.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-family: {TOKENS_V2.typography.mono};"
        )
        self.addWidget(self._duration_label)

        # Action count label
        self._action_count_label = QLabel(" | 0 actions ")
        self._action_count_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        self.addWidget(self._action_count_label)

    def _apply_styles(self) -> None:
        """Apply toolbar styling."""
        self.setStyleSheet(f"""
            QToolBar {{
                background: {THEME_V2.toolbar_bg};
                border-bottom: 1px solid {THEME_V2.toolbar_border};
                spacing: {TOKENS_V2.spacing.md}px;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
            }}
            QToolBar::separator {{
                background: {THEME_V2.border};
                width: 1px;
                margin: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.sm}px;
            }}
            QToolButton {{
                background: transparent;
                color: {THEME_V2.text_primary};
                border: none;
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.lg}px;
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QToolButton:hover {{
                background: {THEME_V2.bg_hover};
            }}
            QToolButton:pressed {{
                background: {THEME_V2.bg_selected};
            }}
            QToolButton:disabled {{
                color: {THEME_V2.text_disabled};
            }}
            QLabel {{
                color: {THEME_V2.text_secondary};
                font-size: {TOKENS_V2.typography.body}px;
                padding: 0 {TOKENS_V2.spacing.sm}px;
            }}
        """)

    def _update_actions_state(self) -> None:
        """Update action states based on recording state."""
        # Record buttons - disabled when recording
        self.action_record_desktop.setEnabled(not self._is_recording)
        self.action_record_browser.setEnabled(not self._is_recording)

        # Stop button - enabled when recording
        self.action_stop.setEnabled(self._is_recording)

        # Pause/Resume toggle
        if self._is_paused:
            self.action_pause.setVisible(False)
            self.action_resume.setVisible(True)
        else:
            self.action_pause.setVisible(True)
            self.action_resume.setVisible(False)

        self.action_pause.setEnabled(self._is_recording and not self._is_paused)
        self.action_resume.setEnabled(self._is_recording and self._is_paused)

        # Status indicator color
        if self._is_recording:
            if self._is_paused:
                color = THEME_V2.warning
            else:
                color = THEME_V2.error
        else:
            color = THEME_V2.text_muted

        self._status_indicator.setStyleSheet(
            f"background-color: {color}; border-radius: {TOKENS_V2.radius.full}px;"
        )

    def _on_record_desktop(self) -> None:
        """Handle record desktop action."""
        logger.debug("Record desktop requested")
        self.record_desktop_requested.emit()

    def _on_record_browser(self) -> None:
        """Handle record browser action."""
        logger.debug("Record browser requested")
        self.record_browser_requested.emit()

    def _on_pause(self) -> None:
        """Handle pause action."""
        logger.debug("Pause recording requested")
        self.pause_recording_requested.emit()

    def _on_resume(self) -> None:
        """Handle resume action."""
        logger.debug("Resume recording requested")
        self.resume_recording_requested.emit()

    def _on_stop(self) -> None:
        """Handle stop action."""
        logger.debug("Stop recording requested")
        self.stop_recording_requested.emit()

    def _update_duration(self) -> None:
        """Update the recording duration display."""
        if not self._is_paused:
            self._recording_seconds += 1
        minutes = self._recording_seconds // 60
        seconds = self._recording_seconds % 60
        self._duration_label.setText(f" {minutes:02d}:{seconds:02d} ")

    def set_recording_state(
        self,
        is_recording: bool,
        recording_type: str | None = None,
        is_paused: bool = False,
    ) -> None:
        """
        Update toolbar based on recording state.

        Args:
            is_recording: Whether recording is active
            recording_type: Type of recording ('desktop' or 'browser')
            is_paused: Whether recording is paused
        """
        was_recording = self._is_recording
        self._is_recording = is_recording
        self._is_paused = is_paused
        self._recording_type = recording_type if is_recording else None

        if is_recording and not was_recording:
            # Starting recording
            self._recording_seconds = 0
            self._action_count = 0
            self._duration_timer.start()
            self._action_count_label.setText(" | 0 actions ")
        elif not is_recording and was_recording:
            # Stopping recording
            self._duration_timer.stop()

        self._update_actions_state()

    def increment_action_count(self) -> None:
        """Increment the recorded action count."""
        self._action_count += 1
        self._action_count_label.setText(f" | {self._action_count} actions ")

    def set_action_count(self, count: int) -> None:
        """
        Set the action count directly.

        Args:
            count: Number of recorded actions
        """
        self._action_count = count
        self._action_count_label.setText(f" | {count} actions ")

    def get_recording_state(self) -> dict:
        """
        Get current recording state.

        Returns:
            Dictionary with is_recording, is_paused, recording_type, action_count
        """
        return {
            "is_recording": self._is_recording,
            "is_paused": self._is_paused,
            "recording_type": self._recording_type,
            "action_count": self._action_count,
            "duration_seconds": self._recording_seconds,
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        self._duration_timer.stop()
        logger.debug("RecordingToolbar cleaned up")

