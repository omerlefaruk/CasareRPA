"""
History Tab for the Bottom Panel.

Displays the execution history of a workflow with improved UX:
- Empty state with guidance
- Color-coded status badges
- Statistics bar with totals
- Click to navigate to node
- Filter by status
- Context menu for copy
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    StatusBadge,
    ToolbarButton,
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)


class HistoryTab(QWidget):
    """
    History tab widget for viewing workflow execution history.

    Displays a chronological list of all executed nodes with:
    - Timestamp
    - Node ID
    - Node Type
    - Execution Time
    - Status (success/failed)

    Features:
    - Empty state when no history
    - Filter by status (All, Success, Failed)
    - Click to navigate to node
    - Statistics summary (total time, avg time, success rate)
    - Context menu for copy

    Signals:
        node_selected: Emitted when user selects a node from history (str: node_id)
        clear_requested: Emitted when user requests to clear history
    """

    node_selected = Signal(str)
    clear_requested = Signal()

    # PERFORMANCE: Maximum deferred entries before forcing update
    MAX_DEFERRED = 50

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the history tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Store full history for filtering
        self._full_history: list[dict[str, Any]] = []
        self._current_filter = "All"

        # PERFORMANCE: Lazy update support - defer updates when tab not visible
        self._deferred_entries: list[dict[str, Any]] = []

        self._setup_ui()
        self._apply_styles()

        logger.debug("History tab initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Set size policy to prevent dock resizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("historyToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(8, 6, 8, 6)
        toolbar.setSpacing(12)

        # Entry count label
        self._count_label = QLabel("0 entries")
        self._count_label.setProperty("muted", True)

        # Filter by status
        filter_label = QLabel("Status:")
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Success", "Failed"])
        self._filter_combo.setFixedWidth(90)
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self._filter_combo.setToolTip("Filter history by execution status")

        # Clear button
        clear_btn = ToolbarButton(
            text="Clear",
            tooltip="Clear execution history",
        )
        clear_btn.clicked.connect(self._on_clear)

        toolbar.addWidget(self._count_label)
        toolbar.addStretch()
        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar_widget)

        # Content stack for empty state vs table
        self._content_stack = QStackedWidget()
        self._content_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Empty state (index 0)
        self._empty_state = EmptyStateWidget(
            icon_text="",  # Clock/history icon
            title="No Execution History",
            description=(
                "Execution history will appear here when:\n"
                "- You run a workflow (F3)\n"
                "- Nodes execute and complete\n\n"
                "Click on an entry to navigate to its node."
            ),
        )
        self._content_stack.addWidget(self._empty_state)

        # Table container (index 1)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(8, 4, 8, 4)
        table_layout.setSpacing(4)

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
        self._table.setColumnWidth(1, 120)  # Timestamp
        self._table.setColumnWidth(2, 120)  # Node ID
        self._table.setColumnWidth(4, 80)  # Time
        self._table.setColumnWidth(5, 80)  # Status

        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(self._on_double_click)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.verticalHeader().setVisible(False)

        table_layout.addWidget(self._table)

        self._content_stack.addWidget(table_container)

        layout.addWidget(self._content_stack, 1)

        # Statistics bar
        stats_widget = QWidget()
        stats_widget.setObjectName("statsBar")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(8, 6, 8, 6)
        stats_layout.setSpacing(16)

        self._total_time_label = QLabel("Total: 0.000s")
        self._avg_time_label = QLabel("Avg: 0.000s")
        self._success_rate_badge = StatusBadge("0%", "idle")

        stats_layout.addWidget(QLabel("Total Time:"))
        stats_layout.addWidget(self._total_time_label)
        stats_layout.addWidget(QLabel("Avg:"))
        stats_layout.addWidget(self._avg_time_label)
        stats_layout.addStretch()
        stats_layout.addWidget(QLabel("Success Rate:"))
        stats_layout.addWidget(self._success_rate_badge)

        layout.addWidget(stats_widget)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            HistoryTab, QWidget, QStackedWidget, QFrame {{
                background-color: {THEME.bg_panel};
            }}
            #historyToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            {get_panel_table_stylesheet()}
            #statsBar {{
                background-color: {THEME.bg_header};
                border-top: 1px solid {THEME.border_dark};
            }}
            #statsBar QLabel {{
                color: {THEME.text_muted};
                font-size: 11px;
            }}
        """)

    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle filter change."""
        self._current_filter = filter_text
        self._apply_filter()
        logger.debug(f"History filter changed to: {filter_text}")

    def _apply_filter(self) -> None:
        """Apply current filter to history."""
        # Clear table
        self._table.setRowCount(0)

        # Add filtered entries
        for i, entry in enumerate(self._full_history, 1):
            if self._should_show_entry(entry):
                self._add_entry_to_table(entry, i)

        # Toggle between table and empty state
        self._update_display()

        # Update statistics
        self._update_statistics()

    def _should_show_entry(self, entry: dict[str, Any]) -> bool:
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

    def _add_entry_to_table(self, entry: dict[str, Any], number: int) -> None:
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
        num_item.setForeground(QBrush(QColor(THEME.text_muted)))
        self._table.setItem(row, 0, num_item)

        # Timestamp (format nicely)
        timestamp = entry.get("timestamp", "")
        if "." in timestamp:
            timestamp = timestamp.split(".")[0]
        if "T" in timestamp:
            timestamp = timestamp.replace("T", " ")
        timestamp_item = QTableWidgetItem(timestamp)
        timestamp_item.setForeground(QBrush(QColor(THEME.text_muted)))
        self._table.setItem(row, 1, timestamp_item)

        # Node ID (clickable style)
        node_id = entry.get("node_id", "")
        node_id_item = QTableWidgetItem(node_id)
        node_id_item.setForeground(QBrush(QColor(THEME.accent_primary)))
        node_id_item.setToolTip(f"Node: {node_id}\nDouble-click to navigate")
        self._table.setItem(row, 2, node_id_item)

        # Node Type
        node_type = entry.get("node_type", "")
        node_type_item = QTableWidgetItem(node_type)
        node_type_item.setToolTip(f"Type: {node_type}")
        self._table.setItem(row, 3, node_type_item)

        # Execution Time (right-aligned)
        exec_time = entry.get("execution_time", 0)
        time_item = QTableWidgetItem(f"{exec_time:.4f}")
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_item.setToolTip(f"Execution time: {exec_time:.6f} seconds")
        self._table.setItem(row, 4, time_item)

        # Status (color-coded badge style)
        status = entry.get("status", "unknown")
        status_item = QTableWidgetItem(status.upper())
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if status == "success":
            status_item.setBackground(QBrush(QColor("#1a3d1a")))
            status_item.setForeground(QBrush(QColor(THEME.status_success)))
        elif status == "failed":
            status_item.setBackground(QBrush(QColor("#3d1a1a")))
            status_item.setForeground(QBrush(QColor(THEME.status_error)))
        else:
            status_item.setForeground(QBrush(QColor(THEME.text_muted)))

        self._table.setItem(row, 5, status_item)

    def _update_statistics(self) -> None:
        """Update statistics labels."""
        if not self._full_history:
            self._total_time_label.setText("0.000s")
            self._avg_time_label.setText("0.000s")
            self._success_rate_badge.set_status("idle", "0%")
            return

        # Calculate statistics from full history
        total_time = sum(e.get("execution_time", 0) for e in self._full_history)
        avg_time = total_time / len(self._full_history)
        success_count = sum(1 for e in self._full_history if e.get("status") == "success")
        success_rate = (success_count / len(self._full_history)) * 100

        self._total_time_label.setText(f"{total_time:.3f}s")
        self._avg_time_label.setText(f"{avg_time:.3f}s")

        # Color-code success rate
        if success_rate >= 90:
            self._success_rate_badge.set_status("success", f"{success_rate:.0f}%")
        elif success_rate >= 50:
            self._success_rate_badge.set_status("warning", f"{success_rate:.0f}%")
        else:
            self._success_rate_badge.set_status("error", f"{success_rate:.0f}%")

    def _update_display(self) -> None:
        """Update empty state vs table display and count label."""
        has_entries = len(self._full_history) > 0
        self._content_stack.setCurrentIndex(1 if has_entries else 0)

        # Update count label
        visible_count = self._table.rowCount()
        total_count = len(self._full_history)
        if visible_count == total_count:
            self._count_label.setText(f"{total_count} entr{'ies' if total_count != 1 else 'y'}")
        else:
            self._count_label.setText(f"{visible_count} of {total_count}")

        self._count_label.setProperty("muted", total_count == 0)
        self._count_label.style().unpolish(self._count_label)
        self._count_label.style().polish(self._count_label)

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

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on history entry."""
        row = item.row()
        node_id_item = self._table.item(row, 2)
        if node_id_item:
            node_id = node_id_item.text()
            if node_id:
                self.node_selected.emit(node_id)

    def _on_context_menu(self, pos) -> None:
        """Show context menu for history entry."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
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

        # Copy node ID
        node_id_item = self._table.item(row, 2)
        if node_id_item:
            copy_id = menu.addAction("Copy Node ID")
            copy_id.triggered.connect(lambda: QApplication.clipboard().setText(node_id_item.text()))

        # Copy entire row
        copy_row = menu.addAction("Copy Entry")
        copy_row.triggered.connect(lambda: self._copy_row(row))

        # Navigate to node
        if node_id_item and node_id_item.text():
            menu.addSeparator()
            nav_action = menu.addAction("Go to Node")
            nav_action.triggered.connect(lambda: self.node_selected.emit(node_id_item.text()))

        menu.exec_(self._table.mapToGlobal(pos))

    def _copy_row(self, row: int) -> None:
        """Copy a history row to clipboard."""
        parts = []
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                parts.append(item.text())
        QApplication.clipboard().setText("\t".join(parts))

    def _on_clear(self) -> None:
        """Handle clear button click."""
        logger.debug("Clear history requested")
        self.clear_requested.emit()

    # ==================== Public API ====================

    def update_history(self, history: list[dict[str, Any]]) -> None:
        """
        Update the displayed execution history.

        Args:
            history: List of execution history entries
        """
        self._full_history = history.copy()
        self._apply_filter()

    def _is_tab_visible(self) -> bool:
        """
        Check if this tab is currently visible.

        PERFORMANCE: Used for lazy updates - defer expensive table updates
        when user isn't looking at this tab.
        """
        if not self.isVisible():
            return False

        parent = self.parent()
        while parent:
            if hasattr(parent, "currentWidget"):
                return parent.currentWidget() == self
            parent = parent.parent()

        return True

    def _flush_deferred_entries(self) -> None:
        """Flush all deferred entries to the table."""
        if not self._deferred_entries:
            return

        for entry in self._deferred_entries:
            self._full_history.append(entry)
            if self._should_show_entry(entry):
                self._add_entry_to_table(entry, len(self._full_history))

        self._deferred_entries.clear()
        self._update_statistics()
        self._update_display()
        logger.debug("Flushed deferred history entries")

    def showEvent(self, event) -> None:
        """Handle tab becoming visible - flush deferred updates."""
        super().showEvent(event)
        if self._deferred_entries:
            self._flush_deferred_entries()

    def append_entry(self, entry: dict[str, Any]) -> None:
        """
        Append a single entry to the history.

        PERFORMANCE: Uses lazy updates - defers table updates when tab
        is not visible to reduce CPU during workflow execution.

        Args:
            entry: Execution history entry
        """
        # PERFORMANCE: Defer updates when tab not visible
        is_visible = self._is_tab_visible()

        if not is_visible and len(self._deferred_entries) < self.MAX_DEFERRED:
            self._deferred_entries.append(entry)
            return

        # Flush deferred entries if now visible
        if is_visible and self._deferred_entries:
            self._flush_deferred_entries()

        # Add this entry directly
        self._full_history.append(entry)

        # If filter allows this entry, add it
        if self._should_show_entry(entry):
            self._add_entry_to_table(entry, len(self._full_history))
            self._update_statistics()

        self._update_display()

    def clear(self) -> None:
        """Clear all history entries."""
        self._full_history.clear()
        self._table.setRowCount(0)
        self._update_statistics()
        self._update_display()
        logger.debug("Execution history cleared")

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the history."""
        if self._table.rowCount() > 0:
            self._table.scrollToBottom()

    def get_entry_count(self) -> int:
        """Get total number of history entries."""
        return len(self._full_history)
