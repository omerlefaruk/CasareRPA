"""Tests for RobotSelectionService domain service.

Domain layer tests - NO mocks. Test pure logic with real objects.
This service is stateless and operates on data passed to methods.

Tests cover:
- select_robot_for_workflow (assignment, auto-selection, capabilities)
- select_robot_for_node (overrides, fallback to workflow selection)
- get_available_robots (filtering by status and capabilities)
- get_robots_by_capability
- calculate_robot_scores
- Edge cases and error conditions
"""

import pytest

from casare_rpa.domain.orchestrator.services.robot_selection_service import (
    RobotSelectionService,
)
from casare_rpa.domain.orchestrator.entities.robot import (
    Robot,
    RobotStatus,
    RobotCapability,
)
from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.domain.orchestrator.errors import (
    NoAvailableRobotError,
    RobotNotFoundError,
)


# Helper functions to create test data
def create_robot(
    robot_id: str,
    name: str = None,
    status: RobotStatus = RobotStatus.ONLINE,
    max_jobs: int = 3,
    current_jobs: int = 0,
    capabilities: set = None,
) -> Robot:
    """Helper to create Robot instances for tests."""
    if name is None:
        name = f"Robot {robot_id}"
    if capabilities is None:
        capabilities = set()

    job_ids = [f"job-{i}" for i in range(current_jobs)]
    return Robot(
        id=robot_id,
        name=name,
        status=status,
        max_concurrent_jobs=max_jobs,
        current_job_ids=job_ids,
        capabilities=capabilities,
    )


