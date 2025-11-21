"""
CasareRPA - Configuration Module
Handles application settings, paths, and logging configuration.
"""

import sys
from pathlib import Path
from typing import Final
from loguru import logger

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Project root directory
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent
SRC_ROOT: Final[Path] = PROJECT_ROOT / "src"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
WORKFLOWS_DIR: Final[Path] = PROJECT_ROOT / "workflows"
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"

# Ensure critical directories exist
LOGS_DIR.mkdir(exist_ok=True)
WORKFLOWS_DIR.mkdir(exist_ok=True)

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
GUI_WINDOW_HEIGHT: Final[int] = 768
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

    # Add console handler with color
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler with rotation
    logger.add(
        LOG_FILE_PATH,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Thread-safe logging
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
BROWSER_ARGS: Final[list[str]] = [
    "--start-maximized",
    "--disable-blink-features=AutomationControlled",
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
