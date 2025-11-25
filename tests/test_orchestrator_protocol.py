"""Tests for orchestrator communication protocol."""
import pytest
import json
from datetime import datetime

from casare_rpa.orchestrator.protocol import (
    MessageType,
    Message,
    MessageBuilder
)


class TestMessageType:
    """Tests for MessageType enum."""

    def test_all_message_types_exist(self):
        """Verify all expected message types exist."""
        expected_types = [
            "REGISTER", "REGISTER_ACK", "HEARTBEAT", "HEARTBEAT_ACK", "DISCONNECT",
            "JOB_ASSIGN", "JOB_ACCEPT", "JOB_REJECT", "JOB_PROGRESS",
            "JOB_COMPLETE", "JOB_FAILED", "JOB_CANCEL", "JOB_CANCELLED",
            "STATUS_REQUEST", "STATUS_RESPONSE",
            "LOG_ENTRY", "LOG_BATCH",
            "PAUSE", "RESUME", "SHUTDOWN",
            "ERROR"
        ]
        for type_name in expected_types:
            assert hasattr(MessageType, type_name)

    def test_message_type_values(self):
        """Verify message type values are lowercase strings."""
        assert MessageType.REGISTER.value == "register"
        assert MessageType.JOB_ASSIGN.value == "job_assign"
        assert MessageType.HEARTBEAT_ACK.value == "heartbeat_ack"


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation(self):
        """Test basic message creation."""
        msg = Message(type=MessageType.REGISTER, payload={"robot_id": "r1"})

        assert msg.type == MessageType.REGISTER
        assert msg.payload == {"robot_id": "r1"}
        assert msg.id is not None
        assert msg.timestamp is not None
        assert msg.correlation_id is None

    def test_message_with_correlation_id(self):
        """Test message with correlation ID."""
        msg = Message(
            type=MessageType.REGISTER_ACK,
            payload={"success": True},
            correlation_id="corr-123"
        )

        assert msg.correlation_id == "corr-123"

    def test_message_to_json(self):
        """Test message serialization to JSON."""
        msg = Message(
            type=MessageType.HEARTBEAT,
            id="msg-123",
            timestamp="2024-01-01T00:00:00",
            payload={"status": "online"},
        )

        json_str = msg.to_json()
        data = json.loads(json_str)

        assert data["type"] == "heartbeat"
        assert data["id"] == "msg-123"
        assert data["timestamp"] == "2024-01-01T00:00:00"
        assert data["payload"] == {"status": "online"}

    def test_message_to_json_with_correlation(self):
        """Test message serialization includes correlation_id."""
        msg = Message(
            type=MessageType.JOB_ACCEPT,
            payload={},
            correlation_id="corr-456"
        )

        json_str = msg.to_json()
        data = json.loads(json_str)

        assert data["correlation_id"] == "corr-456"

    def test_message_from_json(self):
        """Test message deserialization from JSON."""
        json_str = json.dumps({
            "type": "job_progress",
            "id": "msg-456",
            "timestamp": "2024-01-01T12:00:00",
            "payload": {"job_id": "j1", "progress": 50},
            "correlation_id": "corr-789"
        })

        msg = Message.from_json(json_str)

        assert msg.type == MessageType.JOB_PROGRESS
        assert msg.id == "msg-456"
        assert msg.timestamp == "2024-01-01T12:00:00"
        assert msg.payload == {"job_id": "j1", "progress": 50}
        assert msg.correlation_id == "corr-789"

    def test_message_from_json_minimal(self):
        """Test deserialization with minimal fields."""
        json_str = json.dumps({"type": "pause"})

        msg = Message.from_json(json_str)

        assert msg.type == MessageType.PAUSE
        assert msg.id is not None
        assert msg.payload == {}

    def test_message_roundtrip(self):
        """Test serialization/deserialization roundtrip."""
        original = Message(
            type=MessageType.JOB_COMPLETE,
            payload={"result": {"output": "data"}, "duration_ms": 1000},
            correlation_id="roundtrip-test"
        )

        json_str = original.to_json()
        restored = Message.from_json(json_str)

        assert restored.type == original.type
        assert restored.id == original.id
        assert restored.payload == original.payload
        assert restored.correlation_id == original.correlation_id


