"""
Tests for CasareRPA Schedule Dialog components.

Tests WorkflowSchedule model, ScheduleDialog, and ScheduleManagerDialog.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QTime, QDateTime
from PySide6.QtWidgets import QMessageBox

from casare_rpa.canvas.schedule_dialog import (
    WorkflowSchedule,
    ScheduleFrequency,
    ScheduleDialog,
    ScheduleManagerDialog,
)


class TestWorkflowScheduleModel:
    """Tests for WorkflowSchedule data model."""

    def test_create_schedule_with_defaults(self):
        """Test creating schedule with default values."""
        schedule = WorkflowSchedule()
        assert schedule.id is not None
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.time_hour == 9
        assert schedule.time_minute == 0
        assert schedule.enabled is True

    def test_create_schedule_with_custom_values(self):
        """Test creating schedule with custom values."""
        schedule = WorkflowSchedule(
            name="My Schedule",
            workflow_path="/path/to/workflow.json",
            workflow_name="Test Workflow",
            frequency=ScheduleFrequency.WEEKLY,
            time_hour=14,
            time_minute=30,
            day_of_week=4,
        )
        assert schedule.name == "My Schedule"
        assert schedule.workflow_path == "/path/to/workflow.json"
        assert schedule.frequency == ScheduleFrequency.WEEKLY
        assert schedule.time_hour == 14
        assert schedule.day_of_week == 4

    def test_to_dict_serialization(self):
        """Test serializing schedule to dictionary."""
        schedule = WorkflowSchedule(
            id="test-id",
            name="Test Schedule",
            workflow_path="/path/to/workflow.json",
            frequency=ScheduleFrequency.DAILY,
        )
        data = schedule.to_dict()
        assert data["id"] == "test-id"
        assert data["name"] == "Test Schedule"
        assert data["frequency"] == "daily"
        assert data["workflow_path"] == "/path/to/workflow.json"

    def test_from_dict_deserialization(self):
        """Test deserializing schedule from dictionary."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "workflow_path": "/path/to/workflow.json",
            "frequency": "weekly",
            "time_hour": 10,
            "time_minute": 15,
            "day_of_week": 2,
        }
        schedule = WorkflowSchedule.from_dict(data)
        assert schedule.id == "test-id"
        assert schedule.name == "Test Schedule"
        assert schedule.frequency == "weekly"
        assert schedule.time_hour == 10
        assert schedule.day_of_week == 2

    def test_roundtrip_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = WorkflowSchedule(
            name="Roundtrip Test",
            workflow_path="/path/to/workflow.json",
            frequency=ScheduleFrequency.MONTHLY,
            time_hour=8,
            time_minute=45,
            day_of_month=15,
            enabled=False,
        )
        data = original.to_dict()
        restored = WorkflowSchedule.from_dict(data)

        assert restored.name == original.name
        assert restored.workflow_path == original.workflow_path
        assert restored.frequency == original.frequency
        assert restored.time_hour == original.time_hour
        assert restored.day_of_month == original.day_of_month
        assert restored.enabled == original.enabled

    def test_success_rate_calculation(self):
        """Test success rate property calculation."""
        schedule = WorkflowSchedule(run_count=10, success_count=7)
        assert schedule.success_rate == 70.0

    def test_success_rate_zero_runs(self):
        """Test success rate with no runs."""
        schedule = WorkflowSchedule(run_count=0, success_count=0)
        assert schedule.success_rate == 0.0


