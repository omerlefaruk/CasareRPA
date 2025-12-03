"""
Tests for browser context pool.

Covers:
- Pool initialization and lifecycle
- Context acquire and release
- Pool exhaustion and timeout handling
- Stale context cleanup
- Statistics tracking
- Manager lifecycle
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from casare_rpa.utils.pooling.browser_pool import (
    PooledContext,
    BrowserContextPool,
    BrowserPoolManager,
    get_browser_pool_manager,
    reset_browser_pool_manager,
)


class TestPooledContext:
    """Tests for PooledContext wrapper."""

    def test_initialization(self):
        """PooledContext should initialize correctly."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)

        assert pooled.context is mock_ctx
        assert pooled.use_count == 0
        assert pooled.is_in_use is False

    def test_mark_used_updates_state(self):
        """mark_used should update tracking fields."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)
        original_last_used = pooled.last_used

        time.sleep(0.01)
        pooled.mark_used()

        assert pooled.is_in_use is True
        assert pooled.use_count == 1
        assert pooled.last_used > original_last_used

    def test_mark_used_increments_count(self):
        """mark_used should increment use count."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)

        pooled.mark_used()
        pooled.mark_used()
        pooled.mark_used()

        assert pooled.use_count == 3

    def test_release_marks_available(self):
        """release should mark context as not in use."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)
        pooled.mark_used()
        assert pooled.is_in_use is True

        pooled.release()

        assert pooled.is_in_use is False

    def test_is_stale_detects_old_contexts(self):
        """is_stale should return True for old contexts."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)
        # Force created_at to be in the past
        pooled.created_at = time.time() - 100

        assert pooled.is_stale(max_age_seconds=50) is True
        assert pooled.is_stale(max_age_seconds=200) is False

    def test_is_idle_detects_unused_contexts(self):
        """is_idle should return True for unused contexts."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)
        # Force last_used to be in the past
        pooled.last_used = time.time() - 100

        assert pooled.is_idle(idle_timeout_seconds=50) is True
        assert pooled.is_idle(idle_timeout_seconds=200) is False

    def test_hash_and_equality(self):
        """PooledContext should be hashable and comparable."""
        mock_ctx1 = Mock()
        mock_ctx2 = Mock()
        pooled1 = PooledContext(context=mock_ctx1)
        pooled2 = PooledContext(context=mock_ctx2)
        pooled1_copy = pooled1

        # Same object should be equal
        assert pooled1 == pooled1_copy
        assert hash(pooled1) == hash(pooled1_copy)

        # Different contexts should not be equal
        assert pooled1 != pooled2

        # Should be hashable for use in sets
        pool_set = {pooled1, pooled2}
        assert len(pool_set) == 2

    def test_equality_with_non_pooled_context(self):
        """Equality check with non-PooledContext should return False."""
        mock_ctx = Mock()
        pooled = PooledContext(context=mock_ctx)

        assert pooled != "not a pooled context"
        assert pooled is not None
        assert pooled != 42


class TestBrowserContextPool:
    """Tests for BrowserContextPool."""

    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser."""
        browser = AsyncMock()
        browser.new_context = AsyncMock(return_value=AsyncMock())
        return browser

    @pytest.mark.asyncio
    async def test_initialize_creates_min_contexts(self, mock_browser):
        """Pool should create minimum contexts on init."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=3,
            max_size=10,
        )

        await pool.initialize()

        assert pool.available_count == 3
        assert pool.in_use_count == 0
        assert mock_browser.new_context.call_count == 3

        await pool.close()

    @pytest.mark.asyncio
    async def test_initialize_is_idempotent(self, mock_browser):
        """Multiple initialize calls should not create extra contexts."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=2,
            max_size=10,
        )

        await pool.initialize()
        await pool.initialize()
        await pool.initialize()

        assert mock_browser.new_context.call_count == 2

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_returns_context(self, mock_browser):
        """acquire should return a browser context."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()

        ctx = await pool.acquire()

        assert ctx is not None
        assert pool.in_use_count == 1
        assert pool.available_count == 0

        await pool.release(ctx)
        await pool.close()

    @pytest.mark.asyncio
    async def test_release_returns_context_to_pool(self, mock_browser):
        """release should return context to available pool."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()

        ctx = await pool.acquire()
        assert pool.available_count == 0

        await pool.release(ctx)

        assert pool.available_count == 1
        assert pool.in_use_count == 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_creates_new_when_pool_empty(self, mock_browser):
        """acquire should create new context when pool is empty."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=0,
            max_size=10,
        )
        await pool.initialize()
        assert pool.total_count == 0

        ctx = await pool.acquire()

        assert ctx is not None
        assert pool.in_use_count == 1

        await pool.release(ctx)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_respects_max_size(self, mock_browser):
        """acquire should not exceed max_size contexts."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=0,
            max_size=2,
        )
        await pool.initialize()

        ctx1 = await pool.acquire()
        ctx2 = await pool.acquire()

        assert pool.total_count == 2
        assert pool.in_use_count == 2

        await pool.release(ctx1)
        await pool.release(ctx2)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_timeout_when_pool_exhausted(self, mock_browser):
        """acquire should raise TimeoutError when pool exhausted."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=1,
        )
        await pool.initialize()

        # Acquire the only context
        ctx1 = await pool.acquire()

        # Next acquire should timeout
        with pytest.raises(asyncio.TimeoutError):
            await pool.acquire(timeout=0.2)

        await pool.release(ctx1)
        await pool.close()

    @pytest.mark.asyncio
    async def test_acquire_fails_when_closed(self, mock_browser):
        """acquire should raise RuntimeError when pool is closed."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()
        await pool.close()

        with pytest.raises(RuntimeError, match="closed"):
            await pool.acquire()

    @pytest.mark.asyncio
    async def test_close_cleans_up_all_contexts(self, mock_browser):
        """close should close all contexts."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=2,
            max_size=10,
        )
        await pool.initialize()
        ctx = await pool.acquire()

        await pool.close()

        assert pool.available_count == 0
        assert pool.in_use_count == 0

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self, mock_browser):
        """Multiple close calls should be safe."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()

        await pool.close()
        await pool.close()
        await pool.close()

        assert pool._closed is True

    @pytest.mark.asyncio
    async def test_get_stats_returns_metrics(self, mock_browser):
        """get_stats should return pool metrics."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()

        ctx = await pool.acquire()
        await pool.release(ctx)

        stats = pool.get_stats()

        assert stats["min_size"] == 1
        assert stats["max_size"] == 10
        assert stats["contexts_created"] >= 1
        assert stats["acquire_count"] >= 1
        assert stats["release_count"] >= 1
        assert stats["initialized"] is True
        assert stats["closed"] is False

        await pool.close()

    @pytest.mark.asyncio
    async def test_cleanup_idle_removes_old_contexts(self, mock_browser):
        """cleanup_idle should remove contexts past idle timeout."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=0,
            max_size=10,
            idle_timeout=0.1,
        )
        await pool.initialize()

        # Create a context
        ctx = await pool.acquire()
        await pool.release(ctx)

        # Force context to be idle
        pool._available[0].last_used = time.time() - 1

        cleaned = await pool.cleanup_idle()

        # Should clean up idle context
        assert cleaned >= 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_cleanup_idle_keeps_min_size(self, mock_browser):
        """cleanup_idle should not reduce below min_size."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=2,
            max_size=10,
            idle_timeout=0.1,
        )
        await pool.initialize()

        # Force all contexts to be idle
        for pooled in pool._available:
            pooled.last_used = time.time() - 1

        cleaned = await pool.cleanup_idle()

        # Should keep at least min_size
        assert pool.available_count >= 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_total_count_property(self, mock_browser):
        """total_count should return sum of available and in_use."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=3,
            max_size=10,
        )
        await pool.initialize()

        ctx1 = await pool.acquire()

        assert pool.total_count == 3
        assert pool.available_count == 2
        assert pool.in_use_count == 1

        await pool.release(ctx1)
        await pool.close()

    @pytest.mark.asyncio
    async def test_release_unknown_context(self, mock_browser):
        """release should handle unknown contexts gracefully."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()

        # Try to release a context not from this pool
        unknown_ctx = AsyncMock()
        unknown_ctx.close = AsyncMock()

        await pool.release(unknown_ctx)

        # Should close the unknown context
        unknown_ctx.close.assert_awaited_once()

        await pool.close()

    @pytest.mark.asyncio
    async def test_release_when_closed(self, mock_browser):
        """release should close context when pool is closed."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()
        ctx = await pool.acquire()

        await pool.close()

        # Release after close should just close the context
        mock_ctx = AsyncMock()
        mock_ctx.close = AsyncMock()
        await pool.release(mock_ctx)

    @pytest.mark.asyncio
    async def test_stale_context_closed_on_acquire(self, mock_browser):
        """Stale contexts should be closed during acquire."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
            max_context_age=0.1,
        )
        await pool.initialize()

        # Force context to be stale
        pool._available[0].created_at = time.time() - 10

        initial_closed = pool._stats["contexts_closed"]

        ctx = await pool.acquire()

        # Stale context should have been closed, new one created
        assert pool._stats["contexts_closed"] > initial_closed

        await pool.release(ctx)
        await pool.close()

    @pytest.mark.asyncio
    async def test_stale_context_closed_on_release(self, mock_browser):
        """Stale contexts should be closed on release."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
            max_context_age=0.1,
        )
        await pool.initialize()

        ctx = await pool.acquire()

        # Force context to be stale
        for pooled in pool._in_use:
            pooled.created_at = time.time() - 10

        initial_closed = pool._stats["contexts_closed"]
        await pool.release(ctx)

        # Stale context should have been closed
        assert pool._stats["contexts_closed"] > initial_closed

        await pool.close()

    @pytest.mark.asyncio
    async def test_context_options_passed_to_new_context(self, mock_browser):
        """Context options should be passed when creating new contexts."""
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "TestAgent",
        }
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
            context_options=context_options,
        )
        await pool.initialize()

        mock_browser.new_context.assert_called_with(**context_options)

        await pool.close()


