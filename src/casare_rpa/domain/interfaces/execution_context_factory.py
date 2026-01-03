"""Execution context factory interface (domain-level).

Allows application layer code to create an execution context without importing
the infrastructure `ExecutionContext` implementation.
"""

import asyncio
from typing import Any, Protocol

from casare_rpa.domain.interfaces.execution_context import IExecutionContext
from casare_rpa.domain.value_objects.types import ExecutionMode


class IExecutionContextFactory(Protocol):
    """Factory for creating execution context instances."""

    def __call__(
        self,
        *,
        workflow_name: str = "Untitled",
        mode: ExecutionMode = ExecutionMode.NORMAL,
        initial_variables: dict[str, Any] | None = None,
        project_context: Any | None = None,
        pause_event: asyncio.Event | None = None,
    ) -> IExecutionContext:
        """Create a new execution context."""