class TestWorkflowScheduleNextRun:
    """Tests for next run calculation."""

    def test_daily_next_run_future(self):
        """Test daily schedule next run when time is in future today."""
        now = datetime(2025, 1, 15, 8, 0, 0)
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.DAILY,
            time_hour=10,
            time_minute=30,
        )
        next_run = schedule.calculate_next_run(from_time=now)
        assert next_run is not None
        assert next_run.hour == 10
        assert next_run.minute == 30
        assert next_run.day == 15

    def test_daily_next_run_past(self):
        """Test daily schedule next run when time has passed today."""
        now = datetime(2025, 1, 15, 12, 0, 0)
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.DAILY,
            time_hour=10,
            time_minute=30,
        )
        next_run = schedule.calculate_next_run(from_time=now)
        assert next_run is not None
        assert next_run.hour == 10
        assert next_run.minute == 30
        assert next_run.day == 16

    def test_hourly_next_run(self):
        """Test hourly schedule next run."""
        now = datetime(2025, 1, 15, 10, 20, 0)
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.HOURLY,
            time_minute=30,
        )
        next_run = schedule.calculate_next_run(from_time=now)
        assert next_run is not None
        assert next_run.minute == 30
        assert next_run.hour == 10

    def test_weekly_next_run_same_week(self):
        """Test weekly schedule when target day is later this week."""
        # Wednesday at 10 AM
        now = datetime(2025, 1, 15, 10, 0, 0)
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.WEEKLY,
            time_hour=9,
            time_minute=0,
            day_of_week=4,  # Friday
        )
        next_run = schedule.calculate_next_run(from_time=now)
        assert next_run is not None
        assert next_run.weekday() == 4  # Friday

    def test_once_schedule_future(self):
        """Test one-time schedule with future datetime."""
        now = datetime(2025, 1, 15, 10, 0, 0)
        future = datetime(2025, 1, 20, 15, 0, 0)
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.ONCE,
            next_run=future,
        )
        next_run = schedule.calculate_next_run(from_time=now)
        assert next_run == future

    def test_once_schedule_past(self):
        """Test one-time schedule with past datetime returns None."""
        now = datetime(2025, 1, 15, 10, 0, 0)
        past = datetime(2025, 1, 10, 15, 0, 0)
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.ONCE,
            next_run=past,
        )
        next_run = schedule.calculate_next_run(from_time=now)
        assert next_run is None

    def test_cron_returns_none(self):
        """Test cron schedule returns None (handled by scheduler)."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.CRON,
            cron_expression="0 9 * * MON-FRI",
        )
        next_run = schedule.calculate_next_run()
        assert next_run is None


class TestWorkflowScheduleFrequencyDisplay:
    """Tests for frequency display strings."""

    def test_once_display(self):
        """Test once frequency display."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.ONCE,
            next_run=datetime(2025, 3, 15, 14, 30),
        )
        assert "Once at" in schedule.frequency_display
        assert "2025-03-15" in schedule.frequency_display

    def test_hourly_display(self):
        """Test hourly frequency display."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.HOURLY,
            time_minute=15,
        )
        assert "Hourly at :15" in schedule.frequency_display

    def test_daily_display(self):
        """Test daily frequency display."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.DAILY,
            time_hour=9,
            time_minute=30,
        )
        assert "Daily at 09:30" in schedule.frequency_display

    def test_weekly_display(self):
        """Test weekly frequency display."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.WEEKLY,
            time_hour=10,
            time_minute=0,
            day_of_week=0,  # Monday
        )
        assert "Weekly on Mon" in schedule.frequency_display

    def test_monthly_display(self):
        """Test monthly frequency display."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.MONTHLY,
            time_hour=8,
            time_minute=0,
            day_of_month=15,
        )
        assert "Monthly on day 15" in schedule.frequency_display

    def test_cron_display(self):
        """Test cron frequency display."""
        schedule = WorkflowSchedule(
            frequency=ScheduleFrequency.CRON,
            cron_expression="0 9 * * MON-FRI",
        )
        assert "Cron: 0 9 * * MON-FRI" in schedule.frequency_display


