"""
CQRS Query Services for CasareRPA.

Read-optimized query services that bypass domain models for performance.
This is the Query side of Command Query Responsibility Segregation (CQRS).

Key Concepts:
    - Query services read directly from storage
    - Returns DTOs optimized for display, not domain entities
    - No domain validation or business rules on reads
    - Designed for fast, scalable read operations

Usage:
    from casare_rpa.application.queries import (
        WorkflowQueryService,
        WorkflowListItemDTO,
        WorkflowFilter,
        ExecutionQueryService,
        ExecutionLogDTO,
        ExecutionFilter,
    )

    # List workflows
    workflow_service = WorkflowQueryService(Path("./workflows"))
    workflows = await workflow_service.list_workflows(
        WorkflowFilter(name_contains="browser", limit=10)
    )

    # Get execution history
    execution_service = ExecutionQueryService(Path("./executions"))
    recent = await execution_service.get_recent_executions(limit=20)
"""

from casare_rpa.application.queries.workflow_queries import (
    WorkflowQueryService,
    WorkflowListItemDTO,
    WorkflowFilter,
)
from casare_rpa.application.queries.execution_queries import (
    ExecutionQueryService,
    ExecutionLogDTO,
    ExecutionFilter,
)

__all__ = [
    # Workflow queries
    "WorkflowQueryService",
    "WorkflowListItemDTO",
    "WorkflowFilter",
    # Execution queries
    "ExecutionQueryService",
    "ExecutionLogDTO",
    "ExecutionFilter",
]
