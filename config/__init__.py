"""
CasareRPA Configuration Module.

Provides centralized, typed configuration management using Pydantic.

Usage:
    from config import get_config, Config

    # Load configuration (cached singleton)
    config = get_config()

    # Access typed settings
    print(config.database.url)
    print(config.orchestrator.port)

    # Validate on startup
    from config import validate_config
    validate_config()  # Raises ConfigurationError if invalid
"""

from config.schema import (
    Config,
    DatabaseConfig,
    OrchestratorConfig,
    RobotConfig,
    LoggingConfig,
    SecurityConfig,
    QueueConfig,
    TimeoutConfig,
    RateLimitConfig,
    SupabaseConfig,
    VaultConfig,
)
from config.loader import (
    get_config,
    load_config,
    validate_config,
    ConfigurationError,
)

__all__ = [
    # Main config class
    "Config",
    # Nested configs
    "DatabaseConfig",
    "OrchestratorConfig",
    "RobotConfig",
    "LoggingConfig",
    "SecurityConfig",
    "QueueConfig",
    "TimeoutConfig",
    "RateLimitConfig",
    "SupabaseConfig",
    "VaultConfig",
    # Functions
    "get_config",
    "load_config",
    "validate_config",
    # Exceptions
    "ConfigurationError",
]
