"""
Log Tab for the Bottom Panel.

Provides real-time execution log display with filtering and navigation.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QComboBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from loguru import logger

if TYPE_CHECKING:
    from ...core.events import Event


class LogTab(QWidget):
    """
    Log tab widget for displaying execution logs.

    Features:
    - Filter by log level
    - Click to navigate to node
    - Auto-scroll toggle
    - Export to file

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
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Filter dropdown
        filter_label = QLabel("Filter:")
        self._filter_combo = QComboBox()
        self._filter_combo.setFixedSize(70, 16)
        self._filter_combo.addItems(["All", "Info", "Warning", "Error", "Success"])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)

        # Auto-scroll toggle
        self._auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.setFixedSize(80, 16)
        self._auto_scroll_btn.clicked.connect(self._on_auto_scroll_toggled)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(40, 16)
        clear_btn.clicked.connect(self.clear)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.setFixedSize(45, 16)
        export_btn.clicked.connect(self._on_export)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addStretch()
        toolbar.addWidget(self._auto_scroll_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addWidget(export_btn)

        layout.addLayout(toolbar)

        # Log table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Time", "Level", "Node", "Message"])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.itemDoubleClicked.connect(self._on_double_click)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(
            self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_NODE, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        from ..theme import THEME

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                gridline-color: {THEME.border_dark};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }}
            QTableWidget::item {{
                padding: 2px 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_header};
                color: {THEME.text_header};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
                border-radius: 2px;
                padding: 0px 2px;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
            QPushButton:checked {{
                background-color: {THEME.accent_primary};
            }}
            QComboBox {{
                background-color: {THEME.bg_light};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
                border-radius: 2px;
                padding: 0px 2px;
                font-size: 9px;
            }}
            QLabel {{
                color: {THEME.text_secondary};
            }}
        """)

    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle filter change."""
        self._current_filter = filter_text
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current filter to table rows."""
        for row in range(self._table.rowCount()):
            level_item = self._table.item(row, self.COL_LEVEL)
            if level_item:
                level = level_item.text().upper()
                if self._current_filter == "All":
                    self._table.setRowHidden(row, False)
                else:
                    self._table.setRowHidden(row, level != self._current_filter.upper())

    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        """Handle auto-scroll toggle."""
        self._auto_scroll = checked
        self._auto_scroll_btn.setText(f"Auto-scroll: {'ON' if checked else 'OFF'}")

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on log entry."""
        row = item.row()
        node_item = self._table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)

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
        from ..theme import THEME

        colors = {
            "info": QColor(THEME.status_info),
            "warning": QColor(THEME.status_warning),
            "error": QColor(THEME.status_error),
            "success": QColor(THEME.status_success),
        }
        return colors.get(level.lower(), QColor(THEME.text_primary))

    def _trim_log(self) -> None:
        """Trim log to max entries."""
        while self._table.rowCount() > self._max_entries:
            self._table.removeRow(0)

    # ==================== Public API ====================

    def log_event(self, event: "Event") -> None:
        """
        Log an execution event.

        Args:
            event: Event to log
        """
        from ...core.events import EventType

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
            level: Log level (info, warning, error, success)
            node_id: Optional associated node ID
        """
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Time
        from ..theme import THEME

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        time_item = QTableWidgetItem(timestamp)
        time_item.setForeground(QBrush(QColor(THEME.text_muted)))

        # Level
        level_item = QTableWidgetItem(level.upper())
        level_color = self._get_level_color(level)
        level_item.setForeground(QBrush(level_color))

        # Node
        node_item = QTableWidgetItem(
            node_id[:12] + "..." if node_id and len(node_id) > 15 else node_id or ""
        )
        node_item.setData(Qt.ItemDataRole.UserRole, node_id)
        if node_id:
            node_item.setForeground(QBrush(QColor(THEME.accent_primary)))

        # Message
        msg_item = QTableWidgetItem(message)
        msg_item.setForeground(QBrush(level_color))

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

        # Auto-scroll
        if self._auto_scroll:
            self._table.scrollToBottom()

        # Trim if needed
        self._trim_log()

    def clear(self) -> None:
        """Clear the log."""
        self._table.setRowCount(0)

    def get_entry_count(self) -> int:
        """Get the number of log entries."""
        return self._table.rowCount()

    def set_max_entries(self, max_entries: int) -> None:
        """Set maximum number of log entries."""
        self._max_entries = max_entries
        self._trim_log()
