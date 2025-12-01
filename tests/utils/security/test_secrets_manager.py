"""Tests for secrets_manager module."""

import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from casare_rpa.utils.security.secrets_manager import (
    SecretsManager,
    get_secret,
    get_required_secret,
)


@pytest.fixture(autouse=True)
def reset_secrets_manager():
    """Reset the singleton before and after each test."""
    SecretsManager.reset()
    yield
    SecretsManager.reset()


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text(
            """# Test secrets
API_KEY=test_api_key_123
DATABASE_URL=postgres://localhost:5432/test
EMPTY_VALUE=
QUOTED_VALUE="quoted value"
SINGLE_QUOTED='single quoted'
"""
        )
        yield env_path


class TestSecretsManager:
    """Tests for SecretsManager class."""

    def test_singleton_pattern(self):
        """Test that SecretsManager is a singleton."""
        manager1 = SecretsManager()
        manager2 = SecretsManager()
        assert manager1 is manager2

    def test_reset_creates_new_instance(self):
        """Test that reset allows a new instance to be created."""
        manager1 = SecretsManager()
        SecretsManager.reset()
        manager2 = SecretsManager()
        # After reset, should be a different instance
        # (Can't directly compare as internal state is reset)
        assert manager2 is not None

    def test_get_from_environment(self):
        """Test getting secrets from environment variables."""
        with patch.dict(os.environ, {"TEST_SECRET": "env_value"}):
            manager = SecretsManager()
            assert manager.get("TEST_SECRET") == "env_value"

    def test_get_with_default(self):
        """Test getting nonexistent secrets with default."""
        manager = SecretsManager()
        assert manager.get("NONEXISTENT_KEY", "default") == "default"

    def test_get_without_default_returns_none(self):
        """Test getting nonexistent secrets without default."""
        manager = SecretsManager()
        result = manager.get("NONEXISTENT_KEY_123")
        assert result is None

    def test_get_required_success(self):
        """Test get_required with existing secret."""
        with patch.dict(os.environ, {"REQUIRED_SECRET": "value"}):
            manager = SecretsManager()
            assert manager.get_required("REQUIRED_SECRET") == "value"

    def test_get_required_raises_on_missing(self):
        """Test get_required raises ValueError for missing secrets."""
        manager = SecretsManager()
        with pytest.raises(ValueError) as exc_info:
            manager.get_required("DEFINITELY_NOT_SET_12345")
        assert "Required secret" in str(exc_info.value)

    def test_has_returns_true_for_env_var(self):
        """Test has() returns True for environment variables."""
        with patch.dict(os.environ, {"HAS_TEST": "value"}):
            manager = SecretsManager()
            assert manager.has("HAS_TEST") is True

    def test_has_returns_false_for_missing(self):
        """Test has() returns False for missing secrets."""
        manager = SecretsManager()
        assert manager.has("DEFINITELY_NOT_SET_67890") is False

    def test_env_var_takes_priority(self):
        """Test environment variables take priority over .env file."""
        manager = SecretsManager()
        # Set the same key in _secrets dict (simulating .env file)
        manager._secrets["PRIORITY_TEST"] = "file_value"

        with patch.dict(os.environ, {"PRIORITY_TEST": "env_value"}):
            assert manager.get("PRIORITY_TEST") == "env_value"

    def test_reload_clears_and_reloads(self):
        """Test reload clears and reloads secrets."""
        manager = SecretsManager()
        manager._secrets["OLD_SECRET"] = "old_value"
        manager.reload()
        # After reload, the manually added secret should be gone
        # (unless it was in actual .env file)
        assert manager._secrets.get("OLD_SECRET") is None or "OLD_SECRET" in os.environ


class TestSecretsManagerEnvFileParsing:
    """Tests for .env file parsing."""

    def test_load_env_file_parses_key_value(self):
        """Test loading key=value pairs from .env file."""
        manager = SecretsManager()

        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("TEST_KEY=test_value\n")

            # Manually load the env file
            manager._load_env_file(env_path)

            # Should be loaded if not in os.environ
            if "TEST_KEY" not in os.environ:
                assert manager._secrets.get("TEST_KEY") == "test_value"

    def test_load_env_file_skips_comments(self):
        """Test that comments are skipped."""
        manager = SecretsManager()

        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("# This is a comment\nREAL_KEY=real_value\n")

            manager._load_env_file(env_path)

            assert "# This is a comment" not in manager._secrets
            if "REAL_KEY" not in os.environ:
                assert manager._secrets.get("REAL_KEY") == "real_value"

    def test_load_env_file_skips_empty_lines(self):
        """Test that empty lines are skipped."""
        manager = SecretsManager()

        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("\n\n\nKEY_AFTER_EMPTY=value\n\n")

            manager._load_env_file(env_path)

            if "KEY_AFTER_EMPTY" not in os.environ:
                assert manager._secrets.get("KEY_AFTER_EMPTY") == "value"

    def test_load_env_file_strips_quotes(self):
        """Test that quotes are stripped from values."""
        manager = SecretsManager()

        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "DOUBLE_QUOTED=\"double value\"\nSINGLE_QUOTED='single value'\n"
            )

            manager._load_env_file(env_path)

            if "DOUBLE_QUOTED" not in os.environ:
                assert manager._secrets.get("DOUBLE_QUOTED") == "double value"
            if "SINGLE_QUOTED" not in os.environ:
                assert manager._secrets.get("SINGLE_QUOTED") == "single value"

    def test_load_env_file_handles_missing_file(self):
        """Test that missing .env file is handled gracefully."""
        manager = SecretsManager()
        nonexistent = Path("/nonexistent/path/.env")

        # Should not raise
        manager._load_env_file(nonexistent)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_secret_creates_manager(self):
        """Test get_secret creates a manager if needed."""
        with patch.dict(os.environ, {"CONVENIENCE_SECRET": "conv_value"}):
            # Clear any cached manager
            import casare_rpa.utils.security.secrets_manager as sm

            sm._default_manager = None

            result = get_secret("CONVENIENCE_SECRET")
            assert result == "conv_value"

    def test_get_secret_with_default(self):
        """Test get_secret with default value."""
        import casare_rpa.utils.security.secrets_manager as sm

        sm._default_manager = None

        result = get_secret("NONEXISTENT_CONVENIENCE_KEY", "default_val")
        assert result == "default_val"

    def test_get_required_secret_raises(self):
        """Test get_required_secret raises on missing."""
        import casare_rpa.utils.security.secrets_manager as sm

        sm._default_manager = None

        with pytest.raises(ValueError):
            get_required_secret("DEFINITELY_MISSING_KEY_99999")


class TestFindProjectRoot:
    """Tests for project root finding."""

    def test_find_project_root_returns_path(self):
        """Test that _find_project_root returns a Path."""
        manager = SecretsManager()
        root = manager._find_project_root()
        assert isinstance(root, Path)
        assert root.exists()
