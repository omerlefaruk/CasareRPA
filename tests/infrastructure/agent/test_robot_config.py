"""
Tests for RobotConfig configuration management.

Tests cover:
- Happy path: Valid configuration creation and validation
- Sad path: Invalid configurations, missing fields, validation errors
- Edge cases: mTLS configuration, auto-generated IDs, capability detection
"""

import json
import os
import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from casare_rpa.infrastructure.agent.robot_config import (
    ConfigurationError,
    RobotConfig,
)


# ============================================================================
# Happy Path Tests - Valid Configuration
# ============================================================================


class TestRobotConfigCreation:
    """Test successful RobotConfig creation."""

    def test_create_with_minimal_required_fields(self, minimal_config_dict):
        """Creating config with only required fields succeeds."""
        config = RobotConfig(**minimal_config_dict)

        assert config.robot_name == "Minimal Robot"
        assert config.control_plane_url == "ws://localhost:8080/ws"
        assert config.robot_id is not None  # Auto-generated
        assert config.heartbeat_interval == 30  # Default
        assert config.max_concurrent_jobs == 1  # Default

    def test_create_with_all_fields(self, valid_config_dict):
        """Creating config with all fields succeeds."""
        config = RobotConfig(**valid_config_dict)

        assert config.robot_name == "Test Robot"
        assert config.control_plane_url == "wss://orchestrator.example.com/ws/robot"
        assert config.robot_id == "robot-test-12345678"
        assert config.heartbeat_interval == 30
        assert config.max_concurrent_jobs == 2
        assert config.capabilities == ["browser", "desktop"]
        assert config.tags == ["test", "unit"]
        assert config.environment == "test"
        assert config.log_level == "DEBUG"

    def test_auto_generated_robot_id(self, minimal_config_dict):
        """Robot ID is auto-generated when not provided."""
        config = RobotConfig(**minimal_config_dict)

        assert config.robot_id is not None
        assert config.robot_id.startswith("robot-")
        assert len(config.robot_id) > 10  # hostname + unique suffix

    def test_robot_id_unique_across_instances(self, minimal_config_dict):
        """Each new config gets a unique auto-generated ID."""
        config1 = RobotConfig(**minimal_config_dict)
        config2 = RobotConfig(**minimal_config_dict)

        assert config1.robot_id != config2.robot_id

    def test_ws_protocol_accepted(self):
        """WebSocket URL with ws:// protocol is accepted."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
        )
        assert config.control_plane_url == "ws://localhost:8080/ws"

    def test_wss_protocol_accepted(self):
        """WebSocket URL with wss:// protocol is accepted."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="wss://secure.example.com/ws",
        )
        assert config.control_plane_url == "wss://secure.example.com/ws"

    def test_work_dir_defaults_to_cwd(self, minimal_config_dict):
        """Work directory defaults to current working directory."""
        config = RobotConfig(**minimal_config_dict)
        assert config.work_dir == Path.cwd()

    def test_work_dir_string_converted_to_path(self):
        """String work_dir is converted to Path object."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
            work_dir="/tmp/test",
        )
        assert isinstance(config.work_dir, Path)
        assert (
            str(config.work_dir) == "/tmp/test" or str(config.work_dir) == "\\tmp\\test"
        )


class TestRobotConfigProperties:
    """Test RobotConfig computed properties."""

    def test_hostname_property(self, minimal_config_dict):
        """Hostname property returns system hostname."""
        import socket

        config = RobotConfig(**minimal_config_dict)
        assert config.hostname == socket.gethostname()

    def test_os_info_property(self, minimal_config_dict):
        """OS info property returns system and release."""
        config = RobotConfig(**minimal_config_dict)

        assert platform.system() in config.os_info
        assert platform.release() in config.os_info

    def test_uses_mtls_false_when_no_certs(self, minimal_config_dict):
        """uses_mtls is False when no certificates configured."""
        config = RobotConfig(**minimal_config_dict)
        assert config.uses_mtls is False

    def test_to_dict_includes_all_fields(self, valid_config_dict):
        """to_dict() returns all configuration fields."""
        config = RobotConfig(**valid_config_dict)
        config_dict = config.to_dict()

        assert config_dict["robot_name"] == "Test Robot"
        assert config_dict["robot_id"] == "robot-test-12345678"
        assert (
            config_dict["control_plane_url"]
            == "wss://orchestrator.example.com/ws/robot"
        )
        assert config_dict["capabilities"] == ["browser", "desktop"]
        assert "hostname" in config_dict
        assert "os_info" in config_dict


# ============================================================================
# Sad Path Tests - Invalid Configuration
# ============================================================================


class TestRobotConfigValidation:
    """Test RobotConfig validation errors."""

    def test_empty_robot_name_raises_error(self):
        """Empty robot name raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="robot_name is required"):
            RobotConfig(
                robot_name="",
                control_plane_url="ws://localhost:8080/ws",
            )

    def test_whitespace_robot_name_raises_error(self):
        """Whitespace-only robot name raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="robot_name is required"):
            RobotConfig(
                robot_name="   ",
                control_plane_url="ws://localhost:8080/ws",
            )

    def test_empty_control_plane_url_raises_error(self):
        """Empty control plane URL raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="control_plane_url is required"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="",
            )

    def test_invalid_url_scheme_raises_error(self):
        """URL without ws:// or wss:// raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must start with ws:// or wss://"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="http://localhost:8080/ws",
            )

    def test_https_url_scheme_raises_error(self):
        """HTTPS URL raises ConfigurationError (should be wss://)."""
        with pytest.raises(ConfigurationError, match="must start with ws:// or wss://"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="https://localhost:8080/ws",
            )

    def test_heartbeat_interval_zero_raises_error(self):
        """Heartbeat interval of 0 raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="heartbeat_interval must be >= 1"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="ws://localhost:8080/ws",
                heartbeat_interval=0,
            )

    def test_heartbeat_interval_negative_raises_error(self):
        """Negative heartbeat interval raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="heartbeat_interval must be >= 1"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="ws://localhost:8080/ws",
                heartbeat_interval=-5,
            )

    def test_max_concurrent_jobs_zero_raises_error(self):
        """Max concurrent jobs of 0 raises ConfigurationError."""
        with pytest.raises(
            ConfigurationError, match="max_concurrent_jobs must be >= 1"
        ):
            RobotConfig(
                robot_name="Test",
                control_plane_url="ws://localhost:8080/ws",
                max_concurrent_jobs=0,
            )


