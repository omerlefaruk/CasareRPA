"""
Robot Communication Protocol for CasareRPA Orchestrator.
Defines message types and serialization for orchestrator-robot communication.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Types of messages exchanged between orchestrator and robot."""

    # Connection
    REGISTER = "register"
    REGISTER_ACK = "register_ack"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    DISCONNECT = "disconnect"

    # Job management
    JOB_ASSIGN = "job_assign"
    JOB_ACCEPT = "job_accept"
    JOB_REJECT = "job_reject"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETE = "job_complete"
    JOB_FAILED = "job_failed"
    JOB_CANCEL = "job_cancel"
    JOB_CANCELLED = "job_cancelled"

    # Status
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"

    # Logs
    LOG_ENTRY = "log_entry"
    LOG_BATCH = "log_batch"

    # Control
    PAUSE = "pause"
    RESUME = "resume"
    SHUTDOWN = "shutdown"

    # Error
    ERROR = "error"


@dataclass
class Message:
    """Base message class for all protocol messages."""

    type: MessageType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None  # For request-response pairing

    def to_json(self) -> str:
        """Serialize message to JSON."""
        data = {
            "type": self.type.value,
            "id": self.id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }
        if self.correlation_id:
            data["correlation_id"] = self.correlation_id
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            id=data.get("id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(UTC).isoformat()),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
        )


# ==================== MESSAGE BUILDERS ====================


