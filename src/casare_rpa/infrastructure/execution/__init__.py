"""
CasareRPA Infrastructure - Execution Components

Provides execution context and related runtime components.

Entry Points:
    - ExecutionContext: Runtime context for workflow execution
    - RetryHandler: Exponential backoff retry logic
    - HookRunner: Lifecycle hook execution

Key Patterns:
    - Retry with exponential backoff and jitter
    - Lifecycle hooks (on_start, on_success, on_failure, on_complete)
    - Singleton accessors via get_*() functions
"""

from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
from casare_rpa.infrastructure.execution.hook_runner import (
    HookContext,
    HookRunner,
    get_hook_runner,
    reset_hook_runner,
)
from casare_rpa.infrastructure.execution.retry_handler import (
    RetryHandler,
    get_retry_handler,
    reset_retry_handler,
)

__all__ = [
    # Core execution context
    "ExecutionContext",
    # Retry handling
    "RetryHandler",
    "get_retry_handler",
    "reset_retry_handler",
    # Lifecycle hooks
    "HookContext",
    "HookRunner",
    "get_hook_runner",
    "reset_hook_runner",
]
