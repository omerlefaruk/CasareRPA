"""
Reusable UI components for Orchestrator.
Professional widgets - no icons, clean design.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter

from .theme import COLORS, get_status_color, get_job_status_color, get_priority_color


class ProgressBarDelegate(QWidget):
    """Custom progress bar for table cells."""

    def __init__(
        self,
        value: int = 0,
        status: str = "queued",
        show_text: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._value = value
        self._status = status
        self._show_text = show_text
        self.setMinimumHeight(18)
        self.setMaximumHeight(20)

    def set_value(self, value: int, status: str = ""):
        self._value = max(0, min(100, value))
        if status:
            self._status = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 2, -1, -2)

        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS["progress_bg"]))
        painter.drawRoundedRect(rect, 3, 3)

        # Progress fill
        if self._value > 0:
            fill_color = get_job_status_color(self._status)
            fill_width = int(rect.width() * self._value / 100)
            fill_rect = rect.adjusted(0, 0, -(rect.width() - fill_width), 0)
            painter.setBrush(QColor(fill_color))
            painter.drawRoundedRect(fill_rect, 3, 3)

        # Text
        if self._show_text:
            painter.setPen(QColor(COLORS["text_bright"]))
            font = painter.font()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            text = f"{self._value}%"
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()


class StatusIndicator(QWidget):
    """Colored status dot indicator."""

    def __init__(
        self, status: str = "offline", size: int = 10, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._status = status
        self._size = size
        self.setFixedSize(size + 4, size + 4)

    def set_status(self, status: str):
        self._status = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = get_status_color(self._status)

        # Outer glow effect
        painter.setPen(Qt.PenStyle.NoPen)
        glow_color = QColor(color)
        glow_color.setAlpha(50)
        painter.setBrush(glow_color)
        painter.drawEllipse(0, 0, self._size + 4, self._size + 4)

        # Main dot
        painter.setBrush(QColor(color))
        painter.drawEllipse(2, 2, self._size, self._size)

        painter.end()


class PriorityBadge(QLabel):
    """Priority indicator badge."""

    def __init__(self, priority: int = 50, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.set_priority(priority)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(32)

    def set_priority(self, priority: int):
        self._priority = priority
        color = get_priority_color(priority)

        self.setText(str(priority))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {COLORS['text_bright']};
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)


class StatusBadge(QLabel):
    """Status text badge with colored background."""

    def __init__(self, status: str = "Unknown", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_status(self, status: str):
        self._status = status
        color = get_job_status_color(status)

        # Darken color for background
        bg_color = QColor(color)
        bg_color.setAlpha(40)

        self.setText(status.upper())
        self.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.2);
                color: {color};
                border: 1px solid {color}40;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
        """)


class InfoCard(QFrame):
    """KPI card for dashboard."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        color: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        accent = color or COLORS["accent_blue"]

        self.setStyleSheet(f"""
            QFrame#infoCard {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border_medium']};
                border-left: 3px solid {accent};
                border-radius: 4px;
            }}
            QFrame#infoCard:hover {{
                background-color: {COLORS['bg_medium']};
                border-color: {COLORS['border_light']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(title_label)

        # Value
        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(f"""
            color: {COLORS['text_bright']};
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -1px;
        """)
        layout.addWidget(self._value_label)

        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            layout.addWidget(sub_label)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class PoolHeader(QFrame):
    """Expandable pool/group header for tree view."""

    toggled = Signal(bool)

    def __init__(
        self,
        name: str,
        count: int = 0,
        expanded: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._expanded = expanded
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: none;
                border-bottom: 1px solid {COLORS['border_dark']};
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_light']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Expand/collapse indicator (text-based)
        self._arrow = QLabel("v" if expanded else ">")
        self._arrow.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-family: monospace;"
        )
        self._arrow.setFixedWidth(12)
        layout.addWidget(self._arrow)

        # Pool name
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: 600;
            font-size: 12px;
        """)
        layout.addWidget(name_label)

        layout.addStretch()

        # Count badge
        self._count_label = QLabel(str(count))
        self._count_label.setStyleSheet(f"""
            background-color: {COLORS['bg_lighter']};
            color: {COLORS['text_secondary']};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 10px;
            font-weight: 600;
        """)
        layout.addWidget(self._count_label)

    def set_count(self, count: int):
        self._count_label.setText(str(count))

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._arrow.setText("v" if expanded else ">")

    def mousePressEvent(self, event):
        self._expanded = not self._expanded
        self.set_expanded(self._expanded)
        self.toggled.emit(self._expanded)
        super().mousePressEvent(event)


class QuickFilterBar(QFrame):
    """Quick filter toolbar with preset filters."""

    filter_changed = Signal(str)

    def __init__(self, filters: list, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_header']};
                border-bottom: 1px solid {COLORS['border_dark']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        self._buttons = {}
        self._active = None

        for name in filters:
            btn = QLabel(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setProperty("filter_name", name)
            self._buttons[name] = btn
            layout.addWidget(btn)

            # Click handler
            btn.mousePressEvent = lambda e, n=name: self._on_filter_click(n)

        layout.addStretch()
        self._update_styles()

    def _on_filter_click(self, name: str):
        self._active = name if self._active != name else None
        self._update_styles()
        self.filter_changed.emit(self._active or "")

    def _update_styles(self):
        for name, btn in self._buttons.items():
            if name == self._active:
                btn.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['accent_blue']};
                        color: {COLORS['text_bright']};
                        border-radius: 4px;
                        padding: 6px 14px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: {COLORS['text_secondary']};
                        border-radius: 4px;
                        padding: 6px 14px;
                        font-size: 11px;
                    }}
                    QLabel:hover {{
                        background-color: {COLORS['bg_light']};
                        color: {COLORS['text_primary']};
                    }}
                """)


class TimeDisplay(QLabel):
    """Elapsed/remaining time display."""

    def __init__(
        self, seconds: int = 0, prefix: str = "", parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._prefix = prefix
        self.set_seconds(seconds)
        self.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        """)

    def set_seconds(self, seconds: int):
        if seconds <= 0:
            text = "--:--:--"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            text = f"{hours:02d}:{minutes:02d}:{secs:02d}"

        self.setText(f"{self._prefix}{text}" if self._prefix else text)


class SectionTitle(QLabel):
    """Section title label for panels."""

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 8px 0;
        """)


class DataRow(QFrame):
    """Data row for displaying key-value information."""

    def __init__(self, label: str, value: str, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        label_widget.setMinimumWidth(100)
        layout.addWidget(label_widget)

        self._value_widget = QLabel(value)
        self._value_widget.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 12px;"
        )
        layout.addWidget(self._value_widget, stretch=1)

    def set_value(self, value: str):
        self._value_widget.setText(value)
