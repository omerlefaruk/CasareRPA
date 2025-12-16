"""
Service registry and health checking for CasareRPA platform.

Provides centralized service discovery and health monitoring for:
- Orchestrator API
- Database (PostgreSQL)
- Cloudflare Tunnel
- Redis (optional)
"""

import asyncio
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, List
import socket

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

from loguru import logger


class ServiceState(str, Enum):
    """Service health states."""

    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ServiceStatus:
    """Status of a service."""

    name: str
    state: ServiceState
    url: Optional[str] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    last_checked: Optional[str] = None
    required: bool = True


class ServiceRegistry:
    """Central registry for CasareRPA services with health checking."""

    SERVICES = {
        "orchestrator": {
            "urls": ["http://localhost:8000", "https://api.casare.net"],
            "health_path": "/health",
            "required": True,
            "timeout": 5,
        },
        "database": {
            "type": "postgres",
            "required": True,
            "timeout": 5,
        },
        "tunnel": {
            "urls": ["https://api.casare.net"],
            "health_path": "/health",
            "required": False,
            "timeout": 10,
        },
        "redis": {
            "urls": ["redis://localhost:6379"],
            "required": False,
            "timeout": 3,
        },
    }

    def __init__(self):
        self._status_cache: Dict[str, ServiceStatus] = {}
        self._check_lock = asyncio.Lock()

    async def check_all_services(self) -> Dict[str, ServiceStatus]:
        """Check health of all registered services."""
        async with self._check_lock:
            tasks = []
            for service_name in self.SERVICES:
                tasks.append(self.check_service(service_name))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            status_map = {}
            for i, service_name in enumerate(self.SERVICES):
                if isinstance(results[i], Exception):
                    status_map[service_name] = ServiceStatus(
                        name=service_name,
                        state=ServiceState.OFFLINE,
                        error=str(results[i]),
                        required=self.SERVICES[service_name].get("required", False),
                    )
                else:
                    status_map[service_name] = results[i]

            self._status_cache = status_map
            return status_map

    async def check_service(self, name: str) -> ServiceStatus:
        """Check health of a specific service."""
        if name not in self.SERVICES:
            return ServiceStatus(
                name=name,
                state=ServiceState.UNKNOWN,
                error=f"Unknown service: {name}",
            )

        config = self.SERVICES[name]

        # Check based on service type
        if config.get("type") == "postgres":
            return await self._check_postgres()
        elif "urls" in config:
            return await self._check_http_service(name, config)
        else:
            return ServiceStatus(
                name=name,
                state=ServiceState.UNKNOWN,
                error="No checker configured",
            )

    async def _check_http_service(self, name: str, config: dict) -> ServiceStatus:
        """Check HTTP-based service health."""
        if not HAS_AIOHTTP:
            return ServiceStatus(
                name=name,
                state=ServiceState.UNKNOWN,
                error="aiohttp not installed",
                required=config.get("required", False),
            )

        urls = config.get("urls", [])
        health_path = config.get("health_path", "/health")
        timeout = config.get("timeout", 5)

        for base_url in urls:
            try:
                url = f"{base_url}{health_path}"
                import time

                start = time.time()

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as resp:
                        latency_ms = (time.time() - start) * 1000

                        if 200 <= resp.status < 300:
                            return ServiceStatus(
                                name=name,
                                state=ServiceState.ONLINE,
                                url=base_url,
                                latency_ms=round(latency_ms, 1),
                                required=config.get("required", False),
                            )
                        elif resp.status == 503:
                            return ServiceStatus(
                                name=name,
                                state=ServiceState.STARTING,
                                url=base_url,
                                error=f"HTTP {resp.status}",
                                required=config.get("required", False),
                            )
                        else:
                            # Try next URL
                            continue
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Health check failed for {name} at {base_url}: {e}")
                continue

        # All URLs failed
        return ServiceStatus(
            name=name,
            state=ServiceState.OFFLINE,
            error="All endpoints unreachable",
            required=config.get("required", False),
        )

    async def _check_postgres(self) -> ServiceStatus:
        """Check PostgreSQL database health."""
        if not HAS_ASYNCPG:
            return ServiceStatus(
                name="database",
                state=ServiceState.UNKNOWN,
                error="asyncpg not installed",
                required=True,
            )

        postgres_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
        if not postgres_url:
            return ServiceStatus(
                name="database",
                state=ServiceState.OFFLINE,
                error="No POSTGRES_URL configured",
                required=True,
            )

        try:
            import time

            start = time.time()

            conn = await asyncpg.connect(
                postgres_url, timeout=5, statement_cache_size=0
            )
            try:
                await conn.fetchval("SELECT 1")
            finally:
                await conn.close()

            latency_ms = (time.time() - start) * 1000

            return ServiceStatus(
                name="database",
                state=ServiceState.ONLINE,
                url=self._mask_postgres_url(postgres_url),
                latency_ms=round(latency_ms, 1),
                required=True,
            )
        except asyncio.TimeoutError:
            return ServiceStatus(
                name="database",
                state=ServiceState.OFFLINE,
                error="Connection timeout",
                required=True,
            )
        except Exception as e:
            return ServiceStatus(
                name="database",
                state=ServiceState.OFFLINE,
                error=str(e)[:100],
                required=True,
            )

    @staticmethod
    def _mask_postgres_url(url: str) -> str:
        """Mask password in PostgreSQL URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if parsed.password:
                masked = url.replace(parsed.password, "****")
                return masked
            return url
        except Exception:
            return "postgresql://***"

    async def wait_for_service(
        self, name: str, timeout: int = 30, interval: float = 1.0
    ) -> bool:
        """Wait for a service to become available."""
        logger.info(f"Waiting for {name} to become available (timeout: {timeout}s)")

        start = asyncio.get_event_loop().time()
        while True:
            status = await self.check_service(name)

            if status.state == ServiceState.ONLINE:
                logger.info(f"{name} is now available")
                return True

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                logger.warning(f"Timeout waiting for {name}")
                return False

            await asyncio.sleep(interval)

    def get_service_url(self, name: str, prefer_local: bool = True) -> Optional[str]:
        """Get the URL for a service."""
        if name not in self.SERVICES:
            return None

        config = self.SERVICES[name]
        urls = config.get("urls", [])

        if not urls:
            return None

        # Check cache for working URL
        if name in self._status_cache:
            cached = self._status_cache[name]
            if cached.state == ServiceState.ONLINE and cached.url:
                return cached.url

        # Prefer localhost if requested
        if prefer_local:
            for url in urls:
                if "localhost" in url or "127.0.0.1" in url:
                    return url

        # Return first URL as fallback
        return urls[0]

    def get_orchestrator_url(self) -> str:
        """Get orchestrator URL (convenience method)."""
        url = self.get_service_url("orchestrator", prefer_local=True)
        return url or "http://localhost:8000"

    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return False
            except OSError:
                return True


# Global singleton instance
_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry
