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
from PySide6.QtGui import QColor, QBrush

from .constants import ROBOT_STATUS_COLORS


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

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Robot Configuration")
        form = QFormLayout(form_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Robot name")
        if self._robot:
            self._name_edit.setText(self._robot.name)
        form.addRow("Name:", self._name_edit)

        self._hostname_edit = QLineEdit()
        self._hostname_edit.setPlaceholderText("Hostname or IP")
        if self._robot:
            self._hostname_edit.setText(self._robot.hostname)
        form.addRow("Hostname:", self._hostname_edit)

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
            "hostname": self._hostname_edit.text().strip(),
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
        self._add_btn.clicked.connect(self._on_add_robot)
        toolbar.addWidget(self._add_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Name",
                "Status",
                "Hostname",
                "Environment",
                "Jobs",
                "Capabilities",
                "Last Heartbeat",
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(7, 160)

        layout.addWidget(self._table)

        self._status_label = QLabel("0 robots")
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
        """)

    def update_robots(self, robots: List["Robot"]) -> None:
        """Update table with robot list."""
        self._robots = robots
        self._robot_map = {r.id: r for r in robots}
        self._populate_table()
        self._update_status_label()

    def _populate_table(self) -> None:
        """Populate table with current robots."""
        self._table.setRowCount(len(self._robots))

        for row, robot in enumerate(self._robots):
            self._table.setItem(row, 0, QTableWidgetItem(robot.name))

            status_item = QTableWidgetItem(robot.status.value.title())
            status_color = ROBOT_STATUS_COLORS.get(
                robot.status.value, ROBOT_STATUS_COLORS["offline"]
            )
            status_item.setForeground(QBrush(status_color))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            self._table.setItem(row, 1, status_item)

            self._table.setItem(
                row, 2, QTableWidgetItem(getattr(robot, "hostname", robot.name))
            )
            self._table.setItem(row, 3, QTableWidgetItem(robot.environment))
            self._table.setItem(
                row,
                4,
                QTableWidgetItem(f"{robot.current_jobs}/{robot.max_concurrent_jobs}"),
            )

            caps = (
                ", ".join(c.value for c in robot.capabilities)
                if robot.capabilities
                else "-"
            )
            self._table.setItem(row, 5, QTableWidgetItem(caps))

            heartbeat = (
                robot.last_heartbeat.strftime("%H:%M:%S")
                if robot.last_heartbeat
                else "-"
            )
            self._table.setItem(row, 6, QTableWidgetItem(heartbeat))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setMaximumHeight(24)
            edit_btn.clicked.connect(lambda _, r=robot: self._on_edit_robot(r))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumHeight(24)
            delete_btn.clicked.connect(lambda _, r=robot: self._on_delete_robot(r))
            actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 7, actions_widget)

            for col in range(7):
                item = self._table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, robot.id)

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply search and filter to table rows."""
        search_text = self._search_edit.text().lower()
        status_filter = self._status_filter.currentText().lower()
        cap_filter = self._capability_filter.currentText().lower()

        visible_count = 0
        for row in range(self._table.rowCount()):
            robot_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            robot = self._robot_map.get(robot_id)

            if robot is None:
                self._table.setRowHidden(row, True)
                continue

            show = True

            if search_text:
                name_match = search_text in robot.name.lower()
                hostname_match = search_text in robot.hostname.lower()
                if not (name_match or hostname_match):
                    show = False

            if show and status_filter != "all status":
                if robot.status.value.lower() != status_filter:
                    show = False

            if show and cap_filter != "all capabilities":
                cap_map = {
                    "browser": "browser",
                    "desktop": "desktop",
                    "gpu": "gpu",
                    "high memory": "high_memory",
                }
                required_cap = cap_map.get(cap_filter)
                if required_cap:
                    has_cap = any(c.value == required_cap for c in robot.capabilities)
                    if not has_cap:
                        show = False

            self._table.setRowHidden(row, not show)
            if show:
                visible_count += 1

        self._update_status_label(visible_count)

    def _update_status_label(self, visible: Optional[int] = None) -> None:
        """Update status label with robot counts."""
        total = len(self._robots)
        online = sum(1 for r in self._robots if r.status.value == "online")
        busy = sum(1 for r in self._robots if r.status.value == "busy")
        offline = sum(1 for r in self._robots if r.status.value == "offline")

        if visible is not None and visible != total:
            self._status_label.setText(
                f"Showing {visible} of {total} robots | "
                f"Online: {online}, Busy: {busy}, Offline: {offline}"
            )
        else:
            self._status_label.setText(
                f"{total} robots | Online: {online}, Busy: {busy}, Offline: {offline}"
            )

    def _show_context_menu(self, pos) -> None:
        """
        Show context menu for robot row with quick actions.

        Actions available:
        - View Details / Edit
        - View Logs (opens log viewer)
        - View Metrics (shows CPU/memory details)
        - Run Workflow (submit job to this robot)
        - Separator
        - Start / Stop / Pause / Resume (based on current status)
        - Restart
        - Set Maintenance
        - Separator
        - Delete
        """
        item = self._table.itemAt(pos)
        if not item:
            return

        robot_id = item.data(Qt.ItemDataRole.UserRole)
        robot = self._robot_map.get(robot_id)
        if not robot:
            return

        menu = QMenu(self)

        # ===== Quick View Actions =====
        view_details = menu.addAction("View Details")
        view_details.triggered.connect(lambda: self._on_view_robot_details(robot))

        view_logs = menu.addAction("View Logs")
        view_logs.triggered.connect(lambda: self._on_view_robot_logs(robot))

        view_metrics = menu.addAction("View Metrics")
        view_metrics.triggered.connect(lambda: self._on_view_robot_metrics(robot))

        menu.addSeparator()

        # ===== Run Workflow Action =====
        run_workflow = menu.addAction("Run Workflow on Robot...")
        run_workflow.triggered.connect(lambda: self._on_run_workflow_on_robot(robot))

        menu.addSeparator()

        # ===== Status Control Actions =====
        status = robot.status.value

        if status == "offline":
            start_action = menu.addAction("Start Robot")
            start_action.triggered.connect(
                lambda: self.robot_start_requested.emit(robot.id)
            )

        if status in ("online", "busy"):
            stop_action = menu.addAction("Stop Robot")
            stop_action.triggered.connect(
                lambda: self.robot_stop_requested.emit(robot.id)
            )

            if status == "online":
                pause_action = menu.addAction("Pause (No New Jobs)")
                pause_action.triggered.connect(
                    lambda: self.robot_pause_requested.emit(robot.id)
                )

        if status == "maintenance":
            resume_action = menu.addAction("Resume Robot")
            resume_action.triggered.connect(
                lambda: self.robot_resume_requested.emit(robot.id)
            )

        if status in ("online", "busy", "offline"):
            restart_action = menu.addAction("Restart Robot")
            restart_action.triggered.connect(
                lambda: self.robot_restart_requested.emit(robot.id)
            )

        menu.addSeparator()

        # ===== Edit / Maintenance Actions =====
        edit_action = menu.addAction("Edit Robot...")
        edit_action.triggered.connect(lambda: self._on_edit_robot(robot))

        if status != "maintenance":
            maintenance_action = menu.addAction("Set Maintenance Mode")
            maintenance_action.triggered.connect(
                lambda: self._on_set_status(robot, "maintenance")
            )
        else:
            online_action = menu.addAction("Exit Maintenance Mode")
            online_action.triggered.connect(
                lambda: self._on_set_status(robot, "online")
            )

        menu.addSeparator()

        # ===== Danger Zone =====
        if status == "busy":
            force_stop = menu.addAction("Force Stop (Cancel Jobs)")
            force_stop.triggered.connect(
                lambda: self.robot_force_stop_requested.emit(robot.id)
            )

        delete_action = menu.addAction("Delete Robot")
        delete_action.triggered.connect(lambda: self._on_delete_robot(robot))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_view_robot_details(self, robot: "Robot") -> None:
        """Show robot details dialog."""
        self.robot_details_requested.emit(robot.id)

    def _on_view_robot_logs(self, robot: "Robot") -> None:
        """Request robot logs view."""
        self.robot_logs_requested.emit(robot.id)

    def _on_view_robot_metrics(self, robot: "Robot") -> None:
        """Request robot metrics view."""
        self.robot_metrics_requested.emit(robot.id)

    def _on_run_workflow_on_robot(self, robot: "Robot") -> None:
        """Request to run workflow on specific robot."""
        self.robot_run_workflow_requested.emit(robot.id)

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self._table.selectedItems()
        if selected:
            robot_id = selected[0].data(Qt.ItemDataRole.UserRole)
            if robot_id:
                self.robot_selected.emit(robot_id)

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on robot row."""
        robot_id = item.data(Qt.ItemDataRole.UserRole)
        robot = self._robot_map.get(robot_id)
        if robot:
            self._on_edit_robot(robot)

    def _on_add_robot(self) -> None:
        """Open dialog to add new robot."""
        dialog = RobotEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            robot_data = dialog.get_robot_data()
            self.robot_edited.emit("", robot_data)

    def _on_edit_robot(self, robot: "Robot") -> None:
        """Open dialog to edit robot."""
        dialog = RobotEditDialog(robot=robot, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            robot_data = dialog.get_robot_data()
            self.robot_edited.emit(robot.id, robot_data)

    def _on_delete_robot(self, robot: "Robot") -> None:
        """Confirm and delete robot."""
        reply = QMessageBox.question(
            self,
            "Delete Robot",
            f"Are you sure you want to delete '{robot.name}'?\n\n"
            "This will remove the robot from the fleet.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.robot_deleted.emit(robot.id)

    def _on_set_status(self, robot: "Robot", status: str) -> None:
        """Change robot status."""
        self.robot_edited.emit(robot.id, {"status": status})

    def _request_refresh(self) -> None:
        """Request robot list refresh."""
        self.refresh_requested.emit()

    def set_refreshing(self, refreshing: bool) -> None:
        """Set refresh button state."""
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")

    # ==================== Real-Time Updates ====================

    def handle_robot_status_update(self, update: "RobotStatusUpdate") -> None:
        """
        Handle real-time robot status update from WebSocket.

        Updates the robot row in place without full table refresh.

        Args:
            update: RobotStatusUpdate from WebSocketBridge
        """
        robot_id = update.robot_id

        # Find the robot in our map
        robot = self._robot_map.get(robot_id)
        if not robot:
            # Robot not in current list, request refresh
            return

        # Find the row for this robot
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == robot_id:
                self._update_robot_row(row, update)
                break

    def _update_robot_row(self, row: int, update: "RobotStatusUpdate") -> None:
        """
        Update a single robot row with new status data.

        Args:
            row: Table row index
            update: RobotStatusUpdate with new data
        """
        # Update status column
        status_item = self._table.item(row, 1)
        if status_item:
            status_item.setText(update.status.title())
            status_color = ROBOT_STATUS_COLORS.get(
                update.status, ROBOT_STATUS_COLORS["offline"]
            )
            status_item.setForeground(QBrush(status_color))

        # Update current job info if widget exists
        # (CPU/memory could be shown in extended view)

        # Update last heartbeat column
        heartbeat_item = self._table.item(row, 6)
        if heartbeat_item and update.timestamp:
            heartbeat_item.setText(update.timestamp.strftime("%H:%M:%S"))

            # Visual indicator for stale heartbeat
            if self._is_heartbeat_stale(update.timestamp):
                heartbeat_item.setForeground(QBrush(QColor(0xF4, 0x43, 0x36)))
            else:
                heartbeat_item.setForeground(QBrush(QColor(0x4C, 0xAF, 0x50)))

    def _is_heartbeat_stale(self, timestamp: datetime) -> bool:
        """
        Check if heartbeat timestamp is stale.

        Args:
            timestamp: Last heartbeat time

        Returns:
            True if heartbeat is older than threshold
        """
        if not timestamp:
            return True

        age = (datetime.now() - timestamp).total_seconds()
        return age > HEARTBEAT_TIMEOUT_SECONDS

    def handle_batch_robot_updates(self, updates: List["RobotStatusUpdate"]) -> None:
        """
        Handle batch of robot status updates efficiently.

        Args:
            updates: List of RobotStatusUpdate objects
        """
        # Temporarily disable sorting for batch update
        self._table.setSortingEnabled(False)

        try:
            for update in updates:
                self.handle_robot_status_update(update)
        finally:
            self._table.setSortingEnabled(True)

        # Update status label with new counts
        self._update_status_label()

    def get_robot_by_id(self, robot_id: str) -> Optional["Robot"]:
        """
        Get robot entity by ID.

        Args:
            robot_id: Robot identifier

        Returns:
            Robot entity or None
        """
        return self._robot_map.get(robot_id)
