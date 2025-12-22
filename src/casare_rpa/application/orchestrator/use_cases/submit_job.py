"""SubmitJobUseCase - Submit a job for cloud execution.

This use case orchestrates job submission by:
- Loading workflow assignments and overrides
- Selecting a robot (explicit or auto via RobotSelectionService)
- Creating a Job entity
- Persisting to repository
- Dispatching to robot via dispatcher
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from casare_rpa.domain.orchestrator.entities.job import Job, JobPriority, JobStatus
from casare_rpa.domain.orchestrator.entities.robot import Robot, RobotCapability
from casare_rpa.domain.orchestrator.services.robot_selection_service import (
    RobotSelectionService,
)
from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.domain.orchestrator.errors import (
    NoAvailableRobotError,
    RobotNotFoundError,
)
from casare_rpa.infrastructure.persistence.repositories import (
    JobRepository,
    RobotRepository,
    WorkflowAssignmentRepository,
    NodeOverrideRepository,
)
from casare_rpa.application.orchestrator.services.dispatcher_service import (
    JobDispatcher,
)


class SubmitJobUseCase:
    """Use case for submitting a job for cloud execution.

    Orchestrates the complete job submission workflow:
    1. Load assignments/overrides for workflow
    2. Select robot (explicit or auto via RobotSelectionService)
    3. Create Job entity
    4. Save to repository
    5. Dispatch to robot via dispatcher
    6. Return job with status

    This use case coordinates domain logic (RobotSelectionService) with
    infrastructure (repositories, dispatcher) following Clean Architecture.
    """

    def __init__(
        self,
        job_repository: JobRepository,
        robot_repository: RobotRepository,
        assignment_repository: WorkflowAssignmentRepository,
        override_repository: NodeOverrideRepository,
        robot_selection_service: RobotSelectionService,
        dispatcher: JobDispatcher,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            job_repository: Repository for job persistence.
            robot_repository: Repository for robot data.
            assignment_repository: Repository for workflow assignments.
            override_repository: Repository for node overrides.
            robot_selection_service: Domain service for robot selection.
            dispatcher: Job dispatcher for sending jobs to robots.
        """
        self._job_repo = job_repository
        self._robot_repo = robot_repository
        self._assignment_repo = assignment_repository
        self._override_repo = override_repository
        self._robot_selection = robot_selection_service
        self._dispatcher = dispatcher

    async def execute(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        robot_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        variables: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 3600,
        workflow_name: Optional[str] = None,
        environment: str = "default",
        created_by: str = "",
        scheduled_time: Optional[datetime] = None,
    ) -> Job:
        """Submit a job for execution on a robot.

        Args:
            workflow_id: ID of the workflow to execute.
            workflow_data: Serialized workflow JSON data.
            robot_id: Optional specific robot ID. If None, auto-selects.
            priority: Job priority level.
            variables: Optional variables to pass to workflow.
            timeout_seconds: Job timeout in seconds.
            workflow_name: Name of the workflow.
            environment: Execution environment.
            created_by: User/system that created the job.
            scheduled_time: Optional scheduled execution time.

        Returns:
            Created Job entity with PENDING or QUEUED status.

        Raises:
            NoAvailableRobotError: If no suitable robot is available.
            RobotNotFoundError: If specified robot doesn't exist.
            ValueError: If workflow_id is empty or invalid.
        """
        logger.info(f"Submitting job for workflow {workflow_id}")

        # Validate inputs
        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")

        # 1. Load all robots
        all_robots: List[Robot] = await self._robot_repo.get_all()

        # 2. Load workflow assignments
        assignments: List[RobotAssignment] = await self._assignment_repo.get_by_workflow(
            workflow_id
        )

        # 3. Load node overrides for the workflow
        await self._override_repo.get_by_workflow(workflow_id)

        # 4. Select robot
        selected_robot_id: str
        if robot_id:
            # Explicit robot specified - verify it exists and is available
            robot = await self._robot_repo.get_by_id(robot_id)
            if not robot:
                raise RobotNotFoundError(f"Robot {robot_id} not found")
            if not robot.can_accept_job():
                raise NoAvailableRobotError(
                    f"Robot {robot_id} is not available "
                    f"(status={robot.status.value}, jobs={robot.current_jobs}/{robot.max_concurrent_jobs})"
                )
            selected_robot_id = robot_id
            logger.debug(f"Using explicitly specified robot: {robot_id}")
        else:
            # Auto-select using domain service
            # Analyze workflow for required capabilities
            required_capabilities = self._analyze_workflow_capabilities(workflow_data)

            selected_robot_id = self._robot_selection.select_robot_for_workflow(
                workflow_id=workflow_id,
                robots=all_robots,
                assignments=assignments,
                required_capabilities=required_capabilities,
            )
            logger.debug(f"Auto-selected robot: {selected_robot_id}")

        # Get the selected robot for name
        selected_robot = await self._robot_repo.get_by_id(selected_robot_id)
        robot_name = selected_robot.name if selected_robot else ""

        # 5. Prepare workflow JSON with variables
        workflow_json = self._prepare_workflow_json(workflow_data, variables)

        # Determine workflow name
        final_workflow_name = workflow_name
        if not final_workflow_name:
            final_workflow_name = workflow_data.get("metadata", {}).get("name", "")
            if not final_workflow_name:
                final_workflow_name = workflow_data.get("name", f"Workflow-{workflow_id[:8]}")

        # 6. Create Job entity
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            workflow_id=workflow_id,
            workflow_name=final_workflow_name,
            robot_id=selected_robot_id,
            robot_name=robot_name,
            status=JobStatus.PENDING,
            priority=priority,
            environment=environment,
            workflow_json=workflow_json,
            scheduled_time=scheduled_time,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )

        logger.debug(f"Created job entity: {job_id}")

        # 7. Save to repository
        await self._job_repo.save(job)
        logger.info(f"Job {job_id} saved to repository")

        # 8. Dispatch to robot
        try:
            await self._dispatch_job(job, selected_robot)
            logger.info(f"Job {job_id} dispatched to robot {selected_robot_id}")
        except Exception as e:
            logger.error(f"Failed to dispatch job {job_id}: {e}")
            # Job is still saved as PENDING - can be picked up later

        return job

    def _analyze_workflow_capabilities(
        self,
        workflow_data: Dict[str, Any],
    ) -> Optional[Set[RobotCapability]]:
        """Analyze workflow to determine required robot capabilities.

        Inspects workflow nodes to determine what capabilities are needed.

        Args:
            workflow_data: Serialized workflow data.

        Returns:
            Set of required capabilities, or None if no special requirements.
        """
        capabilities: Set[RobotCapability] = set()
        nodes = workflow_data.get("nodes", {})
        if not isinstance(nodes, dict):
            return None
        nodes_list = list(nodes.values())

        for node in nodes_list:
            if isinstance(node, dict):
                node_type = node.get("node_type", "")
            else:
                node_type = getattr(node, "node_type", "") or type(node).__name__

            node_type_lower = node_type.lower()

            # Browser nodes require browser capability
            if any(
                term in node_type_lower
                for term in ["browser", "playwright", "navigate", "click", "scrape"]
            ):
                capabilities.add(RobotCapability.BROWSER)

            # Desktop nodes require desktop capability
            if any(
                term in node_type_lower for term in ["desktop", "uiautomation", "window", "win32"]
            ):
                capabilities.add(RobotCapability.DESKTOP)

            # ML/AI nodes may require GPU
            if any(term in node_type_lower for term in ["ml", "ai", "model", "llm", "ocr"]):
                capabilities.add(RobotCapability.GPU)

        return capabilities if capabilities else None

    def _prepare_workflow_json(
        self,
        workflow_data: Dict[str, Any],
        variables: Optional[Dict[str, Any]],
    ) -> str:
        """Prepare workflow JSON with injected variables.

        Args:
            workflow_data: Workflow data dictionary.
            variables: Optional variables to inject.

        Returns:
            JSON string of workflow with variables.
        """
        import orjson

        if variables:
            # Inject variables into workflow data
            workflow_copy = dict(workflow_data)
            existing_vars = workflow_copy.get("variables", {})
            if isinstance(existing_vars, dict):
                existing_vars.update(variables)
            else:
                existing_vars = variables
            workflow_copy["variables"] = existing_vars
            return orjson.dumps(workflow_copy).decode()

        return orjson.dumps(workflow_data).decode()

    async def _dispatch_job(
        self,
        job: Job,
        robot: Optional[Robot],
    ) -> None:
        """Dispatch job to robot via dispatcher.

        Args:
            job: Job to dispatch.
            robot: Target robot.
        """
        if not robot:
            return

        # Register robot with dispatcher if not already registered
        if not self._dispatcher.get_robot(robot.id):
            self._dispatcher.register_robot(robot)

        # Let dispatcher handle the job
        selected = self._dispatcher.select_robot(job)
        if selected:
            # Transition job to QUEUED
            job.transition_to(JobStatus.QUEUED)
            await self._job_repo.save(job)
            logger.debug(f"Job {job.id} transitioned to QUEUED")


__all__ = ["SubmitJobUseCase"]
