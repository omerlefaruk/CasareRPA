"""
CasareRPA - Application: Execution Engine

A reusable execution engine that handles the core workflow execution loop.
Consolidates logic from ExecuteWorkflowUseCase and SubflowExecutor.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Protocol

from loguru import logger

from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.value_objects.types import NodeId
from casare_rpa.domain.interfaces import IExecutionContext


class INodeExecutor(Protocol):
    async def execute(self, node: Any) -> Any: ...


class IVariableResolver(Protocol):
    def transfer_inputs_to_node(self, node_id: NodeId) -> None: ...
    def validate_output_ports(self, node: Any, result: Dict[str, Any]) -> None: ...


class IExecutionStateManager(Protocol):
    @property
    def is_stopped(self) -> bool: ...
    def mark_node_executed(self, node_id: NodeId) -> None: ...
    def should_execute_node(self, node_id: NodeId) -> bool: ...
    def mark_target_reached(self, node_id: NodeId) -> bool: ...
    async def pause_checkpoint(self) -> None: ...
    def set_current_node(self, node_id: Optional[NodeId]) -> None: ...
    @property
    def executed_nodes(self) -> Set[NodeId]: ...


class BaseExecutionStateManager:
    """Base implementation of IExecutionStateManager with defaults."""

    def __init__(self, context: IExecutionContext):
        self.context = context
        self._executed_nodes: Set[NodeId] = set()

    @property
    def is_stopped(self) -> bool:
        if hasattr(self.context, "is_stopped") and callable(self.context.is_stopped):
            return self.context.is_stopped()
        return False

    def mark_node_executed(self, node_id: NodeId) -> None:
        self._executed_nodes.add(node_id)

    def should_execute_node(self, node_id: NodeId) -> bool:
        return True

    def mark_target_reached(self, node_id: NodeId) -> bool:
        return False

    async def pause_checkpoint(self) -> None:
        if hasattr(self.context, "pause_event") and self.context.pause_event:
            await self.context.pause_event.wait()

    def set_current_node(self, node_id: Optional[NodeId]) -> None:
        pass

    @property
    def executed_nodes(self) -> Set[NodeId]:
        return self._executed_nodes


class WorkflowExecutionEngine:
    """
    Core engine for executing workflows.

    This class encapsulates the sequential execution loop, routing,
    and coordination between state management, node execution, and variable resolution.
    """

    def __init__(
        self,
        orchestrator: ExecutionOrchestrator,
        node_executor: INodeExecutor,
        variable_resolver: IVariableResolver,
        state_manager: IExecutionStateManager,
        node_getter: Callable[[NodeId], Any],
        context: IExecutionContext,
        result_handler: Optional[Any] = None,
        parallel_strategy: Optional[Any] = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.node_executor = node_executor
        self.variable_resolver = variable_resolver
        self.state_manager = state_manager
        self.node_getter = node_getter
        self.context = context
        self.result_handler = result_handler
        self.parallel_strategy = parallel_strategy

    async def run_from_node(self, start_id: NodeId) -> None:
        """Main Loop: Sequential execution from start node."""
        queue: List[NodeId] = [start_id]

        while queue and not self.state_manager.is_stopped:
            await self.state_manager.pause_checkpoint()
            if self.state_manager.is_stopped:
                break

            curr_id = queue.pop(0)
            self.state_manager.set_current_node(curr_id)

            # Skip if executed (unless loop)
            is_loop = self.orchestrator.is_control_flow_node(curr_id)
            if curr_id in self.state_manager.executed_nodes and not is_loop:
                continue

            # Run-to-Node Check
            if not self.state_manager.should_execute_node(curr_id):
                continue

            try:
                node = self.node_getter(curr_id)
            except Exception as e:
                logger.error(f"Failed to get node {curr_id}: {e}")
                continue

            self.variable_resolver.transfer_inputs_to_node(curr_id)
            exec_result = await self.node_executor.execute(node)

            if not exec_result.success:
                if self.result_handler and self.result_handler.handle_execution_failure(
                    curr_id, exec_result.result, queue
                ):
                    continue
                break

            self.state_manager.mark_node_executed(curr_id)
            self.store_node_outputs(curr_id, node)

            if exec_result.result:
                self.variable_resolver.validate_output_ports(node, exec_result.result)

            if self.state_manager.mark_target_reached(curr_id):
                break

            # Routing & Special Results
            if exec_result.result:
                # Handle Parallel Branches
                if "parallel_branches" in exec_result.result and self.parallel_strategy:
                    await self.parallel_strategy.execute_parallel_branches(exec_result.result)
                    join_id = exec_result.result.get("paired_join_id")
                    if join_id:
                        queue.insert(0, join_id)
                    continue

                # Handle Parallel Foreach
                if "parallel_foreach_batch" in exec_result.result and self.parallel_strategy:
                    if hasattr(self.parallel_strategy, "execute_parallel_foreach_batch"):
                        await self.parallel_strategy.execute_parallel_foreach_batch(
                            exec_result.result, curr_id
                        )
                    queue.insert(0, curr_id)
                    continue

                # Handle other special results (Subflows, etc.)
                if self.result_handler and self.result_handler.handle_special_results(
                    curr_id, exec_result, queue
                ):
                    continue

            # Default Routing
            next_ids = self.orchestrator.get_next_nodes(curr_id, exec_result.result)
            queue.extend(next_ids)

    def store_node_outputs(self, node_id: str, node: Any) -> None:
        """Store node output values in context for variable resolution."""
        if not hasattr(node, "output_ports"):
            return

        output_ports = getattr(node, "output_ports", {})
        if not output_ports:
            return

        data_outputs = {}
        for port_name, port in output_ports.items():
            if port_name.startswith("exec") or port_name.startswith("_exec"):
                continue
            value = port.get_value() if hasattr(port, "get_value") else None
            if value is not None:
                data_outputs[port_name] = value

        if data_outputs:
            self.context.set_variable(node_id, data_outputs)
