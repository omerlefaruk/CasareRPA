"""
Tests for config schema module.

Tests Pydantic model validation for all config sections:
- DatabaseConfig
- SupabaseConfig
- SecurityConfig
- OrchestratorConfig
- RobotConfig
- LoggingConfig
- QueueConfig
- TimeoutConfig
- RateLimitConfig
- MetricsConfig
- VaultConfig
- StorageConfig
- CloudflareConfig
- Config (root)
"""

import pytest
from pathlib import Path
from pydantic import ValidationError


class TestDatabaseConfig:
    """Tests for DatabaseConfig schema."""

    def test_database_config_defaults(self):
        """DatabaseConfig has correct defaults."""
        from casare_rpa.config.schema import DatabaseConfig

        config = DatabaseConfig()

        assert config.enabled is True
        assert config.url is None
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "casare_rpa"
        assert config.user == "casare_user"
        assert config.password == ""
        assert config.pool_min_size == 2
        assert config.pool_max_size == 10
        assert config.command_timeout == 60.0
        assert config.max_inactive_lifetime == 300.0

    def test_database_config_connection_url_from_url(self):
        """connection_url property returns explicit URL when set."""
        from casare_rpa.config.schema import DatabaseConfig

        config = DatabaseConfig(url="postgresql://user:pass@host:5432/db")
        assert config.connection_url == "postgresql://user:pass@host:5432/db"

    def test_database_config_connection_url_built(self):
        """connection_url property builds URL from components."""
        from casare_rpa.config.schema import DatabaseConfig

        config = DatabaseConfig(
            host="myhost", port=5433, name="mydb", user="myuser", password="mypass"
        )
        assert config.connection_url == "postgresql://myuser:mypass@myhost:5433/mydb"

    def test_database_config_invalid_url_prefix(self):
        """DatabaseConfig rejects URL without postgresql:// prefix."""
        from casare_rpa.config.schema import DatabaseConfig

        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(url="mysql://user:pass@host/db")

        assert "postgresql://" in str(exc_info.value)

    def test_database_config_valid_url_prefixes(self):
        """DatabaseConfig accepts postgresql:// and postgres:// prefixes."""
        from casare_rpa.config.schema import DatabaseConfig

        config1 = DatabaseConfig(url="postgresql://user:pass@host/db")
        assert config1.url == "postgresql://user:pass@host/db"

        config2 = DatabaseConfig(url="postgres://user:pass@host/db")
        assert config2.url == "postgres://user:pass@host/db"

    def test_database_config_port_bounds(self):
        """DatabaseConfig validates port range (1-65535)."""
        from casare_rpa.config.schema import DatabaseConfig

        # Valid ports
        DatabaseConfig(port=1)
        DatabaseConfig(port=65535)

        # Invalid ports
        with pytest.raises(ValidationError):
            DatabaseConfig(port=0)

        with pytest.raises(ValidationError):
            DatabaseConfig(port=65536)


class TestSupabaseConfig:
    """Tests for SupabaseConfig schema."""

    def test_supabase_config_defaults(self):
        """SupabaseConfig has correct defaults."""
        from casare_rpa.config.schema import SupabaseConfig

        config = SupabaseConfig()

        assert config.url is None
        assert config.key is None
        assert config.service_key is None

    def test_supabase_config_is_configured_false(self):
        """is_configured returns False when not configured."""
        from casare_rpa.config.schema import SupabaseConfig

        config = SupabaseConfig()
        assert config.is_configured is False

        config2 = SupabaseConfig(url="https://test.supabase.co")
        assert config2.is_configured is False  # Missing key

    def test_supabase_config_is_configured_true(self):
        """is_configured returns True when both url and key set."""
        from casare_rpa.config.schema import SupabaseConfig

        config = SupabaseConfig(url="https://test.supabase.co", key="anon-key")
        assert config.is_configured is True

    def test_supabase_config_invalid_url(self):
        """SupabaseConfig rejects URL without https://."""
        from casare_rpa.config.schema import SupabaseConfig

        with pytest.raises(ValidationError) as exc_info:
            SupabaseConfig(url="http://test.supabase.co")

        assert "https://" in str(exc_info.value)


