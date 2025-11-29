"""Domain errors for orchestrator."""


class OrchestratorDomainError(Exception):
    """Base exception for orchestrator domain errors."""

    pass


class RobotAtCapacityError(OrchestratorDomainError):
    """Raised when robot is at max concurrent jobs capacity."""

    pass


class RobotUnavailableError(OrchestratorDomainError):
    """Raised when robot is not available for job assignment."""

    pass


class InvalidRobotStateError(OrchestratorDomainError):
    """Raised when robot operation violates state invariants."""

    pass


class InvalidJobStateError(OrchestratorDomainError):
    """Raised when job operation violates state invariants."""

    pass


class JobTransitionError(OrchestratorDomainError):
    """Raised when invalid job status transition attempted."""

    pass
