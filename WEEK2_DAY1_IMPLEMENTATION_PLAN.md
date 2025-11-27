# Week 2 Day 1: Domain Entities Extraction - Implementation Plan

**Document Version**: 1.0.0
**Created**: November 27, 2025
**Author**: rpa-system-architect
**Target Implementer**: rpa-engine-architect
**Estimated Duration**: 6-8 hours

---

## Overview

This document provides a comprehensive implementation plan for extracting pure domain entities from the existing codebase. The goal is to create a clean domain layer with zero infrastructure dependencies, following Domain-Driven Design (DDD) principles.

### Current State Analysis

After thorough analysis of the existing codebase, I have identified the following:

**Existing Domain Entities (Already Implemented)**:
- `src/casare_rpa/domain/entities/workflow.py` - Contains `WorkflowSchema` class (424 lines)
- `src/casare_rpa/domain/entities/execution_state.py` - Contains `ExecutionState` class (294 lines)
- `src/casare_rpa/domain/entities/node_connection.py` - Contains `NodeConnection` class (120 lines)
- `src/casare_rpa/domain/entities/workflow_metadata.py` - Contains `WorkflowMetadata` class (96 lines)
- `src/casare_rpa/domain/value_objects/types.py` - Contains `NodeStatus` enum and type aliases (320 lines)
- `src/casare_rpa/domain/services/execution_orchestrator.py` - Contains `ExecutionOrchestrator` (539 lines)

**Key Finding**: The domain layer already exists but has several architectural issues:
1. `WorkflowSchema` has infrastructure dependencies (`orjson`, `loguru`, file I/O)
2. Missing pure `Node` entity (currently uses `SerializedNode` type alias)
3. Missing pure `Connection` entity (using `NodeConnection` which is almost pure)
4. `ExecutionState` has infrastructure leakage (`loguru` imports)
5. Domain `__init__.py` exports nothing (`__all__ = []`)

### Objective

Transform the existing domain entities into truly pure domain objects with:
- Zero infrastructure dependencies
- Complete type safety with strict hints
- Comprehensive validation logic
- Clear serialization contracts
- Full test coverage

---

## Detailed Task Breakdown

### Phase 1: Analysis and Preparation (1 hour)

| Time | Task | Description |
|------|------|-------------|
| 0:00-0:20 | Read existing domain entities | Understand current implementation patterns |
| 0:20-0:40 | Document infrastructure leakage | List all non-domain imports to remove |
| 0:40-1:00 | Create test scaffolding | Set up `tests/domain/` directory structure |

#### Critical Files to Analyze:
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\workflow.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\execution_state.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\value_objects\types.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\runner\workflow_runner.py`

### Phase 2: Create Pure Node Entity (1.5 hours)

| Time | Task | Description |
|------|------|-------------|
| 1:00-1:30 | Create `node.py` | Pure node domain entity |
| 1:30-2:00 | Create node validation | Node-level validation rules |
| 2:00-2:30 | Write node tests | Unit tests for Node entity |

**File to Create**: `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\node.py`

### Phase 3: Refactor Connection Entity (30 minutes)

| Time | Task | Description |
|------|------|-------------|
| 2:30-3:00 | Rename and enhance `NodeConnection` | Make immutable with `@dataclass(frozen=True)` |

**File to Modify**: `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\node_connection.py`

### Phase 4: Refactor WorkflowSchema to Pure Workflow (2 hours)

| Time | Task | Description |
|------|------|-------------|
| 3:00-3:30 | Create pure `Workflow` entity | Domain aggregate root without I/O |
| 3:30-4:00 | Extract serialization to infrastructure | Move `save_to_file`/`load_from_file` |
| 4:00-4:30 | Implement graph validation | Cycle detection, unreachable nodes |
| 4:30-5:00 | Write workflow tests | Unit tests for Workflow entity |

**Files to Create/Modify**:
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\workflow_entity.py` (NEW)
- Keep `workflow.py` as `WorkflowSchema` for backward compatibility

### Phase 5: Refactor ExecutionState (1 hour)

| Time | Task | Description |
|------|------|-------------|
| 5:00-5:30 | Remove infrastructure from ExecutionState | Remove `loguru` dependency |
| 5:30-6:00 | Add NodeExecutionResult | Result type for node execution |

**File to Modify**: `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\execution_state.py`

### Phase 6: Create Domain Ports (1 hour)

| Time | Task | Description |
|------|------|-------------|
| 6:00-6:30 | Create `WorkflowRepository` port | Interface for persistence |
| 6:30-7:00 | Create `ExecutionEngine` port | Interface for execution |

**Files to Create**:
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ports\workflow_repository.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ports\execution_engine.py`

### Phase 7: Update Exports and Integration (30 minutes)

| Time | Task | Description |
|------|------|-------------|
| 7:00-7:30 | Update `__init__.py` files | Proper exports, maintain backward compat |

---

## File Structure and Locations

### Directory Structure After Implementation

```
src/casare_rpa/domain/
    __init__.py                          # Domain layer exports
    entities/
        __init__.py                      # Entity exports
        node.py                          # NEW: Pure Node entity
        node_connection.py               # MODIFIED: Immutable Connection
        workflow_entity.py               # NEW: Pure Workflow aggregate
        workflow.py                      # KEEP: WorkflowSchema (backward compat)
        workflow_metadata.py             # KEEP: WorkflowMetadata
        execution_state.py               # MODIFIED: Remove infrastructure
        execution_result.py              # NEW: NodeExecutionResult
        project.py                       # KEEP: Project entities (unchanged)
    value_objects/
        __init__.py                      # Value object exports
        types.py                         # KEEP: Enums and type aliases
        port.py                          # KEEP: Port value object
    services/
        __init__.py                      # Service exports
        execution_orchestrator.py        # KEEP: Domain service (unchanged)
        project_context.py               # KEEP: Project context (unchanged)
    ports/
        __init__.py                      # Port exports
        workflow_repository.py           # NEW: Repository interface
        execution_engine.py              # NEW: Execution interface
        event_publisher.py               # NEW: Event publishing interface
    repositories/
        __init__.py                      # (placeholder for future)

tests/domain/
    __init__.py
    entities/
        __init__.py
        test_node.py                     # NEW
        test_connection.py               # NEW
        test_workflow.py                 # NEW
        test_execution_state.py          # NEW
        test_execution_result.py         # NEW
    services/
        __init__.py
        test_execution_orchestrator.py   # NEW
    ports/
        __init__.py
        test_workflow_repository.py      # NEW (mock implementations)
```

### Import Hierarchy

```
domain/
    entities/ (no external imports except typing, datetime, enum, dataclasses)
        node.py -> value_objects/types.py
        node_connection.py -> value_objects/types.py
        workflow_entity.py -> node.py, node_connection.py, workflow_metadata.py
        execution_state.py -> value_objects/types.py
        execution_result.py -> (none)
    value_objects/ (no external imports)
        types.py -> (none, only stdlib)
        port.py -> types.py
    services/ (can import entities, value_objects)
        execution_orchestrator.py -> entities/, value_objects/
    ports/ (interfaces only, no implementation imports)
        workflow_repository.py -> entities/workflow_entity.py
        execution_engine.py -> entities/workflow_entity.py, entities/execution_state.py
