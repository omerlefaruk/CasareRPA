"""
Auto-discovery system for robots to find and connect to orchestrator.

Implements zero-config robot startup with automatic orchestrator discovery.
"""

import asyncio
import os
from typing import Optional
from loguru import logger

from casare_rpa.infrastructure.services import get_service_registry


class RobotAutoDiscovery:
    """Automatically discover and connect to orchestrator."""

    def __init__(self):
        self._registry = get_service_registry()
        self._discovered_url: Optional[str] = None

    async def discover_orchestrator(self) -> Optional[str]:
        """
        Find orchestrator URL using cascading discovery.

        Order of discovery:
        1. Environment variable (CASARE_ORCHESTRATOR_URL, ORCHESTRATOR_URL)
        2. Local orchestrator (localhost:8000)
        3. Tunneled orchestrator (api.casare.net)

        Returns:
            Orchestrator URL if found, None otherwise
        """
        # 1. Check environment variables
        env_url = self._get_orchestrator_from_env()
        if env_url:
            if await self._verify_orchestrator(env_url):
                logger.info(f"Discovered orchestrator from environment: {env_url}")
                self._discovered_url = env_url
                return env_url
            else:
                logger.warning(f"Orchestrator specified in env ({env_url}) is not responding")

        # 2. Try local orchestrator
        local_url = "http://localhost:8000"
        if await self._verify_orchestrator(local_url):
            logger.info(f"Discovered local orchestrator: {local_url}")
            self._discovered_url = local_url
            return local_url

        # 3. Try tunneled orchestrator
        tunnel_url = "https://api.casare.net"
        if await self._verify_orchestrator(tunnel_url):
            logger.info(f"Discovered tunneled orchestrator: {tunnel_url}")
            self._discovered_url = tunnel_url
            return tunnel_url

        # Could not find orchestrator
        logger.warning("No orchestrator found via auto-discovery")
        return None

    def _get_orchestrator_from_env(self) -> Optional[str]:
        """Get orchestrator URL from environment variables."""
        candidates = [
            "CASARE_ORCHESTRATOR_URL",
            "ORCHESTRATOR_URL",
            "CASARE_API_URL",
        ]

        for var in candidates:
            url = os.getenv(var)
            if url:
                # Ensure it's an HTTP URL not WebSocket
                if url.startswith("ws://") or url.startswith("wss://"):
                    url = url.replace("ws://", "http://").replace("wss://", "https://")
                return url

        return None

    async def _verify_orchestrator(self, url: str, timeout: float = 5.0) -> bool:
        """Verify that an orchestrator is reachable and responding."""
        try:
            import aiohttp

            health_url = f"{url}/health"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_url, timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if 200 <= resp.status < 300:
                        return True
                    elif resp.status == 503:
                        # Service starting
                        logger.debug(f"Orchestrator at {url} is starting (503)")
                        return False
                    else:
                        logger.debug(f"Orchestrator at {url} returned {resp.status}")
                        return False
        except asyncio.TimeoutError:
            logger.debug(f"Timeout checking orchestrator at {url}")
            return False
        except Exception as e:
            logger.debug(f"Error checking orchestrator at {url}: {e}")
            return False

    async def wait_for_orchestrator(
        self, timeout: int = 60, check_interval: float = 2.0
    ) -> Optional[str]:
        """
        Wait for orchestrator to become available.

        Args:
            timeout: Maximum time to wait in seconds
            check_interval: How often to check in seconds

        Returns:
            Orchestrator URL if found, None if timeout
        """
        logger.info(f"Waiting for orchestrator (timeout: {timeout}s)")

        start = asyncio.get_event_loop().time()
        attempt = 0

        while True:
            attempt += 1
            url = await self.discover_orchestrator()

            if url:
                return url

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                logger.error(f"Timeout waiting for orchestrator after {timeout}s")
                return None

            if attempt % 5 == 0:
                logger.info(f"Still waiting for orchestrator... ({int(elapsed)}s elapsed)")

            await asyncio.sleep(check_interval)

    def get_discovered_url(self) -> Optional[str]:
        """Get the last discovered orchestrator URL."""
        return self._discovered_url

    async def get_smart_orchestrator_url(self) -> str:
        """
        Get orchestrator URL with smart fallback.

        Returns:
            Discovered URL if available, otherwise sensible default
        """
        if self._discovered_url:
            return self._discovered_url

        # Try discovery
        discovered = await self.discover_orchestrator()
        if discovered:
            return discovered

        # Fallback to localhost (assume it will start soon)
        return "http://localhost:8000"


def get_auto_discovery() -> RobotAutoDiscovery:
    """Get singleton auto-discovery instance."""
    if not hasattr(get_auto_discovery, "_instance"):
        get_auto_discovery._instance = RobotAutoDiscovery()
    return get_auto_discovery._instance
