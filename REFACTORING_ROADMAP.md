# CasareRPA Refactoring Roadmap

**Version**: 2.0.0
**Created**: November 27, 2025
**Target Completion**: December 18, 2025 (3 weeks)

---

## Executive Summary

This roadmap outlines the architectural refactoring of CasareRPA from a monolithic codebase to a clean architecture pattern. The refactoring focuses on the Canvas (Designer) component, targeting a 90%+ improvement in code navigability while maintaining backward compatibility until v3.0.

### Key Metrics

| Component | Current | Target | Improvement |
|-----------|---------|--------|-------------|
| Visual Nodes | 3,793 lines (1 file) | 141 nodes (26 files) | 95% navigation improvement ✅ |
| WorkflowRunner | 1,404 lines | 200 lines + 8 classes | 86% reduction |
| MainWindow | 2,417 lines | 400 lines + 7 controllers | 83% reduction |
| CasareRPAApp | 2,929 lines | 400 lines + 9 components | 86% reduction |
| Node Status Pattern | 386 occurrences | Migrate to ExecutionResult | 100% migration |

### Architectural Vision

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  (Canvas UI: MainWindow, NodeGraph, Panels, Dialogs)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (Use Cases: RunWorkflow, ValidateWorkflow, SaveWorkflow)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  (Entities: Workflow, Node, Connection | Pure Logic)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▲
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  (Execution Engine, File Persistence, Playwright Adapter)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Week 1: Foundation & Navigation Relief ✅ COMPLETED

**Status**: Complete
**Completion Date**: November 27, 2025

### Accomplished

1. **Visual Nodes Organization** ✅
   - Split 3,793-line monolith into 141 nodes across 12 categories
   - Created category-based directory structure
   - Implemented compatibility layer for backward compatibility
   - Added 6 smoke tests (all passing)

2. **Clean Architecture Directories** ✅
   - Created `domain/`, `application/`, `infrastructure/`, `presentation/` layers
   - Established dependency flow patterns
   - Added placeholder `__init__.py` files

3. **GitHub Community Health** ✅
   - Added LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
   - Updated pyproject.toml with proper dependencies
   - Fixed version constraints for stability

4. **ExecutionResult Migration - Phase 1** ✅
   - Migrated 32 data operation nodes to ExecutionResult pattern
   - Pattern: `{"success": bool, "data": dict, "error": str, "next_nodes": list}`

### Remaining Work

- 20+ node modules still using NodeStatus pattern (354 occurrences)
- WorkflowRunner still 1,404 lines (needs decomposition)
- MainWindow still 2,417 lines (needs controller extraction)
- CasareRPAApp still 2,929 lines (needs component extraction)

---

## Week 2: Domain Entities & Runner Refactoring

**Goal**: Extract domain entities, refactor WorkflowRunner to clean architecture
**Target**: 1,404 → 200 lines + 8 extracted classes

### Day 1: Domain Entities Extraction

**Objective**: Create pure domain entities with zero infrastructure dependencies

#### Tasks

1. **Create Domain Entities** (4-6 hours)

   **Files to Create**:
   - `src/casare_rpa/domain/entities/workflow.py`
   - `src/casare_rpa/domain/entities/node.py`
   - `src/casare_rpa/domain/entities/connection.py`
   - `src/casare_rpa/domain/entities/execution_state.py`
   - `src/casare_rpa/domain/entities/execution_event.py`

   **Implementation**:

   ```python
   # src/casare_rpa/domain/entities/workflow.py
   """
   Domain entity representing a workflow.
   Pure business logic - no infrastructure dependencies.
   """
   from dataclasses import dataclass, field
   from typing import Dict, List, Optional, Set
   from datetime import datetime

   from .node import Node
   from .connection import Connection


   @dataclass
   class WorkflowMetadata:
       """Metadata about a workflow."""
       name: str
       description: str = ""
       author: str = ""
       version: str = "1.0.0"
       created_at: datetime = field(default_factory=datetime.now)
       modified_at: datetime = field(default_factory=datetime.now)
       tags: List[str] = field(default_factory=list)


   @dataclass
   class Workflow:
       """
       Represents a workflow with nodes and connections.

       This is a pure domain entity - it knows nothing about:
       - How workflows are persisted (JSON, DB, etc.)
       - How workflows are executed (WorkflowRunner)
       - How workflows are displayed (NodeGraph UI)
       """

       metadata: WorkflowMetadata
       nodes: Dict[str, Node] = field(default_factory=dict)
       connections: List[Connection] = field(default_factory=list)

       def add_node(self, node: Node) -> None:
           """Add a node to the workflow."""
           if node.node_id in self.nodes:
               raise ValueError(f"Node {node.node_id} already exists")
           self.nodes[node.node_id] = node

       def remove_node(self, node_id: str) -> None:
           """Remove a node and its connections."""
           if node_id not in self.nodes:
               raise ValueError(f"Node {node_id} not found")

           # Remove connections involving this node
           self.connections = [
               conn for conn in self.connections
               if node_id not in (conn.source_node_id, conn.target_node_id)
           ]

           del self.nodes[node_id]

       def add_connection(self, connection: Connection) -> None:
           """Add a connection between nodes."""
           # Validate nodes exist
           if connection.source_node_id not in self.nodes:
               raise ValueError(f"Source node {connection.source_node_id} not found")
           if connection.target_node_id not in self.nodes:
               raise ValueError(f"Target node {connection.target_node_id} not found")

           # Prevent duplicate connections
           if connection in self.connections:
               raise ValueError("Connection already exists")

           self.connections.append(connection)

       def get_start_nodes(self) -> List[Node]:
           """Get all start nodes (nodes with no incoming connections)."""
           nodes_with_inputs = {
               conn.target_node_id for conn in self.connections
           }
           return [
               node for node_id, node in self.nodes.items()
               if node_id not in nodes_with_inputs and node.node_type == "Start"
           ]

       def get_next_nodes(self, node_id: str) -> List[Node]:
           """Get nodes connected to this node's outputs."""
           next_node_ids = [
               conn.target_node_id
               for conn in self.connections
               if conn.source_node_id == node_id
           ]
           return [self.nodes[nid] for nid in next_node_ids if nid in self.nodes]

       def validate(self) -> List[str]:
           """
           Validate workflow structure.

           Returns:
               List of validation error messages (empty if valid)
           """
           errors = []

           # Must have at least one start node
           start_nodes = self.get_start_nodes()
           if not start_nodes:
               errors.append("Workflow must have at least one Start node")

           # Check for cycles (DAG validation)
           if self._has_cycle():
               errors.append("Workflow contains circular dependencies")

           # Check for unreachable nodes
           unreachable = self._get_unreachable_nodes()
           if unreachable:
               errors.append(f"Unreachable nodes: {', '.join(unreachable)}")

           return errors

       def _has_cycle(self) -> bool:
           """Check if workflow has circular dependencies using DFS."""
           visited: Set[str] = set()
           rec_stack: Set[str] = set()

           def dfs(node_id: str) -> bool:
               visited.add(node_id)
               rec_stack.add(node_id)

               for next_node in self.get_next_nodes(node_id):
                   if next_node.node_id not in visited:
                       if dfs(next_node.node_id):
                           return True
                   elif next_node.node_id in rec_stack:
                       return True

               rec_stack.remove(node_id)
               return False

           for node_id in self.nodes:
               if node_id not in visited:
                   if dfs(node_id):
                       return True

           return False

       def _get_unreachable_nodes(self) -> List[str]:
           """Get nodes that are not reachable from any start node."""
           reachable: Set[str] = set()

           def dfs(node_id: str) -> None:
               reachable.add(node_id)
               for next_node in self.get_next_nodes(node_id):
                   if next_node.node_id not in reachable:
                       dfs(next_node.node_id)

           for start_node in self.get_start_nodes():
               dfs(start_node.node_id)

           return [
               node_id for node_id in self.nodes
               if node_id not in reachable
           ]
   ```

   ```python
   # src/casare_rpa/domain/entities/node.py
   """
   Domain entity representing a workflow node.
   """
   from dataclasses import dataclass, field
   from typing import Any, Dict, Optional
   from enum import Enum, auto


   class NodeStatus(Enum):
       """Execution status of a node."""
       IDLE = auto()
       RUNNING = auto()
       SUCCESS = auto()
       ERROR = auto()
       SKIPPED = auto()
       CANCELLED = auto()


   @dataclass
   class Node:
       """
       Represents a single node in a workflow.

       Pure domain entity - no infrastructure dependencies.
       """

       node_id: str
       node_type: str
       config: Dict[str, Any] = field(default_factory=dict)

       # Execution state
       status: NodeStatus = NodeStatus.IDLE
       error_message: Optional[str] = None

       # Position (for visual display)
       x_pos: float = 0.0
       y_pos: float = 0.0

       def reset(self) -> None:
           """Reset node to initial state."""
           self.status = NodeStatus.IDLE
           self.error_message = None

       def mark_running(self) -> None:
           """Mark node as currently executing."""
           self.status = NodeStatus.RUNNING
           self.error_message = None

       def mark_success(self) -> None:
           """Mark node as successfully completed."""
           self.status = NodeStatus.SUCCESS
           self.error_message = None

       def mark_error(self, error: str) -> None:
           """Mark node as failed with error message."""
           self.status = NodeStatus.ERROR
           self.error_message = error

       def mark_skipped(self) -> None:
           """Mark node as skipped (conditional logic)."""
           self.status = NodeStatus.SKIPPED
   ```

   ```python
   # src/casare_rpa/domain/entities/connection.py
   """
   Domain entity representing a connection between nodes.
   """
   from dataclasses import dataclass


   @dataclass(frozen=True)
   class Connection:
       """
       Represents a connection between two nodes.

       Immutable to ensure workflow integrity.
       """

       source_node_id: str
       source_port: str
       target_node_id: str
       target_port: str

       def __str__(self) -> str:
           return (
               f"{self.source_node_id}.{self.source_port} → "
               f"{self.target_node_id}.{self.target_port}"
           )
   ```

   ```python
   # src/casare_rpa/domain/entities/execution_state.py
   """
   Domain entity for tracking workflow execution state.
   """
   from dataclasses import dataclass, field
   from typing import Dict, List, Any, Optional
   from datetime import datetime
   from enum import Enum, auto


   class ExecutionStatus(Enum):
       """Status of workflow execution."""
       IDLE = "idle"
       RUNNING = "running"
       PAUSED = "paused"
       STOPPED = "stopped"
       COMPLETED = "completed"
       ERROR = "error"


   @dataclass
   class NodeExecutionResult:
       """Result of executing a single node."""
       node_id: str
       success: bool
       data: Dict[str, Any] = field(default_factory=dict)
       error: Optional[str] = None
       execution_time: float = 0.0
       timestamp: datetime = field(default_factory=datetime.now)


   @dataclass
   class ExecutionState:
       """
       Tracks the state of a workflow execution.

       Pure domain entity - no infrastructure dependencies.
       """

       workflow_id: str
       status: ExecutionStatus = ExecutionStatus.IDLE

       # Execution tracking
       current_node_id: Optional[str] = None
       executed_nodes: List[str] = field(default_factory=list)
       node_results: Dict[str, NodeExecutionResult] = field(default_factory=dict)

       # Variables (execution context)
       variables: Dict[str, Any] = field(default_factory=dict)

       # Timing
       started_at: Optional[datetime] = None
       completed_at: Optional[datetime] = None

       def start(self) -> None:
           """Mark execution as started."""
           self.status = ExecutionStatus.RUNNING
           self.started_at = datetime.now()

       def complete(self) -> None:
           """Mark execution as completed."""
           self.status = ExecutionStatus.COMPLETED
           self.completed_at = datetime.now()

       def pause(self) -> None:
           """Pause execution."""
           if self.status == ExecutionStatus.RUNNING:
               self.status = ExecutionStatus.PAUSED

       def resume(self) -> None:
           """Resume paused execution."""
           if self.status == ExecutionStatus.PAUSED:
               self.status = ExecutionStatus.RUNNING

       def stop(self) -> None:
           """Stop execution."""
           self.status = ExecutionStatus.STOPPED
           self.completed_at = datetime.now()

       def error(self, error_message: str) -> None:
           """Mark execution as failed."""
           self.status = ExecutionStatus.ERROR
           self.completed_at = datetime.now()

       def record_node_execution(self, result: NodeExecutionResult) -> None:
           """Record the result of a node execution."""
           self.executed_nodes.append(result.node_id)
           self.node_results[result.node_id] = result
           self.current_node_id = result.node_id

       @property
       def execution_time(self) -> float:
           """Get total execution time in seconds."""
           if self.started_at is None:
               return 0.0

           end_time = self.completed_at or datetime.now()
           return (end_time - self.started_at).total_seconds()
   ```

