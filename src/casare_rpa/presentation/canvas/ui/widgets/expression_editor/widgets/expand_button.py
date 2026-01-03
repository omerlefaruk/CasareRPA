"""
Expand Button Widget for CasareRPA Expression Editor.

Small button to trigger the expression editor popup for a property widget.
Positioned next to the variable button in text inputs.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QPushButton, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME


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
        c = THEME
        self.setStyleSheet(f"""
            QPushButton {{
                background: {c.bg_component};
                border: 1px solid {c.border};
                border-radius: 3px;
                color: {c.text_secondary};
                font-size: 9px;
                font-weight: bold;
                font-family: Consolas, monospace;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {c.primary};
                border-color: {c.primary};
                color: {c.text_on_primary};
            }}
            QPushButton:pressed {{
                background: {c.primary_hover};
                border-color: {c.primary_hover};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.clicked.connect(self._on_clicked)

    @Slot()
    def _on_clicked(self) -> None:
        """Handle click event."""
        self.clicked_expand.emit()

