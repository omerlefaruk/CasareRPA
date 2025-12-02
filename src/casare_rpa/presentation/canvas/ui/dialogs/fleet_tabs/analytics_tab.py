"""
Analytics Tab Widget for Fleet Dashboard.

Displays fleet statistics and charts using Qt widgets.
Supports real-time queue metrics updates via WebSocketBridge.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QFrame,
    QPushButton,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont


if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.services.websocket_bridge import (
        QueueMetricsUpdate,
    )


class StatCard(QFrame):
    """Card widget displaying a single statistic."""

    def __init__(
        self,
        title: str,
        value: str = "-",
        subtitle: str = "",
        color: QColor = QColor(0x4C, 0xAF, 0x50),
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._color = color
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(150, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_label = QLabel(self._title)
        title_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(title_label)

        self._value_label = QLabel(self._value)
        self._value_label.setStyleSheet(
            f"color: {self._color.name()}; font-size: 28px; font-weight: bold;"
        )
        layout.addWidget(self._value_label)

        self._subtitle_label = QLabel(self._subtitle)
        self._subtitle_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(self._subtitle_label)

        self.setStyleSheet("""
            StatCard {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
        """)

    def set_value(self, value: str, subtitle: str = "") -> None:
        """Update card value and subtitle."""
        self._value_label.setText(value)
        if subtitle:
            self._subtitle_label.setText(subtitle)


class BarChart(QWidget):
    """Simple horizontal bar chart widget."""

    def __init__(
        self,
        title: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._data: List[tuple] = []
        self._max_value = 100
        self.setMinimumHeight(150)

    def set_data(self, data: List[tuple], max_value: Optional[float] = None) -> None:
        """Set chart data as list of (label, value, color) tuples."""
        self._data = data
        if max_value:
            self._max_value = max_value
        elif data:
            self._max_value = max(d[1] for d in data) * 1.1 if data else 100
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the bar chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        painter.fillRect(0, 0, width, height, QColor("#2a2a2a"))

        if self._title:
            painter.setPen(QPen(QColor("#888888")))
            painter.setFont(QFont("", 11))
            painter.drawText(10, 20, self._title)

        if not self._data:
            painter.setPen(QPen(QColor("#666666")))
            painter.drawText(width // 2 - 30, height // 2, "No data")
            return

        label_width = 100
        chart_left = label_width + 10
        chart_width = width - chart_left - 20
        bar_height = min(25, (height - 40) // len(self._data) - 5)
        y_offset = 35

        for i, (label, value, color) in enumerate(self._data):
            y = y_offset + i * (bar_height + 5)

            painter.setPen(QPen(QColor("#e0e0e0")))
            painter.setFont(QFont("", 9))
            painter.drawText(5, int(y + bar_height * 0.7), label[:15])

            bar_width = (
                int((value / self._max_value) * chart_width)
                if self._max_value > 0
                else 0
            )
            painter.fillRect(chart_left, int(y), bar_width, bar_height, QColor(color))

            painter.setPen(QPen(QColor("#e0e0e0")))
            value_str = f"{value:.0f}" if isinstance(value, float) else str(value)
            painter.drawText(
                chart_left + bar_width + 5, int(y + bar_height * 0.7), value_str
            )


class PieChart(QWidget):
    """Simple pie chart widget."""

    def __init__(
        self,
        title: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._data: List[tuple] = []
        self.setMinimumSize(200, 200)

    def set_data(self, data: List[tuple]) -> None:
        """Set chart data as list of (label, value, color) tuples."""
        self._data = data
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the pie chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        painter.fillRect(0, 0, width, height, QColor("#2a2a2a"))

        if self._title:
            painter.setPen(QPen(QColor("#888888")))
            painter.setFont(QFont("", 11))
            painter.drawText(10, 20, self._title)

        if not self._data:
            painter.setPen(QPen(QColor("#666666")))
            painter.drawText(width // 2 - 30, height // 2, "No data")
            return

        total = sum(d[1] for d in self._data)
        if total == 0:
            painter.setPen(QPen(QColor("#666666")))
            painter.drawText(width // 2 - 30, height // 2, "No data")
            return

        size = min(width, height - 40) - 80
        x = (width - size) // 2 - 40
        y = 35

        start_angle = 90 * 16

        for label, value, color in self._data:
            span_angle = int((value / total) * 360 * 16)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor("#2a2a2a"), 2))
            painter.drawPie(x, y, size, size, start_angle, span_angle)
            start_angle += span_angle

        legend_x = x + size + 20
        legend_y = y + 10

        painter.setFont(QFont("", 9))
        for i, (label, value, color) in enumerate(self._data):
            ly = legend_y + i * 20
            painter.fillRect(legend_x, ly, 12, 12, QColor(color))
            painter.setPen(QPen(QColor("#e0e0e0")))
            pct = (value / total * 100) if total > 0 else 0
            painter.drawText(legend_x + 18, ly + 10, f"{label}: {pct:.1f}%")


class AnalyticsTabWidget(QWidget):
    """
    Widget for displaying fleet analytics and statistics.

    Features:
    - Statistics cards (robots online, jobs today, success rate)
    - Job status distribution (pie chart)
    - Robot utilization (bar chart)
    - Error distribution (bar chart)
    - Jobs over time (simple trend)

    Signals:
        refresh_requested: Emitted when refresh is clicked
    """

    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._analytics: Dict[str, Any] = {}
        self._setup_ui()
        self._apply_styles()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._request_refresh)
        self._refresh_timer.start(60000)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.addStretch()

        self._last_updated_label = QLabel("Last updated: -")
        self._last_updated_label.setStyleSheet("color: #888888;")
        toolbar.addWidget(self._last_updated_label)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self._card_robots_online = StatCard(
            "Robots Online", "-", "of total", QColor(0x4C, 0xAF, 0x50)
        )
        cards_layout.addWidget(self._card_robots_online)

        self._card_jobs_today = StatCard(
            "Jobs Today", "-", "completed", QColor(0x21, 0x96, 0xF3)
        )
        cards_layout.addWidget(self._card_jobs_today)

        self._card_success_rate = StatCard(
            "Success Rate", "-", "last 7 days", QColor(0x00, 0xC8, 0x53)
        )
        cards_layout.addWidget(self._card_success_rate)

        self._card_avg_duration = StatCard(
            "Avg Duration", "-", "per job", QColor(0xFF, 0x98, 0x00)
        )
        cards_layout.addWidget(self._card_avg_duration)

        self._card_queue_depth = StatCard(
            "Queue Depth", "-", "pending jobs", QColor(0x9C, 0x27, 0xB0)
        )
        cards_layout.addWidget(self._card_queue_depth)

        content_layout.addLayout(cards_layout)

        charts_row1 = QHBoxLayout()
        charts_row1.setSpacing(12)

        job_status_group = QGroupBox("Job Status Distribution")
        job_status_layout = QVBoxLayout(job_status_group)
        self._job_status_chart = PieChart()
        job_status_layout.addWidget(self._job_status_chart)
        charts_row1.addWidget(job_status_group)

        robot_util_group = QGroupBox("Robot Utilization")
        robot_util_layout = QVBoxLayout(robot_util_group)
        self._robot_util_chart = BarChart()
        robot_util_layout.addWidget(self._robot_util_chart)
        charts_row1.addWidget(robot_util_group)

        content_layout.addLayout(charts_row1)

        charts_row2 = QHBoxLayout()
        charts_row2.setSpacing(12)

        error_dist_group = QGroupBox("Error Distribution (Last 7 Days)")
        error_dist_layout = QVBoxLayout(error_dist_group)
        self._error_dist_chart = BarChart()
        error_dist_layout.addWidget(self._error_dist_chart)
        charts_row2.addWidget(error_dist_group)

        slowest_group = QGroupBox("Slowest Workflows (Avg Duration)")
        slowest_layout = QVBoxLayout(slowest_group)
        self._slowest_chart = BarChart()
        slowest_layout.addWidget(self._slowest_chart)
        charts_row2.addWidget(slowest_group)

        content_layout.addLayout(charts_row2)

        percentiles_group = QGroupBox("Duration Percentiles (Last 7 Days)")
        percentiles_layout = QHBoxLayout(percentiles_group)

        self._p50_card = StatCard("P50", "-", "median", QColor(0x4C, 0xAF, 0x50))
        self._p90_card = StatCard(
            "P90", "-", "90th percentile", QColor(0xFF, 0xC1, 0x07)
        )
        self._p99_card = StatCard(
            "P99", "-", "99th percentile", QColor(0xF4, 0x43, 0x36)
        )

        percentiles_layout.addWidget(self._p50_card)
        percentiles_layout.addWidget(self._p90_card)
        percentiles_layout.addWidget(self._p99_card)

        content_layout.addWidget(percentiles_group)
        content_layout.addStretch()

        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #e0e0e0;
            }
            QScrollArea {
                background: transparent;
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

    def update_analytics(self, analytics: Dict[str, Any]) -> None:
        """Update all analytics widgets with new data."""
        self._analytics = analytics

        fleet = analytics.get("fleet", {})
        self._card_robots_online.set_value(
            str(fleet.get("active_robots", 0)),
            f"of {fleet.get('total_robots', 0)} total",
        )

        jobs = analytics.get("jobs", {})
        self._card_jobs_today.set_value(
            str(jobs.get("completed_today", 0)), f"{jobs.get('active_jobs', 0)} running"
        )

        success_rate = analytics.get("success_rate", 0)
        self._card_success_rate.set_value(f"{success_rate:.1f}%", "last 7 days")

        avg_duration = analytics.get("average_duration_ms", 0) / 1000
        if avg_duration >= 60:
            duration_str = f"{avg_duration / 60:.1f}m"
        else:
            duration_str = f"{avg_duration:.1f}s"
        self._card_avg_duration.set_value(duration_str, "per job")

        queue_depth = fleet.get("queue_depth", 0)
        self._card_queue_depth.set_value(str(queue_depth), "pending jobs")

        job_status_data = [
            ("Completed", jobs.get("completed", 0), "#00C853"),
            ("Running", jobs.get("running", 0), "#4CAF50"),
            ("Pending", jobs.get("pending", 0), "#9E9E9E"),
            ("Failed", jobs.get("failed", 0), "#F44336"),
        ]
        self._job_status_chart.set_data(job_status_data)

        robot_util = analytics.get("robot_utilization", [])
        robot_data = []
        for r in robot_util[:8]:
            name = r.get("name", "Robot")[:12]
            util = r.get("utilization", 0)
            color = "#4CAF50" if util < 70 else "#FFC107" if util < 90 else "#F44336"
            robot_data.append((name, util, color))
        self._robot_util_chart.set_data(robot_data, 100)

        error_dist = analytics.get("error_distribution", [])
        error_data = []
        for e in error_dist[:6]:
            error_type = e.get("error_type", "Unknown")[:20]
            count = e.get("count", 0)
            error_data.append((error_type, count, "#F44336"))
        self._error_dist_chart.set_data(error_data)

        slowest = analytics.get("slowest_workflows", [])
        slowest_data = []
        for w in slowest[:5]:
            name = w.get("workflow_name", "Workflow")[:15]
            duration = w.get("average_duration_ms", 0) / 1000
            slowest_data.append((name, duration, "#FF9800"))
        self._slowest_chart.set_data(slowest_data)

        p50 = analytics.get("p50_duration_ms", 0) / 1000
        p90 = analytics.get("p90_duration_ms", 0) / 1000
        p99 = analytics.get("p99_duration_ms", 0) / 1000

        self._p50_card.set_value(f"{p50:.1f}s" if p50 < 60 else f"{p50/60:.1f}m")
        self._p90_card.set_value(f"{p90:.1f}s" if p90 < 60 else f"{p90/60:.1f}m")
        self._p99_card.set_value(f"{p99:.1f}s" if p99 < 60 else f"{p99/60:.1f}m")

        self._last_updated_label.setText(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _request_refresh(self) -> None:
        """Request analytics refresh."""
        self.refresh_requested.emit()

    def set_refreshing(self, refreshing: bool) -> None:
        """Set refresh button state."""
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")

    # ==================== Real-Time Updates ====================

    def update_queue_metrics(self, update: "QueueMetricsUpdate") -> None:
        """
        Handle real-time queue metrics update from WebSocket.

        Updates queue depth card without full analytics refresh.

        Args:
            update: QueueMetricsUpdate from WebSocketBridge
        """
        self._card_queue_depth.set_value(str(update.depth), "pending jobs")

        # Update last updated timestamp
        self._last_updated_label.setText(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
        )

    def update_fleet_status(self, active_robots: int, total_robots: int) -> None:
        """
        Update fleet status in real-time.

        Args:
            active_robots: Number of online robots
            total_robots: Total number of robots
        """
        self._card_robots_online.set_value(
            str(active_robots), f"of {total_robots} total"
        )

    def update_active_jobs(self, running: int, completed_today: int) -> None:
        """
        Update active jobs count in real-time.

        Args:
            running: Number of running jobs
            completed_today: Jobs completed today
        """
        self._card_jobs_today.set_value(str(completed_today), f"{running} running")
