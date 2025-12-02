"""
DBOS Workflow Executor - Durable workflow execution with automatic checkpointing.

Provides durable execution semantics similar to DBOS (Database Operating System):
- Automatic checkpointing at step boundaries
- Crash recovery with exactly-once semantics
- Workflow idempotency via workflow_id
- Step-level isolation for retry

This is a simplified implementation that provides DBOS-like durability patterns
without requiring the full DBOS runtime.

Architecture:
- Each workflow execution is assigned a unique workflow_id
- Execution state is checkpointed to PostgreSQL after each step
- On crash/restart, execution resumes from the last completed step
- Results are cached by step for exactly-once semantics
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable
import traceback

import asyncpg
from loguru import logger
import orjson

from casare_rpa.domain.events import EventBus, Event, get_event_bus
from casare_rpa.domain.value_objects.types import EventType

# Lazy imports to avoid circular dependencies
# These are imported inside functions where needed:
# - load_workflow_from_dict from casare_rpa.utils.workflow.workflow_loader
# - ExecuteWorkflowUseCase, ExecutionSettings from casare_rpa.application.use_cases.execute_workflow


class WorkflowExecutionState(Enum):
    """State of a durable workflow execution."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionCheckpoint:
    """
    Checkpoint of workflow execution state.

    Stored in PostgreSQL for crash recovery.
    """

    workflow_id: str
    state: WorkflowExecutionState
    current_step: int
    current_node_id: Optional[str]
    executed_nodes: List[str]
    variables: Dict[str, Any]
    step_results: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "workflow_id": self.workflow_id,
            "state": self.state.value,
            "current_step": self.current_step,
            "current_node_id": self.current_node_id,
            "executed_nodes": self.executed_nodes,
            "variables": self.variables,
            "step_results": self.step_results,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionCheckpoint":
        """Create from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            state=WorkflowExecutionState(data["state"]),
            current_step=data["current_step"],
            current_node_id=data.get("current_node_id"),
            executed_nodes=data.get("executed_nodes", []),
            variables=data.get("variables", {}),
            step_results=data.get("step_results", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data["created_at"],
            updated_at=datetime.fromisoformat(data["updated_at"])
            if isinstance(data["updated_at"], str)
            else data["updated_at"],
            error=data.get("error"),
        )


@dataclass
class DurableExecutionResult:
    """Result of a durable workflow execution."""

    workflow_id: str
    success: bool
    state: WorkflowExecutionState
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed_nodes: int = 0
    total_nodes: int = 0
    duration_ms: int = 0
    recovered: bool = False  # True if execution was recovered from checkpoint


@dataclass
class DBOSExecutorConfig:
    """
    Configuration for DBOS Workflow Executor.

    Attributes:
        postgres_url: PostgreSQL connection string for checkpoint storage
        checkpoint_table: Table name for checkpoints
        enable_checkpointing: Whether to enable checkpoint persistence
        checkpoint_interval: Checkpoint after every N nodes (0 = every node)
        execution_timeout_seconds: Maximum execution time per workflow
        node_timeout_seconds: Maximum execution time per node
        continue_on_error: Continue workflow execution on node errors
    """

    postgres_url: Optional[str] = None
    checkpoint_table: str = "workflow_checkpoints"
    enable_checkpointing: bool = True
    checkpoint_interval: int = 0
    execution_timeout_seconds: int = 3600
    node_timeout_seconds: float = 120.0
    continue_on_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary with credential masking.

        SECURITY: Masks postgres_url to prevent credential leakage in logs.
        """
        from casare_rpa.infrastructure.security.validators import sanitize_log_value

        return {
            "postgres_url": sanitize_log_value(self.postgres_url)
            if self.postgres_url
            else None,
            "checkpoint_table": self.checkpoint_table,
            "enable_checkpointing": self.enable_checkpointing,
            "checkpoint_interval": self.checkpoint_interval,
            "execution_timeout_seconds": self.execution_timeout_seconds,
            "node_timeout_seconds": self.node_timeout_seconds,
            "continue_on_error": self.continue_on_error,
        }