2. **Create Domain Ports (Interfaces)** (2-3 hours)

   **Files to Create**:
   - `src/casare_rpa/domain/ports/workflow_repository.py`
   - `src/casare_rpa/domain/ports/execution_engine.py`
   - `src/casare_rpa/domain/ports/event_publisher.py`

   ```python
   # src/casare_rpa/domain/ports/workflow_repository.py
   """
   Port (interface) for workflow persistence.

   This is the dependency inversion principle in action:
   Domain defines WHAT it needs, Infrastructure implements HOW.
   """
   from abc import ABC, abstractmethod
   from typing import List, Optional
   from pathlib import Path

   from ..entities.workflow import Workflow


   class WorkflowRepository(ABC):
       """
       Abstract interface for workflow storage.

       Implementations can be:
       - JSON file storage (current)
       - Database storage (future)
       - Remote API storage (future)
       """

       @abstractmethod
       async def save(self, workflow: Workflow, path: Path) -> None:
           """Save workflow to storage."""
           pass

       @abstractmethod
       async def load(self, path: Path) -> Workflow:
           """Load workflow from storage."""
           pass

       @abstractmethod
       async def exists(self, path: Path) -> bool:
           """Check if workflow exists at path."""
           pass

       @abstractmethod
       async def list_workflows(self, directory: Path) -> List[Path]:
           """List all workflows in directory."""
           pass
   ```

   ```python
   # src/casare_rpa/domain/ports/execution_engine.py
   """
   Port (interface) for workflow execution.
   """
   from abc import ABC, abstractmethod
   from typing import Optional, Dict, Any

   from ..entities.workflow import Workflow
   from ..entities.execution_state import ExecutionState, NodeExecutionResult


   class ExecutionEngine(ABC):
       """
       Abstract interface for executing workflows.

       Separates WHAT to execute (domain) from HOW to execute (infrastructure).
       """

       @abstractmethod
       async def execute_workflow(
           self,
           workflow: Workflow,
           initial_variables: Optional[Dict[str, Any]] = None
       ) -> ExecutionState:
           """Execute a workflow and return final state."""
           pass

       @abstractmethod
       async def execute_node(
           self,
           workflow: Workflow,
           node_id: str,
           state: ExecutionState
       ) -> NodeExecutionResult:
           """Execute a single node."""
           pass

       @abstractmethod
       async def pause(self) -> None:
           """Pause execution."""
           pass

       @abstractmethod
       async def resume(self) -> None:
           """Resume paused execution."""
           pass

       @abstractmethod
       async def stop(self) -> None:
           """Stop execution."""
           pass
   ```

3. **Update Domain __init__.py** (30 min)

   ```python
   # src/casare_rpa/domain/__init__.py
   """
   Domain layer - Pure business logic.

   This layer has ZERO dependencies on:
   - UI frameworks (Qt, PySide6)
   - Persistence mechanisms (JSON, DB)
   - External libraries (Playwright, etc.)

   All dependencies point INWARD to this layer.
   """

   from .entities.workflow import Workflow, WorkflowMetadata
   from .entities.node import Node, NodeStatus
   from .entities.connection import Connection
   from .entities.execution_state import (
       ExecutionState,
       ExecutionStatus,
       NodeExecutionResult,
   )

   from .ports.workflow_repository import WorkflowRepository
   from .ports.execution_engine import ExecutionEngine

   __all__ = [
       # Entities
       "Workflow",
       "WorkflowMetadata",
       "Node",
       "NodeStatus",
       "Connection",
       "ExecutionState",
       "ExecutionStatus",
       "NodeExecutionResult",

       # Ports
       "WorkflowRepository",
       "ExecutionEngine",
   ]
   ```

#### Success Criteria

- [ ] All domain entity files created and type-check with mypy
- [ ] Zero imports from infrastructure/presentation in domain layer
- [ ] Domain entities have comprehensive docstrings
- [ ] Unit tests for Workflow validation logic
- [ ] Domain layer can be imported independently

#### Testing

```python
# tests/domain/test_workflow_entity.py
"""Tests for domain Workflow entity."""
import pytest
from casare_rpa.domain import Workflow, WorkflowMetadata, Node, Connection


def test_workflow_add_node():
    """Test adding nodes to workflow."""
    workflow = Workflow(metadata=WorkflowMetadata(name="Test"))
    node = Node(node_id="node1", node_type="Start")

    workflow.add_node(node)

    assert "node1" in workflow.nodes
    assert workflow.nodes["node1"] == node


def test_workflow_duplicate_node_raises_error():
    """Test that adding duplicate node raises error."""
    workflow = Workflow(metadata=WorkflowMetadata(name="Test"))
    node = Node(node_id="node1", node_type="Start")

    workflow.add_node(node)

    with pytest.raises(ValueError, match="already exists"):
        workflow.add_node(node)


def test_workflow_validate_requires_start_node():
    """Test validation requires start node."""
    workflow = Workflow(metadata=WorkflowMetadata(name="Test"))

    errors = workflow.validate()

    assert len(errors) > 0
    assert any("Start" in error for error in errors)


def test_workflow_detect_cycle():
    """Test cycle detection in workflow."""
    workflow = Workflow(metadata=WorkflowMetadata(name="Test"))

    # Create cycle: A → B → C → A
    node_a = Node(node_id="A", node_type="Start")
    node_b = Node(node_id="B", node_type="Action")
    node_c = Node(node_id="C", node_type="Action")

    workflow.add_node(node_a)
    workflow.add_node(node_b)
    workflow.add_node(node_c)

    workflow.add_connection(Connection("A", "out", "B", "in"))
    workflow.add_connection(Connection("B", "out", "C", "in"))
    workflow.add_connection(Connection("C", "out", "A", "in"))  # Cycle!

    errors = workflow.validate()

    assert any("circular" in error.lower() for error in errors)
```

---

### Day 2: WorkflowRunner Decomposition

**Objective**: Refactor 1,404-line WorkflowRunner into 200 lines + 8 extracted classes

#### Current State Analysis

**WorkflowRunner responsibilities (violates Single Responsibility)**:
1. Workflow validation
2. Graph traversal
3. Node execution orchestration
4. Retry logic
5. Parallel execution scheduling
6. Event emission
7. State management
8. Error handling
9. Pause/Resume/Stop control
10. Debug integration
11. Subgraph calculation
12. Performance metrics

#### Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WorkflowRunner                        │
│  (200 lines - orchestration only)                       │
│                                                          │
│  - Delegates to specialized classes                     │
│  - Coordinates execution flow                           │
│  - Main async execute() method                          │
└────────────┬────────────────────────────────────────────┘
             │
             ├─► GraphTraverser (graph_traverser.py)
             │   - Calculate execution order
             │   - Resolve dependencies
             │   - Topological sort
             │
             ├─► NodeExecutor (node_executor.py)
             │   - Execute single node
             │   - Handle node-level errors
             │   - Timeout management
             │
             ├─► RetryOrchestrator (retry_orchestrator.py)
             │   - Retry logic
             │   - Backoff calculation
             │   - Retry statistics
             │
             ├─► ParallelScheduler (parallel_scheduler.py)
             │   - Parallel execution planning
             │   - Dependency graph building
             │   - Concurrency control
             │
             ├─► StateManager (state_manager.py)
             │   - Execution state tracking
             │   - Pause/Resume/Stop control
             │   - State persistence
             │
             ├─► EventPublisher (event_publisher.py)
             │   - Event emission
             │   - Event filtering
             │   - Subscriber management
             │
             ├─► ExecutionValidator (execution_validator.py)
             │   - Pre-execution validation
             │   - Runtime validation
             │   - Constraint checking
             │
             └─► MetricsCollector (metrics_collector.py)
                 - Performance metrics
                 - Execution statistics
                 - Debug information
