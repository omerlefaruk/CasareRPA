"""
Distributed Robot Agent for CasareRPA.

Enhanced robot agent for distributed execution with:
- Robot registration with capability advertisement
- Hybrid poll + subscribe job loop using Supabase Realtime
- Resource pooling integration via UnifiedResourceManager
- Presence loop for load balancing
- Enhanced heartbeat with progress tracking and CPU/memory metrics
- State affinity management for workflows with local state
- Graceful shutdown and proper telemetry

Architecture:
    +-----------------------+
    |  DistributedRobotAgent|
    |  (Coordination Hub)   |
    +----------+------------+
               |
    +----------v------------+
    | Hybrid Job Loop       |
    | (Poll + Realtime)     |
    +----------+------------+
               |
    +----------v------------+
    | UnifiedResourceManager|
    | (Browser/DB/HTTP Pool)|
    +----------+------------+
               |
    +----------v------------+
    | DBOSWorkflowExecutor  |
    | (Durable Execute)     |
    +----------+------------+
               |
    +----------v------------+
    | Heartbeat + Presence  |
    | (Lease + Load Balance)|
    +-----------------------+
"""

from __future__ import annotations

import asyncio
import os
import signal
import socket
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger
import orjson

from casare_rpa.infrastructure.queue import (
    PgQueuerConsumer,
    ClaimedJob,
    ConsumerConfig,
    ConnectionState,
)
from casare_rpa.infrastructure.execution.dbos_executor import (
    DBOSWorkflowExecutor,
    DBOSExecutorConfig,
)
from casare_rpa.infrastructure.resources.unified_resource_manager import (
    UnifiedResourceManager,
    JobResources,
)
from casare_rpa.robot.metrics import MetricsCollector, get_metrics_collector

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, resource monitoring limited")

try:
    from supabase import create_client, Client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.debug("Supabase client not available")