class MessageBuilder:
    """Helper class to build protocol messages."""

    @staticmethod
    def register(
        robot_id: str,
        robot_name: str,
        environment: str = "default",
        max_concurrent_jobs: int = 1,
        tags: list[str] | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> Message:
        """Build robot registration message."""
        return Message(
            type=MessageType.REGISTER,
            payload={
                "robot_id": robot_id,
                "robot_name": robot_name,
                "environment": environment,
                "max_concurrent_jobs": max_concurrent_jobs,
                "tags": tags or [],
                "capabilities": capabilities or {},
            },
        )

    @staticmethod
    def register_ack(
        robot_id: str,
        success: bool,
        message: str = "",
        config: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> Message:
        """Build registration acknowledgment."""
        return Message(
            type=MessageType.REGISTER_ACK,
            payload={
                "robot_id": robot_id,
                "success": success,
                "message": message,
                "config": config or {},
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def heartbeat(
        robot_id: str,
        status: str,
        current_jobs: int = 0,
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        disk_percent: float = 0.0,
        active_job_ids: list[str] | None = None,
    ) -> Message:
        """Build heartbeat message."""
        return Message(
            type=MessageType.HEARTBEAT,
            payload={
                "robot_id": robot_id,
                "status": status,
                "current_jobs": current_jobs,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "active_job_ids": active_job_ids or [],
            },
        )

    @staticmethod
    def heartbeat_ack(robot_id: str, correlation_id: str | None = None) -> Message:
        """Build heartbeat acknowledgment."""
        return Message(
            type=MessageType.HEARTBEAT_ACK,
            payload={"robot_id": robot_id},
            correlation_id=correlation_id,
        )

    @staticmethod
    def job_assign(
        job_id: str,
        workflow_id: str,
        workflow_name: str,
        workflow_json: str,
        priority: int = 1,
        timeout_seconds: int = 3600,
        parameters: dict[str, Any] | None = None,
    ) -> Message:
        """Build job assignment message."""
        return Message(
            type=MessageType.JOB_ASSIGN,
            payload={
                "job_id": job_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "workflow_json": workflow_json,
                "priority": priority,
                "timeout_seconds": timeout_seconds,
                "parameters": parameters or {},
            },
        )

    @staticmethod
    def job_accept(job_id: str, robot_id: str, correlation_id: str | None = None) -> Message:
        """Build job acceptance message."""
        return Message(
            type=MessageType.JOB_ACCEPT,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def job_reject(
        job_id: str, robot_id: str, reason: str, correlation_id: str | None = None
    ) -> Message:
        """Build job rejection message."""
        return Message(
            type=MessageType.JOB_REJECT,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
                "reason": reason,
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def job_progress(
        job_id: str,
        robot_id: str,
        progress: int,
        current_node: str = "",
        message: str = "",
    ) -> Message:
        """Build job progress update message."""
        return Message(
            type=MessageType.JOB_PROGRESS,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
                "progress": progress,
                "current_node": current_node,
                "message": message,
            },
        )

    @staticmethod
    def job_complete(
        job_id: str,
        robot_id: str,
        result: dict[str, Any] | None = None,
        duration_ms: int = 0,
    ) -> Message:
        """Build job completion message."""
        return Message(
            type=MessageType.JOB_COMPLETE,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
                "result": result or {},
                "duration_ms": duration_ms,
            },
        )

    @staticmethod
    def job_failed(
        job_id: str,
        robot_id: str,
        error_message: str,
        error_type: str = "ExecutionError",
        stack_trace: str = "",
        failed_node: str = "",
    ) -> Message:
        """Build job failure message."""
        return Message(
            type=MessageType.JOB_FAILED,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
                "error_message": error_message,
                "error_type": error_type,
                "stack_trace": stack_trace,
                "failed_node": failed_node,
            },
        )

    @staticmethod
    def job_cancel(job_id: str, reason: str = "Cancelled by orchestrator") -> Message:
        """Build job cancellation request."""
        return Message(
            type=MessageType.JOB_CANCEL,
            payload={
                "job_id": job_id,
                "reason": reason,
            },
        )

    @staticmethod
    def job_cancelled(job_id: str, robot_id: str, correlation_id: str | None = None) -> Message:
        """Build job cancelled confirmation."""
        return Message(
            type=MessageType.JOB_CANCELLED,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def status_request(robot_id: str) -> Message:
        """Build status request message."""
        return Message(type=MessageType.STATUS_REQUEST, payload={"robot_id": robot_id})

    @staticmethod
    def status_response(
        robot_id: str,
        status: str,
        current_jobs: int,
        active_job_ids: list[str],
        uptime_seconds: int,
        system_info: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> Message:
        """Build status response message."""
        return Message(
            type=MessageType.STATUS_RESPONSE,
            payload={
                "robot_id": robot_id,
                "status": status,
                "current_jobs": current_jobs,
                "active_job_ids": active_job_ids,
                "uptime_seconds": uptime_seconds,
                "system_info": system_info or {},
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def log_entry(
        job_id: str,
        robot_id: str,
        level: str,
        message: str,
        node_id: str = "",
        extra: dict[str, Any] | None = None,
    ) -> Message:
        """Build log entry message."""
        return Message(
            type=MessageType.LOG_ENTRY,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
                "level": level,
                "message": message,
                "node_id": node_id,
                "extra": extra or {},
            },
        )

    @staticmethod
    def log_batch(job_id: str, robot_id: str, entries: list[dict[str, Any]]) -> Message:
        """Build batch log message."""
        return Message(
            type=MessageType.LOG_BATCH,
            payload={
                "job_id": job_id,
                "robot_id": robot_id,
                "entries": entries,
            },
        )

    @staticmethod
    def error(
        error_code: str,
        error_message: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> Message:
        """Build error message."""
        return Message(
            type=MessageType.ERROR,
            payload={
                "error_code": error_code,
                "error_message": error_message,
                "details": details or {},
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def pause(robot_id: str) -> Message:
        """Build pause command."""
        return Message(type=MessageType.PAUSE, payload={"robot_id": robot_id})

    @staticmethod
    def resume(robot_id: str) -> Message:
        """Build resume command."""
        return Message(type=MessageType.RESUME, payload={"robot_id": robot_id})

    @staticmethod
    def shutdown(robot_id: str, graceful: bool = True) -> Message:
        """Build shutdown command."""
        return Message(
            type=MessageType.SHUTDOWN,
            payload={
                "robot_id": robot_id,
                "graceful": graceful,
            },
        )

    @staticmethod
    def disconnect(robot_id: str, reason: str = "") -> Message:
        """Build disconnect message."""
        return Message(
            type=MessageType.DISCONNECT,
            payload={
                "robot_id": robot_id,
                "reason": reason,
            },
        )
