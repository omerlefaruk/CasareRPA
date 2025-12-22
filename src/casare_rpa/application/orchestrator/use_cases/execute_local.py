"""ExecuteLocalUseCase - Execute workflow locally without orchestrator.

This use case provides direct local execution of workflows, bypassing the
orchestrator and job queue. Useful for:
- Canvas "Run" button (F5)
- Testing and development
- Single-machine execution
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.events import EventBus


class ExecutionResult:
    """Result from local workflow execution.

    Encapsulates the execution outcome including success status,
    output variables, error information, and timing data.
    """

    def __init__(
        self,
        success: bool,
        workflow_name: str,
        variables: Dict[str, Any],
        error: Optional[str] = None,
        executed_nodes: int = 0,
        total_nodes: int = 0,
        duration_ms: int = 0,
    ) -> None:
        """Initialize execution result.

        Args:
            success: Whether execution completed successfully.
            workflow_name: Name of the executed workflow.
            variables: Final workflow variables after execution.
            error: Error message if execution failed.
            executed_nodes: Number of nodes executed.
            total_nodes: Total number of nodes in workflow.
            duration_ms: Execution duration in milliseconds.
        """
        self.success = success
        self.workflow_name = workflow_name
        self.variables = variables
        self.error = error
        self.executed_nodes = executed_nodes
        self.total_nodes = total_nodes
        self.duration_ms = duration_ms

    @property
    def progress(self) -> float:
        """Get execution progress percentage.

        Returns:
            Progress as percentage (0-100).
        """
        if self.total_nodes == 0:
            return 100.0 if self.success else 0.0
        return (self.executed_nodes / self.total_nodes) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation of execution result.
        """
        return {
            "success": self.success,
            "workflow_name": self.workflow_name,
            "variables": self.variables,
            "error": self.error,
            "executed_nodes": self.executed_nodes,
            "total_nodes": self.total_nodes,
            "duration_ms": self.duration_ms,
            "progress": self.progress,
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"ExecutionResult({status}, workflow={self.workflow_name!r}, "
            f"progress={self.progress:.1f}%)"
        )


class ExecuteLocalUseCase:
    """Use case for executing workflows locally.

    This is a thin wrapper around ExecuteWorkflowUseCase that provides
    a simpler interface for local execution without creating Job entities
    or interacting with the orchestrator infrastructure.

    Use this when:
    - Running workflows from the Canvas UI
    - Testing workflows locally
    - Single-machine execution without cloud orchestration
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize local execution use case.

        Args:
            event_bus: Optional event bus for progress updates.
        """
        self._event_bus = event_bus

    async def execute(
        self,
        workflow_data: Dict[str, Any],
        variables: Optional[Dict[str, Any]] = None,
        run_to_node_id: Optional[str] = None,
        single_node: bool = False,
        continue_on_error: bool = False,
        node_timeout: float = 120.0,
    ) -> ExecutionResult:
        """Execute a workflow locally.

        This method does NOT create a Job entity - it performs direct execution.
        Progress updates are emitted via the event bus.

        Args:
            workflow_data: Serialized workflow dictionary.
            variables: Optional initial variables for execution.
            run_to_node_id: Optional target node ID for partial execution.
                If set, executes only nodes on the path to this node (F4 mode).
            single_node: If True and run_to_node_id is set, execute only that
                single node (F5 mode on single node).
            continue_on_error: Whether to continue execution after node errors.
            node_timeout: Timeout for individual node execution in seconds.

        Returns:
            ExecutionResult containing outcome and data.

        Raises:
            ValueError: If workflow_data is invalid.
        """
        logger.info("Starting local workflow execution")

        # Validate workflow data
        if not workflow_data:
            raise ValueError("workflow_data cannot be empty")

        # Parse workflow data into WorkflowSchema
        try:
            workflow = self._parse_workflow(workflow_data)
        except Exception as e:
            logger.error(f"Failed to parse workflow: {e}")
            return ExecutionResult(
                success=False,
                workflow_name=workflow_data.get("metadata", {}).get("name", "Unknown"),
                variables=variables or {},
                error=f"Failed to parse workflow: {e}",
            )

        # Configure execution settings
        settings = ExecutionSettings(
            continue_on_error=continue_on_error,
            node_timeout=node_timeout,
            target_node_id=run_to_node_id,
            single_node=single_node,
        )

        # Create and execute the workflow
        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=self._event_bus,
            settings=settings,
            initial_variables=variables,
        )

        try:
            success = await use_case.execute()

            # Extract final variables from context
            final_variables: Dict[str, Any] = {}
            if use_case.context:
                final_variables = dict(use_case.context.variables)

            # Calculate duration
            duration_ms = 0
            if use_case.start_time and use_case.end_time:
                duration_ms = int((use_case.end_time - use_case.start_time).total_seconds() * 1000)

            return ExecutionResult(
                success=success,
                workflow_name=workflow.metadata.name,
                variables=final_variables,
                error=None if success else "Execution failed",
                executed_nodes=len(use_case.executed_nodes),
                total_nodes=len(workflow.nodes),
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.exception(f"Local execution failed: {e}")
            return ExecutionResult(
                success=False,
                workflow_name=workflow.metadata.name,
                variables=variables or {},
                error=str(e),
                executed_nodes=len(use_case.executed_nodes),
                total_nodes=len(workflow.nodes),
            )

    async def execute_from_json(
        self,
        workflow_json: str,
        variables: Optional[Dict[str, Any]] = None,
        run_to_node_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a workflow from JSON string.

        Convenience method that parses JSON before execution.

        Args:
            workflow_json: JSON string of workflow data.
            variables: Optional initial variables.
            run_to_node_id: Optional target node for partial execution.

        Returns:
            ExecutionResult containing outcome and data.

        Raises:
            ValueError: If JSON is invalid.
        """
        import orjson

        try:
            workflow_data = orjson.loads(workflow_json)
        except Exception as e:
            logger.error(f"Failed to parse workflow JSON: {e}")
            return ExecutionResult(
                success=False,
                workflow_name="Unknown",
                variables=variables or {},
                error=f"Invalid JSON: {e}",
            )

        return await self.execute(
            workflow_data=workflow_data,
            variables=variables,
            run_to_node_id=run_to_node_id,
        )

    def _parse_workflow(self, workflow_data: Dict[str, Any]) -> WorkflowSchema:
        """Parse workflow data into WorkflowSchema.

        Args:
            workflow_data: Dictionary containing workflow definition.

        Returns:
            WorkflowSchema instance.

        Raises:
            ValueError: If workflow data is invalid.
        """
        if "metadata" in workflow_data and "nodes" in workflow_data:
            return WorkflowSchema.from_dict(workflow_data)

        raise ValueError("Invalid workflow data format (expected metadata + nodes)")


__all__ = ["ExecuteLocalUseCase", "ExecutionResult"]
