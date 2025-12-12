"""
Infrastructure SubworkflowExecutor for CallSubworkflowNode.

Provides execution capabilities for subworkflows called from CallSubworkflowNode.
Handles:
- Context isolation with parent context reference sharing
- Recursion depth tracking
- Timeout management
- Resource cleanup
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from loguru import logger

from casare_rpa.domain.entities.subflow import Subflow
from casare_rpa.domain.value_objects.types import DataType, NodeId
from casare_rpa.infrastructure.execution import ExecutionContext


MAX_RECURSION_DEPTH = 10


@dataclass
class SubworkflowExecutionResult:
    """Result of subworkflow execution."""

    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_node_id: Optional[str] = None
    execution_time_ms: int = 0
    nodes_executed: int = 0

    @classmethod
    def success_result(
        cls,
        outputs: Dict[str, Any],
        execution_time_ms: int,
        nodes_executed: int,
    ) -> "SubworkflowExecutionResult":
        """Create success result."""
        return cls(
            success=True,
            outputs=outputs,
            execution_time_ms=execution_time_ms,
            nodes_executed=nodes_executed,
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        execution_time_ms: int = 0,
        nodes_executed: int = 0,
        error_node_id: Optional[str] = None,
    ) -> "SubworkflowExecutionResult":
        """Create error result."""
        return cls(
            success=False,
            error=error,
            error_node_id=error_node_id,
            execution_time_ms=execution_time_ms,
            nodes_executed=nodes_executed,
        )


class SubworkflowExecutor:
    """
    Executes subworkflows with proper context isolation and recursion tracking.

    This executor is used by CallSubworkflowNode for sync execution mode.
    For async mode, jobs are submitted to the orchestrator job queue.

    Features:
    - Creates child context with isolated variables
    - Shares browser resources from parent
    - Tracks recursion depth to prevent infinite loops
    - Provides timeout handling
    - Maps inputs/outputs between contexts

    Usage:
        executor = SubworkflowExecutor()
        result = await executor.execute(
            subworkflow=subflow,
            inputs={"url": "https://example.com"},
            parent_context=context,
            call_depth=1,
        )
    """

    def __init__(self, node_timeout: float = 120.0) -> None:
        """
        Initialize executor.

        Args:
            node_timeout: Default timeout for individual node execution
        """
        self.node_timeout = node_timeout
        self._executed_nodes: Set[NodeId] = set()
        self._node_instances: Dict[str, Any] = {}

    async def execute(
        self,
        subworkflow: Subflow,
        inputs: Dict[str, Any],
        parent_context: ExecutionContext,
        call_depth: int = 0,
        param_values: Optional[Dict[str, Any]] = None,
    ) -> SubworkflowExecutionResult:
        """
        Execute subworkflow with given inputs.

        Args:
            subworkflow: Subworkflow entity to execute
            inputs: Input values mapped by port name
            parent_context: Parent execution context
            call_depth: Current recursion depth
            param_values: Optional promoted parameter values

        Returns:
            SubworkflowExecutionResult with outputs or error
        """
        start_time = time.time()

        # Check recursion depth
        if call_depth >= MAX_RECURSION_DEPTH:
            return SubworkflowExecutionResult.error_result(
                f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded",
                execution_time_ms=0,
            )

        logger.info(f"Executing subworkflow '{subworkflow.name}' (depth={call_depth})")

        try:
            # Validate inputs
            validation_error = self._validate_inputs(subworkflow, inputs)
            if validation_error:
                return SubworkflowExecutionResult.error_result(
                    validation_error,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            # Create child execution context
            child_context = self._create_child_context(
                subworkflow, inputs, parent_context, call_depth
            )

            # Inject promoted parameters if provided
            if param_values:
                self._inject_parameters(param_values, child_context)

            # Execute the subworkflow nodes
            execution_result = await self._execute_workflow(subworkflow, child_context)

            if not execution_result["success"]:
                return SubworkflowExecutionResult.error_result(
                    execution_result.get("error", "Subworkflow execution failed"),
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    nodes_executed=len(self._executed_nodes),
                    error_node_id=execution_result.get("error_node_id"),
                )

            # Collect outputs
            outputs = self._collect_outputs(subworkflow, child_context)

            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Subworkflow '{subworkflow.name}' completed in {execution_time_ms}ms "
                f"({len(self._executed_nodes)} nodes)"
            )

            return SubworkflowExecutionResult.success_result(
                outputs=outputs,
                execution_time_ms=execution_time_ms,
                nodes_executed=len(self._executed_nodes),
            )

        except asyncio.CancelledError:
            logger.warning(f"Subworkflow '{subworkflow.name}' cancelled")
            raise

        except Exception as e:
            logger.exception(f"Subworkflow execution error: {e}")
            return SubworkflowExecutionResult.error_result(
                str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
                nodes_executed=len(self._executed_nodes),
            )

        finally:
            self._executed_nodes.clear()
            self._node_instances.clear()

    def _validate_inputs(
        self, subworkflow: Subflow, inputs: Dict[str, Any]
    ) -> Optional[str]:
        """Validate inputs against subworkflow interface."""
        for port in subworkflow.inputs:
            if port.required and port.name not in inputs:
                # Check default value
                if port.default_value is None:
                    return f"Missing required input: {port.name}"
        return None

    def _create_child_context(
        self,
        subworkflow: Subflow,
        inputs: Dict[str, Any],
        parent_context: ExecutionContext,
        call_depth: int,
    ) -> ExecutionContext:
        """
        Create isolated child context for subworkflow execution.

        The child context:
        - Has isolated variables (copy from parent + inputs)
        - Shares browser resources from parent
        - Tracks call depth for recursion prevention
        """
        # Clone context with isolated variables
        child_context = parent_context.clone_for_branch(f"subworkflow_{subworkflow.id}")

        # Set call depth tracking
        child_context.set_variable("_subworkflow_call_depth", call_depth + 1)
        child_context.set_variable("_parent_workflow", parent_context.workflow_name)
        child_context.set_variable("_subworkflow_name", subworkflow.name)

        # Inject input values as variables
        for port in subworkflow.inputs:
            if port.name in inputs:
                child_context.set_variable(port.name, inputs[port.name])
            elif port.default_value is not None:
                child_context.set_variable(port.name, port.default_value)

        return child_context

    def _inject_parameters(
        self, param_values: Dict[str, Any], context: ExecutionContext
    ) -> None:
        """Inject promoted parameter values into context."""
        for name, value in param_values.items():
            context.set_variable(name, value)
            logger.debug(f"Injected parameter '{name}' = {repr(value)[:50]}")

    async def _execute_workflow(
        self, subworkflow: Subflow, context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute the subworkflow's nodes.

        Uses the application layer SubflowExecutor for actual node execution.
        """
        try:
            from casare_rpa.application.use_cases.subflow_executor import (
                SubflowExecutor as AppSubflowExecutor,
                Subflow as SubflowData,
                SubflowInputDefinition,
                SubflowOutputDefinition,
            )
            from casare_rpa.domain.entities.workflow import WorkflowSchema
            from casare_rpa.domain.entities.node_connection import NodeConnection

            # Build WorkflowSchema
            workflow_schema = WorkflowSchema()
            workflow_schema.nodes = subworkflow.nodes

            # Convert connections
            connections = []
            for conn_data in subworkflow.connections:
                if isinstance(conn_data, dict):
                    connections.append(
                        NodeConnection(
                            source_node=conn_data.get("source_node", ""),
                            source_port=conn_data.get("source_port", ""),
                            target_node=conn_data.get("target_node", ""),
                            target_port=conn_data.get("target_port", ""),
                        )
                    )
                elif isinstance(conn_data, NodeConnection):
                    connections.append(conn_data)
            workflow_schema.connections = connections

            # Build input/output definitions
            input_defs = [
                SubflowInputDefinition(
                    name=p.name,
                    data_type=self._data_type_to_str(p.data_type),
                    required=p.required,
                    default_value=p.default_value,
                )
                for p in subworkflow.inputs
            ]

            output_defs = [
                SubflowOutputDefinition(
                    name=p.name,
                    data_type=self._data_type_to_str(p.data_type),
                    source_node_id=p.internal_node_id if p.internal_node_id else None,
                    source_port=p.internal_port_name if p.internal_port_name else None,
                )
                for p in subworkflow.outputs
            ]

            # Create SubflowData
            subflow_data = SubflowData(
                workflow=workflow_schema,
                inputs=input_defs,
                outputs=output_defs,
                name=subworkflow.name,
            )

            # Collect inputs from context
            inputs = {}
            for input_def in input_defs:
                value = context.get_variable(input_def.name)
                if value is not None:
                    inputs[input_def.name] = value

            # Execute
            executor = AppSubflowExecutor(node_timeout=self.node_timeout)
            result = await executor.execute(subflow_data, inputs, context)

            self._executed_nodes = executor._executed_nodes.copy()

            if result.success:
                return {"success": True, "data": result.outputs}
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "error_node_id": result.error_node_id,
                }

        except ImportError as e:
            logger.error(f"Required module not available: {e}")
            return {"success": False, "error": f"Module import error: {e}"}
        except Exception as e:
            logger.exception(f"Workflow execution error: {e}")
            return {"success": False, "error": str(e)}

    def _data_type_to_str(self, data_type: Any) -> str:
        """Convert DataType to string."""
        if isinstance(data_type, DataType):
            return data_type.name
        if isinstance(data_type, str):
            return data_type.upper()
        return "ANY"

    def _collect_outputs(
        self, subworkflow: Subflow, context: ExecutionContext
    ) -> Dict[str, Any]:
        """Collect output values from context."""
        outputs = {}

        for port in subworkflow.outputs:
            value = None

            # Try to get from specified source
            if port.internal_node_id and port.internal_port_name:
                node_outputs = context.get_variable(port.internal_node_id)
                if isinstance(node_outputs, dict):
                    value = node_outputs.get(port.internal_port_name)

            # Fall back to variable with port name
            if value is None:
                value = context.get_variable(port.name)

            if value is not None:
                outputs[port.name] = value

        return outputs


__all__ = ["SubworkflowExecutor", "SubworkflowExecutionResult"]
