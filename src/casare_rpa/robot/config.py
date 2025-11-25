"""
Robot Configuration

Comprehensive configuration for the Robot Agent including:
- Identity and credentials
- Connection settings
- Job execution settings
- Resilience patterns
- Observability settings
"""

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import orjson


# Default paths
CONFIG_DIR = Path.home() / ".casare_rpa"
ROBOT_ID_FILE = CONFIG_DIR / "robot_id"
CONFIG_FILE = CONFIG_DIR / "robot_config.json"
OFFLINE_DB_FILE = CONFIG_DIR / "offline_queue.db"
AUDIT_LOG_DIR = CONFIG_DIR / "audit"

# Environment variable names
ENV_SUPABASE_URL = "SUPABASE_URL"
ENV_SUPABASE_KEY = "SUPABASE_KEY"
ENV_ROBOT_NAME = "CASARE_ROBOT_NAME"
ENV_MAX_CONCURRENT_JOBS = "CASARE_MAX_CONCURRENT_JOBS"


def get_robot_id() -> str:
    """Get or create a persistent unique ID for this robot."""
    if ROBOT_ID_FILE.exists():
        return ROBOT_ID_FILE.read_text().strip()

    # Create new ID
    new_id = str(uuid.uuid4())
    try:
        ROBOT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        ROBOT_ID_FILE.write_text(new_id)
        logger.info(f"Generated new Robot ID: {new_id}")
    except Exception as e:
        logger.error(f"Failed to save Robot ID: {e}")
        return new_id

    return new_id


def get_robot_name() -> str:
    """Get robot display name."""
    return os.getenv(
        ENV_ROBOT_NAME,
        f"Robot-{os.getenv('COMPUTERNAME', 'Unknown')}"
    )


# Legacy exports for compatibility
ROBOT_NAME = get_robot_name()
SUPABASE_URL = os.getenv(ENV_SUPABASE_URL, "")
SUPABASE_KEY = os.getenv(ENV_SUPABASE_KEY, "")


@dataclass
class ConnectionConfig:
    """Configuration for backend connection."""
    url: str = ""
    key: str = ""

    # Reconnection settings
    initial_delay: float = 1.0
    max_delay: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    jitter: bool = True
    max_reconnect_attempts: int = 0  # 0 = infinite

    # Timeouts
    connection_timeout: float = 30.0
    operation_timeout: float = 30.0

    # Heartbeat
    heartbeat_interval: float = 5.0

    @classmethod
    def from_env(cls) -> "ConnectionConfig":
        """Create from environment variables."""
        return cls(
            url=os.getenv(ENV_SUPABASE_URL, ""),
            key=os.getenv(ENV_SUPABASE_KEY, ""),
        )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    half_open_max_calls: int = 3


@dataclass
class JobExecutionConfig:
    """Configuration for job execution."""
    max_concurrent_jobs: int = 3
    job_poll_interval: float = 5.0
    lock_timeout: float = 300.0  # 5 minutes
    cancellation_check_interval: float = 2.0

    # Retry settings for nodes
    node_max_retries: int = 3
    node_initial_delay: float = 1.0
    node_max_delay: float = 30.0
    node_timeout: float = 120.0

    # Checkpointing
    checkpoint_enabled: bool = True
    checkpoint_on_every_node: bool = True

    # Progress reporting
    progress_reporting_enabled: bool = True
    progress_update_interval: float = 1.0

    @classmethod
    def from_env(cls) -> "JobExecutionConfig":
        """Create with env overrides."""
        max_concurrent = os.getenv(ENV_MAX_CONCURRENT_JOBS)
        return cls(
            max_concurrent_jobs=int(max_concurrent) if max_concurrent else 3,
        )


@dataclass
class ObservabilityConfig:
    """Configuration for metrics and logging."""
    # Metrics
    metrics_enabled: bool = True
    resource_monitoring_enabled: bool = True
    resource_sample_interval: float = 5.0

    # Audit logging
    audit_enabled: bool = True
    audit_log_dir: Path = field(default_factory=lambda: AUDIT_LOG_DIR)
    audit_max_file_size_mb: int = 10
    audit_backup_count: int = 5

    # Log retention
    metrics_history_limit: int = 1000


