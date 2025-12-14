"""
CasareRPA Timeout Configuration.

Centralized timeout values for all operations requiring time limits.
Uses frozen dataclasses for immutability with environment variable overrides.

Usage:
    from casare_rpa.config.timeout_config import get_timeout_config

    config = get_timeout_config()
    timeout = config.http_timeout_s
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


def _parse_float(value: str | None, default: float) -> float:
    """Parse float from environment variable string."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_int(value: str | None, default: int) -> int:
    """Parse integer from environment variable string."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class TimeoutConfig:
    """
    Centralized timeout configuration for all CasareRPA operations.

    All timeout values are extracted from hardcoded defaults across the codebase.
    Each field documents its original location and purpose.

    Attributes:
        http_timeout_s: Default HTTP client timeout in seconds.
            Used by UnifiedHttpClient and API requests.

        websocket_close_s: Timeout for gracefully closing WebSocket connections.
            Used in orchestrator communication layer.

        browser_element_ms: Default browser element wait timeout in milliseconds.
            Used for Playwright element operations.

        browser_download_s: Maximum time to wait for file downloads in seconds.
            Used by browser download operations.

        execution_cleanup_s: Timeout for cleanup operations after node execution.
            Allows graceful resource release.

        pool_close_s: Timeout for closing connection pools (DB, HTTP).
            Used during application shutdown.

        agent_execution_s: Maximum execution time for AI agents in seconds.
            Prevents runaway AI operations.

        vision_search_ms: Timeout for AI vision-based element search in milliseconds.
            Used by VisionElementFinder.

        canvas_signal_ms: Timeout for Qt signals in canvas operations in milliseconds.
            Prevents UI deadlocks.

        health_check_s: Timeout for health check HTTP requests in seconds.
            Used by service health monitors.

        websocket_ping_s: Interval for WebSocket ping/pong keepalive in seconds.
            Maintains connection health.

        process_termination_s: Timeout for terminating child processes in seconds.
            Used during graceful shutdown.

        desktop_element_s: Timeout for desktop automation element operations in seconds.
            Used by uiautomation operations.

        selector_find_s: Timeout for selector-based element finding in seconds.
            Used across browser and desktop automation.

        page_load_ms: Default page load timeout in milliseconds.
            Used by Playwright navigation.

        node_default_s: Default per-node execution timeout in seconds.
            Applied when node doesn't specify custom timeout.

        job_timeout_s: Maximum job execution time in seconds.
            Used by orchestrator job queue.
    """

    # HTTP/Network timeouts
    http_timeout_s: float = 30.0
    websocket_close_s: float = 5.0
    websocket_ping_s: float = 10.0
    health_check_s: float = 10.0

    # Browser automation timeouts
    browser_element_ms: int = 100
    browser_download_s: int = 600
    page_load_ms: int = 30000

    # Desktop automation timeouts
    desktop_element_s: float = 5.0
    selector_find_s: float = 10.0

    # Execution timeouts
    execution_cleanup_s: float = 30.0
    node_default_s: int = 30
    job_timeout_s: int = 3600

    # Resource management timeouts
    pool_close_s: float = 10.0
    process_termination_s: float = 5.0

    # AI/ML timeouts
    agent_execution_s: int = 300
    vision_search_ms: int = 10000

    # UI timeouts
    canvas_signal_ms: int = 8000

    @classmethod
    def from_env(cls) -> TimeoutConfig:
        """
        Create TimeoutConfig from environment variables.

        Environment variable names follow the pattern:
        CASARE_TIMEOUT_{CATEGORY}_{NAME}

        Example:
            CASARE_TIMEOUT_HTTP_S=60.0
            CASARE_TIMEOUT_BROWSER_DOWNLOAD_S=900

        Returns:
            TimeoutConfig with values from environment or defaults
        """
        return cls(
            # HTTP/Network
            http_timeout_s=_parse_float(os.getenv("CASARE_TIMEOUT_HTTP_S"), 30.0),
            websocket_close_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_WEBSOCKET_CLOSE_S"), 5.0
            ),
            websocket_ping_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_WEBSOCKET_PING_S"), 10.0
            ),
            health_check_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_HEALTH_CHECK_S"), 10.0
            ),
            # Browser automation
            browser_element_ms=_parse_int(
                os.getenv("CASARE_TIMEOUT_BROWSER_ELEMENT_MS"), 100
            ),
            browser_download_s=_parse_int(
                os.getenv("CASARE_TIMEOUT_BROWSER_DOWNLOAD_S"), 600
            ),
            page_load_ms=_parse_int(os.getenv("CASARE_TIMEOUT_PAGE_LOAD_MS"), 30000),
            # Desktop automation
            desktop_element_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_DESKTOP_ELEMENT_S"), 5.0
            ),
            selector_find_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_SELECTOR_FIND_S"), 10.0
            ),
            # Execution
            execution_cleanup_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_EXECUTION_CLEANUP_S"), 30.0
            ),
            node_default_s=_parse_int(os.getenv("CASARE_TIMEOUT_NODE_DEFAULT_S"), 30),
            job_timeout_s=_parse_int(os.getenv("CASARE_TIMEOUT_JOB_S"), 3600),
            # Resource management
            pool_close_s=_parse_float(os.getenv("CASARE_TIMEOUT_POOL_CLOSE_S"), 10.0),
            process_termination_s=_parse_float(
                os.getenv("CASARE_TIMEOUT_PROCESS_TERMINATION_S"), 5.0
            ),
            # AI/ML
            agent_execution_s=_parse_int(
                os.getenv("CASARE_TIMEOUT_AGENT_EXECUTION_S"), 300
            ),
            vision_search_ms=_parse_int(
                os.getenv("CASARE_TIMEOUT_VISION_SEARCH_MS"), 10000
            ),
            # UI
            canvas_signal_ms=_parse_int(
                os.getenv("CASARE_TIMEOUT_CANVAS_SIGNAL_MS"), 8000
            ),
        )

    def get_http_timeout_ms(self) -> int:
        """Get HTTP timeout in milliseconds."""
        return int(self.http_timeout_s * 1000)

    def get_page_load_s(self) -> float:
        """Get page load timeout in seconds."""
        return self.page_load_ms / 1000.0


# Module-level singleton
_timeout_config: TimeoutConfig | None = None


def get_timeout_config() -> TimeoutConfig:
    """
    Get the timeout configuration singleton.

    Configuration is loaded once from environment variables
    and cached for subsequent calls.

    Returns:
        TimeoutConfig instance
    """
    global _timeout_config
    if _timeout_config is None:
        _timeout_config = TimeoutConfig.from_env()
    return _timeout_config


def reset_timeout_config() -> None:
    """Reset the timeout configuration singleton (for testing)."""
    global _timeout_config
    _timeout_config = None


# Convenience constants for backward compatibility
# These can be used where a simple constant is needed
DEFAULT_HTTP_TIMEOUT_S: Final[float] = 30.0
DEFAULT_BROWSER_DOWNLOAD_S: Final[int] = 600
DEFAULT_PAGE_LOAD_MS: Final[int] = 30000
DEFAULT_NODE_TIMEOUT_S: Final[int] = 30


__all__ = [
    "TimeoutConfig",
    "get_timeout_config",
    "reset_timeout_config",
    "DEFAULT_HTTP_TIMEOUT_S",
    "DEFAULT_BROWSER_DOWNLOAD_S",
    "DEFAULT_PAGE_LOAD_MS",
    "DEFAULT_NODE_TIMEOUT_S",
]
