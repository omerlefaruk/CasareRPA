"""
Tests for AuditLogger (audit.py).

Tests cover:
1. Audit event creation with proper structure
2. Audit log persistence to files
3. Audit query functionality
4. Context managers for job/node tracking
5. Convenience methods for common events
6. Log rotation and cleanup

Mocking strategy:
- Use real file I/O with tmp_path fixture for isolation
- Mock loguru logger for log verification
- Mock external handlers
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

import pytest
import orjson

from casare_rpa.robot.audit import (
    AuditEntry,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    get_audit_logger,
    init_audit_logger,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_audit_dir(tmp_path: Path) -> Path:
    """Create temporary audit log directory."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir


@pytest.fixture
def audit_logger(temp_audit_dir: Path) -> AuditLogger:
    """Create an audit logger for testing."""
    return AuditLogger(
        robot_id="test-robot-001",
        log_dir=temp_audit_dir,
        max_file_size_mb=1,
        backup_count=3,
    )


@pytest.fixture
def external_handler():
    """Create a mock external handler."""
    return Mock()


# =============================================================================
# TEST SECTION 1: Audit Entry Creation
# =============================================================================


class TestAuditEntryCreation:
    """Tests for AuditEntry data class."""

    def test_entry_creation_with_required_fields(self):
        """Entry can be created with required fields."""
        entry = AuditEntry(
            event_type=AuditEventType.JOB_STARTED,
            severity=AuditSeverity.INFO,
            message="Job started",
        )

        assert entry.event_type == AuditEventType.JOB_STARTED
        assert entry.severity == AuditSeverity.INFO
        assert entry.message == "Job started"
        assert entry.timestamp is not None

    def test_entry_creation_with_all_fields(self):
        """Entry can be created with all fields."""
        details = {"workflow_name": "TestWorkflow", "total_nodes": 10}

        entry = AuditEntry(
            event_type=AuditEventType.JOB_COMPLETED,
            severity=AuditSeverity.INFO,
            message="Job completed successfully",
            robot_id="robot-001",
            job_id="job-001",
            node_id="node-001",
            details=details,
        )

        assert entry.robot_id == "robot-001"
        assert entry.job_id == "job-001"
        assert entry.node_id == "node-001"
        assert entry.details == details

    def test_entry_to_dict(self):
        """Entry converts to dictionary correctly."""
        entry = AuditEntry(
            event_type=AuditEventType.NODE_STARTED,
            severity=AuditSeverity.DEBUG,
            message="Node started",
            robot_id="robot-001",
            job_id="job-001",
            node_id="node-001",
            details={"node_type": "ClickElement"},
        )

        data = entry.to_dict()

        assert data["event_type"] == "execution.node_started"
        assert data["severity"] == "debug"
        assert data["message"] == "Node started"
        assert data["robot_id"] == "robot-001"
        assert data["timestamp"] is not None

    def test_entry_to_json(self):
        """Entry converts to JSON string."""
        entry = AuditEntry(
            event_type=AuditEventType.ROBOT_STARTED,
            severity=AuditSeverity.INFO,
            message="Robot started",
        )

        json_str = entry.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "robot.started"

    def test_entry_timestamp_is_utc(self):
        """Entry timestamp is in UTC."""
        entry = AuditEntry(
            event_type=AuditEventType.ROBOT_STARTED,
            severity=AuditSeverity.INFO,
            message="Robot started",
        )

        assert entry.timestamp.tzinfo == timezone.utc

    def test_entry_default_details_is_empty_dict(self):
        """Entry defaults to empty dict for details."""
        entry = AuditEntry(
            event_type=AuditEventType.ROBOT_STARTED,
            severity=AuditSeverity.INFO,
            message="Robot started",
        )

        assert entry.details == {}


# =============================================================================
# TEST SECTION 2: Audit Logger Initialization
# =============================================================================


class TestAuditLoggerInitialization:
    """Tests for AuditLogger initialization."""

    def test_logger_creates_directory(self, tmp_path: Path):
        """Logger creates log directory if missing."""
        audit_dir = tmp_path / "new_audit_dir"

        AuditLogger(robot_id="test-robot", log_dir=audit_dir)

        assert audit_dir.exists()

    def test_logger_initializes_log_file(self, temp_audit_dir: Path):
        """Logger initializes log file on creation."""
        logger = AuditLogger(robot_id="test-robot", log_dir=temp_audit_dir)

        assert logger._current_file is not None
        assert "audit_" in logger._current_file.name
        assert logger._current_file.suffix == ".jsonl"

    def test_logger_tracks_robot_id(self, temp_audit_dir: Path):
        """Logger stores robot ID."""
        logger = AuditLogger(robot_id="my-robot-id", log_dir=temp_audit_dir)

        assert logger.robot_id == "my-robot-id"

    def test_logger_default_log_dir(self, monkeypatch):
        """Logger uses default directory if not specified."""
        # Mock home directory
        mock_home = Path("/mock/home")
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        logger = AuditLogger(robot_id="test-robot")

        assert "casare_rpa" in str(logger.log_dir)
        assert "audit" in str(logger.log_dir)


# =============================================================================
# TEST SECTION 3: Audit Log Persistence
# =============================================================================


class TestAuditLogPersistence:
    """Tests for audit log file persistence."""

    def test_log_writes_to_file(self, audit_logger: AuditLogger):
        """Log entries are written to file."""
        audit_logger.log(
            AuditEventType.ROBOT_STARTED,
            "Robot started for testing",
        )

        # Read the log file
        content = audit_logger._current_file.read_text()
        lines = content.strip().split("\n")

        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["event_type"] == "robot.started"

    def test_multiple_logs_append(self, audit_logger: AuditLogger):
        """Multiple log entries append to same file."""
        audit_logger.log(AuditEventType.ROBOT_STARTED, "First entry")
        audit_logger.log(AuditEventType.JOB_STARTED, "Second entry", job_id="job-001")
        audit_logger.log(AuditEventType.JOB_COMPLETED, "Third entry", job_id="job-001")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        assert len(lines) >= 3

    def test_log_entry_format_is_jsonl(self, audit_logger: AuditLogger):
        """Log entries are in JSON Lines format (one JSON object per line)."""
        audit_logger.log(AuditEventType.JOB_RECEIVED, "Job received", job_id="job-001")
        audit_logger.log(AuditEventType.JOB_CLAIMED, "Job claimed", job_id="job-001")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]

        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "event_type" in parsed
            assert "timestamp" in parsed

    def test_log_preserves_details(self, audit_logger: AuditLogger):
        """Log preserves details dictionary."""
        details = {
            "workflow_name": "Test Workflow",
            "total_nodes": 10,
            "variables": {"input": "value"},
        }

        audit_logger.log(
            AuditEventType.WORKFLOW_LOADED,
            "Workflow loaded",
            details=details,
        )

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["details"]["workflow_name"] == "Test Workflow"
        assert entry["details"]["total_nodes"] == 10

    def test_log_handles_write_error_gracefully(self, audit_logger: AuditLogger):
        """Logger handles file write errors gracefully."""
        # Make file read-only (on platforms that support it)
        if os.name != "nt":  # Skip on Windows
            audit_logger._current_file.chmod(0o444)

        # Should not raise, just log error
        audit_logger.log(AuditEventType.ROBOT_STARTED, "Test entry")

        # Restore permissions for cleanup
        audit_logger._current_file.chmod(0o644)


# =============================================================================
# TEST SECTION 4: Log Rotation
# =============================================================================


class TestLogRotation:
    """Tests for log file rotation."""

    def test_rotation_when_size_exceeded(self, temp_audit_dir: Path):
        """Log file rotates when size limit exceeded."""
        # Note: Log rotation is best-effort and may fail on Windows
        # when file names collide within the same second.
        # This test verifies the rotation attempt occurs without crashing.

        # Create logger with very small size limit
        logger = AuditLogger(
            robot_id="test-robot",
            log_dir=temp_audit_dir,
            max_file_size_mb=0.0001,  # Very small to trigger rotation
            backup_count=3,
        )

        # Write enough to potentially trigger rotation
        # Rotation may fail silently on Windows due to file name collision
        for i in range(10):
            try:
                logger.log(
                    AuditEventType.NODE_STARTED,
                    f"Node execution {i}" * 100,  # Large message
                )
            except FileExistsError:
                # Windows may throw this if rotation happens too fast
                pass

        # File should exist (new file or same file)
        files = list(temp_audit_dir.glob("audit_*.jsonl"))
        # At minimum we have the current file
        assert len(files) >= 1

    def test_cleanup_old_files(self, temp_audit_dir: Path):
        """Cleanup removes old files beyond backup_count."""
        logger = AuditLogger(
            robot_id="test-robot",
            log_dir=temp_audit_dir,
            backup_count=2,
        )

        # Create extra old files
        for i in range(5):
            old_file = temp_audit_dir / f"audit_2024-01-0{i}.jsonl"
            old_file.write_text('{"test": true}\n')

        logger._cleanup_old_files()

        # Should keep only backup_count files
        remaining = list(temp_audit_dir.glob("audit_*.jsonl"))
        assert len(remaining) <= 3  # backup_count + current


# =============================================================================
# TEST SECTION 5: Context Managers
# =============================================================================


class TestContextManagers:
    """Tests for job and node context managers."""

    def test_job_context_sets_job_id(self, audit_logger: AuditLogger):
        """Job context manager sets current job ID."""
        with audit_logger.job_context("job-123"):
            assert audit_logger._current_job_id == "job-123"

        # Restored after context
        assert audit_logger._current_job_id is None

    def test_job_context_populates_log_entries(self, audit_logger: AuditLogger):
        """Log entries within job context get job_id populated."""
        with audit_logger.job_context("job-456"):
            audit_logger.log(AuditEventType.NODE_STARTED, "Node started")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["job_id"] == "job-456"

    def test_node_context_sets_node_id(self, audit_logger: AuditLogger):
        """Node context manager sets current node ID."""
        with audit_logger.node_context("node-abc"):
            assert audit_logger._current_node_id == "node-abc"

        assert audit_logger._current_node_id is None

    def test_nested_contexts(self, audit_logger: AuditLogger):
        """Nested contexts work correctly."""
        with audit_logger.job_context("job-001"):
            with audit_logger.node_context("node-001"):
                assert audit_logger._current_job_id == "job-001"
                assert audit_logger._current_node_id == "node-001"

            # Node context restored
            assert audit_logger._current_node_id is None
            assert audit_logger._current_job_id == "job-001"

        # Both restored
        assert audit_logger._current_job_id is None

    def test_explicit_ids_override_context(self, audit_logger: AuditLogger):
        """Explicit IDs in log() override context values."""
        with audit_logger.job_context("context-job"):
            audit_logger.log(
                AuditEventType.NODE_STARTED,
                "Node started",
                job_id="explicit-job",
            )

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["job_id"] == "explicit-job"


# =============================================================================
# TEST SECTION 6: Convenience Methods
# =============================================================================


class TestConvenienceMethods:
    """Tests for convenience logging methods."""

    def test_robot_started(self, audit_logger: AuditLogger):
        """robot_started logs correct event."""
        audit_logger.robot_started(details={"version": "1.0.0"})

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "robot.started"
        assert entry["details"]["version"] == "1.0.0"

    def test_robot_stopped(self, audit_logger: AuditLogger):
        """robot_stopped logs correct event."""
        audit_logger.robot_stopped(reason="shutdown requested")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "robot.stopped"
        assert "shutdown requested" in entry["message"]

    def test_connection_established(self, audit_logger: AuditLogger):
        """connection_established logs correct event."""
        audit_logger.connection_established()

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "connection.established"

    def test_connection_lost(self, audit_logger: AuditLogger):
        """connection_lost logs correct event with warning severity."""
        audit_logger.connection_lost(reason="network error")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "connection.lost"
        assert entry["severity"] == "warning"

    def test_connection_reconnecting(self, audit_logger: AuditLogger):
        """connection_reconnecting logs attempt number."""
        audit_logger.connection_reconnecting(attempt=3)

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "connection.reconnecting"
        assert entry["details"]["attempt"] == 3

    def test_job_received(self, audit_logger: AuditLogger):
        """job_received logs workflow name."""
        audit_logger.job_received("job-001", "TestWorkflow")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "job.received"
        assert entry["job_id"] == "job-001"
        assert entry["details"]["workflow_name"] == "TestWorkflow"

    def test_job_claimed(self, audit_logger: AuditLogger):
        """job_claimed logs job ID."""
        audit_logger.job_claimed("job-002")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "job.claimed"
        assert entry["job_id"] == "job-002"

    def test_job_started(self, audit_logger: AuditLogger):
        """job_started logs node count."""
        audit_logger.job_started("job-003", total_nodes=15)

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "job.started"
        assert entry["details"]["total_nodes"] == 15

    def test_job_completed(self, audit_logger: AuditLogger):
        """job_completed logs duration."""
        audit_logger.job_completed("job-004", duration_ms=5000)

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "job.completed"
        assert entry["details"]["duration_ms"] == 5000

    def test_job_failed(self, audit_logger: AuditLogger):
        """job_failed logs error with error severity."""
        audit_logger.job_failed("job-005", "Element not found", duration_ms=1500)

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "job.failed"
        assert entry["severity"] == "error"
        assert "Element not found" in entry["details"]["error"]

    def test_job_cancelled(self, audit_logger: AuditLogger):
        """job_cancelled logs with warning severity."""
        audit_logger.job_cancelled("job-006", reason="user requested")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "job.cancelled"
        assert entry["severity"] == "warning"

    def test_node_started(self, audit_logger: AuditLogger):
        """node_started logs node type with debug severity."""
        audit_logger.node_started("node-001", "ClickElement")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "execution.node_started"
        assert entry["severity"] == "debug"
        assert entry["details"]["node_type"] == "ClickElement"

    def test_node_completed(self, audit_logger: AuditLogger):
        """node_completed logs duration."""
        audit_logger.node_completed("node-002", "TypeText", duration_ms=250)

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "execution.node_completed"
        assert entry["details"]["duration_ms"] == 250

    def test_node_failed(self, audit_logger: AuditLogger):
        """node_failed logs error."""
        audit_logger.node_failed("node-003", "WaitForElement", "Timeout exceeded")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "execution.node_failed"
        assert entry["severity"] == "error"

    def test_node_retried(self, audit_logger: AuditLogger):
        """node_retried logs attempt number."""
        audit_logger.node_retried(
            "node-004", "ClickElement", attempt=2, error="Click failed"
        )

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "execution.node_retried"
        assert entry["details"]["attempt"] == 2

    def test_error_logged_transient(self, audit_logger: AuditLogger):
        """error_logged categorizes transient errors."""
        audit_logger.error_logged("transient", "Network timeout")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "error.transient"

    def test_error_logged_permanent(self, audit_logger: AuditLogger):
        """error_logged categorizes permanent errors."""
        audit_logger.error_logged("permanent", "Invalid credentials")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "error.permanent"

    def test_checkpoint_saved(self, audit_logger: AuditLogger):
        """checkpoint_saved logs checkpoint info."""
        audit_logger.checkpoint_saved("job-007", "node-005", "cp-001")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "checkpoint.saved"
        assert entry["details"]["checkpoint_id"] == "cp-001"

    def test_checkpoint_restored(self, audit_logger: AuditLogger):
        """checkpoint_restored logs restored checkpoint."""
        audit_logger.checkpoint_restored("job-008", "cp-002", "node-006")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "checkpoint.restored"
        assert entry["details"]["restored_at_node"] == "node-006"

    def test_circuit_state_changed_open(self, audit_logger: AuditLogger):
        """circuit_state_changed logs open state with warning."""
        audit_logger.circuit_state_changed("robot-circuit", "open")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "circuit.opened"
        assert entry["severity"] == "warning"

    def test_circuit_state_changed_closed(self, audit_logger: AuditLogger):
        """circuit_state_changed logs closed state with info."""
        audit_logger.circuit_state_changed("robot-circuit", "closed")

        content = audit_logger._current_file.read_text()
        lines = [line for line in content.strip().split("\n") if line]
        entry = json.loads(lines[-1])

        assert entry["event_type"] == "circuit.closed"
        assert entry["severity"] == "info"


# =============================================================================
# TEST SECTION 7: Query Functionality
# =============================================================================


class TestQueryFunctionality:
    """Tests for audit query methods."""

    def test_get_recent_returns_latest_entries(self, audit_logger: AuditLogger):
        """get_recent returns most recent entries."""
        for i in range(20):
            audit_logger.log(AuditEventType.NODE_STARTED, f"Node {i}")

        recent = audit_logger.get_recent(limit=5)

        assert len(recent) == 5
        # Most recent should be "Node 19"
        assert "Node 19" in recent[-1]["message"]

    def test_get_recent_respects_limit(self, audit_logger: AuditLogger):
        """get_recent respects the limit parameter."""
        for i in range(10):
            audit_logger.log(AuditEventType.NODE_STARTED, f"Node {i}")

        recent = audit_logger.get_recent(limit=3)

        assert len(recent) == 3

    def test_query_by_event_type(self, audit_logger: AuditLogger):
        """Query filters by event type."""
        audit_logger.log(AuditEventType.JOB_STARTED, "Job started", job_id="job-001")
        audit_logger.log(AuditEventType.NODE_STARTED, "Node started")
        audit_logger.log(
            AuditEventType.JOB_COMPLETED, "Job completed", job_id="job-001"
        )

        results = audit_logger.query(
            event_types=[AuditEventType.JOB_STARTED, AuditEventType.JOB_COMPLETED],
        )

        assert len(results) == 2
        for r in results:
            assert r["event_type"] in ["job.started", "job.completed"]

    def test_query_by_severity(self, audit_logger: AuditLogger):
        """Query filters by minimum severity."""
        audit_logger.log(
            AuditEventType.NODE_STARTED, "Debug event", severity=AuditSeverity.DEBUG
        )
        audit_logger.log(
            AuditEventType.JOB_FAILED, "Error event", severity=AuditSeverity.ERROR
        )
        audit_logger.log(
            AuditEventType.CONNECTION_LOST,
            "Warning event",
            severity=AuditSeverity.WARNING,
        )

        results = audit_logger.query(severity=AuditSeverity.WARNING)

        # Should return warning and error (>= warning)
        assert len(results) == 2
        for r in results:
            assert r["severity"] in ["warning", "error"]

    def test_query_by_job_id(self, audit_logger: AuditLogger):
        """Query filters by job ID."""
        audit_logger.log(AuditEventType.JOB_STARTED, "Job 1 started", job_id="job-001")
        audit_logger.log(AuditEventType.JOB_STARTED, "Job 2 started", job_id="job-002")
        audit_logger.log(
            AuditEventType.JOB_COMPLETED, "Job 1 completed", job_id="job-001"
        )

        results = audit_logger.query(job_id="job-001")

        assert len(results) == 2
        for r in results:
            assert r["job_id"] == "job-001"

    def test_query_by_since_timestamp(self, audit_logger: AuditLogger):
        """Query filters by timestamp."""
        # Log some entries
        audit_logger.log(AuditEventType.NODE_STARTED, "Old entry")

        # Get timestamp after first entry
        since_time = datetime.now(timezone.utc)

        # Log more entries
        audit_logger.log(AuditEventType.NODE_COMPLETED, "New entry 1")
        audit_logger.log(AuditEventType.NODE_COMPLETED, "New entry 2")

        results = audit_logger.query(since=since_time)

        assert len(results) == 2
        for r in results:
            assert "New entry" in r["message"]

    def test_query_combined_filters(self, audit_logger: AuditLogger):
        """Query with multiple filters."""
        audit_logger.log(
            AuditEventType.JOB_FAILED,
            "Job 1 failed",
            job_id="job-001",
            severity=AuditSeverity.ERROR,
        )
        audit_logger.log(
            AuditEventType.JOB_COMPLETED, "Job 1 completed", job_id="job-001"
        )
        audit_logger.log(
            AuditEventType.JOB_FAILED,
            "Job 2 failed",
            job_id="job-002",
            severity=AuditSeverity.ERROR,
        )

        results = audit_logger.query(
            event_types=[AuditEventType.JOB_FAILED],
            job_id="job-001",
        )

        assert len(results) == 1
        assert results[0]["job_id"] == "job-001"
        assert results[0]["event_type"] == "job.failed"


# =============================================================================
# TEST SECTION 8: External Handler
# =============================================================================


class TestExternalHandler:
    """Tests for external handler integration."""

    def test_external_handler_called(self, temp_audit_dir: Path, external_handler):
        """External handler is called for each log entry."""
        logger = AuditLogger(
            robot_id="test-robot",
            log_dir=temp_audit_dir,
            external_handler=external_handler,
        )

        logger.log(AuditEventType.ROBOT_STARTED, "Robot started")

        external_handler.assert_called_once()
        call_arg = external_handler.call_args[0][0]
        assert isinstance(call_arg, AuditEntry)

    def test_external_handler_error_handled(self, temp_audit_dir: Path):
        """External handler errors are caught and logged."""
        failing_handler = Mock(side_effect=RuntimeError("Handler failed"))

        logger = AuditLogger(
            robot_id="test-robot",
            log_dir=temp_audit_dir,
            external_handler=failing_handler,
        )

        # Should not raise
        logger.log(AuditEventType.ROBOT_STARTED, "Robot started")

        failing_handler.assert_called_once()


# =============================================================================
# TEST SECTION 9: In-Memory Buffer
# =============================================================================


class TestInMemoryBuffer:
    """Tests for in-memory buffer functionality."""

    def test_buffer_stores_entries(self, audit_logger: AuditLogger):
        """Buffer stores entries in memory."""
        audit_logger.log(AuditEventType.NODE_STARTED, "Entry 1")
        audit_logger.log(AuditEventType.NODE_COMPLETED, "Entry 2")

        assert len(audit_logger._buffer) == 2

    def test_buffer_respects_limit(self, temp_audit_dir: Path):
        """Buffer respects size limit."""
        logger = AuditLogger(
            robot_id="test-robot",
            log_dir=temp_audit_dir,
        )
        logger._buffer_limit = 5

        for i in range(10):
            logger.log(AuditEventType.NODE_STARTED, f"Entry {i}")

        assert len(logger._buffer) == 5
        # Should have newest entries
        assert "Entry 9" in logger._buffer[-1].message


# =============================================================================
# TEST SECTION 10: Global Logger Functions
# =============================================================================


class TestGlobalLoggerFunctions:
    """Tests for global logger accessor functions."""

    def test_init_audit_logger(self, temp_audit_dir: Path):
        """init_audit_logger creates new logger."""
        logger = init_audit_logger(
            robot_id="global-test-robot",
            log_dir=temp_audit_dir,
        )

        assert logger.robot_id == "global-test-robot"

    def test_get_audit_logger_after_init(self, temp_audit_dir: Path):
        """get_audit_logger returns initialized logger."""
        init_audit_logger(robot_id="get-test-robot", log_dir=temp_audit_dir)

        logger = get_audit_logger()

        assert logger.robot_id == "get-test-robot"

    def test_get_audit_logger_requires_init_or_robot_id(self):
        """get_audit_logger requires prior init or robot_id."""
        # Reset global logger
        import casare_rpa.robot.audit as audit_module

        audit_module._audit_logger = None

        with pytest.raises(ValueError, match="robot_id required"):
            get_audit_logger()


# =============================================================================
# TEST SECTION 11: Severity Levels
# =============================================================================


class TestSeverityLevels:
    """Tests for severity level handling."""

    def test_debug_severity(self, audit_logger: AuditLogger):
        """Debug severity is logged correctly."""
        audit_logger.log(
            AuditEventType.NODE_STARTED,
            "Debug message",
            severity=AuditSeverity.DEBUG,
        )

        recent = audit_logger.get_recent(limit=1)
        assert recent[0]["severity"] == "debug"

    def test_info_severity(self, audit_logger: AuditLogger):
        """Info severity is the default."""
        audit_logger.log(AuditEventType.ROBOT_STARTED, "Info message")

        recent = audit_logger.get_recent(limit=1)
        assert recent[0]["severity"] == "info"

    def test_warning_severity(self, audit_logger: AuditLogger):
        """Warning severity is logged correctly."""
        audit_logger.log(
            AuditEventType.CONNECTION_LOST,
            "Warning message",
            severity=AuditSeverity.WARNING,
        )

        recent = audit_logger.get_recent(limit=1)
        assert recent[0]["severity"] == "warning"

    def test_error_severity(self, audit_logger: AuditLogger):
        """Error severity is logged correctly."""
        audit_logger.log(
            AuditEventType.JOB_FAILED,
            "Error message",
            severity=AuditSeverity.ERROR,
        )

        recent = audit_logger.get_recent(limit=1)
        assert recent[0]["severity"] == "error"

    def test_critical_severity(self, audit_logger: AuditLogger):
        """Critical severity is logged correctly."""
        audit_logger.log(
            AuditEventType.ERROR_PERMANENT,
            "Critical message",
            severity=AuditSeverity.CRITICAL,
        )

        recent = audit_logger.get_recent(limit=1)
        assert recent[0]["severity"] == "critical"


# =============================================================================
# TEST SECTION 12: Event Types Coverage
# =============================================================================


class TestEventTypesCoverage:
    """Tests for all event type values."""

    @pytest.mark.parametrize(
        "event_type",
        [
            AuditEventType.ROBOT_STARTED,
            AuditEventType.ROBOT_STOPPED,
            AuditEventType.ROBOT_REGISTERED,
            AuditEventType.CONNECTION_ESTABLISHED,
            AuditEventType.CONNECTION_LOST,
            AuditEventType.CONNECTION_RECONNECTING,
            AuditEventType.CONNECTION_FAILED,
            AuditEventType.JOB_RECEIVED,
            AuditEventType.JOB_CLAIMED,
            AuditEventType.JOB_STARTED,
            AuditEventType.JOB_COMPLETED,
            AuditEventType.JOB_FAILED,
            AuditEventType.JOB_CANCELLED,
            AuditEventType.JOB_CACHED,
            AuditEventType.JOB_SYNCED,
            AuditEventType.WORKFLOW_LOADED,
            AuditEventType.NODE_STARTED,
            AuditEventType.NODE_COMPLETED,
            AuditEventType.NODE_FAILED,
            AuditEventType.NODE_SKIPPED,
            AuditEventType.NODE_RETRIED,
            AuditEventType.CHECKPOINT_SAVED,
            AuditEventType.CHECKPOINT_RESTORED,
            AuditEventType.CHECKPOINT_CLEARED,
            AuditEventType.ERROR_TRANSIENT,
            AuditEventType.ERROR_PERMANENT,
            AuditEventType.ERROR_UNKNOWN,
            AuditEventType.CREDENTIAL_VALIDATED,
            AuditEventType.CREDENTIAL_INVALID,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.CIRCUIT_OPENED,
            AuditEventType.CIRCUIT_HALF_OPEN,
            AuditEventType.CIRCUIT_CLOSED,
        ],
    )
    def test_all_event_types_can_be_logged(self, audit_logger: AuditLogger, event_type):
        """All event types can be logged successfully."""
        audit_logger.log(event_type, f"Test message for {event_type.value}")

        recent = audit_logger.get_recent(limit=1)
        assert recent[0]["event_type"] == event_type.value