```

---

## Code Patterns and Examples

### Decision: dataclass vs Pydantic vs Plain Class

| Entity | Recommendation | Rationale |
|--------|----------------|-----------|
| Node | `@dataclass` | Simple data container with methods |
| Connection | `@dataclass(frozen=True)` | Immutable value object |
| Workflow | Plain class | Complex aggregate with business logic |
| WorkflowMetadata | `@dataclass` | Simple data transfer object |
| ExecutionState | Plain class | Mutable state with complex methods |
| NodeExecutionResult | `@dataclass(frozen=True)` | Immutable result object |

**Rationale**: Avoid Pydantic to keep domain layer dependency-free. Standard library `dataclasses` provide enough functionality.

---

### Entity 1: Node (`node.py`)

```python
# c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\node.py
"""
CasareRPA - Domain Entity: Node
Pure domain representation of a workflow node.

CRITICAL: This entity has ZERO infrastructure dependencies.
It knows nothing about:
- How nodes are persisted (JSON, DB)
- How nodes are displayed (Qt, NodeGraphQt)
- How nodes are executed (Playwright, async)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum, auto


class NodeStatus(Enum):
    """Execution status of a node (pure domain enum)."""
    IDLE = auto()
    RUNNING = auto()
    SUCCESS = auto()
    ERROR = auto()
    SKIPPED = auto()
    CANCELLED = auto()


@dataclass
class PortDefinition:
    """Definition of a node port."""
    name: str
    port_type: str  # "input" or "output"
    data_type: str  # "STRING", "INTEGER", etc.
    label: Optional[str] = None
    required: bool = True
    default_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize port definition to dictionary."""
        return {
            "name": self.name,
            "port_type": self.port_type,
            "data_type": self.data_type,
            "label": self.label,
            "required": self.required,
            "default_value": self.default_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortDefinition":
        """Create port definition from dictionary."""
        return cls(
            name=data.get("name", ""),
            port_type=data.get("port_type", "input"),
            data_type=data.get("data_type", "ANY"),
            label=data.get("label"),
            required=data.get("required", True),
            default_value=data.get("default_value"),
        )


@dataclass
class Node:
    """
    Domain entity representing a workflow node.

    This is a pure domain entity with no infrastructure concerns.
    It represents the business concept of a node in a workflow.

    Attributes:
        node_id: Unique identifier for this node instance
        node_type: Type name of the node (e.g., "StartNode", "ClickNode")
        config: Node-specific configuration
        input_ports: Definitions of input ports
        output_ports: Definitions of output ports
        position: Visual position (x, y) for serialization
        status: Current execution status
        error_message: Error message if status is ERROR
        metadata: Additional metadata (category, description, etc.)
    """

    node_id: str
    node_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    input_ports: Dict[str, PortDefinition] = field(default_factory=dict)
    output_ports: Dict[str, PortDefinition] = field(default_factory=dict)
    position: tuple[float, float] = field(default=(0.0, 0.0))
    status: NodeStatus = field(default=NodeStatus.IDLE)
    error_message: Optional[str] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime values (not persisted)
    _input_values: Dict[str, Any] = field(default_factory=dict, repr=False)
    _output_values: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Validate node after initialization."""
        if not self.node_id:
            raise ValueError("node_id cannot be empty")
        if not self.node_type:
            raise ValueError("node_type cannot be empty")

    # ========================================================================
    # STATUS MANAGEMENT
    # ========================================================================

    def reset(self) -> None:
        """Reset node to initial idle state."""
        self.status = NodeStatus.IDLE
        self.error_message = None
        self._input_values.clear()
        self._output_values.clear()

    def mark_running(self) -> None:
        """Mark node as currently executing."""
        self.status = NodeStatus.RUNNING
        self.error_message = None

    def mark_success(self) -> None:
        """Mark node as successfully completed."""
        self.status = NodeStatus.SUCCESS
        self.error_message = None

    def mark_error(self, message: str) -> None:
        """Mark node as failed with error message."""
        self.status = NodeStatus.ERROR
        self.error_message = message

    def mark_skipped(self) -> None:
        """Mark node as skipped (conditional logic bypassed it)."""
        self.status = NodeStatus.SKIPPED
        self.error_message = None

    def mark_cancelled(self) -> None:
        """Mark node as cancelled (user stopped execution)."""
        self.status = NodeStatus.CANCELLED
        self.error_message = None

    @property
    def is_completed(self) -> bool:
        """Check if node has finished executing (success or error)."""
        return self.status in (NodeStatus.SUCCESS, NodeStatus.ERROR,
                               NodeStatus.SKIPPED, NodeStatus.CANCELLED)

    @property
    def is_successful(self) -> bool:
        """Check if node completed successfully."""
        return self.status == NodeStatus.SUCCESS

    @property
    def has_error(self) -> bool:
        """Check if node has an error."""
        return self.status == NodeStatus.ERROR

    # ========================================================================
    # PORT VALUE MANAGEMENT (Runtime)
    # ========================================================================

    def set_input_value(self, port_name: str, value: Any) -> None:
        """Set the runtime value of an input port."""
        if port_name not in self.input_ports:
            raise ValueError(f"Input port '{port_name}' not defined on {self.node_type}")
        self._input_values[port_name] = value

    def get_input_value(self, port_name: str, default: Any = None) -> Any:
        """Get the runtime value of an input port."""
        return self._input_values.get(port_name, default)

    def set_output_value(self, port_name: str, value: Any) -> None:
        """Set the runtime value of an output port."""
        if port_name not in self.output_ports:
            raise ValueError(f"Output port '{port_name}' not defined on {self.node_type}")
        self._output_values[port_name] = value

    def get_output_value(self, port_name: str, default: Any = None) -> Any:
        """Get the runtime value of an output port."""
        return self._output_values.get(port_name, default)

    def get_all_input_values(self) -> Dict[str, Any]:
        """Get all input port values."""
        return self._input_values.copy()

    def get_all_output_values(self) -> Dict[str, Any]:
        """Get all output port values."""
        return self._output_values.copy()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate node configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []

        # Check required input ports have values (only if node has been executed)
        if self.status != NodeStatus.IDLE:
            for port_name, port_def in self.input_ports.items():
                if port_def.required and port_name not in self._input_values:
                    errors.append(f"Required input port '{port_name}' has no value")

        # Validate node_id format (should be UUID-based)
        if len(self.node_id) < 8:
            errors.append(f"node_id '{self.node_id}' appears to be invalid")

        return (len(errors) == 0, errors)

    def validate_config(self, required_keys: List[str]) -> tuple[bool, List[str]]:
        """
        Validate that required configuration keys are present.

        Args:
            required_keys: List of required configuration key names

        Returns:
            Tuple of (is_valid, list of missing keys)
        """
        missing = [key for key in required_keys if key not in self.config]
        return (len(missing) == 0, missing)

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize node to dictionary for persistence.

        Note: Runtime values (_input_values, _output_values) are NOT serialized.
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "config": self.config.copy(),
            "input_ports": {
                name: port.to_dict()
                for name, port in self.input_ports.items()
            },
            "output_ports": {
                name: port.to_dict()
                for name, port in self.output_ports.items()
            },
            "position": list(self.position),
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """
        Create node from dictionary.

        Args:
            data: Serialized node dictionary

        Returns:
            Node instance
        """
        input_ports = {
            name: PortDefinition.from_dict(port_data)
            for name, port_data in data.get("input_ports", {}).items()
        }
        output_ports = {
            name: PortDefinition.from_dict(port_data)
            for name, port_data in data.get("output_ports", {}).items()
        }

        position_data = data.get("position", [0.0, 0.0])
        position = (
            float(position_data[0]) if len(position_data) > 0 else 0.0,
            float(position_data[1]) if len(position_data) > 1 else 0.0,
        )

        return cls(
            node_id=data.get("node_id", ""),
            node_type=data.get("node_type", ""),
            config=data.get("config", {}),
            input_ports=input_ports,
            output_ports=output_ports,
            position=position,
            metadata=data.get("metadata", {}),
        )

    # ========================================================================
    # SPECIAL METHODS
    # ========================================================================

    def __eq__(self, other: object) -> bool:
        """Nodes are equal if they have the same node_id."""
        if not isinstance(other, Node):
            return False
        return self.node_id == other.node_id

    def __hash__(self) -> int:
        """Hash based on node_id (identity)."""
        return hash(self.node_id)

    def __repr__(self) -> str:
        """String representation."""
        return f"Node(id='{self.node_id}', type='{self.node_type}', status={self.status.name})"
```

---

### Entity 2: Connection (`connection.py` - Immutable)

```python
# c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\connection.py
"""
CasareRPA - Domain Entity: Connection
Immutable value object representing a connection between node ports.

CRITICAL: This entity is FROZEN (immutable) to ensure workflow integrity.
Connections cannot be modified after creation - only added or removed.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Connection:
    """
    Immutable value object representing a connection between two node ports.

    A connection links an output port of one node to an input port of another,
    defining the flow of data or execution control in a workflow.

    Attributes:
        source_node_id: ID of the source node
        source_port: Name of the source output port
        target_node_id: ID of the target node
        target_port: Name of the target input port

    Note: This class is immutable (frozen=True) to ensure workflow integrity.
    Connections should not be modified - only added or removed from workflows.
    """

    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str

    def __post_init__(self) -> None:
        """Validate connection after initialization."""
        # Using object.__setattr__ because dataclass is frozen
        if not self.source_node_id:
            raise ValueError("source_node_id cannot be empty")
        if not self.source_port:
            raise ValueError("source_port cannot be empty")
        if not self.target_node_id:
            raise ValueError("target_node_id cannot be empty")
        if not self.target_port:
            raise ValueError("target_port cannot be empty")
        if self.source_node_id == self.target_node_id:
            raise ValueError("Connection cannot connect a node to itself")

    @property
    def source_id(self) -> str:
        """Get full source port identifier (node_id.port_name)."""
        return f"{self.source_node_id}.{self.source_port}"

    @property
    def target_id(self) -> str:
        """Get full target port identifier (node_id.port_name)."""
        return f"{self.target_node_id}.{self.target_port}"

    @property
    def is_execution_connection(self) -> bool:
        """Check if this is an execution flow connection (vs data connection)."""
        return "exec" in self.source_port.lower() or "exec" in self.target_port.lower()

    def involves_node(self, node_id: str) -> bool:
        """Check if this connection involves a specific node."""
        return node_id in (self.source_node_id, self.target_node_id)

    def to_dict(self) -> Dict[str, str]:
        """
        Serialize connection to dictionary.

        Returns:
            Dictionary with connection data
        """
        return {
            "source_node": self.source_node_id,
            "source_port": self.source_port,
            "target_node": self.target_node_id,
            "target_port": self.target_port,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Connection":
        """
        Create connection from dictionary.

        Args:
            data: Dictionary containing connection data

        Returns:
            Connection instance
        """
        return cls(
            source_node_id=data.get("source_node", data.get("source_node_id", "")),
            source_port=data["source_port"],
            target_node_id=data.get("target_node", data.get("target_node_id", "")),
            target_port=data["target_port"],
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.source_id} -> {self.target_id}"

    def __repr__(self) -> str:
        """Debug string representation."""
        return f"Connection({self.source_id} -> {self.target_id})"
```

---

### Entity 3: Workflow (Pure Domain Aggregate)

```python
# c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\workflow_entity.py
"""
CasareRPA - Domain Entity: Workflow (Pure Domain Aggregate)

This is the PURE domain version of Workflow with NO infrastructure dependencies.
It knows nothing about:
- File I/O (JSON, orjson)
- Logging (loguru)
- External frameworks

For file operations, use the WorkflowRepository in infrastructure layer.

MIGRATION NOTE: This class coexists with WorkflowSchema during migration period.
Eventually, WorkflowSchema will be deprecated in favor of this pure domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .node import Node
from .connection import Connection


@dataclass
class WorkflowMetadata:
    """
    Metadata about a workflow.

    Pure value object with no infrastructure dependencies.
    """
    name: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    schema_version: str = "1.0.0"

    def update_modified(self) -> None:
        """Update the modified timestamp to current time."""
        self.modified_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "tags": self.tags.copy(),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowMetadata":
        """Create metadata from dictionary."""
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()

        modified_at = None
        if data.get("modified_at"):
            try:
                modified_at = datetime.fromisoformat(data["modified_at"])
            except (ValueError, TypeError):
                modified_at = datetime.now()

        return cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            created_at=created_at,
            modified_at=modified_at,
            tags=data.get("tags", []),
            schema_version=data.get("schema_version", "1.0.0"),
        )


class Workflow:
    """
    Pure domain aggregate root representing a workflow.

    This class manages the collection of nodes and connections that form
    a workflow. It contains business logic for:
    - Adding/removing nodes
    - Adding/removing connections
    - Validating workflow structure (cycles, reachability)
    - Querying workflow topology

    ZERO infrastructure dependencies - no logging, no file I/O, no frameworks.
    """

    def __init__(
        self,
        metadata: Optional[WorkflowMetadata] = None,
        nodes: Optional[Dict[str, Node]] = None,
        connections: Optional[List[Connection]] = None,
        variables: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize workflow.

        Args:
            metadata: Workflow metadata (creates default if None)
            nodes: Dictionary of node_id -> Node
            connections: List of Connection objects
            variables: Global workflow variables
            settings: Workflow execution settings
        """
        self.metadata = metadata or WorkflowMetadata(name="Untitled Workflow")
        self._nodes: Dict[str, Node] = nodes or {}
        self._connections: List[Connection] = connections or []
        self.variables: Dict[str, Any] = variables or {}
        self.settings: Dict[str, Any] = settings or {
            "stop_on_error": True,
            "timeout": 30,
            "retry_count": 0,
        }

    # ========================================================================
    # NODE MANAGEMENT
    # ========================================================================

    @property
    def nodes(self) -> Dict[str, Node]:
        """Get all nodes (read-only view)."""
        return self._nodes.copy()

    @property
    def node_count(self) -> int:
        """Get the number of nodes in the workflow."""
        return len(self._nodes)

    def add_node(self, node: Node) -> None:
        """
        Add a node to the workflow.

        Args:
            node: Node to add

        Raises:
            ValueError: If node with same ID already exists
        """
        if node.node_id in self._nodes:
            raise ValueError(f"Node '{node.node_id}' already exists in workflow")
        self._nodes[node.node_id] = node
        self.metadata.update_modified()

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node and all its connections from the workflow.

        Args:
            node_id: ID of node to remove

        Raises:
            ValueError: If node not found
        """
        if node_id not in self._nodes:
            raise ValueError(f"Node '{node_id}' not found in workflow")

        # Remove all connections involving this node
        self._connections = [
            conn for conn in self._connections
            if not conn.involves_node(node_id)
        ]

        del self._nodes[node_id]
        self.metadata.update_modified()

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.

        Args:
            node_id: Node ID

        Returns:
            Node or None if not found
        """
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the workflow."""
        return node_id in self._nodes

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    @property
    def connections(self) -> List[Connection]:
        """Get all connections (read-only copy)."""
        return self._connections.copy()

    @property
    def connection_count(self) -> int:
        """Get the number of connections in the workflow."""
        return len(self._connections)

    def add_connection(self, connection: Connection) -> None:
        """
        Add a connection between nodes.

        Args:
            connection: Connection to add

        Raises:
            ValueError: If source or target node doesn't exist
            ValueError: If connection already exists
        """
        # Validate nodes exist
        if connection.source_node_id not in self._nodes:
            raise ValueError(f"Source node '{connection.source_node_id}' not found")
        if connection.target_node_id not in self._nodes:
            raise ValueError(f"Target node '{connection.target_node_id}' not found")

        # Check for duplicate
        if connection in self._connections:
            raise ValueError(f"Connection {connection} already exists")

        self._connections.append(connection)
        self.metadata.update_modified()

    def remove_connection(self, connection: Connection) -> None:
        """
        Remove a connection from the workflow.

        Args:
            connection: Connection to remove

        Raises:
            ValueError: If connection not found
        """
        try:
            self._connections.remove(connection)
            self.metadata.update_modified()
        except ValueError:
            raise ValueError(f"Connection {connection} not found in workflow")

    def get_connections_from(self, node_id: str) -> List[Connection]:
        """
        Get all connections originating from a node.

        Args:
            node_id: Source node ID

        Returns:
            List of connections from this node
        """
        return [conn for conn in self._connections if conn.source_node_id == node_id]

    def get_connections_to(self, node_id: str) -> List[Connection]:
        """
        Get all connections targeting a node.

        Args:
            node_id: Target node ID

        Returns:
            List of connections to this node
        """
        return [conn for conn in self._connections if conn.target_node_id == node_id]

    # ========================================================================
    # TOPOLOGY QUERIES
    # ========================================================================

    def get_start_nodes(self) -> List[Node]:
        """
        Get all start nodes in the workflow.

        Start nodes are nodes with type "StartNode" or nodes with no
        incoming execution connections.

        Returns:
            List of start nodes
        """
        start_nodes = []

        for node in self._nodes.values():
            # Explicit StartNode type
            if node.node_type == "StartNode":
                start_nodes.append(node)
                continue

            # Or nodes with no incoming exec connections
            has_incoming_exec = any(
                conn.target_node_id == node.node_id and conn.is_execution_connection
                for conn in self._connections
            )
            if not has_incoming_exec:
                # Only include if it has outgoing connections (not orphan)
                has_outgoing = any(
                    conn.source_node_id == node.node_id
                    for conn in self._connections
                )
                if has_outgoing and node.node_type != "EndNode":
                    start_nodes.append(node)

        return start_nodes

    def get_end_nodes(self) -> List[Node]:
        """
        Get all end nodes in the workflow.

        End nodes are nodes with type "EndNode" or nodes with no
        outgoing execution connections.

        Returns:
            List of end nodes
        """
        end_nodes = []

        for node in self._nodes.values():
            if node.node_type == "EndNode":
                end_nodes.append(node)
                continue

            has_outgoing_exec = any(
                conn.source_node_id == node.node_id and conn.is_execution_connection
                for conn in self._connections
            )
            if not has_outgoing_exec:
                has_incoming = any(
                    conn.target_node_id == node.node_id
                    for conn in self._connections
                )
                if has_incoming and node.node_type != "StartNode":
                    end_nodes.append(node)

        return end_nodes

    def get_next_nodes(self, node_id: str) -> List[Node]:
        """
        Get nodes connected to this node's outputs (successors).

        Args:
            node_id: Source node ID

        Returns:
            List of successor nodes
        """
        next_node_ids = [
            conn.target_node_id
            for conn in self._connections
            if conn.source_node_id == node_id
        ]
        return [self._nodes[nid] for nid in next_node_ids if nid in self._nodes]

    def get_previous_nodes(self, node_id: str) -> List[Node]:
        """
        Get nodes that connect to this node (predecessors).

        Args:
            node_id: Target node ID

        Returns:
            List of predecessor nodes
        """
        prev_node_ids = [
            conn.source_node_id
            for conn in self._connections
            if conn.target_node_id == node_id
        ]
        return [self._nodes[nid] for nid in prev_node_ids if nid in self._nodes]

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate(self) -> List[str]:
        """
        Validate workflow structure.

        Checks:
        - At least one start node exists
        - No circular dependencies (for non-loop structures)
        - No unreachable nodes
        - All connections reference valid nodes

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # Check for start nodes
        start_nodes = self.get_start_nodes()
        if not start_nodes:
            errors.append("Workflow must have at least one Start node")

        # Check for cycles (excluding intentional loop structures)
        cycle_errors = self._detect_cycles()
        errors.extend(cycle_errors)

        # Check for unreachable nodes
        unreachable = self._get_unreachable_nodes()
        if unreachable:
            errors.append(f"Unreachable nodes: {', '.join(unreachable)}")

        # Validate all connections reference existing nodes
        for conn in self._connections:
            if conn.source_node_id not in self._nodes:
                errors.append(f"Connection references missing source node: {conn.source_node_id}")
            if conn.target_node_id not in self._nodes:
                errors.append(f"Connection references missing target node: {conn.target_node_id}")

        return errors

    def _detect_cycles(self) -> List[str]:
        """
        Detect cycles in the workflow using DFS.

        Note: Loops (ForLoop, WhileLoop) are intentional cycles and should
        be handled separately. This detects unintentional cycles.

        Returns:
            List of error messages for detected cycles
        """
        errors: List[str] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str, path: List[str]) -> bool:
            """DFS to detect back edges (cycles)."""
            visited.add(node_id)
            rec_stack.add(node_id)

            for next_node in self.get_next_nodes(node_id):
                # Skip intentional loop back-edges
                node = self._nodes.get(node_id)
                if node and node.node_type in ("ForLoopEndNode", "WhileLoopEndNode"):
                    continue

                if next_node.node_id not in visited:
                    if dfs(next_node.node_id, path + [next_node.node_id]):
                        return True
                elif next_node.node_id in rec_stack:
                    # Found a cycle
                    cycle_path = path[path.index(next_node.node_id):] + [next_node.node_id]
                    errors.append(f"Cycle detected: {' -> '.join(cycle_path)}")
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self._nodes:
            if node_id not in visited:
                dfs(node_id, [node_id])

        return errors

    def _get_unreachable_nodes(self) -> List[str]:
        """
        Find nodes not reachable from any start node.

        Returns:
            List of unreachable node IDs
        """
        if not self._nodes:
            return []

        reachable: Set[str] = set()

        def dfs(node_id: str) -> None:
            if node_id in reachable:
                return
            reachable.add(node_id)
            for next_node in self.get_next_nodes(node_id):
                dfs(next_node.node_id)

        # Start from all start nodes
        for start_node in self.get_start_nodes():
            dfs(start_node.node_id)

        # Find nodes not reached
        return [
            node_id for node_id in self._nodes
            if node_id not in reachable
        ]

    def is_valid(self) -> bool:
        """Check if workflow is valid (no validation errors)."""
        return len(self.validate()) == 0

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize workflow to dictionary.

        Returns:
            Complete workflow data structure
        """
        return {
            "metadata": self.metadata.to_dict(),
            "nodes": {
                node_id: node.to_dict()
                for node_id, node in self._nodes.items()
            },
            "connections": [conn.to_dict() for conn in self._connections],
            "variables": self.variables.copy(),
            "settings": self.settings.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """
        Create workflow from dictionary.

        Args:
            data: Serialized workflow data

        Returns:
            Workflow instance
        """
        metadata = WorkflowMetadata.from_dict(data.get("metadata", {}))

        nodes = {}
        for node_id, node_data in data.get("nodes", {}).items():
            # Handle node_id mismatch (auto-repair)
            if node_data.get("node_id", node_id) != node_id:
                node_data = node_data.copy()
                node_data["node_id"] = node_id
            nodes[node_id] = Node.from_dict(node_data)

        connections = [
            Connection.from_dict(conn_data)
            for conn_data in data.get("connections", [])
        ]

        return cls(
            metadata=metadata,
            nodes=nodes,
            connections=connections,
            variables=data.get("variables", {}),
            settings=data.get("settings", {}),
        )

    # ========================================================================
    # SPECIAL METHODS
    # ========================================================================

    def __len__(self) -> int:
        """Return number of nodes in workflow."""
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if node_id exists in workflow."""
        return node_id in self._nodes

    def __iter__(self):
        """Iterate over nodes."""
        return iter(self._nodes.values())

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Workflow(name='{self.metadata.name}', "
            f"nodes={len(self._nodes)}, "
            f"connections={len(self._connections)})"
        )
```

---

### Entity 4: NodeExecutionResult

```python
# c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\execution_result.py
"""
CasareRPA - Domain Entity: Node Execution Result
Immutable result object from executing a single node.

This is a pure domain entity representing the outcome of node execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class NodeExecutionResult:
    """
    Immutable result of executing a single node.

    This value object captures everything about a node's execution:
    - Success/failure status
    - Output data
    - Error information
    - Timing information
    - Control flow directives

    Being immutable (frozen=True) ensures results cannot be accidentally modified.
    """

    node_id: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Control flow for routing (e.g., "break", "continue", "return")
    control_flow: Optional[str] = None

    # Next nodes to execute (for dynamic routing like If/Switch nodes)
    next_nodes: List[str] = field(default_factory=list)

    # Whether node was bypassed (disabled)
    bypassed: bool = False

    # Retry information
    attempt_number: int = 1
    was_retried: bool = False

    def __post_init__(self) -> None:
        """Validate result after initialization."""
        # Convert mutable defaults (handled by frozen dataclass)
        pass

    @property
    def is_error(self) -> bool:
        """Check if this result represents an error."""
        return not self.success

    @property
    def has_control_flow(self) -> bool:
        """Check if result contains control flow directive."""
        return self.control_flow is not None

    @property
    def has_next_nodes(self) -> bool:
        """Check if result specifies dynamic routing."""
        return len(self.next_nodes) > 0

    @property
    def execution_time_seconds(self) -> float:
        """Get execution time in seconds."""
        return self.execution_time_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize result to dictionary.

        Returns:
            Dictionary representation of result
        """
        return {
            "node_id": self.node_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "control_flow": self.control_flow,
            "next_nodes": list(self.next_nodes),
            "bypassed": self.bypassed,
            "attempt_number": self.attempt_number,
            "was_retried": self.was_retried,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeExecutionResult":
        """Create result from dictionary."""
        timestamp = datetime.now()
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            node_id=data.get("node_id", ""),
            success=data.get("success", False),
            data=data.get("data", {}),
            error=data.get("error"),
            error_code=data.get("error_code"),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            timestamp=timestamp,
            control_flow=data.get("control_flow"),
            next_nodes=data.get("next_nodes", []),
            bypassed=data.get("bypassed", False),
            attempt_number=data.get("attempt_number", 1),
            was_retried=data.get("was_retried", False),
        )

    @classmethod
    def success_result(
        cls,
        node_id: str,
        data: Optional[Dict[str, Any]] = None,
        execution_time_ms: float = 0.0,
        next_nodes: Optional[List[str]] = None,
    ) -> "NodeExecutionResult":
        """
        Factory method for creating a success result.

        Args:
            node_id: ID of the executed node
            data: Output data from the node
            execution_time_ms: Execution time in milliseconds
            next_nodes: Optional list of next nodes for dynamic routing

        Returns:
            Success NodeExecutionResult
        """
        return cls(
            node_id=node_id,
            success=True,
            data=data or {},
            execution_time_ms=execution_time_ms,
            next_nodes=next_nodes or [],
        )

    @classmethod
    def error_result(
        cls,
        node_id: str,
        error: str,
        error_code: Optional[str] = None,
        execution_time_ms: float = 0.0,
        attempt_number: int = 1,
        was_retried: bool = False,
    ) -> "NodeExecutionResult":
        """
        Factory method for creating an error result.

        Args:
            node_id: ID of the executed node
            error: Error message
            error_code: Optional error code for categorization
            execution_time_ms: Execution time in milliseconds
            attempt_number: Which attempt this was (for retry tracking)
            was_retried: Whether this error was retried

        Returns:
            Error NodeExecutionResult
        """
        return cls(
            node_id=node_id,
            success=False,
            error=error,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
            attempt_number=attempt_number,
            was_retried=was_retried,
        )

    @classmethod
    def bypassed_result(cls, node_id: str) -> "NodeExecutionResult":
        """
        Factory method for creating a bypassed (disabled node) result.

        Args:
            node_id: ID of the bypassed node

        Returns:
            Bypassed NodeExecutionResult
        """
        return cls(
            node_id=node_id,
            success=True,
            bypassed=True,
            execution_time_ms=0.0,
        )

    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else f"ERROR: {self.error}"
        return f"NodeExecutionResult(node_id='{self.node_id}', {status}, time={self.execution_time_ms:.2f}ms)"
```

---

### Port Interface: WorkflowRepository

```python
# c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ports\workflow_repository.py
"""
CasareRPA - Domain Port: Workflow Repository
Interface for workflow persistence (Dependency Inversion Principle).

This port defines WHAT operations the domain needs for persistence.
Infrastructure layer provides HOW (JSON files, database, API, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..entities.workflow_entity import Workflow


class WorkflowRepository(ABC):
    """
    Abstract interface for workflow storage.

    This is a PORT in hexagonal architecture - it defines the interface
    that the domain layer uses for persistence, without knowing about
    the actual implementation (JSON, database, API, etc.).

    Implementations:
    - JsonWorkflowRepository (current - JSON files)
    - DatabaseWorkflowRepository (future - database storage)
    - ApiWorkflowRepository (future - remote API)
    """

    @abstractmethod
    async def save(self, workflow: Workflow, path: Path) -> None:
        """
        Save workflow to storage.

        Args:
            workflow: Workflow to save
            path: Path/identifier for the workflow

        Raises:
            PersistenceError: If save fails
        """
        pass

    @abstractmethod
    async def load(self, path: Path) -> Workflow:
        """
        Load workflow from storage.

        Args:
            path: Path/identifier for the workflow

        Returns:
            Loaded workflow

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            PersistenceError: If load fails
        """
        pass

    @abstractmethod
    async def exists(self, path: Path) -> bool:
        """
        Check if workflow exists at path.

        Args:
            path: Path/identifier to check

        Returns:
            True if workflow exists
        """
        pass

    @abstractmethod
    async def delete(self, path: Path) -> None:
        """
        Delete workflow from storage.

        Args:
            path: Path/identifier of workflow to delete

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
        """
        pass

    @abstractmethod
    async def list_workflows(self, directory: Path) -> List[Path]:
        """
        List all workflows in a directory.

        Args:
            directory: Directory to list

        Returns:
            List of workflow paths
        """
        pass

    # Optional: Sync versions for backward compatibility
    def save_sync(self, workflow: Workflow, path: Path) -> None:
        """
        Synchronous save (for backward compatibility).

        Default implementation raises NotImplementedError.
        Override in implementations that support sync operations.
        """
        raise NotImplementedError("Sync save not supported by this repository")

    def load_sync(self, path: Path) -> Workflow:
        """
        Synchronous load (for backward compatibility).

        Default implementation raises NotImplementedError.
        Override in implementations that support sync operations.
        """
        raise NotImplementedError("Sync load not supported by this repository")


class WorkflowNotFoundError(Exception):
    """Raised when a workflow is not found in storage."""

    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Workflow not found: {path}")


class PersistenceError(Exception):
    """Raised when a persistence operation fails."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.cause = cause
        super().__init__(message)
```

---

### Port Interface: ExecutionEngine

```python
# c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ports\execution_engine.py
"""
CasareRPA - Domain Port: Execution Engine
Interface for workflow execution (Dependency Inversion Principle).

This port defines WHAT the domain expects from an execution engine.
Infrastructure layer provides HOW (async runner, parallel executor, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from ..entities.workflow_entity import Workflow
from ..entities.execution_result import NodeExecutionResult


class ExecutionStatus:
    """Execution status constants (pure domain)."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class ExecutionState:
    """
    Pure domain execution state.

    Tracks the state of a workflow execution without infrastructure concerns.
    This is a simplified version for the port interface.
    """

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        self.status = ExecutionStatus.IDLE
        self.current_node_id: Optional[str] = None
        self.executed_nodes: list[str] = []
        self.node_results: Dict[str, NodeExecutionResult] = {}
        self.variables: Dict[str, Any] = {}
        self.errors: list[str] = []

    def record_node_result(self, result: NodeExecutionResult) -> None:
        """Record the result of a node execution."""
        self.executed_nodes.append(result.node_id)
        self.node_results[result.node_id] = result
        if result.is_error and result.error:
            self.errors.append(result.error)


class ExecutionEngine(ABC):
    """
    Abstract interface for workflow execution.

    This port separates WHAT to execute (domain) from HOW to execute
    (infrastructure). Implementations can provide:
    - Sequential execution
    - Parallel execution
    - Distributed execution
    - Mock execution (for testing)
    """

    @abstractmethod
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_variables: Optional[Dict[str, Any]] = None,
        on_node_complete: Optional[Callable[[NodeExecutionResult], None]] = None,
    ) -> ExecutionState:
        """
        Execute a complete workflow.

        Args:
            workflow: Workflow to execute
            initial_variables: Initial variable values
            on_node_complete: Optional callback for each completed node

        Returns:
            Final execution state
        """
        pass

    @abstractmethod
    async def execute_node(
        self,
        workflow: Workflow,
        node_id: str,
        variables: Dict[str, Any],
    ) -> NodeExecutionResult:
        """
        Execute a single node.

        Args:
            workflow: Parent workflow
            node_id: ID of node to execute
            variables: Current variable state

        Returns:
            Node execution result
        """
        pass

    @abstractmethod
    async def pause(self) -> None:
        """Pause execution at next opportunity."""
        pass

    @abstractmethod
    async def resume(self) -> None:
        """Resume paused execution."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop execution as soon as possible."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        pass

    @property
    @abstractmethod
    def is_paused(self) -> bool:
        """Check if execution is paused."""
        pass

    @property
    @abstractmethod
    def current_state(self) -> ExecutionState:
        """Get current execution state."""
        pass
```

---

## Data Contracts

### Node JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Node",
  "type": "object",
  "required": ["node_id", "node_type"],
  "properties": {
    "node_id": {
      "type": "string",
      "description": "Unique identifier (UUID format preferred)",
      "minLength": 1
    },
    "node_type": {
      "type": "string",
      "description": "Node type name (e.g., StartNode, ClickNode)",
      "minLength": 1
    },
    "config": {
      "type": "object",
      "description": "Node-specific configuration",
      "additionalProperties": true
    },
    "input_ports": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/PortDefinition"
      }
    },
    "output_ports": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/PortDefinition"
      }
    },
    "position": {
      "type": "array",
      "items": { "type": "number" },
      "minItems": 2,
      "maxItems": 2
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "definitions": {
    "PortDefinition": {
      "type": "object",
      "required": ["name", "port_type", "data_type"],
      "properties": {
        "name": { "type": "string" },
        "port_type": { "enum": ["input", "output"] },
        "data_type": { "type": "string" },
        "label": { "type": ["string", "null"] },
        "required": { "type": "boolean", "default": true },
        "default_value": {}
      }
    }
  }
}
```

### Connection JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Connection",
  "type": "object",
  "required": ["source_node", "source_port", "target_node", "target_port"],
  "properties": {
    "source_node": {
      "type": "string",
      "description": "Source node ID"
    },
    "source_port": {
      "type": "string",
      "description": "Source output port name"
    },
    "target_node": {
      "type": "string",
      "description": "Target node ID"
    },
    "target_port": {
      "type": "string",
      "description": "Target input port name"
    }
  }
}
```

### NodeExecutionResult JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NodeExecutionResult",
  "type": "object",
  "required": ["node_id", "success"],
  "properties": {
    "node_id": { "type": "string" },
    "success": { "type": "boolean" },
    "data": { "type": "object", "default": {} },
    "error": { "type": ["string", "null"] },
    "error_code": { "type": ["string", "null"] },
    "execution_time_ms": { "type": "number", "default": 0 },
    "timestamp": { "type": "string", "format": "date-time" },
    "control_flow": { "type": ["string", "null"] },
    "next_nodes": { "type": "array", "items": { "type": "string" } },
    "bypassed": { "type": "boolean", "default": false },
    "attempt_number": { "type": "integer", "default": 1 },
    "was_retried": { "type": "boolean", "default": false }
  }
}
```

---

## Dependencies and Prerequisites

### Required Reading (Before Implementation)

1. `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\workflow.py` - Understand current WorkflowSchema
2. `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\execution_state.py` - Current ExecutionState
3. `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\runner\workflow_runner.py` - How entities are used
4. `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\core\base_node.py` - BaseNode interface

### Python Version Features to Use

- **Python 3.12+** (as per CLAUDE.md)
- `@dataclass` with `frozen=True` for immutability
- `tuple[T, ...]` syntax (not `Tuple[T, ...]`)
- `list[T]` syntax (not `List[T]`)
- `dict[K, V]` syntax (not `Dict[K, V]`)
- `str | None` union syntax (not `Optional[str]`)
- `Self` type from `typing` for fluent interfaces

### Libraries Decision

| Library | Decision | Rationale |
|---------|----------|-----------|
| `dataclasses` | USE | Standard library, no external dependency |
| `typing` | USE | Standard library |
| `datetime` | USE | Standard library |
| `enum` | USE | Standard library |
| `pydantic` | DO NOT USE | External dependency, domain must be pure |
| `attrs` | DO NOT USE | External dependency |
| `loguru` | REMOVE from domain | Infrastructure concern |
| `orjson` | REMOVE from domain | Infrastructure concern |

---

## Success Criteria and Validation

### Unit Test Requirements

Create `tests/domain/` with the following test files:

```python
# tests/domain/entities/test_node.py
"""Unit tests for Node domain entity."""
import pytest
from casare_rpa.domain.entities.node import Node, NodeStatus, PortDefinition


class TestNode:
    """Tests for Node entity."""

    def test_node_creation(self):
        """Test basic node creation."""
        node = Node(node_id="node_1", node_type="StartNode")
        assert node.node_id == "node_1"
        assert node.node_type == "StartNode"
        assert node.status == NodeStatus.IDLE

    def test_node_requires_id(self):
        """Test that node_id is required."""
        with pytest.raises(ValueError, match="node_id cannot be empty"):
            Node(node_id="", node_type="StartNode")

    def test_node_requires_type(self):
        """Test that node_type is required."""
        with pytest.raises(ValueError, match="node_type cannot be empty"):
            Node(node_id="node_1", node_type="")

    def test_node_status_transitions(self):
        """Test status transition methods."""
        node = Node(node_id="node_1", node_type="StartNode")

        node.mark_running()
        assert node.status == NodeStatus.RUNNING

        node.mark_success()
        assert node.status == NodeStatus.SUCCESS
        assert node.is_successful

        node.mark_error("Test error")
        assert node.status == NodeStatus.ERROR
        assert node.has_error
        assert node.error_message == "Test error"

    def test_node_port_values(self):
        """Test input/output port value management."""
        node = Node(
            node_id="node_1",
            node_type="TestNode",
            input_ports={"url": PortDefinition(name="url", port_type="input", data_type="STRING")},
            output_ports={"result": PortDefinition(name="result", port_type="output", data_type="STRING")},
        )

        node.set_input_value("url", "https://example.com")
        assert node.get_input_value("url") == "https://example.com"

        node.set_output_value("result", "success")
        assert node.get_output_value("result") == "success"

    def test_node_invalid_port(self):
        """Test that invalid port names raise errors."""
        node = Node(node_id="node_1", node_type="TestNode")

        with pytest.raises(ValueError, match="Input port 'invalid' not defined"):
            node.set_input_value("invalid", "value")

    def test_node_serialization(self):
        """Test to_dict and from_dict."""
        node = Node(
            node_id="node_1",
            node_type="StartNode",
            config={"param": "value"},
            position=(100.0, 200.0),
        )

        data = node.to_dict()
        restored = Node.from_dict(data)

        assert restored.node_id == node.node_id
        assert restored.node_type == node.node_type
        assert restored.config == node.config
        assert restored.position == node.position

    def test_node_equality(self):
        """Test that nodes are equal by node_id."""
        node1 = Node(node_id="same_id", node_type="TypeA")
        node2 = Node(node_id="same_id", node_type="TypeB")
        node3 = Node(node_id="different_id", node_type="TypeA")

        assert node1 == node2  # Same ID
        assert node1 != node3  # Different ID

    def test_node_hashable(self):
        """Test that nodes can be used in sets/dicts."""
        node = Node(node_id="node_1", node_type="StartNode")
        node_set = {node}
        assert node in node_set


class TestConnection:
    """Tests for Connection entity."""

    def test_connection_creation(self):
        """Test basic connection creation."""
        from casare_rpa.domain.entities.connection import Connection

        conn = Connection(
            source_node_id="node_1",
            source_port="exec_out",
            target_node_id="node_2",
            target_port="exec_in",
        )

        assert conn.source_node_id == "node_1"
        assert conn.target_node_id == "node_2"

    def test_connection_immutable(self):
        """Test that connections are immutable."""
        from casare_rpa.domain.entities.connection import Connection

        conn = Connection(
            source_node_id="node_1",
            source_port="exec_out",
            target_node_id="node_2",
            target_port="exec_in",
        )

        with pytest.raises(AttributeError):
            conn.source_node_id = "changed"

    def test_connection_self_loop_forbidden(self):
        """Test that self-loops are rejected."""
        from casare_rpa.domain.entities.connection import Connection

        with pytest.raises(ValueError, match="cannot connect a node to itself"):
            Connection(
                source_node_id="same_node",
                source_port="out",
                target_node_id="same_node",
                target_port="in",
            )


class TestWorkflow:
    """Tests for Workflow aggregate."""

    def test_workflow_creation(self):
        """Test basic workflow creation."""
        from casare_rpa.domain.entities.workflow_entity import Workflow, WorkflowMetadata

        workflow = Workflow(metadata=WorkflowMetadata(name="Test"))
        assert workflow.metadata.name == "Test"
        assert workflow.node_count == 0

    def test_workflow_add_node(self):
        """Test adding nodes."""
        from casare_rpa.domain.entities.workflow_entity import Workflow

        workflow = Workflow()
        node = Node(node_id="node_1", node_type="StartNode")

        workflow.add_node(node)
        assert workflow.node_count == 1
        assert workflow.has_node("node_1")

    def test_workflow_duplicate_node(self):
        """Test that duplicate nodes are rejected."""
        from casare_rpa.domain.entities.workflow_entity import Workflow

        workflow = Workflow()
        node = Node(node_id="node_1", node_type="StartNode")

        workflow.add_node(node)
        with pytest.raises(ValueError, match="already exists"):
            workflow.add_node(node)

    def test_workflow_add_connection(self):
        """Test adding connections."""
        from casare_rpa.domain.entities.workflow_entity import Workflow
        from casare_rpa.domain.entities.connection import Connection

        workflow = Workflow()
        workflow.add_node(Node(node_id="node_1", node_type="StartNode"))
        workflow.add_node(Node(node_id="node_2", node_type="EndNode"))

        conn = Connection(
            source_node_id="node_1",
            source_port="exec_out",
            target_node_id="node_2",
            target_port="exec_in",
        )

        workflow.add_connection(conn)
        assert workflow.connection_count == 1

    def test_workflow_connection_missing_node(self):
        """Test that connections to missing nodes are rejected."""
        from casare_rpa.domain.entities.workflow_entity import Workflow
        from casare_rpa.domain.entities.connection import Connection

        workflow = Workflow()
        workflow.add_node(Node(node_id="node_1", node_type="StartNode"))

        with pytest.raises(ValueError, match="not found"):
            workflow.add_connection(Connection(
                source_node_id="node_1",
                source_port="out",
                target_node_id="missing",
                target_port="in",
            ))

    def test_workflow_validation_requires_start(self):
        """Test that validation requires start node."""
        from casare_rpa.domain.entities.workflow_entity import Workflow

        workflow = Workflow()
        errors = workflow.validate()

        assert any("Start node" in err for err in errors)

    def test_workflow_valid_simple(self):
        """Test valid simple workflow."""
        from casare_rpa.domain.entities.workflow_entity import Workflow
        from casare_rpa.domain.entities.connection import Connection

        workflow = Workflow()
        workflow.add_node(Node(node_id="start", node_type="StartNode"))
        workflow.add_node(Node(node_id="end", node_type="EndNode"))
        workflow.add_connection(Connection(
            source_node_id="start",
            source_port="exec_out",
            target_node_id="end",
            target_port="exec_in",
        ))

        errors = workflow.validate()
        assert len(errors) == 0
        assert workflow.is_valid()

    def test_workflow_serialization(self):
        """Test workflow serialization round-trip."""
        from casare_rpa.domain.entities.workflow_entity import Workflow, WorkflowMetadata
        from casare_rpa.domain.entities.connection import Connection

        workflow = Workflow(metadata=WorkflowMetadata(name="Test Workflow"))
        workflow.add_node(Node(node_id="start", node_type="StartNode"))
        workflow.add_node(Node(node_id="end", node_type="EndNode"))
        workflow.add_connection(Connection(
            source_node_id="start",
            source_port="exec_out",
            target_node_id="end",
            target_port="exec_in",
        ))
        workflow.variables["test_var"] = "test_value"

        data = workflow.to_dict()
        restored = Workflow.from_dict(data)

        assert restored.metadata.name == "Test Workflow"
        assert restored.node_count == 2
        assert restored.connection_count == 1
        assert restored.variables.get("test_var") == "test_value"
```

### Integration Test Scenarios

1. **Domain Independence Test**: Import only `casare_rpa.domain` and verify no infrastructure errors
2. **Serialization Round-Trip**: Serialize workflow to dict, deserialize, verify equality
3. **Validation Suite**: Test all validation rules with various workflow structures
4. **Backward Compatibility**: Ensure existing JSON workflows can be loaded

### Code Review Checklist

- [ ] No `loguru` imports in domain layer
- [ ] No `orjson` imports in domain layer
- [ ] No file I/O operations in domain entities
- [ ] No async/await in pure domain entities
- [ ] All public methods have docstrings
- [ ] All type hints are present and correct
- [ ] Immutable entities use `@dataclass(frozen=True)`
- [ ] Validation methods return `tuple[bool, List[str]]`
- [ ] `to_dict()` and `from_dict()` are inverse operations

### Performance Benchmarks

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Node creation | < 1ms | `timeit` 10000 iterations |
| Workflow with 100 nodes | < 10ms creation | Load test |
| Workflow validation | < 50ms for 500 nodes | Stress test |
| Serialization round-trip | < 100ms for 1000 nodes | Integration test |

---

## Risk Assessment and Mitigation

### Risk 1: Breaking Existing Code

**Risk Level**: HIGH
**Description**: Changing domain entities may break WorkflowRunner and other consumers.

**Mitigation**:
1. Keep existing `WorkflowSchema` class (rename to avoid conflict)
2. Create NEW pure entities alongside existing code
3. Implement adapter pattern for conversion
4. Run full test suite after each change

### Risk 2: Serialization Incompatibility

**Risk Level**: MEDIUM
**Description**: New entity structure may not load old workflow JSON files.

**Mitigation**:
1. Design `from_dict()` to handle legacy field names
2. Add auto-migration for old formats
3. Test with sample workflows from `workflows/` directory
4. Keep `WorkflowSchema.load_from_file()` functional during transition

### Risk 3: Performance Regression

**Risk Level**: LOW
**Description**: New validation logic may slow down workflow operations.

**Mitigation**:
1. Cache validation results where possible
2. Make validation optional (not on every operation)
3. Profile before and after implementation
4. Use lazy evaluation for expensive checks

### Risk 4: Import Cycle

**Risk Level**: MEDIUM
**Description**: Domain entities may accidentally import infrastructure modules.

**Mitigation**:
1. Use `TYPE_CHECKING` for type hints that need infrastructure types
2. Run import checker script: `python -c "from casare_rpa.domain import *"`
3. Set up pre-commit hook to check import hierarchy

---

## Implementation Guide for rpa-engine-architect

### Step-by-Step Coding Sequence

#### Step 1: Set Up Test Structure (15 minutes)

```bash
# Create test directories
mkdir -p tests/domain/entities
mkdir -p tests/domain/services
mkdir -p tests/domain/ports

# Create __init__.py files
touch tests/domain/__init__.py
touch tests/domain/entities/__init__.py
touch tests/domain/services/__init__.py
touch tests/domain/ports/__init__.py
```

**Checkpoint**: Run `pytest tests/domain/ -v` - should show "no tests" but no import errors.

#### Step 2: Create Node Entity (45 minutes)

1. Create `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\node.py` using the code pattern above
2. Create `c:\Users\Rau\Desktop\CasareRPA\tests\domain\entities\test_node.py` with tests
3. Run tests: `pytest tests/domain/entities/test_node.py -v`

**Checkpoint**: All node tests pass.

#### Step 3: Create Connection Entity (30 minutes)

1. Create `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\connection.py`
2. Add connection tests to test file
3. Run tests: `pytest tests/domain/entities/ -v`

**Checkpoint**: All entity tests pass.

#### Step 4: Create Workflow Entity (60 minutes)

1. Create `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\workflow_entity.py`
2. Create `c:\Users\Rau\Desktop\CasareRPA\tests\domain\entities\test_workflow.py`
3. Test incrementally: add_node, add_connection, validate, serialize

**Checkpoint**: Workflow can be created, populated, validated, and serialized.

#### Step 5: Create NodeExecutionResult (30 minutes)

1. Create `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\execution_result.py`
2. Add tests for factory methods and serialization
3. Verify immutability

**Checkpoint**: Results are immutable and serialize correctly.

#### Step 6: Create Domain Ports (45 minutes)

1. Create `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ports\workflow_repository.py`
2. Create `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ports\execution_engine.py`
3. No tests needed yet (interfaces only)

**Checkpoint**: Ports import without errors.

#### Step 7: Update Domain Exports (30 minutes)

1. Update `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\entities\__init__.py`:

```python
"""Domain entities exports."""
from .node import Node, NodeStatus, PortDefinition
from .connection import Connection
from .workflow_entity import Workflow, WorkflowMetadata
from .execution_result import NodeExecutionResult

# Backward compatibility - keep old exports
from .workflow import WorkflowSchema, VariableDefinition
from .node_connection import NodeConnection
from .execution_state import ExecutionState
from .project import (
    Project, Scenario, ProjectVariable, VariablesFile,
    CredentialBinding, CredentialBindingsFile, ProjectSettings,
    ScenarioExecutionSettings, ProjectIndexEntry, ProjectsIndex,
    VariableScope, VariableType, generate_project_id,
    generate_scenario_id, PROJECT_SCHEMA_VERSION,
)

__all__ = [
    # New pure domain entities
    "Node",
    "NodeStatus",
    "PortDefinition",
    "Connection",
    "Workflow",
    "WorkflowMetadata",
    "NodeExecutionResult",
    # Backward compatibility
    "WorkflowSchema",
    "VariableDefinition",
    "NodeConnection",
    "ExecutionState",
    # Project entities
    "Project",
    "Scenario",
    # ... rest of project exports
]
```

2. Update `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\__init__.py`:

```python
"""
CasareRPA Domain Layer - Pure Business Logic

