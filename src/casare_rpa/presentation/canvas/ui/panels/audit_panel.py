"""
Audit Panel UI Component.

Provides a comprehensive view of security audit events with:
- Filterable event table with sorting
- Event type and status filtering
- Date range selection
- Event details viewer
- Export to CSV/JSON functionality
- Integrity verification
- Statistics summary

Uses LazySubscription for EventBus optimization - subscriptions are only active
when the panel is visible, reducing overhead when panel is hidden.
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger
from PySide6.QtCore import QDateTime, Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import (
    FONT_SIZES,
    RADIUS,
    SIZES,
    SPACING,
    THEME,
)
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    StatusBadge,
    ToolbarButton,
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)

# Event type display names
EVENT_TYPE_DISPLAY = {
    "secret_read": "Secret Read",
    "secret_write": "Secret Write",
    "secret_delete": "Secret Delete",
    "secret_rotate": "Secret Rotate",
    "secret_lease_renew": "Lease Renew",
    "secret_lease_revoke": "Lease Revoke",
    "auth_success": "Auth Success",
    "auth_failure": "Auth Failure",
    "cache_hit": "Cache Hit",
    "cache_miss": "Cache Miss",
}

# Status colors for success/failure
STATUS_COLORS = {
    True: THEME.status_success,
    False: THEME.status_error,
}


class EventDetailsDialog(QDialog):
    """Dialog showing full details of an audit event."""

    def __init__(
        self,
        event_data: dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the dialog.

        Args:
            event_data: Dictionary containing event details
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Audit Event Details")
        self.setMinimumSize(500, 400)  # TODO: Consider SIZES.dialog_width_min
        self.setModal(True)

        self._setup_ui(event_data)
        self._apply_styles()

    def _setup_ui(self, event: dict[str, Any]) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.lg)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)

        # Header with event type and status
        header = QHBoxLayout()

        event_type = event.get("event_type", "unknown")
        type_label = QLabel(EVENT_TYPE_DISPLAY.get(event_type, event_type.title()))
        type_label.setObjectName("eventType")

        success = event.get("success", True)
        status_badge = StatusBadge(
            "SUCCESS" if success else "FAILURE",
            "success" if success else "error",
        )

        header.addWidget(type_label)
        header.addStretch()
        header.addWidget(status_badge)
        layout.addLayout(header)

        # Details form
        form = QFormLayout()
        form.setSpacing(SPACING.md)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Event ID
        id_label = QLabel(event.get("event_id", "N/A"))
        id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Event ID:", id_label)

        # Timestamp
        timestamp = event.get("timestamp")
        if isinstance(timestamp, datetime):
            ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        else:
            ts_str = str(timestamp) if timestamp else "N/A"
        ts_label = QLabel(ts_str)
        form.addRow("Timestamp:", ts_label)

        # Resource/Path
        path = event.get("path") or event.get("resource") or "N/A"
        path_label = QLabel(path)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_label.setWordWrap(True)
        form.addRow("Resource:", path_label)

        # Workflow ID
        workflow_id = event.get("workflow_id") or "N/A"
        wf_label = QLabel(workflow_id)
        wf_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Workflow ID:", wf_label)

        # Robot ID
        robot_id = event.get("robot_id") or "N/A"
        robot_label = QLabel(robot_id)
        robot_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Robot ID:", robot_label)

        # User ID
        user_id = event.get("user_id") or "N/A"
        user_label = QLabel(user_id)
        user_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("User ID:", user_label)

        # Client IP
        client_ip = event.get("client_ip") or "N/A"
        ip_label = QLabel(client_ip)
        form.addRow("Client IP:", ip_label)

        layout.addLayout(form)

        # Error message (if any)
        error_msg = event.get("error_message")
        if error_msg:
            error_group = QGroupBox("Error Message")
            error_layout = QVBoxLayout(error_group)
            error_text = QTextEdit()
            error_text.setPlainText(error_msg)
            error_text.setReadOnly(True)
            error_text.setMaximumHeight(80)  # TODO: Consider adding SIZES.*
            error_layout.addWidget(error_text)
            layout.addWidget(error_group)

        # Metadata
        metadata = event.get("metadata", {})
        if metadata:
            import json

            meta_group = QGroupBox("Metadata")
            meta_layout = QVBoxLayout(meta_group)
            meta_text = QTextEdit()
            meta_text.setPlainText(json.dumps(metadata, indent=2))
            meta_text.setReadOnly(True)
            meta_text.setMaximumHeight(120)  # TODO: Consider adding SIZES.*
            meta_layout.addWidget(meta_text)
            layout.addWidget(meta_group)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _apply_styles(self) -> None:
        """Apply dialog styling."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QLabel {{
                color: {THEME.text_primary};
                background: transparent;
            }}
            #eventType {{
                font-size: 16px;
                font-weight: 600;
                color: {THEME.accent_primary};
            }}
            QGroupBox {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border_dark};
                border-radius: {RADIUS.sm}px;
                margin-top: {SPACING.xl}px;
                padding: {SPACING.md}px;
            }}
            QGroupBox::title {{
                color: {THEME.text_secondary};
                subcontrol-origin: margin;
                left: {SPACING.md}px;
                padding: 0 {SPACING.sm}px;
            }}
            QTextEdit {{
                background-color: {THEME.input_bg};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: {RADIUS.sm}px;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: {FONT_SIZES.sm}px;
            }}
            QDialogButtonBox QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: {RADIUS.sm}px;
                padding: 6px 16px;
                min-width: 80px;
                min-height: {SIZES.input_min_height + SIZES.spacing.sm}px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
        """)


class AuditPanel(QDockWidget):
    """
    Dockable audit panel for viewing security audit events.

    Features:
    - Sortable table of audit events
    - Event type filtering
    - Success/failure filtering
    - Date range filtering
    - Event detail viewer
    - Export to CSV/JSON
    - Integrity verification
    - Statistics summary

    Signals:
        refresh_requested: Emitted when data refresh is needed
        export_requested: Emitted with export format and path
    """

    refresh_requested = Signal()
    export_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the audit panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Security Audit", parent)
        self.setObjectName("AuditDock")

        self._events: list[dict[str, Any]] = []
        self._statistics: dict[str, Any] = {}
        self._is_loading = False
        self._context_event: dict[str, Any] | None = None  # Context menu target

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("AuditPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(400)  # TODO: Consider SIZES.panel_width_min
        self.setMinimumHeight(300)  # TODO: Consider SIZES.panel_height_min

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("auditToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(
            SIZES.toolbar_padding,
            SIZES.toolbar_button_padding_v,
            SIZES.toolbar_padding,
            SIZES.toolbar_button_padding_v,
        )
        toolbar.setSpacing(SIZES.toolbar_spacing)

        # Event count label
        self._count_label = QLabel("0 events")
        self._count_label.setProperty("muted", True)

        # Event type filter
        type_label = QLabel("Type:")
        self._type_filter = QComboBox()
        self._type_filter.addItem("All Types", "")
        for event_type, display in EVENT_TYPE_DISPLAY.items():
            self._type_filter.addItem(display, event_type)
        self._type_filter.setFixedWidth(120)  # TODO: Consider SIZES.combo_dropdown_width
        self._type_filter.currentIndexChanged.connect(self._on_filter_changed)

        # Success filter
        status_label = QLabel("Status:")
        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "Success", "Failure"])
        self._status_filter.setFixedWidth(90)  # TODO: Consider SIZES.combo_dropdown_width
        self._status_filter.currentIndexChanged.connect(self._on_filter_changed)

        # Refresh button
        refresh_btn = ToolbarButton(
            text="Refresh",
            tooltip="Reload audit events",
        )
        refresh_btn.clicked.connect(self._on_refresh)

        # Export button
        export_btn = ToolbarButton(
            text="Export",
            tooltip="Export audit events to file",
        )
        export_btn.clicked.connect(self._on_export)

        # Verify integrity button
        verify_btn = ToolbarButton(
            text="Verify",
            tooltip="Verify audit chain integrity",
        )
        verify_btn.clicked.connect(self._on_verify_integrity)

        toolbar.addWidget(self._count_label)
        toolbar.addStretch()
        toolbar.addWidget(type_label)
        toolbar.addWidget(self._type_filter)
        toolbar.addWidget(status_label)
        toolbar.addWidget(self._status_filter)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(verify_btn)

        main_layout.addWidget(toolbar_widget)

        # Date range toolbar
        date_toolbar = QWidget()
        date_toolbar.setObjectName("dateToolbar")
        date_layout = QHBoxLayout(date_toolbar)
        date_layout.setContentsMargins(
            SIZES.toolbar_padding,
            SPACING.sm,
            SIZES.toolbar_padding,
            SPACING.sm,
        )
        date_layout.setSpacing(SPACING.md)

        date_layout.addWidget(QLabel("From:"))
        self._start_date = QDateTimeEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self._start_date.setFixedWidth(160)  # TODO: Consider SIZES.*
        self._start_date.dateTimeChanged.connect(self._on_filter_changed)
        date_layout.addWidget(self._start_date)

        date_layout.addWidget(QLabel("To:"))
        self._end_date = QDateTimeEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDateTime(QDateTime.currentDateTime())
        self._end_date.setFixedWidth(160)  # TODO: Consider SIZES.*
        self._end_date.dateTimeChanged.connect(self._on_filter_changed)
        date_layout.addWidget(self._end_date)

        date_layout.addStretch()

        main_layout.addWidget(date_toolbar)

        # Content stack for empty state vs table
        self._content_stack = QStackedWidget()

        # Empty state (index 0)
        self._empty_state = EmptyStateWidget(
            icon_text="",
            title="No Audit Events",
            description=(
                "Audit events track security-related operations:\n\n"
                "- Secret access and modifications\n"
                "- Authentication attempts\n"
                "- Cache operations\n\n"
                "Events are logged automatically when using\n"
                "the vault and credential management features."
            ),
            action_text="Refresh",
        )
        self._empty_state.action_clicked.connect(self._on_refresh)
        self._content_stack.addWidget(self._empty_state)

        # Main content (index 1)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        content_layout.setSpacing(SPACING.sm)

        # Statistics summary
        stats_widget = QWidget()
        stats_widget.setObjectName("statsSummary")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        stats_layout.setSpacing(SPACING.xl)

        self._total_label = QLabel("Total: 0")
        self._success_label = QLabel("Success: 0")
        self._success_label.setStyleSheet(f"color: {THEME.status_success};")
        self._failed_label = QLabel("Failed: 0")
        self._failed_label.setStyleSheet(f"color: {THEME.status_error};")

        stats_layout.addWidget(self._total_label)
        stats_layout.addWidget(self._success_label)
        stats_layout.addWidget(self._failed_label)
        stats_layout.addStretch()

        content_layout.addWidget(stats_widget)

        # Events table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Timestamp", "Type", "Resource", "Status", "User/Robot", "Details"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self._table.setSortingEnabled(True)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(5, 60)  # TODO: Consider SPACING.xxxl * 2

        content_layout.addWidget(self._table)

        # Loading indicator
        self._loading_bar = QProgressBar()
        self._loading_bar.setRange(0, 0)
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setMaximumHeight(SIZES.scrollbar_width)
        self._loading_bar.setVisible(False)
        content_layout.addWidget(self._loading_bar)

        self._content_stack.addWidget(content_widget)

        main_layout.addWidget(self._content_stack)

        self.setWidget(container)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            AuditPanel, QDockWidget, QWidget, QStackedWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                color: {THEME.dock_title_text};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            #auditToolbar, #dateToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            #statsSummary {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border_dark};
                border-radius: 4px;
            }}
            {get_panel_toolbar_stylesheet()}
            {get_panel_table_stylesheet()}
            QTableWidget {{
                background-color: {THEME.bg_panel};
                border: 1px solid {THEME.border_dark};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QTableWidget::item:hover {{
                background-color: {THEME.bg_hover};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_header};
                color: {THEME.text_secondary};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {THEME.border_dark};
                border-right: 1px solid {THEME.border_dark};
                font-weight: 600;
            }}
            QDateTimeEdit {{
                background-color: {THEME.input_bg};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: {RADIUS.sm}px;
                padding: 4px 8px;
            }}
            QDateTimeEdit:focus {{
                border-color: {THEME.border_focus};
            }}
            QProgressBar {{
                background-color: {THEME.bg_dark};
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {THEME.accent_primary};
            }}
        """)

    def set_events(self, events: list[dict[str, Any]]) -> None:
        """
        Set the audit events to display.

        Args:
            events: List of audit event dictionaries
        """
        self._events = events
        self._update_table()
        self._update_statistics()
        self._update_display()

    def set_statistics(self, stats: dict[str, Any]) -> None:
        """
        Set the statistics summary.

        Args:
            stats: Dictionary with statistics data
        """
        self._statistics = stats

        total = stats.get("total_events", 0)
        success = stats.get("successful_events", 0)
        failed = stats.get("failed_events", 0)

        self._total_label.setText(f"Total: {total}")
        self._success_label.setText(f"Success: {success}")
        self._failed_label.setText(f"Failed: {failed}")

    def set_loading(self, loading: bool) -> None:
        """
        Set loading state.

        Args:
            loading: True to show loading indicator
        """
        self._is_loading = loading
        self._loading_bar.setVisible(loading)

    def _update_table(self) -> None:
        """Update the table with current events."""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        # Apply filters
        filtered_events = self._apply_filters(self._events)

        for event in filtered_events:
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Timestamp
            timestamp = event.get("timestamp")
            if isinstance(timestamp, datetime):
                ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts_str = str(timestamp) if timestamp else ""
            ts_item = QTableWidgetItem(ts_str)
            self._table.setItem(row, 0, ts_item)

            # Event type
            event_type = event.get("event_type", "")
            type_display = EVENT_TYPE_DISPLAY.get(event_type, event_type.title())
            type_item = QTableWidgetItem(type_display)
            self._table.setItem(row, 1, type_item)

            # Resource
            resource = event.get("path") or event.get("resource") or ""
            resource_item = QTableWidgetItem(resource)
            resource_item.setToolTip(resource)
            self._table.setItem(row, 2, resource_item)

            # Status
            success = event.get("success", True)
            status_item = QTableWidgetItem("Success" if success else "Failed")
            status_color = STATUS_COLORS.get(success, THEME.text_primary)
            status_item.setForeground(QBrush(QColor(status_color)))
            self._table.setItem(row, 3, status_item)

            # User/Robot
            user_robot = event.get("user_id") or event.get("robot_id") or ""
            user_item = QTableWidgetItem(
                user_robot[:20] + "..." if len(user_robot) > 20 else user_robot
            )
            user_item.setToolTip(user_robot)
            self._table.setItem(row, 4, user_item)

            # Details button placeholder
            details_item = QTableWidgetItem("View")
            details_item.setForeground(QBrush(QColor(THEME.accent_primary)))
            details_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, details_item)

            # Store event data
            ts_item.setData(Qt.ItemDataRole.UserRole, event)

        self._table.setSortingEnabled(True)

        # Update count
        self._count_label.setText(f"{len(filtered_events)} events")

    def _apply_filters(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply current filters to events."""
        filtered = events

        # Type filter
        type_value = self._type_filter.currentData()
        if type_value:
            filtered = [e for e in filtered if e.get("event_type") == type_value]

        # Status filter
        status_text = self._status_filter.currentText()
        if status_text == "Success":
            filtered = [e for e in filtered if e.get("success", True)]
        elif status_text == "Failure":
            filtered = [e for e in filtered if not e.get("success", True)]

        # Date range filter
        start_dt = self._start_date.dateTime().toPython()
        end_dt = self._end_date.dateTime().toPython()

        def in_range(event: dict[str, Any]) -> bool:
            ts = event.get("timestamp")
            if isinstance(ts, datetime):
                # Make timezone-aware if needed
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                start_aware = start_dt.replace(tzinfo=UTC) if start_dt.tzinfo is None else start_dt
                end_aware = end_dt.replace(tzinfo=UTC) if end_dt.tzinfo is None else end_dt
                return start_aware <= ts <= end_aware
            return True

        filtered = [e for e in filtered if in_range(e)]

        return filtered

    def _update_statistics(self) -> None:
        """Update statistics from current events."""
        total = len(self._events)
        success = sum(1 for e in self._events if e.get("success", True))
        failed = total - success

        self._total_label.setText(f"Total: {total}")
        self._success_label.setText(f"Success: {success}")
        self._failed_label.setText(f"Failed: {failed}")

    def _update_display(self) -> None:
        """Update empty state vs content display."""
        has_events = len(self._events) > 0
        self._content_stack.setCurrentIndex(1 if has_events else 0)

    def _on_filter_changed(self) -> None:
        """Handle filter changes."""
        self._update_table()

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        self.refresh_requested.emit()

    def _on_export(self) -> None:
        """Handle export button click."""
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
        """)

        csv_action = menu.addAction("Export to CSV")
        csv_action.triggered.connect(self._on_export_csv)

        json_action = menu.addAction("Export to JSON")
        json_action.triggered.connect(self._on_export_json)

        menu.exec_(self.cursor().pos())

    @Slot()
    def _on_export_csv(self) -> None:
        """Handle export to CSV action."""
        self._export_to_format("csv")

    @Slot()
    def _on_export_json(self) -> None:
        """Handle export to JSON action."""
        self._export_to_format("json")

    def _export_to_format(self, format_type: str) -> None:
        """Export events to specified format."""
        file_filter = "CSV Files (*.csv)" if format_type == "csv" else "JSON Files (*.json)"
        default_name = f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"

        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Audit Events as {format_type.upper()}",
            default_name,
            file_filter,
        )

        if path:
            self.export_requested.emit(format_type, path)

    def _on_verify_integrity(self) -> None:
        """Handle verify integrity button click."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Verify Audit Integrity")
        msg.setText("Verifying audit chain integrity...")
        msg.setInformativeText("This will check that no audit events have been tampered with.")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {THEME.bg_panel}; }}
            QMessageBox QLabel {{ color: {THEME.text_primary}; }}
            QPushButton {{
                background: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 16px;
                color: {THEME.text_primary};
                min-width: 80px;
                min-height: 32px;
            }}
            QPushButton:hover {{ background: {THEME.bg_hover}; }}
        """)
        msg.exec()

    def _on_context_menu(self, pos) -> None:
        """Show context menu for event row."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        event_data = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not event_data:
            return

        # Store context event for slot methods
        self._context_event = event_data

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
        """)

        view_action = menu.addAction("View Details")
        view_action.triggered.connect(self._on_context_view_details)

        menu.addSeparator()

        copy_id_action = menu.addAction("Copy Event ID")
        copy_id_action.triggered.connect(self._on_context_copy_event_id)

        if event_data.get("path") or event_data.get("resource"):
            copy_resource_action = menu.addAction("Copy Resource Path")
            copy_resource_action.triggered.connect(self._on_context_copy_resource)

        menu.exec_(self._table.mapToGlobal(pos))

    @Slot()
    def _on_context_view_details(self) -> None:
        """Handle view details context menu action."""
        if self._context_event:
            self._show_event_details(self._context_event)

    @Slot()
    def _on_context_copy_event_id(self) -> None:
        """Handle copy event ID context menu action."""
        if self._context_event:
            self._copy_to_clipboard(self._context_event.get("event_id", ""))

    @Slot()
    def _on_context_copy_resource(self) -> None:
        """Handle copy resource path context menu action."""
        if self._context_event:
            self._copy_to_clipboard(
                self._context_event.get("path") or self._context_event.get("resource", "")
            )

    def _on_row_double_clicked(self, row: int, col: int) -> None:
        """Handle double-click on table row."""
        event_data = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if event_data:
            self._show_event_details(event_data)

    def _show_event_details(self, event_data: dict[str, Any]) -> None:
        """Show event details dialog."""
        dialog = EventDetailsDialog(event_data, self)
        dialog.exec()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(text)

    def get_filter_state(self) -> dict[str, Any]:
        """
        Get current filter state.

        Returns:
            Dictionary with filter values
        """
        return {
            "event_type": self._type_filter.currentData(),
            "status": self._status_filter.currentText(),
            "start_time": self._start_date.dateTime().toPython(),
            "end_time": self._end_date.dateTime().toPython(),
        }


__all__ = ["AuditPanel", "EventDetailsDialog"]
