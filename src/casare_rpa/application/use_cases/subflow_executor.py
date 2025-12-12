"""
CasareRPA - Subflow Executor Use Case

Executes a subflow as a single atomic unit with:
- Input mapping from external inputs to internal node inputs
- Output capture from internal node outputs to subflow outputs
- Execution context handling (variables, browser context passing)
- Progress reporting for entire subflow

Design:
- Uses NodeExecutor for individual node execution
- Uses ExecutionOrchestrator for routing decisions
- Respects ExecutionContext for browser sharing
- Emits progress events through EventBus
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.events import (
    EventBus,
    WorkflowStarted,
    WorkflowCompleted,
    WorkflowFailed,
)
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.value_objects.types import NodeId, ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.application.use_cases.node_executor import (
    NodeExecutor,
)
from casare_rpa.application.use_cases.variable_resolver import VariableResolver
from casare_rpa.utils.workflow.workflow_loader import NODE_TYPE_MAP


@dataclass
class SubflowInputDefinition:
    """Definition of a subflow input."""

    name: str
    data_type: str = "any"
    default_value: Any = None
    description: str = ""
    required: bool = False


@dataclass
class SubflowOutputDefinition:
    """Definition of a subflow output."""

    name: str
    data_type: str = "any"
    source_node_id: Optional[NodeId] = None
    source_port: Optional[str] = None
    description: str = ""


@dataclass
class Subflow:
    """
    Represents a subflow - a reusable workflow component.

    Subflows encapsulate a group of nodes that can be executed as a single
    atomic unit with defined inputs and outputs.
    """

    workflow: WorkflowSchema
    inputs: List[SubflowInputDefinition] = field(default_factory=list)
    outputs: List[SubflowOutputDefinition] = field(default_factory=list)
    name: str = "Subflow"
    description: str = ""

    def get_input_names(self) -> List[str]:
        """Get list of input names."""
        return [inp.name for inp in self.inputs]

    def get_output_names(self) -> List[str]:
        """Get list of output names."""
        return [out.name for out in self.outputs]

    def get_required_inputs(self) -> List[str]:
        """Get list of required input names."""
        return [inp.name for inp in self.inputs if inp.required]

    def __repr__(self) -> str:
        return (
            f"Subflow(name='{self.name}', "
            f"inputs={len(self.inputs)}, "
            f"outputs={len(self.outputs)}, "
            f"nodes={len(self.workflow.nodes)})"
        )


@dataclass
class SubflowExecutionResult:
    """Result of subflow execution."""

    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    nodes_executed: int = 0
    error: Optional[str] = None
    error_node_id: Optional[NodeId] = None

    @classmethod
    def success_result(
        cls,
        outputs: Dict[str, Any],
        execution_time: float,
        nodes_executed: int,
    ) -> "SubflowExecutionResult":
        """Create a success result."""
        return cls(
            success=True,
            outputs=outputs,
            execution_time=execution_time,
            nodes_executed=nodes_executed,
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        execution_time: float,
        nodes_executed: int = 0,
        error_node_id: Optional[NodeId] = None,
    ) -> "SubflowExecutionResult":
        """Create an error result."""
        return cls(
            success=False,
            error=error,
            execution_time=execution_time,
            nodes_executed=nodes_executed,
            error_node_id=error_node_id,
        )


def _create_node_from_dict(node_data: dict) -> Any:
    """
    Create a node instance from a dict definition.

    Args:
        node_data: Dict with node_id, type, and optional config

    Returns:
        Node instance

    Raises:
        ValueError: If node type is unknown
    """
    node_type = node_data.get("type") or node_data.get("node_type")
    node_id = node_data.get("node_id")
    config = node_data.get("config", {})

    node_class = NODE_TYPE_MAP.get(node_type)
    if not node_class:
        raise ValueError(f"Unknown node type: {node_type}")

    return node_class(node_id=node_id, config=config)


class SubflowExecutor:
    """
    Executes a subflow as a single atomic unit.

    Responsibilities:
    - Validate inputs match subflow input definitions
    - Create internal variable scope with input values
    - Find start node(s) within subflow
    - Execute nodes in topological order
    - Collect output values from designated output ports
    - Return combined SubflowExecutionResult

    Integration:
    - Uses existing NodeExecutor for individual nodes
    - Respects ExecutionContext for browser sharing
    - Emits progress events through EventBus
    - Handles errors with proper cleanup
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        node_timeout: float = 120.0,
    ) -> None:
        """
        Initialize subflow executor.

        Args:
            event_bus: Optional event bus for progress events
            node_timeout: Timeout for individual node execution in seconds
        """
        if event_bus is None:
            from casare_rpa.domain.events import get_event_bus

            event_bus = get_event_bus()

        self.event_bus = event_bus
        self.node_timeout = node_timeout

        # Execution state (reset per execute call)
        self._node_instances: Dict[str, Any] = {}
        self._executed_nodes: Set[NodeId] = set()
        self._current_subflow: Optional[Subflow] = None

    def _publish_workflow_started(
        self,
        subflow_name: str,
        total_nodes: int,
        inputs: List[str],
    ) -> None:
        """Publish workflow started event for subflow."""
        if self.event_bus:
            from casare_rpa.domain.events import WorkflowStarted

            self.event_bus.publish(
                WorkflowStarted(
                    workflow_id=f"subflow_{subflow_name}",
                    workflow_name=subflow_name,
                    execution_mode=ExecutionMode.NORMAL,
                    total_nodes=total_nodes,
                )
            )

    def _publish_workflow_completed(
        self,
        subflow_name: str,
        nodes_executed: int,
        duration: float,
        outputs: List[str],
    ) -> None:
        """Publish workflow completed event for subflow."""
        if self.event_bus:
            from casare_rpa.domain.events import WorkflowCompleted

            self.event_bus.publish(
                WorkflowCompleted(
                    workflow_id=f"subflow_{subflow_name}",
                    workflow_name=subflow_name,
                    execution_time_ms=duration * 1000,
                    nodes_executed=nodes_executed,
                )
            )

    def _publish_workflow_failed(
        self,
        subflow_name: str,
        error: str,
        nodes_executed: int,
        error_node_id: Optional[str] = None,
    ) -> None:
        """Publish workflow failed event for subflow."""
        if self.event_bus:
            from casare_rpa.domain.events import WorkflowFailed

            self.event_bus.publish(
                WorkflowFailed(
                    workflow_id=f"subflow_{subflow_name}",
                    workflow_name=subflow_name,
                    error_message=error,
                    failed_node_id=error_node_id,
                )
            )

    async def execute(
        self,
        subflow: Subflow,
        inputs: Dict[str, Any],
        context: ExecutionContext,
        param_values: Optional[Dict[str, Any]] = None,
    ) -> SubflowExecutionResult:
        """
        Execute subflow with given inputs.

        Args:
            subflow: Subflow to execute
            inputs: Input values mapped by name
            context: Execution context (browser, variables, resources)
            param_values: Optional promoted parameter values (from SubflowNode config)

        Returns:
            SubflowExecutionResult with success status and output values
        """
        start_time = time.time()
        self._current_subflow = subflow
        self._node_instances.clear()
        self._executed_nodes.clear()

        logger.info(f"Starting subflow execution: {subflow.name}")
        self._publish_workflow_started(
            subflow_name=subflow.name,
            total_nodes=len(subflow.workflow.nodes),
            inputs=list(inputs.keys()),
        )

        try:
            # Step 1: Validate inputs match subflow input definitions
            validation_error = self._validate_inputs(subflow, inputs)
            if validation_error:
                logger.error(f"Subflow input validation failed: {validation_error}")
                return SubflowExecutionResult.error_result(
                    error=validation_error,
                    execution_time=time.time() - start_time,
                )

            # Step 2: Create internal variable scope with input values
            internal_context = self._create_internal_context(subflow, inputs, context)

            # Step 2.5: Inject promoted parameters if provided
            if param_values:
                self._inject_promoted_parameters(
                    subflow, param_values, internal_context
                )

            # Step 3: Find start node(s) within subflow
            orchestrator = ExecutionOrchestrator(subflow.workflow)
            start_node_id = orchestrator.find_start_node()

            if not start_node_id:
                # Try to find nodes with no incoming execution connections
                start_node_id = self._find_entry_node(subflow, orchestrator)

            if not start_node_id:
                return SubflowExecutionResult.error_result(
                    error="No start node found in subflow",
                    execution_time=time.time() - start_time,
                )

            # Step 4: Execute nodes in topological order
            variable_resolver = VariableResolver(
                workflow=subflow.workflow,
                node_getter=self._get_node_instance,
            )

            node_executor = NodeExecutor(
                context=internal_context,
                event_bus=self.event_bus,
                node_timeout=self.node_timeout,
                progress_calculator=lambda: self._calculate_progress(subflow),
            )

            execution_error = await self._execute_nodes(
                start_node_id=start_node_id,
                orchestrator=orchestrator,
                node_executor=node_executor,
                variable_resolver=variable_resolver,
                context=internal_context,
            )

            if execution_error:
                execution_time = time.time() - start_time
                self._publish_workflow_failed(
                    subflow_name=subflow.name,
                    error=execution_error[0],
                    nodes_executed=len(self._executed_nodes),
                    error_node_id=execution_error[1],
                )
                return SubflowExecutionResult.error_result(
                    error=execution_error[0],
                    execution_time=execution_time,
                    nodes_executed=len(self._executed_nodes),
                    error_node_id=execution_error[1],
                )

            # Step 5: Collect output values from designated output ports
            outputs = self._collect_outputs(subflow, internal_context)

            execution_time = time.time() - start_time
            logger.info(
                f"Subflow {subflow.name} completed successfully in {execution_time:.2f}s "
                f"({len(self._executed_nodes)} nodes)"
            )

            self._publish_workflow_completed(
                subflow_name=subflow.name,
                nodes_executed=len(self._executed_nodes),
                duration=execution_time,
                outputs=list(outputs.keys()),
            )

            return SubflowExecutionResult.success_result(
                outputs=outputs,
                execution_time=execution_time,
                nodes_executed=len(self._executed_nodes),
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            logger.exception(f"Subflow execution failed with exception: {subflow.name}")

            self._publish_workflow_failed(
                subflow_name=subflow.name,
                error=error_msg,
                nodes_executed=len(self._executed_nodes),
            )

            return SubflowExecutionResult.error_result(
                error=error_msg,
                execution_time=execution_time,
                nodes_executed=len(self._executed_nodes),
            )

        finally:
            self._current_subflow = None

    def _validate_inputs(
        self,
        subflow: Subflow,
        inputs: Dict[str, Any],
    ) -> Optional[str]:
        """
        Validate that provided inputs match subflow input definitions.

        Args:
            subflow: Subflow with input definitions
            inputs: Provided input values

        Returns:
            Error message if validation fails, None if valid
        """
        # Check required inputs are provided
        required_inputs = subflow.get_required_inputs()
        for req_input in required_inputs:
            if req_input not in inputs:
                return f"Missing required input: {req_input}"

        # Validate input names are defined (warn for unexpected inputs)
        defined_inputs = set(subflow.get_input_names())
        for input_name in inputs:
            if input_name not in defined_inputs:
                logger.warning(
                    f"Unexpected input '{input_name}' provided to subflow "
                    f"'{subflow.name}' - will be ignored"
                )

        return None

    def _create_internal_context(
        self,
        subflow: Subflow,
        inputs: Dict[str, Any],
        parent_context: ExecutionContext,
    ) -> ExecutionContext:
        """
        Create internal variable scope for subflow execution.

        The internal context:
        - Inherits browser resources from parent (shared)
        - Has its own variable namespace (isolated)
        - Receives input values as variables

        Args:
            subflow: Subflow being executed
            inputs: Input values to inject
            parent_context: Parent execution context

        Returns:
            New ExecutionContext for internal execution
        """
        # Create isolated context with shared browser resources
        internal_context = parent_context.clone_for_branch(f"subflow_{subflow.name}")

        # Inject input values as variables
        for input_def in subflow.inputs:
            if input_def.name in inputs:
                value = inputs[input_def.name]
            elif input_def.default_value is not None:
                value = input_def.default_value
            else:
                value = None

            if value is not None:
                internal_context.set_variable(input_def.name, value)
                logger.debug(f"Subflow input: {input_def.name} = {repr(value)[:80]}")

        # Store subflow metadata for debugging
        internal_context.set_variable("_subflow_name", subflow.name)

        return internal_context

    def _inject_promoted_parameters(
        self,
        subflow: Subflow,
        param_values: Dict[str, Any],
        context: ExecutionContext,
    ) -> None:
        """
        Inject promoted parameter values into internal nodes before execution.

        Promoted parameters allow users to configure internal node properties
        from the subflow level, without opening the subflow editor.

        Args:
            subflow: Subflow being executed
            param_values: Values for promoted parameters (from SubflowNode config)
            context: Execution context for variable resolution
        """
        # Check if subflow has parameters attribute (backward compatibility)
        if not hasattr(subflow, "parameters") or not subflow.parameters:
            return

        # Note: This executor uses SubflowExecutor.Subflow (local dataclass),
        # but the domain entity Subflow has the parameters. We need to handle both.
        parameters = getattr(subflow, "parameters", [])
        if not parameters:
            return

        for param in parameters:
            # Determine value with precedence: user input > subflow default > node default
            value = param_values.get(param.name)
            if value is None:
                value = getattr(param, "default_value", None)

            if value is None:
                continue  # No value to inject, let node use its own default

            # Handle variable references like ${variable_name}
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                var_name = value[2:-1]
                resolved = context.get_variable(var_name)
                if resolved is not None:
                    value = resolved

            # Handle nested subflow chains (param.chain = ["nested_subflow_id", "nested_param_name"])
            chain = getattr(param, "chain", None)
            if chain and len(chain) >= 2:
                # Store for nested subflow to pick up later
                context.set_variable(f"_promoted_{param.name}", value)
                logger.debug(
                    f"Stored chained param '{param.name}' = {repr(value)[:50]} for nested resolution"
                )
                continue

            # Get internal node and inject value into its config
            internal_node_id = getattr(param, "internal_node_id", "")
            internal_property_name = getattr(param, "internal_property_name", "")

            if not internal_node_id or not internal_property_name:
                continue

            if internal_node_id in self._node_instances:
                # Node already instantiated - inject directly
                node = self._node_instances[internal_node_id]
                if hasattr(node, "config") and isinstance(node.config, dict):
                    node.config[internal_property_name] = value
                    logger.debug(
                        f"Injected promoted param '{getattr(param, 'display_name', param.name)}' = {repr(value)[:50]} "
                        f"into {internal_node_id}.{internal_property_name}"
                    )
            else:
                # Node not yet instantiated - store in context for lazy injection
                context.set_variable(
                    f"_promoted_{internal_node_id}_{internal_property_name}", value
                )
                logger.debug(
                    f"Stored promoted param '{getattr(param, 'display_name', param.name)}' = {repr(value)[:50]} "
                    f"for lazy injection into {internal_node_id}.{internal_property_name}"
                )

    def _find_entry_node(
        self,
        subflow: Subflow,
        orchestrator: ExecutionOrchestrator,
    ) -> Optional[NodeId]:
        """
        Find entry node when no explicit StartNode exists.

        Finds nodes with no incoming execution connections.

        Args:
            subflow: Subflow to analyze
            orchestrator: Execution orchestrator

        Returns:
            Node ID of entry node or None
        """
        # Get all nodes that have incoming exec connections
        nodes_with_incoming_exec: Set[NodeId] = set()
        for conn in subflow.workflow.connections:
            if "exec" in conn.target_port.lower():
                nodes_with_incoming_exec.add(conn.target_node)

        # Find nodes without incoming exec connections
        for node_id in subflow.workflow.nodes:
            if node_id not in nodes_with_incoming_exec:
                logger.debug(f"Found entry node without incoming exec: {node_id}")
                return node_id

        return None

    def _get_node_instance(self, node_id: str) -> Any:
        """
        Get or create a node instance.

        Args:
            node_id: ID of the node to get

        Returns:
            Node instance

        Raises:
            ValueError: If node not found
        """
        if node_id in self._node_instances:
            return self._node_instances[node_id]

        if self._current_subflow is None:
            raise ValueError(f"Node {node_id} not found - no active subflow")

        node_data = self._current_subflow.workflow.nodes.get(node_id)
        if not node_data:
            raise ValueError(f"Node {node_id} not found in subflow")

        if not isinstance(node_data, dict):
            self._node_instances[node_id] = node_data
            return node_data

        node = _create_node_from_dict(node_data)
        self._node_instances[node_id] = node
        return node

    def _calculate_progress(self, subflow: Subflow) -> float:
        """Calculate execution progress as percentage."""
        total = len(subflow.workflow.nodes)
        if total == 0:
            return 100.0
        return (len(self._executed_nodes) / total) * 100.0

    async def _execute_nodes(
        self,
        start_node_id: NodeId,
        orchestrator: ExecutionOrchestrator,
        node_executor: NodeExecutor,
        variable_resolver: VariableResolver,
        context: ExecutionContext,
    ) -> Optional[tuple[str, Optional[NodeId]]]:
        """
        Execute nodes starting from start_node_id.

        Args:
            start_node_id: Node ID to start from
            orchestrator: Execution orchestrator for routing
            node_executor: Node executor for individual nodes
            variable_resolver: For data transfer between nodes
            context: Execution context

        Returns:
            Tuple of (error_message, error_node_id) if failed, None if success
        """
        nodes_to_execute: deque[NodeId] = deque([start_node_id])

        while nodes_to_execute and not context.is_stopped():
            current_node_id = nodes_to_execute.popleft()

            # Skip if already executed (except control flow nodes)
            is_control_flow = orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in self._executed_nodes and not is_control_flow:
                continue

            # Get node instance
            try:
                node = self._get_node_instance(current_node_id)
            except ValueError as e:
                return (str(e), current_node_id)

            # Transfer data from connected input ports
            variable_resolver.transfer_inputs_to_node(current_node_id)

            # Execute the node
            exec_result = await node_executor.execute(node)

            if not exec_result.success:
                error_msg = (
                    exec_result.result.get("error", "Unknown error")
                    if exec_result.result
                    else "Node execution failed"
                )
                return (error_msg, current_node_id)

            # Mark as executed
            self._executed_nodes.add(current_node_id)

            # Store node outputs in context
            self._store_node_outputs(current_node_id, node, context)

            # Handle loop_back_to
            if exec_result.result and "loop_back_to" in exec_result.result:
                loop_start_id = exec_result.result["loop_back_to"]
                # Clear loop body nodes for re-execution
                body_nodes = orchestrator.find_loop_body_nodes(
                    loop_start_id, current_node_id
                )
                for body_node_id in body_nodes:
                    self._executed_nodes.discard(body_node_id)
                nodes_to_execute.appendleft(loop_start_id)
                continue

            # Get next nodes
            next_node_ids = orchestrator.get_next_nodes(
                current_node_id, exec_result.result
            )
            for next_id in next_node_ids:
                if next_id not in nodes_to_execute:
                    nodes_to_execute.append(next_id)

        # Check if stopped
        if context.is_stopped():
            return ("Execution stopped by user", None)

        return None

    def _store_node_outputs(
        self,
        node_id: str,
        node: Any,
        context: ExecutionContext,
    ) -> None:
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
            context.set_variable(node_id, data_outputs)

    def _collect_outputs(
        self,
        subflow: Subflow,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """
        Collect output values from designated output ports.

        Args:
            subflow: Subflow with output definitions
            context: Execution context with variables

        Returns:
            Dictionary of output name -> value
        """
        outputs: Dict[str, Any] = {}

        for output_def in subflow.outputs:
            value = None

            # Try to get from specified source node/port
            if output_def.source_node_id and output_def.source_port:
                node_outputs = context.get_variable(output_def.source_node_id)
                if isinstance(node_outputs, dict):
                    value = node_outputs.get(output_def.source_port)
                elif node_outputs is not None:
                    value = node_outputs

            # If no source specified or not found, try variable with output name
            if value is None:
                value = context.get_variable(output_def.name)

            if value is not None:
                outputs[output_def.name] = value
                logger.debug(f"Subflow output: {output_def.name} = {repr(value)[:80]}")
            else:
                logger.warning(
                    f"Subflow output '{output_def.name}' has no value "
                    f"(source: {output_def.source_node_id}.{output_def.source_port})"
                )

        return outputs

    def __repr__(self) -> str:
        return f"SubflowExecutor(node_timeout={self.node_timeout})"


__all__ = [
    "Subflow",
    "SubflowInputDefinition",
    "SubflowOutputDefinition",
    "SubflowExecutionResult",
    "SubflowExecutor",
]
