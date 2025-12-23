"""
Transactions Tab for Queue Management Dock.

Provides queue item (transaction) management:
- Table view of queue items
- Filters: Status, Date range, Priority
- Actions: Retry, Delete, View Details
- Bulk operations
"""

from datetime import datetime
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.application.services import QueueService
from casare_rpa.domain.orchestrator.entities import QueueItem, QueueItemStatus
from casare_rpa.presentation.canvas.ui.theme import Theme


class ItemDetailsDialog(QDialog):
    """Dialog for viewing queue item details."""

    def __init__(
        self,
        item: QueueItem,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item = item
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle(f"Item Details - {self._item.id[:8]}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        form.addRow("ID:", QLabel(self._item.id))
        form.addRow("Reference:", QLabel(self._item.reference or "-"))
        form.addRow("Status:", self._create_status_label())
        form.addRow("Priority:", QLabel(str(self._item.priority)))
        form.addRow("Retries:", QLabel(str(self._item.retries)))
        form.addRow("Robot:", QLabel(self._item.robot_name or "-"))
        form.addRow("Duration:", QLabel(self._item.duration_formatted))

        if self._item.created_at:
            form.addRow("Created:", QLabel(self._item.created_at.strftime("%Y-%m-%d %H:%M:%S")))
        if self._item.started_at:
            form.addRow("Started:", QLabel(self._item.started_at.strftime("%Y-%m-%d %H:%M:%S")))
        if self._item.completed_at:
            form.addRow(
                "Completed:",
                QLabel(self._item.completed_at.strftime("%Y-%m-%d %H:%M:%S")),
            )

        layout.addLayout(form)

        if self._item.error_message:
            error_label = QLabel("Error:")
            error_label.setStyleSheet("color: #F48771; font-weight: bold;")
            layout.addWidget(error_label)

            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setText(self._item.error_message)
            error_text.setMaximumHeight(80)
            layout.addWidget(error_text)

        data_label = QLabel("Input Data:")
        layout.addWidget(data_label)

        self._data_text = QTextEdit()
        self._data_text.setReadOnly(True)
        self._load_data()
        layout.addWidget(self._data_text)

        if self._item.output:
            output_label = QLabel("Output Data:")
            layout.addWidget(output_label)

            output_text = QTextEdit()
            output_text.setReadOnly(True)
            import json

            try:
                output_text.setText(json.dumps(self._item.output, indent=2))
            except (TypeError, ValueError):
                output_text.setText(str(self._item.output))
            layout.addWidget(output_text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_status_label(self) -> QLabel:
        """Create a colored status label."""
        label = QLabel(self._item.status.value.upper())
        colors = {
            QueueItemStatus.NEW: "#75BEFF",
            QueueItemStatus.IN_PROGRESS: "#D7BA7D",
            QueueItemStatus.COMPLETED: "#89D185",
            QueueItemStatus.FAILED: "#F48771",
            QueueItemStatus.ABANDONED: "#C586C0",
            QueueItemStatus.RETRY: "#D7BA7D",
            QueueItemStatus.DELETED: "#6B6B6B",
        }
        color = colors.get(self._item.status, "#CCCCCC")
        label.setStyleSheet(f"color: {color}; font-weight: bold;")
        return label

    def _load_data(self) -> None:
        """Load item data into text field."""
        import json

        try:
            self._data_text.setText(json.dumps(self._item.data, indent=2))
        except (TypeError, ValueError):
            self._data_text.setText(str(self._item.data))

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        c = Theme.get_colors()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c.background_alt};
            }}
            QLabel {{
                color: {c.text_primary};
            }}
            QTextEdit {{
                background-color: {c.background};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 11px;
            }}
        """)


class TransactionsTab(QWidget):
    """
    Tab widget for managing queue items (transactions).

    Provides:
    - Table view with status, priority, timing columns
    - Filtering by status, date range
    - Retry, Delete actions
    - Bulk operations
    """

    item_selected = Signal(str, str)

    def __init__(
        self,
        queue_service: QueueService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue_service = queue_service
        self._current_queue_id: str | None = None
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        self._queue_label = QLabel("Select a queue to view items")
        self._queue_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self._queue_label)
        header.addStretch()

        layout.addLayout(header)

        filters = QHBoxLayout()
        filters.setSpacing(8)

        filters.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItem("All", None)
        for status in QueueItemStatus:
            self._status_filter.addItem(status.value.title(), status)
        filters.addWidget(self._status_filter)

        filters.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by reference...")
        self._search_input.setMinimumWidth(150)
        filters.addWidget(self._search_input)

        filters.addStretch()

        layout.addLayout(filters)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._retry_btn = QPushButton("Retry Selected")
        self._retry_btn.setEnabled(False)
        toolbar.addWidget(self._retry_btn)

        self._delete_btn = QPushButton("Delete Selected")
        self._delete_btn.setEnabled(False)
        toolbar.addWidget(self._delete_btn)

        toolbar.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels(
            [
                "ID",
                "Reference",
                "Status",
                "Priority",
                "Robot",
                "Created",
                "Started",
                "Duration",
                "Error",
            ]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        c = Theme.get_colors()
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c.background_alt};
                border: 1px solid {c.border_dark};
                gridline-color: {c.border_dark};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {c.selection};
            }}
            QHeaderView::section {{
                background-color: {c.header};
                color: {c.text_header};
                padding: 6px;
                border: none;
                border-right: 1px solid {c.border_dark};
                border-bottom: 1px solid {c.border_dark};
                font-size: 11px;
            }}
            QComboBox {{
                min-width: 100px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._retry_btn.clicked.connect(self._on_retry_selected)
        self._delete_btn.clicked.connect(self._on_delete_selected)
        self._refresh_btn.clicked.connect(self.refresh)
        self._status_filter.currentIndexChanged.connect(self.refresh)
        self._search_input.textChanged.connect(self._on_search_changed)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

    def set_queue(self, queue_id: str) -> None:
        """Set the current queue to display."""
        self._current_queue_id = queue_id
        queue = self._queue_service.get_queue(queue_id)
        if queue:
            self._queue_label.setText(f"Queue: {queue.name}")
        else:
            self._queue_label.setText("Queue not found")
        self.refresh()

    def refresh(self) -> None:
        """Refresh the items list."""
        self._table.setRowCount(0)

        if not self._current_queue_id:
            return

        status_filter = self._status_filter.currentData()
        items = self._queue_service.list_items(
            self._current_queue_id,
            status=status_filter,
            limit=500,
        )

        search_text = self._search_input.text().lower().strip()
        if search_text:
            items = [i for i in items if search_text in (i.reference or "").lower()]

        self._table.setRowCount(len(items))

        for row, item in enumerate(items):
            self._table.setItem(row, 0, self._create_item(item.id[:8], item.id))
            self._table.setItem(row, 1, self._create_item(item.reference or "-"))
            self._table.setItem(row, 2, self._create_status_item(item.status))
            self._table.setItem(row, 3, self._create_num_item(item.priority))
            self._table.setItem(row, 4, self._create_item(item.robot_name or "-"))
            self._table.setItem(row, 5, self._create_datetime_item(item.created_at))
            self._table.setItem(row, 6, self._create_datetime_item(item.started_at))
            self._table.setItem(row, 7, self._create_item(item.duration_formatted))
            self._table.setItem(
                row,
                8,
                self._create_item(
                    item.error_message[:50] + "..."
                    if len(item.error_message) > 50
                    else item.error_message or "-"
                ),
            )

        logger.debug(f"Refreshed transactions tab: {len(items)} items")

    def _create_item(self, text: str, data: Any = None) -> QTableWidgetItem:
        """Create a table item."""
        item = QTableWidgetItem(text)
        if data is not None:
            item.setData(Qt.ItemDataRole.UserRole, data)
        return item

    def _create_num_item(self, value: int) -> QTableWidgetItem:
        """Create a numeric table item."""
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setData(Qt.ItemDataRole.UserRole, value)
        return item

    def _create_status_item(self, status: QueueItemStatus) -> QTableWidgetItem:
        """Create a status table item with color."""
        item = QTableWidgetItem(status.value.upper())
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setData(Qt.ItemDataRole.UserRole, status)

        colors = {
            QueueItemStatus.NEW: QColor("#75BEFF"),
            QueueItemStatus.IN_PROGRESS: QColor("#D7BA7D"),
            QueueItemStatus.COMPLETED: QColor("#89D185"),
            QueueItemStatus.FAILED: QColor("#F48771"),
            QueueItemStatus.ABANDONED: QColor("#C586C0"),
            QueueItemStatus.RETRY: QColor("#D7BA7D"),
            QueueItemStatus.DELETED: QColor("#6B6B6B"),
        }
        item.setForeground(colors.get(status, QColor("#CCCCCC")))

        return item

    def _create_datetime_item(self, dt: datetime | None) -> QTableWidgetItem:
        """Create a datetime table item."""
        if dt:
            text = dt.strftime("%Y-%m-%d %H:%M")
        else:
            text = "-"
        return QTableWidgetItem(text)

    def _get_selected_item_ids(self) -> list[str]:
        """Get selected item IDs."""
        item_ids = []
        for item in self._table.selectedItems():
            if item.column() == 0:
                item_id = item.data(Qt.ItemDataRole.UserRole)
                if item_id:
                    item_ids.append(item_id)
        return item_ids

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        selected_ids = self._get_selected_item_ids()
        has_selection = bool(selected_ids)
        self._retry_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    def _on_search_changed(self) -> None:
        """Handle search text change."""
        self.refresh()

    def _on_retry_selected(self) -> None:
        """Retry selected items."""
        if not self._current_queue_id:
            return

        item_ids = self._get_selected_item_ids()
        if not item_ids:
            return

        count = 0
        for item_id in item_ids:
            if self._queue_service.retry_item(self._current_queue_id, item_id):
                count += 1

        if count > 0:
            QMessageBox.information(
                self, "Items Retried", f"{count} item(s) have been reset for retry."
            )
            self.refresh()

    def _on_delete_selected(self) -> None:
        """Delete selected items."""
        if not self._current_queue_id:
            return

        item_ids = self._get_selected_item_ids()
        if not item_ids:
            return

        reply = QMessageBox.question(
            self,
            "Delete Items",
            f"Are you sure you want to delete {len(item_ids)} item(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            count = 0
            for item_id in item_ids:
                if self._queue_service.delete_item(self._current_queue_id, item_id):
                    count += 1

            if count > 0:
                self.refresh()

    def _on_context_menu(self, pos) -> None:
        """Show context menu."""
        if not self._table.itemAt(pos):
            return

        menu = QMenu(self)

        view_action = QAction("View Details", self)
        view_action.triggered.connect(self._on_view_details)
        menu.addAction(view_action)

        menu.addSeparator()

        retry_action = QAction("Retry", self)
        retry_action.triggered.connect(self._on_retry_selected)
        menu.addAction(retry_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete_selected)
        menu.addAction(delete_action)

        menu.exec(self._table.mapToGlobal(pos))

    def _on_double_click(self) -> None:
        """Handle double-click to view details."""
        self._on_view_details()

    def _on_view_details(self) -> None:
        """View item details."""
        if not self._current_queue_id:
            return

        item_ids = self._get_selected_item_ids()
        if not item_ids:
            return

        item = self._queue_service.get_item(self._current_queue_id, item_ids[0])
        if item:
            dialog = ItemDetailsDialog(item, self)
            dialog.exec()
