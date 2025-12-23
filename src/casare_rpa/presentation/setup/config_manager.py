"""
Client Configuration Manager.

Handles loading, saving, and validation of client configuration
for CasareRPA Robot + Designer installations.
"""

import os
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator connection."""

    url: str = ""
    api_key: str = ""
    verify_ssl: bool = True
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0


@dataclass
class RobotConfig:
    """Configuration for robot agent."""

    name: str = ""
    capabilities: list[str] = field(default_factory=lambda: ["browser", "desktop"])
    tags: list[str] = field(default_factory=list)
    max_concurrent_jobs: int = 2
    environment: str = "production"


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    directory: str = ""
    max_size_mb: int = 50
    retention_days: int = 30


@dataclass
class ClientConfig:
    """
    Complete client configuration.

    Contains all settings for CasareRPA client installation including
    orchestrator connection, robot settings, and logging preferences.
    """

    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    robot: RobotConfig = field(default_factory=RobotConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    first_run_complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "orchestrator": {
                "url": self.orchestrator.url,
                "api_key": self.orchestrator.api_key,
                "verify_ssl": self.orchestrator.verify_ssl,
                "reconnect_delay": self.orchestrator.reconnect_delay,
                "max_reconnect_delay": self.orchestrator.max_reconnect_delay,
            },
            "robot": {
                "name": self.robot.name,
                "capabilities": self.robot.capabilities,
                "tags": self.robot.tags,
                "max_concurrent_jobs": self.robot.max_concurrent_jobs,
                "environment": self.robot.environment,
            },
            "logging": {
                "level": self.logging.level,
                "directory": self.logging.directory,
                "max_size_mb": self.logging.max_size_mb,
                "retention_days": self.logging.retention_days,
            },
            "first_run_complete": self.first_run_complete,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientConfig":
        """Create configuration from dictionary."""
        config = cls()

        if "orchestrator" in data:
            orch = data["orchestrator"]
            config.orchestrator = OrchestratorConfig(
                url=orch.get("url", ""),
                api_key=orch.get("api_key", ""),
                verify_ssl=orch.get("verify_ssl", True),
                reconnect_delay=orch.get("reconnect_delay", 1.0),
                max_reconnect_delay=orch.get("max_reconnect_delay", 60.0),
            )

        if "robot" in data:
            robot = data["robot"]
            config.robot = RobotConfig(
                name=robot.get("name", ""),
                capabilities=robot.get("capabilities", ["browser", "desktop"]),
                tags=robot.get("tags", []),
                max_concurrent_jobs=robot.get("max_concurrent_jobs", 2),
                environment=robot.get("environment", "production"),
            )

        if "logging" in data:
            log = data["logging"]
            config.logging = LoggingConfig(
                level=log.get("level", "INFO"),
                directory=log.get("directory", ""),
                max_size_mb=log.get("max_size_mb", 50),
                retention_days=log.get("retention_days", 30),
            )

        config.first_run_complete = data.get("first_run_complete", False)
        return config


class ClientConfigManager:
    """
    Manages client configuration file operations.

    Handles:
    - Loading configuration from file
    - Saving configuration to file
    - Configuration validation
    - Default value generation
    """

    DEFAULT_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "CasareRPA"
    DEFAULT_CONFIG_FILE = "config.yaml"

    def __init__(
        self,
        config_dir: Path | None = None,
        config_file: str | None = None,
    ) -> None:
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory for configuration files
            config_file: Name of configuration file
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config_path = self.config_dir / self.config_file

    def ensure_directories(self) -> None:
        """Create configuration directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)
        (self.config_dir / "workflows").mkdir(exist_ok=True)

    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_path.exists()

    def needs_setup(self) -> bool:
        """
        Check if first-run setup is needed.

        Returns:
            True if setup wizard should be shown
        """
        if not self.config_exists():
            return True

        try:
            config = self.load()
            return not config.first_run_complete
        except Exception as e:
            logger.warning(f"Error checking setup status: {e}")
            return True

    def load(self) -> ClientConfig:
        """
        Load configuration from file.

        Returns:
            ClientConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            content = self.config_path.read_text(encoding="utf-8")

            if YAML_AVAILABLE:
                data = yaml.safe_load(content)
            else:
                # Fall back to JSON if YAML not available
                import json

                data = json.loads(content)

            if not isinstance(data, dict):
                raise ValueError("Configuration must be a dictionary")

            return ClientConfig.from_dict(data)

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ValueError(f"Invalid configuration file: {e}") from e

    def save(self, config: ClientConfig) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
        """
        self.ensure_directories()

        data = config.to_dict()

        try:
            if YAML_AVAILABLE:
                content = yaml.dump(
                    data,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            else:
                import json

                content = json.dumps(data, indent=2, ensure_ascii=False)

            # Add header comment
            header = (
                "# CasareRPA Client Configuration\n"
                "# Generated by Setup Wizard\n"
                "#\n"
                "# Edit this file to change settings, or use the Settings dialog in Designer.\n"
                "#\n"
                "# Documentation: https://github.com/omerlefaruk/CasareRPA\n"
                "\n"
            )

            self.config_path.write_text(header + content, encoding="utf-8")
            logger.info(f"Configuration saved to: {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def create_default(self) -> ClientConfig:
        """
        Create default configuration.

        Returns:
            ClientConfig with default values
        """
        hostname = socket.gethostname()

        config = ClientConfig()
        config.robot.name = f"{hostname}-Robot"
        config.logging.directory = str(self.config_dir / "logs")

        return config

    def validate_url(self, url: str) -> str | None:
        """
        Validate orchestrator URL.

        Args:
            url: URL to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not url:
            return None  # Empty URL is allowed (local-only mode)

        url_lower = url.lower().strip()

        if not url_lower.startswith(("ws://", "wss://")):
            return "URL must start with ws:// or wss://"

        if len(url) < 10:
            return "URL appears to be incomplete"

        # Check for common mistakes
        if "localhost" in url_lower and url_lower.startswith("wss://"):
            return "Use ws:// for localhost connections (not wss://)"

        return None

    def validate_api_key(self, api_key: str) -> str | None:
        """
        Validate API key format.

        Args:
            api_key: API key to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not api_key:
            return None  # Empty API key is allowed

        if not api_key.startswith("crpa_"):
            return "API key must start with 'crpa_' prefix"

        if len(api_key) < 40:
            return "API key appears to be truncated"

        return None

    def validate_robot_name(self, name: str) -> str | None:
        """
        Validate robot name.

        Args:
            name: Robot name to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not name or not name.strip():
            return "Robot name is required"

        if len(name) > 100:
            return "Robot name must be 100 characters or less"

        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in name:
                return f"Robot name cannot contain '{char}'"

        return None

    async def test_connection(
        self,
        url: str,
        api_key: str | None = None,
    ) -> tuple[bool, str]:
        """
        Test connection to orchestrator.

        Args:
            url: Orchestrator WebSocket URL
            api_key: Optional API key for authentication

        Returns:
            Tuple of (success, message)
        """
        import asyncio

        try:
            import websockets
        except ImportError:
            return False, "websockets library not installed"

        if not url:
            return False, "No URL provided"

        # Build connection URL with API key if provided
        connect_url = url
        if api_key:
            separator = "&" if "?" in url else "?"
            connect_url = f"{url}{separator}api_key={api_key}"

        try:
            # Attempt WebSocket connection with timeout
            async with asyncio.timeout(10):
                async with websockets.connect(connect_url, close_timeout=5) as ws:
                    # Send a ping to verify connection
                    await ws.ping()
                    return True, "Connection successful"

        except TimeoutError:
            return False, "Connection timed out"
        except ConnectionRefusedError:
            return False, "Connection refused - check URL"
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "4001" in error_msg:
                return False, "Authentication failed - check API key"
            elif "404" in error_msg:
                return False, "Endpoint not found - check URL path"
            elif "ssl" in error_msg.lower():
                return False, "SSL/TLS error - try ws:// instead of wss://"
            else:
                return False, f"Connection failed: {error_msg}"