class TestScheduleDialogCreation:
    """Tests for ScheduleDialog creation and UI."""

    def test_dialog_created(self, schedule_dialog):
        """Test schedule dialog is created successfully."""
        assert schedule_dialog is not None

    def test_dialog_title_for_new_schedule(self, schedule_dialog):
        """Test dialog title for new schedule."""
        assert schedule_dialog.windowTitle() == "Schedule Workflow"

    def test_dialog_has_name_input(self, schedule_dialog):
        """Test dialog has name input field."""
        assert schedule_dialog._name_input is not None
        assert "Test Workflow" in schedule_dialog._name_input.text()

    def test_dialog_has_frequency_combo(self, schedule_dialog):
        """Test dialog has frequency combo box."""
        assert schedule_dialog._frequency_combo is not None
        assert schedule_dialog._frequency_combo.count() == 6

    def test_dialog_has_time_edit(self, schedule_dialog):
        """Test dialog has time edit widget."""
        assert schedule_dialog._time_edit is not None

    def test_dialog_has_enabled_checkbox(self, schedule_dialog):
        """Test dialog has enabled checkbox."""
        assert schedule_dialog._enabled_check is not None
        assert schedule_dialog._enabled_check.isChecked() is True


class TestScheduleDialogFrequencyChange:
    """Tests for frequency change behavior."""

    def test_daily_shows_time(self, schedule_dialog):
        """Test daily frequency shows time field (not hidden)."""
        schedule_dialog._frequency_combo.setCurrentText("Daily")
        # Use isHidden() since widget visibility depends on parent being shown
        assert not schedule_dialog._time_edit.isHidden()

    def test_weekly_shows_day_combo(self, schedule_dialog):
        """Test weekly frequency shows day of week combo (not hidden)."""
        schedule_dialog._frequency_combo.setCurrentText("Weekly")
        assert not schedule_dialog._day_combo.isHidden()

    def test_monthly_shows_day_spin(self, schedule_dialog):
        """Test monthly frequency shows day of month spin (not hidden)."""
        schedule_dialog._frequency_combo.setCurrentText("Monthly")
        assert not schedule_dialog._day_spin.isHidden()

    def test_cron_shows_cron_input(self, schedule_dialog):
        """Test cron frequency shows cron expression input (not hidden)."""
        schedule_dialog._frequency_combo.setCurrentText("Cron")
        assert not schedule_dialog._cron_input.isHidden()

    def test_once_shows_datetime(self, schedule_dialog):
        """Test once frequency shows datetime picker (not hidden)."""
        schedule_dialog._frequency_combo.setCurrentText("Once")
        # Directly call the handler to ensure state is updated
        schedule_dialog._on_frequency_changed("Once")
        assert not schedule_dialog._datetime_edit.isHidden()


class TestScheduleDialogBuildSchedule:
    """Tests for building schedule from dialog."""

    def test_build_daily_schedule(self, schedule_dialog):
        """Test building a daily schedule."""
        schedule_dialog._name_input.setText("Test Daily")
        schedule_dialog._frequency_combo.setCurrentText("Daily")
        schedule_dialog._time_edit.setTime(QTime(10, 30))

        schedule = schedule_dialog._build_schedule()
        assert schedule is not None
        assert schedule.name == "Test Daily"
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.time_hour == 10
        assert schedule.time_minute == 30

    def test_build_weekly_schedule(self, schedule_dialog):
        """Test building a weekly schedule."""
        schedule_dialog._name_input.setText("Test Weekly")
        schedule_dialog._frequency_combo.setCurrentText("Weekly")
        schedule_dialog._time_edit.setTime(QTime(14, 0))
        schedule_dialog._day_combo.setCurrentIndex(4)  # Friday

        schedule = schedule_dialog._build_schedule()
        assert schedule is not None
        assert schedule.frequency == ScheduleFrequency.WEEKLY
        assert schedule.day_of_week == 4

    def test_build_cron_schedule(self, schedule_dialog):
        """Test building a cron schedule."""
        schedule_dialog._name_input.setText("Test Cron")
        schedule_dialog._frequency_combo.setCurrentText("Cron")
        schedule_dialog._cron_input.setText("0 9 * * MON-FRI")

        schedule = schedule_dialog._build_schedule()
        assert schedule is not None
        assert schedule.frequency == ScheduleFrequency.CRON
        assert schedule.cron_expression == "0 9 * * MON-FRI"


