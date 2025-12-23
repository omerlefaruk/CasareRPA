"""
Expand Button Widget for CasareRPA Expression Editor.

Small button to trigger the expression editor popup for a property widget.
Positioned next to the variable button in text inputs.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QPushButton, QWidget

from casare_rpa.presentation.canvas.ui.theme import Theme


class ExpandButton(QPushButton):
    """
    Small button to expand property widget into full expression editor.

    Appearance: [...] icon button
    Position: Right side of property widget (next to variable button)
    Size: 20x20px

    Signals:
        clicked_expand: Emitted when expand is requested
    """

    clicked_expand = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the expand button.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the button UI."""
        self.setText("...")
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Open expression editor (Ctrl+E)")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def _apply_styles(self) -> None:
        """Apply themed styling to the button."""
        c = Theme.get_colors()
        self.setStyleSheet(f"""
            QPushButton {{
                background: {c.surface};
                border: 1px solid {c.border};
                border-radius: 3px;
                color: {c.text_secondary};
                font-size: 9px;
                font-weight: bold;
                font-family: Consolas, monospace;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {c.accent};
                border-color: {c.accent};
                color: {c.text_primary};
            }}
            QPushButton:pressed {{
                background: {c.accent_hover};
                border-color: {c.accent_hover};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.clicked.connect(self._on_clicked)

    @Slot()
    def _on_clicked(self) -> None:
        """Handle click event."""
        self.clicked_expand.emit()
