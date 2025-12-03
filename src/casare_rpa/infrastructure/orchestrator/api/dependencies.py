"""
Dependency injection for FastAPI endpoints.

Provides shared dependencies like database connections and metrics collectors.
"""

import os
import asyncio
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

from fastapi import Request, HTTPException
from loguru import logger
import asyncpg

from casare_rpa.infrastructure.observability.metrics import (
    get_metrics_collector as get_rpa_metrics,
)
from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator
from casare_rpa.infrastructure.orchestrator.api.adapters import MonitoringDataAdapter


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str
    min_size: int
    max_size: int
    command_timeout: float
    max_inactive_connection_lifetime: float

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        import urllib.parse

        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                parsed = urllib.parse.urlparse(db_url)
                return cls(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 5432,
                    database=parsed.path.lstrip("/") or "postgres",
                    user=parsed.username or "postgres",
                    password=parsed.password or "",
                    min_size=int(os.getenv("DB_POOL_MIN_SIZE", "2")),
                    max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
                    command_timeout=float(os.getenv("DB_COMMAND_TIMEOUT", "60.0")),
                    max_inactive_connection_lifetime=float(
                        os.getenv("DB_MAX_INACTIVE_LIFETIME", "300.0")
                    ),
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse DATABASE_URL: {e}. Falling back to individual vars."
                )

        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "casare_rpa"),
            user=os.getenv("DB_USER", "casare_user"),
            password=os.getenv("DB_PASSWORD", ""),
            min_size=int(os.getenv("DB_POOL_MIN_SIZE", "2")),
            max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
            command_timeout=float(os.getenv("DB_COMMAND_TIMEOUT", "60.0")),
            max_inactive_connection_lifetime=float(
                os.getenv("DB_MAX_INACTIVE_LIFETIME", "300.0")
            ),
        )


