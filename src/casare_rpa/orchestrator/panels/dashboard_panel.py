"""
Dashboard panel - KPI cards and summary charts.
Overview of system health and job statistics.
"""

from typing import List, Dict
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter

from ..theme import THEME
from ..models import DashboardMetrics


class KPICard(QFrame):
    """KPI metric card."""

    clicked = Signal(str)  # metric_name

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        color: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._color = color or THEME.accent_primary
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-top: 3px solid {self._color};
                border-radius: 3px;
            }}
            QFrame:hover {{
                background-color: {THEME.bg_hover};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Title
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        """)
        layout.addWidget(self._title_label)

        # Value
        self._value_label = QLabel(self._value)
        self._value_label.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 28px;
            font-weight: 700;
        """)
        layout.addWidget(self._value_label)

        # Subtitle
        if self._subtitle:
            self._subtitle_label = QLabel(self._subtitle)
            self._subtitle_label.setStyleSheet(f"""
                color: {THEME.text_secondary};
                font-size: 11px;
            """)
            layout.addWidget(self._subtitle_label)

        layout.addStretch()

    def set_value(self, value: str, subtitle: str = None):
        self._value_label.setText(value)
        if subtitle and hasattr(self, "_subtitle_label"):
            self._subtitle_label.setText(subtitle)

    def mousePressEvent(self, event):
        self.clicked.emit(self._title)
        super().mousePressEvent(event)


class MiniChart(QWidget):
    """Simple bar chart for job history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict] = []
        self.setMinimumHeight(120)
        self.setStyleSheet(f"background-color: {THEME.bg_panel};")

    def set_data(self, data: List[Dict]):
        """Set chart data. Each item: {date, completed, failed, total}"""
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        padding = 40
        chart_width = rect.width() - padding * 2
        chart_height = rect.height() - padding

        if chart_width <= 0 or chart_height <= 0:
            return

        # Find max value
        max_val = max((d.get("total", 0) for d in self._data), default=1)
        if max_val == 0:
            max_val = 1

        bar_width = min(40, chart_width // len(self._data) - 4) if self._data else 40
        spacing = (chart_width - bar_width * len(self._data)) // max(len(self._data), 1)

        # Draw bars
        x = padding
        for item in self._data:
            completed = item.get("completed", 0)
            failed = item.get("failed", 0)
            total = item.get("total", 0)

            # Calculate heights
            completed_height = (
                int((completed / max_val) * chart_height) if max_val > 0 else 0
            )
            failed_height = int((failed / max_val) * chart_height) if max_val > 0 else 0

            # Draw completed bar (green)
            if completed_height > 0:
                painter.fillRect(
                    x,
                    rect.height() - padding - completed_height,
                    bar_width,
                    completed_height,
                    QColor(THEME.status_online),
                )

            # Draw failed bar (red, stacked on top)
            if failed_height > 0:
                painter.fillRect(
                    x,
                    rect.height() - padding - completed_height - failed_height,
                    bar_width,
                    failed_height,
                    QColor(THEME.status_error),
                )

            # Date label
            painter.setPen(QColor(THEME.text_muted))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            date_str = item.get("date", "")[-5:]  # Show only MM-DD
            painter.drawText(x, rect.height() - 5, date_str)

            x += bar_width + spacing

        # Y-axis labels
        painter.setPen(QColor(THEME.text_muted))
        painter.drawText(5, padding, str(max_val))
        painter.drawText(5, rect.height() - padding, "0")


class StatusSummary(QFrame):
    """Summary of active/queued/completed jobs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-radius: 3px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Job Status")
        title.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        """)
        layout.addWidget(title)

        # Status bars
        self._statuses = {}
        status_configs = [
            ("Running", THEME.job_running, 0),
            ("Queued", THEME.job_queued, 0),
            ("Completed", THEME.job_completed, 0),
            ("Failed", THEME.job_failed, 0),
        ]

        for name, color, count in status_configs:
            row = QHBoxLayout()
            row.setSpacing(8)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 8px;")
            dot.setFixedWidth(12)
            row.addWidget(dot)

            label = QLabel(name)
            label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
            label.setFixedWidth(80)
            row.addWidget(label)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {THEME.progress_bg};
                    border: none;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 4px;
                }}
            """)
            row.addWidget(bar, 1)

            count_label = QLabel(str(count))
            count_label.setStyleSheet(
                f"color: {THEME.text_primary}; font-size: 11px; font-weight: 600;"
            )
            count_label.setFixedWidth(40)
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(count_label)

            layout.addLayout(row)
            self._statuses[name.lower()] = (bar, count_label)

    def set_counts(self, running: int, queued: int, completed: int, failed: int):
        total = running + queued + completed + failed
        if total == 0:
            total = 1

        self._statuses["running"][0].setValue(int(running / total * 100))
        self._statuses["running"][1].setText(str(running))

        self._statuses["queued"][0].setValue(int(queued / total * 100))
        self._statuses["queued"][1].setText(str(queued))

        self._statuses["completed"][0].setValue(int(completed / total * 100))
        self._statuses["completed"][1].setText(str(completed))

        self._statuses["failed"][0].setValue(int(failed / total * 100))
        self._statuses["failed"][1].setText(str(failed))


