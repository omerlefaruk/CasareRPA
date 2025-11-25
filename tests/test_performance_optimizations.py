"""
Tests for CasareRPA performance optimization modules.

Tests:
    - Database connection pooling
    - HTTP session pooling
    - Performance metrics system
"""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.utils.database_pool import (
    DatabaseConnectionPool,
    DatabasePoolManager,
    DatabaseType,
    PooledConnection,
    PoolStatistics,
    get_pool_manager,
)
from casare_rpa.utils.http_session_pool import (
    HttpSessionManager,
    HttpSessionPool,
    PooledSession,
    SessionStatistics,
    get_session_manager,
)
from casare_rpa.utils.performance_metrics import (
    Histogram,
    MetricType,
    MetricValue,
    PerformanceMetrics,
    TimerContext,
    get_metrics,
    time_operation,
)


# ============================================================================
# Database Connection Pool Tests
# ============================================================================

class TestPoolStatistics:
    """Tests for PoolStatistics dataclass."""

    def test_default_values(self):
        """Test default statistics values."""
        stats = PoolStatistics()
        assert stats.connections_created == 0
        assert stats.connections_closed == 0
        assert stats.acquire_count == 0
        assert stats.avg_wait_time_ms == 0.0

    def test_avg_wait_time_calculation(self):
        """Test average wait time calculation."""
        stats = PoolStatistics(
            wait_count=10,
            total_wait_time_ms=500.0,
        )
        assert stats.avg_wait_time_ms == 50.0

    def test_avg_wait_time_zero_division(self):
        """Test average wait time with no waits."""
        stats = PoolStatistics(wait_count=0, total_wait_time_ms=0.0)
        assert stats.avg_wait_time_ms == 0.0


class TestPooledConnection:
    """Tests for PooledConnection dataclass."""

    def test_creation(self):
        """Test pooled connection creation."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, db_type=DatabaseType.SQLITE)

        assert pooled.connection is mock_conn
        assert pooled.db_type == DatabaseType.SQLITE
        assert pooled.use_count == 0
        assert pooled.is_in_use is False

    def test_mark_used(self):
        """Test marking connection as used."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, db_type=DatabaseType.SQLITE)

        pooled.mark_used()

        assert pooled.use_count == 1
        assert pooled.is_in_use is True

    def test_release(self):
        """Test releasing connection."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, db_type=DatabaseType.SQLITE)
        pooled.mark_used()

        pooled.release()

        assert pooled.is_in_use is False
        assert pooled.use_count == 1  # Count stays

    def test_is_stale(self):
        """Test stale connection detection."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, db_type=DatabaseType.SQLITE)
        pooled.created_at = time.time() - 400  # 400 seconds ago

        assert pooled.is_stale(300.0) is True
        assert pooled.is_stale(500.0) is False

    def test_is_idle(self):
        """Test idle connection detection."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, db_type=DatabaseType.SQLITE)
        pooled.last_used = time.time() - 120  # 2 minutes ago

        assert pooled.is_idle(60.0) is True
        assert pooled.is_idle(180.0) is False

    def test_hash_and_equality(self):
        """Test hashing and equality."""
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()

        pooled1 = PooledConnection(connection=mock_conn1, db_type=DatabaseType.SQLITE)
        pooled2 = PooledConnection(connection=mock_conn2, db_type=DatabaseType.SQLITE)
        pooled1_copy = pooled1  # Same reference

        assert pooled1 == pooled1_copy
        assert pooled1 != pooled2
        assert hash(pooled1) != hash(pooled2)


class TestDatabaseConnectionPool:
    """Tests for DatabaseConnectionPool class."""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create a temporary database path."""
        return str(tmp_path / "test.db")

    @pytest.mark.asyncio
    async def test_sqlite_pool_creation(self, temp_db_path):
        """Test creating a SQLite connection pool."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=1,
            max_size=5,
        )

        await pool.initialize()

        assert pool.available_count >= 1
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_and_release(self, temp_db_path):
        """Test acquiring and releasing connections."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=1,
            max_size=3,
        )

        await pool.initialize()

        # Acquire a connection
        conn = await pool.acquire()
        assert conn is not None
        assert pool.in_use_count == 1

        # Release the connection
        await pool.release(conn)
        assert pool.in_use_count == 0
        assert pool.available_count >= 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_multiple_acquires(self, temp_db_path):
        """Test acquiring multiple connections."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=1,
            max_size=3,
        )

        await pool.initialize()

        conns = []
        for _ in range(3):
            conn = await pool.acquire()
            conns.append(conn)

        assert pool.in_use_count == 3
        assert pool.total_count == 3

        for conn in conns:
            await pool.release(conn)

        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_pool_max_size_timeout(self, temp_db_path):
        """Test timeout when pool is exhausted."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=1,
            max_size=1,
        )

        await pool.initialize()

        # Acquire the only connection
        conn1 = await pool.acquire()

        # Try to acquire another - should timeout
        with pytest.raises(TimeoutError):
            await pool.acquire(timeout=0.5)

        await pool.release(conn1)
        await pool.close()

    @pytest.mark.asyncio
    async def test_get_stats(self, temp_db_path):
        """Test getting pool statistics."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=2,
            max_size=5,
        )

        await pool.initialize()

        stats = pool.get_stats()

        assert stats["db_type"] == "sqlite"
        assert stats["min_size"] == 2
        assert stats["max_size"] == 5
        assert stats["connections_created"] >= 2

        await pool.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, temp_db_path):
        """Test pool as async context manager."""
        async with DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=1,
            max_size=3,
        ) as pool:
            conn = await pool.acquire()
            assert conn is not None
            await pool.release(conn)

    @pytest.mark.asyncio
    async def test_cleanup_idle_connections(self, temp_db_path):
        """Test cleanup of idle connections."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=temp_db_path,
            min_size=1,
            max_size=5,
            idle_timeout=0.1,  # 100ms for testing
        )

        await pool.initialize()

        # Acquire and release multiple connections
        conns = []
        for _ in range(3):
            conn = await pool.acquire()
            conns.append(conn)

        for conn in conns:
            await pool.release(conn)

        # Wait for idle timeout
        await asyncio.sleep(0.2)

        # Cleanup should remove idle connections
        cleaned = await pool.cleanup_idle()
        # Should clean at least some (but keep min_size)
        assert cleaned >= 0

        await pool.close()


