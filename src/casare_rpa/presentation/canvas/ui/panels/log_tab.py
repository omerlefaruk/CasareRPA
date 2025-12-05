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
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
    QStackedWidget,
    QComboBox,
    QApplication,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from loguru import logger

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    ToolbarButton,
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)

if TYPE_CHECKING:
    from casare_rpa.domain.events import Event


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

    Signals:
        navigate_to_node: Emitted when user wants to navigate to a node
    """

    navigate_to_node = Signal(str)  # node_id

    # Table columns
    COL_TIME = 0
    COL_LEVEL = 1
    COL_NODE = 2
    COL_MESSAGE = 3

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Log tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._auto_scroll = True
        self._current_filter = "All"
        self._max_entries = 1000

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
        toolbar.setContentsMargins(8, 6, 8, 6)
        toolbar.setSpacing(12)

        # Filter label and dropdown
        filter_label = QLabel("Level:")
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(
            ["All", "Debug", "Info", "Warning", "Error", "Success"]
        )
        self._filter_combo.setFixedWidth(90)
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self._filter_combo.setToolTip("Filter logs by level")

        # Entry count label
        self._count_label = QLabel("0 entries")
        self._count_label.setProperty("muted", True)

        # Auto-scroll toggle button
        self._auto_scroll_btn = ToolbarButton(
            text="Auto-scroll",
            tooltip="Toggle auto-scroll to latest log entry",
        )
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.clicked.connect(self._on_auto_scroll_toggled)
        self._auto_scroll_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.accent_primary};
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {THEME.accent_hover};
            }}
            QPushButton:!checked {{
                background-color: {THEME.bg_light};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
            }}
            QPushButton:!checked:hover {{
                background-color: {THEME.bg_hover};
            }}
        """)

        # Clear button
        clear_btn = ToolbarButton(
            text="Clear",
            tooltip="Clear all log entries",
        )
        clear_btn.clicked.connect(self.clear)

        # Export button
        export_btn = ToolbarButton(
            text="Export",
            tooltip="Export logs to file",
        )
        export_btn.clicked.connect(self._on_export)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addWidget(self._count_label)
        toolbar.addStretch()
        toolbar.addWidget(self._auto_scroll_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addWidget(export_btn)

        layout.addWidget(toolbar_widget)

        # Content area with stacked widget for empty state
        self._content_stack = QStackedWidget()

        # Empty state (index 0)
        self._empty_state = EmptyStateWidget(
            icon_text="",  # Scroll/log icon
            title="No Log Entries",
            description=(
                "Execution logs will appear here when:\n"
                "- You run a workflow (F3)\n"
                "- Nodes execute and emit events\n\n"
                "Double-click a log entry to navigate to its node."
            ),
        )
        self._content_stack.addWidget(self._empty_state)

        # Log table (index 1)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(8, 4, 8, 8)
        table_layout.setSpacing(0)

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
        header.setSectionResizeMode(
            self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_NODE, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

        # Set minimum column widths
        self._table.setColumnWidth(self.COL_NODE, 100)

        table_layout.addWidget(self._table)

        self._content_stack.addWidget(table_container)

        layout.addWidget(self._content_stack)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            LogTab, QWidget, QStackedWidget, QFrame {{
                background-color: {THEME.bg_panel};
            }}
            #logToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            {get_panel_table_stylesheet()}
            QTableWidget {{
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
        """)

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

    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        """Handle auto-scroll toggle."""
        self._auto_scroll = checked

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on log entry."""
        row = item.row()
        node_item = self._table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)

    def _on_context_menu(self, pos) -> None:
        """Show context menu for log entry."""
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

        # Copy message
        msg_item = self._table.item(row, self.COL_MESSAGE)
        if msg_item:
            copy_msg = menu.addAction("Copy Message")
            copy_msg.triggered.connect(
                lambda: QApplication.clipboard().setText(msg_item.text())
            )

        # Copy entire row
        copy_row = menu.addAction("Copy Log Entry")
        copy_row.triggered.connect(lambda: self._copy_row(row))

        # Navigate to node
        node_item = self._table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                menu.addSeparator()
                nav_action = menu.addAction("Go to Node")
                nav_action.triggered.connect(
                    lambda: self.navigate_to_node.emit(node_id)
                )

        menu.exec_(self._table.mapToGlobal(pos))

    def _copy_row(self, row: int) -> None:
        """Copy a log row to clipboard."""
        parts = []
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                parts.append(item.text())
        QApplication.clipboard().setText("\t".join(parts))

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
                    f.write("-" * 80 + "\n")

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
        """Get color for log level using VSCode Dark+ theme."""
        colors = {
            "debug": QColor(THEME.text_muted),
            "info": QColor(THEME.status_info),
            "warning": QColor(THEME.status_warning),
            "error": QColor(THEME.status_error),
            "success": QColor(THEME.status_success),
        }
        return colors.get(level.lower(), QColor(THEME.text_primary))

    def _get_level_background(self, level: str) -> QColor:
        """Get subtle background color for log level."""
        colors = {
            "debug": QColor(THEME.bg_panel),
            "info": QColor(THEME.bg_panel),
            "warning": QColor("#3d3a1a"),
            "error": QColor("#3d1a1a"),
            "success": QColor("#1a3d1a"),
        }
        return colors.get(level.lower(), QColor(THEME.bg_panel))

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

    def log_event(self, event: "Event") -> None:
        """
        Log an execution event.

        Args:
            event: Event to log
        """
        from casare_rpa.domain.events import EventType

        # Map event types to log levels
        level_map = {
            EventType.WORKFLOW_STARTED: "info",
            EventType.WORKFLOW_COMPLETED: "success",
            EventType.WORKFLOW_ERROR: "error",
            EventType.WORKFLOW_STOPPED: "warning",
            EventType.WORKFLOW_PAUSED: "warning",
            EventType.WORKFLOW_RESUMED: "info",
            EventType.NODE_STARTED: "info",
            EventType.NODE_COMPLETED: "success",
            EventType.NODE_ERROR: "error",
        }

        level = level_map.get(event.event_type, "info")
        message = event.event_type.name

        if event.data:
            data_str = ", ".join(f"{k}={v}" for k, v in event.data.items())
            message += f": {data_str}"

        self.log_message(message, level, event.node_id)

    def log_message(
        self, message: str, level: str = "info", node_id: Optional[str] = None
    ) -> None:
        """
        Log a custom message.

        Args:
            message: Message text
            level: Log level (debug, info, warning, error, success)
            node_id: Optional associated node ID
        """
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        time_item = QTableWidgetItem(timestamp)
        time_item.setForeground(QBrush(QColor(THEME.text_muted)))

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
            node_item.setForeground(QBrush(QColor(THEME.accent_primary)))
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
        if (
            self._current_filter != "All"
            and level.upper() != self._current_filter.upper()
        ):
            self._table.setRowHidden(row, True)

        # Update display state
        self._update_display()

        # Auto-scroll
        if self._auto_scroll:
            self._table.scrollToBottom()

        # Trim if needed
        self._trim_log()

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
