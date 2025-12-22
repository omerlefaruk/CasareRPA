"""
Remote Robot Management Dialog.

Provides UI for managing robots remotely including viewing details,
starting/stopping, and updating configuration.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from loguru import logger
from PySide6.QtWidgets import QDialog


if TYPE_CHECKING:
    pass


STATUS_COLORS = {
    "online": "#4CAF50",
    "busy": "#FFC107",
    "offline": "#F44336",
    "error": "#F44336",
    "maintenance": "#9E9E9E",
}


class RemoteRobotDialog(QDialog):
    """
    Dialog for remote robot management.

    Features:
    - View robot details and metrics
    - Start/stop robot remotely
    - Update robot configuration
    - View current jobs
    - Monitor health metrics

    Signals:
        robot_started: Emitted when start requested (robot_id)
        robot_stopped: Emitted when stop requested (robot_id)
        robot_restarted: Emitted when restart requested (robot_id)
        config_updated: Emitted when config updated (robot_id, config_dict)
        refresh_requested: Emitted when refresh clicked
    """

    robot_started = Signal(str)
    robot_stopped = Signal(str)
    robot_restarted = Signal(str)
    config_updated = Signal(str, dict)
    refresh_requested = Signal()

    def __init__(
        self,
        robot_id: str,
        robot_data: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._robot_id = robot_id
        self._robot_data = robot_data or {}
        self._setup_ui()
        self._apply_styles()
        self._populate_data()

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._request_refresh)
        self._refresh_timer.start(10000)  # Refresh every 10 seconds

    def _setup_ui(self) -> None:
        robot_name = self._robot_data.get("name", "Robot")
        self.setWindowTitle(f"Remote Management - {robot_name}")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with status
        header = QHBoxLayout()

        self._name_label = QLabel(robot_name)
        self._name_label.setFont(QFont("", 14, QFont.Weight.Bold))
        header.addWidget(self._name_label)

        header.addStretch()

        self._status_label = QLabel("Unknown")
        self._status_label.setFont(QFont("", 12, QFont.Weight.Bold))
        header.addWidget(self._status_label)

        layout.addLayout(header)

        # Control buttons
        controls = QHBoxLayout()

        self._start_btn = QPushButton("Start")
        self._start_btn.clicked.connect(self._on_start)
        controls.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.clicked.connect(self._on_stop)
        controls.addWidget(self._stop_btn)

        self._restart_btn = QPushButton("Restart")
        self._restart_btn.clicked.connect(self._on_restart)
        controls.addWidget(self._restart_btn)

        controls.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._request_refresh)
        controls.addWidget(self._refresh_btn)

        layout.addLayout(controls)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        # Details tab
        details_tab = self._create_details_tab()
        self._tabs.addTab(details_tab, "Details")

        # Configuration tab
        config_tab = self._create_config_tab()
        self._tabs.addTab(config_tab, "Configuration")

        # Jobs tab
        jobs_tab = self._create_jobs_tab()
        self._tabs.addTab(jobs_tab, "Current Jobs")

        # Metrics tab
        metrics_tab = self._create_metrics_tab()
        self._tabs.addTab(metrics_tab, "Metrics")

        # Logs tab
        logs_tab = self._create_logs_tab()
        self._tabs.addTab(logs_tab, "Logs")

        layout.addWidget(self._tabs)

        # Footer
        footer = QHBoxLayout()

        self._last_update_label = QLabel("Last update: -")
        self._last_update_label.setStyleSheet("color: #888888;")
        footer.addWidget(self._last_update_label)

        footer.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _create_details_tab(self) -> QWidget:
        """Create details tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Basic info
        info_group = QGroupBox("Robot Information")
        info_layout = QFormLayout(info_group)

        self._detail_id = QLabel("-")
        self._detail_id.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_layout.addRow("Robot ID:", self._detail_id)

        self._detail_name = QLabel("-")
        info_layout.addRow("Name:", self._detail_name)

        self._detail_hostname = QLabel("-")
        info_layout.addRow("Hostname:", self._detail_hostname)

        self._detail_environment = QLabel("-")
        info_layout.addRow("Environment:", self._detail_environment)

        self._detail_status = QLabel("-")
        info_layout.addRow("Status:", self._detail_status)

        layout.addWidget(info_group)

        # Capabilities
        caps_group = QGroupBox("Capabilities")
        caps_layout = QVBoxLayout(caps_group)

        self._detail_capabilities = QLabel("-")
        self._detail_capabilities.setWordWrap(True)
        caps_layout.addWidget(self._detail_capabilities)

        layout.addWidget(caps_group)

        # Connection info
        conn_group = QGroupBox("Connection")
        conn_layout = QFormLayout(conn_group)

        self._detail_connected = QLabel("-")
        conn_layout.addRow("Connected At:", self._detail_connected)

        self._detail_last_heartbeat = QLabel("-")
        conn_layout.addRow("Last Heartbeat:", self._detail_last_heartbeat)

        self._detail_uptime = QLabel("-")
        conn_layout.addRow("Uptime:", self._detail_uptime)

        layout.addWidget(conn_group)

        layout.addStretch()
        return tab

    def _create_config_tab(self) -> QWidget:
        """Create configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Job settings
        job_group = QGroupBox("Job Settings")
        job_layout = QFormLayout(job_group)

        self._config_max_jobs = QSpinBox()
        self._config_max_jobs.setRange(1, 20)
        self._config_max_jobs.setValue(3)
        job_layout.addRow("Max Concurrent Jobs:", self._config_max_jobs)

        self._config_environment = QLineEdit()
        self._config_environment.setPlaceholderText("production")
        job_layout.addRow("Environment:", self._config_environment)

        layout.addWidget(job_group)

        # Capabilities
        caps_group = QGroupBox("Capabilities")
        caps_layout = QVBoxLayout(caps_group)

        self._config_browser = QCheckBox("Browser Automation")
        caps_layout.addWidget(self._config_browser)

        self._config_desktop = QCheckBox("Desktop Automation")
        caps_layout.addWidget(self._config_desktop)

        self._config_gpu = QCheckBox("GPU Available")
        caps_layout.addWidget(self._config_gpu)

        self._config_high_memory = QCheckBox("High Memory")
        caps_layout.addWidget(self._config_high_memory)

        self._config_secure = QCheckBox("Secure Zone")
        caps_layout.addWidget(self._config_secure)

        layout.addWidget(caps_group)

        # Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)

        self._config_tags = QLineEdit()
        self._config_tags.setPlaceholderText("tag1, tag2, tag3")
        tags_layout.addWidget(self._config_tags)

        layout.addWidget(tags_group)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._on_save_config)
        save_layout.addWidget(save_btn)

        layout.addLayout(save_layout)
        layout.addStretch()
        return tab

    def _create_jobs_tab(self) -> QWidget:
        """Create current jobs tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._jobs_table = QTableWidget()
        self._jobs_table.setColumnCount(5)
        self._jobs_table.setHorizontalHeaderLabels(
            [
                "Job ID",
                "Workflow",
                "Status",
                "Progress",
                "Started",
            ]
        )
        self._jobs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._jobs_table.verticalHeader().setVisible(False)

        header = self._jobs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._jobs_table)

        # Job actions
        actions = QHBoxLayout()
        actions.addStretch()

        cancel_btn = QPushButton("Cancel Selected Job")
        cancel_btn.clicked.connect(self._on_cancel_job)
        actions.addWidget(cancel_btn)

        layout.addLayout(actions)
        return tab

    def _create_metrics_tab(self) -> QWidget:
        """Create metrics tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # System metrics
        sys_group = QGroupBox("System Metrics")
        sys_layout = QFormLayout(sys_group)

        self._metric_cpu = QProgressBar()
        self._metric_cpu.setMaximum(100)
        sys_layout.addRow("CPU:", self._metric_cpu)

        self._metric_memory = QProgressBar()
        self._metric_memory.setMaximum(100)
        sys_layout.addRow("Memory:", self._metric_memory)

        self._metric_disk = QProgressBar()
        self._metric_disk.setMaximum(100)
        sys_layout.addRow("Disk:", self._metric_disk)

        layout.addWidget(sys_group)

        # Job metrics
        job_group = QGroupBox("Job Metrics")
        job_layout = QFormLayout(job_group)

        self._metric_jobs_total = QLabel("-")
        job_layout.addRow("Total Jobs Executed:", self._metric_jobs_total)

        self._metric_jobs_success = QLabel("-")
        job_layout.addRow("Successful Jobs:", self._metric_jobs_success)

        self._metric_jobs_failed = QLabel("-")
        job_layout.addRow("Failed Jobs:", self._metric_jobs_failed)

        self._metric_avg_duration = QLabel("-")
        job_layout.addRow("Avg Job Duration:", self._metric_avg_duration)

        layout.addWidget(job_group)

        # Network metrics
        net_group = QGroupBox("Network")
        net_layout = QFormLayout(net_group)

        self._metric_latency = QLabel("-")
        net_layout.addRow("Latency:", self._metric_latency)

        self._metric_bytes_sent = QLabel("-")
        net_layout.addRow("Bytes Sent:", self._metric_bytes_sent)

        self._metric_bytes_recv = QLabel("-")
        net_layout.addRow("Bytes Received:", self._metric_bytes_recv)

        layout.addWidget(net_group)
        layout.addStretch()
        return tab

    def _create_logs_tab(self) -> QWidget:
        """Create logs tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Log controls
        controls = QHBoxLayout()

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["All", "Debug", "Info", "Warning", "Error"])
        controls.addWidget(QLabel("Level:"))
        controls.addWidget(self._log_level_combo)

        controls.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_logs)
        controls.addWidget(clear_btn)

        layout.addLayout(controls)

        # Log display
        self._log_display = QTextEdit()
        self._log_display.setReadOnly(True)
        self._log_display.setStyleSheet(
            "font-family: monospace; background: #1a1a1a; color: #e0e0e0;"
        )
        layout.addWidget(self._log_display)

        return tab

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background: #252525;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background: #2a2a2a;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 8px 16px;
                margin-right: 2px;
                color: #a0a0a0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
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
            QProgressBar {
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                background: #2d2d2d;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #4CAF50;
                border-radius: 2px;
            }
            QTableWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
            }
        """)

    def _populate_data(self) -> None:
        """Populate UI with robot data."""
        data = self._robot_data

        # Header
        self._name_label.setText(data.get("name", "Unknown Robot"))
        status = data.get("status", "offline")
        self._status_label.setText(status.title())
        self._status_label.setStyleSheet(
            f"color: {STATUS_COLORS.get(status, '#888888')}; font-weight: bold;"
        )

        # Update control buttons based on status
        is_online = status == "online" or status == "busy"
        self._start_btn.setEnabled(not is_online)
        self._stop_btn.setEnabled(is_online)
        self._restart_btn.setEnabled(is_online)

        # Details tab
        self._detail_id.setText(data.get("id", "-"))
        self._detail_name.setText(data.get("name", "-"))
        self._detail_hostname.setText(data.get("hostname", "-"))
        self._detail_environment.setText(data.get("environment", "-"))
        self._detail_status.setText(status.title())
        self._detail_status.setStyleSheet(f"color: {STATUS_COLORS.get(status, '#888888')};")

        # Capabilities
        caps = data.get("capabilities", [])
        if isinstance(caps, list):
            caps_str = ", ".join(c.title() for c in caps) if caps else "None"
        else:
            caps_str = str(caps)
        self._detail_capabilities.setText(caps_str)

        # Connection info
        connected_at = data.get("connected_at")
        if connected_at:
            if isinstance(connected_at, datetime):
                self._detail_connected.setText(connected_at.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self._detail_connected.setText(str(connected_at))
        else:
            self._detail_connected.setText("-")

        last_heartbeat = data.get("last_heartbeat")
        if last_heartbeat:
            if isinstance(last_heartbeat, datetime):
                self._detail_last_heartbeat.setText(last_heartbeat.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self._detail_last_heartbeat.setText(str(last_heartbeat))
        else:
            self._detail_last_heartbeat.setText("-")

        # Configuration tab
        self._config_max_jobs.setValue(data.get("max_concurrent_jobs", 1))
        self._config_environment.setText(data.get("environment", "production"))

        caps_set = set(caps) if isinstance(caps, list) else set()
        self._config_browser.setChecked("browser" in caps_set)
        self._config_desktop.setChecked("desktop" in caps_set)
        self._config_gpu.setChecked("gpu" in caps_set)
        self._config_high_memory.setChecked("high_memory" in caps_set)
        self._config_secure.setChecked("secure" in caps_set)

        tags = data.get("tags", [])
        self._config_tags.setText(", ".join(tags) if tags else "")

        # Jobs tab
        current_jobs = data.get("current_jobs_data", [])
        self._populate_jobs(current_jobs)

        # Metrics tab
        metrics = data.get("metrics", {})
        self._populate_metrics(metrics)

        # Update timestamp
        self._last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

    def _populate_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Populate jobs table."""
        self._jobs_table.setRowCount(len(jobs))

        for row, job in enumerate(jobs):
            self._jobs_table.setItem(row, 0, QTableWidgetItem(job.get("id", "-")[:8] + "..."))
            self._jobs_table.setItem(row, 1, QTableWidgetItem(job.get("workflow_name", "-")))
            self._jobs_table.setItem(row, 2, QTableWidgetItem(job.get("status", "-").title()))
            self._jobs_table.setItem(row, 3, QTableWidgetItem(f"{job.get('progress', 0)}%"))

            started = job.get("started_at")
            if started:
                if isinstance(started, datetime):
                    started_str = started.strftime("%H:%M:%S")
                else:
                    started_str = str(started)[:8]
            else:
                started_str = "-"
            self._jobs_table.setItem(row, 4, QTableWidgetItem(started_str))

    def _populate_metrics(self, metrics: Dict[str, Any]) -> None:
        """Populate metrics displays."""
        self._metric_cpu.setValue(int(metrics.get("cpu_percent", 0)))
        self._metric_memory.setValue(int(metrics.get("memory_percent", 0)))
        self._metric_disk.setValue(int(metrics.get("disk_percent", 0)))

        self._metric_jobs_total.setText(str(metrics.get("total_jobs", 0)))
        self._metric_jobs_success.setText(str(metrics.get("successful_jobs", 0)))
        self._metric_jobs_failed.setText(str(metrics.get("failed_jobs", 0)))

        avg_duration = metrics.get("avg_job_duration_ms", 0)
        if avg_duration > 0:
            self._metric_avg_duration.setText(f"{avg_duration / 1000:.2f}s")
        else:
            self._metric_avg_duration.setText("-")

        latency = metrics.get("latency_ms", 0)
        self._metric_latency.setText(f"{latency}ms" if latency > 0 else "-")

        bytes_sent = metrics.get("bytes_sent", 0)
        self._metric_bytes_sent.setText(self._format_bytes(bytes_sent))

        bytes_recv = metrics.get("bytes_received", 0)
        self._metric_bytes_recv.setText(self._format_bytes(bytes_recv))

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        if bytes_val == 0:
            return "-"
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"

    def _on_start(self) -> None:
        """Handle start button click."""
        reply = QMessageBox.question(
            self,
            "Start Robot",
            f"Start robot '{self._robot_data.get('name', 'this robot')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.robot_started.emit(self._robot_id)

    def _on_stop(self) -> None:
        """Handle stop button click."""
        reply = QMessageBox.question(
            self,
            "Stop Robot",
            f"Stop robot '{self._robot_data.get('name', 'this robot')}'?\n\n"
            "Running jobs will be interrupted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.robot_stopped.emit(self._robot_id)

    def _on_restart(self) -> None:
        """Handle restart button click."""
        reply = QMessageBox.question(
            self,
            "Restart Robot",
            f"Restart robot '{self._robot_data.get('name', 'this robot')}'?\n\n"
            "Running jobs will be interrupted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.robot_restarted.emit(self._robot_id)

    def _on_save_config(self) -> None:
        """Handle save configuration button click."""
        caps = []
        if self._config_browser.isChecked():
            caps.append("browser")
        if self._config_desktop.isChecked():
            caps.append("desktop")
        if self._config_gpu.isChecked():
            caps.append("gpu")
        if self._config_high_memory.isChecked():
            caps.append("high_memory")
        if self._config_secure.isChecked():
            caps.append("secure")

        tags = [t.strip() for t in self._config_tags.text().split(",") if t.strip()]

        config = {
            "max_concurrent_jobs": self._config_max_jobs.value(),
            "environment": self._config_environment.text().strip() or "production",
            "capabilities": caps,
            "tags": tags,
        }

        self.config_updated.emit(self._robot_id, config)
        QMessageBox.information(
            self, "Configuration Saved", "Robot configuration has been updated."
        )

    def _on_cancel_job(self) -> None:
        """Handle cancel job button click."""
        selected = self._jobs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a job to cancel.")
            return

        job_id = self._jobs_table.item(selected[0].row(), 0).text()
        reply = QMessageBox.question(
            self,
            "Cancel Job",
            f"Cancel job {job_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Cancel job requested: {job_id}")

    def _clear_logs(self) -> None:
        """Clear log display."""
        self._log_display.clear()

    def _request_refresh(self) -> None:
        """Request data refresh."""
        self.refresh_requested.emit()

    def update_robot(self, robot_data: Dict[str, Any]) -> None:
        """Update dialog with new robot data."""
        self._robot_data = robot_data
        self._populate_data()

    def append_log(self, message: str, level: str = "info") -> None:
        """Append a log message."""
        colors = {
            "debug": "#888888",
            "info": "#e0e0e0",
            "warning": "#FFC107",
            "error": "#F44336",
        }
        color = colors.get(level.lower(), "#e0e0e0")
        timestamp = datetime.now().strftime("%H:%M:%S")

        self._log_display.append(
            f'<span style="color: {color}">[{timestamp}] [{level.upper()}] {message}</span>'
        )


__all__ = ["RemoteRobotDialog"]
