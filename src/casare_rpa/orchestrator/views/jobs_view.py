"""
Jobs view for CasareRPA Orchestrator.
Displays job queue, history, and management.
"""

import asyncio
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QMessageBox,
    QMenu,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QDialogButtonBox,
    QTabWidget,
)
from PySide6.QtCore import Qt

from ..styles import COLORS
from ..widgets import (
    SearchBar,
    ActionButton,
    SectionHeader,
    StatusBadge,
    EmptyState,
    ProgressIndicator,
)
from ..models import Job, JobStatus, JobPriority
from ..services import OrchestratorService


class JobDetailsDialog(QDialog):
    """Dialog showing job details and logs."""

    def __init__(self, job: Job, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Job: {job.id[:8]}...")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Tabs
        tabs = QTabWidget()

        # Details tab
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        info_pairs = [
            ("Job ID", job.id),
            ("Workflow", job.workflow_name),
            (
                "Robot",
                f"{job.robot_name} ({job.robot_id[:8]}...)"
                if job.robot_name
                else job.robot_id,
            ),
            ("Status", job.status.value.upper()),
            ("Priority", job.priority.name),
            ("Progress", f"{job.progress}%"),
            ("Current Node", job.current_node or "-"),
            ("Created", str(job.created_at) if job.created_at else "-"),
            ("Started", str(job.started_at) if job.started_at else "-"),
            ("Completed", str(job.completed_at) if job.completed_at else "-"),
            ("Duration", job.duration_formatted),
        ]

        for label, value in info_pairs:
            row = QHBoxLayout()
            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet(
                f"color: {COLORS['text_muted']}; min-width: 100px;"
            )
            row.addWidget(label_widget)

            if label == "Status":
                value_widget = StatusBadge(job.status.value)
            else:
                value_widget = QLabel(str(value))
                value_widget.setStyleSheet(f"color: {COLORS['text_primary']};")

            row.addWidget(value_widget)
            row.addStretch()
            details_layout.addLayout(row)

        if job.error_message:
            error_label = QLabel("Error:")
            error_label.setStyleSheet(
                f"color: {COLORS['accent_error']}; font-weight: 600;"
            )
            details_layout.addWidget(error_label)

            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setPlainText(job.error_message)
            error_text.setMaximumHeight(100)
            error_text.setStyleSheet(f"""
                background-color: {COLORS['bg_medium']};
                color: {COLORS['accent_error']};
                border: 1px solid {COLORS['accent_error']}40;
                border-radius: 4px;
            """)
            details_layout.addWidget(error_text)

        details_layout.addStretch()
        tabs.addTab(details_widget, "Details")

        # Logs tab
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)

        logs_text = QTextEdit()
        logs_text.setReadOnly(True)
        logs_text.setPlainText(job.logs or "No logs available")
        logs_text.setStyleSheet(f"""
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        """)
        logs_layout.addWidget(logs_text)
        tabs.addTab(logs_widget, "Logs")

        layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class JobsView(QWidget):
    """Jobs management view with queue and history."""

    def __init__(self, service: OrchestratorService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._service = service
        self._jobs: List[Job] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = SectionHeader("Jobs", "Refresh")
        header.action_clicked.connect(
            lambda: asyncio.get_event_loop().create_task(self.refresh())
        )
        layout.addWidget(header)

        # Quick stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._running_label = QLabel("Running: 0")
        self._running_label.setStyleSheet(
            f"color: {COLORS['job_running']}; font-weight: 600;"
        )
        stats_layout.addWidget(self._running_label)

        self._queued_label = QLabel("Queued: 0")
        self._queued_label.setStyleSheet(
            f"color: {COLORS['job_queued']}; font-weight: 600;"
        )
        stats_layout.addWidget(self._queued_label)

        self._completed_label = QLabel("Completed: 0")
        self._completed_label.setStyleSheet(
            f"color: {COLORS['job_completed']}; font-weight: 600;"
        )
        stats_layout.addWidget(self._completed_label)

        self._failed_label = QLabel("Failed: 0")
        self._failed_label.setStyleSheet(
            f"color: {COLORS['job_failed']}; font-weight: 600;"
        )
        stats_layout.addWidget(self._failed_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Search and filters
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search = SearchBar(
            "Search jobs...",
            filters=[
                "All",
                "Running",
                "Queued",
                "Pending",
                "Completed",
                "Failed",
                "Cancelled",
            ],
        )
        self._search.search_changed.connect(self._apply_filter)
        self._search.filter_changed.connect(self._apply_filter)
        toolbar.addWidget(self._search)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Jobs table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Status",
                "Workflow",
                "Robot",
                "Priority",
                "Progress",
                "Duration",
                "Created",
                "Actions",
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(0, 100)
        self._table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(4, 120)
        self._table.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(7, 180)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Empty state
        self._empty_state = EmptyState(
            title="No Jobs Found",
            description="No jobs have been executed yet. Dispatch a workflow to get started.",
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
                status_widget = self._table.cellWidget(row, 0)
                if status_widget:
                    status_text = status_widget.text().lower()
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
        """Show context menu for job row."""
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._jobs):
            return

        job = self._jobs[row]
        menu = QMenu(self)

        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self._show_details(job))

        menu.addSeparator()

        if not job.is_terminal:
            cancel_action = menu.addAction("Cancel Job")
            cancel_action.triggered.connect(
                lambda: asyncio.get_event_loop().create_task(self._cancel_job(job))
            )

        if job.status == JobStatus.FAILED:
            retry_action = menu.addAction("Retry Job")
            retry_action.triggered.connect(
                lambda: asyncio.get_event_loop().create_task(self._retry_job(job))
            )

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, row: int, col: int):
        """Handle double-click on table row."""
        if 0 <= row < len(self._jobs):
            self._show_details(self._jobs[row])

    def _show_details(self, job: Job):
        """Show job details dialog."""
        dialog = JobDetailsDialog(job, self)
        dialog.exec()

    async def _cancel_job(self, job: Job):
        """Cancel a job."""
        reply = QMessageBox.question(
            self,
            "Cancel Job",
            f"Are you sure you want to cancel job '{job.id[:8]}...'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = await self._service.cancel_job(job.id)
            if success:
                await self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to cancel job")

    async def _retry_job(self, job: Job):
        """Retry a failed job."""
        new_job = await self._service.retry_job(job.id)
        if new_job:
            QMessageBox.information(
                self, "Job Retried", f"New job created: {new_job.id[:8]}..."
            )
            await self.refresh()
        else:
            QMessageBox.warning(self, "Error", "Failed to retry job")

    def _update_table(self):
        """Update the table with current jobs."""
        self._table.setRowCount(len(self._jobs))

        # Update stats
        running = sum(1 for j in self._jobs if j.status == JobStatus.RUNNING)
        queued = sum(
            1 for j in self._jobs if j.status in (JobStatus.PENDING, JobStatus.QUEUED)
        )
        completed = sum(1 for j in self._jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in self._jobs if j.status == JobStatus.FAILED)

        self._running_label.setText(f"Running: {running}")
        self._queued_label.setText(f"Queued: {queued}")
        self._completed_label.setText(f"Completed: {completed}")
        self._failed_label.setText(f"Failed: {failed}")

        if not self._jobs:
            self._table.hide()
            self._empty_state.show()
            return

        self._table.show()
        self._empty_state.hide()

        for row, job in enumerate(self._jobs):
            # Status badge
            status_badge = StatusBadge(job.status.value)
            self._table.setCellWidget(row, 0, status_badge)

            # Workflow name
            workflow_name = (
                job.workflow_name[:25] + "..."
                if len(job.workflow_name) > 25
                else job.workflow_name
            )
            self._table.setItem(row, 1, QTableWidgetItem(workflow_name))

            # Robot
            robot_name = job.robot_name or job.robot_id[:8] + "..."
            self._table.setItem(row, 2, QTableWidgetItem(robot_name))

            # Priority
            priority_text = job.priority.name
            priority_item = QTableWidgetItem(priority_text)
            if job.priority == JobPriority.HIGH:
                priority_item.setForeground(Qt.GlobalColor.yellow)
            elif job.priority == JobPriority.CRITICAL:
                priority_item.setForeground(Qt.GlobalColor.red)
            self._table.setItem(row, 3, priority_item)

            # Progress
            progress_widget = ProgressIndicator(job.progress)
            self._table.setCellWidget(row, 4, progress_widget)

            # Duration
            self._table.setItem(row, 5, QTableWidgetItem(job.duration_formatted))

            # Created
            created = str(job.created_at)[:19] if job.created_at else "-"
            self._table.setItem(row, 6, QTableWidgetItem(created))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            view_btn = ActionButton("View", primary=False)
            view_btn.clicked.connect(lambda checked, j=job: self._show_details(j))
            actions_layout.addWidget(view_btn)

            if not job.is_terminal:
                cancel_btn = ActionButton("Cancel", primary=False)
                cancel_btn.clicked.connect(
                    lambda checked, j=job: asyncio.get_event_loop().create_task(
                        self._cancel_job(j)
                    )
                )
                actions_layout.addWidget(cancel_btn)

            self._table.setCellWidget(row, 7, actions_widget)

    async def refresh(self):
        """Refresh jobs data."""
        try:
            self._jobs = await self._service.get_jobs(limit=100)
            self._update_table()
        except Exception as e:
            from loguru import logger

            logger.error(f"Failed to refresh jobs: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load jobs: {e}")
