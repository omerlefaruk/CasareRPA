"""
Chain Orchestration Types - Task types, complexity levels, and chain entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(Enum):
    """Task types for agent chaining."""

    IMPLEMENT = "implement"
    FIX = "fix"
    RESEARCH = "research"
    REFACTOR = "refactor"
    EXTEND = "extend"
    CLONE = "clone"
    TEST = "test"
    DOCS = "docs"
    UI = "ui"
    INTEGRATION = "integration"
    SECURITY = "security"


class ComplexityLevel(Enum):
    """Task complexity levels for estimation."""

    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EPIC = 5


class IssueSeverity(Enum):
    """Issue severity levels for loop decisions."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    COSMETIC = 1


class IssueCategory(Enum):
    """Issue categories for routing."""

    SECURITY = "security"
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    CODING_STANDARDS = "coding_standards"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    TESTING = "testing"


class DependencyType(Enum):
    """Types of dependencies between chains."""

    BLOCKING = 1
    BLOCKED_BY = 2
    SHOULD_COMPLETE_BEFORE = 3
    CONFLICTS_WITH = 4
    CAN_RUN_PARALLEL = 5


class ExecutionStrategy(Enum):
    """Execution strategy for multiple chains."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINED = "pipelined"


class ChainStatus(Enum):
    """Status of a chain execution."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ClassificationResult:
    """Result of task classification.

    Attributes:
        task_type: The classified task type (IMPLEMENT, FIX, etc.)
        complexity: The estimated complexity level (TRIVIAL, SIMPLE, etc.)
        confidence: Classification confidence score (0.0 to 1.0)
        estimated_duration: Estimated completion time in minutes
        suggested_parallel: List of agents that can run in parallel
        reasoning: List of strings explaining the classification
        risk_level: Risk assessment ("low", "medium", "high", "critical")
    """

    task_type: TaskType
    complexity: ComplexityLevel
    confidence: float
    estimated_duration: int  # minutes
    suggested_parallel: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    risk_level: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type.value,
            "complexity": self.complexity.value,
            "confidence": self.confidence,
            "estimated_duration": self.estimated_duration,
            "suggested_parallel": self.suggested_parallel,
            "reasoning": self.reasoning,
            "risk_level": self.risk_level,
        }


@dataclass
class Issue:
    """Represents a code review issue."""

    issue_id: str
    category: IssueCategory
    severity: IssueSeverity
    description: str
    file_path: str
    line_number: int
    suggestion: str = ""
    auto_fixable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class LoopDecision:
    """Decision about whether to continue looping."""

    should_continue: bool
    action: str
    max_iterations: int
    current_iteration: int
    reason: str
    issues_by_severity: dict[IssueSeverity, list[Issue]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_continue": self.should_continue,
            "action": self.action,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "reason": self.reason,
            "issues_by_severity": {
                k.value: [i.to_dict() for i in v] for k, v in self.issues_by_severity.items()
            },
        }


@dataclass
class Dependency:
    """Dependency between chains."""

    target_chain_id: str
    dependency_type: DependencyType
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_chain_id": self.target_chain_id,
            "dependency_type": self.dependency_type.value,
            "reason": self.reason,
        }


@dataclass
class ProvidedFeature:
    """Feature provided by a chain."""

    name: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
        }


@dataclass
class ChainSpec:
    """Specification for a chain to be executed."""

    chain_id: str
    task_type: TaskType
    description: str
    depends_on: list[Dependency] = field(default_factory=list)
    provides: list[ProvidedFeature] = field(default_factory=list)
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "depends_on": [d.to_dict() for d in self.depends_on],
            "provides": [p.to_dict() for p in self.provides],
            "priority": self.priority,
        }


@dataclass
class Conflict:
    """Conflict between two chains."""

    conflict_type: str
    chain_a: str
    chain_b: str
    description: str
    affected_files: list[str] = field(default_factory=list)
    resolution_suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "chain_a": self.chain_a,
            "chain_b": self.chain_b,
            "description": self.description,
            "affected_files": self.affected_files,
            "resolution_suggestion": self.resolution_suggestion,
        }


@dataclass
class CostEntry:
    """Token usage and cost entry."""

    chain_id: str
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "agent": self.agent,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


@dataclass
class ChainCost:
    """Cost breakdown for a chain."""

    chain_id: str
    task_type: TaskType
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost: float
    agent_breakdown: dict[str, dict[str, int]]
    optimization_suggestions: list[str] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "task_type": self.task_type.value,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "agent_breakdown": self.agent_breakdown,
            "optimization_suggestions": self.optimization_suggestions,
        }


@dataclass
class TimePrediction:
    """Time prediction for chain execution."""

    estimated_total_minutes: int
    confidence: float
    percentile_estimates: dict[int, int]  # P50, P90, P99
    agent_breakdown: dict[str, int]
    factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimated_total_minutes": self.estimated_total_minutes,
            "confidence": self.confidence,
            "percentile_estimates": self.percentile_estimates,
            "agent_breakdown": self.agent_breakdown,
            "factors": self.factors,
            "recommendations": self.recommendations,
        }


@dataclass
class ChainExecution:
    """Record of a chain execution."""

    chain_id: str
    task_type: TaskType
    complexity: ComplexityLevel
    started: datetime
    completed: datetime
    duration_seconds: int
    agent_durations: dict[str, int]
    success: bool
    iterations: int
    cost: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "task_type": self.task_type.value,
            "complexity": self.complexity.value,
            "started": self.started.isoformat(),
            "completed": self.completed.isoformat(),
            "duration_seconds": self.duration_seconds,
            "agent_durations": self.agent_durations,
            "success": self.success,
            "iterations": self.iterations,
            "cost": self.cost,
        }


@dataclass
class ChainOptions:
    """Options for chain execution.

    Attributes:
        smart_select: Enable ML-based task classification
        dynamic_loops: Enable severity-based loop iteration adjustment
        cost_optimize: Enable cost tracking and optimization
        predictive_timing: Enable completion time prediction
        allow_dependencies: Enable cross-chain dependency management
        max_iterations: Maximum loop iterations before escalation
        budget: Cost budget in USD (None = unlimited)
        max_time: Maximum time in minutes (None = unlimited)
        parallel: List of agent pairs to run in parallel
        model_overrides: Override default model per agent
    """

    smart_select: bool = True
    dynamic_loops: bool = True
    cost_optimize: bool = True
    predictive_timing: bool = True
    allow_dependencies: bool = False
    max_iterations: int = 3
    budget: Optional[float] = None
    max_time: Optional[int] = None  # minutes
    parallel: list[str] = field(default_factory=list)
    model_overrides: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "smart_select": self.smart_select,
            "dynamic_loops": self.dynamic_loops,
            "cost_optimize": self.cost_optimize,
            "predictive_timing": self.predictive_timing,
            "allow_dependencies": self.allow_dependencies,
            "max_iterations": self.max_iterations,
            "budget": self.budget,
            "max_time": self.max_time,
            "parallel": self.parallel,
            "model_overrides": self.model_overrides,
        }
