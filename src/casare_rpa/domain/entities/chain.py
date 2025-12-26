"""
Domain entities for agent chaining system.

This module defines the core value objects and entities used
by the ChainExecutor to orchestrate multi-agent workflows.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(Enum):
    """Types of tasks that can be executed by chains."""

    IMPLEMENT = "implement"
    FIX = "fix"
    REFACTOR = "refactor"
    RESEARCH = "research"
    EXTEND = "extend"
    CLONE = "clone"
    TEST = "test"
    DOCS = "docs"
    SECURITY = "security"
    UI = "ui"
    INTEGRATION = "integration"


class ChainStatus(Enum):
    """Status of a chain execution."""

    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    HALTED = "halted"
    ESCALATED = "escalated"
    FAILED = "failed"


class AgentType(Enum):
    """Types of agents in the system."""

    EXPLORE = "explore"
    ARCHITECT = "architect"
    BUILDER = "builder"
    REFACTOR = "refactor"
    QUALITY = "quality"
    REVIEWER = "reviewer"
    DOCS = "docs"
    RESEARCHER = "researcher"
    UI = "ui"
    INTEGRATIONS = "integrations"
    SECURITY_AUDITOR = "security_auditor"


class IssueSeverity(Enum):
    """Severity levels for review issues."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    COSMETIC = 1


class IssueCategory(Enum):
    """Categories of review issues."""

    SECURITY = "security"
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    CODING_STANDARDS = "coding_standards"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    TESTING = "testing"


@dataclass(frozen=True)
class Issue:
    """A review issue found during chain execution."""

    line: int
    category: IssueCategory
    severity: IssueSeverity
    description: str
    file_path: str | None = None


@dataclass
class AgentResult:
    """Result from an agent execution."""

    success: bool
    agent_type: AgentType
    data: dict[str, Any] = field(default_factory=dict)
    status: str | None = None  # "APPROVED", "ISSUES", etc.
    issues: list[Issue] = field(default_factory=list)
    requires_approval: bool = False
    execution_time_ms: int = 0
    error_message: str | None = None


@dataclass
class ChainResult:
    """Result of a chain execution."""

    task_type: TaskType
    status: ChainStatus
    iterations: int = 0
    total_time_ms: int = 0
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    agent_results: dict[AgentType, AgentResult] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    message: str | None = None
    plan_path: str | None = None  # Path to architect plan
    escalated_reason: str | None = None


@dataclass
class ChainConfig:
    """Configuration for chain execution."""

    task_type: TaskType
    description: str
    max_iterations: int = 3
    timeout_seconds: int = 600
    priority: str = "normal"  # high, normal, low
    dry_run: bool = False
    skip_review: bool = False
    parallel_agents: bool = True
    parallel_types: list[AgentType] = field(default_factory=list)


# Task type to agent chain mapping
CHAIN_TEMPLATES: dict[TaskType, list[AgentType]] = {
    TaskType.IMPLEMENT: [
        AgentType.EXPLORE,
        AgentType.ARCHITECT,
        AgentType.BUILDER,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.FIX: [
        AgentType.EXPLORE,
        AgentType.BUILDER,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.REFACTOR: [
        AgentType.EXPLORE,
        AgentType.REFACTOR,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.RESEARCH: [
        AgentType.EXPLORE,
        AgentType.RESEARCHER,
    ],
    TaskType.EXTEND: [
        AgentType.EXPLORE,
        AgentType.ARCHITECT,
        AgentType.BUILDER,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.CLONE: [
        AgentType.EXPLORE,
        AgentType.BUILDER,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.TEST: [
        AgentType.EXPLORE,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.DOCS: [
        AgentType.EXPLORE,
        AgentType.DOCS,
        AgentType.REVIEWER,
    ],
    TaskType.SECURITY: [
        AgentType.EXPLORE,
        AgentType.SECURITY_AUDITOR,
        AgentType.REVIEWER,
    ],
    TaskType.UI: [
        AgentType.EXPLORE,
        AgentType.UI,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
    TaskType.INTEGRATION: [
        AgentType.EXPLORE,
        AgentType.INTEGRATIONS,
        AgentType.QUALITY,
        AgentType.REVIEWER,
    ],
}

# Parallel execution configuration
# Which agent types can run in parallel during which phase
PARALLEL_PHASES: dict[AgentType, list[AgentType]] = {
    AgentType.EXPLORE: [AgentType.DOCS, AgentType.SECURITY_AUDITOR],
    AgentType.QUALITY: [AgentType.DOCS],
}
