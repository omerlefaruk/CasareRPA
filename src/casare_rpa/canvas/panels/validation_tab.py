"""
Validation Tab for the Bottom Panel.

Provides workflow validation results display with navigation support.
"""

from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

if TYPE_CHECKING:
    from ...core.validation import ValidationResult


class ValidationTab(QWidget):
    """
    Validation tab widget for displaying workflow validation results.

    Features:
    - Tree view with errors/warnings grouped by type
    - Click to navigate to node
    - Auto-validate on change
    - Manual validate button

    Signals:
        validation_requested: Emitted when user requests manual validation
        issue_clicked: Emitted when user clicks an issue (location: str)
    """

    validation_requested = Signal()
    issue_clicked = Signal(str)  # location string

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Validation tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._last_result: Optional["ValidationResult"] = None

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        # Status label
        from ..theme import THEME

        self._status_label = QLabel("No validation run")
        self._status_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-weight: bold;"
        )

        # Validate button
        validate_btn = QPushButton("Validate")
        validate_btn.setFixedSize(50, 16)
        validate_btn.clicked.connect(self.validation_requested.emit)
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b6eaf;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 1px 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a7fc0;
            }
        """)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(40, 16)
        clear_btn.clicked.connect(self.clear)

        header.addWidget(self._status_label)
        header.addStretch()
        header.addWidget(validate_btn)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Issues tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Issue", "Location"])
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Configure columns
        header_view = self._tree.header()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._tree)

        # Summary bar
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet(f"""
            QLabel {{
                background-color: {THEME.bg_light};
                color: {THEME.text_muted};
                padding: 4px 8px;
                font-size: 9pt;
            }}
        """)
        layout.addWidget(self._summary_label)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        from ..theme import THEME

        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 9pt;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QTreeWidget::item:hover {{
                background-color: {THEME.bg_hover};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_header};
                color: {THEME.text_header};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
                border-radius: 2px;
                padding: 0px 2px;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
        """)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("location"):
            self.issue_clicked.emit(data["location"])

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("location"):
            self.issue_clicked.emit(data["location"])

    def _get_severity_color(self, severity: str) -> QColor:
        """Get color for severity level using VSCode Dark+ theme."""
        from ..theme import THEME

        colors = {
            "ERROR": QColor(THEME.status_error),
            "WARNING": QColor(THEME.status_warning),
            "INFO": QColor(THEME.status_info),
        }
        return colors.get(severity.upper(), QColor(THEME.text_primary))

    def _get_severity_prefix(self, severity: str) -> str:
        """Get prefix for severity level."""
        prefixes = {
            "ERROR": "[E]",
            "WARNING": "[W]",
            "INFO": "[I]",
        }
        return prefixes.get(severity.upper(), "[?]")

    # ==================== Public API ====================

    def set_result(self, result: "ValidationResult") -> None:
        """
        Update with validation results.

        Args:
            result: ValidationResult to display
        """
        self._last_result = result
        self._tree.clear()

        # Group issues by severity
        errors = []
        warnings = []
        infos = []

        for issue in result.issues:
            severity = (
                issue.severity.name
                if hasattr(issue.severity, "name")
                else str(issue.severity)
            )
            if severity.upper() == "ERROR":
                errors.append(issue)
            elif severity.upper() == "WARNING":
                warnings.append(issue)
            else:
                infos.append(issue)

        # Add grouped issues
        if errors:
            self._add_issue_group("Errors", errors, "ERROR")
        if warnings:
            self._add_issue_group("Warnings", warnings, "WARNING")
        if infos:
            self._add_issue_group("Info", infos, "INFO")

        # Expand all groups
        self._tree.expandAll()

        # Update status
        self._update_status(result)

    def _add_issue_group(self, title: str, issues: list, severity: str) -> None:
        """Add a group of issues to the tree."""
        color = self._get_severity_color(severity)

        # Create group item
        group = QTreeWidgetItem()
        group.setText(0, f"{title} ({len(issues)})")
        group.setForeground(0, QBrush(color))
        group.setExpanded(True)

        # Add issues
        for issue in issues:
            item = QTreeWidgetItem()

            # Format message
            sev_name = (
                issue.severity.name
                if hasattr(issue.severity, "name")
                else str(issue.severity)
            )
            prefix = self._get_severity_prefix(sev_name)
            message = f"{prefix} {issue.code}: {issue.message}"
            if issue.suggestion:
                message += f"\n    Hint: {issue.suggestion}"

            item.setText(0, message)
            item.setText(1, issue.location or "")
            item.setForeground(0, QBrush(color))

            # Store issue data
            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {
                    "location": issue.location,
                    "code": issue.code,
                    "severity": sev_name,
                },
            )

            group.addChild(item)

        self._tree.addTopLevelItem(group)

    def _update_status(self, result: "ValidationResult") -> None:
        """Update status label and summary."""
        from ..theme import THEME

        if result.is_valid:
            if result.warning_count > 0:
                self._status_label.setText(
                    f"Valid with {result.warning_count} warning(s)"
                )
                self._status_label.setStyleSheet(
                    f"color: {THEME.status_warning}; font-weight: bold;"
                )
            else:
                self._status_label.setText("Valid")
                self._status_label.setStyleSheet(
                    f"color: {THEME.status_success}; font-weight: bold;"
                )
        else:
            self._status_label.setText(f"Invalid: {result.error_count} error(s)")
            self._status_label.setStyleSheet(
                f"color: {THEME.status_error}; font-weight: bold;"
            )

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
        """Clear validation results."""
        self._tree.clear()
        self._last_result = None
        self._status_label.setText("No validation run")
        self._status_label.setStyleSheet("color: #888888; font-weight: bold;")
        self._summary_label.setText("")

    def get_result(self) -> Optional["ValidationResult"]:
        """Get the last validation result."""
        return self._last_result

    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return self._last_result is not None and not self._last_result.is_valid

    def get_issue_count(self) -> tuple:
        """
        Get the count of errors and warnings.

        Returns:
            Tuple of (error_count, warning_count)
        """
        if self._last_result is None:
            return (0, 0)
        return (self._last_result.error_count, self._last_result.warning_count)
