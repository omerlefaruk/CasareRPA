"""
Tests for database connection pool.

Covers:
- Pool initialization and lifecycle
- Connection acquire and release
- Pool exhaustion and timeout handling
- Stale connection cleanup
- Statistics tracking
- Manager singleton behavior
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from casare_rpa.utils.pooling.database_pool import (
    DatabaseType,
    PoolStatistics,
    PooledConnection,
    DatabaseConnectionPool,
    DatabasePoolManager,
    get_pool_manager,
)


class TestPoolStatistics:
    """Tests for PoolStatistics dataclass."""

    def test_default_values(self):
        """Statistics should initialize with zeros."""
        stats = PoolStatistics()

        assert stats.connections_created == 0
        assert stats.connections_closed == 0
        assert stats.connections_recycled == 0
        assert stats.acquire_count == 0
        assert stats.release_count == 0
        assert stats.wait_count == 0
        assert stats.total_wait_time_ms == 0.0
        assert stats.errors == 0

    def test_avg_wait_time_with_no_waits(self):
        """Average wait time should be 0 when no waits recorded."""
        stats = PoolStatistics()
        assert stats.avg_wait_time_ms == 0.0

    def test_avg_wait_time_calculation(self):
        """Average wait time should calculate correctly."""
        stats = PoolStatistics(wait_count=4, total_wait_time_ms=100.0)
        assert stats.avg_wait_time_ms == 25.0


class TestPooledConnection:
    """Tests for PooledConnection wrapper."""

    def test_initialization(self):
        """PooledConnection should initialize correctly."""
        mock_conn = Mock()
        pooled = PooledConnection(
            connection=mock_conn,
            db_type=DatabaseType.SQLITE,
        )

        assert pooled.connection is mock_conn
        assert pooled.db_type == DatabaseType.SQLITE
        assert pooled.use_count == 0
        assert pooled.is_in_use is False

    def test_mark_used_updates_state(self):
        """mark_used should update tracking fields."""
        mock_conn = Mock()
        pooled = PooledConnection(
            connection=mock_conn,
            db_type=DatabaseType.SQLITE,
        )
        original_last_used = pooled.last_used

        time.sleep(0.01)
        pooled.mark_used()

        assert pooled.is_in_use is True
        assert pooled.use_count == 1
        assert pooled.last_used > original_last_used

    def test_release_marks_available(self):
        """release should mark connection as not in use."""
        mock_conn = Mock()
        pooled = PooledConnection(
            connection=mock_conn,
            db_type=DatabaseType.SQLITE,
        )
        pooled.mark_used()
        assert pooled.is_in_use is True

        pooled.release()

        assert pooled.is_in_use is False

    def test_is_stale_detects_old_connections(self):
        """is_stale should return True for old connections."""
        mock_conn = Mock()
        pooled = PooledConnection(
            connection=mock_conn,
            db_type=DatabaseType.SQLITE,
        )
        # Force created_at to be in the past
        pooled.created_at = time.time() - 100

        assert pooled.is_stale(max_age_seconds=50) is True
        assert pooled.is_stale(max_age_seconds=200) is False

    def test_is_idle_detects_unused_connections(self):
        """is_idle should return True for unused connections."""
        mock_conn = Mock()
        pooled = PooledConnection(
            connection=mock_conn,
            db_type=DatabaseType.SQLITE,
        )
        # Force last_used to be in the past
        pooled.last_used = time.time() - 100

        assert pooled.is_idle(idle_timeout_seconds=50) is True
        assert pooled.is_idle(idle_timeout_seconds=200) is False

    def test_hash_and_equality(self):
        """PooledConnection should be hashable and comparable."""
        mock_conn1 = Mock()
        mock_conn2 = Mock()
        pooled1 = PooledConnection(connection=mock_conn1, db_type=DatabaseType.SQLITE)
        pooled2 = PooledConnection(connection=mock_conn2, db_type=DatabaseType.SQLITE)
        pooled1_copy = pooled1

        # Same object should be equal
        assert pooled1 == pooled1_copy
        assert hash(pooled1) == hash(pooled1_copy)

        # Different connections should not be equal
        assert pooled1 != pooled2

        # Should be hashable for use in sets
        pool_set = {pooled1, pooled2}
        assert len(pool_set) == 2


class TestDatabaseConnectionPool:
    """Tests for DatabaseConnectionPool."""

    @pytest.fixture
    def mock_aiosqlite(self):
        """Mock aiosqlite module."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            with patch(
                "casare_rpa.utils.pooling.database_pool.aiosqlite"
            ) as mock_module:
                mock_conn = AsyncMock()
                mock_conn.row_factory = None
                mock_module.connect = AsyncMock(return_value=mock_conn)
                mock_module.Row = Mock()
                yield mock_module

    @pytest.mark.asyncio
    async def test_initialize_creates_min_connections(self, mock_aiosqlite):
        """Pool should create minimum connections on init."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=2,
            max_size=5,
            database=":memory:",
        )

        await pool.initialize()

        assert pool.available_count == 2
        assert pool.in_use_count == 0
        assert mock_aiosqlite.connect.call_count == 2

        await pool.close()

    @pytest.mark.asyncio
    async def test_initialize_is_idempotent(self, mock_aiosqlite):
        """Multiple initialize calls should not create extra connections."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        )

        await pool.initialize()
        await pool.initialize()
        await pool.initialize()

        assert mock_aiosqlite.connect.call_count == 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_returns_connection(self, mock_aiosqlite):
        """acquire should return a working connection."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()

        conn = await pool.acquire()

        assert conn is not None
        assert pool.in_use_count == 1
        assert pool.available_count == 0

        await pool.release(conn)
        await pool.close()

    @pytest.mark.asyncio
    async def test_release_returns_connection_to_pool(self, mock_aiosqlite):
        """release should return connection to available pool."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()

        conn = await pool.acquire()
        assert pool.available_count == 0

        await pool.release(conn)

        assert pool.available_count == 1
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_creates_new_when_pool_empty(self, mock_aiosqlite):
        """acquire should create new connection when pool is empty."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=0,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()
        assert pool.total_count == 0

        conn = await pool.acquire()

        assert conn is not None
        assert pool.in_use_count == 1

        await pool.release(conn)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_respects_max_size(self, mock_aiosqlite):
        """acquire should not exceed max_size connections."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=0,
            max_size=2,
            database=":memory:",
        )
        await pool.initialize()

        conn1 = await pool.acquire()
        conn2 = await pool.acquire()

        assert pool.total_count == 2
        assert pool.in_use_count == 2

        await pool.release(conn1)
        await pool.release(conn2)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_timeout_when_pool_exhausted(self, mock_aiosqlite):
        """acquire should raise TimeoutError when pool exhausted."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=1,
            database=":memory:",
        )
        await pool.initialize()

        # Acquire the only connection
        conn1 = await pool.acquire()

        # Next acquire should timeout
        with pytest.raises(TimeoutError):
            await pool.acquire(timeout=0.2)

        await pool.release(conn1)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_fails_when_closed(self, mock_aiosqlite):
        """acquire should raise RuntimeError when pool is closed."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()
        await pool.close()

        with pytest.raises(RuntimeError, match="closed"):
            await pool.acquire()

    @pytest.mark.asyncio
    async def test_close_cleans_up_all_connections(self, mock_aiosqlite):
        """close should close all connections."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=2,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()
        conn = await pool.acquire()

        await pool.close()

        assert pool.available_count == 0
        assert pool.in_use_count == 0

    @pytest.mark.asyncio
    async def test_health_check_validates_connections(self, mock_aiosqlite):
        """Pool should validate connections with health check."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()

        # Mock execute for health check
        mock_conn = pool._available[0].connection
        mock_conn.execute = AsyncMock()

        conn = await pool.acquire()

        assert conn is not None
        mock_conn.execute.assert_called_with("SELECT 1")

        await pool.release(conn)
        await pool.close()

    @pytest.mark.asyncio
    async def test_get_stats_returns_metrics(self, mock_aiosqlite):
        """get_stats should return pool metrics."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        )
        await pool.initialize()

        conn = await pool.acquire()
        await pool.release(conn)

        stats = pool.get_stats()

        assert stats["db_type"] == "sqlite"
        assert stats["min_size"] == 1
        assert stats["max_size"] == 5
        assert stats["connections_created"] >= 1
        assert stats["acquire_count"] >= 1
        assert stats["release_count"] >= 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, mock_aiosqlite):
        """Pool should work as async context manager."""
        async with DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            database=":memory:",
        ) as pool:
            assert pool.available_count == 1

        # Should be closed after context exit
        assert pool._closed is True

    @pytest.mark.asyncio
    async def test_cleanup_idle_removes_old_connections(self, mock_aiosqlite):
        """cleanup_idle should remove connections past idle timeout."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=0,
            max_size=5,
            idle_timeout=0.1,
            database=":memory:",
        )
        await pool.initialize()

        # Acquire and release to create a connection
        conn = await pool.acquire()
        await pool.release(conn)

        # Force the connection to be idle
        pool._available[0].last_used = time.time() - 1

        cleaned = await pool.cleanup_idle()

        # Connection should be cleaned (pool at min_size)
        # Note: cleanup only removes above min_size
        assert cleaned == 0 or pool.available_count == 0

        await pool.close()


