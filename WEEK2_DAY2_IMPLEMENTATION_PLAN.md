# Week 2 Day 2: Runner Application Layer - Implementation Plan

**Document Version**: 1.0
**Created**: November 27, 2025
**Target Completion**: 8 hours (1 day)
**Author**: rpa-system-architect

---

## Executive Summary

This document provides a comprehensive implementation plan for Week 2 Day 2 of the CasareRPA refactoring roadmap. The objective is to extract application layer services from the existing `WorkflowRunner` (1,404 lines) and create a clean service architecture in `src/casare_rpa/application/services/`.

### Current State Analysis

| Component | Lines | Issues |
|-----------|-------|--------|
| `WorkflowRunner` | 1,404 | Violates Single Responsibility Principle (12 responsibilities) |
| `ExecuteWorkflowUseCase` | 559 | Partially refactored, but still has execution logic mixed with orchestration |
| `ExecutionOrchestrator` | 539 | Pure domain service (correctly implemented) |
| `ExecutionState` | 294 | Pure domain entity (correctly implemented) |

### Target Architecture

```
src/casare_rpa/application/services/
    __init__.py
    workflow_execution_service.py      # Main orchestration service
    node_execution_service.py          # Single node execution with timeout/retry
    state_management_service.py        # Pause/Resume/Stop control
    event_publication_service.py       # Event bus wrapper service
    data_transfer_service.py           # Port-to-port data transfer
    validation_service.py              # Pre-execution validation
    metrics_service.py                 # Performance metrics collection
```

---

## Detailed Task Breakdown (Hour-by-Hour)

### Phase 1: Service Interface Definitions (Hours 1-2)

**Objective**: Define protocols/ABCs for all services to ensure testability and clear contracts.

#### Task 1.1: Create Service Protocols (45 min)

**File**: `src/casare_rpa/application/services/protocols.py`

```python
"""
CasareRPA - Application Layer Service Protocols
Defines abstract interfaces for all execution-related services.

These protocols enable:
- Dependency injection for testability
- Clear service contracts
- Mock substitution in tests
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Set, Callable, Awaitable
from datetime import datetime

from ...domain.value_objects.types import NodeId, ExecutionResult, EventType


class ExecutionResultData:
    """
    Value object representing the result of a single node execution.

    Immutable data container for execution outcomes.
    """
    __slots__ = ('node_id', 'success', 'data', 'error', 'execution_time_ms', 'timestamp')

    def __init__(
        self,
        node_id: NodeId,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0.0,
        timestamp: Optional[datetime] = None
    ) -> None:
        self.node_id = node_id
        self.success = success
        self.data = data or {}
        self.error = error
        self.execution_time_ms = execution_time_ms
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class WorkflowExecutionResult:
    """
    Value object representing the complete result of a workflow execution.
    """
    __slots__ = (
        'workflow_name', 'success', 'node_results', 'total_nodes',
        'executed_nodes', 'execution_time_ms', 'started_at', 'completed_at',
        'error', 'stopped_by_user'
    )

    def __init__(
        self,
        workflow_name: str,
        success: bool,
        node_results: Optional[Dict[NodeId, ExecutionResultData]] = None,
        total_nodes: int = 0,
        executed_nodes: int = 0,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error: Optional[str] = None,
        stopped_by_user: bool = False
    ) -> None:
        self.workflow_name = workflow_name
        self.success = success
        self.node_results = node_results or {}
        self.total_nodes = total_nodes
        self.executed_nodes = executed_nodes
        self.execution_time_ms = execution_time_ms
        self.started_at = started_at
        self.completed_at = completed_at
        self.error = error
        self.stopped_by_user = stopped_by_user


class INodeExecutionService(Protocol):
    """
    Protocol for single node execution.

    Responsibilities:
    - Execute a single node with timeout protection
    - Handle node-level errors and exceptions
    - Return structured execution result
    """

    async def execute(
        self,
        node: Any,
        context: Any,
        timeout_seconds: float = 120.0
    ) -> ExecutionResultData:
        """
        Execute a single node with timeout.

        Args:
            node: The node instance to execute (BaseNode subclass)
            context: Execution context with variables and resources
            timeout_seconds: Maximum execution time

        Returns:
            ExecutionResultData with success/failure and data
        """
        ...


class IStateManagementService(Protocol):
    """
    Protocol for execution state management.

    Responsibilities:
    - Track pause/resume/stop state
    - Provide async wait points for pause
    - Thread-safe state transitions
    """

    async def check_pause(self) -> None:
        """Wait if execution is paused. Returns immediately if not paused."""
        ...

    def pause(self) -> bool:
        """
        Pause execution.

        Returns:
            True if pause was successful, False if already paused/stopped
        """
        ...

    def resume(self) -> bool:
        """
        Resume paused execution.

        Returns:
            True if resume was successful, False if not paused
        """
        ...

    def stop(self) -> None:
        """Request execution stop. Unblocks if paused."""
        ...

    @property
    def is_running(self) -> bool:
        """Check if execution is in running state."""
        ...

    @property
    def is_paused(self) -> bool:
        """Check if execution is paused."""
        ...

    @property
    def is_stopped(self) -> bool:
        """Check if stop was requested."""
        ...


class IEventPublicationService(Protocol):
    """
    Protocol for event publication.

    Responsibilities:
    - Wrap EventBus for consistent event emission
    - Provide typed event methods
    - Handle event failures gracefully
    """

    async def publish_node_started(
        self,
        node_id: NodeId,
        node_type: str
    ) -> None:
        """Publish node started event."""
        ...

    async def publish_node_completed(
        self,
        node_id: NodeId,
        result: ExecutionResultData
    ) -> None:
        """Publish node completed event with result."""
        ...

    async def publish_node_error(
        self,
        node_id: NodeId,
        error: str,
        execution_time_ms: float = 0.0
    ) -> None:
        """Publish node error event."""
        ...

    async def publish_workflow_started(
        self,
        workflow_name: str,
        total_nodes: int
    ) -> None:
        """Publish workflow started event."""
        ...

    async def publish_workflow_completed(
        self,
        result: WorkflowExecutionResult
    ) -> None:
        """Publish workflow completed event."""
        ...

    async def publish_workflow_error(
        self,
        workflow_name: str,
        error: str,
        executed_nodes: int
    ) -> None:
        """Publish workflow error event."""
        ...

    async def publish_workflow_stopped(
        self,
        workflow_name: str,
        executed_nodes: int,
        total_nodes: int
    ) -> None:
        """Publish workflow stopped event."""
        ...


class IDataTransferService(Protocol):
    """
    Protocol for port-to-port data transfer.

    Responsibilities:
    - Transfer output values from source to target ports
    - Handle type conversions if needed
    - Log data transfers for debugging
    """

    def transfer(
        self,
        source_node: Any,
        target_node: Any,
        source_port: str,
        target_port: str
    ) -> bool:
        """
        Transfer data from source output to target input.

        Args:
            source_node: Node with output value
            target_node: Node to receive value
            source_port: Output port name
            target_port: Input port name

        Returns:
            True if transfer was successful
        """
        ...

    def transfer_all_inputs(
        self,
        target_node_id: NodeId,
        nodes: Dict[NodeId, Any],
        connections: List[Any]
    ) -> int:
        """
        Transfer all input values to a target node.

        Args:
            target_node_id: Target node ID
            nodes: Dictionary of all nodes
            connections: List of all connections

        Returns:
            Number of successful transfers
        """
        ...


class IValidationService(Protocol):
    """
    Protocol for pre-execution validation.

    Responsibilities:
    - Validate workflow structure
    - Validate individual nodes before execution
    - Check for required inputs
    """

    def validate_workflow(self, workflow: Any) -> tuple[bool, List[str]]:
        """
        Validate workflow structure.

        Args:
            workflow: Workflow schema to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        ...

    def validate_node(self, node: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a node before execution.

        Args:
            node: Node to validate

        Returns:
            Tuple of (is_valid, error message if invalid)
        """
        ...


class IMetricsService(Protocol):
    """
    Protocol for performance metrics collection.

    Responsibilities:
    - Record node execution times
    - Track workflow execution statistics
    - Provide metrics for performance dashboard
    """

    def record_node_start(self, node_type: str, node_id: NodeId) -> None:
        """Record node execution start."""
        ...

    def record_node_complete(
        self,
        node_type: str,
        node_id: NodeId,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """Record node execution completion."""
        ...

    def record_workflow_start(self, workflow_name: str) -> None:
        """Record workflow execution start."""
        ...

    def record_workflow_complete(
        self,
        workflow_name: str,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """Record workflow execution completion."""
        ...


class IWorkflowExecutionService(Protocol):
    """
    Protocol for the main workflow execution service.

    This is the primary entry point for workflow execution.
    Orchestrates all other services.
    """

    async def execute(self) -> WorkflowExecutionResult:
        """
        Execute the workflow.

        Returns:
            Complete execution result
        """
        ...

    def pause(self) -> bool:
        """Pause execution."""
        ...

    def resume(self) -> bool:
        """Resume paused execution."""
        ...

    def stop(self) -> None:
        """Stop execution."""
        ...

    @property
    def progress(self) -> float:
        """Get execution progress (0-100)."""
        ...
```

