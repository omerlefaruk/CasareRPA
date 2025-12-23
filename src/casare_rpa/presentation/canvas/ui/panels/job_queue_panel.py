"""
Job Queue Panel UI Component.

Dockable panel showing job queue status and management.
Displays pending, running, completed, and failed jobs with filtering and actions.
"""

from functools import partial

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.ui.theme import THEME


def _hex_to_qcolor(hex_color: str) -> QColor:
    """Convert hex color string to QColor."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return QColor(r, g, b)


class JobQueuePanel(QDockWidget):
    """
    Panel showing job queue status and management.

    Features:
    - Tabs: Pending, Running, Completed, Failed (DLQ)
    - Job table with workflow name, robot, status, priority
    - Filters by workflow name and robot
    - Actions: Cancel, Retry, Change Priority

    Signals:
        cancel_job_requested: Cancel job requested (job_id)
        retry_job_requested: Retry failed job requested (job_id)
        priority_changed: Job priority changed (job_id, new_priority)
        refresh_requested: Queue refresh requested (tab_name)
    """

    cancel_job_requested = Signal(str)
    retry_job_requested = Signal(str)
    priority_changed = Signal(str, int)
    refresh_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize Job Queue Panel."""
        super().__init__("Job Queue", parent)
        self.setObjectName("JobQueueDock")

        self._pending_jobs: list[dict] = []
        self._running_jobs: list[dict] = []
        self._completed_jobs: list[dict] = []
        self._failed_jobs: list[dict] = []

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("JobQueuePanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Header with filters and refresh
        header_layout = QHBoxLayout()

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        header_layout.addWidget(filter_label)

        self._workflow_filter = QComboBox()
        self._workflow_filter.addItem("All Workflows")
        self._workflow_filter.setMinimumWidth(120)
        self._workflow_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self._workflow_filter)

        self._robot_filter = QComboBox()
        self._robot_filter.addItem("All Robots")
        self._robot_filter.setMinimumWidth(100)
        self._robot_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self._robot_filter)

        header_layout.addStretch()

        self._queue_stats_label = QLabel("Queue: 0 | Running: 0")
        self._queue_stats_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        header_layout.addWidget(self._queue_stats_label)

        self._refresh_btn = QPushButton("↻ Refresh")
        self._refresh_btn.setFixedHeight(24)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self._refresh_btn)

        main_layout.addLayout(header_layout)

        # Tab widget for different job states
        self._tab_widget = QTabWidget()
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Pending jobs tab
        self._pending_table = self._create_job_table(
            ["Workflow", "Priority", "Submitted", "Actions"]
        )
        pending_widget = self._wrap_table_with_actions(self._pending_table, "pending")
        self._tab_widget.addTab(pending_widget, "Pending (0)")

        # Running jobs tab
        self._running_table = self._create_job_table(
            ["Workflow", "Robot", "Progress", "Started", "Actions"]
        )
        running_widget = self._wrap_table_with_actions(self._running_table, "running")
        self._tab_widget.addTab(running_widget, "Running (0)")

        # Completed jobs tab
        self._completed_table = self._create_job_table(
            ["Workflow", "Robot", "Duration", "Completed"]
        )
        completed_widget = QWidget()
        completed_layout = QVBoxLayout(completed_widget)
        completed_layout.setContentsMargins(0, 0, 0, 0)
        completed_layout.addWidget(self._completed_table)
        self._tab_widget.addTab(completed_widget, "Completed (0)")

        # Failed/DLQ jobs tab
        self._failed_table = self._create_job_table(
            ["Workflow", "Error", "Retries", "Failed At", "Actions"]
        )
        failed_widget = self._wrap_table_with_actions(self._failed_table, "failed")
        self._tab_widget.addTab(failed_widget, "Failed (0)")

        main_layout.addWidget(self._tab_widget, 1)

        self.setWidget(container)

    def _create_job_table(self, headers: list[str]) -> QTableWidget:
        """Create a job table with given headers."""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        return table

    def _wrap_table_with_actions(self, table: QTableWidget, job_type: str) -> QWidget:
        """Wrap table with action buttons bar."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        layout.addWidget(table, 1)

        # Action buttons bar
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        if job_type == "pending":
            cancel_btn = QPushButton("Cancel Selected")
            cancel_btn.clicked.connect(partial(self._on_cancel_action, table))
            actions_layout.addWidget(cancel_btn)

        elif job_type == "running":
            cancel_btn = QPushButton("Cancel Selected")
            cancel_btn.clicked.connect(partial(self._on_cancel_action, table))
            actions_layout.addWidget(cancel_btn)

        elif job_type == "failed":
            retry_btn = QPushButton("Retry Selected")
            retry_btn.clicked.connect(partial(self._on_retry_action, table))
            actions_layout.addWidget(retry_btn)

            purge_btn = QPushButton("Purge All")
            purge_btn.setStyleSheet(f"color: {THEME.error};")
            purge_btn.clicked.connect(self._on_purge_clicked)
            actions_layout.addWidget(purge_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        return widget

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background: {THEME.bg_dark};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background: {THEME.bg_medium};
                padding: 6px;
            }}
            QTabWidget::pane {{
                border: 1px solid {THEME.border};
                background: {THEME.bg_dark};
            }}
            QTabBar::tab {{
                background: {THEME.bg_medium};
                color: {THEME.text_muted};
                padding: 6px 12px;
                border: 1px solid {THEME.border};
                border-bottom: none;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME.bg_dark};
                color: {THEME.text_primary};
            }}
            QTabBar::tab:hover {{
                background: {THEME.bg_light};
            }}
            QComboBox {{
                background: {THEME.bg_light};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 3px 8px;
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {THEME.accent_primary};
            }}
            QTableWidget {{
                background: {THEME.bg_darkest};
                border: 1px solid {THEME.border};
                color: {THEME.text_primary};
                alternate-background-color: {THEME.bg_dark};
                gridline-color: {THEME.border};
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background: {THEME.accent_primary};
            }}
            QHeaderView::section {{
                background: {THEME.bg_medium};
                color: {THEME.text_muted};
                padding: 4px;
                border: none;
                border-right: 1px solid {THEME.border};
            }}
            QPushButton {{
                background: {THEME.bg_light};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_medium};
                border-color: {THEME.accent_primary};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_dark};
            }}
        """)

    def _update_tab_counts(self) -> None:
        """Update tab titles with job counts."""
        self._tab_widget.setTabText(0, f"Pending ({len(self._pending_jobs)})")
        self._tab_widget.setTabText(1, f"Running ({len(self._running_jobs)})")
        self._tab_widget.setTabText(2, f"Completed ({len(self._completed_jobs)})")
        self._tab_widget.setTabText(3, f"Failed ({len(self._failed_jobs)})")

        # Update queue stats
        self._queue_stats_label.setText(
            f"Queue: {len(self._pending_jobs)} | Running: {len(self._running_jobs)}"
        )

    # ==================== Public Methods ====================

    @Slot(list)
    def update_pending_jobs(self, jobs: list[dict]) -> None:
        """Update pending jobs list."""
        self._pending_jobs = jobs
        self._populate_pending_table()
        self._update_tab_counts()

    @Slot(list)
    def update_running_jobs(self, jobs: list[dict]) -> None:
        """Update running jobs list."""
        self._running_jobs = jobs
        self._populate_running_table()
        self._update_tab_counts()

    @Slot(list)
    def update_completed_jobs(self, jobs: list[dict]) -> None:
        """Update completed jobs list."""
        self._completed_jobs = jobs
        self._populate_completed_table()
        self._update_tab_counts()

    @Slot(list)
    def update_failed_jobs(self, jobs: list[dict]) -> None:
        """Update failed/DLQ jobs list."""
        self._failed_jobs = jobs
        self._populate_failed_table()
        self._update_tab_counts()

    def _populate_pending_table(self) -> None:
        """Populate pending jobs table."""
        self._pending_table.setRowCount(len(self._pending_jobs))
        for row, job in enumerate(self._pending_jobs):
            self._pending_table.setItem(
                row, 0, QTableWidgetItem(job.get("workflow_name", "Unknown"))
            )
            self._pending_table.setItem(row, 1, QTableWidgetItem(str(job.get("priority", 10))))
            self._pending_table.setItem(row, 2, QTableWidgetItem(job.get("submitted_at", "-")))

            # Store job ID in first column
            self._pending_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, job.get("job_id"))

    def _populate_running_table(self) -> None:
        """Populate running jobs table."""
        self._running_table.setRowCount(len(self._running_jobs))
        for row, job in enumerate(self._running_jobs):
            self._running_table.setItem(
                row, 0, QTableWidgetItem(job.get("workflow_name", "Unknown"))
            )
            self._running_table.setItem(row, 1, QTableWidgetItem(job.get("robot_name", "-")))

            progress = job.get("progress", 0)
            progress_item = QTableWidgetItem(f"{progress}%")
            if progress > 0:
                progress_item.setForeground(QBrush(_hex_to_qcolor(THEME.success)))
            self._running_table.setItem(row, 2, progress_item)

            self._running_table.setItem(row, 3, QTableWidgetItem(job.get("started_at", "-")))

            # Store job ID
            self._running_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, job.get("job_id"))

    def _populate_completed_table(self) -> None:
        """Populate completed jobs table."""
        self._completed_table.setRowCount(len(self._completed_jobs))
        for row, job in enumerate(self._completed_jobs):
            self._completed_table.setItem(
                row, 0, QTableWidgetItem(job.get("workflow_name", "Unknown"))
            )
            self._completed_table.setItem(row, 1, QTableWidgetItem(job.get("robot_name", "-")))
            self._completed_table.setItem(row, 2, QTableWidgetItem(job.get("duration", "-")))
            self._completed_table.setItem(row, 3, QTableWidgetItem(job.get("completed_at", "-")))

    def _populate_failed_table(self) -> None:
        """Populate failed/DLQ jobs table."""
        self._failed_table.setRowCount(len(self._failed_jobs))
        for row, job in enumerate(self._failed_jobs):
            self._failed_table.setItem(
                row, 0, QTableWidgetItem(job.get("workflow_name", "Unknown"))
            )

            error_item = QTableWidgetItem(job.get("error", "Unknown error")[:50])
            error_item.setForeground(QBrush(_hex_to_qcolor(THEME.error)))
            self._failed_table.setItem(row, 1, error_item)

            self._failed_table.setItem(row, 2, QTableWidgetItem(str(job.get("retry_count", 0))))
            self._failed_table.setItem(row, 3, QTableWidgetItem(job.get("failed_at", "-")))

            # Store job ID
            self._failed_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, job.get("job_id"))

    # ==================== Slot Handlers ====================

    @Slot(int)
    def _on_filter_changed(self, index: int) -> None:
        """Handle filter dropdown change."""
        # Filter is applied via refresh - emit refresh for current tab
        self._on_refresh_clicked()

    @Slot(int)
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        tab_names = ["pending", "running", "completed", "failed"]
        if 0 <= index < len(tab_names):
            logger.debug(f"Job queue tab changed to: {tab_names[index]}")

    @Slot()
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        current_tab = self._tab_widget.currentIndex()
        tab_names = ["pending", "running", "completed", "failed"]
        if 0 <= current_tab < len(tab_names):
            self.refresh_requested.emit(tab_names[current_tab])

    def _on_cancel_action(self, table: QTableWidget) -> None:
        """Handle cancel action for a specific table."""
        self._on_action_clicked("cancel", table)

    def _on_retry_action(self, table: QTableWidget) -> None:
        """Handle retry action for a specific table."""
        self._on_action_clicked("retry", table)

    def _on_action_clicked(self, action: str, table: QTableWidget) -> None:
        """Handle action button click."""
        selected_rows = table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        item = table.item(row, 0)
        if not item:
            return

        job_id = item.data(Qt.ItemDataRole.UserRole)

        if not job_id:
            return

        if action == "cancel":
            self.cancel_job_requested.emit(job_id)
            logger.debug(f"Cancel requested for job: {job_id}")
        elif action == "retry":
            self.retry_job_requested.emit(job_id)
            logger.debug(f"Retry requested for job: {job_id}")

    @Slot()
    def _on_purge_clicked(self) -> None:
        """Handle purge all failed jobs button click."""
        # Emit signal for each failed job
        for job in self._failed_jobs:
            job_id = job.get("job_id")
            if job_id:
                self.cancel_job_requested.emit(job_id)
        logger.debug("Purge all failed jobs requested")

    # ==================== Properties ====================

    @property
    def pending_count(self) -> int:
        """Get pending job count."""
        return len(self._pending_jobs)

    @property
    def running_count(self) -> int:
        """Get running job count."""
        return len(self._running_jobs)

    @property
    def failed_count(self) -> int:
        """Get failed job count."""
        return len(self._failed_jobs)
