"""
History Tab for the Bottom Panel.

Displays the execution history of a workflow with timestamps,
node information, and execution metrics.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
    QStackedWidget,
)
from PySide6.QtGui import QColor
from loguru import logger


class HistoryTab(QWidget):
    """
    History tab widget for viewing workflow execution history.

    Displays a chronological list of all executed nodes with:
    - Timestamp
    - Node ID
    - Node Type
    - Execution Time
    - Status (success/failed)

    Signals:
        node_selected: Emitted when user selects a node from history (str: node_id)
        clear_requested: Emitted when user requests to clear history
    """

    node_selected = Signal(str)
    clear_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the history tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Store full history for filtering
        self._full_history: List[Dict[str, Any]] = []
        self._current_filter = "All"

        self._setup_ui()
        self._apply_styles()

        logger.debug("History tab initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Set size policy to prevent dock resizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Header with controls
        header_layout = QHBoxLayout()

        self._label_count = QLabel("Entries: 0")
        header_layout.addWidget(self._label_count)

        # Filter by status
        header_layout.addWidget(QLabel("Filter:"))
        self._combo_filter = QComboBox()
        self._combo_filter.setFixedHeight(14)
        self._combo_filter.addItems(["All", "Success", "Failed"])
        self._combo_filter.currentTextChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self._combo_filter)

        header_layout.addStretch()

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setFixedSize(32, 14)
        self._btn_clear.setToolTip("Clear execution history")
        self._btn_clear.clicked.connect(self._on_clear)
        header_layout.addWidget(self._btn_clear)

        layout.addLayout(header_layout)

        # Use stacked widget to prevent size changes when switching content
        self._content_stack = QStackedWidget()
        self._content_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Table for history (index 0)
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["#", "Timestamp", "Node ID", "Node Type", "Time (s)", "Status"]
        )

        # Set column resize modes
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Timestamp
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Node ID
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Node Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Time
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Status

        # Set column widths
        self._table.setColumnWidth(0, 40)  # #
        self._table.setColumnWidth(1, 160)  # Timestamp
        self._table.setColumnWidth(2, 120)  # Node ID
        self._table.setColumnWidth(4, 80)  # Time
        self._table.setColumnWidth(5, 80)  # Status

        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.verticalHeader().setVisible(False)

        self._content_stack.addWidget(self._table)  # Index 0

        # Empty state guidance (index 1)
        self._empty_state_label = QLabel(
            "No execution history yet.\n\n"
            "History will appear here when:\n"
            "- You run a workflow (F3)\n"
            "- Nodes execute and complete"
        )
        self._empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state_label.setWordWrap(True)
        self._content_stack.addWidget(self._empty_state_label)  # Index 1

        layout.addWidget(self._content_stack, 1)  # Stretch factor 1

        # Statistics
        stats_layout = QHBoxLayout()

        self._label_total_time = QLabel("Total: 0.000s")
        stats_layout.addWidget(self._label_total_time)

        self._label_avg_time = QLabel("Avg: 0.000s")
        stats_layout.addWidget(self._label_avg_time)

        self._label_success_rate = QLabel("Success: 0%")
        stats_layout.addWidget(self._label_success_rate)

        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # Show empty state initially (index 1)
        self._content_stack.setCurrentIndex(1)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                color: #cccccc;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #404040;
                gridline-color: #404040;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #094771;
            }
            QTableWidget::item:alternate {
                background-color: #2a2a2a;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 6px;
                border: none;
                border-right: 1px solid #404040;
            }
            QPushButton {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #4a4a4a;
                padding: 0px 1px;
                border-radius: 1px;
                font-size: 8px;
            }
            QPushButton:hover {
                background-color: #4a4d50;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QComboBox {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #4a4a4a;
                padding: 0px 1px;
                border-radius: 1px;
                font-size: 8px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QLabel {
                color: #cccccc;
            }
        """)

        self._empty_state_label.setStyleSheet("""
            QLabel {
                color: #7a7f85;
                font-size: 12px;
                padding: 20px;
            }
        """)

    def update_history(self, history: List[Dict[str, Any]]) -> None:
        """
        Update the displayed execution history.

        Args:
            history: List of execution history entries
        """
        self._full_history = history.copy()
        self._apply_filter()

    def append_entry(self, entry: Dict[str, Any]) -> None:
        """
        Append a single entry to the history.

        Args:
            entry: Execution history entry
        """
        self._full_history.append(entry)

        # If filter allows this entry, add it
        if self._should_show_entry(entry):
            self._add_entry_to_table(entry, len(self._full_history))
            self._update_statistics()

        # Show table (index 0)
        self._content_stack.setCurrentIndex(0)

    def _apply_filter(self) -> None:
        """Apply current filter to history."""
        # Clear table
        self._table.setRowCount(0)

        # Add filtered entries
        for i, entry in enumerate(self._full_history, 1):
            if self._should_show_entry(entry):
                self._add_entry_to_table(entry, i)

        # Toggle between table (index 0) and empty state (index 1)
        has_entries = len(self._full_history) > 0
        self._content_stack.setCurrentIndex(0 if has_entries else 1)

        # Update statistics
        self._update_statistics()

    def _should_show_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Check if entry should be shown based on current filter.

        Args:
            entry: History entry

        Returns:
            True if entry should be shown
        """
        if self._current_filter == "All":
            return True
        elif self._current_filter == "Success":
            return entry.get("status") == "success"
        elif self._current_filter == "Failed":
            return entry.get("status") == "failed"
        return True

    def _add_entry_to_table(self, entry: Dict[str, Any], number: int) -> None:
        """
        Add an entry to the table.

        Args:
            entry: History entry
            number: Entry number (1-based)
        """
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Number
        num_item = QTableWidgetItem(str(number))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, 0, num_item)

        # Timestamp
        timestamp = entry.get("timestamp", "")
        # Format timestamp (remove microseconds)
        if "." in timestamp:
            timestamp = timestamp.split(".")[0]
        timestamp_item = QTableWidgetItem(timestamp)
        self._table.setItem(row, 1, timestamp_item)

        # Node ID
        node_id = entry.get("node_id", "")
        node_id_item = QTableWidgetItem(node_id)
        self._table.setItem(row, 2, node_id_item)

        # Node Type
        node_type = entry.get("node_type", "")
        node_type_item = QTableWidgetItem(node_type)
        self._table.setItem(row, 3, node_type_item)

        # Execution Time
        exec_time = entry.get("execution_time", 0)
        time_item = QTableWidgetItem(f"{exec_time:.4f}")
        time_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._table.setItem(row, 4, time_item)

        # Status
        status = entry.get("status", "unknown")
        status_item = QTableWidgetItem(status.capitalize())
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Color code status
        if status == "success":
            status_item.setBackground(QColor(50, 100, 50))  # Dark green
            status_item.setForeground(QColor(150, 255, 150))
        elif status == "failed":
            status_item.setBackground(QColor(100, 50, 50))  # Dark red
            status_item.setForeground(QColor(255, 150, 150))

        self._table.setItem(row, 5, status_item)

    def _update_statistics(self) -> None:
        """Update statistics labels."""
        if not self._full_history:
            self._label_count.setText("Entries: 0")
            self._label_total_time.setText("Total: 0.000s")
            self._label_avg_time.setText("Avg: 0.000s")
            self._label_success_rate.setText("Success: 0%")
            return

        # Count
        visible_count = self._table.rowCount()
        total_count = len(self._full_history)
        if visible_count == total_count:
            self._label_count.setText(f"Entries: {total_count}")
        else:
            self._label_count.setText(f"Entries: {visible_count} / {total_count}")

        # Calculate statistics from full history
        total_time = sum(e.get("execution_time", 0) for e in self._full_history)
        avg_time = total_time / len(self._full_history)
        success_count = sum(
            1 for e in self._full_history if e.get("status") == "success"
        )
        success_rate = (success_count / len(self._full_history)) * 100

        self._label_total_time.setText(f"Total: {total_time:.4f}s")
        self._label_avg_time.setText(f"Avg: {avg_time:.4f}s")
        self._label_success_rate.setText(f"Success: {success_rate:.0f}%")

    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle filter change."""
        self._current_filter = filter_text
        self._apply_filter()
        logger.debug(f"History filter changed to: {filter_text}")

    def _on_selection_changed(self) -> None:
        """Handle selection change in table."""
        selected_rows = self._table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            node_id_item = self._table.item(row, 2)
            if node_id_item:
                node_id = node_id_item.text()
                logger.debug(f"History node selected: {node_id}")
                self.node_selected.emit(node_id)

    def _on_clear(self) -> None:
        """Handle clear button click."""
        logger.debug("Clear history requested")
        self.clear_requested.emit()

    def clear(self) -> None:
        """Clear all history entries."""
        self._full_history.clear()
        self._table.setRowCount(0)
        self._update_statistics()
        # Show empty state (index 1)
        self._content_stack.setCurrentIndex(1)
        logger.debug("Execution history cleared")

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the history."""
        if self._table.rowCount() > 0:
            self._table.scrollToBottom()

    def get_entry_count(self) -> int:
        """Get total number of history entries."""
        return len(self._full_history)
