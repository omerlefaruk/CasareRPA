"""
Audit Logging for Robot Agent.

Provides structured, searchable audit logs for all robot events:
- Job lifecycle events
- Execution details
- Errors and warnings
- Connection state changes
- Security events
"""

from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import orjson
from loguru import logger


class AuditEventType(Enum):
    """Types of audit events."""

    # Robot lifecycle
    ROBOT_STARTED = "robot.started"
    ROBOT_STOPPED = "robot.stopped"
    ROBOT_REGISTERED = "robot.registered"

    # Connection events
    CONNECTION_ESTABLISHED = "connection.established"
    CONNECTION_LOST = "connection.lost"
    CONNECTION_RECONNECTING = "connection.reconnecting"
    CONNECTION_FAILED = "connection.failed"

    # Job lifecycle
    JOB_RECEIVED = "job.received"
    JOB_CLAIMED = "job.claimed"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"
    JOB_CACHED = "job.cached"
    JOB_SYNCED = "job.synced"

    # Execution events
    WORKFLOW_LOADED = "execution.workflow_loaded"
    NODE_STARTED = "execution.node_started"
    NODE_COMPLETED = "execution.node_completed"
    NODE_FAILED = "execution.node_failed"
    NODE_SKIPPED = "execution.node_skipped"
    NODE_RETRIED = "execution.node_retried"

    # Checkpoint events
    CHECKPOINT_SAVED = "checkpoint.saved"
    CHECKPOINT_RESTORED = "checkpoint.restored"
    CHECKPOINT_CLEARED = "checkpoint.cleared"

    # Error events
    ERROR_TRANSIENT = "error.transient"
    ERROR_PERMANENT = "error.permanent"
    ERROR_UNKNOWN = "error.unknown"

    # Security events
    CREDENTIAL_VALIDATED = "security.credential_validated"
    CREDENTIAL_INVALID = "security.credential_invalid"
    ACCESS_DENIED = "security.access_denied"

    # Circuit breaker
    CIRCUIT_OPENED = "circuit.opened"
    CIRCUIT_HALF_OPEN = "circuit.half_open"
    CIRCUIT_CLOSED = "circuit.closed"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEntry:
    """A single audit log entry."""

    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        robot_id: str | None = None,
        job_id: str | None = None,
        node_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.timestamp = datetime.now(UTC)
        self.event_type = event_type
        self.severity = severity
        self.message = message
        self.robot_id = robot_id
        self.job_id = job_id
        self.node_id = node_id
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "robot_id": self.robot_id,
            "job_id": self.job_id,
            "node_id": self.node_id,
            "details": self.details,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return orjson.dumps(self.to_dict()).decode()


