"""
CasareRPA Limits Configuration.

Centralized limit values for workflows, resources, and operations.
Uses frozen dataclasses for immutability with environment variable overrides.

Usage:
    from casare_rpa.config.limits_config import get_limits_config

    config = get_limits_config()
    max_nodes = config.workflow_max_nodes
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


def _parse_int(value: str | None, default: int) -> int:
    """Parse integer from environment variable string."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class LimitsConfig:
    """
    Centralized limits configuration for all CasareRPA operations.

    All limit values are extracted from hardcoded defaults across the codebase.
    These limits protect system resources and prevent runaway operations.

    Attributes:
        workflow_max_nodes: Maximum number of nodes allowed in a workflow.
            Prevents overly complex workflows that impact performance.
            Default: 1000

        workflow_max_connections: Maximum number of connections in a workflow.
            Prevents dense graphs that slow down traversal.
            Default: 5000

        workflow_max_depth: Maximum nesting depth for subworkflows.
            Prevents infinite recursion in workflow execution.
            Default: 10

        html_max_length: Maximum HTML content length to process.
            Prevents memory issues with very large pages.
            Default: 50000

        llm_max_tokens: Default maximum tokens for LLM responses.
            Controls API costs and response length.
            Default: 1000

        llm_context_chars: Maximum context characters for LLM prompts.
            Prevents exceeding model context windows.
            Default: 3000

        llm_max_output_tokens: Maximum output tokens for LLM generation.
            Controls generation length for longer tasks.
            Default: 4000

        batch_size: Default batch size for bulk operations.
            Balances throughput and memory usage.
            Default: 100

        concurrent_jobs_per_robot: Maximum concurrent jobs per robot.
            Prevents resource exhaustion on single robot.
            Default: 1

        event_history_size: Maximum events to keep in history.
            Limits memory usage for event tracking.
            Default: 1000

        variable_name_max_length: Maximum length for variable names.
            Ensures readable variable references.
            Default: 128

        variable_value_max_size: Maximum size for variable values in bytes.
            Prevents memory issues with large variables.
            Default: 10485760 (10 MB)

        file_upload_max_size: Maximum file upload size in bytes.
            Prevents memory issues with large uploads.
            Default: 104857600 (100 MB)

        screenshot_max_size: Maximum screenshot size in bytes.
            Limits storage for debugging screenshots.
            Default: 5242880 (5 MB)

        log_line_max_length: Maximum length for single log lines.
            Prevents log bloat from very long messages.
            Default: 10000

        queue_max_pending: Maximum pending jobs in queue.
            Prevents queue overflow.
            Default: 10000
    """

    # Workflow limits
    workflow_max_nodes: int = 1000
    workflow_max_connections: int = 5000
    workflow_max_depth: int = 10

    # Content limits
    html_max_length: int = 50000
    log_line_max_length: int = 10000

    # LLM limits
    llm_max_tokens: int = 1000
    llm_context_chars: int = 3000
    llm_max_output_tokens: int = 4000

    # Batch/concurrency limits
    batch_size: int = 100
    concurrent_jobs_per_robot: int = 1

    # History/queue limits
    event_history_size: int = 1000
    queue_max_pending: int = 10000

    # Variable limits
    variable_name_max_length: int = 128
    variable_value_max_size: int = 10 * 1024 * 1024  # 10 MB

    # File limits
    file_upload_max_size: int = 100 * 1024 * 1024  # 100 MB
    screenshot_max_size: int = 5 * 1024 * 1024  # 5 MB

    @classmethod
    def from_env(cls) -> LimitsConfig:
        """
        Create LimitsConfig from environment variables.

        Environment variable names follow the pattern:
        CASARE_LIMIT_{CATEGORY}_{NAME}

        Example:
            CASARE_LIMIT_WORKFLOW_MAX_NODES=2000
            CASARE_LIMIT_LLM_MAX_TOKENS=2000

        Returns:
            LimitsConfig with values from environment or defaults
        """
        return cls(
            # Workflow limits
            workflow_max_nodes=_parse_int(os.getenv("CASARE_LIMIT_WORKFLOW_MAX_NODES"), 1000),
            workflow_max_connections=_parse_int(
                os.getenv("CASARE_LIMIT_WORKFLOW_MAX_CONNECTIONS"), 5000
            ),
            workflow_max_depth=_parse_int(os.getenv("CASARE_LIMIT_WORKFLOW_MAX_DEPTH"), 10),
            # Content limits
            html_max_length=_parse_int(os.getenv("CASARE_LIMIT_HTML_MAX_LENGTH"), 50000),
            log_line_max_length=_parse_int(os.getenv("CASARE_LIMIT_LOG_LINE_MAX_LENGTH"), 10000),
            # LLM limits
            llm_max_tokens=_parse_int(os.getenv("CASARE_LIMIT_LLM_MAX_TOKENS"), 1000),
            llm_context_chars=_parse_int(os.getenv("CASARE_LIMIT_LLM_CONTEXT_CHARS"), 3000),
            llm_max_output_tokens=_parse_int(os.getenv("CASARE_LIMIT_LLM_MAX_OUTPUT_TOKENS"), 4000),
            # Batch/concurrency limits
            batch_size=_parse_int(os.getenv("CASARE_LIMIT_BATCH_SIZE"), 100),
            concurrent_jobs_per_robot=_parse_int(
                os.getenv("CASARE_LIMIT_CONCURRENT_JOBS_PER_ROBOT"), 1
            ),
            # History/queue limits
            event_history_size=_parse_int(os.getenv("CASARE_LIMIT_EVENT_HISTORY_SIZE"), 1000),
            queue_max_pending=_parse_int(os.getenv("CASARE_LIMIT_QUEUE_MAX_PENDING"), 10000),
            # Variable limits
            variable_name_max_length=_parse_int(
                os.getenv("CASARE_LIMIT_VARIABLE_NAME_MAX_LENGTH"), 128
            ),
            variable_value_max_size=_parse_int(
                os.getenv("CASARE_LIMIT_VARIABLE_VALUE_MAX_SIZE"), 10 * 1024 * 1024
            ),
            # File limits
            file_upload_max_size=_parse_int(
                os.getenv("CASARE_LIMIT_FILE_UPLOAD_MAX_SIZE"), 100 * 1024 * 1024
            ),
            screenshot_max_size=_parse_int(
                os.getenv("CASARE_LIMIT_SCREENSHOT_MAX_SIZE"), 5 * 1024 * 1024
            ),
        )

    def get_variable_value_max_size_mb(self) -> float:
        """Get variable value max size in megabytes."""
        return self.variable_value_max_size / (1024 * 1024)

    def get_file_upload_max_size_mb(self) -> float:
        """Get file upload max size in megabytes."""
        return self.file_upload_max_size / (1024 * 1024)

    def get_screenshot_max_size_mb(self) -> float:
        """Get screenshot max size in megabytes."""
        return self.screenshot_max_size / (1024 * 1024)

    def is_workflow_valid(self, node_count: int, connection_count: int) -> bool:
        """
        Check if workflow size is within limits.

        Args:
            node_count: Number of nodes in workflow
            connection_count: Number of connections in workflow

        Returns:
            True if workflow is within limits
        """
        return (
            node_count <= self.workflow_max_nodes
            and connection_count <= self.workflow_max_connections
        )


