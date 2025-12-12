"""
Domain Layer - Unit of Work Interface.

The Unit of Work pattern manages transactions across multiple repositories,
ensuring atomic operations and consistent domain event publishing.

Design Pattern: Unit of Work (Martin Fowler's PoEAA)
- Tracks changes to domain entities during a business transaction
- Commits all changes atomically
- Publishes domain events only after successful commit
- Rolls back on failure, ensuring consistency

Usage:
    from casare_rpa.domain.interfaces import AbstractUnitOfWork

    async def create_workflow_use_case(
        uow: AbstractUnitOfWork,
        workflow_data: dict
    ) -> Workflow:
        async with uow:
            workflow = Workflow.create(workflow_data)
            await uow.workflows.add(workflow)
            await uow.commit()  # Persists and publishes domain events
            return workflow
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


class AbstractUnitOfWork(ABC):
    """
    Unit of Work pattern - manages transactions across repositories.

    Responsibilities:
    - Begin/commit/rollback transactions
    - Track domain entities with changes
    - Collect and publish domain events after commit
    - Ensure atomic operations across multiple repositories

    Usage:
        async with uow:
            workflow = await uow.workflows.get(workflow_id)
            workflow.add_node(node)
            await uow.commit()  # Commits and publishes domain events

    Note:
        Concrete implementations should:
        1. Initialize repositories in __aenter__
        2. Collect domain events from aggregates before commit
        3. Persist changes then publish events in commit
        4. Clean up resources in __aexit__
    """

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork":
        """
        Enter the unit of work context.

        Initializes repositories and begins a transaction.

        Returns:
            Self for use in async with statement.
        """
        return self

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: "TracebackType | None",
    ) -> None:
        """
        Exit the unit of work context.

        On exception: rolls back transaction and cleans up.
        On success without explicit commit: rolls back (safety measure).

        Args:
            exc_type: Exception type if an error occurred, None otherwise.
            exc_val: Exception value if an error occurred, None otherwise.
            exc_tb: Exception traceback if an error occurred, None otherwise.
        """

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit the transaction and publish domain events.

        Order of operations:
        1. Collect domain events from tracked aggregates
        2. Persist all changes to storage
        3. Publish collected domain events
        4. Clear pending events

        Raises:
            Exception: If persistence fails (events are not published).
        """

    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback the transaction.

        Discards all pending changes and clears collected domain events.
        """


__all__ = ["AbstractUnitOfWork"]
