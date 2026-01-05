"""
aiohttp WebSocket helper for orchestrator clients.

Kept in infrastructure/http to satisfy UnifiedHttpClient enforcement while
allowing WebSocket connections that UnifiedHttpClient does not support.
"""

from __future__ import annotations

from typing import Any

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False


class AiohttpWebSocketSession:
    """Thin wrapper around aiohttp.ClientSession for WebSocket usage."""

    def __init__(self, timeout: float) -> None:
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for WebSocket support")
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        self._session = aiohttp.ClientSession(timeout=client_timeout)

    async def ws_connect(self, url: str):
        return self._session.ws_connect(url)

    async def close(self) -> None:
        await self._session.close()

    @staticmethod
    def is_text(msg: Any) -> bool:
        return msg.type == aiohttp.WSMsgType.TEXT

    @staticmethod
    def is_error(msg: Any) -> bool:
        return msg.type == aiohttp.WSMsgType.ERROR

    @staticmethod
    def is_closed(msg: Any) -> bool:
        return msg.type == aiohttp.WSMsgType.CLOSED
