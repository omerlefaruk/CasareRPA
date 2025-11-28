"""
DBOS Workflow Runner - Phase 3.2 (Decorated Version).

Applies @DBOS.workflow and @DBOS.step decorators for durable execution.
This is the Phase 3.2 implementation with actual DBOS runtime integration.

Key Changes from Phase 3.1:
- @DBOS.workflow decorator on main execution function
- workflow_id parameter for idempotency
- Proper DBOS initialization and configuration
- Step function orchestration with checkpointing

Architecture:
```
@DBOS.workflow
async def execute_workflow_durable(workflow_id, workflow_data):
    context = await initialize_context_step()  # @DBOS.step

    for node in execution_order:
        result = await execute_node_step(node, context)  # @DBOS.step
        # DBOS automatically checkpoints here

    await cleanup_context_step(context)  # @DBOS.step
```
"""

import asyncio
from typing import Any, Dict, Optional
from uuid import uuid4
from loguru import logger

try:
    from dbos import DBOS, DBOSConfiguredInstance

    DBOS_AVAILABLE = True
except ImportError:
    DBOS_AVAILABLE = False
    logger.warning("DBOS not available - workflow runner will run without durability")

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.value_objects.types import NodeId
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
from casare_rpa.infrastructure.dbos.step_functions import (
    execute_node_step,
    initialize_context_step,
    cleanup_context_step,
)


# ============================================================================
# DBOS Workflow - Main Entry Point
# ============================================================================


if DBOS_AVAILABLE:

    @DBOS.workflow()
    async def execute_workflow_durable(
        workflow_id: str,
        workflow_data: Dict[str, Any],
        initial_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        DBOS durable workflow execution.

        This function is decorated with @DBOS.workflow() to provide:
        - Automatic checkpointing after each @step
        - Crash recovery with state restoration
        - Exactly-once execution guarantees
        - Idempotency via workflow_id

        Args:
            workflow_id: Unique workflow instance ID (for idempotency)
            workflow_data: Serialized workflow schema
            initial_variables: Optional initial variables

        Returns:
            Execution result dictionary with success status

        Example:
            ```python
            # Start durable workflow
            handle = DBOS.start_workflow(
                execute_workflow_durable,
                workflow_id="wf-001",
                workflow_data=workflow.to_dict(),
                initial_variables={"count": 0}
            )

            # Get result
            result = await handle.get_result()
            ```
        """
        logger.info(f"[@workflow] Starting: {workflow_id}")

        try:
            # Load workflow from data
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )

            workflow = load_workflow_from_dict(workflow_data)

            # Step 1: Initialize execution context
            logger.info(f"[@workflow] Initializing context for {workflow_id}")
            context_state = await initialize_context_step(
                workflow_name=workflow.metadata.name,
                initial_variables=initial_variables or {},
                project_context=None,
            )

            # Recreate context from state
            context = ExecutionContext.from_dict(context_state)

            # Step 2: Find start node and compute execution order
            logger.info(f"[@workflow] Computing execution order for {workflow_id}")
            from casare_rpa.domain.services.execution_orchestrator import (
                ExecutionOrchestrator,
            )

            orchestrator = ExecutionOrchestrator(workflow)
            start_node = orchestrator.find_start_node()

            if not start_node:
                logger.error(f"[@workflow] No start node found: {workflow_id}")
                await cleanup_context_step(context)
                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": "No start node found",
                }

            execution_order = orchestrator.compute_execution_order(start_node.id)
            logger.info(
                f"[@workflow] Execution order ({len(execution_order)} nodes): "
                f"{[node.id for node in execution_order]}"
            )

            # Step 3: Execute nodes sequentially (each as a @step)
            executed_count = 0
            failed_node_id = None

            for i, node in enumerate(execution_order):
                logger.info(
                    f"[@workflow] Executing node {i+1}/{len(execution_order)}: "
                    f"{node.id} ({node.__class__.__name__})"
                )

                # Execute node as DBOS step
                step_result = await execute_node_step(
                    node=node, context=context, node_id=node.id, node_timeout=120.0
                )

                # DBOS automatically checkpoints here

                if not step_result.success:
                    logger.error(
                        f"[@workflow] Node failed: {node.id}, error: {step_result.error}"
                    )
                    failed_node_id = node.id
                    break

                # Update context from step result
                if step_result.context_state:
                    context = ExecutionContext.from_dict(step_result.context_state)

                executed_count += 1
                logger.debug(
                    f"[@workflow] Node completed: {node.id} "
                    f"in {step_result.execution_time:.2f}s"
                )

            # Step 4: Cleanup
            logger.info(f"[@workflow] Cleaning up context for {workflow_id}")
            cleanup_success = await cleanup_context_step(context, timeout=30.0)

            # Determine overall success
            all_executed = executed_count == len(execution_order)
            success = all_executed and failed_node_id is None

            logger.info(
                f"[@workflow] Completed: {workflow_id}, "
                f"success={success}, executed={executed_count}/{len(execution_order)}"
            )

            return {
                "success": success,
                "workflow_id": workflow_id,
                "workflow_name": workflow.metadata.name,
                "executed_nodes": executed_count,
                "total_nodes": len(execution_order),
                "failed_node_id": failed_node_id,
                "cleanup_success": cleanup_success,
            }

        except Exception as e:
            logger.exception(f"[@workflow] Exception in {workflow_id}: {e}")

            # Attempt cleanup on error
            try:
                if "context" in locals():
                    await cleanup_context_step(context, timeout=10.0)
            except Exception as cleanup_error:
                logger.error(f"[@workflow] Cleanup failed: {cleanup_error}")

            return {"success": False, "workflow_id": workflow_id, "error": str(e)}

else:
    # Fallback for when DBOS is not available
    async def execute_workflow_durable(
        workflow_id: str,
        workflow_data: Dict[str, Any],
        initial_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fallback execution without DBOS.

        This version runs without durability when DBOS is unavailable.
        """
        logger.warning(
            f"DBOS not available - executing {workflow_id} without durability"
        )

        # Use standard ExecuteWorkflowUseCase
        from casare_rpa.application.use_cases.execute_workflow import (
            ExecuteWorkflowUseCase,
            ExecutionSettings,
        )
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(workflow_data)

        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=None,
            settings=ExecutionSettings(),
            initial_variables=initial_variables or {},
            project_context=None,
        )

        success = await use_case.execute()

        return {
            "success": success,
            "workflow_id": workflow_id,
            "workflow_name": workflow.metadata.name,
        }


