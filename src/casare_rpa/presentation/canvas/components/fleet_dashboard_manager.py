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
    from ..ui.dialogs.fleet_dashboard import FleetDashboardDialog


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

    @staticmethod
    def _normalize_orchestrator_base_url(url: str) -> str:
        base_url = url.replace("ws://", "http://").replace("wss://", "https://")
        base_url = base_url.rstrip("/")
        if base_url.endswith("/ws"):
            base_url = base_url[: -len("/ws")]
        return base_url.rstrip("/")

    @property
    def dialog(self) -> Optional["FleetDashboardDialog"]:
        """Get current fleet dashboard dialog."""
        return self._dialog

    @property
    def _robot_controller(self) -> Optional["RobotController"]:
        return self._main_window._robot_controller

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

        self._dialog.api_key_generated.connect(self._on_api_key_generated)
        self._dialog.api_key_revoked.connect(self._on_api_key_revoked)
        self._dialog.api_key_rotated.connect(self._on_api_key_rotated)

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

            api_keys = await self._get_robot_api_keys()
            if self._dialog:
                self._dialog.update_api_keys(api_keys)

            analytics = await self._get_analytics(robots, jobs)
            if self._dialog:
                self._dialog.update_analytics(analytics)
                self._dialog.set_status("Data refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh fleet data: {e}")
            if self._dialog:
                self._dialog.set_status(f"Refresh failed: {e}")
                if hasattr(self._dialog, "show_toast"):
                    self._dialog.show_toast(f"Refresh failed: {e}", level="error")

    async def _get_robot_api_keys(self) -> List[Dict[str, Any]]:
        """Get robot API keys from orchestrator API."""
        if not (self._robot_controller and self._robot_controller.is_connected):
            return []

        client = self._robot_controller._orchestrator_client
        if not client:
            return []

        try:
            keys = await client.list_robot_api_keys(limit=200)
            result: List[Dict[str, Any]] = []
            for k in keys:
                result.append(
                    {
                        "id": k.id,
                        "name": k.name,
                        "robot_id": k.robot_id,
                        "robot_name": k.robot_name,
                        "status": k.status,
                        "created_at": str(k.created_at) if k.created_at else "",
                        "expires_at": str(k.expires_at) if k.expires_at else "",
                        "last_used_at": str(k.last_used_at) if k.last_used_at else "",
                        "last_used_ip": k.last_used_ip or "",
                        "usage_count": "",  # Not tracked yet
                    }
                )
            return result
        except Exception as e:
            logger.warning(f"Failed to load robot API keys: {e}")
            return []

    def _on_api_key_generated(self, config: dict) -> None:
        import asyncio

        asyncio.create_task(self._generate_api_key(config))

    async def _generate_api_key(self, config: dict) -> None:
        from PySide6.QtWidgets import QApplication, QMessageBox

        if not (self._robot_controller and self._robot_controller.is_connected):
            QMessageBox.information(
                self._main_window,
                "Orchestrator Required",
                "API key management requires orchestrator connection.",
            )
            return

        client = self._robot_controller._orchestrator_client
        if not client:
            QMessageBox.warning(
                self._main_window, "Error", "Orchestrator client not available"
            )
            return

        try:
            resp = await client.create_robot_api_key(
                robot_id=str(config.get("robot_id")),
                name=str(config.get("name")),
                description=str(config.get("description") or ""),
                expires_at=config.get("expires_at"),
            )
            if not resp or "api_key" not in resp:
                raise RuntimeError("API key generation failed")

            raw_key = resp["api_key"]
            QApplication.clipboard().setText(raw_key)
            QMessageBox.information(
                self._main_window,
                "API Key Generated",
                "API key copied to clipboard. Save it now; it will not be shown again.\n\n"
                f"{raw_key}",
            )
            await self._refresh_all_data()
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            QMessageBox.warning(self._main_window, "Generation Failed", str(e))

    def _on_api_key_revoked(self, key_id: str) -> None:
        import asyncio

        asyncio.create_task(self._revoke_api_key(key_id))

    async def _revoke_api_key(self, key_id: str) -> None:
        from PySide6.QtWidgets import QMessageBox

        if not (self._robot_controller and self._robot_controller.is_connected):
            QMessageBox.information(
                self._main_window,
                "Orchestrator Required",
                "API key revocation requires orchestrator connection.",
            )
            return

        client = self._robot_controller._orchestrator_client
        if not client:
            return

        ok = await client.revoke_robot_api_key(key_id)
        if ok:
            self._main_window.show_status("API key revoked", 3000)
            await self._refresh_all_data()
            return

        QMessageBox.warning(
            self._main_window, "Revoke Failed", "Failed to revoke API key"
        )

    def _on_api_key_rotated(self, key_id: str) -> None:
        import asyncio

        asyncio.create_task(self._rotate_api_key(key_id))

    async def _rotate_api_key(self, key_id: str) -> None:
        from PySide6.QtWidgets import QApplication, QMessageBox

        if not (self._robot_controller and self._robot_controller.is_connected):
            QMessageBox.information(
                self._main_window,
                "Orchestrator Required",
                "API key rotation requires orchestrator connection.",
            )
            return

        client = self._robot_controller._orchestrator_client
        if not client:
            return

        try:
            resp = await client.rotate_robot_api_key(key_id)
            if not resp or "api_key" not in resp:
                raise RuntimeError("API key rotation failed")

            raw_key = resp["api_key"]
            QApplication.clipboard().setText(raw_key)
            QMessageBox.information(
                self._main_window,
                "API Key Rotated",
                "New API key copied to clipboard. Update the robot configuration now.\n\n"
                f"{raw_key}",
            )
            await self._refresh_all_data()
        except Exception as e:
            logger.error(f"Failed to rotate API key: {e}")
            QMessageBox.warning(self._main_window, "Rotate Failed", str(e))

    async def _get_robots(self) -> List[Any]:
        """Get robots from robot controller or local repository."""
        if self._robot_controller:
            # Force refresh from orchestrator to clear any deleted items from cache
            if self._robot_controller.is_connected:
                # Clear the controller's internal cache first to ensure we don't return stale data
                self._robot_controller._current_robots = []
                await self._robot_controller.refresh_robots()
            return self._robot_controller.robots

        # Fallback to local storage
        from casare_rpa.infrastructure.orchestrator.persistence import (
            LocalRobotRepository,
            LocalStorageRepository,
        )

        storage = LocalStorageRepository()
        repo = LocalRobotRepository(storage)
        return await repo.get_all()

    async def _get_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs from orchestrator API or local storage."""
        try:
            if self._robot_controller and self._robot_controller.is_connected:
                client = self._robot_controller._orchestrator_client
                if client:
                    job_data_list = await client.get_jobs(limit=100)
                    return [
                        {
                            "job_id": j.id,
                            "workflow_name": j.workflow_name,
                            "robot_name": j.robot_name,
                            "status": j.status,
                            "progress": j.progress,
                            "duration": getattr(j, "duration", 0) or 0,
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
                    "job_id": j.id,
                    "workflow_name": getattr(j, "workflow_name", ""),
                    "robot_name": getattr(j, "robot_name", ""),
                    "status": j.status.value
                    if hasattr(j.status, "value")
                    else j.status,
                    "progress": getattr(j, "progress", 0),
                    "duration": getattr(j, "duration", 0) or 0,
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
        """Get schedules from orchestrator API."""
        try:
            if self._robot_controller and self._robot_controller.is_connected:
                client = self._robot_controller._orchestrator_client
                if client:
                    # Schedules are now managed via orchestrator API
                    # and trigger nodes in workflows
                    schedule_data = await client.get_schedules()
                    return [
                        {
                            "id": s.get("schedule_id", ""),
                            "name": s.get("schedule_name", ""),
                            "workflow_name": s.get(
                                "workflow_name", s.get("schedule_name", "")
                            ),
                            "cron_expression": s.get("cron_expression", ""),
                            "enabled": s.get("enabled", True),
                            "next_run": str(s.get("next_run", "") or ""),
                            "last_run": str(s.get("last_run", "") or ""),
                        }
                        for s in schedule_data
                    ]
        except Exception as e:
            logger.warning(f"Failed to get schedules: {e}")
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
                    # Log rate limit/API errors as debug to reduce noise, return empty analytics
                    logger.debug(
                        f"Failed to get analytics from API (likely rate limit): {e}"
                    )
                    return {
                        "total_robots": len(robots),
                        "robots_by_status": {},
                        "total_jobs": len(jobs),
                        "jobs_by_status": {},
                        "jobs_completed_today": 0,
                        "jobs_failed_today": 0,
                        "success_rate": 0,
                        "avg_duration_ms": 0,
                        "queue_depth": 0,
                    }

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

        if hasattr(self, "_is_refreshing") and self._is_refreshing:
            logger.debug("Refresh already in progress, skipping")
            return

        self._is_refreshing = True
        logger.debug("Fleet dashboard refresh requested")

        task = asyncio.create_task(self._refresh_all_data())
        task.add_done_callback(lambda _: setattr(self, "_is_refreshing", False))

    def _on_robot_edited(self, robot_id: str, robot_data: dict) -> None:
        """Handle robot edit from fleet dashboard."""
        import asyncio

        if hasattr(self, "_is_editing") and self._is_editing:
            logger.warning("Edit already in progress, ignoring request")
            return

        self._is_editing = True
        logger.info(f"Robot edited: {robot_id}")

        task = asyncio.create_task(self._update_robot(robot_id, robot_data))
        task.add_done_callback(lambda _: setattr(self, "_is_editing", False))

    async def _update_robot(self, robot_id: str, robot_data: dict) -> None:
        """Update robot via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        def _generate_robot_id() -> str:
            import uuid

            return str(uuid.uuid4())

        try:
            from casare_rpa.infrastructure.orchestrator.client import (
                OrchestratorClient,
                OrchestratorConfig,
            )
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if not config_manager.config_exists():
                QMessageBox.information(
                    self._main_window,
                    "Local Mode",
                    "Robot editing requires orchestrator connection",
                )
                return

            config = config_manager.load()
            if not config.orchestrator.url:
                QMessageBox.information(
                    self._main_window,
                    "Local Mode",
                    "Robot editing requires orchestrator connection",
                )
                return

            base_url = self._normalize_orchestrator_base_url(config.orchestrator.url)

            client = OrchestratorClient(
                OrchestratorConfig(
                    base_url=base_url, api_key=config.orchestrator.api_key
                )
            )

            # Add Robot: when robot_id is empty, create a new robot id and register it.
            if not robot_id:
                new_robot_id = _generate_robot_id()
                hostname = f"manual-{new_robot_id}"

                ok = await client.register_robot(
                    robot_id=new_robot_id,
                    name=str(robot_data.get("name", "Robot")),
                    hostname=hostname,
                    capabilities=list(robot_data.get("capabilities") or []),
                    environment=str(robot_data.get("environment") or "production"),
                    max_concurrent_jobs=int(robot_data.get("max_concurrent_jobs") or 1),
                    tags=[],
                )

                await client.disconnect()
                if not ok:
                    raise RuntimeError("Robot registration failed")

                logger.info(f"Robot {new_robot_id} created via API")
                self._main_window.show_status(
                    f"Robot created ({new_robot_id}). Create an API key in the API Keys tab.",
                    5000,
                )
                await self._refresh_all_data()
                return

            ok = await client.update_robot(robot_id, robot_data)
            await client.disconnect()

            if not ok:
                raise RuntimeError("Robot update failed")

            logger.info(f"Robot {robot_id} updated via API")
            self._main_window.show_status("Robot updated successfully", 3000)
            await self._refresh_all_data()

        except Exception as e:
            logger.error(f"Failed to update robot: {e}")
            QMessageBox.warning(
                self._main_window,
                "Update Failed",
                f"Failed to update robot:\n{e}",
            )

    def _on_robot_deleted(self, robot_id: str) -> None:
        """Handle robot deletion from fleet dashboard."""
        import asyncio

        if hasattr(self, "_is_deleting") and self._is_deleting:
            logger.warning("Deletion already in progress, ignoring request")
            return

        self._is_deleting = True
        logger.info(f"Robot deleted: {robot_id}")

        task = asyncio.create_task(self._delete_robot(robot_id))
        task.add_done_callback(lambda _: setattr(self, "_is_deleting", False))

    async def _delete_robot(self, robot_id: str) -> None:
        """Delete robot via orchestrator API or local service."""
        from PySide6.QtWidgets import QMessageBox

        try:

            async def _unlink_local_robot_if_needed() -> None:
                try:
                    from dataclasses import replace

                    from casare_rpa.robot.identity_store import (
                        RobotIdentity,
                        RobotIdentityStore,
                    )

                    store = RobotIdentityStore()
                    identity = store.load()
                    if (
                        identity is None
                        or not identity.fleet_linked
                        or identity.fleet_robot_id != robot_id
                    ):
                        return

                    now = RobotIdentity.now_utc_iso()
                    store.save(
                        replace(
                            identity,
                            fleet_linked=False,
                            fleet_unlinked_reason="Deleted from Fleet dashboard",
                            fleet_unlinked_at_utc=now,
                            updated_at_utc=now,
                        )
                    )
                    self._main_window.show_status(
                        "Local robot unlinked (it will keep executing locally until you link again)",
                        5000,
                    )
                except Exception as e:
                    logger.debug(
                        f"Failed to unlink local robot identity after deletion: {e}"
                    )

            # 1. Try using the active OrchestratorClient if connected
            if self._robot_controller and self._robot_controller.is_connected:
                client = self._robot_controller._orchestrator_client
                if client:
                    try:
                        success = await client.delete_robot(robot_id)
                        if success:
                            # Mark as deleted in controller to prevent reappearing
                            self._robot_controller.mark_robot_deleted(robot_id)
                            await _unlink_local_robot_if_needed()
                            logger.info(
                                f"Robot {robot_id} deleted via active OrchestratorClient"
                            )
                            self._main_window.show_status(
                                "Robot deleted successfully", 3000
                            )
                            await self._refresh_all_data()
                            return
                        else:
                            logger.warning(
                                f"Failed to delete robot {robot_id} via API (success=False)"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error deleting robot via OrchestratorClient: {e}"
                        )
                        # Fall through to other methods

            # 2. Try manual API call if client not available but config exists
            import httpx
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url:
                    base_url = self._normalize_orchestrator_base_url(
                        config.orchestrator.url
                    )

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.delete(
                                f"{base_url}/robots/{robot_id}",
                                headers={
                                    "Authorization": f"Bearer {config.orchestrator.api_key}"
                                },
                            )
                            response.raise_for_status()

                        logger.info(f"Robot {robot_id} deleted via manual API call")
                        await _unlink_local_robot_if_needed()
                        self._main_window.show_status(
                            "Robot deleted successfully", 3000
                        )
                        await self._refresh_all_data()
                        return
                    except Exception as e:
                        logger.warning(
                            f"Manual API deletion failed, falling back to local: {e}"
                        )
                        # Fall through to local deletion

            # 3. Local deletion fallback
            from casare_rpa.infrastructure.orchestrator.persistence import (
                LocalRobotRepository,
                LocalStorageRepository,
            )

            storage = LocalStorageRepository()
            repo = LocalRobotRepository(storage)
            await repo.delete(robot_id)

            logger.info(f"Robot {robot_id} deleted from local storage")
            await _unlink_local_robot_if_needed()
            self._main_window.show_status("Robot deleted from local storage", 3000)
            await self._refresh_all_data()

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
        try:
            # Prefer using the already-connected orchestrator client (has correct auth headers).
            if self._robot_controller and self._robot_controller.is_connected:
                client = self._robot_controller._orchestrator_client
                if client and await client.cancel_job(job_id):
                    logger.info(f"Job {job_id} cancelled via OrchestratorClient")
                    self._main_window.show_status("Job cancelled successfully", 3000)
                    await self._refresh_all_data()
                    return

            # Fallback: construct a client from config (only if an API key is available).
            from casare_rpa.infrastructure.orchestrator.client import (
                OrchestratorClient,
                OrchestratorConfig,
            )
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url and config.orchestrator.api_key:
                    base_url = self._normalize_orchestrator_base_url(
                        config.orchestrator.url
                    )
                    tmp_client = OrchestratorClient(
                        OrchestratorConfig(
                            base_url=base_url,
                            api_key=config.orchestrator.api_key,
                        )
                    )
                    ok = await tmp_client.cancel_job(job_id)
                    await tmp_client.disconnect()
                    if ok:
                        logger.info(f"Job {job_id} cancelled via config client")
                        self._main_window.show_status(
                            "Job cancelled successfully", 3000
                        )
                        await self._refresh_all_data()
                        return

            self._main_window.show_status(
                "Job cancellation requires orchestrator + API key", 5000
            )
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            self._main_window.show_status(f"Cancel failed: {e}", 7000)

    def _on_job_retried(self, job_id: str) -> None:
        """Handle job retry from fleet dashboard."""
        import asyncio

        logger.info(f"Job retried: {job_id}")
        asyncio.create_task(self._retry_job(job_id))

    async def _retry_job(self, job_id: str) -> None:
        """Retry failed job via orchestrator API or local service."""
        try:
            if self._robot_controller and self._robot_controller.is_connected:
                client = self._robot_controller._orchestrator_client
                if client:
                    new_job_id = await client.retry_job(job_id)
                    if new_job_id:
                        logger.info(f"Job {job_id} retried as new job {new_job_id}")
                        self._main_window.show_status(
                            f"Job queued for retry: {new_job_id}", 3000
                        )
                        await self._refresh_all_data()
                        return

            from casare_rpa.infrastructure.orchestrator.client import (
                OrchestratorClient,
                OrchestratorConfig,
            )
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                if config.orchestrator.url and config.orchestrator.api_key:
                    base_url = self._normalize_orchestrator_base_url(
                        config.orchestrator.url
                    )
                    tmp_client = OrchestratorClient(
                        OrchestratorConfig(
                            base_url=base_url,
                            api_key=config.orchestrator.api_key,
                        )
                    )
                    new_job_id = await tmp_client.retry_job(job_id)
                    await tmp_client.disconnect()
                    if new_job_id:
                        logger.info(f"Job {job_id} retried as new job {new_job_id}")
                        self._main_window.show_status(
                            f"Job queued for retry: {new_job_id}", 3000
                        )
                        await self._refresh_all_data()
                        return

            self._main_window.show_status(
                "Job retry requires orchestrator + API key", 5000
            )
        except Exception as e:
            logger.error(f"Failed to retry job: {e}")
            self._main_window.show_status(f"Retry failed: {e}", 7000)

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

            # Prefer using the connected orchestrator client's API key
            api_key = None
            if self._robot_controller and self._robot_controller._orchestrator_client:
                client_config = self._robot_controller._orchestrator_client.config
                if client_config:
                    api_key = client_config.api_key

            # Fallback to config file
            if not api_key:
                from casare_rpa.presentation.setup.config_manager import (
                    ClientConfigManager,
                )

                config_manager = ClientConfigManager()
                if config_manager.config_exists():
                    config = config_manager.load()
                    api_key = config.orchestrator.api_key

            # Get base URL from robot controller
            base_url = None
            if self._robot_controller:
                base_url = self._robot_controller.orchestrator_url
            if not base_url:
                from casare_rpa.presentation.setup.config_manager import (
                    ClientConfigManager,
                )

                config_manager = ClientConfigManager()
                if config_manager.config_exists():
                    config = config_manager.load()
                    base_url = config.orchestrator.url

            if not base_url:
                raise ValueError("No orchestrator URL configured")

            base_url = self._normalize_orchestrator_base_url(base_url)

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            endpoint = "enable" if enabled else "disable"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{base_url}/api/v1/schedules/{schedule_id}/{endpoint}",
                    headers=headers,
                )
                response.raise_for_status()

            action = "enabled" if enabled else "disabled"
            logger.info(f"Schedule {schedule_id} {action}")
            self._main_window.show_status(f"Schedule {action} successfully", 3000)
            await self._refresh_all_data()

        except ImportError:
            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Schedule toggle requires orchestrator connection.\n"
                "Use Schedule Trigger nodes in workflows for local scheduling.",
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

        QMessageBox.information(
            self._main_window,
            "Edit Schedule",
            f"Schedule ID: {schedule_id}\n\n"
            "Schedules are managed via orchestrator API or\n"
            "Schedule Trigger nodes in workflows.",
        )

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

            # Prefer using the connected orchestrator client's API key
            api_key = None
            if self._robot_controller and self._robot_controller._orchestrator_client:
                client_config = self._robot_controller._orchestrator_client.config
                if client_config:
                    api_key = client_config.api_key

            # Fallback to config file
            if not api_key:
                from casare_rpa.presentation.setup.config_manager import (
                    ClientConfigManager,
                )

                config_manager = ClientConfigManager()
                if config_manager.config_exists():
                    config = config_manager.load()
                    api_key = config.orchestrator.api_key

            # Get base URL from robot controller
            base_url = None
            if self._robot_controller:
                base_url = self._robot_controller.orchestrator_url
            if not base_url:
                from casare_rpa.presentation.setup.config_manager import (
                    ClientConfigManager,
                )

                config_manager = ClientConfigManager()
                if config_manager.config_exists():
                    config = config_manager.load()
                    base_url = config.orchestrator.url

            if not base_url:
                raise ValueError("No orchestrator URL configured")

            base_url = self._normalize_orchestrator_base_url(base_url)

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{base_url}/api/v1/schedules/{schedule_id}",
                    headers=headers,
                )
                response.raise_for_status()

            logger.info(f"Schedule {schedule_id} deleted")
            self._main_window.show_status("Schedule deleted successfully", 3000)
            await self._refresh_all_data()

        except ImportError:
            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Schedule deletion requires orchestrator connection.\n"
                "Use Schedule Trigger nodes in workflows for local scheduling.",
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

            # Prefer using the connected orchestrator client's API key
            api_key = None
            if self._robot_controller and self._robot_controller._orchestrator_client:
                client_config = self._robot_controller._orchestrator_client.config
                if client_config:
                    api_key = client_config.api_key

            # Fallback to config file
            if not api_key:
                from casare_rpa.presentation.setup.config_manager import (
                    ClientConfigManager,
                )

                config_manager = ClientConfigManager()
                if config_manager.config_exists():
                    config = config_manager.load()
                    api_key = config.orchestrator.api_key

            # Get base URL from robot controller
            base_url = None
            if self._robot_controller:
                base_url = self._robot_controller.orchestrator_url
            if not base_url:
                from casare_rpa.presentation.setup.config_manager import (
                    ClientConfigManager,
                )

                config_manager = ClientConfigManager()
                if config_manager.config_exists():
                    config = config_manager.load()
                    base_url = config.orchestrator.url

            if not base_url:
                raise ValueError("No orchestrator URL configured")

            base_url = self._normalize_orchestrator_base_url(base_url)

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{base_url}/api/v1/schedules/{schedule_id}/trigger",
                    headers=headers,
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
            QMessageBox.information(
                self._main_window,
                "Local Mode",
                "Schedule execution requires orchestrator connection.\n"
                "Use Schedule Trigger nodes in workflows for local scheduling.",
            )
        except Exception as e:
            logger.error(f"Failed to trigger schedule: {e}")
            QMessageBox.warning(
                self._main_window,
                "Trigger Failed",
                f"Failed to trigger schedule:\n{e}",
            )
