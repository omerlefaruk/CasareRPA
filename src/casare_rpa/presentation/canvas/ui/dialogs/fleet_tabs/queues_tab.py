"""
Queues Tab Widget for Fleet Dashboard.

Transaction queue management with queue list, item browser, and statistics.
UiPath-style queue interface for managing workflow queue items.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.base_tab import BaseTabWidget

from casare_rpa.presentation.canvas.theme import THEME


class QueuesTabWidget(BaseTabWidget):
    """
    Transaction queues management tab.

    Features:
    - Queue list with status indicators
    - Transaction/item browser with filtering
    - Queue statistics cards
    - Add/edit/delete queue operations
    - Bulk item operations

    Signals:
        queue_selected: Emitted when queue is selected (queue_id)
        queue_created: Emitted when queue is created (queue_data)
        queue_deleted: Emitted when queue is deleted (queue_id)
        item_selected: Emitted when item is selected (queue_id, item_id)
        item_status_changed: Emitted when item status changes (item_id, new_status)
        queue_item_action: Emitted for bulk actions (queue_id, item_ids, action)
        items_bulk_action: Back-compat alias for queue_item_action
    """

    queue_selected = Signal(str)
    queue_created = Signal(dict)
    queue_deleted = Signal(str)
    item_selected = Signal(str, str)
    item_status_changed = Signal(str, str)
    queue_item_action = Signal(str, list, str)
    items_bulk_action = Signal(str, list, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the queues tab widget."""
        self._queues: List[Dict[str, Any]] = []
        self._queue_items: List[Dict[str, Any]] = []
        self._selected_queue_id: Optional[str] = None
        super().__init__("queues", parent)

    def _setup_content(self) -> None:
        """Set up queues tab content."""
        # Toolbar
        self._toolbar.addWidget(QLabel("Transaction Queues"))
        self._toolbar.addStretch()

        self._add_queue_btn = QPushButton("+ New Queue")
        self._add_queue_btn.setObjectName("AddButton")
        self._toolbar.addWidget(self._add_queue_btn)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Queue list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        queue_label = QLabel("Queues")
        queue_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(queue_label)

        self._queue_table = QTableWidget()
        self._queue_table.setColumnCount(3)
        self._queue_table.setHorizontalHeaderLabels(["Name", "Items", "Status"])
        self._queue_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._queue_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._queue_table.setAlternatingRowColors(True)
        self._queue_table.verticalHeader().setVisible(False)
        self._queue_table.horizontalHeader().setStretchLastSection(True)
        self._queue_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        left_layout.addWidget(self._queue_table)

        # Queue actions
        queue_actions = QHBoxLayout()
        self._delete_queue_btn = QPushButton("Delete")
        self._delete_queue_btn.setEnabled(False)
        self._delete_queue_btn.setObjectName("DeleteButton")
        queue_actions.addWidget(self._delete_queue_btn)
        queue_actions.addStretch()
        left_layout.addLayout(queue_actions)

        splitter.addWidget(left_panel)

        # Right panel - Items and stats
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Statistics cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)

        self._total_card = self._create_stat_card("Total", "0")
        stats_layout.addWidget(self._total_card)

        self._new_card = self._create_stat_card("New", "0", THEME.status_info)
        stats_layout.addWidget(self._new_card)

        self._progress_card = self._create_stat_card(
            "In Progress", "0", THEME.status_warning
        )
        stats_layout.addWidget(self._progress_card)

        self._completed_card = self._create_stat_card(
            "Completed", "0", THEME.status_success
        )
        stats_layout.addWidget(self._completed_card)

        self._failed_card = self._create_stat_card("Failed", "0", THEME.status_error)
        stats_layout.addWidget(self._failed_card)

        right_layout.addLayout(stats_layout)

        # Item filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self._status_filter = QComboBox()
        self._status_filter.addItems(
            ["All", "New", "InProgress", "Completed", "Failed"]
        )
        self._status_filter.setFixedWidth(120)
        filter_layout.addWidget(self._status_filter)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search items...")
        filter_layout.addWidget(self._search_input)

        filter_layout.addStretch()
        right_layout.addLayout(filter_layout)

        # Items table
        items_label = QLabel("Queue Items")
        items_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(items_label)

        self._items_table = QTableWidget()
        self._items_table.setColumnCount(5)
        self._items_table.setHorizontalHeaderLabels(
            ["Reference", "Status", "Priority", "Created", "Updated"]
        )
        self._items_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._items_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._items_table.setAlternatingRowColors(True)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self._items_table)

        # Item actions
        item_actions = QHBoxLayout()

        self._add_item_btn = QPushButton("+ Add Item")
        self._add_item_btn.setEnabled(False)
        item_actions.addWidget(self._add_item_btn)

        self._retry_btn = QPushButton("Retry Failed")
        self._retry_btn.setEnabled(False)
        item_actions.addWidget(self._retry_btn)

        self._mark_complete_btn = QPushButton("Mark Complete")
        self._mark_complete_btn.setEnabled(False)
        item_actions.addWidget(self._mark_complete_btn)

        item_actions.addStretch()

        self._bulk_delete_btn = QPushButton("Delete Selected")
        self._bulk_delete_btn.setEnabled(False)
        self._bulk_delete_btn.setObjectName("DeleteButton")
        item_actions.addWidget(self._bulk_delete_btn)

        right_layout.addLayout(item_actions)

        splitter.addWidget(right_panel)

        # Set splitter sizes (30% queues, 70% items)
        splitter.setSizes([300, 700])

        self._main_layout.addWidget(splitter)

        # Connect signals
        self._connect_tab_signals()

    def _create_stat_card(
        self, title: str, value: str, color: Optional[str] = None
    ) -> QFrame:
        """Create a statistics card widget."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {THEME.bg_panel};
                border: 1px solid {THEME.border};
                border-radius: 8px;
                padding: 8px;
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_color = color or THEME.text_primary
        value_label.setStyleSheet(
            f"color: {value_color}; font-size: 20px; font-weight: bold;"
        )
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)

        return card

    def _update_card_value(self, card: QFrame, value: str) -> None:
        """Update a card's value label."""
        label = card.findChild(QLabel, "value_label")
        if label:
            label.setText(value)

    def _connect_tab_signals(self) -> None:
        """Connect tab-specific signals."""
        self._queue_table.selectionModel().selectionChanged.connect(
            self._on_queue_selection_changed
        )
        self._items_table.selectionModel().selectionChanged.connect(
            self._on_item_selection_changed
        )

        self._add_queue_btn.clicked.connect(self._on_add_queue)
        self._delete_queue_btn.clicked.connect(self._on_delete_queue)
        self._add_item_btn.clicked.connect(self._on_add_item)
        self._retry_btn.clicked.connect(self._on_retry_failed)
        self._mark_complete_btn.clicked.connect(self._on_mark_complete)
        self._bulk_delete_btn.clicked.connect(self._on_bulk_delete)

        self._status_filter.currentIndexChanged.connect(self._apply_item_filter)
        self._search_input.textChanged.connect(self._apply_item_filter)

    def _on_queue_selection_changed(self) -> None:
        """Handle queue selection change."""
        selected = self._queue_table.selectedItems()
        if selected:
            row = selected[0].row()
            queue_id = self._queue_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self._selected_queue_id = queue_id
            self._delete_queue_btn.setEnabled(True)
            self._add_item_btn.setEnabled(True)
            self.queue_selected.emit(queue_id)
        else:
            self._selected_queue_id = None
            self._delete_queue_btn.setEnabled(False)
            self._add_item_btn.setEnabled(False)

    def _on_item_selection_changed(self) -> None:
        """Handle item selection change."""
        selected = self._items_table.selectedItems()
        has_selection = len(selected) > 0

        self._retry_btn.setEnabled(has_selection)
        self._mark_complete_btn.setEnabled(has_selection)
        self._bulk_delete_btn.setEnabled(has_selection)

        if selected and self._selected_queue_id:
            row = selected[0].row()
            item = self._items_table.item(row, 0)
            if item:
                item_id = item.data(Qt.ItemDataRole.UserRole)
                self.item_selected.emit(self._selected_queue_id, item_id)

    def _on_add_queue(self) -> None:
        """Handle add queue button."""
        # Emit signal - parent handles dialog
        self.queue_created.emit({})

    def _on_delete_queue(self) -> None:
        """Handle delete queue button."""
        if self._selected_queue_id:
            self.queue_deleted.emit(self._selected_queue_id)

    def _on_add_item(self) -> None:
        """Handle add item button."""
        # Emit signal - parent handles dialog
        pass

    def _on_retry_failed(self) -> None:
        """Handle retry failed items."""
        if self._selected_queue_id:
            item_ids = self._get_selected_item_ids()
            self.queue_item_action.emit(self._selected_queue_id, item_ids, "retry")
            self.items_bulk_action.emit(self._selected_queue_id, item_ids, "retry")

    def _on_mark_complete(self) -> None:
        """Handle mark complete."""
        if self._selected_queue_id:
            item_ids = self._get_selected_item_ids()
            self.queue_item_action.emit(self._selected_queue_id, item_ids, "complete")
            self.items_bulk_action.emit(self._selected_queue_id, item_ids, "complete")

    def _on_bulk_delete(self) -> None:
        """Handle bulk delete."""
        if self._selected_queue_id:
            item_ids = self._get_selected_item_ids()
            self.queue_item_action.emit(self._selected_queue_id, item_ids, "delete")
            self.items_bulk_action.emit(self._selected_queue_id, item_ids, "delete")

    def _get_selected_item_ids(self) -> List[str]:
        """Get IDs of selected items."""
        item_ids = []
        for item in self._items_table.selectedItems():
            if item.column() == 0:
                item_id = item.data(Qt.ItemDataRole.UserRole)
                if item_id:
                    item_ids.append(item_id)
        return item_ids

    def _apply_item_filter(self) -> None:
        """Apply filters to items table."""
        status_filter = self._status_filter.currentText()
        search_text = self._search_input.text().lower()

        for row in range(self._items_table.rowCount()):
            show = True

            # Status filter
            if status_filter != "All":
                status_item = self._items_table.item(row, 1)
                if status_item and status_item.text() != status_filter:
                    show = False

            # Search filter
            if show and search_text:
                ref_item = self._items_table.item(row, 0)
                if ref_item and search_text not in ref_item.text().lower():
                    show = False

            self._items_table.setRowHidden(row, not show)

    def _apply_additional_styles(self) -> None:
        """Apply additional tab styles."""
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            #AddButton {{
                background-color: {THEME.accent_primary};
                color: {THEME.text_primary};
                border: none;
            }}
            #AddButton:hover {{
                background-color: {THEME.accent_hover};
            }}
            #DeleteButton {{
                background-color: {THEME.accent_error};
                color: {THEME.text_primary};
                border: none;
            }}
            #DeleteButton:hover {{
                background-color: {THEME.status_error};
            }}
        """
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def update_queues(self, queues: List[Dict[str, Any]]) -> None:
        """
        Update the queues list.

        Args:
            queues: List of queue dictionaries
        """
        self._queues = queues
        self._queue_table.setRowCount(0)

        for queue in queues:
            row = self._queue_table.rowCount()
            self._queue_table.insertRow(row)

            # Name
            name_item = QTableWidgetItem(queue.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, queue.get("id"))
            self._queue_table.setItem(row, 0, name_item)

            # Item count
            item_count = queue.get("item_count", 0)
            self._queue_table.setItem(row, 1, QTableWidgetItem(str(item_count)))

            # Status indicator
            status = queue.get("status", "active")
            status_item = QTableWidgetItem(status.title())
            if status == "active":
                status_item.setForeground(QColor(THEME.status_success))
            elif status == "paused":
                status_item.setForeground(QColor(THEME.status_warning))
            else:
                status_item.setForeground(QColor(THEME.text_secondary))
            self._queue_table.setItem(row, 2, status_item)

    def update_queue_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Update the queue items list.

        Args:
            items: List of queue item dictionaries
        """
        self._queue_items = items
        self._items_table.setRowCount(0)

        for item in items:
            row = self._items_table.rowCount()
            self._items_table.insertRow(row)

            # Reference
            ref_item = QTableWidgetItem(item.get("reference", item.get("id", "")))
            ref_item.setData(Qt.ItemDataRole.UserRole, item.get("id"))
            self._items_table.setItem(row, 0, ref_item)

            # Status
            status = item.get("status", "new")
            status_item = QTableWidgetItem(status.title())
            status_colors = {
                "new": THEME.status_info,
                "inprogress": THEME.status_warning,
                "completed": THEME.status_success,
                "failed": THEME.status_error,
            }
            color = status_colors.get(status.lower(), THEME.text_secondary)
            status_item.setForeground(QColor(color))
            self._items_table.setItem(row, 1, status_item)

            # Priority
            priority = item.get("priority", 0)
            self._items_table.setItem(row, 2, QTableWidgetItem(str(priority)))

            # Created
            created = item.get("created_at", "-")
            if hasattr(created, "strftime"):
                created = created.strftime("%Y-%m-%d %H:%M")
            self._items_table.setItem(row, 3, QTableWidgetItem(str(created)))

            # Updated
            updated = item.get("updated_at", "-")
            if hasattr(updated, "strftime"):
                updated = updated.strftime("%Y-%m-%d %H:%M")
            self._items_table.setItem(row, 4, QTableWidgetItem(str(updated)))

        self._apply_item_filter()

    def update_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Update queue statistics.

        Args:
            stats: Statistics dictionary with counts
        """
        self._update_card_value(self._total_card, str(stats.get("total", 0)))
        self._update_card_value(self._new_card, str(stats.get("new", 0)))
        self._update_card_value(self._progress_card, str(stats.get("in_progress", 0)))
        self._update_card_value(self._completed_card, str(stats.get("completed", 0)))
        self._update_card_value(self._failed_card, str(stats.get("failed", 0)))

    def get_selected_queue_id(self) -> Optional[str]:
        """Get currently selected queue ID."""
        return self._selected_queue_id


__all__ = ["QueuesTabWidget"]