class TestRobotSelectionServiceWorkflowSelection:
    """Tests for select_robot_for_workflow method."""

    def setup_method(self):
        """Set up service for each test."""
        self.service = RobotSelectionService()

    def test_select_assigned_robot_when_available(self):
        """Should use assigned robot when it's available."""
        robots = [
            create_robot("robot-1", current_jobs=0),
            create_robot("robot-2", current_jobs=1),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-2")]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-2"

    def test_auto_select_when_no_assignment(self):
        """Should auto-select least loaded robot when no assignment."""
        robots = [
            create_robot("robot-1", current_jobs=2),  # 67% loaded
            create_robot("robot-2", current_jobs=0),  # 0% loaded
            create_robot("robot-3", current_jobs=1),  # 33% loaded
        ]
        assignments = []

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-2"  # Least loaded

    def test_auto_select_when_assigned_robot_unavailable(self):
        """Should auto-select when assigned robot is at capacity."""
        robots = [
            create_robot("robot-1", current_jobs=3, max_jobs=3),  # At capacity
            create_robot("robot-2", current_jobs=1),  # Available
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-2"

    def test_auto_select_when_assigned_robot_offline(self):
        """Should auto-select when assigned robot is offline."""
        robots = [
            create_robot("robot-1", status=RobotStatus.OFFLINE),
            create_robot("robot-2", status=RobotStatus.ONLINE),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-2"

    def test_raise_error_when_assigned_robot_not_found(self):
        """Should raise RobotNotFoundError when assigned robot doesn't exist."""
        robots = [
            create_robot("robot-1"),
        ]
        assignments = [
            RobotAssignment(workflow_id="wf-123", robot_id="robot-nonexistent")
        ]

        with pytest.raises(RobotNotFoundError, match="not found"):
            self.service.select_robot_for_workflow(
                workflow_id="wf-123",
                robots=robots,
                assignments=assignments,
            )

    def test_raise_error_when_no_available_robots(self):
        """Should raise NoAvailableRobotError when all robots unavailable."""
        robots = [
            create_robot("robot-1", status=RobotStatus.OFFLINE),
            create_robot("robot-2", status=RobotStatus.BUSY),
            create_robot("robot-3", current_jobs=3, max_jobs=3),
        ]
        assignments = []

        with pytest.raises(NoAvailableRobotError):
            self.service.select_robot_for_workflow(
                workflow_id="wf-123",
                robots=robots,
                assignments=assignments,
            )

    def test_select_with_required_capabilities(self):
        """Should only consider robots with required capabilities."""
        robots = [
            create_robot("robot-1", current_jobs=0),  # No capabilities
            create_robot(
                "robot-2",
                current_jobs=1,
                capabilities={RobotCapability.GPU},
            ),
            create_robot(
                "robot-3",
                current_jobs=2,
                capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
            ),
        ]
        assignments = []

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
            required_capabilities={RobotCapability.GPU},
        )

        assert result == "robot-2"  # Least loaded with GPU

    def test_fallback_when_assigned_lacks_capabilities(self):
        """Should fallback when assigned robot lacks required capabilities."""
        robots = [
            create_robot("robot-1", capabilities=set()),  # Assigned but no GPU
            create_robot("robot-2", capabilities={RobotCapability.GPU}),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
            required_capabilities={RobotCapability.GPU},
        )

        assert result == "robot-2"

    def test_use_assignment_with_highest_priority(self):
        """Should prefer assignment with highest priority."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
            create_robot("robot-3"),
        ]
        assignments = [
            RobotAssignment(workflow_id="wf-123", robot_id="robot-1", priority=1),
            RobotAssignment(workflow_id="wf-123", robot_id="robot-2", priority=10),
            RobotAssignment(workflow_id="wf-123", robot_id="robot-3", priority=5),
        ]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-2"  # Highest priority

    def test_prefer_default_assignment(self):
        """Should prefer is_default=True assignments."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [
            RobotAssignment(
                workflow_id="wf-123",
                robot_id="robot-1",
                is_default=False,
                priority=100,
            ),
            RobotAssignment(
                workflow_id="wf-123",
                robot_id="robot-2",
                is_default=True,
                priority=1,
            ),
        ]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-2"  # Default takes precedence


class TestRobotSelectionServiceNodeSelection:
    """Tests for select_robot_for_node method."""

    def setup_method(self):
        """Set up service for each test."""
        self.service = RobotSelectionService()

    def test_use_node_override_specific_robot(self):
        """Should use node override when targeting specific robot."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]
        overrides = [
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-456",
                robot_id="robot-2",
                is_active=True,
            )
        ]

        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",
            robots=robots,
            assignments=assignments,
            overrides=overrides,
        )

        assert result == "robot-2"  # Override takes precedence

    def test_ignore_inactive_override(self):
        """Should ignore inactive overrides."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]
        overrides = [
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-456",
                robot_id="robot-2",
                is_active=False,  # Inactive
            )
        ]

        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",
            robots=robots,
            assignments=assignments,
            overrides=overrides,
        )

        assert result == "robot-1"  # Falls back to assignment

    def test_use_capability_based_override(self):
        """Should match robot by capability when override specifies caps."""
        robots = [
            create_robot("robot-1"),  # No capabilities
            create_robot("robot-2", capabilities={RobotCapability.GPU}),
            create_robot(
                "robot-3",
                capabilities={RobotCapability.GPU, RobotCapability.DESKTOP},
            ),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]
        overrides = [
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-456",
                required_capabilities=frozenset({RobotCapability.GPU}),
                is_active=True,
            )
        ]

        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",
            robots=robots,
            assignments=assignments,
            overrides=overrides,
        )

        # Should select robot with GPU, not workflow default
        assert result in ("robot-2", "robot-3")

    def test_fallback_to_workflow_when_no_override(self):
        """Should fall back to workflow selection when no node override."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]
        overrides = []

        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",
            robots=robots,
            assignments=assignments,
            overrides=overrides,
        )

        assert result == "robot-1"

    def test_raise_error_when_override_robot_not_found(self):
        """Should raise error when override references nonexistent robot."""
        robots = [
            create_robot("robot-1"),
        ]
        assignments = []
        overrides = [
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-456",
                robot_id="robot-nonexistent",
                is_active=True,
            )
        ]

        with pytest.raises(RobotNotFoundError, match="not found"):
            self.service.select_robot_for_node(
                workflow_id="wf-123",
                node_id="node-456",
                robots=robots,
                assignments=assignments,
                overrides=overrides,
            )

    def test_fallback_when_override_robot_unavailable(self):
        """Should fallback when override robot is at capacity."""
        robots = [
            create_robot("robot-1"),  # Available
            create_robot("robot-2", current_jobs=3, max_jobs=3),  # At capacity
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]
        overrides = [
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-456",
                robot_id="robot-2",  # At capacity
                required_capabilities=frozenset(),  # Will fallback
                is_active=True,
            )
        ]

        # Override robot is unavailable, but override has no capabilities
        # So it should fall back to workflow selection
        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",
            robots=robots,
            assignments=assignments,
            overrides=overrides,
        )

        assert result == "robot-1"

    def test_override_for_wrong_node_ignored(self):
        """Should ignore override for different node."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]
        overrides = [
            NodeRobotOverride(
                workflow_id="wf-123",
                node_id="node-OTHER",  # Different node
                robot_id="robot-2",
                is_active=True,
            )
        ]

        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",  # Our node
            robots=robots,
            assignments=assignments,
            overrides=overrides,
        )

        assert result == "robot-1"  # Uses workflow default


