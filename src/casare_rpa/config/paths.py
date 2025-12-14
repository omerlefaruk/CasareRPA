"""
CasareRPA Path Configuration.

Platform-aware path management for development and frozen (PyInstaller) executables.
Handles project roots, user data directories, and logging paths.
"""

import os
import sys
from pathlib import Path
from typing import Final


# Detect if running as frozen executable (PyInstaller)
IS_FROZEN: Final[bool] = getattr(sys, "frozen", False)


def _get_project_root() -> Path:
    """Find project root by looking for marker files."""
    if IS_FROZEN:
        return Path(sys.executable).parent

    current = Path(__file__).parent
    markers = ["pyproject.toml", "CLAUDE.md", ".git"]

    for _ in range(10):
        for marker in markers:
            if (current / marker).exists():
                return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fallback: 3 levels up from config/paths.py
    return Path(__file__).parent.parent.parent.parent


def _setup_paths() -> dict:
    """Initialize all application paths based on environment."""
    paths = {}

    if IS_FROZEN:
        # PyInstaller frozen executable
        _appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        _localappdata = os.environ.get(
            "LOCALAPPDATA", str(Path.home() / "AppData" / "Local")
        )

        # User data directory (writable)
        paths["USER_DATA_DIR"] = _appdata / "CasareRPA"

        # Playwright browsers path
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(
            Path(_localappdata) / "ms-playwright"
        )

        # Application installation directory (read-only)
        paths["APP_DIR"] = Path(sys.executable).parent
        paths["PROJECT_ROOT"] = paths["APP_DIR"]
        paths["SRC_ROOT"] = paths["APP_DIR"] / "_internal" / "casare_rpa"
        paths["DOCS_DIR"] = paths["APP_DIR"] / "_internal" / "docs"

        # User-writable directories in AppData
        paths["LOGS_DIR"] = paths["USER_DATA_DIR"] / "logs"
        paths["WORKFLOWS_DIR"] = paths["USER_DATA_DIR"] / "workflows"
        paths["CONFIG_DIR"] = paths["USER_DATA_DIR"] / "config"
    else:
        # Development mode - use project directory
        paths["PROJECT_ROOT"] = _get_project_root()
        paths["SRC_ROOT"] = paths["PROJECT_ROOT"] / "src"
        paths["LOGS_DIR"] = paths["PROJECT_ROOT"] / "logs"
        paths["WORKFLOWS_DIR"] = paths["PROJECT_ROOT"] / "workflows"
        paths["DOCS_DIR"] = paths["PROJECT_ROOT"] / "docs"
        paths["CONFIG_DIR"] = paths["PROJECT_ROOT"] / "config"

    # Derived paths
    paths["SETTINGS_FILE"] = paths["CONFIG_DIR"] / "settings.json"
    paths["HOTKEYS_FILE"] = paths["CONFIG_DIR"] / "hotkeys.json"
    paths["PROJECTS_DIR"] = paths["CONFIG_DIR"] / "projects"
    paths["PROJECTS_INDEX_FILE"] = paths["PROJECTS_DIR"] / "projects_index.json"
    paths["GLOBAL_VARIABLES_FILE"] = paths["CONFIG_DIR"] / "global_variables.json"
    paths["GLOBAL_CREDENTIALS_FILE"] = paths["CONFIG_DIR"] / "global_credentials.json"

    return paths


# Initialize paths
_PATHS = _setup_paths()

# Export path constants
PROJECT_ROOT: Final[Path] = _PATHS["PROJECT_ROOT"]
SRC_ROOT: Final[Path] = _PATHS.get("SRC_ROOT", PROJECT_ROOT / "src")
LOGS_DIR: Final[Path] = _PATHS["LOGS_DIR"]
WORKFLOWS_DIR: Final[Path] = _PATHS["WORKFLOWS_DIR"]
DOCS_DIR: Final[Path] = _PATHS.get("DOCS_DIR", PROJECT_ROOT / "docs")
CONFIG_DIR: Final[Path] = _PATHS["CONFIG_DIR"]