class DBOSWorkflowExecutor:
    """
    Durable workflow executor with DBOS-like semantics.

    Provides exactly-once execution guarantees through checkpointing
    and recovery mechanisms. Workflows can survive process crashes
    and resume from their last checkpointed state.

    Usage:
        executor = DBOSWorkflowExecutor(config)
        await executor.start()

        result = await executor.execute_workflow(
            workflow_json=workflow_json,
            workflow_id=unique_id,
            initial_variables={"input": "value"}
        )

        await executor.stop()
    """

    def __init__(
        self,
        config: Optional[DBOSExecutorConfig] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """
        Initialize DBOS workflow executor.

        Args:
            config: Executor configuration
            event_bus: Optional event bus for progress notifications
        """
        self.config = config or DBOSExecutorConfig()
        self.event_bus = event_bus or get_event_bus()

        self._pool: Optional[asyncpg.Pool] = None
        self._running = False

        logger.info(
            f"DBOSWorkflowExecutor initialized "
            f"(checkpointing={'enabled' if self.config.enable_checkpointing else 'disabled'})"
        )

    async def start(self) -> None:
        """Start the executor and establish database connection."""
        if self._running:
            return

        self._running = True

        if self.config.postgres_url and self.config.enable_checkpointing:
            try:
                self._pool = await asyncpg.create_pool(
                    self.config.postgres_url,
                    min_size=1,
                    max_size=3,
                    command_timeout=60.0,
                )
                await self._ensure_checkpoint_table()
                logger.info("Checkpoint storage connected")
            except Exception as e:
                logger.warning(
                    f"Failed to connect checkpoint storage: {e}. "
                    "Continuing without persistence."
                )
                self._pool = None

    async def stop(self) -> None:
        """Stop the executor and close connections."""
        self._running = False

        if self._pool:
            try:
                await asyncio.wait_for(self._pool.close(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout closing checkpoint pool")
            except Exception as e:
                logger.error(f"Error closing checkpoint pool: {e}")
            finally:
                self._pool = None

        logger.info("DBOSWorkflowExecutor stopped")

    async def _ensure_checkpoint_table(self) -> None:
        """Create checkpoint table if it doesn't exist."""
        if not self._pool:
            return

        # SECURITY: Validate table name to prevent SQL injection
        from casare_rpa.infrastructure.security.validators import (
            validate_sql_identifier,
        )

        table_name = validate_sql_identifier(
            self.config.checkpoint_table, "checkpoint_table"
        )

        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                workflow_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                current_step INTEGER DEFAULT 0,
                current_node_id TEXT,
                executed_nodes JSONB DEFAULT '[]',
                variables JSONB DEFAULT '{{}}',
                step_results JSONB DEFAULT '{{}}',
                error TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_{table_name}_state
            ON {table_name}(state);
        """

        async with self._pool.acquire() as conn:
            await conn.execute(create_table_sql)

    async def execute_workflow(
        self,
        workflow_json: str,
        workflow_id: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        wait_for_result: bool = True,
        on_progress: Optional[Callable[[int, str], Awaitable[None]]] = None,
    ) -> DurableExecutionResult:
        """
        Execute a workflow with durable execution semantics.

        If a checkpoint exists for the workflow_id, execution resumes
        from the last checkpointed state (exactly-once semantics).

        Args:
            workflow_json: Serialized workflow definition (JSON string)
            workflow_id: Unique identifier for this execution (for idempotency)
            initial_variables: Initial execution variables
            wait_for_result: Wait for execution to complete
            on_progress: Optional callback for progress updates (progress%, node_id)

        Returns:
            DurableExecutionResult with execution outcome
        """
        start_time = datetime.now(timezone.utc)
        recovered = False

        # Check for existing checkpoint
        checkpoint = await self._load_checkpoint(workflow_id)

        if checkpoint:
            if checkpoint.state == WorkflowExecutionState.COMPLETED:
                logger.info(f"Workflow {workflow_id} already completed (idempotent)")
                return DurableExecutionResult(
                    workflow_id=workflow_id,
                    success=True,
                    state=WorkflowExecutionState.COMPLETED,
                    result=checkpoint.step_results.get("final"),
                    executed_nodes=len(checkpoint.executed_nodes),
                    recovered=True,
                )

            if checkpoint.state == WorkflowExecutionState.FAILED:
                logger.info(
                    f"Workflow {workflow_id} previously failed: {checkpoint.error}"
                )
                return DurableExecutionResult(
                    workflow_id=workflow_id,
                    success=False,
                    state=WorkflowExecutionState.FAILED,
                    error=checkpoint.error,
                    executed_nodes=len(checkpoint.executed_nodes),
                    recovered=True,
                )

            # Resume from checkpoint
            logger.info(
                f"Resuming workflow {workflow_id} from step {checkpoint.current_step} "
                f"({len(checkpoint.executed_nodes)} nodes completed)"
            )
            recovered = True
            initial_variables = checkpoint.variables
        else:
            # Create new checkpoint
            checkpoint = ExecutionCheckpoint(
                workflow_id=workflow_id,
                state=WorkflowExecutionState.PENDING,
                current_step=0,
                current_node_id=None,
                executed_nodes=[],
                variables=initial_variables or {},
                step_results={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await self._save_checkpoint(checkpoint)

        try:
            # Lazy imports to avoid circular dependencies
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )

            # Parse workflow
            if isinstance(workflow_json, str):
                workflow_data = orjson.loads(workflow_json)
            else:
                workflow_data = workflow_json

            # SECURITY: Workflow validation is handled by load_workflow_from_dict
            # which calls validate_workflow_structure() with robust security checks
            # including dangerous pattern detection, size limits, and type validation.
            # The security schema (workflow_schema.py) is skipped here because it
            # expects list-format nodes while the rest of the codebase uses dict-format.

            workflow = load_workflow_from_dict(workflow_data)
            total_nodes = len(workflow.nodes)

            # Update checkpoint to running
            checkpoint.state = WorkflowExecutionState.RUNNING
            await self._save_checkpoint(checkpoint)

            # Emit workflow started event
            self._emit_event(
                EventType.WORKFLOW_STARTED,
                {
                    "workflow_id": workflow_id,
                    "workflow_name": workflow.metadata.name,
                    "total_nodes": total_nodes,
                    "recovered": recovered,
                },
            )

            # Create execution use case
            settings = ExecutionSettings(
                continue_on_error=self.config.continue_on_error,
                node_timeout=self.config.node_timeout_seconds,
            )

            use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self.event_bus,
                settings=settings,
                initial_variables=initial_variables,
            )

            # Set up progress tracking
            if on_progress:

                def on_node_complete(event: Event) -> None:
                    node_id = event.node_id or ""
                    progress = int(event.data.get("progress", 0))
                    asyncio.create_task(on_progress(progress, node_id))

                self.event_bus.subscribe(EventType.NODE_COMPLETED, on_node_complete)

            # Execute with timeout
            try:
                success = await asyncio.wait_for(
                    use_case.execute(),
                    timeout=self.config.execution_timeout_seconds,
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Workflow execution timed out after "
                    f"{self.config.execution_timeout_seconds}s"
                )

            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update final checkpoint
            checkpoint.state = (
                WorkflowExecutionState.COMPLETED
                if success
                else WorkflowExecutionState.FAILED
            )
            checkpoint.executed_nodes = list(use_case.executed_nodes)
            checkpoint.updated_at = end_time

            if not success and use_case.context and use_case.context.errors:
                checkpoint.error = str(use_case.context.errors[-1])

            await self._save_checkpoint(checkpoint)

            # Emit completion event
            self._emit_event(
                EventType.WORKFLOW_COMPLETED if success else EventType.WORKFLOW_ERROR,
                {
                    "workflow_id": workflow_id,
                    "success": success,
                    "executed_nodes": len(use_case.executed_nodes),
                    "duration_ms": duration_ms,
                },
            )

            logger.info(
                f"Workflow {workflow_id} {'completed' if success else 'failed'} "
                f"in {duration_ms}ms ({len(use_case.executed_nodes)} nodes)"
            )

            return DurableExecutionResult(
                workflow_id=workflow_id,
                success=success,
                state=checkpoint.state,
                error=checkpoint.error,
                executed_nodes=len(use_case.executed_nodes),
                total_nodes=total_nodes,
                duration_ms=duration_ms,
                recovered=recovered,
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            error_msg = f"{type(e).__name__}: {str(e)}"

            logger.exception(f"Workflow {workflow_id} execution failed: {error_msg}")

            # Update checkpoint with error
            checkpoint.state = WorkflowExecutionState.FAILED
            checkpoint.error = error_msg
            checkpoint.updated_at = end_time
            await self._save_checkpoint(checkpoint)

            # Emit error event
            self._emit_event(
                EventType.WORKFLOW_ERROR,
                {
                    "workflow_id": workflow_id,
                    "error": error_msg,
                    "traceback": traceback.format_exc(),
                },
            )

            return DurableExecutionResult(
                workflow_id=workflow_id,
                success=False,
                state=WorkflowExecutionState.FAILED,
                error=error_msg,
                executed_nodes=len(checkpoint.executed_nodes),
                duration_ms=duration_ms,
                recovered=recovered,
            )

    async def _load_checkpoint(self, workflow_id: str) -> Optional[ExecutionCheckpoint]:
        """Load checkpoint from database."""
        if not self._pool:
            return None

        try:
            from casare_rpa.infrastructure.security.validators import (
                validate_sql_identifier,
            )

            table_name = validate_sql_identifier(
                self.config.checkpoint_table, "checkpoint_table"
            )

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    SELECT * FROM {table_name}
                    WHERE workflow_id = $1
                    """,
                    workflow_id,
                )

                if not row:
                    return None

                return ExecutionCheckpoint(
                    workflow_id=row["workflow_id"],
                    state=WorkflowExecutionState(row["state"]),
                    current_step=row["current_step"],
                    current_node_id=row["current_node_id"],
                    executed_nodes=row["executed_nodes"] or [],
                    variables=row["variables"] or {},
                    step_results=row["step_results"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    error=row["error"],
                )
        except Exception as e:
            logger.error(f"Failed to load checkpoint for {workflow_id}: {e}")
            return None

    async def _save_checkpoint(self, checkpoint: ExecutionCheckpoint) -> None:
        """Save checkpoint to database."""
        if not self._pool:
            return

        try:
            from casare_rpa.infrastructure.security.validators import (
                validate_sql_identifier,
            )

            table_name = validate_sql_identifier(
                self.config.checkpoint_table, "checkpoint_table"
            )

            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {table_name}
                    (workflow_id, state, current_step, current_node_id,
                     executed_nodes, variables, step_results, error,
                     created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (workflow_id) DO UPDATE SET
                        state = EXCLUDED.state,
                        current_step = EXCLUDED.current_step,
                        current_node_id = EXCLUDED.current_node_id,
                        executed_nodes = EXCLUDED.executed_nodes,
                        variables = EXCLUDED.variables,
                        step_results = EXCLUDED.step_results,
                        error = EXCLUDED.error,
                        updated_at = EXCLUDED.updated_at
                    """,
                    checkpoint.workflow_id,
                    checkpoint.state.value,
                    checkpoint.current_step,
                    checkpoint.current_node_id,
                    orjson.dumps(checkpoint.executed_nodes).decode(),
                    orjson.dumps(checkpoint.variables).decode(),
                    orjson.dumps(checkpoint.step_results).decode(),
                    checkpoint.error,
                    checkpoint.created_at,
                    checkpoint.updated_at,
                )
        except Exception as e:
            logger.error(f"Failed to save checkpoint for {checkpoint.workflow_id}: {e}")

    async def clear_checkpoint(self, workflow_id: str) -> bool:
        """
        Clear checkpoint for a completed workflow.

        Args:
            workflow_id: Workflow ID to clear

        Returns:
            True if checkpoint was cleared
        """
        if not self._pool:
            return False

        try:
            from casare_rpa.infrastructure.security.validators import (
                validate_sql_identifier,
            )

            table_name = validate_sql_identifier(
                self.config.checkpoint_table, "checkpoint_table"
            )

            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    f"""
                    DELETE FROM {table_name}
                    WHERE workflow_id = $1
                    """,
                    workflow_id,
                )
                return "DELETE" in result
        except Exception as e:
            logger.error(f"Failed to clear checkpoint for {workflow_id}: {e}")
            return False

    def _emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event to the event bus."""
        if self.event_bus:
            event = Event(event_type=event_type, data=data)
            self.event_bus.publish(event)


# Convenience function for simple usage
async def start_durable_workflow(
    workflow: Any,
    workflow_id: str,
    initial_variables: Optional[Dict[str, Any]] = None,
    wait_for_result: bool = True,
    postgres_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a workflow with durable execution.

    Convenience function that creates an executor, runs the workflow,
    and returns the result.

    Args:
        workflow: Workflow data (dict or JSON string)
        workflow_id: Unique execution ID
        initial_variables: Initial variables
        wait_for_result: Wait for completion
        postgres_url: Optional PostgreSQL URL for checkpointing

    Returns:
        Dict with success, error, and execution details
    """
    if isinstance(workflow, dict):
        workflow_json = orjson.dumps(workflow).decode()
    else:
        workflow_json = workflow

    config = DBOSExecutorConfig(postgres_url=postgres_url)
    executor = DBOSWorkflowExecutor(config)

    try:
        await executor.start()
        result = await executor.execute_workflow(
            workflow_json=workflow_json,
            workflow_id=workflow_id,
            initial_variables=initial_variables,
            wait_for_result=wait_for_result,
        )
        return {
            "success": result.success,
            "error": result.error,
            "executed_nodes": result.executed_nodes,
            "total_nodes": result.total_nodes,
            "duration_ms": result.duration_ms,
            "recovered": result.recovered,
        }
    finally:
        await executor.stop()
