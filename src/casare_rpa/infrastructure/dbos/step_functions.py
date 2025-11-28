"""
DBOS Step Functions for Project Aether.

Converts individual node execution into DBOS @step functions for:
- Automatic checkpointing after each node
- Retry on transient failures
- Exactly-once execution guarantees
- Crash recovery with state restoration

Architecture:
- Each @step is an atomic operation
- DBOS auto-checkpoints after successful completion
- Failed steps can be retried with exponential backoff
- Non-serializable resources (Playwright) recreated on recovery
"""

import asyncio
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
import time
from loguru import logger

try:
    from dbos import DBOS, DBOSConfiguredInstance

    DBOS_AVAILABLE = True
except ImportError:
    DBOS_AVAILABLE = False
    logger.warning("DBOS not available - step functions will run without durability")

from casare_rpa.domain.value_objects.types import NodeId, NodeStatus, EventType
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext


class ExecutionStepResult:
    """
    Result of a single execution step.

    Contains:
    - success: Whether step completed successfully
    - node_id: ID of executed node
    - execution_time: Time taken in seconds
    - result: Node execution result
    - error: Error message if failed
    - context_state: Serialized ExecutionContext state
    """

    def __init__(
        self,
        success: bool,
        node_id: NodeId,
        execution_time: float,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        context_state: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.node_id = node_id
        self.execution_time = execution_time
        self.result = result or {}
        self.error = error
        self.context_state = context_state or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for DBOS storage."""
        return {
            "success": self.success,
            "node_id": self.node_id,
            "execution_time": self.execution_time,
            "result": self.result,
            "error": self.error,
            "context_state": self.context_state,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionStepResult":
        """Deserialize from dictionary."""
        return cls(
            success=data["success"],
            node_id=data["node_id"],
            execution_time=data["execution_time"],
            result=data.get("result"),
            error=data.get("error"),
            context_state=data.get("context_state"),
        )


# ============================================================================
# DBOS Step Function: Validate Node
# ============================================================================


async def validate_node_step(
    node: Any,
    node_id: NodeId,
) -> Tuple[bool, Optional[str]]:
    """
    DBOS step for validating a node before execution.

    This will be decorated with @DBOS.step() to enable checkpointing.
    Validation is idempotent and safe to retry.

    Args:
        node: Node instance to validate
        node_id: Node ID for logging

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        is_valid = node.validate()
        if not is_valid:
            return False, "Node validation failed"
        return True, None
    except Exception as e:
        logger.exception(f"Validation exception for node {node_id}")
        return False, str(e)


# ============================================================================
# DBOS Step Function: Execute Node
# ============================================================================


async def execute_node_step(
    node: Any,
    context: ExecutionContext,
    node_id: NodeId,
    node_timeout: float = 120.0,
) -> ExecutionStepResult:
    """
    DBOS step for executing a single node.

    This function will be decorated with @DBOS.step() to provide:
    - Automatic checkpointing after completion
    - Retry on transient failures (network, timeout)
    - Exactly-once execution guarantee

    Args:
        node: Node instance to execute
        context: Execution context with resources and variables
        node_id: Node ID for tracking
        node_timeout: Timeout in seconds

    Returns:
        ExecutionStepResult with success status and result data

    Note:
        This function must be idempotent for retry safety.
        Side effects (browser actions) may execute multiple times on retry.
    """
    start_time = time.time()
    node_type = node.__class__.__name__

    logger.info(f"[@step] Executing node: {node_id} ({node_type})")

    try:
        # Check if node is disabled (bypassed)
        if node.config.get("_disabled", False):
            logger.info(f"Node {node_id} is disabled - bypassing execution")
            node.status = NodeStatus.SUCCESS

            return ExecutionStepResult(
                success=True,
                node_id=node_id,
                execution_time=0,
                result={"success": True, "bypassed": True},
                context_state=context.to_dict() if hasattr(context, "to_dict") else {},
            )

        # Set node status
        node.status = NodeStatus.RUNNING

        # Execute with timeout
        result = await asyncio.wait_for(node.execute(context), timeout=node_timeout)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Update node metadata
        node.execution_count += 1
        node.last_execution_time = execution_time
        node.last_output = result

        # Check result
        if result and result.get("success", False):
            node.status = NodeStatus.SUCCESS

            logger.info(
                f"[@step] Node {node_id} completed successfully "
                f"in {execution_time:.2f}s"
            )

            return ExecutionStepResult(
                success=True,
                node_id=node_id,
                execution_time=execution_time,
                result=result,
                context_state=context.to_dict() if hasattr(context, "to_dict") else {},
            )
        else:
            node.status = NodeStatus.ERROR
            error_msg = result.get("error", "Unknown error") if result else "No result"

            logger.error(f"[@step] Node {node_id} failed: {error_msg}")

            return ExecutionStepResult(
                success=False,
                node_id=node_id,
                execution_time=execution_time,
                result=result,
                error=error_msg,
                context_state=context.to_dict() if hasattr(context, "to_dict") else {},
            )

    except asyncio.TimeoutError:
        execution_time = time.time() - start_time
        node.status = NodeStatus.ERROR
        error_msg = f"Node timed out after {node_timeout}s"

        logger.error(f"[@step] {error_msg}: {node_id}")

        return ExecutionStepResult(
            success=False,
            node_id=node_id,
            execution_time=execution_time,
            error=error_msg,
            context_state=context.to_dict() if hasattr(context, "to_dict") else {},
        )

    except Exception as e:
        execution_time = time.time() - start_time
        node.status = NodeStatus.ERROR
        error_msg = str(e)

        logger.exception(f"[@step] Exception during node execution: {node_id}")

        return ExecutionStepResult(
            success=False,
            node_id=node_id,
            execution_time=execution_time,
            error=error_msg,
            context_state=context.to_dict() if hasattr(context, "to_dict") else {},
        )


# ============================================================================
# DBOS Step Function: Transfer Data Between Nodes
# ============================================================================


async def transfer_data_step(
    connection: Any,
    nodes: Dict[NodeId, Any],
) -> bool:
    """
    DBOS step for transferring data from source port to target port.

    This will be decorated with @DBOS.step() for checkpointing.
    Data transfer is idempotent (setting a value multiple times is safe).

    Args:
        connection: Connection defining source and target
        nodes: Dictionary of node instances

    Returns:
        True if transfer succeeded, False otherwise
    """
    try:
        source_node = nodes.get(connection.source_node)
        target_node = nodes.get(connection.target_node)

        if not source_node or not target_node:
            logger.warning(
                f"Data transfer failed: node not found "
                f"({connection.source_node} -> {connection.target_node})"
            )
            return False

        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)

        # Set value to target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)

            # Log data transfers (non-exec) for debugging
            if "exec" not in connection.source_port.lower():
                logger.debug(
                    f"[@step] Data: {connection.source_port} -> "
                    f"{connection.target_port} = {repr(value)[:80]}"
                )

        return True

    except Exception as e:
        logger.exception(f"Data transfer exception: {e}")
        return False


