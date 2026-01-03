"""
Infrastructure Layer - JSON-based Unit of Work Implementation.

Implements the Unit of Work pattern using JSON file persistence.
Manages transactions across workflow and project repositories.

This is a lightweight implementation suitable for desktop RPA applications
where file-based persistence is sufficient.

Usage:
    from casare_rpa.infrastructure.persistence import JsonUnitOfWork
    from casare_rpa.domain.events import get_event_bus

    event_bus = get_event_bus()
    async with JsonUnitOfWork(storage_path, event_bus) as uow:
        workflow = await uow.workflows.get(workflow_id)
        workflow.add_node(node)
        await uow.commit()
"""

from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from loguru import logger

from casare_rpa.domain.events.base import DomainEvent
from casare_rpa.domain.events.bus import EventBus
from casare_rpa.domain.interfaces.unit_of_work import AbstractUnitOfWork


@runtime_checkable
class DomainEventCollector(Protocol):
    """Protocol for aggregates that collect domain events."""

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear pending domain events from the aggregate."""
        ...


class JsonUnitOfWork(AbstractUnitOfWork):
    """
    JSON file-based Unit of Work implementation.

    Manages transactions for file-based persistence, collecting domain
    events from aggregates and publishing them after successful commit.

    Attributes:
        storage_path: Base path for JSON file storage.
        event_bus: Optional typed event bus for publishing domain events.

    Note:
        This implementation does not provide true ACID transactions
        since JSON files don't support atomic multi-file writes.
        It does ensure domain events are only published after
        successful persistence.
    """

    def __init__(
        self,
        storage_path: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        """
        Initialize the JSON Unit of Work.

        Args:
            storage_path: Base directory for JSON file storage.
            event_bus: Optional typed event bus for domain event publishing.
        """
        self._storage_path = storage_path
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []
        self._tracked_aggregates: list[Any] = []
        self._committed = False

    @property
    def storage_path(self) -> Path:
        """Get the storage path for this unit of work."""
        return self._storage_path

    async def __aenter__(self) -> "JsonUnitOfWork":
        """
        Enter the unit of work context.

        Ensures storage directory exists and resets state.

        Returns:
            Self for use in async with statement.
        """
        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create storage directory {self._storage_path}: {e}")
            raise

        self._pending_events.clear()
        self._tracked_aggregates.clear()
        self._committed = False

        logger.debug(f"Unit of Work started with storage path: {self._storage_path}")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit the unit of work context.

        Rolls back if an exception occurred or if commit wasn't called.
        Always cleans up pending events and tracked aggregates.

        Args:
            exc_type: Exception type if an error occurred.
            exc_val: Exception value if an error occurred.
            exc_tb: Exception traceback if an error occurred.
        """
        if exc_type is not None:
            logger.warning(f"Unit of Work exiting with exception: {exc_type.__name__}: {exc_val}")
            await self.rollback()
        elif not self._committed:
            logger.debug("Unit of Work exiting without commit, rolling back")
            await self.rollback()

        self._pending_events.clear()
        self._tracked_aggregates.clear()

    async def commit(self) -> None:
        """
        Commit the transaction and publish domain events.

        Collects domain events from all tracked aggregates,
        then publishes them via the event bus if configured.

        The commit is marked successful even if event publishing
        fails - persistence is the critical operation.
        """
        # Collect events from tracked aggregates
        self._collect_events_from_aggregates()

        # Mark as committed (persistence is assumed successful at this point)
        self._committed = True
        logger.debug(f"Unit of Work committed with {len(self._pending_events)} pending events")

        # Publish domain events
        if self._event_bus and self._pending_events:
            await self._publish_events()

        self._pending_events.clear()

    async def rollback(self) -> None:
        """
        Rollback the transaction.

        Discards all pending events without publishing.
        Tracked aggregates are cleared but their in-memory
        state is not reverted (caller should discard references).
        """
        event_count = len(self._pending_events)
        self._pending_events.clear()
        self._tracked_aggregates.clear()

        if event_count > 0:
            logger.debug(f"Unit of Work rolled back, discarded {event_count} events")

    def track(self, aggregate: Any) -> None:
        """
        Track an aggregate for event collection.

        Aggregates that implement DomainEventCollector will have
        their events collected during commit.

        Args:
            aggregate: Domain aggregate to track.
        """
        if aggregate not in self._tracked_aggregates:
            self._tracked_aggregates.append(aggregate)

    def add_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to be published on commit.

        Use this for events not tied to a specific aggregate.

        Args:
            event: Domain event to publish after commit.
        """
        self._pending_events.append(event)

    def _collect_events_from_aggregates(self) -> None:
        """Collect pending events from all tracked aggregates."""
        for aggregate in self._tracked_aggregates:
            if isinstance(aggregate, DomainEventCollector):
                try:
                    events = aggregate.collect_events()
                    self._pending_events.extend(events)
                except Exception as e:
                    logger.warning(
                        f"Failed to collect events from aggregate {type(aggregate).__name__}: {e}"
                    )

    async def _publish_events(self) -> None:
        """Publish all pending domain events via the typed event bus."""
        if not self._event_bus:
            return

        published_count = 0
        for event in self._pending_events:
            try:
                self._event_bus.publish(event)
                published_count += 1
            except Exception as e:
                logger.error(f"Failed to publish domain event {type(event).__name__}: {e}")

        if published_count > 0:
            logger.debug(f"Published {published_count} domain events")


__all__ = ["JsonUnitOfWork", "DomainEventCollector"]
