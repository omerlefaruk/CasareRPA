"""
CasareRPA Infrastructure - Execution Components

Provides execution context and related runtime components.
"""

from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
from casare_rpa.infrastructure.execution.subworkflow_executor import (
    SubworkflowExecutor,
    SubworkflowExecutionResult,
)

__all__ = [
    "ExecutionContext",
    "SubworkflowExecutor",
    "SubworkflowExecutionResult",
]
