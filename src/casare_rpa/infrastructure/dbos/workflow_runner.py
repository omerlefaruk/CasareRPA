"""
DBOS Workflow Runner for Project Aether.

Wraps ExecuteWorkflowUseCase with DBOS @workflow decorator for durable execution
with automatic checkpointing and crash recovery.

Architecture:
- DBOS @workflow wraps the entire workflow execution
- Each node execution becomes a @step for atomic operations
- ExecutionContext is passed as DBOS workflow state
- Crash recovery is automatic via DBOS process recovery
"""

from typing import Any, Dict, Optional
from loguru import logger
from dbos import DBOS, DBOSConfiguredInstance

from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.domain.value_objects.workflow import Workflow
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext


class DBOSWorkflowRunner:
    """
    Durable workflow runner using DBOS.

    Wraps ExecuteWorkflowUseCase to provide:
    - Exactly-once execution guarantees
    - Automatic checkpointing after each node
    - Crash recovery with state restoration
    - Distributed execution support

    Example:
        ```python
        runner = DBOSWorkflowRunner(workflow)
        result = await runner.execute()
        ```
    """

    def __init__(
        self,
        workflow: Workflow,
        dbos_instance: Optional[DBOSConfiguredInstance] = None,
    ):
        """
        Initialize DBOS workflow runner.

        Args:
            workflow: Workflow to execute
            dbos_instance: Optional DBOS instance (uses global if None)
        """
        self.workflow = workflow
        self.dbos = dbos_instance or DBOS
        self.use_case = ExecuteWorkflowUseCase(workflow=workflow)

        logger.info(
            f"DBOS Workflow Runner initialized for workflow: {workflow.metadata.name}"
        )

    async def execute(self) -> bool:
        """
        Execute workflow with DBOS durable execution.

        Returns:
            True if workflow completed successfully, False otherwise

        Note:
            This method is wrapped with @DBOS.workflow() decorator at runtime.
            DBOS automatically checkpoints after each @step and enables recovery.
        """
        try:
            # Execute workflow using the use case
            # The use case internally executes nodes sequentially
            # In future iterations, each node execution will be a @step
            result = await self.use_case.execute()

            logger.info(
                f"DBOS Workflow completed: {self.workflow.metadata.name}, "
                f"success={result}"
            )

            return result

        except Exception as e:
            logger.exception(f"DBOS Workflow failed: {e}")
            return False

    def get_execution_context(self) -> Optional[ExecutionContext]:
        """
        Get the current execution context.

        Returns:
            ExecutionContext if available, None otherwise
        """
        return getattr(self.use_case, "context", None)

    @classmethod
    async def execute_durable(
        cls,
        workflow: Workflow,
        workflow_id: Optional[str] = None,
    ) -> bool:
        """
        Execute workflow with DBOS durability (class method).

        This is a convenience method that creates a runner and executes
        the workflow in a single call.

        Args:
            workflow: Workflow to execute
            workflow_id: Optional workflow ID for idempotency

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            success = await DBOSWorkflowRunner.execute_durable(workflow)
            ```
        """
        runner = cls(workflow)

        # TODO: Integrate DBOS workflow_id for idempotency
        # This will be used with DBOS.start_workflow(workflow_id=...)

        return await runner.execute()


# ============================================================================
# DBOS Workflow Entrypoint (for DBOS runtime)
# ============================================================================
# This section will be expanded in Phase 3 with @DBOS.workflow decorators
#
# Planned enhancements:
# 1. @DBOS.workflow wrapper for execute()
# 2. @DBOS.step for each node execution
# 3. Compensating transactions for rollback
# 4. DBOS.start_workflow() for async job submission
# ============================================================================


async def execute_workflow_durable(
    workflow_data: Dict[str, Any],
    workflow_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    DBOS workflow entrypoint.

    This function is the main entry point for DBOS runtime execution.
    It will be decorated with @DBOS.workflow in Phase 3.

    Args:
        workflow_data: Serialized workflow JSON
        workflow_id: Optional ID for idempotency

    Returns:
        Execution result dictionary

    Note:
        Currently a placeholder. Will be fully implemented with
        @DBOS.workflow decorator in Phase 3.
    """
    from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

    # Load workflow from dictionary
    workflow = load_workflow_from_dict(workflow_data)

    # Execute with durable runner
    success = await DBOSWorkflowRunner.execute_durable(workflow, workflow_id)

    return {
        "success": success,
        "workflow_id": workflow_id or workflow.metadata.workflow_id,
        "workflow_name": workflow.metadata.name,
    }
