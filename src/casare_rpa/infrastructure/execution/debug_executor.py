"""
Debug Executor for CasareRPA workflow debugging.

Provides debug-mode execution with:
- Breakpoint integration
- Step-through execution control
- Variable inspection at each step
- Execution state tracking
- Integration with DebugController
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from loguru import logger

from casare_rpa.domain.value_objects.types import NodeId, NodeStatus

if TYPE_CHECKING:
    from casare_rpa.domain.entities.workflow import WorkflowSchema
    from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
    from casare_rpa.presentation.canvas.debugger.debug_controller import DebugController


class DebugState(Enum):
    """Current state of the debug executor."""

    IDLE = auto()
    RUNNING = auto()
    PAUSED_BREAKPOINT = auto()
    PAUSED_STEP = auto()
    STEPPING = auto()
    COMPLETED = auto()
    ERROR = auto()


class StepMode(Enum):
    """Step execution mode."""

    NONE = auto()
    INTO = auto()
    OVER = auto()
    OUT = auto()


@dataclass
class NodeExecutionRecord:
    """
    Record of a node's execution during debug session.

    Attributes:
        node_id: ID of the executed node
        node_type: Type name of the node
        start_time: When execution started
        end_time: When execution ended
        duration_ms: Execution duration in milliseconds
        status: Execution status
        input_values: Input port values at execution time
        output_values: Output port values after execution
        variables_before: Variable state before execution
        variables_after: Variable state after execution
        error_message: Error message if execution failed
    """

    node_id: str
    node_type: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float = 0.0
    status: NodeStatus = NodeStatus.IDLE
    input_values: dict[str, Any] = field(default_factory=dict)
    output_values: dict[str, Any] = field(default_factory=dict)
    variables_before: dict[str, Any] = field(default_factory=dict)
    variables_after: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass
class DebugSession:
    """
    Tracks a debug session.

    Attributes:
        session_id: Unique session identifier
        workflow_name: Name of the workflow being debugged
        start_time: When debug session started
        end_time: When debug session ended
        execution_records: List of node execution records
        breakpoints_hit: Set of node IDs where breakpoints were hit
        step_count: Number of steps taken
        state: Current debug state
    """

    session_id: str
    workflow_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    execution_records: list[NodeExecutionRecord] = field(default_factory=list)
    breakpoints_hit: set[str] = field(default_factory=set)
    step_count: int = 0
    state: DebugState = DebugState.IDLE


class DebugExecutor:
    """
    Debug-mode workflow executor.

    Integrates with DebugController to provide:
    - Breakpoint-aware execution
    - Step-through control (step over, step into, step out)
    - Variable inspection at each step
    - Execution history tracking
    - State snapshots

    Usage:
        debug_controller = DebugController()
        executor = DebugExecutor(workflow, context, debug_controller)

        # Set breakpoints via controller
        debug_controller.add_breakpoint("node_123")

        # Execute with debugging
        await executor.execute()

        # Step through execution
        debug_controller.step_over()
    """

    def __init__(
        self,
        workflow: "WorkflowSchema",
        context: "ExecutionContext",
        debug_controller: "DebugController",
        node_timeout: float = 120.0,
        continue_on_error: bool = False,
    ) -> None:
        """
        Initialize debug executor.

        Args:
            workflow: Workflow schema to execute
            context: Execution context for variables and resources
            debug_controller: Debug controller for breakpoints and stepping
            node_timeout: Timeout for individual node execution in seconds
            continue_on_error: Whether to continue execution on node errors
        """
        self.workflow = workflow
        self.context = context
        self.debug_controller = debug_controller
        self.node_timeout = node_timeout
        self.continue_on_error = continue_on_error

        self._session: DebugSession | None = None
        self._state = DebugState.IDLE
        self._stop_requested = False
        self._step_mode = StepMode.NONE
        self._step_depth = 0
        self._current_depth = 0

        self._executed_nodes: set[NodeId] = set()
        self._current_node_id: NodeId | None = None
        self._current_record: NodeExecutionRecord | None = None

        self._pause_event = asyncio.Event()
        self._pause_event.set()

        logger.debug("DebugExecutor initialized")

    @property
    def state(self) -> DebugState:
        """Get current debug state."""
        return self._state

    @property
    def session(self) -> DebugSession | None:
        """Get current debug session."""
        return self._session

    async def execute(self) -> bool:
        """
        Execute workflow in debug mode.

        Returns:
            True if execution completed successfully
        """
        import uuid

        session_id = str(uuid.uuid4())[:8]
        workflow_name = (
            self.workflow.metadata.name if hasattr(self.workflow, "metadata") else "Unknown"
        )

        self._session = DebugSession(
            session_id=session_id,
            workflow_name=workflow_name,
        )
        self._state = DebugState.RUNNING
        self._stop_requested = False
        self._executed_nodes.clear()

        logger.info(f"Starting debug execution: {workflow_name} (session: {session_id})")

        try:
            start_node_id = self._find_start_node()
            if not start_node_id:
                raise ValueError("No StartNode found in workflow")

            await self._execute_from_node(start_node_id)

            if self._stop_requested:
                self._state = DebugState.IDLE
                logger.info("Debug execution stopped by user")
                return False

            self._state = DebugState.COMPLETED
            self._session.end_time = datetime.now()
            logger.info(
                f"Debug execution completed: {len(self._executed_nodes)} nodes, "
                f"{self._session.step_count} steps"
            )
            return True

        except Exception as e:
            self._state = DebugState.ERROR
            self._session.end_time = datetime.now()
            logger.exception(f"Debug execution failed: {e}")
            return False

    def _find_start_node(self) -> NodeId | None:
        """Find the StartNode in the workflow."""
        for node_id, node in self.workflow.nodes.items():
            if node.__class__.__name__ == "StartNode":
                return node_id
        return None

    async def _execute_from_node(self, start_node_id: NodeId) -> None:
        """
        Execute workflow from a specific node.

        Args:
            start_node_id: Node ID to start execution from
        """
        from casare_rpa.domain.services.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        orchestrator = ExecutionOrchestrator(self.workflow)
        nodes_to_execute: list[NodeId] = [start_node_id]

        while nodes_to_execute and not self._stop_requested:
            current_node_id = nodes_to_execute.pop(0)

            is_loop_node = orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in self._executed_nodes and not is_loop_node:
                continue

            node = self.workflow.nodes.get(current_node_id)
            if not node:
                logger.error(f"Node {current_node_id} not found in workflow")
                continue

            await self._pause_checkpoint()
            if self._stop_requested:
                break

            hit_breakpoint = await self.debug_controller.check_breakpoint(
                current_node_id, self.context
            )
            if hit_breakpoint:
                self._state = DebugState.PAUSED_BREAKPOINT
                self._session.breakpoints_hit.add(current_node_id)

            self._transfer_input_data(current_node_id, orchestrator)

            success, result = await self._execute_node(node, current_node_id)

            if not success and not self.continue_on_error:
                logger.warning(f"Stopping debug execution due to node error: {current_node_id}")
                break

            should_pause = await self.debug_controller.should_pause_for_step(
                current_node_id, self.context
            )
            if should_pause:
                self._state = DebugState.PAUSED_STEP
                self._session.step_count += 1

            next_node_ids = orchestrator.get_next_nodes(current_node_id, result)
            nodes_to_execute.extend(next_node_ids)

    async def _execute_node(self, node: Any, node_id: NodeId) -> tuple[bool, dict[str, Any] | None]:
        """
        Execute a single node with debug tracking.

        Args:
            node: Node instance to execute
            node_id: ID of the node

        Returns:
            Tuple of (success, result)
        """
        import copy
        import time

        if node.config.get("_disabled", False):
            logger.info(f"Node {node_id} is disabled - bypassing")
            return True, {"success": True, "bypassed": True}

        self._current_node_id = node_id
        node_type = node.__class__.__name__

        self._current_record = NodeExecutionRecord(
            node_id=node_id,
            node_type=node_type,
            start_time=datetime.now(),
            variables_before=copy.deepcopy(self.context.variables),
        )

        if hasattr(node, "input_values"):
            self._current_record.input_values = copy.deepcopy(
                dict(getattr(node, "input_values", {}))
            )

        self.debug_controller.push_call_stack(
            node_id=node_id,
            node_name=getattr(node, "name", node_type),
            node_type=node_type,
        )

        start_time = time.perf_counter()

        try:
            if not node.validate():
                self._current_record.status = NodeStatus.ERROR
                self._current_record.error_message = "Validation failed"
                self._current_record.end_time = datetime.now()
                self._session.execution_records.append(self._current_record)
                self.debug_controller.pop_call_stack()
                return False, None

            result = await asyncio.wait_for(
                node.execute(self.context),
                timeout=self.node_timeout,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000
            self._current_record.duration_ms = duration_ms
            self._current_record.end_time = datetime.now()
            self._current_record.variables_after = copy.deepcopy(self.context.variables)

            if hasattr(node, "output_values"):
                self._current_record.output_values = copy.deepcopy(
                    dict(getattr(node, "output_values", {}))
                )

            if result and result.get("success", False):
                self._current_record.status = NodeStatus.SUCCESS
                self._executed_nodes.add(node_id)
                self._session.execution_records.append(self._current_record)
                self.debug_controller.pop_call_stack()
                return True, result
            else:
                self._current_record.status = NodeStatus.ERROR
                self._current_record.error_message = (
                    result.get("error", "Unknown error") if result else "No result"
                )
                self._session.execution_records.append(self._current_record)
                self.debug_controller.pop_call_stack()
                return False, result

        except TimeoutError:
            self._current_record.status = NodeStatus.ERROR
            self._current_record.error_message = f"Timeout after {self.node_timeout}s"
            self._current_record.end_time = datetime.now()
            self._session.execution_records.append(self._current_record)
            self.debug_controller.pop_call_stack()
            logger.error(f"Node {node_id} timed out after {self.node_timeout}s")
            return False, None

        except Exception as e:
            self._current_record.status = NodeStatus.ERROR
            self._current_record.error_message = str(e)
            self._current_record.end_time = datetime.now()
            self._session.execution_records.append(self._current_record)
            self.debug_controller.pop_call_stack()
            logger.exception(f"Node {node_id} execution failed: {e}")
            return False, None

    def _transfer_input_data(self, node_id: NodeId, orchestrator: Any) -> None:
        """
        Transfer data from connected input ports.

        Args:
            node_id: Target node ID
            orchestrator: Execution orchestrator for connection lookup
        """
        for connection in self.workflow.connections:
            if connection.target_node == node_id:
                source_node = self.workflow.nodes.get(connection.source_node)
                target_node = self.workflow.nodes.get(connection.target_node)

                if not source_node or not target_node:
                    continue

                value = source_node.get_output_value(connection.source_port)

                if value is not None:
                    target_node.set_input_value(connection.target_port, value)

                    if "exec" not in connection.source_port.lower():
                        logger.debug(
                            f"Data transfer: {connection.source_port} -> "
                            f"{connection.target_port} = {repr(value)[:50]}"
                        )

    async def _pause_checkpoint(self) -> None:
        """Pause checkpoint - wait if pause event is cleared."""
        if not self._pause_event.is_set():
            logger.debug("Debug execution paused at checkpoint")
            await self._pause_event.wait()
            logger.debug("Debug execution resumed from checkpoint")

    def pause(self) -> None:
        """Pause debug execution."""
        if self._state == DebugState.RUNNING:
            self._pause_event.clear()
            self._state = DebugState.PAUSED_STEP
            logger.info("Debug execution paused")

    def resume(self) -> None:
        """Resume debug execution."""
        if self._state in (DebugState.PAUSED_BREAKPOINT, DebugState.PAUSED_STEP):
            self._pause_event.set()
            self._state = DebugState.RUNNING
            logger.info("Debug execution resumed")

    def stop(self) -> None:
        """Stop debug execution."""
        self._stop_requested = True
        self._pause_event.set()
        logger.info("Debug execution stop requested")

    def get_execution_records(self) -> list[NodeExecutionRecord]:
        """
        Get all execution records from current session.

        Returns:
            List of node execution records
        """
        if self._session:
            return list(self._session.execution_records)
        return []

    def get_current_record(self) -> NodeExecutionRecord | None:
        """
        Get the current node's execution record.

        Returns:
            Current execution record or None
        """
        return self._current_record

    def get_variable_history(self, variable_name: str) -> list[tuple[str, Any]]:
        """
        Get history of a variable's values across execution.

        Args:
            variable_name: Name of the variable

        Returns:
            List of (node_id, value) tuples showing value after each node
        """
        history = []
        if not self._session:
            return history

        for record in self._session.execution_records:
            if variable_name in record.variables_after:
                history.append((record.node_id, record.variables_after[variable_name]))

        return history

    def get_node_execution_info(self, node_id: str) -> NodeExecutionRecord | None:
        """
        Get execution record for a specific node.

        Args:
            node_id: ID of the node

        Returns:
            Execution record or None if node hasn't been executed
        """
        if not self._session:
            return None

        for record in reversed(self._session.execution_records):
            if record.node_id == node_id:
                return record

        return None

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Get summary of the debug session.

        Returns:
            Dictionary with session statistics
        """
        if not self._session:
            return {}

        total_duration = 0.0
        success_count = 0
        error_count = 0

        for record in self._session.execution_records:
            total_duration += record.duration_ms
            if record.status == NodeStatus.SUCCESS:
                success_count += 1
            elif record.status == NodeStatus.ERROR:
                error_count += 1

        return {
            "session_id": self._session.session_id,
            "workflow_name": self._session.workflow_name,
            "state": self._state.name,
            "nodes_executed": len(self._session.execution_records),
            "successful_nodes": success_count,
            "failed_nodes": error_count,
            "total_duration_ms": total_duration,
            "breakpoints_hit": len(self._session.breakpoints_hit),
            "step_count": self._session.step_count,
            "start_time": self._session.start_time.isoformat(),
            "end_time": self._session.end_time.isoformat() if self._session.end_time else None,
        }

    def cleanup(self) -> None:
        """Clean up debug executor resources."""
        self._session = None
        self._state = DebugState.IDLE
        self._executed_nodes.clear()
        self._current_node_id = None
        self._current_record = None
        self._stop_requested = False
        logger.debug("DebugExecutor cleaned up")