class AgentState(Enum):
    """Robot agent lifecycle state."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class RobotCapabilities:
    """
    Robot capability advertisement.

    Describes what this robot can execute for intelligent job routing.
    """

    platform: str  # "win32", "linux", "darwin"
    browser_engines: List[str]  # ["chromium", "firefox", "webkit"]
    desktop_automation: bool  # Windows UIAutomation support
    max_concurrent_jobs: int
    cpu_cores: int
    memory_gb: float
    tags: List[str]  # ["gpu", "high-memory", "sap-certified"]
    python_version: str = field(default_factory=lambda: sys.version.split()[0])
    hostname: str = field(default_factory=socket.gethostname)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RobotRegistration:
    """Robot registration payload for orchestrator."""

    robot_id: str
    hostname: str
    capabilities: RobotCapabilities
    heartbeat_interval_seconds: int = 10
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "robot_id": self.robot_id,
            "hostname": self.hostname,
            "capabilities": self.capabilities.to_dict(),
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "registered_at": self.registered_at,
        }


@dataclass
class StateAffinity:
    """
    State affinity tracking for workflows that maintain local state.

    Some workflows need to run on the same robot (e.g., browser sessions).
    """

    workflow_id: str
    robot_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    state_keys: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if affinity has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class DistributedRobotConfig:
    """
    Configuration for distributed robot agent.

    Attributes:
        robot_id: Unique identifier for this robot (auto-generated if None)
        robot_name: Human-readable robot name
        postgres_url: PostgreSQL connection string
        supabase_url: Supabase URL for realtime
        supabase_key: Supabase API key
        environment: Environment/pool name for job filtering
        batch_size: Jobs to claim at once (1 = single-threaded)
        poll_interval_seconds: Time between poll attempts
        heartbeat_interval_seconds: Time between heartbeat pulses
        presence_interval_seconds: Time between presence updates
        visibility_timeout_seconds: Job lease duration
        graceful_shutdown_seconds: Max wait time for current job on shutdown
        max_concurrent_jobs: Maximum concurrent job executions
        job_timeout_seconds: Maximum job execution time
        node_timeout_seconds: Maximum node execution time
        enable_checkpointing: Enable DBOS-style checkpointing
        enable_realtime: Enable Supabase Realtime subscriptions
        browser_pool_size: Max browser contexts
        db_pool_size: Max database connections
        http_pool_size: Max HTTP sessions
        tags: Capability tags for job routing
        log_dir: Directory for log files
    """

    robot_id: Optional[str] = None
    robot_name: Optional[str] = None
    postgres_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    environment: str = "default"
    batch_size: int = 1
    poll_interval_seconds: float = 1.0
    subscribe_timeout_seconds: float = 5.0
    heartbeat_interval_seconds: float = 10.0
    presence_interval_seconds: float = 5.0
    visibility_timeout_seconds: int = 30
    graceful_shutdown_seconds: int = 60
    max_concurrent_jobs: int = 1
    job_timeout_seconds: int = 3600
    node_timeout_seconds: float = 120.0
    enable_checkpointing: bool = True
    enable_realtime: bool = True
    browser_pool_size: int = 5
    db_pool_size: int = 10
    http_pool_size: int = 20
    tags: List[str] = field(default_factory=list)
    log_dir: Path = field(default_factory=lambda: Path.home() / ".casare_rpa" / "logs")

    def __post_init__(self) -> None:
        """Initialize default values."""
        if not self.robot_id:
            self.robot_id = f"robot-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        if not self.robot_name:
            self.robot_name = f"Robot-{socket.gethostname()}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DistributedRobotConfig":
        """Create configuration from dictionary."""
        return cls(
            robot_id=data.get("robot_id"),
            robot_name=data.get("robot_name"),
            postgres_url=data.get("postgres_url", ""),
            supabase_url=data.get("supabase_url", ""),
            supabase_key=data.get("supabase_key", ""),
            environment=data.get("environment", "default"),
            batch_size=data.get("batch_size", 1),
            poll_interval_seconds=data.get("poll_interval_seconds", 1.0),
            subscribe_timeout_seconds=data.get("subscribe_timeout_seconds", 5.0),
            heartbeat_interval_seconds=data.get("heartbeat_interval_seconds", 10.0),
            presence_interval_seconds=data.get("presence_interval_seconds", 5.0),
            visibility_timeout_seconds=data.get("visibility_timeout_seconds", 30),
            graceful_shutdown_seconds=data.get("graceful_shutdown_seconds", 60),
            max_concurrent_jobs=data.get("max_concurrent_jobs", 1),
            job_timeout_seconds=data.get("job_timeout_seconds", 3600),
            node_timeout_seconds=data.get("node_timeout_seconds", 120.0),
            enable_checkpointing=data.get("enable_checkpointing", True),
            enable_realtime=data.get("enable_realtime", True),
            browser_pool_size=data.get("browser_pool_size", 5),
            db_pool_size=data.get("db_pool_size", 10),
            http_pool_size=data.get("http_pool_size", 20),
            tags=data.get("tags", []),
            log_dir=Path(
                data.get("log_dir", str(Path.home() / ".casare_rpa" / "logs"))
            ),
        )

    @classmethod
    def from_env(cls) -> "DistributedRobotConfig":
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
            subscribe_timeout_seconds=float(
                os.getenv("CASARE_SUBSCRIBE_TIMEOUT", "5.0")
            ),
            heartbeat_interval_seconds=float(
                os.getenv("CASARE_HEARTBEAT_INTERVAL", "10.0")
            ),
            presence_interval_seconds=float(
                os.getenv("CASARE_PRESENCE_INTERVAL", "5.0")
            ),
            visibility_timeout_seconds=int(
                os.getenv("CASARE_VISIBILITY_TIMEOUT", "30")
            ),
            graceful_shutdown_seconds=int(os.getenv("CASARE_SHUTDOWN_GRACE", "60")),
            max_concurrent_jobs=int(os.getenv("CASARE_MAX_CONCURRENT_JOBS", "1")),
            job_timeout_seconds=int(os.getenv("CASARE_JOB_TIMEOUT", "3600")),
            node_timeout_seconds=float(os.getenv("CASARE_NODE_TIMEOUT", "120.0")),
            enable_checkpointing=os.getenv(
                "CASARE_ENABLE_CHECKPOINTING", "true"
            ).lower()
            == "true",
            enable_realtime=os.getenv("CASARE_ENABLE_REALTIME", "true").lower()
            == "true",
            browser_pool_size=int(os.getenv("CASARE_BROWSER_POOL_SIZE", "5")),
            db_pool_size=int(os.getenv("CASARE_DB_POOL_SIZE", "10")),
            http_pool_size=int(os.getenv("CASARE_HTTP_POOL_SIZE", "20")),
            tags=tags,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (masks secrets)."""
        return {
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "postgres_url": "***" if self.postgres_url else "",
            "supabase_url": self.supabase_url,
            "supabase_key": "***" if self.supabase_key else "",
            "environment": self.environment,
            "batch_size": self.batch_size,
            "poll_interval_seconds": self.poll_interval_seconds,
            "subscribe_timeout_seconds": self.subscribe_timeout_seconds,
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "presence_interval_seconds": self.presence_interval_seconds,
            "visibility_timeout_seconds": self.visibility_timeout_seconds,
            "graceful_shutdown_seconds": self.graceful_shutdown_seconds,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "job_timeout_seconds": self.job_timeout_seconds,
            "node_timeout_seconds": self.node_timeout_seconds,
            "enable_checkpointing": self.enable_checkpointing,
            "enable_realtime": self.enable_realtime,
            "browser_pool_size": self.browser_pool_size,
            "db_pool_size": self.db_pool_size,
            "http_pool_size": self.http_pool_size,
            "tags": self.tags,
            "log_dir": str(self.log_dir),
        }


