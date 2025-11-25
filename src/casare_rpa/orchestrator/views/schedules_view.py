"""
Schedules view for CasareRPA Orchestrator.
Displays workflow schedules and scheduling management.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLabel, QMessageBox, QMenu, QDialog,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
    QSpinBox, QTimeEdit, QDateTimeEdit
)
from PySide6.QtCore import Qt, Signal, QTime, QDateTime

from ..styles import COLORS
from ..widgets import SearchBar, ActionButton, SectionHeader, StatusBadge, EmptyState
from ..models import Schedule, ScheduleFrequency, JobPriority, Workflow
from ..services import OrchestratorService


class ScheduleDialog(QDialog):
    """Dialog for creating/editing a schedule."""

    def __init__(
        self,
        service: OrchestratorService,
        schedule: Optional[Schedule] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._service = service
        self._schedule = schedule
        self._workflows: List[Workflow] = []
        self._robots: list = []

        self.setWindowTitle("Edit Schedule" if schedule else "Create Schedule")
        self.setMinimumWidth(450)

        self._setup_ui()

        # Load data
        asyncio.get_event_loop().create_task(self._load_data())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        # Name
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Schedule name...")
        if self._schedule:
            self._name_input.setText(self._schedule.name)
        form.addRow("Name:", self._name_input)

        # Workflow
        self._workflow_combo = QComboBox()
        form.addRow("Workflow:", self._workflow_combo)

        # Robot (optional)
        self._robot_combo = QComboBox()
        self._robot_combo.addItem("Any Available Robot", None)
        form.addRow("Robot:", self._robot_combo)

        # Frequency
        self._frequency_combo = QComboBox()
        self._frequency_combo.addItems(["Once", "Hourly", "Daily", "Weekly", "Monthly", "Cron"])
        self._frequency_combo.currentTextChanged.connect(self._on_frequency_changed)
        if self._schedule:
            self._frequency_combo.setCurrentText(self._schedule.frequency.value.title())
        form.addRow("Frequency:", self._frequency_combo)

        # Time (for daily/weekly/monthly)
        self._time_edit = QTimeEdit()
        self._time_edit.setDisplayFormat("HH:mm")
        self._time_edit.setTime(QTime(9, 0))
        form.addRow("Time:", self._time_edit)

        # Day of week (for weekly)
        self._day_combo = QComboBox()
        self._day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self._day_combo.hide()
        form.addRow("Day:", self._day_combo)
        self._day_label = form.labelForField(self._day_combo)
        self._day_label.hide()

        # Day of month (for monthly)
        self._day_spin = QSpinBox()
        self._day_spin.setRange(1, 28)
        self._day_spin.setValue(1)
        self._day_spin.hide()
        form.addRow("Day of Month:", self._day_spin)
        self._day_month_label = form.labelForField(self._day_spin)
        self._day_month_label.hide()

        # Cron expression (for cron)
        self._cron_input = QLineEdit()
        self._cron_input.setPlaceholderText("0 9 * * MON-FRI")
        self._cron_input.hide()
        if self._schedule and self._schedule.cron_expression:
            self._cron_input.setText(self._schedule.cron_expression)
        form.addRow("Cron Expression:", self._cron_input)
        self._cron_label = form.labelForField(self._cron_input)
        self._cron_label.hide()

        # One-time datetime
        self._datetime_edit = QDateTimeEdit()
        self._datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self._datetime_edit.setCalendarPopup(True)
        self._datetime_edit.hide()
        form.addRow("Date/Time:", self._datetime_edit)
        self._datetime_label = form.labelForField(self._datetime_edit)
        self._datetime_label.hide()

        # Priority
        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["Normal", "Low", "High", "Critical"])
        if self._schedule:
            self._priority_combo.setCurrentText(self._schedule.priority.name.title())
        form.addRow("Priority:", self._priority_combo)

        # Enabled
        self._enabled_check = QCheckBox("Enabled")
        self._enabled_check.setChecked(self._schedule.enabled if self._schedule else True)
        form.addRow("", self._enabled_check)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initial state
        self._on_frequency_changed(self._frequency_combo.currentText())

    def _on_frequency_changed(self, frequency: str):
        """Handle frequency change to show/hide relevant fields."""
        # Hide all optional fields
        self._time_edit.show()
        self._day_combo.hide()
        self._day_label.hide()
        self._day_spin.hide()
        self._day_month_label.hide()
        self._cron_input.hide()
        self._cron_label.hide()
        self._datetime_edit.hide()
        self._datetime_label.hide()

        if frequency == "Once":
            self._time_edit.hide()
            self._datetime_edit.show()
            self._datetime_label.show()
        elif frequency == "Weekly":
            self._day_combo.show()
            self._day_label.show()
        elif frequency == "Monthly":
            self._day_spin.show()
            self._day_month_label.show()
        elif frequency == "Cron":
            self._time_edit.hide()
            self._cron_input.show()
            self._cron_label.show()

    async def _load_data(self):
        """Load workflows and robots."""
        from ..models import WorkflowStatus
        self._workflows = await self._service.get_workflows(status=WorkflowStatus.PUBLISHED)
        self._robots = await self._service.get_robots()

        self._workflow_combo.clear()
        for wf in self._workflows:
            self._workflow_combo.addItem(wf.name, wf.id)

        # Select current workflow if editing
        if self._schedule:
            for i in range(self._workflow_combo.count()):
                if self._workflow_combo.itemData(i) == self._schedule.workflow_id:
                    self._workflow_combo.setCurrentIndex(i)
                    break

        # Add robots
        for robot in self._robots:
            self._robot_combo.addItem(f"{robot.name} ({robot.id[:8]}...)", robot.id)

        if self._schedule and self._schedule.robot_id:
            for i in range(self._robot_combo.count()):
                if self._robot_combo.itemData(i) == self._schedule.robot_id:
                    self._robot_combo.setCurrentIndex(i)
                    break

    def _on_save(self):
        """Save the schedule."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a schedule name")
            return

        workflow_id = self._workflow_combo.currentData()
        if not workflow_id:
            QMessageBox.warning(self, "Validation Error", "Please select a workflow")
            return

        # Build schedule data
        frequency_map = {
            "Once": ScheduleFrequency.ONCE,
            "Hourly": ScheduleFrequency.HOURLY,
            "Daily": ScheduleFrequency.DAILY,
            "Weekly": ScheduleFrequency.WEEKLY,
            "Monthly": ScheduleFrequency.MONTHLY,
            "Cron": ScheduleFrequency.CRON,
        }
        frequency = frequency_map.get(self._frequency_combo.currentText(), ScheduleFrequency.DAILY)

        priority_map = {
            "Low": JobPriority.LOW,
            "Normal": JobPriority.NORMAL,
            "High": JobPriority.HIGH,
            "Critical": JobPriority.CRITICAL,
        }
        priority = priority_map.get(self._priority_combo.currentText(), JobPriority.NORMAL)

        cron_expression = ""
        if frequency == ScheduleFrequency.CRON:
            cron_expression = self._cron_input.text().strip()
            if not cron_expression:
                QMessageBox.warning(self, "Validation Error", "Please enter a cron expression")
                return

        # Calculate next run time
        now = datetime.utcnow()
        next_run = now + timedelta(minutes=5)  # Default

        if frequency == ScheduleFrequency.ONCE:
            next_run = self._datetime_edit.dateTime().toPython()
        elif frequency == ScheduleFrequency.HOURLY:
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif frequency == ScheduleFrequency.DAILY:
            time = self._time_edit.time().toPython()
            next_run = now.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

        self.result_schedule = Schedule(
            id=self._schedule.id if self._schedule else "",
            name=name,
            workflow_id=workflow_id,
            workflow_name=self._workflow_combo.currentText(),
            robot_id=self._robot_combo.currentData(),
            robot_name=self._robot_combo.currentText() if self._robot_combo.currentData() else "",
            frequency=frequency,
            cron_expression=cron_expression,
            timezone="UTC",
            enabled=self._enabled_check.isChecked(),
            priority=priority,
            next_run=next_run.isoformat(),
            created_at=self._schedule.created_at if self._schedule else None,
            run_count=self._schedule.run_count if self._schedule else 0,
            success_count=self._schedule.success_count if self._schedule else 0,
        )

        self.accept()