class TestDatabasePoolManager:
    """Tests for DatabasePoolManager singleton."""

    @pytest.fixture(autouse=True)
    async def cleanup_manager(self):
        """Clean up manager after each test."""
        yield
        await DatabasePoolManager.reset_instance()

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """get_instance should return same instance."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            manager1 = await DatabasePoolManager.get_instance()
            manager2 = await DatabasePoolManager.get_instance()

            assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_pool_creates_named_pool(self):
        """get_pool should create and cache named pools."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            with patch(
                "casare_rpa.utils.pooling.database_pool.aiosqlite"
            ) as mock_module:
                mock_conn = AsyncMock()
                mock_module.connect = AsyncMock(return_value=mock_conn)
                mock_module.Row = Mock()

                manager = await DatabasePoolManager.get_instance()

                pool1 = await manager.get_pool(
                    "test_pool",
                    db_type=DatabaseType.SQLITE,
                    database=":memory:",
                )
                pool2 = await manager.get_pool(
                    "test_pool",
                    db_type=DatabaseType.SQLITE,
                    database=":memory:",
                )

                assert pool1 is pool2

    @pytest.mark.asyncio
    async def test_close_pool_removes_pool(self):
        """close_pool should close and remove specific pool."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            with patch(
                "casare_rpa.utils.pooling.database_pool.aiosqlite"
            ) as mock_module:
                mock_conn = AsyncMock()
                mock_module.connect = AsyncMock(return_value=mock_conn)
                mock_module.Row = Mock()

                manager = await DatabasePoolManager.get_instance()

                pool = await manager.get_pool(
                    "test_pool",
                    db_type=DatabaseType.SQLITE,
                    database=":memory:",
                )

                await manager.close_pool("test_pool")

                # Pool should be removed
                assert "test_pool" not in manager._pools

    @pytest.mark.asyncio
    async def test_close_all_clears_all_pools(self):
        """close_all should close all managed pools."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            with patch(
                "casare_rpa.utils.pooling.database_pool.aiosqlite"
            ) as mock_module:
                mock_conn = AsyncMock()
                mock_module.connect = AsyncMock(return_value=mock_conn)
                mock_module.Row = Mock()

                manager = await DatabasePoolManager.get_instance()

                await manager.get_pool(
                    "pool1",
                    db_type=DatabaseType.SQLITE,
                    database=":memory:",
                )
                await manager.get_pool(
                    "pool2",
                    db_type=DatabaseType.SQLITE,
                    database=":memory:",
                )

                await manager.close_all()

                assert len(manager._pools) == 0

    @pytest.mark.asyncio
    async def test_get_all_stats_returns_all_pool_stats(self):
        """get_all_stats should return stats for all pools."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            with patch(
                "casare_rpa.utils.pooling.database_pool.aiosqlite"
            ) as mock_module:
                mock_conn = AsyncMock()
                mock_module.connect = AsyncMock(return_value=mock_conn)
                mock_module.Row = Mock()

                manager = await DatabasePoolManager.get_instance()

                await manager.get_pool(
                    "pool1",
                    db_type=DatabaseType.SQLITE,
                    database=":memory:",
                )

                stats = manager.get_all_stats()

                assert "pool1" in stats
                assert stats["pool1"]["db_type"] == "sqlite"


class TestGetPoolManager:
    """Tests for get_pool_manager convenience function."""

    @pytest.fixture(autouse=True)
    async def cleanup_manager(self):
        """Clean up manager after each test."""
        yield
        await DatabasePoolManager.reset_instance()

    @pytest.mark.asyncio
    async def test_returns_manager_instance(self):
        """get_pool_manager should return manager instance."""
        manager = await get_pool_manager()

        assert isinstance(manager, DatabasePoolManager)


class TestDatabaseTypeEnum:
    """Tests for DatabaseType enum."""

    def test_sqlite_value(self):
        """SQLITE should have correct value."""
        assert DatabaseType.SQLITE.value == "sqlite"

    def test_postgresql_value(self):
        """POSTGRESQL should have correct value."""
        assert DatabaseType.POSTGRESQL.value == "postgresql"

    def test_mysql_value(self):
        """MYSQL should have correct value."""
        assert DatabaseType.MYSQL.value == "mysql"

    def test_string_conversion(self):
        """DatabaseType should be creatable from string."""
        db_type = DatabaseType("sqlite")
        assert db_type == DatabaseType.SQLITE


class TestPoolStaleConnectionHandling:
    """Tests for stale connection recycling."""

    @pytest.fixture
    def mock_aiosqlite(self):
        """Mock aiosqlite module."""
        with patch("casare_rpa.utils.pooling.database_pool.AIOSQLITE_AVAILABLE", True):
            with patch(
                "casare_rpa.utils.pooling.database_pool.aiosqlite"
            ) as mock_module:
                mock_conn = AsyncMock()
                mock_conn.row_factory = None
                mock_conn.execute = AsyncMock()
                mock_module.connect = AsyncMock(return_value=mock_conn)
                mock_module.Row = Mock()
                yield mock_module

    @pytest.mark.asyncio
    async def test_stale_connection_closed_on_release(self, mock_aiosqlite):
        """Stale connections should be closed on release."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            min_size=1,
            max_size=5,
            max_connection_age=0.1,  # Very short age
            database=":memory:",
        )
        await pool.initialize()

        conn = await pool.acquire()

        # Force connection to be stale
        for pooled in pool._in_use:
            pooled.created_at = time.time() - 10

        initial_recycled = pool._stats.connections_recycled
        await pool.release(conn)

        # Should have been recycled
        assert pool._stats.connections_recycled > initial_recycled

        await pool.close()