class RealtimeChannelManager:
    """
    Manages Supabase Realtime channel subscriptions.

    Handles:
    - Jobs CDC channel (postgres_changes for job inserts)
    - Control broadcast channel (cancel_job, shutdown commands)
    - Presence channel (robot health tracking)
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        robot_id: str,
        environment: str = "default",
    ) -> None:
        """
        Initialize realtime channel manager.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            robot_id: Robot identifier
            environment: Job environment filter
        """
        self._url = supabase_url
        self._key = supabase_key
        self._robot_id = robot_id
        self._environment = environment

        self._client: Optional[Client] = None
        self._channels: Dict[str, Any] = {}
        self._subscribed = False
        self._job_notification_event = asyncio.Event()

        # Callbacks
        self._on_job_inserted: Optional[Callable[[Dict], None]] = None
        self._on_cancel_job: Optional[Callable[[str], None]] = None
        self._on_shutdown: Optional[Callable[[], None]] = None

    async def connect(self) -> bool:
        """
        Connect to Supabase and setup channels.

        Returns:
            True if connected successfully
        """
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase client not available, realtime disabled")
            return False

        if not self._url or not self._key:
            logger.warning("Supabase credentials not configured")
            return False

        try:
            self._client = create_client(self._url, self._key)
            await self._setup_channels()
            self._subscribed = True
            logger.info("Connected to Supabase Realtime")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase Realtime: {e}")
            return False

    async def _setup_channels(self) -> None:
        """Setup all realtime channels."""
        if not self._client:
            return

        # Jobs CDC channel - Postgres Changes
        try:
            jobs_channel = self._client.channel("jobs")

            def on_job_insert(payload: Dict) -> None:
                """Handle job insert notification."""
                logger.debug(f"Realtime job notification: {payload}")
                self._job_notification_event.set()
                if self._on_job_inserted:
                    try:
                        self._on_job_inserted(payload)
                    except Exception as e:
                        logger.error(f"Job insert callback error: {e}")

            jobs_channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="job_queue",
                callback=on_job_insert,
            )

            await jobs_channel.subscribe()
            self._channels["jobs"] = jobs_channel
            logger.info("Subscribed to jobs CDC channel")
        except Exception as e:
            logger.warning(f"Failed to setup jobs channel: {e}")

        # Control broadcast channel
        try:
            control_channel = self._client.channel("control")

            def on_broadcast(payload: Dict) -> None:
                """Handle control broadcast."""
                event = payload.get("event")
                data = payload.get("payload", {})

                logger.debug(f"Control broadcast: {event}")

                if event == "cancel_job" and self._on_cancel_job:
                    job_id = data.get("job_id")
                    if job_id:
                        self._on_cancel_job(job_id)
                elif event == "shutdown" and self._on_shutdown:
                    target_robot = data.get("robot_id")
                    if not target_robot or target_robot == self._robot_id:
                        self._on_shutdown()

            control_channel.on_broadcast(event="*", callback=on_broadcast)

            await control_channel.subscribe()
            self._channels["control"] = control_channel
            logger.info("Subscribed to control broadcast channel")
        except Exception as e:
            logger.warning(f"Failed to setup control channel: {e}")

        # Presence channel for robots
        try:
            presence_channel = self._client.channel("robots")
            await presence_channel.subscribe()
            self._channels["robots"] = presence_channel
            logger.info("Subscribed to robots presence channel")
        except Exception as e:
            logger.warning(f"Failed to setup presence channel: {e}")

    async def wait_for_job_notification(self, timeout: float) -> bool:
        """
        Wait for job notification with timeout.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if notification received, False on timeout
        """
        self._job_notification_event.clear()
        try:
            await asyncio.wait_for(self._job_notification_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def track_presence(self, presence_data: Dict[str, Any]) -> None:
        """
        Update robot presence.

        Args:
            presence_data: Presence payload
        """
        presence_channel = self._channels.get("robots")
        if presence_channel:
            try:
                await presence_channel.track(presence_data)
            except Exception as e:
                logger.debug(f"Presence track error: {e}")

    async def send_heartbeat(self, heartbeat_data: Dict[str, Any]) -> None:
        """
        Send heartbeat via broadcast.

        Args:
            heartbeat_data: Heartbeat payload
        """
        heartbeats_channel = self._channels.get("heartbeats")
        if not heartbeats_channel:
            # Create heartbeats channel if needed
            if self._client:
                try:
                    heartbeats_channel = self._client.channel("heartbeats")
                    await heartbeats_channel.subscribe()
                    self._channels["heartbeats"] = heartbeats_channel
                except Exception as e:
                    logger.debug(f"Failed to create heartbeats channel: {e}")
                    return

        if heartbeats_channel:
            try:
                await heartbeats_channel.send_broadcast(
                    event="heartbeat",
                    payload=heartbeat_data,
                )
            except Exception as e:
                logger.debug(f"Heartbeat broadcast error: {e}")

    async def disconnect(self) -> None:
        """Disconnect from all channels."""
        for name, channel in self._channels.items():
            try:
                await channel.unsubscribe()
                logger.debug(f"Unsubscribed from {name} channel")
            except Exception as e:
                logger.warning(f"Error unsubscribing from {name}: {e}")

        self._channels.clear()
        self._subscribed = False
        logger.info("Disconnected from Supabase Realtime")

    def set_callbacks(
        self,
        on_job_inserted: Optional[Callable[[Dict], None]] = None,
        on_cancel_job: Optional[Callable[[str], None]] = None,
        on_shutdown: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Set event callbacks.

        Args:
            on_job_inserted: Called when new job is inserted
            on_cancel_job: Called when job cancellation requested
            on_shutdown: Called when shutdown requested
        """
        self._on_job_inserted = on_job_inserted
        self._on_cancel_job = on_cancel_job
        self._on_shutdown = on_shutdown


