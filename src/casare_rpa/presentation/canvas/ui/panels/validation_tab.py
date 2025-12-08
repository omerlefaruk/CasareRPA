"""
Validation Tab for the Bottom Panel.

Provides workflow validation results display with improved UX:
- Empty state with guidance
- Color-coded severity indicators
- Click to navigate to node
- Auto-validate trigger
- Clear visual hierarchy with icons
"""

from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QHeaderView,
    QStackedWidget,
    QApplication,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    ToolbarButton,
    StatusBadge,
    get_panel_toolbar_stylesheet,
)

if TYPE_CHECKING:
    from casare_rpa.domain.validation import ValidationResult


class ValidationTab(QWidget):
    """
    Validation tab widget for displaying workflow validation results.

    Features:
    - Empty state when no validation run
    - Tree view with errors/warnings grouped by type
    - Click to navigate to node
    - Color-coded severity icons
    - Status badge showing validation state
    - Context menu for copy
    - Repair button to auto-fix repairable issues

    Signals:
        validation_requested: Emitted when user requests manual validation
        issue_clicked: Emitted when user clicks an issue (location: str)
        repair_requested: Emitted when user requests to repair workflow issues
    """

    validation_requested = Signal()
    issue_clicked = Signal(str)  # location string
    repair_requested = Signal()  # repair workflow issues

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("validationToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(8, 6, 8, 6)
        toolbar.setSpacing(12)

        # Status badge
        self._status_badge = StatusBadge("NOT RUN", "idle")

        # Status description
        self._status_label = QLabel("Click 'Validate' to check workflow")
        self._status_label.setProperty("muted", True)

        # Validate button (primary)
        validate_btn = ToolbarButton(
            text="Validate",
            tooltip="Validate workflow (Ctrl+Shift+V)",
            primary=True,
        )
        validate_btn.clicked.connect(self.validation_requested.emit)

        # Repair button (shown when repairable issues exist)
        self._repair_btn = ToolbarButton(
            text="Repair",
            tooltip="Auto-fix repairable issues (duplicate node IDs, etc.)",
        )
        self._repair_btn.clicked.connect(self.repair_requested.emit)
        self._repair_btn.setVisible(False)  # Hidden until repairable issues found
        # Style repair button with warning color
        self._repair_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.status_warning};
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #e6a700;
            }}
            QPushButton:pressed {{
                background-color: #cc9500;
            }}
        """)

        # Clear button
        clear_btn = ToolbarButton(
            text="Clear",
            tooltip="Clear validation results",
        )
        clear_btn.clicked.connect(self.clear)

        toolbar.addWidget(self._status_badge)
        toolbar.addWidget(self._status_label)
        toolbar.addStretch()
        toolbar.addWidget(self._repair_btn)
        toolbar.addWidget(validate_btn)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar_widget)

        # Content area with stacked widget
        self._content_stack = QStackedWidget()

        # Empty state (index 0)
        self._empty_state = EmptyStateWidget(
            icon_text="",  # Checkmark/shield icon
            title="No Validation Run",
            description=(
                "Workflow validation checks for:\n"
                "- Missing required connections\n"
                "- Invalid node configurations\n"
                "- Circular dependencies\n\n"
                "Click 'Validate' to check your workflow."
            ),
            action_text="Validate Now",
        )
        self._empty_state.action_clicked.connect(self.validation_requested.emit)
        self._content_stack.addWidget(self._empty_state)

        # Success state (index 1)
        self._success_state = EmptyStateWidget(
            icon_text="",  # Checkmark icon
            title="Workflow Valid",
            description="No issues found. Your workflow is ready to run.",
        )
        self._content_stack.addWidget(self._success_state)

        # Issues tree (index 2)
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(8, 4, 8, 8)
        tree_layout.setSpacing(4)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Issue", "Location"])
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)

        # Configure columns
        header_view = self._tree.header()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        tree_layout.addWidget(self._tree)

        # Summary bar
        self._summary_widget = QWidget()
        self._summary_widget.setObjectName("summaryBar")
        summary_layout = QHBoxLayout(self._summary_widget)
        summary_layout.setContentsMargins(8, 6, 8, 6)
        summary_layout.setSpacing(12)

        self._error_badge = StatusBadge("0 errors", "idle")
        self._warning_badge = StatusBadge("0 warnings", "idle")

        summary_layout.addWidget(self._error_badge)
        summary_layout.addWidget(self._warning_badge)
        summary_layout.addStretch()

        tree_layout.addWidget(self._summary_widget)

        self._content_stack.addWidget(tree_container)

        layout.addWidget(self._content_stack)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            ValidationTab, QWidget, QStackedWidget, QFrame {{
                background-color: {THEME.bg_panel};
            }}
            #validationToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            QTreeWidget {{
                background-color: {THEME.bg_panel};
                alternate-background-color: {THEME.bg_dark};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTreeWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QTreeWidget::item:hover {{
                background-color: {THEME.bg_hover};
            }}
            QTreeWidget::branch {{
                background-color: transparent;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_header};
                color: {THEME.text_header};
                padding: 8px 10px;
                border: none;
                border-right: 1px solid {THEME.border_dark};
                border-bottom: 1px solid {THEME.border_dark};
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            #summaryBar {{
                background-color: {THEME.bg_header};
                border-top: 1px solid {THEME.border_dark};
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

    def _on_context_menu(self, pos) -> None:
        """Show context menu for validation item."""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {THEME.accent_primary};
                color: #ffffff;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {THEME.border};
                margin: 4px 8px;
            }}
        """)

        # Copy message
        copy_msg = menu.addAction("Copy Message")
        copy_msg.triggered.connect(
            lambda: QApplication.clipboard().setText(item.text(0))
        )

        # Copy location
        if data.get("location"):
            copy_loc = menu.addAction("Copy Location")
            copy_loc.triggered.connect(
                lambda: QApplication.clipboard().setText(data["location"])
            )

            menu.addSeparator()

            # Navigate to location
            nav_action = menu.addAction("Go to Node")
            nav_action.triggered.connect(
                lambda: self.issue_clicked.emit(data["location"])
            )

        menu.exec_(self._tree.mapToGlobal(pos))

    def _get_severity_color(self, severity: str) -> QColor:
        """Get color for severity level using VSCode Dark+ theme."""
        colors = {
            "ERROR": QColor(THEME.status_error),
            "WARNING": QColor(THEME.status_warning),
            "INFO": QColor(THEME.status_info),
        }
        return colors.get(severity.upper(), QColor(THEME.text_primary))

    def _get_severity_icon(self, severity: str) -> str:
        """Get icon prefix for severity level."""
        icons = {
            "ERROR": "[X]",
            "WARNING": "[!]",
            "INFO": "[i]",
        }
        return icons.get(severity.upper(), "[?]")

    # ==================== Public API ====================

    def set_result(self, result: "ValidationResult") -> None:
        """
        Update with validation results.

        Args:
            result: ValidationResult to display
        """
        self._last_result = result
        self._tree.clear()

        # Check if valid with no issues
        if result.is_valid and result.warning_count == 0:
            self._status_badge.set_status("success", "VALID")
            self._status_label.setText("No issues found")
            self._status_label.setProperty("muted", False)
            self._content_stack.setCurrentIndex(1)  # Success state
            return

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

        # Show tree (index 2)
        self._content_stack.setCurrentIndex(2)

    def _add_issue_group(self, title: str, issues: list, severity: str) -> None:
        """Add a group of issues to the tree."""
        color = self._get_severity_color(severity)
        icon = self._get_severity_icon(severity)

        # Create group item
        group = QTreeWidgetItem()
        group.setText(0, f"{icon} {title} ({len(issues)})")
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
            message = f"{issue.code}: {issue.message}"
            if issue.suggestion:
                message += f"\n    Hint: {issue.suggestion}"

            item.setText(0, message)
            item.setText(1, issue.location or "")
            item.setForeground(0, QBrush(color))
            item.setToolTip(
                0, f"{issue.message}\n\nSuggestion: {issue.suggestion or 'None'}"
            )

            # Location column with accent color
            if issue.location:
                item.setForeground(1, QBrush(QColor(THEME.accent_primary)))
                item.setToolTip(1, f"Click to navigate to: {issue.location}")

            # Store issue data
            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {
                    "location": issue.location,
                    "code": issue.code,
                    "severity": sev_name,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                },
            )

            group.addChild(item)

        self._tree.addTopLevelItem(group)

    def _update_status(self, result: "ValidationResult") -> None:
        """Update status badge and summary."""
        if result.is_valid:
            if result.warning_count > 0:
                self._status_badge.set_status("warning", "WARNINGS")
                self._status_label.setText(
                    f"Valid with {result.warning_count} warning(s)"
                )
            else:
                self._status_badge.set_status("success", "VALID")
                self._status_label.setText("No issues found")
        else:
            self._status_badge.set_status("error", "ERRORS")
            self._status_label.setText(f"{result.error_count} error(s) found")

        self._status_label.setProperty("muted", False)

        # Update summary badges
        if result.error_count > 0:
            self._error_badge.set_status(
                "error",
                f"{result.error_count} error{'s' if result.error_count != 1 else ''}",
            )
        else:
            self._error_badge.set_status("idle", "0 errors")

        if result.warning_count > 0:
            self._warning_badge.set_status(
                "warning",
                f"{result.warning_count} warning{'s' if result.warning_count != 1 else ''}",
            )
        else:
            self._warning_badge.set_status("idle", "0 warnings")

        # Show/hide repair button based on repairable issues
        has_repairable = self._has_repairable_issues(result)
        self._repair_btn.setVisible(has_repairable)

        # Refresh styles
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _has_repairable_issues(self, result: "ValidationResult") -> bool:
        """
        Check if there are any auto-repairable issues in the validation result.

        Repairable issues include:
        - DUPLICATE_NODE_ID: Can regenerate unique IDs

        Args:
            result: ValidationResult to check

        Returns:
            True if there are repairable issues
        """
        repairable_codes = {"DUPLICATE_NODE_ID"}

        for issue in result.issues:
            if issue.code in repairable_codes:
                return True

        return False

    def clear(self) -> None:
        """Clear validation results."""
        self._tree.clear()
        self._last_result = None
        self._status_badge.set_status("idle", "NOT RUN")
        self._status_label.setText("Click 'Validate' to check workflow")
        self._status_label.setProperty("muted", True)
        self._error_badge.set_status("idle", "0 errors")
        self._warning_badge.set_status("idle", "0 warnings")
        self._repair_btn.setVisible(False)  # Hide repair button
        self._content_stack.setCurrentIndex(0)  # Empty state

        # PERFORMANCE: Clear validation cache to free memory
        # Cache is only useful within same workflow session
        from casare_rpa.domain.validation.validators import clear_validation_cache

        clear_validation_cache()

        # Refresh styles
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

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

    def get_all_errors(self) -> list:
        """
        Get all validation errors as a list of dictionaries.

        Returns:
            List of error dictionaries with keys: severity, code, message, location, suggestion
        """
        if self._last_result is None:
            return []
        return [issue.to_dict() for issue in self._last_result.errors]
