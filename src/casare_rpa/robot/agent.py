"""
Unified Robot Agent for CasareRPA.

Consolidates robot functionality into a single class with full lifecycle management:
- Job execution with DBOS durability
- Circuit breaker integration for failure handling
- Checkpoint management for crash recovery
- Metrics collection and reporting
- Audit logging
- Resource pooling (browser, DB, HTTP)

Architecture:
    +---------------------------+
    |       RobotAgent          |
    |   (Unified Coordinator)   |
    +-------------+-------------+
                  |
    +-------------v-------------+
    |     CircuitBreaker        |
    |   (Failure Protection)    |
    +-------------+-------------+
                  |
    +-------------v-------------+
    |   CheckpointManager       |
    |   (Crash Recovery)        |
    +-------------+-------------+
                  |
    +-------------v-------------+
    | UnifiedResourceManager    |
    |  (Browser/DB/HTTP Pool)   |
    +-------------+-------------+
                  |
    +-------------v-------------+
    |  DBOSWorkflowExecutor     |
    |   (Durable Execution)     |
    +---------------------------+
"""

from __future__ import annotations

import asyncio
import os
import signal
import socket
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger
import orjson

from casare_rpa.robot.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)
from casare_rpa.robot.metrics import MetricsCollector, get_metrics_collector
from casare_rpa.robot.audit import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    init_audit_logger,
)

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class AgentState(Enum):
    """Robot agent lifecycle state."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class RobotConfig:
    """
    Configuration for the unified robot agent.

    Consolidates all configuration from DistributedRobotConfig with
    circuit breaker and checkpoint settings.
    """

    # Identity
    robot_id: Optional[str] = None
    robot_name: Optional[str] = None
    hostname: str = field(default_factory=socket.gethostname)

    # Database connection
    postgres_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""

    # Environment
    environment: str = "default"
    tags: List[str] = field(default_factory=list)

    # Job execution
    batch_size: int = 1
    max_concurrent_jobs: int = 1
    job_timeout_seconds: int = 3600
    node_timeout_seconds: float = 120.0

    # Polling and timeouts
    poll_interval_seconds: float = 1.0
    subscribe_timeout_seconds: float = 5.0
    heartbeat_interval_seconds: float = 10.0
    presence_interval_seconds: float = 5.0
    visibility_timeout_seconds: int = 30
    graceful_shutdown_seconds: int = 60

    # Features
    enable_checkpointing: bool = True
    enable_realtime: bool = True
    enable_circuit_breaker: bool = True
    enable_audit_logging: bool = True

    # Resource pools
    browser_pool_size: int = 5
    db_pool_size: int = 10
    http_pool_size: int = 20

    # Circuit breaker
    circuit_breaker: CircuitBreakerConfig = field(
        default_factory=lambda: CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout=60.0,
            half_open_max_calls=3,
        )
    )

    # Checkpointing
    checkpoint_path: Path = field(
        default_factory=lambda: Path.home() / ".casare_rpa" / "checkpoints"
    )
    checkpoint_retention_count: int = 10

    # Logging
    log_dir: Path = field(default_factory=lambda: Path.home() / ".casare_rpa" / "logs")

    def __post_init__(self) -> None:
        """Initialize default values."""
        if not self.robot_id:
            self.robot_id = f"robot-{self.hostname}-{uuid.uuid4().hex[:8]}"
        if not self.robot_name:
            self.robot_name = f"Robot-{self.hostname}"

    @classmethod
    def from_env(cls) -> "RobotConfig":
        """Create configuration from environment variables."""
        tags_str = os.getenv("CASARE_ROBOT_TAGS", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        return cls(
            robot_id=os.getenv("CASARE_ROBOT_ID"),
            robot_name=os.getenv("CASARE_ROBOT_NAME"),
            postgres_url=os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "")),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_KEY", ""),
            environment=os.getenv("CASARE_ENVIRONMENT", "default"),
            batch_size=int(os.getenv("CASARE_BATCH_SIZE", "1")),
            poll_interval_seconds=float(os.getenv("CASARE_POLL_INTERVAL", "1.0")),
            heartbeat_interval_seconds=float(
                os.getenv("CASARE_HEARTBEAT_INTERVAL", "10.0")
            ),
            graceful_shutdown_seconds=int(os.getenv("CASARE_SHUTDOWN_GRACE", "60")),
            max_concurrent_jobs=int(os.getenv("CASARE_MAX_CONCURRENT_JOBS", "1")),
            job_timeout_seconds=int(os.getenv("CASARE_JOB_TIMEOUT", "3600")),
            enable_checkpointing=os.getenv(
                "CASARE_ENABLE_CHECKPOINTING", "true"
            ).lower()
            == "true",
            enable_realtime=os.getenv("CASARE_ENABLE_REALTIME", "true").lower()
            == "true",
            enable_circuit_breaker=os.getenv(
                "CASARE_ENABLE_CIRCUIT_BREAKER", "true"
            ).lower()
            == "true",
            browser_pool_size=int(os.getenv("CASARE_BROWSER_POOL_SIZE", "5")),
            db_pool_size=int(os.getenv("CASARE_DB_POOL_SIZE", "10")),
            http_pool_size=int(os.getenv("CASARE_HTTP_POOL_SIZE", "20")),
            tags=tags,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RobotConfig":
        """Create configuration from dictionary."""
        cb_data = data.pop("circuit_breaker", {})
        cb_config = (
            CircuitBreakerConfig(**cb_data) if cb_data else CircuitBreakerConfig()
        )

        config = cls(**data)
        config.circuit_breaker = cb_config
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (masks secrets)."""
        return {
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "hostname": self.hostname,
            "postgres_url": "***" if self.postgres_url else "",
            "supabase_url": self.supabase_url,
            "supabase_key": "***" if self.supabase_key else "",
            "environment": self.environment,
            "tags": self.tags,
            "batch_size": self.batch_size,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "job_timeout_seconds": self.job_timeout_seconds,
            "enable_checkpointing": self.enable_checkpointing,
            "enable_circuit_breaker": self.enable_circuit_breaker,
            "enable_audit_logging": self.enable_audit_logging,
            "log_dir": str(self.log_dir),
        }


