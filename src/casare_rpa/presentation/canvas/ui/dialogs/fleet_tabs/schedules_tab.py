"""
Schedules Tab Widget for Fleet Dashboard.

Displays workflow schedules with management capabilities.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

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
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QBrush


class SchedulesTabWidget(QWidget):
    """
    Widget for displaying and managing workflow schedules.

    Features:
    - Schedule table with frequency, next run, last run
    - Enable/Disable toggle
    - Search and filter
    - Edit/Delete actions
    - Run now capability

    Signals:
        schedule_selected: Emitted when schedule is selected (schedule_id)
        schedule_enabled_changed: Emitted when schedule is enabled/disabled (schedule_id, enabled)
        schedule_edited: Emitted when schedule edit is requested (schedule_id)
        schedule_deleted: Emitted when schedule is deleted (schedule_id)
        schedule_run_now: Emitted when run now is clicked (schedule_id)
        refresh_requested: Emitted when refresh is clicked
    """

    schedule_selected = Signal(str)
    schedule_enabled_changed = Signal(str, bool)
    schedule_edited = Signal(str)
    schedule_deleted = Signal(str)
    schedule_run_now = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._schedules: List[Dict[str, Any]] = []
        self._schedule_map: Dict[str, Dict[str, Any]] = {}
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

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search schedules...")
        self._search_edit.textChanged.connect(self._apply_filters)
        self._search_edit.setMinimumWidth(200)
        toolbar.addWidget(self._search_edit)

        self._status_filter = QComboBox()
        self._status_filter.addItems(
            [
                "All Schedules",
                "Enabled",
                "Disabled",
            ]
        )
        self._status_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._status_filter)

        self._frequency_filter = QComboBox()
        self._frequency_filter.addItems(
            [
                "All Frequencies",
                "Once",
                "Hourly",
                "Daily",
                "Weekly",
                "Monthly",
                "Cron",
            ]
        )
        self._frequency_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._frequency_filter)

        toolbar.addStretch()

        self._add_btn = QPushButton("Add Schedule")
        self._add_btn.clicked.connect(self._on_add_schedule)
        toolbar.addWidget(self._add_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels(
            [
                "Enabled",
                "Name",
                "Workflow",
                "Frequency",
                "Next Run",
                "Last Run",
                "Success Rate",
                "Runs",
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 70)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(8, 180)

        layout.addWidget(self._table)

        self._status_label = QLabel("0 schedules")
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

    def update_schedules(self, schedules: List[Dict[str, Any]]) -> None:
        """Update table with schedule list."""
        self._schedules = schedules
        self._schedule_map = {s.get("id", ""): s for s in schedules}
        self._populate_table()
        self._update_status_label()

    def _populate_table(self) -> None:
        """Populate table with current schedules."""
        self._table.setRowCount(len(self._schedules))

        for row, schedule in enumerate(self._schedules):
            schedule_id = schedule.get("id", "")

            enabled_widget = QWidget()
            enabled_layout = QHBoxLayout(enabled_widget)
            enabled_layout.setContentsMargins(0, 0, 0, 0)
            enabled_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            enabled_check = QCheckBox()
            enabled_check.setChecked(schedule.get("enabled", True))
            enabled_check.stateChanged.connect(
                lambda state, sid=schedule_id: self._on_enabled_changed(sid, state)
            )
            enabled_layout.addWidget(enabled_check)
            self._table.setCellWidget(row, 0, enabled_widget)

            name_item = QTableWidgetItem(schedule.get("name", "-"))
            name_item.setData(Qt.ItemDataRole.UserRole, schedule_id)
            self._table.setItem(row, 1, name_item)

            self._table.setItem(
                row, 2, QTableWidgetItem(schedule.get("workflow_name", "-"))
            )

            frequency = schedule.get("frequency", "daily")
            freq_display = self._get_frequency_display(schedule)
            self._table.setItem(row, 3, QTableWidgetItem(freq_display))

            next_run = schedule.get("next_run")
            if next_run:
                if isinstance(next_run, datetime):
                    next_run_str = next_run.strftime("%Y-%m-%d %H:%M")
                else:
                    next_run_str = str(next_run)[:16]
            else:
                next_run_str = "-"
            next_item = QTableWidgetItem(next_run_str)

            if schedule.get("enabled", True) and next_run:
                if isinstance(next_run, datetime) and next_run <= datetime.now():
                    next_item.setForeground(QBrush(QColor(0xF4, 0x43, 0x36)))
            self._table.setItem(row, 4, next_item)

            last_run = schedule.get("last_run")
            if last_run:
                if isinstance(last_run, datetime):
                    last_run_str = last_run.strftime("%Y-%m-%d %H:%M")
                else:
                    last_run_str = str(last_run)[:16]
            else:
                last_run_str = "Never"
            self._table.setItem(row, 5, QTableWidgetItem(last_run_str))

            run_count = schedule.get("run_count", 0)
            success_count = schedule.get("success_count", 0)
            if run_count > 0:
                success_rate = (success_count / run_count) * 100
                rate_item = QTableWidgetItem(f"{success_rate:.0f}%")
                if success_rate >= 90:
                    rate_item.setForeground(QBrush(QColor(0x4C, 0xAF, 0x50)))
                elif success_rate >= 70:
                    rate_item.setForeground(QBrush(QColor(0xFF, 0xC1, 0x07)))
                else:
                    rate_item.setForeground(QBrush(QColor(0xF4, 0x43, 0x36)))
            else:
                rate_item = QTableWidgetItem("-")
            self._table.setItem(row, 6, rate_item)

            self._table.setItem(row, 7, QTableWidgetItem(str(run_count)))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            run_btn = QPushButton("Run")
            run_btn.setMaximumHeight(24)
            run_btn.clicked.connect(lambda _, s=schedule: self._on_run_now(s))
            actions_layout.addWidget(run_btn)

            edit_btn = QPushButton("Edit")
            edit_btn.setMaximumHeight(24)
            edit_btn.clicked.connect(lambda _, s=schedule: self._on_edit_schedule(s))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumHeight(24)
            delete_btn.clicked.connect(
                lambda _, s=schedule: self._on_delete_schedule(s)
            )
            actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 8, actions_widget)

        self._apply_filters()

    def _get_frequency_display(self, schedule: Dict[str, Any]) -> str:
        """Get human-readable frequency string."""
        frequency = schedule.get("frequency", "daily")
        time_hour = schedule.get("time_hour", 9)
        time_minute = schedule.get("time_minute", 0)

        if frequency == "once":
            next_run = schedule.get("next_run")
            if next_run:
                if isinstance(next_run, datetime):
                    return f"Once at {next_run.strftime('%Y-%m-%d %H:%M')}"
            return "Once"
        elif frequency == "hourly":
            return f"Hourly at :{time_minute:02d}"
        elif frequency == "daily":
            return f"Daily at {time_hour:02d}:{time_minute:02d}"
        elif frequency == "weekly":
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day = schedule.get("day_of_week", 0)
            return f"{days[day]} at {time_hour:02d}:{time_minute:02d}"
        elif frequency == "monthly":
            day = schedule.get("day_of_month", 1)
            return f"Day {day} at {time_hour:02d}:{time_minute:02d}"
        elif frequency == "cron":
            cron = schedule.get("cron_expression", "")
            return f"Cron: {cron}" if cron else "Cron"

        return frequency.title()

    def _apply_filters(self) -> None:
        """Apply search and filter to table rows."""
        search_text = self._search_edit.text().lower()
        status_filter = self._status_filter.currentText().lower()
        freq_filter = self._frequency_filter.currentText().lower()

        visible_count = 0
        for row in range(self._table.rowCount()):
            schedule_id = self._table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            schedule = self._schedule_map.get(schedule_id)

            if schedule is None:
                self._table.setRowHidden(row, True)
                continue

            show = True

            if search_text:
                name_match = search_text in schedule.get("name", "").lower()
                workflow_match = (
                    search_text in schedule.get("workflow_name", "").lower()
                )
                if not (name_match or workflow_match):
                    show = False

            if show and status_filter == "enabled":
                if not schedule.get("enabled", True):
                    show = False
            elif show and status_filter == "disabled":
                if schedule.get("enabled", True):
                    show = False

            if show and freq_filter != "all frequencies":
                if schedule.get("frequency", "").lower() != freq_filter:
                    show = False

            self._table.setRowHidden(row, not show)
            if show:
                visible_count += 1

        self._update_status_label(visible_count)

    def _update_status_label(self, visible: Optional[int] = None) -> None:
        """Update status label with schedule counts."""
        total = len(self._schedules)
        enabled = sum(1 for s in self._schedules if s.get("enabled", True))
        disabled = total - enabled

        if visible is not None and visible != total:
            self._status_label.setText(
                f"Showing {visible} of {total} schedules | "
                f"Enabled: {enabled}, Disabled: {disabled}"
            )
        else:
            self._status_label.setText(
                f"{total} schedules | Enabled: {enabled}, Disabled: {disabled}"
            )

    def _show_context_menu(self, pos) -> None:
        """Show context menu for schedule row."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        schedule_id = self._table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        schedule = self._schedule_map.get(schedule_id)
        if not schedule:
            return

        menu = QMenu(self)

        run_action = menu.addAction("Run Now")
        run_action.triggered.connect(lambda: self._on_run_now(schedule))

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._on_edit_schedule(schedule))

        menu.addSeparator()

        if schedule.get("enabled", True):
            disable_action = menu.addAction("Disable")
            disable_action.triggered.connect(
                lambda: self.schedule_enabled_changed.emit(
                    schedule.get("id", ""), False
                )
            )
        else:
            enable_action = menu.addAction("Enable")
            enable_action.triggered.connect(
                lambda: self.schedule_enabled_changed.emit(schedule.get("id", ""), True)
            )

        menu.addSeparator()

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete_schedule(schedule))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self._table.selectedItems()
        if selected:
            schedule_id = self._table.item(selected[0].row(), 1).data(
                Qt.ItemDataRole.UserRole
            )
            if schedule_id:
                self.schedule_selected.emit(schedule_id)

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on schedule row."""
        schedule_id = self._table.item(item.row(), 1).data(Qt.ItemDataRole.UserRole)
        if schedule_id:
            self.schedule_edited.emit(schedule_id)

    def _on_enabled_changed(self, schedule_id: str, state: int) -> None:
        """Handle enabled checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.schedule_enabled_changed.emit(schedule_id, enabled)

    def _on_add_schedule(self) -> None:
        """Add new schedule."""
        self.schedule_edited.emit("")

    def _on_edit_schedule(self, schedule: Dict[str, Any]) -> None:
        """Edit schedule."""
        self.schedule_edited.emit(schedule.get("id", ""))

    def _on_delete_schedule(self, schedule: Dict[str, Any]) -> None:
        """Confirm and delete schedule."""
        schedule_id = schedule.get("id", "")
        name = schedule.get("name", "")

        reply = QMessageBox.question(
            self,
            "Delete Schedule",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.schedule_deleted.emit(schedule_id)

    def _on_run_now(self, schedule: Dict[str, Any]) -> None:
        """Run schedule immediately."""
        self.schedule_run_now.emit(schedule.get("id", ""))

    def _request_refresh(self) -> None:
        """Request schedule list refresh."""
        self.refresh_requested.emit()

    def set_refreshing(self, refreshing: bool) -> None:
        """Set refresh button state."""
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")
