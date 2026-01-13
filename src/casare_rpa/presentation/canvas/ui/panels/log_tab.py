"""
Log Tab for the Bottom Panel.

Provides real-time execution log display with improved UX:
- Empty state guidance when no logs
- Filtering by log level
- Click to navigate to node
- Auto-scroll toggle
- Export to file
- Context menu for copy operations
- Color-coded log levels

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import (
    _get_header_stylesheet,
    _get_table_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.selects import Select
from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import EmptyState

if TYPE_CHECKING:
    from casare_rpa.domain.events import DomainEvent


class LogTab(QWidget):
    """
    Log tab widget for displaying execution logs.

    Features:
    - Empty state when no logs
    - Filter by log level (All, Debug, Info, Warning, Error, Success)
    - Click to navigate to node
    - Auto-scroll toggle
    - Export to file
    - Context menu for copy
    - Color-coded level indicators
    - PERFORMANCE: Lazy updates when tab not visible

    Signals:
        navigate_to_node: Emitted when user wants to navigate to a node
    """

    navigate_to_node = Signal(str)  # node_id

    # Table columns
    COL_TIME = 0
    COL_LEVEL = 1
    COL_NODE = 2
    COL_MESSAGE = 3

    # PERFORMANCE: Maximum deferred entries before forcing update
    MAX_DEFERRED = 50

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the Log tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._auto_scroll = True
        self._current_filter = "All"
        self._max_entries = 1000

        # PERFORMANCE: Lazy update support - defer updates when tab not visible
        self._deferred_logs: list = []
        self._last_visible_check = False

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("logToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        toolbar.setSpacing(TOKENS_V2.spacing.xs)

        # Filter label and dropdown
        filter_label = QLabel("Level:")
        self._filter_combo = Select(size="sm")
        self._filter_combo.add_items(["All", "Debug", "Info", "Warning", "Error", "Success"])
        self._filter_combo.set_value("All")
        self._filter_combo.current_changed.connect(self._on_filter_changed)
        self._filter_combo.setToolTip("Filter logs by level")

        # Entry count label
        self._count_label = QLabel("0 entries")
        self._count_label.setProperty("muted", True)

        # Auto-scroll toggle button (v2 PushButton)
        self._auto_scroll_btn = PushButton(
            text="Auto-scroll",
            variant="primary",
            size="sm",
        )
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.setToolTip("Toggle auto-scroll to latest log entry")
        self._auto_scroll_btn.clicked.connect(self._on_auto_scroll_toggled)

        # Clear button (v2 PushButton)
        clear_btn = PushButton(
            text="Clear",
            variant="ghost",
            size="sm",
        )
        clear_btn.setToolTip("Clear all log entries")
        clear_btn.clicked.connect(self.clear)

        # Export button (v2 PushButton)
        export_btn = PushButton(
            text="Export",
            variant="ghost",
            size="sm",
        )
        export_btn.setToolTip("Export logs to file")
        export_btn.clicked.connect(self._on_export)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addWidget(self._count_label)
        toolbar.addStretch()
        toolbar.addWidget(self._auto_scroll_btn)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar_widget)

        # Content area with stacked widget for empty state
        self._content_stack = QStackedWidget()

        # Empty state (index 0) - v2 EmptyState component
        self._empty_state = EmptyState(
            icon="scroll",
            text="No Log Entries",
            action_text="",
        )
        self._empty_state.set_text(
            "Execution logs will appear here when:\n"
            "- You run a workflow (F3)\n"
            "- Nodes execute and emit events\n\n"
            "Double-click a log entry to navigate to its node."
        )
        self._content_stack.addWidget(self._empty_state)

        # Log table (index 1)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(
            TOKENS_V2.spacing.sm, TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.sm, TOKENS_V2.spacing.sm
        )
        table_layout.setSpacing(TOKENS_V2.spacing.xs)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Time", "Level", "Node", "Message"])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.itemDoubleClicked.connect(self._on_double_click)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.verticalHeader().setVisible(False)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_NODE, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

        # Set minimum column widths using v2 tokens
        self._table.setColumnWidth(self.COL_NODE, TOKENS_V2.sizes.panel_default_width)

        table_layout.addWidget(self._table)

        self._content_stack.addWidget(table_container)

        layout.addWidget(self._content_stack)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply v2 theme styling."""
        # Apply table and header styles from lists.py
        self._table.setStyleSheet(_get_table_stylesheet())
        self._table.horizontalHeader().setStyleSheet(_get_header_stylesheet())

        # Main widget styling
        self.setStyleSheet(f"""
            LogTab, QWidget, QStackedWidget, QFrame {{
                background-color: {THEME_V2.bg_surface};
            }}
            #logToolbar {{
                background-color: {THEME_V2.bg_header};
                border-bottom: 1px solid {THEME_V2.border};
            }}
            QLabel {{
                background: transparent;
                color: {THEME_V2.text_secondary};
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QLabel[muted="true"] {{
                color: {THEME_V2.text_muted};
            }}
            QTableWidget {{
                font-family: {TOKENS_V2.typography.mono};
                font-size: {TOKENS_V2.typography.body}px;
            }}
        """)

    @Slot(str)
    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle filter change."""
        self._current_filter = filter_text
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current filter to table rows."""
        visible_count = 0
        for row in range(self._table.rowCount()):
            level_item = self._table.item(row, self.COL_LEVEL)
            if level_item:
                level = level_item.text().upper()
                if self._current_filter == "All":
                    self._table.setRowHidden(row, False)
                    visible_count += 1
                else:
                    hidden = level != self._current_filter.upper()
                    self._table.setRowHidden(row, hidden)
                    if not hidden:
                        visible_count += 1

        # Update count label
        total = self._table.rowCount()
        if self._current_filter == "All":
            self._count_label.setText(f"{total} entr{'ies' if total != 1 else 'y'}")
        else:
            self._count_label.setText(f"{visible_count} of {total}")

    @Slot(bool)
    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        """Handle auto-scroll toggle."""
        self._auto_scroll = checked

    @Slot(QTableWidgetItem)
    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on log entry."""
        row = item.row()
        node_item = self._table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)

    @Slot(QPoint)
    def _on_context_menu(self, pos: QPoint) -> None:
        """Show context menu for log entry."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        # Store row and node_id for slot methods
        self._context_menu_row = row
        self._context_menu_node_id = None

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME_V2.bg_elevated};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px;
            }}
            QMenu::item {{
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
            QMenu::item:selected {{
                background-color: {THEME_V2.bg_selected};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {THEME_V2.border};
                margin: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
            }}
        """)

        # Copy message
        msg_item = self._table.item(row, self.COL_MESSAGE)
        if msg_item:
            self._context_menu_message = msg_item.text()
            copy_msg = menu.addAction("Copy Message")
            copy_msg.triggered.connect(self._on_copy_message)

        # Copy entire row
        copy_row = menu.addAction("Copy Log Entry")
        copy_row.triggered.connect(self._on_copy_row)

        # Navigate to node
        node_item = self._table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self._context_menu_node_id = node_id
                menu.addSeparator()
                nav_action = menu.addAction("Go to Node")
                nav_action.triggered.connect(self._on_navigate_to_node)

        menu.exec_(self._table.mapToGlobal(pos))

    @Slot()
    def _on_copy_message(self) -> None:
        """Copy context menu message to clipboard."""
        if hasattr(self, "_context_menu_message"):
            QApplication.clipboard().setText(self._context_menu_message)

    @Slot()
    def _on_copy_row(self) -> None:
        """Copy context menu row to clipboard."""
        if hasattr(self, "_context_menu_row"):
            self._copy_row(self._context_menu_row)

    @Slot()
    def _on_navigate_to_node(self) -> None:
        """Navigate to node from context menu."""
        if hasattr(self, "_context_menu_node_id") and self._context_menu_node_id:
            self.navigate_to_node.emit(self._context_menu_node_id)

    def _copy_row(self, row: int) -> None:
        """Copy a log row to clipboard."""
        parts = []
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                parts.append(item.text())
        QApplication.clipboard().setText("\t".join(parts))

    @Slot()
    def _on_export(self) -> None:
        """Export log to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Log",
            f"execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    # Write header
                    f.write("Time\tLevel\tNode\tMessage\n")
                    f.write("-" * TOKENS_V2.sizes.button_min_width + "\n")

                    # Write entries
                    for row in range(self._table.rowCount()):
                        time_item = self._table.item(row, self.COL_TIME)
                        level_item = self._table.item(row, self.COL_LEVEL)
                        node_item = self._table.item(row, self.COL_NODE)
                        msg_item = self._table.item(row, self.COL_MESSAGE)

                        time_text = time_item.text() if time_item else ""
                        level_text = level_item.text() if level_item else ""
                        node_text = node_item.text() if node_item else ""
                        msg_text = msg_item.text() if msg_item else ""

                        f.write(f"{time_text}\t{level_text}\t{node_text}\t{msg_text}\n")

                logger.info(f"Exported log to {file_path}")

            except Exception as e:
                logger.error(f"Failed to export log: {e}")

    def _get_level_color(self, level: str) -> QColor:
        """Get color for log level using v2 theme colors."""
        colors = {
            "debug": QColor(THEME_V2.text_muted),
            "info": QColor(THEME_V2.info),
            "warning": QColor(THEME_V2.warning),
            "error": QColor(THEME_V2.error),
            "success": QColor(THEME_V2.success),
        }
        return colors.get(level.lower(), QColor(THEME_V2.text_primary))

    def _get_level_background(self, level: str) -> QColor:
        """Get subtle background color for log level using v2 theme."""
        colors = {
            "debug": QColor(THEME_V2.bg_surface),
            "info": QColor(THEME_V2.bg_surface),
            "warning": QColor(f"{THEME_V2.warning}20"),
            "error": QColor(f"{THEME_V2.error}20"),
            "success": QColor(f"{THEME_V2.success}20"),
        }
        return colors.get(level.lower(), QColor(THEME_V2.bg_surface))

    def _trim_log(self) -> None:
        """Trim log to max entries."""
        while self._table.rowCount() > self._max_entries:
            self._table.removeRow(0)

    def _update_display(self) -> None:
        """Update empty state vs table display."""
        if self._table.rowCount() == 0:
            self._content_stack.setCurrentIndex(0)  # Empty state
            self._count_label.setText("0 entries")
        else:
            self._content_stack.setCurrentIndex(1)  # Table
            self._apply_filter()  # Updates count label

    # ==================== Public API ====================

    def log_event(self, event: "DomainEvent") -> None:
        """
        Log an execution event.

        Args:
            event: Typed domain event to log
        """
        from casare_rpa.domain.events import (
            NodeCompleted,
            NodeFailed,
            NodeStarted,
            WorkflowCompleted,
            WorkflowFailed,
            WorkflowPaused,
            WorkflowResumed,
            WorkflowStarted,
            WorkflowStopped,
        )

        # Map event classes to log levels
        level_map = {
            WorkflowStarted: "info",
            WorkflowCompleted: "success",
            WorkflowFailed: "error",
            WorkflowStopped: "warning",
            WorkflowPaused: "warning",
            WorkflowResumed: "info",
            NodeStarted: "info",
            NodeCompleted: "success",
            NodeFailed: "error",
        }

        event_class = type(event)
        level = level_map.get(event_class, "info")
        message = event_class.__name__

        # Build data string from typed event attributes
        data_parts = []
        for attr in ["node_id", "workflow_id", "error_message", "execution_time_ms"]:
            if hasattr(event, attr):
                val = getattr(event, attr)
                if val is not None:
                    data_parts.append(f"{attr}={val}")

        if data_parts:
            message += f": {', '.join(data_parts)}"

        # Get node_id from typed event
        node_id = getattr(event, "node_id", None)

        self.log_message(message, level, node_id)

    def _is_tab_visible(self) -> bool:
        """
        Check if this tab is currently visible.

        PERFORMANCE: Used for lazy updates - defer expensive table updates
        when user isn't looking at this tab.
        """
        # Check if tab is hidden or parent dock is collapsed
        if not self.isVisible():
            return False

        # Check if our tab is the currently selected one in the tab widget
        parent = self.parent()
        while parent:
            if hasattr(parent, "currentWidget"):
                return parent.currentWidget() == self
            parent = parent.parent()

        return True

    def _flush_deferred_logs(self) -> None:
        """Flush all deferred log entries to the table."""
        if not self._deferred_logs:
            return

        # Batch insert all deferred logs
        for log_entry in self._deferred_logs:
            self._add_log_entry_to_table(*log_entry)

        self._deferred_logs.clear()
        logger.debug(f"Flushed {len(self._deferred_logs)} deferred log entries")

    def showEvent(self, event) -> None:
        """Handle tab becoming visible - flush deferred updates."""
        super().showEvent(event)
        if self._deferred_logs:
            self._flush_deferred_logs()

    def log_message(self, message: str, level: str = "info", node_id: str | None = None) -> None:
        """
        Log a custom message.

        PERFORMANCE: Uses lazy updates - defers table updates when tab
        is not visible to reduce CPU during workflow execution.

        Args:
            message: Message text
            level: Log level (debug, info, warning, error, success)
            node_id: Optional associated node ID
        """
        # PERFORMANCE: Defer updates when tab not visible
        is_visible = self._is_tab_visible()

        if not is_visible and len(self._deferred_logs) < self.MAX_DEFERRED:
            # Defer this log entry
            self._deferred_logs.append((message, level, node_id))
            return

        # Flush any deferred logs first if we're now visible
        if is_visible and self._deferred_logs:
            self._flush_deferred_logs()

        # Add this entry directly
        self._add_log_entry_to_table(message, level, node_id)

    def _add_log_entry_to_table(self, message: str, level: str, node_id: str | None) -> None:
        """Actually add a log entry to the table widget."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        time_item = QTableWidgetItem(timestamp)
        time_item.setForeground(QBrush(QColor(THEME_V2.text_muted)))

        # Level (with color-coded background)
        level_item = QTableWidgetItem(level.upper())
        level_color = self._get_level_color(level)
        level_item.setForeground(QBrush(level_color))
        level_item.setToolTip(f"Log level: {level.title()}")

        # Node (clickable if has node_id)
        node_display = ""
        if node_id:
            node_display = node_id[:12] + "..." if len(node_id) > 15 else node_id
        node_item = QTableWidgetItem(node_display)
        node_item.setData(Qt.ItemDataRole.UserRole, node_id)
        if node_id:
            node_item.setForeground(QBrush(QColor(THEME_V2.primary)))
            node_item.setToolTip(f"Node: {node_id}\nDouble-click to navigate")

        # Message (colored by level)
        msg_item = QTableWidgetItem(message)
        msg_item.setForeground(QBrush(level_color))
        msg_item.setToolTip(message)  # Show full message on hover

        self._table.setItem(row, self.COL_TIME, time_item)
        self._table.setItem(row, self.COL_LEVEL, level_item)
        self._table.setItem(row, self.COL_NODE, node_item)
        self._table.setItem(row, self.COL_MESSAGE, msg_item)

        # Apply filter to new row
        if self._current_filter != "All" and level.upper() != self._current_filter.upper():
            self._table.setRowHidden(row, True)

        # Update display state
        self._update_display()

        # Auto-scroll
        if self._auto_scroll:
            self._table.scrollToBottom()

        # Trim if needed
        self._trim_log()

    @Slot()
    def clear(self) -> None:
        """Clear the log."""
        self._table.setRowCount(0)
        self._update_display()

    def get_entry_count(self) -> int:
        """Get the number of log entries."""
        return self._table.rowCount()

    def set_max_entries(self, max_entries: int) -> None:
        """Set maximum number of log entries."""
        self._max_entries = max_entries
        self._trim_log()
