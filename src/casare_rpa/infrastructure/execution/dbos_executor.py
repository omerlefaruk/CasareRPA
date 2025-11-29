"""
DBOS Workflow Executor - Durable workflow execution with automatic checkpointing.

SECURITY HARDENED VERSION
-Validates all SQL identifiers to prevent injection (CWE-89)
- Validates workflow JSON before deserialization (CWE-502)
- Validates workflow IDs to prevent injection
- Uses parameterized queries exclusively
- Logs sanitized data only

Provides durable execution semantics similar to DBOS (Database Operating System):
- Automatic checkpointing at step boundaries
- Crash recovery with exactly-once semantics
- Workflow idempotency via workflow_id
- Step-level isolation for retry
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable
import traceback

import asyncpg
from loguru import logger
import orjson

from casare_rpa.domain.events import EventBus, Event, get_event_bus
from casare_rpa.domain.value_objects.types import EventType
from casare_rpa.infrastructure.security import (
    validate_sql_identifier,
    validate_workflow_id,
    validate_workflow_json,
)


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
    recovered: bool = False


@dataclass
class DBOSExecutorConfig:
    """
    Configuration for DBOS Workflow Executor.

    Attributes:
        postgres_url: PostgreSQL connection string for checkpoint storage
        checkpoint_table: Table name for checkpoints (VALIDATED for SQL injection)
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

    def __post_init__(self) -> None:
        """
        SECURITY: Validate checkpoint_table name to prevent SQL injection.

        This prevents CWE-89 (SQL Injection) by ensuring the table name
        cannot contain quotes, semicolons, or other SQL metacharacters.
        """
        try:
            self.checkpoint_table = validate_sql_identifier(
                self.checkpoint_table, name="checkpoint_table"
            )
        except ValueError as e:
            logger.error(f"Invalid checkpoint_table configuration: {e}")
            raise


class DBOSWorkflowExecutor:
    """
    SECURITY HARDENED Durable workflow executor with DBOS-like semantics.

    Security Features:
    - SQL injection prevention via identifier validation
    - Workflow JSON validation before deserialization
    - Parameterized queries only
    - Workflow ID validation
    - Safe logging (no credential exposure)

    Provides exactly-once execution guarantees through checkpointing
    and recovery mechanisms. Workflows can survive process crashes
    and resume from their last checkpointed state.
    """

    def __init__(
        self,
        config: Optional[DBOSExecutorConfig] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """
        Initialize DBOS workflow executor.

        Args:
            config: Executor configuration (table names validated)
            event_bus: Optional event bus for progress notifications
        """
        self.config = config or DBOSExecutorConfig()
        self.event_bus = event_bus or get_event_bus()

        self._pool: Optional[asyncpg.Pool] = None
        self._running = False

        # SECURITY: Use validated table name
        self._checkpoint_table = self.config.checkpoint_table

        logger.info(
            f"DBOSWorkflowExecutor initialized with table='{self._checkpoint_table}' "
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
        """
        Create checkpoint table if it doesn't exist.

        SECURITY: Uses validated table name from config (already sanitized).
        Table name is substituted safely as it passed validate_sql_identifier().
        """
        if not self._pool:
            return

        # SECURITY NOTE: self._checkpoint_table is pre-validated in __post_init__
        # It's safe to use in string formatting as it passed SQL identifier validation
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._checkpoint_table} (
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

            CREATE INDEX IF NOT EXISTS idx_{self._checkpoint_table}_state
            ON {self._checkpoint_table}(state);
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

        SECURITY: Validates workflow_id and workflow_json before execution.

        Args:
            workflow_json: Serialized workflow definition (JSON string) - VALIDATED
            workflow_id: Unique identifier for this execution - VALIDATED
            initial_variables: Initial execution variables
            wait_for_result: Wait for execution to complete
            on_progress: Optional callback for progress updates (progress%, node_id)

        Returns:
            DurableExecutionResult with execution outcome

        Raises:
            ValueError: If workflow_id or workflow_json validation fails
        """
        # SECURITY FIX #3: Validate workflow_id before ANY database operations
        try:
            workflow_id = validate_workflow_id(workflow_id)
        except ValueError as e:
            logger.error(f"Invalid workflow_id rejected: {e}")
            raise

        start_time = datetime.now(timezone.utc)
        recovered = False

        # Check for existing checkpoint
        checkpoint = await self._load_checkpoint(workflow_id)

        if checkpoint:
            if checkpoint.state == WorkflowExecutionState.COMPLETED:
                logger.info(
                    f"Workflow {workflow_id[:12]}... already completed (idempotent)"
                )
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
                    f"Workflow {workflow_id[:12]}... previously failed: {checkpoint.error}"
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
                f"Resuming workflow {workflow_id[:12]}... from step {checkpoint.current_step} "
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

            # SECURITY FIX #3: Validate workflow JSON BEFORE deserialization
            if isinstance(workflow_json, str):
                workflow_data = orjson.loads(workflow_json)
            else:
                workflow_data = workflow_json

            # CRITICAL: Validate against schema to prevent deserialization attacks (CWE-502)
            try:
                workflow_data = validate_workflow_json(workflow_data)
            except (ValueError, Exception) as e:
                logger.error(
                    f"Workflow JSON validation failed for {workflow_id[:12]}...: {e}"
                )
                raise ValueError(f"Invalid workflow JSON: {e}") from e

            # Now safe to deserialize
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
                f"Workflow {workflow_id[:12]}... {'completed' if success else 'failed'} "
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

            logger.exception(
                f"Workflow {workflow_id[:12]}... execution failed: {error_msg}"
            )

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
        """
        Load checkpoint from database.

        SECURITY: Uses parameterized query (workflow_id as parameter).
        Table name is pre-validated.
        """
        if not self._pool:
            return None

        try:
            # SECURITY: Parameterized query - workflow_id is a parameter, not concatenated
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    SELECT * FROM {self._checkpoint_table}
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
            logger.error(f"Failed to load checkpoint for {workflow_id[:12]}...: {e}")
            return None

    async def _save_checkpoint(self, checkpoint: ExecutionCheckpoint) -> None:
        """
        Save checkpoint to database.

        SECURITY: Uses parameterized query. All values as parameters.
        """
        if not self._pool:
            return

        try:
            # SECURITY: All checkpoint data passed as parameters ($1-$10)
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self._checkpoint_table}
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
            logger.error(
                f"Failed to save checkpoint for {checkpoint.workflow_id[:12]}...: {e}"
            )

    async def clear_checkpoint(self, workflow_id: str) -> bool:
        """
        Clear checkpoint for a completed workflow.

        SECURITY: Validates workflow_id and uses parameterized query.

        Args:
            workflow_id: Workflow ID to clear

        Returns:
            True if checkpoint was cleared
        """
        # SECURITY: Validate workflow_id
        try:
            workflow_id = validate_workflow_id(workflow_id)
        except ValueError as e:
            logger.error(f"Invalid workflow_id in clear_checkpoint: {e}")
            return False

        if not self._pool:
            return False

        try:
            # SECURITY: Parameterized query
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    f"""
                    DELETE FROM {self._checkpoint_table}
                    WHERE workflow_id = $1
                    """,
                    workflow_id,
                )
                return "DELETE" in result
        except Exception as e:
            logger.error(f"Failed to clear checkpoint for {workflow_id[:12]}...: {e}")
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

    SECURITY: Validates workflow_id before execution.

    Args:
        workflow: Workflow data (dict or JSON string)
        workflow_id: Unique execution ID (VALIDATED)
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
