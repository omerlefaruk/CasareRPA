"""Toast notification widget.

Non-blocking, transient feedback messages for Canvas UI.
Designed to replace blocking QMessageBox usage for routine feedback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import THEME


@dataclass(frozen=True)
class ToastStyle:
    border_color: str


_TOAST_STYLES = {
    "info": ToastStyle(border_color=THEME.status_info),
    "success": ToastStyle(border_color=THEME.status_success),
    "warning": ToastStyle(border_color=THEME.status_warning),
    "error": ToastStyle(border_color=THEME.status_error),
}


class ToastNotification(QWidget):
    """A small, non-modal toast message anchored to a parent widget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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
        layout.setContentsMargins(12, 10, 12, 10)
        layout.addWidget(self._label)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._frame)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        self._animation: Optional[QPropertyAnimation] = None

        self._apply_style(level="info")
        self.hide()

    def show_toast(self, message: str, level: str = "info", duration_ms: int = 2500) -> None:
        """Show a toast message.

        Args:
            message: Toast text.
            level: info|success|warning|error.
            duration_ms: How long the toast stays visible before fading out.
        """
        try:
            self._apply_style(level=level)
            self._label.setText(message)
            self.adjustSize()
            self._reposition()

            self._fade_in()
            self._hide_timer.start(max(500, duration_ms))
        except Exception as exc:
            logger.warning(f"ToastNotification failed to show: {exc}")

    def _apply_style(self, level: str) -> None:
        style = _TOAST_STYLES.get(level, _TOAST_STYLES["info"])
        self._frame.setStyleSheet(
            f"""
            QFrame#toast {{
                background: {THEME.bg_panel};
                border: 1px solid {THEME.border};
                border-left: 4px solid {style.border_color};
                border-radius: 6px;
            }}
            QLabel {{
                color: {THEME.text_primary};
                font-size: 12px;
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

    def _fade_in(self) -> None:
        self._hide_timer.stop()
        self.setWindowOpacity(0.0)
        self.show()

        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(150)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.start()

    def _fade_out(self) -> None:
        if not self.isVisible():
            return

        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(150)
        self._animation.setStartValue(self.windowOpacity())
        self._animation.setEndValue(0.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._animation.finished.connect(self.hide)
        self._animation.start()
