"""
Realtime-Enabled Distributed Robot Agent for CasareRPA.

Extends DistributedRobotAgent with Supabase Realtime integration for:
- Instant job notifications via Postgres Changes CDC
- Control commands (cancel_job, shutdown, pause) via Broadcast
- Robot presence tracking for fleet management

Implements hybrid poll+subscribe model for resilience:
- Primary: Subscribe to Realtime for instant notifications
- Fallback: Poll database if Realtime fails

Architecture:
    +-------------------+
    | RealtimeRobotAgent|
    +--------+----------+
             |
    +--------v----------+     +-------------------+
    | PgQueuerConsumer  |<--->| Supabase Realtime |
    | (Job Claiming)    |     | (Notifications)   |
    +--------+----------+     +-------------------+
             |                        |
    +--------v----------+     +-------v-----------+
    |DBOSWorkflowExec   |     | Presence Channel  |
    |(Durable Execute)  |     | (Health Tracking) |
    +-------------------+     +-------------------+
"""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.queue import (
    PgQueuerConsumer,
    ClaimedJob,
    ConsumerConfig,
)
from casare_rpa.infrastructure.execution.dbos_executor import (
    DBOSWorkflowExecutor,
    DBOSExecutorConfig,
)
from casare_rpa.infrastructure.realtime import (
    RealtimeClient,
    RealtimeConfig,
    RealtimeConnectionState,
    JobInsertedPayload,
    ControlCommandPayload,
    PresenceState,
    RobotPresenceInfo,
)

from .distributed_agent import (
    DistributedRobotAgent,
    DistributedRobotConfig,
    AgentState,
)


@dataclass
class RealtimeRobotConfig(DistributedRobotConfig):
    """
    Configuration for Realtime-enabled robot agent.

    Extends DistributedRobotConfig with Supabase Realtime settings.

    Attributes:
        supabase_url: Supabase project URL
        supabase_key: Supabase anon/service key
        enable_realtime: Enable Realtime integration (can be disabled for fallback)
        realtime_subscribe_timeout_seconds: Timeout for hybrid model
        presence_update_interval_seconds: Interval for presence updates
        capabilities: Robot capabilities for load balancing
    """

    supabase_url: str = ""
    supabase_key: str = ""
    enable_realtime: bool = True
    realtime_subscribe_timeout_seconds: float = 5.0
    presence_update_interval_seconds: float = 5.0
    capabilities: List[str] = field(default_factory=lambda: ["browser", "desktop"])

    @classmethod
    def from_env(cls) -> "RealtimeRobotConfig":
        """Create configuration from environment variables."""
        import os

        base_config = DistributedRobotConfig.from_env()

        return cls(
            robot_id=base_config.robot_id,
            robot_name=base_config.robot_name,
            postgres_url=base_config.postgres_url,
            environment=base_config.environment,
            batch_size=base_config.batch_size,
            poll_interval_seconds=base_config.poll_interval_seconds,
            heartbeat_interval_seconds=base_config.heartbeat_interval_seconds,
            visibility_timeout_seconds=base_config.visibility_timeout_seconds,
            graceful_shutdown_seconds=base_config.graceful_shutdown_seconds,
            max_concurrent_jobs=base_config.max_concurrent_jobs,
            job_timeout_seconds=base_config.job_timeout_seconds,
            node_timeout_seconds=base_config.node_timeout_seconds,
            enable_checkpointing=base_config.enable_checkpointing,
            log_dir=base_config.log_dir,
            # Realtime-specific
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_ANON_KEY", "")),
            enable_realtime=os.getenv("CASARE_ENABLE_REALTIME", "true").lower()
            == "true",
            realtime_subscribe_timeout_seconds=float(
                os.getenv("CASARE_REALTIME_TIMEOUT", "5.0")
            ),
            presence_update_interval_seconds=float(
                os.getenv("CASARE_PRESENCE_INTERVAL", "5.0")
            ),
            capabilities=os.getenv("CASARE_CAPABILITIES", "browser,desktop").split(","),
        )


