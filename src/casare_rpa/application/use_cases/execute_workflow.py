"""
CasareRPA - Application Use Case: Execute Workflow

Coordinates workflow execution via Orchestrator, Context, and Strategy Delegates.
Refactored to minimize token footprint and enforce Single Responsibility.
"""

import asyncio
from datetime import datetime
from typing import Any, cast

from loguru import logger

from casare_rpa.application.use_cases.execution_engine import WorkflowExecutionEngine
from casare_rpa.application.use_cases.execution_handlers import ExecutionResultHandler

# Strategies & Helpers
from casare_rpa.application.use_cases.execution_state_manager import (
    ExecutionSettings,
    ExecutionStateManager,
)
from casare_rpa.application.use_cases.execution_strategies_parallel import (
    ParallelExecutionStrategy,
)
from casare_rpa.application.use_cases.node_executor import (
    NodeExecutor,
    NodeExecutorWithTryCatch,
)
from casare_rpa.application.use_cases.variable_resolver import (
    TryCatchErrorHandler,
    VariableResolver,
)
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.errors import (
    Err,
    NodeExecutionError,
    Ok,
    Result,
    WorkflowExecutionError,
)
from casare_rpa.domain.events import (
    EventBus,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
    WorkflowStopped,
)
from casare_rpa.domain.interfaces import IExecutionContext, IExecutionContextFactory
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.value_objects.types import ExecutionMode, NodeId
from casare_rpa.nodes import get_node_class
from casare_rpa.utils.performance.performance_metrics import get_metrics


def _create_node_from_dict(node_data: dict) -> Any:
    """Factory: Creates Node instance from dict definition."""
    node_type = node_data.get("node_type")
    node_id = node_data.get("node_id")
    config = node_data.get("config", {})

    if not node_type:
        raise ValueError("Workflow node is missing 'node_type'.")
    try:
        node_class = get_node_class(node_type)
    except AttributeError as e:
        raise ValueError(f"Unknown node type: {node_type}") from e

    return node_class(node_id=node_id, config=config)


def _resolve_execution_context_factory(
    factory: IExecutionContextFactory | None,
) -> IExecutionContextFactory:
    if factory is not None:
        return factory

    from casare_rpa.application.dependency_injection import bootstrap_di
    from casare_rpa.application.dependency_injection.container import DIContainer

    bootstrap_di(include_presentation=False)
    return cast(
        IExecutionContextFactory,
        DIContainer.get_instance().resolve("execution_context_factory"),
    )


