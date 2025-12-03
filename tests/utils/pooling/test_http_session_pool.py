"""
Tests for HTTP session pool.

Covers:
- Pool initialization and lifecycle
- Session acquire and release
- Pool exhaustion and timeout handling
- Per-host session management
- Request convenience methods
- Statistics tracking
- Manager singleton behavior
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from casare_rpa.utils.pooling.http_session_pool import (
    SessionStatistics,
    PooledSession,
    HttpSessionPool,
    HttpSessionManager,
    get_session_manager,
)


class TestSessionStatistics:
    """Tests for SessionStatistics dataclass."""

    def test_default_values(self):
        """Statistics should initialize with zeros."""
        stats = SessionStatistics()

        assert stats.sessions_created == 0
        assert stats.sessions_closed == 0
        assert stats.requests_made == 0
        assert stats.requests_succeeded == 0
        assert stats.requests_failed == 0
        assert stats.total_request_time_ms == 0.0
        assert stats.bytes_sent == 0
        assert stats.bytes_received == 0

    def test_avg_request_time_with_no_requests(self):
        """Average request time should be 0 when no requests made."""
        stats = SessionStatistics()
        assert stats.avg_request_time_ms == 0.0

    def test_avg_request_time_calculation(self):
        """Average request time should calculate correctly."""
        stats = SessionStatistics(requests_made=4, total_request_time_ms=100.0)
        assert stats.avg_request_time_ms == 25.0

    def test_success_rate_with_no_requests(self):
        """Success rate should be 0 when no requests made."""
        stats = SessionStatistics()
        assert stats.success_rate == 0.0

    def test_success_rate_calculation(self):
        """Success rate should calculate correctly."""
        stats = SessionStatistics(requests_made=10, requests_succeeded=8)
        assert stats.success_rate == 80.0


class TestPooledSession:
    """Tests for PooledSession wrapper."""

    def test_initialization(self):
        """PooledSession should initialize correctly."""
        mock_session = Mock()
        pooled = PooledSession(
            session=mock_session,
            base_url="https://example.com",
        )

        assert pooled.session is mock_session
        assert pooled.base_url == "https://example.com"
        assert pooled.request_count == 0
        assert pooled.is_in_use is False

    def test_initialization_without_base_url(self):
        """PooledSession should work without base_url."""
        mock_session = Mock()
        pooled = PooledSession(
            session=mock_session,
            base_url=None,
        )

        assert pooled.base_url is None

    def test_mark_used_updates_state(self):
        """mark_used should update tracking fields."""
        mock_session = Mock()
        pooled = PooledSession(session=mock_session, base_url=None)
        original_last_used = pooled.last_used

        time.sleep(0.01)
        pooled.mark_used()

        assert pooled.is_in_use is True
        assert pooled.request_count == 1
        assert pooled.last_used > original_last_used

    def test_release_marks_available(self):
        """release should mark session as not in use."""
        mock_session = Mock()
        pooled = PooledSession(session=mock_session, base_url=None)
        pooled.mark_used()
        assert pooled.is_in_use is True

        pooled.release()

        assert pooled.is_in_use is False

    def test_is_stale_detects_old_sessions(self):
        """is_stale should return True for old sessions."""
        mock_session = Mock()
        pooled = PooledSession(session=mock_session, base_url=None)
        # Force created_at to be in the past
        pooled.created_at = time.time() - 100

        assert pooled.is_stale(max_age_seconds=50) is True
        assert pooled.is_stale(max_age_seconds=200) is False

    def test_is_idle_detects_unused_sessions(self):
        """is_idle should return True for unused sessions."""
        mock_session = Mock()
        pooled = PooledSession(session=mock_session, base_url=None)
        # Force last_used to be in the past
        pooled.last_used = time.time() - 100

        assert pooled.is_idle(idle_timeout_seconds=50) is True
        assert pooled.is_idle(idle_timeout_seconds=200) is False

    def test_hash_and_equality(self):
        """PooledSession should be hashable and comparable."""
        mock_session1 = Mock()
        mock_session2 = Mock()
        pooled1 = PooledSession(session=mock_session1, base_url=None)
        pooled2 = PooledSession(session=mock_session2, base_url=None)
        pooled1_copy = pooled1

        # Same object should be equal
        assert pooled1 == pooled1_copy
        assert hash(pooled1) == hash(pooled1_copy)

        # Different sessions should not be equal
        assert pooled1 != pooled2

        # Should be hashable for use in sets
        pool_set = {pooled1, pooled2}
        assert len(pool_set) == 2


class TestHttpSessionPool:
    """Tests for HttpSessionPool."""

    @pytest.fixture
    def mock_aiohttp(self):
        """Mock aiohttp module."""
        with patch(
            "casare_rpa.utils.pooling.http_session_pool.AIOHTTP_AVAILABLE", True
        ):
            with patch(
                "casare_rpa.utils.pooling.http_session_pool.aiohttp"
            ) as mock_module:
                mock_session = AsyncMock()
                mock_session.closed = False
                mock_session.close = AsyncMock()
                mock_session.request = AsyncMock(return_value=AsyncMock())

                mock_module.ClientSession = Mock(return_value=mock_session)
                mock_module.TCPConnector = Mock()
                mock_module.ClientTimeout = Mock()

                yield mock_module

    @pytest.mark.asyncio
    async def test_initialization(self, mock_aiohttp):
        """Pool should initialize with correct settings."""
        pool = HttpSessionPool(
            max_sessions=5,
            request_timeout=10.0,
            user_agent="TestAgent",
        )

        assert pool._max_sessions == 5
        assert pool._request_timeout == 10.0
        assert pool._user_agent == "TestAgent"
        assert pool.available_count == 0
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_creates_session(self, mock_aiohttp):
        """acquire should create new session when pool is empty."""
        pool = HttpSessionPool(max_sessions=5)

        session = await pool.acquire()

        assert session is not None
        assert pool.in_use_count == 1
        assert pool._stats.sessions_created == 1

        await pool.release(session)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_with_url_creates_host_specific_session(self, mock_aiohttp):
        """acquire with URL should create host-specific session."""
        pool = HttpSessionPool(max_sessions=5)

        session = await pool.acquire(url="https://api.example.com/v1/resource")

        assert session is not None
        assert pool.in_use_count == 1

        await pool.release(session, url="https://api.example.com/v1/resource")
        await pool.close()

    @pytest.mark.asyncio
    async def test_release_returns_session_to_pool(self, mock_aiohttp):
        """release should return session to available pool."""
        pool = HttpSessionPool(max_sessions=5)

        session = await pool.acquire()
        assert pool.available_count == 0

        await pool.release(session)

        assert pool.available_count == 1
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_respects_max_sessions(self, mock_aiohttp):
        """acquire should not exceed max_sessions."""
        pool = HttpSessionPool(max_sessions=2)

        session1 = await pool.acquire()
        session2 = await pool.acquire()

        assert pool.total_count == 2
        assert pool.in_use_count == 2

        await pool.release(session1)
        await pool.release(session2)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_timeout_when_pool_exhausted(self, mock_aiohttp):
        """acquire should raise TimeoutError when pool exhausted."""
        pool = HttpSessionPool(max_sessions=1)

        session1 = await pool.acquire()

        with pytest.raises(TimeoutError):
            await pool.acquire(timeout=0.2)

        await pool.release(session1)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_fails_when_closed(self, mock_aiohttp):
        """acquire should raise RuntimeError when pool is closed."""
        pool = HttpSessionPool(max_sessions=5)
        await pool.close()

        with pytest.raises(RuntimeError, match="closed"):
            await pool.acquire()

    @pytest.mark.asyncio
    async def test_close_cleans_up_all_sessions(self, mock_aiohttp):
        """close should close all sessions."""
        pool = HttpSessionPool(max_sessions=5)

        session1 = await pool.acquire()
        session2 = await pool.acquire()
        await pool.release(session1)

        await pool.close()

        assert pool.available_count == 0
        assert pool.in_use_count == 0

    @pytest.mark.asyncio
    async def test_get_stats_returns_metrics(self, mock_aiohttp):
        """get_stats should return pool metrics."""
        pool = HttpSessionPool(max_sessions=5)

        session = await pool.acquire()
        await pool.release(session)

        stats = pool.get_stats()

        assert stats["max_sessions"] == 5
        assert stats["sessions_created"] >= 1
        assert "requests_made" in stats
        assert "success_rate" in stats

        await pool.close()

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, mock_aiohttp):
        """Pool should work as async context manager."""
        async with HttpSessionPool(max_sessions=5) as pool:
            session = await pool.acquire()
            assert session is not None
            await pool.release(session)

        assert pool._closed is True

    @pytest.mark.asyncio
    async def test_cleanup_idle_removes_old_sessions(self, mock_aiohttp):
        """cleanup_idle should remove sessions past idle timeout."""
        pool = HttpSessionPool(max_sessions=5, idle_timeout=0.1)

        session = await pool.acquire()
        await pool.release(session)

        # Force session to be idle
        for pooled in pool._available:
            pooled.last_used = time.time() - 1

        cleaned = await pool.cleanup_idle()

        assert cleaned >= 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_request_convenience_method(self, mock_aiohttp):
        """request should handle session lifecycle automatically."""
        pool = HttpSessionPool(max_sessions=5)

        response = await pool.request("GET", "https://example.com/api")

        assert response is not None
        assert pool._stats.requests_made == 1
        assert pool._stats.requests_succeeded == 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_request_records_failure(self, mock_aiohttp):
        """request should record failed requests."""
        mock_aiohttp.ClientSession.return_value.request = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        pool = HttpSessionPool(max_sessions=5)

        with pytest.raises(Exception, match="Connection failed"):
            await pool.request("GET", "https://example.com/api")

        assert pool._stats.requests_made == 1
        assert pool._stats.requests_failed == 1

        await pool.close()

    @pytest.mark.asyncio
    async def test_get_convenience_method(self, mock_aiohttp):
        """get should make GET request."""
        pool = HttpSessionPool(max_sessions=5)

        response = await pool.get("https://example.com/api")

        mock_aiohttp.ClientSession.return_value.request.assert_called()
        assert response is not None

        await pool.close()

    @pytest.mark.asyncio
    async def test_post_convenience_method(self, mock_aiohttp):
        """post should make POST request."""
        pool = HttpSessionPool(max_sessions=5)

        response = await pool.post("https://example.com/api", json={"key": "value"})

        mock_aiohttp.ClientSession.return_value.request.assert_called()
        assert response is not None

        await pool.close()

    @pytest.mark.asyncio
    async def test_put_convenience_method(self, mock_aiohttp):
        """put should make PUT request."""
        pool = HttpSessionPool(max_sessions=5)

        response = await pool.put("https://example.com/api", json={"key": "value"})

        assert response is not None

        await pool.close()

    @pytest.mark.asyncio
    async def test_delete_convenience_method(self, mock_aiohttp):
        """delete should make DELETE request."""
        pool = HttpSessionPool(max_sessions=5)

        response = await pool.delete("https://example.com/api/1")

        assert response is not None

        await pool.close()


class TestHttpSessionPoolHostManagement:
    """Tests for per-host session management."""

    @pytest.fixture
    def mock_aiohttp(self):
        """Mock aiohttp module."""
        with patch(
            "casare_rpa.utils.pooling.http_session_pool.AIOHTTP_AVAILABLE", True
        ):
            with patch(
                "casare_rpa.utils.pooling.http_session_pool.aiohttp"
            ) as mock_module:
                mock_session = AsyncMock()
                mock_session.closed = False
                mock_session.close = AsyncMock()

                mock_module.ClientSession = Mock(return_value=mock_session)
                mock_module.TCPConnector = Mock()
                mock_module.ClientTimeout = Mock()

                yield mock_module

    def test_get_host_extracts_host_from_url(self, mock_aiohttp):
        """_get_host should extract host from URL."""
        pool = HttpSessionPool(max_sessions=5)

        host = pool._get_host("https://api.example.com/v1/resource")

        assert host == "https://api.example.com"

    def test_get_host_includes_port(self, mock_aiohttp):
        """_get_host should include port in host."""
        pool = HttpSessionPool(max_sessions=5)

        host = pool._get_host("https://api.example.com:8080/v1/resource")

        assert host == "https://api.example.com:8080"

    @pytest.mark.asyncio
    async def test_host_sessions_tracked_separately(self, mock_aiohttp):
        """Sessions should be tracked per host."""
        pool = HttpSessionPool(max_sessions=10)

        session1 = await pool.acquire(url="https://api1.example.com/v1")
        await pool.release(session1, url="https://api1.example.com/v1")

        session2 = await pool.acquire(url="https://api2.example.com/v1")
        await pool.release(session2, url="https://api2.example.com/v1")

        assert len(pool._host_sessions) == 2
        assert "https://api1.example.com" in pool._host_sessions
        assert "https://api2.example.com" in pool._host_sessions

        await pool.close()


class TestHttpSessionManager:
    """Tests for HttpSessionManager singleton."""

    @pytest.fixture(autouse=True)
    async def cleanup_manager(self):
        """Clean up manager after each test."""
        yield
        await HttpSessionManager.reset_instance()

    @pytest.fixture
    def mock_aiohttp(self):
        """Mock aiohttp module."""
        with patch(
            "casare_rpa.utils.pooling.http_session_pool.AIOHTTP_AVAILABLE", True
        ):
            with patch(
                "casare_rpa.utils.pooling.http_session_pool.aiohttp"
            ) as mock_module:
                mock_session = AsyncMock()
                mock_session.closed = False
                mock_session.close = AsyncMock()
                mock_session.request = AsyncMock(return_value=AsyncMock())

                mock_module.ClientSession = Mock(return_value=mock_session)
                mock_module.TCPConnector = Mock()
                mock_module.ClientTimeout = Mock()

                yield mock_module

    @pytest.mark.asyncio
    async def test_singleton_instance(self, mock_aiohttp):
        """get_instance should return same instance."""
        manager1 = await HttpSessionManager.get_instance()
        manager2 = await HttpSessionManager.get_instance()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_pool_creates_default_pool(self, mock_aiohttp):
        """get_pool without host should create default pool."""
        manager = await HttpSessionManager.get_instance()

        pool1 = await manager.get_pool()
        pool2 = await manager.get_pool()

        assert pool1 is pool2
        assert isinstance(pool1, HttpSessionPool)

    @pytest.mark.asyncio
    async def test_get_pool_creates_host_specific_pool(self, mock_aiohttp):
        """get_pool with host should create host-specific pool."""
        manager = await HttpSessionManager.get_instance()

        pool1 = await manager.get_pool(host="api1.example.com")
        pool2 = await manager.get_pool(host="api2.example.com")

        assert pool1 is not pool2

    @pytest.mark.asyncio
    async def test_request_uses_default_pool(self, mock_aiohttp):
        """request should use default pool."""
        manager = await HttpSessionManager.get_instance()

        response = await manager.request("GET", "https://example.com/api")

        assert response is not None

    @pytest.mark.asyncio
    async def test_close_all_clears_all_pools(self, mock_aiohttp):
        """close_all should close all managed pools."""
        manager = await HttpSessionManager.get_instance()

        await manager.get_pool()
        await manager.get_pool(host="api.example.com")

        await manager.close_all()

        assert manager._default_pool is None
        assert len(manager._host_pools) == 0

    @pytest.mark.asyncio
    async def test_get_all_stats_returns_all_pool_stats(self, mock_aiohttp):
        """get_all_stats should return stats for all pools."""
        manager = await HttpSessionManager.get_instance()

        await manager.get_pool()
        await manager.get_pool(host="api.example.com")

        stats = manager.get_all_stats()

        assert "default" in stats
        assert "api.example.com" in stats


class TestGetSessionManager:
    """Tests for get_session_manager convenience function."""

    @pytest.fixture(autouse=True)
    async def cleanup_manager(self):
        """Clean up manager after each test."""
        yield
        await HttpSessionManager.reset_instance()

    @pytest.fixture
    def mock_aiohttp(self):
        """Mock aiohttp module."""
        with patch(
            "casare_rpa.utils.pooling.http_session_pool.AIOHTTP_AVAILABLE", True
        ):
            with patch(
                "casare_rpa.utils.pooling.http_session_pool.aiohttp"
            ) as mock_module:
                mock_session = AsyncMock()
                mock_session.closed = False

                mock_module.ClientSession = Mock(return_value=mock_session)
                mock_module.TCPConnector = Mock()
                mock_module.ClientTimeout = Mock()

                yield mock_module

    @pytest.mark.asyncio
    async def test_returns_manager_instance(self, mock_aiohttp):
        """get_session_manager should return manager instance."""
        manager = await get_session_manager()

        assert isinstance(manager, HttpSessionManager)


class TestPoolStaleSessionHandling:
    """Tests for stale session recycling."""

    @pytest.fixture
    def mock_aiohttp(self):
        """Mock aiohttp module."""
        with patch(
            "casare_rpa.utils.pooling.http_session_pool.AIOHTTP_AVAILABLE", True
        ):
            with patch(
                "casare_rpa.utils.pooling.http_session_pool.aiohttp"
            ) as mock_module:
                mock_session = AsyncMock()
                mock_session.closed = False
                mock_session.close = AsyncMock()

                mock_module.ClientSession = Mock(return_value=mock_session)
                mock_module.TCPConnector = Mock()
                mock_module.ClientTimeout = Mock()

                yield mock_module

    @pytest.mark.asyncio
    async def test_stale_session_closed_on_acquire(self, mock_aiohttp):
        """Stale sessions should be closed during acquire."""
        pool = HttpSessionPool(max_sessions=5, max_session_age=0.1)

        session = await pool.acquire()
        await pool.release(session)

        # Force session to be stale
        for pooled in pool._available:
            pooled.created_at = time.time() - 10

        initial_closed = pool._stats.sessions_closed

        session2 = await pool.acquire()

        # Stale session should have been closed
        assert pool._stats.sessions_closed > initial_closed

        await pool.release(session2)
        await pool.close()

    @pytest.mark.asyncio
    async def test_stale_session_closed_on_release(self, mock_aiohttp):
        """Stale sessions should be closed on release."""
        pool = HttpSessionPool(max_sessions=5, max_session_age=0.1)

        session = await pool.acquire()

        # Force session to be stale
        for pooled in pool._in_use:
            pooled.created_at = time.time() - 10

        initial_closed = pool._stats.sessions_closed
        await pool.release(session)

        # Stale session should have been closed
        assert pool._stats.sessions_closed > initial_closed

        await pool.close()


class TestPoolDefaultHeaders:
    """Tests for default header handling."""

    @pytest.fixture
    def mock_aiohttp(self):
        """Mock aiohttp module."""
        with patch(
            "casare_rpa.utils.pooling.http_session_pool.AIOHTTP_AVAILABLE", True
        ):
            with patch(
                "casare_rpa.utils.pooling.http_session_pool.aiohttp"
            ) as mock_module:
                mock_session = AsyncMock()
                mock_session.closed = False

                mock_module.ClientSession = Mock(return_value=mock_session)
                mock_module.TCPConnector = Mock()
                mock_module.ClientTimeout = Mock()

                yield mock_module

    @pytest.mark.asyncio
    async def test_default_headers_applied(self, mock_aiohttp):
        """Default headers should be applied to sessions."""
        default_headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        pool = HttpSessionPool(
            max_sessions=5,
            default_headers=default_headers,
        )

        await pool.acquire()

        # Check that ClientSession was called with headers
        call_args = mock_aiohttp.ClientSession.call_args
        assert "headers" in call_args.kwargs
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer token"
        assert call_args.kwargs["headers"]["X-Custom"] == "value"

        await pool.close()

    @pytest.mark.asyncio
    async def test_user_agent_included_in_headers(self, mock_aiohttp):
        """User-Agent should be included in headers."""
        pool = HttpSessionPool(
            max_sessions=5,
            user_agent="CustomAgent/1.0",
        )

        await pool.acquire()

        call_args = mock_aiohttp.ClientSession.call_args
        assert call_args.kwargs["headers"]["User-Agent"] == "CustomAgent/1.0"

        await pool.close()
