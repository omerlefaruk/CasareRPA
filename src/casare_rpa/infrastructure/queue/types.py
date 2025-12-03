"""
CasareRPA Infrastructure Layer - Queue Type Definitions

Provides type-safe definitions for queue operations:
- TypedDicts for structured data (job payloads, results, stats)
- Protocols for callbacks and handlers
- Type aliases for common patterns

These types ensure full type coverage across pgqueuer_consumer and pgqueuer_producer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, TypedDict, Union


# =============================================================================
# Job Payload Types
# =============================================================================


class JobVariables(TypedDict, total=False):
    """
    Workflow variables passed to job execution.

    All keys are optional - workflows define their own variable schemas.
    """

    # Common variable patterns (all optional)
    input_file: str
    output_file: str
    url: str
    credentials: Dict[str, str]
    parameters: Dict[str, Any]


class JobPayload(TypedDict):
    """
    Complete job payload as stored in the queue.

    This represents the full data structure for a queued job.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int
    environment: str
    variables: Dict[str, Any]
    created_at: str  # ISO format datetime
    retry_count: int
    max_retries: int


class ClaimedJobPayload(JobPayload):
    """
    Job payload after being claimed by a robot.

    Extends JobPayload with claim-specific fields.
    """

    claimed_at: str  # ISO format datetime


# =============================================================================
# Queue Message Types
# =============================================================================


class QueueMessage(TypedDict):
    """
    Generic queue message structure.

    Used for internal queue operations and message passing.
    """

    message_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: str  # ISO format datetime
    metadata: Dict[str, Any]


class EnqueueRequest(TypedDict):
    """
    Request to enqueue a new job.

    Validated before submission to ensure all required fields present.
    """

    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int
    environment: str
    variables: Dict[str, Any]
    max_retries: int
    delay_seconds: int


class EnqueueResponse(TypedDict):
    """
    Response from successful job enqueue operation.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    priority: int
    environment: str
    created_at: str  # ISO format datetime
    visible_after: str  # ISO format datetime


# =============================================================================
# Job Result Types
# =============================================================================


class JobResultData(TypedDict, total=False):
    """
    Result data from successful job execution.

    Structure depends on workflow - all fields optional.
    """

    output: Any
    artifacts: List[str]
    metrics: Dict[str, Union[int, float]]
    logs: List[str]


class JobResult(TypedDict):
    """
    Complete job execution result.
    """

    success: bool
    data: JobResultData
    execution_time_ms: int
    node_results: List[Dict[str, Any]]


class JobFailureResult(TypedDict):
    """
    Result from failed job execution.
    """

    success: bool
    error: str
    error_code: str
    traceback: Optional[str]
    node_id: Optional[str]
    retry_count: int
    will_retry: bool


# =============================================================================
# Job Status Types
# =============================================================================


class JobStatusInfo(TypedDict):
    """
    Job status information returned by get_job_status().
    """

    id: str
    status: str
    robot_id: Optional[str]
    visible_after: Optional[str]  # ISO format datetime


class JobDetailedStatus(TypedDict):
    """
    Detailed job status with full metadata.
    """

    job_id: str
    status: str
    robot_id: Optional[str]
    priority: int
    environment: str
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    retry_count: int
    max_retries: int


# =============================================================================
# Queue Statistics Types
# =============================================================================


class QueueStats(TypedDict):
    """
    Queue statistics for monitoring and metrics.
    """

    pending_count: int
    running_count: int
    completed_count: int
    failed_count: int
    cancelled_count: int
    avg_queue_wait_seconds: float
    avg_execution_seconds: float


class QueueDepthByPriority(TypedDict):
    """
    Queue depth grouped by priority level.

    Keys are priority levels (0-100), values are job counts.
    """

    # Note: TypedDict doesn't support int keys, this is for documentation
    # Actual type is Dict[int, int]
    pass


# =============================================================================
# Consumer Statistics Types
# =============================================================================


class ConsumerConfigStats(TypedDict):
    """
    Consumer configuration subset for stats reporting.
    """

    batch_size: int
    visibility_timeout_seconds: int
    heartbeat_interval_seconds: int


class ConsumerStats(TypedDict):
    """
    Consumer statistics for monitoring.
    """

    robot_id: str
    environment: str
    state: str
    is_connected: bool
    active_jobs: int
    active_job_ids: List[str]
    reconnect_attempts: int
    config: ConsumerConfigStats


# =============================================================================
# Producer Statistics Types
# =============================================================================


class ProducerConfigStats(TypedDict):
    """
    Producer configuration subset for stats reporting.
    """

    default_environment: str
    default_priority: int
    default_max_retries: int


class ProducerStats(TypedDict):
    """
    Producer statistics for monitoring.
    """

    state: str
    is_connected: bool
    total_enqueued: int
    total_cancelled: int
    reconnect_attempts: int
    config: ProducerConfigStats


# =============================================================================
# Callback Protocols
# =============================================================================


class StateChangeCallback(Protocol):
    """
    Protocol for connection state change callbacks.

    Implementors receive state change notifications.
    """

    def __call__(self, new_state: Any) -> None:
        """
        Handle state change notification.

        Args:
            new_state: New connection state (ConnectionState or ProducerConnectionState)
        """
        ...


class JobClaimedCallback(Protocol):
    """
    Protocol for job claimed event callbacks.
    """

    def __call__(self, job: ClaimedJobPayload) -> None:
        """
        Handle job claimed event.

        Args:
            job: The claimed job payload
        """
        ...


class JobCompletedCallback(Protocol):
    """
    Protocol for job completed event callbacks.
    """

    def __call__(self, job_id: str, result: JobResult) -> None:
        """
        Handle job completion event.

        Args:
            job_id: ID of completed job
            result: Execution result
        """
        ...


class JobFailedCallback(Protocol):
    """
    Protocol for job failed event callbacks.
    """

    def __call__(self, job_id: str, error: str, will_retry: bool) -> None:
        """
        Handle job failure event.

        Args:
            job_id: ID of failed job
            error: Error message
            will_retry: Whether job will be retried
        """
        ...


class HeartbeatCallback(Protocol):
    """
    Protocol for heartbeat callbacks.
    """

    def __call__(self, job_ids: List[str]) -> None:
        """
        Handle heartbeat event.

        Args:
            job_ids: List of job IDs that received heartbeat
        """
        ...


# =============================================================================
# Error Types
# =============================================================================


class QueueError(TypedDict):
    """
    Standard error response from queue operations.
    """

    error: str
    error_code: str
    details: Optional[Dict[str, Any]]
    timestamp: str


# =============================================================================
# Type Aliases
# =============================================================================

# Common type aliases for readability
JobId = str
WorkflowId = str
RobotId = str
Environment = str
Priority = int

# Database record type (from asyncpg)
DatabaseRecord = Dict[str, Any]
DatabaseRecordList = List[DatabaseRecord]