class TestRobotSelectionServiceAvailableRobots:
    """Tests for get_available_robots method."""

    def setup_method(self):
        """Set up service for each test."""
        self.service = RobotSelectionService()

    def test_filter_by_online_status(self):
        """Should only return online robots."""
        robots = [
            create_robot("robot-1", status=RobotStatus.ONLINE),
            create_robot("robot-2", status=RobotStatus.OFFLINE),
            create_robot("robot-3", status=RobotStatus.BUSY),
            create_robot("robot-4", status=RobotStatus.ERROR),
            create_robot("robot-5", status=RobotStatus.MAINTENANCE),
        ]

        result = self.service.get_available_robots(robots)

        assert len(result) == 1
        assert result[0].id == "robot-1"

    def test_filter_by_capacity(self):
        """Should exclude robots at capacity."""
        robots = [
            create_robot("robot-1", current_jobs=0, max_jobs=3),
            create_robot("robot-2", current_jobs=3, max_jobs=3),  # At capacity
            create_robot("robot-3", current_jobs=2, max_jobs=3),
        ]

        result = self.service.get_available_robots(robots)

        assert len(result) == 2
        ids = [r.id for r in result]
        assert "robot-1" in ids
        assert "robot-3" in ids
        assert "robot-2" not in ids

    def test_filter_by_capabilities(self):
        """Should filter by required capabilities."""
        robots = [
            create_robot("robot-1", capabilities=set()),
            create_robot("robot-2", capabilities={RobotCapability.GPU}),
            create_robot(
                "robot-3",
                capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
            ),
        ]

        result = self.service.get_available_robots(
            robots,
            required_capabilities={RobotCapability.GPU},
        )

        assert len(result) == 2
        ids = [r.id for r in result]
        assert "robot-2" in ids
        assert "robot-3" in ids

    def test_filter_by_multiple_capabilities(self):
        """Should require all specified capabilities."""
        robots = [
            create_robot("robot-1", capabilities={RobotCapability.GPU}),
            create_robot("robot-2", capabilities={RobotCapability.BROWSER}),
            create_robot(
                "robot-3",
                capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
            ),
        ]

        result = self.service.get_available_robots(
            robots,
            required_capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
        )

        assert len(result) == 1
        assert result[0].id == "robot-3"

    def test_sorted_by_utilization(self):
        """Should return robots sorted by utilization (lowest first)."""
        robots = [
            create_robot("robot-1", current_jobs=2, max_jobs=3),  # 67%
            create_robot("robot-2", current_jobs=0, max_jobs=3),  # 0%
            create_robot("robot-3", current_jobs=1, max_jobs=3),  # 33%
        ]

        result = self.service.get_available_robots(robots)

        assert result[0].id == "robot-2"  # 0% - lowest
        assert result[1].id == "robot-3"  # 33%
        assert result[2].id == "robot-1"  # 67% - highest

    def test_empty_robots_returns_empty(self):
        """Should return empty list when no robots provided."""
        result = self.service.get_available_robots([])

        assert result == []


class TestRobotSelectionServiceRobotsByCapability:
    """Tests for get_robots_by_capability method."""

    def setup_method(self):
        """Set up service for each test."""
        self.service = RobotSelectionService()

    def test_filter_by_single_capability(self):
        """Should return robots with specific capability."""
        robots = [
            create_robot("robot-1", capabilities=set()),
            create_robot("robot-2", capabilities={RobotCapability.GPU}),
            create_robot(
                "robot-3",
                capabilities={RobotCapability.GPU, RobotCapability.DESKTOP},
            ),
        ]

        result = self.service.get_robots_by_capability(
            robots,
            capability=RobotCapability.GPU,
        )

        assert len(result) == 2
        ids = [r.id for r in result]
        assert "robot-2" in ids
        assert "robot-3" in ids

    def test_filter_available_only_true(self):
        """Should only return available robots when available_only=True."""
        robots = [
            create_robot(
                "robot-1",
                status=RobotStatus.ONLINE,
                capabilities={RobotCapability.GPU},
            ),
            create_robot(
                "robot-2",
                status=RobotStatus.OFFLINE,
                capabilities={RobotCapability.GPU},
            ),
        ]

        result = self.service.get_robots_by_capability(
            robots,
            capability=RobotCapability.GPU,
            available_only=True,
        )

        assert len(result) == 1
        assert result[0].id == "robot-1"

    def test_filter_available_only_false(self):
        """Should return all matching robots when available_only=False."""
        robots = [
            create_robot(
                "robot-1",
                status=RobotStatus.ONLINE,
                capabilities={RobotCapability.GPU},
            ),
            create_robot(
                "robot-2",
                status=RobotStatus.OFFLINE,
                capabilities={RobotCapability.GPU},
            ),
        ]

        result = self.service.get_robots_by_capability(
            robots,
            capability=RobotCapability.GPU,
            available_only=False,
        )

        assert len(result) == 2


