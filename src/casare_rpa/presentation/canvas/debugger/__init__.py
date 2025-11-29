"""
Debugger module for interactive workflow debugging.

Provides:
- DebugController: Main debugger controller with breakpoints and stepping
- Enhanced DebugPanel: UI for variable inspection, call stack, watch expressions

Note: DebugExecutor is in casare_rpa.infrastructure.execution.debug_executor
      to maintain proper layer separation (Infrastructure layer handles execution).
"""

from .debug_controller import (
    DebugController,
    Breakpoint,
    BreakpointType,
    WatchExpression,
    CallStackFrame,
    ExecutionSnapshot,
)

__all__ = [
    "DebugController",
    "Breakpoint",
    "BreakpointType",
    "WatchExpression",
    "CallStackFrame",
    "ExecutionSnapshot",
]