class TestScheduleManagerDialogCreation:
    """Tests for ScheduleManagerDialog creation."""

    def test_manager_created(self, schedule_manager_dialog):
        """Test manager dialog is created successfully."""
        assert schedule_manager_dialog is not None

    def test_manager_title(self, schedule_manager_dialog):
        """Test manager dialog title."""
        assert schedule_manager_dialog.windowTitle() == "Schedule Manager"

    def test_manager_has_table(self, schedule_manager_dialog):
        """Test manager dialog has table widget."""
        assert schedule_manager_dialog._table is not None
        assert schedule_manager_dialog._table.columnCount() == 8

    def test_manager_empty_table(self, schedule_manager_dialog):
        """Test manager dialog with no schedules has empty table."""
        assert schedule_manager_dialog._table.rowCount() == 0

    def test_manager_summary_label(self, schedule_manager_dialog):
        """Test manager dialog has summary label."""
        assert schedule_manager_dialog._summary_label is not None


class TestScheduleManagerWithSchedules:
    """Tests for ScheduleManagerDialog with schedules."""

    def test_manager_shows_schedules(self, qapp, qtbot):
        """Test manager shows schedules in table."""
        schedules = [
            WorkflowSchedule(
                name="Schedule 1",
                workflow_name="Workflow 1",
                frequency=ScheduleFrequency.DAILY,
            ),
            WorkflowSchedule(
                name="Schedule 2",
                workflow_name="Workflow 2",
                frequency=ScheduleFrequency.WEEKLY,
            ),
        ]
        dialog = ScheduleManagerDialog(schedules=schedules)
        qtbot.addWidget(dialog)

        assert dialog._table.rowCount() == 2

        dialog.close()

    def test_manager_get_schedules(self, qapp, qtbot):
        """Test getting schedules from manager."""
        schedules = [
            WorkflowSchedule(name="Test", workflow_name="Test WF"),
        ]
        dialog = ScheduleManagerDialog(schedules=schedules)
        qtbot.addWidget(dialog)

        result = dialog.get_schedules()
        assert len(result) == 1
        assert result[0].name == "Test"

        dialog.close()

    def test_manager_summary_count(self, qapp, qtbot):
        """Test manager summary shows correct count."""
        schedules = [
            WorkflowSchedule(name="S1", workflow_name="W1", enabled=True),
            WorkflowSchedule(name="S2", workflow_name="W2", enabled=True),
            WorkflowSchedule(name="S3", workflow_name="W3", enabled=False),
        ]
        dialog = ScheduleManagerDialog(schedules=schedules)
        qtbot.addWidget(dialog)

        summary = dialog._summary_label.text()
        assert "3 schedules" in summary
        assert "2 enabled" in summary

        dialog.close()


class TestScheduleManagerActions:
    """Tests for ScheduleManagerDialog actions."""

    def test_toggle_enabled(self, qapp, qtbot):
        """Test toggling schedule enabled state."""
        schedule = WorkflowSchedule(name="Test", workflow_name="Test WF", enabled=True)
        dialog = ScheduleManagerDialog(schedules=[schedule])
        qtbot.addWidget(dialog)

        dialog._on_toggle_enabled(schedule, False)
        assert schedule.enabled is False

        dialog.close()

    def test_delete_schedule_signal(self, qapp, qtbot):
        """Test schedule_changed signal emitted on delete."""
        schedule = WorkflowSchedule(name="Test", workflow_name="Test WF")
        dialog = ScheduleManagerDialog(schedules=[schedule])
        qtbot.addWidget(dialog)

        # Mock the confirmation dialog
        from unittest.mock import patch
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with qtbot.waitSignal(dialog.schedule_changed, timeout=1000):
                dialog._on_delete(schedule)

        assert len(dialog.get_schedules()) == 0

        dialog.close()

    def test_run_schedule_signal(self, qapp, qtbot):
        """Test run_schedule signal emitted."""
        schedule = WorkflowSchedule(name="Test", workflow_name="Test WF")
        dialog = ScheduleManagerDialog(schedules=[schedule])
        qtbot.addWidget(dialog)

        with qtbot.waitSignal(dialog.run_schedule, timeout=1000) as blocker:
            dialog._on_run_now(schedule)

        assert blocker.args[0] == schedule

        dialog.close()
