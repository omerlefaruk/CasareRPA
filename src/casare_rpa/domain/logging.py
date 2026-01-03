"""
Domain-safe logging helpers.

Domain must not depend on concrete logging frameworks (e.g., loguru). All domain
logging routes through the `LoggerService` protocol-based facade.
"""

from __future__ import annotations

import logging

from casare_rpa.domain.interfaces.logger import LoggerService


def get_domain_logger() -> logging.Logger | object:
    """
    Return the configured domain logger.

    If no logger is configured yet, fall back to stdlib logging.
    """

    try:
        return LoggerService.get()
    except Exception:
        return logging.getLogger(__name__)
