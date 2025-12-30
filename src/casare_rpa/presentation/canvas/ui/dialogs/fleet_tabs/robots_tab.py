"""
Robots Tab Widget for Fleet Dashboard.

Displays robot fleet with management capabilities.
Supports real-time status updates via WebSocketBridge.

MIGRATION(Epic 7.4): Changed THEME to THEME_V2, removed DEADLINE_COLORS dependency.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    ROBOT_STATUS_COLORS,
    TAB_WIDGET_BASE_STYLE,
)
from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon
from casare_rpa.robot.identity_store import RobotIdentity, RobotIdentityStore

if TYPE_CHECKING:
    from casare_rpa.domain.orchestrator.entities.robot import Robot


# Heartbeat timeout threshold (seconds) - robot considered stale after this
HEARTBEAT_TIMEOUT_SECONDS = 90


class RobotEditDialog(QDialog):
    """Dialog for editing robot properties."""

    def __init__(
        self,
        robot: Optional["Robot"] = None,
        parent: QWidget | None = None,
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
        self._max_jobs_spin.setValue(self._robot.max_concurrent_jobs if self._robot else 3)
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
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            self._notify_error("Robot name is required.")
            return
        self.accept()

    def _notify_error(self, message: str) -> None:
        window = self.window()
        show_toast = getattr(window, "show_toast", None)
        if callable(show_toast):
            show_toast(message, level="error")
            return

        QMessageBox.warning(self, "Validation Error", message)

    def get_robot_data(self) -> dict:
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

    # View signals
    robot_details_requested = Signal(str)  # robot_id
    robot_logs_requested = Signal(str)  # robot_id
    robot_metrics_requested = Signal(str)  # robot_id
    robot_run_workflow_requested = Signal(str)  # robot_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._robots: list[Robot] = []
        self._robot_map: dict[str, Robot] = {}
        self._identity_store = RobotIdentityStore()
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
        self._refresh_btn.setIcon(get_toolbar_icon("refresh"))
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        local_group = QGroupBox("Local Robot Link (This PC)")
        local_layout = QVBoxLayout(local_group)

        self._local_link_label = QLabel("")
        self._local_link_label.setWordWrap(True)
        self._local_link_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        local_layout.addWidget(self._local_link_label)

        local_btns = QHBoxLayout()
        self._link_selected_btn = QPushButton("Link To Selected Robot")
        self._link_selected_btn.clicked.connect(self._link_to_selected_robot)
        local_btns.addWidget(self._link_selected_btn)

        self._unlink_btn = QPushButton("Unlink")
        self._unlink_btn.clicked.connect(self._unlink_from_fleet)
        local_btns.addWidget(self._unlink_btn)

        local_btns.addStretch()
        local_layout.addLayout(local_btns)
        layout.addWidget(local_group)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            [
                "Name",
                "Status",
                "Environment",
                "Jobs",
                "Last Seen",
                "Capabilities",
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
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

        self._status_label = QLabel("0 robots")
        self._status_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        layout.addWidget(self._status_label)
        self._refresh_local_link_ui()

    def _apply_styles(self) -> None:
        self.setStyleSheet(TAB_WIDGET_BASE_STYLE)

    # =========================================================================
    # Public API
    # =========================================================================

    def update_robots(self, robots: list["Robot"]) -> None:
        self._robots = robots
        self._robot_map = {r.id: r for r in robots}
        self._apply_filters()

    def set_refreshing(self, refreshing: bool) -> None:
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")

    # =========================================================================
    # Internals
    # =========================================================================

    def _request_refresh(self) -> None:
        self.refresh_requested.emit()

    def _apply_filters(self) -> None:
        search_text = self._search_edit.text().strip().lower()

        selected_status = self._status_filter.currentText().strip().lower()
        status_filter = "" if selected_status == "all status" else selected_status

        capability_text = self._capability_filter.currentText().strip().lower()
        capability_filter = ""
        if capability_text == "browser":
            capability_filter = "browser"
        elif capability_text == "desktop":
            capability_filter = "desktop"
        elif capability_text == "gpu":
            capability_filter = "gpu"
        elif capability_text == "high memory":
            capability_filter = "high_memory"

        filtered: list[Robot] = []
        for robot in self._robots:
            if search_text and search_text not in robot.name.lower():
                continue

            robot_status = getattr(robot.status, "value", str(robot.status)).lower()
            if status_filter and robot_status != status_filter:
                continue

            if capability_filter:
                caps = {c.value for c in robot.capabilities}
                if capability_filter not in caps:
                    continue

            filtered.append(robot)

        self._populate_table(filtered)

        total = len(self._robots)
        shown = len(filtered)
        self._status_label.setText(
            f"{shown} robots" if shown == total else f"{shown}/{total} robots"
        )

    def _populate_table(self, robots: list["Robot"]) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for robot in robots:
            row = self._table.rowCount()
            self._table.insertRow(row)

            name_item = QTableWidgetItem(robot.name)
            name_item.setData(Qt.ItemDataRole.UserRole, robot.id)
            self._table.setItem(row, 0, name_item)

            status_value = getattr(robot.status, "value", str(robot.status)).lower()
            status_item = QTableWidgetItem(status_value.upper())
            status_color = ROBOT_STATUS_COLORS.get(status_value, QColor(THEME_V2.text_secondary))
            status_item.setForeground(QBrush(status_color))
            self._table.setItem(row, 1, status_item)

            self._table.setItem(row, 2, QTableWidgetItem(robot.environment or "-"))

            jobs_text = f"{robot.current_jobs}/{robot.max_concurrent_jobs}"
            self._table.setItem(row, 3, QTableWidgetItem(jobs_text))

            last_seen = robot.last_seen or robot.last_heartbeat
            last_seen_text = "-"
            if isinstance(last_seen, datetime):
                last_seen_text = last_seen.strftime("%Y-%m-%d %H:%M")
            self._table.setItem(row, 4, QTableWidgetItem(last_seen_text))

            caps = sorted({c.value for c in robot.capabilities})
            caps_text = ", ".join(caps) if caps else "-"
            self._table.setItem(row, 5, QTableWidgetItem(caps_text))

        self._table.setSortingEnabled(True)

    def _get_selected_robot_id(self) -> str | None:
        selected = self._table.selectedItems()
        if not selected:
            return None
        first = selected[0]
        item = self._table.item(first.row(), 0)
        if item is None:
            return None
        robot_id = item.data(Qt.ItemDataRole.UserRole)
        return str(robot_id) if robot_id else None

    def _on_selection_changed(self) -> None:
        robot_id = self._get_selected_robot_id()
        if robot_id:
            self.robot_selected.emit(robot_id)
        self._refresh_local_link_ui()

    def _refresh_local_link_ui(self) -> None:
        identity = self._identity_store.load()
        if identity is None:
            identity = self._identity_store.resolve()

        if identity.fleet_linked:
            self._local_link_label.setText(
                "Linked to Fleet robot: "
                f"{identity.fleet_robot_name} ({identity.fleet_robot_id}). "
                "If you delete it from the Fleet dashboard, the local robot will keep executing but will stop reporting until you link again."
            )
        else:
            reason = identity.fleet_unlinked_reason or "Not linked"
            self._local_link_label.setText(
                f"Not linked to Fleet (reason: {reason}). "
                "The local robot keeps executing, but it will not appear in the Fleet dashboard until you link it again."
            )

        has_selection = bool(self._get_selected_robot_id())
        self._link_selected_btn.setEnabled(has_selection)
        self._unlink_btn.setEnabled(identity.fleet_linked)

    def _link_to_selected_robot(self) -> None:
        robot_id = self._get_selected_robot_id()
        if not robot_id:
            return
        robot = self._robot_map.get(robot_id)
        if robot is None:
            return

        from dataclasses import replace

        identity = self._identity_store.load() or self._identity_store.resolve()
        now = RobotIdentity.now_utc_iso()
        updated = replace(
            identity,
            fleet_robot_id=robot.id,
            fleet_robot_name=robot.name,
            fleet_linked=True,
            fleet_ever_registered=True,
            fleet_unlinked_reason=None,
            fleet_unlinked_at_utc=None,
            updated_at_utc=now,
        )
        if not self._identity_store.save(updated):
            QMessageBox.warning(
                self,
                "Link Failed",
                "Failed to save local robot link settings. Check permissions for %APPDATA%/CasareRPA.",
            )
            return

        window = self.window()
        show_toast = getattr(window, "show_toast", None)
        if callable(show_toast):
            show_toast("Local robot linked to selected Fleet robot.", level="success")
        self._refresh_local_link_ui()

    def _unlink_from_fleet(self) -> None:
        from dataclasses import replace

        identity = self._identity_store.load() or self._identity_store.resolve()
        if not identity.fleet_linked:
            return

        now = RobotIdentity.now_utc_iso()
        updated = replace(
            identity,
            fleet_linked=False,
            fleet_unlinked_reason="Manual unlink",
            fleet_unlinked_at_utc=now,
            updated_at_utc=now,
        )
        if not self._identity_store.save(updated):
            QMessageBox.warning(
                self,
                "Unlink Failed",
                "Failed to save local robot link settings. Check permissions for %APPDATA%/CasareRPA.",
            )
            return

        window = self.window()
        show_toast = getattr(window, "show_toast", None)
        if callable(show_toast):
            show_toast("Local robot unlinked from Fleet.", level="info")
        self._refresh_local_link_ui()

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        robot_id = self._get_selected_robot_id()
        if robot_id:
            self.robot_details_requested.emit(robot_id)

    def _show_context_menu(self, pos) -> None:
        robot_id = self._get_selected_robot_id()
        if not robot_id:
            return

        robot = self._robot_map.get(robot_id)
        if robot is None:
            return

        menu = QMenu(self)

        details_action = menu.addAction("View Details")
        details_action.triggered.connect(lambda: self.robot_details_requested.emit(robot_id))

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._on_edit_robot(robot_id))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._confirm_delete_robot(robot_id))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _confirm_delete_robot(self, robot_id: str) -> None:
        """Show confirmation dialog before deleting a robot."""
        robot = self._robot_map.get(robot_id)
        robot_name = robot.name if robot else robot_id

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete robot '{robot_name}'?\n\n"
            "This will remove the robot from the orchestrator database.\n"
            "A deleted robot will not automatically re-register.\n"
            "To make a local robot appear again, create a new robot and use 'Link To Selected Robot'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.robot_deleted.emit(robot_id)

    def _on_add_robot(self) -> None:
        dialog = RobotEditDialog(parent=self)
        if dialog.exec():
            self.robot_edited.emit("", dialog.get_robot_data())

    def _on_edit_robot(self, robot_id: str) -> None:
        robot = self._robot_map.get(robot_id)
        dialog = RobotEditDialog(robot=robot, parent=self)
        if dialog.exec():
            self.robot_edited.emit(robot_id, dialog.get_robot_data())
