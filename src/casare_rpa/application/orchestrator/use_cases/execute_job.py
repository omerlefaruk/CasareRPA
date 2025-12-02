"""Execute Job use case."""

from loguru import logger

from casare_rpa.domain.orchestrator.entities import Job, JobStatus
from casare_rpa.domain.orchestrator.repositories import JobRepository, RobotRepository
from casare_rpa.domain.orchestrator.errors import JobTransitionError


class ExecuteJobUseCase:
    """Use case for executing a job on a robot.

    Orchestrates job execution workflow:
    1. Validate job exists and can transition to RUNNING
    2. Verify robot is available
    3. Transition job to RUNNING state
    4. Persist state changes
    """

    def __init__(
        self,
        job_repository: JobRepository,
        robot_repository: RobotRepository,
    ):
        """Initialize use case with repository dependencies.

        Args:
            job_repository: Repository for job persistence
            robot_repository: Repository for robot data
        """
        self._job_repo = job_repository
        self._robot_repo = robot_repository

    async def execute(self, job_id: str) -> Job:
        """Execute a job.

        Args:
            job_id: ID of job to execute

        Returns:
            Updated job with RUNNING status

        Raises:
            ValueError: If job not found
            JobTransitionError: If job cannot transition to RUNNING
        """
        logger.info(f"Executing job {job_id}")

        # 1. Load job
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # 2. Validate robot exists and is online
        robot = await self._robot_repo.get_by_id(job.robot_id)
        if not robot:
            logger.error(f"Robot {job.robot_id} not found for job {job_id}")
            raise ValueError(f"Robot {job.robot_id} not found")

        if not robot.is_available:
            logger.warning(
                f"Robot {robot.id} not available (status: {robot.status.value})"
            )
            raise ValueError(f"Robot {robot.id} is not available")

        # 3. Transition job to RUNNING
        try:
            job.transition_to(JobStatus.RUNNING)
        except JobTransitionError as e:
            logger.error(f"Cannot execute job {job_id}: {e}")
            raise

        # 4. Update robot assignment
        robot.assign_job(job_id)

        # 5. Persist changes
        await self._job_repo.save(job)
        await self._robot_repo.save(robot)

        logger.info(f"Job {job_id} transitioned to RUNNING on robot {robot.id}")
        return job
