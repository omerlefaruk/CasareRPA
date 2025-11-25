"""
Validation Panel for CasareRPA.

Provides a dockable panel showing workflow validation issues in real-time.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QIcon

from ..core.validation import ValidationResult, ValidationIssue, ValidationSeverity
from loguru import logger


class ValidationPanel(QWidget):
    """
    Dockable widget displaying workflow validation issues.

    Shows:
    - Errors (blocking issues)
    - Warnings (potential problems)
    - Real-time validation status

    Signals:
        issue_clicked: Emitted when user clicks an issue (location: str)
        validation_requested: Emitted when user requests manual validation
    """

    issue_clicked = Signal(str)  # location string (e.g., "node:abc123")
    validation_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize validation panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._last_result: Optional[ValidationResult] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header with status and actions
        header = QHBoxLayout()

        # Status label
        self._status_label = QLabel("No validation run")
        self._status_label.setStyleSheet("color: #888888; font-weight: bold;")

        # Validate button
        validate_btn = QPushButton("Validate")
        validate_btn.setFixedWidth(80)
        validate_btn.clicked.connect(self._on_validate_clicked)
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b6eaf;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #5a7fc0;
            }
        """)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                color: #bbbbbb;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4c4f51;
            }
        """)

        header.addWidget(self._status_label)
        header.addStretch()
        header.addWidget(validate_btn)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Issues tree
        self._issues_tree = QTreeWidget()
        self._issues_tree.setHeaderLabels(["Issue", "Location"])
        self._issues_tree.setRootIsDecorated(False)
        self._issues_tree.setAlternatingRowColors(True)
        self._issues_tree.itemClicked.connect(self._on_item_clicked)
        self._issues_tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Configure columns
        header_view = self._issues_tree.header()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        # Style the tree
        self._issues_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 9pt;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #4b6eaf;
            }
            QTreeWidget::item:hover {
                background-color: #3c3f41;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #bbbbbb;
                padding: 4px;
                border: none;
                border-bottom: 1px solid #1e1e1e;
            }
        """)

        layout.addWidget(self._issues_tree)

        # Summary bar at bottom
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("""
            QLabel {
                background-color: #3c3f41;
                color: #888888;
                padding: 4px 8px;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self._summary_label)

    def set_result(self, result: ValidationResult) -> None:
        """
        Update the panel with validation results.

        Args:
            result: ValidationResult to display
        """
        self._last_result = result
        self._issues_tree.clear()

        # Add issues to tree
        for issue in result.issues:
            self._add_issue_item(issue)

        # Update status
        self._update_status(result)

    def _add_issue_item(self, issue: ValidationIssue) -> None:
        """Add a single issue to the tree."""
        item = QTreeWidgetItem()

        # Set icon/prefix based on severity
        severity_prefix = {
            ValidationSeverity.ERROR: "[E]",
            ValidationSeverity.WARNING: "[W]",
            ValidationSeverity.INFO: "[I]",
        }
        prefix = severity_prefix.get(issue.severity, "[?]")

        # Format message
        message = f"{prefix} {issue.code}: {issue.message}"
        if issue.suggestion:
            message += f"\n    Hint: {issue.suggestion}"

        item.setText(0, message)
        item.setText(1, issue.location or "")

        # Store issue data
        item.setData(0, Qt.ItemDataRole.UserRole, {
            "location": issue.location,
            "code": issue.code,
            "severity": issue.severity.name,
        })

        # Set color based on severity
        colors = {
            ValidationSeverity.ERROR: QColor("#ff6b6b"),
            ValidationSeverity.WARNING: QColor("#ffa500"),
            ValidationSeverity.INFO: QColor("#6bb5ff"),
        }
        color = colors.get(issue.severity, QColor("#d4d4d4"))
        item.setForeground(0, QBrush(color))

        self._issues_tree.addTopLevelItem(item)

    def _update_status(self, result: ValidationResult) -> None:
        """Update status label and summary."""
        if result.is_valid:
            if result.warning_count > 0:
                self._status_label.setText(f"Valid with {result.warning_count} warning(s)")
                self._status_label.setStyleSheet("color: #ffa500; font-weight: bold;")
            else:
                self._status_label.setText("Valid")
                self._status_label.setStyleSheet("color: #6bff6b; font-weight: bold;")
        else:
            self._status_label.setText(f"Invalid: {result.error_count} error(s)")
            self._status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")

        # Summary
        parts = []
        if result.error_count > 0:
            parts.append(f"{result.error_count} error(s)")
        if result.warning_count > 0:
            parts.append(f"{result.warning_count} warning(s)")

        if parts:
            self._summary_label.setText(" | ".join(parts))
        else:
            self._summary_label.setText("No issues found")

    def clear(self) -> None:
        """Clear all issues."""
        self._issues_tree.clear()
        self._last_result = None
        self._status_label.setText("No validation run")
        self._status_label.setStyleSheet("color: #888888; font-weight: bold;")
        self._summary_label.setText("")

    def get_result(self) -> Optional[ValidationResult]:
        """Get the last validation result."""
        return self._last_result

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return self._last_result is not None and not self._last_result.is_valid

    def _on_validate_clicked(self) -> None:
        """Handle validate button click."""
        self.validation_requested.emit()

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("location"):
            self.issue_clicked.emit(data["location"])

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click (navigate to issue)."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("location"):
            self.issue_clicked.emit(data["location"])


class ValidationStatusWidget(QWidget):
    """
    Small status widget for toolbar showing validation status.
    """

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)

        self._icon_label = QLabel()
        self._text_label = QLabel("Not validated")
        self._text_label.setStyleSheet("color: #888888; font-size: 9pt;")

        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._status = "unknown"

    def set_status(self, status: str, message: str = "") -> None:
        """
        Set validation status.

        Args:
            status: "valid", "warning", "error", or "unknown"
            message: Optional message to display
        """
        self._status = status

        colors = {
            "valid": "#6bff6b",
            "warning": "#ffa500",
            "error": "#ff6b6b",
            "unknown": "#888888",
        }

        icons = {
            "valid": "OK",
            "warning": "!",
            "error": "X",
            "unknown": "?",
        }

        color = colors.get(status, "#888888")
        icon = icons.get(status, "?")

        self._icon_label.setText(icon)
        self._icon_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._text_label.setText(message or status.capitalize())
        self._text_label.setStyleSheet(f"color: {color}; font-size: 9pt;")

    def mousePressEvent(self, event) -> None:
        """Handle mouse press to emit clicked signal."""
        self.clicked.emit()
        super().mousePressEvent(event)
