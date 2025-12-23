"""
Queues Tab for Queue Management Dock.

Provides queue definition management:
- List of queue definitions
- Create/Edit/Delete queues
- Queue schema (JSON) editor
- Queue settings (max retries, auto-retry)
"""

from typing import Any, Dict, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.application.services import QueueService
from casare_rpa.domain.orchestrator.entities import Queue
from casare_rpa.presentation.canvas.ui.theme import Theme


class QueueEditDialog(QDialog):
    """Dialog for creating/editing a queue."""

    def __init__(
        self,
        parent: QWidget | None = None,
        queue: Queue | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue = queue
        self._setup_ui()
        self._apply_styles()

        if queue:
            self._load_queue(queue)

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Edit Queue" if self._queue else "New Queue")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter queue name...")
        form.addRow("Name:", self._name_input)

        self._description_input = QLineEdit()
        self._description_input.setPlaceholderText("Enter description...")
        form.addRow("Description:", self._description_input)

        self._max_retries_input = QSpinBox()
        self._max_retries_input.setRange(0, 100)
        self._max_retries_input.setValue(3)
        form.addRow("Max Retries:", self._max_retries_input)

        self._retry_delay_input = QSpinBox()
        self._retry_delay_input.setRange(0, 86400)
        self._retry_delay_input.setValue(60)
        self._retry_delay_input.setSuffix(" seconds")
        form.addRow("Retry Delay:", self._retry_delay_input)

        self._auto_retry_input = QCheckBox("Enable automatic retry on failure")
        self._auto_retry_input.setChecked(True)
        form.addRow("Auto Retry:", self._auto_retry_input)

        self._unique_ref_input = QCheckBox("Require unique reference per item")
        form.addRow("Unique Reference:", self._unique_ref_input)

        layout.addLayout(form)

        schema_label = QLabel("Item Schema (JSON):")
        layout.addWidget(schema_label)

        self._schema_input = QTextEdit()
        self._schema_input.setPlaceholderText('{\n  "type": "object",\n  "properties": {}\n}')
        self._schema_input.setMinimumHeight(120)
        layout.addWidget(self._schema_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
            QLineEdit, QSpinBox, QTextEdit {{
                background-color: {c.background};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 6px;
            }}
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
                border-color: {c.accent};
            }}
            QCheckBox {{
                color: {c.text_primary};
            }}
        """)

    def _load_queue(self, queue: Queue) -> None:
        """Load queue data into form."""
        self._name_input.setText(queue.name)
        self._description_input.setText(queue.description)
        self._max_retries_input.setValue(queue.max_retries)
        self._retry_delay_input.setValue(queue.retry_delay_seconds)
        self._auto_retry_input.setChecked(queue.auto_retry)
        self._unique_ref_input.setChecked(queue.enforce_unique_reference)

        if queue.schema:
            import json

            try:
                self._schema_input.setText(json.dumps(queue.schema, indent=2))
            except (TypeError, ValueError):
                self._schema_input.setText("{}")

    def _on_accept(self) -> None:
        """Validate and accept dialog."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Queue name is required.")
            return

        import json

        schema_text = self._schema_input.toPlainText().strip()
        if schema_text:
            try:
                json.loads(schema_text)
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "Validation Error", f"Invalid JSON schema: {e}")
                return

        self.accept()

    def get_queue_data(self) -> dict[str, Any]:
        """Get queue data from form."""
        import json

        schema_text = self._schema_input.toPlainText().strip()
        schema = {}
        if schema_text:
            try:
                schema = json.loads(schema_text)
            except json.JSONDecodeError:
                pass

        return {
            "name": self._name_input.text().strip(),
            "description": self._description_input.text().strip(),
            "max_retries": self._max_retries_input.value(),
            "retry_delay_seconds": self._retry_delay_input.value(),
            "auto_retry": self._auto_retry_input.isChecked(),
            "enforce_unique_reference": self._unique_ref_input.isChecked(),
            "schema": schema,
        }


