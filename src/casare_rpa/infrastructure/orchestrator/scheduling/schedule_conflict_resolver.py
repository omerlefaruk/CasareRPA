"""
Schedule conflict resolution for CasareRPA Orchestrator.

Contains dependency tracking and DAG-based scheduling utilities.
Implements conflict detection and resolution for schedule dependencies.
"""

import asyncio
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger


@dataclass
class DependencyConfig:
    """
    Dependency configuration for DAG-based scheduling.

    Attributes:
        depends_on: List of schedule IDs this schedule depends on
        wait_for_all: Whether to wait for all dependencies or just one
        timeout_seconds: Timeout waiting for dependencies
        trigger_on_success_only: Only trigger if dependencies succeeded
    """

    depends_on: list[str] = field(default_factory=list)
    wait_for_all: bool = True
    timeout_seconds: int = 3600
    trigger_on_success_only: bool = True


@dataclass
class CompletionRecord:
    """Record of a schedule completion."""

    schedule_id: str
    completed_at: datetime
    success: bool
    result: Any = None


class DependencyTracker:
    """
    Tracks workflow dependencies for DAG-based scheduling.

    Manages dependency completion status and triggers dependent schedules.
    Provides async waiting for dependencies with timeout support.
    """

    def __init__(self, ttl_seconds: int = 86400):
        """
        Initialize dependency tracker.

        Args:
            ttl_seconds: Time to keep completion records (default 24 hours)
        """
        self._ttl = timedelta(seconds=ttl_seconds)
        self._completions: dict[str, list[CompletionRecord]] = defaultdict(list)
        self._waiters: dict[str, list[asyncio.Event]] = defaultdict(list)
        self._lock = threading.Lock()

    def record_completion(
        self,
        schedule_id: str,
        success: bool,
        result: Any = None,
    ) -> None:
        """
        Record schedule completion for dependency tracking.

        Args:
            schedule_id: Completed schedule ID
            success: Whether execution succeeded
            result: Optional execution result
        """
        record = CompletionRecord(
            schedule_id=schedule_id,
            completed_at=datetime.now(UTC),
            success=success,
            result=result,
        )

        with self._lock:
            self._completions[schedule_id].append(record)
            self._cleanup_old(schedule_id)

            # Notify all waiters
            waiters = self._waiters.pop(schedule_id, [])
            for event in waiters:
                event.set()

        logger.debug(f"Recorded completion for schedule {schedule_id}: success={success}")

    def is_dependency_satisfied(
        self,
        dependency_id: str,
        since: datetime | None = None,
        require_success: bool = True,
    ) -> bool:
        """
        Check if a dependency has been satisfied.

        Args:
            dependency_id: Schedule ID of dependency
            since: Only check completions since this time
            require_success: Whether to require successful completion

        Returns:
            True if dependency is satisfied
        """
        with self._lock:
            self._cleanup_old(dependency_id)
            completions = self._completions.get(dependency_id, [])

            for record in reversed(completions):
                if since and record.completed_at < since:
                    continue
                if require_success and not record.success:
                    continue
                return True

            return False

    def are_dependencies_satisfied(
        self,
        dependency_ids: list[str],
        wait_for_all: bool = True,
        since: datetime | None = None,
        require_success: bool = True,
    ) -> tuple[bool, list[str]]:
        """
        Check if multiple dependencies are satisfied.

        Args:
            dependency_ids: List of dependency schedule IDs
            wait_for_all: Whether all must be satisfied or just one
            since: Only check completions since this time
            require_success: Whether to require successful completion

        Returns:
            Tuple of (all_satisfied, list_of_unsatisfied)
        """
        unsatisfied = []
        satisfied_count = 0

        for dep_id in dependency_ids:
            if self.is_dependency_satisfied(dep_id, since, require_success):
                satisfied_count += 1
            else:
                unsatisfied.append(dep_id)

        if wait_for_all:
            return len(unsatisfied) == 0, unsatisfied
        else:
            return satisfied_count > 0, unsatisfied

    async def wait_for_dependency(
        self,
        dependency_id: str,
        timeout_seconds: int = 3600,
    ) -> bool:
        """
        Wait for a dependency to complete.

        Args:
            dependency_id: Schedule ID to wait for
            timeout_seconds: Maximum wait time

        Returns:
            True if dependency completed, False if timeout
        """
        # Check if already satisfied
        if self.is_dependency_satisfied(dependency_id):
            return True

        event = asyncio.Event()
        with self._lock:
            self._waiters[dependency_id].append(event)

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
            return True
        except TimeoutError:
            with self._lock:
                waiters = self._waiters.get(dependency_id, [])
                if event in waiters:
                    waiters.remove(event)
            return False

    async def wait_for_dependencies(
        self,
        dependency_ids: list[str],
        wait_for_all: bool = True,
        timeout_seconds: int = 3600,
    ) -> tuple[bool, list[str]]:
        """
        Wait for multiple dependencies to complete.

        Args:
            dependency_ids: List of schedule IDs to wait for
            wait_for_all: Whether to wait for all or just one
            timeout_seconds: Maximum wait time

        Returns:
            Tuple of (success, list_of_timed_out_dependencies)
        """
        if not dependency_ids:
            return True, []

        # Create wait tasks
        tasks = {
            dep_id: asyncio.create_task(self.wait_for_dependency(dep_id, timeout_seconds))
            for dep_id in dependency_ids
        }

        timed_out = []
        start_time = datetime.now(UTC)
        remaining_timeout = timeout_seconds

        if wait_for_all:
            # Wait for all dependencies
            for dep_id, task in tasks.items():
                try:
                    success = await asyncio.wait_for(task, timeout=remaining_timeout)
                    if not success:
                        timed_out.append(dep_id)
                except TimeoutError:
                    timed_out.append(dep_id)
                    task.cancel()

                # Update remaining timeout
                elapsed = (datetime.now(UTC) - start_time).total_seconds()
                remaining_timeout = max(0, timeout_seconds - elapsed)

            return len(timed_out) == 0, timed_out
        else:
            # Wait for any dependency
            done, pending = await asyncio.wait(
                tasks.values(),
                timeout=timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # Check if any completed successfully
            for task in done:
                if task.result():
                    return True, []

            return False, list(dependency_ids)

    def get_latest_completion(self, schedule_id: str) -> CompletionRecord | None:
        """Get most recent completion record for a schedule."""
        with self._lock:
            completions = self._completions.get(schedule_id, [])
            return completions[-1] if completions else None

    def get_completion_history(
        self,
        schedule_id: str,
        limit: int = 10,
        since: datetime | None = None,
    ) -> list[CompletionRecord]:
        """
        Get completion history for a schedule.

        Args:
            schedule_id: Schedule ID
            limit: Maximum records to return
            since: Only get records since this time

        Returns:
            List of completion records (newest first)
        """
        with self._lock:
            self._cleanup_old(schedule_id)
            completions = self._completions.get(schedule_id, [])

            if since:
                completions = [c for c in completions if c.completed_at >= since]

            return list(reversed(completions[-limit:]))

    def clear_history(self, schedule_id: str | None = None) -> None:
        """
        Clear completion history.

        Args:
            schedule_id: Specific schedule to clear (None for all)
        """
        with self._lock:
            if schedule_id:
                self._completions.pop(schedule_id, None)
            else:
                self._completions.clear()

    def _cleanup_old(self, schedule_id: str) -> None:
        """Remove old completion records."""
        cutoff = datetime.now(UTC) - self._ttl
        self._completions[schedule_id] = [
            r for r in self._completions[schedule_id] if r.completed_at > cutoff
        ]


class ConflictResolver:
    """
    Resolves scheduling conflicts between schedules.

    Handles:
    - Resource contention
    - Overlapping execution windows
    - Priority-based resolution
    """

    def __init__(self):
        """Initialize conflict resolver."""
        self._resource_locks: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def acquire_resource(
        self,
        schedule_id: str,
        resource_id: str,
        exclusive: bool = True,
    ) -> bool:
        """
        Attempt to acquire a resource for a schedule.

        Args:
            schedule_id: Schedule requesting the resource
            resource_id: Resource to acquire
            exclusive: Whether exclusive access is required

        Returns:
            True if resource was acquired
        """
        with self._lock:
            current_holders = self._resource_locks[resource_id]

            if exclusive and current_holders:
                logger.debug(
                    f"Resource {resource_id} held by {current_holders}, "
                    f"cannot acquire for {schedule_id}"
                )
                return False

            current_holders.add(schedule_id)
            return True

    def release_resource(
        self,
        schedule_id: str,
        resource_id: str,
    ) -> None:
        """
        Release a resource held by a schedule.

        Args:
            schedule_id: Schedule releasing the resource
            resource_id: Resource to release
        """
        with self._lock:
            self._resource_locks[resource_id].discard(schedule_id)

    def release_all_resources(self, schedule_id: str) -> None:
        """
        Release all resources held by a schedule.

        Args:
            schedule_id: Schedule to release resources for
        """
        with self._lock:
            for holders in self._resource_locks.values():
                holders.discard(schedule_id)

    def get_resource_holders(self, resource_id: str) -> set[str]:
        """
        Get schedules currently holding a resource.

        Args:
            resource_id: Resource to check

        Returns:
            Set of schedule IDs holding the resource
        """
        with self._lock:
            return set(self._resource_locks.get(resource_id, set()))

    def has_conflict(
        self,
        schedule_id: str,
        required_resources: list[str],
        exclusive: bool = True,
    ) -> tuple[bool, list[str]]:
        """
        Check if schedule would conflict with running schedules.

        Args:
            schedule_id: Schedule to check
            required_resources: Resources the schedule needs
            exclusive: Whether exclusive access is required

        Returns:
            Tuple of (has_conflict, list_of_conflicting_resources)
        """
        conflicts = []

        with self._lock:
            for resource_id in required_resources:
                holders = self._resource_locks.get(resource_id, set())
                other_holders = holders - {schedule_id}

                if exclusive and other_holders:
                    conflicts.append(resource_id)

        return len(conflicts) > 0, conflicts


class DependencyGraphValidator:
    """
    Validates dependency graphs for cycles and other issues.

    Ensures DAG structure is valid before execution.
    """

    def __init__(self):
        """Initialize validator."""
        self._graph: dict[str, list[str]] = {}

    def set_graph(self, graph: dict[str, list[str]]) -> None:
        """
        Set the dependency graph.

        Args:
            graph: Dictionary mapping schedule ID to list of dependencies
        """
        self._graph = graph

    def build_graph_from_dependencies(self, dependencies: dict[str, DependencyConfig]) -> None:
        """
        Build graph from dependency configurations.

        Args:
            dependencies: Dictionary mapping schedule ID to DependencyConfig
        """
        self._graph = {}
        for schedule_id, config in dependencies.items():
            self._graph[schedule_id] = config.depends_on

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the dependency graph for cycles.

        Returns:
            Tuple of (is_valid, cycle_path if invalid)
        """
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycle_path: list[str] = []

        def has_cycle(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start_idx = path.index(neighbor)
                    cycle_path.extend(path[cycle_start_idx:])
                    cycle_path.append(neighbor)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self._graph:
            if node not in visited:
                if has_cycle(node, []):
                    return False, cycle_path

        return True, []

    def get_execution_order(self) -> list[str]:
        """
        Get topological execution order of schedules.

        Returns:
            List of schedule IDs in execution order

        Raises:
            ValueError: If graph has cycles
        """
        is_valid, cycle_path = self.validate()
        if not is_valid:
            raise ValueError(f"Dependency graph has cycle: {' -> '.join(cycle_path)}")

        # Topological sort using Kahn's algorithm
        in_degree: dict[str, int] = defaultdict(int)
        for schedule_id in self._graph:
            if schedule_id not in in_degree:
                in_degree[schedule_id] = 0
            for dep in self._graph.get(schedule_id, []):
                in_degree[dep] = in_degree.get(dep, 0)

        # Calculate in-degrees
        for schedule_id, deps in self._graph.items():
            for dep in deps:
                in_degree[schedule_id] += 1

        # Start with nodes that have no dependencies
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Find nodes that depend on this one
            for schedule_id, deps in self._graph.items():
                if node in deps:
                    in_degree[schedule_id] -= 1
                    if in_degree[schedule_id] == 0:
                        queue.append(schedule_id)

        return result

    def get_dependents(self, schedule_id: str) -> list[str]:
        """
        Get all schedules that depend on the given schedule.

        Args:
            schedule_id: Schedule to find dependents for

        Returns:
            List of dependent schedule IDs
        """
        dependents = []
        for sid, deps in self._graph.items():
            if schedule_id in deps:
                dependents.append(sid)
        return dependents

    def get_all_upstream(self, schedule_id: str) -> set[str]:
        """
        Get all upstream dependencies (transitive).

        Args:
            schedule_id: Schedule to find dependencies for

        Returns:
            Set of all upstream schedule IDs
        """
        upstream: set[str] = set()
        to_visit = list(self._graph.get(schedule_id, []))

        while to_visit:
            dep = to_visit.pop(0)
            if dep not in upstream:
                upstream.add(dep)
                to_visit.extend(self._graph.get(dep, []))

        return upstream

    def get_all_downstream(self, schedule_id: str) -> set[str]:
        """
        Get all downstream dependents (transitive).

        Args:
            schedule_id: Schedule to find dependents for

        Returns:
            Set of all downstream schedule IDs
        """
        downstream: set[str] = set()
        to_visit = self.get_dependents(schedule_id)

        while to_visit:
            dep = to_visit.pop(0)
            if dep not in downstream:
                downstream.add(dep)
                to_visit.extend(self.get_dependents(dep))

        return downstream
