"""
Jobs Tab Widget for Fleet Dashboard.

Displays job queue and history with monitoring capabilities.
Supports real-time job updates with progress bars via WebSocketBridge.
"""

from functools import partial
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    JOB_STATUS_COLORS,
    TAB_WIDGET_BASE_STYLE,
)
from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon

if TYPE_CHECKING:
    pass


class JobsTabWidget(QWidget):
    """
    Widget for displaying and monitoring jobs.

    Features:
    - Job table with status, robot, workflow, timing
    - Status filter (pending, running, completed, failed)
    - Search by workflow name
    - Job details panel
    - Log viewer
    - Cancel/Retry actions

    Signals:
        job_selected: Emitted when job is selected (job_id)
        job_cancelled: Emitted when job is cancelled (job_id)
        job_retried: Emitted when job is retried (job_id)
        refresh_requested: Emitted when refresh is clicked
    """

    job_selected = Signal(str)
    job_cancelled = Signal(str)
    job_retried = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._jobs: list[dict[str, Any]] = []
        self._job_map: dict[str, dict[str, Any]] = {}
        self._selected_job: dict[str, Any] | None = None
        self._context_job: dict[str, Any] | None = None  # Context menu target
        self._setup_ui()
        self._apply_styles()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._request_refresh)
        self._refresh_timer.start(10000)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search jobs...")
        self._search_edit.textChanged.connect(self._apply_filters)
        self._search_edit.setMinimumWidth(200)
        toolbar.addWidget(self._search_edit)

        self._status_filter = QComboBox()
        self._status_filter.addItems(
            [
                "All Status",
                "Pending",
                "Queued",
                "Running",
                "Completed",
                "Failed",
                "Cancelled",
            ]
        )
        self._status_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._status_filter)

        self._time_filter = QComboBox()
        self._time_filter.addItems(
            [
                "Last Hour",
                "Last 24 Hours",
                "Last 7 Days",
                "Last 30 Days",
                "All Time",
            ]
        )
        self._time_filter.setCurrentIndex(1)
        self._time_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._time_filter)

        toolbar.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setIcon(get_toolbar_icon("restart"))
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Job ID",
                "Workflow",
                "Robot",
                "Status",
                "Created",
                "Duration",
                "Progress",
                "Actions",
            ]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(self._on_double_click)
        self._table.setShowGrid(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(7, 140)

        splitter.addWidget(self._table)

        details_widget = QWidget()
        details_layout = QHBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        info_group = QGroupBox("Job Details")
        info_layout = QVBoxLayout(info_group)

        self._detail_job_id = QLabel("Job ID: -")
        self._detail_workflow = QLabel("Workflow: -")
        self._detail_robot = QLabel("Robot: -")
        self._detail_status = QLabel("Status: -")
        self._detail_created = QLabel("Created: -")
        self._detail_completed = QLabel("Completed: -")
        self._detail_duration = QLabel("Duration: -")
        self._detail_retries = QLabel("Retries: -")
        self._detail_error = QLabel("Error: -")
        self._detail_error.setWordWrap(True)

        info_layout.addWidget(self._detail_job_id)
        info_layout.addWidget(self._detail_workflow)
        info_layout.addWidget(self._detail_robot)
        info_layout.addWidget(self._detail_status)
        info_layout.addWidget(self._detail_created)
        info_layout.addWidget(self._detail_completed)
        info_layout.addWidget(self._detail_duration)
        info_layout.addWidget(self._detail_retries)
        info_layout.addWidget(self._detail_error)
        info_layout.addStretch()

        details_layout.addWidget(info_group, 1)

        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout(log_group)

        self._log_viewer = QTextEdit()
        self._log_viewer.setReadOnly(True)
        self._log_viewer.setFont(self._log_viewer.font())
        log_layout.addWidget(self._log_viewer)

        details_layout.addWidget(log_group, 2)

        splitter.addWidget(details_widget)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

        self._status_label = QLabel("0 jobs")
        self._status_label.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(self._status_label)

    def _apply_styles(self) -> None:
        self.setStyleSheet(TAB_WIDGET_BASE_STYLE)

    def update_jobs(self, jobs: list[dict[str, Any]]) -> None:
        """Update table with job list."""
        self._jobs = jobs
        self._job_map = {j.get("job_id", ""): j for j in jobs}
        self._populate_table()
        self._update_status_label()

    def _populate_table(self) -> None:
        """Populate table with current jobs."""
        self._table.setRowCount(len(self._jobs))
        self._table.setSortingEnabled(False)

        for row, job in enumerate(self._jobs):
            self._add_table_row(row, job)

    def _add_table_row(self, row: int, job: dict[str, Any]) -> None:
        """Add a row to the table."""
        self._table.insertRow(row)

        job_id = job.get("job_id", "")
        workflow = job.get("workflow_name", "Unknown")
        robot = job.get("robot_name", "Unknown")
        status = job.get("status", "pending")
        created = job.get("created_at", "")
        duration = str(job.get("duration", 0)) + "s"
        progress = job.get("progress", 0)

        # Job ID
        self._table.setItem(row, 0, QTableWidgetItem(job_id))

        # Workflow
        self._table.setItem(row, 1, QTableWidgetItem(workflow))

        # Robot
        self._table.setItem(row, 2, QTableWidgetItem(robot))

        # Status
        status_item = QTableWidgetItem(status.upper())
        status_color = JOB_STATUS_COLORS.get(status.lower(), THEME.text_secondary)
        status_item.setForeground(QBrush(status_color))
        self._table.setItem(row, 3, status_item)

        # Created
        self._table.setItem(row, 4, QTableWidgetItem(created))

        # Duration
        self._table.setItem(row, 5, QTableWidgetItem(duration))

        # Progress
        progress_bar = QProgressBar()
        progress_bar.setValue(int(progress))
        progress_bar.setTextVisible(True)
        self._table.setCellWidget(row, 6, progress_bar)

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(partial(self.job_cancelled.emit, job_id))
        actions_layout.addWidget(cancel_btn)

        self._table.setCellWidget(row, 7, actions_widget)

    def _request_refresh(self) -> None:
        """Request data refresh."""
        self.refresh_requested.emit()

    def _apply_filters(self) -> None:
        """Filter table rows."""
        # Implementation of filtering logic
        pass

    def _show_context_menu(self, pos) -> None:
        """Show context menu."""
        pass

    def _on_selection_changed(self) -> None:
        """Handle row selection."""
        pass

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double click."""
        pass

    def _update_status_label(self) -> None:
        """Update status label."""
        count = len(self._jobs)
        self._status_label.setText(f"{count} jobs")

    def _on_job_selected(self, job_id: str) -> None:
        """Handle job selection."""
        self.job_selected.emit(job_id)