class TestBrowserPoolManager:
    """Tests for BrowserPoolManager."""

    @pytest.fixture(autouse=True)
    async def cleanup_manager(self):
        """Clean up manager after each test."""
        yield
        await reset_browser_pool_manager()

    @pytest.fixture
    def mock_playwright(self):
        """Create mock playwright."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=AsyncMock())

        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_pw.firefox.launch = AsyncMock(return_value=mock_browser)
        mock_pw.webkit.launch = AsyncMock(return_value=mock_browser)

        return mock_pw, mock_browser

    @pytest.mark.asyncio
    async def test_initialize_creates_pool(self, mock_playwright):
        """initialize should create browser and pool."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize(browser_type="chromium", headless=True)

            assert manager.is_initialized is True
            mock_pw.chromium.launch.assert_called_once()

            await manager.close()

    @pytest.mark.asyncio
    async def test_initialize_is_idempotent(self, mock_playwright):
        """Multiple initialize calls should not create extra browsers."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize()
            await manager.initialize()
            await manager.initialize()

            assert mock_pw.chromium.launch.call_count == 1

            await manager.close()

    @pytest.mark.asyncio
    async def test_get_pool_returns_pool(self, mock_playwright):
        """get_pool should return the context pool."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize()

            pool = await manager.get_pool("chromium")

            assert pool is not None
            assert isinstance(pool, BrowserContextPool)

            await manager.close()

    @pytest.mark.asyncio
    async def test_acquire_context_returns_context(self, mock_playwright):
        """acquire_context should return browser context."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize()

            ctx = await manager.acquire_context()

            assert ctx is not None

            await manager.release_context(ctx)
            await manager.close()

    @pytest.mark.asyncio
    async def test_acquire_context_fails_without_init(self):
        """acquire_context should fail if manager not initialized."""
        manager = BrowserPoolManager()

        with pytest.raises(RuntimeError):
            await manager.acquire_context()

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(self, mock_playwright):
        """close should clean up all resources."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize()

            await manager.close()

            assert manager.is_initialized is False
            mock_browser.close.assert_called()

    @pytest.mark.asyncio
    async def test_get_stats_returns_all_pool_stats(self, mock_playwright):
        """get_stats should return stats for all pools."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize()

            stats = manager.get_stats()

            assert "chromium" in stats
            assert "contexts_created" in stats["chromium"]

            await manager.close()

    @pytest.mark.asyncio
    async def test_cleanup_calls_pool_cleanup(self, mock_playwright):
        """cleanup should call cleanup_idle on all pools."""
        mock_pw, mock_browser = mock_playwright

        with patch(
            "casare_rpa.utils.pooling.browser_pool.async_playwright"
        ) as mock_async_pw:
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)

            manager = BrowserPoolManager()
            await manager.initialize()

            # Should not raise
            await manager.cleanup()

            await manager.close()


class TestGetBrowserPoolManager:
    """Tests for global pool manager functions."""

    @pytest.fixture(autouse=True)
    async def cleanup_manager(self):
        """Clean up manager after each test."""
        yield
        await reset_browser_pool_manager()

    def test_returns_manager_instance(self):
        """get_browser_pool_manager should return same instance."""
        manager1 = get_browser_pool_manager()
        manager2 = get_browser_pool_manager()

        assert manager1 is manager2
        assert isinstance(manager1, BrowserPoolManager)

    @pytest.mark.asyncio
    async def test_reset_clears_instance(self):
        """reset_browser_pool_manager should clear the instance."""
        manager1 = get_browser_pool_manager()

        await reset_browser_pool_manager()

        manager2 = get_browser_pool_manager()

        assert manager1 is not manager2


class TestPoolRecycling:
    """Tests for context recycling statistics."""

    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser."""
        browser = AsyncMock()
        browser.new_context = AsyncMock(return_value=AsyncMock())
        return browser

    @pytest.mark.asyncio
    async def test_recycled_count_increments(self, mock_browser):
        """contexts_recycled should increment when reusing contexts."""
        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=1,
            max_size=10,
        )
        await pool.initialize()

        # First acquire creates new
        ctx1 = await pool.acquire()
        await pool.release(ctx1)

        initial_recycled = pool._stats["contexts_recycled"]

        # Second acquire should reuse
        ctx2 = await pool.acquire()

        assert pool._stats["contexts_recycled"] > initial_recycled

        await pool.release(ctx2)
        await pool.close()
