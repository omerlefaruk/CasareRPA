"""Tests for NodeRobotOverride value object.

Domain layer tests - NO mocks. Test pure logic with real objects.
Tests cover:
- Creation with robot_id vs capability-based overrides
- Validation of invariants
- Immutability (frozen dataclass)
- Properties: is_specific_robot, is_capability_based
- Serialization (to_dict/from_dict)
- Edge cases
"""

from datetime import datetime

import pytest

from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.domain.orchestrator.entities.robot import RobotCapability


class TestNodeRobotOverrideCreation:
    """Tests for NodeRobotOverride creation."""

    def test_create_with_specific_robot(self):
        """Create override targeting a specific robot."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )

        assert override.workflow_id == "wf-123"
        assert override.node_id == "node-456"
        assert override.robot_id == "robot-789"
        assert override.required_capabilities == frozenset()
        assert override.is_active is True

    def test_create_with_required_capabilities(self):
        """Create override with capability requirements."""
        capabilities = frozenset({RobotCapability.GPU, RobotCapability.BROWSER})
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=capabilities,
        )

        assert override.workflow_id == "wf-123"
        assert override.node_id == "node-456"
        assert override.robot_id is None
        assert override.required_capabilities == capabilities
        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.BROWSER in override.required_capabilities

    def test_create_with_all_fields(self):
        """Create override with all fields specified."""
        created_at = datetime(2025, 1, 15, 10, 30, 0)
        capabilities = frozenset({RobotCapability.DESKTOP})
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            required_capabilities=capabilities,
            reason="Requires desktop automation on secure machine",
            created_at=created_at,
            created_by="admin",
            is_active=True,
        )

        assert override.workflow_id == "wf-123"
        assert override.node_id == "node-456"
        assert override.robot_id == "robot-789"
        assert override.required_capabilities == capabilities
        assert override.reason == "Requires desktop automation on secure machine"
        assert override.created_at == created_at
        assert override.created_by == "admin"
        assert override.is_active is True


class TestNodeRobotOverrideValidation:
    """Tests for NodeRobotOverride validation invariants."""

    def test_empty_workflow_id_raises_error(self):
        """Empty workflow_id should raise ValueError."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            NodeRobotOverride(
                workflow_id="",
                node_id="node-456",
                robot_id="robot-789",
            )

    def test_whitespace_workflow_id_raises_error(self):
        """Whitespace-only workflow_id should raise ValueError."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            NodeRobotOverride(
                workflow_id="   ",
                node_id="node-456",
                robot_id="robot-789",
            )

    def test_empty_node_id_raises_error(self):
        """Empty node_id should raise ValueError."""
        with pytest.raises(ValueError, match="node_id cannot be empty"):
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="",
                robot_id="robot-789",
            )

    def test_whitespace_node_id_raises_error(self):
        """Whitespace-only node_id should raise ValueError."""
        with pytest.raises(ValueError, match="node_id cannot be empty"):
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="\t\n",
                robot_id="robot-789",
            )

    def test_no_robot_id_and_no_capabilities_raises_error(self):
        """Must specify either robot_id or required_capabilities."""
        with pytest.raises(
            ValueError,
            match="Must specify either robot_id or required_capabilities",
        ):
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-456",
                robot_id=None,
                required_capabilities=frozenset(),
            )

    def test_robot_id_only_is_valid(self):
        """Override with only robot_id should be valid."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )
        assert override.robot_id == "robot-789"

    def test_capabilities_only_is_valid(self):
        """Override with only capabilities should be valid."""
        capabilities = frozenset({RobotCapability.GPU})
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=capabilities,
        )
        assert override.required_capabilities == capabilities


