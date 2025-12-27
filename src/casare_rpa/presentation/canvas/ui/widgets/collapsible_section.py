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

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme_system import (

)
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import set_fixed_size, set_min_size, set_max_size, set_margins, set_spacing, set_min_width, set_max_width, set_fixed_width, set_fixed_height


class CollapsibleSection(QWidget):
    """Expandable/collapsible content section."""

    toggled = Signal(bool)  # Emitted when expanded/collapsed

    def __init__(
        self,
        title: str = "",
        expanded: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._expanded = expanded
        self._content_widget: QWidget | None = None
        self._animation: QPropertyAnimation | None = None
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
        set_margins(layout, (0, 0, 0, 0))
        set_spacing(layout, 0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(32)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = lambda e: self.toggle()

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(TOKENS.spacing.xs, 0, TOKENS.spacing.xs, 0)

        # Arrow indicator
        self._arrow_label = QLabel(
            "\u25bc" if self._expanded else "\u25b6"
        )  # Down or right triangle
        self.set_fixed_width(_arrow_label, 16)

        # Title
        self._title_label = QLabel(title)
        font = self._title_label.font()
        font.setWeight(QFont.Weight.Medium)
        font.setFamily(TOKENS.typography.family)  # Inter font
        font.setPointSize(TOKENS.typography.body_sm)  # 11px
        self._title_label.setFont(font)

        header_layout.addWidget(self._arrow_label)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        # Content frame
        self._content_frame = QFrame()
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(TOKENS.spacing.xs, TOKENS.spacing.xs, TOKENS.spacing.xs, TOKENS.spacing.xs)

        layout.addWidget(self._header)
        layout.addWidget(self._content_frame)

    def _apply_style(self) -> None:
        """Apply theme styling with ElevenLabs design tokens."""
        colors = THEME
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;  /* 4px - ElevenLabs radius-sm */
            }}
            QFrame:hover {{
                background-color: {colors.surface_hover};
            }}
        """)
        self._content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_elevated};
                border: 1px solid {colors.border};
                border-top: none;
                border-radius: 0 0 {TOKENS.radius.sm}px {TOKENS.radius.sm}px;
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

        if animate:
            self._animate_toggle()
        else:
            self._instant_toggle()

        self.toggled.emit(expanded)

    def toggle(self) -> None:
        """Toggle expanded/collapsed state."""
        self.setExpanded(not self._expanded)

    def _animate_toggle(self) -> None:
        """Animate expand/collapse."""
        if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
            self._animation.stop()

        # Update arrow
        self._arrow_label.setText("\u25bc" if self._expanded else "\u25b6")

        # Animate height
        self._animation = QPropertyAnimation(self._content_frame, b"maximumHeight")
        self._animation.setDuration(TOKENS.transitions.medium)  # 200ms

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
        self._content_frame.setMaximumHeight(self._content_height if self._expanded else 0)
