"""
Debug Controller for interactive workflow debugging.

Provides comprehensive debugging capabilities:
- Breakpoint management (regular, conditional, hit-count)
- Step-through execution (step over, step into, step out)
- Variable inspection at each step
- Expression evaluation
- Call stack visualization
- Execution state snapshot/restore
- Watch expressions
"""

import asyncio
import copy
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext

    from ..main_window import MainWindow


class BreakpointType(Enum):
    """Type of breakpoint."""

    REGULAR = auto()
    CONDITIONAL = auto()
    HIT_COUNT = auto()
    LOG_POINT = auto()


@dataclass
class Breakpoint:
    """
    Represents a breakpoint on a workflow node.

    Attributes:
        node_id: ID of the node where breakpoint is set
        enabled: Whether breakpoint is active
        breakpoint_type: Type of breakpoint
        condition: Python expression for conditional breakpoints
        hit_count_target: Number of hits before triggering (for hit-count breakpoints)
        log_message: Message to log (for log points, supports {variable} syntax)
        hit_count: Current number of times this breakpoint has been hit
        created_at: Timestamp when breakpoint was created
    """

    node_id: str
    enabled: bool = True
    breakpoint_type: BreakpointType = BreakpointType.REGULAR
    condition: str | None = None
    hit_count_target: int = 1
    log_message: str | None = None
    hit_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def should_break(self, context: "ExecutionContext") -> bool:
        """
        Determine if execution should break at this breakpoint.

        Args:
            context: Current execution context for evaluating conditions

        Returns:
            True if execution should pause at this breakpoint
        """
        if not self.enabled:
            return False

        self.hit_count += 1

        if self.breakpoint_type == BreakpointType.REGULAR:
            return True

        elif self.breakpoint_type == BreakpointType.CONDITIONAL:
            if not self.condition:
                return True
            return self._evaluate_condition(context)

        elif self.breakpoint_type == BreakpointType.HIT_COUNT:
            return self.hit_count >= self.hit_count_target

        elif self.breakpoint_type == BreakpointType.LOG_POINT:
            self._log_message(context)
            return False

        return True

    def _evaluate_condition(self, context: "ExecutionContext") -> bool:
        """
        Evaluate conditional breakpoint expression.

        Args:
            context: Execution context providing variables

        Returns:
            True if condition evaluates to truthy value
        """
        if not self.condition:
            return True

        try:
            variables = context.variables.copy() if hasattr(context, "variables") else {}
            result = eval(self.condition, {"__builtins__": {}}, variables)
            return bool(result)
        except Exception as e:
            logger.warning(
                f"Breakpoint condition evaluation failed for node {self.node_id}: {e}. "
                f"Condition: '{self.condition}'. Treating as True."
            )
            return True

    def _log_message(self, context: "ExecutionContext") -> None:
        """
        Log message for log points.

        Args:
            context: Execution context for variable substitution
        """
        if not self.log_message:
            return

        message = self.log_message
        variables = context.variables.copy() if hasattr(context, "variables") else {}

        pattern = r"\{(\w+)\}"
        for match in re.finditer(pattern, message):
            var_name = match.group(1)
            if var_name in variables:
                message = message.replace(f"{{{var_name}}}", str(variables[var_name]))

        logger.info(f"[LogPoint {self.node_id}] {message}")

    def reset_hit_count(self) -> None:
        """Reset hit count to zero."""
        self.hit_count = 0


@dataclass
class ExecutionSnapshot:
    """
    Snapshot of execution state for restore capability.

    Attributes:
        snapshot_id: Unique identifier for this snapshot
        node_id: Node ID where snapshot was taken
        variables: Copy of all variables at snapshot time
        execution_path: Nodes executed up to this point
        timestamp: When snapshot was created
        description: Optional user description
    """

    snapshot_id: str
    node_id: str
    variables: dict[str, Any]
    execution_path: list[str]
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""


@dataclass
class WatchExpression:
    """
    Watch expression for monitoring values during debugging.

    Attributes:
        expression: Python expression to evaluate
        last_value: Last evaluated value
        last_error: Error message if evaluation failed
        enabled: Whether watch is active
    """

    expression: str
    last_value: Any = None
    last_error: str | None = None
    enabled: bool = True


