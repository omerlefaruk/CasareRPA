"""
Domain entities for automatic task decomposition and parallel agent execution.

This module defines the core value objects and entities used by the
parallel agent framework to decompose tasks and coordinate execution.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from casare_rpa.domain.entities.chain import AgentType


class SubtaskStatus(Enum):
    """Status of a subtask during execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class SubtaskPriority(Enum):
    """Priority levels for subtask scheduling."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class ResourceType(Enum):
    """Types of resources that agents may need."""

    BROWSER = "browser"
    DESKTOP = "desktop"
    HTTP_CLIENT = "http_client"
    FILE_SYSTEM = "file_system"
    NONE = "none"


@dataclass(frozen=True)
class ResourceRequest:
    """Request for a resource during subtask execution."""

    resource_type: ResourceType
    count: int = 1
    partition_id: str | None = None
    exclusive: bool = False


@dataclass(frozen=True)
class Subtask:
    """A single decomposed unit of work."""

    id: str
    title: str
    description: str
    agent_type: AgentType
    dependencies: list[str] = field(default_factory=list)
    resource_needs: ResourceRequest | None = None
    priority: SubtaskPriority = SubtaskPriority.NORMAL
    estimated_tokens: int = 5000
    timeout_seconds: int = 300
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParallelGroup:
    """A group of subtasks that can execute in parallel."""

    subtask_ids: list[str]
    phase_index: int = 0
    estimated_duration_ms: int = 0
    can_parallel_execute: bool = True


@dataclass
class DecompositionResult:
    """Result of task decomposition."""

    original_task: str
    subtasks: list[Subtask]
    dependency_graph: dict[str, list[str]]
    parallel_groups: list[ParallelGroup]
    total_estimated_tokens: int = 0
    estimated_savings_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubtaskResult:
    """Result of a single subtask execution."""

    subtask_id: str
    success: bool
    agent_type: AgentType
    execution_time_ms: int = 0
    tokens_used: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    output: str = ""
    status: SubtaskStatus = SubtaskStatus.PENDING


@dataclass
class DecompositionExecutionResult:
    """Complete result of decomposed task execution."""

    original_task: str
    subtask_results: dict[str, SubtaskResult]
    total_time_ms: int
    total_tokens: int
    parallel_groups_executed: int
    sequential_phases: int
    status: str  # "completed", "partial", "failed", "dry_run"
    estimated_savings_ms: int = 0
    phases_executed: int = 0