```

#### Tasks

1. **Extract GraphTraverser Class** (2-3 hours)

   **File**: `src/casare_rpa/infrastructure/execution/graph_traverser.py`

   ```python
   """
   Graph traversal logic for workflow execution.

   Responsible for determining execution order based on node dependencies.
   """
   from typing import List, Set, Dict, Optional
   from loguru import logger

   from ...domain.entities.workflow import Workflow
   from ...domain.entities.node import Node
   from ...core.types import NodeId


   class GraphTraverser:
       """
       Handles graph traversal logic for workflow execution.

       Responsibilities:
       - Calculate execution order (topological sort)
       - Find start nodes
       - Resolve node dependencies
       - Path calculation (for Run To Node feature)
       """

       def __init__(self, workflow: Workflow):
           self.workflow = workflow
           self._execution_order_cache: Optional[List[NodeId]] = None

       def get_start_nodes(self) -> List[Node]:
           """Get all start nodes in the workflow."""
           return self.workflow.get_start_nodes()

       def get_next_nodes(self, node_id: NodeId) -> List[Node]:
           """Get nodes connected to this node's outputs."""
           return self.workflow.get_next_nodes(node_id)

       def calculate_execution_order(self) -> List[NodeId]:
           """
           Calculate optimal execution order using topological sort.

           Returns:
               List of node IDs in execution order
           """
           if self._execution_order_cache is not None:
               return self._execution_order_cache

           # Kahn's algorithm for topological sort
           in_degree: Dict[NodeId, int] = {
               node_id: 0 for node_id in self.workflow.nodes
           }

           # Calculate in-degrees
           for conn in self.workflow.connections:
               in_degree[conn.target_node_id] += 1

           # Queue of nodes with no dependencies
           queue: List[NodeId] = [
               node_id for node_id, degree in in_degree.items()
               if degree == 0
           ]

           execution_order: List[NodeId] = []

           while queue:
               node_id = queue.pop(0)
               execution_order.append(node_id)

               # Reduce in-degree for connected nodes
               for next_node in self.get_next_nodes(node_id):
                   in_degree[next_node.node_id] -= 1
                   if in_degree[next_node.node_id] == 0:
                       queue.append(next_node.node_id)

           # Check for cycles
           if len(execution_order) != len(self.workflow.nodes):
               raise ValueError("Workflow contains circular dependencies")

           self._execution_order_cache = execution_order
           return execution_order

       def calculate_path_to_node(
           self,
           target_node_id: NodeId
       ) -> Set[NodeId]:
           """
           Calculate all nodes required to reach target node.

           Used for "Run To Node" feature.

           Args:
               target_node_id: Target node to reach

           Returns:
               Set of node IDs in the path to target
           """
           if target_node_id not in self.workflow.nodes:
               raise ValueError(f"Node {target_node_id} not found")

           required_nodes: Set[NodeId] = set()

           def dfs_backwards(node_id: NodeId) -> None:
               """Trace backwards from target to find dependencies."""
               if node_id in required_nodes:
                   return

               required_nodes.add(node_id)

               # Find all nodes that connect TO this node
               for conn in self.workflow.connections:
                   if conn.target_node_id == node_id:
                       dfs_backwards(conn.source_node_id)

           dfs_backwards(target_node_id)
           return required_nodes
   ```

2. **Extract NodeExecutor Class** (2-3 hours)

   **File**: `src/casare_rpa/infrastructure/execution/node_executor.py`

   ```python
   """
   Single node execution logic.

   Handles execution of individual nodes with timeout and error handling.
   """
   import asyncio
   from typing import Optional, Dict, Any
   from datetime import datetime
   from loguru import logger

   from ...core.base_node import BaseNode
   from ...core.execution_context import ExecutionContext
   from ...core.types import NodeStatus, NodeId
   from ...domain.entities.execution_state import NodeExecutionResult


   class NodeExecutionError(Exception):
       """Raised when node execution fails."""
       pass


   class NodeExecutor:
       """
       Executes individual nodes with timeout and error handling.

       Single Responsibility: Node-level execution only.
       """

       def __init__(self, timeout: float = 120.0):
           """
           Initialize node executor.

           Args:
               timeout: Timeout for node execution in seconds
           """
           self.timeout = timeout

       async def execute_node(
           self,
           node: BaseNode,
           context: ExecutionContext
       ) -> NodeExecutionResult:
           """
           Execute a single node with timeout.

           Args:
               node: Node to execute
               context: Execution context with variables

           Returns:
               NodeExecutionResult with success status and data

           Raises:
               NodeExecutionError: If execution fails
           """
           start_time = datetime.now()

           try:
               logger.debug(f"Executing node {node.node_id} ({node.node_type})")

               # Execute with timeout
               result = await asyncio.wait_for(
                   node.execute(context),
                   timeout=self.timeout
               )

               execution_time = (datetime.now() - start_time).total_seconds()

               # Handle ExecutionResult pattern
               if isinstance(result, dict) and "success" in result:
                   return NodeExecutionResult(
                       node_id=node.node_id,
                       success=result["success"],
                       data=result.get("data", {}),
                       error=result.get("error"),
                       execution_time=execution_time
                   )

               # Fallback for old NodeStatus pattern
               return NodeExecutionResult(
                   node_id=node.node_id,
                   success=node.status == NodeStatus.SUCCESS,
                   data={},
                   error=node.error_message,
                   execution_time=execution_time
               )

           except asyncio.TimeoutError:
               execution_time = (datetime.now() - start_time).total_seconds()
               error_msg = f"Node {node.node_id} timed out after {self.timeout}s"
               logger.error(error_msg)

               return NodeExecutionResult(
                   node_id=node.node_id,
                   success=False,
                   error=error_msg,
                   execution_time=execution_time
               )

           except Exception as e:
               execution_time = (datetime.now() - start_time).total_seconds()
               error_msg = f"Node {node.node_id} failed: {str(e)}"
               logger.error(error_msg)

               return NodeExecutionResult(
                   node_id=node.node_id,
                   success=False,
                   error=error_msg,
                   execution_time=execution_time
               )
   ```

3. **Extract StateManager Class** (2 hours)

   **File**: `src/casare_rpa/infrastructure/execution/state_manager.py`

   ```python
   """
   Execution state management.

   Handles pause/resume/stop control and state persistence.
   """
   import asyncio
   from typing import Optional
   from loguru import logger

   from ...domain.entities.execution_state import ExecutionState, ExecutionStatus


   class StateManager:
       """
       Manages workflow execution state.

       Responsibilities:
       - Track execution status (running/paused/stopped)
       - Handle pause/resume/stop requests
       - Provide state query methods
       """

       def __init__(self, state: ExecutionState):
           self.state = state
           self._pause_event = asyncio.Event()
           self._pause_event.set()  # Start unpaused
           self._stop_requested = False

       async def check_pause(self) -> None:
           """
           Check if execution is paused and wait if so.

           Should be called between node executions.
           """
           if self.state.status == ExecutionStatus.PAUSED:
               logger.info("Execution paused, waiting for resume...")
               await self._pause_event.wait()

       def pause(self) -> None:
           """Pause execution."""
           if self.state.status == ExecutionStatus.RUNNING:
               logger.info("Pausing execution...")
               self.state.pause()
               self._pause_event.clear()

       def resume(self) -> None:
           """Resume paused execution."""
           if self.state.status == ExecutionStatus.PAUSED:
               logger.info("Resuming execution...")
               self.state.resume()
               self._pause_event.set()

       def stop(self) -> None:
           """Stop execution."""
           logger.info("Stopping execution...")
           self._stop_requested = True
           self.state.stop()
           self._pause_event.set()  # Unblock if paused

       def is_stopped(self) -> bool:
           """Check if stop was requested."""
           return self._stop_requested

       def is_running(self) -> bool:
           """Check if execution is running."""
           return self.state.status == ExecutionStatus.RUNNING
   ```

4. **Refactor WorkflowRunner to Use Extracted Classes** (3-4 hours)

   **File**: `src/casare_rpa/runner/workflow_runner.py` (Refactored)

   ```python
   """
   CasareRPA - Workflow Runner (Refactored)

   Orchestrates workflow execution by delegating to specialized components.

   Reduced from 1,404 lines to ~200 lines by extracting:
   - GraphTraverser: Graph traversal logic
   - NodeExecutor: Node execution
   - StateManager: Execution state
   - RetryOrchestrator: Retry logic
   - EventPublisher: Event emission
   - ParallelScheduler: Parallel execution
   - MetricsCollector: Performance tracking
   """

   import asyncio
   from typing import Optional, Dict, Any
   from loguru import logger

   from ..core.workflow_schema import WorkflowSchema
   from ..core.execution_context import ExecutionContext
   from ..core.events import EventBus, get_event_bus
   from ..domain.entities.workflow import Workflow
   from ..domain.entities.execution_state import ExecutionState, ExecutionStatus
   from ..infrastructure.execution.graph_traverser import GraphTraverser
   from ..infrastructure.execution.node_executor import NodeExecutor
   from ..infrastructure.execution.state_manager import StateManager
   from ..infrastructure.execution.event_publisher import EventPublisher
   from ..infrastructure.execution.retry_orchestrator import RetryOrchestrator


   class WorkflowRunner:
       """
       Orchestrates workflow execution.

       Delegates to specialized components for single-responsibility design.
       """

       def __init__(
           self,
           workflow: WorkflowSchema,
           event_bus: Optional[EventBus] = None,
           node_timeout: float = 120.0,
           continue_on_error: bool = False,
           initial_variables: Optional[Dict[str, Any]] = None,
       ):
           """
           Initialize workflow runner.

           Args:
               workflow: Workflow schema to execute
               event_bus: Event bus for progress updates
               node_timeout: Timeout for node execution in seconds
               continue_on_error: Continue on node errors if True
               initial_variables: Initial variables for execution context
           """
           self.workflow_schema = workflow
           self.continue_on_error = continue_on_error

           # Convert WorkflowSchema to domain Workflow
           # (This adapter will be created in infrastructure layer)
           from ..infrastructure.adapters.workflow_adapter import to_domain_workflow
           self.workflow = to_domain_workflow(workflow)

           # Initialize execution state
           self.state = ExecutionState(
               workflow_id=workflow.metadata.name,
               variables=initial_variables or {}
           )

           # Initialize components (dependency injection)
           self.event_bus = event_bus or get_event_bus()
           self.traverser = GraphTraverser(self.workflow)
           self.executor = NodeExecutor(timeout=node_timeout)
           self.state_manager = StateManager(self.state)
           self.event_publisher = EventPublisher(self.event_bus)
           self.retry_orchestrator = RetryOrchestrator()

       async def execute(self) -> ExecutionState:
           """
           Execute the workflow.

           Returns:
               Final execution state
           """
           logger.info(f"Starting workflow execution: {self.workflow.metadata.name}")

           # Validate workflow
           validation_errors = self.workflow.validate()
           if validation_errors:
               error_msg = f"Workflow validation failed: {'; '.join(validation_errors)}"
               logger.error(error_msg)
               self.state.error(error_msg)
               await self.event_publisher.publish_workflow_error(error_msg)
               return self.state

           # Start execution
           self.state.start()
           await self.event_publisher.publish_workflow_started(self.workflow.metadata.name)

           try:
               # Get execution order
               execution_order = self.traverser.calculate_execution_order()
               logger.debug(f"Execution order: {execution_order}")

               # Create execution context
               context = ExecutionContext(
                   variables=self.state.variables.copy()
               )

               # Execute nodes in order
               for node_id in execution_order:
                   # Check for pause/stop
                   await self.state_manager.check_pause()
                   if self.state_manager.is_stopped():
                       logger.info("Execution stopped by user")
                       await self.event_publisher.publish_workflow_stopped()
                       return self.state

                   # Get node from workflow schema
                   node = self.workflow_schema.nodes[node_id]

                   # Execute node with retry
                   result = await self.retry_orchestrator.execute_with_retry(
                       self.executor.execute_node,
                       node,
                       context
                   )

                   # Record result
                   self.state.record_node_execution(result)

                   # Publish events
                   if result.success:
                       await self.event_publisher.publish_node_completed(
                           node_id,
                           result.data
                       )
                   else:
                       await self.event_publisher.publish_node_error(
                           node_id,
                           result.error or "Unknown error"
                       )

                       if not self.continue_on_error:
                           logger.error(f"Node {node_id} failed, stopping execution")
                           self.state.error(result.error or "Node execution failed")
                           return self.state

               # Execution completed successfully
               self.state.complete()
               await self.event_publisher.publish_workflow_completed(
                   execution_time=self.state.execution_time
               )

               logger.info(
                   f"Workflow completed in {self.state.execution_time:.2f}s"
               )

           except Exception as e:
               error_msg = f"Workflow execution failed: {str(e)}"
               logger.exception(error_msg)
               self.state.error(error_msg)
               await self.event_publisher.publish_workflow_error(error_msg)

           return self.state

       async def pause(self) -> None:
           """Pause workflow execution."""
           self.state_manager.pause()

       async def resume(self) -> None:
           """Resume paused execution."""
           self.state_manager.resume()

       async def stop(self) -> None:
           """Stop workflow execution."""
           self.state_manager.stop()
   ```

#### Success Criteria

- [ ] WorkflowRunner reduced to ~200 lines
- [ ] 8 extracted classes created and tested
- [ ] All existing tests pass with refactored runner
- [ ] No breaking changes to public API
- [ ] Performance benchmarks show no regression

#### Migration Path

```python
# Old code (still works via compatibility layer)
from casare_rpa.runner.workflow_runner import WorkflowRunner

runner = WorkflowRunner(workflow)
await runner.execute()

# New code (explicit dependency injection)
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase

use_case = ExecuteWorkflowUseCase()
result = await use_case.execute(workflow)
```

---

### Day 3: Infrastructure Layer - Execution Engine

**Objective**: Move execution logic to infrastructure layer, implement domain ports

#### Tasks

1. **Create Workflow Adapter** (2 hours)

   **File**: `src/casare_rpa/infrastructure/adapters/workflow_adapter.py`

   ```python
   """
   Adapter to convert between WorkflowSchema (legacy) and Workflow (domain).

   Follows Adapter pattern to maintain compatibility.
   """
   from typing import Dict, Any

   from ...core.workflow_schema import WorkflowSchema, NodeConnection
   from ...domain.entities.workflow import Workflow, WorkflowMetadata
   from ...domain.entities.node import Node
   from ...domain.entities.connection import Connection


   def to_domain_workflow(schema: WorkflowSchema) -> Workflow:
       """
       Convert WorkflowSchema to domain Workflow.

       Args:
           schema: Legacy workflow schema

       Returns:
           Domain workflow entity
       """
       # Convert metadata
       metadata = WorkflowMetadata(
           name=schema.metadata.name,
           description=schema.metadata.description,
           author=schema.metadata.author,
           version=schema.metadata.version,
           created_at=schema.metadata.created_at,
           modified_at=schema.metadata.modified_at,
           tags=schema.metadata.tags
       )

       # Create workflow
       workflow = Workflow(metadata=metadata)

       # Convert nodes
       for node_id, base_node in schema.nodes.items():
           node = Node(
               node_id=node_id,
               node_type=base_node.node_type,
               config=base_node.config.copy()
           )
           workflow.add_node(node)

       # Convert connections
       for conn in schema.connections:
           connection = Connection(
               source_node_id=conn.source_node_id,
               source_port=conn.source_port,
               target_node_id=conn.target_node_id,
               target_port=conn.target_port
           )
           workflow.add_connection(connection)

       return workflow


   def from_domain_workflow(workflow: Workflow) -> WorkflowSchema:
       """
       Convert domain Workflow to WorkflowSchema.

       Args:
           workflow: Domain workflow entity

       Returns:
           Legacy workflow schema
       """
       # Implementation for reverse conversion
       # (Needed for saving workflows in legacy format)
       pass
   ```

2. **Implement Remaining Execution Classes** (4-5 hours)

   **Files to Create**:
   - `src/casare_rpa/infrastructure/execution/event_publisher.py`
   - `src/casare_rpa/infrastructure/execution/retry_orchestrator.py`
   - `src/casare_rpa/infrastructure/execution/parallel_scheduler.py`
   - `src/casare_rpa/infrastructure/execution/metrics_collector.py`

   (Implementation details provided in supplementary document)

3. **Create Execution Engine Implementation** (2-3 hours)

   **File**: `src/casare_rpa/infrastructure/execution/workflow_execution_engine.py`

   ```python
   """
   Infrastructure implementation of ExecutionEngine port.
   """
   from typing import Optional, Dict, Any

   from ...domain.ports.execution_engine import ExecutionEngine
   from ...domain.entities.workflow import Workflow
   from ...domain.entities.execution_state import ExecutionState, NodeExecutionResult
   from .graph_traverser import GraphTraverser
   from .node_executor import NodeExecutor
   from .state_manager import StateManager


   class WorkflowExecutionEngine(ExecutionEngine):
       """
       Concrete implementation of ExecutionEngine.

       Uses dependency injection to remain testable.
       """

       def __init__(
           self,
           node_timeout: float = 120.0,
           continue_on_error: bool = False
       ):
           self.node_timeout = node_timeout
           self.continue_on_error = continue_on_error

       async def execute_workflow(
           self,
           workflow: Workflow,
           initial_variables: Optional[Dict[str, Any]] = None
       ) -> ExecutionState:
           """Execute workflow using domain entities."""
           # Implementation similar to refactored WorkflowRunner
           pass
   ```

#### Success Criteria

- [ ] All execution logic moved to infrastructure layer
- [ ] Domain ports implemented in infrastructure
- [ ] Adapters maintain backward compatibility
- [ ] Zero infrastructure imports in domain layer

---

### Day 4: ExecutionResult Migration - Remaining Modules

**Objective**: Migrate remaining 20+ node modules from NodeStatus to ExecutionResult pattern

#### Current State

- **Completed**: 32 data operation nodes (Week 1)
- **Remaining**: 20 modules with 354 NodeStatus occurrences

**Modules to Migrate**:
1. `basic_nodes.py` (8 occurrences)
2. `control_flow_nodes.py` (25 occurrences)
3. `browser_nodes.py` (14 occurrences)
4. `database_nodes.py` (31 occurrences)
5. `error_handling_nodes.py` (41 occurrences)
6. `datetime_nodes.py` (22 occurrences)
7. `email_nodes.py` (35 occurrences)
8. `file_nodes.py` (61 occurrences)
9. `http_nodes.py` (39 occurrences)
10. `ftp_nodes.py` (32 occurrences)
11. `pdf_nodes.py` (19 occurrences)
12. `random_nodes.py` (16 occurrences)
13. `interaction_nodes.py` (10 occurrences)
14. `navigation_nodes.py` (13 occurrences)
15. `data_nodes.py` (10 occurrences)
16. `variable_nodes.py`
17. `wait_nodes.py`
18. `xml_nodes.py`
19. `text_nodes.py`
20. `system_nodes.py`
21. `script_nodes.py`
22. `utility_nodes.py`

#### Migration Pattern

```python
# BEFORE (NodeStatus pattern)
async def execute(self, context: ExecutionContext) -> None:
    try:
        # Node logic
        result = some_operation()
        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS
    except Exception as e:
        logger.error(f"Error: {e}")
        self.error_message = str(e)
        self.status = NodeStatus.ERROR