class TestRobotSelectionServiceScoring:
    """Tests for calculate_robot_scores method."""

    def setup_method(self):
        """Set up service for each test."""
        self.service = RobotSelectionService()

    def test_available_robot_gets_base_score(self):
        """Available robot should get 100 base score."""
        robots = [
            create_robot("robot-1", status=RobotStatus.ONLINE, current_jobs=0),
        ]

        scores = self.service.calculate_robot_scores(
            robots=robots,
            workflow_id="wf-123",
            assignments=[],
        )

        # Available (100) + Load factor (30 * 1.0 = 30) = 130
        assert scores["robot-1"] >= 100

    def test_unavailable_robot_gets_zero_score(self):
        """Unavailable robot should get 0 score."""
        robots = [
            create_robot("robot-1", status=RobotStatus.OFFLINE),
        ]

        scores = self.service.calculate_robot_scores(
            robots=robots,
            workflow_id="wf-123",
            assignments=[],
        )

        assert scores["robot-1"] == 0

    def test_assigned_robot_gets_bonus(self):
        """Assigned robot should get +50 bonus."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-2")]

        scores = self.service.calculate_robot_scores(
            robots=robots,
            workflow_id="wf-123",
            assignments=assignments,
        )

        # robot-2 should score higher due to assignment bonus
        assert scores["robot-2"] > scores["robot-1"]

    def test_capability_matching_bonus(self):
        """Matching capabilities should increase score."""
        robots = [
            create_robot("robot-1", capabilities=set()),
            create_robot("robot-2", capabilities={RobotCapability.GPU}),
            create_robot(
                "robot-3",
                capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
            ),
        ]

        scores = self.service.calculate_robot_scores(
            robots=robots,
            workflow_id="wf-123",
            assignments=[],
            required_capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
        )

        # robot-3 has both caps, robot-2 has one, robot-1 has none
        assert scores["robot-3"] > scores["robot-2"] > scores["robot-1"]

    def test_lower_utilization_higher_score(self):
        """Less loaded robots should score higher."""
        robots = [
            create_robot("robot-1", current_jobs=0, max_jobs=3),  # 0%
            create_robot("robot-2", current_jobs=2, max_jobs=3),  # 67%
        ]

        scores = self.service.calculate_robot_scores(
            robots=robots,
            workflow_id="wf-123",
            assignments=[],
        )

        assert scores["robot-1"] > scores["robot-2"]


class TestRobotSelectionServiceEdgeCases:
    """Edge case tests for RobotSelectionService."""

    def setup_method(self):
        """Set up service for each test."""
        self.service = RobotSelectionService()

    def test_single_robot_available(self):
        """Should work with single available robot."""
        robots = [create_robot("robot-1")]
        assignments = []

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        assert result == "robot-1"

    def test_empty_assignments_list(self):
        """Should handle empty assignments list."""
        robots = [create_robot("robot-1")]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=[],
        )

        assert result == "robot-1"

    def test_empty_overrides_list(self):
        """Should handle empty overrides list."""
        robots = [create_robot("robot-1")]
        assignments = [RobotAssignment(workflow_id="wf-123", robot_id="robot-1")]

        result = self.service.select_robot_for_node(
            workflow_id="wf-123",
            node_id="node-456",
            robots=robots,
            assignments=assignments,
            overrides=[],
        )

        assert result == "robot-1"

    def test_select_least_loaded_empty_list_raises(self):
        """_select_least_loaded should raise on empty list."""
        with pytest.raises(NoAvailableRobotError):
            self.service._select_least_loaded([])

    def test_assignment_for_different_workflow_ignored(self):
        """Assignments for other workflows should be ignored."""
        robots = [
            create_robot("robot-1"),
            create_robot("robot-2"),
        ]
        assignments = [RobotAssignment(workflow_id="wf-OTHER", robot_id="robot-2")]

        # No assignment for wf-123, so auto-select least loaded
        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=assignments,
        )

        # Should auto-select, both have 0 jobs so either is valid
        assert result in ("robot-1", "robot-2")

    def test_all_robots_at_capacity_raises_error(self):
        """Should raise when all robots are at capacity."""
        robots = [
            create_robot("robot-1", current_jobs=3, max_jobs=3),
            create_robot("robot-2", current_jobs=3, max_jobs=3),
        ]

        with pytest.raises(NoAvailableRobotError):
            self.service.select_robot_for_workflow(
                workflow_id="wf-123",
                robots=robots,
                assignments=[],
            )

    def test_no_robots_raises_error(self):
        """Should raise when no robots provided."""
        with pytest.raises(NoAvailableRobotError):
            self.service.select_robot_for_workflow(
                workflow_id="wf-123",
                robots=[],
                assignments=[],
            )

    def test_robot_with_zero_max_jobs(self):
        """Robot with max_concurrent_jobs=0 should not be selected."""
        robots = [
            create_robot("robot-1", max_jobs=0),  # Can never accept jobs
            create_robot("robot-2", max_jobs=1),
        ]

        result = self.service.select_robot_for_workflow(
            workflow_id="wf-123",
            robots=robots,
            assignments=[],
        )

        assert result == "robot-2"
