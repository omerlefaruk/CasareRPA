"""
Test fixtures for setup wizard tests.

Provides:
- Temporary configuration directories
- Mock WebSocket connections
- Pre-configured ClientConfig instances
- Qt test utilities
"""

import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from casare_rpa.presentation.setup.config_manager import (
    ClientConfig,
    ClientConfigManager,
    OrchestratorConfig,
    RobotConfig,
    LoggingConfig,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """
    Create a temporary directory for configuration files.

    Returns:
        Path to temporary config directory.
    """
    config_dir = tmp_path / "CasareRPA"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def config_manager(temp_config_dir: Path) -> ClientConfigManager:
    """
    Create a ClientConfigManager with temporary directory.

    Args:
        temp_config_dir: Temporary directory for config files.

    Returns:
        ClientConfigManager instance pointing to temp directory.
    """
    return ClientConfigManager(config_dir=temp_config_dir)


@pytest.fixture
def default_config() -> ClientConfig:
    """
    Create a ClientConfig with default values.

    Returns:
        ClientConfig with defaults.
    """
    return ClientConfig()


@pytest.fixture
def complete_config() -> ClientConfig:
    """
    Create a fully populated ClientConfig.

    Returns:
        ClientConfig with all fields populated.
    """
    config = ClientConfig()
    config.orchestrator = OrchestratorConfig(
        url="wss://orchestrator.example.com/ws/robot",
        api_key="crpa_1234567890abcdef1234567890abcdef1234567890",
        verify_ssl=True,
        reconnect_delay=1.0,
        max_reconnect_delay=60.0,
    )
    config.robot = RobotConfig(
        name="TestRobot-01",
        capabilities=["browser", "desktop", "high_memory"],
        tags=["finance", "hr"],
        max_concurrent_jobs=4,
        environment="production",
    )
    config.logging = LoggingConfig(
        level="DEBUG",
        directory="/var/log/casarerpa",
        max_size_mb=100,
        retention_days=60,
    )
    config.first_run_complete = True
    return config


@pytest.fixture
def mock_websocket():
    """
    Create a mock WebSocket connection.

    Returns:
        AsyncMock configured as a WebSocket.
    """
    ws = AsyncMock()
    ws.ping = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_websockets_connect(mock_websocket):
    """
    Patch websockets.connect to return mock WebSocket.

    Yields:
        Patched connect function.
    """

    async def mock_connect(*args, **kwargs):
        return mock_websocket

    # Create async context manager
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_websocket)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("casare_rpa.presentation.setup.config_manager.websockets") as mock_ws:
        mock_ws.connect = Mock(return_value=cm)
        yield mock_ws


@pytest.fixture
def mock_websockets_timeout():
    """
    Patch websockets.connect to simulate timeout.

    Yields:
        Patched connect that raises TimeoutError.
    """
    import asyncio

    async def mock_connect(*args, **kwargs):
        raise asyncio.TimeoutError("Connection timed out")

    with patch("casare_rpa.presentation.setup.config_manager.websockets") as mock_ws:
        mock_ws.connect = Mock(side_effect=asyncio.TimeoutError())
        yield mock_ws


@pytest.fixture
def mock_websockets_refused():
    """
    Patch websockets.connect to simulate connection refused.

    Yields:
        Patched connect that raises ConnectionRefusedError.
    """
    with patch("casare_rpa.presentation.setup.config_manager.websockets") as mock_ws:
        mock_ws.connect = Mock(side_effect=ConnectionRefusedError())
        yield mock_ws


@pytest.fixture
def sample_config_yaml() -> str:
    """
    Return a sample YAML configuration string.

    Returns:
        Valid YAML config content.
    """
    return """# CasareRPA Client Configuration
orchestrator:
  url: wss://test.example.com/ws/robot
  api_key: crpa_test1234567890abcdef1234567890abcdef
  verify_ssl: true
  reconnect_delay: 1.0
  max_reconnect_delay: 60.0
robot:
  name: TestRobot
  capabilities:
    - browser
    - desktop
  tags:
    - test
  max_concurrent_jobs: 2
  environment: development
logging:
  level: INFO
  directory: /tmp/logs
  max_size_mb: 50
  retention_days: 30
first_run_complete: true
"""


@pytest.fixture
def sample_config_json() -> str:
    """
    Return a sample JSON configuration string.

    Returns:
        Valid JSON config content.
    """
    import json

    data = {
        "orchestrator": {
            "url": "wss://test.example.com/ws/robot",
            "api_key": "crpa_test1234567890abcdef1234567890abcdef",
            "verify_ssl": True,
            "reconnect_delay": 1.0,
            "max_reconnect_delay": 60.0,
        },
        "robot": {
            "name": "TestRobot",
            "capabilities": ["browser", "desktop"],
            "tags": ["test"],
            "max_concurrent_jobs": 2,
            "environment": "development",
        },
        "logging": {
            "level": "INFO",
            "directory": "/tmp/logs",
            "max_size_mb": 50,
            "retention_days": 30,
        },
        "first_run_complete": True,
    }
    return json.dumps(data, indent=2)