class TestMessageBuilderRegister:
    """Tests for MessageBuilder registration messages."""

    def test_register_message(self):
        """Test building registration message."""
        msg = MessageBuilder.register(
            robot_id="robot-001",
            robot_name="Test Robot",
            environment="production",
            max_concurrent_jobs=2,
            tags=["web", "desktop"],
            capabilities={"browser": True}
        )

        assert msg.type == MessageType.REGISTER
        assert msg.payload["robot_id"] == "robot-001"
        assert msg.payload["robot_name"] == "Test Robot"
        assert msg.payload["environment"] == "production"
        assert msg.payload["max_concurrent_jobs"] == 2
        assert msg.payload["tags"] == ["web", "desktop"]
        assert msg.payload["capabilities"] == {"browser": True}

    def test_register_message_defaults(self):
        """Test register message with default values."""
        msg = MessageBuilder.register(
            robot_id="r1",
            robot_name="Robot 1"
        )

        assert msg.payload["environment"] == "default"
        assert msg.payload["max_concurrent_jobs"] == 1
        assert msg.payload["tags"] == []
        assert msg.payload["capabilities"] == {}

    def test_register_ack_success(self):
        """Test building successful registration acknowledgment."""
        msg = MessageBuilder.register_ack(
            robot_id="r1",
            success=True,
            message="Registered successfully",
            config={"heartbeat_interval": 30},
            correlation_id="corr-123"
        )

        assert msg.type == MessageType.REGISTER_ACK
        assert msg.payload["robot_id"] == "r1"
        assert msg.payload["success"] is True
        assert msg.payload["message"] == "Registered successfully"
        assert msg.payload["config"] == {"heartbeat_interval": 30}
        assert msg.correlation_id == "corr-123"

    def test_register_ack_failure(self):
        """Test building failed registration acknowledgment."""
        msg = MessageBuilder.register_ack(
            robot_id="r1",
            success=False,
            message="Authentication failed"
        )

        assert msg.payload["success"] is False
        assert msg.payload["message"] == "Authentication failed"


class TestMessageBuilderHeartbeat:
    """Tests for MessageBuilder heartbeat messages."""

    def test_heartbeat_message(self):
        """Test building heartbeat message."""
        msg = MessageBuilder.heartbeat(
            robot_id="r1",
            status="online",
            current_jobs=1,
            cpu_percent=50.5,
            memory_percent=60.0,
            disk_percent=40.0,
            active_job_ids=["job-1", "job-2"]
        )

        assert msg.type == MessageType.HEARTBEAT
        assert msg.payload["robot_id"] == "r1"
        assert msg.payload["status"] == "online"
        assert msg.payload["current_jobs"] == 1
        assert msg.payload["cpu_percent"] == 50.5
        assert msg.payload["memory_percent"] == 60.0
        assert msg.payload["disk_percent"] == 40.0
        assert msg.payload["active_job_ids"] == ["job-1", "job-2"]

    def test_heartbeat_defaults(self):
        """Test heartbeat with default values."""
        msg = MessageBuilder.heartbeat(robot_id="r1", status="online")

        assert msg.payload["current_jobs"] == 0
        assert msg.payload["cpu_percent"] == 0.0
        assert msg.payload["active_job_ids"] == []

    def test_heartbeat_ack(self):
        """Test building heartbeat acknowledgment."""
        msg = MessageBuilder.heartbeat_ack(robot_id="r1", correlation_id="hb-123")

        assert msg.type == MessageType.HEARTBEAT_ACK
        assert msg.payload["robot_id"] == "r1"
        assert msg.correlation_id == "hb-123"


class TestMessageBuilderJob:
    """Tests for MessageBuilder job messages."""

    def test_job_assign(self):
        """Test building job assignment message."""
        msg = MessageBuilder.job_assign(
            job_id="job-001",
            workflow_id="wf-001",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
            priority=2,
            timeout_seconds=1800,
            parameters={"input": "value"}
        )

        assert msg.type == MessageType.JOB_ASSIGN
        assert msg.payload["job_id"] == "job-001"
        assert msg.payload["workflow_id"] == "wf-001"
        assert msg.payload["workflow_name"] == "Test Workflow"
        assert msg.payload["workflow_json"] == '{"nodes": []}'
        assert msg.payload["priority"] == 2
        assert msg.payload["timeout_seconds"] == 1800
        assert msg.payload["parameters"] == {"input": "value"}

    def test_job_assign_defaults(self):
        """Test job assign with defaults."""
        msg = MessageBuilder.job_assign(
            job_id="j1",
            workflow_id="w1",
            workflow_name="W1",
            workflow_json="{}"
        )

        assert msg.payload["priority"] == 1
        assert msg.payload["timeout_seconds"] == 3600
        assert msg.payload["parameters"] == {}

    def test_job_accept(self):
        """Test building job acceptance message."""
        msg = MessageBuilder.job_accept(
            job_id="job-001",
            robot_id="r1",
            correlation_id="ja-123"
        )

        assert msg.type == MessageType.JOB_ACCEPT
        assert msg.payload["job_id"] == "job-001"
        assert msg.payload["robot_id"] == "r1"
        assert msg.correlation_id == "ja-123"

    def test_job_reject(self):
        """Test building job rejection message."""
        msg = MessageBuilder.job_reject(
            job_id="job-001",
            robot_id="r1",
            reason="Robot is busy",
            correlation_id="jr-123"
        )

        assert msg.type == MessageType.JOB_REJECT
        assert msg.payload["job_id"] == "job-001"
        assert msg.payload["reason"] == "Robot is busy"

    def test_job_progress(self):
        """Test building job progress message."""
        msg = MessageBuilder.job_progress(
            job_id="job-001",
            robot_id="r1",
            progress=75,
            current_node="node-5",
            message="Processing data"
        )

        assert msg.type == MessageType.JOB_PROGRESS
        assert msg.payload["progress"] == 75
        assert msg.payload["current_node"] == "node-5"
        assert msg.payload["message"] == "Processing data"

    def test_job_complete(self):
        """Test building job completion message."""
        msg = MessageBuilder.job_complete(
            job_id="job-001",
            robot_id="r1",
            result={"output": "success"},
            duration_ms=5000
        )

        assert msg.type == MessageType.JOB_COMPLETE
        assert msg.payload["result"] == {"output": "success"}
        assert msg.payload["duration_ms"] == 5000

    def test_job_failed(self):
        """Test building job failure message."""
        msg = MessageBuilder.job_failed(
            job_id="job-001",
            robot_id="r1",
            error_message="Connection timeout",
            error_type="NetworkError",
            stack_trace="Traceback...",
            failed_node="node-3"
        )

        assert msg.type == MessageType.JOB_FAILED
        assert msg.payload["error_message"] == "Connection timeout"
        assert msg.payload["error_type"] == "NetworkError"
        assert msg.payload["stack_trace"] == "Traceback..."
        assert msg.payload["failed_node"] == "node-3"

    def test_job_cancel(self):
        """Test building job cancellation request."""
        msg = MessageBuilder.job_cancel(
            job_id="job-001",
            reason="User cancelled"
        )

        assert msg.type == MessageType.JOB_CANCEL
        assert msg.payload["job_id"] == "job-001"
        assert msg.payload["reason"] == "User cancelled"

    def test_job_cancelled(self):
        """Test building job cancelled confirmation."""
        msg = MessageBuilder.job_cancelled(
            job_id="job-001",
            robot_id="r1",
            correlation_id="jc-123"
        )

        assert msg.type == MessageType.JOB_CANCELLED
        assert msg.payload["job_id"] == "job-001"


class TestMessageBuilderStatus:
    """Tests for MessageBuilder status messages."""

    def test_status_request(self):
        """Test building status request."""
        msg = MessageBuilder.status_request(robot_id="r1")

        assert msg.type == MessageType.STATUS_REQUEST
        assert msg.payload["robot_id"] == "r1"

    def test_status_response(self):
        """Test building status response."""
        msg = MessageBuilder.status_response(
            robot_id="r1",
            status="online",
            current_jobs=2,
            active_job_ids=["j1", "j2"],
            uptime_seconds=3600,
            system_info={"cpu": 50},
            correlation_id="sr-123"
        )

        assert msg.type == MessageType.STATUS_RESPONSE
        assert msg.payload["robot_id"] == "r1"
        assert msg.payload["status"] == "online"
        assert msg.payload["current_jobs"] == 2
        assert msg.payload["active_job_ids"] == ["j1", "j2"]
        assert msg.payload["uptime_seconds"] == 3600
        assert msg.payload["system_info"] == {"cpu": 50}


class TestMessageBuilderLog:
    """Tests for MessageBuilder log messages."""

    def test_log_entry(self):
        """Test building log entry."""
        msg = MessageBuilder.log_entry(
            job_id="j1",
            robot_id="r1",
            level="INFO",
            message="Starting execution",
            node_id="node-1",
            extra={"step": 1}
        )

        assert msg.type == MessageType.LOG_ENTRY
        assert msg.payload["job_id"] == "j1"
        assert msg.payload["level"] == "INFO"
        assert msg.payload["message"] == "Starting execution"
        assert msg.payload["node_id"] == "node-1"
        assert msg.payload["extra"] == {"step": 1}

    def test_log_batch(self):
        """Test building batch log message."""
        entries = [
            {"level": "INFO", "message": "Step 1"},
            {"level": "DEBUG", "message": "Step 2"},
        ]

        msg = MessageBuilder.log_batch(
            job_id="j1",
            robot_id="r1",
            entries=entries
        )

        assert msg.type == MessageType.LOG_BATCH
        assert msg.payload["entries"] == entries


