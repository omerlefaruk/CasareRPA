"""
CasareRPA - Snippet Breadcrumb Navigation Bar
Visual navigation breadcrumb showing snippet hierarchy: Workflow > Snippet A > Snippet B
"""

from typing import List, Tuple
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from loguru import logger


class SnippetBreadcrumbBar(QWidget):
    """
    Breadcrumb navigation bar for hierarchical snippet navigation.

    Displays clickable path: 🏠 Workflow > 📦 Login > 📦 Form Fill

    Signals:
        level_clicked: Emitted when user clicks a breadcrumb level (level_index)
    """

    level_clicked = Signal(int)  # Emits level index when clicked

    def __init__(self, parent=None):
        """Initialize breadcrumb navigation bar."""
        super().__init__(parent)

        # Current path (initialize BEFORE _setup_ui)
        self._path: List[Tuple[str, str]] = [("Workflow", "workflow")]

        # Setup UI
        self._setup_ui()

        logger.debug("SnippetBreadcrumbBar initialized")

    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(4)

        # VSCode Dark+ styling
        self.setStyleSheet("""
            SnippetBreadcrumbBar {
                background: #252526;
                border-bottom: 1px solid #3E3E42;
            }
            QPushButton {
                background: transparent;
                color: #CCCCCC;
                border: none;
                padding: 4px 8px;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #2A2D2E;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #37373D;
            }
            QLabel {
                color: #858585;
                font-size: 13px;
            }
        """)

        # Set fixed height
        self.setFixedHeight(32)

        # Initial path (just workflow)
        self._rebuild_breadcrumb()

    def set_path(self, path: List[Tuple[str, str]]) -> None:
        """
        Update the breadcrumb path.

        Args:
            path: List of (name, context_type) tuples
                  Example: [("Workflow", "workflow"), ("Login", "snippet")]
        """
        if path == self._path:
            return  # No change

        self._path = path
        self._rebuild_breadcrumb()

        logger.debug(f"Breadcrumb path updated: {' > '.join([p[0] for p in path])}")

    def _rebuild_breadcrumb(self) -> None:
        """Rebuild the breadcrumb UI from current path."""
        # Clear existing widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add breadcrumb items
        for index, (name, context_type) in enumerate(self._path):
            # Add separator (except for first item)
            if index > 0:
                separator = QLabel(">")
                separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.layout.addWidget(separator)

            # Add breadcrumb button
            button = QPushButton()

            # Set icon and text based on context type
            if context_type == "workflow":
                button.setText(f"🏠 {name}")
            else:  # snippet
                button.setText(f"📦 {name}")

            # Set font
            font = QFont()
            font.setFamily("Segoe UI")
            button.setFont(font)

            # Make clickable (except for last item - that's where we are)
            is_current_level = (index == len(self._path) - 1)

            if is_current_level:
                # Current level - not clickable, slightly different style
                button.setEnabled(False)
                button.setStyleSheet("""
                    QPushButton:disabled {
                        background: #37373D;
                        color: #FFFFFF;
                        border: none;
                        padding: 4px 8px;
                        font-size: 13px;
                    }
                """)
            else:
                # Clickable level
                button.setCursor(Qt.CursorShape.PointingHandCursor)

                # Connect click handler (use lambda with default argument to capture index)
                button.clicked.connect(lambda checked=False, idx=index: self._on_level_clicked(idx))

            self.layout.addWidget(button)

        # Add spacer to push everything to the left
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addSpacerItem(spacer)

    def _on_level_clicked(self, level_index: int) -> None:
        """
        Handle breadcrumb level click.

        Args:
            level_index: Index of clicked level
        """
        logger.info(f"Breadcrumb level {level_index} clicked: '{self._path[level_index][0]}'")
        self.level_clicked.emit(level_index)

    def get_current_depth(self) -> int:
        """Get current navigation depth (0 = root)."""
        return len(self._path) - 1

    def get_current_level_name(self) -> str:
        """Get name of current level."""
        if self._path:
            return self._path[-1][0]
        return "Unknown"