class SchedulesView(QWidget):
    """Schedules management view."""

    def __init__(self, service: OrchestratorService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._service = service
        self._schedules: List[Schedule] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        header = SectionHeader("Schedules")
        header_layout.addWidget(header)

        header_layout.addStretch()

        create_btn = ActionButton("Create Schedule", primary=True)
        create_btn.clicked.connect(lambda: asyncio.get_event_loop().create_task(self._create_schedule()))
        header_layout.addWidget(create_btn)

        refresh_btn = ActionButton("Refresh", primary=False)
        refresh_btn.clicked.connect(lambda: asyncio.get_event_loop().create_task(self.refresh()))
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Search and filters
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search = SearchBar(
            "Search schedules...",
            filters=["All", "Enabled", "Disabled"]
        )
        self._search.search_changed.connect(self._apply_filter)
        self._search.filter_changed.connect(self._apply_filter)
        toolbar.addWidget(self._search)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Schedules table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Enabled", "Name", "Workflow", "Frequency", "Next Run", "Last Run", "Success", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 80)
        self._table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(7, 180)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Empty state
        self._empty_state = EmptyState(
            title="No Schedules Found",
            description="Create a schedule to automatically run workflows.",
            action_text="Create Schedule"
        )
        self._empty_state.action_clicked.connect(lambda: asyncio.get_event_loop().create_task(self._create_schedule()))
        self._empty_state.hide()
        layout.addWidget(self._empty_state)

    def _apply_filter(self):
        """Apply search and filter to table."""
        search_text = self._search.get_search_text().lower()
        filter_status = self._search.get_filter()

        for row in range(self._table.rowCount()):
            show = True

            if filter_status == "Enabled":
                enabled_widget = self._table.cellWidget(row, 0)
                if enabled_widget and not enabled_widget.isChecked():
                    show = False
            elif filter_status == "Disabled":
                enabled_widget = self._table.cellWidget(row, 0)
                if enabled_widget and enabled_widget.isChecked():
                    show = False

            if show and search_text:
                row_text = ""
                for col in range(self._table.columnCount()):
                    item = self._table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                if search_text not in row_text:
                    show = False

            self._table.setRowHidden(row, not show)

    def _show_context_menu(self, pos):
        """Show context menu for schedule row."""
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._schedules):
            return

        schedule = self._schedules[row]
        menu = QMenu(self)

        edit_action = menu.addAction("✏️ Edit")
        edit_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._edit_schedule(schedule)))

        toggle_text = "🔴 Disable" if schedule.enabled else "🟢 Enable"
        toggle_action = menu.addAction(toggle_text)
        toggle_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._toggle_schedule(schedule)))

        run_action = menu.addAction("▶️ Run Now")
        run_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._run_now(schedule)))

        menu.addSeparator()

        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._delete_schedule(schedule)))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, row: int, col: int):
        """Handle double-click on table row."""
        if 0 <= row < len(self._schedules):
            asyncio.get_event_loop().create_task(self._edit_schedule(self._schedules[row]))

    async def _create_schedule(self):
        """Create a new schedule."""
        dialog = ScheduleDialog(self._service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            import uuid
            dialog.result_schedule.id = str(uuid.uuid4())
            dialog.result_schedule.created_at = datetime.utcnow().isoformat()

            if await self._service.save_schedule(dialog.result_schedule):
                await self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to create schedule")

    async def _edit_schedule(self, schedule: Schedule):
        """Edit an existing schedule."""
        dialog = ScheduleDialog(self._service, schedule=schedule, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if await self._service.save_schedule(dialog.result_schedule):
                await self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to update schedule")

    async def _toggle_schedule(self, schedule: Schedule):
        """Toggle schedule enabled state."""
        if await self._service.toggle_schedule(schedule.id, not schedule.enabled):
            await self.refresh()
        else:
            QMessageBox.warning(self, "Error", "Failed to toggle schedule")

    async def _run_now(self, schedule: Schedule):
        """Run the scheduled workflow immediately."""
        # Find an available robot or use the assigned one
        robot_id = schedule.robot_id
        if not robot_id:
            robots = await self._service.get_available_robots()
            if robots:
                robot_id = robots[0].id
            else:
                QMessageBox.warning(self, "Error", "No available robots to run the workflow")
                return

        job = await self._service.dispatch_workflow(
            schedule.workflow_id,
            robot_id,
            schedule.priority
        )
        if job:
            QMessageBox.information(self, "Success", f"Job dispatched: {job.id[:8]}...")
        else:
            QMessageBox.warning(self, "Error", "Failed to dispatch workflow")

    async def _delete_schedule(self, schedule: Schedule):
        """Delete a schedule."""
        reply = QMessageBox.question(
            self, "Delete Schedule",
            f"Are you sure you want to delete '{schedule.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if await self._service.delete_schedule(schedule.id):
                await self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete schedule")

    def _update_table(self):
        """Update the table with current schedules."""
        self._table.setRowCount(len(self._schedules))

        if not self._schedules:
            self._table.hide()
            self._empty_state.show()
            return

        self._table.show()
        self._empty_state.hide()

        for row, schedule in enumerate(self._schedules):
            # Enabled checkbox
            enabled_check = QCheckBox()
            enabled_check.setChecked(schedule.enabled)
            enabled_check.stateChanged.connect(
                lambda state, s=schedule: asyncio.get_event_loop().create_task(
                    self._service.toggle_schedule(s.id, state == Qt.CheckState.Checked.value)
                )
            )
            self._table.setCellWidget(row, 0, enabled_check)

            # Name
            self._table.setItem(row, 1, QTableWidgetItem(schedule.name))

            # Workflow
            self._table.setItem(row, 2, QTableWidgetItem(schedule.workflow_name))

            # Frequency
            freq_text = schedule.frequency.value.title()
            if schedule.cron_expression:
                freq_text = f"Cron: {schedule.cron_expression}"
            self._table.setItem(row, 3, QTableWidgetItem(freq_text))

            # Next Run
            next_run = str(schedule.next_run)[:19] if schedule.next_run else "-"
            self._table.setItem(row, 4, QTableWidgetItem(next_run))

            # Last Run
            last_run = str(schedule.last_run)[:19] if schedule.last_run else "Never"
            self._table.setItem(row, 5, QTableWidgetItem(last_run))

            # Success Rate
            self._table.setItem(row, 6, QTableWidgetItem(f"{schedule.success_rate:.0f}%"))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            edit_btn = ActionButton("Edit", primary=False)
            edit_btn.clicked.connect(lambda checked, s=schedule: asyncio.get_event_loop().create_task(self._edit_schedule(s)))
            actions_layout.addWidget(edit_btn)

            run_btn = ActionButton("Run", primary=True)
            run_btn.clicked.connect(lambda checked, s=schedule: asyncio.get_event_loop().create_task(self._run_now(s)))
            actions_layout.addWidget(run_btn)

            self._table.setCellWidget(row, 7, actions_widget)

    async def refresh(self):
        """Refresh schedules data."""
        try:
            self._schedules = await self._service.get_schedules()
            self._update_table()
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to refresh schedules: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load schedules: {e}")
