"""
Database connection pool for CasareRPA.

Provides connection pooling for database connections to improve
performance when running workflows with frequent database operations.

Supports:
    - PostgreSQL via asyncpg (native pool support)
    - SQLite via aiosqlite (connection reuse)
    - MySQL via aiomysql (pool support)
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Deque, Dict, Optional, Set, Union

from loguru import logger


# Try to import optional database drivers
try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False

try:
    import aiomysql

    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False


class DatabaseType(Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class PoolStatistics:
    """Statistics for connection pool monitoring."""

    connections_created: int = 0
    connections_closed: int = 0
    connections_recycled: int = 0
    acquire_count: int = 0
    release_count: int = 0
    wait_count: int = 0
    total_wait_time_ms: float = 0.0
    errors: int = 0

    @property
    def avg_wait_time_ms(self) -> float:
        """Average wait time for acquiring a connection."""
        if self.wait_count == 0:
            return 0.0
        return self.total_wait_time_ms / self.wait_count


@dataclass
class PooledConnection:
    """A database connection managed by the pool."""

    connection: Any
    db_type: DatabaseType
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    is_in_use: bool = False
    _id: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._id = id(self.connection)

    def __hash__(self) -> int:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PooledConnection):
            return False
        return self._id == other._id

    def mark_used(self) -> None:
        """Mark the connection as used."""
        self.last_used = time.time()
        self.use_count += 1
        self.is_in_use = True

    def release(self) -> None:
        """Mark the connection as available."""
        self.is_in_use = False

    def is_stale(self, max_age_seconds: float) -> bool:
        """Check if connection is older than max age."""
        return (time.time() - self.created_at) > max_age_seconds

    def is_idle(self, idle_timeout_seconds: float) -> bool:
        """Check if connection has been idle too long."""
        return (time.time() - self.last_used) > idle_timeout_seconds


class DatabaseConnectionPool:
    """
    Pool of reusable database connections for improved performance.

    Features:
    - Pre-creates a minimum number of connections
    - Dynamically grows up to max_size
    - Recycles connections for reuse
    - Cleans up stale/idle connections
    - Thread-safe for async operations
    - Health checks before returning connections
    """

    def __init__(
        self,
        db_type: Union[DatabaseType, str],
        min_size: int = 1,
        max_size: int = 10,
        max_connection_age: float = 300.0,  # 5 minutes
        idle_timeout: float = 60.0,  # 1 minute
        # Connection parameters
        host: str = "localhost",
        port: int = 5432,
        database: str = "",
        username: str = "",
        password: str = "",
        connection_string: str = "",
        **extra_options: Any,
    ) -> None:
        """
        Initialize the database connection pool.

        Args:
            db_type: Type of database (sqlite, postgresql, mysql)
            min_size: Minimum number of connections to keep warm
            max_size: Maximum number of connections allowed
            max_connection_age: Maximum age of a connection before recycling
            idle_timeout: Time after which idle connections are closed
            host: Database host
            port: Database port
            database: Database name or file path for SQLite
            username: Database username
            password: Database password
            connection_string: Full connection string (optional)
            **extra_options: Additional connection options
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())

        self._db_type = db_type
        self._min_size = min_size
        self._max_size = max_size
        self._max_connection_age = max_connection_age
        self._idle_timeout = idle_timeout

        # Connection parameters
        self._host = host
        self._port = port
        self._database = database
        self._username = username
        self._password = password
        self._connection_string = connection_string
        self._extra_options = extra_options

        # Pool state
        self._available: Deque[PooledConnection] = deque()
        self._in_use: Set[PooledConnection] = set()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._closed = False

        # Native pool for PostgreSQL (asyncpg has built-in pooling)
        self._pg_pool: Optional[Any] = None

        # Statistics
        self._stats = PoolStatistics()

    @property
    def db_type(self) -> DatabaseType:
        """Get the database type."""
        return self._db_type

    @property
    def available_count(self) -> int:
        """Number of available connections."""
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        """Number of connections in use."""
        return len(self._in_use)

    @property
    def total_count(self) -> int:
        """Total number of connections."""
        return self.available_count + self.in_use_count

    async def initialize(self) -> None:
        """Initialize the pool with minimum connections."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info(
                f"Initializing {self._db_type.value} connection pool "
                f"(min={self._min_size}, max={self._max_size})"
            )

            # For PostgreSQL, use native pool
            if self._db_type == DatabaseType.POSTGRESQL:
                await self._init_postgresql_pool()
            else:
                # Create minimum number of connections
                for _ in range(self._min_size):
                    try:
                        pooled = await self._create_connection()
                        self._available.append(pooled)
                    except Exception as e:
                        logger.warning(f"Failed to pre-create connection: {e}")
                        self._stats.errors += 1
                        break

            self._initialized = True
            logger.info(
                f"Database connection pool initialized "
                f"(available={self.available_count})"
            )

    async def _init_postgresql_pool(self) -> None:
        """Initialize native PostgreSQL pool."""
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for PostgreSQL support. "
                "Install with: pip install asyncpg"
            )

        if self._connection_string:
            self._pg_pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=self._min_size,
                max_size=self._max_size,
                max_inactive_connection_lifetime=self._idle_timeout,
                **self._extra_options,
            )
        else:
            self._pg_pool = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._username,
                password=self._password,
                min_size=self._min_size,
                max_size=self._max_size,
                max_inactive_connection_lifetime=self._idle_timeout,
                **self._extra_options,
            )

        self._stats.connections_created = self._min_size

    async def _create_connection(self) -> PooledConnection:
        """Create a new database connection."""
        connection: Any = None

        if self._db_type == DatabaseType.SQLITE:
            if not AIOSQLITE_AVAILABLE:
                raise ImportError(
                    "aiosqlite is required for async SQLite support. "
                    "Install with: pip install aiosqlite"
                )
            database = self._database or ":memory:"
            connection = await aiosqlite.connect(database)
            connection.row_factory = aiosqlite.Row

        elif self._db_type == DatabaseType.MYSQL:
            if not AIOMYSQL_AVAILABLE:
                raise ImportError(
                    "aiomysql is required for MySQL support. "
                    "Install with: pip install aiomysql"
                )
            connection = await aiomysql.connect(
                host=self._host,
                port=self._port,
                db=self._database,
                user=self._username,
                password=self._password,
                **self._extra_options,
            )

        self._stats.connections_created += 1
        logger.debug(
            f"Created new {self._db_type.value} connection "
            f"(total created: {self._stats.connections_created})"
        )

        return PooledConnection(connection=connection, db_type=self._db_type)

    async def acquire(self, timeout: float = 30.0) -> Any:
        """
        Acquire a database connection from the pool.

        Args:
            timeout: Maximum time to wait for a connection

        Returns:
            Database connection

        Raises:
            TimeoutError: If no connection available within timeout
            RuntimeError: If pool is closed
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")

        if not self._initialized:
            await self.initialize()

        # For PostgreSQL, use native pool
        if self._db_type == DatabaseType.POSTGRESQL and self._pg_pool:
            self._stats.acquire_count += 1
            return await self._pg_pool.acquire(timeout=timeout)

        start_time = time.time()
        deadline = start_time + timeout

        while True:
            async with self._lock:
                # Try to get an available connection
                while self._available:
                    pooled = self._available.popleft()

                    # Check if connection is healthy
                    if pooled.is_stale(self._max_connection_age):
                        await self._close_connection(pooled)
                        self._stats.connections_recycled += 1
                        continue

                    if await self._health_check(pooled):
                        pooled.mark_used()
                        self._in_use.add(pooled)
                        self._stats.acquire_count += 1
                        return pooled.connection
                    else:
                        await self._close_connection(pooled)
                        continue

                # Create new connection if under max
                if self.total_count < self._max_size:
                    try:
                        pooled = await self._create_connection()
                        pooled.mark_used()
                        self._in_use.add(pooled)
                        self._stats.acquire_count += 1
                        return pooled.connection
                    except Exception as e:
                        logger.error(f"Failed to create connection: {e}")
                        self._stats.errors += 1

            # Check timeout
            if time.time() >= deadline:
                raise TimeoutError(
                    f"Timeout waiting for database connection "
                    f"(waited {timeout}s, pool size: {self.total_count}/{self._max_size})"
                )

            # Wait and retry
            self._stats.wait_count += 1
            await asyncio.sleep(0.1)

        # Record wait time
        wait_time = (time.time() - start_time) * 1000
        self._stats.total_wait_time_ms += wait_time

    async def release(self, connection: Any) -> None:
        """
        Release a connection back to the pool.

        Args:
            connection: The connection to release
        """
        if self._closed:
            # Close immediately if pool is closed
            await self._close_raw_connection(connection)
            return

        # For PostgreSQL native pool
        if self._db_type == DatabaseType.POSTGRESQL and self._pg_pool:
            await self._pg_pool.release(connection)
            self._stats.release_count += 1
            return

        async with self._lock:
            # Find the pooled connection
            pooled = None
            for p in self._in_use:
                if p.connection is connection:
                    pooled = p
                    break

            if pooled is None:
                logger.warning("Released connection not found in pool")
                await self._close_raw_connection(connection)
                return

            self._in_use.discard(pooled)
            pooled.release()

            # Check if we should keep it
            if pooled.is_stale(self._max_connection_age):
                await self._close_connection(pooled)
                self._stats.connections_recycled += 1
            elif self.available_count < self._max_size:
                self._available.append(pooled)
            else:
                await self._close_connection(pooled)

            self._stats.release_count += 1

    async def _health_check(self, pooled: PooledConnection) -> bool:
        """Check if a connection is healthy."""
        try:
            if self._db_type == DatabaseType.SQLITE:
                await pooled.connection.execute("SELECT 1")
            elif self._db_type == DatabaseType.MYSQL:
                async with pooled.connection.cursor() as cursor:
                    await cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.debug(f"Connection health check failed: {e}")
            return False

    async def _close_connection(self, pooled: PooledConnection) -> None:
        """Close a pooled connection."""
        await self._close_raw_connection(pooled.connection)
        self._stats.connections_closed += 1

    async def _close_raw_connection(self, connection: Any) -> None:
        """Close a raw database connection."""
        try:
            if hasattr(connection, "close"):
                if asyncio.iscoroutinefunction(connection.close):
                    await connection.close()
                else:
                    connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    async def cleanup_idle(self) -> int:
        """
        Clean up idle connections beyond the minimum.

        Returns:
            Number of connections cleaned up
        """
        if self._closed:
            return 0

        # PostgreSQL pool handles this internally
        if self._db_type == DatabaseType.POSTGRESQL:
            return 0

        cleaned = 0
        async with self._lock:
            # Keep at least min_size connections
            while len(self._available) > self._min_size and self._available:
                pooled = self._available[0]
                if pooled.is_idle(self._idle_timeout):
                    self._available.popleft()
                    await self._close_connection(pooled)
                    cleaned += 1
                else:
                    break

        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} idle connections")

        return cleaned

    async def close(self) -> None:
        """Close all connections and shut down the pool."""
        if self._closed:
            return

        async with self._lock:
            self._closed = True

            # Close PostgreSQL pool
            if self._pg_pool:
                await self._pg_pool.close()
                self._pg_pool = None

            # Close all available connections
            while self._available:
                pooled = self._available.popleft()
                await self._close_connection(pooled)

            # Close in-use connections
            for pooled in list(self._in_use):
                await self._close_connection(pooled)
            self._in_use.clear()

        logger.info("Database connection pool closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "db_type": self._db_type.value,
            "available": self.available_count,
            "in_use": self.in_use_count,
            "total": self.total_count,
            "min_size": self._min_size,
            "max_size": self._max_size,
            "connections_created": self._stats.connections_created,
            "connections_closed": self._stats.connections_closed,
            "connections_recycled": self._stats.connections_recycled,
            "acquire_count": self._stats.acquire_count,
            "release_count": self._stats.release_count,
            "wait_count": self._stats.wait_count,
            "avg_wait_time_ms": self._stats.avg_wait_time_ms,
            "errors": self._stats.errors,
        }

    async def __aenter__(self) -> "DatabaseConnectionPool":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class DatabasePoolManager:
    """
    Global manager for database connection pools.

    Provides a singleton-like interface for managing multiple
    database pools across the application.
    """

    _instance: Optional["DatabasePoolManager"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self._pools: Dict[str, DatabaseConnectionPool] = {}
        self._pool_lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "DatabasePoolManager":
        """Get the singleton instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def get_pool(
        self,
        name: str,
        db_type: Union[DatabaseType, str],
        **config: Any,
    ) -> DatabaseConnectionPool:
        """
        Get or create a named connection pool.

        Args:
            name: Pool name/identifier
            db_type: Database type
            **config: Pool configuration

        Returns:
            DatabaseConnectionPool instance
        """
        async with self._pool_lock:
            if name not in self._pools:
                pool = DatabaseConnectionPool(db_type=db_type, **config)
                await pool.initialize()
                self._pools[name] = pool
            return self._pools[name]

    async def close_pool(self, name: str) -> None:
        """Close a specific pool."""
        async with self._pool_lock:
            if name in self._pools:
                await self._pools[name].close()
                del self._pools[name]

    async def close_all(self) -> None:
        """Close all pools."""
        async with self._pool_lock:
            for pool in self._pools.values():
                await pool.close()
            self._pools.clear()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools."""
        return {name: pool.get_stats() for name, pool in self._pools.items()}


# Convenience function for getting the global pool manager
async def get_pool_manager() -> DatabasePoolManager:
    """Get the global database pool manager."""
    return await DatabasePoolManager.get_instance()


__all__ = [
    "DatabaseType",
    "PoolStatistics",
    "PooledConnection",
    "DatabaseConnectionPool",
    "DatabasePoolManager",
    "get_pool_manager",
]
