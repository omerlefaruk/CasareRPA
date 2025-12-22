"""
Queue Service for transaction queue management.

Provides application-layer operations for UiPath-style transaction queues:
- Queue CRUD operations
- Transaction item management
- Dispatcher/Performer pattern support
- Bulk operations
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Callable

from loguru import logger

from casare_rpa.domain.orchestrator.entities import (
    Queue,
    QueueItem,
    QueueItemStatus,
)


class QueueService:
    """
    Application service for transaction queue management.

    Provides UiPath-style queue operations:
    - Create/update/delete queues
    - Add/get/complete/fail transactions
    - Bulk operations for dispatcher pattern
    - Statistics and monitoring
    """

    def __init__(
        self,
        on_queue_changed: Optional[Callable[[str], None]] = None,
        on_item_changed: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize queue service.

        Args:
            on_queue_changed: Callback when queue is modified (queue_id)
            on_item_changed: Callback when item is modified (queue_id, item_id)
        """
        self._queues: Dict[str, Queue] = {}
        self._items: Dict[str, Dict[str, QueueItem]] = {}
        self._on_queue_changed = on_queue_changed
        self._on_item_changed = on_item_changed

        logger.info("QueueService initialized")

    def create_queue(
        self,
        name: str,
        description: str = "",
        schema: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
        auto_retry: bool = True,
        enforce_unique_reference: bool = False,
    ) -> Queue:
        """
        Create a new transaction queue.

        Args:
            name: Queue name (unique)
            description: Queue description
            schema: JSON schema for item validation
            max_retries: Maximum retry attempts for failed items
            retry_delay_seconds: Delay between retries
            auto_retry: Enable automatic retry on failure
            enforce_unique_reference: Require unique reference per item

        Returns:
            Created Queue instance
        """
        queue_id = str(uuid.uuid4())

        queue = Queue(
            id=queue_id,
            name=name,
            description=description,
            schema=schema or {},
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            auto_retry=auto_retry,
            enforce_unique_reference=enforce_unique_reference,
            created_at=datetime.now(timezone.utc),
        )

        self._queues[queue_id] = queue
        self._items[queue_id] = {}

        if self._on_queue_changed:
            self._on_queue_changed(queue_id)

        logger.info(f"Queue '{name}' created with ID {queue_id[:8]}")
        return queue

    def update_queue(
        self,
        queue_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        retry_delay_seconds: Optional[int] = None,
        auto_retry: Optional[bool] = None,
        enforce_unique_reference: Optional[bool] = None,
    ) -> Optional[Queue]:
        """
        Update an existing queue.

        Args:
            queue_id: Queue ID to update
            name: New name (optional)
            description: New description (optional)
            schema: New schema (optional)
            max_retries: New max retries (optional)
            retry_delay_seconds: New retry delay (optional)
            auto_retry: New auto retry setting (optional)
            enforce_unique_reference: New unique reference setting (optional)

        Returns:
            Updated Queue or None if not found
        """
        queue = self._queues.get(queue_id)
        if not queue:
            logger.warning(f"Queue {queue_id} not found for update")
            return None

        if name is not None:
            queue.name = name
        if description is not None:
            queue.description = description
        if schema is not None:
            queue.schema = schema
        if max_retries is not None:
            queue.max_retries = max_retries
        if retry_delay_seconds is not None:
            queue.retry_delay_seconds = retry_delay_seconds
        if auto_retry is not None:
            queue.auto_retry = auto_retry
        if enforce_unique_reference is not None:
            queue.enforce_unique_reference = enforce_unique_reference

        if self._on_queue_changed:
            self._on_queue_changed(queue_id)

        logger.info(f"Queue {queue_id[:8]} updated")
        return queue

    def delete_queue(self, queue_id: str) -> bool:
        """
        Delete a queue and all its items.

        Args:
            queue_id: Queue ID to delete

        Returns:
            True if deleted, False if not found
        """
        if queue_id not in self._queues:
            logger.warning(f"Queue {queue_id} not found for deletion")
            return False

        del self._queues[queue_id]
        self._items.pop(queue_id, None)

        if self._on_queue_changed:
            self._on_queue_changed(queue_id)

        logger.info(f"Queue {queue_id[:8]} deleted")
        return True

    def get_queue(self, queue_id: str) -> Optional[Queue]:
        """Get queue by ID."""
        return self._queues.get(queue_id)

    def get_queue_by_name(self, name: str) -> Optional[Queue]:
        """Get queue by name."""
        for queue in self._queues.values():
            if queue.name == name:
                return queue
        return None

    def list_queues(self) -> List[Queue]:
        """Get all queues."""
        return list(self._queues.values())

    def add_queue_item(
        self,
        queue_id: str,
        data: Dict[str, Any],
        reference: str = "",
        priority: int = 1,
        deadline: Optional[datetime] = None,
        postpone_until: Optional[datetime] = None,
    ) -> Optional[QueueItem]:
        """
        Add a new item to a queue.

        Args:
            queue_id: Queue to add item to
            data: Item data (must match queue schema)
            reference: Unique reference for the item
            priority: Item priority (higher = more urgent)
            deadline: Processing deadline
            postpone_until: Don't process until this time

        Returns:
            Created QueueItem or None if queue not found
        """
        queue = self._queues.get(queue_id)
        if not queue:
            logger.warning(f"Queue {queue_id} not found for add_item")
            return None

        if queue.enforce_unique_reference and reference:
            for item in self._items.get(queue_id, {}).values():
                if item.reference == reference and not item.is_terminal():
                    logger.warning(f"Duplicate reference '{reference}' in queue")
                    return None

        item_id = str(uuid.uuid4())
        item = QueueItem(
            id=item_id,
            queue_id=queue_id,
            reference=reference,
            data=data,
            status=QueueItemStatus.NEW,
            priority=priority,
            deadline=deadline,
            postpone_until=postpone_until,
            created_at=datetime.now(timezone.utc),
        )

        self._items.setdefault(queue_id, {})[item_id] = item
        self._update_queue_counts(queue_id)

        if self._on_item_changed:
            self._on_item_changed(queue_id, item_id)

        logger.debug(f"Item {item_id[:8]} added to queue {queue_id[:8]}")
        return item

    def add_queue_items(
        self,
        queue_id: str,
        items_data: List[Dict[str, Any]],
    ) -> List[QueueItem]:
        """
        Add multiple items to a queue (bulk operation).

        Args:
            queue_id: Queue to add items to
            items_data: List of item data dicts with keys:
                - data: Item data (required)
                - reference: Optional reference
                - priority: Optional priority (default 1)

        Returns:
            List of created QueueItems
        """
        created = []
        for item_data in items_data:
            item = self.add_queue_item(
                queue_id=queue_id,
                data=item_data.get("data", {}),
                reference=item_data.get("reference", ""),
                priority=item_data.get("priority", 1),
            )
            if item:
                created.append(item)

        logger.info(f"Added {len(created)} items to queue {queue_id[:8]}")
        return created

    def get_next_item(
        self,
        queue_id: str,
        robot_id: Optional[str] = None,
        robot_name: str = "",
    ) -> Optional[QueueItem]:
        """
        Get next available item from queue (for performer pattern).

        Gets highest priority NEW item that is not postponed.
        Marks it as IN_PROGRESS.

        Args:
            queue_id: Queue to get item from
            robot_id: Robot taking the item
            robot_name: Robot name

        Returns:
            QueueItem or None if no items available
        """
        queue_items = self._items.get(queue_id, {})
        now = datetime.now(timezone.utc)

        available = []
        for item in queue_items.values():
            if item.status != QueueItemStatus.NEW:
                continue
            if item.postpone_until and item.postpone_until > now:
                continue
            available.append(item)

        if not available:
            return None

        available.sort(key=lambda i: (-i.priority, i.created_at or now))
        item = available[0]

        item.status = QueueItemStatus.IN_PROGRESS
        item.robot_id = robot_id
        item.robot_name = robot_name
        item.started_at = now

        self._update_queue_counts(queue_id)

        if self._on_item_changed:
            self._on_item_changed(queue_id, item.id)

        logger.debug(f"Item {item.id[:8]} assigned to robot {robot_name}")
        return item

    def complete_item(
        self,
        queue_id: str,
        item_id: str,
        output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark an item as completed.

        Args:
            queue_id: Queue ID
            item_id: Item ID to complete
            output: Optional output data

        Returns:
            True if completed, False if not found or not in progress
        """
        item = self._items.get(queue_id, {}).get(item_id)
        if not item:
            logger.warning(f"Item {item_id} not found")
            return False

        if item.status != QueueItemStatus.IN_PROGRESS:
            logger.warning(f"Item {item_id} not in progress")
            return False

        now = datetime.now(timezone.utc)
        item.status = QueueItemStatus.COMPLETED
        item.completed_at = now
        item.output = output or {}

        if item.started_at:
            item.duration_ms = int((now - item.started_at).total_seconds() * 1000)

        self._update_queue_counts(queue_id)

        if self._on_item_changed:
            self._on_item_changed(queue_id, item_id)

        logger.debug(f"Item {item_id[:8]} completed")
        return True

    def fail_item(
        self,
        queue_id: str,
        item_id: str,
        error_message: str = "",
        error_type: str = "ApplicationException",
        exception_type: str = "",
    ) -> bool:
        """
        Mark an item as failed.

        If auto_retry is enabled and retries < max_retries,
        item is marked as RETRY and will be retried.

        Args:
            queue_id: Queue ID
            item_id: Item ID to fail
            error_message: Error description
            error_type: Error type (ApplicationException, BusinessException)
            exception_type: Specific exception type

        Returns:
            True if failed, False if not found or not in progress
        """
        queue = self._queues.get(queue_id)
        item = self._items.get(queue_id, {}).get(item_id)

        if not item or not queue:
            logger.warning(f"Item {item_id} or queue {queue_id} not found")
            return False

        if item.status != QueueItemStatus.IN_PROGRESS:
            logger.warning(f"Item {item_id} not in progress")
            return False

        now = datetime.now(timezone.utc)
        item.error_message = error_message
        item.error_type = error_type
        item.processing_exception_type = exception_type

        if item.started_at:
            item.duration_ms = int((now - item.started_at).total_seconds() * 1000)

        if queue.auto_retry and item.can_retry(queue.max_retries):
            item.status = QueueItemStatus.RETRY
            item.retries += 1
            logger.debug(f"Item {item_id[:8]} marked for retry ({item.retries})")
        else:
            item.status = QueueItemStatus.FAILED
            item.completed_at = now
            logger.debug(f"Item {item_id[:8]} failed")

        self._update_queue_counts(queue_id)

        if self._on_item_changed:
            self._on_item_changed(queue_id, item_id)

        return True

    def retry_item(self, queue_id: str, item_id: str) -> bool:
        """
        Manually retry a failed item.

        Args:
            queue_id: Queue ID
            item_id: Item ID to retry

        Returns:
            True if retried, False if not found or cannot retry
        """
        item = self._items.get(queue_id, {}).get(item_id)
        if not item:
            return False

        if item.status not in (QueueItemStatus.FAILED, QueueItemStatus.RETRY):
            return False

        item.status = QueueItemStatus.NEW
        item.started_at = None
        item.completed_at = None
        item.robot_id = None
        item.robot_name = ""
        item.error_message = ""
        item.error_type = ""
        item.duration_ms = 0

        self._update_queue_counts(queue_id)

        if self._on_item_changed:
            self._on_item_changed(queue_id, item_id)

        logger.debug(f"Item {item_id[:8]} reset for retry")
        return True

    def delete_item(self, queue_id: str, item_id: str) -> bool:
        """
        Delete an item from a queue.

        Args:
            queue_id: Queue ID
            item_id: Item ID to delete

        Returns:
            True if deleted, False if not found
        """
        queue_items = self._items.get(queue_id)
        if not queue_items or item_id not in queue_items:
            return False

        del queue_items[item_id]
        self._update_queue_counts(queue_id)

        if self._on_item_changed:
            self._on_item_changed(queue_id, item_id)

        logger.debug(f"Item {item_id[:8]} deleted")
        return True

    def get_item(self, queue_id: str, item_id: str) -> Optional[QueueItem]:
        """Get item by ID."""
        return self._items.get(queue_id, {}).get(item_id)

    def list_items(
        self,
        queue_id: str,
        status: Optional[QueueItemStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[QueueItem]:
        """
        List items in a queue with optional filtering.

        Args:
            queue_id: Queue ID
            status: Filter by status (optional)
            limit: Maximum items to return
            offset: Items to skip

        Returns:
            List of QueueItems
        """
        queue_items = list(self._items.get(queue_id, {}).values())

        if status:
            queue_items = [i for i in queue_items if i.status == status]

        queue_items.sort(key=lambda i: (-i.priority, i.created_at or datetime.min))

        return queue_items[offset : offset + limit]

    def get_queue_statistics(self, queue_id: str) -> Dict[str, Any]:
        """
        Get statistics for a queue.

        Args:
            queue_id: Queue ID

        Returns:
            Dictionary with queue statistics
        """
        queue = self._queues.get(queue_id)
        if not queue:
            return {}

        items = list(self._items.get(queue_id, {}).values())
        total_duration = sum(i.duration_ms for i in items if i.duration_ms > 0)
        completed_items = [i for i in items if i.status == QueueItemStatus.COMPLETED]
        avg_duration = total_duration / len(completed_items) if completed_items else 0

        return {
            "queue_id": queue_id,
            "queue_name": queue.name,
            "total_items": len(items),
            "new_count": queue.new_count,
            "in_progress_count": queue.in_progress_count,
            "completed_count": queue.completed_count,
            "failed_count": queue.failed_count,
            "success_rate": queue.success_rate,
            "avg_duration_ms": avg_duration,
            "total_duration_ms": total_duration,
        }

    def _update_queue_counts(self, queue_id: str) -> None:
        """Update queue item counts."""
        queue = self._queues.get(queue_id)
        if not queue:
            return

        items = list(self._items.get(queue_id, {}).values())

        queue.item_count = len(items)
        queue.new_count = sum(
            1 for i in items if i.status in (QueueItemStatus.NEW, QueueItemStatus.RETRY)
        )
        queue.in_progress_count = sum(1 for i in items if i.status == QueueItemStatus.IN_PROGRESS)
        queue.completed_count = sum(1 for i in items if i.status == QueueItemStatus.COMPLETED)
        queue.failed_count = sum(1 for i in items if i.status == QueueItemStatus.FAILED)

    def process_retry_items(self, queue_id: str) -> int:
        """
        Process items marked for retry.

        Moves RETRY items back to NEW status after retry delay.

        Args:
            queue_id: Queue ID

        Returns:
            Number of items reset for retry
        """
        queue = self._queues.get(queue_id)
        if not queue:
            return 0

        now = datetime.now(timezone.utc)
        count = 0

        for item in self._items.get(queue_id, {}).values():
            if item.status != QueueItemStatus.RETRY:
                continue

            if item.started_at:
                retry_after = item.started_at.replace(tzinfo=timezone.utc) + __import__(
                    "datetime"
                ).timedelta(seconds=queue.retry_delay_seconds)
                if now >= retry_after:
                    item.status = QueueItemStatus.NEW
                    item.started_at = None
                    item.robot_id = None
                    item.robot_name = ""
                    count += 1

        if count > 0:
            self._update_queue_counts(queue_id)
            logger.debug(f"Reset {count} items for retry in queue {queue_id[:8]}")

        return count
