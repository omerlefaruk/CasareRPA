"""
CasareRPA Configuration Loader.

Handles loading configuration from environment variables and .env files
with validation and sensible defaults.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

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
    MetricsConfig,
    SupabaseConfig,
    VaultConfig,
    StorageConfig,
    CloudflareConfig,
)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""

    def __init__(self, message: str, missing_fields: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_fields = missing_fields or []


# Singleton cache
_config_cache: Optional[Config] = None


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    """Parse boolean from environment variable string."""
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _parse_int(value: Optional[str], default: int) -> int:
    """Parse integer from environment variable string."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: Optional[str], default: float) -> float:
    """Parse float from environment variable string."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_list(value: Optional[str], default: Optional[List[str]] = None) -> List[str]:
    """Parse comma-separated list from environment variable string."""
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_path(value: Optional[str]) -> Optional[Path]:
    """Parse path from environment variable string."""
    if not value:
        return None
    return Path(value)


def _load_env_file(env_path: Path) -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file

    Returns:
        True if file was loaded successfully
    """
    try:
        from dotenv import load_dotenv

        if env_path.exists():
            load_dotenv(env_path, override=False)
            return True
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
    return False


def _find_env_files() -> List[Path]:
    """
    Find .env files in standard locations.

    Search order (first found wins for each variable):
    1. Environment variables (already loaded)
    2. .env in current directory
    3. .env in project root
    4. config/.env in project root

    Returns:
        List of found .env file paths
    """
    found_files = []
    cwd = Path.cwd()

    # Check current directory
    cwd_env = cwd / ".env"
    if cwd_env.exists():
        found_files.append(cwd_env)

    # Check project root (navigate up to find CLAUDE.md or pyproject.toml)
    project_root = _find_project_root()
    if project_root:
        root_env = project_root / ".env"
        if root_env.exists() and root_env not in found_files:
            found_files.append(root_env)

        config_env = project_root / "config" / ".env"
        if config_env.exists() and config_env not in found_files:
            found_files.append(config_env)

    return found_files


def _find_project_root() -> Optional[Path]:
    """Find project root by looking for marker files."""
    current = Path.cwd()
    markers = ["pyproject.toml", "CLAUDE.md", ".git"]

    for _ in range(10):  # Max 10 levels up
        for marker in markers:
            if (current / marker).exists():
                return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def _build_database_config() -> DatabaseConfig:
    """Build DatabaseConfig from environment variables."""
    return DatabaseConfig(
        enabled=_parse_bool(os.getenv("DB_ENABLED"), True),
        url=os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("PGQUEUER_DB_URL"),
        host=os.getenv("DB_HOST", "localhost"),
        port=_parse_int(os.getenv("DB_PORT"), 5432),
        name=os.getenv("DB_NAME", "casare_rpa"),
        user=os.getenv("DB_USER", "casare_user"),
        password=os.getenv("DB_PASSWORD", ""),
        pool_min_size=_parse_int(os.getenv("DB_POOL_MIN_SIZE"), 2),
        pool_max_size=_parse_int(os.getenv("DB_POOL_MAX_SIZE"), 10),
        command_timeout=_parse_float(os.getenv("DB_COMMAND_TIMEOUT"), 60.0),
        max_inactive_lifetime=_parse_float(
            os.getenv("DB_MAX_INACTIVE_LIFETIME"), 300.0
        ),
    )


def _build_supabase_config() -> SupabaseConfig:
    """Build SupabaseConfig from environment variables."""
    return SupabaseConfig(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY"),
        service_key=os.getenv("SUPABASE_SERVICE_KEY"),
    )


def _build_security_config() -> SecurityConfig:
    """Build SecurityConfig from environment variables."""
    return SecurityConfig(
        api_secret=os.getenv("API_SECRET") or os.getenv("JWT_SECRET_KEY"),
        jwt_expiration_seconds=_parse_int(os.getenv("JWT_EXPIRATION_SECONDS"), 3600),
        robot_auth_enabled=_parse_bool(os.getenv("ROBOT_AUTH_ENABLED"), False),
        verify_ssl=_parse_bool(os.getenv("VERIFY_SSL"), True),
        ca_cert_path=_parse_path(os.getenv("CASARE_CA_CERT_PATH")),
        client_cert_path=_parse_path(os.getenv("CASARE_CLIENT_CERT_PATH")),
        client_key_path=_parse_path(os.getenv("CASARE_CLIENT_KEY_PATH")),
    )


