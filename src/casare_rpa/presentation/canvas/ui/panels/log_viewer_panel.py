"""
Log Viewer Panel for Robot Log Streaming.

Provides real-time log display from remote robots with filtering,
searching, and export capabilities. Connects to orchestrator via
WebSocket for live streaming.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import (

    THEME,
)


class LogStreamWorker(QObject):
    """Worker for WebSocket log streaming in background thread."""

    log_received = Signal(dict)
    connected = Signal()
    disconnected = Signal()
    error = Signal(str)

    def __init__(
        self,
        orchestrator_url: str,
        api_secret: str,
        robot_id: str | None = None,
        tenant_id: str | None = None,
        min_level: str = "DEBUG",
    ) -> None:
        """Initialize worker with connection parameters."""
        super().__init__()
        self.orchestrator_url = orchestrator_url
        self.api_secret = api_secret
        self.robot_id = robot_id
        self.tenant_id = tenant_id
        self.min_level = min_level
        self._running = False
        self._ws = None

    def run(self) -> None:
        """Run the WebSocket connection loop."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._connect_loop())
        finally:
            loop.close()

    async def _connect_loop(self) -> None:
        """Main connection loop with reconnection."""
        self._running = True

        while self._running:
            try:
                await self._connect()
            except Exception as e:
                if self._running:
                    self.error.emit(str(e))
                    await asyncio.sleep(5)  # Reconnect delay

    async def _connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            import websockets

            # Build URL
            if self.robot_id:
                url = f"{self.orchestrator_url}/ws/logs/{self.robot_id}"
            else:
                url = f"{self.orchestrator_url}/ws/logs"

            params = [f"api_secret={self.api_secret}", f"min_level={self.min_level}"]
            if self.tenant_id:
                params.append(f"tenant_id={self.tenant_id}")

            full_url = f"{url}?{'&'.join(params)}"

            async with websockets.connect(full_url) as ws:
                self._ws = ws
                self.connected.emit()

                while self._running:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=30)
                        data = json.loads(message)
                        self.log_received.emit(data)
                    except TimeoutError:
                        # Send ping
                        await ws.send("ping")
                    except Exception:
                        if self._running:
                            raise

        except Exception:
            self.disconnected.emit()
            raise

    def stop(self) -> None:
        """Stop the worker."""
        self._running = False