**Acceptance Criteria**:
- [ ] All protocols defined with full type hints
- [ ] Each protocol has docstrings explaining responsibilities
- [ ] Value objects (ExecutionResultData, WorkflowExecutionResult) are immutable
- [ ] No infrastructure imports (EventBus, Playwright)

#### Task 1.2: Create Service Module Structure (15 min)

**File**: `src/casare_rpa/application/services/__init__.py`

```python
"""
CasareRPA - Application Layer Services

This module provides application services that orchestrate domain logic
and infrastructure components for workflow execution.

Service Hierarchy:
- WorkflowExecutionService: Main orchestration (uses all other services)
  - NodeExecutionService: Single node execution
  - StateManagementService: Pause/Resume/Stop
  - EventPublicationService: Event emission
  - DataTransferService: Port data transfer
  - ValidationService: Pre-execution checks
  - MetricsService: Performance tracking

Usage:
    from casare_rpa.application.services import WorkflowExecutionService

    service = WorkflowExecutionService(
        workflow=workflow_schema,
        event_bus=event_bus,
        settings=ExecutionSettings()
    )
    result = await service.execute()
"""

from .protocols import (
    # Value objects
    ExecutionResultData,
    WorkflowExecutionResult,
    # Protocols
    INodeExecutionService,
    IStateManagementService,
    IEventPublicationService,
    IDataTransferService,
    IValidationService,
    IMetricsService,
    IWorkflowExecutionService,
)

from .node_execution_service import NodeExecutionService
from .state_management_service import StateManagementService
from .event_publication_service import EventPublicationService
from .data_transfer_service import DataTransferService
from .validation_service import ValidationService
from .metrics_service import MetricsService
from .workflow_execution_service import WorkflowExecutionService

__all__ = [
    # Value objects
    "ExecutionResultData",
    "WorkflowExecutionResult",
    # Protocols
    "INodeExecutionService",
    "IStateManagementService",
    "IEventPublicationService",
    "IDataTransferService",
    "IValidationService",
    "IMetricsService",
    "IWorkflowExecutionService",
    # Implementations
    "NodeExecutionService",
    "StateManagementService",
    "EventPublicationService",
    "DataTransferService",
    "ValidationService",
    "MetricsService",
    "WorkflowExecutionService",
]
```

---

### Phase 2: Core Service Implementations (Hours 2-5)

#### Task 2.1: NodeExecutionService Implementation (1 hour)

**File**: `src/casare_rpa/application/services/node_execution_service.py`

**Dependencies**:
- Day 1 domain entities (ExecutionState from domain)
- core.execution_context.ExecutionContext (infrastructure)

```python
"""
CasareRPA - Node Execution Service
Handles execution of individual nodes with timeout and error handling.

Single Responsibility: Execute one node, handle timeout, return result.
"""

import asyncio
import time
from typing import Any, Optional
from loguru import logger

from .protocols import ExecutionResultData, INodeExecutionService
from ...domain.value_objects.types import NodeId, NodeStatus


class NodeExecutionError(Exception):
    """
    Raised when node execution fails.

    Attributes:
        node_id: ID of the failed node
        original_error: The underlying exception
    """

    def __init__(self, node_id: NodeId, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.node_id = node_id
        self.original_error = original_error


class NodeExecutionService(INodeExecutionService):
    """
    Service for executing individual nodes.

    Features:
    - Async execution with configurable timeout
    - Structured error handling and result packaging
    - Node status tracking
    - Debug information collection

    This service is stateless - each call to execute() is independent.
    """

    def __init__(self, default_timeout: float = 120.0) -> None:
        """
        Initialize node execution service.

        Args:
            default_timeout: Default timeout in seconds for node execution
        """
        self._default_timeout = default_timeout

    async def execute(
        self,
        node: Any,
        context: Any,
        timeout_seconds: Optional[float] = None
    ) -> ExecutionResultData:
        """
        Execute a single node with timeout protection.

        Args:
            node: The node instance to execute (must have execute() method)
            context: Execution context with variables and resources
            timeout_seconds: Override default timeout (None = use default)

        Returns:
            ExecutionResultData with execution outcome

        Note:
            This method never raises exceptions - all errors are captured
            in the ExecutionResultData.error field.
        """
        timeout = timeout_seconds if timeout_seconds is not None else self._default_timeout
        node_id: NodeId = node.node_id
        node_type: str = node.__class__.__name__

        start_time = time.perf_counter()

        logger.debug(f"Executing node {node_id} ({node_type}) with timeout {timeout}s")

        # Mark node as running
        node.status = NodeStatus.RUNNING

        try:
            # Execute with timeout protection
            raw_result = await asyncio.wait_for(
                self._execute_node_internal(node, context),
                timeout=timeout
            )

            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Process the result
            return self._process_result(
                node_id=node_id,
                raw_result=raw_result,
                execution_time_ms=execution_time_ms,
                node=node
            )

        except asyncio.TimeoutError:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Node {node_id} timed out after {timeout:.1f}s"

            logger.error(error_msg)
            node.status = NodeStatus.ERROR
            node.error_message = error_msg

            return ExecutionResultData(
                node_id=node_id,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Node {node_id} failed: {str(e)}"

            logger.exception(f"Exception during node execution: {node_id}")
            node.status = NodeStatus.ERROR
            node.error_message = error_msg

            return ExecutionResultData(
                node_id=node_id,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time_ms
            )

    async def _execute_node_internal(self, node: Any, context: Any) -> Any:
        """
        Internal method to execute node.

        Separated for easier testing and potential pre/post hooks.

        Args:
            node: Node to execute
            context: Execution context

        Returns:
            Raw result from node.execute()
        """
        result = await node.execute(context)
        return result if result is not None else {"success": False, "error": "No result returned"}

    def _process_result(
        self,
        node_id: NodeId,
        raw_result: Any,
        execution_time_ms: float,
        node: Any
    ) -> ExecutionResultData:
        """
        Process raw node result into ExecutionResultData.

        Handles both new ExecutionResult pattern and legacy NodeStatus pattern.

        Args:
            node_id: ID of executed node
            raw_result: Raw result from node.execute()
            execution_time_ms: Execution time in milliseconds
            node: The node instance (for status checking)

        Returns:
            Structured ExecutionResultData
        """
        # New ExecutionResult pattern: {"success": bool, "data": dict, "error": str}
        if isinstance(raw_result, dict) and "success" in raw_result:
            success = raw_result.get("success", False)

            if success:
                node.status = NodeStatus.SUCCESS
            else:
                node.status = NodeStatus.ERROR
                node.error_message = raw_result.get("error", "Unknown error")

            # Update node debug info
            node.execution_count = getattr(node, 'execution_count', 0) + 1
            node.last_execution_time = execution_time_ms / 1000  # Convert to seconds
            node.last_output = raw_result

            return ExecutionResultData(
                node_id=node_id,
                success=success,
                data=raw_result.get("data", {}),
                error=raw_result.get("error"),
                execution_time_ms=execution_time_ms
            )

        # Legacy pattern: check node.status
        success = node.status == NodeStatus.SUCCESS

        return ExecutionResultData(
            node_id=node_id,
            success=success,
            data={},
            error=node.error_message if not success else None,
            execution_time_ms=execution_time_ms
        )

    def execute_bypass(self, node: Any) -> ExecutionResultData:
        """
        Handle bypassed (disabled) node execution.

        Args:
            node: The disabled node

        Returns:
            ExecutionResultData indicating bypass
        """
        logger.info(f"Node {node.node_id} is disabled - bypassing execution")
        node.status = NodeStatus.SUCCESS

        return ExecutionResultData(
            node_id=node.node_id,
            success=True,
            data={"bypassed": True},
            execution_time_ms=0.0
        )

    def is_node_disabled(self, node: Any) -> bool:
        """
        Check if a node is disabled (should be bypassed).

        Args:
            node: Node to check

        Returns:
            True if node should be bypassed
        """
        return node.config.get("_disabled", False)
```