class RealtimeRobotAgent(DistributedRobotAgent):
    """
    Distributed Robot Agent with Supabase Realtime integration.

    Extends DistributedRobotAgent with event-driven job notifications
    and control commands via Supabase Realtime.

    Features:
    - Instant job notifications (no polling delay)
    - Remote control commands (cancel, shutdown, pause)
    - Presence tracking for fleet monitoring
    - Hybrid poll+subscribe for resilience
    - Automatic fallback to polling if Realtime fails

    Usage:
        config = RealtimeRobotConfig(
            postgres_url="postgresql://...",
            supabase_url="https://xxx.supabase.co",
            supabase_key="your-key",
            robot_id="worker-01",
        )
        agent = RealtimeRobotAgent(config)

        await agent.start()
        # Agent runs until stopped
        await agent.stop()
    """

    def __init__(
        self,
        config: RealtimeRobotConfig,
        on_job_complete: Optional[Callable[[str, bool, Optional[str]], None]] = None,
    ) -> None:
        """
        Initialize Realtime-enabled robot agent.

        Args:
            config: Robot configuration with Realtime settings
            on_job_complete: Optional callback (job_id, success, error)
        """
        super().__init__(config, on_job_complete)

        self._realtime_config = config
        self._realtime_client: Optional[RealtimeClient] = None
        self._realtime_connected = False
        self._paused = False

        # Track start time for uptime
        self._start_time: Optional[datetime] = None

        # Presence update task
        self._presence_task: Optional[asyncio.Task] = None

        logger.info(
            f"RealtimeRobotAgent initialized: realtime={config.enable_realtime}, "
            f"capabilities={config.capabilities}"
        )

    @property
    def is_paused(self) -> bool:
        """Check if agent is paused."""
        return self._paused

    async def start(self) -> None:
        """
        Start the robot agent with Realtime integration.

        Establishes database connections, connects to Supabase Realtime,
        starts background tasks, and begins processing jobs.
        """
        await super().start()
        self._start_time = datetime.now(timezone.utc)

        # Initialize Realtime if enabled
        if self._realtime_config.enable_realtime and self._realtime_config.supabase_url:
            await self._setup_realtime()

    async def _setup_realtime(self) -> None:
        """Setup Supabase Realtime connection and channels."""
        try:
            realtime_config = RealtimeConfig(
                supabase_url=self._realtime_config.supabase_url,
                supabase_key=self._realtime_config.supabase_key,
                robot_id=self.robot_id,
                environment=self._realtime_config.environment,
                presence_update_interval_seconds=self._realtime_config.presence_update_interval_seconds,
            )

            self._realtime_client = RealtimeClient(realtime_config)

            # Register callbacks
            self._realtime_client.on_job_inserted(self._on_job_notification)
            self._realtime_client.on_control_command(self._on_control_command)
            self._realtime_client.on_presence_sync(self._on_presence_sync)
            self._realtime_client.on_connection_state(self._on_realtime_state_change)

            # Connect and subscribe
            await self._realtime_client.connect()
            await self._realtime_client.subscribe_all()

            self._realtime_connected = True

            # Start presence updates
            self._presence_task = asyncio.create_task(self._presence_loop())

            logger.info("Realtime integration enabled")

        except Exception as e:
            logger.warning(
                f"Failed to setup Realtime: {e}. Falling back to polling-only mode."
            )
            self._realtime_connected = False

    async def stop(self) -> None:
        """
        Gracefully stop the robot agent.

        Disconnects from Realtime, stops background tasks, and
        releases resources.
        """
        logger.info(f"Stopping RealtimeRobotAgent: {self.robot_name}")

        # Cancel presence task
        if self._presence_task and not self._presence_task.done():
            self._presence_task.cancel()
            try:
                await self._presence_task
            except asyncio.CancelledError:
                pass

        # Disconnect from Realtime
        if self._realtime_client:
            await self._realtime_client.disconnect()
            self._realtime_client = None

        # Call parent stop
        await super().stop()

    async def _polling_loop(self) -> None:
        """
        Hybrid poll + subscribe job loop.

        Uses Realtime notifications when available, falls back to
        polling when Realtime is unavailable or on timeout.
        """
        logger.info("Hybrid job loop started")

        while self._running:
            try:
                # Skip if paused
                if self._paused:
                    await asyncio.sleep(1.0)
                    continue

                # Check if at capacity
                if self.current_job_count >= self._realtime_config.max_concurrent_jobs:
                    await asyncio.sleep(self._realtime_config.poll_interval_seconds)
                    continue

                # Hybrid: Wait for notification or timeout
                notification_received = False
                if self._realtime_connected and self._realtime_client:
                    notification_received = await self._realtime_client.wait_for_job_notification(
                        timeout=self._realtime_config.realtime_subscribe_timeout_seconds
                    )

                    if notification_received:
                        logger.debug("Job notification received via Realtime")
                    else:
                        logger.debug("No notification, polling queue")
                else:
                    # Realtime not available, use polling interval
                    await asyncio.sleep(self._realtime_config.poll_interval_seconds)

                # Always poll (notification is just a hint for faster response)
                job = await self._consumer.claim_job()

                if job:
                    # Execute job in background
                    asyncio.create_task(self._execute_job_with_realtime(job))
                elif not notification_received:
                    # No jobs and no notification, brief pause before next poll
                    await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in hybrid job loop: {e}")
                await asyncio.sleep(5)

        logger.info("Hybrid job loop stopped")

    async def _execute_job_with_realtime(self, job: ClaimedJob) -> None:
        """
        Execute a job with Realtime heartbeat integration.

        Sends heartbeats via Realtime broadcast in addition to
        database lease extension.

        Args:
            job: The claimed job to execute
        """
        await self._execute_job(job)

    async def _on_job_notification(self, payload: JobInsertedPayload) -> None:
        """
        Handle job insert notification from Realtime.

        This is just a signal - actual claiming happens in polling loop.

        Args:
            payload: Job insert payload
        """
        logger.debug(
            f"Job notification: {payload.job_id[:8]} - {payload.workflow_name} "
            f"(priority={payload.priority})"
        )
        # The notification event is set automatically by RealtimeClient

    async def _on_control_command(self, payload: ControlCommandPayload) -> None:
        """
        Handle control command from orchestrator.

        Args:
            payload: Control command payload
        """
        command = payload.command

        if command == "cancel_job":
            await self._handle_cancel_job(payload.job_id, payload.reason)
        elif command == "shutdown":
            await self._handle_shutdown(payload.reason)
        elif command == "pause":
            await self._handle_pause(payload.reason)
        elif command == "resume":
            await self._handle_resume()
        else:
            logger.warning(f"Unknown control command: {command}")

    async def _handle_cancel_job(
        self, job_id: Optional[str], reason: Optional[str]
    ) -> None:
        """
        Handle cancel_job command.

        Args:
            job_id: Job to cancel
            reason: Cancellation reason
        """
        if not job_id:
            logger.warning("cancel_job command missing job_id")
            return

        if job_id in self._current_jobs:
            logger.info(
                f"Cancelling job {job_id[:8]}: {reason or 'No reason provided'}"
            )
            # Mark job for cancellation - executor should check this flag
            # Note: Full cancellation requires executor support
            await self._consumer.release_job(job_id)
            self._current_jobs.pop(job_id, None)
        else:
            logger.debug(f"Job {job_id[:8]} not found for cancellation")

    async def _handle_shutdown(self, reason: Optional[str]) -> None:
        """
        Handle shutdown command.

        Args:
            reason: Shutdown reason
        """
        logger.info(f"Shutdown command received: {reason or 'No reason provided'}")
        # Trigger graceful shutdown
        asyncio.create_task(self.stop())

    async def _handle_pause(self, reason: Optional[str]) -> None:
        """
        Handle pause command.

        Args:
            reason: Pause reason
        """
        logger.info(f"Pause command received: {reason or 'No reason provided'}")
        self._paused = True

    async def _handle_resume(self) -> None:
        """Handle resume command."""
        logger.info("Resume command received")
        self._paused = False

    async def _on_presence_sync(self, state: PresenceState) -> None:
        """
        Handle presence sync event.

        Args:
            state: Current presence state
        """
        idle_count = len(state.get_idle_robots())
        busy_count = len(state.get_busy_robots())
        logger.debug(f"Presence sync: {idle_count} idle, {busy_count} busy robots")

    def _on_realtime_state_change(self, state: RealtimeConnectionState) -> None:
        """
        Handle Realtime connection state change.

        Args:
            state: New connection state
        """
        if state == RealtimeConnectionState.CONNECTED:
            self._realtime_connected = True
            logger.info("Realtime reconnected")
        elif state in (
            RealtimeConnectionState.DISCONNECTED,
            RealtimeConnectionState.FAILED,
        ):
            self._realtime_connected = False
            logger.warning(f"Realtime disconnected: {state.value}")

    async def _presence_loop(self) -> None:
        """Background task to update robot presence."""
        logger.debug("Presence update loop started")

        while self._running:
            try:
                await asyncio.sleep(
                    self._realtime_config.presence_update_interval_seconds
                )

                if not self._running or not self._realtime_client:
                    break

                # Build presence info
                presence = self._build_presence_info()

                # Track presence
                await self._realtime_client.track_presence(presence)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Presence update error: {e}")
                await asyncio.sleep(5)

        logger.debug("Presence update loop stopped")

    def _build_presence_info(self) -> RobotPresenceInfo:
        """
        Build current robot presence information.

        Returns:
            RobotPresenceInfo with current state
        """
        # Determine status
        if self._state == AgentState.SHUTTING_DOWN:
            status = "shutting_down"
        elif self._paused:
            status = "paused"
        elif self.current_job_count > 0:
            status = "busy"
        else:
            status = "idle"

        # Get current job ID if any
        current_job_id = None
        if self._current_jobs:
            current_job_id = next(iter(self._current_jobs.keys()))

        # Calculate uptime
        uptime_seconds = 0.0
        if self._start_time:
            uptime_seconds = (
                datetime.now(timezone.utc) - self._start_time
            ).total_seconds()

        # Get system metrics if psutil available
        cpu_percent = 0.0
        memory_percent = 0.0
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
        except ImportError:
            pass
        except Exception:
            pass

        return RobotPresenceInfo(
            robot_id=self.robot_id,
            status=status,
            current_job_id=current_job_id,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            jobs_completed=self._stats["jobs_completed"],
            jobs_failed=self._stats["jobs_failed"],
            uptime_seconds=uptime_seconds,
            environment=self._realtime_config.environment,
            capabilities=self._realtime_config.capabilities,
        )

    async def _heartbeat_loop(self) -> None:
        """
        Extended heartbeat loop with Realtime broadcast.

        Extends parent to also send heartbeats via Realtime.
        """
        logger.info("Heartbeat loop started (with Realtime)")

        while self._running:
            try:
                # Extend lease for all current jobs (parent behavior)
                for job_id, job in list(self._current_jobs.items()):
                    try:
                        success = await self._consumer.extend_lease(
                            job_id,
                            extension_seconds=self._realtime_config.visibility_timeout_seconds,
                        )
                        if not success:
                            logger.warning(
                                f"Failed to extend lease for job {job_id[:8]}"
                            )

                        # Also send heartbeat via Realtime
                        if self._realtime_client and self._realtime_connected:
                            await self._realtime_client.send_heartbeat(
                                job_id=job_id,
                                progress_percent=0,  # TODO: get from executor
                                current_node="executing",
                            )

                    except Exception as e:
                        logger.error(f"Heartbeat error for job {job_id[:8]}: {e}")

                await asyncio.sleep(self._realtime_config.heartbeat_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Heartbeat loop stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status including Realtime info."""
        status = super().get_status()

        # Add Realtime-specific status
        status["realtime"] = {
            "enabled": self._realtime_config.enable_realtime,
            "connected": self._realtime_connected,
            "client_status": (
                self._realtime_client.get_status() if self._realtime_client else None
            ),
        }
        status["paused"] = self._paused
        status["capabilities"] = self._realtime_config.capabilities

        return status


async def run_realtime_agent(
    config: Optional[RealtimeRobotConfig] = None,
) -> None:
    """
    Run the Realtime-enabled robot agent.

    Convenience function that creates an agent, runs it until
    interrupted, then shuts down gracefully.

    Args:
        config: Robot configuration (uses env vars if None)
    """
    if config is None:
        config = RealtimeRobotConfig.from_env()

    agent = RealtimeRobotAgent(config)

    try:
        await agent.start()

        # Wait for shutdown signal
        await agent._shutdown_event.wait()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await agent.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_realtime_agent())