class LogViewerPanel(QDockWidget):
    """
    Dockable panel for viewing robot logs.

    Features:
    - Real-time log display with auto-scroll
    - Level filtering (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Text search/filter
    - Robot selector
    - Export to file
    - Connection status indicator

    Signals:
        robot_selected: Emitted when robot is selected (str: robot_id)
    """

    robot_selected = Signal(str)

    # Table columns
    COL_TIME = 0
    COL_LEVEL = 1
    COL_ROBOT = 2
    COL_SOURCE = 3
    COL_MESSAGE = 4

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the log viewer panel."""
        super().__init__("Log Viewer", parent)
        self.setObjectName("LogViewerDock")

        # Connection state
        self._orchestrator_url: str | None = None
        self._api_secret: str | None = None
        self._current_robot: str | None = None
        self._current_tenant: str | None = None

        # Worker thread
        self._thread: QThread | None = None
        self._worker: LogStreamWorker | None = None

        # Log buffer
        self._max_entries = 5000
        self._auto_scroll = True
        self._paused = False

        # Filters
        self._level_filter = "All"
        self._search_text = ""

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("LogViewerPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumHeight(200)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Connection settings group
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)
        conn_layout.setSpacing(8)

        # Robot selector
        robot_label = QLabel("Robot:")
        self._robot_combo = QComboBox()
        self._robot_combo.setMinimumWidth(150)
        self._robot_combo.addItem("All Robots", None)
        self._robot_combo.currentIndexChanged.connect(self._on_robot_changed)

        # Tenant ID
        tenant_label = QLabel("Tenant:")
        self._tenant_edit = QLineEdit()
        self._tenant_edit.setPlaceholderText("tenant-id")
        self._tenant_edit.setMaximumWidth(150)

        # Connect button
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setFixedWidth(70)
        self._connect_btn.clicked.connect(self._toggle_connection)

        # Status indicator
        self._status_label = QLabel("Disconnected")
        self._status_label.setStyleSheet(f"color: {THEME.error};")

        conn_layout.addWidget(robot_label)
        conn_layout.addWidget(self._robot_combo)
        conn_layout.addWidget(tenant_label)
        conn_layout.addWidget(self._tenant_edit)
        conn_layout.addWidget(self._connect_btn)
        conn_layout.addWidget(self._status_label)
        conn_layout.addStretch()

        main_layout.addWidget(conn_group)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Level filter
        level_label = QLabel("Level:")
        self._level_combo = QComboBox()
        self._level_combo.setFixedWidth(80)
        self._level_combo.addItems(
            ["All", "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        self._level_combo.currentTextChanged.connect(self._on_level_changed)

        # Search
        search_label = QLabel("Search:")
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter by text...")
        self._search_edit.setMaximumWidth(200)
        self._search_edit.textChanged.connect(self._on_search_changed)

        # Search button
        search_btn = QPushButton("Filter")
        search_btn.setFixedWidth(50)
        search_btn.clicked.connect(self._apply_filters)

        toolbar.addWidget(level_label)
        toolbar.addWidget(self._level_combo)
        toolbar.addWidget(search_label)
        toolbar.addWidget(self._search_edit)
        toolbar.addWidget(search_btn)
        toolbar.addStretch()

        # Auto-scroll toggle
        self._auto_scroll_cb = QCheckBox("Auto-scroll")
        self._auto_scroll_cb.setChecked(True)
        self._auto_scroll_cb.stateChanged.connect(self._on_auto_scroll_changed)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(50)
        clear_btn.clicked.connect(self.clear)

        # Pause button
        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setFixedWidth(50)
        self._pause_btn.setCheckable(True)
        self._pause_btn.clicked.connect(self._on_pause_clicked)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.setFixedWidth(50)
        export_btn.clicked.connect(self._on_export)

        toolbar.addWidget(self._auto_scroll_cb)
        toolbar.addWidget(clear_btn)
        toolbar.addWidget(self._pause_btn)
        toolbar.addWidget(export_btn)

        main_layout.addLayout(toolbar)

        # Log table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Time", "Level", "Robot", "Source", "Message"])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_ROBOT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_SOURCE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

        main_layout.addWidget(self._table)

        # Status bar
        status_bar = QHBoxLayout()
        self._entry_count_label = QLabel("0 entries")
        self._buffer_label = QLabel(f"Buffer: 0/{self._max_entries}")

        status_bar.addWidget(self._entry_count_label)
        status_bar.addStretch()
        status_bar.addWidget(self._buffer_label)

        main_layout.addLayout(status_bar)

        self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply dark theme styling using theme tokens."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background: {THEME.bg_surface};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background: {THEME.bg_component};
                padding: {TOKENS.spacing.xxs}px;
            }}
            QGroupBox {{
                background: {THEME.bg_component};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                margin-top: {TOKENS.spacing.xxs}px;
                padding-top: {TOKENS.spacing.xxs}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS.spacing.xxs}px;
                padding: 0 {SPACING.xxs}px;
            }}
            QTableWidget {{
                background-color: {THEME.bg_canvas};
                alternate-background-color: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                gridline-color: {THEME.border};
                color: {THEME.text_primary};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: {TOKENS.typography.caption}px;
            }}
            QTableWidget::item {{
                padding: {SPACING.xxs}px {TOKENS.spacing.xxs}px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.primary};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_component};
                color: {THEME.text_primary};
                border: none;
                border-right: 1px solid {THEME.border};
                border-bottom: 1px solid {THEME.border};
                padding: {TOKENS.spacing.xxs}px;
            }}
            QPushButton {{
                background-color: {THEME.bg_component};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.xxs}px;
                border-radius: {TOKENS.radius.sm}px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
            QPushButton:pressed {{
                background-color: {THEME.bg_hover};
            }}
            QPushButton:checked {{
                background-color: {THEME.primary};
            }}
            QComboBox {{
                background-color: {THEME.bg_component};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: {TOKENS.spacing.xxs}px;
                border-radius: {TOKENS.radius.sm}px;
            }}
            QLineEdit {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: {TOKENS.spacing.xxs}px;
                border-radius: {TOKENS.radius.sm}px;
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
            }}
        """)

    def configure(
        self,
        orchestrator_url: str,
        api_secret: str,
        tenant_id: str | None = None,
    ) -> None:
        """
        Configure connection settings.

        Args:
            orchestrator_url: Orchestrator WebSocket URL (ws:// or wss://).
            api_secret: Admin API secret for authentication.
            tenant_id: Optional tenant ID.
        """
        # Convert http to ws if needed
        if orchestrator_url.startswith("http://"):
            orchestrator_url = orchestrator_url.replace("http://", "ws://")
        elif orchestrator_url.startswith("https://"):
            orchestrator_url = orchestrator_url.replace("https://", "wss://")

        self._orchestrator_url = orchestrator_url.rstrip("/")
        self._api_secret = api_secret

        if tenant_id:
            self._tenant_edit.setText(tenant_id)
            self._current_tenant = tenant_id

    def add_robot(self, robot_id: str, robot_name: str) -> None:
        """
        Add a robot to the selector.

        Args:
            robot_id: Robot UUID.
            robot_name: Display name.
        """
        self._robot_combo.addItem(f"{robot_name} ({robot_id[:8]})", robot_id)

    def clear_robots(self) -> None:
        """Clear robot selector except 'All Robots'."""
        self._robot_combo.clear()
        self._robot_combo.addItem("All Robots", None)

    def _on_robot_changed(self, index: int) -> None:
        """Handle robot selection change."""
        robot_id = self._robot_combo.currentData()
        self._current_robot = robot_id

        if robot_id:
            self.robot_selected.emit(robot_id)

        # Reconnect with new filter if connected
        if self._worker is not None:
            self._disconnect()
            self._connect()

    def _on_level_changed(self, level: str) -> None:
        """Handle level filter change."""
        self._level_filter = level
        self._apply_filters()

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._search_text = text

    def _on_auto_scroll_changed(self, state: int) -> None:
        """Handle auto-scroll checkbox change."""
        self._auto_scroll = state == Qt.CheckState.Checked.value

    def _on_pause_clicked(self, checked: bool) -> None:
        """Handle pause button click."""
        self._paused = checked
        self._pause_btn.setText("Resume" if checked else "Pause")

    def _toggle_connection(self) -> None:
        """Toggle WebSocket connection."""
        if self._worker is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self) -> None:
        """Establish WebSocket connection."""
        if not self._orchestrator_url or not self._api_secret:
            logger.warning("Orchestrator URL and API secret required")
            return

        # Get tenant ID
        tenant_id = self._tenant_edit.text().strip() or None
        self._current_tenant = tenant_id

        # Get level filter
        min_level = self._level_combo.currentText()
        if min_level == "All":
            min_level = "DEBUG"

        # Clean up any existing connection
        self._disconnect()

        # Create worker and thread
        self._thread = QThread()
        self._worker = LogStreamWorker(
            orchestrator_url=self._orchestrator_url,
            api_secret=self._api_secret,
            robot_id=self._current_robot,
            tenant_id=tenant_id,
            min_level=min_level,
        )
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.log_received.connect(self._on_log_received)
        self._worker.connected.connect(self._on_connected)
        self._worker.disconnected.connect(self._on_disconnected)
        self._worker.error.connect(self._on_error)

        # Start
        self._thread.start()
        self._connect_btn.setText("Disconnect")

    def _disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)
            self._thread = None

        self._connect_btn.setText("Connect")
        self._status_label.setText("Disconnected")
        self._status_label.setStyleSheet(f"color: {THEME.error};")

    def _on_connected(self) -> None:
        """Handle connection established."""
        self._status_label.setText("Connected")
        self._status_label.setStyleSheet(f"color: {THEME.success};")
        logger.info("Log viewer connected to orchestrator")

    def _on_disconnected(self) -> None:
        """Handle connection lost."""
        self._status_label.setText("Disconnected")
        self._status_label.setStyleSheet(f"color: {THEME.error};")
        logger.info("Log viewer disconnected from orchestrator")

    def _on_error(self, error_msg: str) -> None:
        """Handle connection error."""
        self._status_label.setText(f"Error: {error_msg[:30]}")
        self._status_label.setStyleSheet(f"color: {THEME.error};")
        logger.error(f"Log viewer error: {error_msg}")

    def _on_log_received(self, data: dict[str, Any]) -> None:
        """Handle received log entry."""
        if self._paused:
            return

        msg_type = data.get("type", "")

        if msg_type == "log_entry":
            self._add_log_entry(data)

    def _add_log_entry(self, data: dict[str, Any]) -> None:
        """Add a log entry to the table."""
        # Parse timestamp
        timestamp_str = data.get("timestamp", "")
        try:
            if timestamp_str:
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                ts = datetime.fromisoformat(timestamp_str)
                time_text = ts.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_text = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        except Exception:
            time_text = timestamp_str[:12] if timestamp_str else ""

        level = data.get("level", "INFO")
        robot_id = data.get("robot_id", "")
        source = data.get("source", "")
        message = data.get("message", "")

        # Check filters
        if self._level_filter != "All" and level != self._level_filter:
            return
        if self._search_text and self._search_text.lower() not in message.lower():
            return

        # Add row
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Time
        time_item = QTableWidgetItem(time_text)
        time_item.setForeground(QBrush(QColor(THEME.text_muted)))

        # Level
        level_item = QTableWidgetItem(level)
        level_item.setForeground(QBrush(self._get_level_color(level)))

        # Robot
        robot_short = robot_id[:8] if robot_id else ""
        robot_item = QTableWidgetItem(robot_short)
        robot_item.setToolTip(robot_id)
        robot_item.setForeground(QBrush(QColor(THEME.primary)))

        # Source
        source_item = QTableWidgetItem(source or "")
        source_item.setForeground(QBrush(QColor(THEME.syntax_string)))

        # Message
        msg_item = QTableWidgetItem(message)
        msg_item.setForeground(QBrush(self._get_level_color(level)))

        self._table.setItem(row, self.COL_TIME, time_item)
        self._table.setItem(row, self.COL_LEVEL, level_item)
        self._table.setItem(row, self.COL_ROBOT, robot_item)
        self._table.setItem(row, self.COL_SOURCE, source_item)
        self._table.setItem(row, self.COL_MESSAGE, msg_item)

        # Trim buffer
        while self._table.rowCount() > self._max_entries:
            self._table.removeRow(0)

        # Update labels
        self._entry_count_label.setText(f"{self._table.rowCount()} entries")
        self._buffer_label.setText(f"Buffer: {self._table.rowCount()}/{self._max_entries}")

        # Auto-scroll
        if self._auto_scroll:
            self._table.scrollToBottom()

    def _get_level_color(self, level: str) -> QColor:
        """Get color for log level using theme tokens."""
        colors = {
            "TRACE": QColor(THEME.text_muted),
            "DEBUG": QColor(THEME.text_muted),
            "INFO": QColor(THEME.success),
            "WARNING": QColor(THEME.warning),
            "ERROR": QColor(THEME.error),
            "CRITICAL": QColor(THEME.error),
        }
        return colors.get(level.upper(), QColor(THEME.text_primary))

    def _apply_filters(self) -> None:
        """Apply current filters to all rows."""
        search_lower = self._search_text.lower()

        for row in range(self._table.rowCount()):
            level_item = self._table.item(row, self.COL_LEVEL)
            msg_item = self._table.item(row, self.COL_MESSAGE)

            level = level_item.text() if level_item else ""
            message = msg_item.text() if msg_item else ""

            # Check level filter
            level_match = self._level_filter == "All" or level == self._level_filter

            # Check search filter
            search_match = not search_lower or search_lower in message.lower()

            self._table.setRowHidden(row, not (level_match and search_match))

    def _on_export(self) -> None:
        """Export logs to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"robot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    # Write header
                    f.write("Time\tLevel\tRobot\tSource\tMessage\n")
                    f.write("-" * 100 + "\n")

                    # Write visible entries
                    for row in range(self._table.rowCount()):
                        if self._table.isRowHidden(row):
                            continue

                        cols = []
                        for col in range(5):
                            item = self._table.item(row, col)
                            cols.append(item.text() if item else "")

                        f.write("\t".join(cols) + "\n")

                logger.info(f"Exported logs to {file_path}")

            except Exception as e:
                logger.error(f"Failed to export logs: {e}")

    def clear(self) -> None:
        """Clear the log table."""
        self._table.setRowCount(0)
        self._entry_count_label.setText("0 entries")
        self._buffer_label.setText(f"Buffer: 0/{self._max_entries}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self._disconnect()
        logger.debug("LogViewerPanel cleaned up")


__all__ = ["LogViewerPanel"]