class DatabasePoolManager:
    """
    Manages asyncpg connection pool lifecycle.

    Handles creation, health checking, and graceful shutdown of database pools.
    Implements retry logic for transient connection failures.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self._config = config or DatabaseConfig.from_env()
        self._pool: Optional[asyncpg.Pool] = None
        self._is_healthy = False
        self._connection_attempts = 0
        self._max_retries = 3
        self._retry_delay_base = 1.0  # seconds

    @property
    def pool(self) -> Optional[asyncpg.Pool]:
        """Get the current connection pool."""
        return self._pool

    @property
    def is_healthy(self) -> bool:
        """Check if pool is currently healthy."""
        return self._is_healthy and self._pool is not None

    async def create_pool(self) -> asyncpg.Pool:
        """
        Create database connection pool with retry logic.

        Retries connection on transient failures with exponential backoff.

        Returns:
            asyncpg.Pool: Initialized connection pool

        Raises:
            RuntimeError: If pool creation fails after all retries
        """
        if not self._config.password:
            logger.warning(
                "DB_PASSWORD not set - database connections will fail authentication"
            )

        last_error: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            self._connection_attempts = attempt
            try:
                logger.info(
                    f"Creating database pool (attempt {attempt}/{self._max_retries}): "
                    f"{self._config.database}@{self._config.host}:{self._config.port}"
                )

                self._pool = await asyncpg.create_pool(
                    host=self._config.host,
                    port=self._config.port,
                    database=self._config.database,
                    user=self._config.user,
                    password=self._config.password,
                    min_size=self._config.min_size,
                    max_size=self._config.max_size,
                    command_timeout=self._config.command_timeout,
                    max_inactive_connection_lifetime=self._config.max_inactive_connection_lifetime,
                    statement_cache_size=0,  # Required for Supabase Transaction Mode (Supavisor)
                )

                # Verify pool is working
                await self._verify_connection()
                self._is_healthy = True

                logger.info(
                    f"Database pool created successfully: "
                    f"min_size={self._config.min_size}, max_size={self._config.max_size}"
                )
                return self._pool

            except asyncpg.InvalidCatalogNameError as e:
                # Database doesn't exist - don't retry
                logger.error(f"Database '{self._config.database}' does not exist: {e}")
                raise RuntimeError(
                    f"Database '{self._config.database}' does not exist"
                ) from e

            except asyncpg.InvalidPasswordError as e:
                # Auth failed - don't retry
                logger.error(f"Database authentication failed: {e}")
                raise RuntimeError("Database authentication failed") from e

            except (
                asyncpg.CannotConnectNowError,
                asyncpg.ConnectionDoesNotExistError,
                OSError,
                ConnectionRefusedError,
            ) as e:
                # Transient errors - retry with backoff
                last_error = e
                delay = self._retry_delay_base * (2 ** (attempt - 1))
                logger.warning(
                    f"Database connection failed (attempt {attempt}/{self._max_retries}): {e}. "
                    f"Retrying in {delay:.1f}s"
                )

                if attempt < self._max_retries:
                    await asyncio.sleep(delay)

            except Exception as e:
                # Unexpected error - log and retry
                last_error = e
                delay = self._retry_delay_base * (2 ** (attempt - 1))
                logger.error(
                    f"Unexpected database error (attempt {attempt}/{self._max_retries}): {e}. "
                    f"Retrying in {delay:.1f}s"
                )

                if attempt < self._max_retries:
                    await asyncio.sleep(delay)

        # All retries exhausted
        self._is_healthy = False
        error_msg = f"Failed to create database pool after {self._max_retries} attempts"
        logger.error(f"{error_msg}: {last_error}")
        raise RuntimeError(error_msg) from last_error

    async def _verify_connection(self) -> None:
        """Verify pool works by executing a simple query."""
        if self._pool is None:
            raise RuntimeError("Pool not initialized")

        async with self._pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise RuntimeError("Database verification query failed")

    async def check_health(self) -> dict:
        """
        Perform health check on database connection.

        Returns:
            dict: Health status with details
        """
        if self._pool is None:
            return {
                "healthy": False,
                "error": "Pool not initialized",
                "pool_size": 0,
                "pool_free": 0,
            }

        try:
            async with asyncio.timeout(5.0):
                async with self._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")

            self._is_healthy = True
            return {
                "healthy": True,
                "pool_size": self._pool.get_size(),
                "pool_free": self._pool.get_idle_size(),
                "pool_min": self._pool.get_min_size(),
                "pool_max": self._pool.get_max_size(),
            }

        except asyncio.TimeoutError:
            self._is_healthy = False
            return {
                "healthy": False,
                "error": "Health check timed out",
                "pool_size": self._pool.get_size(),
                "pool_free": self._pool.get_idle_size(),
            }

        except Exception as e:
            self._is_healthy = False
            return {
                "healthy": False,
                "error": str(e),
                "pool_size": self._pool.get_size() if self._pool else 0,
                "pool_free": self._pool.get_idle_size() if self._pool else 0,
            }

    async def close(self) -> None:
        """Close the connection pool gracefully."""
        if self._pool is not None:
            logger.info("Closing database connection pool")
            try:
                await asyncio.wait_for(self._pool.close(), timeout=10.0)
                logger.info("Database pool closed successfully")
            except asyncio.TimeoutError:
                logger.warning("Database pool close timed out, terminating connections")
                self._pool.terminate()
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
                self._pool.terminate()
            finally:
                self._pool = None
                self._is_healthy = False


# Global pool manager instance
_pool_manager: Optional[DatabasePoolManager] = None


def get_pool_manager() -> DatabasePoolManager:
    """Get or create the global pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = DatabasePoolManager()
    return _pool_manager


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """
    FastAPI dependency to get database pool from app state.

    Args:
        request: FastAPI request object

    Returns:
        asyncpg.Pool: Active database connection pool

    Raises:
        HTTPException: If database is unavailable (503)
    """
    pool: Optional[asyncpg.Pool] = getattr(request.app.state, "db_pool", None)

    if pool is None:
        logger.error("Database pool not available - not initialized in app state")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable",
            headers={"Retry-After": "30"},
        )

    return pool


async def get_db_connection(
    request: Request,
) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency to get a database connection from pool.

    Acquires a connection from the pool and automatically releases it
    when the request completes.

    Args:
        request: FastAPI request object

    Yields:
        asyncpg.Connection: Database connection

    Raises:
        HTTPException: If database is unavailable (503)
    """
    pool = await get_db_pool(request)

    try:
        async with pool.acquire() as connection:
            yield connection
    except asyncpg.PoolConnectionLostError as e:
        logger.error(f"Database connection lost during request: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection lost",
            headers={"Retry-After": "5"},
        )
    except asyncpg.TooManyConnectionsError as e:
        logger.warning(f"Database pool exhausted: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service overloaded",
            headers={"Retry-After": "10"},
        )
    except Exception as e:
        logger.error(f"Database error during request: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database error",
            headers={"Retry-After": "5"},
        )


def get_metrics_collector(request: Request):
    """
    Get the monitoring data adapter with database pool injection.

    Returns adapter that provides API-compatible interface to infrastructure metrics.
    Database pool is injected from app state if available.

    Args:
        request: FastAPI request object (for DB pool injection)
    """
    rpa_metrics = get_rpa_metrics()
    analytics = MetricsAggregator.get_instance()

    # Inject database pool from app state if available
    db_pool = getattr(request.app.state, "db_pool", None)

    return MonitoringDataAdapter(rpa_metrics, analytics, db_pool=db_pool)
