"""
Collapsible section widget with animated expand/collapse.

Used in dialogs and panels for grouping related content.

Usage:
    section = CollapsibleSection("Advanced Options")
    section.setContentWidget(my_content_widget)
    section.toggled.connect(lambda expanded: print(f"Expanded: {expanded}"))

    # Start collapsed
    section.setExpanded(False)
"""

from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class CollapsibleSection(QWidget):
    """Expandable/collapsible content section."""

    toggled = Signal(bool)  # Emitted when expanded/collapsed

    def __init__(
        self,
        title: str = "",
        expanded: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._expanded = expanded
        self._content_widget: Optional[QWidget] = None
        self._animation: Optional[QPropertyAnimation] = None
        self._content_height = 0

        self._setup_ui(title)
        self._apply_style()

        # Set initial state
        if not expanded:
            self._content_frame.setMaximumHeight(0)
            self._arrow_label.setText("\u25b6")  # Right-pointing triangle

    def _setup_ui(self, title: str) -> None:
        """Create the section UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(32)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = lambda e: self.toggle()

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(8, 0, 8, 0)

        # Arrow indicator
        self._arrow_label = QLabel(
            "\u25bc" if self._expanded else "\u25b6"
        )  # Down or right triangle
        self._arrow_label.setFixedWidth(16)

        # Title
        self._title_label = QLabel(title)
        font = self._title_label.font()
        font.setWeight(QFont.Weight.Medium)
        self._title_label.setFont(font)

        header_layout.addWidget(self._arrow_label)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        # Content frame
        self._content_frame = QFrame()
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(self._header)
        layout.addWidget(self._content_frame)

    def _apply_style(self) -> None:
        """Apply theme styling."""
        colors = Theme.get_colors()
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: 4px;
            }}
            QFrame:hover {{
                background-color: {colors.surface_hover};
            }}
        """)
        self._content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.background_alt};
                border: 1px solid {colors.border};
                border-top: none;
                border-radius: 0 0 4px 4px;
            }}
        """)

    def setContentWidget(self, widget: QWidget) -> None:
        """Set the widget to show in the content area."""
        # Remove old content
        if self._content_widget:
            self._content_layout.removeWidget(self._content_widget)

        self._content_widget = widget
        self._content_layout.addWidget(widget)

        # Store content height for animation
        self._content_height = widget.sizeHint().height() + 16  # padding

    def setTitle(self, title: str) -> None:
        """Set section title."""
        self._title_label.setText(title)

    def isExpanded(self) -> bool:
        """Check if section is expanded."""
        return self._expanded

    def setExpanded(self, expanded: bool, animate: bool = True) -> None:
        """Set expanded state."""
        if expanded == self._expanded:
            return

        self._expanded = expanded

        if animate and not AccessibilitySettings.prefers_reduced_motion():
            self._animate_toggle()
        else:
            self._instant_toggle()

        self.toggled.emit(expanded)

    def toggle(self) -> None:
        """Toggle expanded/collapsed state."""
        self.setExpanded(not self._expanded)

    def _animate_toggle(self) -> None:
        """Animate expand/collapse."""
        if (
            self._animation
            and self._animation.state() == QPropertyAnimation.State.Running
        ):
            self._animation.stop()

        # Update arrow
        self._arrow_label.setText("\u25bc" if self._expanded else "\u25b6")

        # Animate height
        self._animation = QPropertyAnimation(self._content_frame, b"maximumHeight")
        self._animation.setDuration(ANIMATIONS.medium)  # 200ms

        if self._expanded:
            self._animation.setStartValue(0)
            self._animation.setEndValue(self._content_height)
            self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        else:
            self._animation.setStartValue(self._content_frame.height())
            self._animation.setEndValue(0)
            self._animation.setEasingCurve(QEasingCurve.Type.InCubic)

        self._animation.start()

    def _instant_toggle(self) -> None:
        """Instant toggle without animation."""
        self._arrow_label.setText("\u25bc" if self._expanded else "\u25b6")
        self._content_frame.setMaximumHeight(
            self._content_height if self._expanded else 0
        )