@dataclass
class RobotConfig:
    """Complete robot configuration."""
    robot_id: str = ""
    robot_name: str = ""

    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    job_execution: JobExecutionConfig = field(default_factory=JobExecutionConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    # Offline mode
    offline_db_path: Path = field(default_factory=lambda: OFFLINE_DB_FILE)
    offline_sync_interval: float = 30.0

    def __post_init__(self):
        if not self.robot_id:
            self.robot_id = get_robot_id()
        if not self.robot_name:
            self.robot_name = get_robot_name()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "RobotConfig":
        """
        Load configuration from file with env overrides.

        Args:
            config_path: Path to config file (uses default if None)

        Returns:
            RobotConfig instance
        """
        config_path = config_path or CONFIG_FILE

        # Start with defaults
        config = cls()

        # Load from file if exists
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    data = orjson.loads(f.read())
                config = cls.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

        # Override with environment variables
        config._apply_env_overrides()

        return config

    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        # Connection
        if os.getenv(ENV_SUPABASE_URL):
            self.connection.url = os.getenv(ENV_SUPABASE_URL)
        if os.getenv(ENV_SUPABASE_KEY):
            self.connection.key = os.getenv(ENV_SUPABASE_KEY)

        # Robot identity
        if os.getenv(ENV_ROBOT_NAME):
            self.robot_name = os.getenv(ENV_ROBOT_NAME)

        # Job execution
        max_concurrent = os.getenv(ENV_MAX_CONCURRENT_JOBS)
        if max_concurrent:
            try:
                self.job_execution.max_concurrent_jobs = int(max_concurrent)
            except ValueError:
                pass

    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        config_path = config_path or CONFIG_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "wb") as f:
            f.write(orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2))

        logger.info(f"Configuration saved to {config_path}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RobotConfig":
        """Create from dictionary."""
        return cls(
            robot_id=data.get("robot_id", ""),
            robot_name=data.get("robot_name", ""),
            connection=ConnectionConfig(
                **data.get("connection", {})
            ),
            circuit_breaker=CircuitBreakerConfig(
                **data.get("circuit_breaker", {})
            ),
            job_execution=JobExecutionConfig(
                **data.get("job_execution", {})
            ),
            observability=ObservabilityConfig(
                audit_log_dir=Path(data.get("observability", {}).get("audit_log_dir", str(AUDIT_LOG_DIR))),
                **{k: v for k, v in data.get("observability", {}).items() if k != "audit_log_dir"}
            ),
            offline_db_path=Path(data.get("offline_db_path", str(OFFLINE_DB_FILE))),
            offline_sync_interval=data.get("offline_sync_interval", 30.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "connection": {
                "url": self.connection.url,
                "key": "***" if self.connection.key else "",  # Mask key
                "initial_delay": self.connection.initial_delay,
                "max_delay": self.connection.max_delay,
                "backoff_multiplier": self.connection.backoff_multiplier,
                "jitter": self.connection.jitter,
                "max_reconnect_attempts": self.connection.max_reconnect_attempts,
                "connection_timeout": self.connection.connection_timeout,
                "operation_timeout": self.connection.operation_timeout,
                "heartbeat_interval": self.connection.heartbeat_interval,
            },
            "circuit_breaker": {
                "failure_threshold": self.circuit_breaker.failure_threshold,
                "success_threshold": self.circuit_breaker.success_threshold,
                "timeout": self.circuit_breaker.timeout,
                "half_open_max_calls": self.circuit_breaker.half_open_max_calls,
            },
            "job_execution": {
                "max_concurrent_jobs": self.job_execution.max_concurrent_jobs,
                "job_poll_interval": self.job_execution.job_poll_interval,
                "lock_timeout": self.job_execution.lock_timeout,
                "cancellation_check_interval": self.job_execution.cancellation_check_interval,
                "node_max_retries": self.job_execution.node_max_retries,
                "node_initial_delay": self.job_execution.node_initial_delay,
                "node_max_delay": self.job_execution.node_max_delay,
                "node_timeout": self.job_execution.node_timeout,
                "checkpoint_enabled": self.job_execution.checkpoint_enabled,
                "checkpoint_on_every_node": self.job_execution.checkpoint_on_every_node,
                "progress_reporting_enabled": self.job_execution.progress_reporting_enabled,
                "progress_update_interval": self.job_execution.progress_update_interval,
            },
            "observability": {
                "metrics_enabled": self.observability.metrics_enabled,
                "resource_monitoring_enabled": self.observability.resource_monitoring_enabled,
                "resource_sample_interval": self.observability.resource_sample_interval,
                "audit_enabled": self.observability.audit_enabled,
                "audit_log_dir": str(self.observability.audit_log_dir),
                "audit_max_file_size_mb": self.observability.audit_max_file_size_mb,
                "audit_backup_count": self.observability.audit_backup_count,
                "metrics_history_limit": self.observability.metrics_history_limit,
            },
            "offline_db_path": str(self.offline_db_path),
            "offline_sync_interval": self.offline_sync_interval,
        }


def validate_credentials(url: str, key: str) -> tuple[bool, Optional[str]]:
    """
    Validate Supabase credentials.

    Args:
        url: Supabase URL
        key: Supabase API key

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "Supabase URL is required"

    if not key:
        return False, "Supabase API key is required"

    # Basic URL validation
    if not url.startswith("https://"):
        return False, "Supabase URL must use HTTPS"

    if "supabase" not in url.lower() and ".co" not in url.lower():
        logger.warning("URL doesn't appear to be a Supabase URL")

    # Key format validation (Supabase keys are base64-ish)
    if len(key) < 20:
        return False, "API key appears to be invalid (too short)"

    return True, None


async def validate_credentials_async(
    url: str,
    key: str,
    timeout: float = 10.0,
) -> tuple[bool, Optional[str]]:
    """
    Validate Supabase credentials by attempting connection.

    Args:
        url: Supabase URL
        key: Supabase API key
        timeout: Connection timeout

    Returns:
        Tuple of (is_valid, error_message)
    """
    import asyncio
    from supabase import create_client

    # Basic validation first
    is_valid, error = validate_credentials(url, key)
    if not is_valid:
        return False, error

    try:
        # Try to connect
        client = await asyncio.wait_for(
            asyncio.to_thread(lambda: create_client(url, key)),
            timeout=timeout
        )

        # Try a simple query
        await asyncio.wait_for(
            asyncio.to_thread(
                lambda: client.table("robots").select("id").limit(1).execute()
            ),
            timeout=timeout
        )

        return True, None

    except asyncio.TimeoutError:
        return False, "Connection timed out"

    except Exception as e:
        error_msg = str(e).lower()
        if "invalid api key" in error_msg or "jwt" in error_msg:
            return False, "Invalid API key"
        elif "not found" in error_msg:
            return False, "Database table 'robots' not found - please run migrations"
        else:
            return False, f"Connection failed: {str(e)}"


# Singleton config instance
_config: Optional[RobotConfig] = None


def get_config() -> RobotConfig:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = RobotConfig.load()
    return _config


def reload_config():
    """Reload configuration from file."""
    global _config
    _config = RobotConfig.load()
    return _config
