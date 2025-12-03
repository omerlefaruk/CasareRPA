"""
CasareRPA - Infrastructure Persistence Repositories

PostgreSQL repository implementations for robot orchestration entities.
All repositories use asyncpg with connection pooling for efficient database operations.
"""

from casare_rpa.infrastructure.persistence.repositories.api_key_repository import (
    ApiKeyRepository,
)
from casare_rpa.infrastructure.persistence.repositories.job_repository import (
    JobRepository,
)
from casare_rpa.infrastructure.persistence.repositories.log_repository import (
    LogRepository,
)
from casare_rpa.infrastructure.persistence.repositories.node_override_repository import (
    NodeOverrideRepository,
)
from casare_rpa.infrastructure.persistence.repositories.robot_repository import (
    RobotRepository,
)
from casare_rpa.infrastructure.persistence.repositories.tenant_repository import (
    TenantRepository,
)
from casare_rpa.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from casare_rpa.infrastructure.persistence.repositories.workflow_assignment_repository import (
    WorkflowAssignmentRepository,
)

__all__ = [
    "ApiKeyRepository",
    "JobRepository",
    "LogRepository",
    "NodeOverrideRepository",
    "RobotRepository",
    "TenantRepository",
    "UserRepository",
    "WorkflowAssignmentRepository",
]
