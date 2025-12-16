"""
Server Lifecycle Management for Cloud Orchestrator.

Handles application state, configuration, startup/shutdown, and lifespan.

DDD 2025 Architecture:
- Initializes PostgreSQL robot repository for persistent state
- Injects repository into RobotManager for durability
- Falls back to in-memory mode if database unavailable
"""

import os
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, List, Optional

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

    # Database
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # Redis (optional queue backend)
    redis_url: Optional[str] = None

    # Security
    api_secret: str = ""
    cors_origins: List[str] = field(default_factory=list)

    # Timeouts
    robot_heartbeat_timeout: int = 90  # seconds
    job_timeout_default: int = 3600  # 1 hour
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
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            redis_url=os.getenv("REDIS_URL"),
            api_secret=os.getenv("API_SECRET", ""),
            cors_origins=cors_origins,
            robot_heartbeat_timeout=int(os.getenv("ROBOT_HEARTBEAT_TIMEOUT", "90")),
            job_timeout_default=int(os.getenv("JOB_TIMEOUT_DEFAULT", "3600")),
            websocket_ping_interval=int(os.getenv("WS_PING_INTERVAL", "30")),
        )


@dataclass
class OrchestratorState:
    """Container for orchestrator runtime state."""

    config: Optional[OrchestratorConfig] = None
    robot_manager: Optional[RobotManager] = None
    robot_repository: Any = None  # PgRobotRepository
    job_producer: Any = None  # PgQueuerProducer
    dlq_manager: Any = None  # DLQManager
    db_pool: Any = None  # asyncpg.Pool
    log_streaming_service: Any = None
    log_repository: Any = None
    log_cleanup_job: Any = None


# Thread-safe state management
_state_lock = threading.Lock()
_orchestrator_state = OrchestratorState()


def _get_state() -> OrchestratorState:
    """Get current orchestrator state."""
    return _orchestrator_state


def _set_state_field(field_name: str, value: Any) -> None:
    """Set a field on the orchestrator state."""
    with _state_lock:
        setattr(_orchestrator_state, field_name, value)


def get_config() -> OrchestratorConfig:
    """Get orchestrator configuration."""
    state = _get_state()
    if state.config is not None:
        return state.config

    with _state_lock:
        if _orchestrator_state.config is None:
            _orchestrator_state.config = OrchestratorConfig.from_env()
        return _orchestrator_state.config


def get_robot_manager() -> RobotManager:
    """Get robot manager instance.

    Returns RobotManager with repository if database is configured,
    otherwise returns in-memory-only manager.
    """
    state = _get_state()
    if state.robot_manager is not None:
        return state.robot_manager

    with _state_lock:
        if _orchestrator_state.robot_manager is None:
            config = get_config()
            # Robot manager will be re-initialized with repository in lifespan
            # This is a fallback for early access before database init
            _orchestrator_state.robot_manager = RobotManager(
                job_timeout_default=config.job_timeout_default,
                robot_repository=_orchestrator_state.robot_repository,
            )
        return _orchestrator_state.robot_manager


def get_robot_repository() -> Any:
    """Get robot repository if available."""
    return _get_state().robot_repository


def get_job_producer() -> Any:
    """Get job producer for durable job enqueuing.

    Returns PgQueuerProducer if database is configured, None otherwise.
    When available, use this for job submission instead of RobotManager.submit_job()
    to ensure jobs survive orchestrator restarts.
    """
    return _get_state().job_producer


def get_dlq_manager() -> Any:
    """Get Dead Letter Queue manager if available.

    Returns DLQManager if database is configured, None otherwise.
    Use for handling failed jobs with exponential backoff retry.
    """
    return _get_state().dlq_manager


def get_db_pool() -> Any:
    """Get database pool if available."""
    return _get_state().db_pool


def get_log_streaming_service() -> Any:
    """Get log streaming service if available."""
    return _get_state().log_streaming_service


def get_log_repository() -> Any:
    """Get log repository if available."""
    return _get_state().log_repository


def get_log_cleanup_job() -> Any:
    """Get log cleanup job if available."""
    return _get_state().log_cleanup_job


def reset_orchestrator_state() -> None:
    """Reset orchestrator state for testing."""
    global _orchestrator_state
    with _state_lock:
        _orchestrator_state = OrchestratorState()
    logger.debug("Orchestrator state reset")


async def _init_database(config: OrchestratorConfig) -> None:
    """Initialize database pool and related services."""
    if not config.database_url:
        logger.info("No DATABASE_URL configured - using in-memory mode")
        return

    try:
        import asyncpg

        db_pool = await asyncpg.create_pool(
            config.database_url,
            min_size=2,
            max_size=10,
        )
        _set_state_field("db_pool", db_pool)
        logger.info("Database pool initialized")

        # Initialize robot repository for persistent state
        await _init_robot_repository(db_pool, config)

        # Initialize job producer for durable job enqueuing
        await _init_job_producer(config)

        # Initialize DLQ manager for failed job handling
        await _init_dlq_manager(config)

        # Initialize log repository and streaming service
        await _init_log_services(db_pool)

    except Exception as e:
        logger.warning(f"Database connection failed: {e}")


async def _init_robot_repository(db_pool: Any, config: OrchestratorConfig) -> None:
    """Initialize robot repository for persistent robot state."""
    try:
        from casare_rpa.infrastructure.orchestrator.persistence import (
            PgRobotRepository,
            CREATE_ROBOTS_TABLE_SQL,
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
        from casare_rpa.infrastructure.persistence.repositories.log_repository import (
            LogRepository,
        )
        from casare_rpa.infrastructure.logging.log_streaming_service import (
            LogStreamingService,
        )
        from casare_rpa.infrastructure.logging.log_cleanup import (
            LogCleanupJob,
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
    state = _get_state()

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

    if state.db_pool:
        await state.db_pool.close()
        logger.info("Database pool closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    config = get_config()
    logger.info("Starting CasareRPA Cloud Orchestrator")
    logger.info(f"Host: {config.host}:{config.port}")

    # Initialize database pool if configured
    await _init_database(config)

    # Initialize Supabase if configured
    if config.supabase_url and config.supabase_key:
        logger.info("Supabase integration enabled")

    yield

    # Cleanup
    await _cleanup_services()
    logger.info("Shutting down orchestrator")
