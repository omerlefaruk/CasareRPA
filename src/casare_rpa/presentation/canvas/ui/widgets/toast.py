"""Toast notification widget.

Non-blocking, transient feedback messages for Canvas UI.
Designed to replace blocking QMessageBox usage for routine feedback.

ZERO-MOTION POLICY (Epic 8.1):
- No fade animations - instant show/hide only
- All timers and callbacks remain functional
- Reduced motion for accessibility and performance
"""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from casare_rpa.presentation.canvas.theme import (
    THEME,
    TOKENS,
)


@dataclass(frozen=True)
class ToastStyle:
    border_color: str


_TOAST_STYLES = {
    "info": ToastStyle(border_color=THEME.info),
    "success": ToastStyle(border_color=THEME.success),
    "warning": ToastStyle(border_color=THEME.warning),
    "error": ToastStyle(border_color=THEME.error),
}


class ToastNotification(QWidget):
    """A small, non-modal toast message anchored to a parent widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._frame = QFrame(self)
        self._frame.setObjectName("toast")
        self._label = QLabel("")
        self._label.setWordWrap(True)

        layout = QHBoxLayout(self._frame)
        layout.setContentsMargins(
            TOKENS.spacing.lg, TOKENS.spacing.sm, TOKENS.spacing.lg, TOKENS.spacing.sm
        )
        layout.addWidget(self._label)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._frame)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timeout)

        # ZERO-MOTION: No animation object needed
        self._apply_style(level="info")
        self.hide()

    def show_toast(self, message: str, level: str = "info", duration_ms: int = 2500) -> None:
        """Show a toast message.

        Args:
            message: Toast text.
            level: info|success|warning|error.
            duration_ms: How long the toast stays visible before hiding.
        """
        try:
            self._apply_style(level=level)
            self._label.setText(message)
            self.adjustSize()
            self._reposition()

            # ZERO-MOTION: Instant show (no fade)
            self.setWindowOpacity(1.0)
            self.show()
            self._hide_timer.start(max(500, duration_ms))
        except Exception as exc:
            logger.warning(f"ToastNotification failed to show: {exc}")

    def _apply_style(self, level: str) -> None:
        style = _TOAST_STYLES.get(level, _TOAST_STYLES["info"])
        self._frame.setStyleSheet(
            f"""
            QFrame#toast {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-left: 4px solid {style.border_color};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
            }}
            QLabel {{
                color: {THEME.text_primary};
                font-family: {TOKENS.typography.family};  /* Inter font stack */
                font-size: {TOKENS.typography.body}px;  /* 12px */
            }}
            """
        )

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return

        margin = 16
        parent_rect = parent.rect()
        global_pos = parent.mapToGlobal(
            QPoint(
                max(0, parent_rect.width() - self.width() - margin),
                max(0, parent_rect.height() - self.height() - margin),
            )
        )
        self.move(global_pos)

    def _on_hide_timeout(self) -> None:
        """Handle hide timer expiry - ZERO-MOTION: instant hide."""
        if self.isVisible():
            self.hide()