@dataclass
class CallStackFrame:
    """
    Represents a frame in the debug call stack.

    Attributes:
        node_id: ID of the node in this frame
        node_name: Display name of the node
        node_type: Type of the node (e.g., "IfNode", "LoopNode")
        local_variables: Variables local to this frame
        entry_time: When execution entered this frame
    """

    node_id: str
    node_name: str
    node_type: str
    local_variables: dict[str, Any] = field(default_factory=dict)
    entry_time: datetime = field(default_factory=datetime.now)


class DebugController(QObject):
    """
    Controller for interactive workflow debugging.

    Manages breakpoints, stepping, variable inspection, and debug state.

    Signals:
        debug_mode_changed: Emitted when debug mode is toggled (bool: enabled)
        breakpoint_added: Emitted when breakpoint is added (str: node_id)
        breakpoint_removed: Emitted when breakpoint is removed (str: node_id)
        breakpoint_hit: Emitted when execution hits a breakpoint (str: node_id)
        step_completed: Emitted when a step operation completes (str: node_id)
        variables_updated: Emitted when variables change (dict: variables)
        call_stack_updated: Emitted when call stack changes (list: frames)
        watch_updated: Emitted when watch expressions are evaluated (list: watches)
        snapshot_created: Emitted when snapshot is created (str: snapshot_id)
        execution_paused: Emitted when execution is paused for debugging
        execution_resumed: Emitted when execution resumes from debug pause
    """

    debug_mode_changed = Signal(bool)
    breakpoint_added = Signal(str)
    breakpoint_removed = Signal(str)
    breakpoint_hit = Signal(str)
    step_completed = Signal(str)
    variables_updated = Signal(dict)
    call_stack_updated = Signal(list)
    watch_updated = Signal(list)
    snapshot_created = Signal(str)
    execution_paused = Signal()
    execution_resumed = Signal()

    def __init__(self, main_window: Optional["MainWindow"] = None):
        """
        Initialize debug controller.

        Args:
            main_window: Optional reference to main window for UI integration
        """
        super().__init__()
        self.main_window = main_window

        self._debug_mode_enabled = False
        self._breakpoints: dict[str, Breakpoint] = {}
        self._watch_expressions: list[WatchExpression] = []
        self._snapshots: dict[str, ExecutionSnapshot] = {}
        self._call_stack: list[CallStackFrame] = []

        self._step_event: asyncio.Event | None = None
        self._pause_event: asyncio.Event | None = None
        self._step_mode: str | None = None
        self._step_target_depth: int = 0
        self._current_context: ExecutionContext | None = None
        self._current_node_id: str | None = None

        self._repl_history: list[str] = []
        self._repl_locals: dict[str, Any] = {}

        logger.debug("DebugController initialized")

    def enable_debug_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable debug mode.

        Args:
            enabled: Whether to enable debug mode
        """
        if self._debug_mode_enabled != enabled:
            self._debug_mode_enabled = enabled
            logger.info(f"Debug mode {'enabled' if enabled else 'disabled'}")
            self.debug_mode_changed.emit(enabled)

            if enabled:
                self._step_event = asyncio.Event()
                self._pause_event = asyncio.Event()
                self._pause_event.set()
            else:
                self._step_event = None
                self._pause_event = None
                self._step_mode = None
                self._call_stack.clear()

    @property
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._debug_mode_enabled

    def add_breakpoint(
        self,
        node_id: str,
        breakpoint_type: BreakpointType = BreakpointType.REGULAR,
        condition: str | None = None,
        hit_count_target: int = 1,
        log_message: str | None = None,
    ) -> Breakpoint:
        """
        Add a breakpoint to a node.

        Args:
            node_id: ID of the node to set breakpoint on
            breakpoint_type: Type of breakpoint
            condition: Python expression for conditional breakpoints
            hit_count_target: Hit count threshold for hit-count breakpoints
            log_message: Message for log points

        Returns:
            The created Breakpoint object
        """
        breakpoint = Breakpoint(
            node_id=node_id,
            breakpoint_type=breakpoint_type,
            condition=condition,
            hit_count_target=hit_count_target,
            log_message=log_message,
        )
        self._breakpoints[node_id] = breakpoint
        logger.info(f"Breakpoint added on node {node_id} (type: {breakpoint_type.name})")
        self.breakpoint_added.emit(node_id)
        return breakpoint

    def remove_breakpoint(self, node_id: str) -> bool:
        """
        Remove a breakpoint from a node.

        Args:
            node_id: ID of the node to remove breakpoint from

        Returns:
            True if breakpoint was removed, False if not found
        """
        if node_id in self._breakpoints:
            del self._breakpoints[node_id]
            logger.info(f"Breakpoint removed from node {node_id}")
            self.breakpoint_removed.emit(node_id)
            return True
        return False

    def toggle_breakpoint(self, node_id: str) -> bool:
        """
        Toggle breakpoint on a node.

        Args:
            node_id: ID of the node to toggle breakpoint on

        Returns:
            True if breakpoint is now enabled, False if disabled/removed
        """
        if node_id in self._breakpoints:
            self.remove_breakpoint(node_id)
            return False
        else:
            self.add_breakpoint(node_id)
            return True

    def toggle_breakpoint_enabled(self, node_id: str) -> bool:
        """
        Toggle enabled state of an existing breakpoint.

        Args:
            node_id: ID of the node

        Returns:
            New enabled state, or False if breakpoint not found
        """
        if node_id in self._breakpoints:
            bp = self._breakpoints[node_id]
            bp.enabled = not bp.enabled
            logger.debug(f"Breakpoint {node_id} {'enabled' if bp.enabled else 'disabled'}")
            return bp.enabled
        return False

    def get_breakpoint(self, node_id: str) -> Breakpoint | None:
        """
        Get breakpoint for a node.

        Args:
            node_id: ID of the node

        Returns:
            Breakpoint object or None if not found
        """
        return self._breakpoints.get(node_id)

    def get_all_breakpoints(self) -> list[Breakpoint]:
        """
        Get all breakpoints.

        Returns:
            List of all breakpoints
        """
        return list(self._breakpoints.values())

    def clear_all_breakpoints(self) -> int:
        """
        Remove all breakpoints.

        Returns:
            Number of breakpoints removed
        """
        count = len(self._breakpoints)
        node_ids = list(self._breakpoints.keys())
        self._breakpoints.clear()
        for node_id in node_ids:
            self.breakpoint_removed.emit(node_id)
        logger.info(f"Cleared {count} breakpoints")
        return count

    def has_breakpoint(self, node_id: str) -> bool:
        """
        Check if a node has a breakpoint.

        Args:
            node_id: ID of the node

        Returns:
            True if node has a breakpoint
        """
        return node_id in self._breakpoints

    async def check_breakpoint(self, node_id: str, context: "ExecutionContext") -> bool:
        """
        Check if execution should pause at a breakpoint.

        Called by DebugExecutor before each node execution.

        Args:
            node_id: ID of the node about to execute
            context: Current execution context

        Returns:
            True if execution was paused (breakpoint hit)
        """
        if not self._debug_mode_enabled:
            return False

        self._current_node_id = node_id
        self._current_context = context

        breakpoint = self._breakpoints.get(node_id)
        if breakpoint and breakpoint.should_break(context):
            logger.info(f"Breakpoint hit at node {node_id}")
            self.breakpoint_hit.emit(node_id)
            await self._pause_for_debug()
            return True

        return False

    async def _pause_for_debug(self) -> None:
        """Pause execution for debugging and wait for step/continue command."""
        self.execution_paused.emit()
        self._update_debug_state()

        if self._step_event:
            self._step_event.clear()
            await self._step_event.wait()

        self.execution_resumed.emit()

    def _update_debug_state(self) -> None:
        """Update all debug state displays (variables, watches, call stack)."""
        if self._current_context:
            variables = dict(self._current_context.variables)
            self.variables_updated.emit(variables)

        self._evaluate_watches()
        self.call_stack_updated.emit(list(self._call_stack))

    def step_over(self) -> None:
        """
        Execute current node and pause at next node (same level).

        Does not step into sub-workflows or nested structures.
        """
        if not self._debug_mode_enabled:
            return

        self._step_mode = "over"
        self._step_target_depth = len(self._call_stack)
        logger.debug("Step over requested")

        if self._step_event:
            self._step_event.set()

    def step_into(self) -> None:
        """
        Execute current node and pause at next node (including nested).

        Steps into sub-workflows or nested control structures.
        """
        if not self._debug_mode_enabled:
            return

        self._step_mode = "into"
        logger.debug("Step into requested")

        if self._step_event:
            self._step_event.set()

    def step_out(self) -> None:
        """
        Continue execution until returning from current scope.

        Continues until exiting the current control structure.
        """
        if not self._debug_mode_enabled:
            return

        self._step_mode = "out"
        self._step_target_depth = max(0, len(self._call_stack) - 1)
        logger.debug("Step out requested")

        if self._step_event:
            self._step_event.set()

    def continue_execution(self) -> None:
        """Continue execution until next breakpoint or end."""
        if not self._debug_mode_enabled:
            return

        self._step_mode = None
        logger.debug("Continue execution requested")

        if self._step_event:
            self._step_event.set()

    async def should_pause_for_step(self, node_id: str, context: "ExecutionContext") -> bool:
        """
        Check if execution should pause based on step mode.

        Called by DebugExecutor after each node execution.

        Args:
            node_id: ID of the node just executed
            context: Current execution context

        Returns:
            True if execution should pause
        """
        if not self._debug_mode_enabled:
            return False

        self._current_node_id = node_id
        self._current_context = context

        should_pause = False
        current_depth = len(self._call_stack)

        if self._step_mode == "into":
            should_pause = True

        elif self._step_mode == "over":
            should_pause = current_depth <= self._step_target_depth

        elif self._step_mode == "out":
            should_pause = current_depth < self._step_target_depth

        if should_pause:
            logger.debug(f"Step pause at node {node_id}")
            self.step_completed.emit(node_id)
            await self._pause_for_debug()
            return True

        return False

    def push_call_stack(self, node_id: str, node_name: str, node_type: str) -> None:
        """
        Push a new frame onto the call stack.

        Args:
            node_id: ID of the node
            node_name: Display name of the node
            node_type: Type of the node
        """
        frame = CallStackFrame(
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
        )
        self._call_stack.append(frame)
        self.call_stack_updated.emit(list(self._call_stack))

    def pop_call_stack(self) -> CallStackFrame | None:
        """
        Pop a frame from the call stack.

        Returns:
            The popped frame, or None if stack was empty
        """
        if self._call_stack:
            frame = self._call_stack.pop()
            self.call_stack_updated.emit(list(self._call_stack))
            return frame
        return None

    def get_call_stack(self) -> list[CallStackFrame]:
        """
        Get current call stack.

        Returns:
            List of call stack frames (most recent last)
        """
        return list(self._call_stack)

    def add_watch(self, expression: str) -> WatchExpression:
        """
        Add a watch expression.

        Args:
            expression: Python expression to watch

        Returns:
            The created WatchExpression
        """
        watch = WatchExpression(expression=expression)
        self._watch_expressions.append(watch)
        self._evaluate_watches()
        logger.debug(f"Watch added: {expression}")
        return watch

    def remove_watch(self, expression: str) -> bool:
        """
        Remove a watch expression.

        Args:
            expression: Expression to remove

        Returns:
            True if watch was removed
        """
        for i, watch in enumerate(self._watch_expressions):
            if watch.expression == expression:
                self._watch_expressions.pop(i)
                self._evaluate_watches()
                logger.debug(f"Watch removed: {expression}")
                return True
        return False

    def get_watches(self) -> list[WatchExpression]:
        """
        Get all watch expressions.

        Returns:
            List of watch expressions
        """
        return list(self._watch_expressions)

    def _evaluate_watches(self) -> None:
        """Evaluate all watch expressions and emit update."""
        if not self._current_context:
            return

        variables = dict(self._current_context.variables)

        for watch in self._watch_expressions:
            if not watch.enabled:
                continue

            try:
                watch.last_value = eval(
                    watch.expression,
                    {"__builtins__": {}},
                    variables,
                )
                watch.last_error = None
            except Exception as e:
                watch.last_value = None
                watch.last_error = str(e)

        self.watch_updated.emit(list(self._watch_expressions))

    def evaluate_expression(self, expression: str) -> tuple[Any, str | None]:
        """
        Evaluate an expression in the current debug context.

        Args:
            expression: Python expression to evaluate

        Returns:
            Tuple of (result, error_message). Error is None on success.
        """
        if not self._current_context:
            return None, "No active debug context"

        variables = dict(self._current_context.variables)
        variables.update(self._repl_locals)

        try:
            result = eval(expression, {"__builtins__": {}}, variables)
            self._repl_history.append(expression)
            return result, None
        except SyntaxError:
            try:
                exec(expression, {"__builtins__": {}}, self._repl_locals)
                self._repl_history.append(expression)
                return None, None
            except Exception as e:
                return None, str(e)
        except Exception as e:
            return None, str(e)

    def get_variable_value(self, name: str) -> tuple[Any, bool]:
        """
        Get the value of a variable in the current context.

        Args:
            name: Variable name

        Returns:
            Tuple of (value, found). Found is False if variable doesn't exist.
        """
        if not self._current_context:
            return None, False

        variables = self._current_context.variables
        if name in variables:
            return variables[name], True
        return None, False

    def set_variable_value(self, name: str, value: Any) -> bool:
        """
        Set a variable value in the current context.

        Args:
            name: Variable name
            value: Value to set

        Returns:
            True if successful
        """
        if not self._current_context:
            return False

        self._current_context.set_variable(name, value)
        self._update_debug_state()
        logger.debug(f"Variable set via debugger: {name} = {value!r}")
        return True

    def create_snapshot(self, description: str = "") -> ExecutionSnapshot:
        """
        Create a snapshot of current execution state.

        Args:
            description: Optional description for the snapshot

        Returns:
            The created snapshot
        """
        import uuid

        snapshot_id = str(uuid.uuid4())[:8]

        if not self._current_context:
            logger.warning("Cannot create snapshot: no active context")
            snapshot = ExecutionSnapshot(
                snapshot_id=snapshot_id,
                node_id=self._current_node_id or "",
                variables={},
                execution_path=[],
                description=description,
            )
        else:
            snapshot = ExecutionSnapshot(
                snapshot_id=snapshot_id,
                node_id=self._current_node_id or "",
                variables=copy.deepcopy(self._current_context.variables),
                execution_path=list(self._current_context.execution_path),
                description=description,
            )

        self._snapshots[snapshot_id] = snapshot
        logger.info(f"Snapshot created: {snapshot_id}")
        self.snapshot_created.emit(snapshot_id)
        return snapshot

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore execution state from a snapshot.

        Note: This restores variables only. Execution path cannot be rewound.

        Args:
            snapshot_id: ID of snapshot to restore

        Returns:
            True if snapshot was restored
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.warning(f"Snapshot not found: {snapshot_id}")
            return False

        if not self._current_context:
            logger.warning("Cannot restore snapshot: no active context")
            return False

        self._current_context.variables.clear()
        self._current_context.variables.update(copy.deepcopy(snapshot.variables))

        self._update_debug_state()
        logger.info(f"Snapshot restored: {snapshot_id}")
        return True

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Args:
            snapshot_id: ID of snapshot to delete

        Returns:
            True if snapshot was deleted
        """
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            logger.debug(f"Snapshot deleted: {snapshot_id}")
            return True
        return False

    def get_snapshots(self) -> list[ExecutionSnapshot]:
        """
        Get all snapshots.

        Returns:
            List of snapshots
        """
        return list(self._snapshots.values())

    def get_repl_history(self) -> list[str]:
        """
        Get REPL command history.

        Returns:
            List of executed expressions
        """
        return list(self._repl_history)

    def clear_repl(self) -> None:
        """Clear REPL state and history."""
        self._repl_history.clear()
        self._repl_locals.clear()
        logger.debug("REPL cleared")

    def cleanup(self) -> None:
        """Clean up debug controller resources."""
        self._debug_mode_enabled = False
        self._breakpoints.clear()
        self._watch_expressions.clear()
        self._snapshots.clear()
        self._call_stack.clear()
        self._repl_history.clear()
        self._repl_locals.clear()
        self._current_context = None
        self._current_node_id = None
        logger.debug("DebugController cleaned up")
