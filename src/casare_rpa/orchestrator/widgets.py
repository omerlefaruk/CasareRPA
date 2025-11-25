"""
Reusable widgets for CasareRPA Orchestrator.
"""
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QProgressBar,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor

from .styles import COLORS, get_status_badge_style


class KPICard(QFrame):
    """Card widget for displaying KPI metrics."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        icon: str = "",
        trend: Optional[float] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Apply shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Header with icon and title
        header = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 20px; color: {COLORS['accent_secondary']};")
            header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("card_title")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
        """)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Value
        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 32px;
            font-weight: 700;
        """)
        layout.addWidget(self._value_label)

        # Subtitle and trend
        footer = QHBoxLayout()
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
            footer.addWidget(subtitle_label)

        if trend is not None:
            trend_text = f"↑ {trend:.1f}%" if trend >= 0 else f"↓ {abs(trend):.1f}%"
            trend_color = COLORS['accent_success'] if trend >= 0 else COLORS['accent_error']
            trend_label = QLabel(trend_text)
            trend_label.setStyleSheet(f"color: {trend_color}; font-size: 12px; font-weight: 600;")
            footer.addWidget(trend_label)

        footer.addStretch()
        layout.addLayout(footer)

        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame#card:hover {{
                border-color: {COLORS['accent_secondary']};
            }}
        """)

    def set_value(self, value: str):
        """Update the displayed value."""
        self._value_label.setText(value)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class StatusBadge(QLabel):
    """Badge widget for displaying status."""

    def __init__(self, status: str, parent: Optional[QWidget] = None):
        super().__init__(status.upper(), parent)
        self.set_status(status)

    def set_status(self, status: str):
        """Update the status and styling."""
        self.setText(status.upper())
        self.setStyleSheet(get_status_badge_style(status))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(80)


class SearchBar(QWidget):
    """Search bar with filter options."""

    search_changed = Signal(str)
    filter_changed = Signal(str)

    def __init__(
        self,
        placeholder: str = "Search...",
        filters: Optional[list] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(f"🔍 {placeholder}")
        self._search_input.textChanged.connect(self.search_changed.emit)
        self._search_input.setMinimumWidth(250)
        layout.addWidget(self._search_input)

        # Filter dropdown
        if filters:
            self._filter_combo = QComboBox()
            self._filter_combo.addItems(filters)
            self._filter_combo.currentTextChanged.connect(self.filter_changed.emit)
            self._filter_combo.setMinimumWidth(150)
            layout.addWidget(self._filter_combo)

        layout.addStretch()

    def get_search_text(self) -> str:
        return self._search_input.text()

    def get_filter(self) -> str:
        if hasattr(self, '_filter_combo'):
            return self._filter_combo.currentText()
        return ""

    def clear(self):
        self._search_input.clear()


class ActionButton(QPushButton):
    """Styled action button with icon support."""

    def __init__(
        self,
        text: str,
        icon: str = "",
        primary: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(f"{icon} {text}".strip() if icon else text, parent)

        if not primary:
            self.setProperty("secondary", True)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_light']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    border-color: {COLORS['accent_secondary']};
                }}
            """)


class ProgressIndicator(QWidget):
    """Progress indicator with label."""

    def __init__(
        self,
        value: int = 0,
        text: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(value)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        layout.addWidget(self._progress, stretch=1)

        self._label = QLabel(text or f"{value}%")
        self._label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self._label.setMinimumWidth(40)
        layout.addWidget(self._label)

    def set_value(self, value: int, text: str = ""):
        self._progress.setValue(value)
        self._label.setText(text or f"{value}%")


class SectionHeader(QWidget):
    """Section header with title and optional action button."""

    action_clicked = Signal()

    def __init__(
        self,
        title: str,
        action_text: str = "",
        action_icon: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: 600;
        """)
        layout.addWidget(title_label)
        layout.addStretch()

        if action_text:
            action_btn = ActionButton(action_text, action_icon, primary=False)
            action_btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(action_btn)


class EmptyState(QWidget):
    """Empty state placeholder widget."""

    action_clicked = Signal()

    def __init__(
        self,
        icon: str = "📭",
        title: str = "No data",
        description: str = "",
        action_text: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: 600;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        if action_text:
            action_btn = ActionButton(action_text, "➕")
            action_btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class LoadingSpinner(QWidget):
    """Loading spinner widget."""

    def __init__(self, text: str = "Loading...", parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # Simple text-based loading indicator
        spinner = QLabel("⏳")
        spinner.setStyleSheet("font-size: 32px;")
        spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(spinner)

        label = QLabel(text)
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class InfoRow(QWidget):
    """Information row with label and value."""

    def __init__(
        self,
        label: str,
        value: str,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(16)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
        label_widget.setMinimumWidth(120)
        layout.addWidget(label_widget)

        self._value_widget = QLabel(value)
        self._value_widget.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        layout.addWidget(self._value_widget, stretch=1)

    def set_value(self, value: str):
        self._value_widget.setText(value)
