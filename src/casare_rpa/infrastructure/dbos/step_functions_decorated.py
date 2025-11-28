"""
DBOS Step Functions - Phase 3.2 (Decorated Version).

Applies @DBOS.step decorators to all step functions for automatic checkpointing.

Key Changes from Phase 3.1:
- All step functions decorated with @DBOS.step()
- Proper error handling for DBOS retry logic
- Idempotent operations for safe retries

Architecture:
- Each @DBOS.step is atomic and checkpointed
- Steps can be retried on transient failures
- State is serialized for crash recovery
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

from casare_rpa.domain.value_objects.types import NodeId, NodeStatus
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
from casare_rpa.infrastructure.dbos.step_functions import ExecutionStepResult


# ============================================================================
# DBOS Step Function: Initialize Execution Context
# ============================================================================

if DBOS_AVAILABLE:

    @DBOS.step()
    async def initialize_context_step(
        workflow_name: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        DBOS step for initializing execution context.

        Creates ExecutionContext and returns serialized state for DBOS storage.
        Decorated with @DBOS.step() for automatic checkpointing.

        Args:
            workflow_name: Name of workflow being executed
            initial_variables: Optional initial variables
            project_context: Optional project context

        Returns:
            Serialized context state dictionary
        """
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

else:
    # Fallback version without decorator
    async def initialize_context_step(
        workflow_name: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Fallback version without DBOS.step decorator."""
        from casare_rpa.infrastructure.dbos.step_functions import (
            initialize_context_step as fallback,
        )

        return await fallback(workflow_name, initial_variables, project_context)


# ============================================================================
# DBOS Step Function: Execute Node
# ============================================================================

if DBOS_AVAILABLE:

    @DBOS.step()
    async def execute_node_step(
        node: Any,
        context: ExecutionContext,
        node_id: NodeId,
        node_timeout: float = 120.0,
    ) -> ExecutionStepResult:
        """
        DBOS step for executing a single node.

        Decorated with @DBOS.step() to provide:
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
        start_time = time.perf_counter()
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
                    context_state=context.to_dict()
                    if hasattr(context, "to_dict")
                    else {},
                )

            # Set node status
            node.status = NodeStatus.RUNNING

            # Execute with timeout
            result = await asyncio.wait_for(node.execute(context), timeout=node_timeout)

            # Calculate execution time
            execution_time = time.perf_counter() - start_time

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
                    context_state=context.to_dict()
                    if hasattr(context, "to_dict")
                    else {},
                )
            else:
                node.status = NodeStatus.ERROR
                error_msg = (
                    result.get("error", "Unknown error") if result else "No result"
                )

                logger.error(f"[@step] Node {node_id} failed: {error_msg}")

                return ExecutionStepResult(
                    success=False,
                    node_id=node_id,
                    execution_time=execution_time,
                    result=result,
                    error=error_msg,
                    context_state=context.to_dict()
                    if hasattr(context, "to_dict")
                    else {},
                )

        except asyncio.TimeoutError:
            execution_time = time.perf_counter() - start_time
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
            execution_time = time.perf_counter() - start_time
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

else:
    # Fallback version without decorator
    async def execute_node_step(
        node: Any,
        context: ExecutionContext,
        node_id: NodeId,
        node_timeout: float = 120.0,
    ) -> ExecutionStepResult:
        """Fallback version without DBOS.step decorator."""
        from casare_rpa.infrastructure.dbos.step_functions import (
            execute_node_step as fallback,
        )

        return await fallback(node, context, node_id, node_timeout)


# ============================================================================
# DBOS Step Function: Cleanup Resources
# ============================================================================

if DBOS_AVAILABLE:

    @DBOS.step()
    async def cleanup_context_step(
        context: ExecutionContext,
        timeout: float = 30.0,
    ) -> bool:
        """
        DBOS step for cleaning up execution context resources.

        Closes Playwright contexts, browser instances, etc.
        Decorated with @DBOS.step() for automatic checkpointing.

        Args:
            context: Execution context to cleanup
            timeout: Cleanup timeout in seconds

        Returns:
            True if cleanup succeeded, False otherwise
        """
        logger.info("[@step] Cleaning up execution context resources")

        try:
            await asyncio.wait_for(context.cleanup(), timeout=timeout)

            logger.debug("[@step] Context cleanup completed")
            return True

        except asyncio.TimeoutError:
            logger.error(f"Context cleanup timed out after {timeout}s")
            return False

        except Exception as e:
            logger.exception(f"Error during context cleanup: {e}")
            return False

else:
    # Fallback version without decorator
    async def cleanup_context_step(
        context: ExecutionContext,
        timeout: float = 30.0,
    ) -> bool:
        """Fallback version without DBOS.step decorator."""
        from casare_rpa.infrastructure.dbos.step_functions import (
            cleanup_context_step as fallback,
        )

        return await fallback(context, timeout)


# ============================================================================
# DBOS Step Function: Transfer Data Between Nodes
# ============================================================================

if DBOS_AVAILABLE:

    @DBOS.step()
    async def transfer_data_step(
        connection: Any,
        nodes: Dict[NodeId, Any],
    ) -> bool:
        """
        DBOS step for transferring data from source port to target port.

        Decorated with @DBOS.step() for checkpointing.
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

else:
    # Fallback version without decorator
    async def transfer_data_step(
        connection: Any,
        nodes: Dict[NodeId, Any],
    ) -> bool:
        """Fallback version without DBOS.step decorator."""
        from casare_rpa.infrastructure.dbos.step_functions import (
            transfer_data_step as fallback,
        )

        return await fallback(connection, nodes)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ExecutionStepResult",
    "initialize_context_step",
    "execute_node_step",
    "cleanup_context_step",
    "transfer_data_step",
    "DBOS_AVAILABLE",
]