@dataclass
class RobotCapabilities:
    """Robot capability advertisement for job routing."""

    platform: str
    browser_engines: List[str]
    desktop_automation: bool
    max_concurrent_jobs: int
    cpu_cores: int
    memory_gb: float
    tags: List[str]
    python_version: str = field(default_factory=lambda: sys.version.split()[0])
    hostname: str = field(default_factory=socket.gethostname)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AgentCheckpoint:
    """Agent-level checkpoint for crash recovery."""

    checkpoint_id: str
    robot_id: str
    state: str  # AgentState value
    current_jobs: List[str]
    created_at: str
    last_heartbeat: str
    stats: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCheckpoint":
        return cls(**data)


class RobotAgent:
    """
    Unified Robot Agent with full lifecycle management.

    Consolidates functionality from:
    - DistributedRobotAgent (job loop, registration, heartbeat)
    - CircuitBreaker (failure protection)
    - CheckpointManager (crash recovery)
    - MetricsCollector (performance tracking)
    - AuditLogger (structured logging)

    Usage:
        config = RobotConfig.from_env()
        agent = RobotAgent(config)

        await agent.start()
        # Agent runs until stopped
        await agent.stop()
    """

    def __init__(
        self,
        config: Optional[RobotConfig] = None,
        on_job_complete: Optional[Callable[[str, bool, Optional[str]], None]] = None,
    ) -> None:
        """
        Initialize unified robot agent.

        Args:
            config: Robot configuration (uses env vars if None)
            on_job_complete: Optional callback (job_id, success, error)
        """
        self.config = config or RobotConfig.from_env()
        self.robot_id = self.config.robot_id
        self.name = self.config.robot_name

        # State
        self._state = AgentState.STOPPED
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially

        # Job tracking
        self._current_jobs: Dict[str, Any] = {}
        self._job_progress: Dict[str, Dict[str, Any]] = {}
        self._cancelled_jobs: Set[str] = set()

        # Callbacks
        self._on_job_complete = on_job_complete

        # Capabilities
        self._capabilities = self._build_capabilities()

        # Circuit breaker
        self._circuit_breaker: Optional[CircuitBreaker] = None
        if self.config.enable_circuit_breaker:
            self._circuit_breaker = CircuitBreaker(
                name=f"robot-{self.robot_id}",
                config=self.config.circuit_breaker,
                on_state_change=self._on_circuit_state_change,
            )

        # Components (initialized on start)
        self._consumer = None
        self._executor = None
        self._resource_manager = None
        self._realtime_manager = None
        self._metrics: Optional[MetricsCollector] = None
        self._audit: Optional[AuditLogger] = None

        # Background tasks
        self._job_loop_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._presence_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "jobs_completed": 0,
            "jobs_failed": 0,
            "total_execution_time_ms": 0,
            "started_at": None,
            "circuit_breaker_opens": 0,
            "checkpoints_restored": 0,
        }

        # Checkpoint path
        self._checkpoint_file = (
            self.config.checkpoint_path / f"agent_{self.robot_id}.json"
        )

        self._init_logging()

    def _init_logging(self) -> None:
        """Initialize logging configuration."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(self.config.log_dir / "robot_{time}.log"),
            rotation="1 day",
            retention="7 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
        )

        # Initialize audit logger
        if self.config.enable_audit_logging:
            self._audit = init_audit_logger(
                robot_id=self.robot_id,
                log_dir=self.config.log_dir / "audit",
            )

    def _build_capabilities(self) -> RobotCapabilities:
        """Build robot capabilities from system info."""
        cpu_cores = os.cpu_count() or 1
        memory_gb = 0.0

        if PSUTIL_AVAILABLE:
            try:
                memory_gb = psutil.virtual_memory().total / (1024**3)
            except Exception:
                memory_gb = 4.0

        return RobotCapabilities(
            platform=sys.platform,
            browser_engines=["chromium", "firefox", "webkit"],
            desktop_automation=sys.platform == "win32",
            max_concurrent_jobs=self.config.max_concurrent_jobs,
            cpu_cores=cpu_cores,
            memory_gb=round(memory_gb, 2),
            tags=self.config.tags.copy(),
        )

    def _on_circuit_state_change(
        self, old_state: CircuitState, new_state: CircuitState
    ) -> None:
        """Handle circuit breaker state change."""
        logger.info(f"Circuit breaker: {old_state.value} -> {new_state.value}")

        if new_state == CircuitState.OPEN:
            self._stats["circuit_breaker_opens"] += 1

        if self._audit:
            self._audit.circuit_state_changed(
                circuit_name=f"robot-{self.robot_id}",
                new_state=new_state.value,
            )

    # ==================== LIFECYCLE ====================

    @property
    def state(self) -> AgentState:
        """Get current agent state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._state == AgentState.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if agent is paused."""
        return self._state == AgentState.PAUSED

    @property
    def current_job_count(self) -> int:
        """Get number of currently executing jobs."""
        return len(self._current_jobs)

    @property
    def connected(self) -> bool:
        """Check if connected to backend."""
        return self._consumer is not None and self._running

    @property
    def running(self) -> bool:
        """Alias for _running for backward compatibility."""
        return self._running

    async def start(self) -> None:
        """
        Start the robot agent.

        Establishes connections, restores from checkpoint if available,
        starts background tasks, and begins job loop.
        """
        if self._running:
            logger.warning("Agent already running")
            return

        self._state = AgentState.STARTING
        self._running = True
        self._shutdown_event.clear()
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Starting Robot Agent: {self.name} ({self.robot_id})")

        if self._audit:
            self._audit.robot_started(details=self.config.to_dict())

        # Restore from checkpoint if available
        await self._restore_from_checkpoint()

        # Initialize components
        await self._init_components()

        # Register with orchestrator
        await self._register()

        # Start background tasks
        self._job_loop_task = asyncio.create_task(self._job_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._presence_task = asyncio.create_task(self._presence_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())

        # Setup signal handlers
        self._setup_signal_handlers()

        self._state = AgentState.RUNNING

        logger.info(
            f"Robot Agent started: env={self.config.environment}, "
            f"max_concurrent={self.config.max_concurrent_jobs}"
        )

    async def stop(self) -> None:
        """
        Gracefully stop the robot agent.

        Waits for current jobs to complete (with timeout), saves checkpoint,
        then stops all background tasks and closes connections.
        """
        if not self._running:
            return

        logger.info(f"Stopping Robot Agent: {self.name}")
        self._state = AgentState.SHUTTING_DOWN
        self._running = False
        self._shutdown_event.set()

        if self._audit:
            self._audit.robot_stopped(reason="graceful_shutdown")

        # Wait for current jobs to complete
        if self._current_jobs:
            logger.info(
                f"Waiting for {len(self._current_jobs)} job(s) to complete "
                f"(max {self.config.graceful_shutdown_seconds}s)"
            )
            try:
                await asyncio.wait_for(
                    self._wait_for_jobs_complete(),
                    timeout=self.config.graceful_shutdown_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Graceful shutdown timed out, "
                    f"{len(self._current_jobs)} job(s) may be orphaned"
                )

        # Save checkpoint before stopping
        await self._save_checkpoint()

        # Cancel background tasks
        for task in [
            self._job_loop_task,
            self._heartbeat_task,
            self._presence_task,
            self._metrics_task,
        ]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Update registration
        await self._update_registration_status("offline")

        # Stop components
        await self._stop_components()

        self._state = AgentState.STOPPED

        logger.info(
            f"Robot Agent stopped. "
            f"Completed: {self._stats['jobs_completed']}, "
            f"Failed: {self._stats['jobs_failed']}"
        )

    async def pause(self) -> None:
        """Pause job acquisition (current jobs continue)."""
        if self._state != AgentState.RUNNING:
            logger.warning(f"Cannot pause from state {self._state.value}")
            return

        self._state = AgentState.PAUSED
        self._pause_event.clear()
        logger.info("Robot Agent paused")

        await self._update_registration_status("paused")

    async def resume(self) -> None:
        """Resume job acquisition."""
        if self._state != AgentState.PAUSED:
            logger.warning(f"Cannot resume from state {self._state.value}")
            return

        self._state = AgentState.RUNNING
        self._pause_event.set()
        logger.info("Robot Agent resumed")

        await self._update_registration_status("online")

    # ==================== INITIALIZATION ====================

    async def _init_components(self) -> None:
        """Initialize all agent components."""
        # Import here to avoid circular imports and allow lazy loading
        try:
            from casare_rpa.infrastructure.queue import PgQueuerConsumer, ConsumerConfig
            from casare_rpa.infrastructure.execution.dbos_executor import (
                DBOSWorkflowExecutor,
                DBOSExecutorConfig,
            )
            from casare_rpa.infrastructure.resources.unified_resource_manager import (
                UnifiedResourceManager,
            )

            # Initialize metrics collector
            self._metrics = get_metrics_collector()
            await self._metrics.start_resource_monitoring()

            # Initialize PgQueuer consumer
            if self.config.postgres_url:
                consumer_config = ConsumerConfig(
                    postgres_url=self.config.postgres_url,
                    robot_id=self.robot_id,
                    batch_size=self.config.batch_size,
                    visibility_timeout_seconds=self.config.visibility_timeout_seconds,
                    heartbeat_interval_seconds=self.config.heartbeat_interval_seconds,
                    environment=self.config.environment,
                )
                self._consumer = PgQueuerConsumer(consumer_config)
                await self._consumer.start()

            # Initialize DBOS executor
            executor_config = DBOSExecutorConfig(
                postgres_url=self.config.postgres_url
                if self.config.enable_checkpointing
                else None,
                enable_checkpointing=self.config.enable_checkpointing,
                execution_timeout_seconds=self.config.job_timeout_seconds,
                node_timeout_seconds=self.config.node_timeout_seconds,
            )
            self._executor = DBOSWorkflowExecutor(executor_config)
            await self._executor.start()

            # Initialize resource manager
            self._resource_manager = UnifiedResourceManager(
                browser_pool_size=self.config.browser_pool_size,
                db_pool_size=self.config.db_pool_size,
                http_pool_size=self.config.http_pool_size,
                postgres_url=self.config.postgres_url,
            )
            await self._resource_manager.start()

            if self._audit:
                self._audit.connection_established()

        except ImportError as e:
            logger.warning(f"Some components unavailable: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def _stop_components(self) -> None:
        """Stop all agent components."""
        if self._realtime_manager:
            try:
                await self._realtime_manager.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting realtime: {e}")

        if self._resource_manager:
            try:
                await self._resource_manager.stop()
            except Exception as e:
                logger.warning(f"Error stopping resource manager: {e}")

        if self._executor:
            try:
                await self._executor.stop()
            except Exception as e:
                logger.warning(f"Error stopping executor: {e}")

        if self._consumer:
            try:
                await self._consumer.stop()
            except Exception as e:
                logger.warning(f"Error stopping consumer: {e}")

        if self._metrics:
            try:
                await self._metrics.stop_resource_monitoring()
            except Exception as e:
                logger.warning(f"Error stopping metrics: {e}")

    # ==================== REGISTRATION ====================

    async def _register(self) -> None:
        """Register robot with orchestrator."""
        try:
            if (
                self._consumer
                and hasattr(self._consumer, "_pool")
                and self._consumer._pool
            ):
                async with self._consumer._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO robots (name, hostname, status, environment, capabilities, last_heartbeat, last_seen, created_at, updated_at)
                        VALUES ($1, $2, 'online', $3, $4::jsonb, NOW(), NOW(), NOW(), NOW())
                        ON CONFLICT (hostname) DO UPDATE
                        SET status = 'online',
                            capabilities = $4::jsonb,
                            last_heartbeat = NOW(),
                            last_seen = NOW(),
                            updated_at = NOW()
                        RETURNING robot_id
                        """,
                        self.name,
                        self.config.hostname,
                        self.config.environment,
                        orjson.dumps(self._capabilities.to_dict()).decode("utf-8"),
                    )

            logger.info(f"Robot registered: {self.robot_id}")

            if self._audit:
                self._audit.log(
                    AuditEventType.ROBOT_REGISTERED,
                    f"Robot registered: {self.robot_id}",
                    details={"capabilities": self._capabilities.to_dict()},
                )
        except Exception as e:
            logger.warning(f"Failed to register robot: {e}")

    async def _update_registration_status(self, status: str) -> None:
        """Update robot status in registry."""
        try:
            if (
                self._consumer
                and hasattr(self._consumer, "_pool")
                and self._consumer._pool
            ):
                async with self._consumer._pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE robots SET status = $2, last_seen = NOW(), updated_at = NOW()
                        WHERE hostname = $1
                        """,
                        self.config.hostname,
                        status,
                    )
        except Exception as e:
            logger.warning(f"Failed to update registration status: {e}")

    # ==================== JOB LOOP ====================

    async def _job_loop(self) -> None:
        """Main job acquisition and execution loop with circuit breaker."""
        logger.info("Job loop started")
        backoff_delay = self.config.poll_interval_seconds

        while self._running:
            try:
                # Wait if paused
                await self._pause_event.wait()

                # Check shutdown
                if not self._running:
                    break

                # Check capacity
                if self.current_job_count >= self.config.max_concurrent_jobs:
                    await asyncio.sleep(self.config.poll_interval_seconds)
                    continue

                # Check circuit breaker
                if self._circuit_breaker and self._circuit_breaker.is_open:
                    logger.debug("Circuit breaker open, waiting...")
                    await asyncio.sleep(self.config.poll_interval_seconds)
                    continue

                # Claim job
                job = None
                if self._consumer:
                    if self._circuit_breaker:
                        try:
                            job = await self._circuit_breaker.call(
                                self._consumer.claim_job
                            )
                        except CircuitBreakerOpenError:
                            await asyncio.sleep(self.config.poll_interval_seconds)
                            continue
                    else:
                        job = await self._consumer.claim_job()

                if job:
                    asyncio.create_task(self._execute_job_with_circuit_breaker(job))
                    backoff_delay = self.config.poll_interval_seconds
                else:
                    # Exponential backoff (max 2s)
                    await asyncio.sleep(backoff_delay)
                    backoff_delay = min(backoff_delay * 1.5, 2.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in job loop: {e}")
                await asyncio.sleep(5)

        logger.info("Job loop stopped")

    async def _execute_job_with_circuit_breaker(self, job: Any) -> None:
        """Execute job with circuit breaker protection."""
        job_id = job.job_id

        if self._circuit_breaker:
            try:
                await self._circuit_breaker.call(self._execute_job, job)
            except CircuitBreakerOpenError as e:
                logger.warning(f"Job {job_id[:8]} blocked by circuit breaker: {e}")
                # Release job back to queue
                if self._consumer:
                    await self._consumer.release_job(job_id)
            except Exception as e:
                logger.error(f"Job {job_id[:8]} failed with error: {e}")
        else:
            await self._execute_job(job)

    async def _execute_job(self, job: Any) -> None:
        """Execute a claimed job."""
        job_id = job.job_id
        self._current_jobs[job_id] = job
        self._job_progress[job_id] = {
            "progress_percent": 0,
            "current_node": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Executing job {job_id[:8]}: {job.workflow_name} "
            f"(priority={job.priority}, attempt={job.retry_count + 1})"
        )

        if self._audit:
            self._audit.job_started(job_id, total_nodes=0)

        await self._update_registration_status("busy")

        if self._metrics:
            self._metrics.start_job(job_id, job.workflow_name)

        try:
            # Check cancellation
            if job_id in self._cancelled_jobs:
                raise asyncio.CancelledError("Job cancelled by user")

            # Acquire resources
            resources = None
            if self._resource_manager:
                resources = await self._resource_manager.acquire_resources_for_job(
                    job_id, job.workflow_json
                )

            # Execute with DBOS
            result = await self._executor.execute_workflow(
                workflow_json=job.workflow_json,
                workflow_id=job_id,
                initial_variables=job.variables,
                wait_for_result=True,
                on_progress=lambda p, n: self._on_job_progress(job_id, p, n),
            )

            # Report result
            if result.success:
                await self._consumer.complete_job(
                    job_id,
                    {
                        "executed_nodes": result.executed_nodes,
                        "duration_ms": result.duration_ms,
                        "recovered": result.recovered,
                    },
                )
                self._stats["jobs_completed"] += 1
                self._stats["total_execution_time_ms"] += result.duration_ms

                if self._audit:
                    self._audit.job_completed(job_id, result.duration_ms)
                if self._metrics:
                    self._metrics.end_job(success=True)

                logger.info(
                    f"Job {job_id[:8]} completed successfully "
                    f"({result.executed_nodes} nodes, {result.duration_ms}ms)"
                )
            else:
                await self._consumer.fail_job(
                    job_id,
                    error_message=result.error or "Workflow execution failed",
                )
                self._stats["jobs_failed"] += 1

                if self._audit:
                    self._audit.job_failed(
                        job_id, result.error or "Unknown", result.duration_ms
                    )
                if self._metrics:
                    self._metrics.end_job(success=False, error_message=result.error)

                logger.warning(f"Job {job_id[:8]} failed: {result.error}")

            # Callback
            if self._on_job_complete:
                try:
                    self._on_job_complete(job_id, result.success, result.error)
                except Exception as e:
                    logger.error(f"Job complete callback error: {e}")

            # Release resources
            if resources and self._resource_manager:
                await self._resource_manager.release_resources(resources)

        except asyncio.CancelledError:
            logger.info(f"Job {job_id[:8]} was cancelled")
            if self._consumer:
                await self._consumer.fail_job(job_id, error_message="Job cancelled")
            self._stats["jobs_failed"] += 1

            if self._audit:
                self._audit.job_cancelled(job_id)

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Job {job_id[:8]} execution failed: {error_msg}")

            if self._consumer:
                await self._consumer.fail_job(job_id, error_message=error_msg)
            self._stats["jobs_failed"] += 1

            if self._audit:
                self._audit.job_failed(job_id, error_msg, 0)

            if self._on_job_complete:
                try:
                    self._on_job_complete(job_id, False, error_msg)
                except Exception as callback_error:
                    logger.error(f"Job complete callback error: {callback_error}")

        finally:
            self._current_jobs.pop(job_id, None)
            self._job_progress.pop(job_id, None)
            self._cancelled_jobs.discard(job_id)

            if not self._current_jobs:
                await self._update_registration_status("idle")

    async def _on_job_progress(self, job_id: str, progress: int, node_id: str) -> None:
        """Handle job progress update."""
        self._job_progress[job_id] = {
            "progress_percent": progress,
            "current_node": node_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            if self._consumer:
                await self._consumer.update_progress(job_id, progress, node_id)
        except Exception as e:
            logger.debug(f"Failed to update progress for {job_id}: {e}")

    async def _wait_for_jobs_complete(self) -> None:
        """Wait for all current jobs to complete."""
        while self._current_jobs:
            await asyncio.sleep(1)

    # ==================== BACKGROUND LOOPS ====================

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop for lease extension."""
        logger.info("Heartbeat loop started")

        while self._running:
            try:
                for job_id in list(self._current_jobs.keys()):
                    try:
                        if self._consumer:
                            success = await self._consumer.extend_lease(
                                job_id,
                                extension_seconds=self.config.visibility_timeout_seconds,
                            )
                            if not success:
                                logger.warning(
                                    f"Failed to extend lease for job {job_id[:8]}"
                                )
                    except Exception as e:
                        logger.error(f"Heartbeat error for job {job_id[:8]}: {e}")

                await asyncio.sleep(self.config.heartbeat_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Heartbeat loop stopped")

    async def _presence_loop(self) -> None:
        """Presence loop for load balancing."""
        logger.info("Presence loop started")

        while self._running:
            try:
                presence_data = {
                    "robot_id": self.robot_id,
                    "status": "busy" if self._current_jobs else "idle",
                    "current_job_count": len(self._current_jobs),
                    "max_concurrent_jobs": self.config.max_concurrent_jobs,
                    "environment": self.config.environment,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                if PSUTIL_AVAILABLE:
                    try:
                        presence_data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                        presence_data["memory_percent"] = (
                            psutil.virtual_memory().percent
                        )
                    except Exception:
                        pass

                await self._update_presence_in_db(presence_data)

                await asyncio.sleep(self.config.presence_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Presence loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Presence loop stopped")

    async def _update_presence_in_db(self, presence_data: Dict[str, Any]) -> None:
        """Update presence in database."""
        try:
            if (
                self._consumer
                and hasattr(self._consumer, "_pool")
                and self._consumer._pool
            ):
                async with self._consumer._pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE robots
                        SET status = $2,
                            last_seen = NOW(),
                            metrics = $3
                        WHERE hostname = $1
                        """,
                        self.config.hostname,
                        presence_data.get("status", "idle"),
                        orjson.dumps(
                            {
                                "cpu_percent": presence_data.get("cpu_percent"),
                                "memory_percent": presence_data.get("memory_percent"),
                                "current_job_count": presence_data.get(
                                    "current_job_count", 0
                                ),
                            }
                        ).decode("utf-8"),
                    )
        except Exception as e:
            logger.debug(f"Failed to update presence in DB: {e}")

    async def _metrics_loop(self) -> None:
        """Periodic metrics collection loop."""
        logger.info("Metrics loop started")

        while self._running:
            try:
                # Save checkpoint periodically
                if self.config.enable_checkpointing:
                    await self._save_checkpoint()

                await asyncio.sleep(60)  # Every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(60)

        logger.info("Metrics loop stopped")

    # ==================== CHECKPOINT ====================

    async def _save_checkpoint(self) -> None:
        """Save agent checkpoint for crash recovery."""
        try:
            self.config.checkpoint_path.mkdir(parents=True, exist_ok=True)

            checkpoint = AgentCheckpoint(
                checkpoint_id=uuid.uuid4().hex[:8],
                robot_id=self.robot_id,
                state=self._state.value,
                current_jobs=list(self._current_jobs.keys()),
                created_at=datetime.now(timezone.utc).isoformat(),
                last_heartbeat=datetime.now(timezone.utc).isoformat(),
                stats=self._stats.copy(),
            )

            self._checkpoint_file.write_bytes(
                orjson.dumps(checkpoint.to_dict(), option=orjson.OPT_INDENT_2)
            )

            # Prune old checkpoints
            await self._prune_checkpoints()

        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    async def _restore_from_checkpoint(self) -> None:
        """Restore agent state from checkpoint."""
        if not self._checkpoint_file.exists():
            return

        try:
            data = orjson.loads(self._checkpoint_file.read_bytes())
            checkpoint = AgentCheckpoint.from_dict(data)

            # Restore stats
            self._stats = checkpoint.stats
            self._stats["checkpoints_restored"] += 1

            logger.info(
                f"Restored from checkpoint {checkpoint.checkpoint_id} "
                f"(jobs_completed={self._stats['jobs_completed']})"
            )

            if self._audit:
                self._audit.log(
                    AuditEventType.CHECKPOINT_RESTORED,
                    f"Restored from checkpoint {checkpoint.checkpoint_id}",
                    details={"checkpoint": checkpoint.to_dict()},
                )

        except Exception as e:
            logger.warning(f"Failed to restore from checkpoint: {e}")

    async def _prune_checkpoints(self) -> None:
        """Remove old checkpoint files."""
        try:
            checkpoints = sorted(
                self.config.checkpoint_path.glob("agent_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

            for old_file in checkpoints[self.config.checkpoint_retention_count :]:
                try:
                    old_file.unlink()
                except Exception:
                    pass
        except Exception:
            pass

    # ==================== SIGNAL HANDLING ====================

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            loop = asyncio.get_running_loop()

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self._handle_signal()),
                )
        except (NotImplementedError, RuntimeError):
            # Windows doesn't support add_signal_handler
            logger.debug("Signal handlers not available on this platform")

    async def _handle_signal(self) -> None:
        """Handle shutdown signal."""
        logger.info("Received shutdown signal")
        await self.stop()

    # ==================== STATUS ====================

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        status = {
            "robot_id": self.robot_id,
            "robot_name": self.name,
            "state": self._state.value,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "environment": self.config.environment,
            "current_job_count": self.current_job_count,
            "max_concurrent_jobs": self.config.max_concurrent_jobs,
            "capabilities": self._capabilities.to_dict(),
            "current_jobs": [
                {
                    "job_id": job_id,
                    "progress": self._job_progress.get(job_id, {}),
                }
                for job_id in self._current_jobs.keys()
            ],
            "stats": self._stats,
        }

        # Circuit breaker status
        if self._circuit_breaker:
            status["circuit_breaker"] = self._circuit_breaker.get_status()

        # Resource metrics
        if PSUTIL_AVAILABLE:
            try:
                status["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                status["memory_percent"] = psutil.virtual_memory().percent
            except Exception:
                pass

        return status

    def cancel_job(self, job_id: str) -> bool:
        """Request cancellation of a job."""
        if job_id in self._current_jobs:
            self._cancelled_jobs.add(job_id)
            logger.info(f"Cancellation requested for job {job_id[:8]}")
            return True
        return False


async def run_agent(config: Optional[RobotConfig] = None) -> None:
    """
    Run the robot agent.

    Convenience function that creates an agent, runs it until
    interrupted, then shuts down gracefully.

    Args:
        config: Robot configuration (uses env vars if None)
    """
    if config is None:
        config = RobotConfig.from_env()

    agent = RobotAgent(config)

    try:
        await agent.start()
        await agent._shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(run_agent())
