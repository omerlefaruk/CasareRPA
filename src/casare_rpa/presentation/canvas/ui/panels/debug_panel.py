"""
Debug Panel UI Component.

Provides debug output, execution logs, and breakpoint management.
Combines functionality from LogTab and OutputTab for comprehensive debugging.
"""

from typing import Optional, Any, Dict, List
from datetime import datetime

from PySide6.QtWidgets import (
    QDockWidget,
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
    QTabWidget,
    QTextEdit,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from loguru import logger


class DebugPanel(QDockWidget):
    """
    Dockable debug panel for workflow debugging.

    Features:
    - Execution logs with filtering
    - Breakpoint list
    - Variable inspector
    - Output console

    Signals:
        navigate_to_node: Emitted when user requests to navigate to node (str: node_id)
        breakpoint_toggled: Emitted when breakpoint is toggled (str: node_id, bool: enabled)
        clear_requested: Emitted when user requests to clear logs
    """

    navigate_to_node = Signal(str)
    breakpoint_toggled = Signal(str, bool)
    clear_requested = Signal()

    # Log table columns
    COL_TIME = 0
    COL_LEVEL = 1
    COL_NODE = 2
    COL_MESSAGE = 3

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the debug panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Debug", parent)
        self.setObjectName("DebugDock")

        self._auto_scroll = True
        self._current_filter = "All"
        self._max_log_entries = 1000

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("DebugPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumHeight(150)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab widget for different debug views
        self._tabs = QTabWidget()

        # Logs tab
        logs_tab = self._create_logs_tab()
        self._tabs.addTab(logs_tab, "Logs")

        # Console tab
        console_tab = self._create_console_tab()
        self._tabs.addTab(console_tab, "Console")

        # Breakpoints tab
        breakpoints_tab = self._create_breakpoints_tab()
        self._tabs.addTab(breakpoints_tab, "Breakpoints")

        main_layout.addWidget(self._tabs)
        self.setWidget(container)

    def _create_logs_tab(self) -> QWidget:
        """
        Create the logs tab.

        Returns:
            Logs tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Filter dropdown
        filter_label = QLabel("Filter:")
        self._filter_combo = QComboBox()
        self._filter_combo.setFixedWidth(80)
        self._filter_combo.addItems(["All", "Info", "Warning", "Error", "Success"])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)

        # Auto-scroll toggle
        self._auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.setFixedWidth(100)
        self._auto_scroll_btn.clicked.connect(self._on_auto_scroll_toggled)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear_logs)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addStretch()
        toolbar.addWidget(self._auto_scroll_btn)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # Log table
        self._log_table = QTableWidget()
        self._log_table.setColumnCount(4)
        self._log_table.setHorizontalHeaderLabels(["Time", "Level", "Node", "Message"])

        # Configure table
        self._log_table.setAlternatingRowColors(True)
        self._log_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._log_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._log_table.itemDoubleClicked.connect(self._on_log_double_click)
        self._log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Configure column sizing
        header = self._log_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_NODE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._log_table)

        return widget

    def _create_console_tab(self) -> QWidget:
        """
        Create the console tab for execution output.

        Returns:
            Console tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Console text area
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #3d3d3d;
            }
        """)

        # Toolbar
        toolbar = QHBoxLayout()
        clear_console_btn = QPushButton("Clear Console")
        clear_console_btn.setFixedWidth(100)
        clear_console_btn.clicked.connect(self._console.clear)
        toolbar.addStretch()
        toolbar.addWidget(clear_console_btn)

        layout.addLayout(toolbar)
        layout.addWidget(self._console)

        return widget

    def _create_breakpoints_tab(self) -> QWidget:
        """
        Create the breakpoints tab.

        Returns:
            Breakpoints tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        toolbar = QHBoxLayout()
        clear_bp_btn = QPushButton("Clear All Breakpoints")
        clear_bp_btn.setFixedWidth(150)
        clear_bp_btn.clicked.connect(self._on_clear_breakpoints)
        toolbar.addStretch()
        toolbar.addWidget(clear_bp_btn)
        layout.addLayout(toolbar)

        # Breakpoints table
        self._bp_table = QTableWidget()
        self._bp_table.setColumnCount(3)
        self._bp_table.setHorizontalHeaderLabels(["Node ID", "Node Name", "Enabled"])
        self._bp_table.setAlternatingRowColors(True)
        self._bp_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._bp_table.itemDoubleClicked.connect(self._on_bp_double_click)

        # Configure column sizing
        header = self._bp_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._bp_table)

        return widget

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #252525;
                color: #e0e0e0;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #323232;
                border: 1px solid #4a4a4a;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #5a8a9a;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: none;
                border-right: 1px solid #4a4a4a;
                border-bottom: 1px solid #4a4a4a;
                padding: 4px;
            }
        """)

    def add_log(
        self,
        level: str,
        message: str,
        node_id: Optional[str] = None,
        node_name: Optional[str] = None,
    ) -> None:
        """
        Add a log entry.

        Args:
            level: Log level (Info, Warning, Error, Success)
            message: Log message
            node_id: Optional node ID
            node_name: Optional node name
        """
        # Check if we should display based on filter
        if self._current_filter != "All" and self._current_filter != level:
            return

        # Limit table size
        if self._log_table.rowCount() >= self._max_log_entries:
            self._log_table.removeRow(0)

        # Add row
        row = self._log_table.rowCount()
        self._log_table.insertRow(row)

        # Time
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        self._log_table.setItem(row, self.COL_TIME, time_item)

        # Level with color
        level_item = QTableWidgetItem(level)
        if level == "Error":
            level_item.setForeground(QBrush(QColor("#f44747")))
        elif level == "Warning":
            level_item.setForeground(QBrush(QColor("#cca700")))
        elif level == "Success":
            level_item.setForeground(QBrush(QColor("#89d185")))
        else:
            level_item.setForeground(QBrush(QColor("#d4d4d4")))
        self._log_table.setItem(row, self.COL_LEVEL, level_item)

        # Node
        node_text = node_name if node_name else (node_id[:12] if node_id else "-")
        node_item = QTableWidgetItem(node_text)
        if node_id:
            node_item.setData(Qt.ItemDataRole.UserRole, node_id)
        self._log_table.setItem(row, self.COL_NODE, node_item)

        # Message
        message_item = QTableWidgetItem(message)
        self._log_table.setItem(row, self.COL_MESSAGE, message_item)

        # Auto-scroll
        if self._auto_scroll:
            self._log_table.scrollToBottom()

    def add_console_output(self, text: str, color: str = "#d4d4d4") -> None:
        """
        Add text to console output.

        Args:
            text: Text to add
            color: HTML color for text
        """
        self._console.append(f'<span style="color: {color}">{text}</span>')
        if self._auto_scroll:
            self._console.moveCursor(self._console.textCursor().End)

    def add_breakpoint(self, node_id: str, node_name: str, enabled: bool = True) -> None:
        """
        Add a breakpoint to the list.

        Args:
            node_id: Node ID
            node_name: Node display name
            enabled: Whether breakpoint is enabled
        """
        row = self._bp_table.rowCount()
        self._bp_table.insertRow(row)

        id_item = QTableWidgetItem(node_id)
        id_item.setData(Qt.ItemDataRole.UserRole, node_id)
        self._bp_table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem(node_name)
        self._bp_table.setItem(row, 1, name_item)

        enabled_item = QTableWidgetItem("Yes" if enabled else "No")
        enabled_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
        self._bp_table.setItem(row, 2, enabled_item)

    def remove_breakpoint(self, node_id: str) -> None:
        """
        Remove a breakpoint from the list.

        Args:
            node_id: Node ID
        """
        for row in range(self._bp_table.rowCount()):
            item = self._bp_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == node_id:
                self._bp_table.removeRow(row)
                break

    def clear_logs(self) -> None:
        """Clear all log entries."""
        self._log_table.setRowCount(0)
        logger.debug("Logs cleared")

    def clear_console(self) -> None:
        """Clear console output."""
        self._console.clear()
        logger.debug("Console cleared")

    def clear_breakpoints(self) -> None:
        """Clear all breakpoints."""
        self._bp_table.setRowCount(0)
        logger.debug("Breakpoints cleared")

    def _on_filter_changed(self, filter_text: str) -> None:
        """
        Handle filter change.

        Args:
            filter_text: New filter text
        """
        self._current_filter = filter_text
        logger.debug(f"Log filter changed to: {filter_text}")

    def _on_auto_scroll_toggled(self) -> None:
        """Handle auto-scroll toggle."""
        self._auto_scroll = self._auto_scroll_btn.isChecked()
        self._auto_scroll_btn.setText(
            f"Auto-scroll: {'ON' if self._auto_scroll else 'OFF'}"
        )
        logger.debug(f"Auto-scroll: {self._auto_scroll}")

    def _on_log_double_click(self, item: QTableWidgetItem) -> None:
        """
        Handle log entry double-click.

        Args:
            item: Clicked table item
        """
        row = item.row()
        node_item = self._log_table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)
                logger.debug(f"Navigate to node: {node_id}")

    def _on_bp_double_click(self, item: QTableWidgetItem) -> None:
        """
        Handle breakpoint double-click.

        Args:
            item: Clicked table item
        """
        row = item.row()
        id_item = self._bp_table.item(row, 0)
        if id_item:
            node_id = id_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)
                logger.debug(f"Navigate to breakpoint node: {node_id}")

    def _on_clear_breakpoints(self) -> None:
        """Handle clear all breakpoints."""
        self.clear_breakpoints()
        self.clear_requested.emit()
