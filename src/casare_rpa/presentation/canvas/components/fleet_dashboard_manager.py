"""
Fleet dashboard manager for MainWindow.

Centralizes fleet dashboard dialog interactions and orchestrator API calls.
"""

from collections import Counter
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from ..controllers.robot_controller import RobotController
    from ..controllers.scheduling_controller import SchedulingController
    from ..ui.dialogs.fleet_dashboard_dialog import FleetDashboardDialog


class FleetDashboardManager:
    """
    Manages fleet dashboard dialog and orchestrator interactions.

    Responsibilities:
    - Open and configure fleet dashboard dialog
    - Refresh fleet data from orchestrator/local
    - Handle robot CRUD operations
    - Handle job operations (cancel, retry)
    - Handle schedule operations (toggle, edit, delete, run now)
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize fleet dashboard manager.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window
        self._dialog: Optional["FleetDashboardDialog"] = None

    @property
    def dialog(self) -> Optional["FleetDashboardDialog"]:
        """Get current fleet dashboard dialog."""
        return self._dialog

    @property
    def _robot_controller(self) -> Optional["RobotController"]:
        return self._main_window._robot_controller

    @property
    def _scheduling_controller(self) -> Optional["SchedulingController"]:
        return self._main_window._scheduling_controller

    def open_dashboard(self) -> None:
        """Open the fleet management dashboard dialog."""
        from ..ui.dialogs import FleetDashboardDialog

        self._dialog = FleetDashboardDialog(self._main_window)
        self._dialog.refresh_requested.connect(self._on_refresh_requested)
        self._dialog.robot_edited.connect(self._on_robot_edited)
        self._dialog.robot_deleted.connect(self._on_robot_deleted)
        self._dialog.job_cancelled.connect(self._on_job_cancelled)
        self._dialog.job_retried.connect(self._on_job_retried)
        self._dialog.schedule_enabled_changed.connect(self._on_schedule_toggled)
        self._dialog.schedule_edited.connect(self._on_schedule_edited)
        self._dialog.schedule_deleted.connect(self._on_schedule_deleted)
        self._dialog.schedule_run_now.connect(self._on_schedule_run_now)

        self._check_connection_and_refresh()
        self._dialog.show()
        logger.info("Fleet Dashboard opened")

    def _check_connection_and_refresh(self) -> None:
        """Check orchestrator connection status and trigger initial refresh."""
        import asyncio

        async def connect_and_refresh():
            if self._robot_controller:
                try:
                    connected = await self._robot_controller.connect_to_orchestrator()
                    if connected:
                        url = self._robot_controller.orchestrator_url or "Orchestrator"
                        self._dialog.set_connection_status(True, f"Connected to {url}")
                        self._dialog.set_status("Refreshing data...")
                        await self._refresh_all_data()
                        return
                except Exception as e:
                    logger.warning(f"Failed to connect to orchestrator: {e}")

            self._dialog.set_connection_status(False, "Local Mode")
            self._dialog.set_status("Using local storage (orchestrator not available)")
            await self._refresh_all_data()

        asyncio.create_task(connect_and_refresh())

    async def _refresh_all_data(self) -> None:
        """Refresh all fleet dashboard data from orchestrator/local services."""
        from PySide6.QtWidgets import QMessageBox

        if not self._dialog:
            return

        try:
            robots = await self._get_robots()
            if self._dialog:
                self._dialog.update_robots(robots)
                self._dialog.update_api_keys_robots(
                    [{"id": r.id, "name": r.name} for r in robots]
                )

            jobs = await self._get_jobs()
            if self._dialog:
                self._dialog.update_jobs(jobs)

            schedules = await self._get_schedules()
            if self._dialog:
                self._dialog.update_schedules(schedules)

            analytics = await self._get_analytics(robots, jobs)
            if self._dialog:
                self._dialog.update_analytics(analytics)
                self._dialog.set_status("Data refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh fleet data: {e}")
            if self._dialog:
                self._dialog.set_status(f"Refresh failed: {e}")
            QMessageBox.warning(
                self._main_window,
                "Refresh Failed",
                f"Failed to refresh fleet data:\n{e}",
            )

    async def _get_robots(self) -> List[Any]:
        """Get robots from robot controller or local repository."""
        if self._robot_controller:
            await self._robot_controller.refresh_robots()
            return self._robot_controller.robots
        return []

    async def _get_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs from orchestrator API or local storage."""
        try:
            if self._robot_controller and self._robot_controller.is_connected:
                client = self._robot_controller._orchestrator_client
                if client:
                    job_data_list = await client.get_jobs(limit=100)
                    return [
                        {
                            "id": j.id,
                            "workflow_name": j.workflow_name,
                            "robot_name": j.robot_name,
                            "status": j.status,
                            "progress": j.progress,
                            "created_at": str(j.created_at) if j.created_at else "",
                            "started_at": str(j.started_at) if j.started_at else "",
                            "completed_at": str(j.completed_at)
                            if j.completed_at
                            else "",
                        }
                        for j in job_data_list
                    ]

            from casare_rpa.infrastructure.orchestrator.persistence import (
                LocalJobRepository,
                LocalStorageRepository,
            )

            storage = LocalStorageRepository()
            repo = LocalJobRepository(storage)
            jobs = await repo.get_all()
            return [
                {
                    "id": j.id,
                    "workflow_name": getattr(j, "workflow_name", ""),
                    "robot_name": getattr(j, "robot_name", ""),
                    "status": j.status.value
                    if hasattr(j.status, "value")
                    else j.status,
                    "progress": getattr(j, "progress", 0),
                    "created_at": str(getattr(j, "created_at", "")),
                    "started_at": str(getattr(j, "started_at", "")),
                    "completed_at": str(getattr(j, "completed_at", "")),
                }
                for j in jobs
            ]
        except Exception as e:
            logger.warning(f"Failed to get jobs: {e}")
            return []

    async def _get_schedules(self) -> List[Dict[str, Any]]:
        """Get schedules from scheduling controller or storage."""
        if self._scheduling_controller:
            schedules = self._scheduling_controller.get_schedules()
            return [
                {
                    "id": getattr(s, "id", str(i)),
                    "name": getattr(s, "name", ""),
                    "workflow_name": getattr(s, "workflow_name", ""),
                    "cron_expression": getattr(s, "cron_expression", ""),
                    "enabled": getattr(s, "enabled", True),
                    "next_run": str(getattr(s, "next_run", "")),
                    "last_run": str(getattr(s, "last_run", "")),
                }
                for i, s in enumerate(schedules)
            ]
        return []

    async def _get_analytics(
        self, robots: List[Any], jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get analytics from orchestrator API or generate locally."""
        if self._robot_controller and self._robot_controller.is_connected:
            client = self._robot_controller._orchestrator_client
            if client:
                try:
                    analytics = await client.get_analytics(days=7)
                    fleet_metrics = await client.get_fleet_metrics()

                    return {
                        "total_robots": fleet_metrics.get("total_robots", len(robots)),
                        "robots_by_status": {
                            "online": fleet_metrics.get("active_robots", 0),
                            "busy": fleet_metrics.get("busy_robots", 0),
                            "offline": fleet_metrics.get("offline_robots", 0),
                        },
                        "total_jobs": len(jobs),
                        "jobs_by_status": analytics.get("job_status_distribution", {}),
                        "jobs_completed_today": analytics.get("jobs_completed", 0),
                        "jobs_failed_today": analytics.get("jobs_failed", 0),
                        "success_rate": analytics.get("success_rate", 0),
                        "avg_duration_ms": analytics.get("avg_duration_ms", 0),
                        "queue_depth": fleet_metrics.get("queue_depth", 0),
                    }
                except Exception as e:
                    logger.warning(f"Failed to get analytics from API: {e}")

        robot_statuses = Counter(
            r.status.value if hasattr(r.status, "value") else str(r.status)
            for r in robots
        )
        job_statuses = Counter(j.get("status", "unknown") for j in jobs)

        return {
            "total_robots": len(robots),
            "robots_by_status": dict(robot_statuses),
            "total_jobs": len(jobs),
            "jobs_by_status": dict(job_statuses),
            "jobs_completed_today": sum(
                1 for j in jobs if j.get("status") == "completed"
            ),
            "jobs_failed_today": sum(1 for j in jobs if j.get("status") == "failed"),
        }

    def _on_refresh_requested(self) -> None:
        """Handle fleet dashboard refresh request."""
        import asyncio

        logger.debug("Fleet dashboard refresh requested")
        asyncio.create_task(self._refresh_all_data())

    def _on_robot_edited(self, robot_id: str, robot_data: dict) -> None:
        """Handle robot edit from fleet dashboard."""
        import asyncio

        logger.info(f"Robot edited: {robot_id}")
        asyncio.create_task(self._update_robot(robot_id, robot_data))

    async def _update_robot(self, robot_id: str, robot_data: dict) -> None:
        """Update robot via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url:
                    base_url = config.orchestrator.url.replace(
                        "ws://", "http://"
                    ).replace("wss://", "https://")
                    base_url = base_url.rstrip("/ws").rstrip("/")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.patch(
                            f"{base_url}/robots/{robot_id}",
                            json=robot_data,
                            headers={
                                "Authorization": f"Bearer {config.orchestrator.api_key}"
                            },
                        )
                        response.raise_for_status()

                    logger.info(f"Robot {robot_id} updated via API")
                    self._main_window.show_status("Robot updated successfully", 3000)
                    await self._refresh_all_data()
                    return

            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Robot editing requires orchestrator connection",
            )
        except Exception as e:
            logger.error(f"Failed to update robot: {e}")
            QMessageBox.warning(
                self._main_window, "Update Failed", f"Failed to update robot:\n{e}"
            )

    def _on_robot_deleted(self, robot_id: str) -> None:
        """Handle robot deletion from fleet dashboard."""
        import asyncio

        logger.info(f"Robot deleted: {robot_id}")
        asyncio.create_task(self._delete_robot(robot_id))

    async def _delete_robot(self, robot_id: str) -> None:
        """Delete robot via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url:
                    base_url = config.orchestrator.url.replace(
                        "ws://", "http://"
                    ).replace("wss://", "https://")
                    base_url = base_url.rstrip("/ws").rstrip("/")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.delete(
                            f"{base_url}/robots/{robot_id}",
                            headers={
                                "Authorization": f"Bearer {config.orchestrator.api_key}"
                            },
                        )
                        response.raise_for_status()

                    logger.info(f"Robot {robot_id} deleted via API")
                    self._main_window.show_status("Robot deleted successfully", 3000)
                    await self._refresh_all_data()
                    return

            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Robot deletion requires orchestrator connection",
            )
        except Exception as e:
            logger.error(f"Failed to delete robot: {e}")
            QMessageBox.warning(
                self._main_window, "Delete Failed", f"Failed to delete robot:\n{e}"
            )

    def _on_job_cancelled(self, job_id: str) -> None:
        """Handle job cancellation from fleet dashboard."""
        import asyncio

        logger.info(f"Job cancelled: {job_id}")
        asyncio.create_task(self._cancel_job(job_id))

    async def _cancel_job(self, job_id: str) -> None:
        """Cancel job via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url:
                    base_url = config.orchestrator.url.replace(
                        "ws://", "http://"
                    ).replace("wss://", "https://")
                    base_url = base_url.rstrip("/ws").rstrip("/")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{base_url}/jobs/{job_id}/cancel",
                            json={"reason": "Cancelled by user"},
                            headers={
                                "Authorization": f"Bearer {config.orchestrator.api_key}"
                            },
                        )
                        response.raise_for_status()

                    logger.info(f"Job {job_id} cancelled via API")
                    self._main_window.show_status("Job cancelled successfully", 3000)
                    await self._refresh_all_data()
                    return

            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Job cancellation requires orchestrator connection",
            )
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            QMessageBox.warning(
                self._main_window, "Cancel Failed", f"Failed to cancel job:\n{e}"
            )

    def _on_job_retried(self, job_id: str) -> None:
        """Handle job retry from fleet dashboard."""
        import asyncio

        logger.info(f"Job retried: {job_id}")
        asyncio.create_task(self._retry_job(job_id))

    async def _retry_job(self, job_id: str) -> None:
        """Retry failed job via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url:
                    base_url = config.orchestrator.url.replace(
                        "ws://", "http://"
                    ).replace("wss://", "https://")
                    base_url = base_url.rstrip("/ws").rstrip("/")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{base_url}/jobs/{job_id}/retry",
                            headers={
                                "Authorization": f"Bearer {config.orchestrator.api_key}"
                            },
                        )
                        response.raise_for_status()
                        result = response.json()

                    new_job_id = result.get("job_id", "unknown")
                    logger.info(f"Job {job_id} retried as new job {new_job_id}")
                    self._main_window.show_status(
                        f"Job queued for retry: {new_job_id}", 3000
                    )
                    await self._refresh_all_data()
                    return

            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Job retry requires orchestrator connection",
            )
        except Exception as e:
            logger.error(f"Failed to retry job: {e}")
            QMessageBox.warning(
                self._main_window, "Retry Failed", f"Failed to retry job:\n{e}"
            )

    def _on_schedule_toggled(self, schedule_id: str, enabled: bool) -> None:
        """Handle schedule enable/disable from fleet dashboard."""
        import asyncio

        logger.info(f"Schedule {schedule_id} enabled={enabled}")
        asyncio.create_task(self._toggle_schedule(schedule_id, enabled))

    async def _toggle_schedule(self, schedule_id: str, enabled: bool) -> None:
        """Toggle schedule enabled state via orchestrator API."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if not config_manager.config_exists():
                raise ValueError("No orchestrator configuration found")

            config = config_manager.load()
            if not config.orchestrator.url:
                raise ValueError("No orchestrator URL configured")

            base_url = config.orchestrator.url.replace("ws://", "http://").replace(
                "wss://", "https://"
            )
            base_url = base_url.rstrip("/ws").rstrip("/")

            endpoint = "enable" if enabled else "disable"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{base_url}/schedules/{schedule_id}/{endpoint}",
                    headers={"Authorization": f"Bearer {config.orchestrator.api_key}"},
                )
                response.raise_for_status()

            action = "enabled" if enabled else "disabled"
            logger.info(f"Schedule {schedule_id} {action}")
            self._main_window.show_status(f"Schedule {action} successfully", 3000)
            await self._refresh_all_data()

        except ImportError:
            if self._scheduling_controller:
                schedules = self._scheduling_controller.get_schedules()
                for schedule in schedules:
                    if getattr(schedule, "id", None) == schedule_id:
                        schedule.enabled = enabled
                        self._main_window.show_status(
                            f"Schedule {'enabled' if enabled else 'disabled'}", 3000
                        )
                        await self._refresh_all_data()
                        return
            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Schedule toggle requires orchestrator connection",
            )
        except Exception as e:
            logger.error(f"Failed to toggle schedule: {e}")
            QMessageBox.warning(
                self._main_window,
                "Toggle Failed",
                f"Failed to toggle schedule:\n{e}",
            )

    def _on_schedule_edited(self, schedule_id: str) -> None:
        """Handle schedule edit from fleet dashboard."""
        from PySide6.QtWidgets import QMessageBox

        logger.info(f"Schedule edit requested: {schedule_id}")

        if self._scheduling_controller:
            schedules = self._scheduling_controller.get_schedules()
            for schedule in schedules:
                if getattr(schedule, "id", None) == schedule_id:
                    self._scheduling_controller.manage_schedules()
                    return

        QMessageBox.information(
            self._main_window,
            "Edit Schedule",
            f"Opening schedule editor for: {schedule_id}\n\n"
            "Use the Schedule Manager to edit this schedule.",
        )
        if self._scheduling_controller:
            self._scheduling_controller.manage_schedules()

    def _on_schedule_deleted(self, schedule_id: str) -> None:
        """Handle schedule deletion from fleet dashboard."""
        import asyncio

        logger.info(f"Schedule deleted: {schedule_id}")
        asyncio.create_task(self._delete_schedule(schedule_id))

    async def _delete_schedule(self, schedule_id: str) -> None:
        """Delete schedule via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if not config_manager.config_exists():
                raise ValueError("No orchestrator configuration found")

            config = config_manager.load()
            if not config.orchestrator.url:
                raise ValueError("No orchestrator URL configured")

            base_url = config.orchestrator.url.replace("ws://", "http://").replace(
                "wss://", "https://"
            )
            base_url = base_url.rstrip("/ws").rstrip("/")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{base_url}/schedules/{schedule_id}",
                    headers={"Authorization": f"Bearer {config.orchestrator.api_key}"},
                )
                response.raise_for_status()

            logger.info(f"Schedule {schedule_id} deleted")
            self._main_window.show_status("Schedule deleted successfully", 3000)
            await self._refresh_all_data()

        except ImportError:
            if self._scheduling_controller:
                success = self._scheduling_controller.delete_schedule(schedule_id)
                if success:
                    self._main_window.show_status("Schedule deleted successfully", 3000)
                    await self._refresh_all_data()
                else:
                    QMessageBox.warning(
                        self._main_window, "Delete Failed", "Failed to delete schedule"
                    )
            else:
                QMessageBox.information(
                    self._main_window,
                    "Local Mode",
                    "Schedule deletion requires orchestrator connection",
                )
        except Exception as e:
            logger.error(f"Failed to delete schedule: {e}")
            QMessageBox.warning(
                self._main_window,
                "Delete Failed",
                f"Failed to delete schedule:\n{e}",
            )

    def _on_schedule_run_now(self, schedule_id: str) -> None:
        """Handle schedule run now from fleet dashboard."""
        import asyncio

        logger.info(f"Schedule run now: {schedule_id}")
        asyncio.create_task(self._run_schedule_now(schedule_id))

    async def _run_schedule_now(self, schedule_id: str) -> None:
        """Trigger immediate schedule execution via orchestrator API."""
        from PySide6.QtWidgets import QMessageBox

        try:
            import httpx

            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if not config_manager.config_exists():
                raise ValueError("No orchestrator configuration found")

            config = config_manager.load()
            if not config.orchestrator.url:
                raise ValueError("No orchestrator URL configured")

            base_url = config.orchestrator.url.replace("ws://", "http://").replace(
                "wss://", "https://"
            )
            base_url = base_url.rstrip("/ws").rstrip("/")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{base_url}/schedules/{schedule_id}/trigger",
                    headers={"Authorization": f"Bearer {config.orchestrator.api_key}"},
                )
                response.raise_for_status()
                result = response.json()

            job_id = result.get("job_id", "unknown")
            logger.info(f"Schedule {schedule_id} triggered, job_id={job_id}")
            self._main_window.show_status(
                f"Schedule triggered, job queued: {job_id}", 3000
            )
            await self._refresh_all_data()

        except ImportError:
            if self._scheduling_controller:
                schedules = self._scheduling_controller.get_schedules()
                for schedule in schedules:
                    if getattr(schedule, "id", None) == schedule_id:
                        self._scheduling_controller.run_scheduled_workflow(schedule)
                        return
            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Schedule execution requires orchestrator connection",
            )
        except Exception as e:
            logger.error(f"Failed to trigger schedule: {e}")
            QMessageBox.warning(
                self._main_window,
                "Trigger Failed",
                f"Failed to trigger schedule:\n{e}",
            )
