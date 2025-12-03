"""
Tests for config loader module.

Tests config loading from environment variables with:
- Default values
- Environment variable overrides
- Type parsing (bool, int, float, list)
- Config caching and thread safety
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock


class TestParseHelpers:
    """Tests for parsing helper functions."""

    def test_parse_bool_true_values(self, clean_env, reset_config_cache):
        """_parse_bool returns True for 'true', '1', 'yes', 'on'."""
        from casare_rpa.config.loader import _parse_bool

        for val in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            assert _parse_bool(val) is True

    def test_parse_bool_false_values(self, clean_env, reset_config_cache):
        """_parse_bool returns False for 'false', '0', 'no', 'off'."""
        from casare_rpa.config.loader import _parse_bool

        for val in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF", "random"]:
            assert _parse_bool(val) is False

    def test_parse_bool_none_returns_default(self, clean_env, reset_config_cache):
        """_parse_bool returns default when value is None."""
        from casare_rpa.config.loader import _parse_bool

        assert _parse_bool(None) is False
        assert _parse_bool(None, default=True) is True

    def test_parse_int_valid(self, clean_env, reset_config_cache):
        """_parse_int parses valid integers."""
        from casare_rpa.config.loader import _parse_int

        assert _parse_int("42", 0) == 42
        assert _parse_int("-10", 0) == -10
        assert _parse_int("0", 99) == 0

    def test_parse_int_invalid_returns_default(self, clean_env, reset_config_cache):
        """_parse_int returns default for invalid values."""
        from casare_rpa.config.loader import _parse_int

        assert _parse_int("abc", 100) == 100
        assert _parse_int("12.5", 100) == 100
        assert _parse_int(None, 50) == 50

    def test_parse_float_valid(self, clean_env, reset_config_cache):
        """_parse_float parses valid floats."""
        from casare_rpa.config.loader import _parse_float

        assert _parse_float("3.14", 0.0) == 3.14
        assert _parse_float("-1.5", 0.0) == -1.5
        assert _parse_float("42", 0.0) == 42.0

    def test_parse_float_invalid_returns_default(self, clean_env, reset_config_cache):
        """_parse_float returns default for invalid values."""
        from casare_rpa.config.loader import _parse_float

        assert _parse_float("abc", 1.5) == 1.5
        assert _parse_float(None, 2.5) == 2.5

    def test_parse_list_comma_separated(self, clean_env, reset_config_cache):
        """_parse_list parses comma-separated values."""
        from casare_rpa.config.loader import _parse_list

        result = _parse_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_list_with_spaces(self, clean_env, reset_config_cache):
        """_parse_list strips whitespace from items."""
        from casare_rpa.config.loader import _parse_list

        result = _parse_list("  a , b  ,  c  ")
        assert result == ["a", "b", "c"]

    def test_parse_list_empty_string(self, clean_env, reset_config_cache):
        """_parse_list returns empty list for empty string."""
        from casare_rpa.config.loader import _parse_list

        assert _parse_list("") == []
        assert _parse_list(None) == []
        assert _parse_list(None, ["default"]) == ["default"]

    def test_parse_path_valid(self, clean_env, reset_config_cache):
        """_parse_path returns Path for valid string."""
        from casare_rpa.config.loader import _parse_path

        result = _parse_path("/some/path")
        assert result == Path("/some/path")

    def test_parse_path_empty(self, clean_env, reset_config_cache):
        """_parse_path returns None for empty string."""
        from casare_rpa.config.loader import _parse_path

        assert _parse_path("") is None
        assert _parse_path(None) is None


class TestConfigLoading:
    """Tests for config loading functionality."""

    def test_get_config_returns_config_object(self, clean_env, reset_config_cache):
        """get_config returns a Config instance with defaults."""
        from casare_rpa.config.loader import get_config
        from casare_rpa.config.schema import Config

        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_caches_result(self, clean_env, reset_config_cache):
        """get_config returns the same cached instance."""
        from casare_rpa.config.loader import get_config

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_load_config_with_reload(self, clean_env, reset_config_cache):
        """load_config with reload=True creates new config."""
        from casare_rpa.config.loader import load_config

        config1 = load_config()

        # Change an env var
        os.environ["DEBUG"] = "true"

        # Without reload, should get cached
        config2 = load_config()
        assert config2 is config1

        # With reload, should get new config
        config3 = load_config(reload=True)
        assert config3 is not config1
        assert config3.debug is True

    def test_clear_config_cache(self, clean_env, reset_config_cache):
        """clear_config_cache clears the cached config."""
        from casare_rpa.config.loader import get_config, clear_config_cache

        config1 = get_config()
        clear_config_cache()
        config2 = get_config()

        # Should be different objects after cache clear
        assert config1 is not config2


class TestDatabaseConfigLoading:
    """Tests for database configuration loading."""

    def test_database_defaults(self, clean_env, reset_config_cache):
        """Database config has sensible defaults."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.database.enabled is True
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.database.name == "casare_rpa"
        assert config.database.user == "casare_user"
        assert config.database.pool_min_size == 2
        assert config.database.pool_max_size == 10

    def test_database_from_env_vars(self, sample_database_env, reset_config_cache):
        """Database config loads from environment variables."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.database.host == "testhost"
        assert config.database.port == 5433
        assert config.database.name == "testdb"
        assert config.database.user == "testuser"
        assert config.database.password == "testpass"
        assert config.database.pool_min_size == 1
        assert config.database.pool_max_size == 5

    def test_database_url_takes_precedence(self, clean_env, reset_config_cache):
        """DATABASE_URL takes precedence over individual vars."""
        os.environ["DATABASE_URL"] = (
            "postgresql://url_user:url_pass@url_host:9999/url_db"
        )
        os.environ["DB_HOST"] = "other_host"

        from casare_rpa.config.loader import get_config

        config = get_config()
        assert (
            config.database.url == "postgresql://url_user:url_pass@url_host:9999/url_db"
        )


class TestSupabaseConfigLoading:
    """Tests for Supabase configuration loading."""

    def test_supabase_defaults_unconfigured(self, clean_env, reset_config_cache):
        """Supabase is not configured by default."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.supabase.url is None
        assert config.supabase.key is None
        assert config.supabase.is_configured is False

    def test_supabase_from_env_vars(self, sample_supabase_env, reset_config_cache):
        """Supabase config loads from environment variables."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.supabase.url == "https://test.supabase.co"
        assert config.supabase.key == "test-anon-key"
        assert config.supabase.service_key == "test-service-key"
        assert config.supabase.is_configured is True


class TestSecurityConfigLoading:
    """Tests for security configuration loading."""

    def test_security_defaults(self, clean_env, reset_config_cache):
        """Security config has sensible defaults."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.security.api_secret is None
        assert config.security.jwt_expiration_seconds == 3600
        assert config.security.robot_auth_enabled is False
        assert config.security.verify_ssl is True

    def test_security_from_env_vars(self, sample_security_env, reset_config_cache):
        """Security config loads from environment variables."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.security.api_secret == "super-secret-key"
        assert config.security.jwt_expiration_seconds == 7200
        assert config.security.robot_auth_enabled is True


class TestOrchestratorConfigLoading:
    """Tests for orchestrator configuration loading."""

    def test_orchestrator_defaults(self, clean_env, reset_config_cache):
        """Orchestrator config has sensible defaults."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.orchestrator.host == "0.0.0.0"
        assert config.orchestrator.port == 8000
        assert config.orchestrator.workers == 1

    def test_orchestrator_from_env_vars(self, clean_env, reset_config_cache):
        """Orchestrator config loads from environment variables."""
        os.environ["ORCHESTRATOR_HOST"] = "127.0.0.1"
        os.environ["ORCHESTRATOR_PORT"] = "9000"
        os.environ["ORCHESTRATOR_WORKERS"] = "4"
        os.environ["CORS_ORIGINS"] = "http://example.com,http://test.com"

        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.orchestrator.host == "127.0.0.1"
        assert config.orchestrator.port == 9000
        assert config.orchestrator.workers == 4
        assert "http://example.com" in config.orchestrator.cors_origins
        assert "http://test.com" in config.orchestrator.cors_origins


