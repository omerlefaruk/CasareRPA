import os
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from loguru import logger

from casare_rpa.domain.value_objects.log_entry import DEFAULT_LOG_RETENTION_DAYS
from casare_rpa.infrastructure.orchestrator.robot_manager import RobotManager


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration loaded from environment."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    api_version: str = "1.2.0"

    # Database
    database_url: str | None = None
    db_enabled: bool = True
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10

    # Supabase (optional presence sync)
    supabase_url: str | None = None
    supabase_key: str | None = None

    # Security
    api_secret: str = ""
    cors_origins: list[str] = field(default_factory=list)
    rate_limit_enabled: bool = True

    # Robot Settings
    robot_heartbeat_timeout: int = 90
    job_timeout_default: int = 3600
    websocket_ping_interval: int = 30

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Load configuration from environment variables."""
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]

        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            workers=int(os.getenv("WORKERS", "1")),
            database_url=os.getenv("DATABASE_URL"),
            db_enabled=os.getenv("DB_ENABLED", "true").lower() in ("true", "1", "yes"),
            db_pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "2")),
            db_pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            api_secret=os.getenv("API_SECRET", os.getenv("ADMIN_API_KEY", "")),
            cors_origins=cors_origins,
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1"),
            robot_heartbeat_timeout=int(os.getenv("ROBOT_HEARTBEAT_TIMEOUT", "90")),
            job_timeout_default=int(os.getenv("JOB_TIMEOUT_DEFAULT", "3600")),
            websocket_ping_interval=int(os.getenv("WS_PING_INTERVAL", "30")),
        )


@dataclass
class OrchestratorState:
    """Container for orchestrator runtime state."""

    config: OrchestratorConfig | None = None
    startup_time: float = field(default_factory=time.time)

    # Core Services
    robot_manager: RobotManager | None = None
    robot_repository: Any = None
    job_producer: Any = None
    dlq_manager: Any = None
    db_pool: Any = None
    db_manager: Any = None

    # Logging & Monitoring
    log_streaming_service: Any = None
    log_repository: Any = None
    log_cleanup_job: Any = None
    metrics_collector: Any = None
    metrics_aggregator: Any = None
    event_bus: Any = None

    # Scheduling
    global_scheduler: Any = None


# Thread-safe state management
_state_lock = threading.Lock()
_orchestrator_state = OrchestratorState()


def get_state() -> OrchestratorState:
    """Get current orchestrator state."""
    return _orchestrator_state


def _set_state_field(field_name: str, value: Any) -> None:
    """Set a field on the orchestrator state."""
    with _state_lock:
        setattr(_orchestrator_state, field_name, value)


def get_config() -> OrchestratorConfig:
    """Get orchestrator configuration."""
    state = get_state()
    if state.config is not None:
        return state.config

    with _state_lock:
        if _orchestrator_state.config is None:
            _orchestrator_state.config = OrchestratorConfig.from_env()
        return _orchestrator_state.config


def get_robot_manager() -> RobotManager:
    """Get robot manager instance."""
    state = get_state()
    if state.robot_manager is not None:
        return state.robot_manager

    with _state_lock:
        if _orchestrator_state.robot_manager is None:
            config = get_config()
            _orchestrator_state.robot_manager = RobotManager(
                job_timeout_default=config.job_timeout_default,
                robot_repository=_orchestrator_state.robot_repository,
            )
        return _orchestrator_state.robot_manager


def get_robot_repository() -> Any:
    return get_state().robot_repository


def get_job_producer() -> Any:
    return get_state().job_producer


def get_dlq_manager() -> Any:
    return get_state().dlq_manager


def get_db_pool() -> Any:
    return get_state().db_pool


def get_db_manager() -> Any:
    return get_state().db_manager


def get_log_streaming_service() -> Any:
    return get_state().log_streaming_service


def get_log_repository() -> Any:
    return get_state().log_repository


def get_log_cleanup_job() -> Any:
    return get_state().log_cleanup_job


def get_metrics_collector() -> Any:
    return get_state().metrics_collector


def get_metrics_aggregator() -> Any:
    return get_state().metrics_aggregator


def get_event_bus() -> Any:
    return get_state().event_bus


def get_scheduler() -> Any:
    return get_state().global_scheduler


def reset_orchestrator_state() -> None:
    """Reset orchestrator state for testing."""
    global _orchestrator_state
    with _state_lock:
        _orchestrator_state = OrchestratorState()
    logger.debug("Orchestrator state reset")


async def _init_database(config: OrchestratorConfig) -> None:
    """Initialize database pool and related services."""
    if not config.database_url or not config.db_enabled:
        logger.info("Database disabled or no DATABASE_URL - using in-memory mode")
        return

    try:
        from casare_rpa.infrastructure.orchestrator.api.dependencies import DatabasePoolManager

        pool_manager = DatabasePoolManager()
        db_pool = await pool_manager.create_pool()

        _set_state_field("db_manager", pool_manager)
        _set_state_field("db_pool", db_pool)

        # Initialize monitoring data adapter
        from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator
        from casare_rpa.infrastructure.events import get_monitoring_event_bus
        from casare_rpa.infrastructure.observability.metrics import get_metrics_collector

        metrics_collector = get_metrics_collector()
        metrics_aggregator = MetricsAggregator.get_instance()
        event_bus = get_monitoring_event_bus()

        _set_state_field("metrics_collector", metrics_collector)
        _set_state_field("metrics_aggregator", metrics_aggregator)
        _set_state_field("event_bus", event_bus)

        # Initialize robot repository for persistent state
        await _init_robot_repository(db_pool, config)

        # Initialize job producer for durable job enqueuing
        await _init_job_producer(config)

        # Initialize DLQ manager for failed job handling
        await _init_dlq_manager(config)

        # Initialize log repository and streaming service
        await _init_log_services(db_pool)

    except Exception as e:
        logger.warning(f"Database/Monitoring initialization failed: {e}")


async def _init_robot_repository(db_pool: Any, config: OrchestratorConfig) -> None:
    """Initialize robot repository for persistent robot state."""
    try:
        from casare_rpa.infrastructure.orchestrator.persistence import (
            CREATE_ROBOTS_TABLE_SQL,
            PgRobotRepository,
        )
        from casare_rpa.infrastructure.orchestrator.persistence.pg_robot_api_keys_schema import (
            ensure_robot_api_key_tables,
        )

        # Ensure robots table exists
        async with db_pool.acquire() as conn:
            await conn.execute(CREATE_ROBOTS_TABLE_SQL)

            # Backward/forward compatibility: older deployments may have a partial robots table.
            # Ensure the columns used by the API routers exist.
            await conn.execute(
                "ALTER TABLE robots ADD COLUMN IF NOT EXISTS max_concurrent_jobs INTEGER DEFAULT 1"
            )
            await conn.execute(
                "ALTER TABLE robots ADD COLUMN IF NOT EXISTS registered_at TIMESTAMPTZ"
            )
            await conn.execute(
                "ALTER TABLE robots ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
            )

            # Ensure robot API key tables exist (used by X-Api-Key auth + admin key management)
            await ensure_robot_api_key_tables(conn)
        logger.info("Robots table verified/created")

        # Create repository
        robot_repository = PgRobotRepository(
            db_pool=db_pool,
            heartbeat_timeout_seconds=config.robot_heartbeat_timeout,
        )
        _set_state_field("robot_repository", robot_repository)

        # Reinitialize robot manager with repository
        robot_manager = RobotManager(
            job_timeout_default=config.job_timeout_default,
            robot_repository=robot_repository,
        )
        _set_state_field("robot_manager", robot_manager)

        logger.info("Robot repository initialized - persistent mode enabled")

    except Exception as e:
        logger.warning(f"Robot repository initialization failed: {e}")
        logger.warning("Falling back to in-memory mode for robot state")


async def _init_job_producer(config: OrchestratorConfig) -> None:
    """Initialize job producer for durable job enqueuing."""
    if not config.database_url:
        return

    try:
        from casare_rpa.infrastructure.queue import (
            PgQueuerProducer,
            ProducerConfig,
        )

        producer_config = ProducerConfig(
            postgres_url=config.database_url,
            default_environment="default",
            default_priority=10,
            default_max_retries=3,
            pool_min_size=2,
            pool_max_size=5,
        )

        producer = PgQueuerProducer(producer_config)
        success = await producer.start()

        if success:
            _set_state_field("job_producer", producer)
            logger.info("Job producer initialized - durable job queue enabled")
        else:
            logger.warning("Job producer failed to start")

    except ImportError as e:
        logger.warning(f"Job producer dependencies not available: {e}")
    except Exception as e:
        logger.warning(f"Job producer initialization failed: {e}")
        logger.warning("Falling back to in-memory job queue")


async def _init_dlq_manager(config: OrchestratorConfig) -> None:
    """Initialize Dead Letter Queue manager for failed job handling."""
    if not config.database_url:
        return

    try:
        from casare_rpa.infrastructure.queue import (
            DLQManager,
            DLQManagerConfig,
        )

        dlq_config = DLQManagerConfig(
            postgres_url=config.database_url,
            job_queue_table="job_queue",
            dlq_table="job_queue_dlq",
            pool_min_size=1,
            pool_max_size=3,
        )

        dlq_manager = DLQManager(dlq_config)
        await dlq_manager.start()

        _set_state_field("dlq_manager", dlq_manager)
        logger.info("DLQ manager initialized - failed job handling enabled")

    except ImportError as e:
        logger.warning(f"DLQ manager dependencies not available: {e}")
    except Exception as e:
        logger.warning(f"DLQ manager initialization failed: {e}")


async def _init_log_services(db_pool: Any) -> None:
    """Initialize log repository and streaming service."""
    try:
        from casare_rpa.infrastructure.logging.log_cleanup import (
            LogCleanupJob,
        )
        from casare_rpa.infrastructure.logging.log_streaming_service import (
            LogStreamingService,
        )
        from casare_rpa.infrastructure.persistence.repositories.log_repository import (
            LogRepository,
        )

        log_repository = LogRepository()
        _set_state_field("log_repository", log_repository)

        log_streaming_service = LogStreamingService(log_repository)
        await log_streaming_service.start()
        _set_state_field("log_streaming_service", log_streaming_service)
        logger.info("Log streaming service started")

        # Start log cleanup job
        log_cleanup_job = LogCleanupJob(
            log_repository=log_repository,
            retention_days=DEFAULT_LOG_RETENTION_DAYS,
        )
        await log_cleanup_job.start()
        _set_state_field("log_cleanup_job", log_cleanup_job)
        logger.info("Log cleanup job started")

    except Exception as e:
        logger.warning(f"Log streaming initialization failed: {e}")


async def _cleanup_services() -> None:
    """Cleanup all services during shutdown."""
    state = get_state()

    # Unsubscribe from events
    if state.event_bus:
        try:
            from casare_rpa.infrastructure.events import MonitoringEventType
            from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
                on_job_status_changed,
                on_queue_depth_changed,
                on_robot_heartbeat,
            )

            state.event_bus.unsubscribe(
                MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed
            )
            state.event_bus.unsubscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
            state.event_bus.unsubscribe(
                MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed
            )
        except Exception as e:
            logger.warning(f"Error unsubscribing from event bus: {e}")

    # Shutdown Scheduler
    if state.global_scheduler:
        try:
            from casare_rpa.infrastructure.orchestrator.scheduling import shutdown_global_scheduler

            await shutdown_global_scheduler()
            logger.info("Scheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

    if state.log_cleanup_job:
        await state.log_cleanup_job.stop()
        logger.info("Log cleanup job stopped")

    if state.log_streaming_service:
        await state.log_streaming_service.stop()
        logger.info("Log streaming service stopped")

    if state.job_producer:
        try:
            await state.job_producer.stop()
            logger.info("Job producer stopped")
        except Exception as e:
            logger.warning(f"Error stopping job producer: {e}")

    if state.dlq_manager:
        try:
            await state.dlq_manager.stop()
            logger.info("DLQ manager stopped")
        except Exception as e:
            logger.warning(f"Error stopping DLQ manager: {e}")

    if state.db_manager:
        await state.db_manager.close()
        logger.info("Database connections closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    config = get_config()
    state = get_state()
    logger.info(f"Starting CasareRPA Orchestrator v{config.api_version}")

    # 1. Initialize Database & Base Services
    await _init_database(config)

    # 2. Inject DB pool into Monitoring Routers
    if state.db_pool:
        try:
            from casare_rpa.infrastructure.orchestrator.api.auth import (
                configure_robot_authenticator,
            )
            from casare_rpa.infrastructure.orchestrator.api.routers.jobs import (
                set_db_pool as set_jobs_db_pool,
            )
            from casare_rpa.infrastructure.orchestrator.api.routers.robot_api_keys import (
                set_db_pool as set_robot_api_keys_db_pool,
            )
            from casare_rpa.infrastructure.orchestrator.api.routers.robots import (
                set_db_pool as set_robots_db_pool,
            )
            from casare_rpa.infrastructure.orchestrator.api.routers.schedules import (
                set_db_pool as set_schedules_db_pool,
            )
            from casare_rpa.infrastructure.orchestrator.api.routers.workflows import (
                set_db_pool as set_workflows_db_pool,
            )

            set_workflows_db_pool(state.db_pool)
            set_schedules_db_pool(state.db_pool)
            set_robots_db_pool(state.db_pool)
            set_jobs_db_pool(state.db_pool)
            set_robot_api_keys_db_pool(state.db_pool)
            configure_robot_authenticator(use_database=True, db_pool=state.db_pool)
        except Exception as e:
            logger.warning(f"Failed to inject DB pool into monitoring routers: {e}")

    # 3. Initialize Scheduler
    try:
        from casare_rpa.infrastructure.orchestrator.api.routers.schedules import (
            _execute_scheduled_workflow,
        )
        from casare_rpa.infrastructure.orchestrator.scheduling import init_global_scheduler

        scheduler = await init_global_scheduler(on_schedule_trigger=_execute_scheduled_workflow)
        _set_state_field("global_scheduler", scheduler)
        logger.info("Global scheduler initialized")
    except Exception as e:
        logger.warning(f"Scheduler initialization failed: {e}")

    # 4. Subscribe Monitoring Callbacks
    if state.event_bus:
        try:
            from casare_rpa.infrastructure.events import MonitoringEventType
            from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
                on_job_status_changed,
                on_queue_depth_changed,
                on_robot_heartbeat,
            )

            state.event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed)
            state.event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
            state.event_bus.subscribe(
                MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed
            )
            logger.info("Monitoring event bus callbacks subscribed")
        except Exception as e:
            logger.warning(f"Event bus subscription failed: {e}")

    # Store state in app to expose it via dependencies
    app.state.orchestrator_state = state
    app.state.db_pool = state.db_pool

    yield

    # Cleanup
    await _cleanup_services()
    logger.info("Orchestrator shutdown complete")
