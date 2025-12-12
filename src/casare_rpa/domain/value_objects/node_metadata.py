"""
Node metadata from @node decorator.

Contains retry configuration, lifecycle hooks, and node identity.
Follows Prefect/Airflow patterns for robust execution behavior.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Type


@dataclass(frozen=True)
class NodeMetadata:
    """
    Metadata attached to node classes by the @node decorator.

    Contains retry configuration, lifecycle hooks, and node identity.
    This is immutable (frozen=True) to ensure consistency after decoration.

    Attributes:
        name: Display name for the node
        category: Node category for grouping (e.g., "browser", "data")
        icon: Icon identifier for UI display
        description: Human-readable description of node behavior

        retries: Number of retry attempts on failure
        retry_delay: Initial delay between retries in seconds
        retry_backoff: Multiplier for exponential backoff
        retry_jitter: Random jitter factor (0.0-1.0) to prevent thundering herd
        retry_on: Tuple of exception types that trigger retry

        on_start: Callbacks invoked before node execution
        on_success: Callbacks invoked after successful execution
        on_failure: Callbacks invoked after failed execution
        on_complete: Callbacks invoked after execution (success or failure)

        timeout_seconds: Maximum execution time before timeout
        tags: Tags for filtering and grouping nodes
    """

    name: str
    category: str = "General"
    icon: str = ""
    description: str = ""

    # Retry configuration (Prefect pattern)
    retries: int = 0
    retry_delay: float = 1.0  # seconds
    retry_backoff: float = 2.0  # multiplier
    retry_jitter: float = 0.1  # random jitter factor
    retry_on: Tuple[Type[Exception], ...] = field(default_factory=tuple)

    # Lifecycle hooks (Airflow pattern)
    on_start: Tuple[Callable, ...] = field(default_factory=tuple)
    on_success: Tuple[Callable, ...] = field(default_factory=tuple)
    on_failure: Tuple[Callable, ...] = field(default_factory=tuple)
    on_complete: Tuple[Callable, ...] = field(default_factory=tuple)

    # Timeout
    timeout_seconds: Optional[float] = None

    # Tags for filtering/grouping
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt with exponential backoff.

        Uses exponential backoff with jitter to prevent thundering herd
        when multiple nodes fail simultaneously.

        Args:
            attempt: Current retry attempt number (1-indexed)

        Returns:
            Delay in seconds before the next retry attempt
        """
        import random

        base_delay = self.retry_delay * (self.retry_backoff ** (attempt - 1))
        jitter = base_delay * self.retry_jitter * random.random()
        return base_delay + jitter

    def should_retry_exception(self, exc: Exception) -> bool:
        """
        Check if an exception should trigger a retry.

        If retry_on is empty, retries on any exception.
        Otherwise, only retries if exception is an instance of one of the
        specified exception types.

        Args:
            exc: The exception that occurred

        Returns:
            True if the exception should trigger a retry, False otherwise
        """
        if not self.retry_on:
            return True  # Retry on any exception if no specific types
        return isinstance(exc, self.retry_on)

    def has_retries(self) -> bool:
        """Check if retry is configured."""
        return self.retries > 0

    def has_timeout(self) -> bool:
        """Check if timeout is configured."""
        return self.timeout_seconds is not None and self.timeout_seconds > 0

    def has_lifecycle_hooks(self) -> bool:
        """Check if any lifecycle hooks are configured."""
        return bool(
            self.on_start or self.on_success or self.on_failure or self.on_complete
        )