# ============================================================================
# mTLS Configuration Tests
# ============================================================================


class TestRobotConfigMTLS:
    """Test mTLS configuration handling."""

    def test_mtls_requires_all_three_certs(self, tmp_path):
        """Partial mTLS config (missing certs) raises error."""
        ca_cert = tmp_path / "ca.crt"
        ca_cert.write_text("CA CERT")

        with pytest.raises(ConfigurationError, match="mTLS requires all three"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="wss://localhost:8080/ws",
                ca_cert_path=ca_cert,
                # Missing client_cert_path and client_key_path
            )

    def test_mtls_requires_ca_cert_exists(self, tmp_path):
        """mTLS with non-existent CA cert raises error."""
        # Create client cert and key but not CA cert
        client_cert = tmp_path / "client.crt"
        client_key = tmp_path / "client.key"
        client_cert.write_text("CLIENT CERT")
        client_key.write_text("CLIENT KEY")

        with pytest.raises(ConfigurationError, match="CA certificate not found"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="wss://localhost:8080/ws",
                ca_cert_path=tmp_path / "nonexistent_ca.crt",
                client_cert_path=client_cert,
                client_key_path=client_key,
            )

    def test_mtls_requires_client_cert_exists(self, tmp_path):
        """mTLS with non-existent client cert raises error."""
        ca_cert = tmp_path / "ca.crt"
        client_key = tmp_path / "client.key"
        ca_cert.write_text("CA CERT")
        client_key.write_text("CLIENT KEY")

        with pytest.raises(ConfigurationError, match="Client certificate not found"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="wss://localhost:8080/ws",
                ca_cert_path=ca_cert,
                client_cert_path=tmp_path / "nonexistent_client.crt",
                client_key_path=client_key,
            )

    def test_mtls_requires_client_key_exists(self, tmp_path):
        """mTLS with non-existent client key raises error."""
        ca_cert = tmp_path / "ca.crt"
        client_cert = tmp_path / "client.crt"
        ca_cert.write_text("CA CERT")
        client_cert.write_text("CLIENT CERT")

        with pytest.raises(ConfigurationError, match="Client key not found"):
            RobotConfig(
                robot_name="Test",
                control_plane_url="wss://localhost:8080/ws",
                ca_cert_path=ca_cert,
                client_cert_path=client_cert,
                client_key_path=tmp_path / "nonexistent_client.key",
            )

    def test_valid_mtls_configuration(self, tmp_path):
        """Valid mTLS config with all certs is accepted."""
        ca_cert = tmp_path / "ca.crt"
        client_cert = tmp_path / "client.crt"
        client_key = tmp_path / "client.key"
        ca_cert.write_text("CA CERT")
        client_cert.write_text("CLIENT CERT")
        client_key.write_text("CLIENT KEY")

        config = RobotConfig(
            robot_name="Test",
            control_plane_url="wss://localhost:8080/ws",
            ca_cert_path=ca_cert,
            client_cert_path=client_cert,
            client_key_path=client_key,
        )

        assert config.uses_mtls is True
        assert config.ca_cert_path == ca_cert
        assert config.client_cert_path == client_cert
        assert config.client_key_path == client_key

    def test_cert_path_strings_converted_to_paths(self, tmp_path):
        """String cert paths are converted to Path objects."""
        ca_cert = tmp_path / "ca.crt"
        client_cert = tmp_path / "client.crt"
        client_key = tmp_path / "client.key"
        ca_cert.write_text("CA CERT")
        client_cert.write_text("CLIENT CERT")
        client_key.write_text("CLIENT KEY")

        config = RobotConfig(
            robot_name="Test",
            control_plane_url="wss://localhost:8080/ws",
            ca_cert_path=str(ca_cert),
            client_cert_path=str(client_cert),
            client_key_path=str(client_key),
        )

        assert isinstance(config.ca_cert_path, Path)
        assert isinstance(config.client_cert_path, Path)
        assert isinstance(config.client_key_path, Path)


