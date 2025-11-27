"""
Job Queue Manager for CasareRPA Orchestrator.
Implements priority queue, state machine, deduplication, and timeout management.
"""

import heapq
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set, Callable, Any, Tuple
from collections import defaultdict
import threading

from loguru import logger

from .models import Job, JobStatus, JobPriority, Robot


class JobStateError(Exception):
    """Raised when an invalid state transition is attempted."""

    pass


class JobStateMachine:
    """
    Job state machine with valid transitions.

    State Diagram:
        PENDING -> QUEUED -> RUNNING -> COMPLETED
                      |         |
                      |         +-> FAILED
                      |         +-> TIMEOUT
                      +-> CANCELLED

        Any state can transition to CANCELLED except terminal states.
    """

    # Valid state transitions: from_state -> [to_states]
    VALID_TRANSITIONS: Dict[JobStatus, List[JobStatus]] = {
        JobStatus.PENDING: [JobStatus.QUEUED, JobStatus.CANCELLED],
        JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELLED],
        JobStatus.RUNNING: [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.TIMEOUT,
            JobStatus.CANCELLED,
        ],
        JobStatus.COMPLETED: [],  # Terminal state
        JobStatus.FAILED: [],  # Terminal state
        JobStatus.TIMEOUT: [],  # Terminal state
        JobStatus.CANCELLED: [],  # Terminal state
    }

    # Terminal states (no further transitions allowed)
    TERMINAL_STATES = {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.TIMEOUT,
        JobStatus.CANCELLED,
    }

    # States that count as "active" (consuming resources)
    ACTIVE_STATES = {JobStatus.RUNNING}

    # States that are "pending" (waiting for resources)
    WAITING_STATES = {JobStatus.PENDING, JobStatus.QUEUED}

    @classmethod
    def can_transition(cls, from_state: JobStatus, to_state: JobStatus) -> bool:
        """Check if a state transition is valid."""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, [])

    @classmethod
    def transition(cls, job: Job, to_state: JobStatus) -> Job:
        """
        Transition job to a new state.
        Raises JobStateError if transition is invalid.
        """
        if not cls.can_transition(job.status, to_state):
            raise JobStateError(
                f"Invalid transition from {job.status.value} to {to_state.value} "
                f"for job {job.id}"
            )

        # Update timestamps based on transition
        now = datetime.utcnow()

        if to_state == JobStatus.RUNNING:
            job.started_at = now
        elif to_state in cls.TERMINAL_STATES:
            job.completed_at = now
            if job.started_at:
                started = job.started_at
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace("Z", ""))
                job.duration_ms = int((now - started).total_seconds() * 1000)

        job.status = to_state
        logger.debug(f"Job {job.id[:8]} transitioned to {to_state.value}")
        return job

    @classmethod
    def is_terminal(cls, status: JobStatus) -> bool:
        """Check if status is terminal."""
        return status in cls.TERMINAL_STATES

    @classmethod
    def is_active(cls, status: JobStatus) -> bool:
        """Check if status is active (running)."""
        return status in cls.ACTIVE_STATES


@dataclass(order=True)
class PriorityQueueItem:
    """
    Item in the priority queue.
    Ordering: higher priority first, then earlier created_at.
    """

    priority: int = field(compare=True)  # Negative for max-heap behavior
    created_at: datetime = field(compare=True)
    job_id: str = field(compare=False)
    job: Job = field(compare=False)

    @classmethod
    def from_job(cls, job: Job) -> "PriorityQueueItem":
        """Create queue item from job."""
        # Use negative priority for max-heap behavior (higher priority = lower number)
        priority_value = -(
            job.priority.value
            if isinstance(job.priority, JobPriority)
            else job.priority
        )
        created = job.created_at
        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", ""))
        elif created is None:
            created = datetime.utcnow()
        return cls(priority=priority_value, created_at=created, job_id=job.id, job=job)


