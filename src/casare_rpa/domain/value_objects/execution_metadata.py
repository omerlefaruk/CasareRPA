"""
CasareRPA - Execution Metadata Value Object

Immutable metadata attached to node execution results.
Tracks timing, attempts, and execution context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ExecutionMetadata:
    """Immutable execution metadata attached to node results.

    Tracks execution context including timing, retry attempts,
    and hierarchical relationships (subworkflows, parallel branches).

    Attributes:
        node_id: Unique identifier of the executed node.
        node_type: Type name of the node (e.g., "ClickElementNode").
        attempt: Current attempt number (1-based).
        max_attempts: Maximum retry attempts configured.
        start_time: When execution started.
        end_time: When execution completed (None if still running).
        duration_ms: Execution duration in milliseconds.
        parent_node_id: ID of parent node for subworkflow execution.
        branch_name: Name of parallel branch for concurrent execution.
    """

    node_id: str
    node_type: str
    attempt: int = 1
    max_attempts: int = 1
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    parent_node_id: Optional[str] = None
    branch_name: Optional[str] = None

    def with_end_time(self) -> "ExecutionMetadata":
        """Create new instance with end time set to now.

        Returns:
            New ExecutionMetadata with end_time and duration_ms populated.
        """
        end = datetime.now()
        duration = (end - self.start_time).total_seconds() * 1000
        return ExecutionMetadata(
            node_id=self.node_id,
            node_type=self.node_type,
            attempt=self.attempt,
            max_attempts=self.max_attempts,
            start_time=self.start_time,
            end_time=end,
            duration_ms=duration,
            parent_node_id=self.parent_node_id,
            branch_name=self.branch_name,
        )

    def with_next_attempt(self) -> "ExecutionMetadata":
        """Create new instance for retry attempt.

        Returns:
            New ExecutionMetadata with incremented attempt and fresh start_time.
        """
        return ExecutionMetadata(
            node_id=self.node_id,
            node_type=self.node_type,
            attempt=self.attempt + 1,
            max_attempts=self.max_attempts,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            parent_node_id=self.parent_node_id,
            branch_name=self.branch_name,
        )

    @property
    def is_completed(self) -> bool:
        """Check if execution has completed."""
        return self.end_time is not None

    @property
    def can_retry(self) -> bool:
        """Check if more retry attempts are available."""
        return self.attempt < self.max_attempts