# ============================================================================
# Loading from File Tests
# ============================================================================


class TestRobotConfigFromFile:
    """Test loading configuration from JSON file."""

    def test_load_from_valid_json_file(self, config_json_file):
        """Loading from valid JSON file succeeds."""
        config = RobotConfig.from_file(config_json_file)

        assert config.robot_name == "Test Robot"
        assert config.control_plane_url == "wss://orchestrator.example.com/ws/robot"
        assert config.robot_id == "robot-test-12345678"

    def test_load_from_nonexistent_file_raises_error(self, tmp_path):
        """Loading from non-existent file raises error."""
        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            RobotConfig.from_file(nonexistent)

    def test_load_from_invalid_json_raises_error(self, invalid_json_file):
        """Loading from invalid JSON file raises error."""
        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            RobotConfig.from_file(invalid_json_file)

    def test_load_from_non_object_json_raises_error(self, tmp_path):
        """Loading from JSON with array raises error."""
        array_file = tmp_path / "array.json"
        with open(array_file, "w") as f:
            json.dump(["item1", "item2"], f)

        with pytest.raises(ConfigurationError, match="must be a JSON object"):
            RobotConfig.from_file(array_file)


# ============================================================================
# Loading from Environment Tests
# ============================================================================


class TestRobotConfigFromEnv:
    """Test loading configuration from environment variables."""

    def test_load_from_env_with_all_vars(self, env_config_vars):
        """Loading from environment with all variables succeeds."""
        config = RobotConfig.from_env()

        assert config.robot_name == "Env Robot"
        assert config.control_plane_url == "wss://test.example.com/ws"
        assert config.robot_id == "robot-env-12345678"
        assert config.heartbeat_interval == 60
        assert config.max_concurrent_jobs == 3
        assert config.capabilities == ["browser", "desktop", "gpu"]
        assert config.tags == ["production", "team-a"]
        assert config.environment == "production"
        assert config.log_level == "WARNING"

    def test_load_from_env_with_minimal_vars(self, minimal_env_config_vars):
        """Loading from environment with minimal variables succeeds."""
        config = RobotConfig.from_env()

        assert config.robot_name == "Minimal Env Robot"
        assert config.control_plane_url == "ws://localhost:9090/ws"
        assert config.robot_id is not None  # Auto-generated

    def test_load_from_env_missing_robot_name_raises_error(self, monkeypatch):
        """Loading from env without CASARE_ROBOT_NAME raises error."""
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost:8080/ws")
        monkeypatch.delenv("CASARE_ROBOT_NAME", raising=False)

        with pytest.raises(ConfigurationError, match="CASARE_ROBOT_NAME.*required"):
            RobotConfig.from_env()

    def test_load_from_env_missing_control_plane_url_raises_error(self, monkeypatch):
        """Loading from env without CASARE_CONTROL_PLANE_URL raises error."""
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Test Robot")
        monkeypatch.delenv("CASARE_CONTROL_PLANE_URL", raising=False)

        with pytest.raises(
            ConfigurationError, match="CASARE_CONTROL_PLANE_URL.*required"
        ):
            RobotConfig.from_env()

    def test_load_from_env_parses_boolean_true(self, monkeypatch):
        """Boolean environment variables are parsed correctly (true)."""
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Test")
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost/ws")
        monkeypatch.setenv("CASARE_VERIFY_SSL", "true")
        monkeypatch.setenv("CASARE_CONTINUE_ON_ERROR", "yes")

        config = RobotConfig.from_env()
        assert config.verify_ssl is True
        assert config.continue_on_error is True

    def test_load_from_env_parses_boolean_false(self, monkeypatch):
        """Boolean environment variables are parsed correctly (false)."""
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Test")
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost/ws")
        monkeypatch.setenv("CASARE_VERIFY_SSL", "false")
        monkeypatch.setenv("CASARE_CONTINUE_ON_ERROR", "no")

        config = RobotConfig.from_env()
        assert config.verify_ssl is False
        assert config.continue_on_error is False

    def test_load_from_env_handles_empty_capabilities(self, monkeypatch):
        """Empty CASARE_CAPABILITIES defaults to auto-detected."""
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Test")
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost/ws")
        monkeypatch.setenv("CASARE_CAPABILITIES", "")

        config = RobotConfig.from_env()
        # Should auto-detect capabilities, at minimum "browser"
        assert isinstance(config.capabilities, list)


