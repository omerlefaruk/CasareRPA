"""
CasareRPA Logging Configuration.

Configures loguru logger with file rotation, formatting, and console output.
"""

import sys
from pathlib import Path
from typing import Final

from loguru import logger

from casare_rpa.config.paths import APP_NAME, APP_VERSION, LOGS_DIR


# Logging configuration constants
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

    Should be called once at application startup.
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


__all__ = [
    "LOG_FILE_PATH",
    "LOG_RETENTION",
    "LOG_ROTATION",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "setup_logging",
]
