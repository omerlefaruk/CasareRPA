"""
CasareRPA Configuration Module.

Provides centralized, typed configuration management using Pydantic.

This is the single source of truth for all configuration in CasareRPA.
Do NOT use casare_rpa.utils.config - use this module instead.

Usage:
    from casare_rpa.config import get_config, Config

    # Load configuration (cached singleton)
    config = get_config()

    # Access typed settings
    print(config.database.url)
    print(config.orchestrator.port)

    # Validate on startup
    from casare_rpa.config import validate_config
    validate_config()  # Raises ConfigurationError if invalid

    # Access path constants
    from casare_rpa.config import PROJECT_ROOT, LOGS_DIR, setup_logging
"""

# Schema models (Pydantic)
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

# Environment-based config loader
from casare_rpa.config.loader import (
    ConfigurationError,
    clear_config_cache,
    get_config,
    load_config,
    validate_config,
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
    WORKFLOWS_DIR,
    # Schema
    WORKFLOW_SCHEMA_VERSION,
    # Functions
    ensure_directories,
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

# File-based config loader (for YAML/TOML/JSON files)
from casare_rpa.config.file_loader import (
    ConfigFileLoader,
    ConfigSchema,
    ConfigSource,
    FileConfigurationError,
    TOML_AVAILABLE,
    YAML_AVAILABLE,
    load_config_file,
    load_config_file_with_env,
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
]
