"""
Editor Toolbar for CasareRPA Expression Editors.

Provides a horizontal button row for formatting actions in Markdown
and Rich Text editors. THEME-styled with hover effects.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME


class EditorToolbar(QWidget):
    """
    Horizontal toolbar with formatting buttons for expression editors.

    Features:
    - Add actions with icons and tooltips
    - THEME-styled buttons (20x20px, hover effect)
    - Separator support
    - Used by MarkdownEditor and RichTextEditor

    Usage:
        toolbar = EditorToolbar()
        toolbar.add_action("B", "Bold (Ctrl+B)", self.toggle_bold)
        toolbar.add_action("I", "Italic (Ctrl+I)", self.toggle_italic)
        toolbar.add_separator()
        toolbar.add_action("#", "Heading", self.insert_heading)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the toolbar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the toolbar UI."""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)
        self._layout.addStretch()  # Push buttons to left

    def _apply_styles(self) -> None:
        """Apply THEME styling to the toolbar."""
        c = THEME
        self.setStyleSheet(f"""
            EditorToolbar {{
                background: {c.bg_header};
                border-bottom: 1px solid {c.border_dark};
            }}
        """)

    def add_action(
        self,
        icon: str,
        tooltip: str,
        callback: Callable[[], None],
    ) -> QPushButton:
        """
        Add an action button to the toolbar.

        Args:
            icon: Button text/icon (e.g., "B" for bold, "#" for heading)
            tooltip: Tooltip text (e.g., "Bold (Ctrl+B)")
            callback: Function to call when button is clicked

        Returns:
            The created QPushButton
        """
        c = THEME

        button = QPushButton(icon)
        button.setToolTip(tooltip)
        button.setFixedSize(24, 24)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: {c.text_secondary};
                font-family: "Segoe UI", "SF Pro Text", sans-serif;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {c.bg_hover};
                border-color: {c.border};
                color: {c.text_primary};
            }}
            QPushButton:pressed {{
                background: {c.bg_selected};
                color: {c.text_primary};
            }}
        """)

        button.clicked.connect(callback)

        # Insert before the stretch
        insert_pos = self._layout.count() - 1
        self._layout.insertWidget(insert_pos, button)

        return button

    def add_separator(self) -> None:
        """Add a vertical separator line to the toolbar."""
        c = THEME

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(16)
        separator.setStyleSheet(f"background: {c.border};")

        # Insert before the stretch
        insert_pos = self._layout.count() - 1
        self._layout.insertWidget(insert_pos, separator)

    def add_stretch(self) -> None:
        """Add a stretch to push subsequent buttons to the right."""
        # Insert a stretch before the final stretch
        insert_pos = self._layout.count() - 1
        self._layout.insertStretch(insert_pos)

    def clear(self) -> None:
        """Remove all buttons and separators from the toolbar."""
        while self._layout.count() > 1:  # Keep the final stretch
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
