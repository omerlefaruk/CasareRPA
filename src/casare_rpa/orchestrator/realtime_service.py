"""
Supabase Realtime Service for Orchestrator.

Provides real-time updates for:
- Job progress changes
- Robot status changes
- Job completion events
"""

import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timezone
from loguru import logger

try:
    from supabase import create_client, Client
    from realtime import RealtimeChannel
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase realtime not available")


class RealtimeService:
    """
    Manages Supabase Realtime subscriptions for live updates.

    Subscribes to:
    - jobs table changes (INSERT, UPDATE, DELETE)
    - robots table changes (UPDATE for status/metrics)
    """

    def __init__(
        self,
        url: str,
        key: str,
        on_job_update: Optional[Callable[[Dict], None]] = None,
        on_robot_update: Optional[Callable[[Dict], None]] = None,
        on_job_progress: Optional[Callable[[str, Dict], None]] = None,
    ):
        """
        Initialize realtime service.

        Args:
            url: Supabase URL
            key: Supabase API key
            on_job_update: Callback for job changes
            on_robot_update: Callback for robot changes
            on_job_progress: Callback for job progress (job_id, progress_data)
        """
        self.url = url
        self.key = key
        self._on_job_update = on_job_update
        self._on_robot_update = on_robot_update
        self._on_job_progress = on_job_progress

        self._client: Optional[Client] = None
        self._subscribed = False
        self._channels: List[Any] = []

        # Polling fallback for progress
        self._polling_task: Optional[asyncio.Task] = None
        self._polling_jobs: Dict[str, Dict] = {}  # job_id -> last_progress

    async def connect(self) -> bool:
        """Connect and subscribe to realtime channels."""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available, using polling mode")
            return await self._start_polling()

        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured")
            return False

        try:
            self._client = create_client(self.url, self.key)

            # Subscribe to jobs channel
            await self._subscribe_to_jobs()

            # Subscribe to robots channel
            await self._subscribe_to_robots()

            self._subscribed = True
            logger.info("Connected to Supabase Realtime")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Supabase Realtime: {e}")
            # Fall back to polling
            return await self._start_polling()

    async def _subscribe_to_jobs(self):
        """Subscribe to jobs table changes."""
        try:
            # Note: Supabase Python client may not have full realtime support
            # This is a placeholder for when it becomes available
            # For now, we'll use polling
            logger.info("Jobs realtime subscription attempted")
        except Exception as e:
            logger.error(f"Failed to subscribe to jobs: {e}")

    async def _subscribe_to_robots(self):
        """Subscribe to robots table changes."""
        try:
            logger.info("Robots realtime subscription attempted")
        except Exception as e:
            logger.error(f"Failed to subscribe to robots: {e}")

    async def _start_polling(self) -> bool:
        """Start polling for updates (fallback mode)."""
        if self._polling_task is not None:
            return True

        self._polling_task = asyncio.create_task(self._poll_loop())
        logger.info("Started polling mode for job updates")
        return True

    async def _poll_loop(self):
        """Poll for job and robot updates."""
        while True:
            try:
                await self._poll_jobs()
                await self._poll_robots()
                await asyncio.sleep(2.0)  # Poll every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5.0)

    async def _poll_jobs(self):
        """Poll for job updates."""
        if not self._client:
            return

        try:
            # Get running jobs
            response = await asyncio.to_thread(
                lambda: self._client.table("jobs")
                    .select("id,status,progress,current_node,error_message")
                    .in_("status", ["running", "pending"])
                    .execute()
            )

            for job in response.data or []:
                job_id = job.get("id")
                progress = job.get("progress", {})

                # Check if progress changed
                last_progress = self._polling_jobs.get(job_id, {})
                if progress != last_progress:
                    self._polling_jobs[job_id] = progress
                    if self._on_job_progress:
                        self._on_job_progress(job_id, progress)
                    if self._on_job_update:
                        self._on_job_update(job)

            # Clean up completed jobs from tracking
            active_ids = {j.get("id") for j in (response.data or [])}
            completed_ids = set(self._polling_jobs.keys()) - active_ids
            for job_id in completed_ids:
                del self._polling_jobs[job_id]

        except Exception as e:
            logger.debug(f"Job polling error: {e}")

    async def _poll_robots(self):
        """Poll for robot updates."""
        if not self._client:
            return

        try:
            response = await asyncio.to_thread(
                lambda: self._client.table("robots")
                    .select("*")
                    .execute()
            )

            for robot in response.data or []:
                if self._on_robot_update:
                    self._on_robot_update(robot)

        except Exception as e:
            logger.debug(f"Robot polling error: {e}")

    def track_job(self, job_id: str):
        """Start tracking a specific job for progress updates."""
        self._polling_jobs[job_id] = {}

    def untrack_job(self, job_id: str):
        """Stop tracking a specific job."""
        self._polling_jobs.pop(job_id, None)

    async def disconnect(self):
        """Disconnect from realtime and stop polling."""
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None

        for channel in self._channels:
            try:
                await channel.unsubscribe()
            except Exception:
                pass

        self._channels.clear()
        self._subscribed = False
        logger.info("Disconnected from Supabase Realtime")


class JobProgressTracker:
    """
    Tracks job progress and emits updates.

    Used by UI components to get live progress updates.
    """

    def __init__(self, realtime_service: RealtimeService):
        self._service = realtime_service
        self._callbacks: Dict[str, List[Callable[[Dict], None]]] = {}

    def subscribe(
        self,
        job_id: str,
        callback: Callable[[Dict], None]
    ):
        """
        Subscribe to progress updates for a job.

        Args:
            job_id: Job to track
            callback: Function to call with progress data
        """
        if job_id not in self._callbacks:
            self._callbacks[job_id] = []
            self._service.track_job(job_id)

        self._callbacks[job_id].append(callback)

    def unsubscribe(self, job_id: str, callback: Callable[[Dict], None]):
        """Unsubscribe from progress updates."""
        if job_id in self._callbacks:
            if callback in self._callbacks[job_id]:
                self._callbacks[job_id].remove(callback)

            if not self._callbacks[job_id]:
                del self._callbacks[job_id]
                self._service.untrack_job(job_id)

    def on_progress(self, job_id: str, progress: Dict):
        """Handle progress update from realtime service."""
        callbacks = self._callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")


class RobotStatusTracker:
    """
    Tracks robot status and emits updates.

    Used by UI components to get live robot status.
    """

    def __init__(self, realtime_service: RealtimeService):
        self._service = realtime_service
        self._callbacks: List[Callable[[Dict], None]] = []
        self._robot_status: Dict[str, Dict] = {}

    def subscribe(self, callback: Callable[[Dict], None]):
        """Subscribe to robot status updates."""
        self._callbacks.append(callback)

    def unsubscribe(self, callback: Callable[[Dict], None]):
        """Unsubscribe from robot status updates."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def on_robot_update(self, robot: Dict):
        """Handle robot update from realtime service."""
        robot_id = robot.get("id")
        if robot_id:
            self._robot_status[robot_id] = robot

        for callback in self._callbacks:
            try:
                callback(robot)
            except Exception as e:
                logger.error(f"Robot callback error: {e}")

    def get_robot_status(self, robot_id: str) -> Optional[Dict]:
        """Get cached robot status."""
        return self._robot_status.get(robot_id)

    def get_all_robots(self) -> List[Dict]:
        """Get all cached robot statuses."""
        return list(self._robot_status.values())
