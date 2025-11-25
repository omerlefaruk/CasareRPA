"""
Progress Reporter for Robot Agent.

Reports job execution progress to Orchestrator via Supabase Realtime.
Uses database updates that trigger Supabase Realtime subscriptions.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Callable, Any, Dict, List
from loguru import logger

from .connection import ConnectionManager


class ProgressStage(Enum):
    """Stages of job execution."""
    QUEUED = "queued"
    STARTING = "starting"
    LOADING_WORKFLOW = "loading_workflow"
    EXECUTING = "executing"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressReporter:
    """
    Reports job progress to Orchestrator via Supabase.

    Updates job records with progress information that can be
    observed via Supabase Realtime subscriptions.
    """

    def __init__(
        self,
        connection: ConnectionManager,
        robot_id: str,
        update_interval: float = 1.0,
        batch_updates: bool = True,
    ):
        """
        Initialize progress reporter.

        Args:
            connection: ConnectionManager for Supabase
            robot_id: Robot identifier
            update_interval: Minimum seconds between updates
            batch_updates: Whether to batch rapid updates
        """
        self.connection = connection
        self.robot_id = robot_id
        self.update_interval = update_interval
        self.batch_updates = batch_updates

        # Current job tracking
        self._current_job_id: Optional[str] = None
        self._current_stage: Optional[ProgressStage] = None
        self._total_nodes: int = 0
        self._completed_nodes: int = 0
        self._current_node: Optional[str] = None
        self._started_at: Optional[datetime] = None

        # Update batching
        self._pending_update: Optional[Dict] = None
        self._last_update: Optional[datetime] = None
        self._update_task: Optional[asyncio.Task] = None

        # Listeners
        self._progress_listeners: List[Callable[[Dict], None]] = []

        logger.info("Progress reporter initialized")

    def add_listener(self, listener: Callable[[Dict], None]):
        """Add a progress listener callback."""
        self._progress_listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict], None]):
        """Remove a progress listener callback."""
        if listener in self._progress_listeners:
            self._progress_listeners.remove(listener)

    def _notify_listeners(self, progress: Dict):
        """Notify all listeners of progress update."""
        for listener in self._progress_listeners:
            try:
                listener(progress)
            except Exception as e:
                logger.error(f"Progress listener error: {e}")

    async def start_job(
        self,
        job_id: str,
        workflow_name: str,
        total_nodes: int,
    ):
        """
        Start reporting progress for a job.

        Args:
            job_id: Job identifier
            workflow_name: Name of the workflow
            total_nodes: Total number of nodes in workflow
        """
        self._current_job_id = job_id
        self._current_stage = ProgressStage.STARTING
        self._total_nodes = total_nodes
        self._completed_nodes = 0
        self._current_node = None
        self._started_at = datetime.now(timezone.utc)

        await self._send_update({
            "stage": ProgressStage.STARTING.value,
            "workflow_name": workflow_name,
            "total_nodes": total_nodes,
            "completed_nodes": 0,
            "percent_complete": 0,
            "started_at": self._started_at.isoformat(),
        })

        logger.debug(f"Started progress tracking for job {job_id}")

    async def update_stage(self, stage: ProgressStage, message: Optional[str] = None):
        """
        Update the current execution stage.

        Args:
            stage: New execution stage
            message: Optional status message
        """
        self._current_stage = stage
        update = {"stage": stage.value}
        if message:
            update["message"] = message
        await self._send_update(update)

    async def report_node_start(
        self,
        node_id: str,
        node_type: str,
        node_name: Optional[str] = None,
    ):
        """
        Report that a node has started executing.

        Args:
            node_id: Node identifier
            node_type: Type of the node
            node_name: Display name of the node
        """
        self._current_node = node_id

        await self._send_update({
            "stage": ProgressStage.EXECUTING.value,
            "current_node_id": node_id,
            "current_node_type": node_type,
            "current_node_name": node_name or node_type,
        })

    async def report_node_complete(
        self,
        node_id: str,
        success: bool,
        duration_ms: float,
        error: Optional[str] = None,
    ):
        """
        Report that a node has completed.

        Args:
            node_id: Node identifier
            success: Whether node succeeded
            duration_ms: Execution duration in milliseconds
            error: Error message if failed
        """
        if success:
            self._completed_nodes += 1

        percent = (
            (self._completed_nodes / self._total_nodes * 100)
            if self._total_nodes > 0 else 0
        )

        update = {
            "completed_nodes": self._completed_nodes,
            "percent_complete": round(percent, 1),
            "last_node_id": node_id,
            "last_node_success": success,
            "last_node_duration_ms": duration_ms,
        }

        if error:
            update["last_node_error"] = error[:500]  # Truncate long errors

        await self._send_update(update)

    async def end_job(
        self,
        success: bool,
        error_message: Optional[str] = None,
        logs: Optional[str] = None,
    ):
        """
        End progress reporting for current job.

        Args:
            success: Whether job succeeded
            error_message: Error message if failed
            logs: Execution logs
        """
        if not self._current_job_id:
            return

        completed_at = datetime.now(timezone.utc)
        duration_ms = (
            (completed_at - self._started_at).total_seconds() * 1000
            if self._started_at else 0
        )

        stage = ProgressStage.COMPLETED if success else ProgressStage.FAILED

        update = {
            "stage": stage.value,
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "success": success,
            "percent_complete": 100 if success else self._get_percent(),
        }

        if error_message:
            update["error_message"] = error_message[:1000]

        # Force immediate update for completion
        await self._send_update(update, force=True)

        logger.debug(f"Ended progress tracking for job {self._current_job_id}")

        # Reset state
        self._current_job_id = None
        self._current_stage = None

    async def report_cancelled(self, reason: Optional[str] = None):
        """Report that job was cancelled."""
        await self._send_update({
            "stage": ProgressStage.CANCELLED.value,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancel_reason": reason,
        }, force=True)

        self._current_job_id = None
        self._current_stage = None

    def _get_percent(self) -> float:
        """Get current completion percentage."""
        if self._total_nodes == 0:
            return 0
        return round(self._completed_nodes / self._total_nodes * 100, 1)

    async def _send_update(
        self,
        progress_data: Dict[str, Any],
        force: bool = False,
    ):
        """
        Send progress update to Supabase.

        Args:
            progress_data: Progress data to send
            force: Force immediate update (skip batching)
        """
        if not self._current_job_id:
            return

        # Add common fields
        progress_data["robot_id"] = self.robot_id
        progress_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Notify local listeners
        self._notify_listeners(progress_data)

        # Batch updates if enabled
        if self.batch_updates and not force:
            self._pending_update = {
                **(self._pending_update or {}),
                **progress_data,
            }

            if self._update_task is None or self._update_task.done():
                self._update_task = asyncio.create_task(self._flush_update())
            return

        # Send immediately
        await self._do_send_update(progress_data)

    async def _flush_update(self):
        """Flush pending batched update."""
        await asyncio.sleep(self.update_interval)

        if self._pending_update:
            update = self._pending_update
            self._pending_update = None
            await self._do_send_update(update)

    async def _do_send_update(self, progress_data: Dict[str, Any]):
        """Actually send update to Supabase."""
        if not self._current_job_id or not self.connection.is_connected:
            return

        try:
            # Update job progress column
            await self.connection.execute(
                lambda client: client.table("jobs").update({
                    "progress": progress_data,
                }).eq("id", self._current_job_id).execute(),
                retry_on_failure=False,  # Don't retry progress updates
            )

            self._last_update = datetime.now(timezone.utc)

        except Exception as e:
            # Don't fail job on progress update failure
            logger.warning(f"Failed to send progress update: {e}")


class CancellationChecker:
    """
    Checks for job cancellation requests via Supabase.

    Polls for cancel_requested flag on job records.
    """

    def __init__(
        self,
        connection: ConnectionManager,
        check_interval: float = 2.0,
    ):
        """
        Initialize cancellation checker.

        Args:
            connection: ConnectionManager for Supabase
            check_interval: Seconds between cancellation checks
        """
        self.connection = connection
        self.check_interval = check_interval

        self._current_job_id: Optional[str] = None
        self._cancelled = False
        self._check_task: Optional[asyncio.Task] = None

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled

    def start(self, job_id: str):
        """Start checking for cancellation."""
        self._current_job_id = job_id
        self._cancelled = False
        self._check_task = asyncio.create_task(self._check_loop())

    def stop(self):
        """Stop checking for cancellation."""
        self._current_job_id = None
        if self._check_task:
            self._check_task.cancel()
            self._check_task = None

    async def check_once(self) -> bool:
        """Check cancellation status once."""
        if not self._current_job_id or not self.connection.is_connected:
            return False

        try:
            result = await self.connection.execute(
                lambda client: client.table("jobs")
                    .select("cancel_requested")
                    .eq("id", self._current_job_id)
                    .single()
                    .execute(),
                retry_on_failure=False,
            )

            if result.data and result.data.get("cancel_requested"):
                self._cancelled = True
                logger.info(f"Cancellation requested for job {self._current_job_id}")
                return True

        except Exception as e:
            logger.debug(f"Cancellation check failed: {e}")

        return False

    async def _check_loop(self):
        """Background loop for checking cancellation."""
        while self._current_job_id:
            try:
                await self.check_once()
                if self._cancelled:
                    break
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Cancellation check error: {e}")
                await asyncio.sleep(self.check_interval)


class JobLocker:
    """
    Provides job locking to prevent race conditions.

    Uses atomic database operations to claim jobs exclusively.
    """

    def __init__(
        self,
        connection: ConnectionManager,
        robot_id: str,
        lock_timeout: float = 300.0,  # 5 minutes
    ):
        """
        Initialize job locker.

        Args:
            connection: ConnectionManager for Supabase
            robot_id: Robot identifier
            lock_timeout: Seconds before lock expires
        """
        self.connection = connection
        self.robot_id = robot_id
        self.lock_timeout = lock_timeout

    async def try_claim(self, job_id: str) -> bool:
        """
        Try to claim a job for exclusive execution.

        Uses optimistic locking - only claims if job is still pending.

        Args:
            job_id: Job to claim

        Returns:
            True if successfully claimed
        """
        try:
            claimed_at = datetime.now(timezone.utc).isoformat()

            result = await self.connection.execute(
                lambda client: client.table("jobs")
                    .update({
                        "claimed_by": self.robot_id,
                        "claimed_at": claimed_at,
                        "status": "running",
                    })
                    .eq("id", job_id)
                    .eq("status", "pending")
                    .is_("claimed_by", "null")
                    .execute(),
            )

            # Check if update affected any rows
            if result.data and len(result.data) > 0:
                logger.info(f"Successfully claimed job {job_id}")
                return True
            else:
                logger.debug(f"Failed to claim job {job_id} - already claimed or not pending")
                return False

        except Exception as e:
            logger.error(f"Failed to claim job {job_id}: {e}")
            return False

    async def release(self, job_id: str, status: str = "pending"):
        """
        Release a claimed job.

        Args:
            job_id: Job to release
            status: Status to set (default: pending for retry)
        """
        try:
            await self.connection.execute(
                lambda client: client.table("jobs")
                    .update({
                        "claimed_by": None,
                        "claimed_at": None,
                        "status": status,
                    })
                    .eq("id", job_id)
                    .eq("claimed_by", self.robot_id)
                    .execute(),
            )
            logger.debug(f"Released job {job_id}")

        except Exception as e:
            logger.error(f"Failed to release job {job_id}: {e}")

    async def heartbeat(self, job_id: str):
        """
        Update lock heartbeat to prevent expiry.

        Args:
            job_id: Job to heartbeat
        """
        try:
            await self.connection.execute(
                lambda client: client.table("jobs")
                    .update({"lock_heartbeat": datetime.now(timezone.utc).isoformat()})
                    .eq("id", job_id)
                    .eq("claimed_by", self.robot_id)
                    .execute(),
                retry_on_failure=False,
            )
        except Exception as e:
            logger.debug(f"Lock heartbeat failed for job {job_id}: {e}")
