"""
Robot Metrics Panel for Orchestrator.

Displays real-time metrics from robots:
- CPU and memory usage
- Job execution statistics
- Connection health
- Error rates
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QProgressBar, QScrollArea, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QBrush

from ..theme import THEME


class MetricCard(QFrame):
    """Individual metric display card."""

    def __init__(
        self,
        title: str,
        value: str = "-",
        subtitle: str = "",
        parent=None
    ):
        super().__init__(parent)
        self._setup_ui(title, value, subtitle)

    def _setup_ui(self, title: str, value: str, subtitle: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Title
        self._title = QLabel(title)
        self._title.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 11px;
            font-weight: 500;
        """)
        layout.addWidget(self._title)

        # Value
        self._value = QLabel(value)
        self._value.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 24px;
            font-weight: 700;
        """)
        layout.addWidget(self._value)

        # Subtitle
        if subtitle:
            self._subtitle = QLabel(subtitle)
            self._subtitle.setStyleSheet(f"""
                color: {THEME.text_muted};
                font-size: 10px;
            """)
            layout.addWidget(self._subtitle)
        else:
            self._subtitle = None

    def set_value(self, value: str):
        """Update the metric value."""
        self._value.setText(value)

    def set_subtitle(self, subtitle: str):
        """Update the subtitle."""
        if self._subtitle:
            self._subtitle.setText(subtitle)


class ResourceBar(QFrame):
    """Resource usage bar (CPU/Memory)."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._value = 0
        self._label = label
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # Label
        self._label_widget = QLabel(self._label)
        self._label_widget.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 11px;
            min-width: 60px;
        """)
        layout.addWidget(self._label_widget)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setFormat("%v%")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                height: 18px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {THEME.accent_primary};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self._bar, 1)

    def set_value(self, value: float):
        """Set the resource usage value (0-100)."""
        self._value = int(value)
        self._bar.setValue(self._value)

        # Color based on usage
        if value > 90:
            color = THEME.status_error
        elif value > 75:
            color = THEME.status_warning
        else:
            color = THEME.accent_primary

        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                height: 18px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)


class RobotMetricsCard(QFrame):
    """Card showing metrics for a single robot."""

    def __init__(self, robot_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._robot_id = robot_data.get("id", "")
        self._setup_ui(robot_data)

    def _setup_ui(self, robot: Dict[str, Any]):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_panel};
                border: 1px solid {THEME.border};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header with robot name and status
        header = QHBoxLayout()

        name = robot.get("name", "Unknown Robot")
        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 14px;
            font-weight: 600;
        """)
        header.addWidget(self._name_label)

        header.addStretch()

        # Status indicator
        status = robot.get("status", "offline")
        status_color = self._get_status_color(status)
        self._status_label = QLabel(status.upper())
        self._status_label.setStyleSheet(f"""
            color: {status_color};
            font-size: 11px;
            font-weight: 600;
        """)
        header.addWidget(self._status_label)

        layout.addLayout(header)

        # Resource bars
        metrics = robot.get("metrics", {})

        self._cpu_bar = ResourceBar("CPU")
        self._cpu_bar.set_value(metrics.get("cpu_percent", 0))
        layout.addWidget(self._cpu_bar)

        self._memory_bar = ResourceBar("Memory")
        self._memory_bar.set_value(metrics.get("memory_percent", 0))
        layout.addWidget(self._memory_bar)

        # Statistics
        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)

        # Job stats
        summary = metrics.get("summary", {})
        total_jobs = summary.get("total_jobs", 0)
        success_rate = summary.get("success_rate_percent", 0)

        self._add_stat(stats_layout, 0, 0, "Total Jobs", str(total_jobs))
        self._add_stat(stats_layout, 0, 1, "Success Rate", f"{success_rate:.1f}%")

        current_job = summary.get("current_job")
        if current_job:
            self._add_stat(stats_layout, 1, 0, "Current Job", current_job[:12] + "...")
        else:
            self._add_stat(stats_layout, 1, 0, "Current Job", "-")

        last_seen = robot.get("last_seen", "")
        if last_seen:
            # Format last seen time
            try:
                from datetime import datetime
                if isinstance(last_seen, str):
                    dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00').replace('+00:00', ''))
                    last_seen = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                pass
        self._add_stat(stats_layout, 1, 1, "Last Seen", last_seen or "-")

        layout.addLayout(stats_layout)

    def _add_stat(self, layout: QGridLayout, row: int, col: int, label: str, value: str):
        """Add a statistic to the grid."""
        frame = QFrame()
        frame.setStyleSheet(f"background: transparent;")
        v_layout = QVBoxLayout(frame)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 10px;
        """)
        v_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 12px;
            font-weight: 500;
        """)
        v_layout.addWidget(value_widget)

        layout.addWidget(frame, row, col)

    def _get_status_color(self, status: str) -> str:
        """Get color for robot status."""
        status_colors = {
            "online": THEME.status_success,
            "busy": THEME.status_warning,
            "offline": THEME.text_muted,
            "error": THEME.status_error,
            "maintenance": THEME.accent_secondary,
        }
        return status_colors.get(status.lower(), THEME.text_muted)

    def update_metrics(self, robot: Dict[str, Any]):
        """Update the card with new metrics."""
        status = robot.get("status", "offline")
        status_color = self._get_status_color(status)
        self._status_label.setText(status.upper())
        self._status_label.setStyleSheet(f"""
            color: {status_color};
            font-size: 11px;
            font-weight: 600;
        """)

        metrics = robot.get("metrics", {})
        self._cpu_bar.set_value(metrics.get("cpu_percent", 0))
        self._memory_bar.set_value(metrics.get("memory_percent", 0))