class TestNodeRobotOverrideProperties:
    """Tests for NodeRobotOverride computed properties."""

    def test_is_specific_robot_true_when_robot_id_set(self):
        """is_specific_robot should be True when robot_id is specified."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )

        assert override.is_specific_robot is True

    def test_is_specific_robot_false_when_capability_based(self):
        """is_specific_robot should be False for capability-based override."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=frozenset({RobotCapability.GPU}),
        )

        assert override.is_specific_robot is False

    def test_is_capability_based_true_when_no_robot_id(self):
        """is_capability_based should be True when using capability matching."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=frozenset({RobotCapability.BROWSER}),
        )

        assert override.is_capability_based is True

    def test_is_capability_based_false_when_specific_robot(self):
        """is_capability_based should be False for specific robot override."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )

        assert override.is_capability_based is False

    def test_both_robot_id_and_capabilities_uses_robot_id(self):
        """When both robot_id and capabilities set, is_specific_robot takes precedence."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            required_capabilities=frozenset({RobotCapability.GPU}),
        )

        assert override.is_specific_robot is True
        # Note: is_capability_based is False because robot_id is set
        assert override.is_capability_based is False


class TestNodeRobotOverrideImmutability:
    """Tests for NodeRobotOverride immutability (frozen dataclass)."""

    def test_cannot_modify_workflow_id(self):
        """workflow_id should be immutable."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )

        with pytest.raises(AttributeError):
            override.workflow_id = "wf-modified"  # type: ignore

    def test_cannot_modify_node_id(self):
        """node_id should be immutable."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )

        with pytest.raises(AttributeError):
            override.node_id = "node-modified"  # type: ignore

    def test_cannot_modify_is_active(self):
        """is_active should be immutable."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            is_active=True,
        )

        with pytest.raises(AttributeError):
            override.is_active = False  # type: ignore


class TestNodeRobotOverrideEquality:
    """Tests for NodeRobotOverride equality comparison."""

    def test_equal_overrides_are_equal(self):
        """Overrides with same values should be equal."""
        created_at = datetime(2025, 1, 15, 10, 30, 0)
        capabilities = frozenset({RobotCapability.GPU})

        o1 = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            required_capabilities=capabilities,
            reason="test",
            created_at=created_at,
            created_by="admin",
            is_active=True,
        )
        o2 = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            required_capabilities=capabilities,
            reason="test",
            created_at=created_at,
            created_by="admin",
            is_active=True,
        )

        assert o1 == o2

    def test_different_node_ids_not_equal(self):
        """Overrides with different node_ids should not be equal."""
        o1 = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )
        o2 = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-999",
            robot_id="robot-789",
        )

        assert o1 != o2

    def test_can_be_used_in_set(self):
        """Override should be hashable and usable in sets."""
        o1 = NodeRobotOverride(
            workflow_id="wf-1",
            node_id="node-1",
            robot_id="robot-1",
        )
        o2 = NodeRobotOverride(
            workflow_id="wf-2",
            node_id="node-2",
            robot_id="robot-2",
        )

        override_set = {o1, o2}
        assert len(override_set) == 2


