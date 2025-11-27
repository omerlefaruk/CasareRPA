"""
HTTP session pool for CasareRPA.

Provides session pooling for HTTP requests to improve performance
through connection reuse (HTTP keep-alive) and reduced SSL handshakes.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Optional, Set
from urllib.parse import urlparse

from loguru import logger

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


@dataclass
class SessionStatistics:
    """Statistics for HTTP session pool monitoring."""
    sessions_created: int = 0
    sessions_closed: int = 0
    requests_made: int = 0
    requests_succeeded: int = 0
    requests_failed: int = 0
    total_request_time_ms: float = 0.0
    bytes_sent: int = 0
    bytes_received: int = 0

    @property
    def avg_request_time_ms(self) -> float:
        """Average request time in milliseconds."""
        if self.requests_made == 0:
            return 0.0
        return self.total_request_time_ms / self.requests_made

    @property
    def success_rate(self) -> float:
        """Percentage of successful requests."""
        if self.requests_made == 0:
            return 0.0
        return (self.requests_succeeded / self.requests_made) * 100


@dataclass
class PooledSession:
    """An HTTP session managed by the pool."""
    session: Any  # aiohttp.ClientSession
    base_url: Optional[str]
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    request_count: int = 0
    is_in_use: bool = False
    _id: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._id = id(self.session)

    def __hash__(self) -> int:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PooledSession):
            return False
        return self._id == other._id

    def mark_used(self) -> None:
        """Mark the session as used."""
        self.last_used = time.time()
        self.request_count += 1
        self.is_in_use = True

    def release(self) -> None:
        """Mark the session as available."""
        self.is_in_use = False

    def is_stale(self, max_age_seconds: float) -> bool:
        """Check if session is older than max age."""
        return (time.time() - self.created_at) > max_age_seconds

    def is_idle(self, idle_timeout_seconds: float) -> bool:
        """Check if session has been idle too long."""
        return (time.time() - self.last_used) > idle_timeout_seconds


class HttpSessionPool:
    """
    Pool of reusable HTTP sessions for improved performance.

    Features:
    - Connection pooling with keep-alive
    - Per-host session management
    - Automatic session recycling
    - Configurable timeouts
    - SSL session reuse
    - Request/response statistics
    """

    def __init__(
        self,
        max_sessions: int = 10,
        max_connections_per_host: int = 10,
        max_session_age: float = 300.0,  # 5 minutes
        idle_timeout: float = 60.0,  # 1 minute
        request_timeout: float = 30.0,
        connect_timeout: float = 10.0,
        enable_compression: bool = True,
        user_agent: str = "CasareRPA/1.0",
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the HTTP session pool.

        Args:
            max_sessions: Maximum number of sessions in the pool
            max_connections_per_host: Max connections per host per session
            max_session_age: Maximum age of a session before recycling
            idle_timeout: Time after which idle sessions are closed
            request_timeout: Default timeout for requests
            connect_timeout: Timeout for establishing connections
            enable_compression: Enable automatic response decompression
            user_agent: User-Agent header value
            default_headers: Default headers for all requests
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for HTTP session pooling. "
                "Install with: pip install aiohttp"
            )

        self._max_sessions = max_sessions
        self._max_connections_per_host = max_connections_per_host
        self._max_session_age = max_session_age
        self._idle_timeout = idle_timeout
        self._request_timeout = request_timeout
        self._connect_timeout = connect_timeout
        self._enable_compression = enable_compression
        self._user_agent = user_agent
        self._default_headers = default_headers or {}

        # Pool state
        self._available: Deque[PooledSession] = deque()
        self._in_use: Set[PooledSession] = set()
        self._host_sessions: Dict[str, Deque[PooledSession]] = {}
        self._lock = asyncio.Lock()
        self._closed = False

        # Statistics
        self._stats = SessionStatistics()

    @property
    def available_count(self) -> int:
        """Number of available sessions."""
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        """Number of sessions in use."""
        return len(self._in_use)

    @property
    def total_count(self) -> int:
        """Total number of sessions."""
        return self.available_count + self.in_use_count

    def _get_host(self, url: str) -> str:
        """Extract host from URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def _create_session(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> PooledSession:
        """Create a new HTTP session."""
        connector = aiohttp.TCPConnector(
            limit_per_host=self._max_connections_per_host,
            enable_cleanup_closed=True,
            force_close=False,  # Enable keep-alive
        )

        timeout = aiohttp.ClientTimeout(
            total=self._request_timeout,
            connect=self._connect_timeout,
        )

        # Merge headers
        all_headers = {"User-Agent": self._user_agent}
        all_headers.update(self._default_headers)
        if headers:
            all_headers.update(headers)

        session = aiohttp.ClientSession(
            base_url=base_url,
            connector=connector,
            timeout=timeout,
            headers=all_headers,
            auto_decompress=self._enable_compression,
        )

        self._stats.sessions_created += 1
        logger.debug(
            f"Created new HTTP session "
            f"(total: {self._stats.sessions_created}, base_url: {base_url})"
        )

        return PooledSession(session=session, base_url=base_url)

    async def acquire(
        self,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> Any:
        """
        Acquire an HTTP session from the pool.

        Args:
            url: Optional URL to get a host-specific session
            headers: Additional headers for this session
            timeout: Maximum time to wait for a session

        Returns:
            aiohttp.ClientSession

        Raises:
            TimeoutError: If no session available within timeout
            RuntimeError: If pool is closed
        """
        if self._closed:
            raise RuntimeError("Session pool is closed")

        base_url = self._get_host(url) if url else None
        start_time = time.time()
        deadline = start_time + timeout

        while True:
            async with self._lock:
                # Try to get a host-specific session first
                if base_url and base_url in self._host_sessions:
                    host_queue = self._host_sessions[base_url]
                    while host_queue:
                        pooled = host_queue.popleft()
                        if not pooled.is_stale(self._max_session_age):
                            pooled.mark_used()
                            self._in_use.add(pooled)
                            return pooled.session
                        else:
                            await self._close_session(pooled)

                # Try to get any available session
                while self._available:
                    pooled = self._available.popleft()
                    if not pooled.is_stale(self._max_session_age):
                        pooled.mark_used()
                        self._in_use.add(pooled)
                        return pooled.session
                    else:
                        await self._close_session(pooled)

                # Create new session if under limit
                if self.total_count < self._max_sessions:
                    try:
                        pooled = await self._create_session(base_url, headers)
                        pooled.mark_used()
                        self._in_use.add(pooled)
                        return pooled.session
                    except Exception as e:
                        logger.error(f"Failed to create session: {e}")

            # Check timeout
            if time.time() >= deadline:
                raise TimeoutError(
                    f"Timeout waiting for HTTP session "
                    f"(waited {timeout}s, pool size: {self.total_count})"
                )

            await asyncio.sleep(0.1)

    async def release(self, session: Any, url: Optional[str] = None) -> None:
        """
        Release a session back to the pool.

        Args:
            session: The session to release
            url: URL to associate with host-specific pool
        """
        if self._closed:
            await self._close_raw_session(session)
            return

        async with self._lock:
            # Find the pooled session
            pooled = None
            for p in self._in_use:
                if p.session is session:
                    pooled = p
                    break

            if pooled is None:
                logger.warning("Released session not found in pool")
                await self._close_raw_session(session)
                return

            self._in_use.discard(pooled)
            pooled.release()

            # Check if we should keep it
            if pooled.is_stale(self._max_session_age):
                await self._close_session(pooled)
            else:
                # Add to host-specific queue if applicable
                base_url = pooled.base_url or (self._get_host(url) if url else None)
                if base_url:
                    if base_url not in self._host_sessions:
                        self._host_sessions[base_url] = deque()
                    self._host_sessions[base_url].append(pooled)
                else:
                    self._available.append(pooled)

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> "aiohttp.ClientResponse":
        """
        Make an HTTP request using a pooled session.

        This is a convenience method that handles session acquisition
        and release automatically.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments passed to session.request()

        Returns:
            aiohttp.ClientResponse
        """
        session = await self.acquire(url)
        start_time = time.time()

        try:
            self._stats.requests_made += 1
            response = await session.request(method, url, **kwargs)

            # Update statistics
            elapsed_ms = (time.time() - start_time) * 1000
            self._stats.total_request_time_ms += elapsed_ms
            self._stats.requests_succeeded += 1

            return response

        except Exception as e:
            self._stats.requests_failed += 1
            raise

        finally:
            await self.release(session, url)

    async def get(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def _close_session(self, pooled: PooledSession) -> None:
        """Close a pooled session."""
        await self._close_raw_session(pooled.session)
        self._stats.sessions_closed += 1

    async def _close_raw_session(self, session: Any) -> None:
        """Close a raw aiohttp session."""
        try:
            if not session.closed:
                await session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

    async def cleanup_idle(self) -> int:
        """
        Clean up idle sessions.

        Returns:
            Number of sessions cleaned up
        """
        if self._closed:
            return 0

        cleaned = 0
        async with self._lock:
            # Clean available sessions
            new_available: Deque[PooledSession] = deque()
            while self._available:
                pooled = self._available.popleft()
                if pooled.is_idle(self._idle_timeout):
                    await self._close_session(pooled)
                    cleaned += 1
                else:
                    new_available.append(pooled)
            self._available = new_available

            # Clean host-specific sessions
            for host in list(self._host_sessions.keys()):
                new_queue: Deque[PooledSession] = deque()
                while self._host_sessions[host]:
                    pooled = self._host_sessions[host].popleft()
                    if pooled.is_idle(self._idle_timeout):
                        await self._close_session(pooled)
                        cleaned += 1
                    else:
                        new_queue.append(pooled)
                if new_queue:
                    self._host_sessions[host] = new_queue
                else:
                    del self._host_sessions[host]

        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} idle HTTP sessions")

        return cleaned

    async def close(self) -> None:
        """Close all sessions and shut down the pool."""
        if self._closed:
            return

        async with self._lock:
            self._closed = True

            # Close available sessions
            while self._available:
                pooled = self._available.popleft()
                await self._close_session(pooled)

            # Close host-specific sessions
            for host_queue in self._host_sessions.values():
                while host_queue:
                    pooled = host_queue.popleft()
                    await self._close_session(pooled)
            self._host_sessions.clear()

            # Close in-use sessions
            for pooled in list(self._in_use):
                await self._close_session(pooled)
            self._in_use.clear()

        logger.info("HTTP session pool closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "available": self.available_count,
            "in_use": self.in_use_count,
            "total": self.total_count,
            "max_sessions": self._max_sessions,
            "hosts_tracked": len(self._host_sessions),
            "sessions_created": self._stats.sessions_created,
            "sessions_closed": self._stats.sessions_closed,
            "requests_made": self._stats.requests_made,
            "requests_succeeded": self._stats.requests_succeeded,
            "requests_failed": self._stats.requests_failed,
            "avg_request_time_ms": self._stats.avg_request_time_ms,
            "success_rate": self._stats.success_rate,
        }

    async def __aenter__(self) -> "HttpSessionPool":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class HttpSessionManager:
    """
    Global manager for HTTP session pools.

    Provides a singleton-like interface for managing HTTP sessions
    across the application with optional per-host optimization.
    """

    _instance: Optional["HttpSessionManager"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self._default_pool: Optional[HttpSessionPool] = None
        self._host_pools: Dict[str, HttpSessionPool] = {}
        self._pool_lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "HttpSessionManager":
        """Get the singleton instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def get_pool(
        self,
        host: Optional[str] = None,
        **config: Any,
    ) -> HttpSessionPool:
        """
        Get or create an HTTP session pool.

        Args:
            host: Optional host for host-specific pool
            **config: Pool configuration

        Returns:
            HttpSessionPool instance
        """
        async with self._pool_lock:
            if host:
                if host not in self._host_pools:
                    self._host_pools[host] = HttpSessionPool(**config)
                return self._host_pools[host]
            else:
                if self._default_pool is None:
                    self._default_pool = HttpSessionPool(**config)
                return self._default_pool

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> "aiohttp.ClientResponse":
        """
        Make a request using the appropriate pool.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Request arguments

        Returns:
            aiohttp.ClientResponse
        """
        pool = await self.get_pool()
        return await pool.request(method, url, **kwargs)

    async def close_all(self) -> None:
        """Close all pools."""
        async with self._pool_lock:
            if self._default_pool:
                await self._default_pool.close()
                self._default_pool = None

            for pool in self._host_pools.values():
                await pool.close()
            self._host_pools.clear()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools."""
        stats = {}
        if self._default_pool:
            stats["default"] = self._default_pool.get_stats()
        for host, pool in self._host_pools.items():
            stats[host] = pool.get_stats()
        return stats


# Convenience function for getting the global session manager
async def get_session_manager() -> HttpSessionManager:
    """Get the global HTTP session manager."""
    return await HttpSessionManager.get_instance()


__all__ = [
    "SessionStatistics",
    "PooledSession",
    "HttpSessionPool",
    "HttpSessionManager",
    "get_session_manager",
]
