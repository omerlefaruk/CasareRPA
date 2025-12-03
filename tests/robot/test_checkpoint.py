"""
Tests for Robot Agent Checkpoint System.

Tests checkpoint save/restore functionality for crash recovery:
- CheckpointState dataclass behavior
- CheckpointManager checkpoint creation/restoration
- Variable serialization and browser state capture
- Error recording and tracking
"""

import pytest
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Mock the offline_queue module before importing checkpoint
# This is necessary because offline_queue doesn't exist yet
mock_offline_queue_module = MagicMock()
sys.modules["casare_rpa.robot.offline_queue"] = mock_offline_queue_module

from casare_rpa.robot.checkpoint import (
    CheckpointState,
    CheckpointManager,
    create_checkpoint_state,
)


# --- Mock Classes ---


class MockOfflineQueue:
    """Mock OfflineQueue for testing checkpoint persistence."""

    def __init__(self):
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._save_success = True

    async def save_checkpoint(
        self,
        job_id: str,
        checkpoint_id: str,
        node_id: str,
        state: Dict[str, Any],
    ) -> bool:
        """Save checkpoint to mock storage."""
        if not self._save_success:
            return False
        self._checkpoints[job_id] = {
            "checkpoint_id": checkpoint_id,
            "node_id": node_id,
            "state": state,
        }
        return True

    async def get_latest_checkpoint(
        self,
        job_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get latest checkpoint for a job."""
        return self._checkpoints.get(job_id)

    async def clear_checkpoints(self, job_id: str) -> None:
        """Clear checkpoints for a job."""
        if job_id in self._checkpoints:
            del self._checkpoints[job_id]

    def set_save_failure(self, should_fail: bool = True):
        """Configure mock to fail saves."""
        self._save_success = not should_fail


class MockExecutionContext:
    """Mock ExecutionContext for testing."""

    def __init__(
        self,
        variables: Optional[Dict[str, Any]] = None,
        has_browser: bool = False,
        page_count: int = 0,
    ):
        self.variables = variables or {}
        self.browser = Mock() if has_browser else None
        self.active_page = Mock() if page_count > 0 else None
        self.pages = [Mock() for _ in range(page_count)]
        self._active_page_name = "main_page" if page_count > 0 else None


# --- Fixtures ---


@pytest.fixture
def mock_offline_queue() -> MockOfflineQueue:
    """Provide mock offline queue."""
    return MockOfflineQueue()


@pytest.fixture
def checkpoint_manager(mock_offline_queue: MockOfflineQueue) -> CheckpointManager:
    """Provide checkpoint manager with mock dependencies."""
    return CheckpointManager(
        offline_queue=mock_offline_queue,
        auto_save=True,
    )


@pytest.fixture
def execution_context() -> MockExecutionContext:
    """Provide mock execution context."""
    return MockExecutionContext(
        variables={
            "username": "test_user",
            "count": 42,
            "items": ["a", "b", "c"],
            "data": {"nested": "value"},
        }
    )


@pytest.fixture
def sample_checkpoint_state() -> CheckpointState:
    """Provide sample checkpoint state."""
    return CheckpointState(
        checkpoint_id="abc12345",
        job_id="job-001",
        workflow_name="Test Workflow",
        created_at="2024-01-01T00:00:00+00:00",
        current_node_id="node-003",
        executed_nodes=["node-001", "node-002", "node-003"],
        execution_path=["node-001", "node-002", "node-003"],
        variables={"var1": "value1", "count": 10},
        errors=[],
        has_browser=True,
        active_page_name="login_page",
        page_count=2,
    )


# --- CheckpointState Tests ---


class TestCheckpointState:
    """Tests for CheckpointState dataclass."""

    def test_create_checkpoint_state(self):
        """Creating checkpoint state with required fields."""
        state = CheckpointState(
            checkpoint_id="chk-001",
            job_id="job-001",
            workflow_name="Test Workflow",
            created_at="2024-01-01T00:00:00+00:00",
            current_node_id="node-001",
            executed_nodes=["node-001"],
            execution_path=["node-001"],
            variables={"x": 1},
            errors=[],
        )

        assert state.checkpoint_id == "chk-001"
        assert state.job_id == "job-001"
        assert state.workflow_name == "Test Workflow"
        assert state.current_node_id == "node-001"
        assert state.has_browser is False
        assert state.active_page_name is None
        assert state.page_count == 0

    def test_to_dict_serialization(self, sample_checkpoint_state: CheckpointState):
        """CheckpointState.to_dict() produces valid dictionary."""
        result = sample_checkpoint_state.to_dict()

        assert isinstance(result, dict)
        assert result["checkpoint_id"] == "abc12345"
        assert result["job_id"] == "job-001"
        assert result["workflow_name"] == "Test Workflow"
        assert result["current_node_id"] == "node-003"
        assert result["executed_nodes"] == ["node-001", "node-002", "node-003"]
        assert result["variables"] == {"var1": "value1", "count": 10}
        assert result["has_browser"] is True
        assert result["page_count"] == 2

    def test_from_dict_deserialization(self, sample_checkpoint_state: CheckpointState):
        """CheckpointState.from_dict() recreates state from dictionary."""
        data = sample_checkpoint_state.to_dict()
        restored = CheckpointState.from_dict(data)

        assert restored.checkpoint_id == sample_checkpoint_state.checkpoint_id
        assert restored.job_id == sample_checkpoint_state.job_id
        assert restored.workflow_name == sample_checkpoint_state.workflow_name
        assert restored.current_node_id == sample_checkpoint_state.current_node_id
        assert restored.executed_nodes == sample_checkpoint_state.executed_nodes
        assert restored.variables == sample_checkpoint_state.variables
        assert restored.has_browser == sample_checkpoint_state.has_browser

    def test_roundtrip_serialization(self):
        """to_dict() and from_dict() roundtrip preserves data."""
        original = CheckpointState(
            checkpoint_id="round-trip",
            job_id="job-rt",
            workflow_name="Roundtrip Workflow",
            created_at="2024-06-15T12:30:00+00:00",
            current_node_id="node-end",
            executed_nodes=["n1", "n2", "n3"],
            execution_path=["n1", "n2", "n3"],
            variables={"nested": {"deep": [1, 2, 3]}},
            errors=[{"node_id": "n2", "error": "timeout"}],
            has_browser=True,
            active_page_name="checkout",
            page_count=3,
        )

        data = original.to_dict()
        restored = CheckpointState.from_dict(data)

        assert restored.checkpoint_id == original.checkpoint_id
        assert restored.errors == original.errors
        assert restored.variables["nested"]["deep"] == [1, 2, 3]


class TestCreateCheckpointStateFactory:
    """Tests for create_checkpoint_state factory function."""

    def test_creates_valid_checkpoint(self):
        """Factory creates valid CheckpointState with defaults."""
        state = create_checkpoint_state(
            job_id="job-factory",
            workflow_name="Factory Workflow",
            node_id="node-1",
            executed_nodes=["node-1"],
            variables={"key": "value"},
        )

        assert state.job_id == "job-factory"
        assert state.workflow_name == "Factory Workflow"
        assert state.current_node_id == "node-1"
        assert state.executed_nodes == ["node-1"]
        assert state.execution_path == ["node-1"]
        assert state.variables == {"key": "value"}
        assert state.errors == []
        assert len(state.checkpoint_id) == 8  # UUID prefix
        assert state.created_at  # Timestamp set

    def test_factory_generates_unique_checkpoint_ids(self):
        """Factory generates unique checkpoint IDs."""
        states = [
            create_checkpoint_state(
                job_id="job",
                workflow_name="wf",
                node_id="n1",
                executed_nodes=["n1"],
                variables={},
            )
            for _ in range(10)
        ]

        checkpoint_ids = {s.checkpoint_id for s in states}
        assert len(checkpoint_ids) == 10  # All unique


# --- CheckpointManager Tests ---


class TestCheckpointManagerJobTracking:
    """Tests for job tracking lifecycle."""

    def test_start_job_initializes_state(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """start_job() initializes internal tracking state."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        assert checkpoint_manager._current_job_id == "job-001"
        assert checkpoint_manager._current_workflow_name == "Test Workflow"
        assert len(checkpoint_manager._executed_nodes) == 0
        assert len(checkpoint_manager._execution_path) == 0

    def test_end_job_clears_state(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """end_job() clears job tracking state."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        checkpoint_manager.end_job()

        assert checkpoint_manager._current_job_id is None
        assert checkpoint_manager._current_workflow_name is None

    def test_start_job_clears_previous_state(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """start_job() clears state from previous job."""
        checkpoint_manager.start_job("job-001", "Workflow 1")
        checkpoint_manager._executed_nodes.add("old-node")
        checkpoint_manager._errors.append({"error": "old"})

        checkpoint_manager.start_job("job-002", "Workflow 2")

        assert checkpoint_manager._current_job_id == "job-002"
        assert len(checkpoint_manager._executed_nodes) == 0
        assert len(checkpoint_manager._errors) == 0


class TestCheckpointManagerSaveCheckpoint:
    """Tests for checkpoint save functionality."""

    @pytest.mark.asyncio
    async def test_save_checkpoint_success(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
        execution_context: MockExecutionContext,
    ):
        """save_checkpoint() persists state and returns checkpoint ID."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        checkpoint_id = await checkpoint_manager.save_checkpoint(
            "node-001",
            execution_context,
        )

        assert checkpoint_id is not None
        assert len(checkpoint_id) == 8
        assert "node-001" in checkpoint_manager._executed_nodes
        assert checkpoint_manager._execution_path == ["node-001"]

        # Verify persisted to offline queue
        saved = mock_offline_queue._checkpoints.get("job-001")
        assert saved is not None
        assert saved["node_id"] == "node-001"

    @pytest.mark.asyncio
    async def test_save_checkpoint_without_job_returns_none(
        self,
        checkpoint_manager: CheckpointManager,
        execution_context: MockExecutionContext,
    ):
        """save_checkpoint() returns None when no job is active."""
        result = await checkpoint_manager.save_checkpoint(
            "node-001",
            execution_context,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_save_checkpoint_handles_save_failure(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
        execution_context: MockExecutionContext,
    ):
        """save_checkpoint() returns None when persistence fails."""
        mock_offline_queue.set_save_failure(True)
        checkpoint_manager.start_job("job-001", "Test Workflow")

        result = await checkpoint_manager.save_checkpoint(
            "node-001",
            execution_context,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_save_checkpoint_tracks_multiple_nodes(
        self,
        checkpoint_manager: CheckpointManager,
        execution_context: MockExecutionContext,
    ):
        """save_checkpoint() accumulates executed nodes in order."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", execution_context)
        await checkpoint_manager.save_checkpoint("node-002", execution_context)
        await checkpoint_manager.save_checkpoint("node-003", execution_context)

        assert checkpoint_manager._executed_nodes == {
            "node-001",
            "node-002",
            "node-003",
        }
        assert checkpoint_manager._execution_path == [
            "node-001",
            "node-002",
            "node-003",
        ]


class TestCheckpointManagerVariableSerialization:
    """Tests for variable extraction and serialization."""

    @pytest.mark.asyncio
    async def test_serializes_primitive_variables(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Primitive variables are serialized correctly."""
        context = MockExecutionContext(
            variables={
                "string_var": "hello",
                "int_var": 42,
                "float_var": 3.14,
                "bool_var": True,
                "none_var": None,
            }
        )
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]["variables"]
        assert saved["string_var"] == "hello"
        assert saved["int_var"] == 42
        assert saved["float_var"] == 3.14
        assert saved["bool_var"] is True
        assert saved["none_var"] is None

    @pytest.mark.asyncio
    async def test_serializes_nested_structures(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Nested dicts and lists are serialized."""
        context = MockExecutionContext(
            variables={
                "nested": {"deep": {"value": 123}},
                "list": [1, 2, {"key": "val"}],
            }
        )
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]["variables"]
        assert saved["nested"]["deep"]["value"] == 123
        assert saved["list"] == [1, 2, {"key": "val"}]

    @pytest.mark.asyncio
    async def test_handles_non_serializable_variables(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Non-serializable variables are marked as such."""
        context = MockExecutionContext(
            variables={
                "serializable": "valid",
                "function": lambda x: x,  # Not serializable
                "mock": Mock(),  # Not serializable
            }
        )
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]["variables"]
        assert saved["serializable"] == "valid"
        assert "<non-serializable:" in saved["function"]
        assert "<non-serializable:" in saved["mock"]


class TestCheckpointManagerBrowserStateCapture:
    """Tests for browser state capture."""

    @pytest.mark.asyncio
    async def test_captures_browser_presence(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Browser presence is captured in checkpoint."""
        context = MockExecutionContext(has_browser=True, page_count=0)
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]
        assert saved["has_browser"] is True

    @pytest.mark.asyncio
    async def test_captures_page_count(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Page count is captured in checkpoint."""
        context = MockExecutionContext(has_browser=True, page_count=3)
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]
        assert saved["page_count"] == 3

    @pytest.mark.asyncio
    async def test_captures_active_page_name(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Active page name is captured when available."""
        context = MockExecutionContext(has_browser=True, page_count=1)
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]
        assert saved["active_page_name"] == "main_page"

    @pytest.mark.asyncio
    async def test_handles_no_browser(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """Missing browser is handled gracefully."""
        context = MockExecutionContext(has_browser=False, page_count=0)
        checkpoint_manager.start_job("job-001", "Test Workflow")

        await checkpoint_manager.save_checkpoint("node-001", context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]
        assert saved["has_browser"] is False
        assert saved["active_page_name"] is None
        assert saved["page_count"] == 0


class TestCheckpointManagerGetCheckpoint:
    """Tests for checkpoint retrieval."""

    @pytest.mark.asyncio
    async def test_get_checkpoint_returns_state(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
        execution_context: MockExecutionContext,
    ):
        """get_checkpoint() returns CheckpointState for existing checkpoint."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        await checkpoint_manager.save_checkpoint("node-001", execution_context)
        checkpoint_manager.end_job()

        result = await checkpoint_manager.get_checkpoint("job-001")

        assert result is not None
        assert isinstance(result, CheckpointState)
        assert result.job_id == "job-001"
        assert result.current_node_id == "node-001"

    @pytest.mark.asyncio
    async def test_get_checkpoint_returns_none_for_missing(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """get_checkpoint() returns None when no checkpoint exists."""
        result = await checkpoint_manager.get_checkpoint("non-existent-job")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_checkpoint_handles_malformed_data(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """get_checkpoint() handles malformed checkpoint data."""
        mock_offline_queue._checkpoints["job-001"] = {
            "state": {"invalid": "data"}  # Missing required fields
        }

        result = await checkpoint_manager.get_checkpoint("job-001")

        assert result is None  # Should not raise, returns None


class TestCheckpointManagerRestoreCheckpoint:
    """Tests for checkpoint restoration."""

    @pytest.mark.asyncio
    async def test_restore_checkpoint_restores_variables(
        self,
        checkpoint_manager: CheckpointManager,
        sample_checkpoint_state: CheckpointState,
    ):
        """restore_from_checkpoint() restores variables to context."""
        context = MockExecutionContext()

        result = await checkpoint_manager.restore_from_checkpoint(
            sample_checkpoint_state,
            context,
        )

        assert result is True
        assert context.variables["var1"] == "value1"
        assert context.variables["count"] == 10

    @pytest.mark.asyncio
    async def test_restore_checkpoint_skips_non_serializable_markers(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """restore_from_checkpoint() skips non-serializable markers."""
        checkpoint = CheckpointState(
            checkpoint_id="chk",
            job_id="job",
            workflow_name="wf",
            created_at="2024-01-01T00:00:00+00:00",
            current_node_id="n1",
            executed_nodes=["n1"],
            execution_path=["n1"],
            variables={
                "valid": "value",
                "invalid": "<non-serializable: Mock>",
            },
            errors=[],
        )
        context = MockExecutionContext()

        await checkpoint_manager.restore_from_checkpoint(checkpoint, context)

        assert context.variables["valid"] == "value"
        assert "invalid" not in context.variables

    @pytest.mark.asyncio
    async def test_restore_checkpoint_restores_tracking_state(
        self,
        checkpoint_manager: CheckpointManager,
        sample_checkpoint_state: CheckpointState,
    ):
        """restore_from_checkpoint() restores internal tracking state."""
        context = MockExecutionContext()

        await checkpoint_manager.restore_from_checkpoint(
            sample_checkpoint_state,
            context,
        )

        assert checkpoint_manager._current_job_id == "job-001"
        assert checkpoint_manager._current_workflow_name == "Test Workflow"
        assert checkpoint_manager._executed_nodes == {
            "node-001",
            "node-002",
            "node-003",
        }
        assert checkpoint_manager._execution_path == [
            "node-001",
            "node-002",
            "node-003",
        ]


class TestCheckpointManagerErrorRecording:
    """Tests for error recording."""

    def test_record_error_adds_to_list(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """record_error() adds error to tracking list."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        checkpoint_manager.record_error("node-001", "Timeout waiting for element")

        assert len(checkpoint_manager._errors) == 1
        assert checkpoint_manager._errors[0]["node_id"] == "node-001"
        assert checkpoint_manager._errors[0]["error"] == "Timeout waiting for element"
        assert "timestamp" in checkpoint_manager._errors[0]

    def test_record_multiple_errors(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """record_error() accumulates multiple errors."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        checkpoint_manager.record_error("node-001", "Error 1")
        checkpoint_manager.record_error("node-002", "Error 2")
        checkpoint_manager.record_error("node-003", "Error 3")

        assert len(checkpoint_manager._errors) == 3

    @pytest.mark.asyncio
    async def test_errors_persisted_in_checkpoint(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
        execution_context: MockExecutionContext,
    ):
        """Recorded errors are persisted in checkpoints."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        checkpoint_manager.record_error("node-001", "First error")

        await checkpoint_manager.save_checkpoint("node-002", execution_context)

        saved = mock_offline_queue._checkpoints["job-001"]["state"]
        assert len(saved["errors"]) == 1
        assert saved["errors"][0]["node_id"] == "node-001"


class TestCheckpointManagerNodeTracking:
    """Tests for executed node tracking."""

    def test_get_executed_nodes_returns_copy(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """get_executed_nodes() returns copy of set."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        checkpoint_manager._executed_nodes.add("node-001")

        result = checkpoint_manager.get_executed_nodes()

        assert result == {"node-001"}
        assert result is not checkpoint_manager._executed_nodes  # Copy

    def test_is_node_executed_returns_true_for_executed(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """is_node_executed() returns True for executed nodes."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        checkpoint_manager._executed_nodes.add("node-001")

        assert checkpoint_manager.is_node_executed("node-001") is True

    def test_is_node_executed_returns_false_for_unexecuted(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """is_node_executed() returns False for unexecuted nodes."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        assert checkpoint_manager.is_node_executed("node-001") is False


class TestCheckpointManagerClearCheckpoints:
    """Tests for checkpoint cleanup."""

    @pytest.mark.asyncio
    async def test_clear_checkpoints_removes_data(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
        execution_context: MockExecutionContext,
    ):
        """clear_checkpoints() removes checkpoint data."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        await checkpoint_manager.save_checkpoint("node-001", execution_context)

        await checkpoint_manager.clear_checkpoints("job-001")

        assert "job-001" not in mock_offline_queue._checkpoints


class TestCheckpointManagerVariableUpdate:
    """Tests for variable tracking updates."""

    def test_update_variable_stores_value(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """update_variable() stores value in internal state."""
        checkpoint_manager.start_job("job-001", "Test Workflow")

        checkpoint_manager.update_variable("key", "value")

        assert checkpoint_manager._variables["key"] == "value"

    def test_update_variable_overwrites_existing(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """update_variable() overwrites existing values."""
        checkpoint_manager.start_job("job-001", "Test Workflow")
        checkpoint_manager.update_variable("key", "old_value")

        checkpoint_manager.update_variable("key", "new_value")

        assert checkpoint_manager._variables["key"] == "new_value"


# --- Edge Cases ---


class TestCheckpointManagerEdgeCases:
    """Edge case tests for checkpoint manager."""

    @pytest.mark.asyncio
    async def test_save_checkpoint_with_empty_context(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """save_checkpoint() handles empty context."""
        context = MockExecutionContext(variables={})
        checkpoint_manager.start_job("job-001", "Test Workflow")

        checkpoint_id = await checkpoint_manager.save_checkpoint("node-001", context)

        assert checkpoint_id is not None

    @pytest.mark.asyncio
    async def test_save_checkpoint_context_without_variables_attr(
        self,
        checkpoint_manager: CheckpointManager,
        mock_offline_queue: MockOfflineQueue,
    ):
        """save_checkpoint() handles context without variables attribute."""
        context = object()  # No variables attribute
        checkpoint_manager.start_job("job-001", "Test Workflow")

        checkpoint_id = await checkpoint_manager.save_checkpoint("node-001", context)

        assert checkpoint_id is not None
        saved = mock_offline_queue._checkpoints["job-001"]["state"]
        assert saved["variables"] == {}

    @pytest.mark.asyncio
    async def test_restore_handles_missing_context_variables(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """restore_from_checkpoint() handles context without variables."""
        checkpoint = create_checkpoint_state(
            job_id="job",
            workflow_name="wf",
            node_id="n1",
            executed_nodes=["n1"],
            variables={"key": "value"},
        )

        class MinimalContext:
            def __init__(self):
                self.variables = {}

        context = MinimalContext()

        result = await checkpoint_manager.restore_from_checkpoint(checkpoint, context)

        assert result is True
        assert context.variables["key"] == "value"

    def test_start_job_with_special_characters(
        self,
        checkpoint_manager: CheckpointManager,
    ):
        """start_job() handles special characters in names."""
        checkpoint_manager.start_job(
            "job-with-special/chars:and;stuff",
            "Workflow with spaces & symbols!",
        )

        assert checkpoint_manager._current_job_id == "job-with-special/chars:and;stuff"
        assert (
            checkpoint_manager._current_workflow_name
            == "Workflow with spaces & symbols!"
        )
