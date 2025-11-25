"""
CasareRPA Robot Agent

Hardened robot agent with:
- Connection resilience (exponential backoff, circuit breaker)
- Offline job queue
- Job locking and cancellation
- Progress reporting via Supabase Realtime
- Per-node checkpointing
- Metrics and audit logging
- Configurable concurrent job execution
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from dotenv import load_dotenv
import orjson

from casare_rpa.utils.workflow_loader import load_workflow_from_dict
from casare_rpa.runner.workflow_runner import WorkflowRunner

from .config import (
    RobotConfig,
    get_config,
    validate_credentials,
    validate_credentials_async,
)
from .connection import ConnectionManager, ConnectionConfig, ConnectionState
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)
from .offline_queue import OfflineQueue
from .checkpoint import CheckpointManager
from .metrics import MetricsCollector, get_metrics_collector
from .audit import AuditLogger, init_audit_logger, AuditEventType, AuditSeverity
from .progress_reporter import ProgressReporter, CancellationChecker, JobLocker
from .job_executor import JobExecutor

load_dotenv()


class RobotAgent:
    """
    Hardened Robot Agent for CasareRPA.

    Features:
    - Resilient connection with exponential backoff
    - Circuit breaker for failing operations
    - Offline job queue for disconnected operation
    - Job locking to prevent race conditions
    - Progress reporting to Orchestrator
    - Per-node checkpointing for crash recovery
    - Configurable concurrent job execution
    - Comprehensive metrics and audit logging
    """

    def __init__(self, config: Optional[RobotConfig] = None):
        """
        Initialize robot agent.

        Args:
            config: Robot configuration (loads from file/env if None)
        """
        self.config = config or get_config()

        # Identity
        self.robot_id = self.config.robot_id
        self.name = self.config.robot_name

        # State
        self.running = False
        self._shutdown_event = asyncio.Event()

        # Initialize components
        self._init_logging()
        self._init_components()

        logger.info(f"Robot Agent initialized: {self.name} ({self.robot_id})")

    def _init_logging(self):
        """Initialize logging configuration."""
        logger.add(
            "logs/robot_{time}.log",
            rotation="1 day",
            retention="7 days",
            compression="zip",
        )

    def _init_components(self):
        """Initialize all agent components."""
        # Connection manager
        conn_config = ConnectionConfig(
            initial_delay=self.config.connection.initial_delay,
            max_delay=self.config.connection.max_delay,
            backoff_multiplier=self.config.connection.backoff_multiplier,
            jitter=self.config.connection.jitter,
            max_reconnect_attempts=self.config.connection.max_reconnect_attempts,
            connection_timeout=self.config.connection.connection_timeout,
            heartbeat_interval=self.config.connection.heartbeat_interval,
        )

        self.connection = ConnectionManager(
            url=self.config.connection.url,
            key=self.config.connection.key,
            config=conn_config,
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected,
            on_reconnecting=self._on_reconnecting,
        )

        # Circuit breaker for backend operations
        cb_config = CircuitBreakerConfig(
            failure_threshold=self.config.circuit_breaker.failure_threshold,
            success_threshold=self.config.circuit_breaker.success_threshold,
            timeout=self.config.circuit_breaker.timeout,
            half_open_max_calls=self.config.circuit_breaker.half_open_max_calls,
        )
        self.circuit_breaker = CircuitBreaker(
            "supabase",
            config=cb_config,
            on_state_change=self._on_circuit_state_change,
        )

        # Offline queue
        self.offline_queue = OfflineQueue(
            db_path=self.config.offline_db_path,
            robot_id=self.robot_id,
        )

        # Metrics collector
        self.metrics = get_metrics_collector()

        # Audit logger
        if self.config.observability.audit_enabled:
            self.audit = init_audit_logger(
                self.robot_id,
                log_dir=self.config.observability.audit_log_dir,
                max_file_size_mb=self.config.observability.audit_max_file_size_mb,
                backup_count=self.config.observability.audit_backup_count,
            )
        else:
            self.audit = None

        # Checkpoint manager
        if self.config.job_execution.checkpoint_enabled:
            self.checkpoint_manager = CheckpointManager(
                self.offline_queue,
                auto_save=self.config.job_execution.checkpoint_on_every_node,
            )
        else:
            self.checkpoint_manager = None

        # Progress reporter (initialized when connected)
        self.progress_reporter: Optional[ProgressReporter] = None

        # Job locker
        self.job_locker: Optional[JobLocker] = None

        # Job executor
        self.job_executor = JobExecutor(
            max_concurrent_jobs=self.config.job_execution.max_concurrent_jobs,
            checkpoint_manager=self.checkpoint_manager,
            metrics_collector=self.metrics,
            audit_logger=self.audit,
            on_job_complete=self._on_job_complete,
        )

    def _on_connected(self):
        """Callback when connection established."""
        if self.audit:
            self.audit.connection_established()

        # Initialize connection-dependent components
        self.progress_reporter = ProgressReporter(
            self.connection,
            self.robot_id,
            update_interval=self.config.job_execution.progress_update_interval,
        )
        self.job_locker = JobLocker(
            self.connection,
            self.robot_id,
            lock_timeout=self.config.job_execution.lock_timeout,
        )

        # Update job executor with progress reporter
        self.job_executor.progress_reporter = self.progress_reporter
        self.job_executor.job_locker = self.job_locker

    def _on_disconnected(self):
        """Callback when connection lost."""
        if self.audit:
            self.audit.connection_lost()

    def _on_reconnecting(self, attempt: int):
        """Callback when reconnecting."""
        if self.audit:
            self.audit.connection_reconnecting(attempt)

    def _on_circuit_state_change(self, old_state, new_state):
        """Callback when circuit breaker state changes."""
        if self.audit:
            self.audit.circuit_state_changed("supabase", new_state.value)

    async def _on_job_complete(self, job_id: str, success: bool, error: Optional[str]):
        """Callback when job completes."""
        # Update job status in Supabase
        if self.connection.is_connected:
            try:
                status = "success" if success else "failed"
                await self.connection.execute(
                    lambda client: client.table("jobs").update({
                        "status": status,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "error": error if error else None,
                    }).eq("id", job_id).execute()
                )
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")
                # Cache for later sync
                await self.offline_queue.mark_completed(job_id, success, error=error)

    async def start(self):
        """Start the robot agent."""
        self.running = True
        self._shutdown_event.clear()

        if self.audit:
            self.audit.robot_started({
                "robot_id": self.robot_id,
                "robot_name": self.name,
                "config": self.config.to_dict(),
            })

        logger.info("Robot Agent starting...")

        # Validate credentials
        is_valid, error = validate_credentials(
            self.config.connection.url,
            self.config.connection.key,
        )

        if not is_valid:
            logger.error(f"Invalid credentials: {error}")
            if self.audit:
                self.audit.log(
                    AuditEventType.CREDENTIAL_INVALID,
                    f"Credential validation failed: {error}",
                    severity=AuditSeverity.ERROR,
                )
            # Continue in offline mode
            logger.warning("Running in offline mode due to invalid credentials")

        # Start resource monitoring
        if self.config.observability.resource_monitoring_enabled:
            await self.metrics.start_resource_monitoring()

        # Start job executor
        await self.job_executor.start()

        # Check for interrupted jobs (crash recovery)
        await self._recover_interrupted_jobs()

        # Main agent loop
        await self._run_loop()

    async def _run_loop(self):
        """Main agent loop."""
        logger.info("Agent loop started")

        while self.running:
            try:
                # Ensure connection
                if not self.connection.is_connected:
                    try:
                        await self.circuit_breaker.call(self.connection.connect)
                        if self.connection.is_connected:
                            await self._register()
                    except CircuitBreakerOpenError as e:
                        logger.warning(f"Circuit breaker open: {e}")
                        await asyncio.sleep(10)
                        continue
                    except Exception as e:
                        logger.error(f"Connection failed: {e}")
                        await asyncio.sleep(5)
                        continue

                # Send heartbeat
                await self._heartbeat()

                # Check for new jobs
                await self._check_for_jobs()

                # Sync offline jobs
                await self._sync_offline_jobs()

                # Wait before next iteration
                await asyncio.sleep(self.config.job_execution.job_poll_interval)

            except Exception as e:
                logger.exception(f"Agent loop error: {e}")
                await asyncio.sleep(10)

        logger.info("Agent loop stopped")

    async def _register(self):
        """Register robot with backend."""
        try:
            data = {
                "id": self.robot_id,
                "name": self.name,
                "status": "online",
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "version": "2.0.0",  # Phase 8B
            }

            await self.connection.execute(
                lambda client: client.table("robots").upsert(data).execute()
            )

            if self.audit:
                self.audit.log(
                    AuditEventType.ROBOT_REGISTERED,
                    "Robot registered with backend",
                )

            logger.info("Robot registered successfully")

        except Exception as e:
            logger.error(f"Failed to register robot: {e}")

    async def _heartbeat(self):
        """Send heartbeat to backend."""
        try:
            await self.connection.execute(
                lambda client: client.table("robots").update({
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                    "status": "online",
                    "metrics": self.metrics.get_summary(),
                }).eq("id", self.robot_id).execute(),
                retry_on_failure=False,
            )
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")

    async def _check_for_jobs(self):
        """Check for pending jobs."""
        if not self.connection.is_connected:
            return

        if self.job_executor.is_at_capacity:
            return

        try:
            result = await self.connection.execute(
                lambda client: client.table("jobs")
                    .select("*")
                    .eq("robot_id", self.robot_id)
                    .eq("status", "pending")
                    .is_("claimed_by", "null")
                    .order("created_at")
                    .limit(self.config.job_execution.max_concurrent_jobs)
                    .execute()
            )

            jobs = result.data or []

            for job in jobs:
                # Skip if at capacity
                if self.job_executor.is_at_capacity:
                    break

                # Try to claim job
                if self.job_locker and await self.job_locker.try_claim(job["id"]):
                    if self.audit:
                        self.audit.job_received(
                            job["id"],
                            job.get("workflow", {}).get("metadata", {}).get("name", "unknown")
                        )

                    # Submit to executor
                    workflow_json = job["workflow"]
                    if isinstance(workflow_json, dict):
                        workflow_json = orjson.dumps(workflow_json).decode()

                    await self.job_executor.submit_job(
                        job["id"],
                        workflow_json,
                    )

        except CircuitBreakerOpenError:
            logger.debug("Circuit breaker open, skipping job check")
        except Exception as e:
            logger.error(f"Failed to check for jobs: {e}")

    async def _sync_offline_jobs(self):
        """Sync completed offline jobs to backend."""
        if not self.connection.is_connected:
            return

        jobs_to_sync = await self.offline_queue.get_jobs_to_sync()

        for job in jobs_to_sync:
            try:
                status = "success" if job["cached_status"] == "completed" else "failed"

                await self.connection.execute(
                    lambda client: client.table("jobs").update({
                        "status": status,
                        "completed_at": job.get("completed_at"),
                        "logs": job.get("logs"),
                        "error": job.get("error"),
                    }).eq("id", job["id"]).execute()
                )

                await self.offline_queue.mark_synced(job["id"])

                if self.audit:
                    self.audit.log(
                        AuditEventType.JOB_SYNCED,
                        f"Offline job synced: {job['id']}",
                        job_id=job["id"],
                    )

            except Exception as e:
                logger.error(f"Failed to sync job {job['id']}: {e}")
                await self.offline_queue.increment_sync_attempts(job["id"])

    async def _recover_interrupted_jobs(self):
        """Recover jobs that were interrupted (crash recovery)."""
        in_progress = await self.offline_queue.get_in_progress_jobs()

        for job in in_progress:
            logger.info(f"Recovering interrupted job: {job['id']}")

            if self.audit:
                self.audit.log(
                    AuditEventType.CHECKPOINT_RESTORED,
                    f"Recovering interrupted job from checkpoint",
                    job_id=job["id"],
                )

            # Check if there's a checkpoint to resume from
            if self.checkpoint_manager:
                checkpoint = await self.checkpoint_manager.get_checkpoint(job["id"])
                if checkpoint:
                    logger.info(
                        f"Found checkpoint for job {job['id']} "
                        f"at node {checkpoint.current_node_id}"
                    )

            # Re-submit to executor (it will handle checkpoint restoration)
            await self.job_executor.submit_job(
                job["id"],
                job["workflow_json"],
            )

    async def stop(self):
        """Stop the robot agent gracefully."""
        logger.info("Robot Agent stopping...")
        self.running = False
        self._shutdown_event.set()

        # Stop job executor
        await self.job_executor.stop(cancel_running=False)

        # Stop resource monitoring
        await self.metrics.stop_resource_monitoring()

        # Update status to offline
        if self.connection.is_connected:
            try:
                await self.connection.execute(
                    lambda client: client.table("robots").update({
                        "status": "offline",
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", self.robot_id).execute(),
                    retry_on_failure=False,
                )
            except Exception:
                pass

        # Disconnect
        await self.connection.disconnect()

        if self.audit:
            self.audit.robot_stopped("Graceful shutdown")

        logger.info("Robot Agent stopped")

    def get_status(self) -> dict:
        """Get comprehensive agent status."""
        return {
            "robot_id": self.robot_id,
            "robot_name": self.name,
            "running": self.running,
            "connection": self.connection.get_status(),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "job_executor": self.job_executor.get_status(),
            "metrics": self.metrics.get_summary(),
            "offline_queue": asyncio.get_event_loop().run_until_complete(
                self.offline_queue.get_queue_stats()
            ) if asyncio.get_event_loop().is_running() else {},
        }


# Convenience function for simple usage
async def run_robot(config: Optional[RobotConfig] = None):
    """Run the robot agent."""
    agent = RobotAgent(config)

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(run_robot())