# Module-level singleton
_limits_config: LimitsConfig | None = None


def get_limits_config() -> LimitsConfig:
    """
    Get the limits configuration singleton.

    Configuration is loaded once from environment variables
    and cached for subsequent calls.

    Returns:
        LimitsConfig instance
    """
    global _limits_config
    if _limits_config is None:
        _limits_config = LimitsConfig.from_env()
    return _limits_config


def reset_limits_config() -> None:
    """Reset the limits configuration singleton (for testing)."""
    global _limits_config
    _limits_config = None


# Convenience constants for backward compatibility
DEFAULT_WORKFLOW_MAX_NODES: Final[int] = 1000
DEFAULT_WORKFLOW_MAX_CONNECTIONS: Final[int] = 5000
DEFAULT_HTML_MAX_LENGTH: Final[int] = 50000
DEFAULT_LLM_MAX_TOKENS: Final[int] = 1000
DEFAULT_LLM_CONTEXT_CHARS: Final[int] = 3000


__all__ = [
    "LimitsConfig",
    "get_limits_config",
    "reset_limits_config",
    "DEFAULT_WORKFLOW_MAX_NODES",
    "DEFAULT_WORKFLOW_MAX_CONNECTIONS",
    "DEFAULT_HTML_MAX_LENGTH",
    "DEFAULT_LLM_MAX_TOKENS",
    "DEFAULT_LLM_CONTEXT_CHARS",
]
