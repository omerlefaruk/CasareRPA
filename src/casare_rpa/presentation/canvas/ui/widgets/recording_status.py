"""
Recording Status Widget for CasareRPA.

Displays recording status in the status bar with animated indicator,
action count, and duration display.

Epic 7.6 Migration: Migrated to THEME_V2/TOKENS_V2 styling.
"""

from loguru import logger
from PySide6.QtCore import Property, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2


class RecordingIndicator(QWidget):
    """
    Animated recording indicator (pulsing red dot).

    Pulses between visible and semi-transparent when recording.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the recording indicator."""
        super().__init__(parent)
        self.setFixedSize(12, 12)

        self._is_recording = False
        self._is_paused = False
        self._opacity = 1.0

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_timer.setInterval(500)

        self._pulse_up = False

    def _get_opacity(self) -> float:
        return self._opacity

    def _set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    opacity = Property(float, _get_opacity, _set_opacity)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._is_recording:
            if self._is_paused:
                color = QColor(THEME_V2.warning)
            else:
                color = QColor(THEME_V2.error)
        else:
            color = QColor(THEME_V2.text_muted)

        color.setAlphaF(self._opacity)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 10, 10)

    def _pulse(self) -> None:
        """Pulse animation step."""
        if self._pulse_up:
            self._opacity = min(1.0, self._opacity + 0.2)
            if self._opacity >= 1.0:
                self._pulse_up = False
        else:
            self._opacity = max(0.3, self._opacity - 0.2)
            if self._opacity <= 0.3:
                self._pulse_up = True
        self.update()

    def set_recording(self, is_recording: bool, is_paused: bool = False) -> None:
        """
        Set recording state.

        Args:
            is_recording: Whether recording is active
            is_paused: Whether recording is paused
        """
        self._is_recording = is_recording
        self._is_paused = is_paused

        if is_recording and not is_paused:
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._opacity = 1.0

        self.update()


class RecordingStatusWidget(QWidget):
    """
    Status bar widget showing recording status.

    Features:
    - Animated recording indicator
    - Recording type label (Desktop/Browser)
    - Action count
    - Duration display

    Usage:
        status_widget = RecordingStatusWidget()
        status_bar.addPermanentWidget(status_widget)
        status_widget.set_recording_state(True, "browser")
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the recording status widget."""
        super().__init__(parent)

        self._is_recording = False
        self._is_paused = False
        self._recording_type: str | None = None
        self._action_count = 0
        self._duration_seconds = 0

        self._duration_timer = QTimer(self)
        self._duration_timer.timeout.connect(self._update_duration)
        self._duration_timer.setInterval(1000)

        self._setup_ui()
        self._apply_styles()
        self._update_visibility()

        logger.debug("RecordingStatusWidget initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        # Recording indicator
        self._indicator = RecordingIndicator(self)
        layout.addWidget(self._indicator)

        # Status label
        self._status_label = QLabel("Not Recording")
        layout.addWidget(self._status_label)

        # Separator
        self._separator1 = QLabel("|")
        self._separator1.setStyleSheet(f"color: {THEME_V2.border};")
        layout.addWidget(self._separator1)

        # Duration label
        self._duration_label = QLabel("00:00")
        layout.addWidget(self._duration_label)

        # Separator
        self._separator2 = QLabel("|")
        self._separator2.setStyleSheet(f"color: {THEME_V2.border};")
        layout.addWidget(self._separator2)

        # Action count label
        self._action_count_label = QLabel("0 actions")
        layout.addWidget(self._action_count_label)

    def _apply_styles(self) -> None:
        """Apply styling."""
        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
            }}
            QLabel {{
                color: {THEME_V2.text_secondary};
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.ui};
                padding: 0 2px;
            }}
        """)

    def _update_visibility(self) -> None:
        """Update visibility of elements based on recording state."""
        is_visible = self._is_recording
        self._separator1.setVisible(is_visible)
        self._duration_label.setVisible(is_visible)
        self._separator2.setVisible(is_visible)
        self._action_count_label.setVisible(is_visible)

        if not self._is_recording:
            self._status_label.setText("Not Recording")
            self._status_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        elif self._is_paused:
            self._status_label.setText(f"Recording {self._recording_type or ''} (Paused)")
            self._status_label.setStyleSheet(f"color: {THEME_V2.warning};")
        else:
            self._status_label.setText(f"Recording {self._recording_type or ''}...")
            self._status_label.setStyleSheet(f"color: {THEME_V2.error};")

    def _update_duration(self) -> None:
        """Update duration display."""
        if not self._is_paused:
            self._duration_seconds += 1
        minutes = self._duration_seconds // 60
        seconds = self._duration_seconds % 60
        self._duration_label.setText(f"{minutes:02d}:{seconds:02d}")

    def set_recording_state(
        self,
        is_recording: bool,
        recording_type: str | None = None,
        is_paused: bool = False,
    ) -> None:
        """
        Update recording state.

        Args:
            is_recording: Whether recording is active
            recording_type: Type of recording ('desktop' or 'browser')
            is_paused: Whether recording is paused
        """
        was_recording = self._is_recording
        self._is_recording = is_recording
        self._is_paused = is_paused
        self._recording_type = recording_type.title() if recording_type else None

        self._indicator.set_recording(is_recording, is_paused)

        if is_recording and not was_recording:
            # Starting recording
            self._duration_seconds = 0
            self._action_count = 0
            self._duration_timer.start()
            self._action_count_label.setText("0 actions")
        elif not is_recording and was_recording:
            # Stopping recording
            self._duration_timer.stop()

        self._update_visibility()

    def set_action_count(self, count: int) -> None:
        """
        Update action count display.

        Args:
            count: Number of recorded actions
        """
        self._action_count = count
        suffix = "action" if count == 1 else "actions"
        self._action_count_label.setText(f"{count} {suffix}")

    def increment_action_count(self) -> None:
        """Increment the action count by one."""
        self.set_action_count(self._action_count + 1)

    def get_state(self) -> dict:
        """
        Get current state.

        Returns:
            Dictionary with recording state
        """
        return {
            "is_recording": self._is_recording,
            "is_paused": self._is_paused,
            "recording_type": self._recording_type,
            "action_count": self._action_count,
            "duration_seconds": self._duration_seconds,
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        self._duration_timer.stop()
        self._indicator._pulse_timer.stop()
        logger.debug("RecordingStatusWidget cleaned up")


__all__ = ["RecordingStatusWidget", "RecordingIndicator"]

