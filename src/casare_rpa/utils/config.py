"""
CasareRPA - Configuration Module
Handles application settings, paths, and logging configuration.
"""

import os
import sys
from pathlib import Path
from typing import Final

from loguru import logger

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Detect if running as frozen executable (PyInstaller)
IS_FROZEN: Final[bool] = getattr(sys, "frozen", False)

if IS_FROZEN:
    # When running as executable, use AppData for user-writable directories
    _appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    _localappdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    USER_DATA_DIR: Final[Path] = _appdata / "CasareRPA"

    # CRITICAL: Set Playwright browsers path BEFORE any Playwright imports
    # This tells Playwright to use system-installed browsers instead of looking
    # inside the PyInstaller bundle
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path(_localappdata) / "ms-playwright")

    # Application installation directory (read-only)
    APP_DIR: Final[Path] = Path(sys.executable).parent
    PROJECT_ROOT: Final[Path] = APP_DIR
    SRC_ROOT: Final[Path] = APP_DIR / "_internal" / "casare_rpa"
    DOCS_DIR: Final[Path] = APP_DIR / "_internal" / "docs"

    # User-writable directories in AppData
    LOGS_DIR: Final[Path] = USER_DATA_DIR / "logs"
    WORKFLOWS_DIR: Final[Path] = USER_DATA_DIR / "workflows"
    CONFIG_DIR: Final[Path] = USER_DATA_DIR / "config"
else:
    # Development mode - use project directory
    PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent
    SRC_ROOT: Final[Path] = PROJECT_ROOT / "src"
    LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
    WORKFLOWS_DIR: Final[Path] = PROJECT_ROOT / "workflows"
    DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"
    CONFIG_DIR: Final[Path] = PROJECT_ROOT / "config"

# User settings
SETTINGS_FILE: Final[Path] = CONFIG_DIR / "settings.json"
HOTKEYS_FILE: Final[Path] = CONFIG_DIR / "hotkeys.json"

# Project management paths
PROJECTS_DIR: Final[Path] = CONFIG_DIR / "projects"
PROJECTS_INDEX_FILE: Final[Path] = PROJECTS_DIR / "projects_index.json"
GLOBAL_VARIABLES_FILE: Final[Path] = CONFIG_DIR / "global_variables.json"
GLOBAL_CREDENTIALS_FILE: Final[Path] = CONFIG_DIR / "global_credentials.json"

# Ensure critical directories exist (these are now always writable)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

APP_NAME: Final[str] = "CasareRPA"
APP_VERSION: Final[str] = "0.1.0"
APP_AUTHOR: Final[str] = "CasareRPA Team"
APP_DESCRIPTION: Final[str] = "High-Performance Windows Desktop RPA Platform"

# ============================================================================
# GUI CONFIGURATION
# ============================================================================

# High-DPI Support for Windows
ENABLE_HIGH_DPI: Final[bool] = True

# Window Settings
DEFAULT_WINDOW_WIDTH: Final[int] = 1400
DEFAULT_WINDOW_HEIGHT: Final[int] = 900
MIN_WINDOW_WIDTH: Final[int] = 1024
MIN_WINDOW_HEIGHT: Final[int] = 768

# Aliases for backward compatibility and convenience
GUI_WINDOW_WIDTH: Final[int] = 1280
GUI_WINDOW_HEIGHT: Final[int] = 720
GUI_THEME: Final[str] = "dark"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FILE_PATH: Final[Path] = LOGS_DIR / "casare_rpa_{time:YYYY-MM-DD}.log"
LOG_RETENTION: Final[str] = "30 days"
LOG_ROTATION: Final[str] = "500 MB"
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def setup_logging() -> None:
    """
    Configure loguru logger with file rotation and formatting.
    This should be called once at application startup.
    """
    # Remove default handler
    logger.remove()

    # Add console handler with color (only if stderr is available)
    if sys.stderr:
        logger.add(
            sys.stderr,
            format=LOG_FORMAT,
            level=LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # Add file handler with rotation
    enqueue_logs = (
        os.environ.get("CASARE_RPA_DISABLE_LOGURU_ENQUEUE") not in {"1", "true", "True"}
        and "pytest" not in sys.modules
    )
    logger.add(
        LOG_FILE_PATH,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=enqueue_logs,  # Thread-safe logging (disabled under pytest)
    )

    logger.info(f"{APP_NAME} v{APP_VERSION} - Logging initialized")
    logger.info(f"Log file: {LOG_FILE_PATH}")


# ============================================================================
# RUNNER CONFIGURATION
# ============================================================================

# Execution timeout settings (seconds)
DEFAULT_NODE_TIMEOUT: Final[int] = 30
DEFAULT_PAGE_LOAD_TIMEOUT: Final[int] = 30000  # milliseconds for Playwright

# Error handling
STOP_ON_ERROR: Final[bool] = True  # Default behavior

# ============================================================================
# PLAYWRIGHT CONFIGURATION
# ============================================================================

# Browser settings
DEFAULT_BROWSER: Final[str] = "chromium"  # chromium, firefox, webkit
HEADLESS_MODE: Final[bool] = False  # Show browser by default

# Anti-detection browser arguments
# These flags help make automated Chrome look like a regular user's browser
BROWSER_ARGS: Final[list[str]] = [
    "--start-maximized",
    # Core anti-detection flags
    "--disable-blink-features=AutomationControlled",  # Hides automation markers
    "--disable-infobars",  # Removes "Chrome is being controlled" infobar
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
    # Additional anti-detection flags
    "--disable-extensions",  # Websites can detect extensions
    "--disable-popup-blocking",
    "--disable-translate",
    "--disable-sync",
    "--no-first-run",
    "--no-default-browser-check",
    "--password-store=basic",  # Avoid keyring prompts
    "--use-mock-keychain",
    # Disable automation-related features
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

# Playwright default args to ignore (these reveal automation)
PLAYWRIGHT_IGNORE_ARGS: Final[list[str]] = [
    "--enable-automation",  # This causes "Chrome is being controlled" message
    "--enable-blink-features=IdleDetection",
]

# ============================================================================
# NODE GRAPH CONFIGURATION
# ============================================================================

# Visual settings for node editor
NODE_GRID_SIZE: Final[int] = 20
NODE_SNAP_TO_GRID: Final[bool] = True

# ============================================================================
# SCHEMA VERSION
# ============================================================================

WORKFLOW_SCHEMA_VERSION: Final[str] = "1.0.0"