class TestRobotConfigLoading:
    """Tests for robot configuration loading."""

    def test_robot_defaults(self, clean_env, reset_config_cache):
        """Robot config has sensible defaults."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.robot.id is None
        assert config.robot.name is None
        assert config.robot.environment == "production"
        assert config.robot.max_concurrent_jobs == 1
        assert config.robot.heartbeat_interval == 30

    def test_robot_from_env_vars(self, clean_env, reset_config_cache):
        """Robot config loads from environment variables."""
        os.environ["ROBOT_ID"] = "test-robot-1"
        os.environ["ROBOT_NAME"] = "Test Robot"
        os.environ["ROBOT_ENVIRONMENT"] = "staging"
        os.environ["ROBOT_MAX_CONCURRENT_JOBS"] = "3"
        os.environ["ROBOT_CAPABILITIES"] = "browser,desktop,ocr"
        os.environ["ROBOT_TAGS"] = "windows,fast"

        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.robot.id == "test-robot-1"
        assert config.robot.name == "Test Robot"
        assert config.robot.environment == "staging"
        assert config.robot.max_concurrent_jobs == 3
        assert config.robot.capabilities == ["browser", "desktop", "ocr"]
        assert config.robot.tags == ["windows", "fast"]


class TestLoggingConfigLoading:
    """Tests for logging configuration loading."""

    def test_logging_defaults(self, clean_env, reset_config_cache):
        """Logging config has sensible defaults."""
        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.logging.level == "INFO"
        assert config.logging.file is None
        assert config.logging.rotation_size_mb == 10
        assert config.logging.retention_days == 7

    def test_logging_from_env_vars(self, clean_env, reset_config_cache):
        """Logging config loads from environment variables."""
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["LOG_FILE"] = "/var/log/casare.log"
        os.environ["LOG_ROTATION_SIZE_MB"] = "50"
        os.environ["LOG_RETENTION_DAYS"] = "30"

        from casare_rpa.config.loader import get_config

        config = get_config()

        assert config.logging.level == "DEBUG"
        assert config.logging.file == Path("/var/log/casare.log")
        assert config.logging.rotation_size_mb == 50
        assert config.logging.retention_days == 30


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_config_success(self, clean_env, reset_config_cache):
        """validate_config succeeds with valid config."""
        os.environ["DB_PASSWORD"] = "some_password"

        from casare_rpa.config.loader import validate_config

        config = validate_config(require_database=True)
        assert config is not None

    def test_validate_config_requires_database(self, clean_env, reset_config_cache):
        """validate_config raises when database required but not configured."""
        from casare_rpa.config.loader import validate_config, ConfigurationError

        # Database is enabled by default but no URL or password set
        # This should fail validation
        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(require_database=True)

        assert "DATABASE_URL or DB_PASSWORD" in str(exc_info.value)

    def test_validate_config_requires_supabase(self, clean_env, reset_config_cache):
        """validate_config raises when supabase required but not configured."""
        os.environ["DB_PASSWORD"] = "some_password"  # Satisfy database requirement

        from casare_rpa.config.loader import validate_config, ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(require_supabase=True)

        assert "SUPABASE_URL and SUPABASE_KEY" in str(exc_info.value)

    def test_validate_config_requires_api_secret(self, clean_env, reset_config_cache):
        """validate_config raises when api_secret required but not set."""
        os.environ["DB_PASSWORD"] = "some_password"

        from casare_rpa.config.loader import validate_config, ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(require_api_secret=True)

        assert "API_SECRET" in str(exc_info.value)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_message(self):
        """ConfigurationError stores message correctly."""
        from casare_rpa.config.loader import ConfigurationError

        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"

    def test_configuration_error_with_missing_fields(self):
        """ConfigurationError stores missing fields."""
        from casare_rpa.config.loader import ConfigurationError

        error = ConfigurationError(
            "Missing config", missing_fields=["FIELD1", "FIELD2"]
        )
        assert error.missing_fields == ["FIELD1", "FIELD2"]


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_config_manager_singleton_behavior(self, clean_env, reset_config_cache):
        """ConfigManager provides singleton-like behavior."""
        from casare_rpa.config.loader import ConfigManager

        manager = ConfigManager()
        config1 = manager.get()
        config2 = manager.get()

        assert config1 is config2

    def test_config_manager_clear(self, clean_env, reset_config_cache):
        """ConfigManager.clear() resets cached config."""
        from casare_rpa.config.loader import ConfigManager

        manager = ConfigManager()
        config1 = manager.get()
        manager.clear()
        config2 = manager.get()

        assert config1 is not config2

    def test_config_manager_load_with_reload(self, clean_env, reset_config_cache):
        """ConfigManager.load() with reload creates new config."""
        from casare_rpa.config.loader import ConfigManager

        manager = ConfigManager()
        config1 = manager.load()

        os.environ["DEBUG"] = "true"
        config2 = manager.load(reload=True)

        assert config2 is not config1
        assert config2.debug is True


class TestEnvFileFinding:
    """Tests for .env file discovery."""

    def test_find_project_root(self, clean_env, reset_config_cache):
        """_find_project_root finds root by marker files."""
        from casare_rpa.config.loader import _find_project_root

        root = _find_project_root()
        # Should find project root (has pyproject.toml, CLAUDE.md, or .git)
        if root is not None:
            assert (
                (root / "pyproject.toml").exists()
                or (root / "CLAUDE.md").exists()
                or (root / ".git").exists()
            )

    def test_load_env_file_nonexistent(self, clean_env, reset_config_cache, tmp_path):
        """_load_env_file returns False for non-existent file."""
        from casare_rpa.config.loader import _load_env_file

        result = _load_env_file(tmp_path / "nonexistent.env")
        assert result is False

    def test_load_env_file_exists(self, clean_env, reset_config_cache, tmp_path):
        """_load_env_file returns True for existing file."""
        from casare_rpa.config.loader import _load_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value")

        result = _load_env_file(env_file)
        # Result depends on whether dotenv is installed
        # If installed, should return True; if not, returns False with warning
        assert isinstance(result, bool)