class QueuesTab(QWidget):
    """
    Tab widget for managing queue definitions.

    Provides:
    - Table view of queues with statistics
    - Create/Edit/Delete actions
    - Context menu for quick actions
    """

    queue_selected = Signal(str)

    def __init__(
        self,
        queue_service: QueueService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue_service = queue_service
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._add_btn = QPushButton("New Queue")
        self._add_btn.setProperty("primary", True)
        toolbar.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setEnabled(False)
        toolbar.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        toolbar.addWidget(self._delete_btn)

        toolbar.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            [
                "Name",
                "Description",
                "Items",
                "New",
                "In Progress",
                "Completed",
                "Failed",
            ]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

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
                padding: 6px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {c.selection};
            }}
            QHeaderView::section {{
                background-color: {c.header};
                color: {c.text_header};
                padding: 8px;
                border: none;
                border-right: 1px solid {c.border_dark};
                border-bottom: 1px solid {c.border_dark};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._add_btn.clicked.connect(self._on_add_queue)
        self._edit_btn.clicked.connect(self._on_edit_queue)
        self._delete_btn.clicked.connect(self._on_delete_queue)
        self._refresh_btn.clicked.connect(self.refresh)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

    def refresh(self) -> None:
        """Refresh the queue list."""
        self._table.setRowCount(0)

        queues = self._queue_service.list_queues()
        self._table.setRowCount(len(queues))

        for row, queue in enumerate(queues):
            self._table.setItem(row, 0, self._create_item(queue.name, queue.id))
            self._table.setItem(row, 1, self._create_item(queue.description))
            self._table.setItem(row, 2, self._create_num_item(queue.item_count))
            self._table.setItem(row, 3, self._create_num_item(queue.new_count))
            self._table.setItem(row, 4, self._create_num_item(queue.in_progress_count))
            self._table.setItem(row, 5, self._create_num_item(queue.completed_count))
            self._table.setItem(row, 6, self._create_num_item(queue.failed_count))

        logger.debug(f"Refreshed queues tab: {len(queues)} queues")

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

    def _get_selected_queue_id(self) -> str | None:
        """Get the selected queue ID."""
        selected = self._table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        name_item = self._table.item(row, 0)
        return name_item.data(Qt.ItemDataRole.UserRole) if name_item else None

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        has_selection = bool(self._table.selectedItems())
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

        queue_id = self._get_selected_queue_id()
        if queue_id:
            self.queue_selected.emit(queue_id)

    def _on_add_queue(self) -> None:
        """Handle add queue action."""
        dialog = QueueEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_queue_data()
            self._queue_service.create_queue(
                name=data["name"],
                description=data["description"],
                schema=data["schema"],
                max_retries=data["max_retries"],
                retry_delay_seconds=data["retry_delay_seconds"],
                auto_retry=data["auto_retry"],
                enforce_unique_reference=data["enforce_unique_reference"],
            )
            self.refresh()

    def _on_edit_queue(self) -> None:
        """Handle edit queue action."""
        queue_id = self._get_selected_queue_id()
        if not queue_id:
            return

        queue = self._queue_service.get_queue(queue_id)
        if not queue:
            return

        dialog = QueueEditDialog(self, queue)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_queue_data()
            self._queue_service.update_queue(
                queue_id,
                name=data["name"],
                description=data["description"],
                schema=data["schema"],
                max_retries=data["max_retries"],
                retry_delay_seconds=data["retry_delay_seconds"],
                auto_retry=data["auto_retry"],
                enforce_unique_reference=data["enforce_unique_reference"],
            )
            self.refresh()

    def _on_delete_queue(self) -> None:
        """Handle delete queue action."""
        queue_id = self._get_selected_queue_id()
        if not queue_id:
            return

        queue = self._queue_service.get_queue(queue_id)
        if not queue:
            return

        reply = QMessageBox.question(
            self,
            "Delete Queue",
            f"Are you sure you want to delete queue '{queue.name}'?\n"
            "All items in the queue will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._queue_service.delete_queue(queue_id)
            self.refresh()

    def _on_context_menu(self, pos) -> None:
        """Show context menu."""
        if not self._table.itemAt(pos):
            return

        menu = QMenu(self)

        edit_action = QAction("Edit Queue", self)
        edit_action.triggered.connect(self._on_edit_queue)
        menu.addAction(edit_action)

        delete_action = QAction("Delete Queue", self)
        delete_action.triggered.connect(self._on_delete_queue)
        menu.addAction(delete_action)

        menu.addSeparator()

        view_items_action = QAction("View Items", self)
        view_items_action.triggered.connect(self._on_view_items)
        menu.addAction(view_items_action)

        menu.exec(self._table.mapToGlobal(pos))

    def _on_double_click(self) -> None:
        """Handle double-click to view items."""
        self._on_view_items()

    def _on_view_items(self) -> None:
        """Navigate to view queue items."""
        queue_id = self._get_selected_queue_id()
        if queue_id:
            self.queue_selected.emit(queue_id)
