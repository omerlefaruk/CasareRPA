"""Domain-level recovery interfaces.

These abstractions allow the application layer to coordinate recovery without
depending on infrastructure implementations.
"""

from typing import Protocol

from casare_rpa.domain.errors import ErrorContext, RecoveryDecision
from casare_rpa.domain.interfaces.execution_context import IExecutionContext


class IRecoveryStrategyRegistry(Protocol):
    """Protocol for executing recovery decisions."""

    async def execute_recovery(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: IExecutionContext,
    ) -> bool:
        """Execute the recovery strategy and return whether it succeeded."""