# User settings paths
SETTINGS_FILE: Final[Path] = _PATHS["SETTINGS_FILE"]
HOTKEYS_FILE: Final[Path] = _PATHS["HOTKEYS_FILE"]
PROJECTS_DIR: Final[Path] = _PATHS["PROJECTS_DIR"]
PROJECTS_INDEX_FILE: Final[Path] = _PATHS["PROJECTS_INDEX_FILE"]
GLOBAL_VARIABLES_FILE: Final[Path] = _PATHS["GLOBAL_VARIABLES_FILE"]
GLOBAL_CREDENTIALS_FILE: Final[Path] = _PATHS["GLOBAL_CREDENTIALS_FILE"]

# User data dir (frozen mode only)
USER_DATA_DIR: Final[Path] = _PATHS.get("USER_DATA_DIR", CONFIG_DIR.parent)


def ensure_directories() -> None:
    """Create critical directories if they don't exist."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


# Ensure directories exist on import
ensure_directories()


# Application constants
APP_NAME: Final[str] = "CasareRPA"
APP_VERSION: Final[str] = "0.1.0"
APP_AUTHOR: Final[str] = "CasareRPA Team"
APP_DESCRIPTION: Final[str] = "High-Performance Windows Desktop RPA Platform"

# GUI configuration
ENABLE_HIGH_DPI: Final[bool] = True
DEFAULT_WINDOW_WIDTH: Final[int] = 1400
DEFAULT_WINDOW_HEIGHT: Final[int] = 900
MIN_WINDOW_WIDTH: Final[int] = 1024
MIN_WINDOW_HEIGHT: Final[int] = 768
GUI_WINDOW_WIDTH: Final[int] = 1280
GUI_WINDOW_HEIGHT: Final[int] = 720
GUI_THEME: Final[str] = "dark"

# Execution timeout settings
DEFAULT_NODE_TIMEOUT: Final[int] = 30
DEFAULT_PAGE_LOAD_TIMEOUT: Final[int] = 30000  # milliseconds for Playwright

# Error handling
STOP_ON_ERROR: Final[bool] = True

# Browser settings
DEFAULT_BROWSER: Final[str] = "chromium"
HEADLESS_MODE: Final[bool] = False
BROWSER_ARGS: Final[list[str]] = [
    "--start-maximized",
    "--disable-blink-features=AutomationControlled",
]

# Node graph settings
NODE_GRID_SIZE: Final[int] = 20
NODE_SNAP_TO_GRID: Final[bool] = True

# Schema version
WORKFLOW_SCHEMA_VERSION: Final[str] = "1.0.0"


__all__ = [
    # Environment detection
    "IS_FROZEN",
    # Paths
    "PROJECT_ROOT",
    "SRC_ROOT",
    "LOGS_DIR",
    "WORKFLOWS_DIR",
    "DOCS_DIR",
    "CONFIG_DIR",
    "SETTINGS_FILE",
    "HOTKEYS_FILE",
    "PROJECTS_DIR",
    "PROJECTS_INDEX_FILE",
    "GLOBAL_VARIABLES_FILE",
    "GLOBAL_CREDENTIALS_FILE",
    "USER_DATA_DIR",
    # Functions
    "ensure_directories",
    # App constants
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    # GUI constants
    "ENABLE_HIGH_DPI",
    "DEFAULT_WINDOW_WIDTH",
    "DEFAULT_WINDOW_HEIGHT",
    "MIN_WINDOW_WIDTH",
    "MIN_WINDOW_HEIGHT",
    "GUI_WINDOW_WIDTH",
    "GUI_WINDOW_HEIGHT",
    "GUI_THEME",
    # Execution settings
    "DEFAULT_NODE_TIMEOUT",
    "DEFAULT_PAGE_LOAD_TIMEOUT",
    "STOP_ON_ERROR",
    # Browser settings
    "DEFAULT_BROWSER",
    "HEADLESS_MODE",
    "BROWSER_ARGS",
    # Node graph settings
    "NODE_GRID_SIZE",
    "NODE_SNAP_TO_GRID",
    # Schema
    "WORKFLOW_SCHEMA_VERSION",
]
