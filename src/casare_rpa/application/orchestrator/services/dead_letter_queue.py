"""
Dead Letter Queue for CasareRPA Orchestrator.

Provides a queue for permanently failed jobs that have exceeded maximum retries
or encountered unrecoverable errors. The DLQ allows:
- Inspection of failed jobs and their errors
- Manual retry of failed jobs
- Purging of old entries
- Alerting on DLQ additions
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

from loguru import logger


class DeadLetterReason(Enum):
    """Reasons for job placement in DLQ."""

    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    TIMEOUT = "timeout"
    PERMANENT_ERROR = "permanent_error"
    INVALID_WORKFLOW = "invalid_workflow"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    MANUAL = "manual"


@dataclass
class DeadLetterItem:
    """
    Represents a job that has been moved to the dead letter queue.

    Attributes:
        id: Unique identifier for this DLQ entry
        job_id: Original job ID
        workflow_id: Workflow that failed
        workflow_name: Human-readable workflow name
        parameters: Job parameters at time of failure
        reason: Why the job was moved to DLQ
        final_error: Last error message
        retry_count: Number of retries attempted
        added_at: When added to DLQ
        original_created_at: When the original job was created
        robot_id: Robot that last attempted execution
        robot_name: Robot name
        retried_at: When manual retry was initiated
        retried_job_id: New job ID after retry
        metadata: Additional metadata
    """

    id: str
    job_id: str
    workflow_id: str
    workflow_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    reason: DeadLetterReason = DeadLetterReason.MAX_RETRIES_EXCEEDED
    final_error: str = ""
    retry_count: int = 0
    added_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    original_created_at: Optional[datetime] = None
    robot_id: Optional[str] = None
    robot_name: Optional[str] = None
    retried_at: Optional[datetime] = None
    retried_job_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "parameters": self.parameters,
            "reason": self.reason.value,
            "final_error": self.final_error,
            "retry_count": self.retry_count,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "original_created_at": (
                self.original_created_at.isoformat() if self.original_created_at else None
            ),
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "retried_at": self.retried_at.isoformat() if self.retried_at else None,
            "retried_job_id": self.retried_job_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeadLetterItem":
        """Create from dictionary."""
        reason_str = data.get("reason", "max_retries_exceeded")
        try:
            reason = DeadLetterReason(reason_str)
        except ValueError:
            reason = DeadLetterReason.MAX_RETRIES_EXCEEDED

        def parse_dt(val: Any) -> Optional[datetime]:
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return None

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            job_id=data.get("job_id", ""),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", ""),
            parameters=data.get("parameters", {}),
            reason=reason,
            final_error=data.get("final_error", ""),
            retry_count=data.get("retry_count", 0),
            added_at=parse_dt(data.get("added_at")) or datetime.now(timezone.utc),
            original_created_at=parse_dt(data.get("original_created_at")),
            robot_id=data.get("robot_id"),
            robot_name=data.get("robot_name"),
            retried_at=parse_dt(data.get("retried_at")),
            retried_job_id=data.get("retried_job_id"),
            metadata=data.get("metadata", {}),
        )

    @property
    def is_retried(self) -> bool:
        """Check if this item has been retried."""
        return self.retried_job_id is not None

    @property
    def age_hours(self) -> float:
        """Get age of this item in hours."""
        now = datetime.now(timezone.utc)
        added = self.added_at
        if added.tzinfo is None:
            added = added.replace(tzinfo=timezone.utc)
        delta = now - added
        return delta.total_seconds() / 3600


class DeadLetterQueue:
    """
    Queue for permanently failed jobs.

    Features:
    - Add failed jobs with reason and error details
    - Retry individual items or bulk retry
    - Purge items older than specified age
    - Configurable size limit with FIFO eviction
    - Callbacks for monitoring/alerting
    - Thread-safe operations
    """

    def __init__(
        self,
        max_size: int = 10000,
        retention_days: int = 30,
        on_item_added: Optional[Callable[["DeadLetterItem"], None]] = None,
        on_item_retried: Optional[Callable[["DeadLetterItem", str], None]] = None,
    ) -> None:
        """
        Initialize dead letter queue.

        Args:
            max_size: Maximum number of items (oldest evicted when exceeded)
            retention_days: Default retention period for items
            on_item_added: Callback when item added
            on_item_retried: Callback when item retried (item, new_job_id)
        """
        self._items: Dict[str, DeadLetterItem] = {}
        self._insertion_order: List[str] = []
        self._max_size = max_size
        self._retention_days = retention_days
        self._on_item_added = on_item_added
        self._on_item_retried = on_item_retried
        self._lock = threading.Lock()

        logger.info(
            f"DeadLetterQueue initialized (max_size={max_size}, " f"retention={retention_days}d)"
        )

    async def add(
        self,
        job_id: str,
        workflow_id: str,
        workflow_name: str,
        reason: DeadLetterReason,
        final_error: str,
        retry_count: int,
        parameters: Optional[Dict] = None,
        robot_id: Optional[str] = None,
        robot_name: Optional[str] = None,
        original_created_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ) -> DeadLetterItem:
        """
        Add a failed job to the dead letter queue.

        Args:
            job_id: Original job ID
            workflow_id: Workflow ID
            workflow_name: Workflow name
            reason: Why job is being added to DLQ
            final_error: Last error message
            retry_count: Number of retries attempted
            parameters: Job parameters
            robot_id: Robot ID that last executed
            robot_name: Robot name
            original_created_at: When original job was created
            metadata: Additional metadata

        Returns:
            Created DeadLetterItem
        """
        item = DeadLetterItem(
            id=str(uuid.uuid4()),
            job_id=job_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            parameters=parameters or {},
            reason=reason,
            final_error=final_error,
            retry_count=retry_count,
            robot_id=robot_id,
            robot_name=robot_name,
            original_created_at=original_created_at,
            metadata=metadata or {},
        )

        with self._lock:
            # Check size limit
            while len(self._items) >= self._max_size:
                # Remove oldest item
                if self._insertion_order:
                    oldest_id = self._insertion_order.pop(0)
                    self._items.pop(oldest_id, None)
                    logger.debug(f"DLQ: Evicted oldest item {oldest_id[:8]}")
                else:
                    break

            self._items[item.id] = item
            self._insertion_order.append(item.id)

        logger.warning(f"Job {job_id[:8]} added to DLQ: {reason.value} - {final_error[:100]}")

        # Notify callback
        if self._on_item_added:
            try:
                self._on_item_added(item)
            except Exception as e:
                logger.error(f"DLQ callback error: {e}")

        return item

    async def retry(
        self,
        item_id: str,
        job_submitter: Optional[Callable] = None,
    ) -> Optional[str]:
        """
        Retry a dead letter item by creating a new job.

        Args:
            item_id: ID of the DLQ item to retry
            job_submitter: Async callable that creates new job, returns job_id

        Returns:
            New job ID if successful, None if item not found or retry failed
        """
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                logger.warning(f"DLQ: Item {item_id} not found for retry")
                return None

            if item.is_retried:
                logger.warning(f"DLQ: Item {item_id} already retried as {item.retried_job_id}")
                return item.retried_job_id

        # Submit new job
        new_job_id = None
        if job_submitter:
            try:
                new_job_id = await job_submitter(
                    workflow_id=item.workflow_id,
                    workflow_name=item.workflow_name,
                    parameters=item.parameters,
                )
            except Exception as e:
                logger.error(f"DLQ: Failed to create retry job: {e}")
                return None
        else:
            # Generate ID for external handling
            new_job_id = str(uuid.uuid4())

        if new_job_id:
            with self._lock:
                item.retried_at = datetime.now(timezone.utc)
                item.retried_job_id = new_job_id

            logger.info(f"DLQ: Retried item {item_id[:8]} as job {new_job_id[:8]}")

            # Notify callback
            if self._on_item_retried:
                try:
                    self._on_item_retried(item, new_job_id)
                except Exception as e:
                    logger.error(f"DLQ retry callback error: {e}")

        return new_job_id

    async def bulk_retry(
        self,
        item_ids: Optional[List[str]] = None,
        workflow_id: Optional[str] = None,
        reason: Optional[DeadLetterReason] = None,
        job_submitter: Optional[Callable] = None,
    ) -> Dict[str, Optional[str]]:
        """
        Retry multiple items.

        Args:
            item_ids: Specific items to retry (if None, uses filters)
            workflow_id: Filter by workflow ID
            reason: Filter by reason
            job_submitter: Callable to create new jobs

        Returns:
            Dict mapping item_id -> new_job_id (or None if failed)
        """
        results = {}

        items_to_retry = []
        with self._lock:
            if item_ids:
                items_to_retry = [
                    self._items[id]
                    for id in item_ids
                    if id in self._items and not self._items[id].is_retried
                ]
            else:
                for item in self._items.values():
                    if item.is_retried:
                        continue
                    if workflow_id and item.workflow_id != workflow_id:
                        continue
                    if reason and item.reason != reason:
                        continue
                    items_to_retry.append(item)

        for item in items_to_retry:
            new_job_id = await self.retry(item.id, job_submitter)
            results[item.id] = new_job_id

        logger.info(
            f"DLQ: Bulk retry completed - {sum(1 for v in results.values() if v)}/{len(results)} successful"
        )

        return results

    async def remove(self, item_id: str) -> bool:
        """
        Remove an item from the DLQ.

        Args:
            item_id: ID of item to remove

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if item_id in self._items:
                del self._items[item_id]
                if item_id in self._insertion_order:
                    self._insertion_order.remove(item_id)
                logger.debug(f"DLQ: Removed item {item_id[:8]}")
                return True
        return False

    async def purge(
        self,
        older_than_days: Optional[int] = None,
        include_retried: bool = True,
    ) -> int:
        """
        Purge old items from the DLQ.

        Args:
            older_than_days: Remove items older than this (default: retention_days)
            include_retried: Also purge items that have been retried

        Returns:
            Number of items purged
        """
        if older_than_days is None:
            older_than_days = self._retention_days

        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        purged = 0

        with self._lock:
            items_to_remove = []
            for item_id, item in self._items.items():
                added = item.added_at
                if added.tzinfo is None:
                    added = added.replace(tzinfo=timezone.utc)

                if added < cutoff:
                    if include_retried or not item.is_retried:
                        items_to_remove.append(item_id)

            for item_id in items_to_remove:
                del self._items[item_id]
                if item_id in self._insertion_order:
                    self._insertion_order.remove(item_id)
                purged += 1

        if purged > 0:
            logger.info(f"DLQ: Purged {purged} items older than {older_than_days} days")

        return purged

    def get(self, item_id: str) -> Optional[DeadLetterItem]:
        """Get item by ID."""
        with self._lock:
            return self._items.get(item_id)

    def get_by_job_id(self, job_id: str) -> Optional[DeadLetterItem]:
        """Get item by original job ID."""
        with self._lock:
            for item in self._items.values():
                if item.job_id == job_id:
                    return item
        return None

    def list(
        self,
        workflow_id: Optional[str] = None,
        reason: Optional[DeadLetterReason] = None,
        include_retried: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DeadLetterItem]:
        """
        List DLQ items with optional filtering.

        Args:
            workflow_id: Filter by workflow ID
            reason: Filter by reason
            include_retried: Include items that have been retried
            limit: Maximum items to return
            offset: Offset for pagination

        Returns:
            List of DeadLetterItem matching filters
        """
        with self._lock:
            result = []
            for item in self._items.values():
                if workflow_id and item.workflow_id != workflow_id:
                    continue
                if reason and item.reason != reason:
                    continue
                if not include_retried and item.is_retried:
                    continue
                result.append(item)

            # Sort by added_at descending (newest first)
            result.sort(key=lambda x: x.added_at, reverse=True)

            return result[offset : offset + limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        with self._lock:
            total = len(self._items)
            retried = sum(1 for item in self._items.values() if item.is_retried)

            by_reason = {}
            by_workflow = {}
            age_distribution = {"<1h": 0, "1-24h": 0, "1-7d": 0, ">7d": 0}

            for item in self._items.values():
                # By reason
                reason_key = item.reason.value
                by_reason[reason_key] = by_reason.get(reason_key, 0) + 1

                # By workflow
                wf_key = item.workflow_name or item.workflow_id
                by_workflow[wf_key] = by_workflow.get(wf_key, 0) + 1

                # Age distribution
                age_hours = item.age_hours
                if age_hours < 1:
                    age_distribution["<1h"] += 1
                elif age_hours < 24:
                    age_distribution["1-24h"] += 1
                elif age_hours < 168:
                    age_distribution["1-7d"] += 1
                else:
                    age_distribution[">7d"] += 1

            return {
                "total": total,
                "retried": retried,
                "pending": total - retried,
                "max_size": self._max_size,
                "utilization": (total / self._max_size * 100) if self._max_size else 0,
                "by_reason": by_reason,
                "by_workflow": dict(
                    sorted(by_workflow.items(), key=lambda x: x[1], reverse=True)[:10]
                ),
                "age_distribution": age_distribution,
                "oldest_item_hours": max(
                    (item.age_hours for item in self._items.values()), default=0
                ),
            }

    @property
    def size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self._items)

    @property
    def pending_count(self) -> int:
        """Get count of items not yet retried."""
        with self._lock:
            return sum(1 for item in self._items.values() if not item.is_retried)


__all__ = [
    "DeadLetterQueue",
    "DeadLetterItem",
    "DeadLetterReason",
]
