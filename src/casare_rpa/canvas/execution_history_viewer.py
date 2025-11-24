"""
Execution History Viewer panel for debugging.

Displays the execution history of a workflow with timestamps,
node information, and execution metrics.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QComboBox,
)
from PySide6.QtGui import QColor

from loguru import logger


class ExecutionHistoryViewer(QDockWidget):
    """
    Dock widget for viewing workflow execution history.
    
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
        Initialize the execution history viewer.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__("Execution History", parent)
        
        self.setObjectName("ExecutionHistoryViewer")
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        self.label_count = QLabel("Entries: 0")
        header_layout.addWidget(self.label_count)
        
        # Filter by status
        header_layout.addWidget(QLabel("Filter:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["All", "Success", "Failed"])
        self.combo_filter.currentTextChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.combo_filter)
        
        header_layout.addStretch()
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setToolTip("Clear execution history")
        self.btn_clear.clicked.connect(self._on_clear)
        header_layout.addWidget(self.btn_clear)
        
        layout.addLayout(header_layout)
        
        # Table for history
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "#", "Timestamp", "Node ID", "Node Type", "Time (s)", "Status"
        ])
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Timestamp
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Node ID
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Node Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Time
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Status
        
        # Set column widths
        self.table.setColumnWidth(0, 40)  # #
        self.table.setColumnWidth(1, 180)  # Timestamp
        self.table.setColumnWidth(2, 120)  # Node ID
        self.table.setColumnWidth(3, 150)  # Node Type
        self.table.setColumnWidth(4, 80)  # Time
        self.table.setColumnWidth(5, 80)  # Status
        
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.label_total_time = QLabel("Total: 0.000s")
        stats_layout.addWidget(self.label_total_time)
        
        self.label_avg_time = QLabel("Avg: 0.000s")
        stats_layout.addWidget(self.label_avg_time)
        
        self.label_success_rate = QLabel("Success: 0%")
        stats_layout.addWidget(self.label_success_rate)
        
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        self.setWidget(main_widget)
        
        # Store full history for filtering
        self._full_history: List[Dict[str, Any]] = []
        self._current_filter = "All"
        
        logger.debug("Execution history viewer initialized")
    
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
    
    def _apply_filter(self) -> None:
        """Apply current filter to history."""
        # Clear table
        self.table.setRowCount(0)
        
        # Add filtered entries
        for i, entry in enumerate(self._full_history, 1):
            if self._should_show_entry(entry):
                self._add_entry_to_table(entry, i)
        
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
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Number
        num_item = QTableWidgetItem(str(number))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, num_item)
        
        # Timestamp
        timestamp = entry.get("timestamp", "")
        # Format timestamp (remove microseconds)
        if "." in timestamp:
            timestamp = timestamp.split(".")[0]
        timestamp_item = QTableWidgetItem(timestamp)
        self.table.setItem(row, 1, timestamp_item)
        
        # Node ID
        node_id = entry.get("node_id", "")
        node_id_item = QTableWidgetItem(node_id)
        self.table.setItem(row, 2, node_id_item)
        
        # Node Type
        node_type = entry.get("node_type", "")
        node_type_item = QTableWidgetItem(node_type)
        self.table.setItem(row, 3, node_type_item)
        
        # Execution Time
        exec_time = entry.get("execution_time", 0)
        time_item = QTableWidgetItem(f"{exec_time:.4f}")
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, time_item)
        
        # Status
        status = entry.get("status", "unknown")
        status_item = QTableWidgetItem(status.capitalize())
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color code status
        if status == "success":
            status_item.setBackground(QColor(200, 255, 200))  # Light green
        elif status == "failed":
            status_item.setBackground(QColor(255, 200, 200))  # Light red
        
        self.table.setItem(row, 5, status_item)
    
    def _update_statistics(self) -> None:
        """Update statistics labels."""
        if not self._full_history:
            self.label_count.setText("Entries: 0")
            self.label_total_time.setText("Total: 0.000s")
            self.label_avg_time.setText("Avg: 0.000s")
            self.label_success_rate.setText("Success: 0%")
            return
        
        # Count
        visible_count = self.table.rowCount()
        total_count = len(self._full_history)
        if visible_count == total_count:
            self.label_count.setText(f"Entries: {total_count}")
        else:
            self.label_count.setText(f"Entries: {visible_count} / {total_count}")
        
        # Calculate statistics from full history
        total_time = sum(e.get("execution_time", 0) for e in self._full_history)
        avg_time = total_time / len(self._full_history)
        success_count = sum(1 for e in self._full_history if e.get("status") == "success")
        success_rate = (success_count / len(self._full_history)) * 100
        
        self.label_total_time.setText(f"Total: {total_time:.4f}s")
        self.label_avg_time.setText(f"Avg: {avg_time:.4f}s")
        self.label_success_rate.setText(f"Success: {success_rate:.0f}%")
    
    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle filter change."""
        self._current_filter = filter_text
        self._apply_filter()
        logger.debug(f"History filter changed to: {filter_text}")
    
    def _on_selection_changed(self) -> None:
        """Handle selection change in table."""
        selected_rows = self.table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            node_id_item = self.table.item(row, 2)
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
        self.table.setRowCount(0)
        self._update_statistics()
        logger.debug("Execution history cleared")
    
    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the history."""
        if self.table.rowCount() > 0:
            self.table.scrollToBottom()
