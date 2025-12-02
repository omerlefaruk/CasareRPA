"""
Robot Agent - Main Entry Point for Robot Workers.

Connects to orchestrator via WebSocket, accepts job assignments,
executes workflows, and reports results. Handles reconnection
and graceful shutdown.
"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from .robot_config import RobotConfig
from .heartbeat_service import HeartbeatService
from .job_executor import JobExecutor


class RobotAgentError(Exception):
    """Base exception for robot agent errors."""

    pass


class RobotAgent:
    """
    Main robot agent that connects to orchestrator and executes jobs.

    Features:
    - Secure WebSocket connection (optional mTLS)
    - Automatic reconnection with exponential backoff
    - Concurrent job execution (configurable limit)
    - Heartbeat monitoring with system metrics
    - Graceful shutdown with job completion
    - Progress reporting to orchestrator

    Usage:
        config = RobotConfig.from_env()
        agent = RobotAgent(config)
        await agent.start()  # Runs until stopped
    """

    def __init__(self, config: RobotConfig):
        """
        Initialize robot agent.

        Args:
            config: Robot configuration
        """
        self.config = config

        # Components
        self.executor = JobExecutor(
            progress_callback=self._on_job_progress,
            continue_on_error=config.continue_on_error,
            job_timeout=config.job_timeout,
        )
        self.heartbeat = HeartbeatService(
            interval=config.heartbeat_interval,
            on_heartbeat=self._send_heartbeat,
            on_failure=self._on_heartbeat_failure,
        )

        # WebSocket connection
        self._ws: Optional[Any] = None
        self._running = False
        self._connected = False
        self._registered = False

        # Job tracking
        self._current_jobs: Dict[str, asyncio.Task] = {}
        self._job_semaphore = asyncio.Semaphore(config.max_concurrent_jobs)

        # Reconnection state
        self._reconnect_delay = config.reconnect_delay
        self._reconnect_count = 0

        # Metrics
        self._connected_at: Optional[datetime] = None
        self._jobs_completed = 0
        self._jobs_failed = 0

        # Event callbacks
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_job_started: Optional[Callable[[str], None]] = None
        self.on_job_completed: Optional[Callable[[str, bool], None]] = None

    async def start(self) -> None:
        """
        Start the robot agent.

        Connects to orchestrator and begins accepting jobs.
        Runs indefinitely with automatic reconnection.
        """
        if self._running:
            logger.warning("Robot agent already running")
            return

        self._running = True
        logger.info(
            f"Starting robot agent: {self.config.robot_name} "
            f"(ID: {self.config.robot_id})"
        )
        logger.info(f"Control plane: {self.config.control_plane_url}")
        logger.info(f"Capabilities: {', '.join(self.config.capabilities)}")
        logger.info(f"Max concurrent jobs: {self.config.max_concurrent_jobs}")

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Main loop with reconnection
        while self._running:
            try:
                await self._connect_and_run()
            except Exception as e:
                logger.error(f"Connection error: {e}")

            if self._running:
                # Exponential backoff for reconnection
                logger.info(f"Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * self.config.reconnect_multiplier,
                    self.config.max_reconnect_delay,
                )
                self._reconnect_count += 1

    async def stop(self, wait_for_jobs: bool = True) -> None:
        """
        Stop the robot agent gracefully.

        Args:
            wait_for_jobs: Wait for running jobs to complete (default: True)
        """
        logger.info("Stopping robot agent...")
        self._running = False

        # Wait for running jobs to complete
        if wait_for_jobs and self._current_jobs:
            logger.info(f"Waiting for {len(self._current_jobs)} jobs to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        *self._current_jobs.values(), return_exceptions=True
                    ),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for jobs, forcing shutdown")

        # Stop heartbeat
        await self.heartbeat.stop()

        # Close WebSocket
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            self._ws = None

        self._connected = False
        self._registered = False

        logger.info(
            f"Robot agent stopped. "
            f"Jobs completed: {self._jobs_completed}, Failed: {self._jobs_failed}"
        )

    async def _connect_and_run(self) -> None:
        """Connect to orchestrator and run message loop."""
        try:
            import websockets

            # Build connection kwargs
            connect_kwargs = {
                "ping_interval": 20,
                "ping_timeout": 10,
                "close_timeout": 5,
            }

            # Build extra headers for authentication
            extra_headers = {}
            if self.config.uses_api_key:
                extra_headers["X-Api-Key"] = self.config.api_key
                logger.info("Using API key authentication")

            if extra_headers:
                connect_kwargs["extra_headers"] = extra_headers

            # Configure SSL if using mTLS
            if self.config.uses_mtls:
                from ..tunnel.mtls import MTLSConfig

                mtls = MTLSConfig(
                    ca_cert_path=self.config.ca_cert_path,
                    client_cert_path=self.config.client_cert_path,
                    client_key_path=self.config.client_key_path,
                    verify_server=self.config.verify_ssl,
                )
                connect_kwargs["ssl"] = mtls.create_ssl_context()
                logger.info("Using mTLS authentication")
            elif self.config.control_plane_url.startswith("wss://"):
                import ssl

                # Use default SSL context without client auth
                ssl_ctx = ssl.create_default_context()
                if not self.config.verify_ssl:
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode = ssl.CERT_NONE
                    logger.warning("SSL verification disabled - NOT RECOMMENDED")
                connect_kwargs["ssl"] = ssl_ctx

            # Connect
            logger.info("Connecting to orchestrator...")
            self._ws = await websockets.connect(
                self.config.control_plane_url,
                **connect_kwargs,
            )

            self._connected = True
            self._connected_at = datetime.now(timezone.utc)
            self._reconnect_delay = self.config.reconnect_delay  # Reset backoff

            logger.info("Connected to orchestrator")

            if self.on_connected:
                self.on_connected()

            # Register with orchestrator
            await self._register()

            # Start heartbeat
            await self.heartbeat.start()

            # Message loop
            await self._message_loop()

        except websockets.ConnectionClosed as e:
            logger.warning(f"Connection closed: code={e.code}, reason={e.reason}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
        finally:
            self._connected = False
            self._registered = False

            await self.heartbeat.stop()

            if self.on_disconnected:
                self.on_disconnected()

    async def _register(self) -> None:
        """Register with orchestrator."""
        logger.info("Registering with orchestrator...")

        message = {
            "type": "register",
            "robot_id": self.config.robot_id,
            "robot_name": self.config.robot_name,
            "capabilities": {
                "types": self.config.capabilities,
                "max_concurrent_jobs": self.config.max_concurrent_jobs,
                "tags": self.config.tags,
                "os_info": self.config.os_info,
                "hostname": self.config.hostname,
            },
            "environment": self.config.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Include API key hash for server-side validation (not the raw key)
        # The raw key is sent via header during connection
        if self.config.uses_api_key:
            import hashlib

            key_hash = hashlib.sha256(self.config.api_key.encode()).hexdigest()
            message["api_key_hash"] = key_hash

        await self._send(message)

    async def _send(self, message: Dict[str, Any]) -> None:
        """Send message to orchestrator."""
        if not self._ws:
            raise RobotAgentError("Not connected")

        await self._ws.send(json.dumps(message))
        logger.debug(f"Sent: {message.get('type', 'unknown')}")

    async def _message_loop(self) -> None:
        """Main message receive loop."""
        while self._running and self._ws:
            try:
                raw_message = await self._ws.recv()
                message = json.loads(raw_message)
                await self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message handling error: {e}")

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message from orchestrator."""
        msg_type = message.get("type", "")
        logger.debug(f"Received: {msg_type}")

        handlers = {
            "register_ack": self._handle_register_ack,
            "heartbeat_ack": self._handle_heartbeat_ack,
            "job_assign": self._handle_job_assign,
            "job_cancel": self._handle_job_cancel,
            "error": self._handle_error,
            "ping": self._handle_ping,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(message)
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_register_ack(self, message: Dict[str, Any]) -> None:
        """Handle registration acknowledgement."""
        self._registered = True
        logger.info(
            f"Registered with orchestrator as: {self.config.robot_name} "
            f"({self.config.robot_id})"
        )

    async def _handle_heartbeat_ack(self, message: Dict[str, Any]) -> None:
        """Handle heartbeat acknowledgement."""
        logger.debug("Heartbeat acknowledged")

    async def _handle_job_assign(self, message: Dict[str, Any]) -> None:
        """Handle job assignment from orchestrator."""
        job_id = message.get("job_id")
        workflow_name = message.get("workflow_name", "Unknown")

        logger.info(f"Job assigned: {job_id} ({workflow_name})")

        # Check capacity
        if len(self._current_jobs) >= self.config.max_concurrent_jobs:
            logger.warning(f"At capacity, rejecting job: {job_id}")
            await self._send(
                {
                    "type": "job_reject",
                    "job_id": job_id,
                    "robot_id": self.config.robot_id,
                    "reason": "At maximum capacity",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            return

        # Accept job
        await self._send(
            {
                "type": "job_accept",
                "job_id": job_id,
                "robot_id": self.config.robot_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Execute job in background
        task = asyncio.create_task(self._execute_job(message))
        self._current_jobs[job_id] = task

        if self.on_job_started:
            self.on_job_started(job_id)

    async def _handle_job_cancel(self, message: Dict[str, Any]) -> None:
        """Handle job cancellation request."""
        job_id = message.get("job_id")
        logger.info(f"Job cancellation requested: {job_id}")

        if job_id in self._current_jobs:
            self._current_jobs[job_id].cancel()
            await self._send(
                {
                    "type": "job_cancelled",
                    "job_id": job_id,
                    "robot_id": self.config.robot_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            logger.warning(f"Job not found for cancellation: {job_id}")

    async def _handle_error(self, message: Dict[str, Any]) -> None:
        """Handle error message from orchestrator."""
        error_msg = message.get("message", "Unknown error")
        error_code = message.get("code", "UNKNOWN")
        logger.error(f"Orchestrator error [{error_code}]: {error_msg}")

    async def _handle_ping(self, message: Dict[str, Any]) -> None:
        """Handle ping message."""
        await self._send(
            {
                "type": "pong",
                "robot_id": self.config.robot_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _execute_job(self, job_data: Dict[str, Any]) -> None:
        """Execute a job and report results."""
        job_id = job_data.get("job_id", "unknown")

        async with self._job_semaphore:
            try:
                # Execute workflow
                result = await self.executor.execute(job_data)

                # Report completion
                if result.get("success"):
                    await self._send(
                        {
                            "type": "job_complete",
                            "job_id": job_id,
                            "robot_id": self.config.robot_id,
                            "result": result,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    self._jobs_completed += 1
                else:
                    await self._send(
                        {
                            "type": "job_failed",
                            "job_id": job_id,
                            "robot_id": self.config.robot_id,
                            "error": result.get("error", "Execution failed"),
                            "details": result,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    self._jobs_failed += 1

                if self.on_job_completed:
                    self.on_job_completed(job_id, result.get("success", False))

            except asyncio.CancelledError:
                logger.info(f"Job cancelled: {job_id}")
                await self._send(
                    {
                        "type": "job_cancelled",
                        "job_id": job_id,
                        "robot_id": self.config.robot_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            except Exception as e:
                logger.exception(f"Job execution error: {job_id}")
                await self._send(
                    {
                        "type": "job_failed",
                        "job_id": job_id,
                        "robot_id": self.config.robot_id,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                self._jobs_failed += 1

            finally:
                # Remove from active jobs
                self._current_jobs.pop(job_id, None)

    async def _on_job_progress(self, job_id: str, progress: int, message: str) -> None:
        """Report job progress to orchestrator."""
        if self._ws and self._connected:
            try:
                await self._send(
                    {
                        "type": "job_progress",
                        "job_id": job_id,
                        "robot_id": self.config.robot_id,
                        "progress": progress,
                        "message": message,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send progress for {job_id}: {e}")

    async def _send_heartbeat(self, heartbeat_data: Dict[str, Any]) -> None:
        """Send heartbeat message to orchestrator."""
        if not self._ws or not self._connected:
            return

        message = {
            "type": "heartbeat",
            "robot_id": self.config.robot_id,
            "current_jobs": list(self._current_jobs.keys()),
            "jobs_completed": self._jobs_completed,
            "jobs_failed": self._jobs_failed,
            **heartbeat_data,
        }

        await self._send(message)

    def _on_heartbeat_failure(self, error: Exception) -> None:
        """Handle heartbeat failure."""
        logger.warning(f"Heartbeat failure: {error}")
        # Could trigger reconnection if needed

    def _setup_signal_handlers(self) -> None:
        """Set up OS signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self.stop()),
                )
        else:
            # Windows doesn't support add_signal_handler
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle signals on Windows."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._running

    @property
    def is_connected(self) -> bool:
        """Check if agent is connected to orchestrator."""
        return self._connected

    @property
    def is_registered(self) -> bool:
        """Check if agent is registered with orchestrator."""
        return self._registered

    @property
    def active_job_count(self) -> int:
        """Get count of currently executing jobs."""
        return len(self._current_jobs)

    @property
    def active_job_ids(self) -> List[str]:
        """Get list of active job IDs."""
        return list(self._current_jobs.keys())

    def get_status(self) -> Dict[str, Any]:
        """Get agent status summary."""
        return {
            "robot_id": self.config.robot_id,
            "robot_name": self.config.robot_name,
            "running": self._running,
            "connected": self._connected,
            "registered": self._registered,
            "connected_at": self._connected_at.isoformat()
            if self._connected_at
            else None,
            "active_jobs": len(self._current_jobs),
            "active_job_ids": list(self._current_jobs.keys()),
            "max_concurrent_jobs": self.config.max_concurrent_jobs,
            "jobs_completed": self._jobs_completed,
            "jobs_failed": self._jobs_failed,
            "reconnect_count": self._reconnect_count,
            "heartbeat": self.heartbeat.get_status(),
        }
