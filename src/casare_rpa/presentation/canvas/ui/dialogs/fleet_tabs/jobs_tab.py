"""
Jobs Tab Widget for Fleet Dashboard.

Displays job queue and history with monitoring capabilities.
Supports real-time job updates with progress bars via WebSocketBridge.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QComboBox,
    QLineEdit,
    QLabel,
    QTextEdit,
    QGroupBox,
    QMenu,
    QMessageBox,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QBrush

from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    JOB_STATUS_COLORS,
)


if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.services.websocket_bridge import JobStatusUpdate


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._jobs: List[Dict[str, Any]] = []
        self._job_map: Dict[str, Dict[str, Any]] = {}
        self._selected_job: Optional[Dict[str, Any]] = None
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
        self._status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self._status_label)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QTableWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
                alternate-background-color: #252525;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background: #094771;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #a0a0a0;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
                border-right: 1px solid #3d3d3d;
            }
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #e0e0e0;
            }
            QTextEdit {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                color: #c0c0c0;
                font-family: monospace;
            }
            QLineEdit, QComboBox {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
                min-height: 24px;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def update_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Update table with job list."""
        self._jobs = jobs
        self._job_map = {j.get("job_id", ""): j for j in jobs}
        self._populate_table()
        self._update_status_label()

    def _populate_table(self) -> None:
        """Populate table with current jobs."""
        self._table.setRowCount(len(self._jobs))

        for row, job in enumerate(self._jobs):
            job_id = job.get("job_id", "")
            short_id = job_id[:8] if len(job_id) > 8 else job_id

            id_item = QTableWidgetItem(short_id)
            id_item.setToolTip(job_id)
            id_item.setData(Qt.ItemDataRole.UserRole, job_id)
            self._table.setItem(row, 0, id_item)

            self._table.setItem(row, 1, QTableWidgetItem(job.get("workflow_name", "-")))
            self._table.setItem(
                row,
                2,
                QTableWidgetItem(
                    job.get("robot_id", "-")[:8] if job.get("robot_id") else "-"
                ),
            )

            status = job.get("status", "pending")
            status_item = QTableWidgetItem(status.title())
            status_color = JOB_STATUS_COLORS.get(status, JOB_STATUS_COLORS["pending"])
            status_item.setForeground(QBrush(status_color))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            self._table.setItem(row, 3, status_item)

            created = job.get("created_at")
            if created:
                if isinstance(created, datetime):
                    created_str = created.strftime("%Y-%m-%d %H:%M")
                else:
                    created_str = str(created)[:16]
            else:
                created_str = "-"
            self._table.setItem(row, 4, QTableWidgetItem(created_str))

            duration_ms = job.get("duration_ms")
            if duration_ms:
                duration_str = f"{duration_ms / 1000:.1f}s"
            else:
                duration_str = "-"
            self._table.setItem(row, 5, QTableWidgetItem(duration_str))

            progress = job.get("progress", 0)
            self._table.setItem(row, 6, QTableWidgetItem(f"{progress}%"))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            if status in ("pending", "queued", "running"):
                cancel_btn = QPushButton("Cancel")
                cancel_btn.setMaximumHeight(24)
                cancel_btn.clicked.connect(lambda _, j=job: self._on_cancel_job(j))
                actions_layout.addWidget(cancel_btn)

            if status in ("failed", "cancelled"):
                retry_btn = QPushButton("Retry")
                retry_btn.setMaximumHeight(24)
                retry_btn.clicked.connect(lambda _, j=job: self._on_retry_job(j))
                actions_layout.addWidget(retry_btn)

            view_btn = QPushButton("View")
            view_btn.setMaximumHeight(24)
            view_btn.clicked.connect(lambda _, j=job: self._show_job_details(j))
            actions_layout.addWidget(view_btn)

            self._table.setCellWidget(row, 7, actions_widget)

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply search and filter to table rows."""
        search_text = self._search_edit.text().lower()
        status_filter = self._status_filter.currentText().lower()

        visible_count = 0
        for row in range(self._table.rowCount()):
            job_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            job = self._job_map.get(job_id)

            if job is None:
                self._table.setRowHidden(row, True)
                continue

            show = True

            if search_text:
                workflow_match = search_text in job.get("workflow_name", "").lower()
                id_match = search_text in job.get("job_id", "").lower()
                if not (workflow_match or id_match):
                    show = False

            if show and status_filter != "all status":
                if job.get("status", "").lower() != status_filter:
                    show = False

            self._table.setRowHidden(row, not show)
            if show:
                visible_count += 1

        self._update_status_label(visible_count)

    def _update_status_label(self, visible: Optional[int] = None) -> None:
        """Update status label with job counts."""
        total = len(self._jobs)
        running = sum(1 for j in self._jobs if j.get("status") == "running")
        pending = sum(1 for j in self._jobs if j.get("status") in ("pending", "queued"))
        failed = sum(1 for j in self._jobs if j.get("status") == "failed")

        if visible is not None and visible != total:
            self._status_label.setText(
                f"Showing {visible} of {total} jobs | "
                f"Running: {running}, Pending: {pending}, Failed: {failed}"
            )
        else:
            self._status_label.setText(
                f"{total} jobs | Running: {running}, Pending: {pending}, Failed: {failed}"
            )

    def _show_context_menu(self, pos) -> None:
        """Show context menu for job row."""
        item = self._table.itemAt(pos)
        if not item:
            return

        job_id = self._table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        job = self._job_map.get(job_id)
        if not job:
            return

        menu = QMenu(self)
        status = job.get("status", "")

        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self._show_job_details(job))

        menu.addSeparator()

        if status in ("pending", "queued", "running"):
            cancel_action = menu.addAction("Cancel")
            cancel_action.triggered.connect(lambda: self._on_cancel_job(job))

        if status in ("failed", "cancelled"):
            retry_action = menu.addAction("Retry")
            retry_action.triggered.connect(lambda: self._on_retry_job(job))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self._table.selectedItems()
        if selected:
            job_id = self._table.item(selected[0].row(), 0).data(
                Qt.ItemDataRole.UserRole
            )
            job = self._job_map.get(job_id)
            if job:
                self._show_job_details(job)
                self.job_selected.emit(job_id)

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on job row."""
        job_id = self._table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        job = self._job_map.get(job_id)
        if job:
            self._show_job_details(job)

    def _show_job_details(self, job: Dict[str, Any]) -> None:
        """Show job details in panel."""
        self._selected_job = job

        self._detail_job_id.setText(f"Job ID: {job.get('job_id', '-')}")
        self._detail_workflow.setText(f"Workflow: {job.get('workflow_name', '-')}")
        self._detail_robot.setText(f"Robot: {job.get('robot_id', '-')}")

        status = job.get("status", "-")
        status_color = JOB_STATUS_COLORS.get(status, JOB_STATUS_COLORS["pending"])
        self._detail_status.setText(f"Status: {status.title()}")
        self._detail_status.setStyleSheet(f"color: {status_color.name()};")

        created = job.get("created_at")
        if created:
            if isinstance(created, datetime):
                created_str = created.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = str(created)
        else:
            created_str = "-"
        self._detail_created.setText(f"Created: {created_str}")

        completed = job.get("completed_at")
        if completed:
            if isinstance(completed, datetime):
                completed_str = completed.strftime("%Y-%m-%d %H:%M:%S")
            else:
                completed_str = str(completed)
        else:
            completed_str = "-"
        self._detail_completed.setText(f"Completed: {completed_str}")

        duration_ms = job.get("duration_ms")
        if duration_ms:
            duration_str = f"{duration_ms / 1000:.2f}s"
        else:
            duration_str = "-"
        self._detail_duration.setText(f"Duration: {duration_str}")

        retries = job.get("retry_count", 0)
        self._detail_retries.setText(f"Retries: {retries}")

        error = job.get("error_message", "")
        if error:
            self._detail_error.setText(f"Error: {error}")
            self._detail_error.setStyleSheet("color: #F44336;")
        else:
            self._detail_error.setText("Error: -")
            self._detail_error.setStyleSheet("color: #e0e0e0;")

        logs = job.get("logs", "")
        if logs:
            self._log_viewer.setPlainText(logs)
        else:
            self._log_viewer.setPlainText("No logs available.")

    def _on_cancel_job(self, job: Dict[str, Any]) -> None:
        """Cancel a running job."""
        job_id = job.get("job_id", "")
        reply = QMessageBox.question(
            self,
            "Cancel Job",
            f"Are you sure you want to cancel job {job_id[:8]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.job_cancelled.emit(job_id)

    def _on_retry_job(self, job: Dict[str, Any]) -> None:
        """Retry a failed job."""
        job_id = job.get("job_id", "")
        self.job_retried.emit(job_id)

    def _request_refresh(self) -> None:
        """Request job list refresh."""
        self.refresh_requested.emit()

    def set_refreshing(self, refreshing: bool) -> None:
        """Set refresh button state."""
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")

    def get_selected_job(self) -> Optional[Dict[str, Any]]:
        """Get currently selected job."""
        return self._selected_job

    # ==================== Real-Time Updates ====================

    def handle_job_status_update(self, update: "JobStatusUpdate") -> None:
        """
        Handle real-time job status update from WebSocket.

        Updates the job row in place without full table refresh.

        Args:
            update: JobStatusUpdate from WebSocketBridge
        """
        job_id = update.job_id

        # Find the job in our map
        job = self._job_map.get(job_id)
        if not job:
            # Job not in current list, request refresh for new jobs
            return

        # Update job dict with new status
        job["status"] = update.status
        job["progress"] = update.progress
        if update.current_node:
            job["current_node"] = update.current_node
        if update.error_message:
            job["error_message"] = update.error_message

        # Find and update the row
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == job_id:
                self._update_job_row(row, update)
                break

        # Update details panel if this job is selected
        if self._selected_job and self._selected_job.get("job_id") == job_id:
            self._show_job_details(job)

    def _update_job_row(self, row: int, update: "JobStatusUpdate") -> None:
        """
        Update a single job row with new status data.

        Args:
            row: Table row index
            update: JobStatusUpdate with new data
        """
        # Update status column
        status_item = self._table.item(row, 3)
        if status_item:
            status_item.setText(update.status.title())
            status_color = JOB_STATUS_COLORS.get(
                update.status, JOB_STATUS_COLORS["pending"]
            )
            status_item.setForeground(QBrush(status_color))

        # Update progress column
        progress_item = self._table.item(row, 6)
        if progress_item:
            progress_item.setText(f"{update.progress}%")

        # Update progress bar widget if exists
        progress_widget = self._table.cellWidget(row, 6)
        if isinstance(progress_widget, QProgressBar):
            progress_widget.setValue(update.progress)

            # Color progress bar based on status
            if update.status == "running":
                progress_widget.setStyleSheet(
                    "QProgressBar::chunk { background-color: #4CAF50; }"
                )
            elif update.status == "failed":
                progress_widget.setStyleSheet(
                    "QProgressBar::chunk { background-color: #F44336; }"
                )
            elif update.status == "completed":
                progress_widget.setStyleSheet(
                    "QProgressBar::chunk { background-color: #00C853; }"
                )

    def handle_batch_job_updates(self, updates: List["JobStatusUpdate"]) -> None:
        """
        Handle batch of job status updates efficiently.

        Args:
            updates: List of JobStatusUpdate objects
        """
        # Temporarily disable sorting for batch update
        self._table.setSortingEnabled(False)

        try:
            for update in updates:
                self.handle_job_status_update(update)
        finally:
            self._table.setSortingEnabled(True)

        # Update status label with new counts
        self._update_status_label()

    def create_progress_bar_widget(self, progress: int, status: str) -> QProgressBar:
        """
        Create a progress bar widget for job row.

        Args:
            progress: Progress percentage (0-100)
            status: Job status for color coding

        Returns:
            Configured QProgressBar widget
        """
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(100)
        bar.setValue(progress)
        bar.setTextVisible(True)
        bar.setFormat("%p%")

        # Apply styling based on status
        if status == "running":
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    background: #1e1e1e;
                    text-align: center;
                    color: #e0e0e0;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)
        elif status == "failed":
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    background: #1e1e1e;
                    text-align: center;
                    color: #e0e0e0;
                }
                QProgressBar::chunk {
                    background-color: #F44336;
                    border-radius: 2px;
                }
            """)
        elif status == "completed":
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    background: #1e1e1e;
                    text-align: center;
                    color: #e0e0e0;
                }
                QProgressBar::chunk {
                    background-color: #00C853;
                    border-radius: 2px;
                }
            """)
        else:
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    background: #1e1e1e;
                    text-align: center;
                    color: #e0e0e0;
                }
                QProgressBar::chunk {
                    background-color: #9E9E9E;
                    border-radius: 2px;
                }
            """)

        return bar

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job dict by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job dictionary or None
        """
        return self._job_map.get(job_id)