class RobotsSummary(QFrame):
    """Summary of robot status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-radius: 3px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Robot Status")
        title.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        """)
        layout.addWidget(title)

        # Grid of status counts
        grid = QGridLayout()
        grid.setSpacing(12)

        self._online = self._create_count("Online", "0", THEME.status_online)
        grid.addWidget(self._online, 0, 0)

        self._busy = self._create_count("Busy", "0", THEME.status_busy)
        grid.addWidget(self._busy, 0, 1)

        self._offline = self._create_count("Offline", "0", THEME.status_offline)
        grid.addWidget(self._offline, 1, 0)

        self._error = self._create_count("Error", "0", THEME.status_error)
        grid.addWidget(self._error, 1, 1)

        layout.addLayout(grid)

        # Utilization bar
        layout.addSpacing(8)

        util_label = QLabel("Average Utilization")
        util_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        layout.addWidget(util_label)

        util_row = QHBoxLayout()
        self._util_bar = QProgressBar()
        self._util_bar.setRange(0, 100)
        self._util_bar.setValue(0)
        self._util_bar.setFixedHeight(12)
        self._util_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME.progress_bg};
                border: none;
                border-radius: 6px;
                text-align: center;
                color: {THEME.text_primary};
                font-size: 9px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME.accent_primary};
                border-radius: 6px;
            }}
        """)
        util_row.addWidget(self._util_bar)

        self._util_label = QLabel("0%")
        self._util_label.setStyleSheet(
            f"color: {THEME.text_primary}; font-size: 11px; font-weight: 600;"
        )
        self._util_label.setFixedWidth(40)
        util_row.addWidget(self._util_label)

        layout.addLayout(util_row)

    def _create_count(self, label: str, value: str, color: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        return widget

    def set_counts(
        self, online: int, busy: int, offline: int, error: int, utilization: float
    ):
        self._online.findChild(QLabel, "value").setText(str(online))
        self._busy.findChild(QLabel, "value").setText(str(busy))
        self._offline.findChild(QLabel, "value").setText(str(offline))
        self._error.findChild(QLabel, "value").setText(str(error))

        self._util_bar.setValue(int(utilization))
        self._util_label.setText(f"{utilization:.0f}%")


class DashboardPanel(QWidget):
    """
    Dashboard panel with KPIs and charts.
    Provides system overview.
    """

    navigate_to = Signal(str)  # panel_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.setStyleSheet(f"background-color: {THEME.bg_panel};")

        # KPI Cards row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self._jobs_today = KPICard("Jobs Today", "0", "completed", THEME.accent_primary)
        self._jobs_today.clicked.connect(lambda: self.navigate_to.emit("jobs"))
        kpi_row.addWidget(self._jobs_today)

        self._success_rate = KPICard(
            "Success Rate", "0%", "last 24h", THEME.status_online
        )
        self._success_rate.clicked.connect(lambda: self.navigate_to.emit("jobs"))
        kpi_row.addWidget(self._success_rate)

        self._active_robots = KPICard(
            "Active Robots", "0", "online", THEME.accent_secondary
        )
        self._active_robots.clicked.connect(lambda: self.navigate_to.emit("robots"))
        kpi_row.addWidget(self._active_robots)

        self._avg_duration = KPICard("Avg Duration", "-", "per job", THEME.status_busy)
        kpi_row.addWidget(self._avg_duration)

        layout.addLayout(kpi_row)

        # Main content row
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # Left column - job chart
        left_col = QVBoxLayout()
        left_col.setSpacing(8)

        chart_label = QLabel("Job Activity (Last 7 Days)")
        chart_label.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        """)
        left_col.addWidget(chart_label)

        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-radius: 3px;
            }}
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(8, 8, 8, 8)

        self._chart = MiniChart()
        chart_layout.addWidget(self._chart)

        # Legend
        legend = QHBoxLayout()
        legend.setSpacing(16)

        completed_legend = QHBoxLayout()
        completed_legend.setSpacing(4)
        completed_dot = QLabel("■")
        completed_dot.setStyleSheet(f"color: {THEME.status_online}; font-size: 10px;")
        completed_legend.addWidget(completed_dot)
        completed_text = QLabel("Completed")
        completed_text.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        completed_legend.addWidget(completed_text)
        legend.addLayout(completed_legend)

        failed_legend = QHBoxLayout()
        failed_legend.setSpacing(4)
        failed_dot = QLabel("■")
        failed_dot.setStyleSheet(f"color: {THEME.status_error}; font-size: 10px;")
        failed_legend.addWidget(failed_dot)
        failed_text = QLabel("Failed")
        failed_text.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        failed_legend.addWidget(failed_text)
        legend.addLayout(failed_legend)

        legend.addStretch()
        chart_layout.addLayout(legend)

        left_col.addWidget(chart_frame, 1)
        content_row.addLayout(left_col, 2)

        # Right column - summaries
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        self._job_summary = StatusSummary()
        right_col.addWidget(self._job_summary)

        self._robot_summary = RobotsSummary()
        right_col.addWidget(self._robot_summary)

        right_col.addStretch()
        content_row.addLayout(right_col, 1)

        layout.addLayout(content_row, 1)

    def set_metrics(self, metrics: DashboardMetrics):
        """Update dashboard with metrics."""
        self._jobs_today.set_value(
            str(metrics.jobs_completed_today + metrics.jobs_failed_today),
            f"{metrics.jobs_completed_today} completed",
        )
        self._success_rate.set_value(f"{metrics.success_rate_today:.0f}%")
        self._active_robots.set_value(
            str(metrics.robots_online), f"of {metrics.robots_total} total"
        )
        self._avg_duration.set_value(metrics.avg_execution_time_formatted)

        self._job_summary.set_counts(
            metrics.jobs_running,
            metrics.jobs_queued,
            metrics.jobs_completed_today,
            metrics.jobs_failed_today,
        )

        self._robot_summary.set_counts(
            metrics.robots_online,
            metrics.robots_busy,
            metrics.robots_total - metrics.robots_online - metrics.robots_busy,
            0,  # Error count not in metrics
            metrics.robot_utilization,
        )

    def set_history(self, history: List[Dict]):
        """Update job history chart."""
        self._chart.set_data(history)
