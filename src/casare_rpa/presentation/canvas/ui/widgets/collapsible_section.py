"""
Collapsible section widget with instant expand/collapse.

Used in dialogs and panels for grouping related content.

ZERO-MOTION POLICY (Epic 8.1):
- No height animations - instant resize only
- All callbacks and signals remain functional
- Reduced motion for accessibility and performance

Usage:
    section = CollapsibleSection("Advanced Options")
    section.setContentWidget(my_content_widget)
    section.toggled.connect(lambda expanded: print(f"Expanded: {expanded}"))

    # Start collapsed
    section.setExpanded(False)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme_system import (
    THEME,
    TOKENS,
)
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_width,
    set_margins,
    set_spacing,
)


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
        # ZERO-MOTION: No animation object needed
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
        set_fixed_width(self._arrow_label, 16)

        # Title
        self._title_label = QLabel(title)
        font = self._title_label.font()
        font.setWeight(QFont.Weight.Medium)
        font.setFamily(TOKENS.typography.family)
        font.setPointSize(TOKENS.typography.body_sm)
        self._title_label.setFont(font)

        header_layout.addWidget(self._arrow_label)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        # Content frame
        self._content_frame = QFrame()
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(
            TOKENS.spacing.xs, TOKENS.spacing.xs, TOKENS.spacing.xs, TOKENS.spacing.xs
        )

        layout.addWidget(self._header)
        layout.addWidget(self._content_frame)

    def _apply_style(self) -> None:
        """Apply theme styling with ElevenLabs design tokens."""
        colors = THEME
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.bg_surface};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;  /* 4px - ElevenLabs radius-sm */
            }}
            QFrame:hover {{
                background-color: {colors.bg_hover};
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

        # Store content height for instant resize
        self._content_height = widget.sizeHint().height() + TOKENS.spacing.xs * 2

    def setTitle(self, title: str) -> None:
        """Set section title."""
        self._title_label.setText(title)

    def isExpanded(self) -> bool:
        """Check if section is expanded."""
        return self._expanded

    def setExpanded(self, expanded: bool, animate: bool = False) -> None:
        """Set expanded state.

        Args:
            expanded: True to expand, False to collapse.
            animate: Ignored (ZERO-MOTION policy - always instant).
        """
        if expanded == self._expanded:
            return

        self._expanded = expanded
        self._instant_toggle()
        self.toggled.emit(expanded)

    def toggle(self) -> None:
        """Toggle expanded/collapsed state."""
        self.setExpanded(not self._expanded)

    def _instant_toggle(self) -> None:
        """Instant toggle without animation (ZERO-MOTION)."""
        self._arrow_label.setText("\u25bc" if self._expanded else "\u25b6")
        self._content_frame.setMaximumHeight(self._content_height if self._expanded else 0)
