"""
Tests for config startup module.

Tests startup validation procedures:
- validate_orchestrator_config
- validate_robot_config
- validate_canvas_config
- print_config_summary
- check_required_env_vars
"""

import os
import pytest
from io import StringIO
from unittest.mock import patch, Mock


class TestValidateOrchestratorConfig:
    """Tests for validate_orchestrator_config function."""

    def test_validate_orchestrator_config_success(self, clean_env, reset_config_cache):
        """validate_orchestrator_config succeeds with valid config."""
        os.environ["DB_PASSWORD"] = "test_password"

        from casare_rpa.config.startup import validate_orchestrator_config

        config = validate_orchestrator_config()
        assert config is not None

    def test_validate_orchestrator_config_requires_database(
        self, clean_env, reset_config_cache
    ):
        """validate_orchestrator_config requires database config."""
        from casare_rpa.config.startup import validate_orchestrator_config
        from casare_rpa.config.loader import ConfigurationError

        with pytest.raises(ConfigurationError):
            validate_orchestrator_config()

    def test_validate_orchestrator_config_warns_no_api_secret(
        self, clean_env, reset_config_cache, caplog
    ):
        """validate_orchestrator_config warns when API_SECRET not set."""
        os.environ["DB_PASSWORD"] = "test_password"
        # DEBUG=false (not debug mode, so warning should appear)

        from casare_rpa.config.startup import validate_orchestrator_config
        import logging

        with caplog.at_level(logging.WARNING):
            config = validate_orchestrator_config()

        # Check warning was logged
        assert any("API_SECRET not set" in rec.message for rec in caplog.records)

    def test_validate_orchestrator_config_no_warn_in_debug(
        self, clean_env, reset_config_cache, caplog
    ):
        """validate_orchestrator_config skips API_SECRET warning in debug mode."""
        os.environ["DB_PASSWORD"] = "test_password"
        os.environ["DEBUG"] = "true"

        from casare_rpa.config.startup import validate_orchestrator_config
        import logging

        with caplog.at_level(logging.WARNING):
            config = validate_orchestrator_config()

        # Check warning was NOT logged (debug mode skips it)
        api_secret_warnings = [
            rec for rec in caplog.records if "API_SECRET not set" in rec.message
        ]
        assert len(api_secret_warnings) == 0

    def test_validate_orchestrator_config_warns_cors_wildcard(
        self, clean_env, reset_config_cache, caplog
    ):
        """validate_orchestrator_config warns when CORS_ORIGINS has wildcard."""
        os.environ["DB_PASSWORD"] = "test_password"
        os.environ["API_SECRET"] = "secret"  # Avoid the other warning
        os.environ["CORS_ORIGINS"] = "*"

        from casare_rpa.config.startup import validate_orchestrator_config
        import logging

        with caplog.at_level(logging.WARNING):
            config = validate_orchestrator_config()

        assert any("CORS_ORIGINS includes '*'" in rec.message for rec in caplog.records)


class TestValidateRobotConfig:
    """Tests for validate_robot_config function."""

    def test_validate_robot_config_success(self, clean_env, reset_config_cache):
        """validate_robot_config succeeds with valid config."""
        os.environ["DB_PASSWORD"] = "test_password"

        from casare_rpa.config.startup import validate_robot_config

        config = validate_robot_config()
        assert config is not None

    def test_validate_robot_config_requires_database(
        self, clean_env, reset_config_cache
    ):
        """validate_robot_config requires database config."""
        from casare_rpa.config.startup import validate_robot_config
        from casare_rpa.config.loader import ConfigurationError

        with pytest.raises(ConfigurationError):
            validate_robot_config()

    def test_validate_robot_config_warns_memory_queue(
        self, clean_env, reset_config_cache, caplog
    ):
        """validate_robot_config warns when using memory queue."""
        os.environ["DB_PASSWORD"] = "test_password"
        os.environ["USE_MEMORY_QUEUE"] = "true"

        from casare_rpa.config.startup import validate_robot_config
        import logging

        with caplog.at_level(logging.WARNING):
            config = validate_robot_config()

        assert any("USE_MEMORY_QUEUE=true" in rec.message for rec in caplog.records)


class TestValidateCanvasConfig:
    """Tests for validate_canvas_config function."""

    def test_validate_canvas_config_success(self, clean_env, reset_config_cache):
        """validate_canvas_config succeeds (minimal requirements)."""
        from casare_rpa.config.startup import validate_canvas_config

        config = validate_canvas_config()
        assert config is not None

    def test_validate_canvas_config_logs_supabase_mode(
        self, clean_env, reset_config_cache, caplog
    ):
        """validate_canvas_config logs Supabase mode when configured."""
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_KEY"] = "test-key"

        from casare_rpa.config.startup import validate_canvas_config
        import logging

        with caplog.at_level(logging.INFO):
            config = validate_canvas_config()

        assert any(
            "Supabase cloud sync enabled" in rec.message for rec in caplog.records
        )

    def test_validate_canvas_config_logs_local_mode(
        self, clean_env, reset_config_cache, caplog
    ):
        """validate_canvas_config logs local mode when Supabase not configured."""
        from casare_rpa.config.startup import validate_canvas_config
        import logging

        with caplog.at_level(logging.INFO):
            config = validate_canvas_config()

        assert any("local-only mode" in rec.message for rec in caplog.records)


