"""
Schedule Dialog for CasareRPA Canvas.
Allows scheduling workflows directly from the Canvas editor.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTimeEdit,
    QDateTimeEdit,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt, QTime, QDateTime, Signal

from loguru import logger


class ScheduleFrequency:
    """Schedule frequency types."""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class WorkflowSchedule:
    """Workflow schedule data."""

    def __init__(
        self,
        id: str = "",
        name: str = "",
        workflow_path: str = "",
        workflow_name: str = "",
        frequency: str = ScheduleFrequency.DAILY,
        cron_expression: str = "",
        time_hour: int = 9,
        time_minute: int = 0,
        day_of_week: int = 0,  # 0=Monday
        day_of_month: int = 1,
        timezone: str = "local",
        enabled: bool = True,
        next_run: Optional[datetime] = None,
        last_run: Optional[datetime] = None,
        run_count: int = 0,
        success_count: int = 0,
        failure_count: int = 0,
        created_at: Optional[datetime] = None,
        last_error: str = "",
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.workflow_path = workflow_path
        self.workflow_name = workflow_name
        self.frequency = frequency
        self.cron_expression = cron_expression
        self.time_hour = time_hour
        self.time_minute = time_minute
        self.day_of_week = day_of_week
        self.day_of_month = day_of_month
        self.timezone = timezone
        self.enabled = enabled
        self.next_run = next_run
        self.last_run = last_run
        self.run_count = run_count
        self.success_count = success_count
        self.failure_count = failure_count
        self.created_at = created_at or datetime.now()
        self.last_error = last_error

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "workflow_path": self.workflow_path,
            "workflow_name": self.workflow_name,
            "frequency": self.frequency,
            "cron_expression": self.cron_expression,
            "time_hour": self.time_hour,
            "time_minute": self.time_minute,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowSchedule":
        """Create from dictionary."""

        def parse_datetime(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            try:
                return datetime.fromisoformat(val)
            except (ValueError, TypeError):
                return None

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workflow_path=data.get("workflow_path", ""),
            workflow_name=data.get("workflow_name", ""),
            frequency=data.get("frequency", ScheduleFrequency.DAILY),
            cron_expression=data.get("cron_expression", ""),
            time_hour=data.get("time_hour", 9),
            time_minute=data.get("time_minute", 0),
            day_of_week=data.get("day_of_week", 0),
            day_of_month=data.get("day_of_month", 1),
            timezone=data.get("timezone", "local"),
            enabled=data.get("enabled", True),
            next_run=parse_datetime(data.get("next_run")),
            last_run=parse_datetime(data.get("last_run")),
            run_count=data.get("run_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            created_at=parse_datetime(data.get("created_at")),
            last_error=data.get("last_error", ""),
        )

    def calculate_next_run(
        self, from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate the next run time based on frequency."""
        now = from_time or datetime.now()

        if self.frequency == ScheduleFrequency.ONCE:
            # For one-time, next_run should already be set
            return self.next_run if self.next_run and self.next_run > now else None

        elif self.frequency == ScheduleFrequency.HOURLY:
            # Next hour at the specified minute
            next_run = now.replace(minute=self.time_minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
            return next_run

        elif self.frequency == ScheduleFrequency.DAILY:
            # Today or tomorrow at the specified time
            next_run = now.replace(
                hour=self.time_hour, minute=self.time_minute, second=0, microsecond=0
            )
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif self.frequency == ScheduleFrequency.WEEKLY:
            # Calculate days until the target weekday
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead < 0:  # Target day already passed this week
                days_ahead += 7

            next_run = now.replace(
                hour=self.time_hour, minute=self.time_minute, second=0, microsecond=0
            ) + timedelta(days=days_ahead)

            if next_run <= now:
                next_run += timedelta(weeks=1)
            return next_run

        elif self.frequency == ScheduleFrequency.MONTHLY:
            # Next occurrence of the specified day of month
            next_run = now.replace(
                day=min(self.day_of_month, 28),  # Safe day
                hour=self.time_hour,
                minute=self.time_minute,
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            return next_run

        elif self.frequency == ScheduleFrequency.CRON:
            # Cron parsing would require APScheduler
            # For now, return None - the scheduler service will handle this
            return None

        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100

    @property
    def frequency_display(self) -> str:
        """Get human-readable frequency string."""
        if self.frequency == ScheduleFrequency.ONCE:
            if self.next_run:
                return f"Once at {self.next_run.strftime('%Y-%m-%d %H:%M')}"
            return "Once"
        elif self.frequency == ScheduleFrequency.HOURLY:
            return f"Hourly at :{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.DAILY:
            return f"Daily at {self.time_hour:02d}:{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.WEEKLY:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            return f"Weekly on {days[self.day_of_week]} at {self.time_hour:02d}:{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.MONTHLY:
            return f"Monthly on day {self.day_of_month} at {self.time_hour:02d}:{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.CRON:
            return f"Cron: {self.cron_expression}"
        return self.frequency


class ScheduleDialog(QDialog):
    """Dialog for creating/editing a workflow schedule."""

    def __init__(
        self,
        workflow_path: Optional[Path] = None,
        workflow_name: str = "Untitled",
        schedule: Optional[WorkflowSchedule] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._workflow_path = workflow_path
        self._workflow_name = workflow_name
        self._schedule = schedule
        self.result_schedule: Optional[WorkflowSchedule] = None

        self._setup_ui()

        if schedule:
            self._load_schedule(schedule)

    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(
            "Schedule Workflow" if not self._schedule else "Edit Schedule"
        )
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Workflow info
        info_group = QGroupBox("Workflow")
        info_layout = QFormLayout(info_group)

        self._workflow_label = QLabel(self._workflow_name)
        self._workflow_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Workflow:", self._workflow_label)

        if self._workflow_path:
            path_label = QLabel(str(self._workflow_path))
            path_label.setStyleSheet("color: #888; font-size: 11px;")
            path_label.setWordWrap(True)
            info_layout.addRow("Path:", path_label)

        layout.addWidget(info_group)

        # Schedule settings
        settings_group = QGroupBox("Schedule Settings")
        form = QFormLayout(settings_group)
        form.setSpacing(12)

        # Name
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Schedule name...")
        self._name_input.setText(f"Schedule: {self._workflow_name}")
        form.addRow("Name:", self._name_input)

        # Frequency
        self._frequency_combo = QComboBox()
        self._frequency_combo.addItems(
            ["Once", "Hourly", "Daily", "Weekly", "Monthly", "Cron"]
        )
        self._frequency_combo.currentTextChanged.connect(self._on_frequency_changed)
        form.addRow("Frequency:", self._frequency_combo)

        # Time (for daily/weekly/monthly)
        self._time_edit = QTimeEdit()
        self._time_edit.setDisplayFormat("HH:mm")
        self._time_edit.setTime(QTime(9, 0))
        form.addRow("Time:", self._time_edit)
        self._time_label = form.labelForField(self._time_edit)

        # Day of week (for weekly)
        self._day_combo = QComboBox()
        self._day_combo.addItems(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        form.addRow("Day:", self._day_combo)
        self._day_label = form.labelForField(self._day_combo)
        self._day_combo.hide()
        self._day_label.hide()

        # Day of month (for monthly)
        self._day_spin = QSpinBox()
        self._day_spin.setRange(1, 28)
        self._day_spin.setValue(1)
        form.addRow("Day of Month:", self._day_spin)
        self._day_month_label = form.labelForField(self._day_spin)
        self._day_spin.hide()
        self._day_month_label.hide()

        # Cron expression (for cron)
        self._cron_input = QLineEdit()
        self._cron_input.setPlaceholderText(
            "0 9 * * MON-FRI (minute hour day month weekday)"
        )
        form.addRow("Cron:", self._cron_input)
        self._cron_label = form.labelForField(self._cron_input)
        self._cron_input.hide()
        self._cron_label.hide()

        # One-time datetime
        self._datetime_edit = QDateTimeEdit()
        self._datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self._datetime_edit.setCalendarPopup(True)
        self._datetime_edit.setMinimumDateTime(QDateTime.currentDateTime())
        form.addRow("Date/Time:", self._datetime_edit)
        self._datetime_label = form.labelForField(self._datetime_edit)
        self._datetime_edit.hide()
        self._datetime_label.hide()

        # Enabled
        self._enabled_check = QCheckBox("Enabled")
        self._enabled_check.setChecked(True)
        form.addRow("", self._enabled_check)

        layout.addWidget(settings_group)

        # Next run preview
        self._next_run_label = QLabel("Next run: Calculating...")
        self._next_run_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self._next_run_label)

        # Connect signals for preview update
        self._frequency_combo.currentTextChanged.connect(self._update_next_run_preview)
        self._time_edit.timeChanged.connect(self._update_next_run_preview)
        self._day_combo.currentIndexChanged.connect(self._update_next_run_preview)
        self._day_spin.valueChanged.connect(self._update_next_run_preview)
        self._datetime_edit.dateTimeChanged.connect(self._update_next_run_preview)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initial state
        self._on_frequency_changed("Daily")
        self._update_next_run_preview()

    def _on_frequency_changed(self, frequency: str):
        """Handle frequency change to show/hide relevant fields."""
        # Hide all optional fields first
        self._time_edit.show()
        self._time_label.show()
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
            self._time_label.hide()
            self._datetime_edit.show()
            self._datetime_label.show()
        elif frequency == "Hourly":
            # Only need minute
            self._time_label.setText("Minute:")
        elif frequency == "Daily":
            self._time_label.setText("Time:")
        elif frequency == "Weekly":
            self._time_label.setText("Time:")
            self._day_combo.show()
            self._day_label.show()
        elif frequency == "Monthly":
            self._time_label.setText("Time:")
            self._day_spin.show()
            self._day_month_label.show()
        elif frequency == "Cron":
            self._time_edit.hide()
            self._time_label.hide()
            self._cron_input.show()
            self._cron_label.show()

        self._update_next_run_preview()

    def _update_next_run_preview(self):
        """Update the next run preview label."""
        schedule = self._build_schedule()
        if schedule:
            next_run = schedule.calculate_next_run()
            if next_run:
                self._next_run_label.setText(
                    f"Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self._next_run_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif schedule.frequency == ScheduleFrequency.CRON:
                self._next_run_label.setText("Next run: (calculated by scheduler)")
                self._next_run_label.setStyleSheet("color: #FFA726; font-weight: bold;")
            else:
                self._next_run_label.setText("Next run: Unable to calculate")
                self._next_run_label.setStyleSheet("color: #EF5350; font-weight: bold;")

    def _build_schedule(self) -> Optional[WorkflowSchedule]:
        """Build schedule object from form data."""
        frequency_map = {
            "Once": ScheduleFrequency.ONCE,
            "Hourly": ScheduleFrequency.HOURLY,
            "Daily": ScheduleFrequency.DAILY,
            "Weekly": ScheduleFrequency.WEEKLY,
            "Monthly": ScheduleFrequency.MONTHLY,
            "Cron": ScheduleFrequency.CRON,
        }

        frequency = frequency_map.get(
            self._frequency_combo.currentText(), ScheduleFrequency.DAILY
        )

        time = self._time_edit.time()

        schedule = WorkflowSchedule(
            id=self._schedule.id if self._schedule else str(uuid.uuid4()),
            name=self._name_input.text().strip() or f"Schedule: {self._workflow_name}",
            workflow_path=str(self._workflow_path) if self._workflow_path else "",
            workflow_name=self._workflow_name,
            frequency=frequency,
            cron_expression=self._cron_input.text().strip(),
            time_hour=time.hour(),
            time_minute=time.minute(),
            day_of_week=self._day_combo.currentIndex(),
            day_of_month=self._day_spin.value(),
            timezone="local",
            enabled=self._enabled_check.isChecked(),
            created_at=self._schedule.created_at if self._schedule else datetime.now(),
            run_count=self._schedule.run_count if self._schedule else 0,
            success_count=self._schedule.success_count if self._schedule else 0,
            failure_count=self._schedule.failure_count if self._schedule else 0,
        )

        # Set next_run for one-time schedules
        if frequency == ScheduleFrequency.ONCE:
            schedule.next_run = self._datetime_edit.dateTime().toPython()
        else:
            schedule.next_run = schedule.calculate_next_run()

        return schedule

    def _load_schedule(self, schedule: WorkflowSchedule):
        """Load schedule data into form."""
        self._name_input.setText(schedule.name)

        # Set frequency
        freq_map = {
            ScheduleFrequency.ONCE: "Once",
            ScheduleFrequency.HOURLY: "Hourly",
            ScheduleFrequency.DAILY: "Daily",
            ScheduleFrequency.WEEKLY: "Weekly",
            ScheduleFrequency.MONTHLY: "Monthly",
            ScheduleFrequency.CRON: "Cron",
        }
        self._frequency_combo.setCurrentText(freq_map.get(schedule.frequency, "Daily"))

        # Set time
        self._time_edit.setTime(QTime(schedule.time_hour, schedule.time_minute))

        # Set day of week
        self._day_combo.setCurrentIndex(schedule.day_of_week)

        # Set day of month
        self._day_spin.setValue(schedule.day_of_month)

        # Set cron expression
        self._cron_input.setText(schedule.cron_expression)

        # Set one-time datetime
        if schedule.next_run:
            self._datetime_edit.setDateTime(
                QDateTime(
                    schedule.next_run.year,
                    schedule.next_run.month,
                    schedule.next_run.day,
                    schedule.next_run.hour,
                    schedule.next_run.minute,
                )
            )

        self._enabled_check.setChecked(schedule.enabled)

    def _on_save(self):
        """Validate and save the schedule."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Validation Error", "Please enter a schedule name"
            )
            return

        frequency = self._frequency_combo.currentText()

        # Validate cron expression
        if frequency == "Cron":
            cron = self._cron_input.text().strip()
            if not cron:
                QMessageBox.warning(
                    self, "Validation Error", "Please enter a cron expression"
                )
                return
            parts = cron.split()
            if len(parts) not in (5, 6):
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Invalid cron expression. Use 5 or 6 space-separated fields:\n"
                    "minute hour day month weekday\n"
                    "or: second minute hour day month weekday",
                )
                return

        # Validate one-time is in the future
        if frequency == "Once":
            if self._datetime_edit.dateTime().toPython() <= datetime.now():
                QMessageBox.warning(
                    self, "Validation Error", "One-time schedule must be in the future"
                )
                return

        self.result_schedule = self._build_schedule()
        logger.info(
            f"Schedule created: {self.result_schedule.name} ({self.result_schedule.frequency_display})"
        )
        self.accept()


class ScheduleManagerDialog(QDialog):
    """Dialog for managing all workflow schedules."""

    schedule_changed = Signal()  # Emitted when schedules are modified
    run_schedule = Signal(object)  # Emitted to run a schedule immediately

    def __init__(
        self, schedules: List[WorkflowSchedule], parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._schedules = list(schedules)
        self._setup_ui()
        self._update_table()

    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Schedule Manager")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header with buttons
        header = QHBoxLayout()

        title = QLabel("Scheduled Workflows")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._update_table)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Schedules table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Enabled",
                "Name",
                "Workflow",
                "Frequency",
                "Next Run",
                "Last Run",
                "Success Rate",
                "Actions",
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(0, 70)
        self._table.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(7, 180)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Summary
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #888;")
        layout.addWidget(self._summary_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

    def _update_table(self):
        """Update the table with current schedules."""
        self._table.setRowCount(len(self._schedules))

        enabled_count = 0

        for row, schedule in enumerate(self._schedules):
            # Enabled checkbox
            enabled_check = QCheckBox()
            enabled_check.setChecked(schedule.enabled)
            enabled_check.stateChanged.connect(
                lambda state, s=schedule: self._on_toggle_enabled(s, state)
            )
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(enabled_check)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(row, 0, cell_widget)

            if schedule.enabled:
                enabled_count += 1

            # Name
            self._table.setItem(row, 1, QTableWidgetItem(schedule.name))

            # Workflow
            self._table.setItem(row, 2, QTableWidgetItem(schedule.workflow_name))

            # Frequency
            self._table.setItem(row, 3, QTableWidgetItem(schedule.frequency_display))

            # Next Run
            next_run = (
                schedule.next_run.strftime("%Y-%m-%d %H:%M")
                if schedule.next_run
                else "-"
            )
            self._table.setItem(row, 4, QTableWidgetItem(next_run))

            # Last Run
            last_run = (
                schedule.last_run.strftime("%Y-%m-%d %H:%M")
                if schedule.last_run
                else "Never"
            )
            self._table.setItem(row, 5, QTableWidgetItem(last_run))

            # Success Rate
            success_text = (
                f"{schedule.success_rate:.0f}%" if schedule.run_count > 0 else "-"
            )
            self._table.setItem(row, 6, QTableWidgetItem(success_text))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, s=schedule: self._on_edit(s))
            actions_layout.addWidget(edit_btn)

            run_btn = QPushButton("Run")
            run_btn.clicked.connect(lambda _, s=schedule: self._on_run_now(s))
            actions_layout.addWidget(run_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, s=schedule: self._on_delete(s))
            actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 7, actions_widget)

        # Update summary
        self._summary_label.setText(
            f"Total: {len(self._schedules)} schedules, {enabled_count} enabled"
        )

    def _show_context_menu(self, pos):
        """Show context menu for schedule row."""
        from PySide6.QtWidgets import QMenu

        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._schedules):
            return

        schedule = self._schedules[row]
        menu = QMenu(self)

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._on_edit(schedule))

        toggle_text = "Disable" if schedule.enabled else "Enable"
        toggle_action = menu.addAction(toggle_text)
        toggle_action.triggered.connect(
            lambda: self._on_toggle_enabled(schedule, not schedule.enabled)
        )

        run_action = menu.addAction("Run Now")
        run_action.triggered.connect(lambda: self._on_run_now(schedule))

        menu.addSeparator()

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete(schedule))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, row: int, col: int):
        """Handle double-click on table row."""
        if 0 <= row < len(self._schedules):
            self._on_edit(self._schedules[row])

    def _on_toggle_enabled(self, schedule: WorkflowSchedule, enabled):
        """Toggle schedule enabled state."""
        schedule.enabled = bool(enabled) if isinstance(enabled, int) else enabled
        schedule.next_run = schedule.calculate_next_run() if schedule.enabled else None
        self.schedule_changed.emit()
        self._update_table()

    def _on_edit(self, schedule: WorkflowSchedule):
        """Edit a schedule."""
        dialog = ScheduleDialog(
            workflow_path=Path(schedule.workflow_path)
            if schedule.workflow_path
            else None,
            workflow_name=schedule.workflow_name,
            schedule=schedule,
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_schedule:
            # Update the schedule
            idx = self._schedules.index(schedule)
            self._schedules[idx] = dialog.result_schedule
            self.schedule_changed.emit()
            self._update_table()

    def _on_run_now(self, schedule: WorkflowSchedule):
        """Run a schedule immediately."""
        self.run_schedule.emit(schedule)

    def _on_delete(self, schedule: WorkflowSchedule):
        """Delete a schedule."""
        reply = QMessageBox.question(
            self,
            "Delete Schedule",
            f"Are you sure you want to delete '{schedule.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._schedules.remove(schedule)
            self.schedule_changed.emit()
            self._update_table()

    def get_schedules(self) -> List[WorkflowSchedule]:
        """Get the current list of schedules."""
        return self._schedules