class JobDeduplicator:
    """
    Handles job deduplication to prevent duplicate job submissions.
    Uses workflow_id + parameters hash to detect duplicates.
    """

    def __init__(self, window_seconds: int = 300):
        """
        Initialize deduplicator.

        Args:
            window_seconds: Time window for deduplication (default 5 minutes)
        """
        self._window = timedelta(seconds=window_seconds)
        self._recent_hashes: Dict[str, datetime] = {}
        self._lock = threading.Lock()

    def _compute_hash(
        self, workflow_id: str, robot_id: Optional[str], params: Optional[Dict] = None
    ) -> str:
        """Compute deduplication hash for a job."""
        hash_input = f"{workflow_id}:{robot_id or 'any'}"
        if params:
            # Sort params for consistent hashing
            param_str = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
            hash_input += f":{param_str}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def is_duplicate(
        self,
        workflow_id: str,
        robot_id: Optional[str] = None,
        params: Optional[Dict] = None,
    ) -> bool:
        """
        Check if a job would be a duplicate.

        Args:
            workflow_id: Workflow ID
            robot_id: Target robot ID (optional)
            params: Job parameters (optional)

        Returns:
            True if job would be duplicate
        """
        job_hash = self._compute_hash(workflow_id, robot_id, params)
        now = datetime.utcnow()

        with self._lock:
            # Clean old entries
            self._cleanup()

            if job_hash in self._recent_hashes:
                last_time = self._recent_hashes[job_hash]
                if now - last_time < self._window:
                    return True

        return False

    def record(
        self,
        workflow_id: str,
        robot_id: Optional[str] = None,
        params: Optional[Dict] = None,
    ) -> str:
        """
        Record a job submission for deduplication.

        Returns:
            The deduplication hash
        """
        job_hash = self._compute_hash(workflow_id, robot_id, params)

        with self._lock:
            self._recent_hashes[job_hash] = datetime.utcnow()

        return job_hash

    def _cleanup(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired = [h for h, t in self._recent_hashes.items() if now - t >= self._window]
        for h in expired:
            del self._recent_hashes[h]


class JobTimeoutManager:
    """
    Manages job timeouts.
    Tracks running jobs and marks them as timed out if exceeded.
    """

    def __init__(self, default_timeout_seconds: int = 3600):
        """
        Initialize timeout manager.

        Args:
            default_timeout_seconds: Default timeout (1 hour)
        """
        self._default_timeout = timedelta(seconds=default_timeout_seconds)
        self._job_timeouts: Dict[str, Tuple[datetime, timedelta]] = {}
        self._lock = threading.Lock()

    def start_tracking(self, job_id: str, timeout_seconds: Optional[int] = None):
        """Start tracking a job's timeout."""
        timeout = (
            timedelta(seconds=timeout_seconds)
            if timeout_seconds
            else self._default_timeout
        )
        with self._lock:
            self._job_timeouts[job_id] = (datetime.utcnow(), timeout)
        logger.debug(f"Tracking timeout for job {job_id[:8]}: {timeout}")

    def stop_tracking(self, job_id: str):
        """Stop tracking a job's timeout."""
        with self._lock:
            self._job_timeouts.pop(job_id, None)

    def get_timed_out_jobs(self) -> List[str]:
        """Get list of job IDs that have timed out."""
        now = datetime.utcnow()
        timed_out = []

        with self._lock:
            for job_id, (start_time, timeout) in self._job_timeouts.items():
                if now - start_time > timeout:
                    timed_out.append(job_id)

        return timed_out

    def get_remaining_time(self, job_id: str) -> Optional[timedelta]:
        """Get remaining time before timeout."""
        with self._lock:
            if job_id not in self._job_timeouts:
                return None
            start_time, timeout = self._job_timeouts[job_id]
            elapsed = datetime.utcnow() - start_time
            remaining = timeout - elapsed
            return remaining if remaining.total_seconds() > 0 else timedelta(0)


class JobQueue:
    """
    Priority-based job queue with state management.

    Features:
    - Priority queue (Critical > High > Normal > Low)
    - Job state machine
    - Deduplication
    - Timeout management
    - Robot assignment
    """

    def __init__(
        self,
        dedup_window_seconds: int = 300,
        default_timeout_seconds: int = 3600,
        on_state_change: Optional[Callable[[Job, JobStatus, JobStatus], None]] = None,
    ):
        """
        Initialize job queue.

        Args:
            dedup_window_seconds: Deduplication time window
            default_timeout_seconds: Default job timeout
            on_state_change: Callback for state changes (job, old_state, new_state)
        """
        self._queue: List[PriorityQueueItem] = []
        self._jobs: Dict[str, Job] = {}  # job_id -> Job
        self._running_jobs: Dict[str, str] = {}  # job_id -> robot_id
        self._robot_jobs: Dict[str, Set[str]] = defaultdict(
            set
        )  # robot_id -> {job_ids}

        self._deduplicator = JobDeduplicator(dedup_window_seconds)
        self._timeout_manager = JobTimeoutManager(default_timeout_seconds)

        self._on_state_change = on_state_change
        self._lock = threading.Lock()

        logger.info("JobQueue initialized")

    def enqueue(
        self, job: Job, check_duplicate: bool = True, params: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Add a job to the queue.

        Args:
            job: Job to enqueue
            check_duplicate: Whether to check for duplicates
            params: Optional parameters for deduplication

        Returns:
            Tuple of (success, message)
        """
        # Check for duplicates
        if check_duplicate:
            if self._deduplicator.is_duplicate(job.workflow_id, job.robot_id, params):
                return False, "Duplicate job detected within deduplication window"

        with self._lock:
            # Ensure job is in PENDING state
            if job.status != JobStatus.PENDING:
                return False, f"Job must be in PENDING state, got {job.status.value}"

            # Transition to QUEUED
            try:
                old_status = job.status
                job = JobStateMachine.transition(job, JobStatus.QUEUED)
                job.created_at = job.created_at or datetime.utcnow().isoformat()
            except JobStateError as e:
                return False, str(e)

            # Add to queue
            item = PriorityQueueItem.from_job(job)
            heapq.heappush(self._queue, item)
            self._jobs[job.id] = job

            # Record for deduplication
            self._deduplicator.record(job.workflow_id, job.robot_id, params)

        # Notify state change
        if self._on_state_change:
            self._on_state_change(job, old_status, job.status)

        logger.info(f"Job {job.id[:8]} enqueued with priority {job.priority}")
        return True, "Job enqueued successfully"

    def dequeue(self, robot: Robot) -> Optional[Job]:
        """
        Get next job for a robot.

        Args:
            robot: Robot requesting work

        Returns:
            Next job if available, None otherwise
        """
        if not robot.is_available:
            return None

        with self._lock:
            # Find suitable job
            suitable_items = []
            selected_item = None

            while self._queue:
                item = heapq.heappop(self._queue)
                job = self._jobs.get(item.job_id)

                if not job or job.status != JobStatus.QUEUED:
                    # Job was cancelled or already processed
                    continue

                # Check if job is targeted to specific robot
                if job.robot_id and job.robot_id != robot.id:
                    suitable_items.append(item)
                    continue

                # Check environment match
                # TODO: Add environment matching logic

                selected_item = item
                break

            # Put back unsuitable items
            for item in suitable_items:
                heapq.heappush(self._queue, item)

            if not selected_item:
                return None

            job = self._jobs[selected_item.job_id]
            old_status = job.status

            # Transition to RUNNING
            try:
                job = JobStateMachine.transition(job, JobStatus.RUNNING)
                job.robot_id = robot.id
                job.robot_name = robot.name
            except JobStateError:
                # Put job back
                heapq.heappush(self._queue, selected_item)
                return None

            # Track running job
            self._running_jobs[job.id] = robot.id
            self._robot_jobs[robot.id].add(job.id)
            self._timeout_manager.start_tracking(job.id)

        # Notify state change
        if self._on_state_change:
            self._on_state_change(job, old_status, job.status)

        logger.info(f"Job {job.id[:8]} assigned to robot {robot.name}")
        return job

    def complete(self, job_id: str, result: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Mark a job as completed.

        Args:
            job_id: Job ID
            result: Optional result data

        Returns:
            Tuple of (success, message)
        """
        return self._finish_job(job_id, JobStatus.COMPLETED, result=result)

    def fail(self, job_id: str, error_message: str) -> Tuple[bool, str]:
        """
        Mark a job as failed.

        Args:
            job_id: Job ID
            error_message: Error description

        Returns:
            Tuple of (success, message)
        """
        return self._finish_job(job_id, JobStatus.FAILED, error_message=error_message)

    def timeout(self, job_id: str) -> Tuple[bool, str]:
        """
        Mark a job as timed out.

        Args:
            job_id: Job ID

        Returns:
            Tuple of (success, message)
        """
        return self._finish_job(
            job_id, JobStatus.TIMEOUT, error_message="Job execution timed out"
        )

    def cancel(
        self, job_id: str, reason: str = "Cancelled by user"
    ) -> Tuple[bool, str]:
        """
        Cancel a job.

        Args:
            job_id: Job ID
            reason: Cancellation reason

        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False, "Job not found"

            if JobStateMachine.is_terminal(job.status):
                return False, f"Cannot cancel job in {job.status.value} state"

            old_status = job.status

            try:
                job = JobStateMachine.transition(job, JobStatus.CANCELLED)
                job.error_message = reason
            except JobStateError as e:
                return False, str(e)

            # Clean up tracking
            if job_id in self._running_jobs:
                robot_id = self._running_jobs.pop(job_id)
                self._robot_jobs[robot_id].discard(job_id)
                self._timeout_manager.stop_tracking(job_id)

        # Notify state change
        if self._on_state_change:
            self._on_state_change(job, old_status, job.status)

        logger.info(f"Job {job_id[:8]} cancelled: {reason}")
        return True, "Job cancelled"

    def _finish_job(
        self,
        job_id: str,
        new_status: JobStatus,
        result: Optional[Dict] = None,
        error_message: str = "",
    ) -> Tuple[bool, str]:
        """Internal method to finish a job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False, "Job not found"

            if job.status != JobStatus.RUNNING:
                return False, f"Job is not running (status: {job.status.value})"

            old_status = job.status

            try:
                job = JobStateMachine.transition(job, new_status)
                if result:
                    job.result = result
                if error_message:
                    job.error_message = error_message
                job.progress = (
                    100 if new_status == JobStatus.COMPLETED else job.progress
                )
            except JobStateError as e:
                return False, str(e)

            # Clean up tracking
            if job_id in self._running_jobs:
                robot_id = self._running_jobs.pop(job_id)
                self._robot_jobs[robot_id].discard(job_id)
                self._timeout_manager.stop_tracking(job_id)

        # Notify state change
        if self._on_state_change:
            self._on_state_change(job, old_status, job.status)

        logger.info(f"Job {job_id[:8]} finished with status {new_status.value}")
        return True, f"Job {new_status.value}"

    def update_progress(
        self, job_id: str, progress: int, current_node: str = ""
    ) -> bool:
        """
        Update job progress.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            current_node: Current node being executed

        Returns:
            True if updated successfully
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != JobStatus.RUNNING:
                return False

            job.progress = max(0, min(100, progress))
            if current_node:
                job.current_node = current_node

        return True

    def check_timeouts(self) -> List[str]:
        """
        Check for timed out jobs and mark them.

        Returns:
            List of job IDs that were timed out
        """
        timed_out = self._timeout_manager.get_timed_out_jobs()

        for job_id in timed_out:
            self.timeout(job_id)

        return timed_out

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def get_queued_jobs(self) -> List[Job]:
        """Get all queued jobs."""
        with self._lock:
            return [
                self._jobs[item.job_id]
                for item in self._queue
                if item.job_id in self._jobs
                and self._jobs[item.job_id].status == JobStatus.QUEUED
            ]

    def get_running_jobs(self) -> List[Job]:
        """Get all running jobs."""
        with self._lock:
            return [
                self._jobs[job_id]
                for job_id in self._running_jobs
                if job_id in self._jobs
            ]

    def get_robot_jobs(self, robot_id: str) -> List[Job]:
        """Get jobs assigned to a specific robot."""
        with self._lock:
            return [
                self._jobs[job_id]
                for job_id in self._robot_jobs.get(robot_id, set())
                if job_id in self._jobs
            ]

    def get_queue_depth(self) -> int:
        """Get number of jobs in queue."""
        with self._lock:
            return len(
                [
                    1
                    for item in self._queue
                    if item.job_id in self._jobs
                    and self._jobs[item.job_id].status == JobStatus.QUEUED
                ]
            )

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            queued = [
                self._jobs[item.job_id]
                for item in self._queue
                if item.job_id in self._jobs
                and self._jobs[item.job_id].status == JobStatus.QUEUED
            ]

            running = len(self._running_jobs)

            # Count by priority
            by_priority = defaultdict(int)
            for job in queued:
                priority = (
                    job.priority.value
                    if isinstance(job.priority, JobPriority)
                    else job.priority
                )
                by_priority[priority] += 1

            return {
                "queued": len(queued),
                "running": running,
                "by_priority": {
                    "critical": by_priority.get(3, 0),
                    "high": by_priority.get(2, 0),
                    "normal": by_priority.get(1, 0),
                    "low": by_priority.get(0, 0),
                },
                "total_tracked": len(self._jobs),
            }
