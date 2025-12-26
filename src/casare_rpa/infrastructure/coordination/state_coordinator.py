"""
State coordinator for real-time agent-to-agent communication.

Enables parallel agents to share intermediate results and coordinate execution.
"""

import asyncio
import time
from collections import defaultdict
from typing import Any, AsyncIterator

from loguru import logger

from casare_rpa.domain.entities.agent_coordination import (
    ResourceAllocation,
    SharedState,
)


class StateCoordinator:
    """
    Real-time state sharing between parallel agents.

    Enables agents to:
    - Publish intermediate results
    - Subscribe to other agents' updates
    - Wait for specific conditions before proceeding
    """

    def __init__(self) -> None:
        self._state: dict[str, dict[str, Any]] = {}
        self._subscriptions: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._conditions: dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    async def publish_state(
        self,
        agent_id: str,
        state: dict[str, Any],
        phase_index: int = 0,
        subtask_id: str | None = None,
    ) -> None:
        """
        Publish state update for an agent.

        Args:
            agent_id: ID of the agent publishing state
            state: State data to publish
            phase_index: Current execution phase
            subtask_id: Associated subtask ID
        """
        async with self._lock:
            self._state[agent_id] = {
                **state,
                "_timestamp": time.time(),
                "_phase": phase_index,
                "_subtask": subtask_id,
            }

        # Notify subscribers
        queue: asyncio.Queue
        for queue in self._subscriptions.get(agent_id, set()).copy():
            try:
                await queue.put(
                    SharedState(
                        agent_id=agent_id,
                        state=state,
                        timestamp=time.time(),
                        phase_index=phase_index,
                        subtask_id=subtask_id,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to notify subscriber for {agent_id}: {e}")

    async def subscribe_to(
        self,
        agent_id: str,
        timeout: float = 30.0,
    ) -> AsyncIterator[SharedState]:
        """
        Subscribe to state updates from an agent.

        Args:
            agent_id: Agent to subscribe to
            timeout: Timeout for waiting for updates

        Yields:
            SharedState updates
        """
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            self._subscriptions[agent_id].add(queue)

            # Send current state if available
            if agent_id in self._state:
                await queue.put(
                    SharedState(
                        agent_id=agent_id,
                        state=self._state[agent_id],
                        timestamp=self._state[agent_id].get("_timestamp", time.time()),
                    )
                )

        try:
            while True:
                try:
                    state = await asyncio.wait_for(queue.get(), timeout)
                    yield state
                except TimeoutError:
                    # Check if still subscribed
                    async with self._lock:
                        if queue not in self._subscriptions.get(agent_id, set()):
                            break
        finally:
            async with self._lock:
                self._subscriptions[agent_id].discard(queue)

    async def get_latest_state(self, agent_id: str) -> SharedState | None:
        """
        Get the latest state from an agent without subscribing.

        Args:
            agent_id: Agent to get state from

        Returns:
            SharedState if available, None otherwise
        """
        async with self._lock:
            if agent_id in self._state:
                state = self._state[agent_id].copy()
                timestamp = state.pop("_timestamp", time.time())
                phase = state.pop("_phase", 0)
                subtask = state.pop("_subtask", None)

                return SharedState(
                    agent_id=agent_id,
                    state=state,
                    timestamp=timestamp,
                    phase_index=phase,
                    subtask_id=subtask,
                )
            return None

    def set_condition(self, condition_id: str) -> asyncio.Event:
        """
        Create or get a condition event.

        Args:
            condition_id: Unique identifier for the condition

        Returns:
            Event that can be waited on
        """
        if condition_id not in self._conditions:
            self._conditions[condition_id] = asyncio.Event()
        return self._conditions[condition_id]

    async def wait_for_condition(
        self,
        condition_id: str,
        timeout: float = 30.0,
    ) -> bool:
        """
        Wait for a condition to be set.

        Args:
            condition_id: Condition to wait for
            timeout: Maximum time to wait

        Returns:
            True if condition was set, False if timeout
        """
        event = self.set_condition(condition_id)
        try:
            await asyncio.wait_for(event.wait(), timeout)
            return True
        except TimeoutError:
            return False
        finally:
            # Clear the event after waiting
            event.clear()

    def signal_condition(self, condition_id: str) -> None:
        """
        Signal that a condition has been met.

        Args:
            condition_id: Condition to signal
        """
        if condition_id in self._conditions:
            self._conditions[condition_id].set()

    async def get_agent_states(self, agent_ids: list[str]) -> dict[str, SharedState]:
        """
        Get latest states for multiple agents.

        Args:
            agent_ids: List of agent IDs to get states for

        Returns:
            Dict mapping agent_id to SharedState
        """
        result = {}
        for agent_id in agent_ids:
            state = await self.get_latest_state(agent_id)
            if state:
                result[agent_id] = state
        return result

    async def clear_agent_state(self, agent_id: str) -> None:
        """
        Clear state for an agent.

        Args:
            agent_id: Agent to clear state for
        """
        async with self._lock:
            self._state.pop(agent_id, None)
            # Cancel all subscriptions
            for queue in self._subscriptions.get(agent_id, set()).copy():
                await queue.put(None)  # Signal end

    async def shutdown(self) -> None:
        """Shutdown the coordinator and clean up resources."""
        async with self._lock:
            # Signal all waiting conditions
            for event in self._conditions.values():
                event.set()

            # Clear all queues
            for queues in self._subscriptions.values():
                for queue in queues:
                    try:
                        await queue.put(None)
                    except Exception:
                        pass

            self._state.clear()
            self._subscriptions.clear()
            self._conditions.clear()


class ResourceCoordinator:
    """
    Coordinates resource allocation for parallel agents.

    Manages resource locks and allocation tracking.
    """

    def __init__(self) -> None:
        self._allocations: dict[str, ResourceAllocation] = {}
        self._resource_locks: dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    def register_resource(self, resource_type: str, max_concurrent: int) -> None:
        """
        Register a resource type with concurrency limits.

        Args:
            resource_type: Type of resource (e.g., "browser", "desktop")
            max_concurrent: Maximum concurrent access
        """
        if resource_type not in self._resource_locks:
            self._resource_locks[resource_type] = asyncio.Semaphore(max_concurrent)

    async def acquire_resource(
        self,
        agent_id: str,
        resource_type: str,
        partition_id: str | None = None,
        timeout: float = 30.0,
    ) -> ResourceAllocation | None:
        """
        Acquire a resource for an agent.

        Args:
            agent_id: Agent requesting the resource
            resource_type: Type of resource to acquire
            partition_id: Optional partition ID for isolated access
            timeout: Maximum time to wait

        Returns:
            ResourceAllocation if acquired, None if timeout
        """
        if resource_type not in self._resource_locks:
            self.register_resource(resource_type, 1)

        semaphore = self._resource_locks[resource_type]

        try:
            await asyncio.wait_for(semaphore.acquire(), timeout)

            allocation = ResourceAllocation(
                agent_id=agent_id,
                resource_type=resource_type,
                allocation_id=f"{agent_id}_{resource_type}_{time.time()}",
                partition_id=partition_id,
                acquired_at=time.time(),
            )

            async with self._lock:
                self._allocations[allocation.allocation_id] = allocation

            return allocation

        except TimeoutError:
            return None

    async def release_resource(self, allocation_id: str) -> None:
        """
        Release a previously acquired resource.

        Args:
            allocation_id: Allocation ID to release
        """
        async with self._lock:
            if allocation_id in self._allocations:
                allocation = self._allocations[allocation_id]
                resource_type = allocation.resource_type

                del self._allocations[allocation_id]

                if resource_type in self._resource_locks:
                    self._resource_locks[resource_type].release()

    async def get_active_allocations(self, agent_id: str | None = None) -> list[ResourceAllocation]:
        """
        Get active resource allocations.

        Args:
            agent_id: Optional agent ID to filter by

        Returns:
            List of active allocations
        """
        async with self._lock:
            allocations = list(self._allocations.values())

        if agent_id:
            return [a for a in allocations if a.agent_id == agent_id]
        return allocations

    async def shutdown(self) -> None:
        """Release all resource locks."""
        async with self._lock:
            self._allocations.clear()
            # Semaphores will be garbage collected
            self._resource_locks.clear()
