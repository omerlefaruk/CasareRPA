"""
Robot Agent Configuration.

Provides configuration management for robot agents connecting to orchestrator.
Supports loading from environment variables, config files, or programmatic setup.
"""

import os
import platform
import socket
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from loguru import logger


class ConfigurationError(Exception):
    """Raised when robot configuration is invalid or missing required values."""

    pass


@dataclass
class RobotConfig:
    """
    Configuration for a robot agent.

    Attributes:
        robot_name: Human-readable name for this robot
        control_plane_url: WebSocket URL for orchestrator connection
        robot_id: Unique identifier (auto-generated if not set)
        api_key: API key for orchestrator authentication (format: crpa_...)
        heartbeat_interval: Seconds between heartbeat messages
        max_concurrent_jobs: Maximum jobs this robot can execute simultaneously
        capabilities: List of capability strings (browser, desktop, gpu, etc.)
        tags: Tags for robot filtering and selection
        environment: Environment name (production, staging, development)
        work_dir: Working directory for workflow execution
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    robot_name: str
    control_plane_url: str
    robot_id: Optional[str] = None
    api_key: Optional[str] = None  # API key for authentication (crpa_...)
    heartbeat_interval: int = 30
    max_concurrent_jobs: int = 1
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    environment: str = "production"
    work_dir: Path = field(default_factory=lambda: Path.cwd())
    log_level: str = "INFO"

    # mTLS configuration (optional - for secure connections)
    ca_cert_path: Optional[Path] = None
    client_cert_path: Optional[Path] = None
    client_key_path: Optional[Path] = None
    verify_ssl: bool = True

    # Reconnection settings
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0
    reconnect_multiplier: float = 2.0

    # Job execution settings
    job_timeout: float = 3600.0  # Default 1 hour max per job
    continue_on_error: bool = False

    def __post_init__(self) -> None:
        """Initialize derived values and validate configuration."""
        # Auto-generate robot ID if not provided
        if not self.robot_id:
            hostname = socket.gethostname()
            unique_suffix = uuid.uuid4().hex[:8]
            self.robot_id = f"robot-{hostname}-{unique_suffix}"
            logger.debug(f"Auto-generated robot_id: {self.robot_id}")

        # Ensure work_dir is a Path
        if isinstance(self.work_dir, str):
            self.work_dir = Path(self.work_dir)

        # Ensure cert paths are Path objects if provided
        if self.ca_cert_path and isinstance(self.ca_cert_path, str):
            self.ca_cert_path = Path(self.ca_cert_path)
        if self.client_cert_path and isinstance(self.client_cert_path, str):
            self.client_cert_path = Path(self.client_cert_path)
        if self.client_key_path and isinstance(self.client_key_path, str):
            self.client_key_path = Path(self.client_key_path)

        # Set default capabilities based on platform
        if not self.capabilities:
            self.capabilities = self._detect_capabilities()

        self._validate()

    def _detect_capabilities(self) -> List[str]:
        """Auto-detect robot capabilities based on system."""
        caps = []

        # Always assume browser capability (Playwright works on all platforms)
        caps.append("browser")

        # Desktop capability on Windows only
        if platform.system() == "Windows":
            caps.append("desktop")
            caps.append("on_premise")

        # Check for high memory (>8GB)
        try:
            import psutil

            mem_gb = psutil.virtual_memory().total / (1024**3)
            if mem_gb >= 8:
                caps.append("high_memory")
        except ImportError:
            pass

        return caps

    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.robot_name or not self.robot_name.strip():
            raise ConfigurationError("robot_name is required and cannot be empty")

        if not self.control_plane_url or not self.control_plane_url.strip():
            raise ConfigurationError(
                "control_plane_url is required and cannot be empty"
            )

        # Validate URL scheme
        url_lower = self.control_plane_url.lower()
        if not url_lower.startswith(("ws://", "wss://")):
            raise ConfigurationError(
                f"control_plane_url must start with ws:// or wss://, got: {self.control_plane_url}"
            )

        if self.heartbeat_interval < 1:
            raise ConfigurationError(
                f"heartbeat_interval must be >= 1, got: {self.heartbeat_interval}"
            )

        if self.max_concurrent_jobs < 1:
            raise ConfigurationError(
                f"max_concurrent_jobs must be >= 1, got: {self.max_concurrent_jobs}"
            )

        # Validate API key format if provided
        if self.api_key:
            if not self.api_key.startswith("crpa_"):
                raise ConfigurationError("api_key must start with 'crpa_' prefix")
            if len(self.api_key) < 40:
                raise ConfigurationError("api_key appears to be truncated (too short)")

        # Validate mTLS configuration (all or nothing)
        mtls_paths = [self.ca_cert_path, self.client_cert_path, self.client_key_path]
        mtls_set = sum(1 for p in mtls_paths if p is not None)
        if mtls_set > 0 and mtls_set < 3:
            raise ConfigurationError(
                "mTLS requires all three: ca_cert_path, client_cert_path, client_key_path"
            )

        # Verify mTLS files exist if provided
        if self.ca_cert_path and not self.ca_cert_path.exists():
            raise ConfigurationError(f"CA certificate not found: {self.ca_cert_path}")
        if self.client_cert_path and not self.client_cert_path.exists():
            raise ConfigurationError(
                f"Client certificate not found: {self.client_cert_path}"
            )
        if self.client_key_path and not self.client_key_path.exists():
            raise ConfigurationError(f"Client key not found: {self.client_key_path}")

    @property
    def uses_mtls(self) -> bool:
        """Check if mTLS is configured."""
        return all([self.ca_cert_path, self.client_cert_path, self.client_key_path])

    @property
    def uses_api_key(self) -> bool:
        """Check if API key authentication is configured."""
        return bool(self.api_key)

    @property
    def hostname(self) -> str:
        """Get system hostname."""
        return socket.gethostname()

    @property
    def os_info(self) -> str:
        """Get OS information string."""
        return f"{platform.system()} {platform.release()}"

    @classmethod
    def from_env(cls) -> "RobotConfig":
        """
        Load configuration from environment variables.

        Environment Variables:
            CASARE_ROBOT_NAME - Robot name (required)
            CASARE_CONTROL_PLANE_URL - WebSocket URL (required)
            CASARE_ROBOT_ID - Optional robot ID
            CASARE_API_KEY - API key for authentication (format: crpa_...)
            CASARE_HEARTBEAT_INTERVAL - Heartbeat interval in seconds (default: 30)
            CASARE_MAX_CONCURRENT_JOBS - Max concurrent jobs (default: 1)
            CASARE_CAPABILITIES - Comma-separated capabilities
            CASARE_TAGS - Comma-separated tags
            CASARE_ENVIRONMENT - Environment name (default: production)
            CASARE_WORK_DIR - Working directory
            CASARE_LOG_LEVEL - Log level (default: INFO)
            CASARE_CA_CERT_PATH - CA certificate path for mTLS
            CASARE_CLIENT_CERT_PATH - Client certificate path for mTLS
            CASARE_CLIENT_KEY_PATH - Client key path for mTLS
            CASARE_VERIFY_SSL - Verify SSL (default: true)
            CASARE_JOB_TIMEOUT - Job timeout in seconds (default: 3600)
            CASARE_CONTINUE_ON_ERROR - Continue on error (default: false)

        Returns:
            RobotConfig instance

        Raises:
            ConfigurationError: If required variables are missing
        """
        robot_name = os.environ.get("CASARE_ROBOT_NAME")
        control_plane_url = os.environ.get("CASARE_CONTROL_PLANE_URL")

        if not robot_name:
            raise ConfigurationError(
                "CASARE_ROBOT_NAME environment variable is required"
            )
        if not control_plane_url:
            raise ConfigurationError(
                "CASARE_CONTROL_PLANE_URL environment variable is required"
            )

        # Parse comma-separated lists
        capabilities_str = os.environ.get("CASARE_CAPABILITIES", "")
        capabilities = (
            [c.strip() for c in capabilities_str.split(",") if c.strip()]
            if capabilities_str
            else []
        )

        tags_str = os.environ.get("CASARE_TAGS", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        # Parse paths
        ca_cert = os.environ.get("CASARE_CA_CERT_PATH")
        client_cert = os.environ.get("CASARE_CLIENT_CERT_PATH")
        client_key = os.environ.get("CASARE_CLIENT_KEY_PATH")
        work_dir = os.environ.get("CASARE_WORK_DIR")

        # Parse boolean
        verify_ssl_str = os.environ.get("CASARE_VERIFY_SSL", "true").lower()
        verify_ssl = verify_ssl_str in ("true", "1", "yes")

        continue_on_error_str = os.environ.get(
            "CASARE_CONTINUE_ON_ERROR", "false"
        ).lower()
        continue_on_error = continue_on_error_str in ("true", "1", "yes")

        return cls(
            robot_name=robot_name,
            control_plane_url=control_plane_url,
            robot_id=os.environ.get("CASARE_ROBOT_ID"),
            api_key=os.environ.get("CASARE_API_KEY"),
            heartbeat_interval=int(os.environ.get("CASARE_HEARTBEAT_INTERVAL", "30")),
            max_concurrent_jobs=int(os.environ.get("CASARE_MAX_CONCURRENT_JOBS", "1")),
            capabilities=capabilities,
            tags=tags,
            environment=os.environ.get("CASARE_ENVIRONMENT", "production"),
            work_dir=Path(work_dir) if work_dir else Path.cwd(),
            log_level=os.environ.get("CASARE_LOG_LEVEL", "INFO"),
            ca_cert_path=Path(ca_cert) if ca_cert else None,
            client_cert_path=Path(client_cert) if client_cert else None,
            client_key_path=Path(client_key) if client_key else None,
            verify_ssl=verify_ssl,
            job_timeout=float(os.environ.get("CASARE_JOB_TIMEOUT", "3600")),
            continue_on_error=continue_on_error,
        )

    @classmethod
    def from_file(cls, config_path: Path) -> "RobotConfig":
        """
        Load configuration from a JSON file.

        Args:
            config_path: Path to configuration JSON file

        Returns:
            RobotConfig instance

        Raises:
            ConfigurationError: If file is invalid or missing required fields
        """
        import json

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("Configuration must be a JSON object")

        # Convert path strings to Path objects
        for key in ["work_dir", "ca_cert_path", "client_cert_path", "client_key_path"]:
            if key in data and data[key]:
                data[key] = Path(data[key])

        return cls(**data)

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "robot_name": self.robot_name,
            "robot_id": self.robot_id,
            "control_plane_url": self.control_plane_url,
            "heartbeat_interval": self.heartbeat_interval,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "capabilities": self.capabilities,
            "tags": self.tags,
            "environment": self.environment,
            "hostname": self.hostname,
            "os_info": self.os_info,
            "uses_api_key": self.uses_api_key,
            "uses_mtls": self.uses_mtls,
        }
