"""
CasareRPA - Runner Package
Contains execution engine and workflow interpreter.
"""

__version__ = "0.1.0"

from .workflow_runner import WorkflowRunner, ExecutionState

__all__ = [
    "__version__",
    "WorkflowRunner",
    "ExecutionState",
]
