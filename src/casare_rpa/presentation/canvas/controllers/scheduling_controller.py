"""
Scheduling controller for workflow scheduling management.

Handles all scheduling-related operations:
- Schedule workflow dialogs
- Manage schedules dialog
- Run scheduled workflows
- Schedule state management
"""

from pathlib import Path
from typing import TYPE_CHECKING, List, Any
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QMessageBox
from loguru import logger

from .base_controller import BaseController

if TYPE_CHECKING:
    from ..main_window import MainWindow


class SchedulingController(BaseController):
    """
    Manages workflow scheduling operations.

    Single Responsibility: Schedule creation, management, and execution.

    Signals:
        schedule_created: Emitted when a schedule is created (WorkflowSchedule)
        schedule_deleted: Emitted when a schedule is deleted (str: schedule_id)
        schedule_updated: Emitted when a schedule is modified (WorkflowSchedule)
        schedule_run_requested: Emitted when user wants to run a schedule (WorkflowSchedule)
        schedules_changed: Emitted when schedules list is modified
    """

    # Signals
    schedule_created = Signal(object)  # WorkflowSchedule
    schedule_deleted = Signal(str)  # schedule_id
    schedule_updated = Signal(object)  # WorkflowSchedule
    schedule_run_requested = Signal(object)  # WorkflowSchedule
    schedules_changed = Signal()

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize scheduling controller.

        Args:
            main_window: Reference to main window for accessing shared components
        """
        super().__init__(main_window)
        self._active_schedules: List[Any] = []

    def initialize(self) -> None:
        """Initialize controller resources and connections."""
        super().initialize()
        self._load_schedules()
        logger.info("SchedulingController initialized")

    def cleanup(self) -> None:
        """Clean up controller resources."""
        super().cleanup()
        self._active_schedules.clear()
        logger.info("SchedulingController cleanup")

    def schedule_workflow(self) -> None:
        """
        Open dialog to schedule the current workflow.

        Checks if workflow is saved first, prompting user to save if needed.
        """
        try:
            from ..ui.dialogs.schedule_dialog import ScheduleDialog
            from ....application.scheduling import get_schedule_storage

            current_file = self.main_window.get_current_file()
            if not current_file:
                should_continue = self._prompt_save_workflow()
                if not should_continue:
                    return
                current_file = self.main_window.get_current_file()
                if not current_file:
                    return  # User cancelled save

            workflow_name = current_file.stem if current_file else "Untitled"

            dialog = ScheduleDialog(
                workflow_path=current_file,
                workflow_name=workflow_name,
                parent=self.main_window,
            )

            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_schedule:
                storage = get_schedule_storage()
                if storage.save_schedule(dialog.result_schedule):
                    self._on_schedule_saved(dialog.result_schedule)
                else:
                    self._show_schedule_error("Failed to save schedule")

        except ImportError as e:
            logger.error(f"Failed to import scheduling module: {e}")
            self._show_schedule_error(f"Scheduling module not available: {e}")
        except Exception as e:
            logger.error(f"Failed to schedule workflow: {e}")
            self._show_schedule_error(str(e))

    def manage_schedules(self) -> None:
        """Open dialog to view and manage all schedules."""
        try:
            from ..ui.dialogs.schedule_dialog import ScheduleManagerDialog
            from ....application.scheduling import get_schedule_storage

            storage = get_schedule_storage()
            schedules = storage.get_all_schedules()

            dialog = ScheduleManagerDialog(schedules, parent=self.main_window)
            dialog.schedule_changed.connect(lambda: self._save_all_schedules(dialog))
            dialog.run_schedule.connect(self.run_scheduled_workflow)

            dialog.exec()

        except ImportError as e:
            logger.error(f"Failed to import schedule manager: {e}")
            self._show_schedule_error(f"Schedule manager not available: {e}")
        except Exception as e:
            logger.error(f"Failed to open schedule manager: {e}")
            self._show_schedule_error(str(e))

    def run_scheduled_workflow(self, schedule) -> None:
        """
        Run a scheduled workflow immediately.

        Args:
            schedule: The WorkflowSchedule to run
        """
        workflow_path = Path(schedule.workflow_path)
        if not workflow_path.exists():
            QMessageBox.warning(
                self.main_window,
                "Workflow Not Found",
                f"The scheduled workflow could not be found:\n{workflow_path}",
            )
            logger.warning(f"Scheduled workflow not found: {workflow_path}")
            return

        reply = QMessageBox.question(
            self.main_window,
            "Run Scheduled Workflow",
            f"Open and run '{schedule.workflow_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._execute_scheduled_workflow(schedule, workflow_path)

    def get_schedules(self) -> List[Any]:
        """
        Get all active schedules.

        Returns:
            List of WorkflowSchedule objects
        """
        return self._active_schedules.copy()

    def get_schedule_count(self) -> int:
        """
        Get the number of active schedules.

        Returns:
            Number of schedules
        """
        return len(self._active_schedules)

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule by ID.

        Args:
            schedule_id: ID of the schedule to delete

        Returns:
            True if deletion was successful
        """
        try:
            from ....application.scheduling import get_schedule_storage

            storage = get_schedule_storage()
            if storage.delete_schedule(schedule_id):
                self._active_schedules = [
                    s for s in self._active_schedules if s.id != schedule_id
                ]
                self.schedule_deleted.emit(schedule_id)
                self.schedules_changed.emit()
                logger.info(f"Schedule deleted: {schedule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete schedule {schedule_id}: {e}")
            return False

    def _load_schedules(self) -> None:
        """Load schedules from storage."""
        try:
            from ....application.scheduling import get_schedule_storage

            storage = get_schedule_storage()
            self._active_schedules = storage.get_all_schedules()
            logger.debug(f"Loaded {len(self._active_schedules)} schedules")
        except ImportError:
            logger.debug("Schedule storage not available")
            self._active_schedules = []
        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")
            self._active_schedules = []

    def _prompt_save_workflow(self) -> bool:
        """
        Prompt user to save workflow before scheduling.

        Returns:
            True if user saved or workflow was already saved, False if cancelled
        """
        reply = QMessageBox.question(
            self.main_window,
            "Save Required",
            "The workflow must be saved before scheduling. Save now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Trigger save through workflow controller
            workflow_controller = getattr(
                self.main_window, "_workflow_controller", None
            )
            if workflow_controller:
                workflow_controller.save_workflow_as()
                return True
            else:
                # Fallback to direct signal emission
                self.main_window.workflow_save.emit()
                return True
        return False

    def _on_schedule_saved(self, schedule) -> None:
        """
        Handle successful schedule creation.

        Args:
            schedule: The created WorkflowSchedule
        """
        self._active_schedules.append(schedule)
        self.schedule_created.emit(schedule)
        self.schedules_changed.emit()

        self.main_window.show_status(f"Schedule created: {schedule.name}", 5000)
        logger.info(f"Workflow scheduled: {schedule.name}")

    def _save_all_schedules(self, dialog) -> None:
        """
        Save all schedules from manager dialog.

        Args:
            dialog: The ScheduleManagerDialog instance
        """
        try:
            from ....application.scheduling import get_schedule_storage

            storage = get_schedule_storage()
            schedules = dialog.get_schedules()
            storage.save_all_schedules(schedules)
            self._active_schedules = schedules
            self.schedules_changed.emit()

            self.main_window.show_status("Schedules updated", 3000)
            logger.info(f"Saved {len(schedules)} schedules")
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")
            self._show_schedule_error(f"Failed to save schedules: {e}")

    def _execute_scheduled_workflow(self, schedule, workflow_path: Path) -> None:
        """
        Execute a scheduled workflow.

        Args:
            schedule: The WorkflowSchedule to execute
            workflow_path: Path to the workflow file
        """
        workflow_controller = getattr(self.main_window, "_workflow_controller", None)

        if workflow_controller:
            # Check for unsaved changes
            if workflow_controller.check_unsaved_changes():
                # Open the workflow
                self.main_window.workflow_open.emit(str(workflow_path))
                self.main_window.set_current_file(workflow_path)
                self.main_window.set_modified(False)

                # Run the workflow
                execution_controller = getattr(
                    self.main_window, "_execution_controller", None
                )
                if execution_controller:
                    execution_controller.run_workflow()
                else:
                    self.main_window.workflow_run.emit()

                self.schedule_run_requested.emit(schedule)
                logger.info(f"Running scheduled workflow: {schedule.workflow_name}")
        else:
            # Fallback to direct signal emission
            self.main_window.workflow_open.emit(str(workflow_path))
            self.main_window.workflow_run.emit()

    def _show_schedule_error(self, error_message: str) -> None:
        """
        Display schedule error to user.

        Args:
            error_message: Error message to display
        """
        QMessageBox.warning(
            self.main_window,
            "Schedule Error",
            f"Scheduling operation failed:\n{error_message}",
        )
