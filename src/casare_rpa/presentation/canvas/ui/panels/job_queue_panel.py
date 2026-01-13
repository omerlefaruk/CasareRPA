"""
Job Queue Panel UI Component.

Dockable panel showing job queue status and management.
Displays pending, running, completed, and failed jobs with filtering and actions.

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
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
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import apply_table_style


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
        # Dock-only: NO DockWidgetFloatable (Epic 6.1 requirement)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.setMinimumWidth(TOKENS_V2.sizes.panel_min_width)
        self.setMinimumHeight(200)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)
        main_layout.setSpacing(TOKENS_V2.spacing.sm)

        # Header with filters and refresh
        header_layout = QHBoxLayout()
        header_layout.setSpacing(TOKENS_V2.spacing.xs)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.caption}px;")
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
        self._queue_stats_label.setStyleSheet(f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.caption}px;")
        header_layout.addWidget(self._queue_stats_label)

        # v2 PushButton for refresh
        self._refresh_btn = PushButton(
            text="Refresh",
            variant="secondary",
            size="sm",
        )
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
        table.setAlternatingRowColors(False)  # v2: clean look
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Apply v2 table styling
        apply_table_style(table)

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
        layout.setSpacing(TOKENS_V2.spacing.xs)

        layout.addWidget(table, 1)

        # Action buttons bar (v2 style)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(TOKENS_V2.spacing.xs)

        if job_type == "pending":
            cancel_btn = PushButton(
                text="Cancel Selected",
                variant="danger",
                size="sm",
            )
            cancel_btn.clicked.connect(partial(self._on_cancel_action, table))
            actions_layout.addWidget(cancel_btn)

        elif job_type == "running":
            cancel_btn = PushButton(
                text="Cancel Selected",
                variant="danger",
                size="sm",
            )
            cancel_btn.clicked.connect(partial(self._on_cancel_action, table))
            actions_layout.addWidget(cancel_btn)

        elif job_type == "failed":
            retry_btn = PushButton(
                text="Retry Selected",
                variant="primary",
                size="sm",
            )
            retry_btn.clicked.connect(partial(self._on_retry_action, table))
            actions_layout.addWidget(retry_btn)

            purge_btn = PushButton(
                text="Purge All",
                variant="danger",
                size="sm",
            )
            purge_btn.clicked.connect(self._on_purge_clicked)
            actions_layout.addWidget(purge_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        return widget

    def _apply_styles(self) -> None:
        """Apply v2 theme styling (Epic 6.1)."""
        t = THEME_V2
        tok = TOKENS_V2
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {t.bg_surface};
                color: {t.text_primary};
            }}
            QDockWidget::title {{
                background-color: {t.bg_header};
                color: {t.text_header};
                padding: {tok.spacing.xs}px {tok.spacing.md}px;
                font-weight: {tok.typography.weight_semibold};
                font-size: {tok.typography.caption}px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {t.border};
            }}
            QTabWidget::pane {{
                border: 1px solid {t.border};
                background: {t.bg_surface};
                border-radius: {tok.radius.sm}px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {t.bg_component};
                color: {t.text_secondary};
                padding: {tok.spacing.xs}px {tok.spacing.md}px;
                border: 1px solid {t.border};
                border-bottom: none;
                border-top-left-radius: {tok.radius.xs}px;
                border-top-right-radius: {tok.radius.xs}px;
                margin-right: 2px;
                font-size: {tok.typography.body_sm}px;
            }}
            QTabBar::tab:selected {{
                background: {t.bg_surface};
                color: {t.text_primary};
            }}
            QTabBar::tab:hover {{
                background: {t.bg_hover};
                color: {t.text_primary};
            }}
            QComboBox {{
                background: {t.bg_input};
                border: 1px solid {t.border};
                border-radius: {tok.radius.xs}px;
                color: {t.text_primary};
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                min-height: {tok.sizes.input_height}px;
                font-size: {tok.typography.body_sm}px;
            }}
            QComboBox:hover {{
                border-color: {t.border_hover};
            }}
            QComboBox:focus {{
                border-color: {t.border_focus};
            }}
            QComboBox QAbstractItemView {{
                background: {t.bg_surface};
                border: 1px solid {t.border};
                selection-background-color: {t.bg_selected};
                selection-color: {t.text_primary};
            }}
            QLabel {{
                color: {t.text_secondary};
                font-size: {tok.typography.body_sm}px;
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
                progress_item.setForeground(QBrush(_hex_to_qcolor(THEME_V2.success)))
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
            error_item.setForeground(QBrush(_hex_to_qcolor(THEME_V2.error)))
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

    @Slot()
    def _on_cancel_action(self, table: QTableWidget) -> None:
        """Handle cancel action for a specific table."""
        self._on_action_clicked("cancel", table)

    @Slot()
    def _on_retry_action(self, table: QTableWidget) -> None:
        """Handle retry action for a specific table."""
        self._on_action_clicked("retry", table)

    @Slot()
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