def _build_orchestrator_config() -> OrchestratorConfig:
    """Build OrchestratorConfig from environment variables."""
    cors_origins = _parse_list(
        os.getenv("CORS_ORIGINS"), ["http://localhost:5173", "http://localhost:8000"]
    )

    # Add Cloudflare API URL if configured
    api_url = os.getenv("CASARE_API_URL")
    if api_url and api_url not in cors_origins:
        cors_origins.append(api_url)

    return OrchestratorConfig(
        host=os.getenv("ORCHESTRATOR_HOST")
        or os.getenv("HOST")
        or os.getenv("API_HOST", "0.0.0.0"),
        port=_parse_int(
            os.getenv("ORCHESTRATOR_PORT")
            or os.getenv("PORT")
            or os.getenv("API_PORT"),
            8000,
        ),
        workers=_parse_int(
            os.getenv("ORCHESTRATOR_WORKERS") or os.getenv("WORKERS"), 1
        ),
        cors_origins=cors_origins,
        ssl_keyfile=_parse_path(os.getenv("SSL_KEYFILE")),
        ssl_certfile=_parse_path(os.getenv("SSL_CERTFILE")),
    )


def _build_robot_config() -> RobotConfig:
    """Build RobotConfig from environment variables."""
    return RobotConfig(
        id=os.getenv("ROBOT_ID") or os.getenv("CASARE_ROBOT_ID"),
        name=os.getenv("ROBOT_NAME") or os.getenv("CASARE_ROBOT_NAME"),
        environment=os.getenv("ROBOT_ENVIRONMENT")
        or os.getenv("CASARE_ENVIRONMENT", "production"),
        max_concurrent_jobs=_parse_int(
            os.getenv("ROBOT_MAX_CONCURRENT_JOBS")
            or os.getenv("CASARE_MAX_CONCURRENT_JOBS"),
            1,
        ),
        heartbeat_interval=_parse_int(
            os.getenv("ROBOT_HEARTBEAT_INTERVAL")
            or os.getenv("CASARE_HEARTBEAT_INTERVAL"),
            30,
        ),
        capabilities=_parse_list(
            os.getenv("ROBOT_CAPABILITIES") or os.getenv("CASARE_CAPABILITIES")
        ),
        tags=_parse_list(os.getenv("ROBOT_TAGS") or os.getenv("CASARE_TAGS")),
        reconnect_delay=_parse_float(os.getenv("RECONNECT_DELAY"), 1.0),
        max_reconnect_delay=_parse_float(os.getenv("MAX_RECONNECT_DELAY"), 60.0),
        job_timeout=_parse_float(os.getenv("CASARE_JOB_TIMEOUT"), 3600.0),
    )


def _build_logging_config() -> LoggingConfig:
    """Build LoggingConfig from environment variables."""
    return LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        file=_parse_path(os.getenv("LOG_FILE")),
        rotation_size_mb=_parse_int(os.getenv("LOG_ROTATION_SIZE_MB"), 10),
        retention_days=_parse_int(os.getenv("LOG_RETENTION_DAYS"), 7),
    )


def _build_queue_config() -> QueueConfig:
    """Build QueueConfig from environment variables."""
    return QueueConfig(
        url=os.getenv("PGQUEUER_DB_URL"),
        use_memory_queue=_parse_bool(os.getenv("USE_MEMORY_QUEUE"), False),
        poll_interval=_parse_float(os.getenv("JOB_POLL_INTERVAL"), 1.0),
        job_timeout_default=_parse_int(os.getenv("JOB_TIMEOUT_DEFAULT"), 3600),
    )


def _build_timeout_config() -> TimeoutConfig:
    """Build TimeoutConfig from environment variables."""
    return TimeoutConfig(
        robot_heartbeat=_parse_int(os.getenv("ROBOT_HEARTBEAT_TIMEOUT"), 90),
        ws_ping_interval=_parse_int(os.getenv("WS_PING_INTERVAL"), 30),
        ws_send_timeout=_parse_float(os.getenv("WS_SEND_TIMEOUT"), 1.0),
    )


def _build_rate_limit_config() -> RateLimitConfig:
    """Build RateLimitConfig from environment variables."""
    return RateLimitConfig(
        enabled=_parse_bool(os.getenv("RATE_LIMIT_ENABLED"), True),
        requests_per_minute=_parse_int(
            os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE"), 100
        ),
    )


