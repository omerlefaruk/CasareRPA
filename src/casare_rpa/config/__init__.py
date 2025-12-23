"""
CasareRPA Configuration Module.

Provides centralized, typed configuration management using Pydantic and frozen dataclasses.

This is the single source of truth for all configuration in CasareRPA.
Do NOT use casare_rpa.utils.config - use this module instead.

Configuration Hierarchy:
    - AppConfig: Unified frozen dataclass combining all domain configs
    - Config: Pydantic model for environment-based service configuration

Usage:
    # Unified application config (frozen dataclasses)
    from casare_rpa.config import get_app_config

    config = get_app_config()
    print(config.timeouts.http_timeout_s)
    print(config.ports.orchestrator)
    print(config.retry.max_attempts)
    print(config.limits.workflow_max_nodes)

    # Legacy Pydantic config (for service configuration)
    from casare_rpa.config import get_config, Config

    config = get_config()
    print(config.database.url)
    print(config.orchestrator.port)

    # Validate on startup
    from casare_rpa.config import validate_config
    validate_config()  # Raises ConfigurationError if invalid

    # Access path constants
    from casare_rpa.config import PROJECT_ROOT, LOGS_DIR, setup_logging
"""

# Schema models (Pydantic)
from casare_rpa.config.app_config import (
    AppConfig,
    get_app_config,
    reset_app_config,
    validate_app_config,
)

# File-based config loader (for YAML/TOML/JSON files)
from casare_rpa.config.file_loader import (
    TOML_AVAILABLE,
    YAML_AVAILABLE,
    ConfigFileLoader,
    ConfigSchema,
    ConfigSource,
    FileConfigurationError,
    load_config_file,
    load_config_file_with_env,
)
from casare_rpa.config.limits_config import (
    DEFAULT_HTML_MAX_LENGTH,
    DEFAULT_LLM_CONTEXT_CHARS,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_WORKFLOW_MAX_CONNECTIONS,
    DEFAULT_WORKFLOW_MAX_NODES,
    LimitsConfig,
    get_limits_config,
    reset_limits_config,
)

# Environment-based config loader
from casare_rpa.config.loader import (
    ConfigurationError,
    clear_config_cache,
    get_config,
    load_config,
    validate_config,
)

# Logging setup
from casare_rpa.config.logging_setup import (
    LOG_FILE_PATH,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_RETENTION,
    LOG_ROTATION,
    setup_logging,
)

# Path constants and application metadata
from casare_rpa.config.paths import (
    # App constants
    APP_AUTHOR,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    # Browser settings
    BROWSER_ARGS,
    # Paths
    CONFIG_DIR,
    DEFAULT_BROWSER,
    # Execution settings
    DEFAULT_NODE_TIMEOUT,
    DEFAULT_PAGE_LOAD_TIMEOUT,
    # GUI constants
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DOCS_DIR,
    ENABLE_HIGH_DPI,
    GLOBAL_CREDENTIALS_FILE,
    GLOBAL_VARIABLES_FILE,
    GUI_THEME,
    GUI_WINDOW_HEIGHT,
    GUI_WINDOW_WIDTH,
    HEADLESS_MODE,
    HOTKEYS_FILE,
    # Environment detection
    IS_FROZEN,
    LOGS_DIR,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    # Node graph settings
    NODE_GRID_SIZE,
    NODE_SNAP_TO_GRID,
    PROJECT_ROOT,
    PROJECTS_DIR,
    PROJECTS_INDEX_FILE,
    SETTINGS_FILE,
    SRC_ROOT,
    STOP_ON_ERROR,
    USER_DATA_DIR,
    # Schema
    WORKFLOW_SCHEMA_VERSION,
    WORKFLOWS_DIR,
    # Functions
    ensure_directories,
)
from casare_rpa.config.port_config import (
    DEFAULT_DATABASE_PORT,
    DEFAULT_ORCHESTRATOR_PORT,
    DEFAULT_VAULT_PORT,
    DEFAULT_VITE_DEV_PORT,
    PortConfig,
    get_port_config,
    reset_port_config,
)
from casare_rpa.config.retry_config import (
    DEFAULT_BACKOFF_MULTIPLIER,
    DEFAULT_BASE_DELAY_MS,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_DELAY_MS,
    RetryConfig,
    get_retry_config,
    reset_retry_config,
)
from casare_rpa.config.schema import (
    CloudflareConfig,
    Config,
    DatabaseConfig,
    LoggingConfig,
    MetricsConfig,
    OrchestratorConfig,
    QueueConfig,
    RateLimitConfig,
    RobotConfig,
    SecurityConfig,
    StorageConfig,
    SupabaseConfig,
    TimeoutConfig,
    VaultConfig,
)