**Acceptance Criteria**:
- [ ] execute() never raises exceptions (all errors in result)
- [ ] Timeout protection with asyncio.wait_for
- [ ] Node status updated correctly (RUNNING -> SUCCESS/ERROR)
- [ ] Debug info updated (execution_count, last_execution_time)
- [ ] Handles both ExecutionResult pattern and legacy NodeStatus

---

#### Task 2.2: StateManagementService Implementation (45 min)

**File**: `src/casare_rpa/application/services/state_management_service.py`

```python
"""
CasareRPA - State Management Service
Handles pause/resume/stop control for workflow execution.

Single Responsibility: Manage execution state transitions and async waiting.
"""

import asyncio
from enum import Enum, auto
from typing import Optional
from loguru import logger


class ExecutionStateEnum(Enum):
    """Execution lifecycle states."""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    COMPLETED = auto()
    ERROR = auto()


class StateManagementService:
    """
    Service for managing workflow execution state.

    Features:
    - Thread-safe state transitions
    - Async pause waiting
    - Stop request handling

    State Machine:
        IDLE -> RUNNING -> PAUSED <-> RUNNING -> COMPLETED/STOPPED/ERROR
                    |           |
                    +--> STOPPED <-+
    """

    def __init__(self) -> None:
        """Initialize state management service."""
        self._state = ExecutionStateEnum.IDLE
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Start unpaused (event is "set" = not waiting)
        self._stop_requested = False

    @property
    def state(self) -> ExecutionStateEnum:
        """Get current execution state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Check if execution is in running state."""
        return self._state == ExecutionStateEnum.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if execution is paused."""
        return self._state == ExecutionStateEnum.PAUSED

    @property
    def is_stopped(self) -> bool:
        """Check if stop was requested."""
        return self._stop_requested

    @property
    def is_idle(self) -> bool:
        """Check if execution is idle (not started)."""
        return self._state == ExecutionStateEnum.IDLE

    def start(self) -> bool:
        """
        Transition to running state.

        Returns:
            True if transition was successful
        """
        if self._state != ExecutionStateEnum.IDLE:
            logger.warning(f"Cannot start: already in {self._state.name} state")
            return False

        self._state = ExecutionStateEnum.RUNNING
        self._stop_requested = False
        self._pause_event.set()

        logger.info("Execution started")
        return True

    async def check_pause(self) -> None:
        """
        Wait if execution is paused.

        This should be called between node executions.
        Returns immediately if not paused.
        """
        if self._state == ExecutionStateEnum.PAUSED:
            logger.debug("Execution paused, waiting for resume...")
            await self._pause_event.wait()
            logger.debug("Execution resumed")

    def pause(self) -> bool:
        """
        Pause execution.

        Returns:
            True if pause was successful, False if already paused/stopped
        """
        if self._state != ExecutionStateEnum.RUNNING:
            logger.warning(f"Cannot pause: in {self._state.name} state")
            return False

        self._state = ExecutionStateEnum.PAUSED
        self._pause_event.clear()  # Block waiters

        logger.info("Execution paused")
        return True

    def resume(self) -> bool:
        """
        Resume paused execution.

        Returns:
            True if resume was successful, False if not paused
        """
        if self._state != ExecutionStateEnum.PAUSED:
            logger.warning(f"Cannot resume: in {self._state.name} state")
            return False

        self._state = ExecutionStateEnum.RUNNING
        self._pause_event.set()  # Unblock waiters

        logger.info("Execution resumed")
        return True

    def stop(self) -> None:
        """
        Request execution stop.

        Unblocks if paused to allow graceful shutdown.
        """
        if self._state in (ExecutionStateEnum.COMPLETED, ExecutionStateEnum.ERROR):
            logger.warning("Cannot stop: execution already finished")
            return

        self._stop_requested = True
        self._state = ExecutionStateEnum.STOPPED
        self._pause_event.set()  # Unblock if paused

        logger.info("Execution stop requested")

    def complete(self) -> None:
        """Mark execution as completed successfully."""
        self._state = ExecutionStateEnum.COMPLETED
        logger.info("Execution completed")

    def error(self, message: Optional[str] = None) -> None:
        """
        Mark execution as failed.

        Args:
            message: Optional error message for logging
        """
        self._state = ExecutionStateEnum.ERROR
        if message:
            logger.error(f"Execution error: {message}")
        else:
            logger.error("Execution failed")

    def reset(self) -> None:
        """Reset to initial state for re-execution."""
        self._state = ExecutionStateEnum.IDLE
        self._stop_requested = False
        self._pause_event.set()

        logger.debug("State management reset to IDLE")
```

**Acceptance Criteria**:
- [ ] Thread-safe state transitions
- [ ] check_pause() is non-blocking when not paused
- [ ] stop() unblocks paused execution
- [ ] State machine follows defined transitions

---

#### Task 2.3: EventPublicationService Implementation (45 min)

**File**: `src/casare_rpa/application/services/event_publication_service.py`

```python
"""
CasareRPA - Event Publication Service
Wraps EventBus to provide typed event emission methods.

Single Responsibility: Publish execution events to EventBus.
"""

from typing import Any, Dict, Optional
from loguru import logger

from .protocols import ExecutionResultData, WorkflowExecutionResult
from ...domain.value_objects.types import NodeId, EventType
from ...core.events import Event, EventBus, get_event_bus


class EventPublicationService:
    """
    Service for publishing execution events.

    Provides typed methods for each event type, ensuring consistent
    event structure and handling EventBus failures gracefully.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """
        Initialize event publication service.

        Args:
            event_bus: EventBus instance (uses global if not provided)
        """
        self._event_bus = event_bus or get_event_bus()
        self._current_node_id: Optional[NodeId] = None

    def set_current_node(self, node_id: Optional[NodeId]) -> None:
        """
        Set the current node for event context.

        Args:
            node_id: Current node ID or None
        """
        self._current_node_id = node_id

    def _publish(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """
        Internal method to publish an event.

        Handles EventBus failures gracefully.

        Args:
            event_type: Type of event
            data: Event data payload
        """
        try:
            if self._event_bus:
                event = Event(
                    event_type=event_type,
                    data=data,
                    node_id=self._current_node_id
                )
                self._event_bus.publish(event)
        except Exception as e:
            # Log but don't fail execution due to event errors
            logger.warning(f"Failed to publish {event_type.name} event: {e}")

    async def publish_node_started(
        self,
        node_id: NodeId,
        node_type: str
    ) -> None:
        """
        Publish node started event.

        Args:
            node_id: ID of starting node
            node_type: Type name of node
        """
        self.set_current_node(node_id)
        self._publish(
            EventType.NODE_STARTED,
            {
                "node_id": node_id,
                "node_type": node_type,
            }
        )

    async def publish_node_completed(
        self,
        node_id: NodeId,
        result: ExecutionResultData,
        progress: float = 0.0
    ) -> None:
        """
        Publish node completed event.

        Args:
            node_id: ID of completed node
            result: Execution result data
            progress: Workflow progress percentage
        """
        self._publish(
            EventType.NODE_COMPLETED,
            {
                "node_id": node_id,
                "message": result.data.get("message", "Completed"),
                "progress": progress,
                "execution_time": result.execution_time_ms / 1000,  # Seconds for UI
                "bypassed": result.data.get("bypassed", False),
            }
        )

    async def publish_node_error(
        self,
        node_id: NodeId,
        error: str,
        execution_time_ms: float = 0.0
    ) -> None:
        """
        Publish node error event.

        Args:
            node_id: ID of failed node
            error: Error message
            execution_time_ms: Execution time before failure
        """
        self._publish(
            EventType.NODE_ERROR,
            {
                "node_id": node_id,
                "error": error,
                "execution_time": execution_time_ms / 1000,
            }
        )

    async def publish_workflow_started(
        self,
        workflow_name: str,
        total_nodes: int
    ) -> None:
        """
        Publish workflow started event.

        Args:
            workflow_name: Name of workflow
            total_nodes: Total nodes to execute
        """
        self._publish(
            EventType.WORKFLOW_STARTED,
            {
                "workflow_name": workflow_name,
                "total_nodes": total_nodes,
            }
        )

    async def publish_workflow_completed(
        self,
        result: WorkflowExecutionResult
    ) -> None:
        """
        Publish workflow completed event.

        Args:
            result: Complete execution result
        """
        self._publish(
            EventType.WORKFLOW_COMPLETED,
            {
                "executed_nodes": result.executed_nodes,
                "total_nodes": result.total_nodes,
                "duration": result.execution_time_ms / 1000,
            }
        )

    async def publish_workflow_error(
        self,
        workflow_name: str,
        error: str,
        executed_nodes: int
    ) -> None:
        """
        Publish workflow error event.

        Args:
            workflow_name: Name of workflow
            error: Error message
            executed_nodes: Number of nodes executed before error
        """
        self._publish(
            EventType.WORKFLOW_ERROR,
            {
                "workflow_name": workflow_name,
                "error": error,
                "executed_nodes": executed_nodes,
            }
        )

    async def publish_workflow_stopped(
        self,
        workflow_name: str,
        executed_nodes: int,
        total_nodes: int
    ) -> None:
        """
        Publish workflow stopped event.

        Args:
            workflow_name: Name of workflow
            executed_nodes: Nodes executed before stop
            total_nodes: Total nodes in workflow
        """
        self._publish(
            EventType.WORKFLOW_STOPPED,
            {
                "workflow_name": workflow_name,
                "executed_nodes": executed_nodes,
                "total_nodes": total_nodes,
            }
        )

    async def publish_workflow_paused(
        self,
        workflow_name: str,
        executed_nodes: int,
        total_nodes: int,
        progress: float
    ) -> None:
        """
        Publish workflow paused event.

        Args:
            workflow_name: Name of workflow
            executed_nodes: Nodes executed
            total_nodes: Total nodes
            progress: Progress percentage
        """
        self._publish(
            EventType.WORKFLOW_PAUSED,
            {
                "workflow_name": workflow_name,
                "executed_nodes": executed_nodes,
                "total_nodes": total_nodes,
                "progress": progress,
            }
        )

    async def publish_workflow_resumed(
        self,
        workflow_name: str,
        executed_nodes: int,
        total_nodes: int
    ) -> None:
        """
        Publish workflow resumed event.

        Args:
            workflow_name: Name of workflow
            executed_nodes: Nodes executed
            total_nodes: Total nodes
        """
        self._publish(
            EventType.WORKFLOW_RESUMED,
            {
                "workflow_name": workflow_name,
                "executed_nodes": executed_nodes,
                "total_nodes": total_nodes,
            }
        )
```