# ============================================================================
# DBOS Step Function: Initialize Execution Context
# ============================================================================


async def initialize_context_step(
    workflow_name: str,
    initial_variables: Optional[Dict[str, Any]] = None,
    project_context: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    DBOS step for initializing execution context.

    Creates ExecutionContext and returns serialized state for DBOS storage.
    This will be decorated with @DBOS.step().

    Args:
        workflow_name: Name of workflow being executed
        initial_variables: Optional initial variables
        project_context: Optional project context

    Returns:
        Serialized context state dictionary
    """
    try:
        logger.info(f"[@step] Initializing execution context for: {workflow_name}")

        context = ExecutionContext(
            workflow_name=workflow_name,
            initial_variables=initial_variables or {},
            project_context=project_context,
        )

        # Serialize context state for DBOS
        context_state = (
            context.to_dict()
            if hasattr(context, "to_dict")
            else {
                "workflow_name": workflow_name,
                "variables": initial_variables or {},
            }
        )

        logger.debug(
            f"[@step] Context initialized with state keys: {list(context_state.keys())}"
        )

        return context_state

    except Exception as e:
        logger.exception(f"Failed to initialize context: {e}")
        raise


# ============================================================================
# DBOS Step Function: Cleanup Resources
# ============================================================================


async def cleanup_context_step(
    context: ExecutionContext,
    timeout: float = 30.0,
) -> bool:
    """
    DBOS step for cleaning up execution context resources.

    Closes Playwright contexts, browser instances, etc.
    This will be decorated with @DBOS.step().

    Args:
        context: Execution context to cleanup
        timeout: Cleanup timeout in seconds

    Returns:
        True if cleanup succeeded, False otherwise
    """
    try:
        logger.info("[@step] Cleaning up execution context resources")

        await asyncio.wait_for(context.cleanup(), timeout=timeout)

        logger.debug("[@step] Context cleanup completed")
        return True

    except asyncio.TimeoutError:
        logger.error(f"Context cleanup timed out after {timeout}s")
        return False

    except Exception as e:
        logger.exception(f"Error during context cleanup: {e}")
        return False


# ============================================================================
# Helper: Apply DBOS Decorators (for Phase 3.2)
# ============================================================================


def apply_dbos_decorators(dbos_instance: Optional[Any] = None) -> None:
    """
    Apply @DBOS.step() decorators to all step functions.

    This function will be called during DBOS initialization to
    register step functions with the DBOS runtime.

    Args:
        dbos_instance: DBOS instance to use for decorators

    Note:
        Currently a placeholder. Will be implemented in Phase 3.2
        when @workflow integration is complete.
    """
    if not DBOS_AVAILABLE:
        logger.warning("DBOS not available - decorators not applied")
        return

    dbos = dbos_instance or DBOS

    # TODO: Apply decorators dynamically
    # This will be implemented when DBOS @workflow integration is complete
    logger.info("DBOS decorators ready (manual application required)")


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ExecutionStepResult",
    "validate_node_step",
    "execute_node_step",
    "transfer_data_step",
    "initialize_context_step",
    "cleanup_context_step",
    "apply_dbos_decorators",
]
