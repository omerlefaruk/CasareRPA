"""
Tests for utils/config.py - Application configuration module.
"""

import pytest
from pathlib import Path


class TestConfigConstants:
    """Test configuration constants and paths."""

    def test_project_paths_exist(self):
        """Test that project path constants are defined and are Path objects."""
        from casare_rpa.utils.config import (
            PROJECT_ROOT, SRC_ROOT, LOGS_DIR,
            WORKFLOWS_DIR, DOCS_DIR, CONFIG_DIR
        )

        assert isinstance(PROJECT_ROOT, Path)
        assert isinstance(SRC_ROOT, Path)
        assert isinstance(LOGS_DIR, Path)
        assert isinstance(WORKFLOWS_DIR, Path)
        assert isinstance(DOCS_DIR, Path)
        assert isinstance(CONFIG_DIR, Path)

    def test_critical_directories_created(self):
        """Test that critical directories are created on import."""
        from casare_rpa.utils.config import LOGS_DIR, WORKFLOWS_DIR, CONFIG_DIR

        # These directories should exist after importing config
        assert LOGS_DIR.exists()
        assert WORKFLOWS_DIR.exists()
        assert CONFIG_DIR.exists()

    def test_settings_file_paths(self):
        """Test settings file path constants."""
        from casare_rpa.utils.config import SETTINGS_FILE, HOTKEYS_FILE, CONFIG_DIR

        assert SETTINGS_FILE == CONFIG_DIR / "settings.json"
        assert HOTKEYS_FILE == CONFIG_DIR / "hotkeys.json"

    def test_app_metadata(self):
        """Test application metadata constants."""
        from casare_rpa.utils.config import (
            APP_NAME, APP_VERSION, APP_AUTHOR, APP_DESCRIPTION
        )

        assert APP_NAME == "CasareRPA"
        assert isinstance(APP_VERSION, str)
        assert len(APP_VERSION.split('.')) == 3  # Should be semantic version
        assert isinstance(APP_AUTHOR, str)
        assert isinstance(APP_DESCRIPTION, str)


class TestGUIConfiguration:
    """Test GUI-related configuration."""

    def test_high_dpi_setting(self):
        """Test High DPI support setting."""
        from casare_rpa.utils.config import ENABLE_HIGH_DPI

        assert isinstance(ENABLE_HIGH_DPI, bool)

    def test_window_dimensions(self):
        """Test window dimension constants."""
        from casare_rpa.utils.config import (
            DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
            MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
            GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT
        )

        # Default dimensions should be reasonable
        assert DEFAULT_WINDOW_WIDTH >= MIN_WINDOW_WIDTH
        assert DEFAULT_WINDOW_HEIGHT >= MIN_WINDOW_HEIGHT

        # All should be positive integers
        assert DEFAULT_WINDOW_WIDTH > 0
        assert DEFAULT_WINDOW_HEIGHT > 0
        assert MIN_WINDOW_WIDTH > 0
        assert MIN_WINDOW_HEIGHT > 0
        assert GUI_WINDOW_WIDTH > 0
        assert GUI_WINDOW_HEIGHT > 0

    def test_gui_theme(self):
        """Test GUI theme setting."""
        from casare_rpa.utils.config import GUI_THEME

        assert GUI_THEME in ["dark", "light"]


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_log_constants(self):
        """Test logging configuration constants."""
        from casare_rpa.utils.config import (
            LOG_FILE_PATH, LOG_RETENTION, LOG_ROTATION,
            LOG_LEVEL, LOG_FORMAT
        )

        assert isinstance(LOG_FILE_PATH, Path)
        assert isinstance(LOG_RETENTION, str)
        assert isinstance(LOG_ROTATION, str)
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert isinstance(LOG_FORMAT, str)

    def test_log_file_path_contains_timestamp(self):
        """Test that log file path contains timestamp placeholder."""
        from casare_rpa.utils.config import LOG_FILE_PATH

        # The log file path should contain a time format placeholder
        assert "{time" in str(LOG_FILE_PATH)


class TestRunnerConfiguration:
    """Test runner/execution configuration."""

    def test_timeout_settings(self):
        """Test timeout configuration."""
        from casare_rpa.utils.config import (
            DEFAULT_NODE_TIMEOUT, DEFAULT_PAGE_LOAD_TIMEOUT
        )

        assert DEFAULT_NODE_TIMEOUT > 0
        assert DEFAULT_PAGE_LOAD_TIMEOUT > 0
        # Page load timeout should be in milliseconds
        assert DEFAULT_PAGE_LOAD_TIMEOUT >= 1000

    def test_error_handling_settings(self):
        """Test error handling configuration."""
        from casare_rpa.utils.config import STOP_ON_ERROR

        assert isinstance(STOP_ON_ERROR, bool)


class TestPlaywrightConfiguration:
    """Test Playwright browser configuration."""

    def test_browser_settings(self):
        """Test browser configuration."""
        from casare_rpa.utils.config import (
            DEFAULT_BROWSER, HEADLESS_MODE, BROWSER_ARGS
        )

        assert DEFAULT_BROWSER in ["chromium", "firefox", "webkit"]
        assert isinstance(HEADLESS_MODE, bool)
        assert isinstance(BROWSER_ARGS, list)

    def test_browser_args_are_strings(self):
        """Test that browser args are all strings."""
        from casare_rpa.utils.config import BROWSER_ARGS

        for arg in BROWSER_ARGS:
            assert isinstance(arg, str)


class TestNodeGraphConfiguration:
    """Test node graph editor configuration."""

    def test_grid_settings(self):
        """Test node graph grid settings."""
        from casare_rpa.utils.config import NODE_GRID_SIZE, NODE_SNAP_TO_GRID

        assert NODE_GRID_SIZE > 0
        assert isinstance(NODE_SNAP_TO_GRID, bool)


class TestSchemaVersion:
    """Test workflow schema version."""

    def test_schema_version_format(self):
        """Test schema version is semantic versioning."""
        from casare_rpa.utils.config import WORKFLOW_SCHEMA_VERSION

        parts = WORKFLOW_SCHEMA_VERSION.split('.')
        assert len(parts) == 3
        # All parts should be numeric
        for part in parts:
            assert part.isdigit()


class TestSetupLogging:
    """Test logging setup function."""

    def test_setup_logging_runs_without_error(self):
        """Test that setup_logging can be called without errors."""
        from casare_rpa.utils.config import setup_logging

        # Should not raise an exception
        setup_logging()

    def test_setup_logging_is_idempotent(self):
        """Test that setup_logging can be called multiple times."""
        from casare_rpa.utils.config import setup_logging

        # Multiple calls should not raise
        setup_logging()
        setup_logging()