**Acceptance Criteria**:
- [ ] All event types have corresponding publish methods
- [ ] EventBus failures are caught and logged (don't crash execution)
- [ ] Event data structure matches existing UI expectations
- [ ] Consistent time unit conversion (ms internally, seconds for UI)

---

#### Task 2.4: DataTransferService Implementation (30 min)

**File**: `src/casare_rpa/application/services/data_transfer_service.py`

```python
"""
CasareRPA - Data Transfer Service
Handles port-to-port data transfer between nodes.

Single Responsibility: Move data from output ports to input ports.
"""

from typing import Any, Dict, List
from loguru import logger

from ...domain.value_objects.types import NodeId


class DataTransferService:
    """
    Service for transferring data between node ports.

    Features:
    - Transfer individual port values
    - Bulk transfer all inputs for a target node
    - Debug logging for data flow tracing
    """

    def __init__(self, debug_logging: bool = True) -> None:
        """
        Initialize data transfer service.

        Args:
            debug_logging: If True, log data transfers for debugging
        """
        self._debug_logging = debug_logging

    def transfer(
        self,
        source_node: Any,
        target_node: Any,
        source_port: str,
        target_port: str
    ) -> bool:
        """
        Transfer data from source output port to target input port.

        Args:
            source_node: Node with the output value
            target_node: Node to receive the value
            source_port: Name of output port
            target_port: Name of input port

        Returns:
            True if transfer was successful (value was not None)
        """
        if source_node is None or target_node is None:
            logger.warning("Cannot transfer: source or target node is None")
            return False

        try:
            # Get value from source output port
            value = source_node.get_output_value(source_port)

            if value is None:
                # No value to transfer - this is normal for optional ports
                return False

            # Set value to target input port
            target_node.set_input_value(target_port, value)

            # Log data transfers (non-exec) for debugging
            if self._debug_logging and "exec" not in source_port.lower():
                # Truncate long values for readability
                value_repr = repr(value)
                if len(value_repr) > 80:
                    value_repr = value_repr[:77] + "..."

                logger.info(
                    f"Data: {source_node.node_id}.{source_port} -> "
                    f"{target_node.node_id}.{target_port} = {value_repr}"
                )

            return True

        except Exception as e:
            logger.error(
                f"Failed to transfer data from {source_node.node_id}.{source_port} "
                f"to {target_node.node_id}.{target_port}: {e}"
            )
            return False

    def transfer_all_inputs(
        self,
        target_node_id: NodeId,
        nodes: Dict[NodeId, Any],
        connections: List[Any]
    ) -> int:
        """
        Transfer all input values to a target node based on connections.

        Args:
            target_node_id: ID of the target node
            nodes: Dictionary of all nodes (node_id -> node)
            connections: List of all connections in workflow

        Returns:
            Number of successful transfers
        """
        target_node = nodes.get(target_node_id)
        if target_node is None:
            logger.warning(f"Target node {target_node_id} not found")
            return 0

        successful_transfers = 0

        for connection in connections:
            # Check if this connection targets our node
            if connection.target_node == target_node_id:
                source_node = nodes.get(connection.source_node)

                if source_node is not None:
                    if self.transfer(
                        source_node=source_node,
                        target_node=target_node,
                        source_port=connection.source_port,
                        target_port=connection.target_port
                    ):
                        successful_transfers += 1

        return successful_transfers
```

**Acceptance Criteria**:
- [ ] Handles None values gracefully
- [ ] Truncates long values in debug logs
- [ ] transfer_all_inputs finds all incoming connections
- [ ] Execution ports ("exec_") are not logged as data

---

#### Task 2.5: ValidationService Implementation (30 min)

**File**: `src/casare_rpa/application/services/validation_service.py`

```python
"""
CasareRPA - Validation Service
Handles pre-execution validation of workflows and nodes.

Single Responsibility: Validate before execution.
"""

from typing import Any, List, Optional, Tuple
from loguru import logger

from ...domain.services.execution_orchestrator import ExecutionOrchestrator


class ValidationService:
    """
    Service for pre-execution validation.

    Features:
    - Workflow structure validation (cycles, start node)
    - Individual node validation
    - Required input checking
    """

    def __init__(self) -> None:
        """Initialize validation service."""
        pass

    def validate_workflow(self, workflow: Any) -> Tuple[bool, List[str]]:
        """
        Validate workflow structure before execution.

        Checks:
        - Has at least one Start node
        - No circular dependencies
        - All referenced nodes exist

        Args:
            workflow: Workflow schema to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []

        # Check for start node
        orchestrator = ExecutionOrchestrator(workflow)
        start_node_id = orchestrator.find_start_node()

        if not start_node_id:
            errors.append("Workflow must have a StartNode")

        # Check for circular dependencies
        is_valid, cycle_errors = orchestrator.validate_execution_order()
        if not is_valid:
            errors.extend(cycle_errors)

        # Check all connection targets exist
        for connection in workflow.connections:
            if connection.source_node not in workflow.nodes:
                errors.append(
                    f"Connection source node '{connection.source_node}' not found"
                )
            if connection.target_node not in workflow.nodes:
                errors.append(
                    f"Connection target node '{connection.target_node}' not found"
                )

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"Workflow validation failed: {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.debug("Workflow validation passed")

        return is_valid, errors

    def validate_node(self, node: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a node before execution.

        Args:
            node: Node to validate

        Returns:
            Tuple of (is_valid, error message if invalid)
        """
        try:
            # Use node's built-in validate method
            if hasattr(node, 'validate'):
                is_valid = node.validate()
                if not is_valid:
                    error_msg = getattr(node, 'error_message', 'Validation failed')
                    logger.warning(f"Node {node.node_id} validation failed: {error_msg}")
                    return False, error_msg

            return True, None

        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.exception(f"Exception during node {node.node_id} validation")
            return False, error_msg

    def validate_required_inputs(
        self,
        node: Any,
        provided_inputs: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if all required inputs are provided.

        Args:
            node: Node to check
            provided_inputs: List of input port names that have values

        Returns:
            Tuple of (is_valid, list of missing input names)
        """
        missing_inputs: List[str] = []

        # Get required inputs from node's input_ports
        if hasattr(node, 'input_ports'):
            for port in node.input_ports:
                if port.required and port.name not in provided_inputs:
                    missing_inputs.append(port.name)

        is_valid = len(missing_inputs) == 0

        if not is_valid:
            logger.warning(
                f"Node {node.node_id} missing required inputs: {missing_inputs}"
            )

        return is_valid, missing_inputs
```

**Acceptance Criteria**:
- [ ] Uses ExecutionOrchestrator for cycle detection
- [ ] Validates individual nodes using their validate() method
- [ ] Checks connection integrity
- [ ] Returns structured error messages

---

#### Task 2.6: MetricsService Implementation (30 min)

**File**: `src/casare_rpa/application/services/metrics_service.py`

```python
"""
CasareRPA - Metrics Service
Wraps performance metrics collection for execution tracking.

Single Responsibility: Record execution metrics.
"""

from typing import Optional
from loguru import logger

from ...domain.value_objects.types import NodeId
from ...utils.performance.performance_metrics import get_metrics, PerformanceMetrics


class MetricsService:
    """
    Service for collecting execution metrics.

    Wraps the global PerformanceMetrics singleton for:
    - Node execution timing
    - Workflow execution statistics
    - Success/failure tracking

    Failures in metrics recording never interrupt execution.
    """

    def __init__(self, metrics: Optional[PerformanceMetrics] = None) -> None:
        """
        Initialize metrics service.

        Args:
            metrics: PerformanceMetrics instance (uses global if not provided)
        """
        self._metrics = metrics or get_metrics()

    def record_node_start(self, node_type: str, node_id: NodeId) -> None:
        """
        Record node execution start.

        Args:
            node_type: Type name of node (class name)
            node_id: Unique node ID
        """
        try:
            self._metrics.record_node_start(node_type, node_id)
        except Exception as e:
            logger.debug(f"Failed to record node start metric: {e}")

    def record_node_complete(
        self,
        node_type: str,
        node_id: NodeId,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """
        Record node execution completion.

        Args:
            node_type: Type name of node
            node_id: Unique node ID
            execution_time_ms: Execution time in milliseconds
            success: True if execution was successful
        """
        try:
            self._metrics.record_node_complete(
                node_type, node_id, execution_time_ms, success=success
            )
        except Exception as e:
            logger.debug(f"Failed to record node complete metric: {e}")

    def record_workflow_start(self, workflow_name: str) -> None:
        """
        Record workflow execution start.

        Args:
            workflow_name: Name of workflow
        """
        try:
            self._metrics.record_workflow_start(workflow_name)
        except Exception as e:
            logger.debug(f"Failed to record workflow start metric: {e}")

    def record_workflow_complete(
        self,
        workflow_name: str,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """
        Record workflow execution completion.

        Args:
            workflow_name: Name of workflow
            execution_time_ms: Total execution time in milliseconds
            success: True if workflow completed successfully
        """
        try:
            self._metrics.record_workflow_complete(
                workflow_name, execution_time_ms, success=success
            )
        except Exception as e:
            logger.debug(f"Failed to record workflow complete metric: {e}")
```

**Acceptance Criteria**:
- [ ] Wraps global PerformanceMetrics singleton
- [ ] Never raises exceptions (logs failures silently)
- [ ] Matches existing metrics API

---

### Phase 3: WorkflowExecutionService Integration (Hours 5-7)

#### Task 3.1: WorkflowExecutionService Implementation (2 hours)

**File**: `src/casare_rpa/application/services/workflow_execution_service.py`

This is the main orchestration service that composes all other services.

```python
"""
CasareRPA - Workflow Execution Service
Main orchestration service for workflow execution.

Composes all other services:
- NodeExecutionService: Execute individual nodes
- StateManagementService: Pause/Resume/Stop
- EventPublicationService: Event emission
- DataTransferService: Port data transfer
- ValidationService: Pre-execution validation
- MetricsService: Performance tracking

Also uses domain services:
- ExecutionOrchestrator: Routing and path calculation
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from loguru import logger

from .protocols import (
    ExecutionResultData,
    WorkflowExecutionResult,
    IWorkflowExecutionService,
)
from .node_execution_service import NodeExecutionService
from .state_management_service import StateManagementService
from .event_publication_service import EventPublicationService
from .data_transfer_service import DataTransferService
from .validation_service import ValidationService
from .metrics_service import MetricsService

from ...domain.entities.workflow import WorkflowSchema
from ...domain.services.execution_orchestrator import ExecutionOrchestrator
from ...domain.value_objects.types import NodeId
from ...core.execution_context import ExecutionContext
from ...core.events import EventBus, get_event_bus


class ExecutionSettings:
    """
    Value object for execution configuration.

    Immutable settings for workflow execution.
    """
    __slots__ = (
        'continue_on_error', 'node_timeout', 'target_node_id',
        'debug_mode', 'step_mode'
    )

    def __init__(
        self,
        continue_on_error: bool = False,
        node_timeout: float = 120.0,
        target_node_id: Optional[NodeId] = None,
        debug_mode: bool = False,
        step_mode: bool = False
    ) -> None:
        self.continue_on_error = continue_on_error
        self.node_timeout = node_timeout
        self.target_node_id = target_node_id
        self.debug_mode = debug_mode
        self.step_mode = step_mode


class WorkflowExecutionService(IWorkflowExecutionService):
    """
    Main service for executing workflows.

    This service:
    1. Validates the workflow before execution
    2. Creates execution context with resources
    3. Iterates through nodes using ExecutionOrchestrator
    4. Delegates node execution to NodeExecutionService
    5. Manages pause/resume/stop via StateManagementService
    6. Publishes events via EventPublicationService
    7. Records metrics via MetricsService

    Reduced from 1,404 lines to ~300 lines through service extraction.
    """

    def __init__(
        self,
        workflow: WorkflowSchema,
        event_bus: Optional[EventBus] = None,
        settings: Optional[ExecutionSettings] = None,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None,
        # Dependency injection for testing
        node_execution_service: Optional[NodeExecutionService] = None,
        state_management_service: Optional[StateManagementService] = None,
        event_publication_service: Optional[EventPublicationService] = None,
        data_transfer_service: Optional[DataTransferService] = None,
        validation_service: Optional[ValidationService] = None,
        metrics_service: Optional[MetricsService] = None,
    ) -> None:
        """
        Initialize workflow execution service.

        Args:
            workflow: Workflow schema to execute
            event_bus: EventBus for progress updates
            settings: Execution configuration
            initial_variables: Initial variable values
            project_context: Project context for variable scoping
            *_service: Optional service overrides for testing
        """
        self.workflow = workflow
        self.settings = settings or ExecutionSettings()
        self._initial_variables = initial_variables or {}
        self._project_context = project_context

        # Initialize services (use provided or create defaults)
        self._node_execution = node_execution_service or NodeExecutionService(
            default_timeout=self.settings.node_timeout
        )
        self._state = state_management_service or StateManagementService()
        self._events = event_publication_service or EventPublicationService(
            event_bus=event_bus or get_event_bus()
        )
        self._data_transfer = data_transfer_service or DataTransferService()
        self._validation = validation_service or ValidationService()
        self._metrics = metrics_service or MetricsService()

        # Domain services
        self._orchestrator = ExecutionOrchestrator(workflow)

        # Execution state
        self._context: Optional[ExecutionContext] = None
        self._executed_nodes: Set[NodeId] = set()
        self._node_results: Dict[NodeId, ExecutionResultData] = {}
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

        # Run-to-node support
        self._subgraph_nodes: Optional[Set[NodeId]] = None
        self._target_reached = False

        # Calculate subgraph if target specified
        if self.settings.target_node_id:
            self._calculate_subgraph()

    def _calculate_subgraph(self) -> None:
        """Calculate subgraph for Run-To-Node execution."""
        start_node_id = self._orchestrator.find_start_node()
        if not start_node_id:
            logger.error("Cannot calculate subgraph: no StartNode found")
            return

        target = self.settings.target_node_id
        if not self._orchestrator.is_reachable(start_node_id, target):
            logger.error(f"Target node {target} is not reachable from StartNode")
            return

        self._subgraph_nodes = self._orchestrator.calculate_execution_path(
            start_node_id, target
        )
        logger.info(f"Subgraph calculated: {len(self._subgraph_nodes)} nodes")

    def _should_execute_node(self, node_id: NodeId) -> bool:
        """Check if node should be executed based on subgraph filter."""
        if self._subgraph_nodes is None:
            return True
        return node_id in self._subgraph_nodes

    @property
    def progress(self) -> float:
        """Get execution progress as percentage (0-100)."""
        total = len(self._subgraph_nodes) if self._subgraph_nodes else len(self.workflow.nodes)
        if total == 0:
            return 0.0
        return (len(self._executed_nodes) / total) * 100

    @property
    def total_nodes(self) -> int:
        """Get total nodes to execute."""
        return len(self._subgraph_nodes) if self._subgraph_nodes else len(self.workflow.nodes)

    async def execute(self) -> WorkflowExecutionResult:
        """
        Execute the workflow.

        Returns:
            Complete execution result with all node outcomes
        """
        workflow_name = self.workflow.metadata.name

        # Validate workflow
        is_valid, errors = self._validation.validate_workflow(self.workflow)
        if not is_valid:
            error_msg = f"Workflow validation failed: {'; '.join(errors)}"
            logger.error(error_msg)
            return WorkflowExecutionResult(
                workflow_name=workflow_name,
                success=False,
                error=error_msg,
                total_nodes=len(self.workflow.nodes),
                executed_nodes=0
            )

        # Initialize execution
        self._start_time = datetime.now()
        self._executed_nodes.clear()
        self._node_results.clear()
        self._target_reached = False

        # Start state management
        if not self._state.start():
            return WorkflowExecutionResult(
                workflow_name=workflow_name,
                success=False,
                error="Failed to start execution (already running?)",
                total_nodes=self.total_nodes,
                executed_nodes=0
            )

        # Create execution context
        self._context = ExecutionContext(
            workflow_name=workflow_name,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
        )

        # Publish start events and metrics
        await self._events.publish_workflow_started(workflow_name, self.total_nodes)
        self._metrics.record_workflow_start(workflow_name)

        logger.info(f"Starting workflow execution: {workflow_name}")

        try:
            # Find start node
            start_node_id = self._orchestrator.find_start_node()
            if not start_node_id:
                raise ValueError("No StartNode found in workflow")

            # Execute from start node
            await self._execute_from_node(start_node_id)

            # Determine final result
            return await self._finalize_execution()

        except Exception as e:
            self._state.error(str(e))
            self._end_time = datetime.now()
            execution_time_ms = self._calculate_execution_time_ms()

            logger.exception("Workflow execution failed with exception")

            await self._events.publish_workflow_error(
                workflow_name, str(e), len(self._executed_nodes)
            )
            self._metrics.record_workflow_complete(
                workflow_name, execution_time_ms, success=False
            )

            return WorkflowExecutionResult(
                workflow_name=workflow_name,
                success=False,
                node_results=self._node_results,
                total_nodes=self.total_nodes,
                executed_nodes=len(self._executed_nodes),
                execution_time_ms=execution_time_ms,
                started_at=self._start_time,
                completed_at=self._end_time,
                error=str(e)
            )

        finally:
            # Cleanup context resources
            await self._cleanup_context()

    async def _execute_from_node(self, start_node_id: NodeId) -> None:
        """
        Execute workflow starting from a specific node.

        Uses ExecutionOrchestrator for routing decisions.
        """
        nodes_to_execute: List[NodeId] = [start_node_id]

        while nodes_to_execute and not self._state.is_stopped:
            # Check for pause
            await self._state.check_pause()

            # Get next node
            current_node_id = nodes_to_execute.pop(0)

            # Skip if already executed (except control flow nodes)
            is_control_flow = self._orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in self._executed_nodes and not is_control_flow:
                continue

            # Skip if not in subgraph (Run-To-Node)
            if not self._should_execute_node(current_node_id):
                logger.debug(f"Skipping node {current_node_id} (not in subgraph)")
                continue

            # Get node instance
            node = self.workflow.nodes.get(current_node_id)
            if not node:
                logger.error(f"Node {current_node_id} not found")
                continue

            # Transfer input data
            self._data_transfer.transfer_all_inputs(
                current_node_id, self.workflow.nodes, self.workflow.connections
            )

            # Execute node
            result = await self._execute_single_node(node)

            # Handle failure
            if not result.success:
                if self.settings.continue_on_error:
                    logger.warning(
                        f"Node {current_node_id} failed but continue_on_error is enabled"
                    )
                else:
                    logger.warning(f"Stopping workflow due to node error: {current_node_id}")
                    break

            # Check if target reached
            if result.success and current_node_id == self.settings.target_node_id:
                self._target_reached = True
                logger.info(f"Target node {current_node_id} reached")
                break

            # Get next nodes from orchestrator
            raw_result = {"success": result.success, "data": result.data}
            if "next_nodes" in result.data:
                raw_result["next_nodes"] = result.data["next_nodes"]

            next_node_ids = self._orchestrator.get_next_nodes(current_node_id, raw_result)
            nodes_to_execute.extend(next_node_ids)

    async def _execute_single_node(self, node: Any) -> ExecutionResultData:
        """
        Execute a single node with full event/metrics handling.
        """
        node_id = node.node_id
        node_type = node.__class__.__name__

        # Check if disabled
        if self._node_execution.is_node_disabled(node):
            result = self._node_execution.execute_bypass(node)
            self._executed_nodes.add(node_id)
            self._node_results[node_id] = result

            await self._events.publish_node_completed(node_id, result, self.progress)
            return result

        # Publish node started
        await self._events.publish_node_started(node_id, node_type)
        self._metrics.record_node_start(node_type, node_id)

        # Validate node
        is_valid, error = self._validation.validate_node(node)
        if not is_valid:
            result = ExecutionResultData(
                node_id=node_id,
                success=False,
                error=error or "Validation failed"
            )
            await self._events.publish_node_error(node_id, result.error or "")
            return result

        # Execute node
        result = await self._node_execution.execute(
            node, self._context, self.settings.node_timeout
        )

        # Record result
        self._node_results[node_id] = result

        if result.success:
            self._executed_nodes.add(node_id)
            await self._events.publish_node_completed(node_id, result, self.progress)
        else:
            await self._events.publish_node_error(
                node_id, result.error or "Unknown error", result.execution_time_ms
            )

        # Record metrics
        self._metrics.record_node_complete(
            node_type, node_id, result.execution_time_ms, result.success
        )

        return result

    async def _finalize_execution(self) -> WorkflowExecutionResult:
        """Finalize execution and create result."""
        workflow_name = self.workflow.metadata.name
        self._end_time = datetime.now()
        execution_time_ms = self._calculate_execution_time_ms()

        if self._state.is_stopped:
            self._state.complete()  # Mark as finished

            await self._events.publish_workflow_stopped(
                workflow_name, len(self._executed_nodes), self.total_nodes
            )
            self._metrics.record_workflow_complete(
                workflow_name, execution_time_ms, success=False
            )

            logger.info("Workflow execution stopped by user")

            return WorkflowExecutionResult(
                workflow_name=workflow_name,
                success=False,
                node_results=self._node_results,
                total_nodes=self.total_nodes,
                executed_nodes=len(self._executed_nodes),
                execution_time_ms=execution_time_ms,
                started_at=self._start_time,
                completed_at=self._end_time,
                stopped_by_user=True
            )

        # Successful completion
        self._state.complete()

        await self._events.publish_workflow_completed(WorkflowExecutionResult(
            workflow_name=workflow_name,
            success=True,
            node_results=self._node_results,
            total_nodes=self.total_nodes,
            executed_nodes=len(self._executed_nodes),
            execution_time_ms=execution_time_ms,
            started_at=self._start_time,
            completed_at=self._end_time
        ))
        self._metrics.record_workflow_complete(
            workflow_name, execution_time_ms, success=True
        )

        logger.info(
            f"Workflow completed in {execution_time_ms/1000:.2f}s "
            f"({len(self._executed_nodes)} nodes)"
        )

        return WorkflowExecutionResult(
            workflow_name=workflow_name,
            success=True,
            node_results=self._node_results,
            total_nodes=self.total_nodes,
            executed_nodes=len(self._executed_nodes),
            execution_time_ms=execution_time_ms,
            started_at=self._start_time,
            completed_at=self._end_time
        )

    def _calculate_execution_time_ms(self) -> float:
        """Calculate total execution time in milliseconds."""
        if self._start_time is None:
            return 0.0
        end = self._end_time or datetime.now()
        return (end - self._start_time).total_seconds() * 1000

    async def _cleanup_context(self) -> None:
        """Cleanup execution context resources."""
        if self._context:
            try:
                await asyncio.wait_for(
                    self._context.cleanup(), timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.error("Context cleanup timed out after 30 seconds")
            except Exception as e:
                logger.error(f"Error during context cleanup: {e}")

    # Control methods delegate to StateManagementService

    def pause(self) -> bool:
        """Pause workflow execution."""
        return self._state.pause()

    def resume(self) -> bool:
        """Resume paused execution."""
        return self._state.resume()

    def stop(self) -> None:
        """Stop workflow execution."""
        self._state.stop()
```

**Acceptance Criteria**:
- [ ] Composes all 6 services via dependency injection
- [ ] Reduced to ~300 lines (from 1,404)
- [ ] Full test coverage via mock services
- [ ] Maintains backward compatibility with existing events
- [ ] Handles Run-To-Node feature

---

### Phase 4: Testing and Validation (Hour 7-8)

#### Task 4.1: Unit Tests for Services (1 hour)

**File**: `tests/application/services/test_node_execution_service.py`

```python
"""
Unit tests for NodeExecutionService.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from casare_rpa.application.services.node_execution_service import (
    NodeExecutionService,
    NodeExecutionError,
)
from casare_rpa.application.services.protocols import ExecutionResultData
from casare_rpa.domain.value_objects.types import NodeStatus


class TestNodeExecutionService:
    """Tests for NodeExecutionService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return NodeExecutionService(default_timeout=5.0)

    @pytest.fixture
    def mock_node(self):
        """Create mock node."""
        node = Mock()
        node.node_id = "test_node_1"
        node.status = NodeStatus.IDLE
        node.config = {}
        node.execution_count = 0
        node.last_execution_time = 0
        node.last_output = None
        node.error_message = None
        return node

    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        return Mock()

    @pytest.mark.asyncio
    async def test_execute_success(self, service, mock_node, mock_context):
        """Test successful node execution."""
        mock_node.execute = AsyncMock(return_value={
            "success": True,
            "data": {"message": "Done"}
        })

        result = await service.execute(mock_node, mock_context)

        assert result.success is True
        assert result.node_id == "test_node_1"
        assert result.error is None
        assert result.execution_time_ms > 0
        assert mock_node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_failure(self, service, mock_node, mock_context):
        """Test failed node execution."""
        mock_node.execute = AsyncMock(return_value={
            "success": False,
            "error": "Something went wrong"
        })

        result = await service.execute(mock_node, mock_context)

        assert result.success is False
        assert result.error == "Something went wrong"
        assert mock_node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_execute_timeout(self, service, mock_node, mock_context):
        """Test node execution timeout."""
        async def slow_execute(ctx):
            await asyncio.sleep(10)  # Longer than timeout
            return {"success": True}

        mock_node.execute = slow_execute

        result = await service.execute(mock_node, mock_context, timeout_seconds=0.1)

        assert result.success is False
        assert "timed out" in result.error
        assert mock_node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_execute_exception(self, service, mock_node, mock_context):
        """Test node execution exception handling."""
        mock_node.execute = AsyncMock(side_effect=ValueError("Test error"))

        result = await service.execute(mock_node, mock_context)

        assert result.success is False
        assert "Test error" in result.error
        assert mock_node.status == NodeStatus.ERROR

    def test_execute_bypass_disabled_node(self, service, mock_node):
        """Test bypassing disabled node."""
        mock_node.config = {"_disabled": True}

        assert service.is_node_disabled(mock_node) is True

        result = service.execute_bypass(mock_node)

        assert result.success is True
        assert result.data.get("bypassed") is True
        assert mock_node.status == NodeStatus.SUCCESS


class TestStateManagementService:
    """Tests for StateManagementService."""

    @pytest.fixture
    def service(self):
        from casare_rpa.application.services.state_management_service import (
            StateManagementService,
            ExecutionStateEnum,
        )
        return StateManagementService()

    def test_initial_state_is_idle(self, service):
        """Test service starts in IDLE state."""
        from casare_rpa.application.services.state_management_service import (
            ExecutionStateEnum,
        )
        assert service.state == ExecutionStateEnum.IDLE
        assert service.is_idle is True

    def test_start_transitions_to_running(self, service):
        """Test start() transitions to RUNNING."""
        result = service.start()

        assert result is True
        assert service.is_running is True
        assert service.is_stopped is False

    def test_pause_and_resume(self, service):
        """Test pause/resume cycle."""
        service.start()

        # Pause
        result = service.pause()
        assert result is True
        assert service.is_paused is True

        # Resume
        result = service.resume()
        assert result is True
        assert service.is_running is True

    def test_stop_from_running(self, service):
        """Test stop from running state."""
        service.start()
        service.stop()

        assert service.is_stopped is True

    def test_stop_unblocks_paused(self, service):
        """Test stop unblocks paused execution."""
        service.start()
        service.pause()
        service.stop()

        assert service.is_stopped is True
        # The pause event should be set (unblocked)
        assert service._pause_event.is_set()

    @pytest.mark.asyncio
    async def test_check_pause_blocks_when_paused(self, service):
        """Test check_pause blocks when paused."""
        service.start()
        service.pause()

        # check_pause should block, so we need to resume in background
        async def resume_later():
            await asyncio.sleep(0.1)
            service.resume()

        asyncio.create_task(resume_later())
        await service.check_pause()  # Should unblock after resume

        assert service.is_running is True


class TestEventPublicationService:
    """Tests for EventPublicationService."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        return Mock()

    @pytest.fixture
    def service(self, mock_event_bus):
        from casare_rpa.application.services.event_publication_service import (
            EventPublicationService,
        )
        return EventPublicationService(event_bus=mock_event_bus)

    @pytest.mark.asyncio
    async def test_publish_node_started(self, service, mock_event_bus):
        """Test publishing node started event."""
        await service.publish_node_started("node_1", "TestNode")

        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.data["node_id"] == "node_1"
        assert event.data["node_type"] == "TestNode"

    @pytest.mark.asyncio
    async def test_publish_handles_event_bus_error(self, service, mock_event_bus):
        """Test that event bus errors are caught."""
        mock_event_bus.publish.side_effect = Exception("Event bus error")

        # Should not raise
        await service.publish_node_started("node_1", "TestNode")


class TestDataTransferService:
    """Tests for DataTransferService."""

    @pytest.fixture
    def service(self):
        from casare_rpa.application.services.data_transfer_service import (
            DataTransferService,
        )
        return DataTransferService(debug_logging=False)

    def test_transfer_success(self, service):
        """Test successful data transfer."""
        source = Mock()
        source.node_id = "source_1"
        source.get_output_value = Mock(return_value="test_value")

        target = Mock()
        target.node_id = "target_1"

        result = service.transfer(source, target, "output", "input")

        assert result is True
        target.set_input_value.assert_called_once_with("input", "test_value")

    def test_transfer_none_value(self, service):
        """Test transfer with None value (no-op)."""
        source = Mock()
        source.get_output_value = Mock(return_value=None)
        target = Mock()

        result = service.transfer(source, target, "output", "input")

        assert result is False
        target.set_input_value.assert_not_called()

    def test_transfer_all_inputs(self, service):
        """Test transfer_all_inputs finds all connections."""
        source = Mock()
        source.get_output_value = Mock(return_value="value")

        target = Mock()
        target.node_id = "target_1"

        nodes = {"source_1": source, "target_1": target}

        connection = Mock()
        connection.source_node = "source_1"
        connection.target_node = "target_1"
        connection.source_port = "out"
        connection.target_port = "in"

        count = service.transfer_all_inputs("target_1", nodes, [connection])

        assert count == 1


class TestWorkflowExecutionService:
    """Integration tests for WorkflowExecutionService."""

    @pytest.fixture
    def mock_workflow(self):
        """Create mock workflow."""
        workflow = Mock()
        workflow.metadata = Mock()
        workflow.metadata.name = "Test Workflow"
        workflow.nodes = {}
        workflow.connections = []
        return workflow

    @pytest.fixture
    def mock_services(self):
        """Create mock services for dependency injection."""
        from casare_rpa.application.services.node_execution_service import NodeExecutionService
        from casare_rpa.application.services.state_management_service import StateManagementService
        from casare_rpa.application.services.event_publication_service import EventPublicationService
        from casare_rpa.application.services.data_transfer_service import DataTransferService
        from casare_rpa.application.services.validation_service import ValidationService
        from casare_rpa.application.services.metrics_service import MetricsService

        return {
            "node_execution_service": Mock(spec=NodeExecutionService),
            "state_management_service": Mock(spec=StateManagementService),
            "event_publication_service": Mock(spec=EventPublicationService),
            "data_transfer_service": Mock(spec=DataTransferService),
            "validation_service": Mock(spec=ValidationService),
            "metrics_service": Mock(spec=MetricsService),
        }

    @pytest.mark.asyncio
    async def test_execute_validates_workflow(self, mock_workflow, mock_services):
        """Test that execute validates workflow first."""
        from casare_rpa.application.services.workflow_execution_service import (
            WorkflowExecutionService,
        )

        mock_services["validation_service"].validate_workflow = Mock(
            return_value=(False, ["No StartNode"])
        )

        service = WorkflowExecutionService(
            workflow=mock_workflow,
            **mock_services
        )

        result = await service.execute()

        assert result.success is False
        assert "validation failed" in result.error.lower()
```

**Acceptance Criteria**:
- [ ] Unit tests for all 6 services
- [ ] Mock-based testing for isolation
- [ ] Async test support with pytest-asyncio
- [ ] Edge cases covered (timeout, errors, None values)

---

## File Structure Summary

```
src/casare_rpa/application/services/
    __init__.py                      # Module exports
    protocols.py                     # Service interfaces and value objects
    node_execution_service.py        # Single node execution (~150 lines)
    state_management_service.py      # Pause/Resume/Stop (~120 lines)
    event_publication_service.py     # Event emission (~180 lines)
    data_transfer_service.py         # Port data transfer (~100 lines)
    validation_service.py            # Pre-execution validation (~100 lines)
    metrics_service.py               # Performance metrics (~80 lines)
    workflow_execution_service.py    # Main orchestration (~300 lines)

tests/application/services/
    __init__.py
    test_node_execution_service.py
    test_state_management_service.py
    test_event_publication_service.py
    test_data_transfer_service.py
    test_validation_service.py
    test_metrics_service.py
    test_workflow_execution_service.py
```

---

## Dependencies and Prerequisites

### Day 1 Dependencies (Must Be Complete)

1. **Domain Entities** (from REFACTORING_ROADMAP.md Day 1):
   - `src/casare_rpa/domain/entities/workflow.py` - WorkflowSchema
   - `src/casare_rpa/domain/entities/execution_state.py` - ExecutionState
   - `src/casare_rpa/domain/value_objects/types.py` - NodeId, NodeStatus, EventType

2. **Domain Services**:
   - `src/casare_rpa/domain/services/execution_orchestrator.py` - ExecutionOrchestrator

### External Dependencies

1. **Python Standard Library**:
   - `asyncio` - Async execution and timeout
   - `datetime` - Timestamp handling
   - `enum` - State enums
   - `typing` - Type hints

2. **Third-Party**:
   - `loguru` - Logging

3. **Internal (Infrastructure)**:
   - `core.execution_context.ExecutionContext` - Resource management
   - `core.events.EventBus` - Event publication
   - `utils.performance.performance_metrics` - Metrics collection

---

## Success Criteria and Validation

### Unit Test Requirements

| Service | Test Count | Coverage Target |
|---------|------------|-----------------|
| NodeExecutionService | 8 | 95% |
| StateManagementService | 6 | 95% |
| EventPublicationService | 5 | 90% |
| DataTransferService | 4 | 95% |
| ValidationService | 4 | 90% |
| MetricsService | 4 | 90% |
| WorkflowExecutionService | 6 | 85% |

### Integration Test Scenarios

1. **Simple Workflow Execution**:
   - Start -> Action -> End
   - Verify all events emitted
   - Verify metrics recorded

2. **Pause/Resume/Stop**:
   - Start execution
   - Pause mid-workflow
   - Resume and complete

3. **Error Handling**:
   - Node failure with continue_on_error=False
   - Node failure with continue_on_error=True

4. **Run-To-Node**:
   - Execute subgraph to target
   - Verify only subgraph nodes executed

### Performance Benchmarks

| Metric | Target |
|--------|--------|
| Service instantiation | < 1ms |
| Node execution overhead | < 5ms |
| Event publication | < 1ms |
| State transition | < 0.1ms |

---

## Risk Assessment and Mitigation

### High Risk

1. **Circular Dependency Between Services**
   - Risk: Services importing each other
   - Mitigation: Use protocols for type hints, inject dependencies

2. **Async State Management**
   - Risk: Race conditions in pause/resume
   - Mitigation: Use asyncio.Event for thread-safe signaling

3. **Breaking Existing UI**
   - Risk: Event data structure changes
   - Mitigation: Keep exact same event data format

### Medium Risk

1. **Performance Regression**
   - Risk: Additional service call overhead
   - Mitigation: Benchmark before/after

2. **Test Isolation**
   - Risk: Tests affecting global state
   - Mitigation: Mock all external dependencies

### Low Risk

1. **Logging Verbosity**
   - Risk: Too many debug logs
   - Mitigation: Use appropriate log levels

---

## Implementation Guide for rpa-engine-architect

### Recommended Implementation Order

1. **First** (Foundation):
   - `protocols.py` - All interfaces defined
   - `__init__.py` - Module structure

2. **Second** (Core Services):
   - `state_management_service.py` - No dependencies
   - `metrics_service.py` - Simple wrapper
   - `data_transfer_service.py` - Simple logic

3. **Third** (Event/Validation):
   - `event_publication_service.py` - Depends on protocols
   - `validation_service.py` - Depends on ExecutionOrchestrator

4. **Fourth** (Execution):
   - `node_execution_service.py` - Core execution logic
   - `workflow_execution_service.py` - Composes all services

5. **Fifth** (Testing):
   - Write tests as you implement each service
   - Integration tests after all services complete

### Code Review Checkpoints

1. **After protocols.py**: Review interfaces for completeness
2. **After each service**: Review for single responsibility
3. **After workflow_execution_service.py**: Full integration review
4. **After all tests pass**: Performance benchmark review

### Testing Strategy

1. **Unit Tests First**: Write tests before implementation
2. **Mock Dependencies**: Use unittest.mock for isolation
3. **Async Testing**: Use pytest-asyncio for async tests
4. **Integration Last**: Full workflow tests after all units pass

---

## Appendix: Quick Reference

### Service Responsibility Matrix

| Service | Responsibility | Dependencies |
|---------|---------------|--------------|
| NodeExecutionService | Execute one node | None |
| StateManagementService | Pause/Resume/Stop | None |
| EventPublicationService | Emit events | EventBus |
| DataTransferService | Port-to-port data | None |
| ValidationService | Pre-execution checks | ExecutionOrchestrator |
| MetricsService | Performance tracking | PerformanceMetrics |
| WorkflowExecutionService | Orchestration | All above |

### Key Patterns Used

1. **Protocol Pattern**: Interfaces for dependency injection
2. **Composition**: WorkflowExecutionService composes other services
3. **Value Objects**: ExecutionResultData, WorkflowExecutionResult
4. **State Machine**: StateManagementService state transitions
5. **Async/Await**: All execution methods are async

### Import Guidelines

```python
# Domain imports (allowed)
from ...domain.entities.workflow import WorkflowSchema
from ...domain.services.execution_orchestrator import ExecutionOrchestrator
from ...domain.value_objects.types import NodeId, NodeStatus, EventType

# Infrastructure imports (minimal, inject when possible)
from ...core.execution_context import ExecutionContext
from ...core.events import EventBus, get_event_bus
from ...utils.performance.performance_metrics import get_metrics

# NEVER import directly in service:
# - Playwright
# - PySide6
# - Other services (use protocols)
```

---

**Document End**

This plan should take approximately 8 hours to implement. The rpa-engine-architect should follow the phases in order and use the checkpoints to validate progress.
