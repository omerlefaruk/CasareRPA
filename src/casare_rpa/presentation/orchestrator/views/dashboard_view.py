"""
Dashboard view for CasareRPA Orchestrator.
Displays KPIs, charts, and system overview.
"""

import asyncio
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from ..styles import COLORS
from ..widgets import KPICard, SectionHeader, StatusBadge
from ..models import Job, Robot, RobotStatus
from ..services import OrchestratorService


class JobActivityChart(QFrame):
    """Simple job activity visualization."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(200)
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        header = QLabel("Job Activity (Last 7 Days)")
        header.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
        """)
        layout.addWidget(header)

        self._chart_area = QWidget()
        self._chart_layout = QHBoxLayout(self._chart_area)
        self._chart_layout.setSpacing(8)
        self._chart_layout.setContentsMargins(0, 16, 0, 0)
        layout.addWidget(self._chart_area, stretch=1)

        # Legend
        legend = QHBoxLayout()
        legend.setSpacing(16)

        for label, color in [
            ("Completed", COLORS["accent_success"]),
            ("Failed", COLORS["accent_error"]),
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            legend.addWidget(dot)
            text = QLabel(label)
            text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            legend.addWidget(text)

        legend.addStretch()
        layout.addLayout(legend)

    def set_data(self, history: list):
        """Update chart with job history data."""
        # Clear existing bars
        while self._chart_layout.count():
            item = self._chart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history:
            return

        max_total = max((h.total for h in history), default=1) or 1

        for entry in history:
            bar_widget = QWidget()
            bar_layout = QVBoxLayout(bar_widget)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            bar_layout.setSpacing(4)

            # Stacked bar
            bar_container = QWidget()
            bar_container.setFixedWidth(30)
            bar_container_layout = QVBoxLayout(bar_container)
            bar_container_layout.setContentsMargins(0, 0, 0, 0)
            bar_container_layout.setSpacing(1)

            # Calculate heights (max height = 100px)
            max_height = 100
            completed_height = (
                int((entry.completed / max_total) * max_height) if max_total > 0 else 0
            )
            failed_height = (
                int((entry.failed / max_total) * max_height) if max_total > 0 else 0
            )

            # Spacer for empty space
            empty_height = max_height - completed_height - failed_height
            if empty_height > 0:
                spacer = QWidget()
                spacer.setFixedHeight(empty_height)
                bar_container_layout.addWidget(spacer)

            # Failed bar (on top)
            if failed_height > 0:
                failed_bar = QFrame()
                failed_bar.setFixedHeight(failed_height)
                failed_bar.setStyleSheet(f"""
                    background-color: {COLORS['accent_error']};
                    border-radius: 2px;
                """)
                bar_container_layout.addWidget(failed_bar)

            # Completed bar (on bottom)
            if completed_height > 0:
                completed_bar = QFrame()
                completed_bar.setFixedHeight(completed_height)
                completed_bar.setStyleSheet(f"""
                    background-color: {COLORS['accent_success']};
                    border-radius: 2px;
                """)
                bar_container_layout.addWidget(completed_bar)

            bar_layout.addWidget(bar_container, alignment=Qt.AlignmentFlag.AlignBottom)

            # Date label
            date_parts = entry.date.split("-")
            date_label = QLabel(
                f"{date_parts[1]}/{date_parts[2]}"
                if len(date_parts) >= 3
                else entry.date
            )
            date_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bar_layout.addWidget(date_label)

            self._chart_layout.addWidget(bar_widget)

        self._chart_layout.addStretch()


class RecentJobsWidget(QFrame):
    """Widget showing recent job activity."""

    job_clicked = Signal(str)  # job_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QLabel("Recent Jobs")
        header.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
        """)
        layout.addWidget(header)

        self._jobs_container = QVBoxLayout()
        self._jobs_container.setSpacing(8)
        layout.addLayout(self._jobs_container)
        layout.addStretch()

    def set_jobs(self, jobs: List[Job]):
        """Update the jobs list."""
        # Clear existing
        while self._jobs_container.count():
            item = self._jobs_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for job in jobs[:5]:  # Show last 5
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 8, 0, 8)
            row_layout.setSpacing(12)

            # Workflow name
            name = QLabel(
                job.workflow_name[:30] + "..."
                if len(job.workflow_name) > 30
                else job.workflow_name
            )
            name.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
            row_layout.addWidget(name, stretch=1)

            # Status badge
            badge = StatusBadge(job.status.value)
            row_layout.addWidget(badge)

            self._jobs_container.addWidget(row)

        if not jobs:
            empty = QLabel("No recent jobs")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._jobs_container.addWidget(empty)


class RobotStatusWidget(QFrame):
    """Widget showing robot status overview."""

    robot_clicked = Signal(str)  # robot_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QLabel("Robot Status")
        header.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
        """)
        layout.addWidget(header)

        self._robots_container = QVBoxLayout()
        self._robots_container.setSpacing(8)
        layout.addLayout(self._robots_container)
        layout.addStretch()

    def set_robots(self, robots: List[Robot]):
        """Update the robots list."""
        # Clear existing
        while self._robots_container.count():
            item = self._robots_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for robot in robots[:5]:  # Show first 5
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 8, 0, 8)
            row_layout.setSpacing(12)

            # Status indicator
            status_color = {
                RobotStatus.ONLINE: COLORS["status_online"],
                RobotStatus.OFFLINE: COLORS["status_offline"],
                RobotStatus.BUSY: COLORS["status_busy"],
                RobotStatus.ERROR: COLORS["status_error"],
            }.get(robot.status, COLORS["text_muted"])

            indicator = QLabel("●")
            indicator.setStyleSheet(f"color: {status_color}; font-size: 12px;")
            row_layout.addWidget(indicator)

            # Robot name
            name = QLabel(robot.name)
            name.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
            row_layout.addWidget(name, stretch=1)

            # Status text
            status_text = QLabel(robot.status.value.title())
            status_text.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 12px;"
            )
            row_layout.addWidget(status_text)

            self._robots_container.addWidget(row)

        if not robots:
            empty = QLabel("No robots registered")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._robots_container.addWidget(empty)


