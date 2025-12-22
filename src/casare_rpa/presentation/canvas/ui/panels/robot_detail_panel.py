"""
Robot Detail Panel UI Component.

Dockable panel showing detailed information about a selected robot.
Displays real-time metrics, current job status, recent job history, and logs.
"""

from typing import Optional, List, Dict, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QHeaderView,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QFont

from loguru import logger

from casare_rpa.presentation.canvas.ui.theme import THEME

if TYPE_CHECKING:
    from casare_rpa.domain.orchestrator.entities.robot import Robot


class RobotDetailPanel(QDockWidget):
    """
    Panel showing detailed robot information.

    Features:
    - Robot info card with name, ID, status, capabilities
    - Real-time metrics (CPU, Memory progress bars)
    - Current job info with progress
    - Recent job history table
    - Quick action buttons (pause, stop, restart)
    - Log viewer with live updates

    Signals:
        pause_requested: Robot pause requested (robot_id)
        stop_requested: Robot stop requested (robot_id)
        restart_requested: Robot restart requested (robot_id)
        logs_refresh_requested: Logs refresh requested (robot_id)
    """

    pause_requested = Signal(str)
    stop_requested = Signal(str)
    restart_requested = Signal(str)
    logs_refresh_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize Robot Detail Panel."""
        super().__init__("Robot Details", parent)
        self.setObjectName("RobotDetailDock")

        self._current_robot: Optional["Robot"] = None
        self._current_robot_id: Optional[str] = None

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        # Start with no robot selected
        self._show_no_selection()

        logger.debug("RobotDetailPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(320)
        self.setMinimumHeight(400)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Robot header with name and actions
        header_layout = QHBoxLayout()

        self._robot_name_label = QLabel("No Robot Selected")
        self._robot_name_label.setStyleSheet(
            f"color: {THEME.text_primary}; font-size: 14px; font-weight: bold;"
        )
        header_layout.addWidget(self._robot_name_label, 1)

        # Action buttons
        self._pause_btn = QPushButton("⏸")
        self._pause_btn.setToolTip("Pause robot")
        self._pause_btn.setFixedSize(28, 28)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        header_layout.addWidget(self._pause_btn)

        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setToolTip("Stop robot")
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        header_layout.addWidget(self._stop_btn)

        self._restart_btn = QPushButton("↻")
        self._restart_btn.setToolTip("Restart robot")
        self._restart_btn.setFixedSize(28, 28)
        self._restart_btn.clicked.connect(self._on_restart_clicked)
        header_layout.addWidget(self._restart_btn)

        main_layout.addLayout(header_layout)

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)

        self._status_indicator = QLabel("●")
        self._status_indicator.setStyleSheet(f"color: {THEME.text_muted}; font-size: 16px;")
        status_layout.addWidget(self._status_indicator)

        self._status_label = QLabel("Unknown")
        self._status_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 12px;")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._robot_id_label = QLabel("")
        self._robot_id_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        status_layout.addWidget(self._robot_id_label)

        main_layout.addLayout(status_layout)

        # Splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Metrics group
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(4)

        metrics_label = QLabel("Metrics")
        metrics_label.setStyleSheet(
            f"color: {THEME.text_secondary}; font-size: 11px; font-weight: bold;"
        )
        metrics_layout.addWidget(metrics_label)

        # CPU progress bar
        cpu_row = QHBoxLayout()
        cpu_row.setSpacing(8)
        cpu_label = QLabel("CPU:")
        cpu_label.setFixedWidth(50)
        cpu_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        cpu_row.addWidget(cpu_label)

        self._cpu_bar = QProgressBar()
        self._cpu_bar.setRange(0, 100)
        self._cpu_bar.setValue(0)
        self._cpu_bar.setTextVisible(True)
        self._cpu_bar.setFixedHeight(18)
        cpu_row.addWidget(self._cpu_bar)

        metrics_layout.addLayout(cpu_row)

        # Memory progress bar
        mem_row = QHBoxLayout()
        mem_row.setSpacing(8)
        mem_label = QLabel("Memory:")
        mem_label.setFixedWidth(50)
        mem_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        mem_row.addWidget(mem_label)

        self._mem_bar = QProgressBar()
        self._mem_bar.setRange(0, 100)
        self._mem_bar.setValue(0)
        self._mem_bar.setTextVisible(True)
        self._mem_bar.setFixedHeight(18)
        mem_row.addWidget(self._mem_bar)

        metrics_layout.addLayout(mem_row)

        # Jobs row
        jobs_row = QHBoxLayout()
        jobs_row.setSpacing(8)
        jobs_label = QLabel("Jobs:")
        jobs_label.setFixedWidth(50)
        jobs_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        jobs_row.addWidget(jobs_label)

        self._jobs_label = QLabel("0 / 0")
        self._jobs_label.setStyleSheet(f"color: {THEME.text_primary}; font-size: 11px;")
        jobs_row.addWidget(self._jobs_label)
        jobs_row.addStretch()

        metrics_layout.addLayout(jobs_row)

        splitter.addWidget(metrics_widget)

        # Current job group
        job_widget = QWidget()
        job_layout = QVBoxLayout(job_widget)
        job_layout.setContentsMargins(0, 0, 0, 0)
        job_layout.setSpacing(4)

        job_header = QHBoxLayout()
        job_label = QLabel("Current Job")
        job_label.setStyleSheet(
            f"color: {THEME.text_secondary}; font-size: 11px; font-weight: bold;"
        )
        job_header.addWidget(job_label)
        job_header.addStretch()

        self._job_id_label = QLabel("")
        self._job_id_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        job_header.addWidget(self._job_id_label)

        job_layout.addLayout(job_header)

        self._job_name_label = QLabel("No active job")
        self._job_name_label.setStyleSheet(f"color: {THEME.text_primary}; font-size: 12px;")
        job_layout.addWidget(self._job_name_label)

        # Job progress bar
        self._job_progress_bar = QProgressBar()
        self._job_progress_bar.setRange(0, 100)
        self._job_progress_bar.setValue(0)
        self._job_progress_bar.setTextVisible(True)
        self._job_progress_bar.setFixedHeight(20)
        job_layout.addWidget(self._job_progress_bar)

        self._job_status_label = QLabel("")
        self._job_status_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        job_layout.addWidget(self._job_status_label)

        splitter.addWidget(job_widget)

        # Recent jobs table
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(4)

        history_label = QLabel("Recent Jobs")
        history_label.setStyleSheet(
            f"color: {THEME.text_secondary}; font-size: 11px; font-weight: bold;"
        )
        history_layout.addWidget(history_label)

        self._jobs_table = QTableWidget()
        self._jobs_table.setColumnCount(3)
        self._jobs_table.setHorizontalHeaderLabels(["Workflow", "Status", "Time"])
        self._jobs_table.setAlternatingRowColors(True)
        self._jobs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._jobs_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._jobs_table.verticalHeader().setVisible(False)

        header = self._jobs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        history_layout.addWidget(self._jobs_table)

        splitter.addWidget(history_widget)

        # Logs viewer
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        logs_layout.setContentsMargins(0, 0, 0, 0)
        logs_layout.setSpacing(4)

        logs_header = QHBoxLayout()
        logs_label = QLabel("Logs")
        logs_label.setStyleSheet(
            f"color: {THEME.text_secondary}; font-size: 11px; font-weight: bold;"
        )
        logs_header.addWidget(logs_label)
        logs_header.addStretch()

        self._clear_logs_btn = QPushButton("Clear")
        self._clear_logs_btn.setFixedHeight(20)
        self._clear_logs_btn.clicked.connect(self._on_clear_logs_clicked)
        logs_header.addWidget(self._clear_logs_btn)

        self._refresh_logs_btn = QPushButton("Refresh")
        self._refresh_logs_btn.setFixedHeight(20)
        self._refresh_logs_btn.clicked.connect(self._on_refresh_logs_clicked)
        logs_header.addWidget(self._refresh_logs_btn)

        logs_layout.addLayout(logs_header)

        self._logs_viewer = QTextEdit()
        self._logs_viewer.setReadOnly(True)
        self._logs_viewer.setFont(QFont("Consolas", 9))
        self._logs_viewer.setStyleSheet(
            f"background: {THEME.bg_darkest}; color: {THEME.text_primary}; "
            f"border: 1px solid {THEME.border};"
        )
        logs_layout.addWidget(self._logs_viewer)

        splitter.addWidget(logs_widget)

        # Set splitter sizes
        splitter.setSizes([80, 100, 120, 200])

        main_layout.addWidget(splitter, 1)

        self.setWidget(container)

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
            QPushButton {{
                background: {THEME.bg_light};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_medium};
                border-color: {THEME.accent_primary};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_dark};
            }}
            QPushButton:disabled {{
                background: {THEME.bg_light};
                color: {THEME.text_muted};
            }}
            QProgressBar {{
                background: {THEME.bg_darkest};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                text-align: center;
                color: {THEME.text_primary};
            }}
            QProgressBar::chunk {{
                background: {THEME.accent_primary};
                border-radius: 2px;
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
            QSplitter::handle {{
                background: {THEME.border};
                height: 2px;
            }}
        """)

    def _show_no_selection(self) -> None:
        """Show placeholder when no robot selected."""
        self._robot_name_label.setText("No Robot Selected")
        self._status_indicator.setStyleSheet(f"color: {THEME.text_muted}; font-size: 16px;")
        self._status_label.setText("")
        self._robot_id_label.setText("")
        self._cpu_bar.setValue(0)
        self._mem_bar.setValue(0)
        self._jobs_label.setText("- / -")
        self._job_name_label.setText("No active job")
        self._job_id_label.setText("")
        self._job_progress_bar.setValue(0)
        self._job_status_label.setText("")
        self._jobs_table.setRowCount(0)
        self._logs_viewer.clear()

        # Disable action buttons
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._restart_btn.setEnabled(False)

    @Slot(object)
    def set_robot(self, robot: Optional["Robot"]) -> None:
        """
        Set the robot to display.

        Args:
            robot: Robot entity or None to clear
        """
        if robot is None:
            self._current_robot = None
            self._current_robot_id = None
            self._show_no_selection()
            return

        self._current_robot = robot
        self._current_robot_id = robot.id

        # Update header
        self._robot_name_label.setText(robot.name)
        self._robot_id_label.setText(f"ID: {robot.id[:8]}...")

        # Update status
        status_colors = {
            "online": THEME.success,
            "busy": THEME.warning,
            "offline": THEME.error,
            "error": THEME.error,
            "maintenance": THEME.text_muted,
        }
        status_color = status_colors.get(robot.status.value, THEME.text_muted)
        self._status_indicator.setStyleSheet(f"color: {status_color}; font-size: 16px;")
        self._status_label.setText(robot.status.value.title())

        # Update metrics
        cpu_pct = getattr(robot, "cpu_percent", 0) or 0
        mem_pct = getattr(robot, "memory_percent", 0) or 0
        self._cpu_bar.setValue(int(cpu_pct))
        self._mem_bar.setValue(int(mem_pct))
        self._jobs_label.setText(f"{robot.current_jobs} / {robot.max_concurrent_jobs}")

        # Enable action buttons
        is_online = robot.status.value in ("online", "busy")
        self._pause_btn.setEnabled(is_online)
        self._stop_btn.setEnabled(is_online)
        self._restart_btn.setEnabled(True)

        logger.debug(f"RobotDetailPanel showing robot: {robot.name}")

    @Slot(int)
    def update_job_progress(self, percentage: int) -> None:
        """Update current job progress bar."""
        self._job_progress_bar.setValue(percentage)

    @Slot(str, str, int)
    def set_current_job(self, job_id: str, workflow_name: str, progress: int) -> None:
        """
        Set current job information.

        Args:
            job_id: Job ID
            workflow_name: Name of the workflow
            progress: Progress percentage (0-100)
        """
        self._job_id_label.setText(f"#{job_id[:8]}")
        self._job_name_label.setText(workflow_name)
        self._job_progress_bar.setValue(progress)
        self._job_status_label.setText(f"In progress... {progress}%")

    def clear_current_job(self) -> None:
        """Clear current job display."""
        self._job_id_label.setText("")
        self._job_name_label.setText("No active job")
        self._job_progress_bar.setValue(0)
        self._job_status_label.setText("")

    @Slot(list)
    def update_job_history(self, jobs: List[Dict]) -> None:
        """
        Update recent jobs table.

        Args:
            jobs: List of job dictionaries with 'workflow_name', 'status', 'duration'
        """
        self._jobs_table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            workflow_item = QTableWidgetItem(job.get("workflow_name", "Unknown"))
            status_item = QTableWidgetItem(job.get("status", "Unknown"))
            duration_item = QTableWidgetItem(job.get("duration", "-"))

            # Color status
            status = job.get("status", "").lower()
            if status == "completed":
                status_item.setForeground(self._hex_to_qbrush(THEME.success))
            elif status == "failed":
                status_item.setForeground(self._hex_to_qbrush(THEME.error))
            elif status == "running":
                status_item.setForeground(self._hex_to_qbrush(THEME.warning))

            self._jobs_table.setItem(row, 0, workflow_item)
            self._jobs_table.setItem(row, 1, status_item)
            self._jobs_table.setItem(row, 2, duration_item)

    def _hex_to_qbrush(self, hex_color: str) -> QBrush:
        """Convert hex color to QBrush."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return QBrush(QColor(r, g, b))

    @Slot(list)
    def update_logs(self, logs: List[Dict]) -> None:
        """
        Update logs viewer.

        Args:
            logs: List of log dictionaries with 'timestamp', 'level', 'message'
        """
        log_text = ""
        for log in logs:
            timestamp = log.get("timestamp", "")
            level = log.get("level", "INFO")
            message = log.get("message", "")

            # Format: HH:MM:SS [LEVEL] message
            if timestamp:
                time_str = timestamp.split("T")[-1][:8] if "T" in timestamp else timestamp[:8]
            else:
                time_str = "        "

            log_text += f"{time_str} [{level:5}] {message}\n"

        self._logs_viewer.setPlainText(log_text)
        # Scroll to bottom
        scrollbar = self._logs_viewer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def append_log(self, timestamp: str, level: str, message: str) -> None:
        """Append a single log entry."""
        time_str = timestamp.split("T")[-1][:8] if "T" in timestamp else timestamp[:8]
        log_line = f"{time_str} [{level:5}] {message}\n"
        self._logs_viewer.append(log_line.strip())

    # ==================== Slot Handlers ====================

    @Slot()
    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        if self._current_robot_id:
            self.pause_requested.emit(self._current_robot_id)
            logger.debug(f"Pause requested for robot: {self._current_robot_id}")

    @Slot()
    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        if self._current_robot_id:
            self.stop_requested.emit(self._current_robot_id)
            logger.debug(f"Stop requested for robot: {self._current_robot_id}")

    @Slot()
    def _on_restart_clicked(self) -> None:
        """Handle restart button click."""
        if self._current_robot_id:
            self.restart_requested.emit(self._current_robot_id)
            logger.debug(f"Restart requested for robot: {self._current_robot_id}")

    @Slot()
    def _on_clear_logs_clicked(self) -> None:
        """Handle clear logs button click."""
        self._logs_viewer.clear()

    @Slot()
    def _on_refresh_logs_clicked(self) -> None:
        """Handle refresh logs button click."""
        if self._current_robot_id:
            self.logs_refresh_requested.emit(self._current_robot_id)

    # ==================== Properties ====================

    @property
    def current_robot_id(self) -> Optional[str]:
        """Get current robot ID."""
        return self._current_robot_id
