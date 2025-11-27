"""
Breadcrumb Navigation Bar for CasareRPA.

Shows the current workflow path and selected node for easy navigation context.
"""

from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from loguru import logger


class BreadcrumbBar(QWidget):
    """
    Breadcrumb navigation bar showing workflow path and context.

    Displays: Workflows > filename.json > [Selected Node]

    Signals:
        workflow_clicked: Emitted when workflow breadcrumb is clicked
        node_clicked: Emitted when node breadcrumb is clicked (node_id: str)
    """

    workflow_clicked = Signal()
    node_clicked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the breadcrumb bar.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._current_file: Optional[Path] = None
        self._selected_node_name: Optional[str] = None
        self._selected_node_id: Optional[str] = None

        self._setup_ui()
        self._apply_styles()
        self._update_display()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        # Home/Workflows button
        self._home_btn = QPushButton("Workflows")
        self._home_btn.setFlat(True)
        self._home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._home_btn.clicked.connect(self.workflow_clicked.emit)
        layout.addWidget(self._home_btn)

        # Separator 1
        self._sep1 = QLabel(" › ")
        self._sep1.setStyleSheet("color: #666666;")
        layout.addWidget(self._sep1)

        # Workflow name button
        self._workflow_btn = QPushButton("Untitled")
        self._workflow_btn.setFlat(True)
        self._workflow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._workflow_btn.clicked.connect(self.workflow_clicked.emit)
        layout.addWidget(self._workflow_btn)

        # Separator 2 (for node)
        self._sep2 = QLabel(" › ")
        self._sep2.setStyleSheet("color: #666666;")
        self._sep2.hide()
        layout.addWidget(self._sep2)

        # Selected node button
        self._node_btn = QPushButton("")
        self._node_btn.setFlat(True)
        self._node_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._node_btn.clicked.connect(self._on_node_clicked)
        self._node_btn.hide()
        layout.addWidget(self._node_btn)

        # Stretch to push content left
        layout.addStretch()

        # Modified indicator
        self._modified_label = QLabel("")
        self._modified_label.setStyleSheet("color: #FFA500; font-weight: bold;")
        layout.addWidget(self._modified_label)

        self.setFixedHeight(28)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QWidget {
                background: #2b2b2b;
                border-bottom: 1px solid #3d3d3d;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #a0a0a0;
                padding: 2px 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #ffffff;
                text-decoration: underline;
            }
        """)

    def _on_node_clicked(self) -> None:
        """Handle node breadcrumb click."""
        if self._selected_node_id:
            self.node_clicked.emit(self._selected_node_id)

    def _update_display(self) -> None:
        """Update the breadcrumb display."""
        # Update workflow name
        if self._current_file:
            self._workflow_btn.setText(self._current_file.name)
            self._workflow_btn.setToolTip(str(self._current_file))
        else:
            self._workflow_btn.setText("Untitled")
            self._workflow_btn.setToolTip("Unsaved workflow")

        # Update node display
        if self._selected_node_name:
            self._sep2.show()
            self._node_btn.show()
            self._node_btn.setText(self._selected_node_name)
            self._node_btn.setStyleSheet("""
                QPushButton {
                    background: #3d4a5a;
                    border-radius: 3px;
                    color: #88ccff;
                    padding: 2px 6px;
                }
                QPushButton:hover {
                    background: #4a5a6a;
                }
            """)
        else:
            self._sep2.hide()
            self._node_btn.hide()

    # ==================== Public API ====================

    def set_workflow_file(self, file_path: Optional[Path]) -> None:
        """
        Set the current workflow file.

        Args:
            file_path: Path to workflow file, or None for unsaved
        """
        self._current_file = file_path
        self._update_display()

    def set_selected_node(self, node_name: Optional[str], node_id: Optional[str] = None) -> None:
        """
        Set the currently selected node.

        Args:
            node_name: Node display name, or None to clear
            node_id: Node ID for navigation
        """
        self._selected_node_name = node_name
        self._selected_node_id = node_id
        self._update_display()

    def clear_selection(self) -> None:
        """Clear the selected node display."""
        self._selected_node_name = None
        self._selected_node_id = None
        self._update_display()

    def set_modified(self, modified: bool) -> None:
        """
        Set the modified indicator.

        Args:
            modified: Whether workflow has unsaved changes
        """
        if modified:
            self._modified_label.setText("● Modified")
        else:
            self._modified_label.setText("")
