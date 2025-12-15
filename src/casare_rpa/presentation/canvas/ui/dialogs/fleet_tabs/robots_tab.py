"""
Robots Tab Widget for Fleet Dashboard.

Displays robot fleet with management capabilities.
Supports real-time status updates via WebSocketBridge.
"""

from datetime import datetime
from typing import Optional, List, Dict, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QComboBox,
    QLineEdit,
    QLabel,
    QMenu,
    QMessageBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QBrush, QIcon

from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    ROBOT_STATUS_COLORS,
    TAB_WIDGET_BASE_STYLE,
)
from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon, ToolbarIcons


if TYPE_CHECKING:
    from casare_rpa.domain.orchestrator.entities.robot import Robot
    from casare_rpa.presentation.canvas.services.websocket_bridge import (
        RobotStatusUpdate,
    )


# Heartbeat timeout threshold (seconds) - robot considered stale after this
HEARTBEAT_TIMEOUT_SECONDS = 90


class RobotEditDialog(QDialog):
    """Dialog for editing robot properties."""

    def __init__(
        self,
        robot: Optional["Robot"] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._robot = robot
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Edit Robot" if self._robot else "Add Robot")
        self.setMinimumWidth(400)
        self.setStyleSheet(TAB_WIDGET_BASE_STYLE)

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Robot Configuration")
        form = QFormLayout(form_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Robot name")
        if self._robot:
            self._name_edit.setText(self._robot.name)
        form.addRow("Name:", self._name_edit)

        self._max_jobs_spin = QSpinBox()
        self._max_jobs_spin.setRange(1, 20)
        self._max_jobs_spin.setValue(
            self._robot.max_concurrent_jobs if self._robot else 3
        )
        form.addRow("Max Concurrent Jobs:", self._max_jobs_spin)

        self._environment_edit = QLineEdit()
        self._environment_edit.setPlaceholderText("production, staging, dev")
        if self._robot:
            self._environment_edit.setText(self._robot.environment)
        form.addRow("Environment:", self._environment_edit)

        cap_group = QGroupBox("Capabilities")
        cap_layout = QVBoxLayout(cap_group)
        self._cap_browser = QCheckBox("Browser Automation")
        self._cap_desktop = QCheckBox("Desktop Automation")
        self._cap_gpu = QCheckBox("GPU Available")
        self._cap_high_memory = QCheckBox("High Memory")
        cap_layout.addWidget(self._cap_browser)
        cap_layout.addWidget(self._cap_desktop)
        cap_layout.addWidget(self._cap_gpu)
        cap_layout.addWidget(self._cap_high_memory)

        if self._robot:
            caps = {c.value for c in self._robot.capabilities}
            self._cap_browser.setChecked("browser" in caps)
            self._cap_desktop.setChecked("desktop" in caps)
            self._cap_gpu.setChecked("gpu" in caps)
            self._cap_high_memory.setChecked("high_memory" in caps)

        layout.addWidget(form_group)
        layout.addWidget(cap_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Robot name is required.")
            return
        self.accept()

    def get_robot_data(self) -> Dict:
        """Get robot data from form."""
        caps = []
        if self._cap_browser.isChecked():
            caps.append("browser")
        if self._cap_desktop.isChecked():
            caps.append("desktop")
        if self._cap_gpu.isChecked():
            caps.append("gpu")
        if self._cap_high_memory.isChecked():
            caps.append("high_memory")

        return {
            "name": self._name_edit.text().strip(),
            "max_concurrent_jobs": self._max_jobs_spin.value(),
            "environment": self._environment_edit.text().strip() or "production",
            "capabilities": caps,
        }


class RobotsTabWidget(QWidget):
    """
    Widget for displaying and managing robots.

    Features:
    - Table view of all robots
    - Status filter
    - Search
    - Add/Edit/Delete actions
    - Context menu
    - Real-time status updates

    Signals:
        robot_selected: Emitted when robot is selected (robot_id)
        robot_edited: Emitted when robot is edited (robot_id, robot_data)
        robot_deleted: Emitted when robot is deleted (robot_id)
        refresh_requested: Emitted when refresh is clicked
    """

    robot_selected = Signal(str)
    robot_edited = Signal(str, dict)
    robot_deleted = Signal(str)
    refresh_requested = Signal()

    # Quick action signals
    robot_start_requested = Signal(str)  # robot_id
    robot_stop_requested = Signal(str)  # robot_id
    robot_pause_requested = Signal(str)  # robot_id
    robot_resume_requested = Signal(str)  # robot_id
    robot_restart_requested = Signal(str)  # robot_id
    robot_force_stop_requested = Signal(str)  # robot_id

    # View signals
    robot_details_requested = Signal(str)  # robot_id
    robot_logs_requested = Signal(str)  # robot_id
    robot_metrics_requested = Signal(str)  # robot_id
    robot_run_workflow_requested = Signal(str)  # robot_id

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._robots: List["Robot"] = []
        self._robot_map: Dict[str, "Robot"] = {}
        self._setup_ui()
        self._apply_styles()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._request_refresh)
        self._refresh_timer.start(30000)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search robots...")
        self._search_edit.textChanged.connect(self._apply_filters)
        self._search_edit.setMinimumWidth(200)
        toolbar.addWidget(self._search_edit)

        self._status_filter = QComboBox()
        self._status_filter.addItems(
            [
                "All Status",
                "Online",
                "Busy",
                "Offline",
                "Maintenance",
                "Error",
            ]
        )
        self._status_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._status_filter)

        self._capability_filter = QComboBox()
        self._capability_filter.addItems(
            [
                "All Capabilities",
                "Browser",
                "Desktop",
                "GPU",
                "High Memory",
            ]
        )
        self._capability_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._capability_filter)

        toolbar.addStretch()

        self._add_btn = QPushButton("Add Robot")
        self._add_btn.setIcon(get_toolbar_icon("new"))
        self._add_btn.clicked.connect(self._on_add_robot)
        toolbar.addWidget(self._add_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setIcon(get_toolbar_icon("restart"))
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColum
