"""Tests for RobotAssignment value object.

Domain layer tests - NO mocks. Test pure logic with real objects.
Tests cover:
- Creation with valid/invalid data
- Immutability (frozen dataclass)
- Validation of invariants
- Serialization (to_dict/from_dict)
- Edge cases
"""

from datetime import datetime

import pytest

from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)


class TestRobotAssignmentCreation:
    """Tests for RobotAssignment creation and validation."""

    def test_create_with_required_fields(self):
        """Create assignment with only required fields."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
        )

        assert assignment.workflow_id == "wf-123"
        assert assignment.robot_id == "robot-456"
        assert assignment.is_default is True
        assert assignment.priority == 0
        assert assignment.created_by == ""
        assert assignment.notes is None

    def test_create_with_all_fields(self):
        """Create assignment with all fields specified."""
        created_at = datetime(2025, 1, 15, 10, 30, 0)
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=False,
            priority=10,
            created_at=created_at,
            created_by="admin",
            notes="Special assignment for testing",
        )

        assert assignment.workflow_id == "wf-123"
        assert assignment.robot_id == "robot-456"
        assert assignment.is_default is False
        assert assignment.priority == 10
        assert assignment.created_at == created_at
        assert assignment.created_by == "admin"
        assert assignment.notes == "Special assignment for testing"

    def test_create_with_high_priority(self):
        """Create assignment with high priority value."""
        assignment = RobotAssignment(
            workflow_id="wf-1",
            robot_id="robot-1",
            priority=100,
        )

        assert assignment.priority == 100


class TestRobotAssignmentValidation:
    """Tests for RobotAssignment validation invariants."""

    def test_empty_workflow_id_raises_error(self):
        """Empty workflow_id should raise ValueError."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            RobotAssignment(
                workflow_id="",
                robot_id="robot-456",
            )

    def test_whitespace_workflow_id_raises_error(self):
        """Whitespace-only workflow_id should raise ValueError."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            RobotAssignment(
                workflow_id="   ",
                robot_id="robot-456",
            )

    def test_empty_robot_id_raises_error(self):
        """Empty robot_id should raise ValueError."""
        with pytest.raises(ValueError, match="robot_id cannot be empty"):
            RobotAssignment(
                workflow_id="wf-123",
                robot_id="",
            )

    def test_whitespace_robot_id_raises_error(self):
        """Whitespace-only robot_id should raise ValueError."""
        with pytest.raises(ValueError, match="robot_id cannot be empty"):
            RobotAssignment(
                workflow_id="wf-123",
                robot_id="  \t  ",
            )

    def test_negative_priority_raises_error(self):
        """Negative priority should raise ValueError."""
        with pytest.raises(ValueError, match="priority must be >= 0"):
            RobotAssignment(
                workflow_id="wf-123",
                robot_id="robot-456",
                priority=-1,
            )

    def test_zero_priority_is_valid(self):
        """Zero priority should be valid."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            priority=0,
        )
        assert assignment.priority == 0