class TestNodeRobotOverrideSerialization:
    """Tests for NodeRobotOverride serialization."""

    def test_to_dict_with_robot_id(self):
        """to_dict should serialize specific robot override."""
        created_at = datetime(2025, 1, 15, 10, 30, 0)
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            reason="Must use specific robot",
            created_at=created_at,
            created_by="admin",
            is_active=True,
        )

        result = override.to_dict()

        assert result["workflow_id"] == "wf-123"
        assert result["node_id"] == "node-456"
        assert result["robot_id"] == "robot-789"
        assert result["required_capabilities"] == []
        assert result["reason"] == "Must use specific robot"
        assert result["created_at"] == "2025-01-15T10:30:00"
        assert result["created_by"] == "admin"
        assert result["is_active"] is True

    def test_to_dict_with_capabilities(self):
        """to_dict should serialize capability-based override."""
        capabilities = frozenset({RobotCapability.GPU, RobotCapability.BROWSER})
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=capabilities,
        )

        result = override.to_dict()

        assert result["robot_id"] is None
        # Capabilities serialized as strings
        assert set(result["required_capabilities"]) == {"gpu", "browser"}

    def test_from_dict_with_robot_id(self):
        """from_dict should deserialize specific robot override."""
        data = {
            "workflow_id": "wf-123",
            "node_id": "node-456",
            "robot_id": "robot-789",
            "required_capabilities": [],
            "reason": "Test reason",
            "created_at": "2025-01-15T10:30:00",
            "created_by": "admin",
            "is_active": True,
        }

        override = NodeRobotOverride.from_dict(data)

        assert override.workflow_id == "wf-123"
        assert override.node_id == "node-456"
        assert override.robot_id == "robot-789"
        assert override.required_capabilities == frozenset()
        assert override.reason == "Test reason"
        assert override.created_at == datetime(2025, 1, 15, 10, 30, 0)
        assert override.created_by == "admin"
        assert override.is_active is True

    def test_from_dict_with_capabilities(self):
        """from_dict should deserialize capability-based override."""
        data = {
            "workflow_id": "wf-123",
            "node_id": "node-456",
            "required_capabilities": ["gpu", "browser"],
        }

        override = NodeRobotOverride.from_dict(data)

        assert override.robot_id is None
        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.BROWSER in override.required_capabilities

    def test_from_dict_ignores_unknown_capabilities(self):
        """from_dict should skip unknown capability strings."""
        data = {
            "workflow_id": "wf-123",
            "node_id": "node-456",
            "required_capabilities": ["gpu", "unknown_cap", "browser"],
        }

        override = NodeRobotOverride.from_dict(data)

        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.BROWSER in override.required_capabilities
        assert len(override.required_capabilities) == 2

    def test_from_dict_handles_enum_capabilities(self):
        """from_dict should handle RobotCapability enum values."""
        data = {
            "workflow_id": "wf-123",
            "node_id": "node-456",
            "required_capabilities": [RobotCapability.GPU, RobotCapability.SECURE],
        }

        override = NodeRobotOverride.from_dict(data)

        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.SECURE in override.required_capabilities

    def test_from_dict_minimal(self):
        """from_dict should handle minimal data with robot_id."""
        data = {
            "workflow_id": "wf-123",
            "node_id": "node-456",
            "robot_id": "robot-789",
        }

        override = NodeRobotOverride.from_dict(data)

        assert override.workflow_id == "wf-123"
        assert override.node_id == "node-456"
        assert override.robot_id == "robot-789"
        assert override.is_active is True
        assert override.created_by == ""
        assert override.reason is None

    def test_from_dict_none_created_at_uses_utcnow(self):
        """from_dict should use utcnow when created_at is None."""
        data = {
            "workflow_id": "wf-123",
            "node_id": "node-456",
            "robot_id": "robot-789",
            "created_at": None,
        }

        before = datetime.utcnow()
        override = NodeRobotOverride.from_dict(data)
        after = datetime.utcnow()

        assert before <= override.created_at <= after

    def test_round_trip_serialization_robot_id(self):
        """Override with robot_id should survive round-trip."""
        original = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            reason="Test reason",
            created_at=datetime(2025, 1, 15, 10, 30, 0),
            created_by="test",
            is_active=False,
        )

        restored = NodeRobotOverride.from_dict(original.to_dict())

        assert original == restored

    def test_round_trip_serialization_capabilities(self):
        """Override with capabilities should survive round-trip."""
        capabilities = frozenset({RobotCapability.GPU, RobotCapability.DESKTOP})
        original = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=capabilities,
            reason="Needs GPU and desktop",
            created_at=datetime(2025, 1, 15, 10, 30, 0),
            created_by="test",
            is_active=True,
        )

        restored = NodeRobotOverride.from_dict(original.to_dict())

        assert original == restored


class TestNodeRobotOverrideRepr:
    """Tests for NodeRobotOverride string representation."""

    def test_repr_with_robot_id(self):
        """__repr__ should show robot_id for specific robot override."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
        )

        result = repr(override)

        assert "wf-123" in result
        assert "node-456" in result
        assert "robot-789" in result

    def test_repr_with_capabilities(self):
        """__repr__ should show capabilities for capability-based override."""
        capabilities = frozenset({RobotCapability.GPU})
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=capabilities,
        )

        result = repr(override)

        assert "wf-123" in result
        assert "node-456" in result
        assert "caps:" in result


class TestNodeRobotOverrideEdgeCases:
    """Edge case tests for NodeRobotOverride."""

    def test_inactive_override(self):
        """Create and verify inactive override."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            robot_id="robot-789",
            is_active=False,
        )

        assert override.is_active is False

    def test_single_capability(self):
        """Override with single capability."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=frozenset({RobotCapability.SECURE}),
        )

        assert len(override.required_capabilities) == 1
        assert RobotCapability.SECURE in override.required_capabilities

    def test_all_capabilities(self):
        """Override requiring all capabilities."""
        all_caps = frozenset(RobotCapability)
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-456",
            required_capabilities=all_caps,
        )

        assert override.required_capabilities == all_caps
        assert len(override.required_capabilities) == len(RobotCapability)
