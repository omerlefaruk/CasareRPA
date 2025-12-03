"""
Server Lifecycle Management for Cloud Orchestrator.

Handles application state, configuration, startup/shutdown, and lifespan.
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
    """Get robot manager instance."""
    state = _get_state()
    if state.robot_manager is not None:
        return state.robot_manager

    with _state_lock:
        if _orchestrator_state.robot_manager is None:
            config = get_config()
            _orchestrator_state.robot_manager = RobotManager(
                job_timeout_default=config.job_timeout_default
            )
        return _orchestrator_state.robot_manager


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

        # Initialize log repository and streaming service
        await _init_log_services(db_pool)

    except Exception as e:
        logger.warning(f"Database connection failed: {e}")


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