class DistributedRobotAgent:
    """
    Distributed Robot Agent for enterprise RPA execution.

    This agent runs on worker machines and:
    1. Registers with orchestrator with capability advertisement
    2. Uses hybrid poll + subscribe for job acquisition
    3. Executes workflows with DBOS durability
    4. Manages resource pools (browser, DB, HTTP)
    5. Sends heartbeats with progress and metrics
    6. Tracks presence for load balancing
    7. Handles graceful shutdown

    Features:
    - Exactly-once job execution (via SKIP LOCKED)
    - Crash recovery (via DBOS checkpointing)
    - Automatic lease extension (via heartbeat)
    - Resource pooling for efficiency
    - State affinity for workflow continuity
    - Graceful shutdown (waits for current jobs)

    Usage:
        config = DistributedRobotConfig(
            postgres_url="postgresql://...",
            supabase_url="https://xxx.supabase.co",
            supabase_key="***",
            robot_id="worker-01",
        )
        agent = DistributedRobotAgent(config)

        await agent.start()
        # Agent runs until stopped
        await agent.stop()
    """

    def __init__(
        self,
        config: DistributedRobotConfig,
        on_job_complete: Optional[Callable[[str, bool, Optional[str]], None]] = None,
    ) -> None:
        """
        Initialize distributed robot agent.

        Args:
            config: Robot configuration
            on_job_complete: Optional callback (job_id, success, error)
        """
        self.config = config
        self.robot_id = config.robot_id or f"robot-{uuid.uuid4().hex[:12]}"
        self.robot_name = config.robot_name or f"Robot-{self.robot_id}"

        # State
        self._state = AgentState.STOPPED
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._current_jobs: Dict[str, ClaimedJob] = {}
        self._job_resources: Dict[str, JobResources] = {}
        self._job_progress: Dict[str, Dict[str, Any]] = {}
        self._cancelled_jobs: Set[str] = set()

        # State affinity tracking
        self._state_affinities: Dict[str, StateAffinity] = {}

        # Capabilities
        self._capabilities = self._build_capabilities()

        # Callbacks
        self._on_job_complete = on_job_complete

        # Components (initialized on start)
        self._consumer: Optional[PgQueuerConsumer] = None
        self._executor: Optional[DBOSWorkflowExecutor] = None
        self._resource_manager: Optional[UnifiedResourceManager] = None
        self._realtime_manager: Optional[RealtimeChannelManager] = None
        self._metrics: Optional[MetricsCollector] = None

        # Background tasks
        self._job_loop_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._presence_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "jobs_completed": 0,
            "jobs_failed": 0,
            "total_execution_time_ms": 0,
            "started_at": None,
        }

        self._init_logging()
        logger.info(
            f"DistributedRobotAgent initialized: {self.robot_name} ({self.robot_id})"
        )

    def _init_logging(self) -> None:
        """Initialize logging configuration."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(self.config.log_dir / "robot_{time}.log"),
            rotation="1 day",
            retention="7 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        )

    def _build_capabilities(self) -> RobotCapabilities:
        """Build robot capabilities from system info."""
        cpu_cores = os.cpu_count() or 1
        memory_gb = 0.0

        if PSUTIL_AVAILABLE:
            try:
                memory_gb = psutil.virtual_memory().total / (1024**3)
            except Exception:
                memory_gb = 4.0  # Fallback

        return RobotCapabilities(
            platform=sys.platform,
            browser_engines=["chromium", "firefox", "webkit"],
            desktop_automation=sys.platform == "win32",
            max_concurrent_jobs=self.config.max_concurrent_jobs,
            cpu_cores=cpu_cores,
            memory_gb=round(memory_gb, 2),
            tags=self.config.tags.copy(),
        )

    @property
    def state(self) -> AgentState:
        """Get current agent state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._state == AgentState.RUNNING

    @property
    def current_job_count(self) -> int:
        """Get number of currently executing jobs."""
        return len(self._current_jobs)

    async def start(self) -> None:
        """
        Start the robot agent.

        Establishes database connections, registers with orchestrator,
        starts background tasks, and begins job loop.
        """
        if self._running:
            logger.warning("Agent already running")
            return

        self._state = AgentState.STARTING
        self._running = True
        self._shutdown_event.clear()
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Starting Distributed Robot Agent: {self.robot_name}")

        # Validate configuration
        if not self.config.postgres_url:
            raise ValueError("postgres_url is required for distributed mode")

        # Initialize metrics collector
        self._metrics = get_metrics_collector()
        await self._metrics.start_resource_monitoring()

        # Initialize PgQueuer consumer
        consumer_config = ConsumerConfig(
            postgres_url=self.config.postgres_url,
            robot_id=self.robot_id,
            batch_size=self.config.batch_size,
            visibility_timeout_seconds=self.config.visibility_timeout_seconds,
            heartbeat_interval_seconds=self.config.heartbeat_interval_seconds,
            environment=self.config.environment,
        )
        self._consumer = PgQueuerConsumer(consumer_config)

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

        # Initialize unified resource manager
        self._resource_manager = UnifiedResourceManager(
            browser_pool_size=self.config.browser_pool_size,
            db_pool_size=self.config.db_pool_size,
            http_pool_size=self.config.http_pool_size,
            postgres_url=self.config.postgres_url,
        )

        # Initialize realtime manager
        if self.config.enable_realtime and self.config.supabase_url:
            self._realtime_manager = RealtimeChannelManager(
                supabase_url=self.config.supabase_url,
                supabase_key=self.config.supabase_key,
                robot_id=self.robot_id,
                environment=self.config.environment,
            )
            self._realtime_manager.set_callbacks(
                on_cancel_job=self._handle_cancel_job,
                on_shutdown=self._handle_remote_shutdown,
            )

        # Start components
        try:
            await self._consumer.start()
            await self._executor.start()
            await self._resource_manager.start()

            if self._realtime_manager:
                await self._realtime_manager.connect()

            # Register with orchestrator
            await self._register()

        except Exception as e:
            logger.error(f"Failed to start components: {e}")
            self._state = AgentState.STOPPED
            self._running = False
            raise

        # Start background tasks
        self._job_loop_task = asyncio.create_task(self._hybrid_job_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._presence_task = asyncio.create_task(self._presence_loop())

        # Setup signal handlers
        self._setup_signal_handlers()

        self._state = AgentState.RUNNING
        logger.info(
            f"Distributed Robot Agent started: env={self.config.environment}, "
            f"max_concurrent={self.config.max_concurrent_jobs}"
        )

    async def stop(self) -> None:
        """
        Gracefully stop the robot agent.

        Waits for current jobs to complete (with timeout), then
        stops all background tasks and closes connections.
        """
        if not self._running:
            return

        logger.info(f"Stopping Distributed Robot Agent: {self.robot_name}")
        self._state = AgentState.SHUTTING_DOWN
        self._running = False
        self._shutdown_event.set()

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
                    "Graceful shutdown timed out, "
                    f"{len(self._current_jobs)} job(s) may be orphaned"
                )

        # Cancel background tasks
        for task in [self._job_loop_task, self._heartbeat_task, self._presence_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Update registration to offline
        await self._update_registration_status("offline")

        # Stop components
        if self._realtime_manager:
            await self._realtime_manager.disconnect()

        if self._resource_manager:
            await self._resource_manager.stop()

        if self._executor:
            await self._executor.stop()

        if self._consumer:
            await self._consumer.stop()

        if self._metrics:
            await self._metrics.stop_resource_monitoring()

        self._state = AgentState.STOPPED
        logger.info(
            f"Distributed Robot Agent stopped. "
            f"Completed: {self._stats['jobs_completed']}, "
            f"Failed: {self._stats['jobs_failed']}"
        )

    async def _wait_for_jobs_complete(self) -> None:
        """Wait for all current jobs to complete."""
        while self._current_jobs:
            await asyncio.sleep(1)

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

    def _handle_cancel_job(self, job_id: str) -> None:
        """Handle job cancellation request."""
        logger.info(f"Received cancel request for job {job_id[:8]}")
        self._cancelled_jobs.add(job_id)

    def _handle_remote_shutdown(self) -> None:
        """Handle remote shutdown request."""
        logger.info("Received remote shutdown request")
        asyncio.create_task(self.stop())

    async def _register(self) -> None:
        """Register robot with orchestrator."""
        registration = RobotRegistration(
            robot_id=self.robot_id,
            hostname=socket.gethostname(),
            capabilities=self._capabilities,
            heartbeat_interval_seconds=int(self.config.heartbeat_interval_seconds),
        )

        try:
            # Insert into robots table via consumer's pool
            if self._consumer and self._consumer._pool:
                async with self._consumer._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO robots (robot_id, hostname, capabilities, status, registered_at, last_seen)
                        VALUES ($1, $2, $3, 'idle', NOW(), NOW())
                        ON CONFLICT (robot_id) DO UPDATE
                        SET capabilities = $3,
                            status = 'idle',
                            registered_at = NOW(),
                            last_seen = NOW()
                        """,
                        self.robot_id,
                        socket.gethostname(),
                        orjson.dumps(registration.to_dict()).decode("utf-8"),
                    )

            logger.info(
                f"Robot registered: {self.robot_id} "
                f"(platform={self._capabilities.platform}, "
                f"cores={self._capabilities.cpu_cores}, "
                f"memory={self._capabilities.memory_gb:.1f}GB)"
            )
        except Exception as e:
            logger.warning(f"Failed to register robot: {e}")

    async def _update_registration_status(self, status: str) -> None:
        """Update robot status in registry."""
        try:
            if self._consumer and self._consumer._pool:
                async with self._consumer._pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE robots SET status = $2, last_seen = NOW()
                        WHERE robot_id = $1
                        """,
                        self.robot_id,
                        status,
                    )
        except Exception as e:
            logger.warning(f"Failed to update registration status: {e}")

    async def _hybrid_job_loop(self) -> None:
        """
        Hybrid poll + subscribe job loop.

        Uses Supabase Realtime notifications as hints, but always polls
        to guarantee job acquisition. Falls back to polling if realtime
        is unavailable.
        """
        logger.info("Hybrid job loop started")
        backoff_delay = self.config.poll_interval_seconds

        while self._running:
            try:
                # Check if at capacity
                if self.current_job_count >= self.config.max_concurrent_jobs:
                    await asyncio.sleep(self.config.poll_interval_seconds)
                    continue

                # Wait for notification or timeout
                notification_received = False
                if self._realtime_manager and self._realtime_manager._subscribed:
                    notification_received = (
                        await self._realtime_manager.wait_for_job_notification(
                            timeout=self.config.subscribe_timeout_seconds
                        )
                    )
                    if not notification_received:
                        logger.debug("No realtime notification, polling queue")
                else:
                    # No realtime, just wait poll interval
                    await asyncio.sleep(self.config.poll_interval_seconds)

                # Always poll (notification is just a hint)
                job = await self._consumer.claim_job()

                if job:
                    # Check state affinity
                    if await self._check_state_affinity(job):
                        # Execute job in background
                        asyncio.create_task(self._execute_job(job))
                        backoff_delay = self.config.poll_interval_seconds
                    else:
                        # Release job - it has affinity to another robot
                        await self._consumer.release_job(job.job_id)
                        logger.debug(
                            f"Released job {job.job_id[:8]} due to state affinity"
                        )
                else:
                    # No jobs available, exponential backoff
                    await asyncio.sleep(backoff_delay)
                    backoff_delay = min(backoff_delay * 1.5, 10.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in hybrid job loop: {e}")
                await asyncio.sleep(5)

        logger.info("Hybrid job loop stopped")

    async def _check_state_affinity(self, job: ClaimedJob) -> bool:
        """
        Check if job has state affinity to this robot.

        Args:
            job: Claimed job

        Returns:
            True if job can run on this robot
        """
        # Check if workflow has existing affinity
        affinity = self._state_affinities.get(job.workflow_id)
        if affinity and not affinity.is_expired():
            if affinity.robot_id != self.robot_id:
                # Affinity to another robot
                return False

        return True

    async def _execute_job(self, job: ClaimedJob) -> None:
        """
        Execute a claimed job with DBOS durability and resource pooling.

        Args:
            job: The claimed job to execute
        """
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

        # Update registration status
        await self._update_registration_status("busy")

        # Start metrics tracking
        if self._metrics:
            self._metrics.start_job(job_id, job.workflow_name)

        # Acquire resources from pool
        resources: Optional[JobResources] = None
        try:
            if self._resource_manager:
                resources = await self._resource_manager.acquire_resources_for_job(
                    job_id,
                    job.workflow_json,
                )
                self._job_resources[job_id] = resources
        except Exception as e:
            logger.warning(f"Failed to acquire resources: {e}")

        try:
            # Check for cancellation
            if job_id in self._cancelled_jobs:
                raise asyncio.CancelledError("Job cancelled by user")

            # Execute with DBOS
            result = await self._executor.execute_workflow(
                workflow_json=job.workflow_json,
                workflow_id=job_id,
                initial_variables=job.variables,
                wait_for_result=True,
                on_progress=lambda p, n: asyncio.create_task(
                    self._on_job_progress(job_id, p, n)
                ),
            )

            # Report result to queue
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
                logger.info(
                    f"Job {job_id[:8]} completed successfully "
                    f"({result.executed_nodes} nodes, {result.duration_ms}ms)"
                )

                # End metrics
                if self._metrics:
                    self._metrics.end_job(success=True)
            else:
                await self._consumer.fail_job(
                    job_id,
                    error_message=result.error or "Workflow execution failed",
                )
                self._stats["jobs_failed"] += 1
                logger.warning(f"Job {job_id[:8]} failed: {result.error}")

                # End metrics
                if self._metrics:
                    self._metrics.end_job(success=False, error_message=result.error)

            self._stats["total_execution_time_ms"] += result.duration_ms

            # Callback
            if self._on_job_complete:
                try:
                    self._on_job_complete(job_id, result.success, result.error)
                except Exception as e:
                    logger.error(f"Job complete callback error: {e}")

        except asyncio.CancelledError:
            logger.info(f"Job {job_id[:8]} was cancelled")
            await self._consumer.fail_job(job_id, error_message="Job cancelled")
            self._stats["jobs_failed"] += 1

            if self._metrics:
                self._metrics.end_job(success=False, error_message="Cancelled")

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Job {job_id[:8]} execution failed: {error_msg}")

            await self._consumer.fail_job(
                job_id,
                error_message=error_msg,
            )
            self._stats["jobs_failed"] += 1

            if self._metrics:
                self._metrics.end_job(success=False, error_message=error_msg)

            if self._on_job_complete:
                try:
                    self._on_job_complete(job_id, False, error_msg)
                except Exception as callback_error:
                    logger.error(f"Job complete callback error: {callback_error}")

        finally:
            # Release resources back to pool
            if resources and self._resource_manager:
                await self._resource_manager.release_resources(resources)

            # Cleanup
            self._current_jobs.pop(job_id, None)
            self._job_resources.pop(job_id, None)
            self._job_progress.pop(job_id, None)
            self._cancelled_jobs.discard(job_id)

            # Update registration status if no more jobs
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
            await self._consumer.update_progress(job_id, progress, node_id)
        except Exception as e:
            logger.debug(f"Failed to update progress for {job_id}: {e}")

    async def _heartbeat_loop(self) -> None:
        """
        Heartbeat loop with enhanced metrics.

        Extends job leases and publishes heartbeat with:
        - Progress tracking
        - CPU/memory metrics
        - Current node information
        """
        logger.info("Heartbeat loop started")

        while self._running:
            try:
                # Extend lease for all current jobs
                for job_id, job in list(self._current_jobs.items()):
                    try:
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

                # Build and publish heartbeat
                if self._current_jobs and self._realtime_manager:
                    for job_id in self._current_jobs:
                        progress_info = self._job_progress.get(job_id, {})

                        heartbeat = {
                            "robot_id": self.robot_id,
                            "job_id": job_id,
                            "progress_percent": progress_info.get(
                                "progress_percent", 0
                            ),
                            "current_node": progress_info.get(
                                "current_node", "unknown"
                            ),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }

                        # Add resource metrics
                        if PSUTIL_AVAILABLE:
                            try:
                                process = psutil.Process()
                                heartbeat["memory_mb"] = round(
                                    process.memory_info().rss / (1024 * 1024), 2
                                )
                                heartbeat["cpu_percent"] = process.cpu_percent(
                                    interval=0.1
                                )
                            except Exception:
                                pass

                        await self._realtime_manager.send_heartbeat(heartbeat)

                await asyncio.sleep(self.config.heartbeat_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Heartbeat loop stopped")

    async def _presence_loop(self) -> None:
        """
        Presence loop for load balancing.

        Publishes robot status, metrics, and availability for
        intelligent job routing by orchestrator.
        """
        logger.info("Presence loop started")

        while self._running:
            try:
                presence_data = {
                    "robot_id": self.robot_id,
                    "status": "busy" if self._current_jobs else "idle",
                    "current_job_count": len(self._current_jobs),
                    "max_concurrent_jobs": self.config.max_concurrent_jobs,
                    "environment": self.config.environment,
                    "current_jobs": [
                        {
                            "job_id": job.job_id,
                            "workflow_name": job.workflow_name,
                        }
                        for job in self._current_jobs.values()
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Add system metrics
                if PSUTIL_AVAILABLE:
                    try:
                        presence_data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                        presence_data["memory_percent"] = (
                            psutil.virtual_memory().percent
                        )
                    except Exception:
                        pass

                # Publish via realtime
                if self._realtime_manager:
                    await self._realtime_manager.track_presence(presence_data)

                # Also update database
                await self._update_presence_in_db(presence_data)

                await asyncio.sleep(self.config.presence_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Presence loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Presence loop stopped")

    async def _update_presence_in_db(self, presence_data: Dict[str, Any]) -> None:
        """Update presence in database for persistence."""
        try:
            if self._consumer and self._consumer._pool:
                async with self._consumer._pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE robots
                        SET status = $2,
                            last_seen = NOW(),
                            metrics = $3
                        WHERE robot_id = $1
                        """,
                        self.robot_id,
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

    def create_state_affinity(
        self,
        workflow_id: str,
        state_keys: Optional[List[str]] = None,
        ttl_minutes: int = 30,
    ) -> StateAffinity:
        """
        Create state affinity for a workflow.

        Args:
            workflow_id: Workflow identifier
            state_keys: Keys that define the state
            ttl_minutes: Affinity TTL in minutes

        Returns:
            Created StateAffinity
        """
        from datetime import timedelta as td

        affinity = StateAffinity(
            workflow_id=workflow_id,
            robot_id=self.robot_id,
            state_keys=state_keys or [],
            expires_at=datetime.now(timezone.utc) + td(minutes=ttl_minutes)
            if ttl_minutes > 0
            else None,
        )
        self._state_affinities[workflow_id] = affinity
        logger.debug(f"Created state affinity for workflow {workflow_id}")
        return affinity

    def clear_state_affinity(self, workflow_id: str) -> None:
        """Clear state affinity for a workflow."""
        if workflow_id in self._state_affinities:
            del self._state_affinities[workflow_id]
            logger.debug(f"Cleared state affinity for workflow {workflow_id}")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        status = {
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "state": self._state.value,
            "is_running": self.is_running,
            "environment": self.config.environment,
            "current_job_count": self.current_job_count,
            "max_concurrent_jobs": self.config.max_concurrent_jobs,
            "capabilities": self._capabilities.to_dict(),
            "current_jobs": [
                {
                    "job_id": job.job_id,
                    "workflow_name": job.workflow_name,
                    "claimed_at": job.claimed_at.isoformat()
                    if job.claimed_at
                    else None,
                    "progress": self._job_progress.get(job.job_id, {}),
                }
                for job in self._current_jobs.values()
            ],
            "consumer": self._consumer.get_stats() if self._consumer else None,
            "resources": (
                self._resource_manager.get_stats() if self._resource_manager else None
            ),
            "stats": self._stats,
        }

        # Add resource metrics
        if PSUTIL_AVAILABLE:
            try:
                status["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                status["memory_percent"] = psutil.virtual_memory().percent
            except Exception:
                pass

        return status


async def run_distributed_agent(
    config: Optional[DistributedRobotConfig] = None,
) -> None:
    """
    Run the distributed robot agent.

    Convenience function that creates an agent, runs it until
    interrupted, then shuts down gracefully.

    Args:
        config: Robot configuration (uses env vars if None)
    """
    if config is None:
        config = DistributedRobotConfig.from_env()

    agent = DistributedRobotAgent(config)

    try:
        await agent.start()

        # Wait for shutdown signal
        await agent._shutdown_event.wait()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(run_distributed_agent())