This layer contains:
- Entities: Core business objects (Workflow, Node, Connection)
- Services: Domain services (validation, dependency analysis)
- Ports: Interfaces for adapters (dependency inversion)

CRITICAL: This layer must have ZERO dependencies on infrastructure or presentation.
All domain logic should be framework-agnostic and testable in isolation.
"""

from .entities import (
    Node,
    NodeStatus,
    PortDefinition,
    Connection,
    Workflow,
    WorkflowMetadata,
    NodeExecutionResult,
    # Backward compatibility
    WorkflowSchema,
    VariableDefinition,
    NodeConnection,
    ExecutionState,
)

from .ports.workflow_repository import WorkflowRepository, WorkflowNotFoundError, PersistenceError
from .ports.execution_engine import ExecutionEngine

__all__ = [
    # Entities
    "Node",
    "NodeStatus",
    "PortDefinition",
    "Connection",
    "Workflow",
    "WorkflowMetadata",
    "NodeExecutionResult",
    "WorkflowSchema",
    "VariableDefinition",
    "NodeConnection",
    "ExecutionState",
    # Ports
    "WorkflowRepository",
    "WorkflowNotFoundError",
    "PersistenceError",
    "ExecutionEngine",
]
```

**Checkpoint**: `from casare_rpa.domain import *` works without errors.

#### Step 8: Run Full Test Suite (15 minutes)

```bash
# Run domain tests
pytest tests/domain/ -v

# Run full test suite to ensure no regressions
pytest tests/ -v --ignore=tests/domain/

# Check for import cycles
python -c "from casare_rpa.domain import Node, Workflow, Connection"
```

**Final Checkpoint**: All tests pass, domain layer is pure.

### Documentation Requirements

1. Update docstrings in all new files
2. Add type hints to all public methods
3. Document the migration path in comments
4. Create a brief CHANGELOG entry

---

## Summary

This implementation plan provides a detailed roadmap for extracting pure domain entities for CasareRPA's Week 2 Day 1 objectives. Key deliverables:

1. **New Pure Entities**: `Node`, `Connection`, `Workflow`, `NodeExecutionResult`
2. **Domain Ports**: `WorkflowRepository`, `ExecutionEngine`
3. **Backward Compatibility**: Existing code continues to work via `WorkflowSchema`
4. **Test Coverage**: Comprehensive unit tests for all new entities
5. **Clean Architecture**: Domain layer has zero infrastructure dependencies

The implementation should take 6-8 hours and establishes the foundation for the remaining Week 2 refactoring work.

---

**Document End**