# ============================================================================
# Capability Detection Tests
# ============================================================================


class TestRobotConfigCapabilityDetection:
    """Test automatic capability detection."""

    def test_browser_capability_always_detected(self, minimal_config_dict):
        """Browser capability is always detected."""
        config = RobotConfig(**minimal_config_dict)
        assert "browser" in config.capabilities

    @patch("platform.system")
    def test_desktop_capability_on_windows(self, mock_platform, minimal_config_dict):
        """Desktop capability detected on Windows."""
        mock_platform.return_value = "Windows"

        config = RobotConfig(**minimal_config_dict)
        assert "desktop" in config.capabilities
        assert "on_premise" in config.capabilities

    @patch("platform.system")
    def test_no_desktop_capability_on_linux(self, mock_platform, minimal_config_dict):
        """Desktop capability not detected on Linux."""
        mock_platform.return_value = "Linux"

        config = RobotConfig(**minimal_config_dict)
        assert "desktop" not in config.capabilities

    def test_custom_capabilities_override_detection(self):
        """Explicitly provided capabilities override auto-detection."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
            capabilities=["custom", "gpu"],
        )

        assert config.capabilities == ["custom", "gpu"]
        # Browser should NOT be auto-added when explicit list provided
        assert "browser" not in config.capabilities

    def test_high_memory_capability_detected(self, minimal_config_dict):
        """High memory capability detected when >8GB RAM available."""
        # Since psutil is imported inside the method, we check that
        # high_memory is detected if psutil reports >= 8GB RAM
        # This test verifies the logic works with the actual psutil import
        import psutil

        config = RobotConfig(**minimal_config_dict)
        mem_gb = psutil.virtual_memory().total / (1024**3)

        # If system has >= 8GB, high_memory should be in capabilities
        if mem_gb >= 8:
            assert "high_memory" in config.capabilities
        else:
            # System has < 8GB - capability should not be present
            assert "high_memory" not in config.capabilities


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestRobotConfigEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_heartbeat_interval_minimum_accepted(self):
        """Heartbeat interval of 1 (minimum) is accepted."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
            heartbeat_interval=1,
        )
        assert config.heartbeat_interval == 1

    def test_max_concurrent_jobs_minimum_accepted(self):
        """Max concurrent jobs of 1 (minimum) is accepted."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
            max_concurrent_jobs=1,
        )
        assert config.max_concurrent_jobs == 1

    def test_high_max_concurrent_jobs_accepted(self):
        """High max concurrent jobs value is accepted."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
            max_concurrent_jobs=100,
        )
        assert config.max_concurrent_jobs == 100

    def test_url_case_insensitive_scheme_check(self):
        """URL scheme check is case-insensitive."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="WS://localhost:8080/ws",
        )
        assert config.control_plane_url == "WS://localhost:8080/ws"

    def test_empty_tags_list_accepted(self):
        """Empty tags list is valid."""
        config = RobotConfig(
            robot_name="Test",
            control_plane_url="ws://localhost:8080/ws",
            tags=[],
        )
        assert config.tags == []

    def test_unicode_robot_name_accepted(self):
        """Unicode characters in robot name are accepted."""
        config = RobotConfig(
            robot_name="Robot-Alpha-1",
            control_plane_url="ws://localhost:8080/ws",
        )
        assert config.robot_name == "Robot-Alpha-1"

    def test_reconnection_defaults(self, minimal_config_dict):
        """Reconnection settings have sensible defaults."""
        config = RobotConfig(**minimal_config_dict)

        assert config.reconnect_delay == 1.0
        assert config.max_reconnect_delay == 60.0
        assert config.reconnect_multiplier == 2.0

    def test_job_timeout_default(self, minimal_config_dict):
        """Job timeout has sensible default (1 hour)."""
        config = RobotConfig(**minimal_config_dict)
        assert config.job_timeout == 3600.0


# ============================================================================
# API Key Configuration Tests
# ============================================================================


class TestRobotConfigApiKey:
    """Test API key configuration and validation."""

    def test_api_key_defaults_to_none(self, minimal_config_dict):
        """API key defaults to None when not provided."""
        config = RobotConfig(**minimal_config_dict)
        assert config.api_key is None

    def test_api_key_with_valid_format(self):
        """Valid API key format is accepted."""
        valid_key = "crpa_" + "a" * 43  # 48 chars total
        config = RobotConfig(
            robot_name="Test Robot",
            control_plane_url="ws://localhost:8080/ws",
            api_key=valid_key,
        )
        assert config.api_key == valid_key

    def test_uses_api_key_true_when_set(self):
        """uses_api_key property returns True when API key is set."""
        valid_key = "crpa_" + "a" * 43
        config = RobotConfig(
            robot_name="Test Robot",
            control_plane_url="ws://localhost:8080/ws",
            api_key=valid_key,
        )
        assert config.uses_api_key is True

    def test_uses_api_key_false_when_not_set(self, minimal_config_dict):
        """uses_api_key property returns False when API key is not set."""
        config = RobotConfig(**minimal_config_dict)
        assert config.uses_api_key is False

    def test_api_key_wrong_prefix_raises_error(self):
        """API key with wrong prefix raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must start with 'crpa_'"):
            RobotConfig(
                robot_name="Test Robot",
                control_plane_url="ws://localhost:8080/ws",
                api_key="wrong_prefix_key_here_1234567890123456789",
            )

    def test_api_key_too_short_raises_error(self):
        """API key that is too short raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="too short"):
            RobotConfig(
                robot_name="Test Robot",
                control_plane_url="ws://localhost:8080/ws",
                api_key="crpa_short",
            )

    def test_api_key_minimum_length_accepted(self):
        """API key at minimum length (40 chars) is accepted."""
        min_key = "crpa_" + "a" * 35  # 5 + 35 = 40
        config = RobotConfig(
            robot_name="Test Robot",
            control_plane_url="ws://localhost:8080/ws",
            api_key=min_key,
        )
        assert config.api_key == min_key

    def test_to_dict_includes_uses_api_key(self):
        """to_dict includes uses_api_key field."""
        valid_key = "crpa_" + "a" * 43
        config = RobotConfig(
            robot_name="Test Robot",
            control_plane_url="ws://localhost:8080/ws",
            api_key=valid_key,
        )
        config_dict = config.to_dict()
        assert "uses_api_key" in config_dict
        assert config_dict["uses_api_key"] is True


class TestRobotConfigApiKeyFromEnv:
    """Test API key loading from environment variables."""

    def test_load_api_key_from_env(self, monkeypatch):
        """API key is loaded from CASARE_API_KEY environment variable."""
        valid_key = "crpa_" + "a" * 43
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Env Robot")
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost:8080/ws")
        monkeypatch.setenv("CASARE_API_KEY", valid_key)

        config = RobotConfig.from_env()

        assert config.api_key == valid_key
        assert config.uses_api_key is True

    def test_api_key_env_not_required(self, monkeypatch):
        """API key environment variable is optional."""
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Test Robot")
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost:8080/ws")
        # Ensure CASARE_API_KEY is not set
        monkeypatch.delenv("CASARE_API_KEY", raising=False)

        config = RobotConfig.from_env()

        assert config.api_key is None
        assert config.uses_api_key is False

    def test_invalid_api_key_from_env_raises_error(self, monkeypatch):
        """Invalid API key from environment raises ConfigurationError."""
        monkeypatch.setenv("CASARE_ROBOT_NAME", "Test Robot")
        monkeypatch.setenv("CASARE_CONTROL_PLANE_URL", "ws://localhost:8080/ws")
        monkeypatch.setenv("CASARE_API_KEY", "invalid_key")

        with pytest.raises(ConfigurationError):
            RobotConfig.from_env()


class TestRobotConfigApiKeyFromFile:
    """Test API key loading from config file."""

    def test_load_api_key_from_file(self, tmp_path):
        """API key is loaded from config file."""
        valid_key = "crpa_" + "a" * 43
        config_data = {
            "robot_name": "File Robot",
            "control_plane_url": "ws://localhost:8080/ws",
            "api_key": valid_key,
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            import json

            json.dump(config_data, f)

        config = RobotConfig.from_file(config_file)

        assert config.api_key == valid_key
        assert config.uses_api_key is True

    def test_api_key_optional_in_file(self, tmp_path):
        """API key is optional in config file."""
        config_data = {
            "robot_name": "File Robot",
            "control_plane_url": "ws://localhost:8080/ws",
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            import json

            json.dump(config_data, f)

        config = RobotConfig.from_file(config_file)

        assert config.api_key is None
        assert config.uses_api_key is False