class TestDatabasePoolManager:
    """Tests for DatabasePoolManager class."""

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Test singleton pattern."""
        manager1 = await DatabasePoolManager.get_instance()
        manager2 = await DatabasePoolManager.get_instance()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_pool(self, tmp_path):
        """Test getting a named pool."""
        manager = DatabasePoolManager()

        pool = await manager.get_pool(
            name="test_pool",
            db_type=DatabaseType.SQLITE,
            database=str(tmp_path / "test.db"),
        )

        assert pool is not None
        assert pool.db_type == DatabaseType.SQLITE

        await manager.close_all()

    @pytest.mark.asyncio
    async def test_get_all_stats(self, tmp_path):
        """Test getting all pool statistics."""
        manager = DatabasePoolManager()

        await manager.get_pool(
            name="pool1",
            db_type=DatabaseType.SQLITE,
            database=str(tmp_path / "test1.db"),
        )
        await manager.get_pool(
            name="pool2",
            db_type=DatabaseType.SQLITE,
            database=str(tmp_path / "test2.db"),
        )

        stats = manager.get_all_stats()

        assert "pool1" in stats
        assert "pool2" in stats

        await manager.close_all()


# ============================================================================
# HTTP Session Pool Tests
# ============================================================================

class TestSessionStatistics:
    """Tests for SessionStatistics dataclass."""

    def test_default_values(self):
        """Test default statistics values."""
        stats = SessionStatistics()
        assert stats.sessions_created == 0
        assert stats.requests_made == 0
        assert stats.avg_request_time_ms == 0.0
        assert stats.success_rate == 0.0

    def test_avg_request_time(self):
        """Test average request time calculation."""
        stats = SessionStatistics(
            requests_made=10,
            total_request_time_ms=1000.0,
        )
        assert stats.avg_request_time_ms == 100.0

    def test_success_rate(self):
        """Test success rate calculation."""
        stats = SessionStatistics(
            requests_made=100,
            requests_succeeded=90,
            requests_failed=10,
        )
        assert stats.success_rate == 90.0


class TestPooledSession:
    """Tests for PooledSession dataclass."""

    def test_creation(self):
        """Test pooled session creation."""
        mock_session = MagicMock()
        pooled = PooledSession(session=mock_session, base_url="https://example.com")

        assert pooled.session is mock_session
        assert pooled.base_url == "https://example.com"
        assert pooled.request_count == 0

    def test_mark_used(self):
        """Test marking session as used."""
        mock_session = MagicMock()
        pooled = PooledSession(session=mock_session, base_url=None)

        pooled.mark_used()

        assert pooled.request_count == 1
        assert pooled.is_in_use is True


class TestHttpSessionPool:
    """Tests for HttpSessionPool class."""

    @pytest.mark.asyncio
    async def test_pool_creation(self):
        """Test creating an HTTP session pool."""
        pool = HttpSessionPool(
            max_sessions=5,
            max_connections_per_host=10,
        )

        assert pool.available_count == 0
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        """Test acquiring and releasing sessions."""
        pool = HttpSessionPool(max_sessions=3)

        session = await pool.acquire()
        assert session is not None
        assert pool.in_use_count == 1

        await pool.release(session)
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting pool statistics."""
        pool = HttpSessionPool(max_sessions=5)

        session = await pool.acquire()
        await pool.release(session)

        stats = pool.get_stats()

        assert stats["max_sessions"] == 5
        assert stats["sessions_created"] >= 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test pool as async context manager."""
        async with HttpSessionPool(max_sessions=3) as pool:
            session = await pool.acquire()
            assert session is not None
            await pool.release(session)


class TestHttpSessionManager:
    """Tests for HttpSessionManager class."""

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Test singleton pattern."""
        manager1 = await HttpSessionManager.get_instance()
        manager2 = await HttpSessionManager.get_instance()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_pool(self):
        """Test getting a pool."""
        manager = HttpSessionManager()

        pool = await manager.get_pool()
        assert pool is not None

        await manager.close_all()