# Crypto security configuration (PBKDF2 iterations, etc.)
from casare_rpa.config.security_config import (
    CryptoSecurityConfig,
    get_crypto_security_config,
    reset_crypto_security_config,
)
from casare_rpa.config.timeout_config import (
    DEFAULT_BROWSER_DOWNLOAD_S,
    DEFAULT_HTTP_TIMEOUT_S,
    DEFAULT_NODE_TIMEOUT_S,
    DEFAULT_PAGE_LOAD_MS,
    get_timeout_config,
    reset_timeout_config,
)

# Frozen dataclass configs (new unified config system)
from casare_rpa.config.timeout_config import (
    TimeoutConfig as TimeoutConfigFrozen,
)

__all__ = [
    # Main config class
    "Config",
    # Nested configs (Pydantic models)
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
    "StorageConfig",
    "CloudflareConfig",
    "MetricsConfig",
    # Environment config functions
    "get_config",
    "load_config",
    "validate_config",
    "clear_config_cache",
    # Exceptions
    "ConfigurationError",
    "FileConfigurationError",
    # Environment detection
    "IS_FROZEN",
    # Paths
    "PROJECT_ROOT",
    "SRC_ROOT",
    "LOGS_DIR",
    "WORKFLOWS_DIR",
    "DOCS_DIR",
    "CONFIG_DIR",
    "SETTINGS_FILE",
    "HOTKEYS_FILE",
    "PROJECTS_DIR",
    "PROJECTS_INDEX_FILE",
    "GLOBAL_VARIABLES_FILE",
    "GLOBAL_CREDENTIALS_FILE",
    "USER_DATA_DIR",
    # Path functions
    "ensure_directories",
    # App constants
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    # GUI constants
    "ENABLE_HIGH_DPI",
    "DEFAULT_WINDOW_WIDTH",
    "DEFAULT_WINDOW_HEIGHT",
    "MIN_WINDOW_WIDTH",
    "MIN_WINDOW_HEIGHT",
    "GUI_WINDOW_WIDTH",
    "GUI_WINDOW_HEIGHT",
    "GUI_THEME",
    # Execution settings
    "DEFAULT_NODE_TIMEOUT",
    "DEFAULT_PAGE_LOAD_TIMEOUT",
    "STOP_ON_ERROR",
    # Browser settings
    "DEFAULT_BROWSER",
    "HEADLESS_MODE",
    "BROWSER_ARGS",
    # Node graph settings
    "NODE_GRID_SIZE",
    "NODE_SNAP_TO_GRID",
    # Schema
    "WORKFLOW_SCHEMA_VERSION",
    # Logging
    "LOG_FILE_PATH",
    "LOG_RETENTION",
    "LOG_ROTATION",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "setup_logging",
    # File loader
    "ConfigSource",
    "ConfigSchema",
    "ConfigFileLoader",
    "load_config_file",
    "load_config_file_with_env",
    "YAML_AVAILABLE",
    "TOML_AVAILABLE",
    # Unified app config (frozen dataclasses)
    "AppConfig",
    "get_app_config",
    "reset_app_config",
    "validate_app_config",
    # Timeout config
    "TimeoutConfigFrozen",
    "get_timeout_config",
    "reset_timeout_config",
    "DEFAULT_HTTP_TIMEOUT_S",
    "DEFAULT_BROWSER_DOWNLOAD_S",
    "DEFAULT_PAGE_LOAD_MS",
    "DEFAULT_NODE_TIMEOUT_S",
    # Port config
    "PortConfig",
    "get_port_config",
    "reset_port_config",
    "DEFAULT_ORCHESTRATOR_PORT",
    "DEFAULT_DATABASE_PORT",
    "DEFAULT_VAULT_PORT",
    "DEFAULT_VITE_DEV_PORT",
    # Retry config
    "RetryConfig",
    "get_retry_config",
    "reset_retry_config",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_BASE_DELAY_MS",
    "DEFAULT_MAX_DELAY_MS",
    "DEFAULT_BACKOFF_MULTIPLIER",
    # Limits config
    "LimitsConfig",
    "get_limits_config",
    "reset_limits_config",
    "DEFAULT_WORKFLOW_MAX_NODES",
    "DEFAULT_WORKFLOW_MAX_CONNECTIONS",
    "DEFAULT_HTML_MAX_LENGTH",
    "DEFAULT_LLM_MAX_TOKENS",
    "DEFAULT_LLM_CONTEXT_CHARS",
    # Crypto security config (PBKDF2 iterations)
    "CryptoSecurityConfig",
    "get_crypto_security_config",
    "reset_crypto_security_config",
]