class TestMessageBuilderControl:
    """Tests for MessageBuilder control messages."""

    def test_error(self):
        """Test building error message."""
        msg = MessageBuilder.error(
            error_code="AUTH_FAILED",
            error_message="Invalid token",
            details={"token_type": "bearer"},
            correlation_id="err-123"
        )

        assert msg.type == MessageType.ERROR
        assert msg.payload["error_code"] == "AUTH_FAILED"
        assert msg.payload["error_message"] == "Invalid token"
        assert msg.payload["details"] == {"token_type": "bearer"}
        assert msg.correlation_id == "err-123"

    def test_pause(self):
        """Test building pause command."""
        msg = MessageBuilder.pause(robot_id="r1")

        assert msg.type == MessageType.PAUSE
        assert msg.payload["robot_id"] == "r1"

    def test_resume(self):
        """Test building resume command."""
        msg = MessageBuilder.resume(robot_id="r1")

        assert msg.type == MessageType.RESUME
        assert msg.payload["robot_id"] == "r1"

    def test_shutdown_graceful(self):
        """Test building graceful shutdown command."""
        msg = MessageBuilder.shutdown(robot_id="r1", graceful=True)

        assert msg.type == MessageType.SHUTDOWN
        assert msg.payload["robot_id"] == "r1"
        assert msg.payload["graceful"] is True

    def test_shutdown_immediate(self):
        """Test building immediate shutdown command."""
        msg = MessageBuilder.shutdown(robot_id="r1", graceful=False)

        assert msg.payload["graceful"] is False

    def test_disconnect(self):
        """Test building disconnect message."""
        msg = MessageBuilder.disconnect(robot_id="r1", reason="Shutting down")

        assert msg.type == MessageType.DISCONNECT
        assert msg.payload["robot_id"] == "r1"
        assert msg.payload["reason"] == "Shutting down"


class TestMessageValidation:
    """Tests for message validation and edge cases."""

    def test_invalid_json(self):
        """Test handling invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            Message.from_json("not valid json")

    def test_invalid_message_type(self):
        """Test handling invalid message type."""
        json_str = json.dumps({"type": "unknown_type"})
        with pytest.raises(ValueError):
            Message.from_json(json_str)

    def test_empty_payload(self):
        """Test message with empty payload."""
        msg = Message(type=MessageType.PAUSE)
        assert msg.payload == {}

        json_str = msg.to_json()
        restored = Message.from_json(json_str)
        assert restored.payload == {}

    def test_large_payload(self):
        """Test message with large payload."""
        large_data = {"key_" + str(i): "value_" + str(i) * 100 for i in range(100)}

        msg = Message(type=MessageType.JOB_COMPLETE, payload={"result": large_data})
        json_str = msg.to_json()
        restored = Message.from_json(json_str)

        assert restored.payload["result"] == large_data

    def test_nested_payload(self):
        """Test message with nested payload."""
        nested = {
            "level1": {
                "level2": {
                    "level3": ["a", "b", "c"]
                }
            }
        }

        msg = Message(type=MessageType.LOG_ENTRY, payload=nested)
        json_str = msg.to_json()
        restored = Message.from_json(json_str)

        assert restored.payload == nested

    def test_special_characters_in_payload(self):
        """Test handling special characters."""
        msg = MessageBuilder.log_entry(
            job_id="j1",
            robot_id="r1",
            level="ERROR",
            message="Failed: \"Error\" with 'quotes' and \n newlines",
            node_id="",
        )

        json_str = msg.to_json()
        restored = Message.from_json(json_str)

        assert "newlines" in restored.payload["message"]
        assert "quotes" in restored.payload["message"]

    def test_unicode_in_payload(self):
        """Test handling unicode characters."""
        msg = MessageBuilder.log_entry(
            job_id="j1",
            robot_id="r1",
            level="INFO",
            message="Processing: 日本語, émojis 🎉, symbols ™®©",
            node_id="",
        )

        json_str = msg.to_json()
        restored = Message.from_json(json_str)

        assert "日本語" in restored.payload["message"]
        assert "🎉" in restored.payload["message"]
