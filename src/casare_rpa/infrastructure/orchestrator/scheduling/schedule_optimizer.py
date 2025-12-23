"""
Schedule optimization for CasareRPA Orchestrator.

Contains rate limiting and execution optimization utilities.
Implements sliding window rate limiting for schedule executions.
"""

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class RateLimitConfig:
    """
    Rate limiting configuration (sliding window).

    Attributes:
        max_executions: Maximum executions in time window
        window_seconds: Time window in seconds
        queue_overflow: Whether to queue excess requests or reject
    """

    max_executions: int = 10
    window_seconds: int = 3600
    queue_overflow: bool = True


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter for schedule executions.

    Tracks executions within a time window and enforces limits.
    Uses a thread-safe implementation for concurrent access.
    """

    def __init__(self, max_executions: int, window_seconds: int):
        """
        Initialize rate limiter.

        Args:
            max_executions: Maximum executions allowed in window
            window_seconds: Window duration in seconds
        """
        self._max_executions = max_executions
        self._window = timedelta(seconds=window_seconds)
        self._executions: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    @property
    def max_executions(self) -> int:
        """Get maximum executions allowed."""
        return self._max_executions

    @property
    def window_seconds(self) -> int:
        """Get window duration in seconds."""
        return int(self._window.total_seconds())

    def can_execute(self, schedule_id: str) -> bool:
        """
        Check if execution is allowed for schedule.

        Args:
            schedule_id: Schedule ID to check

        Returns:
            True if execution is allowed
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            return len(self._executions[schedule_id]) < self._max_executions

    def record_execution(self, schedule_id: str) -> None:
        """
        Record an execution for rate limiting.

        Args:
            schedule_id: Schedule ID
        """
        with self._lock:
            self._executions[schedule_id].append(datetime.now(UTC))

    def get_wait_time(self, schedule_id: str) -> int:
        """
        Get seconds to wait before next execution allowed.

        Args:
            schedule_id: Schedule ID

        Returns:
            Seconds to wait (0 if can execute now)
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            executions = self._executions[schedule_id]

            if len(executions) < self._max_executions:
                return 0

            oldest = min(executions)
            wait_until = oldest + self._window
            wait_seconds = (wait_until - datetime.now(UTC)).total_seconds()
            return max(0, int(wait_seconds))

    def get_remaining_capacity(self, schedule_id: str) -> int:
        """
        Get remaining executions allowed in current window.

        Args:
            schedule_id: Schedule ID

        Returns:
            Number of executions remaining
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            return max(0, self._max_executions - len(self._executions[schedule_id]))

    def get_execution_count(self, schedule_id: str) -> int:
        """
        Get current execution count in window.

        Args:
            schedule_id: Schedule ID

        Returns:
            Number of executions in current window
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            return len(self._executions[schedule_id])

    def reset(self, schedule_id: str | None = None) -> None:
        """
        Reset rate limiter for a schedule or all schedules.

        Args:
            schedule_id: Specific schedule to reset (None for all)
        """
        with self._lock:
            if schedule_id:
                self._executions.pop(schedule_id, None)
            else:
                self._executions.clear()

    def _cleanup_old_entries(self, schedule_id: str) -> None:
        """Remove expired entries from tracking."""
        cutoff = datetime.now(UTC) - self._window
        self._executions[schedule_id] = [ts for ts in self._executions[schedule_id] if ts > cutoff]


class ExecutionOptimizer:
    """
    Optimizes schedule execution for performance.

    Features:
    - Coalesces rapid-fire executions
    - Manages execution priorities
    - Handles resource contention
    """

    def __init__(
        self,
        coalesce_window_ms: int = 1000,
        max_concurrent_executions: int = 10,
    ):
        """
        Initialize execution optimizer.

        Args:
            coalesce_window_ms: Window to coalesce rapid executions
            max_concurrent_executions: Maximum parallel executions
        """
        self._coalesce_window = timedelta(milliseconds=coalesce_window_ms)
        self._max_concurrent = max_concurrent_executions
        self._pending_executions: dict[str, datetime] = {}
        self._active_executions: dict[str, datetime] = {}
        self._lock = threading.Lock()

    @property
    def active_count(self) -> int:
        """Get count of active executions."""
        with self._lock:
            return len(self._active_executions)

    def can_start_execution(self) -> bool:
        """Check if a new execution can start."""
        with self._lock:
            return len(self._active_executions) < self._max_concurrent

    def should_coalesce(self, schedule_id: str) -> bool:
        """
        Check if execution should be coalesced with pending one.

        Args:
            schedule_id: Schedule ID to check

        Returns:
            True if execution should be skipped (coalesced)
        """
        with self._lock:
            if schedule_id not in self._pending_executions:
                return False

            pending_time = self._pending_executions[schedule_id]
            elapsed = datetime.now(UTC) - pending_time

            if elapsed < self._coalesce_window:
                logger.debug(
                    f"Coalescing execution for {schedule_id} "
                    f"(elapsed={elapsed.total_seconds():.2f}s)"
                )
                return True

            return False

    def mark_pending(self, schedule_id: str) -> None:
        """
        Mark a schedule execution as pending.

        Args:
            schedule_id: Schedule ID
        """
        with self._lock:
            self._pending_executions[schedule_id] = datetime.now(UTC)

    def mark_started(self, schedule_id: str) -> bool:
        """
        Mark a schedule execution as started.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if execution was allowed to start
        """
        with self._lock:
            if len(self._active_executions) >= self._max_concurrent:
                return False

            self._active_executions[schedule_id] = datetime.now(UTC)
            self._pending_executions.pop(schedule_id, None)
            return True

    def mark_completed(self, schedule_id: str) -> None:
        """
        Mark a schedule execution as completed.

        Args:
            schedule_id: Schedule ID
        """
        with self._lock:
            self._active_executions.pop(schedule_id, None)

    def get_execution_duration(self, schedule_id: str) -> timedelta | None:
        """
        Get duration of current execution.

        Args:
            schedule_id: Schedule ID

        Returns:
            Duration or None if not executing
        """
        with self._lock:
            start_time = self._active_executions.get(schedule_id)
            if start_time:
                return datetime.now(UTC) - start_time
            return None

    def get_active_executions(self) -> list[dict[str, datetime]]:
        """Get list of active executions with start times."""
        with self._lock:
            return [
                {"schedule_id": sid, "started_at": started}
                for sid, started in self._active_executions.items()
            ]


class PriorityQueue:
    """
    Priority queue for schedule executions.

    Higher priority schedules are executed first.
    """

    def __init__(self):
        """Initialize priority queue."""
        self._queues: dict[int, list[str]] = defaultdict(list)
        self._lock = threading.Lock()

    def enqueue(self, schedule_id: str, priority: int = 1) -> None:
        """
        Add schedule to queue with priority.

        Args:
            schedule_id: Schedule ID to enqueue
            priority: Priority level (0-3, higher = more important)
        """
        with self._lock:
            if schedule_id not in self._queues[priority]:
                self._queues[priority].append(schedule_id)

    def dequeue(self) -> str | None:
        """
        Get next schedule to execute by priority.

        Returns:
            Schedule ID or None if queue is empty
        """
        with self._lock:
            # Process highest priority first (3, 2, 1, 0)
            for priority in range(3, -1, -1):
                if self._queues[priority]:
                    return self._queues[priority].pop(0)
            return None

    def peek(self) -> str | None:
        """
        Peek at next schedule without removing.

        Returns:
            Schedule ID or None if queue is empty
        """
        with self._lock:
            for priority in range(3, -1, -1):
                if self._queues[priority]:
                    return self._queues[priority][0]
            return None

    def remove(self, schedule_id: str) -> bool:
        """
        Remove schedule from queue.

        Args:
            schedule_id: Schedule ID to remove

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            for priority in range(4):
                if schedule_id in self._queues[priority]:
                    self._queues[priority].remove(schedule_id)
                    return True
            return False

    def size(self) -> int:
        """Get total queue size across all priorities."""
        with self._lock:
            return sum(len(q) for q in self._queues.values())

    def size_by_priority(self) -> dict[int, int]:
        """Get queue sizes by priority level."""
        with self._lock:
            return {p: len(q) for p, q in self._queues.items() if q}

    def clear(self) -> None:
        """Clear all queues."""
        with self._lock:
            self._queues.clear()
