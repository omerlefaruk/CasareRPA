"""
Robots view for CasareRPA Orchestrator.
Displays robot list, status, and management.
"""

import asyncio
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QMessageBox,
    QMenu,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal

from ..styles import COLORS
from ..widgets import SearchBar, ActionButton, SectionHeader, StatusBadge, EmptyState
from ..models import Robot, RobotStatus
from ..services import OrchestratorService


class RobotDetailsDialog(QDialog):
    """Dialog showing robot details."""

    def __init__(self, robot: Robot, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Robot: {robot.name}")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Info rows
        info_layout = QFormLayout()
        info_layout.setSpacing(12)

        info_layout.addRow("ID:", QLabel(robot.id))
        info_layout.addRow("Name:", QLabel(robot.name))

        status_badge = StatusBadge(robot.status.value)
        info_layout.addRow("Status:", status_badge)

        info_layout.addRow("Environment:", QLabel(robot.environment))
        info_layout.addRow(
            "Max Concurrent Jobs:", QLabel(str(robot.max_concurrent_jobs))
        )
        info_layout.addRow("Current Jobs:", QLabel(str(robot.current_jobs)))
        info_layout.addRow(
            "Last Seen:", QLabel(str(robot.last_seen) if robot.last_seen else "Never")
        )

        if robot.tags:
            info_layout.addRow("Tags:", QLabel(", ".join(robot.tags)))

        layout.addLayout(info_layout)

        # Metrics section
        if robot.metrics:
            metrics_label = QLabel("Metrics")
            metrics_label.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-weight: 600;"
            )
            layout.addWidget(metrics_label)

            for key, value in robot.metrics.items():
                row = QHBoxLayout()
                row.addWidget(QLabel(key.replace("_", " ").title()))
                row.addWidget(QLabel(str(value)))
                layout.addLayout(row)

        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class RobotsView(QWidget):
    """Robots management view."""

    dispatch_requested = Signal(str)  # robot_id

    def __init__(self, service: OrchestratorService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._service = service
        self._robots: List[Robot] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = SectionHeader("Robots", "Refresh")
        header.action_clicked.connect(
            lambda: asyncio.get_event_loop().create_task(self.refresh())
        )
        layout.addWidget(header)

        # Search and filters
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search = SearchBar(
            "Search robots...", filters=["All", "Online", "Offline", "Busy", "Error"]
        )
        self._search.search_changed.connect(self._apply_filter)
        self._search.filter_changed.connect(self._apply_filter)
        toolbar.addWidget(self._search)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Robots table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Status", "Name", "ID", "Environment", "Jobs", "Last Seen", "Actions"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(0, 100)
        self._table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(6, 150)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Empty state (hidden by default)
        self._empty_state = EmptyState(
            title="No Robots Found",
            description="No robots are currently registered. Start a Robot agent to see it here.",
        )
        self._empty_state.hide()
        layout.addWidget(self._empty_state)

    def _apply_filter(self):
        """Apply search and filter to table."""
        search_text = self._search.get_search_text().lower()
        filter_status = self._search.get_filter()

        for row in range(self._table.rowCount()):
            show = True

            # Check status filter
            if filter_status and filter_status != "All":
                status_item = self._table.cellWidget(row, 0)
                if status_item:
                    status_text = status_item.text().lower()
                    if filter_status.lower() != status_text:
                        show = False

            # Check search text
            if show and search_text:
                row_text = ""
                for col in range(self._table.columnCount()):
                    item = self._table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                if search_text not in row_text:
                    show = False

            self._table.setRowHidden(row, not show)

    def _show_context_menu(self, pos):
        """Show context menu for robot row."""
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._robots):
            return

        robot = self._robots[row]
        menu = QMenu(self)

        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self._show_details(robot))

        dispatch_action = menu.addAction("Dispatch Workflow")
        dispatch_action.triggered.connect(
            lambda: self.dispatch_requested.emit(robot.id)
        )
        dispatch_action.setEnabled(robot.is_available)

        menu.addSeparator()

        if robot.status == RobotStatus.ONLINE:
            # Could add maintenance mode toggle, etc.
            pass

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, row: int, col: int):
        """Handle double-click on table row."""
        if 0 <= row < len(self._robots):
            self._show_details(self._robots[row])

    def _show_details(self, robot: Robot):
        """Show robot details dialog."""
        dialog = RobotDetailsDialog(robot, self)
        dialog.exec()

    def _update_table(self):
        """Update the table with current robots."""
        self._table.setRowCount(len(self._robots))

        if not self._robots:
            self._table.hide()
            self._empty_state.show()
            return

        self._table.show()
        self._empty_state.hide()

        for row, robot in enumerate(self._robots):
            # Status badge
            status_badge = StatusBadge(robot.status.value)
            self._table.setCellWidget(row, 0, status_badge)

            # Name
            self._table.setItem(row, 1, QTableWidgetItem(robot.name))

            # ID (truncated)
            id_text = robot.id[:8] + "..." if len(robot.id) > 8 else robot.id
            self._table.setItem(row, 2, QTableWidgetItem(id_text))

            # Environment
            self._table.setItem(row, 3, QTableWidgetItem(robot.environment))

            # Jobs
            jobs_text = f"{robot.current_jobs}/{robot.max_concurrent_jobs}"
            self._table.setItem(row, 4, QTableWidgetItem(jobs_text))

            # Last seen
            last_seen = str(robot.last_seen)[:19] if robot.last_seen else "Never"
            self._table.setItem(row, 5, QTableWidgetItem(last_seen))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            dispatch_btn = ActionButton("Dispatch", primary=True)
            dispatch_btn.setEnabled(robot.is_available)
            dispatch_btn.clicked.connect(
                lambda checked, r=robot: self.dispatch_requested.emit(r.id)
            )
            actions_layout.addWidget(dispatch_btn)

            self._table.setCellWidget(row, 6, actions_widget)

    async def refresh(self):
        """Refresh robots data."""
        try:
            self._robots = await self._service.get_robots()
            self._update_table()
        except Exception as e:
            from loguru import logger

            logger.error(f"Failed to refresh robots: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load robots: {e}")