class TestSecurityConfig:
    """Tests for SecurityConfig schema."""

    def test_security_config_defaults(self):
        """SecurityConfig has correct defaults."""
        from casare_rpa.config.schema import SecurityConfig

        config = SecurityConfig()

        assert config.api_secret is None
        assert config.jwt_expiration_seconds == 3600
        assert config.robot_auth_enabled is False
        assert config.verify_ssl is True
        assert config.ca_cert_path is None
        assert config.client_cert_path is None
        assert config.client_key_path is None

    def test_security_config_uses_mtls_false(self):
        """uses_mtls returns False when mTLS not configured."""
        from casare_rpa.config.schema import SecurityConfig

        config = SecurityConfig()
        assert config.uses_mtls is False

        config2 = SecurityConfig(ca_cert_path=Path("/ca.pem"))
        assert config2.uses_mtls is False  # Missing other paths

    def test_security_config_uses_mtls_true(self):
        """uses_mtls returns True when all mTLS paths set."""
        from casare_rpa.config.schema import SecurityConfig

        config = SecurityConfig(
            ca_cert_path=Path("/ca.pem"),
            client_cert_path=Path("/client.pem"),
            client_key_path=Path("/client-key.pem"),
        )
        assert config.uses_mtls is True

    def test_security_config_mtls_partial_fails(self):
        """SecurityConfig rejects partial mTLS configuration."""
        from casare_rpa.config.schema import SecurityConfig

        # Only 1 of 3 mTLS paths set
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(ca_cert_path=Path("/ca.pem"))

        assert "mTLS requires all three" in str(exc_info.value)

        # Only 2 of 3 mTLS paths set
        with pytest.raises(ValidationError):
            SecurityConfig(
                ca_cert_path=Path("/ca.pem"), client_cert_path=Path("/client.pem")
            )

    def test_security_config_jwt_expiration_minimum(self):
        """SecurityConfig validates jwt_expiration_seconds minimum (60)."""
        from casare_rpa.config.schema import SecurityConfig

        SecurityConfig(jwt_expiration_seconds=60)  # Valid

        with pytest.raises(ValidationError):
            SecurityConfig(jwt_expiration_seconds=59)


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig schema."""

    def test_orchestrator_config_defaults(self):
        """OrchestratorConfig has correct defaults."""
        from casare_rpa.config.schema import OrchestratorConfig

        config = OrchestratorConfig()

        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.workers == 1
        assert "http://localhost:5173" in config.cors_origins
        assert config.ssl_keyfile is None
        assert config.ssl_certfile is None

    def test_orchestrator_config_uses_ssl_false(self):
        """uses_ssl returns False when SSL not configured."""
        from casare_rpa.config.schema import OrchestratorConfig

        config = OrchestratorConfig()
        assert config.uses_ssl is False

    def test_orchestrator_config_uses_ssl_true(self):
        """uses_ssl returns True when both SSL files set."""
        from casare_rpa.config.schema import OrchestratorConfig

        config = OrchestratorConfig(
            ssl_keyfile=Path("/key.pem"), ssl_certfile=Path("/cert.pem")
        )
        assert config.uses_ssl is True

    def test_orchestrator_config_port_bounds(self):
        """OrchestratorConfig validates port range."""
        from casare_rpa.config.schema import OrchestratorConfig

        with pytest.raises(ValidationError):
            OrchestratorConfig(port=0)

        with pytest.raises(ValidationError):
            OrchestratorConfig(port=70000)


class TestRobotConfig:
    """Tests for RobotConfig schema."""

    def test_robot_config_defaults(self):
        """RobotConfig has correct defaults."""
        from casare_rpa.config.schema import RobotConfig

        config = RobotConfig()

        assert config.id is None
        assert config.name is None
        assert config.environment == "production"
        assert config.max_concurrent_jobs == 1
        assert config.heartbeat_interval == 30
        assert config.capabilities == []
        assert config.tags == []
        assert config.reconnect_delay == 1.0
        assert config.max_reconnect_delay == 60.0
        assert config.job_timeout == 3600.0

    def test_robot_config_max_concurrent_jobs_minimum(self):
        """RobotConfig validates max_concurrent_jobs minimum (1)."""
        from casare_rpa.config.schema import RobotConfig

        RobotConfig(max_concurrent_jobs=1)  # Valid

        with pytest.raises(ValidationError):
            RobotConfig(max_concurrent_jobs=0)

    def test_robot_config_with_capabilities(self):
        """RobotConfig accepts capabilities list."""
        from casare_rpa.config.schema import RobotConfig

        config = RobotConfig(
            capabilities=["browser", "desktop", "ocr"], tags=["windows", "fast"]
        )

        assert config.capabilities == ["browser", "desktop", "ocr"]
        assert config.tags == ["windows", "fast"]


class TestLoggingConfig:
    """Tests for LoggingConfig schema."""

    def test_logging_config_defaults(self):
        """LoggingConfig has correct defaults."""
        from casare_rpa.config.schema import LoggingConfig

        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.file is None
        assert config.rotation_size_mb == 10
        assert config.retention_days == 7

    def test_logging_config_valid_levels(self):
        """LoggingConfig accepts valid log levels."""
        from casare_rpa.config.schema import LoggingConfig

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level

        # Lowercase should be normalized to uppercase
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"

    def test_logging_config_invalid_level(self):
        """LoggingConfig rejects invalid log levels."""
        from casare_rpa.config.schema import LoggingConfig

        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(level="TRACE")

        assert "Invalid log level" in str(exc_info.value)


class TestQueueConfig:
    """Tests for QueueConfig schema."""

    def test_queue_config_defaults(self):
        """QueueConfig has correct defaults."""
        from casare_rpa.config.schema import QueueConfig

        config = QueueConfig()

        assert config.url is None
        assert config.use_memory_queue is False
        assert config.poll_interval == 1.0
        assert config.job_timeout_default == 3600

    def test_queue_config_poll_interval_minimum(self):
        """QueueConfig validates poll_interval minimum (0.1)."""
        from casare_rpa.config.schema import QueueConfig

        QueueConfig(poll_interval=0.1)  # Valid

        with pytest.raises(ValidationError):
            QueueConfig(poll_interval=0.05)


class TestTimeoutConfig:
    """Tests for TimeoutConfig schema."""

    def test_timeout_config_defaults(self):
        """TimeoutConfig has correct defaults."""
        from casare_rpa.config.schema import TimeoutConfig

        config = TimeoutConfig()

        assert config.robot_heartbeat == 90
        assert config.ws_ping_interval == 30
        assert config.ws_send_timeout == 1.0

    def test_timeout_config_robot_heartbeat_minimum(self):
        """TimeoutConfig validates robot_heartbeat minimum (10)."""
        from casare_rpa.config.schema import TimeoutConfig

        TimeoutConfig(robot_heartbeat=10)  # Valid

        with pytest.raises(ValidationError):
            TimeoutConfig(robot_heartbeat=9)


class TestRateLimitConfig:
    """Tests for RateLimitConfig schema."""

    def test_rate_limit_config_defaults(self):
        """RateLimitConfig has correct defaults."""
        from casare_rpa.config.schema import RateLimitConfig

        config = RateLimitConfig()

        assert config.enabled is True
        assert config.requests_per_minute == 100

    def test_rate_limit_config_requests_minimum(self):
        """RateLimitConfig validates requests_per_minute minimum (1)."""
        from casare_rpa.config.schema import RateLimitConfig

        RateLimitConfig(requests_per_minute=1)  # Valid

        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_minute=0)


class TestMetricsConfig:
    """Tests for MetricsConfig schema."""

    def test_metrics_config_defaults(self):
        """MetricsConfig has correct defaults."""
        from casare_rpa.config.schema import MetricsConfig

        config = MetricsConfig()

        assert config.enabled is True
        assert config.collection_interval == 5
        assert config.event_history_size == 1000

    def test_metrics_config_event_history_minimum(self):
        """MetricsConfig validates event_history_size minimum (100)."""
        from casare_rpa.config.schema import MetricsConfig

        MetricsConfig(event_history_size=100)  # Valid

        with pytest.raises(ValidationError):
            MetricsConfig(event_history_size=99)


class TestVaultConfig:
    """Tests for VaultConfig schema."""

    def test_vault_config_defaults(self):
        """VaultConfig has correct defaults."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig()

        assert config.addr is None
        assert config.token is None
        assert config.role_id is None
        assert config.secret_id is None

    def test_vault_config_is_configured_false(self):
        """is_configured returns False when not configured."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig()
        assert config.is_configured is False

        config2 = VaultConfig(addr="http://vault:8200")
        assert config2.is_configured is False  # Missing auth

    def test_vault_config_is_configured_with_token(self):
        """is_configured returns True with addr + token."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig(addr="http://vault:8200", token="s.token123")
        assert config.is_configured is True

    def test_vault_config_is_configured_with_approle(self):
        """is_configured returns True with addr + role_id + secret_id."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig(
            addr="http://vault:8200", role_id="role123", secret_id="secret456"
        )
        assert config.is_configured is True

    def test_vault_config_auth_method_token(self):
        """auth_method returns 'token' when token configured."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig(addr="http://vault:8200", token="s.token123")
        assert config.auth_method == "token"

    def test_vault_config_auth_method_approle(self):
        """auth_method returns 'approle' when approle configured."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig(
            addr="http://vault:8200", role_id="role123", secret_id="secret456"
        )
        assert config.auth_method == "approle"

    def test_vault_config_auth_method_none(self):
        """auth_method returns None when not configured."""
        from casare_rpa.config.schema import VaultConfig

        config = VaultConfig()
        assert config.auth_method is None

        config2 = VaultConfig(addr="http://vault:8200")
        assert config2.auth_method is None


class TestStorageConfig:
    """Tests for StorageConfig schema."""

    def test_storage_config_defaults(self):
        """StorageConfig has correct defaults."""
        from casare_rpa.config.schema import StorageConfig

        config = StorageConfig()

        assert config.workflows_dir == Path("./workflows")
        assert config.backup_enabled is True


class TestCloudflareConfig:
    """Tests for CloudflareConfig schema."""

    def test_cloudflare_config_defaults(self):
        """CloudflareConfig has correct defaults (all None)."""
        from casare_rpa.config.schema import CloudflareConfig

        config = CloudflareConfig()

        assert config.api_url is None
        assert config.webhook_url is None
        assert config.robot_ws_url is None


class TestConfig:
    """Tests for root Config schema."""

    def test_config_defaults(self):
        """Config has correct defaults for all sections."""
        from casare_rpa.config.schema import Config

        config = Config()

        # Check all subsections exist with defaults
        assert config.database is not None
        assert config.supabase is not None
        assert config.security is not None
        assert config.orchestrator is not None
        assert config.robot is not None
        assert config.logging is not None
        assert config.queue is not None
        assert config.timeouts is not None
        assert config.rate_limit is not None
        assert config.metrics is not None
        assert config.vault is not None
        assert config.storage is not None
        assert config.cloudflare is not None

        assert config.debug is False
        assert config.reload is False
        assert config.tenant_id is None

    def test_config_get_summary(self):
        """Config.get_summary returns dict with masked secrets."""
        from casare_rpa.config.schema import Config

        config = Config()
        summary = config.get_summary(mask_secrets=True)

        assert isinstance(summary, dict)
        assert "database" in summary
        assert "supabase" in summary
        assert "orchestrator" in summary
        assert "robot" in summary
        assert "security" in summary
        assert "logging" in summary
        assert "debug" in summary

    def test_config_ignores_extra_fields(self):
        """Config ignores unknown fields (extra='ignore')."""
        from casare_rpa.config.schema import Config

        # Should not raise, just ignore unknown field
        config = Config(unknown_field="value")
        assert not hasattr(config, "unknown_field")

    def test_config_nested_validation(self):
        """Config validates nested sections."""
        from casare_rpa.config.schema import Config, DatabaseConfig

        # Should fail because nested DatabaseConfig has invalid port
        with pytest.raises(ValidationError):
            Config(database=DatabaseConfig(port=0))