class TestPrintConfigSummary:
    """Tests for print_config_summary function."""

    def test_print_config_summary_outputs_to_stdout(
        self, clean_env, reset_config_cache, capsys
    ):
        """print_config_summary outputs config summary to stdout."""
        from casare_rpa.config.startup import print_config_summary

        print_config_summary()

        captured = capsys.readouterr()
        assert "CasareRPA Configuration Summary" in captured.out
        assert "database" in captured.out.lower()
        assert "orchestrator" in captured.out.lower()

    def test_print_config_summary_with_provided_config(
        self, clean_env, reset_config_cache, capsys
    ):
        """print_config_summary accepts config argument."""
        from casare_rpa.config.startup import print_config_summary
        from casare_rpa.config.schema import Config

        config = Config(debug=True)
        print_config_summary(config)

        captured = capsys.readouterr()
        assert "CasareRPA Configuration Summary" in captured.out


class TestCheckRequiredEnvVars:
    """Tests for check_required_env_vars function."""

    def test_check_required_env_vars_all_present(self, clean_env, reset_config_cache):
        """check_required_env_vars returns True when all present."""
        os.environ["REQUIRED_VAR_1"] = "value1"
        os.environ["REQUIRED_VAR_2"] = "value2"

        from casare_rpa.config.startup import check_required_env_vars

        result = check_required_env_vars(["REQUIRED_VAR_1", "REQUIRED_VAR_2"])
        assert result is True

    def test_check_required_env_vars_missing_raises(
        self, clean_env, reset_config_cache
    ):
        """check_required_env_vars raises when required var missing."""
        os.environ["REQUIRED_VAR_1"] = "value1"
        # REQUIRED_VAR_2 not set

        from casare_rpa.config.startup import check_required_env_vars
        from casare_rpa.config.loader import ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            check_required_env_vars(["REQUIRED_VAR_1", "REQUIRED_VAR_2"])

        assert "REQUIRED_VAR_2" in str(exc_info.value)

    def test_check_required_env_vars_warns_optional(
        self, clean_env, reset_config_cache, caplog
    ):
        """check_required_env_vars warns about missing optional vars."""
        os.environ["REQUIRED_VAR"] = "value"
        # OPTIONAL_VAR not set

        from casare_rpa.config.startup import check_required_env_vars
        import logging

        with caplog.at_level(logging.WARNING):
            result = check_required_env_vars(
                required=["REQUIRED_VAR"], optional_warnings=["OPTIONAL_VAR"]
            )

        assert result is True
        assert any("OPTIONAL_VAR not set" in rec.message for rec in caplog.records)

    def test_check_required_env_vars_empty_list(self, clean_env, reset_config_cache):
        """check_required_env_vars succeeds with empty required list."""
        from casare_rpa.config.startup import check_required_env_vars

        result = check_required_env_vars([])
        assert result is True

    def test_check_required_env_vars_multiple_missing(
        self, clean_env, reset_config_cache
    ):
        """check_required_env_vars reports all missing vars."""
        from casare_rpa.config.startup import check_required_env_vars
        from casare_rpa.config.loader import ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            check_required_env_vars(["MISSING_1", "MISSING_2", "MISSING_3"])

        error = exc_info.value
        assert "MISSING_1" in error.missing_fields
        assert "MISSING_2" in error.missing_fields
        assert "MISSING_3" in error.missing_fields


class TestStartupIntegration:
    """Integration tests for startup procedures."""

    def test_startup_flow_orchestrator(self, clean_env, reset_config_cache):
        """Test typical orchestrator startup flow."""
        os.environ["DB_HOST"] = "localhost"
        os.environ["DB_PASSWORD"] = "password"
        os.environ["API_SECRET"] = "secret"

        from casare_rpa.config.startup import validate_orchestrator_config

        config = validate_orchestrator_config()

        assert config.database.host == "localhost"
        assert config.security.api_secret == "secret"

    def test_startup_flow_robot(self, clean_env, reset_config_cache):
        """Test typical robot startup flow."""
        os.environ["DB_PASSWORD"] = "password"
        os.environ["ROBOT_NAME"] = "Test Robot"
        os.environ["ROBOT_ENVIRONMENT"] = "staging"

        from casare_rpa.config.startup import validate_robot_config

        config = validate_robot_config()

        assert config.robot.name == "Test Robot"
        assert config.robot.environment == "staging"

    def test_startup_flow_canvas(self, clean_env, reset_config_cache):
        """Test typical canvas startup flow."""
        from casare_rpa.config.startup import validate_canvas_config

        config = validate_canvas_config()

        # Canvas has minimal requirements
        assert config is not None
        assert config.storage is not None