class TestRobotAssignmentImmutability:
    """Tests for RobotAssignment immutability (frozen dataclass)."""

    def test_cannot_modify_workflow_id(self):
        """workflow_id should be immutable."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
        )

        with pytest.raises(AttributeError):
            assignment.workflow_id = "wf-modified"  # type: ignore

    def test_cannot_modify_robot_id(self):
        """robot_id should be immutable."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
        )

        with pytest.raises(AttributeError):
            assignment.robot_id = "robot-modified"  # type: ignore

    def test_cannot_modify_priority(self):
        """priority should be immutable."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            priority=5,
        )

        with pytest.raises(AttributeError):
            assignment.priority = 10  # type: ignore


class TestRobotAssignmentEquality:
    """Tests for RobotAssignment equality comparison."""

    def test_equal_assignments_are_equal(self):
        """Assignments with same values should be equal."""
        created_at = datetime(2025, 1, 15, 10, 30, 0)
        a1 = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=True,
            priority=5,
            created_at=created_at,
            created_by="admin",
            notes="test",
        )
        a2 = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=True,
            priority=5,
            created_at=created_at,
            created_by="admin",
            notes="test",
        )

        assert a1 == a2

    def test_different_workflow_ids_not_equal(self):
        """Assignments with different workflow_ids should not be equal."""
        a1 = RobotAssignment(workflow_id="wf-123", robot_id="robot-456")
        a2 = RobotAssignment(workflow_id="wf-999", robot_id="robot-456")

        assert a1 != a2

    def test_different_robot_ids_not_equal(self):
        """Assignments with different robot_ids should not be equal."""
        a1 = RobotAssignment(workflow_id="wf-123", robot_id="robot-456")
        a2 = RobotAssignment(workflow_id="wf-123", robot_id="robot-999")

        assert a1 != a2

    def test_can_be_used_in_set(self):
        """Assignment should be hashable and usable in sets."""
        a1 = RobotAssignment(workflow_id="wf-1", robot_id="robot-1")
        a2 = RobotAssignment(workflow_id="wf-2", robot_id="robot-2")

        assignment_set = {a1, a2}
        assert len(assignment_set) == 2


class TestRobotAssignmentSerialization:
    """Tests for RobotAssignment serialization."""

    def test_to_dict_full(self):
        """to_dict should serialize all fields correctly."""
        created_at = datetime(2025, 1, 15, 10, 30, 0)
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=False,
            priority=10,
            created_at=created_at,
            created_by="admin",
            notes="Important assignment",
        )

        result = assignment.to_dict()

        assert result["workflow_id"] == "wf-123"
        assert result["robot_id"] == "robot-456"
        assert result["is_default"] is False
        assert result["priority"] == 10
        assert result["created_at"] == "2025-01-15T10:30:00"
        assert result["created_by"] == "admin"
        assert result["notes"] == "Important assignment"

    def test_to_dict_minimal(self):
        """to_dict should handle minimal assignment."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
        )

        result = assignment.to_dict()

        assert result["workflow_id"] == "wf-123"
        assert result["robot_id"] == "robot-456"
        assert result["is_default"] is True
        assert result["priority"] == 0
        assert result["created_by"] == ""
        assert result["notes"] is None

    def test_from_dict_full(self):
        """from_dict should deserialize all fields correctly."""
        data = {
            "workflow_id": "wf-123",
            "robot_id": "robot-456",
            "is_default": False,
            "priority": 10,
            "created_at": "2025-01-15T10:30:00",
            "created_by": "admin",
            "notes": "Important assignment",
        }

        assignment = RobotAssignment.from_dict(data)

        assert assignment.workflow_id == "wf-123"
        assert assignment.robot_id == "robot-456"
        assert assignment.is_default is False
        assert assignment.priority == 10
        assert assignment.created_at == datetime(2025, 1, 15, 10, 30, 0)
        assert assignment.created_by == "admin"
        assert assignment.notes == "Important assignment"

    def test_from_dict_minimal(self):
        """from_dict should handle minimal data with defaults."""
        data = {
            "workflow_id": "wf-123",
            "robot_id": "robot-456",
        }

        assignment = RobotAssignment.from_dict(data)

        assert assignment.workflow_id == "wf-123"
        assert assignment.robot_id == "robot-456"
        assert assignment.is_default is True
        assert assignment.priority == 0
        assert assignment.created_by == ""
        assert assignment.notes is None

    def test_from_dict_none_created_at_uses_utcnow(self):
        """from_dict should use utcnow when created_at is None."""
        data = {
            "workflow_id": "wf-123",
            "robot_id": "robot-456",
            "created_at": None,
        }

        before = datetime.utcnow()
        assignment = RobotAssignment.from_dict(data)
        after = datetime.utcnow()

        assert before <= assignment.created_at <= after

    def test_round_trip_serialization(self):
        """Assignment should survive round-trip serialization."""
        original = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=False,
            priority=5,
            created_at=datetime(2025, 1, 15, 10, 30, 0),
            created_by="test",
            notes="Round trip test",
        )

        restored = RobotAssignment.from_dict(original.to_dict())

        assert original == restored


class TestRobotAssignmentRepr:
    """Tests for RobotAssignment string representation."""

    def test_repr_shows_key_fields(self):
        """__repr__ should show workflow_id, robot_id, and is_default."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=True,
        )

        result = repr(assignment)

        assert "wf-123" in result
        assert "robot-456" in result
        assert "is_default=True" in result

    def test_repr_shows_false_default(self):
        """__repr__ should correctly show is_default=False."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=False,
        )

        result = repr(assignment)

        assert "is_default=False" in result