class AuditLogger:
    """
    Structured audit logger for robot events.

    Writes audit entries to:
    - Rotating log files (JSON format)
    - Loguru (for console/standard logging)
    - Optional callback for external systems
    """

    def __init__(
        self,
        robot_id: str,
        log_dir: Path | None = None,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        external_handler: Callable[..., Any] | None = None,
    ):
        """
        Initialize audit logger.

        Args:
            robot_id: Robot identifier
            log_dir: Directory for audit log files
            max_file_size_mb: Max size per log file in MB
            backup_count: Number of backup files to keep
            external_handler: Optional callback for external logging
        """
        self.robot_id = robot_id
        self.log_dir = log_dir or (Path.home() / ".casare_rpa" / "audit")
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.external_handler = external_handler

        # Ensure directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current log file
        self._current_file: Path | None = None
        self._current_size = 0

        # In-memory buffer for recent entries
        self._buffer: list[AuditEntry] = []
        self._buffer_limit = 1000

        # Context for automatic field population
        self._current_job_id: str | None = None
        self._current_node_id: str | None = None

        self._init_log_file()
        logger.info(f"Audit logger initialized at {self.log_dir}")

    def _init_log_file(self):
        """Initialize or rotate log file."""
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        base_name = f"audit_{date_str}.jsonl"
        self._current_file = self.log_dir / base_name
        self._current_size = self._current_file.stat().st_size if self._current_file.exists() else 0

    def _rotate_if_needed(self):
        """Rotate log file if size limit reached."""
        if self._current_size >= self.max_file_size:
            # Rename current file with timestamp
            timestamp = datetime.now(UTC).strftime("%H%M%S")
            rotated = self._current_file.with_suffix(f".{timestamp}.jsonl")
            self._current_file.rename(rotated)

            # Cleanup old files
            self._cleanup_old_files()

            # Start new file
            self._init_log_file()

    def _cleanup_old_files(self):
        """Remove old audit log files beyond backup_count."""
        files = sorted(
            self.log_dir.glob("audit_*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for old_file in files[self.backup_count :]:
            try:
                old_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete old audit file: {e}")

    @contextmanager
    def job_context(self, job_id: str):
        """Context manager for automatic job_id population."""
        old_job_id = self._current_job_id
        self._current_job_id = job_id
        try:
            yield
        finally:
            self._current_job_id = old_job_id

    @contextmanager
    def node_context(self, node_id: str):
        """Context manager for automatic node_id population."""
        old_node_id = self._current_node_id
        self._current_node_id = node_id
        try:
            yield
        finally:
            self._current_node_id = old_node_id

    def log(
        self,
        event_type: AuditEventType,
        message: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        job_id: str | None = None,
        node_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Log an audit event.

        Args:
            event_type: Type of the event
            message: Human-readable message
            severity: Event severity
            job_id: Optional job ID (uses context if not provided)
            node_id: Optional node ID (uses context if not provided)
            details: Additional event details
        """
        entry = AuditEntry(
            event_type=event_type,
            severity=severity,
            message=message,
            robot_id=self.robot_id,
            job_id=job_id or self._current_job_id,
            node_id=node_id or self._current_node_id,
            details=details,
        )

        # Write to file
        self._write_entry(entry)

        # Buffer in memory
        self._buffer.append(entry)
        if len(self._buffer) > self._buffer_limit:
            self._buffer.pop(0)

        # Log to loguru at appropriate level
        log_msg = f"[AUDIT] {event_type.value}: {message}"
        if severity == AuditSeverity.DEBUG:
            logger.debug(log_msg)
        elif severity == AuditSeverity.INFO:
            logger.info(log_msg)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_msg)
        elif severity == AuditSeverity.ERROR:
            logger.error(log_msg)
        elif severity == AuditSeverity.CRITICAL:
            logger.critical(log_msg)

        # External handler
        if self.external_handler:
            try:
                self.external_handler(entry)
            except Exception as e:
                logger.error(f"External audit handler error: {e}")

    def _write_entry(self, entry: AuditEntry):
        """Write entry to log file."""
        self._rotate_if_needed()

        try:
            with open(self._current_file, "a", encoding="utf-8") as f:
                line = entry.to_json() + "\n"
                f.write(line)
                self._current_size += len(line.encode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to write audit entry: {e}")

    # Convenience methods for common events

    def robot_started(self, details: dict | None = None):
        """Log robot started event."""
        self.log(
            AuditEventType.ROBOT_STARTED,
            "Robot agent started",
            details=details,
        )

    def robot_stopped(self, reason: str | None = None):
        """Log robot stopped event."""
        self.log(
            AuditEventType.ROBOT_STOPPED,
            f"Robot agent stopped{': ' + reason if reason else ''}",
        )

    def connection_established(self):
        """Log successful connection."""
        self.log(
            AuditEventType.CONNECTION_ESTABLISHED,
            "Connected to backend",
        )

    def connection_lost(self, reason: str | None = None):
        """Log connection lost."""
        self.log(
            AuditEventType.CONNECTION_LOST,
            f"Connection lost{': ' + reason if reason else ''}",
            severity=AuditSeverity.WARNING,
        )

    def connection_reconnecting(self, attempt: int):
        """Log reconnection attempt."""
        self.log(
            AuditEventType.CONNECTION_RECONNECTING,
            f"Reconnection attempt {attempt}",
            details={"attempt": attempt},
        )

    def job_received(self, job_id: str, workflow_name: str):
        """Log job received."""
        self.log(
            AuditEventType.JOB_RECEIVED,
            f"Received job: {workflow_name}",
            job_id=job_id,
            details={"workflow_name": workflow_name},
        )

    def job_claimed(self, job_id: str):
        """Log job claimed."""
        self.log(
            AuditEventType.JOB_CLAIMED,
            "Job claimed for execution",
            job_id=job_id,
        )

    def job_started(self, job_id: str, total_nodes: int):
        """Log job execution started."""
        self.log(
            AuditEventType.JOB_STARTED,
            f"Job execution started ({total_nodes} nodes)",
            job_id=job_id,
            details={"total_nodes": total_nodes},
        )

    def job_completed(self, job_id: str, duration_ms: float):
        """Log job completed successfully."""
        self.log(
            AuditEventType.JOB_COMPLETED,
            f"Job completed successfully in {duration_ms:.0f}ms",
            job_id=job_id,
            details={"duration_ms": duration_ms},
        )

    def job_failed(self, job_id: str, error: str, duration_ms: float):
        """Log job failed."""
        self.log(
            AuditEventType.JOB_FAILED,
            f"Job failed: {error[:200]}",
            severity=AuditSeverity.ERROR,
            job_id=job_id,
            details={"error": error, "duration_ms": duration_ms},
        )

    def job_cancelled(self, job_id: str, reason: str | None = None):
        """Log job cancelled."""
        self.log(
            AuditEventType.JOB_CANCELLED,
            f"Job cancelled{': ' + reason if reason else ''}",
            severity=AuditSeverity.WARNING,
            job_id=job_id,
        )

    def node_started(self, node_id: str, node_type: str):
        """Log node execution started."""
        self.log(
            AuditEventType.NODE_STARTED,
            f"Node started: {node_type}",
            severity=AuditSeverity.DEBUG,
            node_id=node_id,
            details={"node_type": node_type},
        )

    def node_completed(self, node_id: str, node_type: str, duration_ms: float):
        """Log node completed."""
        self.log(
            AuditEventType.NODE_COMPLETED,
            f"Node completed: {node_type} ({duration_ms:.0f}ms)",
            severity=AuditSeverity.DEBUG,
            node_id=node_id,
            details={"node_type": node_type, "duration_ms": duration_ms},
        )

    def node_failed(self, node_id: str, node_type: str, error: str):
        """Log node failed."""
        self.log(
            AuditEventType.NODE_FAILED,
            f"Node failed: {node_type} - {error[:100]}",
            severity=AuditSeverity.ERROR,
            node_id=node_id,
            details={"node_type": node_type, "error": error},
        )

    def node_retried(self, node_id: str, node_type: str, attempt: int, error: str):
        """Log node retry."""
        self.log(
            AuditEventType.NODE_RETRIED,
            f"Node retry attempt {attempt}: {node_type}",
            severity=AuditSeverity.WARNING,
            node_id=node_id,
            details={"node_type": node_type, "attempt": attempt, "error": error},
        )

    def error_logged(self, category: str, error: str, details: dict | None = None):
        """Log an error with classification."""
        event_type = {
            "transient": AuditEventType.ERROR_TRANSIENT,
            "permanent": AuditEventType.ERROR_PERMANENT,
        }.get(category, AuditEventType.ERROR_UNKNOWN)

        self.log(
            event_type,
            f"Error ({category}): {error[:200]}",
            severity=AuditSeverity.ERROR,
            details={"category": category, "error": error, **(details or {})},
        )

    def checkpoint_saved(self, job_id: str, node_id: str, checkpoint_id: str):
        """Log checkpoint saved."""
        self.log(
            AuditEventType.CHECKPOINT_SAVED,
            f"Checkpoint saved: {checkpoint_id}",
            severity=AuditSeverity.DEBUG,
            job_id=job_id,
            node_id=node_id,
            details={"checkpoint_id": checkpoint_id},
        )

    def checkpoint_restored(self, job_id: str, checkpoint_id: str, node_id: str):
        """Log checkpoint restored."""
        self.log(
            AuditEventType.CHECKPOINT_RESTORED,
            f"Restored from checkpoint: {checkpoint_id}",
            job_id=job_id,
            details={"checkpoint_id": checkpoint_id, "restored_at_node": node_id},
        )

    def circuit_state_changed(self, circuit_name: str, new_state: str):
        """Log circuit breaker state change."""
        event_type = {
            "open": AuditEventType.CIRCUIT_OPENED,
            "half_open": AuditEventType.CIRCUIT_HALF_OPEN,
            "closed": AuditEventType.CIRCUIT_CLOSED,
        }.get(new_state, AuditEventType.CIRCUIT_OPENED)

        severity = AuditSeverity.WARNING if new_state == "open" else AuditSeverity.INFO

        self.log(
            event_type,
            f"Circuit breaker '{circuit_name}' -> {new_state}",
            severity=severity,
            details={"circuit_name": circuit_name, "state": new_state},
        )

    # Query methods

    def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent audit entries from buffer."""
        return [entry.to_dict() for entry in self._buffer[-limit:]]

    def query(
        self,
        event_types: list[AuditEventType] | None = None,
        severity: AuditSeverity | None = None,
        job_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query audit entries from buffer.

        Args:
            event_types: Filter by event types
            severity: Minimum severity level
            job_id: Filter by job ID
            since: Filter by timestamp
            limit: Maximum entries to return
        """
        results = []
        severity_order = [s.value for s in AuditSeverity]

        for entry in reversed(self._buffer):
            if len(results) >= limit:
                break

            # Apply filters
            if event_types and entry.event_type not in event_types:
                continue

            if severity:
                entry_idx = severity_order.index(entry.severity.value)
                filter_idx = severity_order.index(severity.value)
                if entry_idx < filter_idx:
                    continue

            if job_id and entry.job_id != job_id:
                continue

            if since and entry.timestamp < since:
                continue

            results.append(entry.to_dict())

        return results


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger(robot_id: str | None = None) -> AuditLogger:
    """Get or create global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        if robot_id is None:
            raise ValueError("robot_id required for first initialization")
        _audit_logger = AuditLogger(robot_id)
    return _audit_logger


def init_audit_logger(robot_id: str, **kwargs) -> AuditLogger:
    """Initialize global audit logger with custom settings."""
    global _audit_logger
    _audit_logger = AuditLogger(robot_id, **kwargs)
    return _audit_logger