# ============================================================================
# Helper Functions for Workflow Submission
# ============================================================================


async def start_durable_workflow(
    workflow: WorkflowSchema,
    workflow_id: Optional[str] = None,
    initial_variables: Optional[Dict[str, Any]] = None,
    wait_for_result: bool = False,
) -> Dict[str, Any]:
    """
    Start a durable workflow execution.

    Args:
        workflow: Workflow schema to execute
        workflow_id: Optional workflow ID (generated if None)
        initial_variables: Optional initial variables
        wait_for_result: If True, wait for completion; if False, return immediately

    Returns:
        If wait_for_result=True: Execution result
        If wait_for_result=False: {"workflow_id": "...", "status": "started"}

    Example:
        ```python
        # Fire and forget
        info = await start_durable_workflow(workflow, wait_for_result=False)
        print(f"Started workflow: {info['workflow_id']}")

        # Wait for completion
        result = await start_durable_workflow(workflow, wait_for_result=True)
        print(f"Workflow completed: {result['success']}")
        ```
    """
    # Generate workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"wf-{uuid4().hex[:12]}"

    workflow_data = workflow.to_dict()

    if DBOS_AVAILABLE:
        # Use DBOS.start_workflow for durable execution
        handle = DBOS.start_workflow(
            execute_workflow_durable, workflow_id, workflow_data, initial_variables
        )

        if wait_for_result:
            # Wait for workflow to complete
            result = await handle.get_result()
            return result
        else:
            # Return immediately with workflow ID
            return {"workflow_id": workflow_id, "status": "started", "durable": True}
    else:
        # Fallback: Execute directly without DBOS
        if wait_for_result:
            result = await execute_workflow_durable(
                workflow_id, workflow_data, initial_variables
            )
            return result
        else:
            # Start as background task
            asyncio.create_task(
                execute_workflow_durable(workflow_id, workflow_data, initial_variables)
            )
            return {"workflow_id": workflow_id, "status": "started", "durable": False}


async def get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a running workflow.

    Args:
        workflow_id: Workflow instance ID

    Returns:
        Status dictionary or None if not found

    Example:
        ```python
        status = await get_workflow_status("wf-001")
        if status:
            print(f"Status: {status['status']}")
        ```
    """
    if not DBOS_AVAILABLE:
        logger.warning("DBOS not available - cannot get workflow status")
        return None

    try:
        # Use DBOS API to get workflow status
        handle = DBOS.retrieve_workflow(workflow_id)
        status = await handle.get_status()

        return {
            "workflow_id": workflow_id,
            "status": status.status,  # PENDING, RUNNING, SUCCESS, ERROR
            "result": status.result if status.result else None,
        }
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        return None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "execute_workflow_durable",
    "start_durable_workflow",
    "get_workflow_status",
    "DBOS_AVAILABLE",
]