class ExecuteWorkflowUseCase:
    """Executes workflows using Domain Orchestration and Infrastructure Context.

    Coordinates:
    - StateManager: Tracks progress/stop/pause.
    - NodeExecutor: Runs individual nodes.
    - ParallelStrategy: Handles concurrency (Forks, Run-All).
    - ResultHandler: managing routing and errors.
    """

    def __init__(
        self,
        workflow: WorkflowSchema,
        event_bus: EventBus | None = None,
        settings: ExecutionSettings | None = None,
        initial_variables: dict[str, Any] | None = None,
        project_context: Any | None = None,
        pause_event: asyncio.Event | None = None,
        execution_context_factory: IExecutionContextFactory | None = None,
    ) -> None:
        self.workflow = workflow
        self.settings = settings or ExecutionSettings()
        self._initial_variables = initial_variables or {}
        self._project_context = project_context

        if event_bus is None:
            from casare_rpa.domain.events import get_event_bus

            event_bus = get_event_bus()
        self.event_bus = event_bus

        self.orchestrator = ExecutionOrchestrator(workflow)
        self.pause_event = pause_event or asyncio.Event()
        self.pause_event.set()
        self._context_factory = _resolve_execution_context_factory(execution_context_factory)

        self.state_manager = ExecutionStateManager(
            workflow=workflow,
            orchestrator=self.orchestrator,
            event_bus=event_bus,
            settings=self.settings,
            pause_event=self.pause_event,
        )

        self.context: IExecutionContext | None = None
        self._node_instances: dict[str, Any] = {}

        # Delegates (Init in execute)
        self._node_executor: NodeExecutorWithTryCatch | None = None
        self._variable_resolver: VariableResolver | None = None
        self._error_handler: TryCatchErrorHandler | None = None
        self._parallel_strategy: ParallelExecutionStrategy | None = None
        self._result_handler: ExecutionResultHandler | None = None
        self._engine: WorkflowExecutionEngine | None = None

    # --- Backward Compat Properties ---
    @property
    def executed_nodes(self) -> set[NodeId]:
        return self.state_manager.executed_nodes

    @property
    def current_node_id(self) -> NodeId | None:
        return self.state_manager.current_node_id

    @property
    def start_time(self) -> datetime | None:
        return self.state_manager.start_time

    @property
    def end_time(self) -> datetime | None:
        return self.state_manager.end_time

    def stop(self) -> None:
        self.state_manager.stop()

    def _get_node_instance(self, node_id: str) -> Any:
        """Retrieves or creates Node instance (Cached)."""
        if node_id in self._node_instances:
            return self._node_instances[node_id]

        node_data = self.workflow.nodes.get(node_id)
        if not node_data:
            raise ValueError(f"Node {node_id} not found")

        if not isinstance(node_data, dict):
            self._node_instances[node_id] = node_data
            return node_data

        node = _create_node_from_dict(node_data)
        self._node_instances[node_id] = node
        return node

    def _store_node_outputs(self, node_id: str, node: Any) -> None:
        """Persists node outputs to context for reference (e.g. {{id.out}})."""
        if not self.context or not hasattr(node, "output_ports"):
            return

        outputs = {}
        for name, port in getattr(node, "output_ports", {}).items():
            if name.startswith("exec") or name.startswith("_exec"):
                continue
            val = port.get_value() if hasattr(port, "get_value") else None
            if val is not None:
                outputs[name] = val

        if outputs:
            self.context.set_variable(node_id, outputs)

    async def execute(self, run_all: bool = False) -> bool:
        """Executes the workflow."""
        self.state_manager.start_execution()

        # 1. Setup Infrastructure
        self.context = self._context_factory(
            workflow_name=self.workflow.metadata.name,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
            pause_event=self.pause_event,
        )

        # 2. Setup Strategies
        self._error_handler = TryCatchErrorHandler(self.context)
        self._variable_resolver = VariableResolver(self.workflow, self._get_node_instance)
        self._node_executor = NodeExecutorWithTryCatch(
            context=self.context,
            event_bus=self.event_bus,
            node_timeout=self.settings.node_timeout,
            progress_calculator=self.state_manager.calculate_progress,
            error_capturer=self._error_handler.capture_error,
        )
        self._parallel_strategy = ParallelExecutionStrategy(
            context=self.context,
            event_bus=self.event_bus,
            node_getter=self._get_node_instance,
            state_manager=self.state_manager,
            variable_resolver=self._variable_resolver,
            node_executor_factory=lambda ctx: NodeExecutor(
                ctx, self.event_bus, self.settings.node_timeout
            ),
            orchestrator=self.orchestrator,
        )
        self._result_handler = ExecutionResultHandler(
            orchestrator=self.orchestrator,
            state_manager=self.state_manager,
            error_handler=self._error_handler,
            settings=self.settings,
            parallel_strategy=self._parallel_strategy,
        )
        self._engine = WorkflowExecutionEngine(
            orchestrator=self.orchestrator,
            node_executor=self._node_executor,
            variable_resolver=self._variable_resolver,
            state_manager=self.state_manager,
            node_getter=self._get_node_instance,
            context=self.context,
            result_handler=self._result_handler,
            parallel_strategy=self._parallel_strategy,
        )

        # 3. Start
        self.state_manager.publish_event(
            WorkflowStarted(
                workflow_id=self.workflow.metadata.id,
                workflow_name=self.workflow.metadata.name,
                execution_mode=ExecutionMode.NORMAL,
                total_nodes=len(self.workflow.nodes),
            )
        )
        get_metrics().record_workflow_start(self.workflow.metadata.name)
        logger.info(f"Start: {self.workflow.metadata.name}")

        try:
            if self.settings.single_node and self.settings.target_node_id:
                await self._execute_single_node(self.settings.target_node_id)
            elif run_all:
                start_nodes = self.orchestrator.find_all_start_nodes()
                if len(start_nodes) > 1:
                    await self._parallel_strategy.execute_parallel_workflows(start_nodes)
                elif start_nodes:
                    await self._engine.run_from_node(start_nodes[0])
                else:
                    raise ValueError("No StartNode found")
            else:
                start_id = self.orchestrator.find_start_node()
                if not start_id:
                    raise ValueError("No StartNode found")
                await self._engine.run_from_node(start_id)

            return self._finalize_execution()

        except Exception as e:
            return self._handle_workflow_exception(e)
        finally:
            if self.context:
                try:
                    await asyncio.wait_for(self.context.cleanup(), 30.0)
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
            self.state_manager.set_current_node(None)

    async def _execute_single_node(self, node_id: NodeId) -> None:
        """F5 Mode: Executes target node in isolation."""
        try:
            node = self._get_node_instance(node_id)
        except ValueError as e:
            self.state_manager.mark_failed(str(e))
            return

        self._variable_resolver.transfer_inputs_to_node(node_id)
        result = await self._node_executor.execute(node)

        if result.success:
            self._store_node_outputs(node_id, node)
        else:
            self.state_manager.mark_failed(result.result.get("error", "Execution failed"))

    async def _execute_from_node(self, start_id: NodeId) -> None:
        """Execute workflow from a specific start node."""
        if self._engine is None:
            raise RuntimeError("Engine not initialized. Call execute() first.")
        await self._engine.run_from_node(start_id)

    def _finalize_execution(self) -> bool:
        self.state_manager.mark_completed()
        duration = self.state_manager.duration
        success = not self.state_manager.is_failed and not self.state_manager.is_stopped

        if self.state_manager.is_stopped:
            self.state_manager.publish_event(
                WorkflowStopped(
                    workflow_id=self.workflow.metadata.id,
                    stopped_at_node_id=self.current_node_id,
                    reason="user_request",
                )
            )
        elif success:
            self.state_manager.publish_event(
                WorkflowCompleted(
                    workflow_id=self.workflow.metadata.id,
                    workflow_name=self.workflow.metadata.name,
                    execution_time_ms=duration * 1000,
                    nodes_executed=len(self.executed_nodes),
                )
            )
        else:
            self.state_manager.publish_event(
                WorkflowFailed(
                    workflow_id=self.workflow.metadata.id,
                    workflow_name=self.workflow.metadata.name,
                    error_message=self.state_manager.execution_error or "Unknown error",
                    execution_time_ms=duration * 1000,
                )
            )

        get_metrics().record_workflow_complete(
            self.workflow.metadata.name, duration * 1000, success
        )

        return success

    def _handle_workflow_exception(self, e: Exception) -> bool:
        self.state_manager.mark_completed()
        logger.exception("Workflow Error")
        self.state_manager.publish_event(
            WorkflowFailed(
                workflow_id=self.workflow.metadata.id,
                workflow_name=self.workflow.metadata.name,
                error_message=str(e) or "Unknown error",
                execution_time_ms=self.state_manager.duration * 1000,
            )
        )
        get_metrics().record_workflow_complete(self.workflow.metadata.name, 0, False)
        return False

    # --- Result Pattern Wrappers ---
    async def execute_safe(self, run_all: bool = False) -> Result[bool, WorkflowExecutionError]:
        try:
            return Ok(await self.execute(run_all))
        except Exception as e:
            return Err(WorkflowExecutionError(str(e), self.workflow.metadata.id, original_error=e))

    def get_node_instance_safe(self, node_id: str) -> Result[Any, NodeExecutionError]:
        try:
            return Ok(self._get_node_instance(node_id))
        except Exception as e:
            return Err(NodeExecutionError("Failed to get node", node_id, original_error=e))
