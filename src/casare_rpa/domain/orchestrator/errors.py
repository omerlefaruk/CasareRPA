"""Domain errors for orchestrator."""


class OrchestratorDomainError(Exception):
    """Base exception for orchestrator domain errors."""

    pass


# Robot-related errors


class RobotAtCapacityError(OrchestratorDomainError):
    """Raised when robot is at max concurrent jobs capacity."""

    pass


class RobotUnavailableError(OrchestratorDomainError):
    """Raised when robot is not available for job assignment."""

    pass


class RobotNotFoundError(OrchestratorDomainError):
    """Raised when specified robot does not exist."""

    pass


class NoAvailableRobotError(OrchestratorDomainError):
    """Raised when no robot is available to handle a job.

    This can happen when:
    - All robots are offline
    - All robots are at capacity
    - No robots have required capabilities
    """

    pass


class InvalidRobotStateError(OrchestratorDomainError):
    """Raised when robot operation violates state invariants."""

    pass


class DuplicateJobAssignmentError(OrchestratorDomainError):
    """Raised when trying to assign a job that's already assigned to the robot."""

    pass


# Job-related errors


class InvalidJobStateError(OrchestratorDomainError):
    """Raised when job operation violates state invariants."""

    pass


class JobTransitionError(OrchestratorDomainError):
    """Raised when invalid job status transition attempted."""

    pass


class JobNotFoundError(OrchestratorDomainError):
    """Raised when specified job does not exist."""

    pass


# Assignment-related errors


class InvalidAssignmentError(OrchestratorDomainError):
    """Raised when a robot assignment is invalid.

    This can happen when:
    - Assigning to a non-existent workflow
    - Assigning to a non-existent robot
    - Creating conflicting assignments
    """

    pass


class DuplicateAssignmentError(OrchestratorDomainError):
    """Raised when creating a duplicate assignment."""

    pass