# AFTER (ExecutionResult pattern)
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    try:
        # Node logic
        result = some_operation()
        self.set_output_value("result", result)
        return {
            "success": True,
            "data": {"result": result},
            "next_nodes": []
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        self.error_message = str(e)
        return {
            "success": False,
            "error": str(e),
            "next_nodes": []
        }
```

#### Tasks

1. **Migrate High-Priority Modules** (3 hours)
   - `browser_nodes.py` (14 occurrences)
   - `control_flow_nodes.py` (25 occurrences)
   - `error_handling_nodes.py` (41 occurrences)

2. **Migrate Medium-Priority Modules** (3 hours)
   - `file_nodes.py` (61 occurrences - largest)
   - `http_nodes.py` (39 occurrences)
   - `database_nodes.py` (31 occurrences)
   - `email_nodes.py` (35 occurrences)
   - `ftp_nodes.py` (32 occurrences)

3. **Migrate Remaining Modules** (2-3 hours)
   - All remaining modules (smaller counts)

#### Success Criteria

- [ ] All node modules return ExecutionResult
- [ ] NodeStatus only used internally for state tracking
- [ ] All existing tests pass
- [ ] Documentation updated with new pattern

#### Testing Strategy

```python
# tests/nodes/test_execution_result_migration.py
"""Test ExecutionResult migration."""
import pytest
from casare_rpa.nodes.browser_nodes import LaunchBrowserNode
from casare_rpa.core.execution_context import ExecutionContext


@pytest.mark.asyncio
async def test_node_returns_execution_result():
    """Test that nodes return ExecutionResult."""
    node = LaunchBrowserNode(node_id="test1")
    context = ExecutionContext()

    result = await node.execute(context)

    # Validate ExecutionResult structure
    assert isinstance(result, dict)
    assert "success" in result
    assert "data" in result or "error" in result
    assert "next_nodes" in result
```

---

### Day 5: Integration Testing & Validation

**Objective**: Ensure all Week 2 changes integrate correctly and Canvas loads

#### Tasks

1. **Integration Testing** (3 hours)

   **Test Suites to Run**:
   - Domain entity tests
   - WorkflowRunner refactored tests
   - Node execution result tests
   - End-to-end workflow execution

   ```python
   # tests/integration/test_week2_refactoring.py
   """Integration tests for Week 2 refactoring."""
   import pytest
   from casare_rpa.domain import Workflow, WorkflowMetadata, Node, Connection
   from casare_rpa.runner.workflow_runner import WorkflowRunner
   from casare_rpa.core.workflow_schema import WorkflowSchema


   @pytest.mark.asyncio
   async def test_domain_workflow_execution():
       """Test workflow execution with domain entities."""
       # Create domain workflow
       workflow = Workflow(metadata=WorkflowMetadata(name="Test"))

       start = Node(node_id="start", node_type="Start")
       end = Node(node_id="end", node_type="End")

       workflow.add_node(start)
       workflow.add_node(end)
       workflow.add_connection(Connection("start", "out", "end", "in"))

       # Validate
       errors = workflow.validate()
       assert len(errors) == 0


   @pytest.mark.asyncio
   async def test_refactored_runner_executes():
       """Test refactored WorkflowRunner executes workflows."""
       # Create simple workflow
       workflow = create_test_workflow()

       runner = WorkflowRunner(workflow)
       state = await runner.execute()

       assert state.status == "completed"
       assert len(state.executed_nodes) > 0
   ```

2. **Canvas Load Verification** (2 hours)

   **Manual Testing**:
   - [ ] Run `python run.py`
   - [ ] Verify Canvas loads without errors
   - [ ] Create new workflow
   - [ ] Add nodes from all categories
   - [ ] Connect nodes
   - [ ] Execute workflow
   - [ ] Verify execution completes
   - [ ] Check log output for errors

3. **Performance Benchmarking** (2 hours)

   ```python
   # tests/performance/test_runner_performance.py
   """Benchmark refactored runner performance."""
   import time
   import pytest


   @pytest.mark.benchmark
   def test_runner_overhead():
       """Ensure refactored runner has minimal overhead."""
       # Create workflow with 100 nodes
       workflow = create_large_workflow(num_nodes=100)

       # Time old runner (if still available)
       # start = time.perf_counter()
       # old_runner.execute()
       # old_time = time.perf_counter() - start

       # Time new runner
       start = time.perf_counter()
       runner = WorkflowRunner(workflow)
       await runner.execute()
       new_time = time.perf_counter() - start

       # Assert no significant performance regression
       # assert new_time <= old_time * 1.1  # Max 10% slowdown
       print(f"Execution time: {new_time:.2f}s")
   ```

4. **Documentation Updates** (1-2 hours)

   **Files to Update**:
   - `REFACTORING_LOG.md` - Add Week 2 completion notes
   - `ARCHITECTURE.md` - Document new clean architecture
   - `MIGRATION_GUIDE.md` - Add ExecutionResult migration guide

#### Success Criteria

- [ ] All unit tests pass (1255+ tests)
- [ ] All integration tests pass
- [ ] Canvas loads and runs workflows
- [ ] No performance regression (< 10% slowdown)
- [ ] Documentation updated

---

## Week 2 Summary

### Deliverables

1. **Domain Layer** (5 files)
   - `domain/entities/workflow.py`
   - `domain/entities/node.py`
   - `domain/entities/connection.py`
   - `domain/entities/execution_state.py`
   - `domain/ports/execution_engine.py`

2. **Infrastructure Layer** (8 files)
   - `infrastructure/execution/graph_traverser.py`
   - `infrastructure/execution/node_executor.py`
   - `infrastructure/execution/state_manager.py`
   - `infrastructure/execution/event_publisher.py`
   - `infrastructure/execution/retry_orchestrator.py`
   - `infrastructure/execution/parallel_scheduler.py`
   - `infrastructure/execution/metrics_collector.py`
   - `infrastructure/adapters/workflow_adapter.py`

3. **Refactored Core**
   - `runner/workflow_runner.py` (1,404 → 200 lines)

4. **Node Migrations**
   - 20+ modules migrated to ExecutionResult pattern
   - 354 NodeStatus occurrences migrated

### Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| WorkflowRunner LOC | 1,404 | 200 | 86% reduction |
| Extracted Classes | 0 | 8 | New architecture |
| ExecutionResult Coverage | 32 modules | 52+ modules | 100% coverage |
| Domain Layer Dependencies | N/A | 0 infrastructure | Clean separation |

---

## Week 3: Canvas/MainWindow Refactoring

**Goal**: Decompose MainWindow (2,417 lines) and CasareRPAApp (2,929 lines) into controllers and components

### Day 1: Canvas Controllers Extraction

**Objective**: Extract workflow, node, and connection management from MainWindow

#### Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      MainWindow                          │
│  (400 lines - UI setup only)                            │
│                                                          │
│  - Window configuration                                 │
│  - Menu/toolbar setup                                   │
│  - Dock widget layout                                   │
│  - Signal routing                                       │
└────────────┬────────────────────────────────────────────┘
             │
             ├─► WorkflowController (workflow_controller.py)
             │   - New/Open/Save/Close workflows
             │   - Workflow validation
             │   - Undo/Redo management
             │
             ├─► NodeController (node_controller.py)
             │   - Node creation/deletion
             │   - Node selection
             │   - Node property updates
             │
             ├─► ConnectionController (connection_controller.py)
             │   - Connection creation/deletion
             │   - Connection validation
             │   - Port management
             │
             ├─► ExecutionController (execution_controller.py)
             │   - Run/Pause/Resume/Stop
             │   - Debug mode
             │   - Breakpoint management
             │
             ├─► PanelController (panel_controller.py)
             │   - Bottom panel tabs
             │   - Properties panel
             │   - Variable inspector
             │
             ├─► MenuController (menu_controller.py)
             │   - Menu bar management
             │   - Toolbar management
             │   - Action state updates
             │
             └─► EventBusController (event_bus_controller.py)
                 - Qt signal → Event bus bridge
                 - Event filtering
                 - Event logging
```

#### Tasks

1. **Create Controller Base Class** (1 hour)

   **File**: `src/casare_rpa/presentation/canvas/controllers/base_controller.py`

   ```python
   """
   Base class for Canvas controllers.

   All controllers follow the same pattern for consistency.
   """
   from abc import ABC
   from typing import Optional
   from PySide6.QtCore import QObject
   from loguru import logger


   class BaseController(QObject):
       """
       Base class for all Canvas controllers.

       Controllers are responsible for:
       - Handling user interactions
       - Updating model state
       - Coordinating between components

       Controllers should NOT:
       - Directly manipulate UI widgets (use signals)
       - Contain business logic (delegate to use cases)
       - Access infrastructure directly (use dependency injection)
       """

       def __init__(self, parent: Optional[QObject] = None):
           super().__init__(parent)
           self._setup_connections()

       def _setup_connections(self) -> None:
           """
           Setup signal/slot connections.

           Override in subclasses to connect signals.
           """
           pass

       def cleanup(self) -> None:
           """
           Cleanup resources.

           Called when controller is destroyed.
           """
           pass
   ```

2. **Extract WorkflowController** (3-4 hours)

   **File**: `src/casare_rpa/presentation/canvas/controllers/workflow_controller.py`

   ```python
   """
   Workflow lifecycle controller.

   Handles all workflow-related operations:
   - New/Open/Save/Save As/Close
   - Import/Export
   - Validation
   - Undo/Redo
   """
   from pathlib import Path
   from typing import Optional
   from PySide6.QtCore import Signal
   from loguru import logger

   from .base_controller import BaseController
   from ....core.workflow_schema import WorkflowSchema
   from ....application.use_cases.save_workflow import SaveWorkflowUseCase
   from ....application.use_cases.load_workflow import LoadWorkflowUseCase


   class WorkflowController(BaseController):
       """
       Manages workflow lifecycle operations.

       Single Responsibility: Workflow file management.
       """

       # Signals
       workflow_loaded = Signal(WorkflowSchema)
       workflow_saved = Signal(Path)
       workflow_modified = Signal(bool)
       workflow_validation_changed = Signal(list)  # List of errors

       def __init__(self, parent=None):
           super().__init__(parent)
           self._current_file: Optional[Path] = None
           self._is_modified = False
           self._workflow: Optional[WorkflowSchema] = None

           # Use cases (dependency injection)
           self._save_use_case = SaveWorkflowUseCase()
           self._load_use_case = LoadWorkflowUseCase()

       async def new_workflow(self, name: str = "Untitled") -> None:
           """Create a new empty workflow."""
           logger.info(f"Creating new workflow: {name}")

           # Create empty workflow
           from ....core.workflow_schema import WorkflowMetadata
           metadata = WorkflowMetadata(name=name)
           self._workflow = WorkflowSchema(metadata=metadata)

           self._current_file = None
           self._set_modified(False)

           self.workflow_loaded.emit(self._workflow)

       async def open_workflow(self, file_path: Path) -> None:
           """Open workflow from file."""
           logger.info(f"Opening workflow: {file_path}")

           try:
               self._workflow = await self._load_use_case.execute(file_path)
               self._current_file = file_path
               self._set_modified(False)

               self.workflow_loaded.emit(self._workflow)

           except Exception as e:
               logger.error(f"Failed to open workflow: {e}")
               raise

       async def save_workflow(self, file_path: Optional[Path] = None) -> None:
           """Save workflow to file."""
           if file_path is None:
               file_path = self._current_file

           if file_path is None:
               raise ValueError("No file path specified for save")

           logger.info(f"Saving workflow to: {file_path}")

           try:
               await self._save_use_case.execute(self._workflow, file_path)
               self._current_file = file_path
               self._set_modified(False)

               self.workflow_saved.emit(file_path)

           except Exception as e:
               logger.error(f"Failed to save workflow: {e}")
               raise

       def validate_workflow(self) -> list[str]:
           """
           Validate current workflow.

           Returns:
               List of validation errors (empty if valid)
           """
           if self._workflow is None:
               return ["No workflow loaded"]

           from ....domain.adapters.workflow_adapter import to_domain_workflow
           domain_workflow = to_domain_workflow(self._workflow)

           errors = domain_workflow.validate()
           self.workflow_validation_changed.emit(errors)

           return errors

       def mark_modified(self) -> None:
           """Mark workflow as modified."""
           self._set_modified(True)

       def _set_modified(self, modified: bool) -> None:
           """Update modified state and emit signal."""
           if self._is_modified != modified:
               self._is_modified = modified
               self.workflow_modified.emit(modified)

       @property
       def current_file(self) -> Optional[Path]:
           """Get current file path."""
           return self._current_file

       @property
       def is_modified(self) -> bool:
           """Check if workflow has unsaved changes."""
           return self._is_modified
   ```

3. **Extract ExecutionController** (2-3 hours)

   **File**: `src/casare_rpa/presentation/canvas/controllers/execution_controller.py`

   ```python
   """
   Workflow execution controller.

   Handles all execution-related operations:
   - Run/Pause/Resume/Stop
   - Debug mode
   - Step execution
   - Breakpoints
   """
   import asyncio
   from typing import Optional
   from PySide6.QtCore import Signal
   from loguru import logger

   from .base_controller import BaseController
   from ....runner.workflow_runner import WorkflowRunner
   from ....core.workflow_schema import WorkflowSchema
   from ....domain.entities.execution_state import ExecutionState, ExecutionStatus


   class ExecutionController(BaseController):
       """
       Manages workflow execution.

       Single Responsibility: Execution lifecycle management.
       """

       # Signals
       execution_started = Signal()
       execution_completed = Signal(ExecutionState)
       execution_paused = Signal()
       execution_resumed = Signal()
       execution_stopped = Signal()
       execution_error = Signal(str)

       def __init__(self, parent=None):
           super().__init__(parent)
           self._runner: Optional[WorkflowRunner] = None
           self._task: Optional[asyncio.Task] = None
           self._is_running = False

       async def run_workflow(
           self,
           workflow: WorkflowSchema,
           initial_variables: Optional[dict] = None
       ) -> None:
           """
           Run workflow from start to end.

           Args:
               workflow: Workflow to execute
               initial_variables: Initial variable values
           """
           if self._is_running:
               logger.warning("Workflow already running")
               return

           logger.info("Starting workflow execution")

           try:
               self._runner = WorkflowRunner(
                   workflow=workflow,
                   initial_variables=initial_variables
               )

               self._is_running = True
               self.execution_started.emit()

               # Execute asynchronously
               state = await self._runner.execute()

               self.execution_completed.emit(state)

           except Exception as e:
               error_msg = f"Execution failed: {str(e)}"
               logger.error(error_msg)
               self.execution_error.emit(error_msg)

           finally:
               self._is_running = False
               self._runner = None

       async def pause(self) -> None:
           """Pause running workflow."""
           if self._runner:
               await self._runner.pause()
               self.execution_paused.emit()

       async def resume(self) -> None:
           """Resume paused workflow."""
           if self._runner:
               await self._runner.resume()
               self.execution_resumed.emit()

       async def stop(self) -> None:
           """Stop running workflow."""
           if self._runner:
               await self._runner.stop()
               self.execution_stopped.emit()
               self._is_running = False

       @property
       def is_running(self) -> bool:
           """Check if workflow is currently executing."""
           return self._is_running
   ```

4. **Update MainWindow to Use Controllers** (2-3 hours)

   **File**: `src/casare_rpa/canvas/main_window.py` (Refactored)

   ```python
   """
   Main application window for CasareRPA (Refactored).

   Reduced from 2,417 lines to ~400 lines by extracting controllers.
   """
   from pathlib import Path
   from typing import Optional
   from PySide6.QtWidgets import QMainWindow
   from loguru import logger

   from .controllers.workflow_controller import WorkflowController
   from .controllers.execution_controller import ExecutionController
   from .controllers.node_controller import NodeController


   class MainWindow(QMainWindow):
       """
       Main application window.

       Responsibilities:
       - UI layout and setup
       - Signal routing to controllers
       - Menu/toolbar management

       Business logic delegated to controllers.
       """

       def __init__(self, parent=None):
           super().__init__(parent)

           # Initialize controllers
           self._workflow_controller = WorkflowController(self)
           self._execution_controller = ExecutionController(self)
           self._node_controller = NodeController(self)

           # Setup UI
           self._setup_window()
           self._create_menus()
           self._create_toolbars()
           self._create_dock_widgets()

           # Connect controller signals
           self._connect_controller_signals()

       def _setup_window(self) -> None:
           """Configure window properties."""
           self.setWindowTitle("CasareRPA Canvas")
           self.resize(1920, 1080)

       def _create_menus(self) -> None:
           """Create menu bar."""
           # Menu creation logic (delegated to MenuController in full implementation)
           pass

       def _connect_controller_signals(self) -> None:
           """Connect controller signals to UI updates."""
           # Workflow controller
           self._workflow_controller.workflow_loaded.connect(
               self._on_workflow_loaded
           )
           self._workflow_controller.workflow_modified.connect(
               self._on_workflow_modified
           )

           # Execution controller
           self._execution_controller.execution_started.connect(
               self._on_execution_started
           )
           self._execution_controller.execution_completed.connect(
               self._on_execution_completed
           )

       def _on_workflow_loaded(self, workflow) -> None:
           """Handle workflow loaded signal."""
           logger.info(f"Workflow loaded: {workflow.metadata.name}")
           self._update_window_title()

       def _on_workflow_modified(self, is_modified: bool) -> None:
           """Handle workflow modified signal."""
           self._update_window_title()

       def _update_window_title(self) -> None:
           """Update window title with file name and modified indicator."""
           title = "CasareRPA Canvas"

           if self._workflow_controller.current_file:
               title += f" - {self._workflow_controller.current_file.name}"

           if self._workflow_controller.is_modified:
               title += " *"

           self.setWindowTitle(title)
   ```

#### Success Criteria

- [ ] MainWindow reduced to ~400 lines
- [ ] 7 controllers extracted and tested
- [ ] All signals properly routed
- [ ] No breaking changes to existing functionality

---

### Day 2: CasareRPAApp Decomposition

**Objective**: Extract components from 2,929-line CasareRPAApp

#### Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CasareRPAApp                          │
│  (400 lines - initialization only)                      │
│                                                          │
│  - Qt application setup                                 │
│  - Event loop integration                               │
│  - Component initialization                             │
│  - Signal routing                                       │
└────────────┬────────────────────────────────────────────┘
             │
             ├─► WorkflowLifecycleComponent
             │   - New/Open/Save handlers
             │   - File change detection
             │   - Autosave management
             │
             ├─► ExecutionComponent
             │   - Execution orchestration
             │   - Event bus integration
             │   - Progress tracking
             │
             ├─► NodeRegistryComponent
             │   - Node type registration
             │   - Node factory
             │   - Visual node mapping
             │
             ├─► SelectorComponent
             │   - Browser element picker
             │   - Selector integration
             │   - Selector caching
             │
             ├─► TriggerComponent
             │   - Trigger management
             │   - Trigger execution
             │   - Scenario coordination
             │
             ├─► ProjectComponent
             │   - Project management
             │   - Scenario management
             │   - Hierarchy navigation
             │
             ├─► PreferencesComponent
             │   - Settings management
             │   - Hotkey configuration
             │   - Theme management
             │
             ├─► DragDropComponent
             │   - File drag-drop support
             │   - Workflow import
             │   - JSON parsing
             │
             └─► AutosaveComponent
                 - Periodic autosave
                 - Crash recovery
                 - Backup management
```

#### Tasks

1. **Create Component Base Class** (1 hour)

   **File**: `src/casare_rpa/presentation/canvas/components/base_component.py`

   ```python
   """
   Base class for Canvas components.
   """
   from abc import ABC
   from typing import Optional
   from PySide6.QtCore import QObject
   from loguru import logger


   class BaseComponent(QObject):
       """
       Base class for all Canvas components.

       Components are responsible for:
       - Encapsulating related functionality
       - Managing their own lifecycle
       - Exposing clean interfaces

       Components should:
       - Be independently testable
       - Have minimal coupling
       - Follow single responsibility
       """

       def __init__(self, parent: Optional[QObject] = None):
           super().__init__(parent)
           self._initialized = False

       def initialize(self) -> None:
           """
           Initialize component.

           Called after all components are constructed.
           """
           if self._initialized:
               logger.warning(f"{self.__class__.__name__} already initialized")
               return

           self._do_initialize()
           self._initialized = True

       def _do_initialize(self) -> None:
           """
           Actual initialization logic.

           Override in subclasses.
           """
           pass

       def cleanup(self) -> None:
           """
           Cleanup resources.

           Called when component is destroyed.
           """
           pass
   ```

2. **Extract Key Components** (4-5 hours)

   Create 9 component files:
   - `workflow_lifecycle_component.py`
   - `execution_component.py`
   - `node_registry_component.py`
   - `selector_component.py`
   - `trigger_component.py`
   - `project_component.py`
   - `preferences_component.py`
   - `drag_drop_component.py`
   - `autosave_component.py`

   (Implementation details in supplementary document)

3. **Refactor CasareRPAApp** (3-4 hours)

   **File**: `src/casare_rpa/canvas/app.py` (Refactored)

   ```python
   """
   Main application class (Refactored).

   Reduced from 2,929 lines to ~400 lines by extracting components.
   """
   import sys
   import asyncio
   from PySide6.QtWidgets import QApplication
   from PySide6.QtCore import Qt
   from qasync import QEventLoop
   from loguru import logger

   from .main_window import MainWindow
   from .components.workflow_lifecycle_component import WorkflowLifecycleComponent
   from .components.execution_component import ExecutionComponent
   from .components.node_registry_component import NodeRegistryComponent


   class CasareRPAApp:
       """
       Main application class.

       Responsibilities:
       - Qt application initialization
       - Component lifecycle management
       - Event loop integration

       Business logic delegated to components.
       """

       def __init__(self):
           logger.info("Initializing CasareRPA...")

           # Setup Qt application
           self._setup_qt_application()

           # Create main window
           self._main_window = MainWindow()

           # Initialize components
           self._initialize_components()

           # Connect component signals
           self._connect_components()

           logger.info("Application initialized successfully")

       def _setup_qt_application(self) -> None:
           """Setup Qt application and event loop."""
           # High-DPI support
           QApplication.setHighDpiScaleFactorRoundingPolicy(
               Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
           )

           # Create Qt app
           self._app = QApplication(sys.argv)

           # Create qasync event loop
           self._loop = QEventLoop(self._app)
           asyncio.set_event_loop(self._loop)

       def _initialize_components(self) -> None:
           """Initialize all application components."""
           # Workflow lifecycle
           self._workflow_component = WorkflowLifecycleComponent(
               self._main_window
           )

           # Execution
           self._execution_component = ExecutionComponent(
               self._main_window
           )

           # Node registry
           self._node_registry_component = NodeRegistryComponent(
               self._main_window
           )

           # Initialize all components
           for component in self._get_all_components():
               component.initialize()

       def _connect_components(self) -> None:
           """Connect component signals."""
           # Workflow lifecycle → Execution
           self._workflow_component.workflow_loaded.connect(
               self._execution_component.on_workflow_loaded
           )

           # Add more signal connections as needed

       def _get_all_components(self) -> list:
           """Get all initialized components."""
           return [
               self._workflow_component,
               self._execution_component,
               self._node_registry_component,
           ]

       def run(self) -> int:
           """
           Run the application.

           Returns:
               Exit code
           """
           self._main_window.show()

           with self._loop:
               return self._loop.run_forever()
   ```

#### Success Criteria

- [ ] CasareRPAApp reduced to ~400 lines
- [ ] 9 components extracted and tested
- [ ] All functionality preserved
- [ ] Component coupling minimized

---

### Day 3: UI Components Extraction

**Objective**: Extract reusable UI components from MainWindow

#### Tasks

1. **Extract Panel Components** (3 hours)
   - Bottom panel (tabs: Variables, Output, Log, Validation)
   - Properties panel (right dock)
   - Variable inspector (execution tracking)
   - Execution timeline

2. **Extract Toolbar Components** (2 hours)
   - Main toolbar
   - Debug toolbar
   - Execution toolbar

3. **Extract Dialog Components** (2 hours)
   - Preferences dialog
   - Template selector dialog
   - About dialog
   - Command palette

4. **Create UI Component Library** (1 hour)

   **Directory Structure**:
   ```
   src/casare_rpa/presentation/canvas/ui/
   ├── panels/
   │   ├── bottom_panel.py
   │   ├── properties_panel.py
   │   ├── variable_inspector.py
   │   └── execution_timeline.py
   ├── toolbars/
   │   ├── main_toolbar.py
   │   ├── debug_toolbar.py
   │   └── execution_toolbar.py
   ├── dialogs/
   │   ├── preferences_dialog.py
   │   ├── template_dialog.py
   │   └── command_palette.py
   └── widgets/
       ├── node_search_widget.py
       └── validation_widget.py
   ```

#### Success Criteria

- [ ] 12+ UI components extracted
- [ ] Components are reusable
- [ ] Minimal coupling between components
- [ ] All components have tests

---

### Day 4: Event Bus & Signal System

**Objective**: Create unified event bus for component communication

#### Tasks

1. **Create Event Bus Architecture** (3 hours)

   **File**: `src/casare_rpa/presentation/canvas/events/canvas_event_bus.py`

   ```python
   """
   Canvas-specific event bus.

   Bridges Qt signals with application event system.
   """
   from typing import Callable, Dict, List
   from PySide6.QtCore import QObject, Signal
   from enum import Enum, auto
   from loguru import logger


   class CanvasEvent(Enum):
       """Canvas-specific events."""

       # Workflow events
       WORKFLOW_NEW = auto()
       WORKFLOW_OPENED = auto()
       WORKFLOW_SAVED = auto()
       WORKFLOW_MODIFIED = auto()
       WORKFLOW_CLOSED = auto()

       # Node events
       NODE_CREATED = auto()
       NODE_DELETED = auto()
       NODE_SELECTED = auto()
       NODE_MODIFIED = auto()

       # Execution events
       EXECUTION_STARTED = auto()
       EXECUTION_PAUSED = auto()
       EXECUTION_RESUMED = auto()
       EXECUTION_STOPPED = auto()
       EXECUTION_COMPLETED = auto()

       # UI events
       PANEL_TOGGLED = auto()
       THEME_CHANGED = auto()
       PREFERENCES_UPDATED = auto()


   class CanvasEventBus(QObject):
       """
       Event bus for Canvas UI.

       Provides:
       - Type-safe event emission
       - Event filtering
       - Event logging
       - Qt signal integration
       """

       # Generic event signal
       event_emitted = Signal(CanvasEvent, dict)

       def __init__(self):
           super().__init__()
           self._subscribers: Dict[CanvasEvent, List[Callable]] = {}

       def subscribe(
           self,
           event: CanvasEvent,
           handler: Callable[[dict], None]
       ) -> None:
           """Subscribe to an event."""
           if event not in self._subscribers:
               self._subscribers[event] = []

           self._subscribers[event].append(handler)
           logger.debug(f"Subscribed to {event.name}")

       def emit(self, event: CanvasEvent, data: dict = None) -> None:
           """Emit an event."""
           data = data or {}

           logger.debug(f"Emitting {event.name}: {data}")

           # Emit Qt signal
           self.event_emitted.emit(event, data)

           # Call subscribers
           if event in self._subscribers:
               for handler in self._subscribers[event]:
                   try:
                       handler(data)
                   except Exception as e:
                       logger.error(f"Event handler error: {e}")


   # Global instance
   _canvas_event_bus: CanvasEventBus | None = None


   def get_canvas_event_bus() -> CanvasEventBus:
       """Get global Canvas event bus instance."""
       global _canvas_event_bus

       if _canvas_event_bus is None:
           _canvas_event_bus = CanvasEventBus()

       return _canvas_event_bus
   ```

2. **Integrate Event Bus with Controllers** (2 hours)

   Update all controllers to emit events through event bus

3. **Create Event Logger Component** (1 hour)

   Component that subscribes to all events and logs them to UI

#### Success Criteria

- [ ] Event bus implemented and tested
- [ ] All controllers use event bus
- [ ] Event logging working
- [ ] No direct controller coupling

---

### Day 5: Integration Testing & Canvas Validation

**Objective**: Ensure all Week 3 changes work together correctly

#### Tasks

1. **Integration Testing** (3 hours)

   **Test Suites**:
   - Controller integration tests
   - Component integration tests
   - UI interaction tests
   - Event bus tests

2. **Manual Testing** (2 hours)

   **Test Scenarios**:
   - [ ] Create new workflow
   - [ ] Add 20+ nodes
   - [ ] Connect nodes
   - [ ] Run workflow
   - [ ] Pause/Resume execution
   - [ ] Save workflow
   - [ ] Close and reopen
   - [ ] Import workflow
   - [ ] Export nodes
   - [ ] Test all menu items
   - [ ] Test all toolbar buttons
   - [ ] Test keyboard shortcuts

3. **Performance Testing** (2 hours)

   **Metrics to Test**:
   - Canvas load time
   - Node creation time
   - Workflow save/load time
   - Execution startup time

4. **Documentation** (1 hour)

   Update:
   - `REFACTORING_LOG.md`
   - `ARCHITECTURE.md`
   - Component documentation

#### Success Criteria

- [ ] All tests pass
- [ ] Canvas fully functional
- [ ] No performance regression
- [ ] Documentation complete

---

## Week 3 Summary

### Deliverables

1. **Controllers** (7 files)
   - `workflow_controller.py`
   - `execution_controller.py`
   - `node_controller.py`
   - `connection_controller.py`
   - `panel_controller.py`
   - `menu_controller.py`
   - `event_bus_controller.py`

2. **Components** (9 files)
   - `workflow_lifecycle_component.py`
   - `execution_component.py`
   - `node_registry_component.py`
   - `selector_component.py`
   - `trigger_component.py`
   - `project_component.py`
   - `preferences_component.py`
   - `drag_drop_component.py`
   - `autosave_component.py`

3. **UI Components** (12+ files)
   - Panels, toolbars, dialogs, widgets

4. **Refactored Core**
   - `main_window.py` (2,417 → 400 lines)
   - `app.py` (2,929 → 400 lines)

### Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| MainWindow LOC | 2,417 | 400 | 83% reduction |
| CasareRPAApp LOC | 2,929 | 400 | 86% reduction |
| Extracted Controllers | 0 | 7 | New architecture |
| Extracted Components | 0 | 9 | New architecture |
| UI Components | Mixed | 12+ | Modular design |

---

## v2.0 Release Goals

### Feature Completeness

#### Must Have (Blocking Release)

- [ ] All visual nodes loading and functional
- [ ] Workflow execution working (run/pause/resume/stop)
- [ ] Workflow save/load working
- [ ] Node graph editing working
- [ ] All existing tests passing
- [ ] No critical bugs

#### Should Have (Important)

- [ ] ExecutionResult pattern 100% migrated
- [ ] Clean architecture fully implemented
- [ ] All controllers/components extracted
- [ ] Performance benchmarks met
- [ ] Documentation complete

#### Nice to Have (Optional)

- [ ] Enhanced error messages
- [ ] Performance improvements
- [ ] Additional UI polish

### Breaking Changes List

#### v2.0 Breaking Changes (with Migration Path)

1. **ExecutionResult Pattern**
   - **Breaking**: Node `execute()` must return `ExecutionResult` dict
   - **Migration**: Update custom nodes to return `{"success": bool, "data": dict, "error": str}`
   - **Compatibility**: v2.0 supports both patterns, v3.0 removes NodeStatus

2. **Domain Entities**
   - **Breaking**: `Workflow`, `Node`, `Connection` moved to `domain.entities`
   - **Migration**: Update imports from `core` to `domain.entities`
   - **Compatibility**: v2.0 re-exports from old location, v3.0 removes re-exports

3. **WorkflowRunner API**
   - **Breaking**: Constructor parameters changed (removed some options)
   - **Migration**: Use new parameter names (see migration guide)
   - **Compatibility**: v2.0 supports old parameters with warnings, v3.0 removes

4. **Visual Node Imports**
   - **Breaking**: Visual nodes moved to category-based modules
   - **Migration**: Import from new location or use compatibility layer
   - **Compatibility**: v2.0 re-exports from old location, v3.0 removes

5. **Event System**
   - **Breaking**: Canvas events now use `CanvasEventBus`
   - **Migration**: Subscribe to new event bus instead of Qt signals directly
   - **Compatibility**: v2.0 emits both old and new events, v3.0 removes old

### Migration Guide Structure

**File**: `MIGRATION_GUIDE_v2.md`

```markdown
# Migration Guide: v1.x to v2.0

## Overview

Version 2.0 introduces clean architecture patterns while maintaining
backward compatibility. v3.0 will remove all compatibility layers.

## Breaking Changes

### 1. ExecutionResult Pattern

**Old Code (v1.x)**:
```python
async def execute(self, context):
    self.status = NodeStatus.SUCCESS
```

**New Code (v2.0)**:
```python
async def execute(self, context) -> ExecutionResult:
    return {"success": True, "data": {}, "next_nodes": []}
```

### 2. Import Changes

**Old Imports (v1.x)**:
```python
from casare_rpa.canvas.visual_nodes import VisualBrowserNode
from casare_rpa.core.workflow_schema import Workflow
```

**New Imports (v2.0)**:
```python
from casare_rpa.presentation.canvas.visual_nodes.browser import VisualBrowserNode
from casare_rpa.domain.entities.workflow import Workflow
```

**Compatibility Layer (v2.0 only)**:
```python
# Still works in v2.0, removed in v3.0
from casare_rpa.canvas.visual_nodes import VisualBrowserNode
```

## Deprecation Timeline

- **v2.0** (December 2025): Compatibility layers active, warnings issued
- **v2.5** (March 2026): Deprecation warnings increase
- **v3.0** (June 2026): Compatibility layers removed

## Automated Migration Tool

```bash
# Run migration tool to update imports
python scripts/migrate_to_v2.py --path src/

# Dry run to see changes
python scripts/migrate_to_v2.py --path src/ --dry-run
```
```

### Testing Requirements

#### Unit Tests

- [ ] All domain entities tested (100% coverage)
- [ ] All controllers tested (90%+ coverage)
- [ ] All components tested (90%+ coverage)
- [ ] All node modules tested (existing coverage maintained)

#### Integration Tests

- [ ] Workflow execution end-to-end
- [ ] Canvas UI interactions
- [ ] File save/load roundtrip
- [ ] Event bus integration

#### Performance Tests

- [ ] Canvas load time < 2 seconds
- [ ] Node creation < 50ms
- [ ] Workflow save < 500ms
- [ ] Execution startup < 1 second

### Documentation Requirements

#### Required Documentation

- [ ] `ARCHITECTURE.md` - Clean architecture overview
- [ ] `MIGRATION_GUIDE_v2.md` - v1.x to v2.0 migration
- [ ] `REFACTORING_LOG.md` - Complete refactoring history
- [ ] `API_REFERENCE.md` - New API documentation
- [ ] `CONTRIBUTING.md` - Updated contribution guidelines
- [ ] Component README files (per component)

### Release Checklist

- [ ] All tests passing (1255+ tests)
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Migration guide tested
- [ ] Breaking changes documented
- [ ] Changelog updated
- [ ] Version bumped to 2.0.0
- [ ] Git tags created
- [ ] GitHub release created
- [ ] Deprecation warnings added

---

## v3.0 Release Goals

### Objectives

1. **Remove Compatibility Layers**
   - Delete all v1.x compatibility re-exports
   - Enforce clean architecture boundaries
   - Remove deprecated APIs

2. **Full Clean Architecture**
   - 100% dependency inversion compliance
   - Zero infrastructure imports in domain
   - All use cases in application layer

3. **Performance Improvements**
   - Lazy loading for all components
   - Connection pooling optimized
   - Parallel execution improved

4. **API Stability Guarantees**
   - Semantic versioning enforced
   - Public API documented and frozen
   - Breaking changes policy defined

### Breaking Changes (v3.0)

1. **Remove NodeStatus Pattern**
   - All nodes must use ExecutionResult
   - Remove `NodeStatus` enum from public API

2. **Remove Visual Node Compatibility Layer**
   - Old import paths no longer work
   - Must use category-based imports

3. **Remove Old Event System**
   - Qt signals replaced with event bus
   - Direct signal connections no longer work

4. **Enforce Type Hints**
   - All public APIs require type hints
   - mypy strict mode enforced

### Features (v3.0)

1. **Enhanced Execution Engine**
   - Advanced parallel execution
   - Resource pooling across workflows
   - Execution result caching

2. **Improved UI**
   - Performance dashboard
   - Advanced debugging tools
   - Workflow analytics

3. **Enterprise Features**
   - Multi-user collaboration (if applicable)
   - Advanced scheduling
   - Audit logging

---

## Component Data Contracts

### Workflow JSON Schema

#### Current Schema (v1.x)

```json
{
  "metadata": {
    "name": "string",
    "description": "string",
    "author": "string",
    "version": "string",
    "created_at": "ISO8601",
    "modified_at": "ISO8601",
    "tags": ["string"]
  },
  "nodes": {
    "node_id": {
      "type": "string",
      "config": {},
      "x": 0.0,
      "y": 0.0
    }
  },
  "connections": [
    {
      "source": "node_id",
      "source_port": "port_name",
      "target": "node_id",
      "target_port": "port_name"
    }
  ]
}
```

#### Target Schema (v2.0)

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "name": "string",
    "description": "string",
    "author": "string",
    "version": "string",
    "created_at": "ISO8601",
    "modified_at": "ISO8601",
    "tags": ["string"],
    "variables": {
      "var_name": {
        "type": "string|number|boolean",
        "default": "any",
        "description": "string"
      }
    }
  },
  "nodes": [
    {
      "id": "string",
      "type": "string",
      "config": {},
      "position": {"x": 0.0, "y": 0.0},
      "metadata": {
        "label": "string",
        "description": "string",
        "breakpoint": false
      }
    }
  ],
  "connections": [
    {
      "id": "string",
      "source_node": "string",
      "source_port": "string",
      "target_node": "string",
      "target_port": "string"
    }
  ],
  "frames": [
    {
      "id": "string",
      "title": "string",
      "nodes": ["node_id"],
      "position": {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}
    }
  ]
}
```

### Node Execution State Schema

#### ExecutionResult Schema (v2.0+)

```typescript
interface ExecutionResult {
  success: boolean;
  data?: {
    [key: string]: any;  // Output port values
  };
  error?: string;  // Error message if success=false
  next_nodes?: string[];  // Node IDs to execute next (for control flow)
  metadata?: {
    execution_time?: number;  // Seconds
    retry_count?: number;
    warnings?: string[];
  };
}
```

#### ExecutionState Schema (Domain)

```typescript
interface ExecutionState {
  workflow_id: string;
  status: "idle" | "running" | "paused" | "stopped" | "completed" | "error";
  current_node_id?: string;
  executed_nodes: string[];
  node_results: {
    [node_id: string]: NodeExecutionResult;
  };
  variables: {
    [var_name: string]: any;
  };
  started_at?: string;  // ISO8601
  completed_at?: string;  // ISO8601
}

interface NodeExecutionResult {
  node_id: string;
  success: boolean;
  data: {[key: string]: any};
  error?: string;
  execution_time: number;
  timestamp: string;  // ISO8601
}
```

### Canvas-to-Runner Communication Protocol

#### Run Workflow Request

```typescript
interface RunWorkflowRequest {
  workflow_id: string;
  initial_variables?: {[key: string]: any};
  execution_mode?: "normal" | "debug" | "validate";
  target_node_id?: string;  // For "Run To Node"
  breakpoints?: string[];  // Node IDs with breakpoints
  options?: {
    continue_on_error?: boolean;
    parallel_execution?: boolean;
    max_parallel_nodes?: number;
    node_timeout?: number;  // Seconds
  };
}
```

#### Execution Events

```typescript
// Event: workflow.started
interface WorkflowStartedEvent {
  workflow_id: string;
  timestamp: string;
  execution_mode: string;
}

// Event: node.started
interface NodeStartedEvent {
  node_id: string;
  node_type: string;
  timestamp: string;
}

// Event: node.completed
interface NodeCompletedEvent {
  node_id: string;
  success: boolean;
  data?: {[key: string]: any};
  error?: string;
  execution_time: number;
  timestamp: string;
}

// Event: workflow.completed
interface WorkflowCompletedEvent {
  workflow_id: string;
  status: "completed" | "error" | "stopped";
  execution_time: number;
  timestamp: string;
  statistics: {
    total_nodes: number;
    executed_nodes: number;
    failed_nodes: number;
    skipped_nodes: number;
  };
}
```

### Robot-to-Orchestrator Communication (Future)

**Note**: Robot/Orchestrator integration not part of this refactoring (Canvas-focused)

Future contract for when Robot/Orchestrator are integrated:

```typescript
// Job submission
interface JobRequest {
  workflow_id: string;
  robot_id?: string;  // Optional robot selection
  priority: number;  // 1-10
  scheduled_time?: string;  // ISO8601
  initial_variables?: {[key: string]: any};
}

// Job status
interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  robot_id?: string;
  started_at?: string;
  completed_at?: string;
  execution_state?: ExecutionState;
}
```

---

## Implementation Roadmap for rpa-engine-architect Agent

### Step-by-Step Implementation Guides

Each refactoring task follows this pattern:

#### Phase 1: Planning (Before Writing Code)

1. **Read Existing Code**
   - Use `Read` tool to examine current implementation
   - Identify responsibilities and dependencies
   - Note coupling points

2. **Design New Structure**
   - Create class diagram (ASCII or description)
   - Define interfaces (ports)
   - Plan data contracts

3. **Identify Breaking Changes**
   - List API changes
   - Document migration path
   - Plan compatibility layer

#### Phase 2: Implementation

1. **Create New Files**
   - Write new classes/modules
   - Implement interfaces
   - Add comprehensive docstrings

2. **Write Tests First** (TDD)
   - Unit tests for new classes
   - Integration tests for interactions
   - Migration tests for compatibility

3. **Refactor Existing Code**
   - Update to use new structure
   - Add compatibility layer
   - Add deprecation warnings

4. **Update Documentation**
   - Update docstrings
   - Update architecture docs
   - Update migration guide

#### Phase 3: Validation

1. **Run Tests**
   - All unit tests pass
   - All integration tests pass
   - Performance benchmarks met

2. **Manual Testing**
   - Canvas loads successfully
   - All features work
   - No visual regressions

3. **Code Review**
   - Self-review for:
     - Type hints complete
     - Docstrings comprehensive
     - No infrastructure in domain
     - Single responsibility maintained

### Code Patterns to Follow

#### 1. Domain Entity Pattern

```python
"""
Domain entity example.

Key principles:
- Dataclass for immutability preference
- Zero infrastructure dependencies
- Business logic only
- Rich behavior, not anemic model
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class DomainEntity:
    """
    Pure domain entity.

    Rules:
    - No Qt imports
    - No database imports
    - No file I/O
    - Pure Python only
    """

    id: str
    name: str
    items: List[str] = field(default_factory=list)

    def add_item(self, item: str) -> None:
        """Business logic method."""
        if item in self.items:
            raise ValueError(f"Item {item} already exists")
        self.items.append(item)

    def validate(self) -> List[str]:
        """
        Validation logic.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not self.name:
            errors.append("Name is required")

        if len(self.items) > 100:
            errors.append("Too many items (max 100)")

        return errors
```

#### 2. Port (Interface) Pattern

```python
"""
Port (interface) example.

Key principles:
- ABC for interface definition
- Domain defines what it needs
- Infrastructure implements how
"""
from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from ..entities.domain_entity import DomainEntity


class EntityRepository(ABC):
    """
    Abstract repository interface.

    Domain defines WHAT it needs.
    Infrastructure implements HOW.
    """

    @abstractmethod
    async def save(self, entity: DomainEntity, path: Path) -> None:
        """Save entity to storage."""
        pass

    @abstractmethod
    async def load(self, path: Path) -> DomainEntity:
        """Load entity from storage."""
        pass

    @abstractmethod
    async def list_all(self, directory: Path) -> List[DomainEntity]:
        """List all entities in directory."""
        pass
```

#### 3. Infrastructure Implementation Pattern

```python
"""
Infrastructure implementation example.

Key principles:
- Implements domain port
- Contains all infrastructure code
- No domain logic (delegates to domain)
"""
import json
from pathlib import Path
from typing import List
from loguru import logger

from ...domain.ports.entity_repository import EntityRepository
from ...domain.entities.domain_entity import DomainEntity


class JsonEntityRepository(EntityRepository):
    """
    JSON file implementation of EntityRepository.

    Infrastructure layer - knows about:
    - File I/O
    - JSON serialization
    - Error handling

    Does NOT know about:
    - Business rules (in domain)
    - UI concerns (in presentation)
    """

    async def save(self, entity: DomainEntity, path: Path) -> None:
        """Save entity to JSON file."""
        logger.info(f"Saving entity to {path}")

        try:
            data = {
                "id": entity.id,
                "name": entity.name,
                "items": entity.items
            }

            path.write_text(json.dumps(data, indent=2))

        except Exception as e:
            logger.error(f"Failed to save entity: {e}")
            raise

    async def load(self, path: Path) -> DomainEntity:
        """Load entity from JSON file."""
        logger.info(f"Loading entity from {path}")

        try:
            data = json.loads(path.read_text())

            return DomainEntity(
                id=data["id"],
                name=data["name"],
                items=data.get("items", [])
            )

        except Exception as e:
            logger.error(f"Failed to load entity: {e}")
            raise
```

#### 4. Controller Pattern (Presentation)

```python
"""
Controller example (Presentation layer).

Key principles:
- Handles user interactions
- Delegates to use cases
- Emits Qt signals for UI updates
- No business logic
"""
from typing import Optional
from PySide6.QtCore import Signal
from loguru import logger

from .base_controller import BaseController
from ...application.use_cases.save_entity import SaveEntityUseCase
from ...domain.entities.domain_entity import DomainEntity


class EntityController(BaseController):
    """
    Controller for entity operations.

    Responsibilities:
    - Handle user actions
    - Coordinate use cases
    - Emit UI update signals

    Does NOT:
    - Contain business logic
    - Directly access infrastructure
    - Manipulate UI widgets
    """

    # Signals for UI updates
    entity_saved = Signal(str)  # entity_id
    entity_save_failed = Signal(str)  # error_message

    def __init__(self, parent=None):
        super().__init__(parent)

        # Dependency injection
        self._save_use_case = SaveEntityUseCase()

    async def save_entity(self, entity: DomainEntity) -> None:
        """
        Save entity.

        Args:
            entity: Entity to save
        """
        logger.info(f"Controller: Saving entity {entity.id}")

        try:
            # Delegate to use case
            await self._save_use_case.execute(entity)

            # Emit success signal
            self.entity_saved.emit(entity.id)

        except Exception as e:
            error_msg = f"Failed to save entity: {str(e)}"
            logger.error(error_msg)

            # Emit error signal
            self.entity_save_failed.emit(error_msg)
```

### Error Handling Standards

#### Pattern 1: Domain Layer Errors

```python
# Domain layer - raise domain exceptions
class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""
    pass


def validate_workflow(workflow: Workflow) -> None:
    """Validate workflow structure."""
    errors = workflow.validate()
    if errors:
        raise WorkflowValidationError(f"Validation failed: {'; '.join(errors)}")
```

#### Pattern 2: Infrastructure Layer Errors

```python
# Infrastructure layer - catch, log, re-raise
from loguru import logger

async def save_workflow(workflow: Workflow, path: Path) -> None:
    """Save workflow to file."""
    try:
        # I/O operation
        path.write_text(serialize_workflow(workflow))

    except PermissionError as e:
        logger.error(f"Permission denied saving workflow: {e}")
        raise WorkflowSaveError(f"Cannot write to {path}") from e

    except Exception as e:
        logger.exception(f"Unexpected error saving workflow: {e}")
        raise
```

#### Pattern 3: Presentation Layer Errors

```python
# Presentation layer - catch, log, show to user
from PySide6.QtWidgets import QMessageBox

async def on_save_clicked(self) -> None:
    """Handle save button click."""
    try:
        await self._controller.save_workflow()

    except WorkflowSaveError as e:
        logger.error(f"Save failed: {e}")
        QMessageBox.critical(
            self,
            "Save Failed",
            f"Could not save workflow:\n{str(e)}"
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        QMessageBox.critical(
            self,
            "Error",
            "An unexpected error occurred. Check logs for details."
        )
```

### Logging Patterns (loguru)

```python
from loguru import logger

# Info level - normal operations
logger.info("Starting workflow execution")

# Debug level - detailed tracing
logger.debug(f"Node {node_id} inputs: {inputs}")

# Warning level - recoverable issues
logger.warning(f"Node {node_id} took {duration}s (expected < 1s)")

# Error level - operation failed
logger.error(f"Failed to load workflow: {error}")

# Exception level - unexpected errors with traceback
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Unexpected error: {e}")

# Structured logging with context
logger.bind(
    workflow_id="wf_123",
    node_id="node_456"
).info("Node execution completed")
```

### Type Hint Requirements

```python
"""
Type hint examples.

Requirements:
- All function signatures must have type hints
- All class attributes must have type hints
- Use modern Python 3.12+ syntax
"""
from typing import Optional, List, Dict, Any
from pathlib import Path


# ✅ Good - complete type hints
async def execute_workflow(
    workflow: Workflow,
    initial_variables: Optional[Dict[str, Any]] = None,
    timeout: float = 120.0
) -> ExecutionState:
    """Execute workflow with timeout."""
    pass


# ❌ Bad - missing type hints
async def execute_workflow(workflow, initial_variables=None, timeout=120.0):
    """Execute workflow with timeout."""
    pass


# ✅ Good - class with typed attributes
class WorkflowRunner:
    """Workflow execution engine."""

    workflow: Workflow
    timeout: float
    state: ExecutionState
    _runner: Optional[asyncio.Task] = None

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.timeout = 120.0


# ✅ Good - modern union syntax (Python 3.12+)
def get_node(node_id: str) -> Node | None:
    """Get node by ID."""
    pass


# ❌ Bad - old union syntax
from typing import Union
def get_node(node_id: str) -> Union[Node, None]:
    pass
```

---

## Risk Assessment & Mitigation

### High-Risk Areas

#### 1. WorkflowRunner Refactoring

**Risk**: Breaking existing workflows
**Probability**: Medium
**Impact**: High

**Mitigation**:
- Maintain full backward compatibility in v2.0
- Comprehensive integration tests
- Gradual migration with compatibility layer
- Performance benchmarks to catch regressions

#### 2. ExecutionResult Migration

**Risk**: Missing edge cases in node logic
**Probability**: Medium
**Impact**: Medium

**Mitigation**:
- Automated testing for each migrated node
- Pattern validation script
- Manual testing of critical paths
- Rollback plan if issues found

#### 3. UI Controller Extraction

**Risk**: Signal/slot connection errors
**Probability**: Low
**Impact**: Medium

**Mitigation**:
- Incremental extraction (one controller at a time)
- UI interaction tests
- Manual testing checklist
- Event bus logging for debugging

### Medium-Risk Areas

#### 4. Domain Layer Dependencies

**Risk**: Accidental infrastructure imports in domain
**Probability**: Low
**Impact**: Medium

**Mitigation**:
- Import validation script
- mypy strict mode
- Code review checklist
- CI checks for domain purity

#### 5. Performance Regression

**Risk**: Refactored code slower than original
**Probability**: Low
**Impact**: Medium

**Mitigation**:
- Benchmark suite
- Performance tests in CI
- Profiling before/after
- Optimization if needed

### Low-Risk Areas

#### 6. Documentation Gaps

**Risk**: Incomplete migration guide
**Probability**: Low
**Impact**: Low

**Mitigation**:
- Documentation review checklist
- Examples for all breaking changes
- User feedback during beta

---

## Success Metrics

### Week 2 Success Metrics

- [ ] WorkflowRunner: 1,404 → 200 lines (85%+ reduction)
- [ ] 8 execution classes extracted
- [ ] Domain layer has 0 infrastructure imports
- [ ] All 52+ node modules use ExecutionResult
- [ ] All tests pass (1255+)
- [ ] Canvas loads successfully

### Week 3 Success Metrics

- [ ] MainWindow: 2,417 → 400 lines (83%+ reduction)
- [ ] CasareRPAApp: 2,929 → 400 lines (86%+ reduction)
- [ ] 7 controllers extracted
- [ ] 9 components extracted
- [ ] 12+ UI components extracted
- [ ] Event bus functional
- [ ] No performance regression

### Overall Success Metrics

- [ ] 90%+ code navigability improvement
- [ ] Zero critical bugs
- [ ] < 10% performance impact
- [ ] 100% test pass rate
- [ ] Documentation complete
- [ ] Migration guide validated

---

## Appendix

### Glossary

**Clean Architecture**: Architectural pattern separating concerns into layers (domain, application, infrastructure, presentation) with dependency inversion

**Domain Layer**: Core business logic with zero infrastructure dependencies

**Infrastructure Layer**: Framework implementations, file I/O, database, external APIs

**Presentation Layer**: UI components (Qt widgets, controllers)

**Application Layer**: Use cases coordinating domain and infrastructure

**Port**: Interface defined by domain, implemented by infrastructure

**Adapter**: Implementation of a port in infrastructure layer

**ExecutionResult**: New pattern for node execution return values

**NodeStatus**: Old pattern for tracking node state (deprecated in v3.0)

### References

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### File Path Reference

All paths in this document are relative to:
`C:\Users\Rau\Desktop\CasareRPA\`

**Key Directories**:
- `src/casare_rpa/domain/` - Domain layer
- `src/casare_rpa/application/` - Application layer
- `src/casare_rpa/infrastructure/` - Infrastructure layer
- `src/casare_rpa/presentation/canvas/` - Canvas UI
- `src/casare_rpa/core/` - Legacy core (being migrated)
- `src/casare_rpa/runner/` - Workflow runner
- `src/casare_rpa/nodes/` - Node implementations
- `tests/` - Test suites

---

**Last Updated**: November 27, 2025
**Document Version**: 1.0.0
**Status**: Draft for Review
