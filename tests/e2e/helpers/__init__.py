"""
CasareRPA - E2E Test Helpers.

Provides utilities for building and executing test workflows.

Classes:
- WorkflowBuilder: Fluent builder for creating test workflows
- WorkflowExecutionResult: Result container for workflow execution

Usage:
    from tests.e2e.helpers import WorkflowBuilder

    async def test_simple_workflow():
        result = await (
            WorkflowBuilder()
            .add_start()
            .add_set_variable("counter", 0)
            .add_increment_variable("counter")
            .add_end()
            .execute()
        )
        assert result["success"]
        assert result["variables"]["counter"] == 1
"""

from .workflow_builder import (
    WorkflowBuilder,
    WorkflowExecutionResult,
)

__all__ = [
    "WorkflowBuilder",
    "WorkflowExecutionResult",
]
