"""
Schedule Storage for CasareRPA Canvas.
Handles persistence of workflow schedules to JSON files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from loguru import logger

from casare_rpa.presentation.canvas.ui.dialogs.schedule_dialog import WorkflowSchedule


class ScheduleStorage:
    """
    Handles storage and retrieval of workflow schedules.
    Stores schedules in a JSON file in the user's config directory.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize schedule storage.

        Args:
            storage_path: Path to schedules JSON file. If None, uses default location.
        """
        if storage_path:
            self._storage_path = storage_path
        else:
            # Default to user's home directory
            config_dir = Path.home() / ".casare_rpa" / "canvas"
            config_dir.mkdir(parents=True, exist_ok=True)
            self._storage_path = config_dir / "schedules.json"

        # Create file if it doesn't exist
        if not self._storage_path.exists():
            self._storage_path.write_text("[]")

        logger.debug(f"Schedule storage initialized at: {self._storage_path}")

    def _load_raw(self) -> List[Dict[str, Any]]:
        """Load raw JSON data from storage file."""
        try:
            content = self._storage_path.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load schedules: {e}")
            return []

    def _save_raw(self, data: List[Dict[str, Any]]) -> bool:
        """Save raw JSON data to storage file."""
        try:
            content = json.dumps(data, indent=2, default=str)
            self._storage_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")
            return False

    def get_all_schedules(self) -> List[WorkflowSchedule]:
        """
        Get all saved schedules.

        Returns:
            List of WorkflowSchedule objects
        """
        raw_data = self._load_raw()
        schedules = []

        for item in raw_data:
            try:
                schedule = WorkflowSchedule.from_dict(item)
                schedules.append(schedule)
            except Exception as e:
                logger.warning(f"Failed to parse schedule: {e}")

        return schedules

    def get_schedule(self, schedule_id: str) -> Optional[WorkflowSchedule]:
        """
        Get a specific schedule by ID.

        Args:
            schedule_id: Schedule ID to find

        Returns:
            WorkflowSchedule or None if not found
        """
        schedules = self.get_all_schedules()
        for schedule in schedules:
            if schedule.id == schedule_id:
                return schedule
        return None

    def save_schedule(self, schedule: WorkflowSchedule) -> bool:
        """
        Save or update a schedule.

        Args:
            schedule: Schedule to save

        Returns:
            True if saved successfully
        """
        raw_data = self._load_raw()

        # Update existing or add new
        updated = False
        for i, item in enumerate(raw_data):
            if item.get("id") == schedule.id:
                raw_data[i] = schedule.to_dict()
                updated = True
                break

        if not updated:
            raw_data.append(schedule.to_dict())

        success = self._save_raw(raw_data)
        if success:
            logger.info(f"Schedule saved: {schedule.name} ({schedule.id})")
        return success

    def save_all_schedules(self, schedules: List[WorkflowSchedule]) -> bool:
        """
        Save all schedules (replaces existing).

        Args:
            schedules: List of schedules to save

        Returns:
            True if saved successfully
        """
        raw_data = [s.to_dict() for s in schedules]
        success = self._save_raw(raw_data)
        if success:
            logger.info(f"Saved {len(schedules)} schedules")
        return success

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule by ID.

        Args:
            schedule_id: Schedule ID to delete

        Returns:
            True if deleted successfully
        """
        raw_data = self._load_raw()
        original_count = len(raw_data)

        raw_data = [item for item in raw_data if item.get("id") != schedule_id]

        if len(raw_data) < original_count:
            success = self._save_raw(raw_data)
            if success:
                logger.info(f"Schedule deleted: {schedule_id}")
            return success

        return False  # Not found

    def get_enabled_schedules(self) -> List[WorkflowSchedule]:
        """
        Get all enabled schedules.

        Returns:
            List of enabled WorkflowSchedule objects
        """
        return [s for s in self.get_all_schedules() if s.enabled]

    def get_due_schedules(self) -> List[WorkflowSchedule]:
        """
        Get schedules that are due to run.

        Returns:
            List of schedules where next_run <= now
        """
        now = datetime.now()
        due = []

        for schedule in self.get_enabled_schedules():
            if schedule.next_run and schedule.next_run <= now:
                due.append(schedule)

        return due

    def mark_schedule_run(
        self, schedule_id: str, success: bool, error_message: str = ""
    ) -> bool:
        """
        Mark a schedule as having run.

        Updates last_run, run_count, success/failure counts, and calculates next_run.

        Args:
            schedule_id: Schedule ID
            success: Whether the run was successful
            error_message: Error message if failed

        Returns:
            True if updated successfully
        """
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return False

        schedule.last_run = datetime.now()
        schedule.run_count += 1

        if success:
            schedule.success_count += 1
            schedule.last_error = ""
        else:
            schedule.failure_count += 1
            schedule.last_error = error_message

        # Calculate next run time
        schedule.next_run = schedule.calculate_next_run()

        return self.save_schedule(schedule)

    def get_schedules_for_workflow(self, workflow_path: str) -> List[WorkflowSchedule]:
        """
        Get all schedules for a specific workflow.

        Args:
            workflow_path: Path to the workflow file

        Returns:
            List of schedules for this workflow
        """
        return [s for s in self.get_all_schedules() if s.workflow_path == workflow_path]


# Singleton instance
_storage_instance: Optional[ScheduleStorage] = None


def get_schedule_storage() -> ScheduleStorage:
    """
    Get the global schedule storage instance.

    Returns:
        ScheduleStorage singleton instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ScheduleStorage()
    return _storage_instance


def set_schedule_storage(storage: ScheduleStorage) -> None:
    """
    Set the global schedule storage instance (for testing).

    Args:
        storage: ScheduleStorage instance to use
    """
    global _storage_instance
    _storage_instance = storage