def _build_metrics_config() -> MetricsConfig:
    """Build MetricsConfig from environment variables."""
    return MetricsConfig(
        enabled=_parse_bool(os.getenv("METRICS_ENABLED"), True),
        collection_interval=_parse_int(os.getenv("METRICS_COLLECTION_INTERVAL"), 5),
        event_history_size=_parse_int(os.getenv("EVENT_HISTORY_SIZE"), 1000),
    )


def _build_vault_config() -> VaultConfig:
    """Build VaultConfig from environment variables."""
    return VaultConfig(
        addr=os.getenv("VAULT_ADDR"),
        token=os.getenv("VAULT_TOKEN"),
        role_id=os.getenv("VAULT_ROLE_ID"),
        secret_id=os.getenv("VAULT_SECRET_ID"),
    )


def _build_storage_config() -> StorageConfig:
    """Build StorageConfig from environment variables."""
    return StorageConfig(
        workflows_dir=Path(os.getenv("WORKFLOWS_DIR", "./workflows")),
        backup_enabled=_parse_bool(os.getenv("WORKFLOW_BACKUP_ENABLED"), True),
    )


def _build_cloudflare_config() -> CloudflareConfig:
    """Build CloudflareConfig from environment variables."""
    return CloudflareConfig(
        api_url=os.getenv("CASARE_API_URL"),
        webhook_url=os.getenv("CASARE_WEBHOOK_URL"),
        robot_ws_url=os.getenv("CASARE_ROBOT_WS_URL"),
    )


def load_config(env_file: Optional[Path] = None, reload: bool = False) -> Config:
    """
    Load configuration from environment variables and .env files.

    Args:
        env_file: Optional explicit .env file path
        reload: Force reload even if cached

    Returns:
        Config instance with all settings

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _config_cache

    if _config_cache is not None and not reload:
        return _config_cache

    # Load .env files
    if env_file:
        loaded = _load_env_file(env_file)
        if loaded:
            logger.debug(f"Loaded configuration from: {env_file}")
    else:
        env_files = _find_env_files()
        for ef in env_files:
            loaded = _load_env_file(ef)
            if loaded:
                logger.debug(f"Loaded configuration from: {ef}")

    # Build configuration from environment
    try:
        config = Config(
            database=_build_database_config(),
            supabase=_build_supabase_config(),
            security=_build_security_config(),
            orchestrator=_build_orchestrator_config(),
            robot=_build_robot_config(),
            logging=_build_logging_config(),
            queue=_build_queue_config(),
            timeouts=_build_timeout_config(),
            rate_limit=_build_rate_limit_config(),
            metrics=_build_metrics_config(),
            vault=_build_vault_config(),
            storage=_build_storage_config(),
            cloudflare=_build_cloudflare_config(),
            debug=_parse_bool(os.getenv("DEBUG"), False),
            reload=_parse_bool(os.getenv("RELOAD"), False),
            tenant_id=os.getenv("TENANT_ID"),
        )
    except Exception as e:
        raise ConfigurationError(f"Invalid configuration: {e}") from e

    _config_cache = config
    return config


def get_config() -> Config:
    """
    Get cached configuration or load it.

    This is the primary way to access configuration throughout the application.
    Configuration is loaded once and cached.

    Returns:
        Config instance
    """
    global _config_cache
    if _config_cache is None:
        return load_config()
    return _config_cache


def validate_config(
    require_database: bool = False,
    require_supabase: bool = False,
    require_api_secret: bool = False,
) -> Config:
    """
    Load and validate configuration, raising errors for missing required fields.

    Use this at application startup to fail fast if configuration is invalid.

    Args:
        require_database: Require database to be configured
        require_supabase: Require Supabase to be configured
        require_api_secret: Require API secret to be set

    Returns:
        Validated Config instance

    Raises:
        ConfigurationError: If required configuration is missing
    """
    config = load_config(reload=True)
    missing = []

    if require_database and config.database.enabled:
        if not config.database.url and not config.database.password:
            missing.append("DATABASE_URL or DB_PASSWORD")

    if require_supabase and not config.supabase.is_configured:
        missing.append("SUPABASE_URL and SUPABASE_KEY")

    if require_api_secret and not config.security.api_secret:
        missing.append("API_SECRET")

    if missing:
        msg = "Missing required configuration: " + ", ".join(missing)
        logger.error(msg)
        raise ConfigurationError(msg, missing_fields=missing)

    # Log configuration summary
    summary = config.get_summary(mask_secrets=True)
    logger.info(f"Configuration loaded: {summary}")

    return config


def clear_config_cache() -> None:
    """Clear the configuration cache (useful for testing)."""
    global _config_cache
    _config_cache = None
