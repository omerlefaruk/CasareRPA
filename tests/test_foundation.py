"""
CasareRPA - Foundation Tests
Tests for Phase 1: Project structure, configuration, and imports.
"""

import sys
from pathlib import Path
import pytest

# Add src directory to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))


class TestProjectStructure:
    """Test that all necessary directories and files exist."""

    def test_project_root_exists(self) -> None:
        """Verify project root directory exists."""
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    def test_source_structure(self) -> None:
        """Verify source directory structure."""
        src_dir = PROJECT_ROOT / "src" / "casare_rpa"
        assert src_dir.exists()
        assert (src_dir / "__init__.py").exists()

    def test_core_package_exists(self) -> None:
        """Verify core package structure."""
        core_dir = PROJECT_ROOT / "src" / "casare_rpa" / "core"
        assert core_dir.exists()
        assert (core_dir / "__init__.py").exists()

    def test_nodes_package_exists(self) -> None:
        """Verify nodes package structure."""
        nodes_dir = PROJECT_ROOT / "src" / "casare_rpa" / "nodes"
        assert nodes_dir.exists()
        assert (nodes_dir / "__init__.py").exists()

    def test_gui_package_exists(self) -> None:
        """Verify GUI package structure."""
        gui_dir = PROJECT_ROOT / "src" / "casare_rpa" / "gui"
        assert gui_dir.exists()
        assert (gui_dir / "__init__.py").exists()

    def test_runner_package_exists(self) -> None:
        """Verify runner package structure."""
        runner_dir = PROJECT_ROOT / "src" / "casare_rpa" / "runner"
        assert runner_dir.exists()
        assert (runner_dir / "__init__.py").exists()

    def test_utils_package_exists(self) -> None:
        """Verify utils package structure."""
        utils_dir = PROJECT_ROOT / "src" / "casare_rpa" / "utils"
        assert utils_dir.exists()
        assert (utils_dir / "__init__.py").exists()
        assert (utils_dir / "config.py").exists()

    def test_workflows_directory_exists(self) -> None:
        """Verify workflows directory exists."""
        workflows_dir = PROJECT_ROOT / "workflows"
        assert workflows_dir.exists()

    def test_logs_directory_exists(self) -> None:
        """Verify logs directory exists."""
        logs_dir = PROJECT_ROOT / "logs"
        assert logs_dir.exists()

    def test_tests_directory_exists(self) -> None:
        """Verify tests directory exists."""
        tests_dir = PROJECT_ROOT / "tests"
        assert tests_dir.exists()

    def test_docs_directory_exists(self) -> None:
        """Verify docs directory exists."""
        docs_dir = PROJECT_ROOT / "docs"
        assert docs_dir.exists()


class TestConfigurationFiles:
    """Test that configuration files exist and are valid."""

    def test_requirements_txt_exists(self) -> None:
        """Verify requirements.txt exists."""
        req_file = PROJECT_ROOT / "requirements.txt"
        assert req_file.exists()
        content = req_file.read_text()
        assert "PySide6" in content
        assert "NodeGraphQt" in content
        assert "playwright" in content
        assert "qasync" in content
        assert "orjson" in content
        assert "loguru" in content

    def test_pyproject_toml_exists(self) -> None:
        """Verify pyproject.toml exists."""
        pyproject_file = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_file.exists()
        content = pyproject_file.read_text()
        assert "casare-rpa" in content
        assert "0.1.0" in content

    def test_readme_exists(self) -> None:
        """Verify README.md exists."""
        readme_file = PROJECT_ROOT / "README.md"
        assert readme_file.exists()
        content = readme_file.read_text(encoding="utf-8")
        assert "CasareRPA" in content


class TestImports:
    """Test that all packages can be imported correctly."""

    def test_import_main_package(self) -> None:
        """Test importing main package."""
        import casare_rpa

        assert hasattr(casare_rpa, "__version__")
        assert casare_rpa.__version__ == "0.1.0"

    def test_import_utils(self) -> None:
        """Test importing utils package."""
        from casare_rpa import utils

        assert hasattr(utils, "APP_NAME")
        assert hasattr(utils, "APP_VERSION")
        assert hasattr(utils, "setup_logging")

    def test_import_config(self) -> None:
        """Test importing configuration module."""
        from casare_rpa.utils import config

        assert hasattr(config, "APP_NAME")
        assert hasattr(config, "APP_VERSION")
        assert hasattr(config, "PROJECT_ROOT")
        assert hasattr(config, "LOGS_DIR")
        assert hasattr(config, "WORKFLOWS_DIR")

    def test_import_core_package(self) -> None:
        """Test importing core package."""
        from casare_rpa import core

        assert hasattr(core, "__version__")

    def test_import_nodes_package(self) -> None:
        """Test importing nodes package."""
        from casare_rpa import nodes

        assert hasattr(nodes, "__version__")

    def test_import_gui_package(self) -> None:
        """Test importing GUI package."""
        from casare_rpa import gui

        assert hasattr(gui, "__version__")

    def test_import_runner_package(self) -> None:
        """Test importing runner package."""
        from casare_rpa import runner

        assert hasattr(runner, "__version__")


class TestConfiguration:
    """Test configuration values and settings."""

    def test_app_constants(self) -> None:
        """Test application constants."""
        from casare_rpa.utils.config import APP_NAME, APP_VERSION, APP_AUTHOR

        assert APP_NAME == "CasareRPA"
        assert APP_VERSION == "0.1.0"
        assert APP_AUTHOR == "CasareRPA Team"

    def test_path_constants(self) -> None:
        """Test path constants."""
        from casare_rpa.utils.config import PROJECT_ROOT, LOGS_DIR, WORKFLOWS_DIR

        assert isinstance(PROJECT_ROOT, Path)
        assert isinstance(LOGS_DIR, Path)
        assert isinstance(WORKFLOWS_DIR, Path)
        assert LOGS_DIR.exists()
        assert WORKFLOWS_DIR.exists()

    def test_logging_config(self) -> None:
        """Test logging configuration."""
        from casare_rpa.utils.config import (
            LOG_LEVEL,
            LOG_RETENTION,
            LOG_ROTATION,
        )

        assert LOG_LEVEL == "INFO"
        assert LOG_RETENTION == "30 days"
        assert LOG_ROTATION == "500 MB"

    def test_gui_config(self) -> None:
        """Test GUI configuration."""
        from casare_rpa.utils.config import (
            DEFAULT_WINDOW_WIDTH,
            DEFAULT_WINDOW_HEIGHT,
            ENABLE_HIGH_DPI,
        )

        assert DEFAULT_WINDOW_WIDTH == 1400
        assert DEFAULT_WINDOW_HEIGHT == 900
        assert ENABLE_HIGH_DPI is True

    def test_playwright_config(self) -> None:
        """Test Playwright configuration."""
        from casare_rpa.utils.config import (
            DEFAULT_BROWSER,
            HEADLESS_MODE,
        )

        assert DEFAULT_BROWSER == "chromium"
        assert HEADLESS_MODE is False


class TestLogging:
    """Test logging functionality."""

    def test_setup_logging(self) -> None:
        """Test that logging can be initialized."""
        from casare_rpa.utils import setup_logging

        # Should not raise any exceptions
        setup_logging()

    def test_logger_import(self) -> None:
        """Test that loguru logger can be imported."""
        from loguru import logger

        assert logger is not None


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
