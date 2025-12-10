"""RobotSelectionService - Pure domain service for robot selection logic.

This is a PURE domain service with NO infrastructure dependencies:
- NO async/await
- NO database access
- NO external APIs
- NO I/O operations

All robot data and assignments must be passed in as parameters.
"""

from typing import List, Optional, Set, Dict
import logging

logger = logging.getLogger(__name__)

from casare_rpa.domain.orchestrator.entities.robot import Robot, RobotCapability
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


class RobotSelectionService:
    """Domain service for selecting robots for workflow/node execution.

    Selection priority (highest to lowest):
    1. Node-level override (if exists and active)
    2. Workflow default assignment
    3. Auto-selection (least loaded available robot with required capabilities)

    This service is stateless and operates on data passed to its methods.
    All I/O (fetching robots, assignments) happens in the application layer.
    """

    def select_robot_for_workflow(
        self,
        workflow_id: str,
        robots: List[Robot],
        assignments: List[RobotAssignment],
        required_capabilities: Optional[Set[RobotCapability]] = None,
    ) -> str:
        """Select the best robot to execute a workflow.

        Selection logic:
        1. Check for workflow assignment (default robot)
        2. If assigned robot is available, use it
        3. Otherwise, auto-select based on availability and capabilities

        Args:
            workflow_id: ID of the workflow to execute.
            robots: List of all robots to consider.
            assignments: List of workflow-to-robot assignments.
            required_capabilities: Optional capabilities required for the workflow.

        Returns:
            Robot ID of the selected robot.

        Raises:
            NoAvailableRobotError: If no robot can handle the workflow.
            RobotNotFoundError: If assigned robot doesn't exist.
        """
        logger.debug(f"Selecting robot for workflow {workflow_id}")

        # Step 1: Check for workflow assignment
        assigned_robot_id = self._get_workflow_assignment(workflow_id, assignments)

        if assigned_robot_id:
            logger.debug(f"Found workflow assignment: {assigned_robot_id}")
            robot = self._find_robot_by_id(assigned_robot_id, robots)

            if robot is None:
                raise RobotNotFoundError(
                    f"Assigned robot {assigned_robot_id} not found for workflow {workflow_id}"
                )

            # Check if assigned robot can accept the job
            if robot.can_accept_job():
                # Verify capabilities if required
                if required_capabilities:
                    if robot.has_all_capabilities(required_capabilities):
                        logger.info(
                            f"Using assigned robot {robot.id} for workflow {workflow_id}"
                        )
                        return robot.id
                    else:
                        logger.warning(
                            f"Assigned robot {robot.id} lacks required capabilities, "
                            f"falling back to auto-selection"
                        )
                else:
                    logger.info(
                        f"Using assigned robot {robot.id} for workflow {workflow_id}"
                    )
                    return robot.id
            else:
                logger.warning(
                    f"Assigned robot {robot.id} is unavailable "
                    f"(status={robot.status.value}, jobs={robot.current_jobs}/{robot.max_concurrent_jobs}), "
                    f"falling back to auto-selection"
                )

        # Step 2: Auto-select based on availability
        available_robots = self.get_available_robots(robots, required_capabilities)

        if not available_robots:
            raise NoAvailableRobotError(
                f"No available robots for workflow {workflow_id} "
                f"with capabilities {required_capabilities}"
            )

        # Select least loaded robot
        selected = self._select_least_loaded(available_robots)
        logger.info(f"Auto-selected robot {selected.id} for workflow {workflow_id}")
        return selected.id

    def select_robot_for_node(
        self,
        workflow_id: str,
        node_id: str,
        robots: List[Robot],
        assignments: List[RobotAssignment],
        overrides: List[NodeRobotOverride],
        default_capabilities: Optional[Set[RobotCapability]] = None,
    ) -> str:
        """Select the best robot to execute a specific node.

        Selection priority:
        1. Active node-level override (if exists)
           a. Specific robot override
           b. Capability-based override
        2. Workflow default assignment
        3. Auto-selection

        Args:
            workflow_id: ID of the workflow containing the node.
            node_id: ID of the node to execute.
            robots: List of all robots to consider.
            assignments: List of workflow-to-robot assignments.
            overrides: List of node-level robot overrides.
            default_capabilities: Default capabilities required if no override.

        Returns:
            Robot ID of the selected robot.

        Raises:
            NoAvailableRobotError: If no robot can handle the node.
            RobotNotFoundError: If specified robot doesn't exist.
        """
        logger.debug(f"Selecting robot for node {node_id} in workflow {workflow_id}")

        # Step 1: Check for node-level override
        override = self._get_node_override(workflow_id, node_id, overrides)

        if override and override.is_active:
            logger.debug(f"Found active override for node {node_id}")

            if override.is_specific_robot:
                # Override specifies a specific robot
                robot = self._find_robot_by_id(override.robot_id, robots)
                if robot is None:
                    raise RobotNotFoundError(
                        f"Override robot {override.robot_id} not found for node {node_id}"
                    )
                if robot.can_accept_job():
                    logger.info(
                        f"Using override robot {robot.id} for node {node_id} "
                        f"(reason: {override.reason})"
                    )
                    return robot.id
                else:
                    logger.warning(
                        f"Override robot {robot.id} is unavailable, "
                        f"falling back to capability matching"
                    )

            # Override uses capability matching or specific robot unavailable
            if override.required_capabilities:
                capabilities = set(override.required_capabilities)
            else:
                capabilities = default_capabilities
        else:
            capabilities = default_capabilities

        # Step 2: Fall back to workflow-level selection
        return self.select_robot_for_workflow(
            workflow_id=workflow_id,
            robots=robots,
            assignments=assignments,
            required_capabilities=capabilities,
        )

    def get_available_robots(
        self,
        robots: List[Robot],
        required_capabilities: Optional[Set[RobotCapability]] = None,
    ) -> List[Robot]:
        """Get list of available robots matching required capabilities.

        A robot is available if:
        - Status is ONLINE
        - Has capacity for more jobs (current_jobs < max_concurrent_jobs)
        - Has all required capabilities (if specified)

        Args:
            robots: List of all robots to filter.
            required_capabilities: Optional capabilities to filter by.

        Returns:
            List of available robots sorted by utilization (lowest first).
        """
        available: List[Robot] = []

        for robot in robots:
            if not robot.can_accept_job():
                continue

            if required_capabilities:
                if not robot.has_all_capabilities(required_capabilities):
                    continue

            available.append(robot)

        # Sort by utilization (prefer less loaded robots)
        available.sort(key=lambda r: r.utilization)

        logger.debug(
            f"Found {len(available)} available robots "
            f"(of {len(robots)} total, capabilities={required_capabilities})"
        )
        return available

    def get_robots_by_capability(
        self,
        robots: List[Robot],
        capability: RobotCapability,
        available_only: bool = True,
    ) -> List[Robot]:
        """Get robots that have a specific capability.

        Args:
            robots: List of all robots to filter.
            capability: Capability to filter by.
            available_only: If True, only return available robots.

        Returns:
            List of robots with the capability.
        """
        result: List[Robot] = []

        for robot in robots:
            if not robot.has_capability(capability):
                continue

            if available_only and not robot.can_accept_job():
                continue

            result.append(robot)

        return result

    def calculate_robot_scores(
        self,
        robots: List[Robot],
        workflow_id: str,
        assignments: List[RobotAssignment],
        required_capabilities: Optional[Set[RobotCapability]] = None,
    ) -> Dict[str, float]:
        """Calculate selection scores for robots.

        Scoring factors (higher = better):
        - Availability: +100 if can accept job, 0 otherwise
        - Assignment: +50 if assigned to workflow
        - Capabilities: +20 per matching capability
        - Load: +30 * (1 - utilization/100)
        - Environment match: +10 if same environment

        Args:
            robots: List of robots to score.
            workflow_id: Workflow being assigned.
            assignments: Current assignments.
            required_capabilities: Required capabilities.

        Returns:
            Dictionary mapping robot_id to score.
        """
        scores: Dict[str, float] = {}
        assigned_robot_id = self._get_workflow_assignment(workflow_id, assignments)

        for robot in robots:
            score = 0.0

            # Availability (must-have)
            if robot.can_accept_job():
                score += 100.0
            else:
                scores[robot.id] = score
                continue  # Skip unavailable robots in remaining scoring

            # Assignment bonus
            if robot.id == assigned_robot_id:
                score += 50.0

            # Capability matching
            if required_capabilities:
                matching_caps = robot.capabilities.intersection(required_capabilities)
                score += 20.0 * len(matching_caps)

            # Load factor (prefer less loaded)
            score += 30.0 * (1.0 - robot.utilization / 100.0)

            scores[robot.id] = score

        return scores

    def _get_workflow_assignment(
        self,
        workflow_id: str,
        assignments: List[RobotAssignment],
    ) -> Optional[str]:
        """Find the default robot assignment for a workflow.

        Args:
            workflow_id: Workflow to look up.
            assignments: List of assignments to search.

        Returns:
            Robot ID if found, None otherwise.
        """
        # Filter assignments for this workflow, prefer defaults and higher priority
        workflow_assignments = [a for a in assignments if a.workflow_id == workflow_id]

        if not workflow_assignments:
            return None

        # Sort by: is_default (True first), priority (higher first)
        workflow_assignments.sort(key=lambda a: (not a.is_default, -a.priority))

        return workflow_assignments[0].robot_id

    def _get_node_override(
        self,
        workflow_id: str,
        node_id: str,
        overrides: List[NodeRobotOverride],
    ) -> Optional[NodeRobotOverride]:
        """Find the override for a specific node.

        Args:
            workflow_id: Workflow containing the node.
            node_id: Node to look up.
            overrides: List of overrides to search.

        Returns:
            NodeRobotOverride if found, None otherwise.
        """
        for override in overrides:
            if (
                override.workflow_id == workflow_id
                and override.node_id == node_id
                and override.is_active
            ):
                return override
        return None

    def _find_robot_by_id(
        self,
        robot_id: str,
        robots: List[Robot],
    ) -> Optional[Robot]:
        """Find a robot by ID.

        Args:
            robot_id: ID to search for.
            robots: List of robots.

        Returns:
            Robot if found, None otherwise.
        """
        for robot in robots:
            if robot.id == robot_id:
                return robot
        return None

    def _select_least_loaded(self, robots: List[Robot]) -> Robot:
        """Select the least loaded robot from a list.

        Args:
            robots: Non-empty list of available robots.

        Returns:
            Robot with lowest utilization.

        Raises:
            NoAvailableRobotError: If list is empty.
        """
        if not robots:
            raise NoAvailableRobotError("No robots provided for selection")

        return min(robots, key=lambda r: r.utilization)