class MetricsPanel(QWidget):
    """
    Main metrics panel showing robot statistics and health.

    Displays:
    - Summary metrics (total robots, jobs, success rate)
    - Individual robot metrics cards
    - Resource usage charts
    """

    robot_selected = Signal(str)  # robot_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._robot_cards: Dict[str, RobotMetricsCard] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_panel};
            }}
        """)

        # Header
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("Robot Metrics")
        title.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 14px;
            font-weight: 600;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Refresh button
        refresh_label = QLabel("Auto-refresh: 5s")
        refresh_label.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 10px;
        """)
        header_layout.addWidget(refresh_label)

        layout.addWidget(header)

        # Summary metrics
        summary_frame = QWidget()
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(12)

        self._total_robots_card = MetricCard("Total Robots", "0", "registered")
        summary_layout.addWidget(self._total_robots_card)

        self._online_robots_card = MetricCard("Online", "0", "available")
        summary_layout.addWidget(self._online_robots_card)

        self._busy_robots_card = MetricCard("Busy", "0", "executing jobs")
        summary_layout.addWidget(self._busy_robots_card)

        self._avg_utilization_card = MetricCard("Avg Utilization", "0%", "across all robots")
        summary_layout.addWidget(self._avg_utilization_card)

        layout.addWidget(summary_frame)

        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {THEME.border_dark};")
        layout.addWidget(separator)

        # Robot cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {THEME.bg_panel};
            }}
        """)

        self._cards_container = QWidget()
        self._cards_layout = QGridLayout(self._cards_container)
        self._cards_layout.setContentsMargins(12, 12, 12, 12)
        self._cards_layout.setSpacing(12)

        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll, 1)

    def set_robots(self, robots: List[Dict[str, Any]]):
        """Update the panel with robot data."""
        # Update summary
        total = len(robots)
        online = len([r for r in robots if r.get("status") == "online"])
        busy = len([r for r in robots if r.get("status") == "busy"])

        self._total_robots_card.set_value(str(total))
        self._online_robots_card.set_value(str(online))
        self._busy_robots_card.set_value(str(busy))

        # Calculate average utilization
        if total > 0:
            total_util = sum(
                r.get("metrics", {}).get("summary", {}).get("robot_utilization", 0)
                for r in robots
            )
            avg_util = total_util / total
            self._avg_utilization_card.set_value(f"{avg_util:.1f}%")
        else:
            self._avg_utilization_card.set_value("0%")

        # Update or create robot cards
        existing_ids = set(self._robot_cards.keys())
        new_ids = {r.get("id") for r in robots if r.get("id")}

        # Remove cards for robots no longer present
        for robot_id in existing_ids - new_ids:
            card = self._robot_cards.pop(robot_id)
            card.setParent(None)
            card.deleteLater()

        # Update or create cards
        row, col = 0, 0
        max_cols = 3

        for robot in robots:
            robot_id = robot.get("id")
            if not robot_id:
                continue

            if robot_id in self._robot_cards:
                # Update existing card
                self._robot_cards[robot_id].update_metrics(robot)
            else:
                # Create new card
                card = RobotMetricsCard(robot)
                self._robot_cards[robot_id] = card
                self._cards_layout.addWidget(card, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def update_robot(self, robot: Dict[str, Any]):
        """Update a single robot's metrics."""
        robot_id = robot.get("id")
        if robot_id and robot_id in self._robot_cards:
            self._robot_cards[robot_id].update_metrics(robot)
