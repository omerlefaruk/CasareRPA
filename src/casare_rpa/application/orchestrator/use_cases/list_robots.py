"""ListRobotsUseCase - List and filter robots.

This use case provides queries for robots with various filtering options:
- Get all registered robots
- Get available robots (can accept jobs)
- Get robots by capability
- Get robots assigned to a workflow
"""

from loguru import logger

from casare_rpa.domain.orchestrator.entities.robot import Robot, RobotCapability
from casare_rpa.infrastructure.persistence.repositories import (
    RobotRepository,
    WorkflowAssignmentRepository,
)


class ListRobotsUseCase:
    """Use case for listing and filtering robots.

    Provides read-only queries against the robot repository with
    various filtering options. Useful for:
    - Robot management UI
    - Robot selection dialogs
    - Monitoring dashboards
    """

    def __init__(
        self,
        robot_repository: RobotRepository,
        assignment_repository: WorkflowAssignmentRepository | None = None,
    ) -> None:
        """Initialize use case with repositories.

        Args:
            robot_repository: Repository for robot data.
            assignment_repository: Optional repository for workflow assignments.
                Required for get_for_workflow().
        """
        self._robot_repo = robot_repository
        self._assignment_repo = assignment_repository

    async def get_all(self) -> list[Robot]:
        """Get all registered robots.

        Returns:
            List of all Robot entities, sorted by name.
        """
        logger.debug("Fetching all robots")
        robots = await self._robot_repo.get_all()
        logger.debug(f"Found {len(robots)} robots")
        return robots

    async def get_available(self) -> list[Robot]:
        """Get robots that can accept jobs.

        A robot is available if:
        - Status is ONLINE
        - Has capacity for more jobs (current_jobs < max_concurrent_jobs)

        Returns:
            List of available Robot entities, sorted by load (lowest first).
        """
        logger.debug("Fetching available robots")
        robots = await self._robot_repo.get_available()
        logger.debug(f"Found {len(robots)} available robots")
        return robots

    async def get_by_capability(
        self,
        capability: RobotCapability,
    ) -> list[Robot]:
        """Get robots with a specific capability.

        Args:
            capability: Required capability to filter by.

        Returns:
            List of robots with the specified capability.
        """
        logger.debug(f"Fetching robots with capability: {capability.value}")
        robots = await self._robot_repo.get_by_capability(capability)
        logger.debug(f"Found {len(robots)} robots with capability {capability.value}")
        return robots

    async def get_by_capabilities(
        self,
        capabilities: list[RobotCapability],
    ) -> list[Robot]:
        """Get robots with all specified capabilities.

        Args:
            capabilities: List of required capabilities.

        Returns:
            List of robots with all specified capabilities.
        """
        logger.debug(f"Fetching robots with capabilities: {capabilities}")
        capability_set = set(capabilities)
        robots = await self._robot_repo.get_by_capabilities(capability_set)
        logger.debug(f"Found {len(robots)} robots with all required capabilities")
        return robots

    async def get_for_workflow(
        self,
        workflow_id: str,
    ) -> list[Robot]:
        """Get robots assigned to a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            List of robots assigned to the workflow.

        Raises:
            ValueError: If assignment_repository was not provided.
        """
        if not self._assignment_repo:
            raise ValueError("assignment_repository required for get_for_workflow()")

        logger.debug(f"Fetching robots for workflow: {workflow_id}")

        # Get workflow assignments
        assignments = await self._assignment_repo.get_by_workflow(workflow_id)

        if not assignments:
            logger.debug(f"No robots assigned to workflow {workflow_id}")
            return []

        # Fetch robots for each assignment
        robots: list[Robot] = []
        for assignment in assignments:
            robot = await self._robot_repo.get_by_id(assignment.robot_id)
            if robot:
                robots.append(robot)

        logger.debug(f"Found {len(robots)} robots for workflow {workflow_id}")
        return robots

    async def get_default_for_workflow(
        self,
        workflow_id: str,
    ) -> Robot | None:
        """Get the default robot for a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            Default Robot for the workflow, or None if not assigned.

        Raises:
            ValueError: If assignment_repository was not provided.
        """
        if not self._assignment_repo:
            raise ValueError("assignment_repository required for get_default_for_workflow()")

        logger.debug(f"Fetching default robot for workflow: {workflow_id}")

        # Get default assignment
        assignment = await self._assignment_repo.get_default_for_workflow(workflow_id)

        if not assignment:
            logger.debug(f"No default robot for workflow {workflow_id}")
            return None

        robot = await self._robot_repo.get_by_id(assignment.robot_id)
        if robot:
            logger.debug(f"Default robot for workflow {workflow_id}: {robot.name}")
        return robot

    async def get_by_id(
        self,
        robot_id: str,
    ) -> Robot | None:
        """Get a specific robot by ID.

        Args:
            robot_id: ID of the robot.

        Returns:
            Robot entity or None if not found.
        """
        logger.debug(f"Fetching robot: {robot_id}")
        return await self._robot_repo.get_by_id(robot_id)

    async def get_by_name(
        self,
        name: str,
    ) -> Robot | None:
        """Get a robot by name/hostname.

        Args:
            name: Name or hostname of the robot.

        Returns:
            Robot entity or None if not found.
        """
        logger.debug(f"Fetching robot by name: {name}")
        return await self._robot_repo.get_by_hostname(name)

    async def get_online(self) -> list[Robot]:
        """Get all online robots.

        Returns:
            List of robots with ONLINE status.
        """
        from casare_rpa.domain.orchestrator.entities.robot import RobotStatus

        logger.debug("Fetching online robots")
        robots = await self._robot_repo.get_by_status(RobotStatus.ONLINE)
        logger.debug(f"Found {len(robots)} online robots")
        return robots

    async def get_offline(self) -> list[Robot]:
        """Get all offline robots.

        Returns:
            List of robots with OFFLINE status.
        """
        from casare_rpa.domain.orchestrator.entities.robot import RobotStatus

        logger.debug("Fetching offline robots")
        robots = await self._robot_repo.get_by_status(RobotStatus.OFFLINE)
        logger.debug(f"Found {len(robots)} offline robots")
        return robots

    async def get_busy(self) -> list[Robot]:
        """Get all busy robots (at max capacity).

        Returns:
            List of robots with BUSY status.
        """
        from casare_rpa.domain.orchestrator.entities.robot import RobotStatus

        logger.debug("Fetching busy robots")
        robots = await self._robot_repo.get_by_status(RobotStatus.BUSY)
        logger.debug(f"Found {len(robots)} busy robots")
        return robots

    async def get_with_available_capacity(
        self,
        min_capacity: int = 1,
    ) -> list[Robot]:
        """Get robots with at least minimum available capacity.

        Args:
            min_capacity: Minimum number of job slots required.

        Returns:
            List of robots with sufficient capacity.
        """
        logger.debug(f"Fetching robots with at least {min_capacity} capacity")

        # Get all available robots first
        available = await self._robot_repo.get_available()

        # Filter by capacity
        robots = [r for r in available if (r.max_concurrent_jobs - r.current_jobs) >= min_capacity]

        logger.debug(f"Found {len(robots)} robots with capacity >= {min_capacity}")
        return robots

    async def search(
        self,
        query: str,
    ) -> list[Robot]:
        """Search robots by name or tags.

        Args:
            query: Search query string.

        Returns:
            List of robots matching the query.
        """
        logger.debug(f"Searching robots: {query}")

        all_robots = await self._robot_repo.get_all()
        query_lower = query.lower()

        robots = [
            r
            for r in all_robots
            if query_lower in r.name.lower() or any(query_lower in tag.lower() for tag in r.tags)
        ]

        logger.debug(f"Found {len(robots)} robots matching '{query}'")
        return robots

    async def get_statistics(self) -> dict:
        """Get robot fleet statistics.

        Returns:
            Dictionary with fleet statistics.
        """
        from casare_rpa.domain.orchestrator.entities.robot import RobotStatus

        all_robots = await self._robot_repo.get_all()

        # Count by status
        online = sum(1 for r in all_robots if r.status == RobotStatus.ONLINE)
        offline = sum(1 for r in all_robots if r.status == RobotStatus.OFFLINE)
        busy = sum(1 for r in all_robots if r.status == RobotStatus.BUSY)
        error = sum(1 for r in all_robots if r.status == RobotStatus.ERROR)
        maintenance = sum(1 for r in all_robots if r.status == RobotStatus.MAINTENANCE)

        # Capacity statistics
        total_capacity = sum(r.max_concurrent_jobs for r in all_robots)
        current_load = sum(r.current_jobs for r in all_robots)
        available_capacity = total_capacity - current_load

        # Calculate utilization
        utilization = (current_load / total_capacity * 100) if total_capacity > 0 else 0

        # Capability distribution
        capabilities_count: dict = {}
        for robot in all_robots:
            for cap in robot.capabilities:
                cap_name = cap.value
                capabilities_count[cap_name] = capabilities_count.get(cap_name, 0) + 1

        return {
            "total": len(all_robots),
            "by_status": {
                "online": online,
                "offline": offline,
                "busy": busy,
                "error": error,
                "maintenance": maintenance,
            },
            "capacity": {
                "total": total_capacity,
                "current_load": current_load,
                "available": available_capacity,
                "utilization_percent": round(utilization, 1),
            },
            "capabilities": capabilities_count,
        }


__all__ = ["ListRobotsUseCase"]
