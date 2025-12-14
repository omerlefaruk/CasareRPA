"""
CasareRPA Unified Application Configuration.

Combines all configuration domains into a single frozen dataclass
with centralized access via singleton pattern.

Usage:
    from casare_rpa.config.app_config import get_app_config

    config = get_app_config()

    # Access nested configs
    timeout = config.timeouts.http_timeout_s
    port = config.ports.orchestrator
    retries = config.retry.max_attempts
    limit = config.limits.workflow_max_nodes
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from casare_rpa.config.timeout_config import TimeoutConfig, get_timeout_config
from casare_rpa.config.port_config import PortConfig, get_port_config
from casare_rpa.config.retry_config import RetryConfig, get_retry_config
from casare_rpa.config.limits_config import LimitsConfig, get_limits_config

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class AppConfig:
    """
    Unified application configuration combining all config domains.

    This is the primary configuration class for CasareRPA, aggregating
    all domain-specific configurations into a single immutable object.

    The class follows the Composition pattern, delegating to specialized
    config classes for each domain while providing a unified access point.

    Attributes:
        timeouts: Timeout configuration for all operations.
            Access via: config.timeouts.http_timeout_s

        ports: Port numbers for services and integrations.
            Access via: config.ports.orchestrator

        retry: Retry and backoff settings for resilience.
            Access via: config.retry.max_attempts

        limits: Resource limits for workflows and operations.
            Access via: config.limits.workflow_max_nodes

    Example:
        >>> config = get_app_config()
        >>> print(f"API runs on port {config.ports.orchestrator}")
        >>> print(f"HTTP timeout: {config.timeouts.http_timeout_s}s")
        >>> print(f"Max retries: {config.retry.max_attempts}")
        >>> print(f"Max nodes: {config.limits.workflow_max_nodes}")
    """

    timeouts: TimeoutConfig
    ports: PortConfig
    retry: RetryConfig
    limits: LimitsConfig

    @classmethod
    def from_env(cls) -> AppConfig:
        """
        Create AppConfig by loading all sub-configs from environment.

        Each sub-config class handles its own environment variable parsing.
        This method composes them into a unified configuration object.

        Returns:
            AppConfig with all sub-configs loaded from environment
        """
        return cls(
            timeouts=TimeoutConfig.from_env(),
            ports=PortConfig.from_env(),
            retry=RetryConfig.from_env(),
            limits=LimitsConfig.from_env(),
        )

    @classmethod
    def from_cached(cls) -> AppConfig:
        """
        Create AppConfig using cached singleton instances of sub-configs.

        This is more efficient when sub-configs have already been loaded,
        as it reuses the cached instances instead of parsing environment
        variables again.

        Returns:
            AppConfig with all sub-configs from cache
        """
        return cls(
            timeouts=get_timeout_config(),
            ports=get_port_config(),
            retry=get_retry_config(),
            limits=get_limits_config(),
        )

    def get_summary(self) -> dict:
        """
        Get a summary of the configuration for logging.

        Returns:
            Dictionary with key configuration values
        """
        return {
            "timeouts": {
                "http_s": self.timeouts.http_timeout_s,
                "job_s": self.timeouts.job_timeout_s,
                "node_default_s": self.timeouts.node_default_s,
            },
            "ports": {
                "orchestrator": self.ports.orchestrator,
                "database": self.ports.database,
            },
            "retry": {
                "max_attempts": self.retry.max_attempts,
                "base_delay_ms": self.retry.base_delay_ms,
            },
            "limits": {
                "workflow_max_nodes": self.limits.workflow_max_nodes,
                "llm_max_tokens": self.limits.llm_max_tokens,
            },
        }

    def validate(self) -> list[str]:
        """
        Validate configuration values for consistency.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Validate timeout relationships
        if self.timeouts.job_timeout_s < self.timeouts.node_default_s:
            errors.append(
                f"job_timeout_s ({self.timeouts.job_timeout_s}) must be >= "
                f"node_default_s ({self.timeouts.node_default_s})"
            )

        # Validate retry relationships
        if self.retry.base_delay_ms > self.retry.max_delay_ms:
            errors.append(
                f"base_delay_ms ({self.retry.base_delay_ms}) must be <= "
                f"max_delay_ms ({self.retry.max_delay_ms})"
            )

        # Validate workflow limits
        if self.limits.workflow_max_connections < self.limits.workflow_max_nodes:
            errors.append(
                f"workflow_max_connections ({self.limits.workflow_max_connections}) "
                f"should typically be >= workflow_max_nodes ({self.limits.workflow_max_nodes})"
            )

        # Validate port ranges
        for name in ["orchestrator", "database", "vault", "websocket"]:
            port = getattr(self.ports, name)
            if not (1 <= port <= 65535):
                errors.append(f"Port {name} ({port}) must be between 1 and 65535")

        return errors


# Thread-safe singleton pattern
_app_config: AppConfig | None = None
_app_config_lock = threading.Lock()


def get_app_config() -> AppConfig:
    """
    Get the unified application configuration singleton.

    Configuration is loaded once from environment variables
    and cached for subsequent calls. Uses double-checked locking
    for thread-safe lazy initialization.

    Returns:
        AppConfig instance with all sub-configs
    """
    global _app_config
    if _app_config is None:
        with _app_config_lock:
            if _app_config is None:
                _app_config = AppConfig.from_cached()
    return _app_config


def reset_app_config() -> None:
    """
    Reset the application configuration singleton (for testing).

    Also resets all sub-config singletons to ensure fresh reload.
    """
    global _app_config
    with _app_config_lock:
        _app_config = None

    # Reset sub-config singletons
    from casare_rpa.config.timeout_config import reset_timeout_config
    from casare_rpa.config.port_config import reset_port_config
    from casare_rpa.config.retry_config import reset_retry_config
    from casare_rpa.config.limits_config import reset_limits_config

    reset_timeout_config()
    reset_port_config()
    reset_retry_config()
    reset_limits_config()


def validate_app_config() -> AppConfig:
    """
    Load, validate, and return the application configuration.

    Raises ConfigurationError if validation fails.

    Returns:
        Validated AppConfig instance

    Raises:
        ValueError: If configuration validation fails
    """
    config = get_app_config()
    errors = config.validate()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(
            f"  - {e}" for e in errors
        )
        raise ValueError(error_msg)
    return config


__all__ = [
    "AppConfig",
    "get_app_config",
    "reset_app_config",
    "validate_app_config",
]