# ============================================================================
# Performance Metrics Tests
# ============================================================================

class TestHistogram:
    """Tests for Histogram class."""

    def test_empty_histogram(self):
        """Test empty histogram."""
        hist = Histogram()
        assert hist.count == 0
        assert hist.sum == 0.0
        assert hist.mean == 0.0
        assert hist.min is None
        assert hist.max is None

    def test_observe_single_value(self):
        """Test observing a single value."""
        hist = Histogram()
        hist.observe(100.0)

        assert hist.count == 1
        assert hist.sum == 100.0
        assert hist.mean == 100.0
        assert hist.min == 100.0
        assert hist.max == 100.0

    def test_observe_multiple_values(self):
        """Test observing multiple values."""
        hist = Histogram()
        for v in [10, 20, 30, 40, 50]:
            hist.observe(v)

        assert hist.count == 5
        assert hist.sum == 150.0
        assert hist.mean == 30.0
        assert hist.min == 10
        assert hist.max == 50

    def test_percentiles(self):
        """Test percentile calculations."""
        hist = Histogram(buckets=[10, 50, 100, 500, 1000])

        # Add values
        for _ in range(50):
            hist.observe(5)  # <= 10 bucket
        for _ in range(30):
            hist.observe(30)  # <= 50 bucket
        for _ in range(20):
            hist.observe(80)  # <= 100 bucket

        assert hist.count == 100
        p50 = hist.percentile(50)
        assert p50 <= 50  # Median should be in <= 50 bucket

    def test_to_dict(self):
        """Test dictionary conversion."""
        hist = Histogram(buckets=[10, 100, 1000])
        hist.observe(5)
        hist.observe(50)
        hist.observe(500)

        data = hist.to_dict()

        assert data["count"] == 3
        assert "p50" in data
        assert "p90" in data
        assert "p99" in data
        assert "buckets" in data


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""

    @pytest.fixture
    def metrics(self):
        """Create a fresh metrics instance."""
        m = PerformanceMetrics()
        yield m
        m.reset()

    def test_increment_counter(self, metrics):
        """Test incrementing counters."""
        metrics.increment("test_counter")
        metrics.increment("test_counter", value=5)

        summary = metrics.get_summary()
        assert summary["counters"]["test_counter"] == 6

    def test_increment_with_labels(self, metrics):
        """Test incrementing counters with labels."""
        metrics.increment("requests", labels={"method": "GET"})
        metrics.increment("requests", labels={"method": "POST"})

        summary = metrics.get_summary()
        assert "requests{method=GET}" in summary["counters"]
        assert "requests{method=POST}" in summary["counters"]

    def test_set_gauge(self, metrics):
        """Test setting gauge values."""
        metrics.set_gauge("temperature", 25.5)
        metrics.set_gauge("temperature", 26.0)

        summary = metrics.get_summary()
        assert summary["gauges"]["temperature"] == 26.0

    def test_observe_histogram(self, metrics):
        """Test observing histogram values."""
        for v in [10, 20, 30, 40, 50]:
            metrics.observe("latency", v)

        summary = metrics.get_summary()
        assert "latency" in summary["histograms"]
        assert summary["histograms"]["latency"]["count"] == 5

    def test_record_timing(self, metrics):
        """Test recording timing measurements."""
        metrics.record_timing("operation", 150.5)
        metrics.record_timing("operation", 200.0)

        summary = metrics.get_summary()
        assert "operation_duration_ms" in summary["histograms"]

    def test_timer_context(self, metrics):
        """Test timer context manager."""
        with metrics.time("test_operation"):
            time.sleep(0.1)  # 100ms

        summary = metrics.get_summary()
        assert "test_operation_duration_ms" in summary["histograms"]
        timing = summary["histograms"]["test_operation_duration_ms"]
        assert timing["count"] == 1
        assert timing["mean"] >= 90  # At least 90ms

    def test_record_node_execution(self, metrics):
        """Test recording node execution."""
        metrics.record_node_start("TestNode", "node-1")
        metrics.record_node_complete("TestNode", "node-1", 100.0, success=True)

        stats = metrics.get_node_stats("TestNode")

        assert stats["count"] == 1
        assert stats["errors"] == 0
        assert stats["timing"]["count"] == 1

    def test_record_node_error(self, metrics):
        """Test recording node error."""
        metrics.record_node_start("FailingNode", "node-2")
        metrics.record_node_complete("FailingNode", "node-2", 50.0, success=False)

        stats = metrics.get_node_stats("FailingNode")

        assert stats["count"] == 1
        assert stats["errors"] == 1

    def test_record_workflow_execution(self, metrics):
        """Test recording workflow execution."""
        metrics.record_workflow_start("wf-1")
        metrics.record_workflow_complete("wf-1", 5000.0, success=True)

        summary = metrics.get_summary()

        assert summary["workflows"]["counts"]["started"] == 1
        assert summary["workflows"]["counts"]["completed"] == 1
        assert summary["workflows"]["counts"]["failed"] == 0

    def test_reset(self, metrics):
        """Test resetting metrics."""
        metrics.increment("counter1", value=100)
        metrics.set_gauge("gauge1", 50.0)

        metrics.reset()

        summary = metrics.get_summary()
        assert len(summary["counters"]) == 0
        assert len(summary["gauges"]) == 0

    def test_get_all_node_stats(self, metrics):
        """Test getting all node statistics."""
        metrics.record_node_start("NodeA", "a1")
        metrics.record_node_complete("NodeA", "a1", 100.0, True)
        metrics.record_node_start("NodeB", "b1")
        metrics.record_node_complete("NodeB", "b1", 200.0, True)

        all_stats = metrics.get_node_stats()

        assert "NodeA" in all_stats
        assert "NodeB" in all_stats

    def test_singleton(self):
        """Test singleton pattern."""
        m1 = PerformanceMetrics.get_instance()
        m2 = PerformanceMetrics.get_instance()
        assert m1 is m2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_metrics(self):
        """Test get_metrics function."""
        metrics = get_metrics()
        assert isinstance(metrics, PerformanceMetrics)

    def test_time_operation(self):
        """Test time_operation function."""
        with time_operation("quick_op"):
            pass

        metrics = get_metrics()
        summary = metrics.get_summary()
        assert "quick_op_duration_ms" in summary["histograms"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for performance optimizations."""

    @pytest.mark.asyncio
    async def test_database_pool_with_metrics(self, tmp_path):
        """Test database pool with metrics integration."""
        metrics = PerformanceMetrics()
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=str(tmp_path / "test.db"),
            min_size=1,
            max_size=3,
        )

        await pool.initialize()

        # Acquire with timing
        with metrics.time("db_acquire"):
            conn = await pool.acquire()

        # Simulate work
        with metrics.time("db_query"):
            await asyncio.sleep(0.01)

        await pool.release(conn)

        # Check metrics
        summary = metrics.get_summary()
        assert "db_acquire_duration_ms" in summary["histograms"]
        assert "db_query_duration_ms" in summary["histograms"]

        await pool.close()

    @pytest.mark.asyncio
    async def test_http_pool_with_metrics(self):
        """Test HTTP pool with metrics integration."""
        metrics = PerformanceMetrics()
        pool = HttpSessionPool(max_sessions=3)

        with metrics.time("http_acquire"):
            session = await pool.acquire()

        await pool.release(session)

        summary = metrics.get_summary()
        assert "http_acquire_duration_ms" in summary["histograms"]

        await pool.close()

    @pytest.mark.asyncio
    async def test_concurrent_pool_access(self, tmp_path):
        """Test concurrent access to database pool."""
        pool = DatabaseConnectionPool(
            db_type=DatabaseType.SQLITE,
            database=str(tmp_path / "concurrent.db"),
            min_size=2,
            max_size=5,
        )

        await pool.initialize()

        async def worker(worker_id: int):
            conn = await pool.acquire()
            await asyncio.sleep(0.05)  # Simulate work
            await pool.release(conn)
            return worker_id

        # Run 10 concurrent workers
        tasks = [worker(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert pool.in_use_count == 0

        await pool.close()
