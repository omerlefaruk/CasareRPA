"""
CasareRPA Port Configuration.

Centralized port numbers for all services and integrations.
Uses frozen dataclasses for immutability with environment variable overrides.

Usage:
    from casare_rpa.config.port_config import get_port_config

    config = get_port_config()
    port = config.orchestrator
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


def _parse_int(value: str | None, default: int) -> int:
    """Parse integer from environment variable string."""
    if value is None:
        return default
    try:
        parsed = int(value)
        # Validate port range
        if 1 <= parsed <= 65535:
            return parsed
        return default
    except ValueError:
        return default


@dataclass(frozen=True)
class PortConfig:
    """
    Centralized port configuration for all CasareRPA services.

    All port values are extracted from hardcoded defaults across the codebase.
    Each field documents its purpose and typical usage.

    Attributes:
        orchestrator: Port for the CasareRPA Orchestrator API server.
            FastAPI/uvicorn server that handles job scheduling and robot management.
            Default: 8000

        database: Port for PostgreSQL database connections.
            Used for workflow persistence, job queue (PgQueuer), and user data.
            Default: 5432

        vault: Port for HashiCorp Vault secret management.
            Used for credential storage and rotation.
            Default: 8200

        vite_dev: Port for Vite development server.
            Used during web dashboard development.
            Default: 5173

        redis: Port for Redis cache/message broker.
            Used for caching and pub/sub messaging.
            Default: 6379

        metrics: Port for Prometheus metrics endpoint.
            Exposed for monitoring and observability.
            Default: 9090

        websocket: Port for dedicated WebSocket server.
            Used when WebSocket runs separately from REST API.
            Default: 8001
    """

    # Core services
    orchestrator: int = 8000
    database: int = 5432
    vault: int = 8200

    # Development
    vite_dev: int = 5173

    # Infrastructure
    redis: int = 6379
    metrics: int = 9090

    # Communication
    websocket: int = 8001

    @classmethod
    def from_env(cls) -> PortConfig:
        """
        Create PortConfig from environment variables.

        Environment variable names follow the pattern:
        CASARE_PORT_{SERVICE}

        Example:
            CASARE_PORT_ORCHESTRATOR=8080
            CASARE_PORT_DATABASE=5433

        Legacy environment variables are also supported:
            ORCHESTRATOR_PORT, API_PORT, PORT -> orchestrator
            DB_PORT -> database
            VAULT_PORT -> vault
            VITE_PORT -> vite_dev

        Returns:
            PortConfig with values from environment or defaults
        """
        return cls(
            orchestrator=_parse_int(
                os.getenv("CASARE_PORT_ORCHESTRATOR")
                or os.getenv("ORCHESTRATOR_PORT")
                or os.getenv("API_PORT")
                or os.getenv("PORT"),
                8000,
            ),
            database=_parse_int(
                os.getenv("CASARE_PORT_DATABASE") or os.getenv("DB_PORT"), 5432
            ),
            vault=_parse_int(
                os.getenv("CASARE_PORT_VAULT") or os.getenv("VAULT_PORT"), 8200
            ),
            vite_dev=_parse_int(
                os.getenv("CASARE_PORT_VITE_DEV") or os.getenv("VITE_PORT"), 5173
            ),
            redis=_parse_int(
                os.getenv("CASARE_PORT_REDIS") or os.getenv("REDIS_PORT"), 6379
            ),
            metrics=_parse_int(
                os.getenv("CASARE_PORT_METRICS") or os.getenv("METRICS_PORT"), 9090
            ),
            websocket=_parse_int(
                os.getenv("CASARE_PORT_WEBSOCKET") or os.getenv("WS_PORT"), 8001
            ),
        )

    def get_orchestrator_url(
        self, host: str = "localhost", scheme: str = "http"
    ) -> str:
        """
        Build orchestrator base URL.

        Args:
            host: Hostname or IP address
            scheme: URL scheme (http or https)

        Returns:
            Full URL string like "http://localhost:8000"
        """
        return f"{scheme}://{host}:{self.orchestrator}"

    def get_websocket_url(self, host: str = "localhost", secure: bool = False) -> str:
        """
        Build WebSocket base URL.

        Args:
            host: Hostname or IP address
            secure: Use wss:// instead of ws://

        Returns:
            Full URL string like "ws://localhost:8001"
        """
        scheme = "wss" if secure else "ws"
        return f"{scheme}://{host}:{self.websocket}"

    def get_database_url(
        self,
        host: str = "localhost",
        user: str = "casare_user",
        password: str = "",
        database: str = "casare_rpa",
    ) -> str:
        """
        Build PostgreSQL connection URL.

        Args:
            host: Database hostname
            user: Database username
            password: Database password
            database: Database name

        Returns:
            PostgreSQL connection string
        """
        return f"postgresql://{user}:{password}@{host}:{self.database}/{database}"


# Module-level singleton
_port_config: PortConfig | None = None


def get_port_config() -> PortConfig:
    """
    Get the port configuration singleton.

    Configuration is loaded once from environment variables
    and cached for subsequent calls.

    Returns:
        PortConfig instance
    """
    global _port_config
    if _port_config is None:
        _port_config = PortConfig.from_env()
    return _port_config


def reset_port_config() -> None:
    """Reset the port configuration singleton (for testing)."""
    global _port_config
    _port_config = None


# Convenience constants for backward compatibility
DEFAULT_ORCHESTRATOR_PORT: Final[int] = 8000
DEFAULT_DATABASE_PORT: Final[int] = 5432
DEFAULT_VAULT_PORT: Final[int] = 8200
DEFAULT_VITE_DEV_PORT: Final[int] = 5173


__all__ = [
    "PortConfig",
    "get_port_config",
    "reset_port_config",
    "DEFAULT_ORCHESTRATOR_PORT",
    "DEFAULT_DATABASE_PORT",
    "DEFAULT_VAULT_PORT",
    "DEFAULT_VITE_DEV_PORT",
]