class DashboardView(QWidget):
    """Main dashboard view with KPIs and overview."""

    navigate_to = Signal(str)  # page name

    def __init__(self, service: OrchestratorService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._service = service
        self._setup_ui()

    def _setup_ui(self):
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Header
        header = SectionHeader("Dashboard", "Refresh")
        header.action_clicked.connect(
            lambda: asyncio.get_event_loop().create_task(self.refresh())
        )
        layout.addWidget(header)

        # KPI Cards Row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self._kpi_jobs_today = KPICard("Jobs Today", "0", "executions")
        self._kpi_jobs_today.clicked.connect(lambda: self.navigate_to.emit("jobs"))
        kpi_layout.addWidget(self._kpi_jobs_today)

        self._kpi_success_rate = KPICard("Success Rate", "0%", "today")
        kpi_layout.addWidget(self._kpi_success_rate)

        self._kpi_robots_online = KPICard("Robots Online", "0", "available")
        self._kpi_robots_online.clicked.connect(lambda: self.navigate_to.emit("robots"))
        kpi_layout.addWidget(self._kpi_robots_online)

        self._kpi_queue_depth = KPICard("Queue Depth", "0", "pending jobs")
        self._kpi_queue_depth.clicked.connect(lambda: self.navigate_to.emit("jobs"))
        kpi_layout.addWidget(self._kpi_queue_depth)

        layout.addLayout(kpi_layout)

        # Charts and Lists Row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Job Activity Chart
        self._job_chart = JobActivityChart()
        charts_row.addWidget(self._job_chart, stretch=2)

        # Right column
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        self._recent_jobs = RecentJobsWidget()
        right_col.addWidget(self._recent_jobs)

        self._robot_status = RobotStatusWidget()
        right_col.addWidget(self._robot_status)

        charts_row.addLayout(right_col, stretch=1)
        layout.addLayout(charts_row)

        # Additional metrics row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        self._kpi_throughput = KPICard("Throughput", "0/hr", "jobs per hour")
        metrics_row.addWidget(self._kpi_throughput)

        self._kpi_avg_time = KPICard("Avg Execution", "-", "time per job")
        metrics_row.addWidget(self._kpi_avg_time)

        self._kpi_workflows = KPICard("Workflows", "0", "published")
        self._kpi_workflows.clicked.connect(lambda: self.navigate_to.emit("workflows"))
        metrics_row.addWidget(self._kpi_workflows)

        self._kpi_schedules = KPICard("Active Schedules", "0", "running")
        self._kpi_schedules.clicked.connect(lambda: self.navigate_to.emit("schedules"))
        metrics_row.addWidget(self._kpi_schedules)

        layout.addLayout(metrics_row)
        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    async def refresh(self):
        """Refresh dashboard data."""
        try:
            # Get metrics
            metrics = await self._service.get_dashboard_metrics()

            # Update KPIs
            self._kpi_jobs_today.set_value(str(metrics.total_jobs_today))
            self._kpi_success_rate.set_value(f"{metrics.success_rate_today:.0f}%")
            self._kpi_robots_online.set_value(
                f"{metrics.robots_online}/{metrics.robots_total}"
            )
            self._kpi_queue_depth.set_value(str(metrics.jobs_queued))
            self._kpi_throughput.set_value(f"{metrics.throughput_per_hour:.1f}/hr")
            self._kpi_avg_time.set_value(metrics.avg_execution_time_formatted)
            self._kpi_workflows.set_value(str(metrics.workflows_published))
            self._kpi_schedules.set_value(str(metrics.schedules_active))

            # Get job history for chart
            history = await self._service.get_job_history(days=7)
            self._job_chart.set_data(history)

            # Get recent jobs
            jobs = await self._service.get_jobs(limit=5)
            self._recent_jobs.set_jobs(jobs)

            # Get robots
            robots = await self._service.get_robots()
            self._robot_status.set_robots(robots)

        except Exception as e:
            from loguru import logger

            logger.error(f"Failed to refresh dashboard: {e}")
